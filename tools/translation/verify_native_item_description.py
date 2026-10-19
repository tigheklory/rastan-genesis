#!/usr/bin/env python3
"""Independent static gate for the native item-description Plane-B ring."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROWS, COLS, PHYS = 64, 64, 32
CELL_BYTES, ROW_BYTES = 4, 0x100
PAGE_A_PC, PAGE_B_PC, WRITER_PC = 0x5602C, 0x56056, 0x563A6
ITEM_SCENE = 0
ITEM_SPRITE_COLBANK = 0x30


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def aliases(data: bytes):
    result = {}
    for offset in range(0x563CE, 0x56440, 2):
        if u16(data, offset) == 0x0C40 and u16(data, offset + 6) == 0x303C:
            result[u16(data, offset + 2)] = u16(data, offset + 8)
    if not result:
        fail("arcade text alias chain")
    return result


def stream(data: bytes, offset: int, alias):
    result = [[]]
    while data[offset]:
        value = data[offset]
        offset += 1
        if value == 0xFF:
            result.append([])
        else:
            result[-1].append(alias.get(value, value))
    return result


def icons(data: bytes, offset: int):
    result = []
    while u16(data, offset) != 0xFFFF:
        result.append(tuple(u16(data, offset + n) for n in (0, 2, 4, 6)))
        offset += 8
    return result


def fail(message: str):
    raise SystemExit("NATIVE_ITEM_VERIFY_FAIL: " + message)


def assembly_constant(source: str, name: str) -> int:
    match = re.search(rf"^\s*\.equ\s+{name},\s*(\d+)\s*$", source, re.MULTILINE)
    if not match:
        fail(f"missing current {name}")
    return int(match.group(1))


def palette_lut(source: str):
    values = []
    active = False
    for raw in source.splitlines():
        line = raw.strip()
        if line == "pc090oj_palsel_lut:":
            active = True
            continue
        if active and line.startswith(".byte"):
            values += [int(token.strip(), 0) for token in line[5:].split(",")]
        elif active and values and line.startswith(".section"):
            break
    if len(values) != 512 or any(not 0 <= value <= 3 for value in values):
        fail("current PC090OJ palette LUT is not 4x128")
    return values


def cwindow_row_col(destination: int):
    offset = destination & 0x3FFF
    return offset // ROW_BYTES, (offset % ROW_BYTES) // CELL_BYTES


def page_call(data: bytes, pc: int):
    if (u16(data, pc), u16(data, pc + 6), u16(data, pc + 12), u16(data, pc + 20)) != \
            (0x207C, 0x227C, 0x323C, 0x207C):
        fail(f"arcade page loader shape at {pc:#x}")
    return u32(data, pc + 2), u32(data, pc + 8), u16(data, pc + 14), u32(data, pc + 22)


def expected_surfaces(data: bytes):
    alias = aliases(data)
    delimiter = u32(data, WRITER_PC + 0x1E)
    if u16(data, WRITER_PC + 0x1C) != 0xD5FC or delimiter % ROW_BYTES:
        fail("arcade delimiter geometry")
    row_step = delimiter // ROW_BYTES
    initial = [[0x20] * COLS for _ in range(ROWS)]
    final = [row[:] for row in initial]
    pages = []
    for pc in (PAGE_A_PC, PAGE_B_PC):
        target = initial if pc == PAGE_A_PC else final
        source, destination, attr, icon_source = page_call(data, pc)
        first_row, first_col = cwindow_row_col(destination)
        decoded = stream(data, source, alias)
        for index, values in enumerate(decoded):
            row = (first_row + index * row_step) & 63
            if first_col + len(values) > COLS:
                fail("arcade text row overflow")
            target[row][first_col:first_col + len(values)] = values
        pages.append((source, destination, attr, icon_source, first_row, first_col, len(decoded)))
        if pc == PAGE_A_PC:
            final = [row[:] for row in initial]
    return initial, final, pages, row_step


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("maincpu", "pc080sn", "pc090oj", "hud-report", "logical-map",
                 "plane-patterns", "icon-patterns", "icon-records", "report",
                 "assembly", "sprite-source", "palette-lut", "spec"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--initial-rows", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--mismatch-report", type=Path)
    args = parser.parse_args()
    main = args.maincpu.read_bytes()
    pc080 = args.pc080sn.read_bytes()
    pc090 = args.pc090oj.read_bytes()
    logical = args.logical_map.read_bytes()
    if len(logical) != ROWS * COLS * 2:
        fail(f"logical map is {len(logical)} bytes, expected 8192")
    report = json.loads(args.report.read_text())
    hud_report = json.loads(args.hud_report.read_text())
    sprite_source = args.sprite_source.read_text()
    palsel = palette_lut(args.palette_lut.read_text())
    sprite_base = assembly_constant(sprite_source, "SPRITE_TILE_BASE")
    native_cells = assembly_constant(sprite_source, "NATIVE_CELLS")
    hud_cells = hud_report.get("fixed_residency_cells")
    if report.get("vram_ownership") != {
        "frontend_hud_fixed_cells": hud_cells,
        "native_cells": native_cells,
        "physical_pattern_limit_exclusive": 1536,
        "plane_pattern_limit_exclusive": sprite_base,
        "source": "current pc090oj_hooks.s constants + native_hud_report.json",
        "sprite_tile_base": sprite_base,
    }:
        fail("VRAM ownership metadata is not derived from current owners")
    # Independently execute the ROM-authored page streams using the hardware
    # row width; no generated placement metadata participates in this oracle.
    initial_codes, expected_codes, pages, row_step = expected_surfaces(main)
    package = args.plane_patterns.read_bytes()
    slot_bytes = {}
    cursor = 0
    while u16(package, cursor) != 0xFFFF:
        slot = u16(package, cursor)
        raw = package[cursor + 2:cursor + 34]
        if not 1 <= slot < sprite_base or len(raw) != 32 or slot in slot_bytes:
            fail("invalid/duplicate Plane-B pattern package entry")
        slot_bytes[slot] = raw
        cursor += 34
    if cursor + 2 != len(package):
        fail("Plane-B pattern package terminator")
    mismatches = []
    for row in range(ROWS):
        for col in range(COLS):
            word = u16(logical, (row * COLS + col) * 2)
            code = expected_codes[row][col]
            if code == 0x20:
                if word != 0:
                    mismatches.append(("unexpected-final-text", row, col, code, word))
            else:
                if word not in slot_bytes:
                    mismatches.append(("missing-final-text", row, col, code, word))
                else:
                    source = pc080[(code & 0x3FFF) * 32:(code & 0x3FFF) * 32 + 32]
                    if slot_bytes[word] != source:
                        mismatches.append(("wrong-final-pattern", row, col, code, word))

    if args.initial_rows:
        initial = args.initial_rows.read_bytes()
        if len(initial) != PHYS * COLS * 2:
            fail(f"initial snapshot is {len(initial)} bytes, expected 4096")
    else:
        # Diagnostic compatibility path used to prove the preserved Build-0454
        # package fails this new oracle. Reconstruct its assembly-declared seed.
        top = assembly_constant(args.assembly.read_text(), "ITEM_INITIAL_TOP_ROW")
        mutable = bytearray(PHYS * COLS * 2)
        for delta in range(PHYS):
            logical_row = (top + delta) & 63
            physical_row = logical_row & 31
            src = logical_row * COLS * 2
            dst = physical_row * COLS * 2
            mutable[dst:dst + COLS * 2] = logical[src:src + COLS * 2]
        initial = bytes(mutable)
    for row in range(PHYS):
        for col in range(COLS):
            word = u16(initial, (row * COLS + col) * 2)
            code = initial_codes[row][col]
            if code == 0x20:
                if word != 0:
                    mismatches.append(("stale-entry-text", row, col, code, word))
            elif word not in slot_bytes or slot_bytes[word] != pc080[(code & 0x3FFF) * 32:(code & 0x3FFF) * 32 + 32]:
                mismatches.append(("missing-or-wrong-entry-text", row, col, code, word))
    if args.mismatch_report:
        categories = {}
        for category, *_rest in mismatches:
            categories[category] = categories.get(category, 0) + 1
        first = None
        if mismatches:
            category, row, col, code, word = mismatches[0]
            first = {"category": category, "row": row, "column": col,
                     "expected_arcade_code": f"0x{code:04X}", "native_word": f"0x{word:04X}"}
        args.mismatch_report.write_text(json.dumps({"total": len(mismatches),
                                                    "categories": categories,
                                                    "first": first}, indent=2, sort_keys=True) + "\n")
    if mismatches:
        category, row, col, code, word = mismatches[0]
        fail(f"oracle mismatches={len(mismatches)} first={category} row={row} col={col} "
             f"expected={code:#06x} native={word:#06x}")

    # Exhaust all 64 possible logical top rows. The physical ring must contain
    # each 32-row window exactly, and N+32 must replace N in the same row.
    for top in range(ROWS):
        owners = [None] * PHYS
        for delta in range(PHYS):
            logical_row = (top + delta) & 63
            physical = logical_row & 31
            if owners[physical] is not None:
                fail(f"duplicate physical owner at top {top}")
            owners[physical] = logical_row
        if sorted(owners) != sorted((top + n) & 63 for n in range(PHYS)):
            fail(f"ring projection mismatch at top {top}")
    for n in range(32):
        if (n & 31) != ((n + 32) & 31):
            fail("N/N+32 identity")
    if (63 & 31) != 31 or (0 & 31) != 0:
        fail("logical/physical wrap")

    # Independently validate the two authoritative icon tables and all fixed
    # pattern uploads. No runtime PC090OJ source-record interpretation remains.
    source_a, source_b = icons(main, pages[0][3]), icons(main, pages[1][3])
    records = args.icon_records.read_bytes()
    if len(records) != (len(source_a) + len(source_b)) * 8:
        fail("icon record count")
    icon_package = args.icon_patterns.read_bytes()
    icon_slot_bytes = {}
    cursor = 0
    while u16(icon_package, cursor) != 0xFFFF:
        slot = u16(icon_package, cursor)
        icon_slot_bytes[slot] = icon_package[cursor + 2:cursor + 34]
        cursor += 34
    if cursor + 2 != len(icon_package):
        fail("icon pattern package terminator")
    first_item_slot = sprite_base + hud_cells * 4
    owner_limit = sprite_base + native_cells * 4
    if icon_slot_bytes and (min(icon_slot_bytes) != first_item_slot or
                            max(icon_slot_bytes) >= owner_limit or owner_limit > 1536):
        fail("icon slots overlap FRONTEND_FULL or name tables")
    for index, (attr, y, code, x) in enumerate(source_a + source_b):
        off = index * 8
        got_y, tile, got_x, got_code = (u16(records, off + n) for n in (0, 2, 4, 6))
        if (got_y, got_x, got_code) != (y, x, code):
            fail(f"icon {index} semantic tuple mismatch")
        base_slot = tile & 0x07FF
        effective_bank = ITEM_SPRITE_COLBANK | (attr & 0x000F)
        expected_line = palsel[ITEM_SCENE * 128 + effective_bank]
        expected_attributes = 0x8000 | (expected_line << 13) | ((attr >> 3) & 0x1800)
        if tile & 0xF800 != expected_attributes:
            fail(f"icon {index} priority/palette/flip mismatch: "
                 f"attr={attr:#06x} bank={effective_bank:#04x} "
                 f"expected-line={expected_line} tile={tile:#06x}")
        raw = pc090[code * 128:code * 128 + 128]
        for quadrant in range(4):
            if icon_slot_bytes.get(base_slot + quadrant) != raw[quadrant * 32:(quadrant + 1) * 32]:
                fail(f"icon {index} pattern mismatch")

    if report.get("format") != "rastan-native-item-description-ring-v3":
        fail("report format")
    if report["geometry"] != {
        "columns": 64, "initial_top_row": 0, "logical_rows": 64,
        "mapping": "physical_row = logical_row & 31", "page_b_install_pixel": 96,
        "physical_rows": 32,
        "page_a_destination": "0x00C00828", "page_a_logical_row": 8,
        "page_a_column": 10, "page_b_destination": "0x00C00028",
        "page_b_physical_row": 0, "page_b_logical_row": 64,
        "page_b_column": 10, "stream_row_stride": 2,
    }:
        fail("geometry metadata")

    if args.reference:
        reference = json.loads(args.reference.read_text())
        if (reference.get("write_count") != 725 or
                reference.get("decoded_immediates", {}).get("delimiter_rows") != row_step or
                len(reference.get("write_ledger", [])) != reference.get("write_count")):
            fail("ROM-driven reference ledger")

    assembly = args.assembly.read_text()
    required = ("genesistan_item_description_enter", "genesistan_item_ring_advance",
                "native_item_logical_map", "native_item_initial_rows", "0x10EE(%a5)", "#31, %d7",
                "bg_row_dirty", "genesistan_hud_activate_frontend")
    if any(token not in assembly for token in required):
        fail("native assembly contract incomplete")
    advance = assembly[assembly.index("genesistan_item_ring_advance:"):
                       assembly.index("genesistan_item_emit_native:")]
    if "#0xFFFFFFFF" in advance or "genesistan_hook_tilemap_bg_fill" in advance:
        fail("ring advance contains full-plane dirty/projector work")
    if advance.count("bset") != 1 or "#31, %d7" not in advance:
        fail("ordinary crossing is not exactly one row/dirty bit")
    sprites = sprite_source
    if "sub.w   transient_items_scroll" in sprites or "addq.w  #1, transient_items_scroll" in sprites:
        fail("separate Genesis item scroll counter remains")
    spec = json.loads(args.spec.read_text())
    cuts = [entry for entry in spec["shift_replacements"] if entry.get("arcade_pc") == "0x05602C"]
    if len(cuts) != 1 or "genesistan_item_description_enter" not in cuts[0].get("replacement_bytes", ""):
        fail("arcade 0x5602C semantic cut absent")
    tick_cuts = [entry for entry in spec["shift_replacements"] if entry.get("arcade_pc") == "0x05607C"]
    if len(tick_cuts) != 1 or "genesistan_pc090oj_hook_sprite_decay_5607c" not in tick_cuts[0].get("replacement_bytes", ""):
        fail("arcade 0x5607C native tick cut absent")
    if any(entry.get("arcade_pc") == "0x05607C" for entry in spec["opcode_replace"]):
        fail("old padded 0x5607C body replacement remains")

    print("NATIVE_ITEM_VERIFY_PASS oracle=ROM+PC080SN logical=64x64 physical=64x32 crossings=64 "
          f"plane_patterns={len(slot_bytes)} icons={len(source_a)}+{len(source_b)}")


if __name__ == "__main__":
    main()
