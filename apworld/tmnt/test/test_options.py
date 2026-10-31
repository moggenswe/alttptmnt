from . import TMNTTestBase
from ..items import AREA_PASSES, TOOLS, TURTLES


def precollected_names(test: TMNTTestBase) -> list[str]:
    return [item.name for item in test.multiworld.precollected_items[1]]


def pool_names(test: TMNTTestBase) -> list[str]:
    return [item.name for item in test.multiworld.itempool if item.player == 1]


class TestStartDonatello(TMNTTestBase):
    options = {"start_turtle": "donatello"}

    def test_start_turtle_precollected(self):
        self.assertIn("Donatello", precollected_names(self))
        self.assertNotIn("Donatello", pool_names(self))


class TestRandomStartTurtle(TMNTTestBase):
    options = {"start_turtle": "random"}

    def test_random_start_turtle_is_one_of_four(self):
        starts = [name for name in precollected_names(self) if name in TURTLES]
        self.assertEqual(len(starts), 1)
        self.assertNotIn(starts[0], pool_names(self))


class TestStartArea3(TMNTTestBase):
    options = {"start_area": "area_3"}

    def test_start_area_3_pass_precollected(self):
        self.assertIn("Sewer Pass: Area 3", precollected_names(self))
        self.assertIn("Sewer Pass: Area 1", pool_names(self))

    def test_start_area_3_is_playable_from_start(self):
        self.assertIn("Missile Pack", precollected_names(self))
        self.assertIn("Rope Pack", precollected_names(self))
        self.assertTrue(self.can_reach_location("Area 3 - Sewer Entrance"))

    def test_start_area_3_is_still_beatable(self):
        self.collect_by_name([*TURTLES, *AREA_PASSES, *TOOLS])
        self.assertBeatable(True)


class TestStartArea4(TMNTTestBase):
    options = {"start_area": "area_4"}

    def test_start_area_4_comes_with_ropes(self):
        self.assertIn("Rope Pack", precollected_names(self))
        self.assertNotIn("Missile Pack", precollected_names(self))
        self.assertTrue(self.can_reach_location("Area 4 - Sewer Entrance"))


class TestSlotData(TMNTTestBase):
    options = {"start_turtle": "leonardo", "start_area": "area_2"}

    def test_slot_data(self):
        self.assertEqual(self.world.fill_slot_data(),
                         {"start_turtle": "Leonardo", "start_area": 2, "include_pickups": False})


class TestUniversalTracker(TMNTTestBase):
    """Universal Tracker regenerates the world from slot_data, so a random start must come back the same."""
    options = {"start_turtle": "raphael", "start_area": "area_1"}

    def test_regen_takes_choices_from_slot_data(self):
        self.multiworld.re_gen_passthrough = {self.world.game: {"start_turtle": "Donatello", "start_area": 4,
                                                                "include_pickups": False}}
        self.world.generate_early()
        self.assertEqual((self.world.start_turtle, self.world.start_area), ("Donatello", 4))

    def test_interpret_slot_data_hands_it_back(self):
        slot_data = self.world.fill_slot_data()
        self.assertEqual(type(self.world).interpret_slot_data(slot_data), slot_data)
