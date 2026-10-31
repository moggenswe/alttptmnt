-- Checks mailbox candidates while BizHawk 2.6.1 plays TAS 4543M (--movie): writes a marker value into each
-- candidate byte on frame MARK_AT and logs the first frame the game overwrites it. If the game read any of
-- them the TAS would desync, so the area changes are logged too (expected 5499 18596 30041 46072 49799).
-- Candidates come from tools/analyze_tas_ram.py (bytes that never changed during the TAS).
--
-- Run: EmuHawk.exe --movie=<repo>\tas\4543M\tmnt-en.bk2 --lua=<repo>\lua\tmnt_tas_mailbox_check.lua <rom>

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
-- TMNT_MAILBOX_RUNS (e.g. "07F8-07FF,0778-077F") and TMNT_MAILBOX_OUT override the defaults, so several
-- BizHawk instances can test disjoint candidate sets at once.
local OUT = SCRIPT_DIR .. "..\\tas\\4543M\\ramdump\\" .. (os.getenv("TMNT_MAILBOX_OUT") or "mailbox_check.txt")
local MARK_AT = 200
local MARKER = 0xA7
local RUNS = {
  { 0x0388, 0x03AF }, { 0x03F0, 0x03F9 }, { 0x049F, 0x04AF }, { 0x04CF, 0x04DF }, { 0x0600, 0x0603 },
  { 0x060A, 0x0610 }, { 0x0618, 0x0627 }, { 0x064C, 0x064F }, { 0x06B1, 0x06B7 }, { 0x0778, 0x077F },
  { 0x07F8, 0x07FF },
}
local override = os.getenv("TMNT_MAILBOX_RUNS")
if override then
  RUNS = {}
  for first, last in override:gmatch("(%x+)-(%x+)") do RUNS[#RUNS + 1] = { tonumber(first, 16), tonumber(last, 16) } end
end

local log = assert(io.open(OUT, "w"))
local function note(text)
  log:write(text, "\n")
  log:flush()
end

local frame_count = movie.length()
pcall(client.speedmode, 6400)
client.unpause()

local alive = {}
local last_area = memory.readbyte(0x0048, "RAM")
while emu.framecount() < frame_count do
  emu.frameadvance()
  local frame = emu.framecount()
  if frame == MARK_AT then
    for _, run in ipairs(RUNS) do
      for address = run[1], run[2] do
        memory.writebyte(address, MARKER, "RAM")
        alive[address] = true
      end
    end
  elseif frame > MARK_AT then
    for address in pairs(alive) do
      local value = memory.readbyte(address, "RAM")
      if value ~= MARKER then
        note(string.format("overwritten $%04X at frame %d -> %02X", address, frame, value))
        alive[address] = nil
      end
    end
  end
  local area = memory.readbyte(0x0048, "RAM")
  if area ~= last_area then note(string.format("area %d at frame %d", area, frame)) end
  last_area = area
end

for _, run in ipairs(RUNS) do
  local kept = 0
  for address = run[1], run[2] do if alive[address] then kept = kept + 1 end end
  note(string.format("run $%04X-$%04X kept %d of %d", run[1], run[2], kept, run[2] - run[1] + 1))
end
note("done")
log:close()
client.pause()
