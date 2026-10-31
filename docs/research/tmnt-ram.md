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
| 4 lediga bytes (brevlåda) | `$07F0–$07F3` | sidan `07xx` saknar anteckningar; ska aldrig ändras under spel | Gissning |
| Ledigt ROM-utrymme för AP-taggen (PRG-offset) | `0x1BE00` | 582 byte `0xFF` på `$1BD92–$1BFD7` (bank 6); taggen tar 70 byte | Skannat ur ROM-filen |

## R1 – går det att låsa en sköldpadda genom att sätta HP till fångad-värdet?

Resultat: **JA** (2026-10-31). Med Mike aktiv sattes `$0078` (Raph) till `00`. På pausskärmen saknade Raph porträtt och hälsomätare och gick inte att välja, och Splinter sa "Find and help your friend in this stage". Spelet behandlar honom alltså som tillfångatagen. Att skriva `00` till den *aktiva* sköldpaddan utlöser dödsanimationen. Klienten skriver bara fångad-värdet vid full sync direkt efter en area-laddning, så det bör inte hända, men det testas i Task 7.

Frigivning: **JA**. Efter `80` på `$0078` gick Raph att välja igen direkt. Klienten kan alltså frige en sköldpadda mitt i en area.

## R2 – minns spelet upplockade pickups?

Resultat:

## MISSILE_REFILL / ROPE_REFILL

Minsta antal som räcker i Area 3:   → värde (+50 %):

## Övrigt / överraskningar

- `$001B` (var i spelet) = 4 på pausskärmen i Area 1.
- RAM-kartan (TMNT.xls) har Raph och Mike omkastade för hälsan. Rätt ordning följer sköldpaddsnumret.
