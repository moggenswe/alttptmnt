# TMNT × ALttP MVP ("Sewer Bridge") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ett TMNT (NES)-stöd för Archipelago, så att en löpare kan spela en solo-seed med ALttP + TMNT. Föremål hoppar mellan spelen, TMNT-areas låses upp med pass och "portalen" är ett OBS-scenbyte.

**Architecture:** TMNT-stödet är ett Archipelago-world-paket, `apworld/tmnt/`, med items, locations, regler, options och ROM-patch. Till det hör en BizHawk-klient (`client.py`) som läser bossvinster ur NES-RAM och skriver mottagna föremål. Ett separat BizHawk-Lua-skript (`lua/tmnt_area_select.lua`) laddar savestates för upplåsta areas. Skriptet och klienten pratar bara via en "brevlåda" på några lediga bytes i NES-RAM. ALttP körs oförändrat via Archipelagos befintliga ALttP-world och SNI.

**Tech Stack:** Python 3.12, Archipelago (källkod, låst tagg), BizHawk 2.9+ (NES-core), Lua 5.4 (BizHawk), pytest, OBS.

**Spec:** `docs/superpowers/specs/2026-10-31-tmnt-alttp-randomizer-design.md`

## Global Constraints

- Python `>= 3.12.10, < 3.14` på Windows (Archipelagos `ModuleUpdate.py` vägrar annat).
- Archipelago körs från källkod. Den tagg som checkas ut i Task 0 skrivs i `docs/archipelago-version.txt` och byts inte under projektet.
- TMNT-ROM: NES, nordamerikansk, md5 `5e24ccd733d15e42d847274e7add0a76` (ren iNES-header, 262 160 byte; tmnt_randos `c14e760c…` kommer från en äldre dump med samma speldata).
- Ingen ROM, savestate eller patchad ROM får hamna i git (`.gitignore`: `*.nes`, `*.sfc`, `*.State`, `*.aptmnt`, `Archipelago/`, `output/`).
- Spelnamnet i Archipelago är exakt `"Teenage Mutant Ninja Turtles"`. Item- och location-ID:n börjar på `8_870_000`.
- Kod och identifierare skrivs på engelska. Dokumentation och runbook skrivs på svenska.
- Målet är Ganon (ALttP-slotten, standardmål) **och** Shredder (TMNT-slotten). Seeden är klar när båda slottarna har nått sitt mål.
- ALttP-slotten: `mode: open`, inga dörrar och ingen entrance-shuffle. Hookshot, Flippers och Moon Pearl ligger i `non_local_items`.
- TMNT-slotten: alla sköldpaddor, alla Area-pass, Missile Pack, Rope Pack och Zora's Scuba Kit ligger i `non_local_items`.

## Review Focus

1. **Emulator-reset eller omstartad klient mitt i en area:** inventariet ska stämma igen inom en sekund, och inga location-checks får skickas dubbelt eller tappas. Testas i Task 6 (`test_resync_after_reset`).
2. **En sköldpadda dör i spelet och blir "tillfångatagen":** hon ska förbli fångad tills nästa area laddas, och sedan vara fri igen om hon finns i inventariet. Klienten får inte väcka henne varje tick. Testas i Task 6 (`test_dead_turtle_not_revived_midarea`).
3. **Spelaren försöker ladda en låst area i väljaren:** det ska inte gå, och ett meddelande ska visas. Testas manuellt i Task 7, steg 4.
4. **Ett föremål tas emot mitt i en area:** det ska gälla direkt. En ny sköldpadda blir fri och missiles läggs till, utan att resten av inventariet skrivs över. Testas i Task 6 (`test_incremental_item_midarea`).
5. **RAM-flimmer under area-övergångar ger en falsk bossvinst:** en bossvinst får bara räknas när flaggan har synts två ticks i rad. Testas i Task 6 (`test_boss_flag_debounce`).

---

## File Structure

