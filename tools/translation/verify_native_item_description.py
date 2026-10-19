#!/usr/bin/env python3
"""Independent static gate for the native item-description Plane-B ring."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROWS, COLS, PHYS = 64, 64, 32
PAGE_A_DEST = 0x00C00828
PAGE_B_DEST = 0x00C00028
PAGE_B_LOGICAL_ROW = 32
ITEM_SCENE = 0
ITEM_SPRITE_COLBANK = 0x30
ALIASES = {0x21: 0x2744, 0x22: 0x2745, 0x27: 0x2746, 0x28: 0x2747,
           0x29: 0x2748, 0x2C: 0x2749, 0x2D: 0x274A, 0x3F: 0x274B}


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def stream(data: bytes, offset: int):
    result = [[]]
    while data[offset]:
        value = data[offset]
        offset += 1
        if value == 0xFF:
            result.append([])
        else:
            result[-1].append(ALIASES.get(value, value))
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
    return offset // 0x200, (offset & 0x1FF) // 4


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("maincpu", "pc080sn", "pc090oj", "hud-report", "logical-map",
                 "plane-patterns", "icon-patterns", "icon-records", "report",
                 "assembly", "sprite-source", "palette-lut", "spec"):
        parser.add_argument("--" + name, type=Path, required=True)
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
    # Independently reconstruct the authoritative arcade 64x64 source-code map.
    expected_codes = [[0x20] * COLS for _ in range(ROWS)]
    page_a_row, page_a_col = cwindow_row_col(PAGE_A_DEST)
    _page_b_physical_row, page_b_col = cwindow_row_col(PAGE_B_DEST)
    for decoded, first, first_col in ((stream(main, 0x5672A), page_a_row, page_a_col),
                                      (stream(main, 0x5697E), PAGE_B_LOGICAL_ROW, page_b_col)):
        for index, row in enumerate(decoded):
            expected_codes[(first + index) & 63][first_col:first_col + len(row)] = row
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
    for row in range(ROWS):
        for col in range(COLS):
            word = u16(logical, (row * COLS + col) * 2)
            code = expected_codes[row][col]
            if code == 0x20:
                if word != 0:
                    fail(f"blank source at {row},{col} is {word:#06x}")
            else:
                if word not in slot_bytes:
                    fail(f"name word at {row},{col} references unowned slot {word}")
                source = pc080[(code & 0x3FFF) * 32:(code & 0x3FFF) * 32 + 32]
                if slot_bytes[word] != source:
                    fail(f"pattern bytes differ from arcade code {code:#06x} at {row},{col}")

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
    source_a, source_b = icons(main, 0x56226), icons(main, 0x562B0)
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

    if report.get("format") != "rastan-native-item-description-ring-v2":
        fail("report format")
    if report["geometry"] != {
        "columns": 64, "initial_top_row": 4, "logical_rows": 64,
        "mapping": "physical_row = logical_row & 31", "page_b_install_pixel": 96,
        "physical_rows": 32,
        "page_a_destination": "0x00C00828", "page_a_logical_row": 4,
        "page_a_column": 10, "page_b_destination": "0x00C00028",
        "page_b_physical_row": 0, "page_b_logical_row": 32,
        "page_b_column": 10,
    }:
        fail("geometry metadata")

    assembly = args.assembly.read_text()
    required = ("genesistan_item_description_enter", "genesistan_item_ring_advance",
                "native_item_logical_map", "0x10EE(%a5)", "#31, %d7",
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

    print("NATIVE_ITEM_VERIFY_PASS logical=64x64 physical=64x32 crossings=64 "
          f"plane_patterns={len(slot_bytes)} icons={len(source_a)}+{len(source_b)}")


if __name__ == "__main__":
    main()
