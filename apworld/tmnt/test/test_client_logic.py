import unittest

from .. import ram
from ..client_logic import (Inventory, SignalDebouncer, area6_unlocked, beaten_from_mailbox, boss_defeated,
                            capture_writes, full_sync_writes,
                            incremental_writes,
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

    def test_pass_bitmask_area4_needs_ropes(self):
        self.assertEqual(pass_bitmask(inv("Sewer Pass: Area 4"), set()), 0)
        self.assertEqual(pass_bitmask(inv("Sewer Pass: Area 4", "Rope Pack"), set()), 0b01000)

    def test_area6_bit_requires_four_turtles_three_clears(self):
        four = inv("Leonardo", "Michelangelo", "Donatello", "Raphael")
        three = inv("Leonardo", "Michelangelo", "Raphael")
        self.assertFalse(area6_unlocked(four, {1, 2}))
        self.assertFalse(area6_unlocked(three, {1, 2, 4}))
        self.assertTrue(area6_unlocked(four, {1, 2, 4}))
        self.assertEqual(pass_bitmask(four, {1, 2, 4}) & 0b100000, 0b100000)


class TestWrites(unittest.TestCase):
    def test_full_sync_captures_missing_turtles(self):
        writes = dict(full_sync_writes(inv("Raphael"), active="Raphael"))
        self.assertEqual(writes[ram.TURTLE_HP["Leonardo"]], [ram.CAPTURED_HP_VALUE])
        self.assertEqual(writes[ram.TURTLE_HP["Raphael"]], [ram.FULL_HP_VALUE])
        self.assertEqual(writes[ram.MISSILE_COUNT], [0])

    def test_full_sync_switches_away_from_an_unowned_active_turtle(self):
        # The area savestates all start with Leo active. The switch must come first: the client writes
        # the list in one go, and $0067 + HP in the same frame is safe (lua/tmnt_turtle_swap_test.lua).
        writes = full_sync_writes(inv("Raphael", "Donatello"), active="Leonardo")
        self.assertEqual(writes[0], (ram.ACTIVE_TURTLE, [ram.TURTLE_BY_ID.index("Raphael")]))
        self.assertEqual(dict(writes)[ram.TURTLE_HP["Leonardo"]], [ram.CAPTURED_HP_VALUE])

    def test_full_sync_keeps_an_owned_active_turtle(self):
        writes = dict(full_sync_writes(inv("Raphael", "Leonardo"), active="Leonardo"))
        self.assertNotIn(ram.ACTIVE_TURTLE, writes)
        self.assertEqual(writes[ram.TURTLE_HP["Leonardo"]], [ram.FULL_HP_VALUE])

    def test_full_sync_without_turtles_leaves_the_active_one(self):
        writes = dict(full_sync_writes(inv(), active="Leonardo"))
        self.assertNotIn(ram.ACTIVE_TURTLE, writes)
        self.assertNotIn(ram.TURTLE_HP["Leonardo"], writes)
        self.assertEqual(writes[ram.TURTLE_HP["Michelangelo"]], [ram.CAPTURED_HP_VALUE])

    def test_full_sync_refills_packs(self):
        writes = dict(full_sync_writes(inv("Raphael", "Missile Pack", "Rope Pack"), active="Raphael"))
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
        self.assertEqual(incremental_writes(old, new, ram_now), [])

    def test_full_sync_keeps_higher_count(self):
        ram_now = {ram.MISSILE_COUNT: ram.MISSILE_REFILL + 3}
        writes = dict(full_sync_writes(inv("Raphael", "Missile Pack"), active="Raphael", ram_now=ram_now))
        self.assertNotIn(ram.MISSILE_COUNT, writes)

    def test_owned_pack_refills_at_zero(self):
        same = inv("Raphael", "Rope Pack")
        self.assertEqual(incremental_writes(same, same, {ram.ROPE_COUNT: 0}), [(ram.ROPE_COUNT, [ram.ROPE_REFILL])])
        self.assertEqual(incremental_writes(same, same, {ram.ROPE_COUNT: 1}), [])



class TestSignalDebouncer(unittest.TestCase):
    def test_boss_flag_debounce(self):
        debouncer = SignalDebouncer()
        self.assertEqual(debouncer.update({1: True}, now=0.0), set())
        self.assertEqual(debouncer.update({1: True}, now=0.5), {1})
        self.assertEqual(debouncer.update({1: True}, now=1.0), set())

    def test_flicker_does_not_count(self):
        debouncer = SignalDebouncer()
        debouncer.update({2: True}, now=0.0)
        debouncer.update({2: False}, now=0.5)
        self.assertEqual(debouncer.update({2: True}, now=1.0), set())

    def test_two_quick_reads_do_not_count(self):
        debouncer = SignalDebouncer()
        debouncer.update({3: True}, now=0.0)
        self.assertEqual(debouncer.update({3: True}, now=0.01), set())
        self.assertEqual(debouncer.update({3: True}, now=0.3), {3})


class TestNeedsFullSync(unittest.TestCase):
    def test_steady_state(self):
        self.assertFalse(needs_full_sync(counter=5, ack=5, magic_ok=True, expected_ack=5))

    def test_new_area_load(self):
        self.assertTrue(needs_full_sync(counter=6, ack=5, magic_ok=True, expected_ack=5))

    def test_power_cycle(self):
        self.assertTrue(needs_full_sync(counter=0, ack=0, magic_ok=False, expected_ack=5))

    def test_restored_older_state(self):
        self.assertTrue(needs_full_sync(counter=2, ack=2, magic_ok=True, expected_ack=5))

    def test_first_tick(self):
        self.assertTrue(needs_full_sync(counter=0, ack=0, magic_ok=True, expected_ack=None))


class TestBossDefeated(unittest.TestCase):
    """A boss win shows up as the area byte ($0048, 0-based) going N-1 -> N without a savestate load."""

    def test_area_byte_increment_is_a_boss_win(self):
        self.assertEqual(boss_defeated(prev_area=0, area=1, prev_counter=3, counter=3), 1)
        self.assertEqual(boss_defeated(prev_area=4, area=5, prev_counter=3, counter=3), 5)

    def test_savestate_load_is_not_a_boss_win(self):
        self.assertIsNone(boss_defeated(prev_area=0, area=1, prev_counter=3, counter=4))

    def test_nothing_loaded_yet(self):
        self.assertIsNone(boss_defeated(prev_area=0, area=1, prev_counter=0, counter=0))

    def test_first_tick(self):
        self.assertIsNone(boss_defeated(prev_area=None, area=1, prev_counter=None, counter=3))

    def test_jumps_and_steady_state(self):
        self.assertIsNone(boss_defeated(prev_area=0, area=2, prev_counter=3, counter=3))
        self.assertIsNone(boss_defeated(prev_area=2, area=2, prev_counter=3, counter=3))
        self.assertIsNone(boss_defeated(prev_area=5, area=6, prev_counter=3, counter=3))  # no Area 6 boss location


class TestCaptureWrites(unittest.TestCase):
    """The game frees unowned turtles at a continue, a new game and its own rescue; the client recaptures."""

    def hp(self, **values: int) -> dict[int, int]:
        return {ram.TURTLE_HP[name]: value for name, value in values.items()}

    def test_freed_unowned_turtle_is_captured(self):
        ram_now = self.hp(Raphael=0x80, Leonardo=0x80)
        self.assertEqual(capture_writes(inv("Raphael"), "Raphael", ram_now),
                         [(ram.TURTLE_HP["Leonardo"], [ram.CAPTURED_HP_VALUE])])

    def test_captured_ones_are_left_alone(self):
        self.assertEqual(capture_writes(inv("Raphael"), "Raphael", self.hp(Raphael=0x80)), [])

    def test_freed_turtle_on_screen_is_switched_out_first(self):
        ram_now = self.hp(Raphael=0x80, Leonardo=0x60)
        writes = capture_writes(inv("Raphael"), "Leonardo", ram_now)
        self.assertEqual(writes, [(ram.ACTIVE_TURTLE, [ram.TURTLE_BY_ID.index("Raphael")]),
                                  (ram.TURTLE_HP["Leonardo"], [ram.CAPTURED_HP_VALUE])])

    def test_no_switch_to_a_captured_owned_turtle(self):
        # Raph (owned) was caught by the game; Leo (unowned, rescued) is the only one left on screen.
        ram_now = self.hp(Raphael=0, Leonardo=0x60)
        self.assertEqual(capture_writes(inv("Raphael"), "Leonardo", ram_now), [])


class TestBeatenMailbox(unittest.TestCase):
    def test_bits_to_areas(self):
        self.assertEqual(beaten_from_mailbox(0b100101), {1, 3})  # bit 5 is Shredder, not an area
