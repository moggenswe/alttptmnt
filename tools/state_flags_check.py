"""Checks whether the progress bytes the area savestates lack matter (see lua/tmnt_state_flags_check.lua).

    python tools/state_flags_check.py            # launch one BizHawk 2.6.1 per area 2-6, in parallel
    python tools/state_flags_check.py --areas 3 --group zp   # only one address group, to bisect a desync
    python tools/state_flags_check.py --report   # read the results

Needs tas/4543M/ramdump/dumps.txt (lua/tmnt_tas_ram_dump.lua) and savestates/state_ram.txt (RAM of the six
area states, one "<area> <hex>" line each, dumped in BizHawk 2.11.1).
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EMUHAWK = Path.home() / "Downloads" / "BizHawk-2.6.1-win-x64" / "EmuHawk.exe"
ROM = REPO / "roms" / "Teenage Mutant Ninja Turtles (USA).nes"
MOVIE = REPO / "tas" / "4543M" / "tmnt-en.bk2"
OUT = REPO / "tas" / "4543M" / "flags"
# Frames where the TAS's area byte goes up (Area N+1 briefing starts) and where the movie ends.
AREA_STARTS = [200, 5499, 18596, 30041, 46072, 49799, 56264]
SETTLE = 1500  # write this long after the area byte changed, once the area is being played
# Bytes that are the run's state rather than progress: stack, mailbox, HP, active turtle, weapons, ammo,
# pause, and the $07xx screen buffer.
IGNORED = {*range(0x100, 0x200), *range(0x388, 0x390), *range(0x77, 0x7B), 0x67, *range(0xA8, 0xAC), 0xA7, 0xBF,
           0x94, *range(0x700, 0x800)}


def load_dumps() -> list[tuple[int, bytes]]:
    with open(REPO / "tas" / "4543M" / "ramdump" / "dumps.txt") as file:
        return [(int(frame), bytes.fromhex(data)) for frame, data in (line.split() for line in file)]


def load_states() -> dict[int, bytes]:
    with open(REPO / "savestates" / "state_ram.txt") as file:
        return {int(parts[0]): bytes.fromhex(parts[1]) for parts in (line.split() for line in file) if len(parts) == 2}


def differing(dumps: list[tuple[int, bytes]], states: dict[int, bytes], area: int) -> dict[int, int]:
    """Bytes constant while the TAS plays `area` whose value differs from the area state: address -> state value."""
    window = [ram for frame, ram in dumps if AREA_STARTS[area - 1] + SETTLE <= frame < AREA_STARTS[area] - 300]
    return {address: states[area][address] for address in range(0x800)
            if address not in IGNORED and all(ram[address] == window[0][address] for ram in window)
            and states[area][address] != window[0][address]}


# Address groups for bisecting a desync: zero page, $00F9-$00FB, the $035x-$038x object table, the rest.
GROUPS = {"zp": range(0x00, 0xF9), "f9": range(0xF9, 0x100), "obj": range(0x300, 0x388), "rest": range(0x390, 0x700)}


def change_counts(dumps: list[tuple[int, bytes]]) -> list[int]:
    counts = [0] * 0x800
    for (_, before), (_, after) in zip(dumps, dumps[1:]):
        for address in range(0x800):
            counts[address] += before[address] != after[address]
    return counts


def carried(dumps: list[tuple[int, bytes]], states: dict[int, bytes], area: int, counts: list[int]) -> dict[int, int]:
    """Bytes the TAS carries into `area` (as it starts) that differ from the area state and rarely change
    (12 times or less in the whole TAS, so not timers or positions): address -> state value."""
    at_start = dict(dumps)[AREA_STARTS[area - 1] // 5 * 5 + 5]
    return {address: states[area][address] for address in range(0x800)
            if address not in IGNORED and counts[address] <= 12 and at_start[address] != states[area][address]}


def launch_carried(areas: list[int], only: list[int] | None, exclude: list[int] | None = None) -> None:
    """Writes the carried bytes 5 frames after the area byte changed (April's briefing), i.e. as if the area
    had been loaded from our state, and checks that the TAS still finishes the area on the same frame."""
    dumps, states = load_dumps(), load_states()
    counts = change_counts(dumps)
    OUT.mkdir(exist_ok=True)
    for area in areas:
        writes = {address: value for address, value in carried(dumps, states, area, counts).items()
                  if (only is None or address in only) and address not in (exclude or [])}
        name = (f"carried{area}" + "".join(f"_{a:04X}" for a in only or [])
                + "".join(f"_no{a:04X}" for a in exclude or []))
        stop = AREA_STARTS[area] + 5 if area < 6 else AREA_STARTS[6] - 14
        (OUT / f"{name}.json").write_text(json.dumps(sorted(writes)))
        env = dict(os.environ, TMNT_FLAGS_AT=str(AREA_STARTS[area - 1] + 5), TMNT_FLAGS_UNTIL=str(stop),
                   TMNT_FLAGS_WRITES=",".join(f"{a:04X}={v:02X}" for a, v in sorted(writes.items())),
                   TMNT_FLAGS_OUT=f"{name}.txt")
        print(f"{name}: writing {len(writes)} bytes: " + " ".join(f"${a:04X}" for a in sorted(writes)))
        subprocess.Popen([str(EMUHAWK), f"--movie={MOVIE}", f"--lua={REPO / 'lua' / 'tmnt_state_flags_check.lua'}",
                          str(ROM)], env=env)


def launch(areas: list[int], group: str | None, only: list[int] | None = None) -> None:
    dumps, states = load_dumps(), load_states()
    OUT.mkdir(exist_ok=True)
    for area in areas:
        # Progress-like: differs here and in the next area (or the previous one, for Area 6).
        here = differing(dumps, states, area)
        other = differing(dumps, states, area + 1 if area < 6 else area - 1)
        writes = {address: value for address, value in here.items() if address in other
                  and (group is None or address in GROUPS[group]) and (only is None or address in only)}
        stop = AREA_STARTS[area] + 5 if area < 6 else AREA_STARTS[6] - 14
        name = f"area{area}" + (f"_{group}" if group else "") + "".join(f"_{a:04X}" for a in only or [])
        env = dict(os.environ, TMNT_FLAGS_AT=str(AREA_STARTS[area - 1] + SETTLE), TMNT_FLAGS_UNTIL=str(stop),
                   TMNT_FLAGS_WRITES=",".join(f"{a:04X}={v:02X}" for a, v in sorted(writes.items())),
                   TMNT_FLAGS_OUT=f"{name}.txt")
        print(f"{name}: writing {len(writes)} bytes: " + " ".join(f"${a:04X}" for a in sorted(writes)))
        subprocess.Popen([str(EMUHAWK), f"--movie={MOVIE}", f"--lua={REPO / 'lua' / 'tmnt_state_flags_check.lua'}",
                          str(ROM)], env=env)


def report() -> None:
    dumps = dict(load_dumps())
    for path in sorted([*OUT.glob("area*.txt"), *OUT.glob("carried*.txt")]):
        area = int(path.stem.removeprefix("area").removeprefix("carried")[0])
        lines = path.read_text().splitlines() if path.exists() else []
        if "done" not in lines:
            print(f"{path.stem}: not finished")
            continue
        changes = [line for line in lines if line.startswith("area ")]
        if area < 6:
            expected = f"area {area} at frame {AREA_STARTS[area]}"
            print(f"{path.stem}: {'IN SYNC' if expected in changes else 'DESYNC'} ({'; '.join(changes)})")
        else:
            frame, data = next(line.split()[1:] for line in lines if line.startswith("ram "))
            reference = dumps.get(int(frame))
            written = json.loads(path.with_suffix(".json").read_text()) if path.with_suffix(".json").exists() else []
            ram = bytes.fromhex(data)
            same = reference is not None and all(ram[a] == reference[a] for a in range(0x800) if a not in written)
            print(f"{path.stem}: RAM at frame {frame} {'matches the unchanged run' if same else 'DIFFERS (desync?)'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--areas", type=int, nargs="*", default=[2, 3, 4, 5, 6])
    parser.add_argument("--group", choices=GROUPS, help="write only this address group (to bisect a desync)")
    parser.add_argument("--only", type=lambda text: int(text, 16), nargs="*", help="write only these addresses (hex)")
    parser.add_argument("--exclude", type=lambda text: int(text, 16), nargs="*", help="never write these (hex)")
    parser.add_argument("--carried", action="store_true",
                        help="write the bytes the TAS carries into each area, as the area starts")
    args = parser.parse_args()
    if args.report:
        report()
    elif args.carried:
        launch_carried(args.areas, args.only, args.exclude)
    else:
        launch(args.areas, args.group, args.only)
