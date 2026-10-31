"""Keeps PopTracker's settings file usable; tools/start_stream.ps1 runs it before it starts PopTracker.

    .venv/Scripts/python.exe tools/poptracker_config.py [--config %APPDATA%\\PopTracker\\PopTracker.json]

PopTracker writes the file when it closes, and a shorter file written over a longer one can keep the end of the
old one (seen twice on 2026-10-31 after closing both windows, also one at a time: text after the JSON). PopTracker
then treats the file as missing: it asks "Check for PopTracker updates on start?" and waits, unconnected. This
keeps the first JSON value in the file, sets the settings the stream needs, and writes the file in one go.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT = Path(os.environ.get("APPDATA", "")) / "PopTracker" / "PopTracker.json"
STREAM_SETTINGS = {
    "software_renderer": True,   # OBS window capture shows hardware-rendered PopTracker as black
    "check_for_updates": False,  # no question on start
    "add_emo_packs": False,      # no question about EmoTracker packs
}


def repaired(text: str) -> tuple[dict, bool]:
    """(settings, whether the text needed repair). Unreadable text gives empty settings."""
    try:
        return json.loads(text), False
    except ValueError:
        pass
    try:
        value, _ = json.JSONDecoder().raw_decode(text.lstrip())
    except ValueError:
        return {}, True
    return (value if isinstance(value, dict) else {}), True


def ensure(config: Path) -> str:
    text = config.read_text(encoding="utf-8-sig") if config.exists() else "{}"
    settings, broken = repaired(text)
    changed = broken or any(settings.get(key) != value for key, value in STREAM_SETTINGS.items())
    if not changed:
        return "PopTracker settings OK"
    settings.update(STREAM_SETTINGS)
    config.parent.mkdir(parents=True, exist_ok=True)
    partial = config.with_suffix(".json.writing")
    partial.write_text(json.dumps(settings, indent=4) + "\n", encoding="utf-8")
    partial.replace(config)
    return "repaired PopTracker's settings file" if broken else "set PopTracker's stream settings"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", type=Path, default=DEFAULT)
    print(ensure(parser.parse_args().config))
    return 0


if __name__ == "__main__":
    sys.exit(main())
