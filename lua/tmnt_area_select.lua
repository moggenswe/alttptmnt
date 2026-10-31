-- Area select for the TMNT Archipelago slot (plan Task 7). Runs in BizHawk next to Archipelago's
-- connector_bizhawk_generic.lua (open both in the Lua console, or lua/tmnt_stream.luases).
--
-- Select+Up opens the menu, Select+Down or B closes it, Up/Down moves, A loads the area. Game input is held
-- back while the menu is open. An area loads only if its bit is set in the pass mask that the AP client
-- writes to the mailbox; the menu does not open at all until the client has written its magic byte.
--
-- After a boss the game moves on to the next area by itself (area byte N-1 -> N). If the player lacks that
-- area's pass the menu opens and cannot be closed until another area is loaded. If the pass is there, the
-- script counts it as a load (so the client syncs the inventory) once the client has had time to see the
-- boss win, which it reads from the area byte moving while the load counter stays put.
--
-- Two more ways into an area also count as loads, since the client only syncs turtles and packs on one:
--   * Continue after a game over restarts the area with every turtle at full HP, unowned ones too. The
--     continue byte changes at the game over; once all four HP are full again the counter goes up.
--   * A new game from the title screen (game phase 3, which the area states never pass through) would
--     start Area 1 without a pass, so the menu is forced open.
--
-- A one-line HUD at the top of the screen shows what the client says the player owns: turtles, packs,
-- bosses beaten (x/3 needed for the Technodrome) and GO MODE once Shredder is in logic. Select+Left hides
-- or shows it.
--
-- The script also records what it sees in MAILBOX_BEATEN: a boss win (area byte N-1 -> N without a load)
-- and Shredder's ending ($001B = 5). The client sends those even if it was disconnected at the time.
--
-- A missing or unreadable area state is shown as "(saknas)" in the menu and never half-loaded.
--
-- Mailbox and addresses: keep in step with apworld/tmnt/ram.py.

local MAILBOX_PASSES = 0x0388
local MAILBOX_LOAD_COUNTER = 0x0389
local MAILBOX_ACK = 0x038A
local MAILBOX_MAGIC = 0x038B
local MAILBOX_INVENTORY = 0x038C  -- bit 0-3 turtles (Leo, Raph, Mike, Don), 4 Missile Pack, 5 Rope Pack, 6 Scuba
local MAILBOX_CLEARED = 0x038D    -- bit N-1 = Area N's boss beaten (from the server, via the client)
local MAILBOX_BEATEN = 0x038E     -- written here: bit N-1 = saw Area N's boss beaten, bit 5 = saw the ending
local MAILBOX_FIRST, MAILBOX_LAST = 0x0388, 0x038E
local SHREDDER_BEATEN_BIT = 0x20
local PHASE_ENDING = 5
local CLEARS_FOR_TECHNODROME = 3  -- apworld/tmnt/rules.py
local AREA6_BIT = 0x20
local MAGIC_VALUE = 0xA7
local CURRENT_AREA = 0x0048  -- 0-based: Area N = value + 1
local GAME_PHASE = 0x001B
local PHASE_AREA_LOAD = 3
local CONTINUES = 0x0046     -- changes at every game over (0 wraps to 255; the game never runs out)
local TURTLE_HP = { 0x0077, 0x0078, 0x0079, 0x007A }
local FULL_HP_VALUE = 0x80
local AREAS = 6
-- The client polls about every 0.5 s; it must see the area byte move before the counter does.
local BOSS_ADVANCE_DELAY = 120
local MESSAGE_FRAMES = 120

local SCRIPT_DIR = debug.getinfo(1, "S").source:sub(2):match("^(.*[/\\])") or ""
local M = { state_dir = TMNT_AREA_SELECT_STATE_DIR or (SCRIPT_DIR .. "..\\savestates\\") }

local function read(address) return memory.readbyte(address, "RAM") end
local function write(address, value) memory.writebyte(address, value, "RAM") end

local function next_counter(counter)
  return counter % 255 + 1  -- 1..255, never 0: 0 means "nothing loaded yet" to the client
end

local menu_open, forced, cursor = false, false, 1
local message, message_left = nil, 0
local held = {}
local hud_shown = true
local last_area, advanced_at = nil, nil
local last_phase, last_continues, continued = nil, nil, false