```
tmntalttp/
├─ .gitignore
├─ README.md                         # kort: vad, hur man genererar och spelar
├─ docs/
│  ├─ archipelago-version.txt        # låst AP-tagg
│  ├─ research/tmnt-ram.md           # spike-resultat: adresser, beteenden, beslut R1/R2
│  └─ runbook.md                     # stream-uppsättning + genrep-checklista (svenska)
├─ apworld/tmnt/                     # junction-länkas in som Archipelago/worlds/tmnt
│  ├─ __init__.py                    # TMNTWorld, TMNTWeb
│  ├─ items.py                       # item-tabell + klassificering
│  ├─ locations.py                   # location-tabell
│  ├─ options.py                     # StartTurtle, StartArea, IncludePickups
│  ├─ regions.py                     # create_regions()
│  ├─ rules.py                       # set_rules()
│  ├─ ram.py                         # RAM-adresser + brevlåda (från spiken)
│  ├─ client_logic.py                # rena funktioner: diff av RAM → checks, items → skrivningar
│  ├─ client.py                      # TMNTClient(BizHawkClient), tunt lager över client_logic
│  ├─ rom.py                         # TMNTProcedurePatch + write_patch()
│  └─ test/
│     ├─ __init__.py                 # TMNTTestBase(WorldTestBase)
│     ├─ test_pool.py
│     ├─ test_rules.py
│     ├─ test_options.py
│     ├─ test_rom.py
│     └─ test_client_logic.py
├─ lua/
│  ├─ tmnt_ram_probe.lua             # spike-verktyg: visar adresser på skärmen
│  └─ tmnt_area_select.lua           # areaväljare
├─ players/
│  ├─ alttp.yaml
│  └─ tmnt.yaml
├─ tools/gen_many.py                 # genererar N seeds, räknar fel
└─ savestates/                       # gitignore:at; area1.State … area6.State
```

---

### Task 0: Utvecklingsmiljö och repo

**Files:**
- Create: `.gitignore`, `README.md`, `docs/archipelago-version.txt`

- [ ] **Steg 1:** Kör `git init` i `C:\Project\tmntalttp`. Skapa `.gitignore` med mönstren från Global Constraints.
- [ ] **Steg 2:** Klona Archipelago till `C:\Project\tmntalttp\Archipelago` och checka ut den senaste release-taggen. Skriv taggen i `docs/archipelago-version.txt`.
- [ ] **Steg 3:** Skapa en venv med Python 3.12 och kör `python ModuleUpdate.py --yes` i `Archipelago/`.
  Förväntat: körs utan fel.
- [ ] **Steg 4:** Lägg ALttP-ROM:en (JP 1.0, md5 `03a63945398191337e896e5771f77173`) där `host.yaml` pekar. Generera en ALttP-seed: `python Generate.py --player_files_path <mapp med en alttp.yaml>`.
  Förväntat: en zip i `Archipelago/output/`.
- [ ] **Steg 5:** Spela in seeden via SNI i vald SNES-emulator och kontrollera att AP-klienten ansluter till en lokalt startad `MultiServer.py`.
- [ ] **Steg 6:** Committa.

```bash
git add .gitignore README.md docs/archipelago-version.txt
git commit -m "chore: init repo and pin Archipelago version"
```

---

### Task 1: Spike – TMNT:s RAM-karta (risk R1 och R2)

Det här är en forskningsuppgift. Resultatet är ett dokument och konstanter, och det avgör om planen ska fortsätta enligt huvudspåret.

**Files:**
- Create: `lua/tmnt_ram_probe.lua`, `docs/research/tmnt-ram.md`, `apworld/tmnt/ram.py`

**Interfaces:**
- Produces (`ram.py`, alla `int`-adresser i domänen `"RAM"`):
  `CURRENT_AREA`, `TURTLE_HP: dict[str, int]` (nycklarna `"Leonardo"`, `"Michelangelo"`, `"Donatello"`, `"Raphael"`), `CAPTURED_HP_VALUE: int`, `FULL_HP_VALUE: int`, `MISSILE_COUNT`, `ROPE_COUNT`, `BOSS_DEFEATED_SIGNAL: dict[int, tuple[int, int]]` (area → (adress, värde)), `SHREDDER_DEFEATED: tuple[int, int]`, `MAILBOX_BASE` (4 lediga bytes: `+0` pass-bitmask, `+1` laddningsräknare, `+2` klientens ack av räknaren, `+3` magic `0xA7`), `MISSILE_REFILL: int`, `ROPE_REFILL: int`, `PICKUPS_PERSISTENT: bool`.

