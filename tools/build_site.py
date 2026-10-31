"""Builds the hosted site: public/ = site/ plus downloads/tmnt-alttp.zip (everything a player needs) and
downloads/version.json (size, date, commit) for the download button.

    python tools/build_site.py            (Vercel runs this on every push, see vercel.json)

The zip holds the installer, the start menu, the TMNT world, the BizHawk scripts, the tools, the player files, the
TMNT PopTracker pack and the offline copy of the site, under one folder "tmnt-alttp". It leaves out docs/ (design
notes, on GitHub), the original key art and everything installed or generated. The build stops if anything that
must never be shared would go in: a ROM, a savestate or a seed's patch file.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLIC = REPO / "public"
ZIP_NAME = "tmnt-alttp.zip"
FOLDER = "tmnt-alttp"  # the folder the zip unpacks to
INCLUDE_FILES = ["install.cmd", "install.ps1", "start.cmd"]
INCLUDE_DIRS = ["apworld", "lua", "players", "poptracker", "site", "tools"]
SKIP_PARTS = {"__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc"}
FORBIDDEN_SUFFIXES = {".nes", ".sfc", ".smc", ".state", ".saveram", ".aplttp", ".aptmnt", ".apsave", ".bk2"}

README = """TMNT x A Link to the Past
An Archipelago randomizer created by Mogswe - BETA
Version {commit}, {date}

WHAT IS THIS?
  One runner plays two games at once: The Legend of Zelda: A Link to the Past (SNES)
  and Teenage Mutant Ninja Turtles (NES). The items of both games are shuffled
  together, so Link can find a turtle in a Hyrule chest and the turtles can find
  Link's Moon Pearl in a New York sewer. You win when Ganon and Shredder are both beaten.

WHAT YOU NEED
  - A PC with Windows 10 or 11 and an internet connection for the first install.
  - Your own two ROM files (they are not included and never will be):
      * A Link to the Past, the Japanese 1.0 version (.sfc or .smc)
      * Teenage Mutant Ninja Turtles, the NES USA version (.nes)
    The installer checks them and tells you if a ROM is the wrong version.
  - OBS Studio, only if you want to stream.

GET STARTED (about 10 minutes)
  1. Unzip this folder to a SHORT path, for example C:\\tmntalttp
     (a long path such as inside Downloads can make the install fail).
  2. Double-click install.cmd.
     - Pick your two ROMs when it asks.
     - It lists what it will download (about 290 MB) and asks "Can I download these?".
       Answer Y. Everything is installed inside this folder; nothing else on the PC changes.
     - A game window opens and closes by itself once; that is normal.
  3. Double-click start.cmd and choose with a number:
       1  Create a seed           - makes a new shuffled game
       2  Start a session         - opens both games, the trackers and everything else
       3  Check before going live - every line should say OK
       4  Stop the session        - closes everything and saves your game

WHILE PLAYING
  - Both games run side by side. Press Select+Start to pause and jump to the other game
    (or Ctrl+Shift+Space on the keyboard). Press Start to play on.
  - In TMNT, Select+Up opens the Area menu: you pick which Area to play.
  - When something arrives for the other game, the game you are playing tells you
    at the bottom left, for example "Zelda got Hookshot".

IF SOMETHING GOES WRONG
  - Run start.cmd -> 3 "Check before going live". Every problem line says what to do.
  - Close everything with start.cmd -> 4 and start again with 2. Your progress is kept
    on the server and in the game's save.
  - More help: open site\\index.html in this folder (the full guide, also online at
    https://alttptmnt.vercel.app), page "Help".

THIS IS A BETA
  It works and is tested, but has not had a full playthrough yet. Get the newest
  version from https://alttptmnt.vercel.app before each session.

WHAT IS IN THIS FOLDER
  install.cmd / start.cmd   the two files you double-click
  site\\                     the full guide (open index.html)
  apworld\\, lua\\, tools\\    the randomizer itself; no need to touch
  players\\                  the seed settings (alttp.yaml, tmnt.yaml)
  poptracker\\               the TMNT item tracker
"""


def files_to_ship() -> list[Path]:
    found = [REPO / name for name in INCLUDE_FILES]
    for folder in INCLUDE_DIRS:
        for path in sorted((REPO / folder).rglob("*")):
            relative = path.relative_to(REPO)
            if path.is_file() and not SKIP_PARTS & set(relative.parts) and path.suffix.lower() not in SKIP_SUFFIXES:
                found.append(path)
    forbidden = [str(p.relative_to(REPO)) for p in found if p.suffix.lower() in FORBIDDEN_SUFFIXES]
    if forbidden:
        sys.exit(f"build stopped: these must never be shared: {', '.join(forbidden)}")
    return found


def commit_id() -> str:
    sha = os.environ.get("VERCEL_GIT_COMMIT_SHA")
    if sha:
        return sha[:7]
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "local"


def build_zip(target: Path, commit: str, date: str) -> int:
    files = files_to_ship()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(f"{FOLDER}/README.txt", README.format(commit=commit, date=date).replace("\n", "\r\n"))
        for path in files:
            archive.write(path, f"{FOLDER}/{path.relative_to(REPO).as_posix()}")
    return len(files) + 1


def main() -> int:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    shutil.copytree(REPO / "site", PUBLIC)
    downloads = PUBLIC / "downloads"
    downloads.mkdir()
    commit, date = commit_id(), time.strftime("%Y-%m-%d", time.gmtime())
    count = build_zip(downloads / ZIP_NAME, commit, date)
    data = (downloads / ZIP_NAME).read_bytes()
    version = {"file": ZIP_NAME, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "date": date,
               "commit": commit, "files": count}
    (downloads / "version.json").write_text(json.dumps(version, indent=2) + "\n", encoding="utf-8")
    print(f"{PUBLIC}: site + {ZIP_NAME} ({count} files, {len(data) / 1048576:.1f} MB, {commit}, {date})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
