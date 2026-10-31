# TMNT (NES) – RAM-karta (spike, Task 1)

ROM: Teenage Mutant Ninja Turtles (USA), md5 `c14e760c4d5a086e4186d2e1fc9b7743`. Emulator: BizHawk (NES-core), domän `RAM` om inget annat står.

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
| Ledigt ROM-utrymme för AP-taggen (PRG-offset) | | 70 bytes `0xFF` eller `0x00` | |

## R1 – går det att låsa en sköldpadda genom att sätta HP till fångad-värdet?

Resultat:

## R2 – minns spelet upplockade pickups?

Resultat:

## MISSILE_REFILL / ROPE_REFILL

Minsta antal som räcker i Area 3:   → värde (+50 %):

## Övrigt / överraskningar
