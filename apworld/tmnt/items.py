from BaseClasses import Item, ItemClassification

GAME_NAME = "Teenage Mutant Ninja Turtles"
BASE_ID = 8_870_000

TURTLES = ("Leonardo", "Michelangelo", "Donatello", "Raphael")
AREA_PASSES = tuple(f"Sewer Pass: Area {n}" for n in range(1, 6))
TOOLS = ("Missile Pack", "Rope Pack", "Zora's Scuba Kit")
FILLER = "Whole Pizza"

item_table: dict[str, tuple[int, ItemClassification]] = {
    name: (BASE_ID + offset, ItemClassification.progression)
    for offset, name in enumerate(TURTLES + AREA_PASSES + TOOLS)
}
item_table[FILLER] = (BASE_ID + len(item_table), ItemClassification.filler)


class TMNTItem(Item):
    game = GAME_NAME
