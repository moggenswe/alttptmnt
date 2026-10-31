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

README = """TMNT x A Link to the Past - an Archipelago randomizer created by Mogswe

1. Double-click install.cmd. It asks for your two ROMs (A Link to the Past, Japan 1.0, and
   Teenage Mutant Ninja Turtles, NES USA), lists what it needs to download and asks before it does.
2. Double-click start.cmd: create a seed, start a session, check everything before going live, stop it.

The full guide is in site/index.html (open it in a browser). Windows 10 or 11.
Version {commit}, {date}.
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
