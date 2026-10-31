"""Pure client logic: turns received items into RAM writes and RAM signals into checks.

No BizHawk or network code here, so all of it is unit-testable.
"""
from dataclasses import dataclass

from . import ram
from .items import AREA_PASSES, TURTLES
from .rules import AREA_TOOL_REQUIREMENTS, CLEARS_FOR_TECHNODROME

Write = tuple[int, list[int]]

AREA6_BIT = 1 << 5


@dataclass(frozen=True)
class Inventory:
    turtles: frozenset[str]
    passes: frozenset[int]
    missiles: bool
    ropes: bool
    scuba: bool


def inventory_from_items(item_names: list[str]) -> Inventory:
    names = set(item_names)
    return Inventory(turtles=frozenset(names & set(TURTLES)),
                     passes=frozenset(AREA_PASSES.index(name) + 1 for name in names & set(AREA_PASSES)),
                     missiles="Missile Pack" in names,
                     ropes="Rope Pack" in names,
                     scuba="Zora's Scuba Kit" in names)


def area6_unlocked(inv: Inventory, cleared_areas: set[int]) -> bool:
    return len(inv.turtles) == len(TURTLES) and len(cleared_areas) >= CLEARS_FOR_TECHNODROME


def has_tool(inv: Inventory, tool: str) -> bool:
    return {"Missile Pack": inv.missiles, "Rope Pack": inv.ropes, "Zora's Scuba Kit": inv.scuba}[tool]


def _area_playable(inv: Inventory, area: int) -> bool:
    return area in inv.passes and all(has_tool(inv, tool) for tool in AREA_TOOL_REQUIREMENTS.get(area, ()))


def pass_bitmask(inv: Inventory, cleared_areas: set[int]) -> int:
    mask = sum(1 << (area - 1) for area in range(1, 6) if _area_playable(inv, area))
    if area6_unlocked(inv, cleared_areas):
        mask |= AREA6_BIT
    return mask


def received_message(item: str, sender: str | None) -> str:
    """BizHawk on-screen text for a received item; sender is None for the player's own TMNT checks."""
    # On-screen text is English (the stream's language for overlays); BizHawk's message font is ASCII only.
    return f"Found {item}" if sender is None else f"Got {item} from {sender}"


def inventory_byte(inv: Inventory) -> int:
    """MAILBOX_INVENTORY for the Lua HUD: bit 0-3 turtles by ID, 4 Missile Pack, 5 Rope Pack, 6 Scuba Kit."""
    turtles = sum(1 << turtle_id for turtle_id, turtle in enumerate(ram.TURTLE_BY_ID) if turtle in inv.turtles)
    return turtles | inv.missiles << 4 | inv.ropes << 5 | inv.scuba << 6


def cleared_byte(cleared_areas: set[int]) -> int:
    """MAILBOX_CLEARED for the Lua HUD: bit N-1 = Area N's boss beaten."""
    return sum(1 << (area - 1) for area in cleared_areas if 1 <= area <= 5)


def _packs(inv: Inventory) -> tuple[tuple[bool, int, int], ...]:
    return ((inv.missiles, ram.MISSILE_COUNT, ram.MISSILE_REFILL), (inv.ropes, ram.ROPE_COUNT, ram.ROPE_REFILL))


def full_sync_writes(inv: Inventory, active: str | None, ram_now: dict[int, int] | None = None) -> list[Write]:
    """Full HP for owned turtles, captured for the rest.

    If the turtle on screen is not owned, the first write makes an owned turtle active, and then she is
    captured like the others. Writing $0067 and her HP in the same frame neither kills her nor glitches the
    game; the sprite only takes the new turtle's colours at the next pause or room change (BizHawk,
    lua/tmnt_turtle_swap_test.lua, 2026-10-31). Without an owned turtle to switch to she is left alone.
    """
    switch_to = None
    if active is not None and active not in inv.turtles and inv.turtles:
        switch_to = next(turtle for turtle in ram.TURTLE_BY_ID if turtle in inv.turtles)
    writes = [(ram.ACTIVE_TURTLE, [ram.TURTLE_BY_ID.index(switch_to)])] if switch_to else []
    writes += [(address, [ram.FULL_HP_VALUE if turtle in inv.turtles else ram.CAPTURED_HP_VALUE])
               for turtle, address in ram.TURTLE_HP.items()
               if turtle in inv.turtles or turtle != active or switch_to]
    # Owned packs are topped up to their refill (more from vanilla pickups is kept); unowned ones emptied.
    # Vanilla pickups stay usable as bonus ammo: the area select keeps the player out of areas whose packs
    # are missing, and missiles and ropes only lie in Areas 3 and 4 (docs/research/tmnt-ammo-and-trackers.md).
    for has, address, refill in _packs(inv):
        now = (ram_now or {}).get(address, 0)
        if not has:
            writes.append((address, [0]))
        elif now < refill:
            writes.append((address, [refill]))
    return writes


