#!/usr/bin/env python3
"""Verify offline native scene-fill maps and the post-scroll runtime boundary."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECORDS = 46
TABLE_BYTES = RECORDS * 4
MAP_BYTES = 64 * 64 * 4
NATIVE_MAP_BYTES = 32 * 64 * 2
PAN_MAP_BYTES = 64 * 64 * 2


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--pc080sn", type=Path, required=True)
    parser.add_argument("--maps", type=Path, required=True)
    parser.add_argument("--pan-maps", type=Path, required=True)
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--cache-source", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()

    decoder = load_module(ROOT / "tools/audit_round1_phase1_plane_a.py", "scene_fill_decoder")
    compiler = load_module(ROOT / "tools/translation/compile_pc080sn_genesis.py",
                           "scene_fill_compiler")
    maincpu = args.maincpu.read_bytes()
    patterns = args.pc080sn.read_bytes()
    actual = args.maps.read_bytes()
    pan_actual = args.pan_maps.read_bytes()
    packages = args.packages.read_bytes()
    report = json.loads(args.report.read_text())

    decoded = (compiler.decode_plane_b_progression(maincpu, 0) +
               compiler.decode_plane_b_progression(maincpu, 23))
    scene_records = sorted(record["segment"] for record in decoded if record["scene_reinit"])
    if scene_records != [0, 16, 22, 23, 39, 45]:
        raise SystemExit(f"FAIL scene-fill record set changed: {scene_records}")
    expected_size = TABLE_BYTES + len(scene_records) * NATIVE_MAP_BYTES
    if len(actual) != expected_size:
        raise SystemExit(f"FAIL scene-fill map size {len(actual)} != {expected_size}")

    checked = 0
    for record in range(RECORDS):
        offset = be32(actual, record * 4)
        if record not in scene_records:
            if offset != 0xFFFFFFFF:
                raise SystemExit(f"FAIL non-fill record {record} has map offset {offset:#x}")
            continue
        if offset < TABLE_BYTES or offset + NATIVE_MAP_BYTES > len(actual):
            raise SystemExit(f"FAIL record {record} map offset {offset:#x}")
        selector = compiler.decode_record_selector(maincpu, record)
        cells = decoder.reconstruct_segment(maincpu, patterns, record, "scene-fill",
                                            selector=selector)
        by_position = {(cell.world_row, cell.segment_column): cell for cell in cells}
        package_index = report["record_to_package"][record]
        layout = report["binary_contract"]["package_layout"][package_index]
        map_start = layout["map_start"]
        map_count = layout["map_count"]
        slot_by_code = {
            be16(packages, map_start + pair * 4):
            be16(packages, map_start + pair * 4 + 2)
            for pair in range(map_count)
        }
        camera_record = record + 1
        scroll_y = be16(maincpu, 0x50850 + camera_record * 12 + 2)
        visible_top = ((-scroll_y + 8) & 0x1FF) >> 3
        for delta in range(32):
            row = (visible_top + delta) & 63
            physical_row = row & 31
            for column in range(64):
                cell = by_position.get((row, column))
                code = cell.tile_code if cell else 0
                attr = cell.attr if cell else 0
                native_attr = 0x6000 | ((attr & 0xC000) >> 3)
                slot = slot_by_code.get(code, 0)
                if code and not slot:
                    raise SystemExit(
                        f"FAIL record {record} code {code:04X} lacks package slot")
                expected = native_attr | slot
                entry = offset + (physical_row * 64 + column) * 2
                if be16(actual, entry) != expected:
                    raise SystemExit(
                        f"FAIL record {record} logical row {row} physical row "
                        f"{physical_row} column {column}: got {be16(actual, entry):04X}, "
                        f"expected {expected:04X} (code {code:04X}, slot {slot:04X})")
                checked += 1

    pan_records = [record for record in range(RECORDS)
                   if compiler.decode_record_selector(maincpu, record) in (1, 2)]
    if pan_records != [17, 21, 43, 44] or report.get("pan_row_records") != pan_records:
        raise SystemExit(f"FAIL selector pan-row record set changed: {pan_records}")
    pan_expected_size = TABLE_BYTES + len(pan_records) * PAN_MAP_BYTES
    if len(pan_actual) != pan_expected_size:
        raise SystemExit(f"FAIL pan-row map size {len(pan_actual)} != {pan_expected_size}")
    pan_checked = 0
    for record in range(RECORDS):
        offset = be32(pan_actual, record * 4)
        if record not in pan_records:
            if offset != 0xFFFFFFFF:
                raise SystemExit(f"FAIL non-vertical record {record} has pan map {offset:#x}")
            continue
        if offset < TABLE_BYTES or offset + PAN_MAP_BYTES > len(pan_actual):
            raise SystemExit(f"FAIL record {record} pan map offset {offset:#x}")
        cells = decoder.reconstruct_segment(
            maincpu, patterns, record, "pan-row",
            selector=compiler.decode_record_selector(maincpu, record))
        by_position = {(cell.world_row, cell.segment_column): cell for cell in cells}
        package_index = report["record_to_package"][record]
        layout = report["binary_contract"]["package_layout"][package_index]
        map_start = layout["map_start"]
        slot_by_code = {
            be16(packages, map_start + pair * 4):
            be16(packages, map_start + pair * 4 + 2)
            for pair in range(layout["map_count"])
        }
        for logical_row in range(64):
            for column in range(64):
                cell = by_position.get((logical_row, column))
                code = cell.tile_code if cell else 0
                attr = cell.attr if cell else 0
                slot = slot_by_code.get(code, 0)
                if code and not slot:
                    raise SystemExit(
                        f"FAIL record {record} pan code {code:04X} lacks package slot")
                expected = 0x6000 | ((attr & 0xC000) >> 3) | slot
                entry = offset + (logical_row * 64 + column) * 2
                if be16(pan_actual, entry) != expected:
                    raise SystemExit(
                        f"FAIL record {record} pan row {logical_row} column {column}: "
                        f"got {be16(pan_actual, entry):04X}, expected {expected:04X}")
                pan_checked += 1

    source = args.source.read_text()
    required_source = (
        "genesistan_plane_a_scene_scroll_reseed_native:",
        "tst.b   fg_scene_scroll_reseed_pending",
        "clr.b   fg_scene_scroll_reseed_pending",
        "move.w  0x013E(%a5), %d0",
        "subq.w  #1, %d0",
        "genesistan_plane_a_scene_fill_maps",
        "move.w  #1023, %d7",
        "move.l  (%a0)+, (%a6)+",
        "genesistan_plane_a_pan_row_maps",
        "FG_PAN_ROW_MAP_BYTES",
        ".Lplane_a_row_precompiled_copy:",
        "move.l  #0xFFFFFFFF, fg_row_dirty",
        '.incbin "../../build/pc080sn_boundary/scene_fill_maps.bin"',
        '.incbin "../../build/pc080sn_boundary/pan_row_maps.bin"',
    )
    for token in required_source:
        if token not in source:
            raise SystemExit(f"FAIL scene-fill source omits {token}")
    cache_source = args.cache_source.read_text()
    for token in (".global fg_scene_scroll_reseed_pending",
                  "move.b  #1, fg_scene_scroll_reseed_pending",
                  "fg_scene_scroll_reseed_pending:         .space 1"):
        if token not in cache_source:
            raise SystemExit(f"FAIL scene-fill handoff omits {token}")
    forbidden = ("staged_fg_tall_buffer", "C08000", "runtime transpose",
                 "fg_cache_resolve", "fg_boundary_active_lut",
                 "ARCADE_PC080SN_SCROLL_Y_FG_OFFSET")
    helper = source[source.index("genesistan_plane_a_scene_scroll_reseed_native:"):
                    source.index("/* Native Plane A no-publication vertical-scroll route.")]
    for token in forbidden:
        if token in helper:
            raise SystemExit(f"FAIL scene-fill helper contains forbidden {token}")

    spec = json.loads(args.spec.read_text())
    if "genesistan_plane_a_scene_scroll_reseed_native" not in spec["required_symbols"]:
        raise SystemExit("FAIL scene-fill helper missing from required_symbols")
    replacements = [row for row in spec["shift_replacements"]
                    if row.get("arcade_pc", "").lower() == "0x050538"]
    if len(replacements) != 1 or "genesistan_plane_a_scene_scroll_reseed_native" not in \
            replacements[0].get("replacement_bytes", ""):
        raise SystemExit("FAIL missing post-0x504FA scene-fill replacement")

    print(f"PASS native scene-fill/pan maps: scene_records={scene_records} "
          f"scene_cells={checked} scene_bytes={len(actual)}; pan_records={pan_records} "
          f"pan_cells={pan_checked} pan_bytes={len(pan_actual)}; "
          "post-scroll boundary=0x050538; collision untouched")


if __name__ == "__main__":
    main()
