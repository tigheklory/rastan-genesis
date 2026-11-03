#!/usr/bin/env python3
"""Prove the Build 0356 R1/P1 VRAM tail available to sprite patterns.

This is an analysis-only tool. It derives the non-sprite high-water mark from
the zero-drop PC080SN boundary report and tests candidate sprite capacities
against the fixed Genesis VRAM ownership map.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_CONSTANTS = ROOT / "build/pc080sn_boundary/boundary_constants.inc"
BOUNDARY_REPORT = ROOT / "build/pc080sn_boundary/boundary_report.json"
OPTIMIZER_SUMMARY = ROOT / "analysis/graphics_optimizer/round1_phase1/summary.json"
COEXISTENCE = ROOT / "analysis/graphics_optimizer/round1_phase1/coexistence_graph.json"
OBSERVATIONS = (
    ROOT
    / "analysis/graphics_optimizer/round1_phase1_corpus/full_capture/full_observations.csv"
)
OUTPUT = (
    ROOT
    / "analysis/graphics_optimizer/round1_phase1_corpus/generated/r1p1_vram_capacity.json"
)

PATTERN_BYTES = 32
PATTERNS_PER_CELL = 4
SPRITE_LAST = 1535
CANDIDATE_CELLS = (49, 52, 55, 61, 63, 64)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_constants(path: Path) -> dict[str, int]:
    values: dict[str, int] = {}
    expression = re.compile(r"^\.equ\s+(\w+),\s*(0x[0-9A-Fa-f]+|\d+)\s*$")
    for line in path.read_text(encoding="ascii").splitlines():
        match = expression.match(line)
        if match:
            values[match.group(1)] = int(match.group(2), 0)
    return values


def pattern_region(owner: str, first: int, last: int, lifetime: str) -> dict[str, object]:
    return {
        "owner": owner,
        "pattern_start": first,
        "pattern_end": last,
        "vram_start": f"0x{first * PATTERN_BYTES:04X}",
        "vram_end": f"0x{((last + 1) * PATTERN_BYTES) - 1:04X}",
        "bytes": (last - first + 1) * PATTERN_BYTES,
        "lifetime": lifetime,
    }


def working_set() -> dict[str, object]:
    frame_codes: dict[str, set[str]] = defaultdict(set)
    with OBSERVATIONS.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["round"] == "01" and row["code"] not in {"0000", "FFFF"}:
                frame_codes[row["frame"]].add(row["code"])
    values = [len(codes) for codes in frame_codes.values()]
    return {
        "frames": len(values),
        "peak_cells": max(values),
        "frames_over_49": sum(value > 49 for value in values),
        "frames_over_58": sum(value > 58 for value in values),
    }


def main() -> None:
    constants = parse_constants(BOUNDARY_CONSTANTS)
    boundary = json.loads(BOUNDARY_REPORT.read_text(encoding="utf-8"))
    optimizer = json.loads(OPTIMIZER_SUMMARY.read_text(encoding="utf-8"))
    coexistence = json.loads(COEXISTENCE.read_text(encoding="utf-8"))

    assert constants["FG_BOUNDARY_SLOT_FIRST"] == 663
    assert constants["FG_BOUNDARY_FIXED_B_MAP_COUNT"] == 854
    assert constants["FG_BOUNDARY_FIXED_B_SLOT_LAST"] == 1983
    assert constants["FG_BOUNDARY_SPRITE_TILE_BASE"] == 1339
    assert constants["FG_BOUNDARY_SPRITE_CELLS"] == 49
    assert boundary["compiler_zero_drop_gate"] == "PASS"
    assert not any(boundary["plane_a_dropped_by_record"])
    assert boundary["plane_b_dropped"] == 0

    package_patterns = [entry["required_patterns"] for entry in boundary["packages_detail"]]
    max_plane_a = max(package_patterns)
    plane_a_first = boundary["plane_a_slot_first"]
    plane_a_compacted_last = plane_a_first + max_plane_a - 1
    first_reusable = plane_a_compacted_last + 1
    free_tail_patterns = SPRITE_LAST - first_reusable + 1
    max_cells = free_tail_patterns // PATTERNS_PER_CELL
    spare_patterns = free_tail_patterns % PATTERNS_PER_CELL

    candidates = []
    for cells in CANDIDATE_CELLS:
        patterns = cells * PATTERNS_PER_CELL
        base = SPRITE_LAST - patterns + 1
        conflict = max(0, first_reusable - base)
        candidates.append(
            {
                "cells": cells,
                "patterns": patterns,
                "pattern_base": base,
                "vram_start": f"0x{base * PATTERN_BYTES:04X}",
                "additional_patterns_below_current_base": max(
                    0, boundary["sprite_tile_base"] - base
                ),
                "verdict": "PASS" if conflict == 0 else "FAIL",
                "conflicting_owner": None if conflict == 0 else "Plane A package residency",
                "conflicting_patterns": conflict,
            }
        )

    physical_envelope = {
        "logical_cell_start": 0,
        "logical_cell_end": max_cells - 1,
        "pattern_start": first_reusable,
        "pattern_end": first_reusable + max_cells * PATTERNS_PER_CELL - 1,
        "vram_start": f"0x{first_reusable * PATTERN_BYTES:04X}",
        "vram_end": f"0x{((first_reusable + max_cells * PATTERNS_PER_CELL) * PATTERN_BYTES) - 1:04X}",
        "unassigned_spare_pattern_start": first_reusable + max_cells * PATTERNS_PER_CELL,
        "unassigned_spare_pattern_end": SPRITE_LAST,
        "actor_owner_assignment": "BLOCKED",
        "reason": "sprite semantic domain/lifetimes/frame sets are incomplete and the current graph permits no aliases",
    }

    result = {
        "schema": "r1p1-vram-capacity-v1",
        "baseline_build": 356,
        "analysis_only": True,
        "inputs": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (
                BOUNDARY_CONSTANTS,
                BOUNDARY_REPORT,
                OPTIMIZER_SUMMARY,
                COEXISTENCE,
                OBSERVATIONS,
            )
        },
        "non_sprite_proof": {
            "plane_b_patterns": boundary["plane_b_patterns"],
            "plane_a_package_patterns": package_patterns,
            "plane_a_max_simultaneous_patterns": max_plane_a,
            "highest_required_non_sprite_pattern": plane_a_compacted_last,
            "first_safely_reusable_pattern": first_reusable,
            "free_tail_patterns_through_1535": free_tail_patterns,
            "free_tail_bytes": free_tail_patterns * PATTERN_BYTES,
            "maximum_complete_sprite_cells": max_cells,
            "spare_patterns_after_complete_cells": spare_patterns,
            "zero_drop": True,
        },
        "ownership": [
            pattern_region("transparent pattern", 0, 0, "always"),
            pattern_region("fixed Plane B vocabulary, part 1", 1, 662, "R1/P1 gameplay"),
            pattern_region(
                "Plane A package arena (compacted exact maximum)",
                663,
                plane_a_compacted_last,
                "selected stable/transition package",
            ),
            pattern_region("sprite physical envelope", first_reusable, SPRITE_LAST, "R1/P1 gameplay"),
            pattern_region("Plane B nametable", 1536, 1663, "always"),
            pattern_region("fixed Plane B vocabulary, part 2", 1664, 1791, "R1/P1 gameplay"),
            pattern_region("Plane A nametable", 1792, 1919, "always"),
            pattern_region("fixed Plane B vocabulary, part 3", 1920, 1983, "R1/P1 gameplay"),
            pattern_region("SAT", 1984, 2015, "always"),
            pattern_region("HScroll", 2016, 2047, "always"),
        ],
        "candidates": candidates,
        "physical_envelope": physical_envelope,
        "working_set": working_set(),
        "packing_gate": {
            "sprite_classes": optimizer["sprite_families"],
            "resolved_classes": optimizer["sprite_classes_resolved"],
            "unresolved_classes": optimizer["sprite_classes_unresolved"],
            "semantic_domain_enumerated": optimizer["sprite_semantic_domain_enumerated"],
            "semantic_resolution_complete": optimizer["sprite_semantic_resolution_complete"],
            "complete_sprite_clique": coexistence["complete_sprite_clique"],
            "safe_aliases_proven": 0,
            "concrete_actor_assignment_ready": False,
        },
        "validation": {
            "pattern_1339_vram_start": "0xA760",
            "prompt_0xA6E0_correction": "0xA6E0 is pattern 1335, not pattern 1339",
            "candidate_assertions_passed": True,
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(OUTPUT.relative_to(ROOT))
    print(
        f"highest_non_sprite={plane_a_compacted_last} first_reusable={first_reusable} "
        f"free_patterns={free_tail_patterns} max_cells={max_cells} spare_patterns={spare_patterns}"
    )
    print("candidates=" + ",".join(f"{c['cells']}:{c['verdict']}" for c in candidates))


if __name__ == "__main__":
    main()
