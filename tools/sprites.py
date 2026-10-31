"""Our own 16x16 pixel icons for the stream overlay, the TMNT PopTracker pack and the pizza-wipe stinger.

    .venv/Scripts/python.exe tools/sprites.py

Writes tools/obs/sprites/<name>.png at 4x (64x64, nearest neighbour). All art here is drawn for this project:
no game sprites and no fan art, since free TMNT fan art does not exist (the characters belong to Nickelodeon).
Each grid row is one line of pixels; each letter is a colour from PALETTE, "." is transparent.
"""
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent / "obs" / "sprites"
SCALE = 4

PALETTE = {
    "K": "#101418",  # outline
    "G": "#45a84f", "L": "#7fd36b", "g": "#2a7036", "M": "#1c4a24",  # turtle skin, light, shade, mouth
    "W": "#f6f6f6", "k": "#000000",  # eye white, pupil
    "B": "#2f6fe4", "b": "#1d4596",  # Leonardo blue
    "R": "#e23b3b", "r": "#9a1f24",  # Raphael red
    "O": "#f5962a", "o": "#b0601a",  # Michelangelo orange
    "P": "#9b5de5", "p": "#5f3299",  # Donatello purple
    "S": "#c7ced6", "s": "#7d8894", "d": "#4b545e",  # metal light, mid, dark
    "Y": "#ffd84a", "y": "#e8902a",  # flame / cheese
    "N": "#b07a45", "n": "#6e4826",  # rope / crust
    "C": "#7ad7ff", "c": "#3a8fc2",  # glass
    "H": "#ff4d6d", "h": "#a8203e", "I": "#ffb3c1",  # heart
    "T": "#d64a2a", "t": "#f2c46b",  # tomato sauce, cheese light
}

TURTLE_HEAD = [
    "....KKKKKKKK....",
    "..KKGGGGGGGGKK..",
    ".KGGLLLGGGGGGgK.",
    ".KGLLGGGGGGGGgK.",
    "KGGGGGGGGGGGGGgK",
    "KXXXXXXXXXXXXXXK",
    "KXWWkXXXXXXkWWXK",
    "KxXXXXXXXXXXXXxK",
    "KGGGGGGGGGGGGGgK",
    "KGGGGGGGGGGGGGgK",
    ".KGGGMMMMMMGGgK.",
    ".KGGGGMMMMGGGgK.",
    "..KgGGGGGGGGgK..",
    "...KKggggggKK...",
    ".....KKKKKK.....",
    "................",
]
BANDANAS = {"leonardo": "Bb", "raphael": "Rr", "michelangelo": "Oo", "donatello": "Pp"}

