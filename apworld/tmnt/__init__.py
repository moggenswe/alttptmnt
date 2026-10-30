from typing import Any

from worlds.AutoWorld import World

from .items import AREA_PASSES, FILLER, GAME_NAME, TOOLS, TURTLES, TMNTItem, item_table
from .locations import location_table
from .options import TMNTOptions
from .regions import create_regions
from .rules import AREA_TOOL_REQUIREMENTS, set_rules


class TMNTWorld(World):
    """Teenage Mutant Ninja Turtles (NES), where every Area is a dungeon behind a sewer pass."""

    game = GAME_NAME
    item_name_to_id = {name: item_id for name, (item_id, _) in item_table.items()}
    location_name_to_id = location_table

    options_dataclass = TMNTOptions
    options: TMNTOptions

    start_turtle: str
    start_area: int

    def generate_early(self) -> None:
        self.start_turtle = self.options.start_turtle.current_key.capitalize()
        self.start_area = self.options.start_area.value

    def create_item(self, name: str) -> TMNTItem:
        item_id, classification = item_table[name]
        return TMNTItem(name, classification, item_id, self.player)

    def create_regions(self) -> None:
        create_regions(self)

    def create_items(self) -> None:
        # The start area must be playable right away, so its tools come with its pass.
        start_items = (self.start_turtle, AREA_PASSES[self.start_area - 1],
                       *AREA_TOOL_REQUIREMENTS.get(self.start_area, ()))
        for name in start_items:
            self.multiworld.push_precollected(self.create_item(name))

        pool = [self.create_item(name) for name in TURTLES + AREA_PASSES + TOOLS
                if name not in start_items]
        open_slots = len(self.multiworld.get_unfilled_locations(self.player)) - len(pool)
        pool += [self.create_item(FILLER) for _ in range(open_slots)]
        self.multiworld.itempool += pool

    def set_rules(self) -> None:
        set_rules(self)

    def get_filler_item_name(self) -> str:
        return FILLER

    def fill_slot_data(self) -> dict[str, Any]:
        return {"start_turtle": self.start_turtle,
                "start_area": self.start_area,
                "include_pickups": bool(self.options.include_pickups)}
