"""TMNT (NES, USA) RAM map used by the client and the area select Lua script.

Sources: adelikat & JXQ's RAM map (files.tasvideos.org/gameresources/nes/tmnt/TMNT.xls, "RAM" sheet) and
tasvideos.org/GameResources/NES/TeenageMutantNinjaTurtles. "doc" = documented there but not yet checked in
BizHawk; "guess" = nothing documented. Flip VERIFIED to True only after docs/research/tmnt-ram.md confirms all.
"""

VERIFIED = False

# Domain "RAM" (NES internal 2 KiB) unless noted.
CURRENT_AREA = 0x0048            # doc: "world number"; whether Area 1 reads 0 or 1 is unchecked
GAME_PHASE = 0x001B              # doc: "where in the game", 5 = ending credits
ACTIVE_TURTLE = 0x0067           # doc: 0=Leo, 1=Raph, 2=Mike, 3=Don
TURTLE_HP: dict[str, int] = {    # doc: 128 max, 16 per bar
    "Leonardo": 0x0077,
    "Michelangelo": 0x0078,
    "Raphael": 0x0079,
    "Donatello": 0x007A,
}
CAPTURED_HP_VALUE = 0x00         # guess: a turtle at 0 HP is captured (risk R1)
FULL_HP_VALUE = 0x80             # doc: 128
MISSILE_COUNT = 0x00BF           # doc: "# of missles"
ROPE_COUNT = 0x00A7              # doc: "# ropes"
BOSS_DEFEATED_SIGNAL: dict[int, tuple[int, int]] = {area: (0x00A0, area) for area in range(1, 6)}  # guess
SHREDDER_DEFEATED: tuple[int, int] = (GAME_PHASE, 5)  # doc: phase 5 = ending credits

# Mailbox shared with lua/tmnt_area_select.lua (keep the Lua constants in sync).
MAILBOX_BASE = 0x07F0            # guess: page 07xx has no documented use
MAILBOX_PASSES = MAILBOX_BASE + 0
MAILBOX_LOAD_COUNTER = MAILBOX_BASE + 1
MAILBOX_ACK = MAILBOX_BASE + 2
MAILBOX_MAGIC = MAILBOX_BASE + 3
MAGIC_VALUE = 0xA7

MISSILE_REFILL = 10              # guess: set after playing Area 3
ROPE_REFILL = 5                  # guess: set after playing Area 3
PICKUPS_PERSISTENT = False       # unchecked (risk R2)

# Domain "PRG ROM": free bytes for the AP tag written by rom.py. VERIFIED from the ROM file:
# PRG $1BD92-$1BFD7 is 582 bytes of 0xFF (bank 6); the old guess 0x1FF00 was live code.
ROM_TAG_OFFSET = 0x1BE00
