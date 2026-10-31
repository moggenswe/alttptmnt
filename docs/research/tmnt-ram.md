# TMNT (NES) – RAM-karta (spike, Task 1)

ROM: Teenage Mutant Ninja Turtles (USA).nes, md5 `5e24ccd733d15e42d847274e7add0a76`. Emulator: BizHawk (NES-core), domän `RAM` om inget annat står.

Fyll i allt eftersom. När allt nedan är ifyllt förs värdena in i `apworld/tmnt/ram.py`, och där sätts `VERIFIED = True`.

Källor: adelikats och JXQ:s RAM-karta (`files.tasvideos.org/gameresources/nes/tmnt/TMNT.xls`, fliken "RAM", 2006–2010) och [TASVideos sida för TMNT](https://tasvideos.org/GameResources/NES/TeenageMutantNinjaTurtles). "Dok" betyder dokumenterat där. "Bekräftat" betyder kontrollerat av oss i BizHawk.

## Adresser

| Vad | Adress | Värden / beteende | Status |
|---|---|---|---|
| Aktuell area ("world number") | `$0048` | Area N = värde + 1 (Area 1 = 0) | **Bekräftat** (pausskärmen visar AREA 1 när värdet är 0) |
| Var i spelet | `$001B` | 5 = eftertexter | Dok |
| Aktiv sköldpadda | `$0067` | 0 = Leo, 1 = Raph, 2 = Mike, 3 = Don | **Bekräftat** (2 med Mike aktiv) |
| HP Leonardo | `$0077` | max 128 (`$80`), 16 per streck; fångad = `00` | Dok (fångad/fri bekräftat på Raph) |
| HP Raphael | `$0078` | som ovan | **Bekräftat**: `00` gjorde Raph fångad |
| HP Michelangelo | `$0079` | som ovan; full = `$80` | **Bekräftat**: `00` här tömde Mikes mätare |
| HP Donatello | `$007A` | som ovan | Dok |
| Antal missiles | `$00BF` | | Dok |
| Antal rep | `$00A7` | | Dok |
| Kastvapen per sköldpadda | `$00A8–$00AB` | Leo, Raph, Mike, Don | Dok |
| Desarmerade bomber (Area 2) | `$007D` | | Dok |
| Pausad | `$0094` | 3 vid paus, 0 annars | Dok |
| Antal continues | `$0046` | börjar på 3 | Dok |
| Bossvinst Area 1–5 | | inte dokumenterad; troligen när `$0048` räknas upp | Okänd |
| Shredder besegrad | `$001B` = 5 | eftertexterna börjar | Dok |
| 4 lediga bytes (brevlåda) | ~~`$07F0–$07F3`~~ | **Används av spelet**: alla fyra blev `44` under spel i Area 1. Ny plats letas med "Track unused". | Underkänd |
| Ledigt ROM-utrymme för AP-taggen (PRG-offset) | `0x1BE00` | 582 byte `0xFF` på `$1BD92–$1BFD7` (bank 6); taggen tar 70 byte | Skannat ur ROM-filen |

## R1 – går det att låsa en sköldpadda genom att sätta HP till fångad-värdet?

Resultat: **JA** (2026-10-31). Med Mike aktiv sattes `$0078` (Raph) till `00`. På pausskärmen saknade Raph porträtt och hälsomätare och gick inte att välja, och Splinter sa "Find and help your friend in this stage". Spelet behandlar honom alltså som tillfångatagen. Att skriva `00` till den *aktiva* sköldpaddan utlöser dödsanimationen. Klienten skriver bara fångad-värdet vid full sync direkt efter en area-laddning, så det bör inte hända, men det testas i Task 7.

Frigivning: **JA**. Efter `80` på `$0078` gick Raph att välja igen direkt. Klienten kan alltså frige en sköldpadda mitt i en area.

## R2 – minns spelet upplockade pickups?

Resultat: **NEJ** (2026-10-31). En pizza i första byggnaden i Area 1 låg där igen efter ut- och ingång. `PICKUPS_PERSISTENT = False`, och Task 9 utgår.

## MISSILE_REFILL / ROPE_REFILL

Minsta antal som räcker i Area 3:   → värde (+50 %):

## Övrigt / överraskningar

- `$001B` (var i spelet) = 4 på pausskärmen i Area 1.
- RAM-kartan (TMNT.xls) har Raph och Mike omkastade för hälsan. Rätt ordning följer sköldpaddsnumret.

## Area-savestates (Task 7 steg 1)

Gjorda 2026-10-31 i BizHawk 2.11.1 med `lua/tmnt_make_area_states.lua`. Resultatet hamnar i `savestates/area1.State` … `area6.State`, med en skärmdump bredvid varje fil. Mappen ligger inte i git.

- **Metod:** vid ett nytt spel sätts `$0048` till 0 på den frame där `$001B` blir 3. Arean laddas några frames senare. Om N−1 skrivs till `$0048` på den framen och de två följande laddar spelet Area N i stället. Skärmdumparna visar rätt area för alla sex: startön, dammen, staden med Party Wagon, Area 4, Area 5 och insidan av Technodrome. Varje state sparas 120 frames efter laddningen.
- **Utgångsläge:** statesen kommer från ett nytt spel. Alla fyra sköldpaddor har full HP, Leo är aktiv och inga vapen finns.
- **Öppen risk till Task 7:** om spelaren inte har Leo skriver klienten `00` till hans HP vid full sync, och han är då aktiv. Enligt R1 utlöser det dödsanimationen. Lösningen är antingen att byta aktiv sköldpadda (`$0067`) före HP-skrivningen eller att göra states per startsköldpadda.
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
