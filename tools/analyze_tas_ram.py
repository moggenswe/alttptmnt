"""Analyses the RAM dump that lua/tmnt_tas_ram_dump.lua writes while BizHawk 2.6.1 plays TAS 4543M.

    python tools/analyze_tas_ram.py [tas/4543M/ramdump]

Prints three things for docs/research/tmnt-ram.md:
  1. runs of RAM bytes that never changed during the whole TAS (mailbox candidates),
  2. per area, bytes that changed exactly once while it was played (boss-defeated flag candidates),
  3. missile and rope counts while Area 3 was played.
"""
import sys
from collections import defaultdict
from pathlib import Path

RAM_SIZE = 0x800
STACK = range(0x100, 0x200)
MIN_RUN = 4
AREA = 0x0048
# Frames where the TAS's area byte goes up (Area N+1 briefing starts); see docs/research/tmnt-ram.md.
AREA_STARTS = [200, 5499, 18596, 30041, 46072, 49799]


def load_dumps(path: Path) -> list[tuple[int, bytes]]:
    dumps = []
    with open(path) as file:
        for line in file:
            frame, hexdata = line.split()
            dumps.append((int(frame), bytes.fromhex(hexdata)))
    return dumps


def unused_runs(changes_path: Path) -> list[tuple[int, int, list[int]]]:
    unchanged = {}
    with open(changes_path) as file:
        for line in file:
            address, count, first, last = line.split()
            if int(count) == 0 and int(address, 16) not in STACK:
                unchanged[int(address, 16)] = int(last)
    runs, start = [], None
    for address in range(RAM_SIZE + 1):
        if address in unchanged and start is None:
            start = address
        elif address not in unchanged and start is not None:
            if address - start >= MIN_RUN:
                runs.append((start, address - start, [unchanged[a] for a in range(start, address)]))
            start = None
    return runs


def single_changes(dumps: list[tuple[int, bytes]], begin: int, end: int) -> dict[int, tuple[int, int, int]]:
    """Addresses that changed exactly once between frames begin and end: address -> (frame, old, new)."""
    window = [(frame, ram) for frame, ram in dumps if begin <= frame < end]
    seen: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for (_, before), (frame, after) in zip(window, window[1:]):
        for address in range(RAM_SIZE):
            if before[address] != after[address]:
                seen[address].append((frame, before[address], after[address]))
    return {address: changes[0] for address, changes in seen.items() if len(changes) == 1}


def main() -> None:
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "tas/4543M/ramdump")
    dumps = load_dumps(folder / "dumps.txt")
    last_frame = dumps[-1][0]

    print("== RAM runs that never changed after frame 200 (stack $0100-$01FF left out)")
    for start, length, values in unused_runs(folder / "changes.txt"):
        print(f"${start:04X}-${start + length - 1:04X} ({length} bytes) values {' '.join(f'{v:02X}' for v in values[:8])}")

    print("\n== Bytes that changed exactly once while each area was played")
    bounds = AREA_STARTS + [last_frame + 1]
    per_area = []
    for area, (begin, end) in enumerate(zip(bounds, bounds[1:]), start=1):
        # Start a little after the area loads so its setup writes do not count.
        once = single_changes(dumps, begin + 300, end - 1)
        per_area.append(once)
        print(f"Area {area} (frames {begin}-{end}): {len(once)} addresses")
    common = set.intersection(*(set(once) for once in per_area[:5]))
    print(f"Changed exactly once in each of Area 1-5: {len(common)}")
    for address in sorted(common):
        cells = []
        for area, once in enumerate(per_area, start=1):
            if address in once:
                frame, old, new = once[address]
                cells.append(f"A{area} f{frame} {old:02X}->{new:02X}")
        print(f"  ${address:04X}: " + "; ".join(cells))

    print("\n== Missiles ($00BF) and ropes ($00A7) changes in Area 3")
    begin, end = AREA_STARTS[2], AREA_STARTS[3]
    with open(folder / "watch.txt") as file:
        for line in file:
            frame, change = line.split()
            if begin <= int(frame) < end and change.split("=")[0] in ("missiles", "ropes"):
                print(f"  f{frame} {change}")


if __name__ == "__main__":
    main()
