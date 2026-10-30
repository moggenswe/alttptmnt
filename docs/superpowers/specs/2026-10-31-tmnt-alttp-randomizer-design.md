# TMNT × A Link to the Past – meme-randomizer för speedrun-maraton

Designspec och genomförandeplan. Status: **utkast för granskning** (2026-10-31).

---

## 0. Förståelse av uppdraget

**Det Oscar har sagt**
- Ett "meme"-projekt för ett välgörenhetsmaraton för speedrun. Det ska vara **roligt att titta på och spela**, inte perfekt.
- Spelen är *A Link to the Past* (SNES) och *Teenage Mutant Ninja Turtles* (troligen NES-ettan).
- Förebilden är SMZ3: två spel, en delad item-pool och övergångar mellan spelen.
- TMNT måste få någon form av gating och kopplas ihop med ALttP.

**Antaganden (rätta gärna)**
- Maratonet körs på **PC-emulator** och streamas via OBS. Det krävs ingen riktig SNES- eller FXPak-hårdvara.
- En person spelar båda spelen i ett och samma race eller showcase. Det är alltså en solo-körning, inte multiworld mellan flera spelare.
- Målet är att körningen tar ungefär **1,5–2,5 timmar**, vilket passar ett maraton-schema.
- Det finns några veckors kvällstid till förfogande, inte flera månader.

**Lyckat resultat:** en seed som går att slutföra hela vägen, där publiken *ser* korsningarna mellan spelen (portaler, sköldpaddor som dyker upp i Hyrule, Link-items som låser upp TMNT-nivåer), och där inget softlock sabbar sändningen.

---

## 1. Researchresultat

### 1.1 tmnt_rando gäller NES-versionen
- `randomizer.py` anropar `run_interface(ALL_OBJECTS, snes=False)`, och `tables/master.txt` identifierar ROM:en som `TMNT_NA` med md5 `c14e760c4d5a086e4186d2e1fc9b7743`. Det är **NES-originalet** (Konami/Ultra, 1989, MMC1).
- Repot har funnits sedan 2018 och består av cirka 300 rader Python ovanpå abyssonyms `randomtools`. Det har tre flaggor:
  - `i` slumpar items (pizza, shuriken, bumerang, scroll, invincibility, **Missile 0x0C, Rope 0x0D**),
  - `m` slumpar fiender,
  - `e` slumpar ingångar, men bara inom en stage, och READMEn kallar det själv "unsafe".
- Det som är värt att ta med sig: **ROM-adresserna för alla 243 item-placeringar** (`tables/item_pointers.txt`) och ingångstabellerna. Det är en färdig lista med "locations" för TMNT. Koden i övrigt är inte värd att bygga vidare på.
  - *Obs:* tmnt_rando ändrar bara *vad* som ligger på en plats i ROM:en. Den säger ingenting om huruvida spelet kommer ihåg att en pickup är upplockad (se risk R2).
- Missiles och ropes är redan **naturliga nycklar** i spelet. I Area 3 behöver Party Wagon missiles för att spränga vägspärrar och rep för att ta sig över luckor. tmnt_rando garanterar till och med att båda finns i Area 1 när ingångar slumpas.

