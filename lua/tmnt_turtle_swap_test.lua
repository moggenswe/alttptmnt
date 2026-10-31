-- Tests whether the client can capture the turtle on screen by first switching the active turtle ($0067).
-- Writing 00 to the active turtle's HP starts the death animation (docs/research/tmnt-ram.md, R1), so the
-- area states (Leo active) would kill Leo whenever the player does not own him.
--
-- For each variant: load savestates/area1.State, make the writes, then idle, walk right and open the pause
-- menu, with screenshots and a RAM log in savestates/swap_test/. Variants:
--   control  Leo HP 00 only (expected: death animation)
--   same     $0067 = Raph and Leo HP 00 on the same frame
--   later    $0067 = Raph, one frame later Leo HP 00
--
-- Run in the BizHawk that made the area states (2.11.1):
--   EmuHawk.exe --lua=<repo>\lua\tmnt_turtle_swap_test.lua "<repo>\roms\Teenage Mutant Ninja Turtles (USA).nes"

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local STATE = SCRIPT_DIR .. "..\\savestates\\area1.State"
local OUT = SCRIPT_DIR .. "..\\savestates\\swap_test\\"

local ACTIVE, PHASE, PAUSED = 0x0067, 0x001B, 0x0094
local HP = { 0x0077, 0x0078, 0x0079, 0x007A }  -- Leo, Raph, Mike, Don
local LEO_HP, RAPH = 0x0077, 1

os.execute('mkdir "' .. OUT .. '" 2>nul')
local log = assert(io.open(OUT .. "swap_test.txt", "w"))
local function note(text)
  log:write(text, "\n")
  log:flush()
end

local function read(address) return memory.readbyte(address, "RAM") end
local function write(address, value) memory.writebyte(address, value, "RAM") end

local function status(label)
  note(string.format("  %-14s f%d active=%d hp=%02X %02X %02X %02X phase=%d paused=%d", label, emu.framecount(),
    read(ACTIVE), read(HP[1]), read(HP[2]), read(HP[3]), read(HP[4]), read(PHASE), read(PAUSED)))
end

local function run(frames, buttons, label)
  for i = 1, frames do
    joypad.set(buttons or {}, 1)
    emu.frameadvance()
    if i % 20 == 0 then status(label) end
  end
end

local VARIANTS = {
  { "control", function() write(LEO_HP, 0) end },
  { "same", function() write(ACTIVE, RAPH); write(LEO_HP, 0) end },
  { "later", function() write(ACTIVE, RAPH); emu.frameadvance(); write(LEO_HP, 0) end },
}

pcall(client.speedmode, 400)
client.unpause()

for _, variant in ipairs(VARIANTS) do
  local name, apply = variant[1], variant[2]
  note("== " .. name)
  savestate.load(STATE)
  status("before")
  apply()
  status("after write")
  run(120, nil, "idle")
  client.screenshot(OUT .. name .. "_1_idle.png")
  run(60, { Right = true }, "walk")
  client.screenshot(OUT .. name .. "_2_walk.png")
  run(2, { Start = true }, "start")
  run(90, nil, "pause")
  client.screenshot(OUT .. name .. "_3_pause.png")
end

note("done")
log:close()
client.pause()
