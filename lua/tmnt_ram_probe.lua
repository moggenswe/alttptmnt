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
-- Snapshot / Diff: Snapshot remembers all RAM; Diff writes changed bytes to docs/research/diff.txt.
-- Track unused / Print unused: drops every byte that changes on any frame; what is left after a long
-- play session is a mailbox candidate. Print writes runs of 4+ to docs/research/unused_ram.txt.
--
-- The WATCH addresses and the first 15 candidates are drawn on the game screen.
-- Edit WATCH as addresses are found; the values feed apworld/tmnt/ram.py.

local WATCH = {
  -- { "label", 0xADDR },  (source: adelikat/JXQ TMNT.xls RAM sheet; see apworld/tmnt/ram.py)
  { "world",     0x0048 },
  { "phase",     0x001B },
  { "turtle",    0x0067 },
  { "hp leo",    0x0077 },
  { "hp raph",   0x0078 },
  { "hp mike",   0x0079 },
  { "hp don",    0x007A },
  { "missiles",  0x00BF },
  { "ropes",     0x00A7 },
  { "mbox $388", 0x0388 },
  { "mbox $389", 0x0389 },
  { "mbox $38A", 0x038A },
  { "mbox $38B", 0x038B },
}

local RAM_SIZE = 0x800
local DIFF_PRINT_LIMIT = 60  -- BizHawk's Lua console stops printing ("Flood warning") above ~100 lines
-- Results go to docs/research/ next to this script's lua/ folder.
local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local OUTPUT_DIR = SCRIPT_DIR .. "..\\docs\\research\\"

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
  local lines = {}
  for address = 0, RAM_SIZE - 1 do
    local old, new = snapshot[address], read(address)
    if old ~= new then
      lines[#lines + 1] = string.format("$%04X: %02X -> %02X (%+d)", address, old, new, new - old)
    end
  end
  local file = io.open(OUTPUT_DIR .. "diff.txt", "w")
  if file ~= nil then
    file:write(table.concat(lines, "\n") .. "\n")
    file:close()
    set_status(string.format("Diff: %d byte(s) changed -> docs/research/diff.txt", #lines))
  else
    for i = 1, math.min(#lines, DIFF_PRINT_LIMIT) do console.log(lines[i]) end
    set_status(string.format("Diff: %d byte(s) changed (first %d in Output)", #lines,
                             math.min(#lines, DIFF_PRINT_LIMIT)))
  end
end

-- Unused-byte tracking: every frame, any address whose value differs from its value at the start is
-- dropped. What survives a long play session is a candidate for the client's mailbox.
local untouched_start, untouched, tracked_frames = nil, nil, 0

local function read_all()
  if memory.read_bytes_as_array ~= nil then
    local bytes = memory.read_bytes_as_array(0, RAM_SIZE, "RAM")
    local out = {}
    for address = 0, RAM_SIZE - 1 do out[address] = bytes[address + 1] end
    return out
  end
  local out = {}
  for address = 0, RAM_SIZE - 1 do out[address] = read(address) end
  return out
end

local function track_unused()
  untouched_start, untouched, tracked_frames = read_all(), {}, 0
  for address = 0, RAM_SIZE - 1 do untouched[address] = true end
  set_status("Tracking unused bytes: now play (rooms, fights, pause, death)")
end

local function update_unused()
  if untouched == nil then return end
  local now = read_all()
  for address in pairs(untouched) do
    if now[address] ~= untouched_start[address] then untouched[address] = nil end
  end
  tracked_frames = tracked_frames + 1
end

local function print_unused()
  if untouched == nil then
    set_status("Press Track unused first")
    return
  end
  local lines, start = {}, nil
  for address = 0, RAM_SIZE do
    local free = address < RAM_SIZE and untouched[address]
    if free and start == nil then start = address end
    if not free and start ~= nil then
      if address - start >= 4 then
        lines[#lines + 1] = string.format("$%04X-$%04X (%d bytes, value %02X)", start, address - 1,
                                          address - start, untouched_start[start])
      end
      start = nil
    end
  end
  local summary = string.format("%d untouched bytes after %d frames; %d runs of 4+",
                                count(untouched), tracked_frames, #lines)
  local file = io.open(OUTPUT_DIR .. "unused_ram.txt", "w")
  if file ~= nil then
    file:write(summary .. "\n" .. table.concat(lines, "\n") .. "\n")
    file:close()
    set_status(summary .. " -> docs/research/unused_ram.txt")
  else
    for i = 1, math.min(#lines, DIFF_PRINT_LIMIT) do console.log(lines[i]) end
    set_status(summary .. " (could not write file; first lines in Output)")
  end
end

local form = forms.newform(260, 326, "TMNT RAM probe")
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
  { "Track unused", track_unused },
  { "Print unused", print_unused },
}
for i, button in ipairs(buttons) do
  local column, row = (i - 1) % 2, math.floor((i - 1) / 2)
  forms.button(form, button[1], button[2], 10 + column * 120, 10 + row * 32, 110, 28)
end
status_label = forms.label(form, "Press New to start", 10, 241, 230, 40)

while true do
  update_unused()
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
