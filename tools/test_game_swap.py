"""Tests for tools/game_swap.py that need neither BizHawk nor OBS (a stand-in obs-websocket server is used).

    .venv/Scripts/python.exe -m unittest discover -s tools -p "test_*.py"
"""
import base64
import hashlib
import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from websockets.sync.server import serve

import game_swap


class Pure(unittest.TestCase):
    def test_system_of_title(self):
        self.assertEqual(game_swap.system_of_title("tmnt-stream [NES] - BizHawk"), "NES")
        self.assertEqual(game_swap.system_of_title("alttp-stream [SNES] - BizHawk"), "SNES")
        self.assertIsNone(game_swap.system_of_title("BizHawk"))
        self.assertIsNone(game_swap.system_of_title("Lua Console"))
        self.assertIsNone(game_swap.system_of_title("notes [NES].txt - Notepad"))

    def test_other(self):
        self.assertEqual(game_swap.other("NES"), "SNES")
        self.assertEqual(game_swap.other("SNES"), "NES")

    def test_parse_hotkey(self):
        self.assertEqual(game_swap.parse_hotkey("ctrl+shift+space"), (0x2 | 0x4, 0x20))
        self.assertEqual(game_swap.parse_hotkey("Alt+F9"), (0x1, 0x78))
        self.assertEqual(game_swap.parse_hotkey("ctrl+s"), (0x2, ord("S")))
        self.assertEqual(game_swap.parse_hotkey("pause"), (0, 0x13))
        for bad in ("", "ctrl+", "hyper+a", "ctrl+f25", "ctrl+ä"):
            with self.assertRaises(ValueError, msg=bad):
                game_swap.parse_hotkey(bad)

    def test_obs_auth(self):
        # Worked by hand from the obs-websocket 5 protocol description.
        secret = base64.b64encode(hashlib.sha256(b"pw" + b"salt").digest())
        expected = base64.b64encode(hashlib.sha256(secret + b"challenge").digest()).decode()
        self.assertEqual(game_swap.obs_auth("pw", "salt", "challenge"), expected)


class RequestFiles(unittest.TestCase):
    def test_old_requests_are_ignored_and_new_ones_answered(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / "NES-request.txt").write_text("100-1")  # from before the helper started
            requests = game_swap.Requests(folder)
            self.assertEqual(requests.poll(), [])
            (folder / "NES-request.txt").write_text("100-2")
            self.assertEqual(requests.poll(), ["NES"])
            self.assertEqual((folder / "NES-ack.txt").read_text(), "100-2")
            self.assertEqual(requests.poll(), [])
            (folder / "SNES-request.txt").write_text("200-1")
            self.assertEqual(requests.poll(), ["SNES"])

    def test_scripts_that_start_and_stop_are_reported_once(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            requests = game_swap.Requests(folder)
            self.assertEqual(requests.changes_in_scripts(), [])
            (folder / "NES-ready.txt").write_text("100")
            now = (folder / "NES-ready.txt").stat().st_mtime
            self.assertEqual(requests.changes_in_scripts(now + 1), [("NES", True)])
            self.assertEqual(requests.changes_in_scripts(now + 5), [])
            self.assertEqual(requests.changes_in_scripts(now + 20), [("NES", False)])

    def test_missing_folder_is_made(self):
        with tempfile.TemporaryDirectory() as folder:
            game_swap.Requests(Path(folder) / "output" / "swap")
            self.assertTrue((Path(folder) / "output" / "swap").is_dir())


class FakeObs:
    """Enough of obs-websocket 5 for game_swap.Obs: hello with a password challenge, identify, two requests."""

    def __init__(self, password="secret", scene="Hyrule"):
        self.password, self.scene, self.calls = password, scene, []
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            self.port = probe.getsockname()[1]
        self.server = serve(self.handle, "127.0.0.1", self.port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def handle(self, ws):
        ws.send(json.dumps({"op": 0, "d": {"rpcVersion": 1,
                                           "authentication": {"salt": "s4lt", "challenge": "ch4llenge"}}}))
        identify = json.loads(ws.recv())
        if identify["d"].get("authentication") != game_swap.obs_auth(self.password, "s4lt", "ch4llenge"):
            ws.close(4009, "Authentication failed.")
            return
        ws.send(json.dumps({"op": 2, "d": {"negotiatedRpcVersion": 1}}))
        for raw in ws:
            d = json.loads(raw)["d"]
            self.calls.append((d["requestType"], d["requestData"]))
            data, ok = {}, True
            if d["requestType"] == "GetCurrentProgramScene":
                data = {"sceneName": self.scene, "currentProgramSceneName": self.scene}
            elif d["requestType"] == "SetCurrentProgramScene":
                self.scene = d["requestData"]["sceneName"]
            else:
                ok = False
            ws.send(json.dumps({"op": 7, "d": {"requestType": d["requestType"], "requestId": d["requestId"],
                                               "requestStatus": {"result": ok, "code": 100 if ok else 204},
                                               "responseData": data}}))

    def close(self):
        self.server.shutdown()


class ObsClient(unittest.TestCase):
    GAME_SCENES = {"Hyrule", "New York"}

    def setUp(self):
        self.fake = FakeObs()
        self.lines = []

    def tearDown(self):
        self.fake.close()

    def client(self, password="secret"):
        return game_swap.Obs(f"ws://127.0.0.1:{self.fake.port}", password, self.lines.append)

    def test_switches_between_game_scenes(self):
        obs = self.client()
        obs.show("New York", self.GAME_SCENES)
        self.assertEqual(self.fake.scene, "New York")
        obs.show("New York", self.GAME_SCENES)  # already there: no second switch
        self.assertEqual([c[0] for c in self.fake.calls].count("SetCurrentProgramScene"), 1)
        obs.show("Hyrule", self.GAME_SCENES)
        self.assertEqual(self.fake.scene, "Hyrule")
        obs.close()

    def test_leaves_a_host_scene_alone(self):
        self.fake.scene = "Interview"
        obs = self.client()
        obs.show("New York", self.GAME_SCENES)
        self.assertEqual(self.fake.scene, "Interview")
        self.assertTrue(any("left as it is" in line for line in self.lines))
        obs.close()

    def test_wrong_password_is_reported_once_and_does_not_raise(self):
        obs = self.client(password="wrong")
        obs.show("New York", self.GAME_SCENES)
        obs.next_try = 0
        obs.show("New York", self.GAME_SCENES)
        self.assertEqual(self.fake.scene, "Hyrule")
        self.assertEqual(len([line for line in self.lines if "OBS not reachable" in line]), 1)

    def test_obs_closed(self):
        obs = game_swap.Obs("ws://127.0.0.1:1", "x", self.lines.append)
        self.assertIsNone(obs.request("GetCurrentProgramScene"))
        self.assertIsNone(obs.request("GetCurrentProgramScene"))  # waits RETRY_SECONDS before trying again
        self.assertEqual(len(self.lines), 1)


if __name__ == "__main__":
    unittest.main()
