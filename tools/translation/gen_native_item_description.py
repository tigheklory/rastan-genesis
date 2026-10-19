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
CELL_BYTES = 4
TILE_PIXELS = 8
CWINDOW_ROW_BYTES = PLANE_COLUMNS * CELL_BYTES
WRITER_PC = 0x0563A6
PAGE_A_PC = 0x05602C
PAGE_B_PC = 0x056056
SCROLL_PC = 0x05607C
ROW_ADVANCE_PC = 0x0560DA
ITEM_SCENE = 0
ITEM_SPRITE_COLBANK = 0x30  # arcade sprite control 0x0060 -> (ctrl & 0xe0) >> 1


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def words(values) -> bytes:
    return b"".join((value & 0xFFFF).to_bytes(2, "big") for value in values)


def decode_aliases(main: bytes) -> dict[int, int]:
    """Decode the compare/immediate substitution chain at arcade 0x563CE."""
    result: dict[int, int] = {}
    cursor = 0x0563CE
    while cursor < 0x056440:
        if u16(main, cursor) == 0x0C40 and u16(main, cursor + 6) == 0x303C:
            result[u16(main, cursor + 2)] = u16(main, cursor + 8)
            cursor += 10
        else:
            cursor += 2
    if not result:
        raise ValueError("could not decode item text alias chain")
    return result


def decode_text_stream(main: bytes, source: int, aliases: dict[int, int]) -> list[list[tuple[int, int]]]:
    """Return (source byte address, translated tile code) records per stream row."""
    rows: list[list[tuple[int, int]]] = [[]]
    cursor = source
    while True:
        value = main[cursor]
        cursor += 1
        if value == 0:
            return rows
        if value == 0xFF:
            rows.append([])
        else:
            rows[-1].append((cursor - 1, aliases.get(value, value)))


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


def parse_palette_lut(source: str) -> list[int]:
    values: list[int] = []
    active = False
    for raw in source.splitlines():
        line = raw.strip()
        if line == "pc090oj_palsel_lut:":
            active = True
            continue
        if not active:
            continue
        if line.startswith(".byte"):
            values.extend(int(token.strip(), 0) for token in line[5:].split(","))
        elif values and line.startswith(".section"):
            break
    if len(values) != 4 * 128 or any(not 0 <= value <= 3 for value in values):
        raise ValueError("current PC090OJ palette LUT is not a 4x128 line map")
    return values


def cwindow_row_col(destination: int) -> tuple[int, int]:
    offset = destination & 0x3FFF
    return offset // CWINDOW_ROW_BYTES, (offset % CWINDOW_ROW_BYTES) // CELL_BYTES


def decode_page_call(main: bytes, pc: int) -> dict[str, int]:
    if u16(main, pc) != 0x207C or u16(main, pc + 6) != 0x227C or u16(main, pc + 12) != 0x323C:
        raise ValueError(f"unexpected item-page loader at 0x{pc:06X}")
    if u16(main, pc + 20) != 0x207C or u16(main, pc + 26) != 0x227C:
        raise ValueError(f"unexpected item icon loader at 0x{pc:06X}")
    return {"text_source": u32(main, pc + 2), "destination": u32(main, pc + 8),
            "attribute": u16(main, pc + 14), "icon_source": u32(main, pc + 22),
            "icon_destination": u32(main, pc + 28)}


