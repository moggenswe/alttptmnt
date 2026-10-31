-- Watches all 2 KiB of RAM while BizHawk plays TAS 4543M (--movie, BizHawk 2.6.1 only; see
-- docs/research/tmnt-ram.md) and writes what tools/analyze_tas_ram.py needs:
--   dumps.txt   "<frame> <4096 hex chars>" every DUMP_EVERY frames
--   watch.txt   "<frame> <name>=<old>-><new>" whenever a WATCH byte changes
--   changes.txt per address: how many frames it changed on after TRACK_FROM, plus first and last value
--
-- Run: EmuHawk.exe --movie=<repo>\tas\4543M\tmnt-en.bk2 --lua=<repo>\lua\tmnt_tas_ram_dump.lua <rom>

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local OUT = SCRIPT_DIR .. "..\\tas\\4543M\\ramdump\\"
local RAM_SIZE = 0x800
local DUMP_EVERY = 5
local TRACK_FROM = 200  -- after the title screen; earlier writes are power-on setup
local WATCH = {
  { "area", 0x0048 }, { "phase", 0x001B }, { "turtle", 0x0067 },
  { "hp_leo", 0x0077 }, { "hp_raph", 0x0078 }, { "hp_mike", 0x0079 }, { "hp_don", 0x007A },
  { "missiles", 0x00BF }, { "ropes", 0x00A7 },
  { "weapon_leo", 0x00A8 }, { "weapon_raph", 0x00A9 }, { "weapon_mike", 0x00AA }, { "weapon_don", 0x00AB },
}

os.execute('mkdir "' .. OUT .. '" 2>nul')
local dumps = assert(io.open(OUT .. "dumps.txt", "w"))
local watch = assert(io.open(OUT .. "watch.txt", "w"))

local HEX = {}
for value = 0, 255 do HEX[value] = string.format("%02x", value) end

local function snapshot()
  local raw = memory.readbyterange(0, RAM_SIZE, "RAM")
  local base = raw[0] ~= nil and 0 or 1  -- 0-based in older BizHawk, 1-based in newer
  local ram = {}
  for address = 0, RAM_SIZE - 1 do ram[address] = raw[address + base] end
  return ram
end

local frame_count = movie.length()
pcall(client.speedmode, 6400)
client.unpause()

local previous = snapshot()
local change_count, first_value = {}, {}
for address = 0, RAM_SIZE - 1 do change_count[address] = 0 end

while emu.framecount() < frame_count do
  emu.frameadvance()
  local frame = emu.framecount()
  local ram = snapshot()

  for _, entry in ipairs(WATCH) do
    local name, address = entry[1], entry[2]
    if ram[address] ~= previous[address] then
      watch:write(string.format("%d %s=%d->%d\n", frame, name, previous[address], ram[address]))
    end
  end

  if frame == TRACK_FROM then
    for address = 0, RAM_SIZE - 1 do first_value[address] = ram[address] end
  elseif frame > TRACK_FROM then
    for address = 0, RAM_SIZE - 1 do
      if ram[address] ~= previous[address] then change_count[address] = change_count[address] + 1 end
    end
  end

  if frame % DUMP_EVERY == 0 then
    local parts = {}
    for address = 0, RAM_SIZE - 1 do parts[address + 1] = HEX[ram[address]] end
    dumps:write(frame, " ", table.concat(parts), "\n")
  end
  previous = ram
end

local changes = assert(io.open(OUT .. "changes.txt", "w"))
for address = 0, RAM_SIZE - 1 do
  changes:write(string.format("%04x %d %d %d\n", address, change_count[address], first_value[address] or -1,
    previous[address]))
end
changes:close()
dumps:close()
watch:close()
local done = assert(io.open(OUT .. "done.txt", "w"))
done:write("frames ", emu.framecount(), "\n")
done:close()
client.pause()
