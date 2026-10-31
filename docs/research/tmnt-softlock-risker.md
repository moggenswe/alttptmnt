# Softlock- och logikrisker för TMNT-slotten (2026-10-31)

Frågan: kan spelaren fastna för att något som krävs inte går att nå, eller för att spelet och logiken inte stämmer överens? Det här är en genomgång av logiken (`apworld/tmnt/rules.py`), klienten, areaväljaren och spelet. Det mesta är testat. Det som inte är testat står under "Kvar att göra".

## Slutsats

Ingen känd väg leder till att spelaren fastnar för gott i TMNT-delen.

- **Inget går att missa:** varje TMNT-location går att ta igen.
- **Inget tar slut:** continues och ammo med pack tar aldrig slut.
- **Inga vägar runt passen:** areor utan pass nås inte.

Den största kvarvarande osäkerheten är area-states för Area 5 och 6. De kommer från ett nytt spel och saknar ett par bytes som en riktig genomspelning har satt. Ingen har spelat igenom de areorna från våra states, och en människa bör göra det.

## 1. Kan ett föremål som krävs bli onåbart?

| Risk | Läge | Hur det är skyddat |
|---|---|---|
| Fill lägger ett föremål bakom sig självt | Löst av AP | Reglerna är strikta. Generering är testad med 30 och 20 seeds (fast start) och 100 seeds (slumpad startsköldpadda och startarea), alla godkända. Startarean får sitt pass och sina verktyg från start. |
| En TMNT-location går att missa för alltid | Nej | Bossar går att slå igen via menyn. Ingångar räknas vid varje laddning. Turtle Lair-gåvorna skickas vid anslutning. |
| Bossvinst eller Shredder medan klienten är frånkopplad | Löst (7b681e2) | Väljaren skriver vinsten i `$038E`, och klienten skickar den när den ansluter igen. Det gäller inte om man gör power-cycle innan klienten hunnit läsa byten, men då kan man slå bossen igen. |
| Logiken kräver mindre än spelet | Nej | Se tabellen nedan. Logiken är överallt lika sträng eller strängare än spelet. |

| Area | Spelet kräver (TAS + ROM) | Logiken kräver |
|---|---|---|
| 1 | inget | pass |
| 2 | inget extra (Scuba Kit är ett påhittat lås) | pass + Zora's Scuba Kit |
| 3 | missiler mot vägspärrar (TAS: 10 skott). Rep används inte av TAS:en (ropeless). | pass + Missile Pack + Rope Pack |
| 4 | rep (TAS: 1 kast, en upplockning på 3 i banan) | pass + Rope Pack |
| 5 | inget extra | pass; bossen kräver Donatello (designval) |
| 6 | inget extra | alla fyra sköldpaddor + 3 avklarade bossar |

TAS-datan bekräftar att missiler bara används i Area 3 och rep bara i Area 4.

## 2. Kan spelaren fastna i själva spelet?

| Situation | Vad som händer |
|---|---|
| Alla ägda sköldpaddor fångas | Game over, sedan CONTINUE. Continues tar aldrig slut (`$0046` 0 blir 255). Arean startar om, och de ägda sköldpaddorna är fria igen. Testat i BizHawk. |
| Ammo tar slut | Den som har ett pack fylls på när räknaren står på 0. Spelets egna upplockningar i Area 3 och 4 återuppstår dessutom. |
| Spelet går vidare till en låst area efter en boss | Menyn tvingas upp och kan inte stängas förrän en upplåst area laddats. Testat. |
| Nytt spel från titelskärmen (END eller reset) | Menyn tvingas upp, och ingen area spelas utan pass. Testat. |
| State saknas eller är gjord i en annan BizHawk | Menyn visar "(saknas)" eller "Kunde inte ladda Area N". Inget halvladdas och laddningen räknas inte. Testat för saknad fil. |
| Den aktiva sköldpaddan ägs inte (alla states har Leo) | Klienten byter till en ägd sköldpadda och fångar sedan Leo. Testat. |

