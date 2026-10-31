-- Counts how many game overs the game allows: from savestates/area1.State, lets the enemies in the first
-- sewer kill every turtle, picks CONTINUE, and repeats GAME_OVERS times, logging $0046 (continues) and
-- whether the area came back with full HP. Run it on the clean ROM and on a patched one (rom.py makes
-- continues unlimited) to compare. Log: savestates/continue_test/<TMNT_CONTINUE_OUT or result.txt>.
--
-- Run: EmuHawk.exe --lua=<repo>\lua\tmnt_continue_test.lua <rom>

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local STATE = SCRIPT_DIR .. "..\\savestates\\area1.State"
local OUT = SCRIPT_DIR .. "..\\savestates\\continue_test\\"
local GAME_OVERS = 5

local ACTIVE, PHASE, CONTINUES = 0x0067, 0x001B, 0x0046
local HP = { 0x0077, 0x0078, 0x0079, 0x007A }

os.execute('mkdir "' .. OUT .. '" 2>nul')
local log = assert(io.open(OUT .. (os.getenv("TMNT_CONTINUE_OUT") or "result.txt"), "w"))
local function note(text)
  log:write(text, "\n")
  log:flush()
end

local function read(address) return memory.readbyte(address, "RAM") end

local function run(frames, buttons)
  for _ = 1, frames do
    joypad.set(buttons or {}, 1)
    emu.frameadvance()
  end
end

local function hp_line()
  return string.format("hp=%02X %02X %02X %02X cont=%d phase=%d", read(HP[1]), read(HP[2]), read(HP[3]), read(HP[4]),
    read(CONTINUES), read(PHASE))
end

pcall(client.speedmode, 800)
client.unpause()
savestate.load(STATE)
note("start " .. hp_line())
for round = 1, GAME_OVERS do
  run(40, { Left = true })  -- down the manhole left of the start
  run(200)
  -- HP 0 kills nobody by itself: the others to 0, the one on screen to 1, then walk into the enemies.
  for id, address in ipairs(HP) do memory.writebyte(address, id - 1 == read(ACTIVE) and 1 or 0, "RAM") end
  run(60, { Down = true })
  for _ = 1, 6 do
    run(60, { Right = true })
    run(60, { Left = true })
  end
  run(300)
  client.screenshot(string.format("%sround%d_over.png", OUT, round))
  run(2, { Start = true })  -- the cursor starts on CONTINUE
  run(400)
  client.screenshot(string.format("%sround%d_after.png", OUT, round))
  local back = read(HP[1]) == 0x80 and read(HP[2]) == 0x80
  note(string.format("game over %d: %s -> %s", round, back and "CONTINUED (full HP)" or "NOT continued", hp_line()))
end
note("done")
log:close()
client.pause()
