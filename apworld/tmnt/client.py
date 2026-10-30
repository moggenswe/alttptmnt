import logging
from typing import TYPE_CHECKING

from NetUtils import ClientStatus
from worlds._bizhawk import read, write
from worlds._bizhawk.client import BizHawkClient

from . import ram
from .client_logic import (BossDebouncer, Inventory, full_sync_writes, incremental_writes, inventory_from_items,
                           needs_full_sync, pass_bitmask)
from .items import GAME_NAME
from .locations import BOSS_LOCATIONS, ENTRANCE_LOCATIONS, START_LOCATIONS, location_table
from .rom import AUTH_LENGTH, ROM_TAG

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger("Client")


class TMNTClient(BizHawkClient):
    game = GAME_NAME
    system = "NES"
    patch_suffix = ".aptmnt"

    def __init__(self) -> None:
        super().__init__()
        self.debouncer = BossDebouncer()
        self.last_inventory: Inventory | None = None

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
        if ctx.server is None or ctx.slot_data is None:
            return

        addresses = [ram.MAILBOX_MAGIC, ram.MAILBOX_LOAD_COUNTER, ram.MAILBOX_ACK, ram.CURRENT_AREA,
                     ram.MISSILE_COUNT, ram.ROPE_COUNT, ram.SHREDDER_DEFEATED[0],
                     *(address for address, _ in ram.BOSS_DEFEATED_SIGNAL.values())]
        values = dict(zip(addresses, (b[0] for b in await read(
            ctx.bizhawk_ctx, [(address, 1, "RAM") for address in addresses]))))

        inventory = inventory_from_items(
            [ctx.item_names.lookup_in_game(item.item, self.game) for item in ctx.items_received])

        await self._send_checks(ctx, values)
        cleared = {area for area, name in BOSS_LOCATIONS.items() if location_table[name] in ctx.checked_locations}

        writes = [(ram.MAILBOX_PASSES, [pass_bitmask(inventory, cleared)])]
        if values[ram.MAILBOX_MAGIC] != ram.MAGIC_VALUE:
            writes.append((ram.MAILBOX_MAGIC, [ram.MAGIC_VALUE]))
        counter, ack = values[ram.MAILBOX_LOAD_COUNTER], values[ram.MAILBOX_ACK]
        if self.last_inventory is None or needs_full_sync(counter, ack):
            writes += full_sync_writes(inventory)
            writes.append((ram.MAILBOX_ACK, [counter]))
        else:
            writes += incremental_writes(self.last_inventory, inventory, values)
        self.last_inventory = inventory
        await write(ctx.bizhawk_ctx, [(address, data, "RAM") for address, data in writes])

        shredder_address, shredder_value = ram.SHREDDER_DEFEATED
        if not ctx.finished_game and values[shredder_address] == shredder_value:
            await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            ctx.finished_game = True

    async def _send_checks(self, ctx: "BizHawkClientContext", values: dict[int, int]) -> None:
        signals = {area: values[address] == value for area, (address, value) in ram.BOSS_DEFEATED_SIGNAL.items()}
        found = {location_table[BOSS_LOCATIONS[area]] for area in self.debouncer.update(signals)}
        found |= {location_table[name] for name in START_LOCATIONS}  # free gifts, sent on connect
        if values[ram.CURRENT_AREA] in ENTRANCE_LOCATIONS:
            found.add(location_table[ENTRANCE_LOCATIONS[values[ram.CURRENT_AREA]]])
        new = found - ctx.checked_locations
        if new:
            await ctx.send_msgs([{"cmd": "LocationChecks", "locations": sorted(new)}])
