"""The hand-drawn 16x16 pixel art that is left: the heart (site) and the pizza (pizza-wipe stinger, site icon).
The overlay's item and boss icons come from tools/icons.py.

    .venv/Scripts/python.exe tools/sprites.py

Writes tools/obs/sprites/<name>.png at 4x (64x64, nearest neighbour) and <name>.svg, the same pixels as vector
squares, which stay sharp at any size. Each grid row is one line of pixels; each letter is a colour from PALETTE, "." is transparent.
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

SPRITES = {
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


def svg(rows: list[str], swap: dict[str, str] | None = None) -> str:
    """The grid as an SVG with one square per pixel (runs of one colour in a row merged), crisp at any size."""
    assert all(len(row) == len(rows[0]) for row in rows), "ragged grid"
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            colour = PALETTE.get((swap or {}).get(row[x], row[x]))
            run = 1
            while x + run < len(row) and PALETTE.get((swap or {}).get(row[x + run], row[x + run])) == colour:
                run += 1
            if colour:
                rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="{colour}"/>')
            x += run
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {len(rows[0])} {len(rows)}" '
            f'shape-rendering="crispEdges">{"".join(rects)}</svg>\n')


def all_grids() -> dict[str, tuple[list[str], dict[str, str] | None]]:
    """name -> (grid, colour swap) for every sprite."""
    return {name: (rows, None) for name, rows in SPRITES.items()}


def all_sprites(scale: int = SCALE) -> dict[str, Image.Image]:
    return {name: render(rows, swap, scale) for name, (rows, swap) in all_grids().items()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sprites = all_sprites()
    for name, image in sprites.items():
        image.save(OUT / f"{name}.png")
    for name, (rows, swap) in all_grids().items():
        (OUT / f"{name}.svg").write_text(svg(rows, swap), encoding="utf-8")
    sheet = Image.new("RGBA", (len(sprites) * 72, 72), (32, 48, 64, 255))
    for i, image in enumerate(sprites.values()):
        sheet.alpha_composite(image, (i * 72 + 4, 4))
    sheet.save(OUT.parent / "sprites_preview.png")
    print(f"{len(sprites)} sprites -> {OUT}")


if __name__ == "__main__":
    main()
