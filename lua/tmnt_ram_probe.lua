-- TMNT (NES) RAM probe for the RAM spike (plan Task 1).
--
-- Load in BizHawk: Tools > Lua Console > Script > Open Script. A small "TMNT RAM probe" window opens.
-- Everything is a button there, so no keyboard shortcut can clash with BizHawk's own hotkeys.
--
-- Narrowing search (like BizHawk's RAM Search):
--   New       every address is a candidate; current values are remembered.
--   Decreased keep candidates whose value went down since the last step.
--   Increased keep candidates whose value went up since the last step.
--   Same      keep candidates whose value did not change since the last step.
--   Changed   keep candidates whose value changed in either direction since the last step.
--   Undo      go back one step.
--   Print     list all candidates in the Lua console's Output.
-- Snapshot / Diff: Snapshot remembers all RAM; Diff prints every byte changed since then.
--
-- The WATCH addresses and the first 15 candidates are drawn on the game screen.
-- Edit WATCH as addresses are found; the values feed apworld/tmnt/ram.py.

local WATCH = {
  -- { "label", 0xADDR },  (source: adelikat/JXQ TMNT.xls RAM sheet; see apworld/tmnt/ram.py)
  { "world",     0x0048 },
  { "phase",     0x001B },
  { "turtle",    0x0067 },
  { "hp leo",    0x0077 },
  { "hp mike",   0x0078 },
  { "hp raph",   0x0079 },
  { "hp don",    0x007A },
  { "missiles",  0x00BF },
  { "ropes",     0x00A7 },
  { "mbox $7F0", 0x07F0 },
  { "mbox $7F1", 0x07F1 },
  { "mbox $7F2", 0x07F2 },
  { "mbox $7F3", 0x07F3 },
}

local RAM_SIZE = 0x800

local candidates = nil
local history = {}
local snapshot = nil
local status_label = nil

local function read(address)
  return memory.readbyte(address, "RAM")
end

local function count(tbl)
  local n = 0
  for _ in pairs(tbl) do n = n + 1 end
  return n
end

local function set_status(text)
  console.log(text)
  if status_label ~= nil then forms.settext(status_label, text) end
end

local function new_search()
  candidates, history = {}, {}
  for address = 0, RAM_SIZE - 1 do candidates[address] = read(address) end
  set_status("New: " .. count(candidates) .. " candidates")
end

local function narrow(label, keep)
  if candidates == nil then
    set_status("Press New first")
    return
  end
  history[#history + 1] = candidates
  local kept = {}
  for address, old in pairs(candidates) do
    local new = read(address)
    if keep(old, new) then kept[address] = new end
  end
  candidates = kept
  set_status(string.format("%s: %d candidates left (step %d)", label, count(candidates), #history))
end

local function undo()
  if #history == 0 then
    set_status("Nothing to undo")
    return
  end
  candidates = table.remove(history)
  set_status(string.format("Undo: %d candidates (step %d)", count(candidates), #history))
end

local function sorted_candidates()
  local list = {}
  for address in pairs(candidates) do list[#list + 1] = address end
  table.sort(list)
  return list
end

local function print_candidates()
  if candidates == nil then
    set_status("Press New first")
    return
  end
  for _, address in ipairs(sorted_candidates()) do
    local value = read(address)
    console.log(string.format("$%04X = %02X (%d)", address, value, value))
  end
  set_status(string.format("Printed %d candidates", count(candidates)))
end

local function take_snapshot()
  snapshot = {}
  for address = 0, RAM_SIZE - 1 do snapshot[address] = read(address) end
  set_status(string.format("Snapshot at frame %d", emu.framecount()))
end

local function print_diff()
  if snapshot == nil then
    set_status("Take a Snapshot first")
    return
  end
  local lines = 0
  for address = 0, RAM_SIZE - 1 do
    local old, new = snapshot[address], read(address)
    if old ~= new then
      console.log(string.format("$%04X: %02X -> %02X (%+d)", address, old, new, new - old))
      lines = lines + 1
    end
  end
  set_status(string.format("Diff: %d byte(s) changed", lines))
end

local form = forms.newform(260, 262, "TMNT RAM probe")
local buttons = {
  { "New",       new_search },
  { "Decreased", function() narrow("Decreased", function(old, new) return new < old end) end },
  { "Increased", function() narrow("Increased", function(old, new) return new > old end) end },
  { "Same",      function() narrow("Same", function(old, new) return new == old end) end },
  { "Changed",   function() narrow("Changed", function(old, new) return new ~= old end) end },
  { "Undo",      undo },
  { "Print",     print_candidates },
  { "Snapshot",  take_snapshot },
  { "Diff",      print_diff },
}
for i, button in ipairs(buttons) do
  local column, row = (i - 1) % 2, math.floor((i - 1) / 2)
  forms.button(form, button[1], button[2], 10 + column * 120, 10 + row * 32, 110, 28)
end
status_label = forms.label(form, "Press New to start", 10, 177, 230, 40)

while true do
  for i, entry in ipairs(WATCH) do
    local value = read(entry[2])
    gui.text(2, 10 + 12 * i, string.format("%-9s $%04X = %02X (%d)", entry[1], entry[2], value, value))
  end
  if candidates ~= nil then
    local list = sorted_candidates()
    gui.text(2, 170, string.format("search: %d candidates", #list))
    for i = 1, math.min(15, #list) do
      local value = read(list[i])
      gui.text(2, 170 + 12 * i, string.format("$%04X = %02X (%d)", list[i], value, value))
    end
  end
  emu.frameadvance()
end
