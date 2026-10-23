#!/usr/bin/env python3
"""Regression: reflow must not mutate bytes wholly replaced by a later pass."""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

from shift_table_patcher import apply_shift_table, new_offset


def main() -> int:
    original = bytearray(0x80)
    # Outside branch enters the later opaque region.
    original[0x08:0x0C] = bytes.fromhex("60000036")  # 08+2+36 = 40
    # Internal opaque branch points backward across the variable replacement.
    original[0x40:0x44] = bytes.fromhex("6000FFCE")  # 40+2-32 = 10
    original[0x20:0x22] = bytes.fromhex("4E75")
    replacement = {
        "arcade_pc": "0x20",
        "original_bytes": "4E75",
        "replacement_bytes": "4E714E714E75",       # synthetic +4 bytes
    }
    disasm = "   8:\t6000 0036 \tbra.w 0x40\n   40:\t6000 ffce \tbra.w 0x10\n"
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "synthetic.disasm.txt"
        path.write_text(disasm)
        result = apply_shift_table(
            bytes(original), [replacement], str(path), 0, len(original),
            opaque_source_ranges=[(0x40, 0x44)],
        )
    outside_disp = struct.unpack_from(">h", result, 0x0A)[0]
    assert 0x08 + 2 + outside_disp == new_offset(0x40, [(0x20, 4)])
    opaque_start = new_offset(0x40, [(0x20, 4)])
    assert result[opaque_start:opaque_start + 4] == bytes.fromhex("6000FFCE")
    print("SHIFT_OPAQUE_RANGE_TEST_PASS external-reference-relocated internal-bytes-preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
