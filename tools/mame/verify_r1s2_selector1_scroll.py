#!/usr/bin/env python3
"""Verify reached selector-1 rows and Plane B against independent arcade data."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def words(path: Path) -> list[int]:
    data = path.read_bytes()
    return [int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2)]


def state(path: Path) -> dict[str, int]:
    with path.open(newline="") as source:
        row = next(csv.DictReader(source, delimiter="\t"))
    return {key: int(value, 16) if key != "frame" else int(value)
            for key, value in row.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--genesis", type=Path, required=True)
    parser.add_argument("--arcade-entry", type=Path, required=True)
    parser.add_argument("--pan-maps", type=Path, required=True)
    parser.add_argument("--patterns", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed-top", type=int, default=33)
    args = parser.parse_args()

    current = state(args.genesis / "state.tsv")
    record, selector = current["record"], current["selector"]
    if selector not in (1, 2):
        raise SystemExit(f"capture selector is {selector}, not 1/2")
    top_a = ((-current["scroll_a_y"] + 8) & 0x1FF) >> 3
    top_b = ((-current["scroll_b_y"] + 8) & 0x1FF) >> 3

    pan = args.pan_maps.read_bytes()
    pan_offset = int.from_bytes(pan[record * 4:record * 4 + 4], "big")
    if pan_offset == 0xFFFFFFFF:
        raise SystemExit(f"record {record} has no compiled pan map")
    staged_a, staged_b = words(args.genesis / "staged_plane_a.bin"), words(args.genesis / "staged_plane_b.bin")
    vram_a, vram_b = words(args.genesis / "vram_plane_a.bin"), words(args.genesis / "vram_plane_b.bin")
    lut = words(args.genesis / "active_lut.bin")
    vram = (args.genesis / "vram.bin").read_bytes()
    patterns = args.patterns.read_bytes()
    name_ram = (args.arcade_entry / "pc080sn_name_ram.bin").read_bytes()

    entered_rows = list(range(top_a, args.seed_top)) if top_a <= args.seed_top else []
    a_compiled_mismatch = a_vdp_mismatch = 0
    first_a = None
    for logical_row in entered_rows:
        physical_row = logical_row & 31
        for column in range(64):
            expected_offset = pan_offset + (logical_row * 64 + column) * 2
            expected = int.from_bytes(pan[expected_offset:expected_offset + 2], "big")
            index = physical_row * 64 + column
            actual, hardware = staged_a[index], vram_a[index]
            if actual != expected:
                a_compiled_mismatch += 1
                first_a = first_a or [logical_row, column, expected, actual]
            a_vdp_mismatch += actual != hardware

    b_pattern_mismatch = b_attr_mismatch = b_lut_missing = 0
    b_vdp_mismatch = b_resident_mismatch = 0
    first_b = None
    for delta in range(32):
        logical_row = (top_b + delta) & 63
        physical_row = logical_row & 31
        for column in range(64):
            source = logical_row * 0x100 + column * 4
            attr = int.from_bytes(name_ram[source:source + 2], "big")
            code = int.from_bytes(name_ram[source + 2:source + 4], "big") & 0x3FFF
            slot = lut[code] if code < len(lut) else 0
            expected_attr = ((((attr >> 13) & 1) << 15) | ((attr & 3) << 13) |
                             (((attr >> 15) & 1) << 12) | (((attr >> 14) & 1) << 11))
            index = physical_row * 64 + column
            actual, hardware = staged_b[index], vram_b[index]
            pattern_bad = (actual & 0x7FF) != slot
            attr_bad = (actual & 0xF800) != expected_attr
            b_pattern_mismatch += pattern_bad
            b_attr_mismatch += attr_bad
            b_lut_missing += bool(code and not slot)
            b_vdp_mismatch += actual != hardware
            resident_bad = bool(code and slot and
                                patterns[code * 32:(code + 1) * 32] !=
                                vram[slot * 32:(slot + 1) * 32])
            b_resident_mismatch += resident_bad
            if pattern_bad or attr_bad or resident_bad:
                first_b = first_b or [logical_row, column, code, slot, actual]

    arcade_collision = (args.arcade_entry / "collision_map.bin").read_bytes()
    genesis_collision = (args.genesis / "collision_map.bin").read_bytes()
    collision_mismatch = sum(
        arcade_collision[i:i + 2] != genesis_collision[i:i + 2]
        for i in range(0, min(len(arcade_collision), len(genesis_collision)), 2))
    summary = {
        "record": record, "selector": selector,
        "scroll_a_y": current["scroll_a_y"], "scroll_b_y": current["scroll_b_y"],
        "plane_a_visible_top": top_a, "plane_b_visible_top": top_b,
        "plane_a_entered_rows": entered_rows,
        "plane_a_compiled_row_mismatches": a_compiled_mismatch,
        "plane_a_staged_vdp_mismatches": a_vdp_mismatch,
        "plane_b_pattern_mismatches": b_pattern_mismatch,
        "plane_b_attribute_mismatches": b_attr_mismatch,
        "plane_b_lut_missing": b_lut_missing,
        "plane_b_staged_vdp_mismatches": b_vdp_mismatch,
        "plane_b_resident_pattern_mismatches": b_resident_mismatch,
        "collision_word_mismatches": collision_mismatch,
        "first_plane_a_difference": first_a, "first_plane_b_difference": first_b,
    }
    summary["gate"] = "PASS" if all(
        value == 0 for key, value in summary.items()
        if key.endswith(("_mismatches", "_missing"))) else "FAIL"
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
