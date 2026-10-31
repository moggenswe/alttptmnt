-- Plays the player's part in tools/e2e_run.py: runs next to Archipelago's connector_bizhawk_generic.lua
-- (lua/tmnt_e2e.luases), drives lua/tmnt_area_select.lua with scripted buttons and logs what the AP client
-- writes. It talks to e2e_run.py through files in the folder given by TMNT_E2E_DIR:
--   driver.txt      what happened, one line per step
--   want_send.txt   "Donatello" when the server should /send that item (e2e_run.py deletes it when sent)
--   done.txt        written last
-- Seed assumptions (output/tmnt_only/tmnt.yaml, seed 11): start Raphael + Area 1 pass; the two free start
-- locations give the Area 2 and Area 3 passes; Area 1's entrance holds Zora's Scuba Kit.

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local DIR = (os.getenv("TMNT_E2E_DIR") or (SCRIPT_DIR .. "..\\output\\e2e")) .. "\\"

TMNT_AREA_SELECT_LIBRARY = true
local select = dofile(SCRIPT_DIR .. "tmnt_area_select.lua")

local PASSES, COUNTER, ACK, MAGIC = 0x0388, 0x0389, 0x038A, 0x038B
local AREA, ACTIVE = 0x0048, 0x0067
local HP = { 0x0077, 0x0078, 0x0079, 0x007A }  -- Leo, Raph, Mike, Don
local MISSILES, ROPES = 0x00BF, 0x00A7

local log = assert(io.open(DIR .. "driver.txt", "w"))
local function note(text)
  log:write(string.format("f%-6d %s\n", emu.framecount(), text))
  log:flush()
end

local function read(address) return memory.readbyte(address, "RAM") end

local function ram_line()
  return string.format("mail=%02X %02X %02X %02X area=%d active=%d hp=%02X %02X %02X %02X missiles=%d ropes=%d",
    read(PASSES), read(COUNTER), read(ACK), read(MAGIC), read(AREA), read(ACTIVE),
    read(HP[1]), read(HP[2]), read(HP[3]), read(HP[4]), read(MISSILES), read(ROPES))
end

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

local function wait_for(what, condition, frames)
  for _ = 1, frames do
    if condition() then
      note("ok: " .. what .. " | " .. ram_line())
      return true
    end
    step({})
  end
  note("TIMEOUT: " .. what .. " | " .. ram_line())
  return false
end

local function load_area(area)
  step({ Select = true })
  press({ Select = true, Up = true })
  for _ = 2, area do press({ Down = true }) end
  press({ A = true })
end

local function file_exists(path)
  local file = io.open(path, "r")
  if file then file:close() end
  return file ~= nil
end

client.unpause()
note("driver started | " .. ram_line())
step({}, 60)

-- 1. The client connects and writes its magic byte and the pass mask (Area 1 only: no Scuba Kit yet).
wait_for("client wrote the magic byte", function() return read(MAGIC) == 0xA7 end, 60 * 120)
wait_for("pass mask has Area 1", function() return read(PASSES) & 0x01 ~= 0 end, 60 * 10)

-- 2. Load Area 1 from the menu, alongside the connector.
load_area(1)
note("loaded Area 1 | " .. ram_line())
wait_for("client acked the load (ack == counter)", function() return read(ACK) == read(COUNTER) end, 60 * 5)
step({}, 60)
note("after full sync | " .. ram_line())
-- The state has Leo on screen, whom the player does not own: the client switches to Raphael and captures Leo.
wait_for("Raphael active, Leo and Mike captured", function()
  return read(ACTIVE) == 1 and read(HP[1]) == 0 and read(HP[2]) == 0x80 and read(HP[3]) == 0
end, 60 * 5)
-- Area 1's entrance check gives Zora's Scuba Kit, which with the Area 2 pass unlocks Area 2.
wait_for("Area 2 unlocked by the entrance check", function() return read(PASSES) & 0x02 ~= 0 end, 60 * 10)

-- 3. An item sent mid-area frees the turtle at once.
local want = assert(io.open(DIR .. "want_send.txt", "w"))
want:write("Donatello\n")
want:close()
wait_for("server sent Donatello", function() return not file_exists(DIR .. "want_send.txt") end, 60 * 30)
wait_for("Donatello has full HP", function() return read(HP[4]) == 0x80 end, 60 * 10)

-- 4. A locked area does not load (Area 3 needs Missile Pack and Rope Pack).
local counter = read(COUNTER)
load_area(3)
note(string.format("tried Area 3: message=%s counter %d -> %d | %s", tostring(select.message()), counter,
  read(COUNTER), ram_line()))
press({ B = true })

-- 5. Boss win: the area byte moves 0 -> 1 with the counter unchanged. Area 2 is unlocked, so after the
-- delay the selector counts it as a load and the client does a full sync.
counter = read(COUNTER)
memory.writebyte(AREA, 1, "RAM")
step({}, 60)
note(string.format("boss win written, counter still %d | %s", read(COUNTER), ram_line()))
wait_for("selector counted the advance as a load", function() return read(COUNTER) ~= counter end, 60 * 5)
step({}, 120)
note("end | " .. ram_line())

local done = assert(io.open(DIR .. "done.txt", "w"))
done:write("done\n")
done:close()
log:close()
while true do step({}) end
