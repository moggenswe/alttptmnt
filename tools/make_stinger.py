"""Makes the "pizza-wipe" stinger transition for OBS: tools/obs/pizza_wipe.webm (VP9 with alpha, 1920x1080, 60 fps).

    .venv/Scripts/python.exe tools/make_stinger.py

A band of tomato sauce covered in rolling pizzas (tools/sprites.py's own pixel art) sweeps across the screen
from right to left, slowing down in the middle where it covers the whole frame; OBS swaps the scenes there.
Use it in OBS as a Stinger transition with transition point TRANSITION_POINT_MS (the scene collection from
tools/make_obs_collection.py already does). Needs imageio-ffmpeg.
"""
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

import sprites

OUT = Path(__file__).resolve().parent / "obs" / "pizza_wipe.webm"
WIDTH, HEIGHT, FPS, FRAMES = 1920, 1080, 60, 60
PIZZA_SCALE = 24  # 16 px art -> 384 px pizzas
STEP = 340  # distance between pizzas on the band, a little less than a pizza so they overlap
BAND_WIDTH = WIDTH + 2 * STEP  # wider than the screen, so it covers everything in the middle
BAND_COLOUR = (214, 74, 42, 255)  # tomato sauce
TRANSITION_POINT_MS = 500  # the middle, where the band covers everything


def band_centre(t: float) -> float:
    """Band centre x at time t in [0, 1]: from off the right edge to off the left, slow in the middle."""
    reach = WIDTH / 2 + BAND_WIDTH / 2 + PIZZA_SCALE * 8 + 40
    return WIDTH / 2 - reach * (2 * t - 1) ** 3


def main() -> None:
    pizza = sprites.render(sprites.SPRITES["pizza"], scale=PIZZA_SCALE)
    turns = [pizza.rotate(-90 * quarter, resample=Image.NEAREST) for quarter in range(4)]
    rows = [STEP // 2 + row * STEP - (3 * STEP - HEIGHT) // 2 for row in range(3)]
    with tempfile.TemporaryDirectory() as folder:
        for frame in range(FRAMES):
            canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            centre = band_centre(frame / (FRAMES - 1))
            left = round(centre - BAND_WIDTH / 2)
            if left < WIDTH and left + BAND_WIDTH > 0:
                canvas.paste(BAND_COLOUR, (max(left, 0), 0, min(left + BAND_WIDTH, WIDTH), HEIGHT))
            for column in range(BAND_WIDTH // STEP + 1):
                x = left + column * STEP
                for row, y in enumerate(rows):
                    # Pizzas on alternate rows roll in opposite directions, a quarter turn every 6 frames.
                    turn = turns[(frame // 6 * (1 if row % 2 else -1)) % 4]
                    box = (x - turn.width // 2, y - turn.height // 2)
                    if -turn.width < box[0] < WIDTH and -turn.height < box[1] < HEIGHT:
                        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
                        layer.paste(turn, box, turn)
                        canvas.alpha_composite(layer)
            canvas.save(Path(folder) / f"frame_{frame:03d}.png")
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS),
                        "-i", str(Path(folder) / "frame_%03d.png"), "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
                        "-b:v", "0", "-crf", "32", "-auto-alt-ref", "0", str(OUT)], check=True)
    print(f"stinger -> {OUT} ({OUT.stat().st_size // 1024} KiB, transition point {TRANSITION_POINT_MS} ms)")


if __name__ == "__main__":
    main()
