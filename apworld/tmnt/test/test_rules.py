from . import TMNTTestBase
from ..items import AREA_PASSES, TOOLS, TURTLES


class TestRules(TMNTTestBase):
    def reach_after_sweep(self, location: str) -> bool:
        self.multiworld.state.sweep_for_advancements()
        return self.can_reach_location(location)

    def test_area2_needs_scuba(self):
        self.assertAccessDependency(["Area 2 - Boss"], [["Zora's Scuba Kit"]], only_check_listed=True)

    def test_area3_needs_missiles_and_ropes(self):
        self.collect_by_name(["Sewer Pass: Area 3", "Missile Pack"])
        self.assertFalse(self.can_reach_location("Area 3 - Boss"))
        self.collect_by_name("Rope Pack")
        self.assertTrue(self.can_reach_location("Area 3 - Boss"))

    def test_area4_needs_ropes(self):
        self.collect_by_name("Sewer Pass: Area 4")
        self.assertFalse(self.can_reach_location("Area 4 - Boss"))
        self.collect_by_name("Rope Pack")
        self.assertTrue(self.can_reach_location("Area 4 - Boss"))

    def test_area5_boss_needs_donatello(self):
        self.assertAccessDependency(["Area 5 - Boss"], [["Donatello"]], only_check_listed=True)

    def test_area6_needs_four_turtles_and_three_clears(self):
        self.collect_by_name([*AREA_PASSES, *TOOLS, "Leonardo", "Michelangelo"])
        self.assertFalse(self.reach_after_sweep("Area 6 - Shredder"))
        self.collect_by_name("Donatello")
        self.assertTrue(self.reach_after_sweep("Area 6 - Shredder"))

    def test_area6_needs_three_clears_not_two(self):
        self.collect_by_name([*TURTLES, "Sewer Pass: Area 2", "Zora's Scuba Kit"])
        self.assertFalse(self.reach_after_sweep("Area 6 - Shredder"))
        self.collect_by_name(["Sewer Pass: Area 4", "Rope Pack"])
        self.assertTrue(self.reach_after_sweep("Area 6 - Shredder"))

    def test_beatable(self):
        self.collect_by_name([*TURTLES, *AREA_PASSES, *TOOLS])
        self.assertBeatable(True)
