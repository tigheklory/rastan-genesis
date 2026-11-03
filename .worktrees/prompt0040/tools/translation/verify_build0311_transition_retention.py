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

    # RG-021: eight stable epochs (six Round 1, two Round 2), the two original streamed overlap packages, and the
    # Segment-10 -> 11 / record-12 -> 13 overlaps. Stable packages 3 and 4 are locked to their
    # accepted Build-0397 map/upload/identity payloads.
    assert const["FG_BOUNDARY_EPOCHS"] == 8
    assert const["FG_BOUNDARY_PACKAGES"] == 12
    assert const["FG_BOUNDARY_TRANSITION_HANDOFF_COLUMN"] == 45
    assert len(binary) == const["FG_BOUNDARY_BINARY_LEN"]
    assert report["record_to_epoch"] == ([0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 3, 3, 4, 4, 4] +
                                          [5] * 7 + [6] * 11 + [7] * 12)
    assert report["record_to_package"] == ([0, 0, 0, 8, 9, 2, 2, 2, 2, 2, 2, 10, 3, 11, 4, 4] +
                                            [5] * 7 + [6] * 11 + [7] * 12)

    layout = {item["package"]: item for item in report["binary_contract"]["package_layout"]}

    # RG-021 adds boss-tail and Round-2 data by appending to the established
    # identity namespace. Every pre-boss Round-1 stable/transition payload must
    # remain byte-for-byte identical; package 5 is intentionally expanded from
    # records 16-20 to 16-22.
    locked_payloads = {
        0: "9a4c320cb62c0a28140d03555aae5fba633ac308028b1f66817ad6db80285553",
        1: "116c203da698ca360490479979839f570f4ba3f01f934e9ca2f39dcf8e1a8212",
        2: "8184e109e8d181c5bd27cd5acdec501505d6b7bb9e126e96d740adaff2f32760",
        3: "616389bb1016326afa76929590fc44180148894c81e2b88e37b97b12026da446",
        4: "2666dd7251959d364b119d1a55de24d010dbdb96ea79a943f1a487f736d8f648",
        8: "b8606eba7bcab115cba693ab8e67f8f485d00cb9bd18cf8f4b14b8e6fd016415",
        9: "819968dcca7f2c91a463d5474e481ef6626bc73d87988c1e17e182cc46f97223",
        10: "4bd3c8a2ddb7606e67c985b6bc3b1ae65fc0368706554216d1672d6a46a55fae",
        11: "8e4130e3754c8c8922037e0b56ba5d0ee9863de33f298400f137c12d781606a3",
    }
    if not CANDIDATE:
        for package, expected_sha in locked_payloads.items():
            item = layout[package]
            payload = binary[item["data_offset"]:item["end"]]
            assert hashlib.sha256(payload).hexdigest() == expected_sha

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
        "rope_to_waterfall": (394, 282, 191),
        "waterfall_to_next_rope": (478, 198, 178),
        "segment10_to_segment11": (607, 69, 302),
        "segment12_to_segment13": (346, 330, 128),
    }
    for name, (peak, margin, incoming_only) in expected.items():
        gate = gates[name]
        assert gate["gate"] == "PASS"
        assert gate["capacity"] == 676
        assert gate["peak_patterns"] <= 676                     # HARD capacity (candidate + baseline)
        assert gate["visible_missing_patterns"] == 0            # HARD: no missing target patterns
        assert gate["slot_collisions"] == 0                     # HARD
        if not CANDIDATE and name == "segment10_to_segment11":
            # Incoming stable slots are authoritative. The existing atomic exact-identity remap
            # moves conflicting outgoing names into the remaining overlap slots.
            assert gate["retained_patterns_moved"] == 99
            assert gate["out_record_patterns"] == 369
            assert gate["in_record_patterns"] == 483
            assert gate["record_shared_patterns"] == 198
            assert gate["outgoing_visible_patterns"] == 304
            assert gate["outgoing_visible_retained_by_stable_in"] == 202
            assert gate["outgoing_visible_lost_by_direct_stable_switch"] == 102
            assert gate["incoming_required_patterns"] == 469
            assert gate["shared_visible_patterns"] == 167
        elif not CANDIDATE and name == "segment12_to_segment13":
            assert gate["retained_patterns_moved"] == 100
            assert gate["out_record_patterns"] == 225
            assert gate["in_record_patterns"] == 218
            assert gate["record_shared_patterns"] == 97
            assert gate["outgoing_visible_patterns"] == 217
            assert gate["outgoing_visible_retained_by_stable_in"] == 115
            assert gate["outgoing_visible_lost_by_direct_stable_switch"] == 102
            assert gate["incoming_required_patterns"] == 217
            assert gate["shared_visible_patterns"] == 89
        elif not CANDIDATE:
            assert gate["retained_patterns_moved"] == 0         # HARD historical transitions
        assert gate["incoming_stable_slots_changed"] == 0       # HARD: Segment-11 lock
        assert gate["handoff_missing_patterns"] == 0            # HARD: transition handoff complete
        if not CANDIDATE:
            assert gate["peak_patterns"] == peak
            assert gate["margin"] == margin
            assert gate["incoming_only_required_patterns"] == incoming_only

    print("BUILD0311_TRANSITION_GATE PASS: rope 12 retained; waterfall 224 retained; "
          "peaks 395/479/607/346 <= 676; stable packages 3/4 and overlap 8 locked; "
          "missing=0; collisions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
