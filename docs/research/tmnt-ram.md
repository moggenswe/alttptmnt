# TMNT (NES) – RAM-karta (spike, Task 1)

ROM: Teenage Mutant Ninja Turtles (USA).nes, md5 `5e24ccd733d15e42d847274e7add0a76`. Emulator: BizHawk (NES-core), domän `RAM` om inget annat står.

Fyll i allt eftersom. När allt nedan är ifyllt förs värdena in i `apworld/tmnt/ram.py`, och där sätts `VERIFIED = True`.

## Adresser

| Vad | Adress | Värden / beteende | Hur hittad |
|---|---|---|---|
| Aktuell area | | | |
| HP Leonardo | | full = ?, fångad = ? | |
| HP Michelangelo | | | |
| HP Donatello | | | |
| HP Raphael | | | |
| Antal missiles | | | |
| Antal rep | | | |
| Bossvinst Area 1–5 | | | |
| Shredder besegrad | | | |
| 4 lediga bytes (brevlåda) | | aldrig skrivna under Area 1–3 | |
| Ledigt ROM-utrymme för AP-taggen (PRG-offset) | `0x1BE00` | 582 byte `0xFF` på `$1BD92–$1BFD7` (bank 6); taggen tar 70 byte | Skannat ur ROM-filen |

## R1 – går det att låsa en sköldpadda genom att sätta HP till fångad-värdet?

Resultat:

## R2 – minns spelet upplockade pickups?

Resultat:

## MISSILE_REFILL / ROPE_REFILL

Minsta antal som räcker i Area 3:   → värde (+50 %):

## Övrigt / överraskningar