SPRITES = {
    "missile": [
        "................",
        "................",
        "....KKK.........",
        "....KRrK........",
        ".....KRrKKKKKK..",
        "y..KKSSSSSSSSRK.",
        "yYyKSSSWWSSSSRRK",
        "YYYKSSSSSSSSsRRK",
        "yYyKsssssssssRRK",
        "y..KKddddddddRK.",
        ".....KRrKKKKKK..",
        "....KRrK........",
        "....KKK.........",
        "................",
        "................",
        "................",
    ],
    "rope": [
        "........KKKK....",
        ".......KSSSdK...",
        "........KKSdK...",
        ".........KSdK...",
        "....KKKKKKSK....",
        "..KKNNNNNNKK....",
        ".KNNnnnnnnNNK...",
        "KNNnKKKKKKnNNK..",
        "KNnK......KnNK..",
        "KNnK.KKKK.KnNK..",
        "KNNnKNNNNKnNNK..",
        ".KNNnnnnnnNNK...",
        "..KKNNNNNNKK....",
        "....KKKKKK......",
        "................",
        "................",
    ],
    "scuba": [
        "............KK..",
        "...........KYyK.",
        "..KKKKKKKKKKYyK.",
        ".KddddddddddKyK.",
        "KdCCCCdKdCCCCdK.",
        "KdCWCCdKdCWCCdK.",
        "KdCCCcdKdCCCcdK.",
        "KdCCccdKdCCccdK.",
        ".KddddddddddKyK.",
        "..KKKKKKKKKKYyK.",
        "............KyK.",
        "..........KKYyK.",
        "..........KyyK..",
        "...........KK...",
        "................",
        "................",
    ],
    "pass": [
        ".....KKKKKK.....",
        "...KKddddddKK...",
        "..KdssssssssdK..",
        ".KdsSdSSSSdSsdK.",
        ".KdsSSSSSSSSsdK.",
        "KdsSdSKKKKSdSsdK",
        "KdsSSSKSSSSSSsdK",
        "KdsSdSKKKKSdSsdK",
        "KdsSSSSSSKSSSsdK",
        "KdsSdSKKKKSdSsdK",
        ".KdsSSSSSSSSsdK.",
        ".KdsSdSSSSdSsdK.",
        "..KdssssssssdK..",
        "...KKddddddKK...",
        ".....KKKKKK.....",
        "................",
    ],
    "boss": [
        ".....KKKKKK.....",
        "...KKddddddKK...",
        "..KddsssssddK...",
        ".KdsssssssssdK..",
        ".KdsKKKsKKKsdK..",
        "KdsKRRKsKRRKsdK.",
        "KdssKKsssKKssdK.",
        "KddsssssssssddK.",
        ".KddssKKKssddK..",
        "..KddsdsdsddK...",
        "...KddddddddK...",
        "....KKKKKKKK....",
        "................",
        "................",
        "................",
        "................",
    ],
    "heart": [
        "................",
        "..KKKK....KKKK..",
        ".KHHHHK..KHHHHK.",
        "KHIIHHHKKHHHHHhK",
        "KHIHHHHHHHHHHHhK",
        "KHHHHHHHHHHHHHhK",
        "KHHHHHHHHHHHHhhK",
        ".KHHHHHHHHHHhhK.",
        "..KHHHHHHHHhhK..",
        "...KHHHHHHhhK...",
        "....KHHHHhhK....",
        ".....KHHhhK.....",
        "......KhhK......",
        ".......KK.......",
        "................",
        "................",
    ],
    "pizza": [
        ".....KKKKKK.....",
        "...KKnnnnnnKK...",
        "..KnNNNNNNNNnK..",
        ".KnNtytttyttNnK.",
        ".KnNtTTtytTTNnK.",
        "KnNttTTttyTTtNnK",
        "KnNytttytttyyNnK",
        "KnNtytTTttytNNnK",
        "KnNtttTTtyttNNnK",
        "KnNttyttttTTtNnK",
        ".KnNtytTTttTNnK.",
        ".KnNNtttyttNNnK.",
        "..KnNNNNNNNNnK..",
        "...KKnnnnnnKK...",
        ".....KKKKKK.....",
        "................",
    ],
}


MEDALLION = [  # X is the medallion's face; a glyph is drawn over rows 5-9, columns 4-11
    "................",
    ".....KKKKKK.....",
    "...KKYYYYYYKK...",
    "..KYYyyyyyyYYK..",
    "..KYyXXXXXXyYK..",
    ".KYyXXXXXXXXyYK.",
    ".KYyXXXXXXXXyYK.",
    ".KYyXXXXXXXXyYK.",
    ".KYyXXXXXXXXyYK.",
    ".KYyXXXXXXXXyYK.",
    "..KYyXXXXXXyYK..",
    "..KYYyyyyyyYYK..",
    "...KKYYYYYYKK...",
    ".....KKKKKK.....",
    "................",
    "................",
]
MEDALLION_GLYPHS = {  # 8x5, "a" and "b" are the glyph's two colours
    "flame": ["...aa...", "..aaaa..", ".aabbaa.", ".abbbba.", "..aaaa.."],
    "bolt": ["....aa..", "...aa...", "..aaaa..", "...aa...", "..aa...."],
    "ring": ["..aaaa..", ".a....a.", ".a.bb.a.", ".a....a.", "..aaaa.."],
}


def medallion(face: str, glyph: str, a: str, b: str) -> list[str]:
    rows = [row.replace("X", face) for row in MEDALLION]
    for y, glyph_row in enumerate(MEDALLION_GLYPHS[glyph]):
        row = list(rows[5 + y])
        for x, pixel in enumerate(glyph_row):
            if pixel != ".":
                row[4 + x] = a if pixel == "a" else b
        rows[5 + y] = "".join(row)
    return rows


def rod(top: list[str], shaft: str, shade: str) -> list[str]:
    """A staff: five rows of head, a metal collar, then the shaft."""
    return [*top, "......KSSK......", *[f"......K{shaft}{shade}K......"] * 8, "......KSSK......", ".......KK......."]


