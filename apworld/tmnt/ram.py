"""TMNT (NES, USA) RAM map used by the client and the area select Lua script.

Sources: adelikat & JXQ's RAM map (files.tasvideos.org/gameresources/nes/tmnt/TMNT.xls, "RAM" sheet) and
tasvideos.org/GameResources/NES/TeenageMutantNinjaTurtles. "doc" = documented there but not yet checked in
BizHawk; "guess" = nothing documented. Flip VERIFIED to True only after docs/research/tmnt-ram.md confirms all.
"""

VERIFIED = False

# Domain "RAM" (NES internal 2 KiB) unless noted.
CURRENT_AREA = 0x0048            # doc: "world number"; confirmed: reads 0 in Area 1
AREA_NUMBER_OFFSET = 1           # Area N = value + 1
GAME_PHASE = 0x001B              # doc: "where in the game", 5 = ending credits
ACTIVE_TURTLE = 0x0067           # confirmed: 0=Leo, 1=Raph, 2=Mike, 3=Don
TURTLE_BY_ID = ("Leonardo", "Raphael", "Michelangelo", "Donatello")
TURTLE_HP: dict[str, int] = {    # doc: 128 max, 16 per bar. Order follows the turtle ID (Leo, Raph, Mike, Don):
    "Leonardo": 0x0077,          # the xls labels $78 Mike / $79 Raph, but zeroing $79 in BizHawk emptied
    "Raphael": 0x0078,           # Mike's health bar (seen by the owner, 2026-10-31), matching the ID order used by
    "Michelangelo": 0x0079,      # $0067 and the throwing weapon counts $A8-$AB.
    "Donatello": 0x007A,
}
CAPTURED_HP_VALUE = 0x00         # confirmed: 0 = captured; writing 0x80 back frees her (risk R1 cleared)
FULL_HP_VALUE = 0x80             # doc: 128
MISSILE_COUNT = 0x00BF           # doc: "# of missles"
ROPE_COUNT = 0x00A7              # doc: "# ropes"
# Boss wins have no flag of their own: see client_logic.boss_defeated (area byte N-1 -> N, TAS-confirmed).
SHREDDER_DEFEATED: tuple[int, int] = (GAME_PHASE, 5)  # TAS-confirmed: 5 for ~40 s from "You defeated Shredder"

# Mailbox shared with lua/tmnt_area_select.lua (keep the Lua constants in sync).
MAILBOX_BASE = 0x0388            # TAS-confirmed: $0388-$03AF never written; markers there kept the TAS in sync to Area 6
                                 # ($07F0 was rejected: the game wrote 0x44 there in Area 1)
MAILBOX_PASSES = MAILBOX_BASE + 0
MAILBOX_LOAD_COUNTER = MAILBOX_BASE + 1
MAILBOX_ACK = MAILBOX_BASE + 2
MAILBOX_MAGIC = MAILBOX_BASE + 3
MAGIC_VALUE = 0xA7
# Read only by the Lua HUD (lua/tmnt_area_select.lua): what the player owns and which bosses are beaten.
MAILBOX_INVENTORY = MAILBOX_BASE + 4  # bit 0-3 turtles by ID (TURTLE_BY_ID), 4 Missile Pack, 5 Rope Pack, 6 Scuba Kit
MAILBOX_CLEARED = MAILBOX_BASE + 5    # bit N-1 = Area N's boss beaten (N = 1..5)
# Written by the Lua area select, which sees every frame: bit N-1 = it saw Area N's boss beaten (the area byte
# moving N-1 -> N without a load), bit 5 = it saw Shredder's ending. The client sends these too, so a win
# while the client was disconnected is not lost.
MAILBOX_BEATEN = MAILBOX_BASE + 6
SHREDDER_BEATEN_BIT = 1 << 5

MISSILE_REFILL = 15              # the TAS uses all 10 missiles it finds in Area 3; 15 gives room for misses
ROPE_REFILL = 5                  # guess: the TAS skips ropes (damage boost), so play Area 3 to set this
PICKUPS_PERSISTENT = False       # confirmed: a pizza respawns after leaving the room (risk R2: no)

# Domain "PRG ROM": free bytes for the AP tag written by rom.py. VERIFIED from the ROM file:
# PRG $1BD92-$1BFD7 is 582 bytes of 0xFF (bank 6); the old guess 0x1FF00 was live code.
ROM_TAG_OFFSET = 0x1BE00
