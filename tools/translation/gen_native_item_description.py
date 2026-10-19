#!/usr/bin/env python3
"""Build the item-description attract screen's native Plane-B ring assets."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

LOGICAL_ROWS = 64
PLANE_COLUMNS = 64
PHYSICAL_ROWS = 32
INITIAL_TOP_ROW = 4
PAGE_B_INSTALL_PIXEL = 96
PAGE_A_SOURCE = 0x05672A
PAGE_B_SOURCE = 0x05697E
PAGE_A_DEST_ROW = 8
PAGE_B_DEST_ROW = 0
TEXT_COLUMN = 10
PAGE_A_ICONS = 0x056226
PAGE_B_ICONS = 0x0562B0
ALIASES = {
    0x21: 0x2744, 0x22: 0x2745, 0x27: 0x2746, 0x28: 0x2747,
    0x29: 0x2748, 0x2C: 0x2749, 0x2D: 0x274A, 0x3F: 0x274B,
}


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def words(values) -> bytes:
    return b"".join((value & 0xFFFF).to_bytes(2, "big") for value in values)


def decode_text_stream(main: bytes, source: int) -> list[list[int]]:
    rows: list[list[int]] = [[]]
    cursor = source
    while True:
        value = main[cursor]
        cursor += 1
        if value == 0:
            return rows
        if value == 0xFF:
            rows.append([])
        else:
            rows[-1].append(ALIASES.get(value, value))


def decode_icons(main: bytes, source: int) -> list[tuple[int, int, int, int]]:
    records = []
    cursor = source
    while u16(main, cursor) != 0xFFFF:
        records.append(tuple(u16(main, cursor + offset) for offset in (0, 2, 4, 6)))
        cursor += 8
    return records


def assembly_constant(source: str, name: str) -> int:
    match = re.search(rf"^\s*\.equ\s+{name},\s*(\d+)\s*$", source, re.MULTILINE)
    if not match:
        raise ValueError(f"missing numeric {name} in current sprite owner")
    return int(match.group(1))


def build(main: bytes, pc080: bytes, pc090: bytes, hud_report: dict, sprite_source: str):
    sprite_tile_base = assembly_constant(sprite_source, "SPRITE_TILE_BASE")
    sprite_cell_limit = assembly_constant(sprite_source, "NATIVE_CELLS")
    hud_fixed_cells = hud_report["fixed_residency_cells"]
    hud_slots = sorted(hud_report["sprite_slots"].values())
    expected_hud_slots = list(range(sprite_tile_base, sprite_tile_base + hud_fixed_cells * 4, 4))
    if hud_slots != expected_hud_slots:
        raise ValueError("current FRONTEND_FULL report is not a contiguous fixed-cell owner")
    page_a = decode_text_stream(main, PAGE_A_SOURCE)
    page_b = decode_text_stream(main, PAGE_B_SOURCE)
    source_codes = [[0x20] * PLANE_COLUMNS for _ in range(LOGICAL_ROWS)]
    for rows, first_row in ((page_a, PAGE_A_DEST_ROW), (page_b, PAGE_B_DEST_ROW)):
        for row_index, row in enumerate(rows):
            logical_row = (first_row + row_index) & 63
            if TEXT_COLUMN + len(row) > PLANE_COLUMNS:
                raise ValueError("item text row exceeds 64 columns")
            source_codes[logical_row][TEXT_COLUMN:TEXT_COLUMN + len(row)] = row

    pattern_by_bytes: dict[bytes, int] = {}
    plane_entries: list[tuple[int, int, bytes]] = []
    next_slot = 1
    logical_words: list[int] = []
    source_to_slot: dict[int, int] = {0x20: 0}
    for row in source_codes:
        for code in row:
            if code == 0x20:
                logical_words.append(0)
                continue
            raw = pc080[(code & 0x3FFF) * 32:(code & 0x3FFF) * 32 + 32]
            if len(raw) != 32:
                raise ValueError(f"missing PC080SN pattern 0x{code:04X}")
            slot = pattern_by_bytes.get(raw)
            if slot is None:
                slot = next_slot
                next_slot += 1
                if slot >= sprite_tile_base:
                    raise ValueError("item Plane-B vocabulary overlaps sprite patterns")
                pattern_by_bytes[raw] = slot
                plane_entries.append((slot, code, raw))
            source_to_slot[code] = slot
            logical_words.append(slot)  # arcade attribute 0 -> Genesis palette line 0

    plane_patterns = bytearray()
    for slot, _code, raw in plane_entries:
        plane_patterns += slot.to_bytes(2, "big") + raw
    plane_patterns += b"\xFF\xFF"

    icons_a = decode_icons(main, PAGE_A_ICONS)
    icons_b = decode_icons(main, PAGE_B_ICONS)
    icon_codes: list[int] = []
    for _attr, _y, code, _x in icons_a + icons_b:
        if code not in icon_codes:
            icon_codes.append(code)
    if hud_fixed_cells + len(icon_codes) > sprite_cell_limit:
        raise ValueError("item icons exceed the sprite cells remaining after FRONTEND_FULL")
    icon_cell = {code: hud_fixed_cells + index for index, code in enumerate(icon_codes)}

    icon_patterns = bytearray()
    for code in icon_codes:
        raw = pc090[code * 128:code * 128 + 128]
        if len(raw) != 128:
            raise ValueError(f"missing PC090OJ icon 0x{code:04X}")
        base_slot = sprite_tile_base + icon_cell[code] * 4
        for quadrant in range(4):
            icon_patterns += (base_slot + quadrant).to_bytes(2, "big")
            icon_patterns += raw[quadrant * 32:(quadrant + 1) * 32]
    icon_patterns += b"\xFF\xFF"

    # Native icon records: base arcade Y, final Genesis SAT tile word, final X,
    # and source code for independent provenance/debug verification.
    def native_icons(records):
        result = []
        for attr, y, code, x in records:
            line = 0  # scene-0 palette LUT maps effective banks 0 and 3 to line 0
            flips = ((attr >> 3) & 0x1800)
            tile_word = 0x8000 | (line << 13) | flips | (sprite_tile_base + icon_cell[code] * 4)
            result.append((y, tile_word, x, code))
        return result

    native_a = native_icons(icons_a)
    native_b = native_icons(icons_b)
    icon_records = bytearray()
    for record in native_a + native_b:
        icon_records += words(record)

    outputs = {
        "logical_map": words(logical_words),
        "plane_patterns": bytes(plane_patterns),
        "icon_patterns": bytes(icon_patterns),
        "icon_records": bytes(icon_records),
    }
    report = {
        "format": "rastan-native-item-description-ring-v1",
        "semantic_cut": "arcade item attract state/scroll/dwell -> native Plane-B ring and native icon SAT",
        "arcade_sources": {
            "page_a_text": f"0x{PAGE_A_SOURCE:06X}",
            "page_b_text": f"0x{PAGE_B_SOURCE:06X}",
            "page_a_icons": f"0x{PAGE_A_ICONS:06X}",
            "page_b_icons": f"0x{PAGE_B_ICONS:06X}",
        },
        "geometry": {
            "logical_rows": LOGICAL_ROWS,
            "columns": PLANE_COLUMNS,
            "physical_rows": PHYSICAL_ROWS,
            "initial_top_row": INITIAL_TOP_ROW,
            "mapping": "physical_row = logical_row & 31",
            "page_b_install_pixel": PAGE_B_INSTALL_PIXEL,
        },
        "text": {
            "page_a_rows": len(page_a), "page_b_rows": len(page_b),
            "unique_patterns": len(plane_entries),
            "pattern_slots": [1, len(plane_entries)] if plane_entries else [],
            "source_to_slot": {f"0x{k:04X}": v for k, v in sorted(source_to_slot.items())},
        },
        "icons": {
            "page_a_records": len(native_a), "page_b_records": len(native_b),
            "unique_cells": len(icon_codes),
            "resident_cells": [hud_fixed_cells, hud_fixed_cells + len(icon_codes) - 1],
            "pattern_slots": [sprite_tile_base + hud_fixed_cells * 4,
                              sprite_tile_base + (hud_fixed_cells + len(icon_codes)) * 4 - 1],
            "source_codes": [f"0x{code:04X}" for code in icon_codes],
        },
        "vram_ownership": {
            "source": "current pc090oj_hooks.s constants + native_hud_report.json",
            "sprite_tile_base": sprite_tile_base,
            "native_cells": sprite_cell_limit,
            "frontend_hud_fixed_cells": hud_fixed_cells,
            "plane_pattern_limit_exclusive": sprite_tile_base,
            "physical_pattern_limit_exclusive": 1536,
        },
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()},
    }
    return outputs, report


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("maincpu", "pc080sn", "pc090oj", "hud-report", "sprite-source",
                 "map-output", "plane-pattern-output", "icon-pattern-output",
                 "icon-record-output", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    outputs, report = build(args.maincpu.read_bytes(), args.pc080sn.read_bytes(),
                            args.pc090oj.read_bytes(), json.loads(args.hud_report.read_text()),
                            args.sprite_source.read_text())
    paths = {
        args.map_output: outputs["logical_map"],
        args.plane_pattern_output: outputs["plane_patterns"],
        args.icon_pattern_output: outputs["icon_patterns"],
        args.icon_record_output: outputs["icon_records"],
    }
    for path, data in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
