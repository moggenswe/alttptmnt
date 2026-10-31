-- Test for game_swap.lua, in BizHawk with any NES or SNES game loaded:
--   EmuHawk.exe --lua=<repo>\lua\game_swap_test.lua <rom>
-- Writes PASS/FAIL lines to savestates\game_swap_test\<system>-result.txt and closes BizHawk.

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local DIR = SCRIPT_DIR .. "..\\savestates\\game_swap_test\\"
os.execute('mkdir "' .. DIR .. '" 2>nul')
local system = emu.getsystemid()
for _, name in ipairs({ "-request.txt", "-ack.txt", "-ready.txt" }) do os.remove(DIR .. system .. name) end

GAME_SWAP_DIR, GAME_SWAP_LIBRARY = DIR, true
local swap = dofile(SCRIPT_DIR .. "game_swap.lua")
GAME_SWAP_LIBRARY = nil

local lines, failed = {}, 0
local function check(name, ok)
  lines[#lines + 1] = (ok and "PASS " or "FAIL ") .. name
  if not ok then failed = failed + 1 end
end
local function read(name)
  local file = io.open(DIR .. system .. name, "r")
  if not file then return nil end
  local text = file:read("*l")
  file:close()
  return text
end
local function frames(n, buttons)
  for _ = 1, n do
    swap.frame(buttons or {})
    emu.frameadvance()
  end
end

frames(5, { Select = true })
check("the script says it runs", read("-ready.txt") ~= nil)
check("Select alone asks for nothing", read("-request.txt") == nil)
frames(5, { Start = true })
check("Start alone asks for nothing", read("-request.txt") == nil)
frames(1, { Select = true, Start = true })
local first = read("-request.txt")
check("Select+Start writes a request", first ~= nil and swap.presses() == 1)
frames(30, { Select = true, Start = true })
check("holding the combo asks once", swap.presses() == 1 and read("-request.txt") == first)

-- Answered like tools\game_swap.py does: no complaint.
local ack = io.open(DIR .. system .. "-ack.txt", "w")
ack:write(first)
ack:close()
frames(130)
check("an answered request shows no message", swap.message() == nil)

frames(1, { Select = true, Start = true })
local second = read("-request.txt")
check("a new press writes a new token", second ~= nil and second ~= first and swap.presses() == 2)
frames(125)
check("an unanswered request says to start the helper",
      swap.message() ~= nil and swap.message():find("game_swap.py", 1, true) ~= nil)

lines[#lines + 1] = failed == 0 and "ALL PASS" or (failed .. " FAILED")
local out = io.open(DIR .. system .. "-result.txt", "w")
out:write(table.concat(lines, "\n") .. "\n")
out:close()
client.exit()