# A Link to the Past items that matter for going to Ganon, drawn in the same style (not the game's sprites).
ALTTP_SPRITES = {
    "alttp_sword": [
        "..............KK", ".............KWK", "............KWSK", "...........KWSK.",
        "..........KWSK..", ".........KWSK...", "........KWSK....", ".......KWSK.....",
        "..KK..KWSK......", "..KYKKWSK.......", "...KYYSK........", "....KYyK........",
        "...KBKKyK.......", "..KBbK.KyK......", ".KBbK...KK......", ".KKK............",
    ],
    "alttp_bow": [
        "...KKKKKKKK.....", "..KNNNNNNNWK....", "..KNnKKKKKWK....", ".KNnK.....WK....",
        ".KNK......WK....", ".KNK......WK....", ".KNK......WK....", ".KNKddddddWSSK..",
        ".KNK......WK....", ".KNK......WK....", ".KNK......WK....", ".KNK......WK....",
        ".KNnK.....WK....", "..KNnKKKKKWK....", "..KNNNNNNNWK....", "...KKKKKKKK.....",
    ],
    "alttp_hookshot": [
        "................", "................", "................", "................",
        "...........KK...", "..........KSdK..", "KKKK......KSK...", "KRRKKKKKKKSdK...",
        "KRrKSdSdSdSSK...", "KRRKKKKKKKSdK...", "KKKK......KSK...", "..........KSdK..",
        "...........KK...", "................", "................", "................",
    ],
    "alttp_hammer": [
        "................", "..KKKKKKKKKKK...", ".KSSSSSSSSSSdK..", ".KSWSSSSSSSSdK..",
        ".KSSSSSSSSSSdK..", ".KddddddddddKK..", "..KKKKKNKKKKK...", "......KNnK......",
        "......KNnK......", "......KNnK......", "......KNnK......", "......KNnK......",
        "......KNnK......", "......KNnK......", "......KKKK......", "................",
    ],
    "alttp_firerod": rod([".......KK.......", "......KYOK......", ".....KYYOOK.....", ".....KOYYRK.....",
                          "......KRRK......"], "R", "r"),
    "alttp_icerod": rod([".......KK.......", "......KWCK......", ".....KWCCcK.....", ".....KCWCcK.....",
                         "......KccK......"], "B", "b"),
    "alttp_lamp": [
        "................", "......KK........", ".....KYOK.......", ".....KYOK.......",
        "......KK........", "....KKKKKK......", "...KYYYYYYK.....", "..KYWYYYYYYKKK..",
        ".KYYYYYYYYYYyYK.", ".KYYYYYYYYYYKKyK", ".KyYYYYYYYYyK.K.", "..KyyyyyyyyK....",
        "...KKKKKKKK.....", "................", "................", "................",
    ],
    "alttp_mirror": [
        ".....KKKKKK.....", "...KKPPPPPPKK...", "..KPCCCCCCCCPK..", "..KPCWCCCCCCPK..",
        ".KPCWCCCCCCCcPK.", ".KPCCCCCCCCCcPK.", ".KPCCCCCCCCccPK.", "..KPCCCCCCccPK..",
        "..KPcCCCCcccPK..", "...KKPPPPPPKK...", "......KPpK......", "......KPpK......",
        "......KPpK......", ".....KPPppK.....", "......KKKK......", "................",
    ],
    "alttp_pearl": [
        "................", ".....KKKKKK.....", "...KKIIIIIIKK...", "..KIWWIIIIIIPK..",
        "..KIWIIIIIIIPK..", ".KIIIIIIIIIIIPK.", ".KIIIIIIIIIIIPK.", ".KIIIIIIIIIIPPK.",
        ".KIIIIIIIIIIPPK.", ".KIIIIIIIIIPPPK.", "..KIIIIIIIPPPK..", "..KPIIIIIPPPPK..",
        "...KKPPPPPPKK...", ".....KKKKKK.....", "................", "................",
    ],
    "alttp_flippers": [
        "................", "..KKK.....KKK...", ".KBBBK...KBBBK..", ".KBBBK...KBBBK..",
        "KBBbBBK.KBBbBBK.", "KBbBbBK.KBbBbBK.", "KBbBbBK.KBbBbBK.", "KBbBbBK.KBbBbBK.",
        "KBbBbBK.KBbBbBK.", "KBbBbBK.KBbBbBK.", ".KBBBK...KBBBK..", "..KdK.....KdK...",
        "..KdK.....KdK...", "...K.......K....", "................", "................",
    ],
    "alttp_boots": [
        "................", "....KKKKK.......", "...KRRRRRK......", "...KRWRRrK..KK..",
        "...KRRRRrK.KWWK.", "...KRRRRrKKWWK..", "...KRRRRrKWWK...", "...KRRRRrKKK....",
        "...KRRRRRrK.....", "...KRRRRRRrKK...", "...KRRRRRRRRrK..", "..KRRRRRRRRRRrK.",
        "..KnnnnnnnnnnnK.", "...KKKKKKKKKKKK.", "................", "................",
    ],
    "alttp_glove": [
        "................", "....KKKKKKK.....", "...KSSKSSKSK....", "...KSSKSSKSKK...",
        "..KKSSKSSKSKSK..", "..KSKSSSSSSSSK..", "..KSSSSSSSSSSK..", "..KSSSSSSSSSsK..",
        "..KSSSSSSSSssK..", "...KSSSSSSssK...", "...KBBBBBBBBK...", "...KBbBbBbBbK...",
        "...KKKKKKKKKK...", "................", "................", "................",
    ],
    "alttp_book": [
        "................", "..KKKKKKKKKKK...", "..KGGGGGGGGGgK..", "..KGYYYYYYYGgK..",
        "..KGYGGGGGYGgK..", "..KGYGLLGGYGgK..", "..KGYGLLGGYGgK..", "..KGYGGGGGYGgK..",
        "..KGYYYYYYYGgK..", "..KGGGGGGGGGgK..", "..KGGGGGGGGGgK..", "..KgggggggggWK..",
        "..KWWWWWWWWWWK..", "...KKKKKKKKKKK..", "................", "................",
    ],
    "alttp_somaria": [
        "....KKKK........", "...KRRRRK.......", "..KRrKKRrK......", "..KRK..KRK......",
        "..KK...KRK......", ".......KRK......", ".......KYK......", ".......KRK......",
        ".......KRK......", ".......KRK......", ".......KRK......", ".......KRK......",
        ".......KRK......", ".......KRK......", ".......KRK......", ".......KKK......",
    ],
    "alttp_flute": [
        "................", "................", "................", "................",
        "................", "................", "KKKKKKKKKKKKKKK.", "KCWCCCCCCCCCCCcK",
        "KCCKCCKCCKCCKCcK", "KcccccccccccccK.", ".KKKKKKKKKKKKKK.", "................",
        "................", "................", "................", "................",
    ],
    "alttp_bombos": medallion("r", "flame", "O", "Y"),
    "alttp_ether": medallion("b", "bolt", "C", "W"),
    "alttp_quake": medallion("g", "ring", "L", "G"),
}


