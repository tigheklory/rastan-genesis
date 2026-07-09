#!/usr/bin/env python3
"""Build a per-code PC090OJ opaque-pixel bounding-box table.

For every PC090OJ sprite code (0..4095) this emits the tight bounding box of the
cell's opaque (non-zero) pixels, in unflipped 16x16 cell space:

    byte 0: min opaque row  (0..15)
    byte 1: max opaque row  (0..15)
    byte 2: min opaque col  (0..15)
    byte 3: max opaque col  (0..15)

The runtime PC090OJ decode (`.Lpc090oj_decode_record`) uses this to keep a mirror
record out of the Genesis SAT only when NO opaque pixel of its current pattern
survives the arcade+Genesis viewport clip (see Build 0147). Fully-blank cells are
already rejected earlier via `pc090oj_blank_code_bitset`, so their box is never
read; they are emitted as 0,0,0,0 purely as a deterministic placeholder.

Input is the raw (pre-`preconvert`) cell region: 16 rows x 8 bytes/row, 4bpp
packed nibbles, high nibble = left (even) pixel, low nibble = right (odd) pixel.
This is the same code index used by the runtime `code` field and the blank bitset.
"""

from __future__ import annotations

import argparse
from pathlib import Path

CELL_BYTES = 128
ROW_BYTES = 8
ROWS_PER_CELL = 16
COLS_PER_CELL = 16
CODE_COUNT = 4096
ENTRY_BYTES = 4


def cell_bbox(cell: bytes) -> tuple[int, int, int, int]:
    """Return (min_row, max_row, min_col, max_col) of opaque pixels, or all-zero
    for a fully blank cell."""
    min_row = min_col = 0xFF
    max_row = max_col = 0
    any_opaque = False
    for row in range(ROWS_PER_CELL):
        base = row * ROW_BYTES
        for byte_idx in range(ROW_BYTES):
            value = cell[base + byte_idx]
            if value == 0:
                continue
            hi = value >> 4          # left (even) pixel
            lo = value & 0x0F        # right (odd) pixel
            for col, pixel in ((2 * byte_idx, hi), (2 * byte_idx + 1, lo)):
                if pixel == 0:
                    continue
                any_opaque = True
                if row < min_row:
                    min_row = row
                if row > max_row:
                    max_row = row
                if col < min_col:
                    min_col = col
                if col > max_col:
                    max_col = col
    if not any_opaque:
        return (0, 0, 0, 0)
    return (min_row, max_row, min_col, max_col)


def build_table(data: bytes) -> bytes:
    expected = CODE_COUNT * CELL_BYTES
    if len(data) != expected:
        raise ValueError(f"expected {expected} bytes, got {len(data)}")
    out = bytearray(CODE_COUNT * ENTRY_BYTES)
    for code in range(CODE_COUNT):
        cell = data[code * CELL_BYTES:(code + 1) * CELL_BYTES]
        min_row, max_row, min_col, max_col = cell_bbox(cell)
        base = code * ENTRY_BYTES
        out[base + 0] = min_row
        out[base + 1] = max_row
        out[base + 2] = min_col
        out[base + 3] = max_col
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="build/regions/pc090oj.bin")
    parser.add_argument("--output", default="build/pc090oj_opaque_bbox.bin")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    table = build_table(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(table)

    nonblank = sum(
        1
        for code in range(CODE_COUNT)
        if table[code * ENTRY_BYTES:code * ENTRY_BYTES + ENTRY_BYTES] != b"\x00\x00\x00\x00"
    )
    print(f"wrote {dst} ({len(table)} bytes); non-blank cells={nonblank}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