local function say(text)
  message, message_left = text, MESSAGE_FRAMES
end

local function unlocked(area)
  return (read(MAILBOX_PASSES) & (1 << (area - 1))) ~= 0
end

local function state_path(area)
  return M.state_dir .. "area" .. area .. ".State"
end

local function state_exists(area)
  local file = io.open(state_path(area), "rb")
  if file then file:close() end
  return file ~= nil
end

local missing = {}
for area = 1, AREAS do
  if not state_exists(area) then
    missing[area] = true
    console.log("TMNT area select: missing " .. state_path(area))
  end
end

-- Returns false if the state could not be loaded; RAM is then untouched.
local function load_area(area)
  if missing[area] then
    say("State saknas för Area " .. area)
    return false
  end
  local mailbox = {}
  for address = MAILBOX_FIRST, MAILBOX_LAST do mailbox[address] = read(address) end
  -- BizHawk returns false when a state does not load (e.g. one made in another BizHawk version).
  if savestate.load(state_path(area)) == false then
    say("Kunde inte ladda Area " .. area)
    return false
  end
  -- The state overwrote RAM, mailbox included: put the values back and count the load.
  for address = MAILBOX_FIRST, MAILBOX_LAST do write(address, mailbox[address]) end
  write(MAILBOX_LOAD_COUNTER, next_counter(mailbox[MAILBOX_LOAD_COUNTER]))
  write(MAILBOX_MAGIC, MAGIC_VALUE)
  if read(CURRENT_AREA) ~= area - 1 then say("Fel state för Area " .. area) end
  last_area, advanced_at = read(CURRENT_AREA), nil
  last_phase, last_continues, continued = read(GAME_PHASE), read(CONTINUES), false
  return true
end

local function record_beaten(bit)
  write(MAILBOX_BEATEN, read(MAILBOX_BEATEN) | bit)
end

local function count_load()
  write(MAILBOX_LOAD_COUNTER, next_counter(read(MAILBOX_LOAD_COUNTER)))
end

local function force_menu(text)
  menu_open, forced, cursor = true, true, 1
  say(text)
end

local function all_full_hp()
  for _, address in ipairs(TURTLE_HP) do
    if read(address) ~= FULL_HP_VALUE then return false end
  end
  return true
end

local function watch_continue_and_new_game()
  local phase, continues = read(GAME_PHASE), read(CONTINUES)
  if last_continues ~= nil and continues ~= last_continues and read(MAILBOX_LOAD_COUNTER) ~= 0 then
    continued = true
  end
  if continued and all_full_hp() then
    continued = false
    count_load()
  end
  if phase == PHASE_ENDING and read(MAILBOX_LOAD_COUNTER) ~= 0 then record_beaten(SHREDDER_BEATEN_BIT) end
  if last_phase ~= nil and phase == PHASE_AREA_LOAD and last_phase ~= PHASE_AREA_LOAD
      and read(MAILBOX_MAGIC) == MAGIC_VALUE then
    force_menu("Välj area")
  end
  last_phase, last_continues = phase, continues
end

local function watch_area()
  local area = read(CURRENT_AREA)
  if last_area ~= nil and area == last_area + 1 and read(MAILBOX_LOAD_COUNTER) ~= 0 then
    advanced_at = emu.framecount()
    if area <= 5 then record_beaten(1 << (area - 1)) end  -- byte N = Area N's boss was just beaten
  end
  last_area = area
  if advanced_at and emu.framecount() - advanced_at >= BOSS_ADVANCE_DELAY then
    advanced_at = nil
    if unlocked(area + 1) then
      count_load()
    else
      force_menu("Area " .. (area + 1) .. " är låst")
    end
  end
end

local function pressed(buttons, name)
  return buttons[name] and not held[name]
end

local HUD_ITEMS = {  -- label, mailbox byte, bit
  { "LEO", MAILBOX_INVENTORY, 0 }, { "RAPH", MAILBOX_INVENTORY, 1 }, { "MIKE", MAILBOX_INVENTORY, 2 },
  { "DON", MAILBOX_INVENTORY, 3 }, { "MISSILE", MAILBOX_INVENTORY, 4 }, { "ROPE", MAILBOX_INVENTORY, 5 },
  { "SCUBA", MAILBOX_INVENTORY, 6 },
}

