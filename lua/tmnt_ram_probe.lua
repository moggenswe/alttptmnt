-- TMNT (NES) RAM probe for the RAM spike (plan Task 1).
--
-- Load in BizHawk: Tools > Lua Console > Script > Open Script.
--   * Shows the WATCH addresses on screen every frame.
--   * K: take a snapshot of all 2 KiB of RAM.
--   * L: print every byte that changed since the snapshot to the Lua console.
--   * J: like L, but only bytes that changed by exactly -1 or +1 (counters, item counts).
-- Built-in narrowing search (works like RAM Search, one key per step):
--   * N: new search - every address is a candidate, current values are remembered.
--   * D: keep candidates that DECREASED since the last step.
--   * I: keep candidates that INCREASED since the last step.
--   * S: keep candidates that stayed the SAME since the last step.
--   The candidate count and the first 15 candidates are drawn on screen; P prints all to the console.
-- Edit WATCH as addresses are found; the values feed apworld/tmnt/ram.py.

local WATCH = {
  -- { "label", 0xADDR },
  { "area",     0x0020 },
  { "hp leo",   0x0077 },
  { "hp mike",  0x0078 },
  { "hp don",   0x0079 },
  { "hp raph",  0x007A },
  { "missiles", 0x0090 },
  { "ropes",    0x0091 },
  { "mailbox0", 0x07F0 },
  { "mailbox1", 0x07F1 },
  { "mailbox2", 0x07F2 },
  { "mailbox3", 0x07F3 },
}

local RAM_SIZE = 0x800
local snapshot = nil
local held = {}

local function pressed(key, keys)
  local now = keys[key] == true
  local edge = now and not held[key]
  held[key] = now
  return edge
end

local function take_snapshot()
  snapshot = {}
  for address = 0, RAM_SIZE - 1 do
    snapshot[address] = memory.readbyte(address, "RAM")
  end
  console.log(string.format("snapshot taken at frame %d", emu.framecount()))
end

local function print_diff(only_steps)
  if snapshot == nil then
    console.log("no snapshot yet: press K first")
    return
  end
  local lines = 0
  for address = 0, RAM_SIZE - 1 do
    local old, new = snapshot[address], memory.readbyte(address, "RAM")
    local delta = new - old
    if old ~= new and (not only_steps or delta == 1 or delta == -1) then
      console.log(string.format("$%04X: %02X -> %02X (%+d)", address, old, new, delta))
      lines = lines + 1
    end
  end
  console.log(string.format("-- %d byte(s) changed --", lines))
end

-- Narrowing search: candidates[address] = value at the last step.
local candidates = nil

local function count_candidates()
  local n = 0
  for _ in pairs(candidates) do n = n + 1 end
  return n
end

local function new_search()
  candidates = {}
  for address = 0, RAM_SIZE - 1 do
    candidates[address] = memory.readbyte(address, "RAM")
  end
  console.log("new search: " .. count_candidates() .. " candidates")
end

local function narrow(label, keep)
  if candidates == nil then
    console.log("no search yet: press N first")
    return
  end
  local kept = {}
  for address, old in pairs(candidates) do
    local new = memory.readbyte(address, "RAM")
    if keep(old, new) then kept[address] = new end
  end
  candidates = kept
  console.log(string.format("%s: %d candidates left", label, count_candidates()))
end

local function sorted_candidates()
  local list = {}
  for address in pairs(candidates) do list[#list + 1] = address end
  table.sort(list)
  return list
end

local function print_candidates()
  if candidates == nil then return end
  for _, address in ipairs(sorted_candidates()) do
    console.log(string.format("$%04X = %02X (%d)", address, candidates[address], candidates[address]))
  end
end

local function draw_candidates()
  if candidates == nil then return end
  local list = sorted_candidates()
  gui.text(2, 170, string.format("search: %d candidates", #list))
  for i = 1, math.min(15, #list) do
    local value = memory.readbyte(list[i], "RAM")
    gui.text(2, 170 + 12 * i, string.format("$%04X = %02X (%d)", list[i], value, value))
  end
end

while true do
  local keys = input.get()
  if pressed("K", keys) then take_snapshot() end
  if pressed("L", keys) then print_diff(false) end
  if pressed("J", keys) then print_diff(true) end
  if pressed("N", keys) then new_search() end
  if pressed("D", keys) then narrow("decreased", function(old, new) return new < old end) end
  if pressed("I", keys) then narrow("increased", function(old, new) return new > old end) end
  if pressed("S", keys) then narrow("same", function(old, new) return new == old end) end
  if pressed("P", keys) then print_candidates() end
  draw_candidates()

  for i, entry in ipairs(WATCH) do
    local value = memory.readbyte(entry[2], "RAM")
    gui.text(2, 10 + 12 * i, string.format("%-9s $%04X = %02X (%d)", entry[1], entry[2], value, value))
  end
  emu.frameadvance()
end
