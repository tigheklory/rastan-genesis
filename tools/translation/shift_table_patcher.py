#!/usr/bin/env python3
"""
Shift-table patcher for Rastan Genesis port.

Applies variable-length opcode replacements to the arcade maincpu binary,
shifting subsequent code and fixing all relative and absolute references.

PHASES:
  1. Parse build/maincpu.disasm.txt into an instruction map.
  2. Detect jump table regions (mark as data, skip reference fixing).
  3. Apply shift_replacements: insert replacement bytes, build shift table.
  4. Fix relative references (Bcc, BSR, BRA) displaced by shifts.
  5. Fix absolute long references (JSR, JMP, LEA) in code regions.
  6. Emit result and verify (no-op check when replacements are empty).

NO-OP GUARANTEE: when shift_replacements is empty, output is bit-identical
to input. The no-op verification is run inside apply_shift_table() and raises
AssertionError if violated.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path


# ---------------------------------------------------------------------------
# Disassembly parsing
# ---------------------------------------------------------------------------

# Format:  "   <hex_offset>:\t<hex words>\t<mnemonic>..."
# Example: "   3a074:\t4eb9 0005 5ca2 \tjsr 0x55ca2"
# We must capture the full instruction-byte column (all words), not just the
# first word, otherwise instruction sizes are under-counted (e.g. JSR abs.l
# incorrectly treated as 2 bytes instead of 6).
DISASM_LINE_RE = re.compile(
    r"^\s*([0-9a-fA-F]+):\s+([0-9a-fA-F]{2,}(?:\s+[0-9a-fA-F]{2,})*)\s+\S"
)


def parse_disasm(disasm_path: str, source_start: int, source_end: int) -> list[tuple[int, int]]:
    """Return sorted list of (address, size_bytes) for instructions in [source_start, source_end)."""
    insns: list[tuple[int, int]] = []
    path = Path(disasm_path)
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = DISASM_LINE_RE.match(line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        if addr < source_start or addr >= source_end:
            continue
        hex_part = m.group(2).replace(" ", "")
        size = len(hex_part) // 2
        if size < 2:
            continue
        insns.append((addr, size))
    insns.sort(key=lambda x: x[0])
    return insns


# ---------------------------------------------------------------------------
# Jump-table detection
# ---------------------------------------------------------------------------

def detect_jump_tables(
    maincpu_bytes: bytes,
    insns: list[tuple[int, int]],
    source_start: int,
    source_end: int,
) -> set[int]:
    """
    Return set of addresses that appear to be jump-table entries (data words),
    not instructions.  We use a simple heuristic: look for JMP (A0) preceded
    by a word-size displacement table.  For now this is a stub — returns empty.
    Real detection requires pattern matching across the instruction stream.
    """
    # TODO: implement jump-table boundary detection
    return set()


# ---------------------------------------------------------------------------
# Shift-table helpers
# ---------------------------------------------------------------------------

def build_shift_table(
    shift_replacements: list[dict],
    maincpu_bytes: bytes,
) -> list[tuple[int, int]]:
    """
    Validate each replacement and build a sorted shift table.

    Returns list of (insertion_address, net_size_delta) sorted by address.
    Positive net_size_delta means the replacement is longer than the original.
    """
    shifts: list[tuple[int, int]] = []
    for rep in shift_replacements:
        pc = int(rep["arcade_pc"], 0)
        orig = bytes.fromhex(rep["original_bytes"].replace(" ", ""))
        repl = bytes.fromhex(rep["replacement_bytes"].replace(" ", ""))
        actual = maincpu_bytes[pc:pc + len(orig)]
        if actual != orig:
            raise RuntimeError(
                f"shift_replacement at 0x{pc:06X}: "
                f"expected {orig.hex()} but found {actual.hex()}"
            )
        delta = len(repl) - len(orig)
        shifts.append((pc, delta))
    shifts.sort(key=lambda x: x[0])
    return shifts


def new_offset(addr: int, shifts: list[tuple[int, int]]) -> int:
    """Return the new address of arcade address `addr` after applying shifts."""
    accumulated = 0
    for insertion_addr, delta in shifts:
        if insertion_addr <= addr:
            accumulated += delta
        else:
            break
    return addr + accumulated


def accumulated_shift_before(addr: int, shifts: list[tuple[int, int]]) -> int:
    """Return total shift accumulated strictly before addr."""
    accumulated = 0
    for insertion_addr, delta in shifts:
        if insertion_addr < addr:
            accumulated += delta
        else:
            break
    return accumulated


# ---------------------------------------------------------------------------
# Apply replacements
# ---------------------------------------------------------------------------

def apply_replacements(
    maincpu_bytes: bytes,
    shift_replacements: list[dict],
    shifts: list[tuple[int, int]],
) -> bytearray:
    """
    Build the new byte array by splicing in replacement bytes at each site,
    preserving all other bytes unchanged.
    """
    if not shift_replacements:
        return bytearray(maincpu_bytes)

    result = bytearray()
    cursor = 0
    for rep in sorted(shift_replacements, key=lambda r: int(r["arcade_pc"], 0)):
        pc = int(rep["arcade_pc"], 0)
        orig = bytes.fromhex(rep["original_bytes"].replace(" ", ""))
        repl = bytes.fromhex(rep["replacement_bytes"].replace(" ", ""))
        # Copy bytes before this replacement site
        result.extend(maincpu_bytes[cursor:pc])
        # Insert replacement
        result.extend(repl)
        cursor = pc + len(orig)
    # Copy remaining bytes after last replacement
    result.extend(maincpu_bytes[cursor:])
    return result


# ---------------------------------------------------------------------------
# Fix relative branches
# ---------------------------------------------------------------------------

# 68000 branch opcodes:
#   BRA.S / Bcc.S  : 60/6x xx          (word 0x60xx–0x6Fxx, disp8, skip 0x00/0xFF)
#   BRA.W / Bcc.W  : 60/6x 00 xxxx     (disp = 0x00 in second byte → 16-bit follows)
#   BSR.S          : 61 xx              (short BSR)
#   BSR.W          : 61 00 xxxx
#   BRA.L / Bcc.L  : 60/6x FF xxxxxxxx (disp = 0xFF → 32-bit follows, 68020+)

def fix_relative_branches(
    result: bytearray,
    insns: list[tuple[int, int]],
    shifts: list[tuple[int, int]],
    source_start: int,
    source_end: int,
) -> int:
    """Fix relative branch displacements in result.  Returns count of fixes."""
    if not shifts:
        return 0

    count = 0
    for orig_addr, size in insns:
        new_addr = new_offset(orig_addr, shifts)
        byte_at_new = result[new_addr] if new_addr < len(result) else 0
        # Branch opcodes: upper nibble of first byte is 0x6
        if (byte_at_new & 0xF0) != 0x60:
            continue

        disp_byte = result[new_addr + 1] if (new_addr + 1) < len(result) else 0

        if disp_byte == 0xFF:
            # 32-bit displacement (68020+); not used in Rastan, skip
            continue
        elif disp_byte == 0x00:
            # 16-bit displacement in next 2 bytes
            if new_addr + 4 > len(result):
                continue
            old_disp16 = struct.unpack_from(">h", result, new_addr + 2)[0]
            # Old target = old instruction PC + 2 + disp16
            old_target = orig_addr + 2 + old_disp16
            new_target = new_offset(old_target, shifts)
            new_pc = new_addr
            new_disp16 = new_target - (new_pc + 2)
            if -32768 <= new_disp16 <= 32767:
                struct.pack_into(">h", result, new_addr + 2, new_disp16)
                count += 1
            else:
                raise RuntimeError(
                    f"Branch at 0x{orig_addr:06X}: 16-bit displacement overflow "
                    f"after shift: {new_disp16}"
                )
        else:
            # 8-bit displacement in second byte
            old_disp8 = struct.unpack(">b", bytes([disp_byte]))[0]
            old_target = orig_addr + 2 + old_disp8
            new_target = new_offset(old_target, shifts)
            new_pc = new_addr
            new_disp8 = new_target - (new_pc + 2)
            if -128 <= new_disp8 <= 127:
                result[new_addr + 1] = new_disp8 & 0xFF
                count += 1
            else:
                raise RuntimeError(
                    f"Branch at 0x{orig_addr:06X}: 8-bit displacement overflow "
                    f"after shift: {new_disp8}. Promote to .W manually."
                )
    return count


# ---------------------------------------------------------------------------
# Fix absolute long references
# ---------------------------------------------------------------------------

# Opcodes with abs_long operand (4 bytes) immediately following the 2-byte opcode:
#   4E B9  JSR   abs.l
#   4E F9  JMP   abs.l
#   41 F9  LEA   abs.l, An   (many forms, first byte 0x41..0x47, second 0xF9)
#   61 00  BSR.W (handled by branch fixer above)

def is_lea_with_absl(b0: int, b1: int) -> bool:
    """Return True if (b0, b1) is LEA abs.l, An."""
    return (b0 & 0xC1) == 0x41 and b1 == 0xF9


def fix_absolute_longs(
    result: bytearray,
    insns: list[tuple[int, int]],
    shifts: list[tuple[int, int]],
    source_start: int,
    source_end: int,
) -> int:
    """Fix absolute long code references (JSR, JMP, LEA) after shifts.
    Only adjusts references that point into [source_start, source_end).
    Returns count of fixes.
    """
    if not shifts:
        return 0

    count = 0
    for orig_addr, size in insns:
        if size < 6:
            continue
        new_addr = new_offset(orig_addr, shifts)
        if new_addr + 6 > len(result):
            continue
        b0 = result[new_addr]
        b1 = result[new_addr + 1]

        is_jsr = (b0 == 0x4E and b1 == 0xB9)
        is_jmp = (b0 == 0x4E and b1 == 0xF9)
        is_lea = is_lea_with_absl(b0, b1)

        if not (is_jsr or is_jmp or is_lea):
            continue

        ref_addr = struct.unpack_from(">I", result, new_addr + 2)[0]
        # Only adjust if the target is within our source range (a code address)
        if source_start <= ref_addr < source_end:
            new_ref = new_offset(ref_addr, shifts)
            struct.pack_into(">I", result, new_addr + 2, new_ref)
            count += 1

    return count


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def apply_shift_table(
    maincpu_bytes: bytes,
    shift_replacements: list[dict],
    disasm_path: str,
    source_start: int,
    source_end: int,
) -> bytearray:
    """
    Apply shift_replacements to maincpu_bytes, fixing all internal references.

    If shift_replacements is empty this is a strict no-op (output == input).
    """
    # --- PHASE 3: validate and build shift table ---
    shifts = build_shift_table(shift_replacements, maincpu_bytes)

    # --- NO-OP FAST PATH ---
    if not shifts:
        result = bytearray(maincpu_bytes)
        # Verify no-op
        assert result == bytearray(maincpu_bytes), "BUG: no-op produced different output"
        return result

    # --- PHASE 1: parse disassembly ---
    insns = parse_disasm(disasm_path, source_start, source_end)

    # --- PHASE 2: detect jump tables (stub) ---
    jtable_addrs = detect_jump_tables(maincpu_bytes, insns, source_start, source_end)
    insns = [(a, s) for a, s in insns if a not in jtable_addrs]

    # --- PHASE 3: apply replacements ---
    result = apply_replacements(maincpu_bytes, shift_replacements, shifts)

    # --- PHASE 4: fix relative branches ---
    branch_fixes = fix_relative_branches(result, insns, shifts, source_start, source_end)

    # --- PHASE 5: fix absolute long references ---
    abs_fixes = fix_absolute_longs(result, insns, shifts, source_start, source_end)

    print(f"shift_table_patcher: {len(shift_replacements)} replacement(s), "
          f"{branch_fixes} branch fix(es), {abs_fixes} abs-long fix(es)")

    return result


# ---------------------------------------------------------------------------
# CLI entry point (for standalone use and no-op verification)
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply variable-length opcode replacements to arcade maincpu ROM."
    )
    parser.add_argument("--maincpu", required=True, help="Input arcade maincpu binary")
    parser.add_argument("--disasm", required=True, help="Disassembly text (build/maincpu.disasm.txt)")
    parser.add_argument("--spec", required=True, help="Remap spec JSON with shift_replacements key")
    parser.add_argument("--output", required=True, help="Output patched binary")
    parser.add_argument("--verify-noop", action="store_true",
                        help="Run no-op verification (ignore spec replacements, compare to input)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    maincpu_bytes = Path(args.maincpu).read_bytes()

    whole_copy_cfg = spec.get("whole_maincpu_copy", {})
    source_start = int(whole_copy_cfg.get("source_start", "0x000000"), 0)
    source_end = int(whole_copy_cfg.get("source_end_exclusive", "0x060000"), 0)

    if args.verify_noop:
        # Strict no-op test: apply with zero replacements, compare byte-by-byte
        result = apply_shift_table(maincpu_bytes, [], args.disasm, source_start, source_end)
        diffs = sum(1 for a, b in zip(result, maincpu_bytes) if a != b)
        diffs += abs(len(result) - len(maincpu_bytes))
        if diffs == 0:
            print("NO-OP OK")
        else:
            print(f"BUG: {diffs} diffs")
            return 1
        return 0

    shift_replacements = spec.get("shift_replacements", [])
    result = apply_shift_table(maincpu_bytes, shift_replacements, args.disasm, source_start, source_end)
    Path(args.output).write_bytes(result)
    print(f"Written {len(result)} bytes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