- [ ] **Steg 1:** Skriv `tmnt_ram_probe.lua`. Varje frame ska den med `gui.text` visa värdena på en lista adresser som läses från en tabell högst upp i skriptet. Ladda skriptet i BizHawk med TMNT-ROM:en.
  Förväntat: värdena syns och ändras när man spelar.
- [ ] **Steg 2:** Hitta adresserna med BizHawks RAM Search och probe-skriptet. Fyll i `docs/research/tmnt-ram.md` med följande:
  - adress och värde för varje sköldpaddas HP och för tillstånden "fångad" och "full HP",
  - aktuell area,
  - antal missiles och ropes,
  - signal för bossvinst i Area 1–5 och för Shredder,
  - fyra bytes som aldrig skrivs under en hel Area 1–3-genomspelning (kandidater: `$07F0–$07FF`).
- [ ] **Steg 3:** Gör R1-testet. Sätt en sköldpaddas HP till fångad-värdet via probe-skriptet i början av Area 1, gå till pausmenyn och försök välja henne.
  Förväntat: hon kan inte väljas. Notera resultatet.
- [ ] **Steg 4:** Gör R2-testet. Plocka upp en pizza, gå ut ur byggnaden och in igen. Undersök om något RAM-värde minns att pizzan är tagen.
  Sätt `PICKUPS_PERSISTENT` efter resultatet och skriv beslutet i dokumentet.
- [ ] **Steg 5:** Bestäm `MISSILE_REFILL` och `ROPE_REFILL` genom att spela Area 3 med kända mängder. Det minsta antal som räcker plus 50 % blir värdet.
- [ ] **Steg 6 (gate):** Om steg 3 misslyckas: stoppa och rapportera till Oscar (planen behöver ett annat sätt att låsa sköldpaddor). Om steg 4 ger `False`: Task 9 hoppas över. Allt annat fortsätter.
- [ ] **Steg 7:** Committa.

```bash
git add lua/tmnt_ram_probe.lua docs/research/tmnt-ram.md apworld/tmnt/ram.py
git commit -m "research: TMNT NES RAM map and R1/R2 decisions"
```

---

### Task 2: Spike – savestates bredvid AP-connectorn

**Files:**
- Create: `lua/tmnt_area_select.lua` (minimal version, byggs ut i Task 7)

- [ ] **Steg 1:** Skapa `savestates/area1.State` manuellt i början av Area 1 (efter introt, alla fyra sköldpaddor fria).
- [ ] **Steg 2:** Skriv en minimal `tmnt_area_select.lua` som anropar `savestate.load("<repo>/savestates/area1.State")` när Select+Upp trycks.
- [ ] **Steg 3:** Öppna Archipelagos `data/lua/connector_bizhawk_generic.lua` och `tmnt_area_select.lua` samtidigt i BizHawks Lua-konsol. Starta `BizHawkClient` från Archipelagos launcher.
  Förväntat: klienten visar att den är ansluten till BizHawk.
- [ ] **Steg 4:** Tryck Select+Upp.
  Förväntat: statet laddas, båda skripten fortsätter köra och klienten förblir ansluten. Om något av det inte stämmer: skriv i `docs/research/tmnt-ram.md` och använd reservplanen från specen (areanummer via RAM).
- [ ] **Steg 5:** Committa.

```bash
git add lua/tmnt_area_select.lua
git commit -m "spike: savestate loading alongside AP connector"
```

---

### Task 3: World-skelett – items, locations, item-pool

**Files:**
- Create: `apworld/tmnt/__init__.py`, `items.py`, `locations.py`, `regions.py` (bara Menu → en region), `test/__init__.py`, `test/test_pool.py`
- Setup: `mklink /J Archipelago\worlds\tmnt apworld\tmnt`

