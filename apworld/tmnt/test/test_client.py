"""Control-flow tests for TMNTClient.game_watcher with a fake BizHawk RAM and a fake client context."""
import asyncio
import unittest
from types import SimpleNamespace
from unittest import mock

from worlds._bizhawk.context import AuthStatus
from NetUtils import ClientStatus
from worlds._bizhawk import RequestFailedError

from .. import client as client_module, ram
from ..client import TMNTClient
from ..items import item_table
from ..locations import ENTRANCE_LOCATIONS, location_table

NAME_BY_ID = {item_id: name for name, (item_id, _) in item_table.items()}


class FakeRam:
    def __init__(self) -> None:
        self.bytes: dict[int, int] = {}
        self.fail_reads = False
        self.fail_writes = False

    async def read(self, _ctx, read_list):
        if self.fail_reads:
            raise RequestFailedError("connector gone")
        return [bytes([self.bytes.get(address, 0)]) for address, _, _ in read_list]

    async def write(self, _ctx, write_list):
        if self.fail_writes:
            raise RequestFailedError("connector gone")
        for address, data, _ in write_list:
            self.bytes[address] = data[0]


class ClientTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.ram = FakeRam()
        self.now = 0.0
        self.sent: list[dict] = []
        patches = [mock.patch.object(client_module, "read", self.ram.read),
                   mock.patch.object(client_module, "write", self.ram.write),
                   mock.patch.object(client_module, "monotonic", lambda: self.now)]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

        async def send_msgs(msgs):
            self.sent.extend(msgs)

        self.ctx = SimpleNamespace(
            server=object(), slot_data={}, auth_status=AuthStatus.AUTHENTICATED, bizhawk_ctx=None,
            items_received=[], checked_locations=set(), finished_game=False, send_msgs=send_msgs,
            item_names=SimpleNamespace(lookup_in_game=lambda item_id, _game=None: NAME_BY_ID[item_id]))
        self.client = TMNTClient()

    def give(self, *names: str) -> None:
        self.ctx.items_received = [SimpleNamespace(item=item_table[name][0]) for name in names]

    def tick(self, seconds: float = 0.5) -> None:
        self.now += seconds
        asyncio.run(self.client.game_watcher(self.ctx))

    def sent_locations(self) -> set[int]:
        return {loc for msg in self.sent if msg["cmd"] == "LocationChecks" for loc in msg["locations"]}

    def hp(self, turtle: str) -> int:
        return self.ram.bytes[ram.TURTLE_HP[turtle]]


class TestResync(ClientTestCase):
    def test_power_cycle_forces_full_sync(self):
        self.give("Raphael", "Sewer Pass: Area 1")
        self.tick()
        self.ram.bytes = {address: ram.FULL_HP_VALUE for address in ram.TURTLE_HP.values()}  # fresh boot
        self.tick()
        self.assertEqual(self.hp("Leonardo"), ram.CAPTURED_HP_VALUE)

    def test_savestate_restore_forces_full_sync(self):
        self.give("Raphael", "Sewer Pass: Area 1")
        self.ram.bytes[ram.MAILBOX_LOAD_COUNTER] = 3
        self.tick()
        snapshot = dict(self.ram.bytes)
        self.ram.bytes[ram.MAILBOX_LOAD_COUNTER] = 4
        self.tick()
        self.ram.bytes = snapshot | {ram.TURTLE_HP["Leonardo"]: ram.FULL_HP_VALUE,
                                     ram.MAILBOX_LOAD_COUNTER: 2, ram.MAILBOX_ACK: 2}  # older manual state
        self.tick()
        self.assertEqual(self.hp("Leonardo"), ram.CAPTURED_HP_VALUE)


class TestRobustness(ClientTestCase):
    def test_request_failure_does_not_raise(self):
        self.give("Raphael", "Sewer Pass: Area 1")
        self.ram.fail_reads = True
        self.tick()  # must not raise, or the BizHawk watcher task dies for good

    def test_write_failure_keeps_item_pending(self):
        self.give("Raphael", "Sewer Pass: Area 1")
        self.tick()
        self.give("Raphael", "Sewer Pass: Area 1", "Donatello")
        self.ram.fail_writes = True
        self.tick()
        self.ram.fail_writes = False
        self.tick()
        self.assertEqual(self.hp("Donatello"), ram.FULL_HP_VALUE)

    def test_reconnect_does_not_revive_dead_turtle(self):
        self.give("Raphael", "Leonardo", "Sewer Pass: Area 1")
        self.tick()
        self.ram.bytes[ram.TURTLE_HP["Leonardo"]] = ram.CAPTURED_HP_VALUE  # died in-game
        self.ctx.items_received = []  # CommonClient clears this on disconnect
        self.tick()
        self.give("Raphael", "Leonardo", "Sewer Pass: Area 1")
        self.tick()
        self.assertEqual(self.hp("Leonardo"), ram.CAPTURED_HP_VALUE)


class TestGoal(ClientTestCase):
    ALL = ("Leonardo", "Michelangelo", "Donatello", "Raphael")

    def goal_sent(self) -> bool:
        return any(msg["cmd"] == "StatusUpdate" and msg["status"] == ClientStatus.CLIENT_GOAL for msg in self.sent)

    def set_shredder(self, on: bool) -> None:
        address, value = ram.SHREDDER_DEFEATED
        self.ram.bytes[address] = value if on else 0

    def test_goal_flicker_not_sent(self):
        self.give(*self.ALL)
        self.ctx.checked_locations = {location_table[f"Area {n} - Boss"] for n in (1, 2, 4)}
        self.set_shredder(True)
        self.tick()
        self.set_shredder(False)
        self.tick()
        self.assertFalse(self.goal_sent())

    def test_goal_needs_area6_unlocked(self):
        self.give("Raphael")
        self.set_shredder(True)
        self.tick()
        self.tick()
        self.assertFalse(self.goal_sent())

    def test_goal_sent_when_sustained_and_unlocked(self):
        self.give(*self.ALL)
        self.ctx.checked_locations = {location_table[f"Area {n} - Boss"] for n in (1, 2, 4)}
        self.set_shredder(True)
        self.tick()
        self.tick()
        self.assertTrue(self.goal_sent())


class TestEntrances(ClientTestCase):
    def test_entrance_needs_pass(self):
        self.give("Raphael", "Sewer Pass: Area 1")
        self.ram.bytes[ram.CURRENT_AREA] = 4
        self.tick()
        self.tick()
        self.assertNotIn(location_table[ENTRANCE_LOCATIONS[4]], self.sent_locations())

    def test_entrance_flicker_not_sent(self):
        self.give("Raphael", "Sewer Pass: Area 1")
        self.ram.bytes[ram.CURRENT_AREA] = 1
        self.tick()
        self.ram.bytes[ram.CURRENT_AREA] = 0
        self.tick()
        self.assertNotIn(location_table[ENTRANCE_LOCATIONS[1]], self.sent_locations())

    def test_entrance_sent_when_sustained(self):
        self.give("Raphael", "Sewer Pass: Area 1")
        self.ram.bytes[ram.CURRENT_AREA] = 1
        self.tick()
        self.tick()
        self.assertIn(location_table[ENTRANCE_LOCATIONS[1]], self.sent_locations())
