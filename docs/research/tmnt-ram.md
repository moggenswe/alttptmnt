# TMNT (NES) – RAM-karta (spike, Task 1)

ROM: Teenage Mutant Ninja Turtles (USA).nes, md5 `5e24ccd733d15e42d847274e7add0a76`. Emulator: BizHawk (NES-core), domän `RAM` om inget annat står.

Fyll i allt eftersom. När allt nedan är ifyllt förs värdena in i `apworld/tmnt/ram.py`, och där sätts `VERIFIED = True`.

Källor: adelikats och JXQ:s RAM-karta (`files.tasvideos.org/gameresources/nes/tmnt/TMNT.xls`, fliken "RAM", 2006–2010) och [TASVideos sida för TMNT](https://tasvideos.org/GameResources/NES/TeenageMutantNinjaTurtles). "Dok" betyder dokumenterat där. "Bekräftat" betyder kontrollerat av oss i BizHawk.

## Adresser

| Vad | Adress | Värden / beteende | Status |
|---|---|---|---|
| Aktuell area ("world number") | `$0048` | Area 1 = 0 eller 1? | Dok |
| Var i spelet | `$001B` | 5 = eftertexter | Dok |
| Aktiv sköldpadda | `$0067` | 0 = Leo, 1 = Raph, 2 = Mike, 3 = Don | Dok |
| HP Leonardo | `$0077` | max 128 (`$80`), 16 per streck; fångad = ? | Dok |
| HP Raphael | `$0078` | som ovan | Dok (rättad: kartan säger Mike) |
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

Resultat:

## R2 – minns spelet upplockade pickups?

Resultat:

## MISSILE_REFILL / ROPE_REFILL

Minsta antal som räcker i Area 3:   → värde (+50 %):

## Övrigt / överraskningar