def render(rows: list[str], swap: dict[str, str] | None = None, scale: int = SCALE) -> Image.Image:
    assert all(len(row) == len(rows[0]) for row in rows), "ragged grid"
    image = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, pixel in enumerate(row):
            colour = PALETTE.get((swap or {}).get(pixel, pixel))
            if colour:
                image.putpixel((x, y), tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST)


def all_sprites(scale: int = SCALE) -> dict[str, Image.Image]:
    sprites = {name: render(TURTLE_HEAD, {"X": colours[0], "x": colours[1]}, scale)
               for name, colours in BANDANAS.items()}
    sprites |= {name: render(rows, scale=scale) for name, rows in SPRITES.items()}
    sprites |= {name: render(rows, scale=scale) for name, rows in ALTTP_SPRITES.items()}
    return sprites


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sprites = all_sprites()
    for name, image in sprites.items():
        image.save(OUT / f"{name}.png")
    columns = 11
    rows = -(-len(sprites) // columns)
    sheet = Image.new("RGBA", (columns * 72, rows * 72), (32, 48, 64, 255))
    for i, image in enumerate(sprites.values()):
        sheet.alpha_composite(image, (i % columns * 72 + 4, i // columns * 72 + 4))
    sheet.save(OUT.parent / "sprites_preview.png")
    print(f"{len(sprites)} sprites -> {OUT}")


if __name__ == "__main__":
    main()
