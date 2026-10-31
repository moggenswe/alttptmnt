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

- **Panelen:**
  - **Hyrule:** dungeon-bossar x/10 och DONE när Ganon är besegrad.
  - **New York:** sköldpaddor x/4, verktyg, pass, bossar x/3, GO MODE, och DONE när Shredder är besegrad.
  - **ALttP:s föremål** visas med de vanliga ikonerna i ALttP-packen till PopTracker, som communityn och ESA känner igen. Panelen har inga egna Zelda-ikoner. De provades och togs bort 2026-10-31 på Oscars beslut.
- TMNT-ikonerna och hjärtana är egen pixelgrafik från `tools/sprites.py`, inga spelspritar. Det man har lyser, och det som saknas är grått och dämpat.
- **All text som syns på streamen är engelsk:** panelen, BizHawk-menyn (SELECT AREA, Locked, Connect the AP client), meddelandena ("Got X from Y", "Found X") och OBS-texten "Into the sewers...". Dokumentationen är fortfarande svensk.
- Den ansluter som en skrivskyddad Tracker-klient och påverkar inte spelet.
- Med `&demo=1` visas påhittade värden utan server, och `&layout=row` lägger korten bredvid varandra.
- Panelen ritas i 670×290 och visas i 1:1 i scenerna. Tidigare ritades den i 900×240 och pressades ihop till 670 px med filtret "point", vilket gjorde texten suddig och hackig (påpekat av Oscar 2026-10-31). Ikonerna, som är 64 px, visas nu i exakt 32 px. Trackrarna skalas med "bicubic", spelen fortfarande med "point".
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

Skriptet patchar ROM:arna om de saknas och kopierar dem till de fasta namnen `alttp-stream.sfc` och `tmnt-stream.nes`. Då får BizHawk-fönstren samma titel oavsett seed, och OBS-samlingen hittar dem. Om porten redan används avbryts skriptet. Sedan startar det MultiServer i ett eget konsolfönster, där `/send` och `/hint` skrivs, följt av SNI, spelbytet (`tools/game_swap.py`, eget konsolfönster), BizHawk med ALttP och `lua/alttp_stream.luases` (SNI:s Lua-connector och bytesskriptet), BizHawk med TMNT och `lua/tmnt_stream.luases` (connectorn, områdesmenyn och bytesskriptet), SNI Client, BizHawk Client och två PopTracker-fönster: ALttP-packen för Link och vår TMNT-pack för Turtles. Till sist skriver det ut panelens adress för OBS. Det provades 2026-10-31 med ett nytt seed: Link och Turtles anslöt som spelare och PopTracker som tracker. Med `-NoTracker` hoppar skriptet över PopTracker.

## Startmenyn (start.cmd)

`start.cmd` i repomappen öppnar en meny där man väljer med en siffra, så ingen behöver PowerShell. Bakom menyn ligger `tools/menu.ps1`.

1. **Create a seed:** kör Generate.py med `players/` och lägger resultatet i `output/seeds`.
2. **Start a session:** man väljer seed, där Enter ger det nyaste. Menyn kör `tools/start_stream.ps1` och efter 20 sekunder kontrollen.
3. **Check before going live:** kör `tools/preflight.py`. Den ger en rad per del, OK, WARN eller FAIL, och en åtgärd under varje problem. Den kollar:
   - installationen;
   - servern och slottarna, som den läser som Tracker;
   - SNI;
   - båda BizHawk-fönstren och deras titlar;
   - TCP-kopplingarna BizHawk ↔ SNI och BizHawk ↔ BizHawk Client;
   - att båda klienterna och båda PopTracker är anslutna till servern;
   - spelbytet och Lua-skripten;
   - i OBS: scensamling, scener och övergång.
4. **Stop the session:** stänger BizHawk varsamt först, så att Zeldas sparfil skrivs, och därefter PopTracker, klienterna, servern och SNI.

Provat 2026-10-31 genom att styra menyn med ett skript: seed skapat, session startad, kontrollen gav OK på allt utom att OBS inte var igång, och sessionen stoppades rent.

## Zeldas sparfil

`tools/bizhawk_saves.py` körs av startskriptet innan BizHawk startar. Uppförandet hos BizHawk 2.11.1 provades för hand 2026-10-31.

- **Autosparning:** "AutosaveSaveRAM" sätts på, med en gång i minuten (3600 bildrutor). Utan den hamnar sparfilen på disk först när BizHawk stängs normalt, så en krasch tappar hela passet.
- **Efter en krasch:** autosparningen skrivs till `alttp-stream.AutoSaveRAM.SaveRAM`, men BizHawk läser den bara om den vanliga `alttp-stream.SaveRAM` saknas. Är autosparningen nyare kopierar skriptet den över den vanliga filen. Den gamla behålls som `.before-recovery`.
- **En sparfil per seed:** alla seeds körs som `alttp-stream.sfc`, och BizHawk döper sparfilen efter ROM:en. Förra seedets sparfil parkeras därför som `alttp-stream.<seed>.SaveRAM` och det här seedets läggs tillbaka. `alttp-stream.seed` anger vems filen är.

## Föremålsnotiser

`tools/game_swap.py` följer servern som Tracker. När ett föremål kommer till spelet i bakgrunden skrivs en rad i `output/swap/<system>-notice.txt` för spelet i förgrunden. `lua/game_swap.lua` visar den med `gui.addmessage`, längst ner till vänster i två sekunder, till exempel "Zelda got Hookshot" i TMNT. Områdesmenyn skriver `NES-event.txt` när klienten öppnar ett nytt pass, och det blir "TMNT: Area 3 is open" i det spel man spelar.

