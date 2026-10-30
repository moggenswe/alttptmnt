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


def full_sync_writes(inv: Inventory) -> list[Write]:
    writes = [(address, [ram.FULL_HP_VALUE if turtle in inv.turtles else ram.CAPTURED_HP_VALUE])
              for turtle, address in ram.TURTLE_HP.items()]
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


def needs_full_sync(counter: int, ack: int) -> bool:
    return counter != ack


class BossDebouncer:
    """Reports an area's boss as defeated once its signal has been seen on two updates in a row."""

    def __init__(self) -> None:
        self._seen_once: set[int] = set()
        self._reported: set[int] = set()

    def update(self, area_signals: dict[int, bool]) -> set[int]:
        confirmed = {area for area, on in area_signals.items()
                     if on and area in self._seen_once and area not in self._reported}
        self._seen_once = {area for area, on in area_signals.items() if on}
        self._reported |= confirmed
        return confirmed
