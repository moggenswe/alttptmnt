from typing import TYPE_CHECKING

from worlds.generic.Rules import add_rule, set_rule

from .items import AREA_PASSES, TURTLES
from .locations import AREAS, BOSS_LOCATIONS
from .regions import FINAL_AREA, SHREDDER_EVENT, cleared_event, cleared_location

if TYPE_CHECKING:
    from . import TMNTWorld

AREA_TOOL_REQUIREMENTS: dict[int, tuple[str, ...]] = {
    2: ("Zora's Scuba Kit",),
    3: ("Missile Pack", "Rope Pack"),
    # Area 4's rooftop crossing needs ropes and the area has one vanilla rope pickup (3 ropes); ropeless is
    # a damage boost no charity runner should need (docs/research/tmnt-ammo-och-tracker.md).
    4: ("Rope Pack",),
}
BOSS_TURTLE_REQUIREMENTS: dict[int, str] = {5: "Donatello"}  # Don's bo reach (spec 3.1)
CLEARS_FOR_TECHNODROME = 3


def set_rules(world: "TMNTWorld") -> None:
    player, multiworld = world.player, world.multiworld

    for area in AREAS:
        needed = (AREA_PASSES[area - 1], *AREA_TOOL_REQUIREMENTS.get(area, ()))
        set_rule(multiworld.get_entrance(f"Menu -> Area {area}", player),
                 lambda state, needed=needed: state.has_all(needed, player))
        turtle = BOSS_TURTLE_REQUIREMENTS.get(area)
        if turtle:
            for name in (BOSS_LOCATIONS[area], cleared_location(area)):
                add_rule(multiworld.get_location(name, player),
                         lambda state, turtle=turtle: state.has(turtle, player))

    clears = [cleared_event(area) for area in AREAS]
    set_rule(multiworld.get_entrance(f"Menu -> Area {FINAL_AREA}", player),
             lambda state: state.has_all(TURTLES, player)
             and state.has_from_list(clears, player, CLEARS_FOR_TECHNODROME))

    multiworld.completion_condition[player] = lambda state: state.has(SHREDDER_EVENT, player)
