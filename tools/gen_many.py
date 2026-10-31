"""Generate many seeds (without output files) and count failures.

Usage: python tools/gen_many.py --count 200 --players players/ --ap Archipelago/
Exits 0 only if every seed generated.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def generate(ap_dir: Path, players: Path, seed: int) -> bool:
    result = subprocess.run(
        [sys.executable, "-W", "ignore", "Generate.py", "--player_files_path", str(players.resolve()),
         "--seed", str(seed), "--skip_output"],
        cwd=ap_dir, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--players", type=Path, default=Path("players"))
    parser.add_argument("--ap", type=Path, default=Path("Archipelago"))
    args = parser.parse_args()

    failed = [seed for seed in range(1, args.count + 1) if not generate(args.ap, args.players, seed)]
    print(f"ok={args.count - len(failed)} failed={len(failed)}")
    if failed:
        print("failed seeds:", " ".join(map(str, failed)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
