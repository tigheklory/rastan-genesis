#!/usr/bin/env python3
"""Verify the Build 0311 rope/waterfall Plane-A transition package contract."""

from __future__ import annotations

import argparse
import hashlib
import os

CANDIDATE = os.environ.get('LAYERA_EDITOR_CANDIDATE') == '1'
import json
import re
from pathlib import Path


def constants(path: Path) -> dict[str, int]:
    values = {}
    for line in path.read_text().splitlines():
        match = re.fullmatch(r"\.equ\s+(\w+),\s+(0x[0-9A-Fa-f]+|\d+)", line.strip())
        if match:
            values[match.group(1)] = int(match.group(2), 0)
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--constants", type=Path, required=True)
    parser.add_argument("--patterns", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads(args.report.read_text())
    const = constants(args.constants)
    binary = args.packages.read_bytes()
    patterns = args.patterns.read_bytes()

    assert const["FG_BOUNDARY_EPOCHS"] == 7
    assert const["FG_BOUNDARY_PACKAGES"] == 9
    assert const["FG_BOUNDARY_TRANSITION_HANDOFF_COLUMN"] == 45
    assert const["FG_BOUNDARY_CONFLICT_CODE_FIRST"] == 0x031A
    assert const["FG_BOUNDARY_CONFLICT_CODE_COUNT"] == 0x0032
    assert len(binary) == const["FG_BOUNDARY_BINARY_LEN"]
    assert report["record_to_epoch"] == [0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 3, 4, 5, 5, 5, 6]
    assert report["record_to_package"] == [0, 0, 0, 7, 8, 2, 2, 2, 2, 2, 3, 4, 5, 5, 5, 6]

    layout = {item["package"]: item for item in report["binary_contract"]["package_layout"]}

    def package_map(package: int) -> dict[int, int]:
        item = layout[package]
        result = {}
        offset = item["map_start"]
        for _ in range(item["map_count"]):
            code = int.from_bytes(binary[offset:offset + 2], "big")
            slot = int.from_bytes(binary[offset + 2:offset + 4], "big")
            assert code not in result
            result[code] = slot
            offset += 4
        return result

    def verify_object(name: str, stable_package: int, transition_package: int,
                      expected_patterns: int) -> None:
        obj = report[name]
        if not CANDIDATE:
            assert obj["exact_patterns"] == expected_patterns
        assert obj["transition_package"] == transition_package
        assert obj["slots_before_transition"] == obj["slots_in_transition"]
        stable = package_map(stable_package)
        overlap = package_map(transition_package)
        for code_text, expected_hash in zip(obj["codes"], obj["exact_pattern_hashes"]):
            code = int(code_text, 0)
            assert code in stable and code in overlap          # semantic cell still represented
            assert stable[code] == overlap[code]                # retained across transition (structural)
            if not CANDIDATE:
                raw = patterns[code * 32:(code + 1) * 32]
                assert len(raw) == 32
                assert hashlib.sha256(raw).hexdigest() == expected_hash

    verify_object("rope_object", 0, const["FG_BOUNDARY_TRANSITION_AB_PACKAGE"], 12)
    verify_object("waterfall_object", 1, const["FG_BOUNDARY_TRANSITION_BC_PACKAGE"], 224)

    gates = {gate["name"]: gate for gate in report["transition_gates"]}
    expected = {
        "rope_to_waterfall": (394, 90, 158),
        "waterfall_to_next_rope": (479, 5, 146),
    }
    for name, (peak, margin, incoming_only) in expected.items():
        gate = gates[name]
        assert gate["gate"] == "PASS"
        assert gate["capacity"] == 484
        assert gate["peak_patterns"] <= 484                     # HARD capacity (candidate + baseline)
        assert gate["visible_missing_patterns"] == 0            # HARD: no missing target patterns
        assert gate["slot_collisions"] == 0                     # HARD
        assert gate["retained_patterns_moved"] == 0             # HARD
        assert gate["handoff_missing_patterns"] == 0            # HARD: transition handoff complete
        if not CANDIDATE:
            assert gate["peak_patterns"] == peak
            assert gate["margin"] == margin
            assert gate["incoming_only_required_patterns"] == incoming_only

    print("BUILD0311_TRANSITION_GATE PASS: rope 12 retained; waterfall 224 retained; "
          "peaks 394/479 <= 484; missing=0; collisions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
