#!/usr/bin/env python3
"""Compare one matched ORIGINAL ARCADE / GENESIS NTSC stage-entry snapshot.

The original PC080SN name RAM is an oracle only.  Production remains the native
semantic-source -> final Genesis VDP path.  This verifier checks that the final
resident Genesis name-table pattern identities occupy the same logical cells as
the arcade oracle, and separately reports attributes, VRAM publication, and the
collision side channel.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def words(path: Path) -> list[int]:
    data = path.read_bytes()
    if len(data) & 1:
        raise SystemExit(f"odd-sized word file: {path}")
    return [int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2)]


def row(path: Path) -> dict[str, int | str]:
    with path.open(newline="") as source:
        raw = next(csv.DictReader(source, delimiter="\t"))
    return {key: (value if key in {"snapshot"} else int(value, 16) if key != "frame" else int(value))
            for key, value in raw.items()}


def visible_top(scroll: int) -> int:
    return ((-scroll + 8) & 0x1FF) >> 3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arcade", type=Path, required=True)
    parser.add_argument("--genesis", type=Path, required=True)
    parser.add_argument("--patterns", type=Path, required=True,
                        help="native build's 32-byte code-indexed PC080SN pattern ROM")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    arcade = row(args.arcade / "capture.tsv")
    genesis = row(args.genesis / "state.tsv")
    matched_fields = ("record", "selector", "scroll_a_x", "scroll_a_y",
                      "scroll_b_x", "scroll_b_y", "strip_index", "strip_group")
    mismatched_state = {
        key: [arcade[key], genesis[key]] for key in matched_fields
        if arcade[key] != genesis[key]
    }
    if mismatched_state:
        raise SystemExit(f"snapshots are not semantically matched: {mismatched_state}")

    name_ram = (args.arcade / "pc080sn_name_ram.bin").read_bytes()
    lut = words(args.genesis / "active_lut.bin")
    staged_a = words(args.genesis / "staged_plane_a.bin")
    staged_b = words(args.genesis / "staged_plane_b.bin")
    vram_a = words(args.genesis / "vram_plane_a.bin")
    vram_b = words(args.genesis / "vram_plane_b.bin")
    vram_patterns = (args.genesis / "vram.bin").read_bytes()
    source_patterns = args.patterns.read_bytes()
    if len(vram_patterns) != 0x10000:
        raise SystemExit(f"expected 64 KiB Genesis VRAM dump, got {len(vram_patterns)} bytes")

    def u16(offset: int) -> int:
        return int.from_bytes(name_ram[offset:offset + 2], "big")

    details: list[dict[str, int | str]] = []
    summary: dict[str, int | str | dict[str, list[int | str]]] = {
        "state_match": "YES", "matched_state": {key: genesis[key] for key in matched_fields}
    }
    for plane, base, scroll, staged, vram in (
            ("A", 0x8000, int(genesis["scroll_a_y"]), staged_a, vram_a),
            ("B", 0x0000, int(genesis["scroll_b_y"]), staged_b, vram_b)):
        top = visible_top(scroll)
        pattern_mismatch = attr_mismatch = lut_missing = vram_mismatch = 0
        vram_pattern_mismatch = 0
        bad_slots: set[int] = set()
        compared = excluded = 0
        # Plane A is reseeded after the retained camera initializer has chosen
        # the final 64-row PC080SN window.  A 32-row Genesis plane displays the
        # same sequence by placing each selected logical row at row & 31; VSRAM
        # then starts on top & 31.  Score exactly that selected window.  This is
        # the distinction the old physical-row comparison missed at R1-S2.
        #
        # Plane B is outside this correction and retains the established gate's
        # physical-row model (only row zero shows the final fill alias).
        if plane == "A":
            row_pairs = [((top + delta) & 63, (top + delta) & 31)
                         for delta in range(32)]
        else:
            row_pairs = [(32 if physical_row == 0 else physical_row,
                          physical_row)
                         for physical_row in range(32)]
        for logical_row, physical_row in row_pairs:
            for column in range(64):
                # Plane A row zero is presentation-owned by the native HUD after
                # the stage fill, and column zero is the deliberately blank
                # off-screen origin column (H-scroll carries the 16px origin
                # bias).  Neither is a gameplay stage-assembly output at this
                # capture point, so report but do not score them.
                if plane == "A" and (physical_row == 0 or column == 0):
                    excluded += 1
                    continue
                compared += 1
                pc080sn = base + logical_row * 0x100 + column * 4
                arcade_attr = u16(pc080sn)
                arcade_code = u16(pc080sn + 2) & 0x3FFF
                slot = lut[arcade_code] if arcade_code < len(lut) else 0
                index = physical_row * 64 + column
                actual = staged[index]
                hardware = vram[index]
                if arcade_code and not slot:
                    lut_missing += 1
                pattern_bad = (actual & 0x07FF) != slot
                expected_pattern = source_patterns[arcade_code * 32:(arcade_code + 1) * 32]
                actual_pattern = vram_patterns[slot * 32:(slot + 1) * 32]
                resident_bad = bool(arcade_code and slot and expected_pattern != actual_pattern)
                # Plane A intentionally uses one authored carrier line.  Attribute
                # comparison here is restricted to orientation, which is independent
                # of RG-022 palette authorship.
                expected_flip = (arcade_attr & 0xC000) >> 3
                attr_bad = (actual & 0x1800) != expected_flip
                vram_bad = actual != hardware
                pattern_mismatch += int(pattern_bad)
                attr_mismatch += int(attr_bad)
                vram_mismatch += int(vram_bad)
                vram_pattern_mismatch += int(resident_bad)
                if resident_bad:
                    bad_slots.add(slot)
                if (pattern_bad or attr_bad or vram_bad or resident_bad) and len(details) < 256:
                    details.append({
                        "plane": plane, "physical_row": physical_row,
                        "logical_row": logical_row, "column": column,
                        "arcade_attr": f"0x{arcade_attr:04X}",
                        "arcade_code": f"0x{arcade_code:04X}",
                        "expected_slot": f"0x{slot:04X}",
                        "staged_word": f"0x{actual:04X}",
                        "vram_word": f"0x{hardware:04X}",
                        "resident_pattern_match": not resident_bad,
                        "expected_pattern_prefix": expected_pattern[:8].hex(),
                        "resident_pattern_prefix": actual_pattern[:8].hex(),
                    })
        summary[f"plane_{plane.lower()}_visible_top"] = top
        summary[f"plane_{plane.lower()}_cells_compared"] = compared
        summary[f"plane_{plane.lower()}_presentation_cells_excluded"] = excluded
        summary[f"plane_{plane.lower()}_pattern_mismatches"] = pattern_mismatch
        summary[f"plane_{plane.lower()}_orientation_mismatches"] = attr_mismatch
        summary[f"plane_{plane.lower()}_lut_missing"] = lut_missing
        summary[f"plane_{plane.lower()}_vram_mismatches"] = vram_mismatch
        summary[f"plane_{plane.lower()}_vram_pattern_mismatches"] = vram_pattern_mismatch
        summary[f"plane_{plane.lower()}_bad_resident_slots"] = len(bad_slots)

    arcade_collision = (args.arcade / "collision_map.bin").read_bytes()
    genesis_collision = (args.genesis / "collision_map.bin").read_bytes()
    collision_words = sum(
        arcade_collision[i:i + 2] != genesis_collision[i:i + 2]
        for i in range(0, min(len(arcade_collision), len(genesis_collision)), 2))
    summary["collision_word_mismatches"] = collision_words
    summary["gate"] = "PASS" if all(
        value == 0 for key, value in summary.items()
        if key.endswith(("_mismatches", "_missing"))) else "FAIL"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "first_differences": details}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
