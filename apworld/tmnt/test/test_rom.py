from worlds.Files import APTokenTypes

from . import TMNTTestBase
from ..rom import AUTH_LENGTH, ROM_TAG, TMNTProcedurePatch, tag_file_offset, write_patch


def parse_tokens(blob: bytes) -> list[tuple[int, int, bytes]]:
    """Decode APTokenMixin.get_token_binary(): u32 count, then (u8 type, u32 offset, u32 size, data) per token."""
    count, pos, tokens = int.from_bytes(blob[:4], "little"), 4, []
    for _ in range(count):
        token_type = blob[pos]
        offset = int.from_bytes(blob[pos + 1:pos + 5], "little")
        size = int.from_bytes(blob[pos + 5:pos + 9], "little")
        tokens.append((token_type, offset, blob[pos + 9:pos + 9 + size]))
        pos += 9 + size
    return tokens


class TestRomPatch(TMNTTestBase):
    def test_patch_writes_tag(self):
        patch = TMNTProcedurePatch(player=self.player, player_name="Turtles")
        write_patch(self.world, patch)
        tokens = parse_tokens(patch.get_token_binary())
        writes = {offset: data for token_type, offset, data in tokens if token_type == APTokenTypes.WRITE}
        self.assertTrue(writes[tag_file_offset()].startswith(ROM_TAG))

    def test_patch_writes_padded_slot_name(self):
        patch = TMNTProcedurePatch(player=self.player, player_name="Turtles")
        write_patch(self.world, patch)
        data = {offset: data for _, offset, data in parse_tokens(patch.get_token_binary())}[tag_file_offset()]
        auth = data[len(ROM_TAG):]
        self.assertEqual(len(auth), AUTH_LENGTH)
        self.assertEqual(auth.rstrip(b"\x00").decode("utf-8"), self.multiworld.player_name[self.player])
