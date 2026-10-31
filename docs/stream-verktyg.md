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

**Meddelanden:** när ett föremål kommer visar klienten "Fick Rope Pack från Link" eller "Hittade Leonardo" i BizHawks meddelandefält. Det syns i fönstret och därmed i OBS:s fönsterfångst.

## OBS: go mode-panelen

Lägg till `tools/obs/go-mode.html` som en Browser-källa med lokal fil. Lägg till parametrarna i URL:en:

```
file:///C:/Project/tmntalttp/tools/obs/go-mode.html?server=ws://localhost:38281&alttp=Link&tmnt=Turtles
```

- Panelen visar Hyrule (dungeon-bossar x/10, KLART när Ganon är besegrad) och New York (sköldpaddor x/4, bossar x/3, GO MODE, KLART när Shredder är besegrad).
- Den ansluter som en skrivskyddad Tracker-klient och påverkar inte spelet.
- Med `&demo=1` visas påhittade värden utan server, och `&layout=column` lägger korten under varandra.
- ALttP:s kristaller syns inte i panelen. De är logikhändelser utan ID och slumpas mellan dungeons. Runnern ser dem på kartan i spelet.
- Testad 2026-10-31 mot en lokal MultiServer (TMNT-seed): `/send` och `/send_location` uppdaterade panelen live till GO MODE. Inte testad i OBS.

## Hints och spelarfiler

- `players/tmnt.yaml` har `start_hints` för Leonardo, Michelangelo, Donatello, Missile Pack och Rope Pack, så att vägen till go mode syns från start.
- Båda spelarfilerna har `progression_balancing: 75`.
- Värden kan under streamen köra `/hint Turtles <föremål>` från serverkonsolen, till exempel som donationsmål. `/send` fungerar som nödutgång.
- Spoilerloggen (host.yaml `spoiler: 3`) innehåller playthrough och hör hemma hos produktionen, utanför bild.

## Trackers

- **Universal Tracker** (TMNT): världen stöder att UT bygger om seeden från slot_data utan YAML. Det är inte provat mot den riktiga `tracker.apworld` än.
- **ALttP:** PopTracker med StripesOO7/alttp-ap-poptracker-pack (AP-autotracking). Den är inte nedladdad eller provad här.
- **Föremålsflöde i OBS (valfritt):** Nic-del/Broadcast-Archipelago. Den är inte provad här.
- **Egen TMNT-pack till PopTracker:** valfri, cirka 1–2 dagar. Se rapporten.
