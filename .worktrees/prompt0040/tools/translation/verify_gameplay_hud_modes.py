#!/usr/bin/env python3
"""Static Build-0435 gameplay-HUD semantic and isolation verifier."""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import struct
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "apps/rastan-direct/src/pc090oj_hooks.s"
ARCADE = ROOT / "build/regions/maincpu.bin"


def fail(message: str) -> None:
    raise AssertionError(message)


def words(blob: bytes, offset: int, count: int) -> list[int]:
    return list(struct.unpack_from(f">{count}H", blob, offset))


def require_all(text: str, needles: list[str], label: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        fail(f"{label}: missing {missing}")


def emitted_digits(value: int, start_x: int) -> list[tuple[int, int, int, int]]:
    digits = [(value // (10 ** power)) % 10 for power in range(5, -1, -1)]
    visible = False
    result = []
    for position, digit in enumerate(digits):
        visible = visible or digit != 0
        if visible:
            result.append((0, 0x10, 0xD02A + digit, start_x + position * 8))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode2-before", type=pathlib.Path)
    parser.add_argument("--mode2-after", type=pathlib.Path)
    args = parser.parse_args()

    source = SOURCE.read_text(encoding="utf-8")
    arcade = ARCADE.read_bytes()

    # Original 0x3B802 mode table: P1 and P2 both consume active score +0x11E;
    # high score consumes +0x142.  Destination words distinguish the columns.
    expected_modes = [
        0x0610, 0x00D0, 0x0108, 0x0010, 0xC11E,
        0x0610, 0x00D0, 0x0150, 0x0010, 0xC11E,
        0x0610, 0x00D0, 0x00D8, 0x0010, 0xC142,
    ]
    actual_modes = words(arcade, 0x3B87E, len(expected_modes))
    if actual_modes != expected_modes:
        fail(f"arcade 0x3B87E mode table changed: {actual_modes!r}")

    # Exact fixed gameplay template tuples (Y, code, X).
    high_label = [(0x00, 0x3B, 0x88), (0x00, 0x3A, 0x78),
                  (0x00, 0x3C, 0x98), (0x00, 0x3D, 0xA8),
                  (0x08, 0x3E, 0xB8)]
    p1_label = [(0x10, 0x39, 0x40), (0x00, 0x48, 0x28), (0x00, 0x46, 0x38)]
    p2_label = [(0x10, 0x39, 0x120), (0x00, 0x49, 0x108), (0x00, 0x47, 0x118)]

    def template_records(offset: int, count: int) -> list[tuple[int, int, int]]:
        raw = words(arcade, offset, count * 2)
        return [(raw[i] >> 8, raw[i] & 0xFF, raw[i + 1])
                for i in range(0, len(raw), 2)]

    if template_records(0x3B950, 5) != high_label:
        fail("HIGH label does not match original gameplay template records 4..8")
    if template_records(0x3B9C8, 3) != p1_label:
        fail("1UP label does not match original gameplay template records 28..30")
    if template_records(0x3B9EC, 3) != p2_label:
        fail("2UP label does not match original gameplay template records 37..39")
    if words(arcade, 0x3B998, 12)[1::2] != [0xA8, 0xA0, 0x98, 0x90, 0x88, 0x80]:
        fail("HIGH digit X geometry changed")
    if words(arcade, 0x3B9B0, 12)[1::2] != [0x30, 0x28, 0x20, 0x18, 0x10, 0x08]:
        fail("P1 digit X geometry changed")
    if words(arcade, 0x3B9D4, 12)[1::2] != [0x110, 0x108, 0x100, 0xF8, 0xF0, 0xE8]:
        fail("P2 digit X geometry changed")

    require_all(source, [
        ".if RASTAN_GAMEPLAY_HUD_SPRITES == 1",
        ".equ NATIVE_HUD_BOUND, 37",
        "bsr     .Lnq_project_full_hud",
        "lea     0x0142(%a5), %a0",
        "lea     0x011E(%a5), %a0",
        "lea     0x009E(%a5), %a0",
        "lea     0x00DE(%a5), %a0",
        "native_hud_status_valid",
        "move.w  #13, native_hud_count",
        "move.w  #0xD049, %d3",
        "move.w  #0xD047, %d3",
    ], "mode-1 native implementation")

    full = source.split(".Lnq_project_full_hud:", 1)[1].split("\n.endif", 1)[0]
    for forbidden in ("pc090oj_legacy_emit_pass", ".Lpc090oj_emit_slot",
                      "genesistan_shadow_d00000", "0x00D00000"):
        if forbidden in full:
            fail(f"mode-1 projector reintroduced forbidden legacy dependency: {forbidden}")

    # Exhaust all decimal glyph values at every score position and representative
    # six-digit values for the accepted leading-zero rule.
    for start_x in (0x08, 0x80, 0xE8):
        for position in range(6):
            for digit in range(10):
                value = digit * (10 ** (5 - position))
                output = emitted_digits(value, start_x)
                if digit == 0:
                    if output:
                        fail("all-zero score must remain hidden")
                else:
                    if output[0] != (0, 0x10, 0xD02A + digit, start_x + position * 8):
                        fail("BCD digit identity/position mismatch")
        if [item[3] for item in emitted_digits(123456, start_x)] != [start_x + i * 8 for i in range(6)]:
            fail("six-position BCD ordering mismatch")

    # The retained energy semantic maps 0..48 units onto exactly six cells:
    # full cells use 0x3CD, partial 1..7 use 0x3D4..0x3CE, remainder 0x3D5.
    partial_codes = [0x3D5, 0x3D4, 0x3D3, 0x3D2, 0x3D1, 0x3D0, 0x3CF, 0x3CE]
    for units in range(49):
        full_cells, partial = divmod(units, 8)
        cells = [0x3CD] * full_cells
        if partial:
            cells.append(partial_codes[partial])
        cells.extend([0x3D5] * (6 - len(cells)))
        if len(cells) != 6 or full_cells > 6:
            fail(f"energy cell mapping failed for {units}")
    require_all(source, ["0x013A(%a5)", "0x1328(%a5)", "0x1308(%a5)",
                         "#0x03D5", ".Lstatus_blink_store"], "energy/blink semantics")

    # The protected mode-2 source block and HUD-white routing remain present.
    mode2 = source.split(".Lnq_project_p1_hud:", 1)[1]
    mode2 = mode2.split("\n    .global profile_native_lane_entry", 1)[0]
    require_all(mode2, ["#0x00FF011E", "#0x08", "#0x10", "#0x18", "#0x20",
                        "#0x28", "#0x30", "#0xD039", "#0xD048", "#0xD046",
                        ".Lnq_emit_hud_digit"], "protected mode-2 projector")

    if bool(args.mode2_before) != bool(args.mode2_after):
        fail("provide both --mode2-before and --mode2-after")
    if args.mode2_before:
        before = args.mode2_before.read_bytes()
        after = args.mode2_after.read_bytes()
        if before != after:
            fail("mode-2 assembled .text is not byte-identical")
        digest = hashlib.sha256(after).hexdigest()
        print(f"MODE2_TEXT_IDENTITY PASS sha256={digest} bytes={len(after)}")

    print("ARCADE_HUD_ORACLE PASS")
    print("MODE1_BCD_MATRIX PASS digits=0..9 positions=6 groups=3")
    print("MODE1_ENERGY_MATRIX PASS units=0..48 cells=6 blink=retained")
    print("MODE1_NATIVE_ONLY PASS")
    print("GAMEPLAY_HUD_MODES PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, OSError, ValueError) as exc:
        print(f"GAMEPLAY_HUD_MODES FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
