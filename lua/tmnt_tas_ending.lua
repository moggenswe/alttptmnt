-- Plays TAS 4543M to its end in BizHawk 2.6.1 (--movie) and keeps the emulator running without input, to see
-- what the game does after the last hit on Shredder: whether $001B (game phase) reaches 5, the documented
-- "ending" value, and when. Logs every change of $001B and $0048 plus a screenshot every SHOT_EVERY frames.
--
-- Run: EmuHawk.exe --movie=<repo>\tas\4543M\tmnt-en.bk2 --lua=<repo>\lua\tmnt_tas_ending.lua <rom>

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local OUT = SCRIPT_DIR .. "..\\tas\\4543M\\ending\\"
local AFTER_FRAMES = 6000
local SHOT_EVERY = 300
local WATCH = { { "phase", 0x001B }, { "area", 0x0048 }, { "paused", 0x0094 } }

os.execute('mkdir "' .. OUT .. '" 2>nul')
local log = assert(io.open(OUT .. "ending.txt", "w"))
local function note(text)
  log:write(text, "\n")
  log:flush()
end

local function read(address) return memory.readbyte(address, "RAM") end

local frame_count = movie.length()
client.speedmode(1600)  -- 2.6.1 rejects 6400 ("Invalid speed value") and then runs at 100 %
client.unpause()

local last = {}
for _, entry in ipairs(WATCH) do last[entry[1]] = read(entry[2]) end
local function watch(frame)
  for _, entry in ipairs(WATCH) do
    local value = read(entry[2])
    if value ~= last[entry[1]] then
      note(string.format("%d %s=%d->%d", frame, entry[1], last[entry[1]], value))
      last[entry[1]] = value
    end
  end
end

-- BizHawk pauses at the end of a movie, which would also stop this script. So the movie is stopped
-- TAIL_FRAMES early and its last inputs are fed in by hand (stopping one frame early lost the final hit:
-- Shredder caught Donatello instead).
local TAIL_FRAMES = 30
while emu.framecount() < frame_count - TAIL_FRAMES do
  emu.frameadvance()
  if emu.framecount() > frame_count - 2000 then watch(emu.framecount()) end
end
local tail = {}
for frame = emu.framecount(), frame_count - 1 do
  local buttons = {}
  for name, down in pairs(movie.getinput(frame) or {}) do
    if down == true then buttons[(name:gsub("^P1 ", ""))] = true end
  end
  tail[#tail + 1] = buttons
end
movie.stop()
client.unpause()
for _, buttons in ipairs(tail) do
  joypad.set(buttons, 1)
  emu.frameadvance()
  watch(emu.framecount())
end
note(string.format("movie ended at frame %d, phase %d area %d", emu.framecount(), read(0x001B), read(0x0048)))
savestate.save(OUT .. "movie_end.State")
client.screenshot(OUT .. "movie_end.png")

local stop = emu.framecount() + AFTER_FRAMES
while emu.framecount() < stop do
  joypad.set({}, 1)
  emu.frameadvance()
  local frame = emu.framecount()
  watch(frame)
  if frame % SHOT_EVERY == 0 then client.screenshot(string.format("%sf%05d.png", OUT, frame)) end
end
note("done")
log:close()
client.pause()
