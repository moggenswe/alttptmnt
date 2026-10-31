# TMNT × A Link to the Past – meme randomizer for a speedrun marathon

Design spec and implementation plan. Status: **draft for review** (2026-10-31).

---

## 0. Understanding the brief

**What the owner has said**
- A "meme" project for a charity speedrun marathon. It should be **fun to watch and to play**, not perfect.
- The games are *A Link to the Past* (SNES) and *Teenage Mutant Ninja Turtles* (probably the first NES game).
- The model is SMZ3: two games, a shared item pool and transitions between the games.
- TMNT needs some form of gating and has to be tied to ALttP.

**Assumptions (please correct)**
- The marathon runs on a **PC emulator** and is streamed through OBS. No real SNES or FXPak hardware is needed.
- One person plays both games in a single race or showcase. So it is a solo run, not a multiworld between several players.
- The goal is a run of roughly **1.5–2.5 hours**, which fits a marathon schedule.
- There are a few weeks of evenings available, not several months.

**Success:** a seed that can be completed all the way, where the audience *sees* the crossovers between the games (portals, turtles turning up in Hyrule, Link items unlocking TMNT levels), and where no softlock ruins the broadcast.

---

## 1. Research findings

### 1.1 tmnt_rando targets the NES version
- `randomizer.py` calls `run_interface(ALL_OBJECTS, snes=False)`, and `tables/master.txt` identifies the ROM as `TMNT_NA` with md5 `c14e760c4d5a086e4186d2e1fc9b7743`. That is the **NES original** (Konami/Ultra, 1989, MMC1).
- The repo has existed since 2018 and is about 300 lines of Python on top of abyssonym's `randomtools`. It has three flags:
  - `i` randomizes items (pizza, shuriken, boomerang, scroll, invincibility, **Missile 0x0C, Rope 0x0D**),
  - `m` randomizes enemies,
  - `e` randomizes entrances, but only within a stage, and the README itself calls it "unsafe".
- What is worth taking from it: **the ROM addresses of all 243 item placements** (`tables/item_pointers.txt`) and the entrance tables. That is a ready-made list of "locations" for TMNT. The rest of the code is not worth building on.
  - *Note:* tmnt_rando only changes *what* sits at a location in the ROM. It says nothing about whether the game remembers that a pickup has been collected (see risk R2).
- Missiles and ropes are already **natural keys** in the game. In Area 3 the Party Wagon needs missiles to blow up roadblocks and rope to get across gaps. tmnt_rando even guarantees that both are in Area 1 when entrances are randomized.

