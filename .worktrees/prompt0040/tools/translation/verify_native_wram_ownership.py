#!/usr/bin/env python3
"""Check that the native Plane-A LUT and linker-owned crash record are disjoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def symbols(path: Path) -> dict[str, int]:
    result = {}
    for line in path.read_text().splitlines():
        fields = line.split()
        if len(fields) >= 3:
            try:
                result[fields[-1]] = int(fields[0], 16)
            except ValueError:
                pass
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", type=Path, default=ROOT / "apps/rastan-direct/out/symbol.txt")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    syms = symbols(args.symbols)
    required = [
        "fg_boundary_active_lut",
        "FG_BOUNDARY_LUT_WORDS",
        "CRASH_RECORD_BASE",
        "CRASH_A5_VALID",
        "CRASH_RECORD_END",
    ]
    missing = [name for name in required if name not in syms]
    if missing:
        raise SystemExit("missing symbols: " + ", ".join(missing))

    base = syms["fg_boundary_active_lut"]
    words = syms["FG_BOUNDARY_LUT_WORDS"]
    lut_first = base
    lut_end = base + words * 2
    fixed_first = syms["CRASH_RECORD_BASE"]
    fixed_end = syms["CRASH_RECORD_END"]
    overlap = max(lut_first, fixed_first) < min(lut_end, fixed_end)
    crash_layout_valid = fixed_end - fixed_first == 0x64 and syms["CRASH_A5_VALID"] == fixed_end - 2
    result = {
        "schema_version": 2,
        "symbols": str(args.symbols),
        "indexed_owner": {
            "name": "fg_boundary_active_lut",
            "base": f"0x{base:08X}",
            "word_count": words,
            "last_inclusive": f"0x{lut_end - 1:08X}",
        },
        "fixed_owner": {
            "name": "crash record",
            "first": f"0x{fixed_first:08X}",
            "last_inclusive": f"0x{fixed_end - 1:08X}",
            "byte_count": fixed_end - fixed_first,
        },
        "physical_overlap": overlap,
        "crash_layout_valid": crash_layout_valid,
        "manual_diversion_required": False,
        "result": "PASS" if not overlap and crash_layout_valid else "FAIL",
        "limitations": [
            "Checks the complete dense LUT and linker-owned crash-record ranges represented by linked symbols.",
            "Does not discover arbitrary computed pointers, undocumented fixed owners, or stale ROM code-pointer tables.",
            "Does not validate runtime sequencing; it is a pre-publication static ownership invariant.",
        ],
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