Provat live 2026-10-31: en kontroll på servern gav "Zelda got Bombs (3)" i TMNT-fönstret efter cirka 0,5 sekunder.

## Byta spel

- **Select+Start** på handkontrollen pausar spelet man lämnar (Start), tar fram det andra spelets BizHawk-fönster och byter OBS-scen med pizza-wipen. **Ctrl+Shift+Space** gör samma sak från tangentbordet, men utan paus. Alt+Tab och klick fungerar också, eftersom OBS följer det spelfönster som ligger överst.
- **Så fungerar det:** `lua/game_swap.lua` körs i båda BizHawk. Vid Select+Start skriver det en token i `output/swap/<system>-request.txt`. `tools/game_swap.py` svarar i `-ack.txt` och tar fram det andra fönstret. Utan svar inom två sekunder visar BizHawk "Game swap: start tools\game_swap.py". Skriptet skriver dessutom `-ready.txt` var tionde sekund, så att hjälpprogrammet kan logga när kontrollbytet är igång i respektive spel.
- **Pausen:** i TMNT visas informationsskärmen. I ALttP öppnas föremålsmenyn, eller rutan "Continue / Save and Quit" med Continue förvalt om Select hann före. Start tar en tillbaka från båda. Provat 2026-10-31 med skriptade tryck i BizHawk.
- **OBS:** scenbytet sker via OBS WebSocket-server (Tools → WebSocket Server Settings → Enable). Port och lösenord läses ur OBS:s egna inställningar på samma dator. Scenen byts bara när OBS visar Hyrule eller New York, så värdens egna scener lämnas i fred. Med `-NoObsSwitch` byts bara fönster.
- **Provat 2026-10-31:**
  - Enhetstester mot en låtsas-OBS med lösenord.
  - Lua-test i BizHawk för NES och SNES.
  - Helhetskörning med båda stream-sessionerna, SNI, hjälpprogrammet och låtsas-OBS: Select+Start i båda riktningarna, snabbtangenten, OBS som följer med, en värdscen som lämnas orörd och stängda spel som märks. Allt gick igenom.
  - Riktig OBS 32.2.2 (WebSocket 5.7.4), provad samma kväll med en session startad via `start.cmd`:
    - Lösenordet lästes automatiskt ur OBS:s inställningar.
    - Select+Start åt båda hållen och snabbtangenten fick OBS att växla mellan Hyrule och New York.
    - Med Kloak uppe gick sex byten i rad rätt, och OBS stannade på Kloak.
    - Fönsterfångsten i den nya scenen var klar 0,3 sekunder efter bytet.
    - Kontrollen före sändning gav "All set".
  - **PopTracker:** PopTracker skriver sin inställningsfil när den stängs, och ibland blir slutet av en äldre fil kvar efter JSON:en. Då frågar PopTracker om uppdateringar och ansluter inte. Det hände två gånger. `tools/poptracker_config.py`, som startskriptet kör, lagar filen.

**På streamdatorn:** BizHawk 2.11 visar en egen rad i fönstret, "Click the blue silhouette below for onboarding". Den syns i fönsterfångsten, så klicka bort den en gång innan streamen.

## OBS: scensamling och pizza-wipe

- `tools/obs/tmnt-alttp-scenes.json` byggs av `tools/make_obs_collection.py` och importeras i OBS under Scene Collection → Import. Kör om skriptet om repot flyttas, eftersom sökvägarna är absoluta.
- **Scener:**
  - **Hyrule:** ALttP-fönstret, ALttP-trackern (PopTracker med de vanliga ikonerna) och go mode-panelen.
  - **Kloak (övergång):** kloakgrön bakgrund, texten "Into the sewers...", panelen i mitten och båda PopTracker-fönstren.
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

TMNT-grafiken, hjärtat och pizzan är ritade för projektet i `tools/sprites.py`, som 16x16 pixelkonst. ALttP visas som vanligt med ALttP-packens ikoner i PopTracker. Det är ESA:s och communityns standard, och ansvaret för Nintendos grafik ligger där. Det finns ingen fritt licensierad TMNT-fan art: figurerna tillhör Nickelodeon, så fan art kan inte licensieras fritt, och sökningen hittade bara TMNT-spritar utan licens. Det enda med CC0 var generiska ninjor och sköldpaddor. Panelen, PopTracker-packen och pizza-wipen använder alla samma bilder.

## Installation (gjord och provad 2026-10-31 på Oscars dator)

| Vad | Version | Var | Källa |
|---|---|---|---|
| ALttP-ROM | JP 1.0, md5 `03a63945398191337e896e5771f77173` | `Archipelago\Zelda no Densetsu - Kamigami no Triforce (Japan).sfc`, utan header | `roms\Zelda no Densetsu.smc` med de 512 header-bytena borttagna |
| SNI | v0.0.103 | `Archipelago\SNI\` (SNIClient startar den själv därifrån) | https://github.com/alttpo/sni/releases |
| Universal Tracker | Tracker_v0.3.8 | `Archipelago\custom_worlds\tracker.apworld` | https://github.com/FarisTheAncient/Archipelago/releases |
| PopTracker | v0.36.0 | `Downloads\PopTracker-0.36.0\` | https://github.com/black-sliver/PopTracker/releases |
| ALttP-pack | v0.5.1 (stabil; v0.5.2-beta10 finns) | `Downloads\PopTracker-0.36.0\packs\` | https://github.com/StripesOO7/alttp-ap-poptracker-pack/releases |
| OBS Studio | 32.0.4 | redan installerat | |

Nedladdade original ligger i `Downloads\ap-tools\`.

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