def capture_writes(inv: Inventory, active: str | None, ram_now: dict[int, int]) -> list[Write]:
    """Unowned turtles the game has freed are captured again at once. The game frees them at a continue, at a
    new game and through its own rescue (one captured turtle per area from Area 3 on). If the freed one is on
    screen, an owned turtle that is not captured becomes active first, as in full_sync_writes."""
    loose = [turtle for turtle in ram.TURTLE_BY_ID
             if turtle not in inv.turtles and ram_now.get(ram.TURTLE_HP[turtle], 0) != ram.CAPTURED_HP_VALUE]
    writes = []
    if active in loose:
        playable = [turtle for turtle in ram.TURTLE_BY_ID if turtle in inv.turtles
                    and ram_now.get(ram.TURTLE_HP[turtle], 0) != ram.CAPTURED_HP_VALUE]
        if not playable:
            loose.remove(active)  # nobody to switch to: leave her until the next full sync
        else:
            writes.append((ram.ACTIVE_TURTLE, [ram.TURTLE_BY_ID.index(playable[0])]))
    return writes + [(ram.TURTLE_HP[turtle], [ram.CAPTURED_HP_VALUE]) for turtle in loose]


def beaten_from_mailbox(value: int) -> set[int]:
    """Areas (1..5) whose boss the Lua area select saw beaten (ram.MAILBOX_BEATEN)."""
    return {area for area in BOSS_AREAS if value & (1 << (area - 1))}


def incremental_writes(old: Inventory, new: Inventory, ram_now: dict[int, int]) -> list[Write]:
    """Newly received turtles get full HP. A pack refills when it arrives and again whenever its count is
    at 0 (shot empty, or reset by the game at a continue), so owning a pack never leaves the player stuck."""
    writes = [(ram.TURTLE_HP[turtle], [ram.FULL_HP_VALUE])
              for turtle in ram.TURTLE_HP if turtle in new.turtles - old.turtles]
    for (had, _, _), (has, address, refill) in zip(_packs(old), _packs(new)):
        now = ram_now.get(address, 0)
        if has and (not had or now == 0) and now < refill:
            writes.append((address, [refill]))
    return writes


def needs_full_sync(counter: int, ack: int, magic_ok: bool, expected_ack: int | None) -> bool:
    """True after an area load (counter moved), a power cycle (magic gone), a restored older savestate
    (ack is not the one we last wrote) or on the client's first tick."""
    return not magic_ok or expected_ack is None or counter != ack or ack != expected_ack


BOSS_AREAS = range(1, 6)


def boss_defeated(prev_area: int | None, area: int, prev_counter: int | None, counter: int) -> int | None:
    """The 1-based area whose boss was just beaten, or None.

    TMNT has no boss flag: after a boss the game itself moves the 0-based area byte from N-1 to N when
    April's briefing for the next area starts (TAS 4543M, once per boss). An area select load also moves
    the byte, but it bumps the load counter too, and nothing counts before the first load (counter 0).
    """
    if prev_area is None or prev_counter is None or counter == 0 or counter != prev_counter:
        return None
    beaten = area  # 0-based byte N is the 1-based number of the area that was just finished
    return beaten if area == prev_area + 1 and beaten in BOSS_AREAS else None


MIN_SIGNAL_SECONDS = 0.2


class SignalDebouncer:
    """Reports a key once its signal has stayed on for MIN_SIGNAL_SECONDS across consecutive updates.

    Measured in time, not updates: the watcher also wakes on server packets, so two updates can be
    milliseconds apart. Each key is reported at most once.
    """

    def __init__(self) -> None:
        self._on_since: dict[int, float] = {}
        self._reported: set[int] = set()

    def update(self, signals: dict[int, bool], now: float) -> set[int]:
        self._on_since = {key: self._on_since.get(key, now) for key, on in signals.items() if on}
        confirmed = {key for key, since in self._on_since.items()
                     if now - since >= MIN_SIGNAL_SECONDS and key not in self._reported}
        self._reported |= confirmed
        return confirmed