def arcade_reference(main: bytes):
    """Execute the ROM-authored item writers on the proven PC080SN 64x64 surface."""
    aliases = decode_aliases(main)
    page_a, page_b = decode_page_call(main, PAGE_A_PC), decode_page_call(main, PAGE_B_PC)
    if u16(main, WRITER_PC + 0x1C) != 0xD5FC:
        raise ValueError("item writer delimiter opcode changed")
    delimiter_bytes = u32(main, WRITER_PC + 0x1E)
    if delimiter_bytes % CWINDOW_ROW_BYTES:
        raise ValueError("item writer delimiter is not an integral PC080SN row count")
    delimiter_rows = delimiter_bytes // CWINDOW_ROW_BYTES
    if u16(main, SCROLL_PC + 0x1C) != 0x0241 or u16(main, SCROLL_PC + 0x1E) != 0x01FF:
        raise ValueError("item scroll modulo immediate changed")
    scroll_modulus = u16(main, SCROLL_PC + 0x1E) + 1
    if scroll_modulus != LOGICAL_ROWS * TILE_PIXELS:
        raise ValueError("arcade item surface is not independently 512 pixels")
    cursor_start = u32(main, 0x055E56)
    trigger = u32(main, ROW_ADVANCE_PC + 6)
    cursor_step = u32(main, ROW_ADVANCE_PC + 0x26)
    page_b_install_pixel = (((trigger - cursor_start) // cursor_step) + 1) * TILE_PIXELS

    initial = [[0x20] * PLANE_COLUMNS for _ in range(LOGICAL_ROWS)]
    final = [row[:] for row in initial]
    ledger = []

    def publish(page_name: str, desc: dict[str, int], surface, unwrapped_base: int):
        first_row, first_col = cwindow_row_col(desc["destination"])
        decoded = decode_text_stream(main, desc["text_source"], aliases)
        for stream_row, values in enumerate(decoded):
            physical_row = (first_row + stream_row * delimiter_rows) & (LOGICAL_ROWS - 1)
            world_row = unwrapped_base + stream_row * delimiter_rows
            for column_delta, (source_address, code) in enumerate(values):
                col = first_col + column_delta
                if col >= PLANE_COLUMNS:
                    raise ValueError("item text write crosses a PC080SN row")
                surface[physical_row][col] = code
                ledger.append({"page": page_name, "source_address": f"0x{source_address:06X}",
                               "source_byte": main[source_address], "tile_code": f"0x{code:04X}",
                               "destination": f"0x{(desc['destination'] + stream_row * delimiter_bytes + column_delta * CELL_BYTES):08X}",
                               "hardware_row": physical_row, "hardware_column": col,
                               "world_row": world_row, "world_column": col,
                               "semantic_visible_x": col * TILE_PIXELS - 16,
                               "semantic_visible_y_at_page_origin": world_row * TILE_PIXELS - 8,
                               "attribute": f"0x{desc['attribute']:04X}"})
        return decoded, first_row, first_col

    decoded_a, a_row, a_col = publish("A", page_a, initial, cwindow_row_col(page_a["destination"])[0])
    final = [row[:] for row in initial]
    b_physical, b_col = cwindow_row_col(page_b["destination"])
    a_last_world = a_row + (len(decoded_a) - 1) * delimiter_rows
    b_world = b_physical
    while b_world <= a_last_world:
        b_world += LOGICAL_ROWS
    decoded_b, _b_row, _ = publish("B", page_b, final, b_world)
    reference = {
        "format": "rastan-arcade-item-description-reference-v1",
        "hardware_proof": {"tilemap": "PC080SN 64x64 TILEMAP_SCAN_ROWS", "tile_pixels": 8,
                           "cell_bytes": CELL_BYTES, "row_bytes": CWINDOW_ROW_BYTES,
                           "circular_height_pixels": scroll_modulus, "x_display_offset": -16,
                           "visible_raster_top": 8},
        "decoded_immediates": {"page_a": page_a, "page_b": page_b,
                               "delimiter_bytes": delimiter_bytes, "delimiter_rows": delimiter_rows,
                               "cursor_start": cursor_start, "page_b_trigger": trigger,
                               "cursor_step": cursor_step, "page_b_install_pixel": page_b_install_pixel},
        "pages": {"A": {"stream_rows": len(decoded_a), "hardware_row": a_row, "column": a_col},
                  "B": {"stream_rows": len(decoded_b), "hardware_row": b_physical,
                        "world_row": b_world, "column": b_col}},
        "write_count": len(ledger), "write_ledger": ledger,
    }
    return initial, final, page_a, page_b, reference


def build(main: bytes, pc080: bytes, pc090: bytes, hud_report: dict,
          sprite_source: str, palette_lut_source: str):
    sprite_tile_base = assembly_constant(sprite_source, "SPRITE_TILE_BASE")
    sprite_cell_limit = assembly_constant(sprite_source, "NATIVE_CELLS")
    hud_fixed_cells = hud_report["fixed_residency_cells"]
    hud_slots = sorted(hud_report["sprite_slots"].values())
    expected_hud_slots = list(range(sprite_tile_base, sprite_tile_base + hud_fixed_cells * 4, 4))
    if hud_slots != expected_hud_slots:
        raise ValueError("current FRONTEND_FULL report is not a contiguous fixed-cell owner")
    palette_lut = parse_palette_lut(palette_lut_source)
    initial_codes, source_codes, page_a_desc, page_b_desc, reference = arcade_reference(main)

    pattern_by_bytes: dict[bytes, int] = {}
    plane_entries: list[tuple[int, int, bytes]] = []
    next_slot = 1
    source_to_slot: dict[int, int] = {0x20: 0}
    for row in source_codes + initial_codes[:PHYSICAL_ROWS]:
        for code in row:
            if code == 0x20:
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

    logical_words = [0 if code == 0x20 else source_to_slot[code]
                     for row in source_codes for code in row]

    initial_words = []
    for row in initial_codes[:PHYSICAL_ROWS]:
        for code in row:
            initial_words.append(0 if code == 0x20 else source_to_slot[code])

    plane_patterns = bytearray()
    for slot, _code, raw in plane_entries:
        plane_patterns += slot.to_bytes(2, "big") + raw
    plane_patterns += b"\xFF\xFF"

    icons_a = decode_icons(main, page_a_desc["icon_source"])
    icons_b = decode_icons(main, page_b_desc["icon_source"])
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
            effective_bank = ITEM_SPRITE_COLBANK | (attr & 0x000F)
            line = palette_lut[ITEM_SCENE * 128 + effective_bank]
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
        "initial_rows": words(initial_words),
        "plane_patterns": bytes(plane_patterns),
        "icon_patterns": bytes(icon_patterns),
        "icon_records": bytes(icon_records),
    }
    report = {
        "format": "rastan-native-item-description-ring-v3",
        "semantic_cut": "arcade item attract state/scroll/dwell -> native Plane-B ring and native icon SAT",
        "arcade_sources": {
            "page_a_text": f"0x{page_a_desc['text_source']:06X}",
            "page_b_text": f"0x{page_b_desc['text_source']:06X}",
            "page_a_icons": f"0x{page_a_desc['icon_source']:06X}",
            "page_b_icons": f"0x{page_b_desc['icon_source']:06X}",
        },
        "geometry": {
            "logical_rows": LOGICAL_ROWS,
            "columns": PLANE_COLUMNS,
            "physical_rows": PHYSICAL_ROWS,
            "initial_top_row": 0,
            "mapping": "physical_row = logical_row & 31",
            "page_b_install_pixel": reference["decoded_immediates"]["page_b_install_pixel"],
            "page_a_destination": f"0x{page_a_desc['destination']:08X}",
            "page_a_logical_row": reference["pages"]["A"]["hardware_row"],
            "page_a_column": reference["pages"]["A"]["column"],
            "page_b_destination": f"0x{page_b_desc['destination']:08X}",
            "page_b_physical_row": reference["pages"]["B"]["hardware_row"],
            "page_b_logical_row": reference["pages"]["B"]["world_row"],
            "page_b_column": reference["pages"]["B"]["column"],
            "stream_row_stride": reference["decoded_immediates"]["delimiter_rows"],
        },
        "text": {
            "page_a_rows": reference["pages"]["A"]["stream_rows"],
            "page_b_rows": reference["pages"]["B"]["stream_rows"],
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
            "arcade_sprite_control": "0x0060",
            "effective_colbank": "0x30",
            "palette_lines_by_attribute": {
                f"0x{attr:04X}": palette_lut[ITEM_SCENE * 128 +
                                               (ITEM_SPRITE_COLBANK | (attr & 0xF))]
                for attr in sorted({record[0] for record in icons_a + icons_b})
            },
            "palette_authority": "generated pc090oj_palsel_lut scene 0",
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
                 "palette-lut",
                 "map-output", "initial-rows-output", "plane-pattern-output", "icon-pattern-output",
                 "icon-record-output", "reference-output", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    outputs, report = build(args.maincpu.read_bytes(), args.pc080sn.read_bytes(),
                            args.pc090oj.read_bytes(), json.loads(args.hud_report.read_text()),
                            args.sprite_source.read_text(), args.palette_lut.read_text())
    paths = {
        args.map_output: outputs["logical_map"],
        args.initial_rows_output: outputs["initial_rows"],
        args.plane_pattern_output: outputs["plane_patterns"],
        args.icon_pattern_output: outputs["icon_patterns"],
        args.icon_record_output: outputs["icon_records"],
    }
    for path, data in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    _initial, _final, _a, _b, reference = arcade_reference(args.maincpu.read_bytes())
    args.reference_output.write_text(json.dumps(reference, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
