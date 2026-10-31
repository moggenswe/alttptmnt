# Verktyg för spelaren och streamen

Det här är verktygen som finns i repot. Bakgrunden och prioriteringen står i `docs/research/tmnt-ammo-och-tracker.md`. Den här sidan blir underlag när paketet för streamen byggs.

## I BizHawk (TMNT)

Ladda `lua/tmnt_stream.luases` i BizHawk 2.11:s Lua-konsol (File → Open Session). Den startar Archipelagos connector och `lua/tmnt_area_select.lua` samtidigt. Starta sedan `BizHawkClient` från Archipelago-launchern.

| Knappar | Vad som händer |
|---|---|
| Select+Upp | öppnar areamenyn; låsta areor är gråa |
| Upp/Ned, A | väljer och laddar en area |
| B eller Select+Ned | stänger menyn (går inte när menyn har tvingats upp efter en boss eller vid nytt spel) |
| Select+Vänster | döljer eller visar HUD-raden |

**HUD-raden** högst upp visar LEO RAPH MIKE DON, MISSILE ROPE SCUBA (vitt = har, grått = saknas) och BOSS x/3. Den växlar till GO MODE när Technodrome är i logik.

**Meddelanden:** när ett föremål kommer visar klienten "Fick Rope Pack av Link" eller "Hittade Leonardo" i BizHawks meddelandefält, nere till vänster i fönstret. Det syns i OBS:s fönsterfångst. Typsnittet saknar å/ä/ö, så texten använder bara vanliga bokstäver. Bekräftat med en fönsterbild under e2e-testet 2026-10-31.

## OBS: go mode-panelen

Lägg till `tools/obs/go-mode.html` som en Browser-källa med lokal fil. Lägg till parametrarna i URL:en:

```
file:///C:/Project/tmntalttp/tools/obs/go-mode.html?server=ws://localhost:38281&alttp=Link&tmnt=Turtles
```

- Panelen visar Hyrule (dungeon-bossar x/10, KLART när Ganon är besegrad) och New York (sköldpaddor x/4, bossar x/3, GO MODE, KLART när Shredder är besegrad).
- Ikonerna är egenritad pixelgrafik direkt i filen, inga spelspritar: fyra sköldpaddshuvuden i pannbandsfärgerna, fem boss-markeringar, Missile Pack, Rope Pack, Scuba Kit, fem kloaklock för passen och tio hjärtbehållare för Hyrules dungeon-bossar. Det man har lyser, och det som saknas är grått och dämpat.
- Den ansluter som en skrivskyddad Tracker-klient och påverkar inte spelet.
- Med `&demo=1` visas påhittade värden utan server, och `&layout=column` lägger korten under varandra.
- ALttP:s kristaller syns inte i panelen. De är logikhändelser utan ID och slumpas mellan dungeons. Runnern ser dem på kartan i spelet.
- Testad 2026-10-31 mot en lokal MultiServer, både med ett TMNT-seed (`/send` och `/send_location` gav live-uppdatering till GO MODE) och med ett helt ALttP+TMNT-seed. Inte testad i OBS.

## Hints och spelarfiler

- `players/tmnt.yaml` har `start_hints` för Leonardo, Michelangelo, Donatello, Missile Pack och Rope Pack, så att vägen till go mode syns från start.
- Båda spelarfilerna har `progression_balancing: 75`.
- Värden kan under streamen köra `/hint Turtles <föremål>` från serverkonsolen, till exempel som donationsmål. `/send` fungerar som nödutgång.
- Spoilerloggen (host.yaml `spoiler: 3`) innehåller playthrough och hör hemma hos produktionen, utanför bild.

## Starta allt med ett kommando

```
powershell -ExecutionPolicy Bypass -File tools\start_stream.ps1 -Seed output\<mapp>\AP_<seed>.zip
```

Skriptet patchar ROM:arna om de saknas och kopierar dem till de fasta namnen `alttp-stream.sfc` och `tmnt-stream.nes`. Då får BizHawk-fönstren samma titel oavsett seed, och OBS-samlingen hittar dem. Om porten redan används avbryts skriptet. Sedan startar det MultiServer i ett eget konsolfönster, där `/send` och `/hint` skrivs, följt av SNI, BizHawk med ALttP och SNI:s Lua-connector, BizHawk med TMNT och `lua/tmnt_stream.luases`, SNI Client, BizHawk Client och två PopTracker-fönster: ALttP-packen för Link och vår TMNT-pack för Turtles. Till sist skriver det ut panelens adress för OBS. Det provades 2026-10-31 med ett nytt seed: Link och Turtles anslöt som spelare och PopTracker som tracker. Med `-NoTracker` hoppar skriptet över PopTracker.

**På streamdatorn:** BizHawk 2.11 visar en egen rad i fönstret, "Click the blue silhouette below for onboarding". Den syns i fönsterfångsten, så klicka bort den en gång innan streamen.

## OBS: scensamling och pizza-wipe

- `tools/obs/tmnt-alttp-scenes.json` byggs av `tools/make_obs_collection.py` och importeras i OBS under Scene Collection → Import. Kör om skriptet om repot flyttas, eftersom sökvägarna är absoluta.
- **Scener:**
  - **Hyrule:** ALttP-fönstret, ALttP-trackern och go mode-panelen.
  - **Kloak (övergång):** kloakgrön bakgrund, texten "Genom kloaken...", panelen i mitten och båda trackerna.
  - **New York:** TMNT-fönstret, TMNT-trackern och panelen.
