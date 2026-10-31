-- Game swap for the TMNT x ALttP stream. Runs in both BizHawk windows (lua\tmnt_stream.luases and
-- lua\alttp_stream.luases). Pressing Select+Start on the controller pauses the game (Start is passed on: it opens
-- the item menu in A Link to the Past and pauses TMNT) and asks tools\game_swap.py to bring the other game's
-- window to the front; game_swap.py then switches OBS to that game's scene.
--
-- The request is a small file, output\swap\<system>-request.txt (system: NES or SNES), holding a token that
-- changes with every press. game_swap.py answers by writing the same token to <system>-ack.txt; without an
-- answer within two seconds BizHawk says so in its on-screen messages (gui.addmessage, which the area select's
-- gui.clearGraphics does not wipe). Every ten seconds the script also rewrites <system>-ready.txt, so
-- game_swap.py can tell which games have the controller swap running.
--
-- Notices the other way: game_swap.py writes lines "<number> <text>" to <system>-notice.txt for the game being
-- played ("TMNT got Rope Pack", "TMNT: Area 3 is open"); each new number is shown once with gui.addmessage.
--
-- Globals for tests: GAME_SWAP_DIR (folder for the files), GAME_SWAP_LIBRARY (return the module, do not loop).

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local M = { dir = GAME_SWAP_DIR or (SCRIPT_DIR .. "..\\output\\swap\\") }

local ACK_FRAMES = 120  -- two seconds
local READY_FRAMES = 600  -- ten seconds
local NOTICE_FRAMES = 15  -- a quarter second
local NO_HELPER = "Game swap: start tools\\game_swap.py"

local system = emu.getsystemid()
local session = tostring(os.time())
local frames = 0
local presses = 0
local waiting_for, waited = nil, 0
local last_message = nil
local combo_held = false
local seen_notice = nil  -- the highest notice number seen; nil until the first look, which shows nothing
local shown = {}

local function say(text)
  last_message = text
  gui.addmessage(text)
end

local function read_file(path)
  local file = io.open(path, "r")
  if not file then return nil end
  local text = file:read("*l")
  file:close()
  return text
end

local function request()
  presses = presses + 1
  local token = session .. "-" .. presses
  local file = io.open(M.dir .. system .. "-request.txt", "w")
  if not file then  -- game_swap.py makes the folder when it starts
    say(NO_HELPER)
    return
  end
  file:write(token)
  file:close()
  waiting_for, waited = token, 0
end

local function heartbeat()
  local file = io.open(M.dir .. system .. "-ready.txt", "w")
  if file then
    file:write(session)
    file:close()
  end
end

local function show_notices()
  local newest = seen_notice or 0
  local file = io.open(M.dir .. system .. "-notice.txt", "r")
  if file then
    for line in file:lines() do
      local number, text = line:match("^(%d+) (.+)$")
      number = tonumber(number)
      if number then
        if seen_notice and number > seen_notice then
          gui.addmessage(text)
          shown[#shown + 1] = text
        end
        newest = math.max(newest, number)
      end
    end
    file:close()
  end
  seen_notice = newest
end

-- One frame of the script. buttons: P1 buttons held this frame, e.g. { Select = true, Start = true }.
function M.frame(buttons)
  if frames % READY_FRAMES == 0 then heartbeat() end
  if frames % NOTICE_FRAMES == 0 then show_notices() end
  frames = frames + 1

  local combo = buttons.Select and buttons.Start
  if combo and not combo_held then request() end
  combo_held = combo and true or false

  if waiting_for then
    waited = waited + 1
    if read_file(M.dir .. system .. "-ack.txt") == waiting_for then
      waiting_for = nil
    elseif waited >= ACK_FRAMES then
      waiting_for = nil
      say(NO_HELPER)
    end
  end
end

function M.message() return last_message end
function M.presses() return presses end
function M.shown() return shown end

-- Physical P1 buttons; the keys may come with or without a "P1 " prefix.
local function read_pad()
  local buttons = {}
  for name, down in pairs(joypad.getimmediate(1) or {}) do
    if down == true then buttons[(name:gsub("^P1 ", ""))] = true end
  end
  return buttons
end

if GAME_SWAP_LIBRARY then return M end

console.log("Game swap ready (" .. system .. "): Select+Start pauses and switches to the other game")
while true do
  M.frame(read_pad())
  emu.frameadvance()
end
