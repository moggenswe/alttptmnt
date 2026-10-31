"""Check before going live: is every part of the stream set up, running and connected? Prints one line per check
(OK, WARN or FAIL, with what to do) and exits with 1 if anything failed. start.cmd -> "Check before going live".

    .venv/Scripts/python.exe tools/preflight.py [--port 38281] [--alttp Link] [--tmnt Turtles] [--no-obs]

It only reads: it joins the server as a read-only Tracker and asks OBS (if its WebSocket server is on) about scenes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import psutil

import bizhawk_saves
import game_swap

REPO = Path(__file__).resolve().parent.parent
BIZHAWK_DIRS = (REPO / "apps" / "BizHawk-2.11.1", Path.home() / "Downloads" / "BizHawk-2.11.1-win-x64")
POPTRACKER_PACKS = (REPO / "apps" / "PopTracker-0.36.0" / "packs", Path.home() / "Downloads" / "PopTracker-0.36.0" / "packs")
SNI_LUA_PORT = 65398          # Archipelago\SNI\lua\Connector.lua
BIZHAWK_CONNECTOR_PORT = 43055  # Archipelago\data\lua\connector_bizhawk_generic.lua (first of a few)
COLLECTION, SCENES, TRANSITION = "TMNT x ALttP", ("Hyrule", "Kloak (övergång)", "New York"), "Pizza-wipe"
TITLES = {"SNES": "alttp-stream [SNES]", "NES": "tmnt-stream [NES]"}  # tools/start_stream.ps1, the OBS captures

COLOURS = {"OK": "\033[32m", "WARN": "\033[33m", "FAIL": "\033[31m"}


class Report:
    def __init__(self):
        self.counts = {"OK": 0, "WARN": 0, "FAIL": 0}

    def line(self, level: str, text: str, fix: str = "") -> None:
        self.counts[level] += 1
        label = f"{COLOURS[level]}{level:<4}\033[0m" if sys.stdout.isatty() else f"{level:<4}"
        print(f"  {label}  {text}" + (f"\n        -> {fix}" if fix else ""), flush=True)

    def check(self, ok: bool, text: str, fix: str = "", level: str = "FAIL") -> bool:
        self.line("OK" if ok else level, text, "" if ok else fix)
        return ok


# --- what is running ---------------------------------------------------------------------------------------

def processes() -> list[tuple[psutil.Process, str]]:
    found = []
    for process in psutil.process_iter(["name", "cmdline"]):
        try:
            found.append((process, " ".join(process.info["cmdline"] or []) or process.info["name"] or ""))
        except (psutil.Error, TypeError):
            continue
    return found


def connections() -> list:
    try:
        return [c for c in psutil.net_connections("tcp") if c.status == psutil.CONN_ESTABLISHED and c.raddr]
    except psutil.Error:
        return []


def pids_of(found, needle: str) -> set[int]:
    return {process.pid for process, line in found if needle.lower() in line.lower()}


def connected(conns, pids: set[int], port: int) -> bool:
    return any(c.pid in pids and c.raddr.port == port for c in conns)


# --- the server --------------------------------------------------------------------------------------------

def server_check(url: str, slot: str) -> tuple[str | None, str | None]:
    """(seed name, problem) after joining as a Tracker on slot."""
    from websockets.sync.client import connect
    try:
        with connect(url, open_timeout=3, close_timeout=1, max_size=None) as ws:
            room = json.loads(ws.recv(timeout=3))[0]
            ws.send(json.dumps([{"cmd": "Connect", "password": "", "game": "", "name": slot, "items_handling": 0,
                                 "uuid": f"preflight-{slot}", "tags": ["Tracker"], "slot_data": False,
                                 "version": {"major": 0, "minor": 6, "build": 8, "class": "Version"}}]))
            end = time.monotonic() + 5
            while time.monotonic() < end:
                for packet in json.loads(ws.recv(timeout=5)):
                    if packet.get("cmd") == "Connected":
                        return room.get("seed_name"), None
                    if packet.get("cmd") == "ConnectionRefused":
                        return room.get("seed_name"), ", ".join(packet.get("errors", []))
            return room.get("seed_name"), "no answer to the login"
    except Exception as error:
        return None, str(error) or type(error).__name__


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--port", type=int, default=38281)
    parser.add_argument("--alttp", default="Link")
    parser.add_argument("--tmnt", default="Turtles")
    parser.add_argument("--no-obs", action="store_true", help="skip the OBS checks")
    args = parser.parse_args()
    os.system("")  # lets the Windows console show the colours
    report = Report()
    print("TMNT x A Link to the Past - check before going live\n")

    print("Install")
    bizhawk = next((d for d in BIZHAWK_DIRS if (d / "EmuHawk.exe").exists()), None)
    report.check(bizhawk is not None, "BizHawk 2.11.1", "run install.cmd")
    if bizhawk:
        config = bizhawk / "config.ini"
        text = config.read_text(encoding="utf-8-sig") if config.exists() else ""
        report.check(bizhawk_saves.autosave_on(text), "BizHawk autosaves A Link to the Past's save every minute",
                     "start the session with start.cmd (it turns the autosave on while BizHawk is closed)", "WARN")
    states = [REPO / "savestates" / f"area{n}.State" for n in range(1, 7)]
    report.check(all(s.exists() for s in states), "TMNT area savestates (6)", "run install.cmd again")
    packs = next((d for d in POPTRACKER_PACKS if d.exists()), None)
    report.check(bool(packs and list(packs.glob("alttp*")) and list(packs.glob("tmnt*"))),
                 "PopTracker with the ALttP and TMNT packs", "run install.cmd again", "WARN")

    print("\nSession")
    found, conns = processes(), connections()
    url = f"ws://localhost:{args.port}"
    seed, problem = server_check(url, args.alttp)
    if seed is None:  # nothing to check without a session; one line instead of a dozen failures
        report.line("FAIL", f"no session is running (no Archipelago server on port {args.port})",
                    "start.cmd -> Start a session, wait half a minute, then check again")
        return finish(report)
    if report.check(problem is None, f"Archipelago server on port {args.port}, seed {seed}, slot {args.alttp}",
                    f"{args.alttp}: {problem}; check players\\*.yaml"):
        _, problem = server_check(url, args.tmnt)
        report.check(problem is None, f"slot {args.tmnt} is in the seed", f"{args.tmnt}: {problem}; check players\\*.yaml")
    sni = pids_of(found, "sni.exe")
    report.check(bool(sni), "SNI is running", "start the session again")
    windows = {system: game_swap.window_title(hwnd) for system, hwnd in game_swap.game_windows().items()}
    for system, title in TITLES.items():
        report.check(title in windows.get(system, ""), f"BizHawk window '{title} - BizHawk' (OBS captures it)",
                     "start the games with start.cmd, which gives the windows these titles")
    emuhawk = pids_of(found, "emuhawk")
    report.check(connected(conns, emuhawk, SNI_LUA_PORT), "A Link to the Past's BizHawk is connected to SNI",
                 "in that BizHawk: Tools -> Lua Console, open lua\\alttp_stream.luases")
    bizhawk_client = pids_of(found, "BizHawkClient.py")
    report.check(any(c.pid in bizhawk_client and BIZHAWK_CONNECTOR_PORT <= c.raddr.port < BIZHAWK_CONNECTOR_PORT + 5
                     for c in conns), "TMNT's BizHawk is connected to the BizHawk Client",
                 "check the BizHawk Client window; in TMNT's BizHawk the Lua Console must run lua\\tmnt_stream.luases")
    for name, needle in (("SNI Client", "SNIClient.py"), ("BizHawk Client", "BizHawkClient.py")):
        report.check(connected(conns, pids_of(found, needle), args.port), f"{name} is connected to the server",
                     f"type /connect localhost:{args.port} in the {name} window")
    trackers = sum(1 for c in conns if c.pid in pids_of(found, "poptracker") and c.raddr.port == args.port)
    report.check(trackers >= 2, f"both PopTracker windows are connected to the server ({trackers} of 2)",
                 "in PopTracker: the AP button at the top, server localhost:" + str(args.port), "WARN")
    report.check(bool(pids_of(found, "game_swap.py")), "game swap is running (Select+Start, OBS follows the game)",
                 "start the session again, or run .venv\\Scripts\\python.exe tools\\game_swap.py")
    requests = game_swap.Requests(game_swap.SWAP_DIR)
    running = dict(requests.changes_in_scripts())
    for system in game_swap.SYSTEMS:
        report.check(running.get(system, False), f"{game_swap.GAME_NAMES[system]}: swap script runs in BizHawk",
                     "restart that BizHawk with start.cmd", "WARN")

    if not args.no_obs:
        print("\nOBS")
        if report.check(bool(pids_of(found, "obs64")), "OBS is running", "start OBS", "WARN"):
            lines = []
            obs = game_swap.Obs(None, None, lines.append)
            collection = obs.request("GetSceneCollectionList")
            if report.check(collection is not None, "OBS WebSocket server answers",
                            "OBS: Tools -> WebSocket Server Settings -> Enable WebSocket server"
                            + (f" ({lines[-1]})" if lines else "")):
                report.check(collection.get("currentSceneCollectionName") == COLLECTION,
                             f"scene collection '{COLLECTION}' is active",
                             f"OBS: Scene Collection -> {COLLECTION} (import tools\\obs\\tmnt-alttp-scenes.json first)")
                scenes = {s.get("sceneName") for s in (obs.request("GetSceneList") or {}).get("scenes", [])}
                missing = [s for s in SCENES if s not in scenes]
                report.check(not missing, "scenes Hyrule, Kloak and New York", f"missing: {', '.join(missing)}")
                transition = (obs.request("GetCurrentSceneTransition") or {}).get("transitionName")
                report.check(transition == TRANSITION, f"transition is the {TRANSITION}",
                             f"OBS: Scene Transitions -> {TRANSITION} (now: {transition})", "WARN")
                program = (obs.request("GetCurrentProgramScene") or {}).get("sceneName")
                report.line("OK", f"OBS shows '{program}' now")
            obs.close()
    return finish(report)


def finish(report: Report) -> int:
    counts = report.counts
    print()
    if counts["FAIL"]:
        print(f"{counts['FAIL']} problem(s) and {counts['WARN']} warning(s): see the lines above.")
    elif counts["WARN"]:
        print(f"Ready, with {counts['WARN']} warning(s).")
    else:
        print("All set. Have a good stream!")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
