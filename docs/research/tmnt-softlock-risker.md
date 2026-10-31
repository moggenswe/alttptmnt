# Softlock- och logikrisker för TMNT-slotten (2026-10-31)

Frågan: kan spelaren fastna för att något som krävs inte går att nå, eller för att spelet och logiken inte stämmer överens? Det här är en genomgång av logiken (`apworld/tmnt/rules.py`), klienten, areaväljaren och spelet. Det mesta är testat. Det som inte är testat står under "Kvar att göra".

## Slutsats

Ingen känd väg leder till att spelaren fastnar för gott i TMNT-delen.

- **Inget går att missa:** varje TMNT-location går att ta igen.
- **Inget tar slut:** continues och ammo med pack tar aldrig slut.
- **Inga vägar runt passen:** areor utan pass nås inte.
- **Inga framsteg saknas i våra area-states:** de skiljer sig från en riktig genomspelning bara i kastvapen, kartläge, poäng och ett värde som sätts när spelet startar.

Det som återstår är att en människa spelar igenom areorna från våra states, som en sista kontroll.

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

Varje skillnad som spelet läser är spårad till en enskild byte, i ett 60-tal TAS-körningar:

| Byte | Vad det är | Var spelet läser den | Framsteg? |
|---|---|---|---|
| `$0073`–`$0076` | troligen kastvapentyp per sköldpadda: `$0076` sattes på samma frame som Donatello plockade upp ett vapen, `$0074` när Raph gjorde det | Area 3–6 | Nej. Våra states har inga vapen, som ett nytt spel. |
| `$0614` | växlar 0/1/2 redan i Area 1 och ser ut som lägesstatus på kartan | Area 3–4 | Nej |
| `$C2`–`$C4`, `$C8`–`$CA` | **poäng och high score**. `$C2` räknas upp i tiotal när fiender dör, och init-rutinen för nytt spel (ROM 0x1C66B) nollställer `$C2`–`$C4` tillsammans med continues, HP, ammo och vapen. `$C4`/`$CA` blev 1 när poängen passerade 100 000 i Area 4. | Area 5–6 | Nej |
| `$0055` | sätts en gång vid frame 145 när spelet startar (2 i TAS:en, 4 i våra states; vi tryckte Start en frame förskjutet) och ändras aldrig sedan, troligen ett slumpfrö | Area 5 | Nej |
| `$007B`, `$007C` | ser ut som framsteg (följer areanumret, bitmask som växer) | ingenstans | Nej |

Med de här bytesen orörda håller TAS:en exakt synk i Area 2, 3, 4, 5 och 6, trots att alla andra bytes som TAS:en burit med sig skrivits över med våra states värden. Våra states saknar alltså inget framsteg som spelet läser på TAS-vägen. Poäng och slumpfrö gör att fienderna kan bete sig lite annorlunda än i TAS:en, men det låser inget.

## 5. Kvar att göra

1. **Spela varje area från sin state till och med bossen**, som slutkontroll. TAS-testet täcker bara TAS-vägen genom varje area.
2. **Gör states i den BizHawk-version som används på streamen.** States från andra versioner laddas inte, och menyn säger då till.
3. **Hela seedet med ALttP** är inte testat här, eftersom ALttP-ROM:en saknas på den här datorn. ALttP-logiken är Archipelagos egen (open, inga glitches).
4. **Spelets egen räddning** är inte sedd i BizHawk. E2E-testet visar att klienten fångar en friad sköldpadda igen inom tio frames.

## Testläge 2026-10-31

- 134 enhetstester
- Areaväljartestet 40/40, i BizHawk 2.11.1
- E2E-kedjan med server, BizHawk, väljare och klient godkänd. Den täcker också en bossvinst medan klienten är avstängd, en friad sköldpadda och meddelandet på skärmen.
- 150 genererade seeds utan fel
- 60-tal TAS-körningar för area-states, med resultat i `tas/4543M/flags/` (inte i git)
