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


class TestSlotData(TMNTTestBase):
    options = {"start_turtle": "leonardo", "start_area": "area_2"}

    def test_slot_data(self):
        self.assertEqual(self.world.fill_slot_data(),
                         {"start_turtle": "Leonardo", "start_area": 2, "include_pickups": False})
