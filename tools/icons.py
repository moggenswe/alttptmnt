"""Turns the two icon sheets made with ChatGPT (art/icons/) into the overlay's icons.

    .venv/Scripts/python.exe tools/icons.py

For every icon on the sheets it cuts the icon out, removes the background (flood fill from the edges), and redraws
it as real pixel art on a GRID x GRID grid: the sheet's colours are reduced to a small palette and each grid cell
takes its most common colour. That gives clean edges and lets the icon be written as an SVG of squares, which stays
sharp at any size. Each icon also gets a grey "-off" variant for things not found yet.

Writes tools/obs/sprites/<name>.png (4x, nearest neighbour), <name>.svg, <name>-off.png and <name>-off.svg, and
tools/obs/icons_preview.png. The names are listed in ZELDA and TMNT below, in the order they appear on the sheets.
"""
from __future__ import annotations

from collections import Counter, deque
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
SHEETS = REPO / "art" / "icons"
OUT = REPO / "tools" / "obs" / "sprites"
GRID = 32
PNG_SCALE = 4
COLOURS = 28  # palette size per icon

# Left to right. The sheet has Kholdstare twice; the second one (None) is skipped.
ZELDA = ("zelda-bosses-chatgpt.png", (0, 398, 2170, 532),  # the icon row inside the dark card
         [["alttp-armos", "alttp-lanmolas", "alttp-moldorm", "alttp-helmasaur", "alttp-arrghus", "alttp-mothula",
           "alttp-blind", "alttp-kholdstare", None, "alttp-vitreous", "alttp-trinexx"]])
# Row by row.
TMNT = ("tmnt-icons-chatgpt.png", None,
        [["leonardo", "raphael", "donatello", "michelangelo"],
         ["missile", "rope", "scuba"],
         [f"pass{n}" for n in range(1, 6)],
         [f"boss{n}" for n in range(1, 6)]])


def pixels_of(image: Image.Image) -> list[tuple]:
    """Every pixel as a tuple, row by row (Image.getdata is on its way out of Pillow)."""
    raw, bands = image.tobytes(), len(image.getbands())
    return [tuple(raw[i:i + bands]) for i in range(0, len(raw), bands)]


def close(a: tuple, b: tuple, tolerance: int) -> bool:
    return sum(abs(x - y) for x, y in zip(a[:3], b[:3])) <= tolerance


def runs(flags: list[bool], min_gap: int) -> list[tuple[int, int]]:
    """Spans of True separated by at least min_gap False."""
    spans, start, gap = [], None, 0
    for i, flag in enumerate(flags + [False] * (min_gap + 1)):
        if flag:
            if start is None:
                start = i
            gap, end = 0, i + 1
        elif start is not None:
            gap += 1
            if gap > min_gap:
                spans.append((start, end))
                start = None
    return spans


def find_icons(sheet: Image.Image, region, rows: list[list]) -> list[tuple[str, tuple]]:
    x0, y0, x1, y1 = region or (0, 0, sheet.width, sheet.height)
    area = sheet.crop((x0, y0, x1, y1))
    background = area.getpixel((2, 2))
    mask = Image.new("L", area.size)
    mask.putdata([0 if close(p, background, 50) else 255 for p in pixels_of(area)])
    row_spans = runs([mask.crop((0, y, mask.width, y + 1)).getbbox() is not None for y in range(mask.height)], 25)
    if len(row_spans) != len(rows):
        raise SystemExit(f"expected {len(rows)} rows of icons, found {len(row_spans)}: {row_spans}")
    found = []
    for (top, bottom), names in zip(row_spans, rows):
        band = mask.crop((0, top, mask.width, bottom))
        cols = runs([band.crop((x, 0, x + 1, band.height)).getbbox() is not None for x in range(band.width)], 18)
        if len(cols) != len(names):
            raise SystemExit(f"expected {len(names)} icons in a row, found {len(cols)}: {cols}")
        for (left, right), name in zip(cols, names):
            if name:
                found.append((name, (x0 + left, y0 + top, x0 + right, y0 + bottom), background))
    return found