## 3. Läckor utanför logiken

Ingen av de här låser fast spelaren, men de gör föremål mindre värda.

- **Spelets egen räddning:** från Area 3 kan man rädda en fången sköldpadda per area. Klienten fångar nu varje sköldpadda man inte äger så fort hennes HP inte är 0 (7b681e2). Det gäller också continue och nytt spel.
- **Missiler och rep i banan:** de finns bara i Area 3 och 4, och dit kommer man bara med respektive pack. Läckan är därför stängd av menyn.

## 4. Area-states mot en riktig genomspelning

Våra states kommer från ett nytt spel där areabyten skrivits om. Det som en riktig genomspelning har satt före arean saknas alltså. Testmetoden (`lua/tmnt_state_flags_check.lua`, `tools/state_flags_check.py`):
- Spela TAS 4543M i BizHawk 2.6.1.
- När areabyten byts, skriv in våra states värden för de bytes som TAS:en bär in i arean.
- Se om TAS:en ändå klarar arean på exakt samma frame.

En avsynk betyder bara att spelet läser byten någonstans. Det betyder inte att arean blir omöjlig.

| Area | Resultat |
|---|---|
| 2 | Synk med alla burna bytes. Våra states saknar inget som spelet läser där. |
| 3, 4 | Synk med alla utom `$0073`–`$0076` och `$0614`. `$0076` och `$0074` sattes på samma frame som Donatello respektive Raph plockade upp kastvapen, så de är troligen vapentypen per sköldpadda. `$0614` växlar redan i Area 1 och ser ut som lägesstatus på kartan. Inget av det är framsteg. |
| 5 | Avsynk. `$00C4` och `$00CA` (0 → 1 samtidigt långt in i Area 4, mitt i en objekttabell `$00C0`–`$00CF`) räcker var för sig för att få TAS:en ur synk. Utan dem blir det ändå avsynk av en kombination av de övriga bytesen. Den kombinationen är inte hittad, men inget av dem gör det ensamt. |
| 6 | Synk när `$00C4`/`$00CA` och vapen- och kartbytesen lämnas orörda. Med `$00C4`/`$00CA` nollade blir det avsynk. |
| — | `$007B` (följer areanumret) och `$007C` (växande bitmask) ser ut som framsteg men påverkar ingen area. |

**Tolkning:** inget pekar på en flagga som spärrar en väg. `$00C4`/`$00CA` är det enda som ser ut som tillstånd från en tidigare area som spelet läser senare, i Area 5 och 6. Om det är något som "dörren är öppen" eller bara gammal objektstatus vet vi inte. Det avgörs av att någon spelar Area 5 och 6 från våra states.

## 5. Kvar att göra

1. **Spela varje area från sin state till och med bossen**, främst Area 5 och 6. Om något inte fungerar kan states göras om med TAS:ens värden för `$00C4`/`$00CA` och därefter testas igen.
2. **Gör states i den BizHawk-version som används på streamen.** States från andra versioner laddas inte, och menyn säger då till.
3. **Hela seedet med ALttP** är inte testat här, eftersom ALttP-ROM:en saknas på den här datorn. ALttP-logiken är Archipelagos egen (open, inga glitches).
4. **Spelets egen räddning** är inte sedd i BizHawk. Enhetstesterna visar att klienten fångar sköldpaddan igen, men inte hur det ser ut i spelet.
5. **`$0055`** (2 i TAS:en, 4 i våra states, från spelets start) är oförklarad men påverkar inte synken.

## Testläge 2026-10-31

- 134 enhetstester
- Areaväljartestet 40/40, i BizHawk 2.11.1
- E2E-kedjan med server, BizHawk, väljare och klient godkänd
- 150 genererade seeds utan fel
- 40-tal TAS-körningar för area-states, med resultat i `tas/4543M/flags/` (inte i git)
