# Tools for the player and the stream

These are the tools in the repo. The background and priorities are in `docs/research/tmnt-ammo-and-trackers.md`. This page is the basis for building the stream package.

## In BizHawk (TMNT)

Load `lua/tmnt_stream.luases` in the BizHawk 2.11 Lua console (File → Open Session). It starts the Archipelago connector and `lua/tmnt_area_select.lua` together. Then start `BizHawkClient` from the Archipelago launcher.

| Buttons | What happens |
|---|---|
| Select+Up | opens the area menu; locked areas are grey |
| Up/Down, A | picks and loads an area |
| B or Select+Down | closes the menu (not possible when the menu was forced open after a boss or on a new game) |
| Select+Left | hides or shows the HUD row |

**The HUD row** at the top shows LEO RAPH MIKE DON, MISSILE ROPE SCUBA (white = have, grey = missing) and BOSS x/3. It switches to GO MODE when Technodrome is in logic.

**Messages:** when an item arrives, the client shows "Got Rope Pack from Link" or "Found Leonardo" in BizHawk's message area, bottom left of the window. It shows up in the OBS window capture. The font has no å/ä/ö, so the text uses plain letters only. Confirmed with a window screenshot during the e2e test 2026-10-31.

## OBS: the go mode panel

Add `tools/obs/go-mode.html` as a Browser source with a local file. Add the parameters to the URL:

```
file:///C:/Project/tmntalttp/tools/obs/go-mode.html?server=ws://localhost:38281&alttp=Link&tmnt=Turtles
```

- **The panel:**
  - **Hyrule:** dungeon bosses x/10, and DONE when Ganon is defeated.
  - **New York:** turtles x/4, tools, passes, bosses x/3, GO MODE, and DONE when Shredder is defeated.
  - **ALttP items** are shown with the standard icons from the ALttP pack for PopTracker, which the community and ESA recognise. The panel has no Zelda icons of its own. They were tried and removed 2026-10-31 by the owner's decision.
- The icons (the ten Zelda dungeon bosses, the turtles, tools, passes and Area bosses) come from `tools/icons.py`, which turns the ChatGPT-made sheets in `art/icons/` into 32x32 pixel art. What you have is in colour; what is missing shows its grey "-off" variant.
- **All text shown on stream is in English:** the panel, the BizHawk menu (SELECT AREA, Locked, Connect the AP client), the messages ("Got X from Y", "Found X") and the OBS text "Into the sewers...".
- It connects as a read-only Tracker client and does not affect the game.
- With `&demo=1` it shows made-up values without a server, and `&layout=row` puts the cards side by side.
- **The panel is vector-based:** the text is HTML, and the icons are SVG from `tools/icons.py`, with each pixel as a square. The page scales itself to the source size with CSS `zoom`. The base size is 670×340, and 1330×225 with `layout=row`. Tried in OBS 32.2.2 at several sizes, and it was sharp at all of them.
- **Change the size in the source, not on the canvas:**
  1. Right-click the panel → Properties → Width/Height.
  2. Right-click again → Transform → Reset Transform, so it is shown at 1:1.

  Dragging the corners of the frame makes OBS stretch a finished image, and the panel turns blurry. That was why it was blurry before: it was drawn at 900×240 and squeezed down to 670 px with the "point" filter (reported by the owner 2026-10-31).
- **Sizes in the collection:** Hyrule and New York use 670×340. Sewers has its own source at 1005×510. The trackers are scaled with "bicubic", the games still with "point".
- ALttP crystals are not shown in the panel. They are logic events without an ID and are shuffled between dungeons. The runner sees them on the in-game map.
- Tested 2026-10-31 against a local MultiServer, both with a TMNT seed (`/send` and `/send_location` gave live updates up to GO MODE) and with a full ALttP+TMNT seed. Not tested in OBS.

## Hints and player files

- `players/tmnt.yaml` has `start_hints` for Leonardo, Michelangelo, Donatello, Missile Pack and Rope Pack, so the path to go mode is visible from the start.
- Both player files have `progression_balancing: 75`.
- During the stream, the host can run `/hint Turtles <item>` from the server console, for example as a donation goal. `/send` works as an emergency exit.
- The spoiler log (host.yaml `spoiler: 3`) contains the playthrough and belongs with the production, off screen.

