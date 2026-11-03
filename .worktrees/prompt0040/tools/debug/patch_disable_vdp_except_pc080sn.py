#!/usr/bin/env python3
"""
VDP Isolation Patcher — PC080SN-Only Mode

Disables all non-PC080SN VDP activity by replacing selected functions with
RTS + NOP fill.  This allows isolating the PC080SN tilemap pipeline for
debugging.

Usage:
    python tools/debug/patch_disable_vdp_except_pc080sn.py \
        --input  dist/Rastan_318.bin \
        --output dist/Rastan_318_pc080sn_only.bin \
        [--symbols apps/rastan/out/symbol.txt] \
        [--disable-text] \
        [--apply-debug-palette]
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

RTS = 0x4E75
NOP = 0x4E71

# Number of NOP words to write after the RTS (neutralizes function prologue).
NOP_FILL_WORDS = 8  # 16 bytes

# Required functions to disable (always patched).
REQUIRED_FUNCTIONS = [
    "genesistan_palette_commit_asm",
    "genesistan_scroll_commit_vdp",
    "genesistan_sprite_commit_asm",
]

# Optional text-writer functions (patched only with --disable-text).
TEXT_FUNCTIONS = [
    "genesistan_hook_text_writer_3bb48_impl",
    "genesistan_hook_text_writer_3c3fe",
]

# Functions that MUST NOT be patched (safety check).
PROTECTED_FUNCTIONS = [
    "genesistan_pc080sn_commit_planes",
]

# ── Debug Palette ────────────────────────────────────────────────────────────
# 64 entries across 4 palette lines (16 entries each).
# Genesis format: 0000 BBB0 GGG0 RRR0
#
# Design:
#   Entry 0 of each line = black (transparent background)
#   Entries 1-15 = distinct hues per line, increasing brightness
#
# Line 0 (entries  0-15): Red/warm ramp
# Line 1 (entries 16-31): Green/cyan ramp
# Line 2 (entries 32-47): Blue/purple ramp
# Line 3 (entries 48-63): Yellow/orange ramp
#
# Each line uses a different dominant channel so palette line assignment
# is immediately visible by hue.

def _gen(r: int, g: int, b: int) -> int:
    """Pack 3-bit RGB (0-7 each) into Genesis CRAM word."""
    return ((b & 7) << 9) | ((g & 7) << 5) | ((r & 7) << 1)

DEBUG_PALETTE: list[int] = [
    # Line 0: Red/warm ramp  (entries 0-15)
    _gen(0, 0, 0),  # 0: black
    _gen(1, 0, 0),  # 1: dark red
    _gen(2, 0, 0),  # 2
    _gen(3, 0, 0),  # 3
    _gen(4, 0, 0),  # 4
    _gen(5, 0, 0),  # 5
    _gen(6, 0, 0),  # 6
    _gen(7, 0, 0),  # 7: bright red
    _gen(7, 1, 0),  # 8: red-orange
    _gen(7, 2, 0),  # 9
    _gen(7, 3, 0),  # 10
    _gen(7, 4, 0),  # 11
    _gen(7, 5, 1),  # 12
    _gen(7, 6, 2),  # 13
    _gen(7, 7, 3),  # 14
    _gen(7, 7, 7),  # 15: white

    # Line 1: Green/cyan ramp  (entries 16-31)
    _gen(0, 0, 0),  # 0: black
    _gen(0, 1, 0),  # 1: dark green
    _gen(0, 2, 0),  # 2
    _gen(0, 3, 0),  # 3
    _gen(0, 4, 0),  # 4
    _gen(0, 5, 0),  # 5
    _gen(0, 6, 0),  # 6
    _gen(0, 7, 0),  # 7: bright green
    _gen(0, 7, 1),  # 8: green-cyan
    _gen(0, 7, 2),  # 9
    _gen(0, 7, 3),  # 10
    _gen(1, 7, 4),  # 11
    _gen(2, 7, 5),  # 12
    _gen(3, 7, 6),  # 13
    _gen(4, 7, 7),  # 14
    _gen(7, 7, 7),  # 15: white

    # Line 2: Blue/purple ramp  (entries 32-47)
    _gen(0, 0, 0),  # 0: black
    _gen(0, 0, 1),  # 1: dark blue
    _gen(0, 0, 2),  # 2
    _gen(0, 0, 3),  # 3
    _gen(0, 0, 4),  # 4
    _gen(0, 0, 5),  # 5
    _gen(0, 0, 6),  # 6
    _gen(0, 0, 7),  # 7: bright blue
    _gen(1, 0, 7),  # 8: blue-purple
    _gen(2, 0, 7),  # 9
    _gen(3, 0, 7),  # 10
    _gen(4, 1, 7),  # 11
    _gen(5, 2, 7),  # 12
    _gen(6, 3, 7),  # 13
    _gen(7, 4, 7),  # 14
    _gen(7, 7, 7),  # 15: white

    # Line 3: Yellow/orange ramp  (entries 48-63)
    _gen(0, 0, 0),  # 0: black
    _gen(1, 1, 0),  # 1: dark yellow
    _gen(2, 2, 0),  # 2
    _gen(3, 3, 0),  # 3
    _gen(4, 4, 0),  # 4
    _gen(5, 5, 0),  # 5
    _gen(6, 6, 0),  # 6
    _gen(7, 7, 0),  # 7: bright yellow
    _gen(7, 6, 0),  # 8: yellow-orange
    _gen(7, 5, 0),  # 9
    _gen(7, 4, 0),  # 10
    _gen(7, 3, 0),  # 11
    _gen(6, 2, 0),  # 12
    _gen(5, 1, 0),  # 13
    _gen(7, 3, 1),  # 14
    _gen(7, 7, 7),  # 15: white
]

assert len(DEBUG_PALETTE) == 64


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_symbol_file(path: Path) -> dict[str, int]:
    """Parse nm-style symbol file into {name: address} dict."""
    symbols: dict[str, int] = {}
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                addr_str, _typ, name = parts[0], parts[1], parts[2]
                try:
                    symbols[name] = int(addr_str, 16)
                except ValueError:
                    continue
    return symbols


def addr_to_rom_offset(addr: int) -> int:
    """Convert a 68000 address to a ROM file offset."""
    return addr


def patch_function(rom: bytearray, offset: int, name: str) -> list[str]:
    """Overwrite function at *offset* with RTS + NOP fill.  Returns log lines."""
    log: list[str] = []

    end = offset + 2 + NOP_FILL_WORDS * 2
    if end > len(rom):
        log.append(f"  SKIP {name}: address 0x{offset:06X} outside ROM (size 0x{len(rom):06X})")
        return log

    orig_bytes = rom[offset : offset + 2 + NOP_FILL_WORDS * 2]
    orig_hex = orig_bytes.hex()

    struct.pack_into(">H", rom, offset, RTS)

    for i in range(NOP_FILL_WORDS):
        struct.pack_into(">H", rom, offset + 2 + i * 2, NOP)

    log.append(f"  {name}")
    log.append(f"    address : 0x{offset:06X}")
    log.append(f"    original: {orig_hex}")
    log.append(f"    patched : {rom[offset:end].hex()}")

    return log


def apply_debug_palette_patch(
    rom: bytearray,
    symbols: dict[str, int],
) -> list[str]:
    """Replace genesistan_palette_commit_asm with a minimal CRAM writer that
    streams 64 fixed debug palette entries from genesistan_palette_rom_table,
    and write those 64 entries into the ROM table.

    Returns log lines.
    """
    log: list[str] = []

    # ── Resolve required symbols ─────────────────────────────────────────
    palette_fn = symbols.get("genesistan_palette_commit_asm")
    rom_table = symbols.get("genesistan_palette_rom_table")
    if palette_fn is None or rom_table is None:
        log.append("  ERROR: required symbols not found for debug palette")
        return log

    fn_off = addr_to_rom_offset(palette_fn)
    tbl_off = addr_to_rom_offset(rom_table)

    # ── Step 1: Write 64 debug palette entries into ROM table ────────────
    for i, color in enumerate(DEBUG_PALETTE):
        struct.pack_into(">H", rom, tbl_off + i * 2, color)

    log.append("  Debug palette written to genesistan_palette_rom_table")
    log.append(f"    ROM offset: 0x{tbl_off:06X}")
    log.append(f"    entries   : {len(DEBUG_PALETTE)}")

    # ── Step 2: Replace palette_commit_asm with minimal CRAM writer ──────
    #
    # Hand-assembled 68000 code (34 bytes):
    #
    #   movea.l  #0x00C00004, %a1       ; 227C 00C0 0004
    #   move.l   #0xC0000000, (%a1)     ; 22BC C000 0000   (CRAM write addr 0)
    #   lea      <rom_table_addr>, %a0  ; 41F9 xxxx xxxx
    #   movea.l  #0x00C00000, %a1       ; 227C 00C0 0000
    #   moveq    #63, %d0              ; 703F
    # .loop:
    #   move.w   (%a0)+, (%a1)         ; 3298
    #   dbra     %d0, .loop            ; 51C8 FFFC
    #   rts                            ; 4E75
    #
    # Total: 6+6+6+6+2+2+4+2 = 34 bytes

    code = bytearray()
    # movea.l #0x00C00004, %a1
    code += struct.pack(">HI", 0x227C, 0x00C00004)
    # move.l #0xC0000000, (%a1)
    code += struct.pack(">HI", 0x22BC, 0xC0000000)
    # lea <rom_table_addr>.l, %a0
    code += struct.pack(">HI", 0x41F9, rom_table)
    # movea.l #0x00C00000, %a1
    code += struct.pack(">HI", 0x227C, 0x00C00000)
    # moveq #63, %d0
    code += struct.pack(">H", 0x703F)
    # move.w (%a0)+, (%a1)
    code += struct.pack(">H", 0x3298)
    # dbra %d0, -4 (relative to PC after dbra = back to move.w)
    code += struct.pack(">Hh", 0x51C8, -4)
    # rts
    code += struct.pack(">H", 0x4E75)

    assert len(code) == 34, f"expected 34 bytes, got {len(code)}"

    orig_bytes = rom[fn_off : fn_off + len(code)]
    rom[fn_off : fn_off + len(code)] = code

    log.append("  Palette commit replaced with debug CRAM writer")
    log.append(f"    function  : 0x{fn_off:06X}")
    log.append(f"    code size : {len(code)} bytes")
    log.append(f"    original  : {orig_bytes.hex()}")
    log.append(f"    patched   : {code.hex()}")

    return log


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="VDP Isolation Patcher — disable all non-PC080SN VDP paths",
    )
    parser.add_argument("--input", required=True, help="Input ROM path")
    parser.add_argument("--output", required=True, help="Output ROM path")
    parser.add_argument(
        "--symbols",
        default="apps/rastan/out/symbol.txt",
        help="Path to nm-style symbol file (default: apps/rastan/out/symbol.txt)",
    )
    parser.add_argument(
        "--disable-text",
        action="store_true",
        help="Also disable text-writer hooks (title text)",
    )
    parser.add_argument(
        "--apply-debug-palette",
        action="store_true",
        help="Apply a fixed visible debug palette (diagnostic only)",
    )
    args = parser.parse_args()

    # ── Load symbol table ────────────────────────────────────────────────
    sym_path = Path(args.symbols)
    if not sym_path.exists():
        print(f"ERROR: symbol file not found: {sym_path}", file=sys.stderr)
        sys.exit(1)
    symbols = parse_symbol_file(sym_path)

    # ── Build target list ────────────────────────────────────────────────
    targets = list(REQUIRED_FUNCTIONS)
    if args.disable_text:
        targets.extend(TEXT_FUNCTIONS)

    # When debug palette is active, palette_commit_asm gets a replacement
    # routine instead of a plain RTS, so remove it from the RTS target list.
    if args.apply_debug_palette:
        targets = [t for t in targets if t != "genesistan_palette_commit_asm"]

    # ── Resolve addresses ────────────────────────────────────────────────
    resolved: list[tuple[str, int]] = []
    for name in targets:
        if name not in symbols:
            print(f"ERROR: symbol '{name}' not found in {sym_path}", file=sys.stderr)
            sys.exit(1)
        addr = symbols[name]
        offset = addr_to_rom_offset(addr)
        resolved.append((name, offset))

    # ── Safety: verify protected functions are NOT in target list ─────────
    for prot in PROTECTED_FUNCTIONS:
        if prot in targets:
            print(f"ERROR: protected function '{prot}' in target list!", file=sys.stderr)
            sys.exit(1)

    # ── Load ROM ─────────────────────────────────────────────────────────
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input ROM not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    rom = bytearray(input_path.read_bytes())

    # ── Patch ────────────────────────────────────────────────────────────
    log_lines: list[str] = []
    log_lines.append("VDP Isolation Patcher — PC080SN-Only Mode")
    log_lines.append(f"Input : {args.input}")
    log_lines.append(f"Output: {args.output}")
    log_lines.append(f"Text disabled: {args.disable_text}")
    log_lines.append(f"Debug palette: {args.apply_debug_palette}")
    log_lines.append("")
    log_lines.append("Functions patched (RTS):")

    for name, offset in resolved:
        log_lines.extend(patch_function(rom, offset, name))

    if args.apply_debug_palette:
        log_lines.append("")
        log_lines.append("Debug palette patch:")
        log_lines.extend(apply_debug_palette_patch(rom, symbols))

    log_lines.append("")
    log_lines.append("Functions preserved (NOT patched):")
    for prot in PROTECTED_FUNCTIONS:
        if prot in symbols:
            log_lines.append(f"  {prot} at 0x{symbols[prot]:06X}")

    # ── Write output ─────────────────────────────────────────────────────
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(rom)

    # ── Print log ────────────────────────────────────────────────────────
    for line in log_lines:
        print(line)

    print(f"\nWrote {output_path} ({len(rom)} bytes)")


if __name__ == "__main__":
    main()