local function bit_count(value)
  local count = 0
  while value > 0 do
    count, value = count + (value & 1), value >> 1
  end
  return count
end

local function draw_hud()
  gui.drawBox(0, 0, 255, 9, 0xC0000000, 0xC0000000)
  local x = 2
  for _, item in ipairs(HUD_ITEMS) do
    local owned = (read(item[2]) & (1 << item[3])) ~= 0
    gui.pixelText(x, 1, item[1], owned and 0xFFFFFFFF or 0xFF505050, 0x00000000)
    x = x + #item[1] * 4 + 4
  end
  if (read(MAILBOX_PASSES) & AREA6_BIT) ~= 0 then
    gui.pixelText(x + 2, 1, "GO MODE", 0xFF40FF40, 0x00000000)
  else
    local cleared = math.min(bit_count(read(MAILBOX_CLEARED)), CLEARS_FOR_TECHNODROME)
    gui.pixelText(x + 2, 1, string.format("BOSS %d/%d", cleared, CLEARS_FOR_TECHNODROME), 0xFFFFFF00, 0x00000000)
  end
end

local function draw()
  gui.cleartext()
  gui.clearGraphics()
  if hud_shown and read(MAILBOX_MAGIC) == MAGIC_VALUE then draw_hud() end
  if menu_open then
    gui.drawBox(56, 40, 204, 70 + AREAS * 12, 0xFFFFFFFF, 0xE0000000)
    gui.drawText(64, 46, "VÄLJ AREA", 0xFFFFFF00)
    for area = 1, AREAS do
      local mark = area == cursor and ">" or " "
      local lock = missing[area] and "  (saknas)" or unlocked(area) and "" or "  (låst)"
      gui.drawText(64, 52 + area * 12, mark .. " Area " .. area .. lock, unlocked(area) and 0xFFFFFFFF or 0xFF808080)
    end
  end
  if message_left > 0 then
    gui.drawText(64, 24, message, 0xFFFF4040, 0xE0000000)
    message_left = message_left - 1
  end
end

-- One frame of the script. buttons: P1 buttons held this frame, e.g. { Select = true, Up = true }.
function M.frame(buttons)
  local connected = read(MAILBOX_MAGIC) == MAGIC_VALUE
  watch_area()
  watch_continue_and_new_game()

  if buttons.Select and pressed(buttons, "Left") then hud_shown = not hud_shown end
  if not menu_open then
    if buttons.Select and pressed(buttons, "Up") then
      if connected then
        menu_open, cursor = true, 1
      else
        say("Anslut AP-klienten")
      end
    end
  else
    if pressed(buttons, "Up") and not buttons.Select then cursor = (cursor - 2) % AREAS + 1 end
    if pressed(buttons, "Down") and not buttons.Select then cursor = cursor % AREAS + 1 end
    if not forced and (pressed(buttons, "B") or (buttons.Select and pressed(buttons, "Down"))) then
      menu_open = false
    elseif pressed(buttons, "A") then
      if unlocked(cursor) then
        if load_area(cursor) then menu_open, forced = false, false end
      else
        say("Låst")
      end
    end
    joypad.set({ Up = false, Down = false, Left = false, Right = false, A = false, B = false, Select = false,
                 Start = false }, 1)
  end

  held = {}
  for name, down in pairs(buttons) do held[name] = down end
  draw()
end

function M.is_open() return menu_open end
function M.is_forced() return forced end
function M.message() return message_left > 0 and message or nil end
function M.hud_shown() return hud_shown end

-- Physical P1 buttons; the keys may come with or without a "P1 " prefix.
local function read_pad()
  local buttons = {}
  for name, down in pairs(joypad.getimmediate(1) or {}) do
    if down == true then buttons[(name:gsub("^P1 ", ""))] = true end
  end
  return buttons
end

if TMNT_AREA_SELECT_LIBRARY then return M end

console.log("TMNT area select ready: Select+Up opens the menu")
while true do
  M.frame(read_pad())
  emu.frameadvance()
end
