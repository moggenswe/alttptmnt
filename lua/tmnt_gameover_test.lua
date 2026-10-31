-- Tests what pause, game over, continue and running out of continues do to the mailbox ($0388-$038B) and to
-- the turtles' HP, which the TAS never shows (docs/research/tmnt-ram.md). From savestates/area1.State it
-- writes a mailbox (passes 1F, counter 3, ack 3, magic A7), pauses, then twice walks into the first
-- sewer and lets the enemies kill every turtle: once with continues left and once with $0046 = 0. Logs RAM and
-- screenshots to savestates/gameover_test/.
--
-- Run in the BizHawk that made the area states (2.11.1):
--   EmuHawk.exe --lua=<repo>\lua\tmnt_gameover_test.lua "<repo>\roms\Teenage Mutant Ninja Turtles (USA).nes"

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local STATE = SCRIPT_DIR .. "..\\savestates\\area1.State"
local OUT = SCRIPT_DIR .. "..\\savestates\\gameover_test\\"

local MAILBOX = 0x0388  -- see apworld/tmnt/ram.py
local MAIL = { 0x1F, 0x03, 0x03, 0xA7 }
local ACTIVE, PHASE, AREA, PAUSED, CONTINUES = 0x0067, 0x001B, 0x0048, 0x0094, 0x0046
local HP = { 0x0077, 0x0078, 0x0079, 0x007A }

os.execute('mkdir "' .. OUT .. '" 2>nul')
local log = assert(io.open(OUT .. "gameover_test.txt", "w"))
local function note(text)
  log:write(text, "\n")
  log:flush()
end

local function read(address) return memory.readbyte(address, "RAM") end

local last_line
local function status(label)
  local line = string.format("mail=%02X %02X %02X %02X active=%d hp=%02X %02X %02X %02X phase=%d area=%d paused=%d cont=%d",
    read(MAILBOX), read(MAILBOX + 1), read(MAILBOX + 2), read(MAILBOX + 3), read(ACTIVE),
    read(HP[1]), read(HP[2]), read(HP[3]), read(HP[4]), read(PHASE), read(AREA), read(PAUSED), read(CONTINUES))
  if line ~= last_line then note(string.format("%-10s f%-6d %s", label, emu.framecount(), line)) end
  last_line = line
end

local shot = 0
local function run(frames, buttons, label, shot_every)
  for i = 1, frames do
    joypad.set(buttons or {}, 1)
    emu.frameadvance()
    status(label)
    if shot_every and i % shot_every == 0 then
      shot = shot + 1
      client.screenshot(string.format("%s%03d_%s.png", OUT, shot, label))
    end
  end
end

local function press(button, label)
  run(2, { [button] = true }, label)
  run(30, nil, label)
end

local function kill_all(label)
  -- HP 0 alone kills nobody (the game checks HP when a hit lands), and zeroing the turtle on screen is
  -- what R1 warned about. So: the others to 0, the one on screen to 1, then walk into the enemies.
  for id, address in ipairs(HP) do
    memory.writebyte(address, id - 1 == read(ACTIVE) and 1 or 0, "RAM")
  end
  run(60, { Down = true }, label .. "_down")
  for _ = 1, 6 do
    run(60, { Right = true }, label, 60)
    run(60, { Left = true }, label, 60)
  end
end

pcall(client.speedmode, 400)
client.unpause()

local function play_until_game_over(label, continues)
  savestate.load(STATE)
  for i, value in ipairs(MAIL) do memory.writebyte(MAILBOX + i - 1, value, "RAM") end
  if continues then memory.writebyte(CONTINUES, continues, "RAM") end
  status(label .. "_start")
  -- HP 0 does nothing on the overworld map, so go down the manhole left of the start first.
  run(40, { Left = true }, label .. "_to_sewer")
  run(200, nil, label .. "_sewer", 100)
  kill_all(label .. "_death")
  run(300, nil, label .. "_over", 100)
  press("Start", label .. "_continue")  -- the cursor starts on CONTINUE
  run(600, nil, label .. "_after", 100)
end

savestate.load(STATE)
for i, value in ipairs(MAIL) do memory.writebyte(MAILBOX + i - 1, value, "RAM") end
press("Start", "pause")
run(60, nil, "paused", 60)
press("Start", "unpause")

play_until_game_over("cont3")
play_until_game_over("cont0", 0)

note("done")
log:close()
client.pause()
