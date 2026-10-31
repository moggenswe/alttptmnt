"""TMNT (NES, TMNT_NA) RAM map used by the client and the area select Lua script.

PLACEHOLDERS: every address below is a guess until the RAM spike (plan Task 1) fills it in and
documents it in docs/research/tmnt-ram.md. Flip VERIFIED to True only after that.
"""

VERIFIED = False

# Domain "RAM" (NES internal 2 KiB) unless noted.
CURRENT_AREA = 0x0020
TURTLE_HP: dict[str, int] = {
    "Leonardo": 0x0077,
    "Michelangelo": 0x0078,
    "Donatello": 0x0079,
    "Raphael": 0x007A,
}
CAPTURED_HP_VALUE = 0x00
FULL_HP_VALUE = 0x16
MISSILE_COUNT = 0x0090
ROPE_COUNT = 0x0091
BOSS_DEFEATED_SIGNAL: dict[int, tuple[int, int]] = {area: (0x00A0, area) for area in range(1, 6)}
SHREDDER_DEFEATED: tuple[int, int] = (0x00A0, 6)

# Mailbox shared with lua/tmnt_area_select.lua (keep the Lua constants in sync).
MAILBOX_BASE = 0x07F0
MAILBOX_PASSES = MAILBOX_BASE + 0
MAILBOX_LOAD_COUNTER = MAILBOX_BASE + 1
MAILBOX_ACK = MAILBOX_BASE + 2
MAILBOX_MAGIC = MAILBOX_BASE + 3
MAGIC_VALUE = 0xA7

MISSILE_REFILL = 10
ROPE_REFILL = 5
PICKUPS_PERSISTENT = False

# Domain "PRG ROM": free bytes for the AP tag written by rom.py. VERIFIED from the ROM file:
# PRG $1BD92-$1BFD7 is 582 bytes of 0xFF (bank 6); the old guess 0x1FF00 was live code.
ROM_TAG_OFFSET = 0x1BE00