**Interfaces:**
- Produces:
  - `items.py`:
    - `TURTLES = ("Leonardo", "Michelangelo", "Donatello", "Raphael")`
    - `AREA_PASSES = tuple(f"Sewer Pass: Area {n}" for n in range(1, 6))`
    - `TOOLS = ("Missile Pack", "Rope Pack", "Zora's Scuba Kit")`
    - `FILLER = "Whole Pizza"`
    - `item_table: dict[str, tuple[int, ItemClassification]]`: ID:n från `8_870_000` i ordningen turtles, passes, tools, filler. Allt är `progression` utom pizzan, som är `filler`.
    - `class TMNTItem(Item): game = "Teenage Mutant Ninja Turtles"`
  - `locations.py`:
    - `BOSS_LOCATIONS = {n: f"Area {n} - Boss" for n in 1..5}`
    - `ENTRANCE_LOCATIONS = {n: f"Area {n} - Sewer Entrance" for n in 1..5}`
    - `location_table: dict[str, int]`: ID:n från `8_870_100`.
  - `TMNTWorld.game = "Teenage Mutant Ninja Turtles"`, `create_item(name) -> TMNTItem`
  - `test/__init__.py`: `class TMNTTestBase(WorldTestBase): game = "Teenage Mutant Ninja Turtles"`

- [ ] **Steg 1:** Skriv testerna i `test_pool.py`.

```python
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
```

- [ ] **Steg 2:** Kör `python -m pytest worlds/tmnt/test/test_pool.py -v` från `Archipelago/`.
  Förväntat: FAIL (modulen saknas).
- [ ] **Steg 3:** Implementera `items.py`, `locations.py`, `regions.py` (alla locations i regionen `"Menu"` tills vidare) och `TMNTWorld` med `create_regions`, `create_items` och `create_item`.
  - Startsköldpadda och startpass hårdkodas som `Raphael` och `Area 1` och läggs in med `multiworld.push_precollected`. De byts mot options i Task 5.
  - Pizza fyller ut tills antalet items är lika med antalet locations.
- [ ] **Steg 4:** Kör testerna.
  Förväntat: PASS.
- [ ] **Steg 5:** Committa.

```bash
git add apworld/tmnt
git commit -m "feat(tmnt): world skeleton with items, locations and pool"
```

---

### Task 4: Regioner och regler (gating)

**Files:**
- Modify: `apworld/tmnt/regions.py`, `apworld/tmnt/__init__.py`
- Create: `apworld/tmnt/rules.py`, `test/test_rules.py`

**Interfaces:**
- Consumes: namnen från Task 3.
- Produces:
  - Regionerna `"Menu"`, `"Area 1"` … `"Area 6"`.
  - Eventen `"Area N Cleared"` (N = 1..5) på event-locations `"Area N - Cleared"` i respektive area.
  - Event-itemet `"Shredder Defeated"` på location `"Area 6 - Shredder"`.
  - `completion_condition = has("Shredder Defeated")`.
  - `set_rules(world: TMNTWorld) -> None`.

Regler (från specens avsnitt 3.1 och 3.4):

| Ingång / location | Krav |
|---|---|
| Menu → Area N (1–5) | `Sewer Pass: Area N` |
| Menu → Area 2 | dessutom `Zora's Scuba Kit` |
| Menu → Area 3 | dessutom `Missile Pack` och `Rope Pack` |
| Area 5 - Boss och Area 5 - Cleared | `Donatello` (bo-räckvidd, specens 3.1). Event-locationen `Area N - Cleared` har alltid samma regel som `Area N - Boss`. |
| Menu → Area 6 | alla fyra sköldpaddor och minst 3 av `Area 1–5 Cleared` |

- [ ] **Steg 1:** Skriv testerna i `test_rules.py`.
  - `test_area2_needs_scuba`: `assertAccessDependency(["Area 2 - Boss"], [["Zora's Scuba Kit"]])`.
  - `test_area3_needs_missiles_and_ropes`: med passet men bara Missile Pack ska `can_reach_location("Area 3 - Boss")` ge `False`. Med Rope Pack också ska det ge `True`.
  - `test_area5_boss_needs_donatello`.
  - `test_area6_needs_four_turtles_and_three_clears`: samla alla pass, verktyg och tre sköldpaddor → `False`. Lägg till den fjärde → `True`.
  - `test_beatable`: `assertBeatable(True)` efter `collect_by_name` på allt.
- [ ] **Steg 2:** Kör testerna.
  Förväntat: FAIL.
