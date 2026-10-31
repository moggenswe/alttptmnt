"""Swap between the two games with one press, and keep OBS on the game that is being played.

    .venv/Scripts/python.exe tools/game_swap.py [--hotkey ctrl+shift+space] [--no-obs]

tools/start_stream.ps1 starts it in its own console window. While it runs:
- Select+Start on the controller (lua/game_swap.lua, in both BizHawk windows) or the keyboard hotkey brings the
  other game's BizHawk window to the front. Start also pauses the game being left.
- Whenever a game window comes to the front (a swap, Alt+Tab or a click), OBS switches to that game's scene
  (Hyrule or New York) through OBS's WebSocket server, with the collection's default transition (the pizza-wipe).
  OBS is only switched while it shows one of the two game scenes, so a host's own scene is left alone.
- With --server, items that arrive for the game behind are shown in the game being played ("TMNT got Rope Pack",
  "Zelda got Hookshot"), and so are new TMNT areas ("TMNT: Area 3 is open", from lua/tmnt_area_select.lua). It
  watches the server as a read-only Tracker on --slot.

OBS: Tools -> WebSocket Server Settings -> Enable WebSocket server (OBS 28 or later). The port and password are read
from OBS's settings on this PC; --obs-url, --obs-password or OBS_WEBSOCKET_PASSWORD override them.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import os
import queue
import re
import sys
import threading
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SWAP_DIR = REPO / "output" / "swap"  # lua/game_swap.lua writes <system>-request.txt here
SYSTEMS = ("SNES", "NES")             # emu.getsystemid(): A Link to the Past, TMNT
GAME_NAMES = {"SNES": "A Link to the Past", "NES": "TMNT"}
SHORT_NAMES = {"SNES": "Zelda", "NES": "TMNT"}  # in notices, which BizHawk shows in small type
AP_GAMES = {"A Link to the Past": "SNES", "Teenage Mutant Ninja Turtles": "NES"}  # Archipelago's game names
DEFAULT_SCENES = {"SNES": "Hyrule", "NES": "New York"}  # tools/make_obs_collection.py
OBS_SETTINGS = Path(os.environ.get("APPDATA", "")) / "obs-studio" / "plugin_config" / "obs-websocket" / "config.json"


# --- pure helpers (tools/test_game_swap.py) ---------------------------------------------------------------

def system_of_title(title: str) -> str | None:
    """The system of a BizHawk main window, from titles like 'tmnt-stream [NES] - BizHawk'."""
    if "BizHawk" not in title:
        return None
    for system in SYSTEMS:
        if f"[{system}]" in title:
            return system
    return None


def other(system: str) -> str:
    return SYSTEMS[1] if system == SYSTEMS[0] else SYSTEMS[0]


MODIFIERS = {"alt": 0x1, "ctrl": 0x2, "control": 0x2, "shift": 0x4, "win": 0x8}
NAMED_KEYS = {"space": 0x20, "tab": 0x09, "enter": 0x0D, "pause": 0x13, "insert": 0x2D, "delete": 0x2E,
              "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22, "scrolllock": 0x91}


def parse_hotkey(text: str) -> tuple[int, int]:
    """'ctrl+shift+space' -> (modifiers, virtual key) for RegisterHotKey."""
    parts = [part.strip().lower() for part in text.split("+")]
    if not parts or not all(parts):
        raise ValueError(f"not a hotkey: {text!r}")
    modifiers = 0
    for part in parts[:-1]:
        if part not in MODIFIERS:
            raise ValueError(f"unknown modifier {part!r} in {text!r} (use ctrl, shift, alt, win)")
        modifiers |= MODIFIERS[part]
    key = parts[-1]
    if key in NAMED_KEYS:
        return modifiers, NAMED_KEYS[key]
    if re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", key):
        return modifiers, 0x6F + int(key[1:])
    if len(key) == 1 and key.isascii() and key.isalnum():
        return modifiers, ord(key.upper())
    raise ValueError(f"unknown key {key!r} in {text!r}")


def obs_auth(password: str, salt: str, challenge: str) -> str:
    """obs-websocket 5 authentication string."""
    secret = base64.b64encode(hashlib.sha256((password + salt).encode()).digest()).decode()
    return base64.b64encode(hashlib.sha256((secret + challenge).encode()).digest()).decode()


class Requests:
    """Swap requests from lua/game_swap.lua: a token per press in <system>-request.txt, answered in -ack.txt.
    The script also rewrites <system>-ready.txt every ten seconds while it runs. Game events (a token line, then a
    text line) come in <system>-event.txt."""

    ALIVE_SECONDS = 15

    def __init__(self, folder: Path):
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        self.seen = {system: self._read(system) for system in SYSTEMS}  # presses from before we started
        self.seen_events = {system: self._read_event(system)[0] for system in SYSTEMS}
        self.alive = {system: False for system in SYSTEMS}

    def _read_event(self, system: str) -> tuple[str | None, str | None]:
        try:
            lines = (self.folder / f"{system}-event.txt").read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            return None, None
        return (lines[0].strip() or None, lines[1].strip()) if len(lines) >= 2 else (None, None)

    def events(self) -> list[tuple[str, str]]:
        """(system, text) of each event written since the last call."""
        found = []
        for system in SYSTEMS:
            token, text = self._read_event(system)
            if token and token != self.seen_events[system]:
                self.seen_events[system] = token
                found.append((system, text))
        return found

    def changes_in_scripts(self, now: float | None = None) -> list[tuple[str, bool]]:
        """(system, running) for each game whose script started or stopped since the last call."""
        now = time.time() if now is None else now
        changes = []
        for system in SYSTEMS:
            try:
                running = now - (self.folder / f"{system}-ready.txt").stat().st_mtime < self.ALIVE_SECONDS
            except OSError:
                running = False
            if running != self.alive[system]:
                self.alive[system] = running
                changes.append((system, running))
        return changes

    def _read(self, system: str) -> str | None:
        try:
            return (self.folder / f"{system}-request.txt").read_text(encoding="ascii").strip() or None
        except (OSError, UnicodeDecodeError):
            return None

    def poll(self) -> list[str]:
        """Systems that asked for a swap since the last poll; each request is answered."""
        asked = []
        for system in SYSTEMS:
            token = self._read(system)
            if token and token != self.seen[system]:
                self.seen[system] = token
                (self.folder / f"{system}-ack.txt").write_text(token, encoding="ascii")
                asked.append(system)
        return asked


class Notices:
    """Lines "<number> <text>" in <system>-notice.txt; lua/game_swap.lua shows each new number once."""

    KEEP = 20

    def __init__(self, folder: Path):
        self.folder = folder
        self.lines = {system: [] for system in SYSTEMS}
        # Numbers keep growing across restarts of this script (above the last one written, and at least the
        # time in milliseconds), so the game never mistakes a new notice for one it has already shown.
        self.number = 0
        for system in SYSTEMS:
            try:
                text = (folder / f"{system}-notice.txt").read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                head = line.split(" ", 1)[0]
                if head.isdigit():
                    self.number = max(self.number, int(head))

    def add(self, system: str, text: str) -> None:
        self.number = max(self.number + 1, int(time.time() * 1000))
        lines = (self.lines[system] + [f"{self.number} {' '.join(text.split())}"])[-self.KEEP:]
        self.lines[system] = lines
        (self.folder / f"{system}-notice.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def item_notice(item_system: str | None, item: str, playing: str | None) -> tuple[str, str] | None:
    """(system to show it in, text) for an item that arrived, or None when the game being played shows it itself."""
    if not item_system or not playing or item_system == playing:
        return None
    return playing, f"{SHORT_NAMES[item_system]} got {item}"


class ItemWatch(threading.Thread):
    """Watches the Archipelago server as a read-only Tracker and queues (system, item name) for every item sent to
    one of the two games. Reconnects every five seconds; problems are logged once."""

    def __init__(self, url: str, slot: str, password: str | None, log):
        super().__init__(daemon=True)
        self.url, self.slot, self.password, self.log = url, slot, password or "", log
        self.items: queue.Queue = queue.Queue()
        self.last_problem = None

    def run(self) -> None:
        while True:
            try:
                self._watch()
            except Exception as error:
                problem = f"items: server not reachable at {self.url} ({error or type(error).__name__})"
                if problem != self.last_problem:
                    self.log(problem)
                    self.last_problem = problem
            time.sleep(5)

    def _watch(self) -> None:
        from websockets.sync.client import connect
        with connect(self.url, open_timeout=5, close_timeout=1, max_size=None) as ws:
            def packets():
                for raw in ws:
                    yield from json.loads(raw)

            stream = packets()
            room = next(p for p in stream if p.get("cmd") == "RoomInfo")
            ws.send(json.dumps([{"cmd": "GetDataPackage", "games": room.get("games", [])}]))
            package = next(p for p in stream if p.get("cmd") == "DataPackage")
            names = {game: {number: name for name, number in data.get("item_name_to_id", {}).items()}
                     for game, data in package["data"]["games"].items()}
            ws.send(json.dumps([{"cmd": "Connect", "password": self.password, "game": "", "name": self.slot,
                                 "uuid": "tmnt-alttp-game-swap", "items_handling": 0, "tags": ["Tracker"],
                                 "version": {"major": 0, "minor": 6, "build": 8, "class": "Version"},
                                 "slot_data": False}]))
            reply = next(p for p in stream if p.get("cmd") in ("Connected", "ConnectionRefused"))
            if reply["cmd"] == "ConnectionRefused":
                raise ConnectionError(f"refused: {', '.join(reply.get('errors', []))}")
            games = {int(slot): info.get("game") for slot, info in reply.get("slot_info", {}).items()}
            self.last_problem = None
            self.log(f"items: watching the server at {self.url}")
            for packet in stream:
                if packet.get("cmd") == "PrintJSON" and packet.get("type") in ("ItemSend", "ItemCheat"):
                    game = games.get(packet.get("receiving"))
                    item = names.get(game, {}).get(packet.get("item", {}).get("item"))
                    if game in AP_GAMES and item:
                        self.items.put((AP_GAMES[game], item))


# --- OBS -------------------------------------------------------------------------------------------------

class Obs:
    """A small obs-websocket 5 client: connects when needed, retries every ten seconds, never raises."""

    RETRY_SECONDS = 10

    def __init__(self, url: str | None, password: str | None, log):
        self.url, self.password, self.log = url, password, log
        self.ws = None
        self.next_try = 0.0
        self.last_problem = None

    def _settings(self) -> dict:
        try:
            return json.loads(OBS_SETTINGS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _problem(self, text: str) -> None:
        if text != self.last_problem:  # say each problem once, not every retry
            self.log(text)
            self.last_problem = text

    def _connect(self):
        from websockets.sync.client import connect
        settings = self._settings()
        url = self.url or f"ws://127.0.0.1:{settings.get('server_port', 4455)}"
        ws = connect(url, open_timeout=2, close_timeout=1)
        try:
            hello = json.loads(ws.recv(timeout=2))
            identify = {"rpcVersion": 1, "eventSubscriptions": 0}
            auth = hello.get("d", {}).get("authentication")
            if auth:
                password = self.password or os.environ.get("OBS_WEBSOCKET_PASSWORD") or settings.get("server_password")
                if not password:
                    raise ConnectionError("OBS wants a password; pass --obs-password")
                identify["authentication"] = obs_auth(password, auth["salt"], auth["challenge"])
            ws.send(json.dumps({"op": 1, "d": identify}))
            reply = json.loads(ws.recv(timeout=2))
            if reply.get("op") != 2:
                raise ConnectionError("OBS did not accept the login")
        except BaseException:
            ws.close()
            raise
        return ws, url

    def request(self, kind: str, data: dict | None = None) -> dict | None:
        if self.ws is None:
            if time.monotonic() < self.next_try:
                return None
            try:
                self.ws, url = self._connect()
            except Exception as error:  # OBS closed, server off, wrong password: try again later
                self.next_try = time.monotonic() + self.RETRY_SECONDS
                hint = "" if self._settings().get("server_enabled", True) else \
                    " - turn it on in OBS: Tools -> WebSocket Server Settings -> Enable WebSocket server"
                self._problem(f"OBS not reachable ({error or type(error).__name__}){hint}")
                return None
            self.last_problem = None
            self.log(f"connected to OBS at {url}")
        request_id = uuid.uuid4().hex
        try:
            self.ws.send(json.dumps({"op": 6, "d": {"requestType": kind, "requestId": request_id,
                                                    "requestData": data or {}}}))
            while True:
                message = json.loads(self.ws.recv(timeout=3))
                if message.get("op") == 7 and message["d"].get("requestId") == request_id:
                    break
        except Exception as error:
            self.close()
            self._problem(f"lost OBS ({error or type(error).__name__})")
            return None
        status = message["d"].get("requestStatus", {})
        if not status.get("result"):
            self.log(f"OBS: {kind} failed: {status.get('comment', status.get('code'))}")
            return None
        return message["d"].get("responseData") or {}

    def show(self, scene: str, game_scenes: set[str]) -> None:
        current = self.request("GetCurrentProgramScene")
        if current is None:
            return
        name = current.get("sceneName") or current.get("currentProgramSceneName")
        if name == scene:
            return
        if name not in game_scenes:
            self.log(f"OBS shows '{name}', not a game scene: left as it is")
            return
        if self.request("SetCurrentProgramScene", {"sceneName": scene}) is not None:
            self.log(f"OBS -> {scene}")

    def close(self) -> None:
        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None


# --- Windows ---------------------------------------------------------------------------------------------

user32 = ctypes.WinDLL("user32", use_last_error=True) if sys.platform == "win32" else None
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if sys.platform == "win32" else None
ENUM_PROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
WM_HOTKEY, PM_REMOVE, MOD_NOREPEAT, SW_RESTORE = 0x0312, 0x0001, 0x4000, 9
ERROR_ALREADY_EXISTS = 183


def _declare() -> None:
    signatures = {
        "EnumWindows": (wt.BOOL, [ENUM_PROC, wt.LPARAM]),
        "IsWindowVisible": (wt.BOOL, [wt.HWND]),
        "GetWindowTextLengthW": (ctypes.c_int, [wt.HWND]),
        "GetWindowTextW": (ctypes.c_int, [wt.HWND, wt.LPWSTR, ctypes.c_int]),
        "GetForegroundWindow": (wt.HWND, []),
        "SetForegroundWindow": (wt.BOOL, [wt.HWND]),
        "BringWindowToTop": (wt.BOOL, [wt.HWND]),
        "IsIconic": (wt.BOOL, [wt.HWND]),
        "ShowWindow": (wt.BOOL, [wt.HWND, ctypes.c_int]),
        "GetWindowThreadProcessId": (wt.DWORD, [wt.HWND, ctypes.POINTER(wt.DWORD)]),
        "AttachThreadInput": (wt.BOOL, [wt.DWORD, wt.DWORD, wt.BOOL]),
        "RegisterHotKey": (wt.BOOL, [wt.HWND, ctypes.c_int, wt.UINT, wt.UINT]),
        "UnregisterHotKey": (wt.BOOL, [wt.HWND, ctypes.c_int]),
        "PeekMessageW": (wt.BOOL, [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT, wt.UINT]),
    }
    for name, (restype, argtypes) in signatures.items():
        function = getattr(user32, name)
        function.restype, function.argtypes = restype, argtypes
    kernel32.GetCurrentThreadId.restype = wt.DWORD
    kernel32.CreateMutexW.restype = wt.HANDLE
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wt.BOOL, wt.LPCWSTR]


def window_title(hwnd) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def game_windows() -> dict[str, int]:
    """The visible BizHawk main window of each system."""
    found: dict[str, int] = {}

    def visit(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            system = system_of_title(window_title(hwnd))
            if system and system not in found:
                found[system] = hwnd
        return True

    user32.EnumWindows(ENUM_PROC(visit), 0)
    return found


def foreground_system() -> str | None:
    hwnd = user32.GetForegroundWindow()
    return system_of_title(window_title(hwnd)) if hwnd else None


def bring_to_front(hwnd) -> bool:
    """Windows only lets the foreground thread change the foreground window, so borrow its input queue."""
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    foreground = user32.GetForegroundWindow()
    their_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
    our_thread = kernel32.GetCurrentThreadId()
    attached = bool(their_thread and their_thread != our_thread
                    and user32.AttachThreadInput(our_thread, their_thread, True))
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(our_thread, their_thread, False)
    return user32.GetForegroundWindow() == hwnd


# --- main ------------------------------------------------------------------------------------------------

def log(text: str) -> None:
    print(time.strftime("%H:%M:%S"), text, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--hotkey", default="ctrl+shift+space", help="keyboard swap key, or 'none'")
    parser.add_argument("--no-obs", action="store_true", help="only swap windows, leave OBS alone")
    parser.add_argument("--obs-url", help="default: ws://127.0.0.1:<port from OBS's settings>")
    parser.add_argument("--obs-password", help="default: OBS_WEBSOCKET_PASSWORD, else OBS's settings")
    parser.add_argument("--scene-alttp", default=DEFAULT_SCENES["SNES"])
    parser.add_argument("--scene-tmnt", default=DEFAULT_SCENES["NES"])
    parser.add_argument("--swap-dir", type=Path, default=SWAP_DIR)
    parser.add_argument("--server", help="Archipelago server, e.g. ws://localhost:38281, for item notices")
    parser.add_argument("--slot", default="Turtles", help="any slot of the seed, to watch the server as a tracker")
    parser.add_argument("--server-password")
    args = parser.parse_args()
    scenes = {"SNES": args.scene_alttp, "NES": args.scene_tmnt}

    _declare()
    kernel32.CreateMutexW(None, False, "Local\\tmnt-alttp-game-swap")
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        log("game swap is already running")
        return 1

    hotkey = None
    if args.hotkey.lower() != "none":
        modifiers, key = parse_hotkey(args.hotkey)
        if user32.RegisterHotKey(None, 1, modifiers | MOD_NOREPEAT, key):
            hotkey = args.hotkey
        else:
            log(f"could not take the hotkey {args.hotkey} (another program has it); pass --hotkey")
    requests = Requests(args.swap_dir)
    notices = Notices(args.swap_dir)
    obs = None if args.no_obs else Obs(args.obs_url, args.obs_password, log)
    watch = None
    if args.server:
        watch = ItemWatch(args.server, args.slot, args.server_password, log)
        watch.start()
    shown = foreground_system()
    last_played = shown

    def swap(from_system: str | None) -> None:
        source = from_system or last_played
        target = other(source) if source else SYSTEMS[0]
        hwnd = game_windows().get(target)
        if not hwnd:
            log(f"no {GAME_NAMES[target]} window (BizHawk with a [{target}] game) to swap to")
            return
        if bring_to_front(hwnd):
            log(f"-> {GAME_NAMES[target]}")
        else:
            log(f"Windows did not let {GAME_NAMES[target]} come to the front; click its window")

    log("game swap ready: Select+Start on the controller" + (f" or {hotkey}" if hotkey else "")
        + (", OBS follows the game" if obs else ", OBS left alone (--no-obs)")
        + (", item notices on" if watch else ""))
    message = wt.MSG()
    next_script_check = 0.0
    try:
        while True:
            while user32.PeekMessageW(ctypes.byref(message), None, 0, 0, PM_REMOVE):
                if message.message == WM_HOTKEY:
                    swap(foreground_system())
            for system in requests.poll():
                swap(system)
            if time.monotonic() >= next_script_check:
                next_script_check = time.monotonic() + 1
                for system, running in requests.changes_in_scripts():
                    log(f"{GAME_NAMES[system]}: controller swap " + ("ready" if running else
                                                                    "stopped (is BizHawk with its script running?)"))
            playing = foreground_system()
            if playing and playing != shown:
                shown = last_played = playing
                if obs:
                    obs.show(scenes[playing], set(scenes.values()))
            for system, text in requests.events():  # "TMNT: Area 3 is open": wherever the runner is
                if last_played:
                    notices.add(last_played, text)
                    log(f"notice in {GAME_NAMES[last_played]}: {text}")
            while watch and not watch.items.empty():
                notice = item_notice(*watch.items.get(), last_played)
                if notice:
                    notices.add(*notice)
                    log(f"notice in {GAME_NAMES[notice[0]]}: {notice[1]}")
            time.sleep(0.03)
    except KeyboardInterrupt:
        return 0
    finally:
        if hotkey:
            user32.UnregisterHotKey(None, 1)
        if obs:
            obs.close()


if __name__ == "__main__":
    sys.exit(main())