- **Övergång:** "Pizza-wipe", en stinger med `tools/obs/pizza_wipe.webm` (byggd av `tools/make_stinger.py`) och övergångspunkt 500 ms. Ett band av tomatsås med rullande pizzor sveper över och täcker hela bilden i mitten.
- **Provat 2026-10-31 i OBS 32.0.4:**
  - Samlingen laddades utan fel.
  - Hyrule-scenen visade ALttP-spelet, ALttP-trackern och panelen live.
  - Stingern hittades.
  - Samlingen ligger installerad men är inte aktiv. Din aktiva samling återställdes.
- **Måste vara på:** PopTracker ritar svart i fönsterfångst med hårdvarurendering. `software_renderer` är därför satt till true i `%APPDATA%\PopTracker\PopTracker.json`.
- **Kvar att finjustera:** beskärningen av BizHawks meny- och statusrad (`crop_top` 21 och `crop_bottom` 22 px) och trackerrutornas storlek.

## TMNT-packen till PopTracker

`tools/make_poptracker_pack.py --install` bygger `poptracker/tmnt-ap/` från apworldens tabeller och installerar zip-filen i PopTracker.
- **Innehåll:** de fyra sköldpaddorna, Missile Pack, Rope Pack, Scuba Kit, fem numrerade pass och fem numrerade bossar.
- **Varianten "Item Tracker - AP"** tänder föremål när de tas emot och bossar när deras plats kontrolleras.
- **Provat 2026-10-31:** startföremålen, föremål skickade med `/send` och en boss markerad med `/send_location` tändes.

## Grafik

All grafik är ritad för projektet i `tools/sprites.py`, som 16x16 pixelkonst: sköldpaddshuvuden, verktyg, pass, boss, hjärta och pizza. Det finns ingen fritt licensierad TMNT-fan art: figurerna tillhör Nickelodeon, så fan art kan inte licensieras fritt, och sökningen hittade bara TMNT-spritar utan licens. Det enda med CC0 var generiska ninjor och sköldpaddor. Panelen, PopTracker-packen och pizza-wipen använder alla samma bilder.

## Installation (gjord och provad 2026-10-31 på Oscars dator)

| Vad | Version | Var | Källa |
|---|---|---|---|
| ALttP-ROM | JP 1.0, md5 `03a63945398191337e896e5771f77173` | `Archipelago\Zelda no Densetsu - Kamigami no Triforce (Japan).sfc`, utan header | `roms\Zelda no Densetsu.smc` med de 512 header-bytena borttagna |
| SNI | v0.0.103 | `Archipelago\SNI\` (SNIClient startar den själv därifrån) | https://github.com/alttpo/sni/releases |
| Universal Tracker | Tracker_v0.3.8 | `Archipelago\custom_worlds	racker.apworld` | https://github.com/FarisTheAncient/Archipelago/releases |
| PopTracker | v0.36.0 | `Downloads\PopTracker-0.36.0\` | https://github.com/black-sliver/PopTracker/releases |
| ALttP-pack | v0.5.1 (stabil; v0.5.2-beta10 finns) | `Downloads\PopTracker-0.36.0\packs\` | https://github.com/StripesOO7/alttp-ap-poptracker-pack/releases |
| OBS Studio | 32.0.4 | redan installerat | |

Nedladdade original ligger i `Downloadsp-tools\`.

## Hela kedjan, provad 2026-10-31

Ett seed med både ALttP och TMNT genererades och patchades från `players/` (seed 21). Allt nedan körde samtidigt mot samma lokala server:

1. `MultiServer.py <seed>.zip --host 127.0.0.1`
2. **ALttP:** `Archipelago\SNI\sni.exe`, BizHawk 2.11.1 med den patchade `.sfc` och Lua-skriptet `Archipelago\SNI\lua\Connector.lua`, och `SNIClient.py`. Klienten hittade SNI och BizHawk ("Attached to luabridge"), kände igen ROM:en och anslöt som Link.
3. **TMNT:** BizHawk 2.11.1 med den patchade `.nes` och `lua/tmnt_stream.luases`, och `BizHawkClient.py`. Klienten anslöt som Turtles och skickade gåvorna från Turtle Lair, Magic Mirror och Flippers, till Link.
4. **PopTracker** för ALttP anslöt som Tracker för Link:
   ```
   poptracker.exe --load-pack ap_alltp --pack-variant "Map Tracker - AP" --ap-host localhost:38281 --ap-slot Link
   ```
   Första gången frågar PopTracker om uppdateringskontroll och om EmoTracker-mappen. Båda är besvarade med nej i `%APPDATA%\PopTracker\PopTracker.json` (`check_for_updates` och `add_emo_packs` = false). PopTracker ritar med OpenGL, så min skärmbild via `PrintWindow` blev svart. Kontrollera att OBS fönsterfångst visar den.
5. **Go mode-panelen** visade båda slottarna live: Hyrule 0/10, New York 1/4 sköldpaddor och 0/3 bossar.

## Trackers

- **Universal Tracker (TMNT)** fungerar utan YAML, provat med `tracker.apworld` v0.3.8:
  - Vid start listar den gåvorna, Area 1-ingången och Area 1-bossen.
  - Med Area 4-passet och Rope Pack tillkommer Area 4.
  - Mappen `Archipelago\Players` måste finnas. Annars öppnar UT en dold mappväljare och hänger. Mappen får vara tom.
  - Starta via Archipelago-launchern ("Universal Tracker") och anslut till `localhost:38281` som `Turtles`.
- **ALttP:** PopTracker med ALttP-packen, se ovan.
- **Föremålsflöde i OBS (valfritt):** Nic-del/Broadcast-Archipelago. Den är inte provad här.
- **Egen TMNT-pack till PopTracker:** valfri, cirka 1–2 dagar. Se rapporten.