- [ ] **Steg 3:** Implementera regionerna och `set_rules`. Kravet "3 av 5 avklarade" implementeras med `state.has_from_list([...], player, 3)`.
- [ ] **Steg 4:** Kör hela `worlds/tmnt/test`.
  Förväntat: PASS.
- [ ] **Steg 5:** Committa: `feat(tmnt): area gating rules`.

---

### Task 5: Options

**Files:**
- Create: `apworld/tmnt/options.py`, `test/test_options.py`
- Modify: `apworld/tmnt/__init__.py` (`options_dataclass`, `generate_early`, `create_items`, `fill_slot_data`)

**Interfaces:**
- Produces:
  - `StartTurtle(Choice)`: `random=0, leonardo=1, michelangelo=2, donatello=3, raphael=4`, standard `raphael`.
  - `StartArea(Choice)`: `area_1`…`area_5`, standard `area_1`.
  - `IncludePickups(Toggle)`: standard av. Den används först i Task 9.
  - `TMNTOptions(PerGameCommonOptions)`.
  - `fill_slot_data() -> {"start_turtle": str, "start_area": int, "include_pickups": bool}`.

- [ ] **Steg 1:** Skriv testerna.
  - `test_start_turtle_precollected`: options `{"start_turtle": "donatello"}` → Donatello finns i `multiworld.precollected_items[1]` men inte i poolen.
  - `test_random_start_turtle_is_one_of_four`.
  - `test_start_area_3_is_still_beatable`: options `{"start_area": "area_3"}` → `assertBeatable(True)` efter att allt annat samlats.
- [ ] **Steg 2:** Kör testerna.
  Förväntat: FAIL.
- [ ] **Steg 3:** Implementera. `generate_early` löser upp `random` till ett av sköldpaddsnamnen och sparar resultatet på world-objektet.
- [ ] **Steg 4:** Kör hela testsviten.
  Förväntat: PASS.
- [ ] **Steg 5:** Committa: `feat(tmnt): start turtle, start area and pickup options`.

---

### Task 6: Klientlogik (rena funktioner) och BizHawk-klient

**Files:**
- Create: `apworld/tmnt/client_logic.py`, `apworld/tmnt/client.py`, `test/test_client_logic.py`
- Modify: `apworld/tmnt/__init__.py` (`from . import client` så att klienten registreras)

**Interfaces:**
- Consumes: alla konstanter i `ram.py` (Task 1), namnen i `items.py` och `locations.py`.
- Produces (`client_logic.py`):
  - `@dataclass(frozen=True) class Inventory: turtles: frozenset[str]; passes: frozenset[int]; missiles: bool; ropes: bool; scuba: bool`
  - `inventory_from_items(item_names: list[str]) -> Inventory`
  - `area6_unlocked(inv: Inventory, cleared_areas: set[int]) -> bool`
  - `pass_bitmask(inv: Inventory, cleared_areas: set[int]) -> int`: bit 0–4 = Area 1–5. Area 2 sätts bara om Scuba finns och Area 3 bara om Missile Pack och Rope Pack finns, så att väljaren inte kan ladda en area som logiken inte tillåter. Bit 5 = Area 6.
  - `full_sync_writes(inv: Inventory) -> list[tuple[int, list[int]]]`: HP till full för sköldpaddor man har och till fångad för övriga, plus `MISSILE_REFILL`/`ROPE_REFILL` om packen finns, annars 0.
  - `incremental_writes(old: Inventory, new: Inventory, ram_now: dict[int, int]) -> list[tuple[int, list[int]]]`: bara nytillkomna sköldpaddor (full HP) och nytillkomna packs (refill).
  - `class BossDebouncer: def update(self, area_signals: dict[int, bool]) -> set[int]`: returnerar de areas vars signal varit sann två uppdateringar i rad, varje area bara en gång.
  - `needs_full_sync(counter: int, ack: int) -> bool`: True när räknaren och ack skiljer sig åt.
