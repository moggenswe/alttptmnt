from typing import TYPE_CHECKING

from BaseClasses import ItemClassification, Region

from .items import TMNTItem
from .locations import AREAS, BOSS_LOCATIONS, ENTRANCE_LOCATIONS, START_LOCATIONS, TMNTLocation, location_table

if TYPE_CHECKING:
    from . import TMNTWorld

FINAL_AREA = 6
SHREDDER_LOCATION = "Area 6 - Shredder"
SHREDDER_EVENT = "Shredder Defeated"


def cleared_location(area: int) -> str:
    return f"Area {area} - Cleared"


def cleared_event(area: int) -> str:
    return f"Area {area} Cleared"


def add_event(region: Region, location_name: str, item_name: str) -> None:
    location = TMNTLocation(region.player, location_name, None, region)
    location.place_locked_item(TMNTItem(item_name, ItemClassification.progression, None, region.player))
    region.locations.append(location)


def create_regions(world: "TMNTWorld") -> None:
    player, multiworld = world.player, world.multiworld
    menu = Region("Menu", player, multiworld)
    menu.locations += [TMNTLocation(player, name, location_table[name], menu) for name in START_LOCATIONS]
    multiworld.regions.append(menu)

    for area in AREAS:
        region = Region(f"Area {area}", player, multiworld)
        for name in (ENTRANCE_LOCATIONS[area], BOSS_LOCATIONS[area]):
            region.locations.append(TMNTLocation(player, name, location_table[name], region))
        add_event(region, cleared_location(area), cleared_event(area))
        multiworld.regions.append(region)
        menu.connect(region)

    final = Region(f"Area {FINAL_AREA}", player, multiworld)
    add_event(final, SHREDDER_LOCATION, SHREDDER_EVENT)
    multiworld.regions.append(final)
    menu.connect(final)
