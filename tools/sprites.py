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
    return sprites


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sprites = all_sprites()
    for name, image in sprites.items():
        image.save(OUT / f"{name}.png")
    sheet = Image.new("RGBA", (len(sprites) * 72, 72), (32, 48, 64, 255))
    for i, image in enumerate(sprites.values()):
        sheet.alpha_composite(image, (i * 72 + 4, 4))
    sheet.save(OUT.parent / "sprites_preview.png")
    print(f"{len(sprites)} sprites -> {OUT}")


if __name__ == "__main__":
    main()