- Produces (`client.py`):
  - `class TMNTClient(BizHawkClient)`: `game = "Teenage Mutant Ninja Turtles"`, `system = "NES"`, `patch_suffix = ".aptmnt"`.
  - `validate_rom`: läser ROM-taggen som Task 8 skriver.
  - `game_watcher`:
    - läser RAM och skickar `LocationChecks` för nya bossvinster och nya area-ingångar,
    - skriver om laddningsräknaren (`MAILBOX+1`) skiljer sig från ack (`MAILBOX+2`): kör `full_sync_writes` och sätter ack = räknaren,
    - annars kör den `incremental_writes`,
    - skriver alltid `pass_bitmask`,
    - skickar `StatusUpdate CLIENT_GOAL` när `SHREDDER_DEFEATED` syns.

- [ ] **Steg 1:** Skriv testerna i `test_client_logic.py`. Det är rena enhetstester, utan BizHawk.
  - `test_pass_bitmask_hides_area2_without_scuba`: passen 1 och 2 utan scuba → `0b00001`.
  - `test_area6_bit_requires_four_turtles_three_clears`
  - `test_full_sync_captures_missing_turtles`: inventariet {Raphael} → skrivning `TURTLE_HP["Leonardo"] = CAPTURED_HP_VALUE`.
  - `test_dead_turtle_not_revived_midarea` (Review Focus 2): samma inventarie före och efter, Raphaels HP i `ram_now` = fångad → `incremental_writes` returnerar `[]`.
  - `test_incremental_item_midarea` (Review Focus 4): Donatello är ny → exakt en skrivning, Donatellos HP = full.
  - `test_resync_after_reset` (Review Focus 1): räknaren 5 och ack 0 → klienten väljer full sync. Testa via den rena hjälpfunktionen `needs_full_sync(counter: int, ack: int) -> bool`.
  - `test_boss_flag_debounce` (Review Focus 5): `update({1: True})` → `set()`, igen → `{1}`, igen → `set()`.
- [ ] **Steg 2:** Kör testerna.
  Förväntat: FAIL.
- [ ] **Steg 3:** Implementera `client_logic.py`. Implementera sedan `client.py` som ett tunt lager som anropar `bizhawk.read`/`bizhawk.write` och logiken. Klientens kod har inga egna enhetstester. Den verifieras i steg 5.
- [ ] **Steg 4:** Kör testerna.
  Förväntat: PASS.
- [ ] **Steg 5 (manuellt):** Generera en seed med en TMNT-YAML, starta `MultiServer.py`, ladda den patchade ROM:en (Task 8 måste vara klar, så kör det här steget efter Task 8) och anslut klienten. Skriv `/send <TMNT-spelarens namn> Donatello` i serverkonsolen.
  Förväntat: Donatello kan väljas direkt i pausmenyn.
- [ ] **Steg 6:** Committa: `feat(tmnt): BizHawk client and pure client logic`.

---

### Task 7: Areaväljaren (Lua) och area-savestates

**Files:**
- Modify: `lua/tmnt_area_select.lua`
- Create (inte i git): `savestates/area1.State` … `area6.State`

**Interfaces:**
- Consumes: `MAILBOX_BASE` och magic-värdet från `ram.py`. Adresserna skrivs som konstanter högst upp i Lua-skriptet med en kommentar som pekar på `ram.py`.
- Produces: laddningsräknaren `MAILBOX+1` räknas upp med 1 (mod 256) direkt efter varje lyckad `savestate.load`.

- [ ] **Steg 1:** Skapa savestates för Area 1–6, alla tagna direkt efter area-introt med alla fyra sköldpaddor fria.
  - Senare areas nås genom att skriva areanumret med probe-skriptet om Task 1 hittade en sådan adress, annars genom att spela fram.
  - Skriv i `docs/research/tmnt-ram.md` hur varje state skapades.