def cut_out(sheet: Image.Image, box: tuple, background: tuple) -> Image.Image:
    """The icon with the background around it made transparent (flood fill from the crop's edges)."""
    left, top, right, bottom = box
    icon = sheet.crop((left - 6, top - 6, right + 6, bottom + 6)).convert("RGBA")
    width, height = icon.size
    pixels = icon.load()
    seen = set()
    queue = deque((x, y) for x in range(width) for y in (0, height - 1))
    queue.extend((x, y) for y in range(height) for x in (0, width - 1))
    while queue:
        x, y = queue.popleft()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        seen.add((x, y))
        if close(pixels[x, y], background, 70):
            pixels[x, y] = (0, 0, 0, 0)
            queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return icon.crop(icon.getbbox())


def pixelate(icon: Image.Image) -> Image.Image:
    """GRID x GRID pixel art: a small palette, and each cell's most common colour (or transparent)."""
    side = max(icon.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.alpha_composite(icon, ((side - icon.width) // 2, (side - icon.height) // 2))
    opaque = Image.new("RGB", square.size, (0, 0, 0))
    opaque.paste(square, mask=square.getchannel("A"))
    palette_image = opaque.quantize(COLOURS, method=Image.Quantize.MEDIANCUT)
    palette = palette_image.getpalette()[:COLOURS * 3]
    indices, alpha = palette_image.load(), square.getchannel("A").load()
    out = Image.new("RGBA", (GRID, GRID), (0, 0, 0, 0))
    cell = side / GRID
    for gy in range(GRID):
        for gx in range(GRID):
            votes = Counter()
            for y in range(int(gy * cell), max(int((gy + 1) * cell), int(gy * cell) + 1)):
                for x in range(int(gx * cell), max(int((gx + 1) * cell), int(gx * cell) + 1)):
                    votes[indices[x, y] if alpha[x, y] >= 128 else None] += 1
            winner = votes.most_common(1)[0][0]
            if winner is not None:
                out.putpixel((gx, gy), tuple(palette[winner * 3:winner * 3 + 3]) + (255,))
    return out


def greyed(icon: Image.Image) -> Image.Image:
    """The "not found yet" look: grey, darker and flatter, still readable on the panel's dark cards."""
    out = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    for (x, y), (r, g, b, a) in zip(((x, y) for y in range(icon.height) for x in range(icon.width)), pixels_of(icon)):
        if a:
            level = round(55 + (0.3 * r + 0.59 * g + 0.11 * b) * 0.45)
            out.putpixel((x, y), (level, level, min(255, level + 6), 255))
    return out


def svg(icon: Image.Image) -> str:
    rects = []
    for y in range(icon.height):
        x = 0
        while x < icon.width:
            colour = icon.getpixel((x, y))
            run = 1
            while x + run < icon.width and icon.getpixel((x + run, y)) == colour:
                run += 1
            if colour[3]:
                rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="#{colour[0]:02x}{colour[1]:02x}'
                             f'{colour[2]:02x}"/>')
            x += run
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {icon.width} {icon.height}" '
            f'shape-rendering="crispEdges">{"".join(rects)}</svg>\n')


def all_icons() -> dict[str, Image.Image]:
    icons = {}
    for file, region, rows in (ZELDA, TMNT):
        sheet = Image.open(SHEETS / file).convert("RGB")
        for name, box, background in find_icons(sheet, region, rows):
            icons[name] = pixelate(cut_out(sheet, box, background))
    return icons


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    icons = all_icons()
    for name, icon in icons.items():
        for suffix, image in (("", icon), ("-off", greyed(icon))):
            image.resize((GRID * PNG_SCALE,) * 2, Image.NEAREST).save(OUT / f"{name}{suffix}.png")
            (OUT / f"{name}{suffix}.svg").write_text(svg(image), encoding="utf-8")
    size = GRID * 3
    preview = Image.new("RGBA", (len(icons) * (size + 8) + 8, 2 * (size + 8) + 8), (24, 28, 40, 255))
    for i, icon in enumerate(icons.values()):
        preview.alpha_composite(icon.resize((size, size), Image.NEAREST), (8 + i * (size + 8), 8))
        preview.alpha_composite(greyed(icon).resize((size, size), Image.NEAREST), (8 + i * (size + 8), size + 16))
    preview.save(OUT.parent / "icons_preview.png")
    print(f"{len(icons)} icons -> {OUT}")


if __name__ == "__main__":
    main()
