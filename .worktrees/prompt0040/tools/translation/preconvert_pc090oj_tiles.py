#!/usr/bin/env python3
"""Preconvert PC090OJ 16x16 cells into Genesis 8x8 tile order.

Input layout per cell (128 bytes):
- 16 rows, 8 bytes per row (4bpp planar-packed nibbles already in Genesis format)

Output layout per cell (128 bytes):
- 4 tiles x 32 bytes in TL, BL, TR, BR slot order
- Matches previous frontend_decode_pc090oj_cell() runtime byte rearrangement exactly.
"""

from __future__ import annotations

import argparse
from pathlib import Path

CELL_BYTES = 128
ROW_BYTES = 8
ROWS_PER_CELL = 16
TILE_BYTES = 32
OUTPUT_CELL_BYTES = 4 * TILE_BYTES


def convert_cell(cell: bytes) -> bytes:
    if len(cell) != CELL_BYTES:
        raise ValueError(f"cell size mismatch: expected {CELL_BYTES}, got {len(cell)}")

    out = bytearray(OUTPUT_CELL_BYTES)

    for y in range(ROWS_PER_CELL):
        src_row = cell[y * ROW_BYTES:(y + 1) * ROW_BYTES]

        if y < 8:
            left_base = 0 * TILE_BYTES
            right_base = 2 * TILE_BYTES
            dst_row = y
        else:
            left_base = 1 * TILE_BYTES
            right_base = 3 * TILE_BYTES
            dst_row = y - 8

        left_off = left_base + dst_row * 4
        right_off = right_base + dst_row * 4

        out[left_off:left_off + 4] = src_row[0:4]
        out[right_off:right_off + 4] = src_row[4:8]

    return bytes(out)


def convert_blob(data: bytes) -> bytes:
    if len(data) % CELL_BYTES != 0:
        raise ValueError(
            f"input size {len(data)} is not a multiple of {CELL_BYTES} bytes"
        )

    out = bytearray(len(data))
    cell_count = len(data) // CELL_BYTES

    for i in range(cell_count):
        start = i * CELL_BYTES
        out[start:start + CELL_BYTES] = convert_cell(data[start:start + CELL_BYTES])

    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preconvert PC090OJ tiles for Genesis runtime DMA")
    parser.add_argument(
        "--input",
        default="build/regions/pc090oj.bin",
        help="Source PC090OJ binary",
    )
    parser.add_argument(
        "--output",
        default="build/pc090oj_genesis.bin",
        help="Output preconverted binary",
    )
    args = parser.parse_args()

    src_path = Path(args.input)
    dst_path = Path(args.output)

    src = src_path.read_bytes()
    dst = convert_blob(src)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_bytes(dst)

    print(f"wrote {dst_path} ({len(dst)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
