#!/usr/bin/env python3
"""Generate a ROM-resident PC080SN attribute lookup table."""

from __future__ import annotations

import argparse
import os
import struct
from pathlib import Path


def build_attr_lut() -> list[int]:
    values: list[int] = []
    for key in range(32):
        pal = key & 0x03
        hflip = (key >> 2) & 0x01
        vflip = (key >> 3) & 0x01
        prio = (key >> 4) & 0x01
        values.append((prio << 15) | (pal << 13) | (vflip << 12) | (hflip << 11))
    return values


def write_be16_bin(path: Path, values: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for value in values:
            f.write(struct.pack(">H", value & 0xFFFF))


def write_c_words_include(path: Path, values: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for idx, value in enumerate(values):
            sep = "," if idx != len(values) - 1 else ""
            f.write(f"    0x{value:04X}{sep}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Precompute PC080SN attribute LUT (32 entries)."
    )
    parser.add_argument(
        "--output",
        default="build/pc080sn_attr_lut.bin",
        help="Binary output path (big-endian u16 entries).",
    )
    parser.add_argument(
        "--include",
        default="build/pc080sn_attr_lut_words.inc",
        help="C include output path (u16 word literals).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    values = build_attr_lut()
    write_be16_bin(Path(args.output), values)
    write_c_words_include(Path(args.include), values)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
