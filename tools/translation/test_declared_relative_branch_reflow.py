#!/usr/bin/env python3
"""Regression test for semantic declared branches omitted by linear disassembly."""

from __future__ import annotations

import struct

from shift_table_patcher import fix_declared_relative_branches, new_offset, new_target_offset


SOURCE = 0x20
TARGET = 0x80
DECLARATION = {
    "arcade_pc": hex(SOURCE),
    "target_arcade_pc": hex(TARGET),
    "instruction_size_bytes": 4,
    "original_bytes": "6000005E",
}


def decode_target(image: bytes | bytearray, source: int) -> int:
    assert image[source:source + 2] == b"\x60\x00"
    return source + 2 + struct.unpack_from(">h", image, source + 2)[0]


def resolve(shifts: list[tuple[int, int]]) -> tuple[int, int, int]:
    original = bytearray(0xA0)
    original[SOURCE:SOURCE + 4] = bytes.fromhex(DECLARATION["original_bytes"])
    # The representative synthetic shift is insertion-only.
    if shifts:
        assert len(shifts) == 1 and shifts[0][1] > 0
        address, delta = shifts[0]
        final = original[:address] + bytearray(delta) + original[address:]
    else:
        final = bytearray(original)
    fixes = fix_declared_relative_branches(final, original, [DECLARATION], shifts, 0, len(original))
    final_source = new_offset(SOURCE, shifts)
    expected_target = new_target_offset(TARGET, shifts)
    return fixes, decode_target(final, final_source), expected_target


def main() -> int:
    fixes_a, decoded_a, expected_a = resolve([])
    shifts_b = [(0x50, 6)]
    fixes_b, decoded_b, expected_b = resolve(shifts_b)
    stale_b = new_offset(SOURCE, shifts_b) + 2 + 0x005E
    assert fixes_a == 1 and decoded_a == expected_a == TARGET
    assert fixes_b == 1 and decoded_b == expected_b == TARGET + 6
    assert stale_b != expected_b, "synthetic reflow must expose the old stale-displacement behavior"
    print(
        "DECLARED_BRANCH_REFLOW_TEST_PASS "
        f"layout_a=0x{decoded_a:06X} layout_b=0x{decoded_b:06X} stale_b=0x{stale_b:06X}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
