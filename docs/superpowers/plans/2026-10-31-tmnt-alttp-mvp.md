# TMNT × ALttP MVP ("Sewer Bridge") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** TMNT (NES) support for Archipelago, so that a runner can play a solo seed with ALttP + TMNT. Items jump between the games, TMNT areas are unlocked with passes, and the "portal" is an OBS scene switch.

**Architecture:** TMNT support is an Archipelago world package, `apworld/tmnt/`, with items, locations, rules, options and a ROM patch. It comes with a BizHawk client (`client.py`) that reads boss wins from NES RAM and writes received items. A separate BizHawk Lua script (`lua/tmnt_area_select.lua`) loads savestates for unlocked areas. The script and the client talk only through a "mailbox" of a few free bytes in NES RAM. ALttP runs unchanged through Archipelago's existing ALttP world and SNI.

**Tech Stack:** Python 3.12, Archipelago (source, pinned tag), BizHawk 2.9+ (NES core), Lua 5.4 (BizHawk), pytest, OBS.

**Spec:** `docs/superpowers/specs/2026-10-31-tmnt-alttp-randomizer-design.md`

## Global Constraints

- Python `>= 3.12.10, < 3.14` on Windows (Archipelago's `ModuleUpdate.py` refuses anything else).
- Archipelago runs from source. The tag checked out in Task 0 is written to `docs/archipelago-version.txt` and is not changed during the project.
- TMNT ROM: NES, North American, md5 `5e24ccd733d15e42d847274e7add0a76` (clean iNES header, 262 160 bytes; tmnt_rando's `c14e760c…` comes from an older dump with the same game data).
- No ROM, savestate or patched ROM may end up in git (`.gitignore`: `*.nes`, `*.sfc`, `*.State`, `*.aptmnt`, `Archipelago/`, `output/`).
- The game name in Archipelago is exactly `"Teenage Mutant Ninja Turtles"`. Item and location IDs start at `8_870_000`.
- Code and identifiers are written in English. Documentation and the runbook are written in English (first written in Swedish, translated on 2026-10-31).
- The goal is Ganon (the ALttP slot, default goal) **and** Shredder (the TMNT slot). The seed is finished when both slots have reached their goal.
- The ALttP slot: `mode: open`, no doors and no entrance shuffle. Hookshot, Flippers and Moon Pearl are in `non_local_items`.
- The TMNT slot: all turtles, all Area passes, Missile Pack, Rope Pack and Zora's Scuba Kit are in `non_local_items`.

## Review Focus

1. **Emulator reset or restarted client in the middle of an area:** the inventory must be correct again within one second, and no location checks may be sent twice or lost. Tested in Task 6 (`test_resync_after_reset`).
2. **A turtle dies in the game and becomes "captured":** she must stay captured until the next area is loaded, and then be free again if she is in the inventory. The client must not revive her every tick. Tested in Task 6 (`test_dead_turtle_not_revived_midarea`).
3. **The player tries to load a locked area in the selector:** it must not work, and a message must be shown. Tested manually in Task 7, step 4.
4. **An item is received in the middle of an area:** it must take effect immediately. A new turtle becomes free and missiles are added, without the rest of the inventory being overwritten. Tested in Task 6 (`test_incremental_item_midarea`).
5. **RAM flicker during area transitions gives a false boss win:** a boss win may only count once the flag has been seen two ticks in a row. Tested in Task 6 (`test_boss_flag_debounce`).

---

## File Structure

```
tmntalttp/
├─ .gitignore
├─ README.md                         # short: what it is, how to generate and play
├─ docs/
│  ├─ archipelago-version.txt        # pinned AP tag
│  ├─ research/tmnt-ram.md           # spike results: addresses, behaviours, R1/R2 decisions
│  └─ runbook.md                     # stream setup + dress rehearsal checklist
├─ apworld/tmnt/                     # junction-linked in as Archipelago/worlds/tmnt
│  ├─ __init__.py                    # TMNTWorld, TMNTWeb
│  ├─ items.py                       # item table + classification
│  ├─ locations.py                   # location table
│  ├─ options.py                     # StartTurtle, StartArea, IncludePickups
│  ├─ regions.py                     # create_regions()
│  ├─ rules.py                       # set_rules()
│  ├─ ram.py                         # RAM addresses + mailbox (from the spike)
│  ├─ client_logic.py                # pure functions: RAM diff → checks, items → writes
│  ├─ client.py                      # TMNTClient(BizHawkClient), thin layer over client_logic
│  ├─ rom.py                         # TMNTProcedurePatch + write_patch()
│  └─ test/
│     ├─ __init__.py                 # TMNTTestBase(WorldTestBase)
│     ├─ test_pool.py
│     ├─ test_rules.py
│     ├─ test_options.py
│     ├─ test_rom.py
│     └─ test_client_logic.py
├─ lua/
│  ├─ tmnt_ram_probe.lua             # spike tool: shows addresses on screen
│  └─ tmnt_area_select.lua           # area selector
├─ players/
│  ├─ alttp.yaml
│  └─ tmnt.yaml
├─ tools/gen_many.py                 # generates N seeds, counts failures
└─ savestates/                       # gitignored; area1.State … area6.State
```

---

### Task 0: Development environment and repo

**Files:**
- Create: `.gitignore`, `README.md`, `docs/archipelago-version.txt`

- [ ] **Step 1:** Run `git init` in `C:\Project\tmntalttp`. Create `.gitignore` with the patterns from Global Constraints.
- [ ] **Step 2:** Clone Archipelago to `C:\Project\tmntalttp\Archipelago` and check out the latest release tag. Write the tag to `docs/archipelago-version.txt`.
- [ ] **Step 3:** Create a venv with Python 3.12 and run `python ModuleUpdate.py --yes` in `Archipelago/`.
  Expected: runs without errors.
- [ ] **Step 4:** Put the ALttP ROM (JP 1.0, md5 `03a63945398191337e896e5771f77173`) where `host.yaml` points. Generate an ALttP seed: `python Generate.py --player_files_path <folder with an alttp.yaml>`.
  Expected: a zip in `Archipelago/output/`.
- [ ] **Step 5:** Play the seed via SNI in the chosen SNES emulator and check that the AP client connects to a locally started `MultiServer.py`.
- [ ] **Step 6:** Commit.

```bash
git add .gitignore README.md docs/archipelago-version.txt
git commit -m "chore: init repo and pin Archipelago version"
```

---

### Task 1: Spike – TMNT's RAM map (risks R1 and R2)

This is a research task. The result is a document and constants, and it decides whether the plan continues on the main track.

**Files:**
- Create: `lua/tmnt_ram_probe.lua`, `docs/research/tmnt-ram.md`, `apworld/tmnt/ram.py`

**Interfaces:**
- Produces (`ram.py`, all `int` addresses in the `"RAM"` domain):
  `CURRENT_AREA`, `TURTLE_HP: dict[str, int]` (keys `"Leonardo"`, `"Michelangelo"`, `"Donatello"`, `"Raphael"`), `CAPTURED_HP_VALUE: int`, `FULL_HP_VALUE: int`, `MISSILE_COUNT`, `ROPE_COUNT`, `BOSS_DEFEATED_SIGNAL: dict[int, tuple[int, int]]` (area → (address, value)), `SHREDDER_DEFEATED: tuple[int, int]`, `MAILBOX_BASE` (4 free bytes: `+0` pass bitmask, `+1` load counter, `+2` the client's ack of the counter, `+3` magic `0xA7`), `MISSILE_REFILL: int`, `ROPE_REFILL: int`, `PICKUPS_PERSISTENT: bool`.

- [ ] **Step 1:** Write `tmnt_ram_probe.lua`. Every frame it should use `gui.text` to show the values of a list of addresses read from a table at the top of the script. Load the script in BizHawk with the TMNT ROM.
  Expected: the values show up and change as you play.
- [ ] **Step 2:** Find the addresses with BizHawk's RAM Search and the probe script. Fill in `docs/research/tmnt-ram.md` with the following:
  - address and value for each turtle's HP and for the "captured" and "full HP" states,
  - current area,
  - number of missiles and ropes,
  - boss win signal for Area 1–5 and for Shredder,
  - four bytes that are never written during a full Area 1–3 playthrough (candidates: `$07F0–$07FF`).
- [ ] **Step 3:** Do the R1 test. Set a turtle's HP to the captured value with the probe script at the start of Area 1, go to the pause menu and try to select her.
  Expected: she cannot be selected. Note the result.
- [ ] **Step 4:** Do the R2 test. Pick up a pizza, leave the building and go back in. Check whether any RAM value remembers that the pizza has been taken.
  Set `PICKUPS_PERSISTENT` from the result and write the decision in the document.
- [ ] **Step 5:** Decide `MISSILE_REFILL` and `ROPE_REFILL` by playing Area 3 with known amounts. The smallest amount that is enough, plus 50 %, becomes the value.
- [ ] **Step 6 (gate):** If step 3 fails: stop and report to the owner (the plan needs another way to lock turtles). If step 4 gives `False`: Task 9 is skipped. Everything else continues.
- [ ] **Step 7:** Commit.

```bash
git add lua/tmnt_ram_probe.lua docs/research/tmnt-ram.md apworld/tmnt/ram.py
git commit -m "research: TMNT NES RAM map and R1/R2 decisions"
```

---

### Task 2: Spike – savestates next to the AP connector

**Files:**
- Create: `lua/tmnt_area_select.lua` (minimal version, extended in Task 7)

- [ ] **Step 1:** Create `savestates/area1.State` manually at the start of Area 1 (after the intro, all four turtles free).
- [ ] **Step 2:** Write a minimal `tmnt_area_select.lua` that calls `savestate.load("<repo>/savestates/area1.State")` when Select+Up is pressed.
- [ ] **Step 3:** Open Archipelago's `data/lua/connector_bizhawk_generic.lua` and `tmnt_area_select.lua` at the same time in BizHawk's Lua console. Start `BizHawkClient` from Archipelago's launcher.
  Expected: the client shows that it is connected to BizHawk.
- [ ] **Step 4:** Press Select+Up.
  Expected: the state loads, both scripts keep running and the client stays connected. If any of that does not hold: write it in `docs/research/tmnt-ram.md` and use the fallback from the spec (area number via RAM).
- [ ] **Step 5:** Commit.

```bash
git add lua/tmnt_area_select.lua
git commit -m "spike: savestate loading alongside AP connector"
```

---

### Task 3: World skeleton – items, locations, item pool

**Files:**
- Create: `apworld/tmnt/__init__.py`, `items.py`, `locations.py`, `regions.py` (only Menu → one region), `test/__init__.py`, `test/test_pool.py`
- Setup: `mklink /J Archipelago\worlds\tmnt apworld\tmnt`

**Interfaces:**
- Produces:
  - `items.py`:
    - `TURTLES = ("Leonardo", "Michelangelo", "Donatello", "Raphael")`
    - `AREA_PASSES = tuple(f"Sewer Pass: Area {n}" for n in range(1, 6))`
    - `TOOLS = ("Missile Pack", "Rope Pack", "Zora's Scuba Kit")`
    - `FILLER = "Whole Pizza"`
    - `item_table: dict[str, tuple[int, ItemClassification]]`: IDs from `8_870_000` in the order turtles, passes, tools, filler. Everything is `progression` except the pizza, which is `filler`.
    - `class TMNTItem(Item): game = "Teenage Mutant Ninja Turtles"`
  - `locations.py`:
    - `BOSS_LOCATIONS = {n: f"Area {n} - Boss" for n in 1..5}`
    - `ENTRANCE_LOCATIONS = {n: f"Area {n} - Sewer Entrance" for n in 1..5}`
    - `location_table: dict[str, int]`: IDs from `8_870_100`.
  - `TMNTWorld.game = "Teenage Mutant Ninja Turtles"`, `create_item(name) -> TMNTItem`
  - `test/__init__.py`: `class TMNTTestBase(WorldTestBase): game = "Teenage Mutant Ninja Turtles"`

- [ ] **Step 1:** Write the tests in `test_pool.py`.

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

- [ ] **Step 2:** Run `python -m pytest worlds/tmnt/test/test_pool.py -v` from `Archipelago/`.
  Expected: FAIL (the module is missing).
- [ ] **Step 3:** Implement `items.py`, `locations.py`, `regions.py` (all locations in the `"Menu"` region for now) and `TMNTWorld` with `create_regions`, `create_items` and `create_item`.
  - The starting turtle and starting pass are hard-coded as `Raphael` and `Area 1` and added with `multiworld.push_precollected`. They are replaced with options in Task 5.
  - Pizza fills up until the number of items equals the number of locations.
- [ ] **Step 4:** Run the tests.
  Expected: PASS.
- [ ] **Step 5:** Commit.

```bash
git add apworld/tmnt
git commit -m "feat(tmnt): world skeleton with items, locations and pool"
```

---

### Task 4: Regions and rules (gating)

**Files:**
- Modify: `apworld/tmnt/regions.py`, `apworld/tmnt/__init__.py`
- Create: `apworld/tmnt/rules.py`, `test/test_rules.py`

**Interfaces:**
- Consumes: the names from Task 3.
- Produces:
  - The regions `"Menu"`, `"Area 1"` … `"Area 6"`.
  - The events `"Area N Cleared"` (N = 1..5) on event locations `"Area N - Cleared"` in each area.
  - The event item `"Shredder Defeated"` on location `"Area 6 - Shredder"`.
  - `completion_condition = has("Shredder Defeated")`.
  - `set_rules(world: TMNTWorld) -> None`.

Rules (from sections 3.1 and 3.4 of the spec):

| Entrance / location | Requirement |
|---|---|
| Menu → Area N (1–5) | `Sewer Pass: Area N` |
| Menu → Area 2 | also `Zora's Scuba Kit` |
| Menu → Area 3 | also `Missile Pack` and `Rope Pack` |
| Area 5 - Boss and Area 5 - Cleared | `Donatello` (bo reach, spec 3.1). The event location `Area N - Cleared` always has the same rule as `Area N - Boss`. |
| Menu → Area 6 | all four turtles and at least 3 of `Area 1–5 Cleared` |

- [ ] **Step 1:** Write the tests in `test_rules.py`.
  - `test_area2_needs_scuba`: `assertAccessDependency(["Area 2 - Boss"], [["Zora's Scuba Kit"]])`.
  - `test_area3_needs_missiles_and_ropes`: with the pass but only Missile Pack, `can_reach_location("Area 3 - Boss")` should give `False`. With Rope Pack as well it should give `True`.
  - `test_area5_boss_needs_donatello`.
  - `test_area6_needs_four_turtles_and_three_clears`: collect all passes, tools and three turtles → `False`. Add the fourth → `True`.
  - `test_beatable`: `assertBeatable(True)` after `collect_by_name` on everything.
- [ ] **Step 2:** Run the tests.
  Expected: FAIL.
- [ ] **Step 3:** Implement the regions and `set_rules`. The "3 of 5 cleared" requirement is implemented with `state.has_from_list([...], player, 3)`.
- [ ] **Step 4:** Run all of `worlds/tmnt/test`.
  Expected: PASS.
- [ ] **Step 5:** Commit: `feat(tmnt): area gating rules`.

---

### Task 5: Options

**Files:**
- Create: `apworld/tmnt/options.py`, `test/test_options.py`
- Modify: `apworld/tmnt/__init__.py` (`options_dataclass`, `generate_early`, `create_items`, `fill_slot_data`)

**Interfaces:**
- Produces:
  - `StartTurtle(Choice)`: `random=0, leonardo=1, michelangelo=2, donatello=3, raphael=4`, default `raphael`.
  - `StartArea(Choice)`: `area_1`…`area_5`, default `area_1`.
  - `IncludePickups(Toggle)`: off by default. It is only used in Task 9.
  - `TMNTOptions(PerGameCommonOptions)`.
  - `fill_slot_data() -> {"start_turtle": str, "start_area": int, "include_pickups": bool}`.

- [ ] **Step 1:** Write the tests.
  - `test_start_turtle_precollected`: options `{"start_turtle": "donatello"}` → Donatello is in `multiworld.precollected_items[1]` but not in the pool.
  - `test_random_start_turtle_is_one_of_four`.
  - `test_start_area_3_is_still_beatable`: options `{"start_area": "area_3"}` → `assertBeatable(True)` after everything else has been collected.
- [ ] **Step 2:** Run the tests.
  Expected: FAIL.
- [ ] **Step 3:** Implement. `generate_early` resolves `random` to one of the turtle names and stores the result on the world object.
- [ ] **Step 4:** Run the whole test suite.
  Expected: PASS.
- [ ] **Step 5:** Commit: `feat(tmnt): start turtle, start area and pickup options`.

---

### Task 6: Client logic (pure functions) and BizHawk client

**Files:**
- Create: `apworld/tmnt/client_logic.py`, `apworld/tmnt/client.py`, `test/test_client_logic.py`
- Modify: `apworld/tmnt/__init__.py` (`from . import client` so that the client is registered)

**Interfaces:**
- Consumes: all constants in `ram.py` (Task 1), the names in `items.py` and `locations.py`.
- Produces (`client_logic.py`):
  - `@dataclass(frozen=True) class Inventory: turtles: frozenset[str]; passes: frozenset[int]; missiles: bool; ropes: bool; scuba: bool`
  - `inventory_from_items(item_names: list[str]) -> Inventory`
  - `area6_unlocked(inv: Inventory, cleared_areas: set[int]) -> bool`
  - `pass_bitmask(inv: Inventory, cleared_areas: set[int]) -> int`: bits 0–4 = Area 1–5. Area 2 is only set if Scuba is owned and Area 3 only if Missile Pack and Rope Pack are owned, so that the selector cannot load an area the logic does not allow. Bit 5 = Area 6.
  - `full_sync_writes(inv: Inventory) -> list[tuple[int, list[int]]]`: HP to full for turtles you have and to captured for the rest, plus `MISSILE_REFILL`/`ROPE_REFILL` if the pack is owned, otherwise 0.
  - `incremental_writes(old: Inventory, new: Inventory, ram_now: dict[int, int]) -> list[tuple[int, list[int]]]`: only newly added turtles (full HP) and newly added packs (refill).
  - `class BossDebouncer: def update(self, area_signals: dict[int, bool]) -> set[int]`: returns the areas whose signal has been true for two updates in a row, each area only once.
  - `needs_full_sync(counter: int, ack: int) -> bool`: True when the counter and the ack differ.
- Produces (`client.py`):
  - `class TMNTClient(BizHawkClient)`: `game = "Teenage Mutant Ninja Turtles"`, `system = "NES"`, `patch_suffix = ".aptmnt"`.
  - `validate_rom`: reads the ROM tag that Task 8 writes.
  - `game_watcher`:
    - reads RAM and sends `LocationChecks` for new boss wins and new area entrances,
    - if the load counter (`MAILBOX+1`) differs from the ack (`MAILBOX+2`): runs `full_sync_writes` and sets ack = counter,
    - otherwise it runs `incremental_writes`,
    - always writes `pass_bitmask`,
    - sends `StatusUpdate CLIENT_GOAL` when `SHREDDER_DEFEATED` is seen.

- [ ] **Step 1:** Write the tests in `test_client_logic.py`. They are pure unit tests, without BizHawk.
  - `test_pass_bitmask_hides_area2_without_scuba`: passes 1 and 2 without scuba → `0b00001`.
  - `test_area6_bit_requires_four_turtles_three_clears`
  - `test_full_sync_captures_missing_turtles`: the inventory {Raphael} → write `TURTLE_HP["Leonardo"] = CAPTURED_HP_VALUE`.
  - `test_dead_turtle_not_revived_midarea` (Review Focus 2): the same inventory before and after, Raphael's HP in `ram_now` = captured → `incremental_writes` returns `[]`.
  - `test_incremental_item_midarea` (Review Focus 4): Donatello is new → exactly one write, Donatello's HP = full.
  - `test_resync_after_reset` (Review Focus 1): counter 5 and ack 0 → the client chooses a full sync. Test through the pure helper function `needs_full_sync(counter: int, ack: int) -> bool`.
  - `test_boss_flag_debounce` (Review Focus 5): `update({1: True})` → `set()`, again → `{1}`, again → `set()`.
- [ ] **Step 2:** Run the tests.
  Expected: FAIL.
- [ ] **Step 3:** Implement `client_logic.py`. Then implement `client.py` as a thin layer that calls `bizhawk.read`/`bizhawk.write` and the logic. The client's code has no unit tests of its own. It is verified in step 5.
- [ ] **Step 4:** Run the tests.
  Expected: PASS.
- [ ] **Step 5 (manual):** Generate a seed with a TMNT YAML, start `MultiServer.py`, load the patched ROM (Task 8 must be done, so run this step after Task 8) and connect the client. Type `/send <TMNT player's name> Donatello` in the server console.
  Expected: Donatello can be selected straight away in the pause menu.
- [ ] **Step 6:** Commit: `feat(tmnt): BizHawk client and pure client logic`.

---

### Task 7: The area selector (Lua) and area savestates

**Files:**
- Modify: `lua/tmnt_area_select.lua`
- Create (not in git): `savestates/area1.State` … `area6.State`

**Interfaces:**
- Consumes: `MAILBOX_BASE` and the magic value from `ram.py`. The addresses are written as constants at the top of the Lua script with a comment pointing to `ram.py`.
- Produces: the load counter `MAILBOX+1` is incremented by 1 (mod 256) right after every successful `savestate.load`.

- [ ] **Step 1:** Create savestates for Area 1–6, all taken right after the area intro with all four turtles free.
  - Later areas are reached by writing the area number with the probe script if Task 1 found such an address, otherwise by playing up to them.
  - Write down in `docs/research/tmnt-ram.md` how each state was created.
- [ ] **Step 2:** Extend the script.
  - Select+Up/Down opens and closes a menu drawn with `gui.text`. It lists Area 1–6 and marks locked areas.
  - The menu does not open if the magic byte (`MAILBOX+3`) is missing, that is, if the client is not connected. The text "Connect the AP client" is then shown.
  - A selects an area. If its bit in the pass bitmask (`MAILBOX+0`) is set, the savestate is loaded. Then `MAILBOX+1` is incremented and the magic byte is written back (the savestate overwrites RAM).
  - All area states have Leo active. Solved 2026-10-31: writing `$0067` before HP is safe (`lua/tmnt_turtle_swap_test.lua`), so the client switches to an owned turtle during a full sync and then captures Leo.
  - Done 2026-10-31: `lua/tmnt_area_select.lua` with the automated test `lua/tmnt_area_select_test.lua` (33/33). The whole chain with server, connector, selector and client has been run through `tools/e2e_run.py`. Steps 3–5 below are covered automatically, but a manual test with a real controller remains. Continue and a new game also count as loads (see `docs/research/tmnt-ram.md`).
  - The counter must never become 0 (255 → 1).
  - After a boss win the game moves on to the next area by itself (`$0048` N−1 → N), even without that area's pass. The selector must detect this (the area byte changes without the counter having changed) and send the player back to the menu, after the client has had time to see the boss win (at least one client tick, about 1 s).
  - The mailbox is at `$0388–$038B` (TAS-confirmed). Keep the Lua constants in step with `ram.py`. The client reads 0 as "no area loaded yet", because the area byte `$0048` is also 0 at startup.
- [ ] **Step 3:** Do a manual test with a connected client that has passes 1 and 3, but no Missile Pack and Rope Pack.
  Expected: only Area 1 can be selected.
- [ ] **Step 4 (Review Focus 3):** Try to select Area 3.
  Expected: nothing loads and the text "Locked" is shown for 2 seconds.
- [ ] **Step 5:** Load Area 1.
  Expected: within one second, only the turtles you own have full HP, and the rest are captured (the client has done a full sync).
- [ ] **Step 6:** Commit: `feat: area select menu with pass gating`.

---

### Task 8: ROM patch and ROM validation

**Files:**
- Create: `apworld/tmnt/rom.py`, `test/test_rom.py`
- Modify: `apworld/tmnt/__init__.py` (`generate_output`)

**Interfaces:**
- Produces:
  - `class TMNTProcedurePatch(APProcedurePatch, APTokenMixin)`: `game = "Teenage Mutant Ninja Turtles"`, `hash = "c14e760c4d5a086e4186d2e1fc9b7743"`, `patch_file_ending = ".aptmnt"`, `result_file_ending = ".nes"`, `procedure = [("apply_tokens", ["token_data.bin"])]`.
  - `write_patch(world: TMNTWorld, patch: TMNTProcedurePatch) -> None`: writes the tag `b"TMNTAP"` plus 6 bytes of the seed name to a free ROM location found in Task 1. If the offset was not found in the spike: look for an area of `0xFF` in the last PRG bank and document it in `ram.py` as `ROM_TAG_OFFSET`.
  - `validate_rom` in Task 6 reads `ROM_TAG_OFFSET` in the `"PRG ROM"` domain.

- [ ] **Step 1:** Write the test `test_patch_writes_tag`. Run `write_patch` on a patch object and check with `patch.get_token_binary()` that it contains a `WRITE` token at `ROM_TAG_OFFSET` with data starting with `b"TMNTAP"`. The test does not need a real ROM.
- [ ] **Step 2:** Run the test.
  Expected: FAIL.
- [ ] **Step 3:** Implement `rom.py` and `generate_output`, which writes `<outfilebase>.aptmnt` to `output_directory`.
- [ ] **Step 4:** Run the tests.
  Expected: PASS. Then generate a seed and open the `.aptmnt` from the launcher.
  Expected: a patched `.nes` is created and the BizHawk client accepts it (`validate_rom` = True). Now run Task 6, step 5.
- [ ] **Step 5:** Commit: `feat(tmnt): procedure patch with ROM tag`.

---

### Task 9 (only if `PICKUPS_PERSISTENT` is True): Pickups as locations

**Files:**
- Modify: `locations.py`, `regions.py`, `rom.py`, `client_logic.py`, `client.py`, `ram.py`
- Test: `test/test_pool.py`, `test/test_client_logic.py`

**Interfaces:**
- Produces:
  - `PICKUP_LOCATIONS: dict[str, tuple[int, int]]` (name → (area, ROM offset)), with 20–30 selected locations from tmnt_rando's `tables/item_pointers.txt`. Copy the addresses and give the source in a comment. The locations are chosen in Task 1, step 4.
  - Location IDs from `8_870_200`.
  - With `include_pickups` on, pizza is added to the pool so that the number of items still matches the number of locations.
  - `write_patch` sets the item type `0x08` (scroll) on pickups that hold AP items. That is the spec's marker for the MVP, and the scroll's effect comes along with it.
  - `pickup_checks(ram_flags: bytes) -> set[str]` in `client_logic.py`.

- [ ] **Step 1:** Test that `test_pool_matches_locations` still passes with `{"include_pickups": True}`, and that `pickup_checks` maps a set flag to the right name.
- [ ] **Step 2:** Run the tests.
  Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run the tests.
  Expected: PASS.
- [ ] **Step 5:** Do a manual test: pick up a marked scroll and check that the check shows up in the server console.
- [ ] **Step 6:** Commit: `feat(tmnt): optional pickup locations`.

---

### Task 10: Player YAMLs and bulk generation

**Files:**
- Create: `players/alttp.yaml`, `players/tmnt.yaml`, `tools/gen_many.py`

**Interfaces:**
- Produces: `python tools/gen_many.py --count 200 --players players/ --ap Archipelago/` prints `ok=<n> failed=<m>` and exits with code 0 only if `failed == 0`.

- [ ] **Step 1:** Write the YAML files according to Global Constraints. ALttP: `mode: open`, `goal: ganon`, `non_local_items: [Hookshot, Flippers, Moon Pearl]`. TMNT: `start_turtle: raphael`, `non_local_items` according to Global Constraints.
- [ ] **Step 2:** Write `gen_many.py`. It runs `Generate.py` in a subprocess with `--seed <i>` for i = 1..count and counts failures. Output goes to `output/` (gitignored).
- [ ] **Step 3:** Run `python tools/gen_many.py --count 200 ...`.
  Expected: `ok=200 failed=0`. Also run it with `start_area: area_3`.
- [ ] **Step 4:** Check in 5 spoiler logs that at least one TMNT pass ends up behind ALttP progression and that at least one ALttP item is on a TMNT boss.
- [ ] **Step 5:** Commit: `feat: player yamls and bulk generation check`.

---

### Task 11: Stream setup and dress rehearsal

**Files:**
- Create: `docs/runbook.md`

- [ ] **Step 1:** Write `runbook.md`. It should cover:
  - start order: MultiServer → SNI + SNES emulator + SNI client → BizHawk + connector + `tmnt_area_select.lua` + BizHawkClient,
  - the OBS scenes "Hyrule", "Sewers (transition)" and "New York",
  - the stinger transition "pizza-wipe",
  - hotkeys: one key that pauses the active emulator and switches scene,
  - what to do after a crash: restart the client and load the latest area state.
- [ ] **Step 2:** Do a dress rehearsal. Play a whole seed on the stream machine and note the total time, softlocks and unclear points in the runbook's checklist.
  Expected: the seed can be completed, both goals are reached and the time is 1.5–2.5 hours. Otherwise: adjust `MISSILE_REFILL` and `ROPE_REFILL`, `start_area` or ALttP's `crystals_needed_for_gt` and do a new dress rehearsal.
- [ ] **Step 3:** Commit: `docs: stream runbook and rehearsal results`.

---

## Deviation from the spec

The spec's fallback for locations (R2) says "boss wins and Area completions". The boss win *is* the end of an area, so the plan instead uses **boss win + area entrance** (5 + 5 = 10 locations). That is enough for TMNT's 10 progression items (3 turtles, 4 passes and 3 tools) without needing pickups.

## Outside this plan (per the spec)

Automatic portal via ALttP room detection, `pizza_traps`, `easy_tmnt`, a custom AP item sprite in TMNT, MSU-1, enemy shuffle and track B (one ROM in SMZ3 style).
