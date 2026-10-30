from BaseClasses import Location

from .items import GAME_NAME

BASE_ID = 8_870_100

AREAS = range(1, 6)
BOSS_LOCATIONS = {n: f"Area {n} - Boss" for n in AREAS}
ENTRANCE_LOCATIONS = {n: f"Area {n} - Sewer Entrance" for n in AREAS}

location_table: dict[str, int] = {
    name: BASE_ID + offset
    for offset, name in enumerate([*BOSS_LOCATIONS.values(), *ENTRANCE_LOCATIONS.values()])
}


class TMNTLocation(Location):
    game = GAME_NAME
