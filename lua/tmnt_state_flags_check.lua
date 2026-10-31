-- Checks whether progress the area savestates lack matters to the game. The states come from a new game
-- with the area byte rewritten (lua/tmnt_make_area_states.lua), so bytes a real run sets in earlier areas
-- (e.g. $007D after Area 2's bombs) are 0 in them. This plays TAS 4543M in BizHawk 2.6.1 (--movie) and, at
-- frame TMNT_FLAGS_AT inside the area under test, writes the area state's values into those bytes. If the
-- TAS still reaches the next area on the same frame, the game did not read them on the TAS route there.
--
-- Environment (set by tools/state_flags_check.py):
--   TMNT_FLAGS_AT      frame to write on
--   TMNT_FLAGS_UNTIL   frame to stop on (the next area change, or the movie end)
--   TMNT_FLAGS_WRITES  "0074=00,007D=00,..." (hex address = hex value)
--   TMNT_FLAGS_OUT     output file name in tas/4543M/flags/
--
-- Run: EmuHawk.exe --movie=<repo>\tas\4543M\tmnt-en.bk2 --lua=<repo>\lua\tmnt_state_flags_check.lua <rom>

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local OUT_DIR = SCRIPT_DIR .. "..\\tas\\4543M\\flags\\"
os.execute('mkdir "' .. OUT_DIR .. '" 2>nul')

local at = tonumber(os.getenv("TMNT_FLAGS_AT"))
local stop = tonumber(os.getenv("TMNT_FLAGS_UNTIL"))
local writes = {}
for address, value in (os.getenv("TMNT_FLAGS_WRITES") or ""):gmatch("(%x+)=(%x+)") do
  writes[#writes + 1] = { tonumber(address, 16), tonumber(value, 16) }
end

local log = assert(io.open(OUT_DIR .. (os.getenv("TMNT_FLAGS_OUT") or "flags.txt"), "w"))
local function note(text)
  log:write(text, "\n")
  log:flush()
end

client.speedmode(1600)
client.unpause()
local last_area = memory.readbyte(0x0048, "RAM")
while emu.framecount() < stop do
  emu.frameadvance()
  local frame = emu.framecount()
  if frame == at then
    for _, write in ipairs(writes) do memory.writebyte(write[1], write[2], "RAM") end
    note(string.format("wrote %d bytes at frame %d", #writes, frame))
  end
  local area = memory.readbyte(0x0048, "RAM")
  if area ~= last_area then note(string.format("area %d at frame %d", area, frame)) end
  last_area = area
end
-- The RAM at the stop frame, to compare with the unchanged run when there is no later area change.
local parts = {}
for address = 0, 0x7FF do parts[#parts + 1] = string.format("%02x", memory.readbyte(address, "RAM")) end
note("ram " .. emu.framecount() .. " " .. table.concat(parts))
note("done")
log:close()
client.pause()
