from typing import TYPE_CHECKING

from BaseClasses import Region

from .locations import TMNTLocation, location_table

if TYPE_CHECKING:
    from . import TMNTWorld


def create_regions(world: "TMNTWorld") -> None:
    menu = Region("Menu", world.player, world.multiworld)
    menu.locations += [TMNTLocation(world.player, name, address, menu)
                       for name, address in location_table.items()]
    world.multiworld.regions.append(menu)
