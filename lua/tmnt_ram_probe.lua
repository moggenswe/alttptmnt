-- TMNT (NES) RAM probe for the RAM spike (plan Task 1).
--
-- Load in BizHawk: Tools > Lua Console > Script > Open Script.
--   * Shows the WATCH addresses on screen every frame.
--   * K: take a snapshot of all 2 KiB of RAM.
--   * L: print every byte that changed since the snapshot to the Lua console.
--   * J: like L, but only bytes that changed by exactly -1 or +1 (counters, item counts).
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

while true do
  local keys = input.get()
  if pressed("K", keys) then take_snapshot() end
  if pressed("L", keys) then print_diff(false) end
  if pressed("J", keys) then print_diff(true) end

  for i, entry in ipairs(WATCH) do
    local value = memory.readbyte(entry[2], "RAM")
    gui.text(2, 10 + 12 * i, string.format("%-9s $%04X = %02X (%d)", entry[1], entry[2], value, value))
  end
  emu.frameadvance()
end
