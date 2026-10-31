import logging
from time import monotonic
from typing import TYPE_CHECKING

from NetUtils import ClientStatus
from worlds._bizhawk import RequestFailedError, read, write
from worlds._bizhawk.client import BizHawkClient

from . import ram
from .client_logic import (AREA6_BIT, Inventory, SignalDebouncer, boss_defeated, full_sync_writes,
                           incremental_writes,
                           inventory_from_items, needs_full_sync, pass_bitmask)
from .items import GAME_NAME
from .locations import BOSS_LOCATIONS, ENTRANCE_LOCATIONS, START_LOCATIONS, location_table
from .rom import AUTH_LENGTH, ROM_TAG

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger("Client")

SHREDDER_KEY = 6


class TMNTClient(BizHawkClient):
    game = GAME_NAME
    system = "NES"
    patch_suffix = ".aptmnt"

    def __init__(self) -> None:
        super().__init__()
        self.prev_area: int | None = None
        self.prev_counter: int | None = None
        self.entrances = SignalDebouncer()
        self.goal = SignalDebouncer()
        self.last_inventory: Inventory | None = None
        self.expected_ack: int | None = None

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        tag = (await read(ctx.bizhawk_ctx, [(ram.ROM_TAG_OFFSET, len(ROM_TAG), "PRG ROM")]))[0]
        if tag != ROM_TAG:
            return False
        ctx.game = self.game
        ctx.items_handling = 0b111
        ctx.want_slot_data = True
        if not ram.VERIFIED:
            logger.warning("TMNT RAM addresses are unverified placeholders (ram.py). Expect nonsense.")
        return True

    async def set_auth(self, ctx: "BizHawkClientContext") -> None:
        raw = (await read(ctx.bizhawk_ctx, [(ram.ROM_TAG_OFFSET + len(ROM_TAG), AUTH_LENGTH, "PRG ROM")]))[0]
        ctx.auth = raw.rstrip(b"\x00").decode("utf-8")

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        # Start inventory always holds a turtle and a pass, so an empty list means the server's
        # ReceivedItems has not (re)arrived yet; acting on it would capture every turtle.
        if ctx.server is None or ctx.slot_data is None or not ctx.items_received:
            return
        try:
            await self._tick(ctx)
        except RequestFailedError:
            pass  # BizHawk does not catch errors from game_watcher; the next tick retries

    async def _tick(self, ctx: "BizHawkClientContext") -> None:
        addresses = [ram.MAILBOX_MAGIC, ram.MAILBOX_LOAD_COUNTER, ram.MAILBOX_ACK, ram.CURRENT_AREA, ram.ACTIVE_TURTLE,
                     ram.MISSILE_COUNT, ram.ROPE_COUNT, ram.SHREDDER_DEFEATED[0]]
        values = dict(zip(addresses, (b[0] for b in await read(
            ctx.bizhawk_ctx, [(address, 1, "RAM") for address in addresses]))))
        now = monotonic()

        inventory = inventory_from_items(
            [ctx.item_names.lookup_in_game(item.item, self.game) for item in ctx.items_received])
        cleared = {area for area, name in BOSS_LOCATIONS.items() if location_table[name] in ctx.checked_locations}
        passes = pass_bitmask(inventory, cleared)

        await self._send_checks(ctx, values, passes, now)

        writes = [(ram.MAILBOX_PASSES, [passes]), (ram.MAILBOX_MAGIC, [ram.MAGIC_VALUE])]
        counter, ack = values[ram.MAILBOX_LOAD_COUNTER], values[ram.MAILBOX_ACK]
        magic_ok = values[ram.MAILBOX_MAGIC] == ram.MAGIC_VALUE
        if self.last_inventory is None or needs_full_sync(counter, ack, magic_ok, self.expected_ack):
            active_id = values[ram.ACTIVE_TURTLE]
            active = ram.TURTLE_BY_ID[active_id] if active_id < len(ram.TURTLE_BY_ID) else None
            writes += full_sync_writes(inventory, active)
            writes.append((ram.MAILBOX_ACK, [counter]))
            new_ack = counter
        else:
            writes += incremental_writes(self.last_inventory, inventory, values)
            new_ack = ack
        await write(ctx.bizhawk_ctx, [(address, data, "RAM") for address, data in writes])
        self.last_inventory, self.expected_ack = inventory, new_ack  # only once the write landed

        shredder_address, shredder_value = ram.SHREDDER_DEFEATED
        shredder = values[shredder_address] == shredder_value and bool(passes & AREA6_BIT)
        if not ctx.finished_game and self.goal.update({SHREDDER_KEY: shredder}, now):
            await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            ctx.finished_game = True

    async def _send_checks(self, ctx: "BizHawkClientContext", values: dict[int, int], passes: int,
                           now: float) -> None:
        area = values[ram.CURRENT_AREA] + ram.AREA_NUMBER_OFFSET
        # Before the area select has loaded anything (power-on, title screen) the area byte reads 0 = Area 1.
        area_loaded = values[ram.MAILBOX_LOAD_COUNTER] != 0
        entrances = {area: area_loaded and area in ENTRANCE_LOCATIONS and bool(passes & (1 << (area - 1)))}

        counter = values[ram.MAILBOX_LOAD_COUNTER]
        beaten = boss_defeated(self.prev_area, values[ram.CURRENT_AREA], self.prev_counter, counter)
        self.prev_area, self.prev_counter = values[ram.CURRENT_AREA], counter
        found = {location_table[BOSS_LOCATIONS[beaten]]} if beaten else set()
        found |= {location_table[ENTRANCE_LOCATIONS[a]] for a in self.entrances.update(entrances, now)}
        found |= {location_table[name] for name in START_LOCATIONS}  # free gifts, sent on connect
        new = found - ctx.checked_locations
        if new:
            await ctx.send_msgs([{"cmd": "LocationChecks", "locations": sorted(new)}])