### 1.2 Is there a SNES version?
- **Officially, no.** TMNT 1 was never released on the SNES. *Turtles in Time* (SNES) is a completely different game, a beat-'em-up with no structure that can be gated.
- **Unofficially, yes.** Infidelity released a *native* NES→SNES port of TMNT 1 in October 2025, with hidden MSU-1 features for audio and video (intro, cartoon) and turtle switching with X ([Time Extension, Oct 2025](https://www.timeextension.com/news/2025/10/teenage-mutant-ninja-turtles-is-the-next-nes-classic-to-get-a-native-snes-port), download via archive.org). That means the idea of **a single SNES ROM basically holds up**.
  - *Not verified:* how the port is distributed (patch or ROM), whether the source code is open and what its ROM layout is. That decides all of track B below.

### 1.3 How SMZ3 fits two games into one ROM
From `tewtal/alttp_sm_combo_randomizer_rom` (`banks.txt`, `src/main.asm`, `src/sm/transition.asm`):
1. **ExHiROM merge.** ALttP's banks go at `$00–$1F`, SM's at `$80+`, and randomizer tables, extra graphics and free space at `$40–$5F`. Each game gets a `hirom.asm` patch that moves its pointers.
2. **Shared SRAM.** Both games keep their inventory in SRAM. When one game receives an item from the other game, it is written to the other game's SRAM area ("foreign items").
3. **The transition** (`transition_to_sm`): turn off IRQ/NMI/HDMA, turn on forced blank, reset the SPC so the sound engine can be reloaded, **DMA a ready-made "template" of VRAM and WRAM for the target game from ROM**, load the target game's save file and enter through a door or portal in the target game.
4. **Logic and generation** are done in C# (`Randomizer.SMZ3`). Each portal has its own access rule, for example `CanAccessMiseryMirePortal` and `CanAccessNorfairLowerPortal`, and the fill is an ordinary assumed fill over both worlds.
5. **MSU-1** is supported through `sm/msu.asm` and `spc.asm`. SA-1 is not used at all.

### 1.4 ALttPDoorRandomizer
This is a Python fork of the classic ER/Berserker randomizer, with regions, rules, fill and ROM patching via `base2current.bps`. It is valuable as a **reference for ALttP logic**, but adds nothing this particular project needs: door shuffling only makes things harder for both the audience and the player. It has its own multiworld that is **not** Archipelago-compatible. The recommendation is *not* to build on it.

### 1.5 The hardware question in brief
| Question | Answer |
|---|---|
| Can a SNES run NES code? | The 65816 has a 6502 mode, but the PPU, APU and MMC1 mapper are completely different. Real-time NES emulation on a SNES does not work in practice. That is why a **port** is needed. |
| Emulation or porting? | With two ROMs you run two emulators on the PC, which is trivial. With one ROM you need a port, and one now exists (Infidelity). |
| MSU-1? | Fun but optional. The port already has MSU-1 hooks and SMZ3 has MSU-1 support. Emulators such as snes9x, bsnes and BizHawk run MSU-1. Nice for the showcase but not needed. |
| SA-1? | **Not needed.** Neither game uses it, and adding SA-1 would only complicate the memory mapping. |

---

## 2. Design options

### A. "Sewer Bridge" – two emulators and Archipelago ⭐ recommended
ALttP runs in a SNES emulator and TMNT (NES) in BizHawk, and both connect to a local Archipelago server. The player has two "slots" in the same seed (Archipelago's standard mode for a solo multiworld).
- **For free:** the ALttP world already exists in Archipelago with logic, fill, spoiler, tracker and item delivery via SNI.
- **To build:** a `tmnt.apworld` (locations, items and rules) and a BizHawk client that reads and writes TMNT RAM.
- **Portals:** a small orchestration script and OBS. When Link goes down into a "sewer", the stream switches scene to TMNT with a pizza-wipe as the transition, and the other way round.
- **Pros:** realistic in a few weeks, low risk, and generation and logic are right from the start.
- **Cons:** not a single ROM. The transition is a scene switch in OBS, not a real door in the game. Items can only have meaning in *one* of the games (see 3.3).

### B. "The SMZ3 clone" – one SNES ROM
Infidelity's SNES port of TMNT and ALttP are merged into one ExHiROM using SMZ3's transition technique: SRAM handoff, SPC reset and DMA of WRAM/VRAM templates. It needs its own generator, for example a fork of SMZ3's C#.
- **Pros:** the real "wow" feeling. Received TMNT items show up directly in ALttP's menu and the portal is a real door in the game.
- **Cons:** needs the port's source code or our own disassembly, relocation of both games, RAM conflicts, swapping sound engines and item graphics in both games. That is **3–6+ months** of hobby-level assembly work. There is a big risk it never gets finished, and the port is not our code (the licence and permission from Infidelity need to be sorted out).

### C. "Relay" – zero code
A regular ALttP randomizer and tmnt_rando run separately. The rule is that when you clear an ALttP dungeon you play the next TMNT area, and OBS switches.
- **Pros:** done in one evening.
- **Cons:** no shared item pool, and it is just two games one after the other. It is only good enough as an emergency fallback.

**Recommendation:** Build **A** for the marathon. Treat **B** as a follow-up project if A is a hit and Infidelity is on board. Keep **C** as plan B if time runs out.

---

## 3. Game design: how TMNT is gated

TMNT is linear (Area 1 → 6, with the Technodrome and Shredder last). We make it non-linear by **treating each Area as a dungeon** that you enter through a portal, and by making the turtles and tools items.

### 3.1 Building blocks
| Mechanic | How it works | Meme value |
|---|---|---|
| **Turtles as items** | You start with *one* random turtle (meme flag: always Raphael). The other three are "captured" and are somewhere in Hyrule. The game already has a captured state, so a turtle we have not found yet is set as captured when TMNT loads. | Very high: "Donatello found in Kakariko's chicken house!" |
| **Donatello's bo as an "ability"** | The logic counts Don as the requirement for a few hard bosses or rooms (long reach). No code needed, only rules. | Medium |
| **Area passes** (`Sewer Pass: Area 1–5`) | Required to enter Area N. There are five passes, and you start with one of them. Areas unlock in any order. Area 6 (Technodrome) has no pass but requires the condition in 3.4. | The backbone of progression |
| **Missiles / Ropes** | Progression items for Area 3 (Party Wagon). They replace tmnt_rando's guarantee. | Natural, easy to understand |
| **Dam diving gear** | Item required for Area 2 (the dam). Without it you cannot choose Area 2. | The audience loves to hate the dam |
| **Regular TMNT pickups** | Pizza, shuriken, boomerang and scroll go into the shared pool as filler in both directions. | A pizza in an ALttP chest |

### 3.2 Rewards that tie the games together in the other direction
- Every TMNT boss win is a *location* that can hold ALttP progression, for example the Hookshot behind Area 3's boss.
- Sewer portals in ALttP: **the Hyrule Castle sewers** (the theme is perfect), the Kakariko well and one in the Dark World. The portal *is* the menu for choosing an Area.

### 3.3 Items with a double meaning (track B only, or a later extension)
"Flippers unlock the dam" and "Hookshot = Rope" are the most fun, but in Archipelago an item belongs to *one* slot, and logic across two slots is not supported. In track A we therefore use **themed names** instead, for example calling the diving gear "Zora's Scuba Kit". If it should be at Zora's, that can be forced with Archipelago's `plando_items`, but it is optional. Real items with a double meaning require modelling both games as *one* world, the same way SMZ3 does.

### 3.4 Goal
- **Goal:** beat both Ganon *and* Shredder. In Archipelago each slot has its own goal, and the seed counts as finished when both slots are finished. The clock stops at the later of the two.
- The Technodrome (Area 6) requires all 4 turtles and 3 cleared Areas.
- **How the games are forced to interleave.** ALttP's crystals cannot be moved to TMNT, because Archipelago's ALttP world cannot shuffle dungeon rewards to other worlds (checked in `worlds/alttp/Options.py`). The interleaving is done instead with Archipelago's standard setting `non_local_items`:
  - The TMNT slot sets turtles, Area passes, missiles and ropes as `non_local_items`, so they can only end up in Hyrule.
  - The ALttP slot sets, for example, Hookshot, Flippers and Moon Pearl as `non_local_items`, so they can only end up in TMNT.
  - Effect: you cannot get far in either game without switching.
- Settings for the meme mode: `start_turtle: raphael`, `pizza_traps` (a "trap" that gives Link a pizza hat or inverted controls for 10 seconds) and `dam_timer_halved` (only for those who really want it).

### 3.5 Play time and difficulty
TMNT NES is hard, and the dam is notorious. To keep the broadcast from dying, each turtle gives a buffer (more "lives"). Missiles and ropes are handed out in reasonable amounts, and the `easy_tmnt` setting halves damage by having the client write to RAM.

---

## 4. Technical architecture for track A

```
┌─────────────── PC / stream ───────────────┐
│ SNES-emu (ALttP AP-ROM) ──SNI──┐           │
│                                 ├─ AP server (local)
│ BizHawk (TMNT NES) ──Lua──► TMNT client ─┘ │
│            ▲                       │       │
│            └── area menu/savestates│       │
│ Portal orchestrator ◄──────────────┘──► OBS (scene switch + pizza-wipe)
└───────────────────────────────────────────┘
```

**Units (each one can be tested on its own)**
1. **`tmnt.apworld`** (Python, Archipelago's API)
   - *Locations:* item pickups (the addresses from tmnt_rando's `item_pointers.txt`, plus filtering per Area) and one per boss win.
   - *Items:* 4 turtles (minus the starting turtle), 5 Area passes (minus the starting pass), missiles, ropes, the diving gear and filler. The number of missiles and ropes is decided once Area 3 has been tested.
   - *Rules:* Area passes, Area 3 requires missiles and ropes, Area 2 requires diving gear, Area 6 as in 3.4.
   - *ROM patch:* replace the pickup type at the locations that hold AP items, following tmnt_rando's method. The MVP uses an existing item, for example a scroll, as a marker, and the player also gets the scroll's effect. It is only a cosmetic bug. A custom sprite or palette is outside the MVP.
2. **The TMNT client** (Archipelago's BizHawk client framework)
   - *Read:* collected pickups, boss wins, current area and HP per turtle.
   - *Write:* received items (turtle freed, missiles/ropes/sub-weapons) and "captured" for missing turtles.
3. **Area selector / savestate loader.** A ready-made savestate at the start of each Area. When the player picks an unlocked Area, the state is loaded and the inventory is then injected. This gets around the linear progression without a ROM hack.
   - *Checked:* Archipelago's generic BizHawk connector (`data/lua/connector_bizhawk_generic.lua`) can only read and write memory, lock the emulator and show messages. It **cannot load savestates**.
   - The area selector therefore becomes **a small Lua script of our own** that runs in BizHawk next to the connector (BizHawk can run several scripts at once, and `savestate.load` is in the Lua API). The script reads which passes are unlocked from a memory address that the TMNT client writes to. So the client and the selector talk through the emulator's RAM and do not need to talk to each other directly.
   - Fallback if it misbehaves: write the area number to RAM and let the game's own area transition do the work. That needs more RAM research.
4. **The portal orchestrator.** It listens to the ALttP room via SNI. When the player enters a sewer room, it pauses the SNES emulator, asks OBS to switch scene and opens the area selector. On "Exit Sewer" in TMNT the reverse happens. **MVP:** a hotkey instead of room detection.

**Error handling:** the client must survive an emulator reset and restore the inventory from the AP server's state, which Archipelago clients do by default. The area selector never loads a locked Area.

**Testing:** generate about 200 seeds per settings profile (Archipelago's `Generate.py` validates that the seed can be completed). Do manual playthroughs of each Area start state, and do at least one full dress rehearsal on the stream machine.

---

## 5. An MVP that can be ready for the marathon

**In the MVP:**
- `tmnt.apworld` with locations for boss wins and, if risk R2 can be solved, a selection of safe pickups (about 20–30 of the 243).
- Items: 4 turtles, Area passes, missiles, ropes, diving gear and pizza filler.
- BizHawk client that reads boss wins and pickups and writes turtles and tools.
- Area selector via savestates.
- OBS hotkey for the "portal" with a pizza-wipe as the transition.
- Goal: Ganon + Shredder.
- ALttP: Archipelago's standard ALttP with simple settings (open mode, no doors, no ER).

**Outside the MVP (nice-to-have, in this order):** automatic portal via room detection, `pizza_traps`, a custom AP item sprite in TMNT, MSU-1 music, enemy shuffle in TMNT.

**Outside the project:** track B (one ROM) and items with a double meaning.

---

## 6. Rough effort (evenings/weekends, one person, some Python experience)

| Step | Effort |
|---|---|
| Set up Archipelago from source, ALttP via SNI, BizHawk | 1–2 days |
| Map TMNT RAM: turtle HP/captured, area, pickups, boss, inventory | 3–5 days *(biggest uncertainty)* |
| `tmnt.apworld`: items, locations, rules and patch | 3–4 days |
| BizHawk client and area selector (own Lua script for savestates) | 4–5 days |
| OBS portal: hotkey, transition, layout | 1 day |
| Seed testing, balancing, dress rehearsal | 3–5 days |
| **Total MVP** | **≈ 3–5 weeks of evenings** |
| Track B (one ROM, SMZ3 style) | 3–6+ months, depending on the port's source code |

## 7. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| R1: TMNT's RAM map is harder to find than expected, especially the captured state | Medium | Start with it (spike in week 1). |
| R2: TMNT has **no persistent flag** for collected pickups (items can reappear when you go back into a room), so the client does not know *which* pickup was taken | Medium–high | The spike decides. Fallback 1: the client recognises the pickup by room + object position + item type. Fallback 2: locations only on boss wins and Area completions (about 10–12 locations is enough for an MVP). |
| Savestate injection causes odd states, for example the wrong turtle active | Medium | Write the state only after the area intro. Test each Area separately. |
| TMNT gets too hard for the play time (the dam) | High | `easy_tmnt`, diving gear late in the logic, and practise the route beforehand. |
| Archipelago's API changes during the work | Low | Pin the Archipelago version. |
| Trouble with two emulators on the stream machine | Medium | Dress rehearsal on the same machine. Save the OBS profile. |
| The licence question around Infidelity's port (track B only) | – | Ask Infidelity before doing anything. |
| Spoilers or softlock live | Low–medium | Only use generated and validated seeds. Run a test seed all the way through. |

## 8. Open questions for the owner
1. **When is the marathon?** That decides whether the MVP is enough or whether there is time for automatic portals.
2. **Emulator or real hardware?** Everything above assumes an emulator.
3. **Who is playing?** A runner who knows TMNT can handle harder settings.
4. Is there Archipelago and Python experience in the team, or will it be learning from scratch?

## 9. Proposed first week (spike)
1. Install Archipelago from source and run an ALttP seed via SNI.
2. Open TMNT (NA, md5 as above) in BizHawk and find the RAM addresses for the turtles' HP/captured state and the current area. Also find out whether collected pickups are stored anywhere (risk R2).
3. Test that a Lua script of our own can run `savestate.load` while Archipelago's connector is running.
4. If (2) and (3) go well, track A is green and it is time to write the implementation plan. If R2 turns out badly, fallback 2 is used: only boss wins as locations.

---

## 10. Review log (2026-10-31)
Corrected after review against the sources:
- **Savestates:** Archipelago's BizHawk connector cannot load savestates. The area selector therefore becomes a Lua script of our own (4.3), and the effort has been raised.
- **Crystals:** having TMNT bosses give ALttP crystals is not possible in Archipelago. It has been replaced with `non_local_items` (3.4).
- **Area passes:** it said six passes, but Area 6 has no pass. The number has been corrected to five.
- **Pickups:** new risk R2, that collected pickups are not stored. The fallback is boss wins as locations.
- **Goal:** clarified how "both goals" works in Archipelago.
- **Verified:** that tmnt_rando targets the NES, that SMZ3 uses assumed fill and the ExHiROM layout, and that tmnt_rando has 243 pickup locations.
- **Still not verified:** how Infidelity's SNES port is distributed and whether the source code is open, and the full TMNT RAM map.

---
**Sources:** [aerinon/ALttPDoorRandomizer](https://github.com/aerinon/ALttPDoorRandomizer), [tewtal/SMZ3Randomizer](https://github.com/tewtal/SMZ3Randomizer), [tewtal/alttp_sm_combo_randomizer_rom](https://github.com/tewtal/alttp_sm_combo_randomizer_rom), [abyssonym/tmnt_rando](https://github.com/abyssonym/tmnt_rando), [Time Extension – TMNT native SNES port](https://www.timeextension.com/news/2025/10/teenage-mutant-ninja-turtles-is-the-next-nes-classic-to-get-a-native-snes-port), [Time Extension – announced Aug 2025](https://www.timeextension.com/news/2025/08/teenage-mutant-ninja-turtles-will-be-the-next-nes-classic-to-get-a-native-snes-port).
