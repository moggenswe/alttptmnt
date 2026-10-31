import hashlib
import os
from typing import TYPE_CHECKING

import Utils
from settings import get_settings
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

from . import ram
from .items import GAME_NAME

if TYPE_CHECKING:
    from . import TMNTWorld

BASE_ROM_MD5 = "c14e760c4d5a086e4186d2e1fc9b7743"  # TMNT_NA, from tmnt_rando's tables/master.txt
INES_HEADER_SIZE = 0x10
ROM_TAG = b"TMNTAP"
AUTH_LENGTH = 64  # slot names are at most 16 characters, i.e. at most 64 bytes of UTF-8


def tag_file_offset() -> int:
    """File offset of the AP tag: PRG ROM offset plus the iNES header in front of it."""
    return INES_HEADER_SIZE + ram.ROM_TAG_OFFSET


class TMNTProcedurePatch(APProcedurePatch, APTokenMixin):
    game = GAME_NAME
    hash = BASE_ROM_MD5
    patch_file_ending = ".aptmnt"
    result_file_ending = ".nes"
    procedure = [("apply_tokens", ["token_data.bin"])]

    @classmethod
    def get_source_data(cls) -> bytes:
        return get_base_rom_bytes()


def write_patch(world: "TMNTWorld", patch: TMNTProcedurePatch) -> None:
    slot_name = world.multiworld.player_name[world.player].encode("utf-8")
    patch.write_token(APTokenTypes.WRITE, tag_file_offset(), ROM_TAG + slot_name.ljust(AUTH_LENGTH, b"\x00"))
    patch.write_file("token_data.bin", patch.get_token_binary())


def get_base_rom_bytes() -> bytes:
    file_name = get_settings()["tmnt_options"]["rom_file"]
    if not os.path.exists(file_name):
        file_name = Utils.user_path(file_name)
    with open(file_name, "rb") as file:
        data = file.read()
    if hashlib.md5(data).hexdigest() != BASE_ROM_MD5:
        raise Exception("Supplied base ROM does not match Teenage Mutant Ninja Turtles (NES, USA).")
    return data
