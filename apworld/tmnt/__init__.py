from worlds.AutoWorld import World

from .items import AREA_PASSES, FILLER, GAME_NAME, TOOLS, TURTLES, TMNTItem, item_table
from .locations import location_table
from .regions import create_regions
from .rules import set_rules


class TMNTWorld(World):
    """Teenage Mutant Ninja Turtles (NES), where every Area is a dungeon behind a sewer pass."""

    game = GAME_NAME
    item_name_to_id = {name: item_id for name, (item_id, _) in item_table.items()}
    location_name_to_id = location_table

    start_turtle = "Raphael"
    start_area = 1

    def create_item(self, name: str) -> TMNTItem:
        item_id, classification = item_table[name]
        return TMNTItem(name, classification, item_id, self.player)

    def create_regions(self) -> None:
        create_regions(self)

    def create_items(self) -> None:
        start_pass = AREA_PASSES[self.start_area - 1]
        self.multiworld.push_precollected(self.create_item(self.start_turtle))
        self.multiworld.push_precollected(self.create_item(start_pass))

        pool = [self.create_item(name) for name in TURTLES + AREA_PASSES + TOOLS
                if name not in (self.start_turtle, start_pass)]
        open_slots = len(self.multiworld.get_unfilled_locations(self.player)) - len(pool)
        pool += [self.create_item(FILLER) for _ in range(open_slots)]
        self.multiworld.itempool += pool

    def set_rules(self) -> None:
        set_rules(self)

    def get_filler_item_name(self) -> str:
        return FILLER
