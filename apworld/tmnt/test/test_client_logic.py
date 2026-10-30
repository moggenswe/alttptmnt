import unittest

from .. import ram
from ..client_logic import (BossDebouncer, Inventory, area6_unlocked, full_sync_writes, incremental_writes,
                            inventory_from_items, needs_full_sync, pass_bitmask)


def inv(*names: str) -> Inventory:
    return inventory_from_items(list(names))


class TestInventory(unittest.TestCase):
    def test_inventory_from_items(self):
        result = inv("Raphael", "Sewer Pass: Area 1", "Sewer Pass: Area 3", "Rope Pack", "Whole Pizza")
        self.assertEqual(result, Inventory(turtles=frozenset({"Raphael"}), passes=frozenset({1, 3}),
                                           missiles=False, ropes=True, scuba=False))


class TestPassBitmask(unittest.TestCase):
    def test_pass_bitmask_hides_area2_without_scuba(self):
        self.assertEqual(pass_bitmask(inv("Sewer Pass: Area 1", "Sewer Pass: Area 2"), set()), 0b00001)

    def test_pass_bitmask_area2_with_scuba(self):
        self.assertEqual(pass_bitmask(inv("Sewer Pass: Area 2", "Zora's Scuba Kit"), set()), 0b00010)

    def test_pass_bitmask_area3_needs_both_packs(self):
        self.assertEqual(pass_bitmask(inv("Sewer Pass: Area 3", "Missile Pack"), set()), 0)
        self.assertEqual(pass_bitmask(inv("Sewer Pass: Area 3", "Missile Pack", "Rope Pack"), set()), 0b00100)

    def test_area6_bit_requires_four_turtles_three_clears(self):
        four = inv("Leonardo", "Michelangelo", "Donatello", "Raphael")
        three = inv("Leonardo", "Michelangelo", "Raphael")
        self.assertFalse(area6_unlocked(four, {1, 2}))
        self.assertFalse(area6_unlocked(three, {1, 2, 4}))
        self.assertTrue(area6_unlocked(four, {1, 2, 4}))
        self.assertEqual(pass_bitmask(four, {1, 2, 4}) & 0b100000, 0b100000)


class TestWrites(unittest.TestCase):
    def test_full_sync_captures_missing_turtles(self):
        writes = dict(full_sync_writes(inv("Raphael")))
        self.assertEqual(writes[ram.TURTLE_HP["Leonardo"]], [ram.CAPTURED_HP_VALUE])
        self.assertEqual(writes[ram.TURTLE_HP["Raphael"]], [ram.FULL_HP_VALUE])
        self.assertEqual(writes[ram.MISSILE_COUNT], [0])

    def test_full_sync_refills_packs(self):
        writes = dict(full_sync_writes(inv("Raphael", "Missile Pack", "Rope Pack")))
        self.assertEqual(writes[ram.MISSILE_COUNT], [ram.MISSILE_REFILL])
        self.assertEqual(writes[ram.ROPE_COUNT], [ram.ROPE_REFILL])

    def test_dead_turtle_not_revived_midarea(self):
        same = inv("Raphael", "Leonardo")
        ram_now = {ram.TURTLE_HP["Raphael"]: ram.CAPTURED_HP_VALUE}
        self.assertEqual(incremental_writes(same, same, ram_now), [])

    def test_incremental_item_midarea(self):
        old, new = inv("Raphael"), inv("Raphael", "Donatello")
        self.assertEqual(incremental_writes(old, new, {}), [(ram.TURTLE_HP["Donatello"], [ram.FULL_HP_VALUE])])

    def test_incremental_pack_keeps_higher_count(self):
        old, new = inv("Raphael"), inv("Raphael", "Missile Pack")
        ram_now = {ram.MISSILE_COUNT: ram.MISSILE_REFILL + 3}
        self.assertEqual(incremental_writes(old, new, ram_now), [(ram.MISSILE_COUNT, [ram.MISSILE_REFILL + 3])])

    def test_resync_after_reset(self):
        self.assertTrue(needs_full_sync(counter=5, ack=0))
        self.assertFalse(needs_full_sync(counter=5, ack=5))


class TestBossDebouncer(unittest.TestCase):
    def test_boss_flag_debounce(self):
        debouncer = BossDebouncer()
        self.assertEqual(debouncer.update({1: True}), set())
        self.assertEqual(debouncer.update({1: True}), {1})
        self.assertEqual(debouncer.update({1: True}), set())

    def test_flicker_does_not_count(self):
        debouncer = BossDebouncer()
        debouncer.update({2: True})
        debouncer.update({2: False})
        self.assertEqual(debouncer.update({2: True}), set())
