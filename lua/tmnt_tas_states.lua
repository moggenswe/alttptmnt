-- Plays TASVideos publication 4543M (NES TMNT by DreamYao, BizHawk 2.6.1, NesHawk) from its input log
-- and drops savestates and screenshots wherever the area ($0048) or game phase ($001B) changes.
-- Used to make the area-start savestates for Task 2/7 without playing the game by hand.
--
-- The movie's LogKey is localised (Chinese button names), so this script reads the log itself
-- instead of letting BizHawk play the .bk2. Column order per frame: |power reset|P1 U D L R St Se B A|P2 ...|
--
-- Run from a freshly booted ROM (frame 0), e.g.:
--   EmuHawk.exe --lua=<repo>\lua\tmnt_tas_states.lua "<repo>\roms\Teenage Mutant Ninja Turtles (USA).nes"
-- Input:  tas/4543M/bk2/Input Log.txt (unzipped from tasvideos.org/4543M?handler=Download)
-- Output: tas/4543M/run/trace.txt, screenshots there, savestates in savestates/tas/

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local REPO = SCRIPT_DIR .. "..\\"
local INPUT_LOG = REPO .. "tas\\4543M\\bk2\\Input Log.txt"
local RUN_DIR = REPO .. "tas\\4543M\\run\\"
local STATE_DIR = REPO .. "savestates\\tas\\"

local BUTTONS = { "Up", "Down", "Left", "Right", "Start", "Select", "B", "A" }
local AREA, PHASE, TURTLE = 0x0048, 0x001B, 0x0067
local HP = { 0x0077, 0x0078, 0x0079, 0x007A }  -- Leo, Raph, Mike, Don (ram.py)
local SCREENSHOT_EVERY = 3000
local MAX_EVENTS = 400

os.execute('mkdir "' .. RUN_DIR .. '" 2>nul')
os.execute('mkdir "' .. STATE_DIR .. '" 2>nul')

local trace = assert(io.open(RUN_DIR .. "trace.txt", "w"))
trace:write("script started\n")
trace:flush()

-- With --movie BizHawk plays the inputs itself (using the movie's sync settings); the script only watches.
-- BizHawk 2.6.1's Lua stalls reading the 1.3 MB log, so it is only parsed when there is no movie.
local native = movie.isloaded()
local frames = {}
local frame_count
if native then
  frame_count = movie.length()
else
  for line in io.lines(INPUT_LOG) do
    local p1 = line:match("^|..|(........)|")
    if p1 then frames[#frames + 1] = p1 end
  end
  frame_count = #frames
end

local function log(text)
  trace:write(text, "\n")
  trace:flush()
  console.log(text)
end

local function read(address) return memory.readbyte(address, "RAM") end

local function status()
  return string.format("area=%d phase=%d turtle=%d hp=%02X,%02X,%02X,%02X", read(AREA), read(PHASE),
    read(TURTLE), read(HP[1]), read(HP[2]), read(HP[3]), read(HP[4]))
end

-- BizHawk has usually run a frame before --lua scripts start; those frames had no input, so the loop
-- below starts at the log line for the current frame (the movie's first lines are empty too).
log(string.format("%d input frames; starting at emulator frame %d", frame_count, emu.framecount()))
log(native and "movie loaded: BizHawk plays the inputs" or "no movie: feeding inputs from the log")
for index = 1, emu.framecount() do
  if not native and frames[index] ~= "........" then log("WARNING: skipped a frame with input, the movie will not sync") end
end
pcall(client.speedmode, 6400)
pcall(emu.limitframerate, false)
client.unpause()

local last_area, last_phase, events = read(AREA), read(PHASE), 0
while emu.framecount() < frame_count do
  local index = emu.framecount() + 1
  if not native then
    local p1 = frames[index]
    local pad = {}
    for i, name in ipairs(BUTTONS) do pad[name] = p1:sub(i, i) ~= "." end
    joypad.set(pad, 1)
  end
  emu.frameadvance()

  local area, phase = read(AREA), read(PHASE)
  local name = nil
  if (area ~= last_area or phase ~= last_phase) and events < MAX_EVENTS then
    events = events + 1
    name = string.format("f%05d_a%d_p%d", index, area, phase)
    savestate.save(STATE_DIR .. name .. ".State")
  elseif index % SCREENSHOT_EVERY == 0 then
    name = string.format("f%05d_tick", index)
  end
  if name then
    client.screenshot(RUN_DIR .. name .. ".png")
    log(string.format("%s %s", name, status()))
  end
  last_area, last_phase = area, phase
end

log("done: " .. status())
trace:close()
client.pause()
