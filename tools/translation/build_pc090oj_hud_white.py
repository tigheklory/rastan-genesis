#!/usr/bin/env python3
"""Build a PC090OJ HUD glyph slice with opaque pixels remapped to palette index 2."""

from __future__ import annotations

import argparse
from pathlib import Path

CELL_BYTES = 128
HUD_CODE_FIRST = 0x02A
HUD_CODE_LAST = 0x048
WHITE_INDEX = 0x2


def remap_cell(cell: bytes) -> bytes:
    out = bytearray()
    for value in cell:
        hi = WHITE_INDEX if (value >> 4) else 0
        lo = WHITE_INDEX if (value & 0x0F) else 0
        out.append((hi << 4) | lo)
    return bytes(out)


def build_slice(data: bytes) -> bytes:
    expected_multiple = CELL_BYTES
    if len(data) % expected_multiple:
        raise ValueError(f"input size {len(data)} is not a multiple of {CELL_BYTES}")

    cell_count = len(data) // CELL_BYTES
    if cell_count <= HUD_CODE_LAST:
        raise ValueError(f"input has only {cell_count} cells; need code 0x{HUD_CODE_LAST:03X}")

    out = bytearray()
    for code in range(HUD_CODE_FIRST, HUD_CODE_LAST + 1):
        start = code * CELL_BYTES
        out.extend(remap_cell(data[start:start + CELL_BYTES]))
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="build/pc090oj_genesis.bin")
    parser.add_argument("--output", default="build/pc090oj_hud_white_genesis.bin")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(build_slice(src.read_bytes()))
    print(
        f"wrote {dst} ({dst.stat().st_size} bytes); "
        f"codes=0x{HUD_CODE_FIRST:03X}..0x{HUD_CODE_LAST:03X}; "
        f"opaque_index={WHITE_INDEX}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
