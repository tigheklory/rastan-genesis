#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MAINCPU = ROOT / "build" / "regions" / "maincpu.bin"


def read_u16be(blob: bytes, offset: int) -> int:
    return (blob[offset] << 8) | blob[offset + 1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Dump Rastan 0x0508 state jump table")
    parser.add_argument("--maincpu", type=Path, default=MAINCPU)
    parser.add_argument("--base", type=lambda x: int(x, 0), default=0x4213A)
    parser.add_argument("--states", type=int, default=20)
    args = parser.parse_args()

    blob = args.maincpu.read_bytes()
    base = args.base

    print(f"0x0508 jump table @ 0x{base:05x}")
    for state in range(args.states):
        rel = read_u16be(blob, base + state * 2)
        target = (base + rel) & 0xFFFFFF
        print(f"  state {state:2d}: rel=0x{rel:04x} target=0x{target:05x}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
