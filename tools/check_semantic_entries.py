#!/usr/bin/env python3
"""Read-only semantic entry validator.

Checks whether callsites resolve to declared semantic routine entries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_hex(value: str) -> int:
    value = value.strip().lower()
    if value.startswith("0x"):
        return int(value, 16)
    return int(value, 16)


@dataclass
class CaseResult:
    case_id: str
    callsite: int
    target: Optional[int]
    target_source: str
    expected_entry: Optional[int]
    classification: str
    reason: str
    confidence: str


def read_u16_be(data: bytes, off: int) -> int:
    return (data[off] << 8) | data[off + 1]


def read_u32_be(data: bytes, off: int) -> int:
    return (
        (data[off] << 24)
        | (data[off + 1] << 16)
        | (data[off + 2] << 8)
        | data[off + 3]
    )


def decode_call_target(rom: bytes, callsite: int) -> Tuple[Optional[int], str]:
    if callsite < 0 or callsite + 2 > len(rom):
        return None, "rom_oob"

    op = read_u16_be(rom, callsite)

    # JSR abs.l / JMP abs.l
    if op in (0x4EB9, 0x4EF9):
        if callsite + 6 > len(rom):
            return None, "rom_oob_abs_long"
        return read_u32_be(rom, callsite + 2), "rom_abs_long"

    # BSR.B (disp8 in low byte)
    if (op & 0xFF00) == 0x6100 and (op & 0x00FF) != 0:
        disp8 = op & 0x00FF
        if disp8 & 0x80:
            disp8 -= 0x100
        return (callsite + 2 + disp8) & 0xFFFFFFFF, "rom_bsr_byte"

    # BSR.W (disp16 extension)
    if op == 0x6100:
        if callsite + 4 > len(rom):
            return None, "rom_oob_bsr_w"
        disp16 = read_u16_be(rom, callsite + 2)
        if disp16 & 0x8000:
            disp16 -= 0x10000
        return (callsite + 2 + disp16) & 0xFFFFFFFF, "rom_bsr_word"

    return None, f"unsupported_opcode_0x{op:04X}"


def parse_disasm_calls(path: Path) -> Dict[int, int]:
    calls: Dict[int, int] = {}
    if not path.exists():
        return calls

    # Example line: "   3a074:\t4eb9 0005 5ca2 \tjsr 0x55ca2"
    rx = re.compile(r"^\s*([0-9a-fA-F]+):.*\b(jsr|jmp|bsrw?|bsrs?)\s+0x([0-9a-fA-F]+)\b")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = rx.search(line)
        if not m:
            continue
        src = int(m.group(1), 16)
        dst = int(m.group(3), 16)
        calls[src] = dst
    return calls


def classify_target(
    target: Optional[int],
    expected_entry: Optional[int],
    known_internal: List[int],
) -> Tuple[str, str]:
    if target is None:
        return "UNRESOLVED", "Target could not be resolved confidently"

    if expected_entry is None:
        return "UNRESOLVED", "No expected entry declared for logical target"

    if target == expected_entry:
        return "MATCH_ENTRY", "Callsite lands exactly on declared semantic entry"

    if target in known_internal:
        return "INSIDE_BODY", "Callsite lands on known non-entry internal routine address"

    return "OUTSIDE_EXPECTED", "Callsite target differs from semantic entry and known internal addresses"


def main() -> int:
    parser = argparse.ArgumentParser(description="Semantic routine entry checker (read-only batch validator)")
    parser.add_argument(
        "--manifest",
        default="docs/research/semantic_entry_manifest.json",
        help="Path to semantic entry manifest JSON",
    )
    parser.add_argument(
        "--rom",
        default="dist/Rastan_214.bin",
        help="Path to ROM for direct call target decoding",
    )
    parser.add_argument(
        "--disasm",
        default="build/maincpu.disasm.txt",
        help="Optional disassembly text for fallback/visibility",
    )
    parser.add_argument(
        "--fail-on-suspect",
        action="store_true",
        help="Return nonzero if any INSIDE_BODY, OUTSIDE_EXPECTED, or UNRESOLVED case is found.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    routines = {r["logical_name"]: r for r in manifest.get("routines", [])}
    cases = manifest.get("validation_cases", [])
    if not cases:
        print("No validation_cases in manifest.")
        return 0

    rom_bytes: Optional[bytes] = None
    rom_path = Path(args.rom)
    if rom_path.exists():
        rom_bytes = rom_path.read_bytes()

    disasm_calls = parse_disasm_calls(Path(args.disasm))

    results: List[CaseResult] = []

    for case in cases:
        case_id = case.get("case_id", "<unnamed>")
        callsite = parse_hex(case["callsite_genesis"])
        logical_target = case["logical_target"]
        routine = routines.get(logical_target)
        expected_entry = parse_hex(routine["genesis_entry"]) if routine and routine.get("genesis_entry") else None

        known_internal: List[int] = []
        if routine:
            known_internal = [parse_hex(x) for x in routine.get("known_non_entry_internal_targets", [])]

        target: Optional[int] = None
        target_source = ""

        if rom_bytes is not None:
            target, target_source = decode_call_target(rom_bytes, callsite)

        if target is None and callsite in disasm_calls:
            target = disasm_calls[callsite]
            target_source = "disasm"

        if target is None and case.get("observed_target_genesis"):
            target = parse_hex(case["observed_target_genesis"])
            target_source = "manifest_observed"

        classification, reason = classify_target(target, expected_entry, known_internal)

        results.append(
            CaseResult(
                case_id=case_id,
                callsite=callsite,
                target=target,
                target_source=target_source or "unresolved",
                expected_entry=expected_entry,
                classification=classification,
                reason=reason,
                confidence=str(case.get("confidence", "UNKNOWN")),
            )
        )

    print("Semantic Entry Validation Results")
    print(f"manifest: {manifest_path}")
    print(f"rom: {rom_path if rom_path.exists() else 'MISSING'}")
    print(f"disasm: {args.disasm}")
    print(f"routines_covered: {len(routines)}")
    print(f"validation_cases: {len(cases)}")
    print()

    counts: Dict[str, int] = {}
    review_needed: List[CaseResult] = []
    for r in results:
        counts[r.classification] = counts.get(r.classification, 0) + 1
        if r.classification in ("INSIDE_BODY", "OUTSIDE_EXPECTED", "UNRESOLVED"):
            review_needed.append(r)
        print(f"case_id: {r.case_id}")
        print(f"  callsite_genesis: 0x{r.callsite:06X}")
        print(
            "  resolved_target_genesis: "
            + (f"0x{r.target:06X}" if r.target is not None else "UNKNOWN")
        )
        print(f"  target_source: {r.target_source}")
        print(
            "  declared_entry_genesis: "
            + (f"0x{r.expected_entry:06X}" if r.expected_entry is not None else "UNKNOWN")
        )
        print(f"  confidence: {r.confidence}")
        print(f"  classification: {r.classification}")
        print(f"  reason: {r.reason}")
        print()

    print("Summary")
    for key in ("MATCH_ENTRY", "INSIDE_BODY", "OUTSIDE_EXPECTED", "UNRESOLVED"):
        print(f"  {key}: {counts.get(key, 0)}")

    print()
    print("Cases Requiring Human Review")
    if not review_needed:
        print("  none")
    else:
        for r in review_needed:
            target_text = f"0x{r.target:06X}" if r.target is not None else "UNKNOWN"
            print(
                "  "
                + f"{r.case_id}: callsite=0x{r.callsite:06X}, target={target_text}, "
                + f"classification={r.classification}, confidence={r.confidence}"
            )

    if args.fail_on_suspect and review_needed:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
