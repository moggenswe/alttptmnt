-- Makes savestates/area1.State ... area6.State for the area select (plan Task 7) in the BizHawk that runs it.
--
-- How: a new game sets the area byte $0048 to 0 on the frame the game phase $001B becomes 3 and loads the
-- area a few frames later. Writing N-1 to $0048 on that frame and the next two makes the game load Area N
-- instead (found 2026-10-31: writing 2 loaded Area 3 with the Party Wagon). Each state is saved
-- SETTLE_FRAMES after that, with a screenshot next to it to check by eye.
--
-- Run from a freshly booted ROM, e.g.:
--   EmuHawk.exe --lua=<repo>\lua\tmnt_make_area_states.lua "<repo>\roms\Teenage Mutant Ninja Turtles (USA).nes"
-- States are tied to the BizHawk version that made them, so make them in the version used on stream.

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local STATE_DIR = SCRIPT_DIR .. "..\\savestates\\"

local AREA, PHASE = 0x0048, 0x001B  -- see apworld/tmnt/ram.py
local PHASE_AREA_LOAD = 3
local WRITE_FRAMES = 3
local SETTLE_FRAMES = 120
local AREAS = 6

os.execute('mkdir "' .. STATE_DIR .. '" 2>nul')
local log = assert(io.open(STATE_DIR .. "make_area_states.txt", "w"))
local function note(text)
  log:write(text, "\n")
  log:flush()
  console.log(text)
end

local function read(address) return memory.readbyte(address, "RAM") end

pcall(client.speedmode, 800)
client.unpause()

-- Start skips the intro (as the TAS does on frames 4 and 8); without it the attract mode loops.
-- Run to the frame before the area load and keep it as the starting point for every area.
while read(PHASE) ~= PHASE_AREA_LOAD - 1 do
  local f = emu.framecount()
  joypad.set({ Start = (f >= 4 and f <= 5) or (f >= 10 and f <= 11) }, 1)
  emu.frameadvance()
  if emu.framecount() > 600 then error("no area load within 600 frames") end
end
local base = STATE_DIR .. "base_before_area_load.State"
savestate.save(base)
note(string.format("base state at frame %d", emu.framecount()))

for area = 1, AREAS do
  savestate.load(base)
  while read(PHASE) ~= PHASE_AREA_LOAD do emu.frameadvance() end
  for _ = 1, WRITE_FRAMES do
    memory.writebyte(AREA, area - 1, "RAM")
    emu.frameadvance()
  end
  for _ = 1, SETTLE_FRAMES do emu.frameadvance() end
  local name = "area" .. area
  savestate.save(STATE_DIR .. name .. ".State")
  client.screenshot(STATE_DIR .. name .. ".png")
  note(string.format("%s: frame %d area byte %d phase %d", name, emu.framecount(), read(AREA), read(PHASE)))
end

os.remove(base)
note("done")
log:close()
client.pause()
