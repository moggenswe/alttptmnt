# Softlock and logic risks for the TMNT slot (2026-10-31)

The question: can the player get stuck because something required cannot be reached, or because the game and the logic disagree? This is a review of the logic (`apworld/tmnt/rules.py`), the client, the area selector and the game. Most of it is tested. What is not tested is listed under "Still to do".

## Conclusion

No known path leaves the player permanently stuck in the TMNT part.

- **Nothing can be missed:** every TMNT location can be collected again.
- **Nothing runs out:** continues (through the ROM patch) and ammo with a pack never run out.
- **No ways around the passes:** areas without a pass cannot be reached.
- **No progress is missing from our area states:** they differ from a real playthrough only in throwing weapons, map state, score and a value set when the game starts.

What remains is for a human to play through the areas from our states, as a final check.

## 1. Can a required item become unreachable?

| Risk | Status | How it is protected |
|---|---|---|
| Fill places an item behind itself | Solved by AP | The rules are strict. Generation is tested with 30 and 20 seeds (fixed start) and 100 seeds (random starting turtle and starting area), all passed. The starting area gets its pass and its tools from the start. |
| A TMNT location can be missed forever | No | Bosses can be beaten again via the menu. Entrances are counted on every load. The Turtle Lair gifts are sent on connect. |
| Boss win or Shredder while the client is disconnected | Solved (7b681e2) | The selector writes the win to `$038E`, and the client sends it when it reconnects. That does not hold if you power-cycle before the client has read the byte, but then you can beat the boss again. |
| The logic requires less than the game | No | See the table below. The logic is everywhere as strict as the game or stricter. |

| Area | The game requires (TAS + ROM) | The logic requires |
|---|---|---|
| 1 | nothing | pass |
| 2 | nothing extra (Scuba Kit is an invented lock) | pass + Zora's Scuba Kit |
| 3 | missiles against roadblocks (TAS: 10 shots). Ropes are not used by the TAS (ropeless). | pass + Missile Pack + Rope Pack |
| 4 | ropes (TAS: 1 throw, one pickup of 3 in the level) | pass + Rope Pack |
| 5 | nothing extra | pass; the boss requires Donatello (design choice) |
| 6 | nothing extra | all four turtles + 3 cleared bosses |

The TAS data confirms that missiles are only used in Area 3 and ropes only in Area 4.

## 2. Can the player get stuck in the game itself?

| Situation | What happens |
|---|---|
| All owned turtles are captured | Game over, then CONTINUE. The area restarts, and the owned turtles are free again. The original game only gives two continues: at the third game over you end up on the title screen. The ROM patch (`rom.py`, PRG `$1CD24`) always jumps to the continue screen. Tested with five game overs in a row, both on the original ROM (over after the third) and the patched ROM (continue every time). Without the patch the selector would still force the menu open on a new game, so it was not a softlock, just a detour via the title screen. |
| Ammo runs out | Anyone who has a pack is refilled when the counter is at 0. The game's own pickups in Area 3 and 4 also respawn. |
| The game moves on to a locked area after a boss | The menu is forced open and cannot be closed until an unlocked area has been loaded. Tested. |
| New game from the title screen (END or reset) | The menu is forced open, and no area is played without a pass. Tested. |
| A state is missing or was made in a different BizHawk | The menu shows "(missing)" or "Could not load Area N". Nothing is half-loaded and the load is not counted. Tested for a missing file. |
| The active turtle is not owned (all states have Leo) | The client switches to an owned turtle and then captures Leo. Tested. |

## 3. Leaks outside the logic

None of these lock the player in, but they make items worth less.

- **The game's own rescue:** from Area 3 on, you can rescue one captured turtle per area. The client now captures every turtle you do not own as soon as its HP is not 0 (7b681e2). That also applies to continue and a new game.
- **Missiles and ropes in the level:** they only exist in Area 3 and 4, and you only get there with the respective pack. The leak is therefore closed by the menu.

## 4. Area states versus a real playthrough

Our states come from a new game where the area byte has been rewritten. So whatever a real playthrough has set before the area is missing. The test method (`lua/tmnt_state_flags_check.lua`, `tools/state_flags_check.py`):
- Play TAS 4543M in BizHawk 2.6.1.
- When the area byte changes, write our states' values into the bytes the TAS carries into the area.
- See whether the TAS still clears the area on exactly the same frame.

A desync only means that the game reads the byte somewhere. It does not mean the area becomes impossible.

Every difference the game reads has been traced to a single byte, over some 60 TAS runs:

| Byte | What it is | Where the game reads it | Progress? |
|---|---|---|---|
| `$0073`–`$0076` | probably throwing weapon type per turtle: `$0076` was set on the same frame Donatello picked up a weapon, `$0074` when Raph did | Area 3–6 | No. Our states have no weapons, like a new game. |
| `$0614` | toggles 0/1/2 already in Area 1 and looks like a state flag on the map | Area 3–4 | No |
| `$C2`–`$C4`, `$C8`–`$CA` | **score and high score**. `$C2` counts up in tens when enemies die, and the init routine for a new game (ROM 0x1C66B) resets `$C2`–`$C4` along with continues, HP, ammo and weapons. `$C4`/`$CA` became 1 when the score passed 100,000 in Area 4. | Area 5–6 | No |
| `$0055` | set once at frame 145 when the game starts (2 in the TAS, 4 in our states; we pressed Start one frame off) and never changes after that, probably a random seed | Area 5 | No |
| `$007B`, `$007C` | look like progress (follow the area number, a growing bitmask) | nowhere | No |

With these bytes left untouched, the TAS keeps exact sync in Area 2, 3, 4, 5 and 6, even though every other byte the TAS carried over has been overwritten with our states' values. So our states lack no progress that the game reads along the TAS route. Score and random seed can make enemies behave a little differently than in the TAS, but that does not lock anything.

## 5. Still to do

1. **Play each area from its state up to and including the boss**, as a final check. The TAS test only covers the TAS route through each area.
2. **Make the states in the BizHawk version used on the stream.** States from other versions do not load, and the menu then says so.
3. **The full seed with ALttP** is not tested here, because the ALttP ROM is missing on this computer. The ALttP logic is Archipelago's own (open, no glitches).
4. **The game's own rescue** has not been seen in BizHawk. The E2E test shows that the client captures a freed turtle again within ten frames.

## Test status 2026-10-31

- 134 unit tests
- The area selector test 40/40, in BizHawk 2.11.1
- The E2E chain with server, BizHawk, selector and client passed. It also covers a boss win while the client is off, a freed turtle and the on-screen message.
- 150 generated seeds without errors
- Some 60 TAS runs for area states, with results in `tas/4543M/flags/` (not in git)
