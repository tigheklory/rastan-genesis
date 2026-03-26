#!/usr/bin/env python3
"""Arcade-anchored semantic entry validator (read-only).

Expected Genesis targets are derived from arcade-entry truth using:
  expected_genesis = arcade_addr + relocation_delta + cumulative_shift(<= arcade_addr)
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_hex(value: str) -> int:
    value = value.strip().lower()
    if value.startswith("0x"):
        return int(value, 16)
    return int(value, 16)


@dataclass
class ShiftEntry:
    arcade_pc: int
    delta: int


@dataclass
class RoutineResolved:
    logical_name: str
    arcade_entry: int
    genesis_entry_expected: int
    internal_arcade: List[int]
    internal_genesis_expected: List[int]


@dataclass
class CaseResult:
    case_id: str
    confidence: str
    callsite_genesis: int
    callsite_arcade_context: Optional[int]
    logical_target: str
    opcode: Optional[int]
    resolved_target_genesis: Optional[int]
    target_source: str
    expected_target_genesis: Optional[int]
    expected_target_arcade: Optional[int]
    classification: str
    reason: str


def read_u16_be(data: bytes, off: int) -> int:
    return (data[off] << 8) | data[off + 1]


def read_u32_be(data: bytes, off: int) -> int:
    return (
        (data[off] << 24)
        | (data[off + 1] << 16)
        | (data[off + 2] << 8)
        | data[off + 3]
    )


def decode_call_target(rom: bytes, callsite: int) -> Tuple[Optional[int], Optional[int], str]:
    if callsite < 0 or callsite + 2 > len(rom):
        return None, None, "rom_oob"

    op = read_u16_be(rom, callsite)

    if op in (0x4EB9, 0x4EF9):
        if callsite + 6 > len(rom):
            return op, None, "rom_oob_abs_long"
        return op, read_u32_be(rom, callsite + 2), "rom_abs_long"

    # BSR.B
    if (op & 0xFF00) == 0x6100 and (op & 0x00FF) != 0:
        disp8 = op & 0x00FF
        if disp8 & 0x80:
            disp8 -= 0x100
        return op, (callsite + 2 + disp8) & 0xFFFFFFFF, "rom_bsr_byte"

    # BSR.W
    if op == 0x6100:
        if callsite + 4 > len(rom):
            return op, None, "rom_oob_bsr_w"
        disp16 = read_u16_be(rom, callsite + 2)
        if disp16 & 0x8000:
            disp16 -= 0x10000
        return op, (callsite + 2 + disp16) & 0xFFFFFFFF, "rom_bsr_word"

    return op, None, f"unsupported_opcode_0x{op:04X}"


def build_shift_entries(shift_replacements: list[dict]) -> List[ShiftEntry]:
    entries: List[ShiftEntry] = []
    for rep in shift_replacements:
        pc = parse_hex(rep["arcade_pc"])
        orig = bytes.fromhex(rep["original_bytes"].replace(" ", ""))
        repl = bytes.fromhex(rep["replacement_bytes"].replace(" ", ""))
        entries.append(ShiftEntry(arcade_pc=pc, delta=len(repl) - len(orig)))
    entries.sort(key=lambda e: e.arcade_pc)
    return entries


def cumulative_shift_at_or_before(addr: int, shifts: List[ShiftEntry]) -> int:
    total = 0
    for s in shifts:
        if s.arcade_pc <= addr:
            total += s.delta
        else:
            break
    return total


def map_arcade_to_genesis(addr: int, relocation_delta: int, shifts: List[ShiftEntry]) -> int:
    return addr + relocation_delta + cumulative_shift_at_or_before(addr, shifts)


def classify(
    actual_target: Optional[int],
    expected_target: Optional[int],
    internal_targets: List[int],
) -> Tuple[str, str]:
    if actual_target is None:
        return "UNRESOLVED", "Call target could not be decoded confidently"

    if expected_target is None:
        return "UNRESOLVED", "No expected semantic target available"

    if actual_target == expected_target:
        return "MATCH_ENTRY", "Callsite resolves to expected semantic entry"

    if actual_target in internal_targets:
        return "INSIDE_BODY", "Callsite resolves inside routine body/non-entry address"

    return "WRONG_FUNCTION", "Callsite target is outside expected routine entry/body set"


def main() -> int:
    parser = argparse.ArgumentParser(description="Arcade-anchored semantic entry validator")
    parser.add_argument("--manifest", default="docs/research/semantic_entry_manifest.json")
    parser.add_argument("--spec", default="specs/startup_title_remap.json")
    parser.add_argument("--rom", default="dist/Rastan_214.bin")
    parser.add_argument("--fail-on-suspect", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    spec_path = Path(args.spec)
    rom_path = Path(args.rom)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    relocation_delta = parse_hex(manifest.get("mapping", {}).get("relocation_delta", "0x200"))
    shifts = build_shift_entries(spec.get("shift_replacements", []))
    shift_count = len(shifts)

    routines: Dict[str, RoutineResolved] = {}
    for r in manifest.get("routines", []):
        logical = r["logical_name"]
        arcade_entry = parse_hex(r["arcade_entry"])
        internal_arcade = [parse_hex(x) for x in r.get("internal_non_entry_arcade", [])]
        expected_gen = map_arcade_to_genesis(arcade_entry, relocation_delta, shifts)
        internal_gen = [map_arcade_to_genesis(x, relocation_delta, shifts) for x in internal_arcade]
        routines[logical] = RoutineResolved(
            logical_name=logical,
            arcade_entry=arcade_entry,
            genesis_entry_expected=expected_gen,
            internal_arcade=internal_arcade,
            internal_genesis_expected=internal_gen,
        )

    rom = rom_path.read_bytes() if rom_path.exists() else b""

    results: List[CaseResult] = []
    for case in manifest.get("validation_cases", []):
        case_id = case.get("case_id", "<unnamed>")
        callsite_genesis = parse_hex(case["callsite_genesis"])
        callsite_arcade_ctx = parse_hex(case["callsite_arcade_context"]) if case.get("callsite_arcade_context") else None
        logical_target = case["logical_target"]
        conf = str(case.get("confidence", "UNKNOWN"))

        routine = routines.get(logical_target)
        expected_target_gen = routine.genesis_entry_expected if routine else None
        expected_target_arc = routine.arcade_entry if routine else None
        internal_gen = routine.internal_genesis_expected if routine else []

        opcode: Optional[int]
        target: Optional[int]
        source: str
        if rom:
            opcode, target, source = decode_call_target(rom, callsite_genesis)
        else:
            opcode, target, source = None, None, "rom_missing"

        classification, reason = classify(target, expected_target_gen, internal_gen)

        results.append(
            CaseResult(
                case_id=case_id,
                confidence=conf,
                callsite_genesis=callsite_genesis,
                callsite_arcade_context=callsite_arcade_ctx,
                logical_target=logical_target,
                opcode=opcode,
                resolved_target_genesis=target,
                target_source=source,
                expected_target_genesis=expected_target_gen,
                expected_target_arcade=expected_target_arc,
                classification=classification,
                reason=reason,
            )
        )

    print("Arcade-Anchored Semantic Entry Validation")
    print(f"manifest: {manifest_path}")
    print(f"spec: {spec_path}")
    print(f"rom: {rom_path if rom_path.exists() else 'MISSING'}")
    print(f"shift_table_entry_count: {shift_count}")
    print(f"relocation_delta: 0x{relocation_delta:06X}")
    print(f"routines_covered: {len(routines)}")
    print(f"validation_cases: {len(results)}")
    print()

    counts: Dict[str, int] = {"MATCH_ENTRY": 0, "INSIDE_BODY": 0, "WRONG_FUNCTION": 0, "UNRESOLVED": 0}
    review: List[CaseResult] = []

    for r in results:
        counts[r.classification] = counts.get(r.classification, 0) + 1
        if r.classification != "MATCH_ENTRY":
            review.append(r)

        print(f"case_id: {r.case_id}")
        print(f"  logical_target: {r.logical_target}")
        print(f"  confidence: {r.confidence}")
        print(f"  callsite_genesis: 0x{r.callsite_genesis:06X}")
        if r.callsite_arcade_context is not None:
            print(f"  callsite_arcade_context: 0x{r.callsite_arcade_context:06X}")
        print(f"  decoded_opcode: {('0x%04X' % r.opcode) if r.opcode is not None else 'UNKNOWN'}")
        print(
            "  resolved_target_genesis: "
            + (f"0x{r.resolved_target_genesis:06X}" if r.resolved_target_genesis is not None else "UNKNOWN")
        )
        print(f"  target_source: {r.target_source}")
        print(
            "  expected_target_arcade: "
            + (f"0x{r.expected_target_arcade:06X}" if r.expected_target_arcade is not None else "UNKNOWN")
        )
        print(
            "  expected_target_genesis: "
            + (f"0x{r.expected_target_genesis:06X}" if r.expected_target_genesis is not None else "UNKNOWN")
        )
        print(f"  classification: {r.classification}")
        print(f"  reason: {r.reason}")
        print()

    print("Summary")
    for key in ("MATCH_ENTRY", "INSIDE_BODY", "WRONG_FUNCTION", "UNRESOLVED"):
        print(f"  {key}: {counts.get(key, 0)}")

    print()
    print("Cases Requiring Human Review")
    if not review:
        print("  none")
    else:
        for r in review:
            actual = f"0x{r.resolved_target_genesis:06X}" if r.resolved_target_genesis is not None else "UNKNOWN"
            expected = f"0x{r.expected_target_genesis:06X}" if r.expected_target_genesis is not None else "UNKNOWN"
            print(
                "  "
                + f"{r.case_id}: actual={actual}, expected={expected}, "
                + f"class={r.classification}, confidence={r.confidence}"
            )

    if args.fail_on_suspect and review:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