### 1.2 Finns det en SNES-version?
- **Officiellt nej.** TMNT 1 släpptes aldrig till SNES. *Turtles in Time* (SNES) är ett helt annat spel, ett beat-'em-up utan någon struktur som går att gate:a.
- **Inofficiellt ja.** Infidelity släppte en *native* NES→SNES-port av TMNT 1 i oktober 2025, med dolda MSU-1-funktioner för ljud och video (intro, tecknad serie) och byte av sköldpadda med X ([Time Extension, okt 2025](https://www.timeextension.com/news/2025/10/teenage-mutant-ninja-turtles-is-the-next-nes-classic-to-get-a-native-snes-port), nedladdning via archive.org). Det betyder att idén om **en enda SNES-ROM i princip håller**.
  - *Inte verifierat:* hur porten distribueras (patch eller ROM), om källkoden är öppen och vilken ROM-layout den har. Det avgör hela spår B nedan.

### 1.3 Så får SMZ3 in två spel i samma ROM
Från `tewtal/alttp_sm_combo_randomizer_rom` (`banks.txt`, `src/main.asm`, `src/sm/transition.asm`):
1. **ExHiROM-sammanslagning.** ALttP:s banker läggs på `$00–$1F`, SM:s på `$80+`, och randomizer-tabeller, extra grafik och fritt utrymme på `$40–$5F`. Varje spel får en `hirom.asm`-patch som flyttar dess pekare.
2. **Delad SRAM.** Båda spelen sparar sitt inventarie i SRAM. När ett spel får ett item från det andra spelet skrivs det till det andra spelets SRAM-område ("foreign items").
3. **Övergången** (`transition_to_sm`): stäng av IRQ/NMI/HDMA, slå på forced blank, återställ SPC:n så att ljudmotorn kan laddas om, **DMA:a in en färdig "mall" av VRAM och WRAM för målspelet från ROM**, ladda målspelets sparfil och hoppa in via en dörr eller portal i målspelet.
4. **Logik och generering** sker i C# (`Randomizer.SMZ3`). Varje portal har en egen åtkomstregel, till exempel `CanAccessMiseryMirePortal` och `CanAccessNorfairLowerPortal`, och fyllningen är en vanlig assumed fill över båda världarna.
5. **MSU-1** stöds via `sm/msu.asm` och `spc.asm`. SA-1 används inte alls.

### 1.4 ALttPDoorRandomizer
Det här är en Python-fork av den klassiska ER/Berserker-randomizern, med regioner, regler, fill och ROM-patch via `base2current.bps`. Den är värdefull som **referens för ALttP-logik**, men tillför inget som just det här projektet behöver: dörrslumpning gör det bara svårare för både publik och spelare. Den har en egen multiworld som **inte** är Archipelago-kompatibel. Rekommendationen är att *inte* bygga på den.

### 1.5 Hårdvarufrågan i korthet
| Fråga | Svar |
|---|---|
| Kan SNES köra NES-kod? | 65816 har ett 6502-läge, men PPU, APU och MMC1-mappern skiljer sig helt. Realtidsemulering av NES på SNES fungerar inte i praktiken. Därför behövs en **port**. |
| Emulering eller portning? | Med två ROM:ar kör man två emulatorer på PC, vilket är trivialt. Med en ROM krävs en port, och den finns nu (Infidelity). |
| MSU-1? | Kul men valfritt. Porten har redan MSU-1-hooks och SMZ3 har MSU-1-stöd. Emulatorer som snes9x, bsnes och BizHawk kör MSU-1. Fint för showcasen men behövs inte. |
| SA-1? | **Behövs inte.** Inget av spelen använder det, och att lägga till SA-1 skulle bara krångla till minnesmappningen. |

---

## 2. Designalternativ

### A. "Sewer Bridge" – två emulatorer och Archipelago ⭐ rekommenderas
ALttP körs i en SNES-emulator och TMNT (NES) i BizHawk, som båda ansluter till en lokal Archipelago-server. Spelaren har två "slots" i samma seed (Archipelagos standardläge för solo-multiworld).
- **Gratis:** ALttP-världen finns redan i Archipelago med logik, fill, spoiler, tracker och item-leverans via SNI.
- **Att bygga:** en `tmnt.apworld` (locations, items och regler) och en BizHawk-klient som läser och skriver TMNT-RAM.
- **Portaler:** ett litet orkestreringsskript och OBS. När Link går ner i en "kloak" byter streamen scen till TMNT med en pizza-wipe som övergång, och tvärtom.
- **För:** realistiskt på några veckor, låg risk, och generering och logik blir rätt från början.
- **Emot:** inte en enda ROM. Övergången är ett scenbyte i OBS, inte en riktig dörr i spelet. Items kan bara ha mening i *ett* av spelen (se 3.3).

### B. "SMZ3-klonen" – en SNES-ROM
Infidelitys SNES-port av TMNT och ALttP slås ihop i en ExHiROM med SMZ3:s transition-teknik: SRAM-handoff, SPC-reset och DMA av WRAM/VRAM-mallar. Det kräver en egen generator, till exempel en fork av SMZ3:s C#.
- **För:** den riktiga "wow"-känslan. Mottagna TMNT-items syns direkt i ALttP:s meny och portalen är en riktig dörr i spelet.
- **Emot:** kräver portens källkod eller en egen disassembly, flytt av båda spelen, RAM-konflikter, ljudmotorbyte och item-grafik i båda spelen. Det är **3–6+ månader** av assemblerarbete på hobbynivå. Det finns stor risk att det inte blir klart, och porten är inte vår kod (licensen och tillåtelse från Infidelity behöver lösas).

### C. "Stafett" – noll kod
En vanlig ALttP-randomizer och tmnt_rando körs separat. Regeln är att när du klarar en ALttP-dungeon spelar du nästa TMNT-area, och OBS växlar.
- **För:** klart på en kväll.
- **Emot:** ingen delad item-pool, och det är bara två spel efter varandra. Det duger bara som nödlösning.

**Rekommendation:** Bygg **A** till maratonet. Se **B** som ett efterhandsprojekt om A blir en hit och Infidelity är med på det. Ha **C** som plan B om tiden tar slut.

---

## 3. Speldesign: hur TMNT gate:as

TMNT är linjärt (Area 1 → 6, med Technodrome och Shredder sist). Vi gör det icke-linjärt genom att **behandla varje Area som en dungeon** som man går in i via en portal, och låter sköldpaddor och verktyg vara items.

### 3.1 Byggstenar
| Mekanik | Hur den fungerar | Meme-värde |
|---|---|---|
| **Sköldpaddor som items** | Du börjar med *en* slumpad sköldpadda (meme-flagga: alltid Raphael). De andra tre är "tillfångatagna" och ligger någonstans i Hyrule. Spelet har redan ett fångat-tillstånd, så en sköldpadda vi inte har hittat än sätts som tillfångatagen när TMNT laddas. | Mycket högt: "Donatello hittad i Kakarikos kyckling-hus!" |
| **Donatellos bo som "förmåga"** | Logiken räknar Don som kravet för några svåra bossar eller rum (lång räckvidd). Ingen kod behövs, bara regler. | Medel |
| **Area-pass** (`Sewer Pass: Area 1–5`) | Krävs för att gå in i Area N. Det finns fem pass, och du börjar med ett av dem. Areas låses upp i valfri ordning. Area 6 (Technodrome) har inget pass utan kräver villkoret i 3.4. | Ryggraden i progressionen |
| **Missiles / Ropes** | Progression-items för Area 3 (Party Wagon). De ersätter tmnt_randos garanti. | Naturligt, går att förstå |
| **Dam-dykutrustning** | Item som krävs för Area 2 (dammen). Utan den får man inte välja Area 2. | Publiken älskar att hata dammen |
| **Vanliga TMNT-pickups** | Pizza, shuriken, bumerang och scroll går in i den delade poolen som filler i båda riktningarna. | En pizza i en ALttP-kista |

### 3.2 Belöningar som kopplar ihop spelen åt andra hållet
- Varje TMNT-bossvinst är en *location* som kan innehålla ALttP-progression, till exempel Hookshot bakom Area 3:s boss.
- Kloakportaler i ALttP: **Hyrule Castle-kloaken** (temat är perfekt), Kakariko-brunnen och en i Dark World. Portalen *är* menyn för att välja Area.

### 3.3 Items med dubbel betydelse (bara spår B, alternativt en senare utökning)
"Flippers låser upp dammen" och "Hookshot = Rope" är roligast, men i Archipelago tillhör ett item *en* slot, och logik över två slots stöds inte. I spår A använder vi därför **tematiska namn** i stället, till exempel att dykutrustningen heter "Zora's Scuba Kit". Om den ska ligga hos Zora går det att tvinga fram med Archipelagos `plando_items`, men det är valfritt. Riktiga items med dubbel mening kräver att båda spelen modelleras som *en* värld, alltså på samma sätt som SMZ3.

### 3.4 Mål
- **Mål:** besegra både Ganon *och* Shredder. I Archipelago har varje slot sitt eget mål, och seeden räknas som klar när båda slottarna är klara. Klockan stannar vid det sista av de två.
- Technodrome (Area 6) kräver alla 4 sköldpaddor och 3 avklarade Areas.
- **Så tvingas spelen att flätas ihop.** ALttP:s kristaller kan inte flyttas till TMNT, eftersom Archipelagos ALttP-värld inte kan slumpa dungeon-belöningar till andra världar (kontrollerat i `worlds/alttp/Options.py`). Sammanflätningen sker i stället med Archipelagos standardinställning `non_local_items`:
  - TMNT-slotten sätter sköldpaddor, Area-pass, missiles och ropes som `non_local_items`, så att de bara kan hamna i Hyrule.
  - ALttP-slotten sätter till exempel Hookshot, Flippers och Moon Pearl som `non_local_items`, så att de bara kan hamna i TMNT.
  - Effekt: du kommer inte långt i något av spelen utan att växla.
- Inställningar för meme-läget: `start_turtle: raphael`, `pizza_traps` (en "trap" som ger Link pizzahatt eller inverterade kontroller i 10 sekunder) och `dam_timer_halved` (bara för den som verkligen vill det).

### 3.5 Speltid och svårighet
TMNT NES är svårt, och dammen är ökänd. För att undvika att sändningen dör ger varje sköldpadda en buffert (fler "liv"). Missiles och ropes delas ut i rimliga mängder, och inställningen `easy_tmnt` ger halverad skada genom att klienten skriver till RAM.

---

## 4. Teknisk arkitektur för spår A

```
┌─────────────── PC / stream ───────────────┐
│ SNES-emu (ALttP AP-ROM) ──SNI──┐           │
│                                 ├─ AP-server (lokal)
│ BizHawk (TMNT NES) ──Lua──► TMNT-klient ─┘ │
│            ▲                       │       │
│            └── areaval / savestates│       │
│ Portal-orkestrerare ◄──────────────┘──► OBS (scenbyte + pizza-wipe)
└───────────────────────────────────────────┘
```

**Enheter (var och en går att testa för sig)**
1. **`tmnt.apworld`** (Python, Archipelagos API)
   - *Locations:* item-pickups (adresserna från tmnt_randos `item_pointers.txt`, plus filtrering per Area) och en per bossvinst.
   - *Items:* 4 sköldpaddor (minus startsköldpaddan), 5 Area-pass (minus startpasset), missiles, ropes, dykutrustningen och filler. Antalet missiles och ropes bestäms när Area 3 har testats.
   - *Regler:* Area-pass, Area 3 kräver missiles och ropes, Area 2 kräver dykutrustning, Area 6 enligt 3.4.
   - *ROM-patch:* ersätt pickup-typen på de platser som innehåller AP-items, enligt tmnt_randos metod. I MVP används ett befintligt item, till exempel en scroll, som markör, och spelaren får även scrollens effekt. Det är bara en kosmetisk bugg. En egen sprite eller palett ligger utanför MVP.
2. **TMNT-klienten** (Archipelagos BizHawk-klientramverk)
   - *Läsa:* plockade pickups, bossvinst, nuvarande area och HP per sköldpadda.
   - *Skriva:* mottagna items (sköldpadda frigiven, missiles/ropes/sub-vapen) och "tillfångatagen" för saknade sköldpaddor.
3. **Areaväljare / savestate-laddare.** En färdig savestate i början av varje Area. När spelaren väljer en upplåst Area laddas statet och inventariet injiceras sedan. Det kringgår den linjära progressionen utan ROM-hack.
   - *Kontrollerat:* Archipelagos generiska BizHawk-connector (`data/lua/connector_bizhawk_generic.lua`) kan bara läsa och skriva minne, låsa emulatorn och visa meddelanden. Den kan **inte ladda savestates**.
   - Areaväljaren blir därför ett **eget litet Lua-skript** som körs i BizHawk bredvid connectorn (BizHawk kan köra flera skript samtidigt, och `savestate.load` finns i Lua-API:t). Skriptet läser vilka pass som är upplåsta från en minnesadress som TMNT-klienten skriver till. Klienten och väljaren pratar alltså via emulatorns RAM och behöver inte prata direkt med varandra.
   - Alternativ om det strular: skriv areanumret till RAM och låt spelets egen area-övergång göra jobbet. Det kräver mer RAM-forskning.
4. **Portal-orkestreraren.** Den lyssnar på ALttP-rummet via SNI. När spelaren går in i ett kloakrum pausar den SNES-emulatorn, ber OBS byta scen och öppnar areaväljaren. Vid "Exit Sewer" i TMNT sker det omvända. **MVP:** en snabbtangent i stället för rum-detektering.

**Felhantering:** klienten måste överleva en emulator-reset och återställa inventariet från AP-serverns state, vilket Archipelago-klienter gör som standard. Areaväljaren laddar aldrig en låst Area.

**Test:** generera cirka 200 seeds per inställningsprofil (Archipelagos `Generate.py` validerar att seeden går att slutföra). Gör manuella genomspelningar av varje Area-start-state, och kör minst en hel genrep-körning på stream-maskinen.

---

## 5. MVP som hinner bli klar till maratonet

**Med i MVP:**
- `tmnt.apworld` med locations för bossvinster och, om risk R2 går att lösa, ett urval säkra pickups (cirka 20–30 av de 243).
- Items: 4 sköldpaddor, Area-pass, missiles, ropes, dykutrustning och pizza-filler.
- BizHawk-klient som läser bossvinster och pickups och skriver sköldpaddor och verktyg.
- Areaväljare via savestates.
- OBS-snabbtangent för "portalen" med en pizza-wipe som övergång.
- Mål: Ganon + Shredder.
- ALttP: Archipelagos standard-ALttP med enkla inställningar (open mode, inga dörrar, ingen ER).

**Utanför MVP (nice-to-have i den här ordningen):** automatisk portal via rumdetektering, `pizza_traps`, egen AP-item-sprite i TMNT, MSU-1-musik, fiendeslump i TMNT.

**Utanför projektet:** spår B (en ROM) och items med dubbel betydelse.

---

## 6. Ungefärlig arbetsinsats (kvällar/helger, en person, viss Python-vana)

| Steg | Insats |
|---|---|
| Sätta upp Archipelago från källkod, ALttP via SNI, BizHawk | 1–2 dagar |
| Kartlägga TMNT-RAM: sköldpaddornas HP/fångad, area, pickups, boss, inventarie | 3–5 dagar *(största osäkerheten)* |
| `tmnt.apworld`: items, locations, regler och patch | 3–4 dagar |
| BizHawk-klient och areaväljare (eget Lua-skript för savestates) | 4–5 dagar |
| OBS-portal: snabbtangent, övergång, layout | 1 dag |
| Seed-test, balansering, genrep | 3–5 dagar |
| **Totalt MVP** | **≈ 3–5 veckor kvällstid** |
| Spår B (en ROM, SMZ3-stil) | 3–6+ månader, beroende på portens källkod |

## 7. Risker

| Risk | Sannolikhet | Hantering |
|---|---|---|
| R1: TMNT:s RAM-karta är svårare att hitta än väntat, särskilt fångad-tillståndet | Medel | Börja med det (spike vecka 1). |
| R2: TMNT har **ingen bestående flagga** för upplockade pickups (föremål kan dyka upp igen när man går tillbaka in i ett rum), så klienten vet inte *vilken* pickup som togs | Medel–hög | Spiken avgör. Fallback 1: klienten känner igen upplockningen på rum + objektplats + item-typ. Fallback 2: locations bara på bossvinster och Area-avslut (cirka 10–12 locations räcker för en MVP). |
| Savestate-injektion ger konstiga lägen, till exempel fel sköldpadda aktiv | Medel | Skriv state först efter area-intro. Testa varje Area separat. |
| TMNT blir för svårt för speltiden (dammen) | Hög | `easy_tmnt`, dykutrustning sent i logiken, och träna rutten innan. |
| Archipelagos API ändras under arbetet | Låg | Lås versionen av Archipelago. |
| Krångel med två emulatorer på stream-maskinen | Medel | Genrep på samma maskin. Spara OBS-profilen. |
| Licensfrågan kring Infidelitys port (bara spår B) | – | Fråga Infidelity innan något görs. |
| Spoilers eller softlock live | Låg–medel | Använd bara genererade och validerade seeds. Kör en testseed helt igenom. |

## 8. Öppna frågor till Oscar
1. **När är maratonet?** Det avgör om MVP räcker eller om det finns tid för automatiska portaler.
2. **Emulator eller riktig hårdvara?** Allt ovan förutsätter emulator.
3. **Vem spelar?** En TMNT-van löpare tål svårare inställningar.
4. Finns det Archipelago- och Python-vana i teamet, eller blir det inlärning från noll?

## 9. Föreslagen första vecka (spike)
1. Installera Archipelago från källkod och kör en ALttP-seed via SNI.
2. Öppna TMNT (NA, md5 enligt ovan) i BizHawk och hitta RAM-adresserna för sköldpaddornas HP/fångad och aktuell area. Ta också reda på om upplockade pickups sparas någonstans (risk R2).
3. Testa att ett eget Lua-skript kan köra `savestate.load` samtidigt som Archipelagos connector är igång.
4. Om (2) och (3) går bra är spår A grönt och det är dags att skriva implementationsplanen. Om R2 faller ut dåligt används fallback 2: bara bossvinster som locations.

---

## 10. Granskningslogg (2026-10-31)
Rättat efter granskning mot källorna:
- **Savestates:** Archipelagos BizHawk-connector kan inte ladda savestates. Areaväljaren blir därför ett eget Lua-skript (4.3), och insatsen har höjts.
- **Kristaller:** att TMNT-bossar skulle ge ALttP-kristaller går inte i Archipelago. Det har ersatts med `non_local_items` (3.4).
- **Area-pass:** det stod sex pass, men Area 6 har inget pass. Antalet är rättat till fem.
- **Pickups:** ny risk R2, att upplockade pickups inte sparas. Fallback är bossvinster som locations.
- **Mål:** förtydligat hur "båda målen" fungerar i Archipelago.
- **Verifierat:** att tmnt_rando gäller NES, att SMZ3 använder assumed fill och ExHiROM-layouten, och att tmnt_rando har 243 pickup-platser.
- **Fortfarande inte verifierat:** hur Infidelitys SNES-port distribueras och om källkoden är öppen, och hela TMNT:s RAM-karta.

---
**Källor:** [aerinon/ALttPDoorRandomizer](https://github.com/aerinon/ALttPDoorRandomizer), [tewtal/SMZ3Randomizer](https://github.com/tewtal/SMZ3Randomizer), [tewtal/alttp_sm_combo_randomizer_rom](https://github.com/tewtal/alttp_sm_combo_randomizer_rom), [abyssonym/tmnt_rando](https://github.com/abyssonym/tmnt_rando), [Time Extension – TMNT native SNES-port](https://www.timeextension.com/news/2025/10/teenage-mutant-ninja-turtles-is-the-next-nes-classic-to-get-a-native-snes-port), [Time Extension – aviserad aug 2025](https://www.timeextension.com/news/2025/08/teenage-mutant-ninja-turtles-will-be-the-next-nes-classic-to-get-a-native-snes-port).
