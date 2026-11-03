#!/usr/bin/env python3
"""Post-freeze comparison of the independent audit with the current compiler input.

This file was created only after blind_freeze.sha256 was written and verified.
It deliberately imports the current collector because that is the implementation
being compared, not the source of the frozen independent set.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = Path(__file__).resolve().parent
PHASE1_SEGMENTS = tuple(range(16))
CURRENT_COMPILER_SEGMENTS = tuple(range(23))


def load_current_collector():
    path = ROOT / "tools/translation/precompute_pc080sn_tile_lut.py"
    spec = importlib.util.spec_from_file_location("postfreeze_pc080sn_collector", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pattern_hashes(gfx: bytes, codes: set[int]) -> set[str]:
    return {
        hashlib.sha256(gfx[code * 32:(code + 1) * 32]).hexdigest()
        for code in codes
    }


def main() -> None:
    maincpu = (ROOT / "build/regions/maincpu.bin").read_bytes()
    gfx = (ROOT / "build/regions/pc080sn.bin").read_bytes()
    collector = load_current_collector()

    with (ANALYSIS / "physical_patterns.csv").open(newline="") as handle:
        independent_hashes = {
            row["exact_pattern_hash"] for row in csv.DictReader(handle)
        }
    column_hashes: dict[int, set[str]] = {}
    with (ANALYSIS / "map_usage.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            column_hashes.setdefault(int(row["world_column"]), set()).add(
                row["exact_pattern_hash"]
            )

    def max_window(width: int) -> dict[str, int]:
        count = -1
        start = 0
        for first in range(1024 - width + 1):
            candidate = len(set().union(*(column_hashes[column]
                                          for column in range(first, first + width))))
            if candidate > count:
                count, start = candidate, first
        return {"width": width, "patterns": count, "start": start,
                "end": start + width - 1}

    boundary = json.loads(
        (ROOT / "build/pc080sn_boundary/boundary_report.json").read_text()
    )

    per_segment_codes = {
        segment: set(collector.collect_runtime_gameplay_fg_tiles(maincpu, (segment,)))
        for segment in CURRENT_COMPILER_SEGMENTS
    }
    per_segment_hashes = {
        segment: pattern_hashes(gfx, codes)
        for segment, codes in per_segment_codes.items()
    }
    compiler_codes = set().union(*per_segment_codes.values())
    compiler_hashes = set().union(*per_segment_hashes.values())
    compiler_phase1_hashes = set().union(
        *(per_segment_hashes[segment] for segment in PHASE1_SEGMENTS)
    )
    extra = compiler_hashes - independent_hashes
    missing = independent_hashes - compiler_hashes
    wrong_phase = set().union(
        *(per_segment_hashes[segment] for segment in range(16, 23))
    ) - independent_hashes

    report = {
        "freeze_manifest": "blind_freeze.sha256",
        "comparison_performed_after_freeze": True,
        "current_compiler_records": list(CURRENT_COMPILER_SEGMENTS),
        "current_compiler_rows_per_record": [0, 63],
        "current_compiler_columns_per_record": [0, 63],
        "current_compiler_source_table_entries_per_record": 256,
        "current_compiler_input_codes": len(compiler_codes),
        "current_compiler_input_exact_patterns": len(compiler_hashes),
        "current_compiler_phase1_exact_patterns": len(compiler_phase1_hashes),
        "independent_phase1_exact_patterns": len(independent_hashes),
        "extra_compiler_patterns": len(extra),
        "missing_compiler_patterns": len(missing),
        "extra_categories": {
            "wrong_phase_records_16_22": len(wrong_phase),
            "other": len(extra - wrong_phase),
        },
        "exact_match": compiler_hashes == independent_hashes,
        "phase1_subset_exact_match": compiler_phase1_hashes == independent_hashes,
        "per_record_code_counts": [len(per_segment_codes[s]) for s in CURRENT_COMPILER_SEGMENTS],
        "per_record_exact_pattern_counts": [
            len(per_segment_hashes[s]) for s in CURRENT_COMPILER_SEGMENTS
        ],
        "capacity": {
            "pattern_slots_0_through_1535": 1536,
            "blank_slot": 0,
            "fixed_plane_b_slots": [boundary["plane_b_slot_first"],
                                    boundary["plane_b_slot_last"]],
            "fixed_plane_b_patterns": boundary["plane_b_patterns"],
            "plane_a_slots": [boundary["plane_a_slot_first"],
                              boundary["plane_a_slot_last"]],
            "plane_a_capacity": boundary["plane_a_slot_capacity"],
            "sprite_tile_base": boundary["sprite_tile_base"],
            "sprite_complete_16x16_cells": boundary["sprite_16x16_cells"],
            "sprite_pattern_slots": boundary["sprite_16x16_cells"] * 4,
            "spare_pattern_slot": 1535,
            "phase1_exact_vocabulary": len(independent_hashes),
            "phase1_flip_normalized_vocabulary": 1246,
            "max_64_column_ring": max_window(64),
            "max_40_column_visible_view": max_window(40),
            "max_41_column_subtile_scrolled_view": max_window(41),
        },
        "notes": [
            "The collector walks all 16 source banks, 16 descriptor groups, four columns, and four rows for each selected record.",
            "For records 0-15 that traversal equals the independently reconstructed 64x64 legal Phase-1 map.",
            "The production boundary compiler selects all Round-1 records 0-22, so its aggregate input crosses from Phase 1 into castle/boss records 16-22.",
            "The allocator deduplicates exact 32-byte pattern bytes; logical-code aliases do not consume duplicate physical slots.",
        ],
    }
    (ANALYSIS / "postfreeze_compiler_comparison.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
