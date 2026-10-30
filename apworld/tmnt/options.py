from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Toggle


class StartTurtle(Choice):
    """Which turtle is free at the start. The other three are captured somewhere in the multiworld.
    Use "random" (built into every Archipelago choice) to pick one of the four."""
    display_name = "Start Turtle"
    option_leonardo = 0
    option_michelangelo = 1
    option_donatello = 2
    option_raphael = 3
    default = option_raphael


class StartArea(Choice):
    """Which Area's sewer pass you start with."""
    display_name = "Start Area"
    option_area_1 = 1
    option_area_2 = 2
    option_area_3 = 3
    option_area_4 = 4
    option_area_5 = 5
    default = option_area_1


class IncludePickups(Toggle):
    """Add item pickups inside Areas as locations. Only works if the game remembers collected pickups."""
    display_name = "Include Pickups"


@dataclass
class TMNTOptions(PerGameCommonOptions):
    start_turtle: StartTurtle
    start_area: StartArea
    include_pickups: IncludePickups