## Start everything with one command

```
powershell -ExecutionPolicy Bypass -File tools\start_stream.ps1 -Seed output\<folder>\AP_<seed>.zip
```

The script patches the ROMs if they are missing and copies them to the fixed names `alttp-stream.sfc` and `tmnt-stream.nes`. That way the BizHawk windows get the same title whatever the seed, and the OBS collection finds them. If the port is already in use, the script stops. It then starts MultiServer in its own console window, where `/send` and `/hint` are typed, followed by SNI, the game swap (`tools/game_swap.py`, own console window), BizHawk with ALttP and `lua/alttp_stream.luases` (SNI's Lua connector and the swap script), BizHawk with TMNT and `lua/tmnt_stream.luases` (the connector, the area menu and the swap script), SNI Client, BizHawk Client and two PopTracker windows: the ALttP pack for Link and our TMNT pack for Turtles. Finally it prints the panel's address for OBS. Tried 2026-10-31 with a new seed: Link and Turtles connected as players and PopTracker as tracker. With `-NoTracker` the script skips PopTracker.

## The start menu (start.cmd)

`start.cmd` in the repo folder opens a menu where you choose with a number, so nobody needs PowerShell. Behind the menu is `tools/menu.ps1`.

1. **Create a seed:** runs Generate.py with `players/` and puts the result in `output/seeds`.
2. **Start a session:** you choose a seed; Enter gives the newest. The menu runs `tools/start_stream.ps1` and, after 20 seconds, the check.
3. **Check before going live:** runs `tools/preflight.py`. It gives one line per part, OK, WARN or FAIL, and a fix under each problem. It checks:
   - the installation;
   - the server and the slots, which it reads as a Tracker;
   - SNI;
   - both BizHawk windows and their titles;
   - the TCP connections BizHawk ↔ SNI and BizHawk ↔ BizHawk Client;
   - that both clients and both PopTrackers are connected to the server;
   - the game swap and the Lua scripts;
   - in OBS: scene collection, scenes and transition.
4. **Stop the session:** closes BizHawk gently first, so the Zelda save file is written, and then PopTracker, the clients, the server and SNI.

Tried 2026-10-31 by driving the menu with a script: seed created, session started, the check gave OK on everything except that OBS was not running, and the session stopped cleanly.

## The Zelda save file

`tools/bizhawk_saves.py` is run by the start script before BizHawk starts. The behaviour of BizHawk 2.11.1 was tested by hand 2026-10-31.

- **Autosave:** "AutosaveSaveRAM" is turned on, once a minute (3600 frames). Without it, the save file only reaches disk when BizHawk closes normally, so a crash loses the whole session.
- **After a crash:** the autosave is written to `alttp-stream.AutoSaveRAM.SaveRAM`, but BizHawk only reads it if the regular `alttp-stream.SaveRAM` is missing. If the autosave is newer, the script copies it over the regular file. The old one is kept as `.before-recovery`.
- **One save file per seed:** every seed runs as `alttp-stream.sfc`, and BizHawk names the save file after the ROM. The previous seed's save file is therefore parked as `alttp-stream.<seed>.SaveRAM` and this seed's is put back. `alttp-stream.seed` says which seed the file belongs to.

## Item notices

`tools/game_swap.py` follows the server as a Tracker. When an item arrives for the game in the background, a line is written to `output/swap/<system>-notice.txt` for the game in the foreground. `lua/game_swap.lua` shows it with `gui.addmessage`, bottom left for two seconds, for example "Zelda got Hookshot" in TMNT. The area menu writes `NES-event.txt` when the client opens a new pass, and that becomes "TMNT: Area 3 is open" in whichever game is being played.

Tried live 2026-10-31: a check on the server gave "Zelda got Bombs (3)" in the TMNT window after about 0.5 seconds.

## Swapping games

- **Select+Start** on the controller pauses the game you are leaving (Start), brings up the other game's BizHawk window and switches the OBS scene with the pizza wipe. **Ctrl+Shift+Space** does the same from the keyboard, but without pausing. Alt+Tab and clicking also work, because OBS follows whichever game window is on top.
- **How it works:** `lua/game_swap.lua` runs in both BizHawks. On Select+Start it writes a token to `output/swap/<system>-request.txt`. `tools/game_swap.py` answers in `-ack.txt` and brings up the other window. With no answer within two seconds, BizHawk shows "Game swap: start tools\game_swap.py". The script also writes `-ready.txt` every ten seconds, so the helper can log when the controller swap is active in each game.
- **The pause:** in TMNT the info screen is shown. In ALttP the item menu opens, or the "Continue / Save and Quit" box with Continue preselected if Select got in first. Start takes you back from both. Tried 2026-10-31 with scripted presses in BizHawk.
- **OBS:** the scene switch goes through the OBS WebSocket server (Tools → WebSocket Server Settings → Enable). Port and password are read from OBS's own settings on the same computer. The scene only switches when OBS is showing Hyrule or New York, so the host's own scenes are left alone. With `-NoObsSwitch` only the windows are swapped.
- **Tried 2026-10-31:**
  - Unit tests against a fake OBS with a password.
  - Lua test in BizHawk for NES and SNES.
  - Full run with both stream sessions, SNI, the helper and the fake OBS: Select+Start in both directions, the hotkey, OBS following along, a host scene left untouched and closed games detected. Everything passed.
  - Real OBS 32.2.2 (WebSocket 5.7.4), tried the same evening with a session started from `start.cmd`:
    - The password was read automatically from OBS's settings.
    - Select+Start both ways and the hotkey made OBS switch between Hyrule and New York.
    - With Sewers showing, six swaps in a row went right, and OBS stayed on Sewers.
    - The window capture in the new scene was ready 0.3 seconds after the swap.
    - The check before going live gave "All set".
  - **PopTracker:** PopTracker writes its settings file when it closes, and sometimes the end of an older file is left after the JSON. PopTracker then asks about updates and does not connect. This happened twice. `tools/poptracker_config.py`, which the start script runs, repairs the file.

**On the stream computer:** BizHawk 2.11 shows its own line in the window, "Click the blue silhouette below for onboarding". It shows in the window capture, so click it away once before the stream.

## OBS: scene collection and pizza wipe

- `tools/obs/tmnt-alttp-scenes.json` is built by `tools/make_obs_collection.py` and imported in OBS under Scene Collection → Import. Rerun the script if the repo moves, because the paths are absolute.
- **Scenes:**
  - **Hyrule:** the ALttP window, the ALttP tracker (PopTracker with the standard icons) and the go mode panel.
  - **Sewers (transition):** sewer-green background, the text "Into the sewers...", the panel in the middle and both PopTracker windows.
  - **New York:** the TMNT window, the TMNT tracker and the panel.
- **Transition:** "Pizza-wipe", a stinger with `tools/obs/pizza_wipe.webm` (built by `tools/make_stinger.py`) and a transition point of 500 ms. A band of tomato sauce with rolling pizzas sweeps across and covers the whole picture in the middle.
- **Tried 2026-10-31 in OBS 32.0.4:**
  - The collection loaded without errors.
  - The Hyrule scene showed the ALttP game, the ALttP tracker and the panel live.
  - The stinger was found.
  - The collection is installed but not active. Your active collection was restored.
- **Must be on:** PopTracker draws black in window capture with hardware rendering. `software_renderer` is therefore set to true in `%APPDATA%\PopTracker\PopTracker.json`.
- **Still to fine-tune:** the cropping of BizHawk's menu and status bar (`crop_top` 21 and `crop_bottom` 22 px) and the size of the tracker boxes.

## The TMNT pack for PopTracker

`tools/make_poptracker_pack.py --install` builds `poptracker/tmnt-ap/` from the apworld's tables and installs the zip file in PopTracker.
- **Contents:** the four turtles, Missile Pack, Rope Pack, Scuba Kit, five numbered passes and five numbered bosses.
- **The "Item Tracker - AP" variant** lights up items when they are received and bosses when their location is checked.
- **Tried 2026-10-31:** the starting items, items sent with `/send` and a boss marked with `/send_location` lit up.

## Graphics

The overlay icons were made with ChatGPT for the project (sheets in `art/icons/`) and turned into 32x32 pixel art by `tools/icons.py`; the characters they show belong to their owners. The heart and the pizza are drawn in `tools/sprites.py`, as 16x16 pixel art. ALttP is shown as usual with the ALttP pack's icons in PopTracker. That is the ESA and community standard, and responsibility for Nintendo's graphics lies there. The panel and the TMNT PopTracker pack use the same icons.

## Installation (done and tested 2026-10-31 on the owner's computer)

| What | Version | Where | Source |
|---|---|---|---|
| ALttP ROM | JP 1.0, md5 `03a63945398191337e896e5771f77173` | `Archipelago\Zelda no Densetsu - Kamigami no Triforce (Japan).sfc`, headerless | `roms\Zelda no Densetsu.smc` with the 512 header bytes removed |
| SNI | v0.0.103 | `Archipelago\SNI\` (SNIClient starts it from there itself) | https://github.com/alttpo/sni/releases |
| Universal Tracker | Tracker_v0.3.8 | `Archipelago\custom_worlds\tracker.apworld` | https://github.com/FarisTheAncient/Archipelago/releases |
| PopTracker | v0.36.0 | `Downloads\PopTracker-0.36.0\` | https://github.com/black-sliver/PopTracker/releases |
| ALttP pack | v0.5.1 (stable; v0.5.2-beta10 exists) | `Downloads\PopTracker-0.36.0\packs\` | https://github.com/StripesOO7/alttp-ap-poptracker-pack/releases |
| OBS Studio | 32.0.4 | already installed | |

The downloaded originals are in `Downloads\ap-tools\`.

## The whole chain, tested 2026-10-31

A seed with both ALttP and TMNT was generated and patched from `players/` (seed 21). Everything below ran at the same time against the same local server:

1. `MultiServer.py <seed>.zip --host 127.0.0.1`
2. **ALttP:** `Archipelago\SNI\sni.exe`, BizHawk 2.11.1 with the patched `.sfc` and the Lua script `Archipelago\SNI\lua\Connector.lua`, and `SNIClient.py`. The client found SNI and BizHawk ("Attached to luabridge"), recognised the ROM and connected as Link.
3. **TMNT:** BizHawk 2.11.1 with the patched `.nes` and `lua/tmnt_stream.luases`, and `BizHawkClient.py`. The client connected as Turtles and sent the gifts from Turtle Lair, Magic Mirror and Flippers, to Link.
4. **PopTracker** for ALttP connected as Tracker for Link:
   ```
   poptracker.exe --load-pack ap_alltp --pack-variant "Map Tracker - AP" --ap-host localhost:38281 --ap-slot Link
   ```
   The first time, PopTracker asks about update checks and about the EmoTracker folder. Both are answered no in `%APPDATA%\PopTracker\PopTracker.json` (`check_for_updates` and `add_emo_packs` = false). PopTracker draws with OpenGL, so a screenshot via `PrintWindow` came out black. Check that the OBS window capture shows it.
5. **The go mode panel** showed both slots live: Hyrule 0/10, New York 1/4 turtles and 0/3 bosses.

## Trackers

- **Universal Tracker (TMNT)** works without a YAML, tested with `tracker.apworld` v0.3.8:
  - At start it lists the gifts, the Area 1 entrance and the Area 1 boss.
  - With the Area 4 pass and Rope Pack, Area 4 is added.
  - The folder `Archipelago\Players` must exist. Otherwise UT opens a hidden folder picker and hangs. The folder may be empty.
  - Start it from the Archipelago launcher ("Universal Tracker") and connect to `localhost:38281` as `Turtles`.
- **ALttP:** PopTracker with the ALttP pack, see above.
- **Item feed in OBS (optional):** Nic-del/Broadcast-Archipelago. Not tested here.
- **Own TMNT pack for PopTracker:** optional, about 1–2 days. See the report.
