-- TMNT (NES) Archipelago item tracker. Built by tools/make_poptracker_pack.py.
Tracker:AddItems("items/items.json")
Tracker:AddLayouts("layouts/tracker.json")
if Archipelago then
  ScriptHost:LoadScript("scripts/mapping.lua")
  ScriptHost:LoadScript("scripts/autotracking.lua")
end
