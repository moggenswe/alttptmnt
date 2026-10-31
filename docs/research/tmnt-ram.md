# TMNT (NES) – RAM map (spike, Task 1)

ROM: Teenage Mutant Ninja Turtles (USA).nes, md5 `5e24ccd733d15e42d847274e7add0a76`. Emulator: BizHawk (NES core), domain `RAM` unless stated otherwise.

Fill this in as you go. Once everything below is filled in, the values go into `apworld/tmnt/ram.py`, and `VERIFIED = True` is set there.

Sources: adelikat's and JXQ's RAM map (`files.tasvideos.org/gameresources/nes/tmnt/TMNT.xls`, the "RAM" tab, 2006–2010) and [the TASVideos page for TMNT](https://tasvideos.org/GameResources/NES/TeenageMutantNinjaTurtles). "Doc" means documented there. "Confirmed" means checked by us in BizHawk.

## Addresses

| What | Address | Values / behaviour | Status |
|---|---|---|---|
| Current area ("world number") | `$0048` | Area N = value + 1 (Area 1 = 0) | **Confirmed** (the pause screen shows AREA 1 when the value is 0) |
| Where in the game | `$001B` | 5 = end credits | Doc |
| Active turtle | `$0067` | 0 = Leo, 1 = Raph, 2 = Mike, 3 = Don. Writable: switches the turtle immediately | **Confirmed** (see "Switching the active turtle") |
| HP Leonardo | `$0077` | max 128 (`$80`), 16 per bar; captured = `00` | Doc (captured/free confirmed on Raph) |
| HP Raphael | `$0078` | as above | **Confirmed**: `00` made Raph captured |
| HP Michelangelo | `$0079` | as above; full = `$80` | **Confirmed**: `00` here emptied Mike's meter |
| HP Donatello | `$007A` | as above | Doc |
| Missile count | `$00BF` | | Doc |
| Rope count | `$00A7` | | Doc |
| Throwing weapon per turtle | `$00A8–$00AB` | Leo, Raph, Mike, Don | Doc |
| Defused bombs (Area 2) | `$007D` | | Doc |
| Paused | `$0094` | 3 when paused, 0 otherwise | Doc |
| Score / high score | `$C2`–`$C4` / `$C8`–`$CA` | `$C2` counts up in tens; reset on a new game (ROM 0x1C66B) | **Confirmed with TAS** (see `tmnt-softlock-risks.md`) |
| Throwing weapon type per turtle | `$0073`–`$0076` (likely) | set when a throwing weapon is picked up | TAS (not fully confirmed) |
| Start value | `$0055` | set once when the game starts, depends on the exact frame Start is pressed | TAS |
| Number of continues | `$0046` | Starts at 3 and counts down at each game over (ROM `$CD24`: `DEC $46` / `BNE continue` / `JMP slut`). When it reaches 0 the game is over, that is, at the third game over. `rom.py` patches the jump so continues are unlimited. The earlier claim "never runs out" came from a test that set the value to 0, and 0 counts down to 255. | **Confirmed** (`lua/tmnt_continue_test.lua`, 2026-10-31) |
| Boss win Area 1–5 | `$0048` counts up | No dedicated flag found. `$0048` goes N−1 → N exactly once per boss win (5 times over the whole TAS), when April's briefing for the next area begins | **Confirmed with TAS** (see "TAS analysis") |
| Shredder defeated | `$001B` = 5 | set when the text "You defeated Shredder" appears, about 31 s after the last hit, and stays for about 40 s. After that `$001B` becomes 0 and `$0048` 0 (title screen) | **Confirmed with TAS** (see "Shredder") |
| 4 free bytes (mailbox) | `$0388–$038B` | All of `$0388–$03AF` (40 bytes) never changes during the TAS; marker values there were never overwritten and the TAS synced all the way to Area 6. ~~`$07F0–$07F3`~~ is used by the game (became `44` in Area 1), and `$0778–$077F`/`$07F8–$07FF` are read by the game (the TAS desyncs in Area 3) | **Confirmed with TAS** |
| Free ROM space for the AP tag (PRG offset) | `0x1BE00` | 582 bytes of `0xFF` at `$1BD92–$1BFD7` (bank 6); the tag takes 70 bytes | Scanned from the ROM file |

## R1 – can a turtle be locked by setting its HP to the captured value?

Result: **YES** (2026-10-31). With Mike active, `$0078` (Raph) was set to `00`. On the pause screen Raph had no portrait or health meter and could not be selected, and Splinter said "Find and help your friend in this stage". So the game treats him as captured. Writing `00` to the *active* turtle triggers the death animation. The client only writes the captured value during a full sync right after an area load, so that should not happen, but it is tested in Task 7.

Correction (2026-10-31, `lua/tmnt_gameover_test.lua`): HP `00` kills nobody until an enemy hits the turtle. On the map nothing happens at all, and in the sewer the turtle stays standing until it takes damage. So the death animation in the R1 test came from a hit.

Release: **YES**. After `80` was written to `$0078`, Raph could be selected again immediately. So the client can release a turtle in the middle of an area.

## R2 – does the game remember collected pickups?

Result: **NO** (2026-10-31). A pizza in the first building in Area 1 was back after leaving and re-entering. `PICKUPS_PERSISTENT = False`, and Task 9 is dropped.

## MISSILE_REFILL / ROPE_REFILL

Missiles: the TAS picks up 10 in Area 3 (frame 20188) and fires all 10 before Area 4. So a regular player needs at least 10, probably more → suggestion `MISSILE_REFILL = 15`.

Ropes: the TAS has 0 ropes throughout Area 3 and picks up its first ones in Area 4 (3 of them, frame 30757, uses 1). That is the **ropeless** skip, a damage boost that is also done in real time, but only by the very best players (the owner, 2026-10-31). The logic therefore keeps "Area 3 requires Rope Pack". The number of ropes a regular player needs cannot be read from the TAS; `ROPE_REFILL` has to be found by playing.

## Other / surprises

- `$001B` (where in the game) = 4 on the pause screen in Area 1.
- The RAM map (TMNT.xls) has Raph and Mike swapped for health. The correct order follows the turtle number.

## Area savestates (Task 7 step 1)

Made 2026-10-31 in BizHawk 2.11.1 with `lua/tmnt_make_area_states.lua`. The result ends up in `savestates/area1.State` … `area6.State`, with a screenshot next to each file. The folder is not in git.

- **Method:** on a new game, `$0048` is set to 0 on the frame where `$001B` becomes 3. The area loads a few frames later. If N−1 is written to `$0048` on that frame and the two following ones, the game loads Area N instead. The screenshots show the right area for all six: the starting island, the dam, the city with the Party Wagon, Area 4, Area 5 and the inside of the Technodrome. Each state is saved 120 frames after the load.
- **Starting point:** the states come from a new game. All four turtles have full HP, Leo is active and there are no weapons.
- **Solved risk:** if the player does not have Leo, who is active in all states, the client first switches `$0067` to an owned turtle and then captures Leo (see "Switching the active turtle").
- **Not tested:** that each area can be played to the end from such a state, for example if something is only set when the previous boss is defeated.
- **Versions:** the states only work in the BizHawk version that created them. 2.11.1 refuses to load states from 2.6.1 ("doesn't contain sync settings … Loadstate cancelled"). So remake them in the version used on the stream.

## TAS 4543M (DreamYao, BizHawk 2.6.1) as a reference

The TASVideos publication 4543M is in `tas/4543M/` (not in git). It only syncs in BizHawk 2.6.1, which is in `Downloads\BizHawk-2.6.1-win-x64`. In 2.11.1 it gets stuck in Area 1. The movie's ROM sha1 is `89adf2d9…` for the whole .nes file, the same as our ROM.

`lua/tmnt_tas_states.lua` (run with `--movie`) logged when `$0048` counts up. That happens when April's briefing for the next area begins:

| Frame | `$0048` becomes | Area that begins |
|---|---|---|
| 5499 | 1 | Area 2 |
| 18596 | 2 | Area 3 |
| 30041 | 3 | Area 4 |
| 46072 | 4 | Area 5 |
| 49799 | 5 | Area 6 |

The boss wins come shortly before these frames. That makes the movie useful for finding a boss flag: take a RAM snapshot before and after the boss's last hit and compare. The movie ends with `$001B` = 4, that is, before the end credits.

## TAS analysis: boss win, mailbox, missiles (2026-10-31)

Done with TAS 4543M in BizHawk 2.6.1 (`--movie`). Scripts: `lua/tmnt_tas_ram_dump.lua` (RAM every 5th frame + every change to known addresses), `tools/analyze_tas_ram.py` and `lua/tmnt_tas_mailbox_check.lua`. Raw data in `tas/4543M/ramdump/` (not in git).

- **Boss flag:** no byte changes exactly once per area, and no byte stays still for 5–30 s before each area change and then flips. The best signal is therefore the area change itself: `$0048` goes N−1 → N once per boss win and never otherwise during the TAS. It happens when April's briefing for the next area begins, that is, a while after the boss win itself.
  - **Consequence for Task 7:** after a boss win the game moves on to the next area by itself, even if the player lacks its pass. The area selector or the client has to catch the `$0048` change (without a preceding savestate load) and send the player back to the menu.
  - **Shredder:** see the "Shredder" section below; `$001B` = 5 is confirmed.
- **Mailbox:** 23 contiguous ranges (at least 4 bytes, the stack `$0100–$01FF` excluded) never changed after frame 200. The marker value `A7` was written on frame 200 in eleven of them:
  - Overwritten by the game (frame 673, at the start of Area 1): `$03F7–$03F9`, `$049F`, `$04CF`, `$0618–$0627`, `$064C–$064F`, `$06B1–$06B7`.
  - Read by the game: markers in `$0778–$077F` and `$07F8–$07FF` make the TAS desync in Area 3.
  - Safe: `$0388–$03AF` and `$0600–$0603`, `$060A–$0610` — no overwrites, and the TAS reaches Area 6 on exactly the same frames.
  - **Suggestion:** `MAILBOX_BASE = 0x0388`.
  - **Limitation:** the TAS does not cover everything (game over, the continue screen and the pause menu are barely used), and writes of the same value (`00` → `00`) do not show up in a dump.

## Switching the active turtle (`$0067`), 2026-10-31

Done in BizHawk 2.11.1 from `savestates/area1.State` (Leo active) with `lua/tmnt_turtle_swap_test.lua`. Images and the RAM log end up in `savestates/swap_test/`.

- **`$0067` = 1 and Leo's HP = `00`, on the same frame or one frame apart:** no death animation. The pause menu shows Raph selected and Leo without a portrait, and Splinter says "Find and help your friend". So the game treats Leo as captured.
- **On the map:** the figure keeps Leo's blue colour until you go in somewhere. Down in the sewer the turtle has a red bandana and sai, that is, Raph.
- **Inside the sewer:** the switch works the same way. The colours change at the next pause or room change, and until then Leo's colours are shown.
- **Consequence for the client:** during a full sync the client can first switch to an owned turtle and then capture the one on screen. This is built into `client_logic.full_sync_writes`, and so the risk "Leo active in all states" in Task 7 is gone.

## Game over and continue, 2026-10-31

Done in BizHawk 2.11.1 with `lua/tmnt_gameover_test.lua`. From `area1.State` a mailbox was written, the game was paused, and then the enemies in the first sewer were left to kill all four turtles.

- **The mailbox** `$0388–$038B` survived pause, game over, the continue screen and the restart of the area.
- **Continue restarts the area on the map, and all four turtles get full HP**, even the ones that were captured. The load counter does not change, so the client notices nothing. That is why `lua/tmnt_area_select.lua` counts the counter up when `$0046` has changed and all four have full HP again. The client then does a full sync.
- **`$0046`** counts down at game over, before you choose. ~~With `$0046` = 0 the value became 255 and CONTINUE was offered anyway, so continues never run out.~~ That was wrong: the game ends when the counter *reaches* 0, that is, at the third game over in a normal game. Writing 0 before a game over gives 255, which is why it looked unlimited. Fixed with a ROM patch, see the "Number of continues" row above.
- **Pause** (`$0094`: 1 → 2 → 3) does not touch the mailbox.
- **END and a new game from the title screen** were not tested directly. A new game passes `$001B` = 3, which the area states never do, so the selector then forces the menu open. That is covered by the test in `lua/tmnt_area_select_test.lua`, which does `client.reboot_core()`.

## The area selector and the whole chain, 2026-10-31

- **`lua/tmnt_area_select.lua`:** Select+Up opens the menu, Select+Down or B closes it, Up/Down moves and A loads. The game's buttons are held back while the menu is open. Drawn with `gui.drawText`, which does not show in `client.screenshot` but does show in the window.
- **`lua/tmnt_area_select_test.lua`** tests the selector without a player or client: 33 checks in BizHawk 2.11.1, all passed. It covers:
  - missing magic,
  - a locked area ("Locked"),
  - loading all six areas,
  - that the counter skips 0,
  - a forced menu after a boss win into a locked area, and counting up into an unlocked one,
  - a real game over with continue,
  - a new game after a restart.
- **`tools/e2e_run.py`** runs the whole chain locally:
  - MultiServer on 127.0.0.1,
  - BizHawk 2.11.1 with `lua/tmnt_e2e.luases`, where the AP connector and `lua/tmnt_e2e_driver.lua` run at the same time,
  - `BizHawkClient.py --nogui`.

  With seed 11 (`output/tmnt_only/tmnt.yaml`) every step passed:
  - the client connects and writes magic and the pass mask,
  - Area 1 loads from the menu while the connector runs (Task 2: `savestate.load` from another script does not disturb the connector),
  - full sync makes Raph active and captures Leo and Mike,
  - entrance check, then `/send Turtles Donatello`, after which Donatello has full HP within a second,
  - Area 3 is locked,
  - a boss win (`$0048` 0 → 1) sends "Area 1 - Boss", and after that the selector counts the counter up.
- **Savestates from the clean ROM work with the patched one.** The ROM tag sits in unused space. So the same area states can be used for every seed.

## Missiles and ropes exist in the levels, 2026-10-31

The game has its own pickups: the TAS picks up 10 missiles in Area 3 (frame 20188) and 3 ropes in Area 4 (frame 30757). StrategyWiki mentions 3 ropes in building F in Area 3. According to the TASVideos forum, Area 4 has a rope section with three gaps.

**Open design question:** "Area 3 requires Missile Pack and Rope Pack" only stops the selector. Inside the level the player can pick up the game's own missiles and ropes even without a pack, and the client only writes 0 during a full sync. Either that is enough, or the client should keep the count at 0 without a pack. That decision is the owner's. `ROPE_REFILL` = 5 is enough for at least one rope section with three gaps.

## Shredder, 2026-10-31

Done with `lua/tmnt_tas_ending.lua` in BizHawk 2.6.1. The script plays TAS 4543M up to 30 frames before the end, stops the movie (otherwise BizHawk pauses at the end of the movie, and then the script stands still), feeds in the buttons of the last 30 frames and then lets the game run without input. Stopping only one frame before the end lost the last hit, and then Shredder took Donatello.

| Frame | Event |
|---|---|
| 56264 | movie over, last hit fed in (`$001B` = 4, `$0048` = 5) |
| 58123 | `$001B` 4 → 5, "You defeated Shredder" |
| 60527 | `$001B` 5 → 0, `$0048` 5 → 0, title screen |

The client's goal (`SHREDDER_DEFEATED` = (`$001B`, 5) and the Area 6 bit) therefore has plenty of time: the signal stays for about 40 s.
