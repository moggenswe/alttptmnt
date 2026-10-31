-- Lights received items and beaten bosses from the Archipelago server (variant "Item Tracker - AP").

local function set(code, active)
  local object = Tracker:FindObjectForCode(code)
  if object then object.Active = active end
end

local function on_clear(slot_data)
  for _, code in pairs(ITEM_MAPPING) do set(code, false) end
  for _, code in pairs(LOCATION_MAPPING) do set(code, false) end
end

local function on_item(index, item_id, item_name, player_number)
  local code = ITEM_MAPPING[item_id]
  if code then set(code, true) end
end

local function on_location(location_id, location_name)
  local code = LOCATION_MAPPING[location_id]
  if code then set(code, true) end
end

Archipelago:AddClearHandler("tmnt clear", on_clear)
Archipelago:AddItemHandler("tmnt item", on_item)
Archipelago:AddLocationHandler("tmnt location", on_location)