- [ ] **Steg 2:** Bygg ut skriptet.
  - Select+Upp/Ned öppnar och stänger en meny som ritas med `gui.text`. Den listar Area 1–6 och markerar låsta areas.
  - Menyn öppnas inte om magic-byten (`MAILBOX+3`) saknas, alltså om klienten inte är ansluten. Då visas texten "Anslut AP-klienten".
  - A väljer en area. Om dess bit i pass-bitmasken (`MAILBOX+0`) är satt laddas savestaten. Därefter räknas `MAILBOX+1` upp och magic-byten skrivs tillbaka (savestaten skriver över RAM).
  - Alla area-states har Leo aktiv. Klienten fångar aldrig den aktiva sköldpaddan, eftersom HP 0 på henne startar dödsanimationen. En sköldpadda man inte äger kan alltså spelas tills man byter bort henne. Lös det här: antingen states per aktiv sköldpadda, där väljaren laddar en state med en ägd sköldpadda aktiv, eller testa i BizHawk om det är säkert att skriva `$0067` innan HP skrivs.
  - Räknaren får aldrig bli 0 (255 → 1). Klienten tolkar 0 som "ingen area laddad än", eftersom areabyten `$0048` också är 0 vid uppstart.
- [ ] **Steg 3:** Gör ett manuellt test med en ansluten klient som har passen 1 och 3, men utan Missile Pack och Rope Pack.
  Förväntat: bara Area 1 kan väljas.
- [ ] **Steg 4 (Review Focus 3):** Försök välja Area 3.
  Förväntat: inget laddas och texten "Låst" visas i 2 sekunder.
- [ ] **Steg 5:** Ladda Area 1.
  Förväntat: inom en sekund har bara de sköldpaddor man har full HP, och övriga är fångade (klienten har gjort en full sync).
- [ ] **Steg 6:** Committa: `feat: area select menu with pass gating`.

---

### Task 8: ROM-patch och ROM-validering

**Files:**
- Create: `apworld/tmnt/rom.py`, `test/test_rom.py`
- Modify: `apworld/tmnt/__init__.py` (`generate_output`)

**Interfaces:**
- Produces:
  - `class TMNTProcedurePatch(APProcedurePatch, APTokenMixin)`: `game = "Teenage Mutant Ninja Turtles"`, `hash = "c14e760c4d5a086e4186d2e1fc9b7743"`, `patch_file_ending = ".aptmnt"`, `result_file_ending = ".nes"`, `procedure = [("apply_tokens", ["token_data.bin"])]`.
  - `write_patch(world: TMNTWorld, patch: TMNTProcedurePatch) -> None`: skriver taggen `b"TMNTAP"` plus 6 bytes av seed-namnet till en ledig ROM-plats som hittas i Task 1. Om offseten inte hittades i spiken: leta efter ett område med `0xFF` i sista PRG-banken och dokumentera det i `ram.py` som `ROM_TAG_OFFSET`.
  - `validate_rom` i Task 6 läser `ROM_TAG_OFFSET` i domänen `"PRG ROM"`.

- [ ] **Steg 1:** Skriv testet `test_patch_writes_tag`. Kör `write_patch` på ett patch-objekt och kontrollera med `patch.get_token_binary()` att det innehåller en `WRITE`-token på `ROM_TAG_OFFSET` med data som börjar på `b"TMNTAP"`. Testet behöver ingen riktig ROM.
- [ ] **Steg 2:** Kör testet.
  Förväntat: FAIL.
- [ ] **Steg 3:** Implementera `rom.py` och `generate_output`, som skriver `<outfilebase>.aptmnt` till `output_directory`.
- [ ] **Steg 4:** Kör testerna.
  Förväntat: PASS. Generera sedan en seed och öppna `.aptmnt` från launchern.
  Förväntat: en patchad `.nes` skapas och BizHawk-klienten accepterar den (`validate_rom` = True). Kör nu Task 6, steg 5.
- [ ] **Steg 5:** Committa: `feat(tmnt): procedure patch with ROM tag`.

---

### Task 9 (bara om `PICKUPS_PERSISTENT` är True): Pickups som locations

**Files:**
- Modify: `locations.py`, `regions.py`, `rom.py`, `client_logic.py`, `client.py`, `ram.py`
- Test: `test/test_pool.py`, `test/test_client_logic.py`

**Interfaces:**
- Produces:
  - `PICKUP_LOCATIONS: dict[str, tuple[int, int]]` (namn → (area, ROM-offset)), med 20–30 utvalda platser ur tmnt_randos `tables/item_pointers.txt`. Kopiera adresserna och ange källan i en kommentar. Platserna väljs ut i Task 1, steg 4.
  - Location-ID:n från `8_870_200`.
  - Med `include_pickups` på läggs pizza till i poolen så att antalet items fortfarande stämmer med antalet locations.
  - `write_patch` sätter item-typen `0x08` (scroll) på pickups som har AP-items. Det är specens markör för MVP, och scrollens effekt följer med.
  - `pickup_checks(ram_flags: bytes) -> set[str]` i `client_logic.py`.

