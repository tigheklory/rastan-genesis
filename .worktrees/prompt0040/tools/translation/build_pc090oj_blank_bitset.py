#!/usr/bin/env python3
"""Build a 4096-bit PC090OJ blank-cell bitset from converted sprite cells."""

from __future__ import annotations

import argparse
from pathlib import Path

CELL_BYTES = 128
CODE_COUNT = 4096
BITSET_BYTES = CODE_COUNT // 8


def build_bitset(data: bytes) -> bytes:
    expected = CODE_COUNT * CELL_BYTES
    if len(data) != expected:
        raise ValueError(f"expected {expected} bytes, got {len(data)}")

    out = bytearray(BITSET_BYTES)
    for code in range(CODE_COUNT):
        cell = data[code * CELL_BYTES:(code + 1) * CELL_BYTES]
        if all(b == 0 for b in cell):
            out[code >> 3] |= 1 << (code & 7)
    return bytes(out)


def blank_codes(bitset: bytes) -> list[int]:
    codes: list[int] = []
    for code in range(CODE_COUNT):
        if bitset[code >> 3] & (1 << (code & 7)):
            codes.append(code)
    return codes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="build/pc090oj_genesis.bin")
    parser.add_argument("--output", default="build/pc090oj_blank_bitset.bin")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    bitset = build_bitset(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bitset)

    codes = " ".join(f"0x{code:03X}" for code in blank_codes(bitset))
    print(f"wrote {dst} ({len(bitset)} bytes); blank_count={len(blank_codes(bitset))}; blank_codes={codes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
