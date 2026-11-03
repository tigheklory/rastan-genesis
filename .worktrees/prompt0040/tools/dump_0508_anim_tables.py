#!/usr/bin/env python3
"""Dump animation descriptor tables used by the 0x0508 actor state machine."""

from pathlib import Path


ROM_PATH = Path("build/regions/maincpu.bin")

# Each record is consumed by 0x41d08 and copied to:
#   +0x02, +0x08, +0x0d, +0x0e, +0x0f, +0x10, +0x11, +0x13
FIELDS = ("attr2", "delay", "anim_pos", "anim_end", "anim_step", "hold_a", "hold_b", "misc")

TABLES = (
    ("41d26 base descriptors", 0x41D26, 16),
    ("42d42 state-1 descriptors", 0x42D42, 9),
    ("42d8a explicit descriptors", 0x42D8A, 14),
    ("42e08 gated descriptors", 0x42E08, 6),
)


def format_record(index: int, data: bytes) -> str:
    parts = [f"{name}={value:#04x}" for name, value in zip(FIELDS, data)]
    raw = " ".join(f"{b:02x}" for b in data)
    return f"  {index:2d}: {raw}    " + ", ".join(parts)


def main() -> int:
    rom = ROM_PATH.read_bytes()
    for title, address, count in TABLES:
        print(f"{title} @ {address:#06x}")
        for index in range(count):
            start = address + (index * 8)
            record = rom[start : start + 8]
            print(format_record(index, record))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
