"""Pure client logic: turns received items into RAM writes and RAM signals into checks.

No BizHawk or network code here, so all of it is unit-testable.
"""
from dataclasses import dataclass

from . import ram
from .items import AREA_PASSES, TURTLES
from .rules import CLEARS_FOR_TECHNODROME

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


def _area_playable(inv: Inventory, area: int) -> bool:
    if area not in inv.passes:
        return False
    if area == 2:
        return inv.scuba
    if area == 3:
        return inv.missiles and inv.ropes
    return True


def pass_bitmask(inv: Inventory, cleared_areas: set[int]) -> int:
    mask = sum(1 << (area - 1) for area in range(1, 6) if _area_playable(inv, area))
    if area6_unlocked(inv, cleared_areas):
        mask |= AREA6_BIT
    return mask


def full_sync_writes(inv: Inventory, active: str | None) -> list[Write]:
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
    writes.append((ram.MISSILE_COUNT, [ram.MISSILE_REFILL if inv.missiles else 0]))
    writes.append((ram.ROPE_COUNT, [ram.ROPE_REFILL if inv.ropes else 0]))
    return writes


def incremental_writes(old: Inventory, new: Inventory, ram_now: dict[int, int]) -> list[Write]:
    writes = [(ram.TURTLE_HP[turtle], [ram.FULL_HP_VALUE])
              for turtle in ram.TURTLE_HP if turtle in new.turtles - old.turtles]
    for had, has, address, refill in ((old.missiles, new.missiles, ram.MISSILE_COUNT, ram.MISSILE_REFILL),
                                      (old.ropes, new.ropes, ram.ROPE_COUNT, ram.ROPE_REFILL)):
        if has and not had:
            writes.append((address, [max(ram_now.get(address, 0), refill)]))
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
