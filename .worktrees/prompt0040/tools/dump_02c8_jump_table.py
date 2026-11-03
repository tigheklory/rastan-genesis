#!/usr/bin/env python3
"""Dump the 0x02c8 actor state jump table rooted at 0x40bc2."""

from pathlib import Path


ROM = Path("build/regions/maincpu.bin")
TABLE = 0x40BC2
COUNT = 34


def be16(blob: bytes, offset: int) -> int:
    return int.from_bytes(blob[offset : offset + 2], "big")


def main() -> int:
    blob = ROM.read_bytes()
    print(f"0x02c8 jump table @ 0x{TABLE:05x}")
    for state in range(COUNT):
        rel = be16(blob, TABLE + state * 2)
        target = (TABLE + rel) & 0xFFFFFF
        print(f"  state {state:2d}: rel=0x{rel:04x} target=0x{target:05x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
