"""Tests for tools/bizhawk_saves.py.

    .venv/Scripts/python.exe -m unittest discover -s tools -p "test_*.py"
"""
import os
import tempfile
import time
import unittest
from pathlib import Path

import bizhawk_saves as saves

CONFIG = '{\n  "BackupSaveram": true,\n  "AutosaveSaveRAM": false,\n  "FlushSaveRamFrames": 0,\n  "Other": 1\n}\n'


class Autosave(unittest.TestCase):
    def test_turns_it_on_and_keeps_the_rest(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "config.ini"
            config.write_text(CONFIG)
            self.assertIn("turned on", saves.ensure_autosave(config))
            text = config.read_text()
            self.assertIn('"AutosaveSaveRAM": true', text)
            self.assertIn(f'"FlushSaveRamFrames": {saves.FLUSH_FRAMES}', text)
            self.assertIn('"Other": 1', text)
            self.assertIn("every minute", saves.ensure_autosave(config))

    def test_no_config_yet(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertIn("no ", saves.ensure_autosave(Path(folder) / "config.ini"))

    def test_autosave_on(self):
        self.assertFalse(saves.autosave_on(CONFIG))
        self.assertTrue(saves.autosave_on(saves.with_autosave(CONFIG)))
        self.assertFalse(saves.autosave_on('"AutosaveSaveRAM": true, "FlushSaveRamFrames": 99999'))


class AlttpSave(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.dir = Path(self.folder.name) / "SNES" / "SaveRAM"
        self.dir.mkdir(parents=True)

    def tearDown(self):
        self.folder.cleanup()

    def file(self, name, content, age=0.0):
        path = self.dir / name
        path.write_bytes(content)
        stamp = time.time() - age
        os.utime(path, (stamp, stamp))
        return path

    def read(self, name):
        return (self.dir / name).read_bytes()

    def test_first_session_of_a_seed(self):
        self.assertEqual(saves.prepare_alttp_save(self.dir, "AP_1"), [])
        self.assertEqual((self.dir / "alttp-stream.seed").read_text(), "AP_1")
        self.assertFalse((self.dir / "alttp-stream.SaveRAM").exists())

    def test_same_seed_again_keeps_the_save(self):
        saves.prepare_alttp_save(self.dir, "AP_1")
        self.file("alttp-stream.SaveRAM", b"progress")
        self.assertEqual(saves.prepare_alttp_save(self.dir, "AP_1"), [])
        self.assertEqual(self.read("alttp-stream.SaveRAM"), b"progress")

    def test_new_seed_parks_the_old_save_and_back_again(self):
        saves.prepare_alttp_save(self.dir, "AP_1")
        self.file("alttp-stream.SaveRAM", b"seed one")
        saves.prepare_alttp_save(self.dir, "AP_2")
        self.assertFalse((self.dir / "alttp-stream.SaveRAM").exists())
        self.assertEqual(self.read("alttp-stream.AP_1.SaveRAM"), b"seed one")
        self.file("alttp-stream.SaveRAM", b"seed two")
        done = saves.prepare_alttp_save(self.dir, "AP_1")
        self.assertEqual(self.read("alttp-stream.SaveRAM"), b"seed one")
        self.assertEqual(self.read("alttp-stream.AP_2.SaveRAM"), b"seed two")
        self.assertTrue(any("put back" in line for line in done))

    def test_save_from_before_the_marker_is_kept(self):
        self.file("alttp-stream.SaveRAM", b"old")
        saves.prepare_alttp_save(self.dir, "AP_1", now=0)
        self.assertEqual(self.read("alttp-stream.unknown-" + time.strftime("%Y%m%d-%H%M%S", time.localtime(0))
                                   + ".SaveRAM"), b"old")

    def test_crash_recovers_the_newer_autosave(self):
        saves.prepare_alttp_save(self.dir, "AP_1")
        self.file("alttp-stream.SaveRAM", b"at last clean exit", age=600)
        self.file("alttp-stream.AutoSaveRAM.SaveRAM", b"one minute before the crash")
        self.file("alttp-stream.AutoSaveRAM.SaveRAM.bak", b"older autosave")
        done = saves.prepare_alttp_save(self.dir, "AP_1")
        self.assertEqual(self.read("alttp-stream.SaveRAM"), b"one minute before the crash")
        self.assertEqual(self.read("alttp-stream.SaveRAM.before-recovery"), b"at last clean exit")
        self.assertFalse((self.dir / "alttp-stream.AutoSaveRAM.SaveRAM").exists())
        self.assertFalse((self.dir / "alttp-stream.AutoSaveRAM.SaveRAM.bak").exists())
        self.assertTrue(any("using BizHawk's autosave" in line for line in done))

    def test_crash_before_any_clean_exit(self):
        saves.prepare_alttp_save(self.dir, "AP_1")
        self.file("alttp-stream.AutoSaveRAM.SaveRAM", b"autosave only")
        saves.prepare_alttp_save(self.dir, "AP_1")
        self.assertEqual(self.read("alttp-stream.SaveRAM"), b"autosave only")

    def test_clean_exit_after_autosave_wins(self):
        saves.prepare_alttp_save(self.dir, "AP_1")
        self.file("alttp-stream.AutoSaveRAM.SaveRAM", b"autosave", age=30)
        self.file("alttp-stream.SaveRAM", b"clean exit")
        self.assertEqual(saves.prepare_alttp_save(self.dir, "AP_1"), [])
        self.assertEqual(self.read("alttp-stream.SaveRAM"), b"clean exit")

    def test_crash_then_new_seed_parks_the_recovered_save(self):
        saves.prepare_alttp_save(self.dir, "AP_1")
        self.file("alttp-stream.SaveRAM", b"old", age=600)
        self.file("alttp-stream.AutoSaveRAM.SaveRAM", b"newest of seed one")
        saves.prepare_alttp_save(self.dir, "AP_2")
        self.assertEqual(self.read("alttp-stream.AP_1.SaveRAM"), b"newest of seed one")


if __name__ == "__main__":
    unittest.main()
