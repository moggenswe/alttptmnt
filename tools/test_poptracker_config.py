"""Tests for tools/poptracker_config.py.

    .venv/Scripts/python.exe -m unittest discover -s tools -p "test_*.py"
"""
import json
import tempfile
import unittest
from pathlib import Path

import poptracker_config as pop

# What PopTracker left behind on 2026-10-31 after closing (shortened).
BROKEN = '{\n    "at_slot": "Turtles",\n    "check_for_updates": false,\n    "software_renderer": true\n}\n\n}\n'


class Settings(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.config = Path(self.folder.name) / "PopTracker" / "PopTracker.json"

    def tearDown(self):
        self.folder.cleanup()

    def test_stray_end_is_repaired_and_the_rest_kept(self):
        self.config.parent.mkdir()
        self.config.write_text(BROKEN)
        self.assertEqual(pop.ensure(self.config), "repaired PopTracker's settings file")
        settings = json.loads(self.config.read_text())
        self.assertEqual(settings["at_slot"], "Turtles")
        self.assertFalse(settings["check_for_updates"])
        self.assertFalse(settings["add_emo_packs"])
        self.assertTrue(settings["software_renderer"])

    def test_good_file_is_left_alone(self):
        self.config.parent.mkdir()
        good = json.dumps({**pop.STREAM_SETTINGS, "fps_limit": 120})
        self.config.write_text(good)
        self.assertEqual(pop.ensure(self.config), "PopTracker settings OK")
        self.assertEqual(self.config.read_text(), good)

    def test_missing_settings_are_added(self):
        self.config.parent.mkdir()
        self.config.write_text('{"fps_limit": 120, "check_for_updates": true}')
        self.assertEqual(pop.ensure(self.config), "set PopTracker's stream settings")
        settings = json.loads(self.config.read_text())
        self.assertEqual(settings["fps_limit"], 120)
        self.assertFalse(settings["check_for_updates"])

    def test_no_file_yet(self):
        pop.ensure(self.config)
        self.assertEqual(json.loads(self.config.read_text()), pop.STREAM_SETTINGS)

    def test_garbage(self):
        self.config.parent.mkdir()
        self.config.write_text("not json at all")
        self.assertEqual(pop.ensure(self.config), "repaired PopTracker's settings file")
        self.assertEqual(json.loads(self.config.read_text()), pop.STREAM_SETTINGS)


if __name__ == "__main__":
    unittest.main()
