from . import TMNTTestBase
from ..items import TURTLES, AREA_PASSES


class TestPool(TMNTTestBase):
    def test_pool_matches_locations(self):
        pool = [i for i in self.multiworld.itempool if i.player == 1]
        locs = [l for l in self.multiworld.get_locations(1) if l.address is not None]
        self.assertEqual(len(pool), len(locs))

    def test_ids_unique(self):
        from ..items import item_table
        from ..locations import location_table
        ids = [i for i, _ in item_table.values()] + list(location_table.values())
        self.assertEqual(len(ids), len(set(ids)))

    def test_start_turtle_and_pass_not_in_pool(self):
        names = [i.name for i in self.multiworld.itempool if i.player == 1]
        self.assertEqual(sum(n in TURTLES for n in names), 3)
        self.assertEqual(sum(n in AREA_PASSES for n in names), 4)
