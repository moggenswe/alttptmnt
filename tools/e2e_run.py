"""End-to-end check of the TMNT slot without a player: MultiServer + BizHawk (connector + area select driver)
+ BizHawkClient, all on this machine.

    .venv/Scripts/python.exe tools/e2e_run.py --seed-zip output/e2e/AP_<seed>.zip --rom output/e2e/<patched>.nes

lua/tmnt_e2e_driver.lua plays the player's part and logs to <out>/driver.txt; this script starts everything,
forwards the driver's /send requests to the server console and stops everything when the driver is done.
Server and client output go to <out>/server.log and <out>/client.log.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AP = REPO / "Archipelago"
EMUHAWK = Path.home() / "Downloads" / "BizHawk-2.11.1-win-x64" / "EmuHawk.exe"
PORT = 38281
SLOT = "Turtles"


def wait_for_text(path: Path, text: str, timeout: float) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.exists() and text in path.read_text(encoding="utf-8", errors="replace"):
            return True
        time.sleep(0.5)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-zip", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=REPO / "output" / "e2e")
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    out = args.out.resolve()
    for name in ("driver.txt", "want_send.txt", "done.txt"):
        (out / name).unlink(missing_ok=True)

    python = sys.executable
    env = dict(os.environ, TMNT_E2E_DIR=str(out), PYTHONIOENCODING="utf-8")
    server_log = open(out / "server.log", "w", encoding="utf-8")
    server = subprocess.Popen([python, "-u", "MultiServer.py", str(args.seed_zip.resolve()), "--host", "127.0.0.1",
                               "--port", str(PORT)],
                              cwd=AP, stdin=subprocess.PIPE, stdout=server_log, stderr=subprocess.STDOUT,
                              text=True, env=env)
    processes = [server]
    try:
        if not wait_for_text(out / "server.log", "Hosting game", 60):
            print("server did not start")
            return 1
        emuhawk = subprocess.Popen([str(EMUHAWK), f"--lua={REPO / 'lua' / 'tmnt_e2e.luases'}", str(args.rom.resolve())],
                                   env=env)
        processes.append(emuhawk)
        time.sleep(5)
        client_log = open(out / "client.log", "w", encoding="utf-8")
        client = subprocess.Popen([python, "-u", "BizHawkClient.py", "--nogui", "--connect", f"localhost:{PORT}"],
                                  cwd=AP, stdin=subprocess.PIPE, stdout=client_log, stderr=subprocess.STDOUT,
                                  text=True, env=env)
        processes.append(client)

        end = time.monotonic() + args.timeout
        while time.monotonic() < end and not (out / "done.txt").exists():
            want = out / "want_send.txt"
            if want.exists():
                item = want.read_text(encoding="utf-8").strip()
                server.stdin.write(f"/send {SLOT} {item}\n")
                server.stdin.flush()
                want.unlink()
            time.sleep(0.5)
        finished = (out / "done.txt").exists()
        print("driver finished" if finished else "TIMEOUT")
        print((out / "driver.txt").read_text(encoding="utf-8") if (out / "driver.txt").exists() else "no driver log")
        return 0 if finished else 1
    finally:
        for process in reversed(processes):
            process.terminate()


if __name__ == "__main__":
    sys.exit(main())
