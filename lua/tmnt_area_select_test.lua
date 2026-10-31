-- Automatic test of lua/tmnt_area_select.lua (plan Task 7, Review Focus 3) without a player or an AP client:
-- loads the selector as a library, plays the client's part by writing the mailbox, feeds it buttons and
-- checks RAM after each step. Results go to savestates/area_select_test/result.txt, one PASS/FAIL per line.
--
-- Run from a freshly booted ROM in the BizHawk that made the area states (2.11.1):
--   EmuHawk.exe --lua=<repo>\lua\tmnt_area_select_test.lua "<repo>\roms\Teenage Mutant Ninja Turtles (USA).nes"

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local OUT = SCRIPT_DIR .. "..\\savestates\\area_select_test\\"

TMNT_AREA_SELECT_LIBRARY = true
local select = dofile(SCRIPT_DIR .. "tmnt_area_select.lua")

local PASSES, COUNTER, ACK, MAGIC = 0x0388, 0x0389, 0x038A, 0x038B
local AREA, ACTIVE = 0x0048, 0x0067
local HP = { 0x0077, 0x0078, 0x0079, 0x007A }

local function next_counter(counter) return counter % 255 + 1 end

os.execute('mkdir "' .. OUT .. '" 2>nul')
local log = assert(io.open(OUT .. "result.txt", "w"))
local failures = 0
local function check(ok, what)
  if not ok then failures = failures + 1 end
  log:write(ok and "PASS " or "FAIL ", what, "\n")
  log:flush()
end

local function read(address) return memory.readbyte(address, "RAM") end
local function write(address, value) memory.writebyte(address, value, "RAM") end

-- The buttons reach the game too, as a player's would; the selector holds them back while its menu is open.
local function step(buttons, frames)
  for _ = 1, frames or 1 do
    joypad.set(buttons, 1)
    select.frame(buttons)
    emu.frameadvance()
  end
end

local function press(buttons)
  step(buttons)
  step({})
end

local function open_menu()
  step({ Select = true })
  press({ Select = true, Up = true })
end

local function mailbox(passes, counter, ack)
  write(PASSES, passes)
  write(COUNTER, counter)
  write(ACK, ack)
  write(MAGIC, 0xA7)
end

pcall(client.speedmode, 800)
client.unpause()
step({}, 300)  -- title screen; nothing is loaded and the client has not written anything

-- No client: the menu stays shut.
open_menu()
check(not select.is_open(), "menu stays shut without the magic byte")
check(select.message() == "Anslut AP-klienten", "asks for the AP client without the magic byte")

-- Client connected with only Area 1 playable.
mailbox(0x01, 0, 0)
open_menu()
check(select.is_open(), "Select+Up opens the menu once the magic byte is there")
client.screenshot(OUT .. "menu.png")
press({ Down = true })
press({ Down = true })
press({ A = true })
check(select.is_open(), "a locked area keeps the menu open")
check(select.message() == "Låst", "a locked area says Låst")
check(read(COUNTER) == 0, "a locked area loads nothing (counter still 0)")
press({ B = true })
check(not select.is_open(), "B closes the menu")

-- Loading Area 1.
open_menu()
press({ A = true })
check(not select.is_open(), "loading closes the menu")
check(read(AREA) == 0, "Area 1 is loaded (area byte 0)")
check(read(COUNTER) == 1, "the load counter goes 0 -> 1")
check(read(PASSES) == 0x01 and read(MAGIC) == 0xA7 and read(ACK) == 0, "passes, ack and magic survive the load")
step({}, 30)
client.screenshot(OUT .. "area1.png")

-- The counter skips 0.
write(COUNTER, 255)
open_menu()
press({ A = true })
check(read(COUNTER) == 1, "the load counter wraps 255 -> 1")

-- Boss beaten, next area locked: the menu is forced open.
step({}, 10)
write(AREA, 1)
step({}, 60)
check(not select.is_open() and read(COUNTER) == 1, "nothing happens before the client has seen the boss win")
step({}, 70)
check(select.is_open() and select.is_forced(), "a locked next area forces the menu open")
press({ B = true })
check(select.is_open(), "B cannot close a forced menu")
press({ A = true })
check(not select.is_open() and not select.is_forced(), "loading an area ends the forced menu")
check(read(AREA) == 0 and read(COUNTER) == 2, "the forced menu loaded Area 1")

-- Boss beaten, next area unlocked: counted as a load after the delay, no menu.
write(PASSES, 0x03)
step({}, 10)
write(AREA, 1)
step({}, 60)
check(read(COUNTER) == 2, "counter unchanged while the client reads the boss win")
step({}, 70)
check(not select.is_open() and read(COUNTER) == 3, "an unlocked next area counts as a load")

-- Every area loads its own state.
write(PASSES, 0x3F)
for area = 1, 6 do
  open_menu()
  for _ = 2, area do press({ Down = true }) end
  press({ A = true })
  step({}, 5)
  check(read(AREA) == area - 1, "Area " .. area .. " loads (area byte " .. read(AREA) .. ")")
end

-- Up from Area 1 wraps to Area 6.
open_menu()
press({ Up = true })
press({ A = true })
check(read(AREA) == 5, "Up from Area 1 wraps to Area 6")

-- A real game over and continue in Area 1 counts as one load, once the game has refilled every turtle.
open_menu()
press({ A = true })
local before = read(COUNTER)
step({ Left = true }, 40)  -- down the manhole left of the start; HP 0 does nothing on the map
step({}, 200)
for id, address in ipairs(HP) do write(address, id - 1 == read(ACTIVE) and 1 or 0) end
step({ Down = true }, 60)
for _ = 1, 6 do
  step({ Right = true }, 60)
  step({ Left = true }, 60)
end
step({}, 300)
check(read(COUNTER) == before, "the game over itself is not a load")
check(not select.is_open(), "no menu at the game over")
press({ Start = true })  -- CONTINUE; the menu is shut, so the game gets the button
step({}, 300)
check(read(COUNTER) == next_counter(before), "continue counts as a load (counter " .. read(COUNTER) .. ")")
check(read(AREA) == 0 and not select.is_open(), "continue stays in Area 1 without a menu")

-- A new game from the title screen forces the menu open.
client.reboot_core()
local started = false
for frame = 1, 900 do
  if frame == 30 then mailbox(0x01, 7, 7) end  -- after the game's own RAM setup
  -- Start skips the intro and starts the game, as in lua/tmnt_make_area_states.lua.
  if (frame >= 4 and frame <= 5) or (frame >= 10 and frame <= 11) then joypad.set({ Start = true }, 1) end
  select.frame({})
  emu.frameadvance()
  if select.is_forced() then started = true break end
end
check(started, "a new game from the title screen forces the menu open")
press({ A = true })
-- The new game refills every turtle after the continue byte moved at power-on, which counts as a load too,
-- so the counter may be past 8. Any count is fine as long as it moved.
check(read(AREA) == 0 and read(COUNTER) >= 8 and not select.is_open(), string.format(
  "the forced menu then loads Area 1 (area byte %d, counter %d, magic %02X)", read(AREA), read(COUNTER), read(MAGIC)))

log:write(failures == 0 and "ALL PASS\n" or string.format("%d FAILED\n", failures))
log:write("done\n")
log:close()
client.pause()
