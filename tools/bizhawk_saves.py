"""Keeps A Link to the Past's save safe in BizHawk; tools/start_stream.ps1 runs it before it starts BizHawk.

    .venv/Scripts/python.exe tools/bizhawk_saves.py --bizhawk <BizHawk folder> --seed AP_<seed>

1. Autosave: turns on BizHawk's "AutosaveSaveRAM" (every FLUSH_FRAMES frames) in config.ini. Without it the save
   reaches the disk only when BizHawk closes normally, so a crash loses everything since the start of the session.
2. Crash recovery: the autosave goes to <rom>.AutoSaveRAM.SaveRAM, but BizHawk loads it only when there is no
   regular <rom>.SaveRAM. After a crash the autosave is the newer one, so it is copied over the regular save here.
3. One save per seed: every seed's ROM is copied to alttp-stream.sfc (fixed window titles for OBS), and BizHawk
   names the save after the ROM. The save of the seed played before is parked as alttp-stream.<seed>.SaveRAM and
   this seed's own save, if any, is put back. alttp-stream.seed says whose save alttp-stream.SaveRAM is.

All three behaviours of BizHawk 2.11.1 were checked by hand on 2026-10-31 (docs/stream-tools.md).
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
from pathlib import Path

ROM_NAME = "alttp-stream"  # tools/start_stream.ps1
FLUSH_FRAMES = 3600        # one minute at 60 frames per second


def autosave_on(config_text: str) -> bool:
    flush = re.search(r'"FlushSaveRamFrames":\s*(\d+)', config_text)
    return bool(re.search(r'"AutosaveSaveRAM":\s*true', config_text)) and bool(flush) and 0 < int(flush[1]) <= FLUSH_FRAMES


def with_autosave(config_text: str) -> str:
    text = re.sub(r'"AutosaveSaveRAM":\s*(true|false)', '"AutosaveSaveRAM": true', config_text)
    return re.sub(r'"FlushSaveRamFrames":\s*\d+', f'"FlushSaveRamFrames": {FLUSH_FRAMES}', text)


def ensure_autosave(config: Path) -> str:
    """Turn the autosave on in BizHawk's config.ini; BizHawk must be closed (it rewrites the file on exit)."""
    if not config.exists():
        return f"no {config} yet (BizHawk writes it when it closes the first time); autosave not set"
    text = config.read_text(encoding="utf-8-sig")
    if autosave_on(text):
        return "BizHawk autosaves A Link to the Past's save every minute"
    if '"AutosaveSaveRAM"' not in text or '"FlushSaveRamFrames"' not in text:
        return f"{config} has no autosave settings; autosave not set"
    config.write_text(with_autosave(text), encoding="utf-8")
    return "turned on BizHawk's autosave of A Link to the Past's save (every minute)"


def prepare_alttp_save(save_dir: Path, seed: str, now: float | None = None) -> list[str]:
    """Recover after a crash, then make alttp-stream.SaveRAM this seed's save. Returns what was done."""
    done = []
    save_dir.mkdir(parents=True, exist_ok=True)
    regular = save_dir / f"{ROM_NAME}.SaveRAM"
    auto = save_dir / f"{ROM_NAME}.AutoSaveRAM.SaveRAM"
    marker = save_dir / f"{ROM_NAME}.seed"
    owner = marker.read_text(encoding="utf-8").strip() if marker.exists() else None

    if auto.exists() and (not regular.exists() or auto.stat().st_mtime > regular.stat().st_mtime):
        if regular.exists():
            shutil.copy2(regular, save_dir / f"{ROM_NAME}.SaveRAM.before-recovery")
        shutil.copy2(auto, regular)
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(auto.stat().st_mtime))
        done.append(f"A Link to the Past: using BizHawk's autosave of {stamp}, newer than the save file "
                    "(after a crash, or a session in which the game wrote nothing new)")
    for leftover in (auto, save_dir / f"{auto.name}.bak"):
        leftover.unlink(missing_ok=True)

    if owner != seed:
        if regular.exists():
            parked_as = owner or "unknown-" + time.strftime("%Y%m%d-%H%M%S", time.localtime(now))
            regular.replace(save_dir / f"{ROM_NAME}.{parked_as}.SaveRAM")
            done.append(f"put away the save of {parked_as} as {ROM_NAME}.{parked_as}.SaveRAM")
        own = save_dir / f"{ROM_NAME}.{seed}.SaveRAM"
        if own.exists():
            own.replace(regular)
            done.append(f"put back the save of {seed}")
        marker.write_text(seed, encoding="utf-8")
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--bizhawk", type=Path, required=True, help="the folder with EmuHawk.exe")
    parser.add_argument("--seed", required=True, help="the seed's name, e.g. AP_12345 (the zip without .zip)")
    args = parser.parse_args()
    print(ensure_autosave(args.bizhawk / "config.ini"))
    for line in prepare_alttp_save(args.bizhawk / "SNES" / "SaveRAM", args.seed):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