- [ ] **Steg 1:** Testa att `test_pool_matches_locations` fortfarande går igenom med `{"include_pickups": True}`, och att `pickup_checks` mappar en satt flagga till rätt namn.
- [ ] **Steg 2:** Kör testerna.
  Förväntat: FAIL.
- [ ] **Steg 3:** Implementera.
- [ ] **Steg 4:** Kör testerna.
  Förväntat: PASS.
- [ ] **Steg 5:** Gör ett manuellt test: plocka upp en markerad scroll och kontrollera att checken syns i serverkonsolen.
- [ ] **Steg 6:** Committa: `feat(tmnt): optional pickup locations`.

---

### Task 10: Spelar-YAMLs och massgenerering

**Files:**
- Create: `players/alttp.yaml`, `players/tmnt.yaml`, `tools/gen_many.py`

**Interfaces:**
- Produces: `python tools/gen_many.py --count 200 --players players/ --ap Archipelago/` skriver ut `ok=<n> failed=<m>` och avslutas med kod 0 bara om `failed == 0`.

- [ ] **Steg 1:** Skriv YAML-filerna enligt Global Constraints. ALttP: `mode: open`, `goal: ganon`, `non_local_items: [Hookshot, Flippers, Moon Pearl]`. TMNT: `start_turtle: raphael`, `non_local_items` enligt Global Constraints.
- [ ] **Steg 2:** Skriv `gen_many.py`. Det kör `Generate.py` i en subprocess med `--seed <i>` för i = 1..count och räknar fel. Utdata hamnar i `output/` (gitignore).
- [ ] **Steg 3:** Kör `python tools/gen_many.py --count 200 ...`.
  Förväntat: `ok=200 failed=0`. Kör det även med `start_area: area_3`.
- [ ] **Steg 4:** Kontrollera i 5 spoiler-loggar att minst ett TMNT-pass hamnar bakom ALttP-progression och att minst ett ALttP-item ligger på en TMNT-boss.
- [ ] **Steg 5:** Committa: `feat: player yamls and bulk generation check`.

---

### Task 11: Stream-uppsättning och genrep

**Files:**
- Create: `docs/runbook.md`

- [ ] **Steg 1:** Skriv `runbook.md` på svenska. Den ska ta upp:
  - startordning: MultiServer → SNI + SNES-emulator + SNI-klient → BizHawk + connector + `tmnt_area_select.lua` + BizHawkClient,
  - OBS-scener "Hyrule", "Kloak (övergång)" och "New York",
  - stinger-övergången "pizza-wipe",
  - snabbtangenter: en tangent som pausar den aktiva emulatorn och byter scen,
  - åtgärder vid krasch: starta om klienten och ladda senaste area-state.
- [ ] **Steg 2:** Gör ett genrep. Spela en hel seed på stream-maskinen och notera totaltid, softlocks och oklarheter i runbookens checklista.
  Förväntat: seeden går att slutföra, båda målen nås och tiden ligger på 1,5–2,5 timmar. Annars: justera `MISSILE_REFILL` och `ROPE_REFILL`, `start_area` eller ALttP:s `crystals_needed_for_gt` och kör ett nytt genrep.
- [ ] **Steg 3:** Committa: `docs: stream runbook and rehearsal results`.

---

## Avvikelse från specen

Specens reservplan för locations (R2) säger "bossvinster och Area-avslut". Bossvinsten *är* avslutet på en area, så planen använder i stället **bossvinst + area-ingång** (5 + 5 = 10 locations). Det räcker för TMNT:s 10 progressionsföremål (3 sköldpaddor, 4 pass och 3 verktyg) utan att kräva pickups.

## Utanför den här planen (enligt specen)

Automatisk portal via ALttP-rumdetektering, `pizza_traps`, `easy_tmnt`, en egen AP-item-sprite i TMNT, MSU-1, fiendeslump och spår B (en ROM i SMZ3-stil).
