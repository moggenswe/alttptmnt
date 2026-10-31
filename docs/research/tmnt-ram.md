# TMNT (NES) – RAM-karta (spike, Task 1)

ROM: Teenage Mutant Ninja Turtles (USA).nes, md5 `5e24ccd733d15e42d847274e7add0a76`. Emulator: BizHawk (NES-core), domän `RAM` om inget annat står.

Fyll i allt eftersom. När allt nedan är ifyllt förs värdena in i `apworld/tmnt/ram.py`, och där sätts `VERIFIED = True`.

Källor: adelikats och JXQ:s RAM-karta (`files.tasvideos.org/gameresources/nes/tmnt/TMNT.xls`, fliken "RAM", 2006–2010) och [TASVideos sida för TMNT](https://tasvideos.org/GameResources/NES/TeenageMutantNinjaTurtles). "Dok" betyder dokumenterat där. "Bekräftat" betyder kontrollerat av oss i BizHawk.

## Adresser

| Vad | Adress | Värden / beteende | Status |
|---|---|---|---|
| Aktuell area ("world number") | `$0048` | Area N = värde + 1 (Area 1 = 0) | **Bekräftat** (pausskärmen visar AREA 1 när värdet är 0) |
| Var i spelet | `$001B` | 5 = eftertexter | Dok |
| Aktiv sköldpadda | `$0067` | 0 = Leo, 1 = Raph, 2 = Mike, 3 = Don. Går att skriva: byter sköldpadda direkt | **Bekräftat** (se "Byte av aktiv sköldpadda") |
| HP Leonardo | `$0077` | max 128 (`$80`), 16 per streck; fångad = `00` | Dok (fångad/fri bekräftat på Raph) |
| HP Raphael | `$0078` | som ovan | **Bekräftat**: `00` gjorde Raph fångad |
| HP Michelangelo | `$0079` | som ovan; full = `$80` | **Bekräftat**: `00` här tömde Mikes mätare |
| HP Donatello | `$007A` | som ovan | Dok |
| Antal missiles | `$00BF` | | Dok |
| Antal rep | `$00A7` | | Dok |
| Kastvapen per sköldpadda | `$00A8–$00AB` | Leo, Raph, Mike, Don | Dok |
| Desarmerade bomber (Area 2) | `$007D` | | Dok |
| Pausad | `$0094` | 3 vid paus, 0 annars | Dok |
| Poäng / high score | `$C2`–`$C4` / `$C8`–`$CA` | `$C2` räknas upp i tiotal; nollställs vid nytt spel (ROM 0x1C66B) | **Bekräftat med TAS** (se `tmnt-softlock-risker.md`) |
| Kastvapentyp per sköldpadda | `$0073`–`$0076` (trolig) | sätts när ett kastvapen plockas upp | TAS (inte helt bekräftat) |
| Startvärde | `$0055` | sätts en gång när spelet startar, beror på exakt frame för Start | TAS |
| Antal continues | `$0046` | Börjar på 3 och räknas ner vid varje game over (ROM `$CD24`: `DEC $46` / `BNE continue` / `JMP slut`). När den når 0 är spelet slut, alltså vid tredje game over. `rom.py` patchar hoppet så att continues blir obegränsade. Det tidigare påståendet "tar aldrig slut" kom från ett test som satte värdet till 0, och 0 räknas ner till 255. | **Bekräftat** (`lua/tmnt_continue_test.lua`, 2026-10-31) |
| Bossvinst Area 1–5 | `$0048` räknas upp | Ingen egen flagga hittad. `$0048` går N−1 → N exakt en gång per bossvinst (5 gånger på hela TAS:en), när Aprils genomgång inför nästa area börjar | **Bekräftat med TAS** (se "TAS-analys") |
| Shredder besegrad | `$001B` = 5 | sätts när texten "You defeated Shredder" visas, cirka 31 s efter sista slaget, och ligger kvar i cirka 40 s. Därefter blir `$001B` 0 och `$0048` 0 (titelskärmen) | **Bekräftat med TAS** (se "Shredder") |
| 4 lediga bytes (brevlåda) | `$0388–$038B` | Hela `$0388–$03AF` (40 byte) ändras aldrig under TAS:en; markörvärden där skrevs aldrig över och TAS:en synkade ända till Area 6. ~~`$07F0–$07F3`~~ används av spelet (blev `44` i Area 1), och `$0778–$077F`/`$07F8–$07FF` läses av spelet (TAS:en desynkar i Area 3) | **Bekräftat med TAS** |
| Ledigt ROM-utrymme för AP-taggen (PRG-offset) | `0x1BE00` | 582 byte `0xFF` på `$1BD92–$1BFD7` (bank 6); taggen tar 70 byte | Skannat ur ROM-filen |

## R1 – går det att låsa en sköldpadda genom att sätta HP till fångad-värdet?

Resultat: **JA** (2026-10-31). Med Mike aktiv sattes `$0078` (Raph) till `00`. På pausskärmen saknade Raph porträtt och hälsomätare och gick inte att välja, och Splinter sa "Find and help your friend in this stage". Spelet behandlar honom alltså som tillfångatagen. Att skriva `00` till den *aktiva* sköldpaddan utlöser dödsanimationen. Klienten skriver bara fångad-värdet vid full sync direkt efter en area-laddning, så det bör inte hända, men det testas i Task 7.

Korrigering (2026-10-31, `lua/tmnt_gameover_test.lua`): HP `00` dödar ingen förrän en fiende träffar sköldpaddan. På kartan händer ingenting alls, och i kloaken står hon kvar tills hon tar skada. Dödsanimationen i R1-testet kom alltså av en träff.

Frigivning: **JA**. Efter `80` på `$0078` gick Raph att välja igen direkt. Klienten kan alltså frige en sköldpadda mitt i en area.

## R2 – minns spelet upplockade pickups?

Resultat: **NEJ** (2026-10-31). En pizza i första byggnaden i Area 1 låg där igen efter ut- och ingång. `PICKUPS_PERSISTENT = False`, och Task 9 utgår.

## MISSILE_REFILL / ROPE_REFILL

Missiles: TAS:en plockar 10 i Area 3 (frame 20188) och skjuter alla 10 innan Area 4. En vanlig spelare behöver alltså minst 10, sannolikt fler → förslag `MISSILE_REFILL = 15`.

Ropes: TAS:en har 0 rep i hela Area 3 och plockar sina första i Area 4 (3 st, frame 30757, använder 1). Det är **ropeless**-skippet, en damage boost som också görs i realtid men bara av de allra bästa (Oscar, 2026-10-31). Logiken behåller därför "Area 3 kräver Rope Pack". Antalet rep en vanlig spelare behöver går inte att läsa ur TAS:en; `ROPE_REFILL` måste spelas fram.

## Övrigt / överraskningar

- `$001B` (var i spelet) = 4 på pausskärmen i Area 1.
- RAM-kartan (TMNT.xls) har Raph och Mike omkastade för hälsan. Rätt ordning följer sköldpaddsnumret.

## Area-savestates (Task 7 steg 1)

Gjorda 2026-10-31 i BizHawk 2.11.1 med `lua/tmnt_make_area_states.lua`. Resultatet hamnar i `savestates/area1.State` … `area6.State`, med en skärmdump bredvid varje fil. Mappen ligger inte i git.

- **Metod:** vid ett nytt spel sätts `$0048` till 0 på den frame där `$001B` blir 3. Arean laddas några frames senare. Om N−1 skrivs till `$0048` på den framen och de två följande laddar spelet Area N i stället. Skärmdumparna visar rätt area för alla sex: startön, dammen, staden med Party Wagon, Area 4, Area 5 och insidan av Technodrome. Varje state sparas 120 frames efter laddningen.
- **Utgångsläge:** statesen kommer från ett nytt spel. Alla fyra sköldpaddor har full HP, Leo är aktiv och inga vapen finns.
- **Löst risk:** om spelaren inte har Leo, som är aktiv i alla states, byter klienten först `$0067` till en ägd sköldpadda och fångar sedan Leo (se "Byte av aktiv sköldpadda").
- **Inte testat:** att varje area går att spela klart från en sådan state, till exempel om något sätts först när föregående boss besegras.
- **Versioner:** statesen fungerar bara i den BizHawk-version som skapade dem. 2.11.1 vägrar ladda states från 2.6.1 ("doesn't contain sync settings … Loadstate cancelled"). Gör dem därför om i den version som används på streamen.

## TAS 4543M (DreamYao, BizHawk 2.6.1) som referens

TASVideos-publikationen 4543M ligger i `tas/4543M/` (inte i git). Den synkar bara i BizHawk 2.6.1, som ligger i `Downloads\BizHawk-2.6.1-win-x64`. I 2.11.1 kör den fast i Area 1. Filmens ROM-sha1 är `89adf2d9…` för hela .nes-filen, samma som vår ROM.

`lua/tmnt_tas_states.lua` (körs med `--movie`) loggade när `$0048` räknas upp. Det sker när Aprils genomgång inför nästa area börjar:

| Frame | `$0048` blir | Area som börjar |
|---|---|---|
| 5499 | 1 | Area 2 |
| 18596 | 2 | Area 3 |
| 30041 | 3 | Area 4 |
| 46072 | 4 | Area 5 |
| 49799 | 5 | Area 6 |

Bossvinsterna ligger strax före dessa frames. Det gör filmen användbar för att hitta en bossflagga: ta en RAM-ögonblicksbild före och efter bossens sista träff och jämför. Filmen slutar med `$001B` = 4, alltså före eftertexterna.

## TAS-analys: bossvinst, brevlåda, missiles (2026-10-31)

Gjord med TAS 4543M i BizHawk 2.6.1 (`--movie`). Skript: `lua/tmnt_tas_ram_dump.lua` (RAM var 5:e frame + varje ändring av kända adresser), `tools/analyze_tas_ram.py` och `lua/tmnt_tas_mailbox_check.lua`. Rådata i `tas/4543M/ramdump/` (inte i git).

- **Bossflagga:** ingen byte ändras exakt en gång per area, och ingen byte står still i 5–30 s före varje areabyte för att sedan slå om. Bästa signalen är därför areabyten själv: `$0048` går N−1 → N en gång per bossvinst och aldrig annars under TAS:en. Det sker när Aprils genomgång inför nästa area börjar, alltså en stund efter själva bossvinsten.
  - **Följd för Task 7:** efter en bossvinst fortsätter spelet av sig själv till nästa area, även om spelaren saknar dess pass. Areaväljaren eller klienten måste fånga `$0048`-ändringen (utan föregående savestate-laddning) och skicka spelaren tillbaka till menyn.
  - **Shredder:** se avsnittet "Shredder" nedan; `$001B` = 5 är bekräftat.
- **Brevlåda:** 23 sammanhängande områden (minst 4 byte, stacken `$0100–$01FF` utesluten) ändrades aldrig efter frame 200. Markörvärdet `A7` skrevs på frame 200 i elva av dem:
  - Skrivs över av spelet (frame 673, i början av Area 1): `$03F7–$03F9`, `$049F`, `$04CF`, `$0618–$0627`, `$064C–$064F`, `$06B1–$06B7`.
  - Läses av spelet: markörer i `$0778–$077F` och `$07F8–$07FF` får TAS:en att desynka i Area 3.
  - Säkra: `$0388–$03AF` och `$0600–$0603`, `$060A–$0610` — inga överskrivningar, och TAS:en når Area 6 på exakt samma frames.
  - **Förslag:** `MAILBOX_BASE = 0x0388`.
  - **Begränsning:** TAS:en täcker inte allt (game over, continue-skärmen, pausmenyn används nästan inte), och skrivningar av samma värde (`00` → `00`) syns inte i en dump.

## Byte av aktiv sköldpadda (`$0067`), 2026-10-31

Gjort i BizHawk 2.11.1 från `savestates/area1.State` (Leo aktiv) med `lua/tmnt_turtle_swap_test.lua`. Bilder och RAM-logg hamnar i `savestates/swap_test/`.

- **`$0067` = 1 och Leos HP = `00`, på samma frame eller med en frames mellanrum:** ingen dödsanimation. Pausmenyn visar Raph vald och Leo utan porträtt, och Splinter säger "Find and help your friend". Spelet behandlar alltså Leo som fångad.
- **På kartan:** figuren behåller Leos blå färg tills man går in någonstans. Nere i kloaken har sköldpaddan rött pannband och sai, alltså Raph.
- **Inne i kloaken:** bytet fungerar likadant. Färgerna byts vid nästa paus eller rumsbyte, och fram till dess syns Leos färger.
- **Följd för klienten:** vid full sync kan klienten byta till en ägd sköldpadda först och sedan fånga den som syns. Det är inbyggt i `client_logic.full_sync_writes`, och risken "Leo aktiv i alla states" i Task 7 är därmed borta.

## Game over och continue, 2026-10-31

Gjort i BizHawk 2.11.1 med `lua/tmnt_gameover_test.lua`. Från `area1.State` skrevs en brevlåda, spelet pausades, och sedan fick fienderna i första kloaken döda alla fyra sköldpaddorna.

- **Brevlådan** `$0388–$038B` överlevde paus, game over, continue-skärmen och omstarten av arean.
- **Continue startar om arean på kartan, och alla fyra sköldpaddor får full HP**, även de som var fångade. Laddningsräknaren ändras inte, så klienten märker inget. Därför räknar `lua/tmnt_area_select.lua` upp räknaren när `$0046` har ändrats och alla fyra har full HP igen. Klienten gör då en full sync.
- **`$0046`** räknas ner vid game over, innan man väljer. ~~Med `$0046` = 0 blev värdet 255 och CONTINUE erbjöds ändå, så continues tar aldrig slut.~~ Det var fel: spelet slutar när räknaren *når* 0, alltså vid tredje game over i ett vanligt spel. Att skriva in 0 före ett game over ger 255, och därför såg det obegränsat ut. Rättat med en ROM-patch, se raden "Antal continues" ovan.
- **Paus** (`$0094`: 1 → 2 → 3) rör inte brevlådan.
- **END och nytt spel från titelskärmen** testades inte direkt. Ett nytt spel passerar `$001B` = 3, vilket areastatesen aldrig gör, så väljaren tvingar då upp menyn. Det täcks av testet i `lua/tmnt_area_select_test.lua`, som gör `client.reboot_core()`.

## Areaväljaren och hela kedjan, 2026-10-31

- **`lua/tmnt_area_select.lua`:** Select+Upp öppnar menyn, Select+Ned eller B stänger den, Upp/Ned flyttar och A laddar. Spelets knappar hålls tillbaka medan menyn är öppen. Ritat med `gui.drawText`, som inte syns i `client.screenshot` men syns i fönstret.
- **`lua/tmnt_area_select_test.lua`** testar väljaren utan spelare och klient: 33 kontroller i BizHawk 2.11.1, alla godkända. Det täcker:
  - magic saknas,
  - låst area ("Låst"),
  - laddning av alla sex areor,
  - att räknaren hoppar över 0,
  - tvingad meny efter bossvinst mot låst area, och uppräkning mot upplåst,
  - ett riktigt game over med continue,
  - nytt spel efter omstart.
- **`tools/e2e_run.py`** kör hela kedjan lokalt:
  - MultiServer på 127.0.0.1,
  - BizHawk 2.11.1 med `lua/tmnt_e2e.luases`, där AP-connectorn och `lua/tmnt_e2e_driver.lua` körs samtidigt,
  - `BizHawkClient.py --nogui`.

  Med seed 11 (`output/tmnt_only/tmnt.yaml`) gick alla steg igenom:
  - klienten ansluter och skriver magic och passmask,
  - Area 1 laddas från menyn medan connectorn kör (Task 2: `savestate.load` från ett annat skript stör inte connectorn),
  - full sync gör Raph aktiv och fångar Leo och Mike,
  - ingångscheck, sedan `/send Turtles Donatello`, varefter Donatello har full HP inom en sekund,
  - Area 3 är låst,
  - en bossvinst (`$0048` 0 → 1) skickar "Area 1 - Boss", och därefter räknar väljaren upp räknaren.
- **Savestates från den rena ROM:en fungerar med den patchade.** ROM-taggen ligger i oanvänt utrymme. Samma area-states kan alltså användas för varje seed.

## Missiles och rep finns i banorna, 2026-10-31

Spelet har egna upplockningar: TAS:en plockar 10 missiles i Area 3 (frame 20188) och 3 rep i Area 4 (frame 30757). StrategyWiki nämner 3 rep i byggnad F i Area 3. Enligt TASVideos-forumet har Area 4 en rep-sträcka med tre luckor.

**Öppen designfråga:** "Area 3 kräver Missile Pack och Rope Pack" stoppar bara väljaren. Inne i banan kan spelaren plocka spelets egna missiles och rep även utan pack, och klienten skriver bara 0 vid full sync. Antingen räcker det, eller så ska klienten hålla antalet på 0 utan pack. Det beslutet är Oscars. `ROPE_REFILL` = 5 räcker till minst en rep-sträcka med tre luckor.

## Shredder, 2026-10-31

Gjort med `lua/tmnt_tas_ending.lua` i BizHawk 2.6.1. Skriptet spelar TAS 4543M till 30 frames före slutet, stoppar filmen (BizHawk pausar annars vid filmslut, och då står skriptet still), matar in de sista 30 framesens knappar och låter sedan spelet gå utan input. Att stoppa bara en frame före slutet tappade sista slaget, och då tog Shredder Donatello.

| Frame | Händelse |
|---|---|
| 56264 | filmen slut, sista slaget inmatat (`$001B` = 4, `$0048` = 5) |
| 58123 | `$001B` 4 → 5, "You defeated Shredder" |
| 60527 | `$001B` 5 → 0, `$0048` 5 → 0, titelskärmen |

Klientens mål (`SHREDDER_DEFEATED` = (`$001B`, 5) och Area 6-biten) har alltså gott om tid: signalen ligger kvar i cirka 40 s.
