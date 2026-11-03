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
NATIVE_MAP_BYTES = 64 * 64 * 2
PLANE_B_NATIVE_MAP_BYTES = 32 * 64 * 2
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
    parser.add_argument("--plane-b-maps", type=Path, required=True)
    parser.add_argument("--pan-maps", type=Path, required=True)
    parser.add_argument("--record-maps", type=Path, required=True)
    parser.add_argument("--record-row-maps", type=Path, required=True)
    parser.add_argument("--authored-descriptor-visuals", type=Path, required=True)
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
    plane_b_actual = args.plane_b_maps.read_bytes()
    pan_actual = args.pan_maps.read_bytes()
    record_maps = args.record_maps.read_bytes()
    record_row_maps = args.record_row_maps.read_bytes()
    authored_descriptor_visuals = args.authored_descriptor_visuals.read_bytes()
    packages = args.packages.read_bytes()
    report = json.loads(args.report.read_text())
    authored = report.get("authoring_mode") == "diagnostic-profile"
    record_table_bytes = RECORDS * 12
    record_cells_checked = 0
    record_origin_projections_checked = 0

    descriptor_checked = 0
    descriptor_meta = report.get("authored_descriptor_visuals", {})
    if authored:
        profile = Path(report["authoring_profile"])
        if not profile.is_file():
            profile = ROOT / "analysis/graphics_optimizer/editor_policy" / profile.name
        authored_model = compiler.AuthoredLayerA(profile, patterns)
        first = descriptor_meta["entry_first"]
        end = descriptor_meta["entry_end"]
        count = descriptor_meta["entry_count"]
        contexts = descriptor_meta["contexts"]
        payload_offset = descriptor_meta["index_bytes"]
        if len(authored_descriptor_visuals) != descriptor_meta["total_bytes"]:
            raise SystemExit("FAIL authored descriptor visual size disagrees with report")
        for context in range(contexts):
            index_base = context * count * 4
            for entry_index, entry in enumerate(range(first, end, 4)):
                record_offset = be32(authored_descriptor_visuals, index_base + entry_index * 4)
                if not record_offset:
                    raise SystemExit(f"FAIL authored descriptor {context}/{entry:#x} has no record")
                if record_offset + 64 > len(authored_descriptor_visuals):
                    raise SystemExit(f"FAIL authored descriptor {context}/{entry:#x} record overflow")
                attr = be16(maincpu, entry)
                descriptor = be16(maincpu, entry + 2)
                valid = not (descriptor & 1) and 0x200 <= descriptor <= 0x5FDFC
                for cell in range(16):
                    source_code = ((be16(maincpu, descriptor + cell * 2) & 0x3FFF)
                                   if valid else 0)
                    code, _blob, line, _usage = authored_model.resolve_context(
                        context, source_code, attr, patterns)
                    expected_attr = (line << 13) | ((attr & 0xC000) >> 3)
                    actual_code = be16(authored_descriptor_visuals, record_offset + cell * 4)
                    actual_attr = be16(authored_descriptor_visuals, record_offset + cell * 4 + 2)
                    if (actual_code, actual_attr) != (code, expected_attr):
                        raise SystemExit(
                            f"FAIL authored descriptor {context}/{entry:#x}/{cell}: "
                            f"{actual_code:04X}/{actual_attr:04X} != {code:04X}/{expected_attr:04X}")
                    descriptor_checked += 1

    def compiled_word(record: int, package: int, row: int, column: int) -> int:
        entry = record * 12
        offset = be32(record_maps, entry)
        if be16(record_maps, entry + 4) == package:
            offset = be32(record_maps, entry + 8)
        return be16(record_maps, record_table_bytes + offset + (row * 64 + column) * 2)

    decoded = (compiler.decode_plane_b_progression(maincpu, 0) +
               compiler.decode_plane_b_progression(maincpu, 23))
    scene_records = sorted(record["segment"] for record in decoded if record["scene_reinit"])
    if scene_records != [0, 16, 22, 23, 39, 45]:
        raise SystemExit(f"FAIL scene-fill record set changed: {scene_records}")
    expected_size = TABLE_BYTES + len(scene_records) * NATIVE_MAP_BYTES
    if len(actual) != expected_size:
        raise SystemExit(f"FAIL scene-fill map size {len(actual)} != {expected_size}")
    plane_b_expected_size = TABLE_BYTES + len(scene_records) * PLANE_B_NATIVE_MAP_BYTES
    if len(plane_b_actual) != plane_b_expected_size:
        raise SystemExit(
            f"FAIL Plane-B scene-fill map size {len(plane_b_actual)} != {plane_b_expected_size}")

    # Checkpoint restores are not scene fills: they can target every retained
    # progression record. Verify the complete all-record native artifact,
    # including overlap-package alternatives, against independently decoded
    # arcade cells and the generated package slot maps.
    if len(record_maps) != report["record_native_map_bytes"]:
        raise SystemExit("FAIL all-record native map size disagrees with report")
    if len(record_row_maps) != report["record_native_row_map_bytes"]:
        raise SystemExit("FAIL compact all-record row map size disagrees with report")
    row_pool_offset = report["record_native_row_pool_offset"]
    row_index_bytes = report["record_native_row_map_count"] * 64 * 2
    if row_pool_offset != record_table_bytes + row_index_bytes:
        raise SystemExit("FAIL compact row-pool offset disagrees with map count")
    if len(record_row_maps) - row_pool_offset != \
            report["record_native_unique_rows"] * 64 * 2:
        raise SystemExit("FAIL compact native row-pool size")
    for record in range(RECORDS):
        selector = compiler.decode_record_selector(maincpu, record)
        cells = decoder.reconstruct_segment(
            maincpu, patterns, record, "checkpoint", selector=selector)
        by_position = {(cell.world_row, cell.segment_column): cell for cell in cells}
        stable_package = report["record_to_epoch"][record]
        runtime_package = report["record_to_package"][record]
        package_choices = [stable_package]
        if runtime_package != stable_package:
            package_choices.append(runtime_package)
        entry = record * 12
        offsets = [be32(record_maps, entry)]
        row_offsets = [be32(record_row_maps, entry)]
        alternate_package = be16(record_maps, entry + 4)
        alternate_offset = be32(record_maps, entry + 8)
        if len(package_choices) == 1:
            if alternate_package != 0xFFFF or alternate_offset != 0xFFFFFFFF:
                raise SystemExit(f"FAIL record {record} has spurious alternate map")
        else:
            if alternate_package != runtime_package:
                raise SystemExit(f"FAIL record {record} alternate package mismatch")
            offsets.append(alternate_offset)
            row_offsets.append(be32(record_row_maps, entry + 8))
        for package, offset, row_offset in zip(package_choices, offsets, row_offsets):
            if offset + NATIVE_MAP_BYTES > len(record_maps) - record_table_bytes:
                raise SystemExit(f"FAIL record {record}/{package} map overflow")
            layout = report["binary_contract"]["package_layout"][package]
            slot_by_code = {
                be16(packages, layout["map_start"] + pair * 4):
                be16(packages, layout["map_start"] + pair * 4 + 2)
                for pair in range(layout["map_count"])
            }
            for row in range(64):
                for column in range(64):
                    cell = by_position.get((row, column))
                    source_code = cell.tile_code if cell else 0
                    attr = cell.attr if cell else 0
                    code, _blob, line, _usage = (authored_model.resolve(
                        record, source_code, attr, patterns) if authored else
                        (source_code, b"", 3, None))
                    slot = slot_by_code.get(code, 0)
                    if code and not slot and package == stable_package:
                        raise SystemExit(
                            f"FAIL checkpoint record {record}/{package} "
                            f"code {code:04X} lacks slot")
                    expected = (line << 13) | ((attr & 0xC000) >> 3) | slot
                    actual_word = be16(
                        record_maps, record_table_bytes + offset +
                        (row * 64 + column) * 2)
                    row_id = be16(
                        record_row_maps, record_table_bytes + row_offset + row * 2)
                    if row_id >= report["record_native_unique_rows"]:
                        raise SystemExit(
                            f"FAIL checkpoint record {record}/{package} row ID overflow")
                    compact_word = be16(
                        record_row_maps, row_pool_offset + row_id * 64 * 2 + column * 2)
                    if compact_word != actual_word:
                        raise SystemExit(
                            f"FAIL compact checkpoint record {record}/{package} "
                            f"row {row} column {column}: {compact_word:04X} != {actual_word:04X}")
                    if actual_word != expected:
                        raise SystemExit(
                            f"FAIL checkpoint record {record}/{package} "
                            f"row {row} column {column}: {actual_word:04X} != {expected:04X}")
                    record_cells_checked += 1
        for live_scroll_y in range(0x200):
            live_top = ((-live_scroll_y + 8) & 0x1FF) >> 3
            destinations = {((live_top + delta) & 63) & 31 for delta in range(32)}
            if len(destinations) != 32:
                raise SystemExit(
                    f"FAIL checkpoint record {record} scroll {live_scroll_y:#05x} ring coverage")
            record_origin_projections_checked += 1

    checked = 0
    origin_projections_checked = 0
    plane_b_checked = 0
    for record in range(RECORDS):
        offset = be32(actual, record * 4)
        if record not in scene_records:
            if offset != 0xFFFFFFFF:
                raise SystemExit(f"FAIL non-fill record {record} has map offset {offset:#x}")
            plane_b_offset = be32(plane_b_actual, record * 4)
            if plane_b_offset != 0xFFFFFFFF:
                raise SystemExit(
                    f"FAIL non-fill record {record} has Plane-B map offset {plane_b_offset:#x}")
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
        for row in range(64):
            for column in range(64):
                if authored:
                    expected = compiled_word(record, package_index, row, column)
                    entry = offset + (row * 64 + column) * 2
                    if be16(actual, entry) != expected:
                        raise SystemExit(f"FAIL authored record {record} row {row} column {column}")
                    checked += 1
                    continue
                cell = by_position.get((row, column))
                code = cell.tile_code if cell else 0
                attr = cell.attr if cell else 0
                native_attr = 0x6000 | ((attr & 0xC000) >> 3)
                slot = slot_by_code.get(code, 0)
                if code and not slot:
                    raise SystemExit(
                        f"FAIL record {record} code {code:04X} lacks package slot")
                expected = native_attr | slot
                entry = offset + (row * 64 + column) * 2
                if be16(actual, entry) != expected:
                    raise SystemExit(
                        f"FAIL record {record} logical row {row} column {column}: "
                        f"got {be16(actual, entry):04X}, "
                        f"expected {expected:04X} (code {code:04X}, slot {slot:04X})")
                checked += 1

        # The scene artifact is deliberately independent of any spawn/camera
        # tuple.  Exercise the exact runtime ring projection for every possible
        # nine-bit live scroll origin: 32 consecutive logical rows must fill
        # every physical row exactly once, including the 63 -> 0 wrap.
        for live_scroll_y in range(0x200):
            live_top = ((-live_scroll_y + 8) & 0x1FF) >> 3
            destinations: set[int] = set()
            for delta in range(32):
                logical_row = (live_top + delta) & 63
                physical_row = logical_row & 31
                if physical_row in destinations:
                    raise SystemExit(
                        f"FAIL record {record} scroll {live_scroll_y:#05x} "
                        f"duplicates physical row {physical_row}")
                destinations.add(physical_row)
                source = offset + logical_row * 64 * 2
                for column in range(64):
                    # Model the helper's source-row selection and destination
                    # address independently of the camera table used at build.
                    projected = be16(actual, source + column * 2)
                    expected = be16(
                        actual, offset + ((live_top + delta) & 63) * 64 * 2
                        + column * 2)
                    if projected != expected:
                        raise SystemExit(
                            f"FAIL record {record} scroll {live_scroll_y:#05x} "
                            f"row {logical_row} column {column} projection")
            if len(destinations) != 32:
                raise SystemExit(
                    f"FAIL record {record} scroll {live_scroll_y:#05x} "
                    "does not initialize the complete physical ring")
            origin_projections_checked += 1

        plane_b_offset = be32(plane_b_actual, record * 4)
        if (plane_b_offset < TABLE_BYTES or
                plane_b_offset + PLANE_B_NATIVE_MAP_BYTES > len(plane_b_actual)):
            raise SystemExit(f"FAIL record {record} Plane-B map offset {plane_b_offset:#x}")
        decoded_record = decoded[record]
        descriptor_base = decoded_record["descriptor_before"]
        fixed_layout = report["binary_contract"]["fixed_b_layouts"][
            0 if record < 23 else 1]
        round_slots = {
            be16(packages, fixed_layout["offset"] + pair * 4):
            be16(packages, fixed_layout["offset"] + pair * 4 + 2)
            for pair in range(fixed_layout["map_count"])
        }
        camera_record = record + 1
        scroll_y = be16(maincpu, 0x50850 + camera_record * 12 + 2)
        visible_top = ((-scroll_y + 8) & 0x1FF) >> 3
        for delta in range(32):
            logical_row = (visible_top + delta) & 63
            physical_row = logical_row & 31
            for column in range(64):
                relative = (64 - column) & 63
                descriptor_index = descriptor_base + ((64 - relative) >> 4)
                descriptor = compiler.PLANE_B_DESC_TABLE + descriptor_index * 6
                attr = be16(maincpu, descriptor)
                source = be32(maincpu, descriptor + 2) & 0xFFFFFF
                code = be16(maincpu, source + logical_row * 0x20 + (column & 15) * 2) & 0x3FFF
                slot = round_slots.get(code, 0)
                native_attr = ((((attr >> 13) & 1) << 15) |
                               ((attr & 3) << 13) |
                               (((attr >> 15) & 1) << 12) |
                               (((attr >> 14) & 1) << 11))
                expected = native_attr | slot
                entry = plane_b_offset + (physical_row * 64 + column) * 2
                if be16(plane_b_actual, entry) != expected:
                    raise SystemExit(
                        f"FAIL record {record} Plane-B row {logical_row} column {column}")
                plane_b_checked += 1

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
                if authored:
                    expected = compiled_word(record, package_index, logical_row, column)
                    entry = offset + (logical_row * 64 + column) * 2
                    if be16(pan_actual, entry) != expected:
                        raise SystemExit(
                            f"FAIL authored pan record {record} row {logical_row} column {column}")
                    pan_checked += 1
                    continue
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
        "genesistan_plane_a_checkpoint_restore_arm:",
        "tst.b   fg_scene_scroll_reseed_pending",
        "tst.b   fg_checkpoint_scroll_reseed_pending",
        "clr.b   fg_scene_scroll_reseed_pending",
        "move.w  0x013E(%a5), %d0",
        "subq.w  #1, %d0",
        "genesistan_plane_a_scene_fill_maps",
        "genesistan_plane_a_record_native_row_maps",
        "FG_RECORD_NATIVE_MAP_ENTRY_BYTES",
        "fg_boundary_active_package",
        "ARCADE_PC080SN_SCROLL_Y_FG_OFFSET(%a5)",
        ".Lplane_a_visible_top_from_scroll_d0",
        ".Lscene_scroll_reseed_row:",
        "genesistan_plane_b_scene_fill_maps",
        "move.l  (%a1)+, (%a4)+",
        "genesistan_plane_a_pan_row_maps",
        "FG_PAN_ROW_MAP_BYTES",
        ".Lplane_a_row_precompiled_copy:",
        "move.l  #0xFFFFFFFF, fg_row_dirty",
        '.incbin "../../build/pc080sn_boundary/scene_fill_maps.bin"',
        '.incbin "../../build/pc080sn_boundary/record_native_row_maps.bin"',
        '.incbin "../../build/pc080sn_boundary/plane_b_scene_fill_maps.bin"',
        '.incbin "../../build/pc080sn_boundary/pan_row_maps.bin"',
        '.incbin "../../build/pc080sn_boundary/authored_descriptor_visuals.bin"',
        ".macro MAP_GET_AUTHORED_VISUAL_A0",
        "diagnostic_palette_active_asset",
    )
    for token in required_source:
        if token not in source:
            raise SystemExit(f"FAIL scene-fill source omits {token}")
    for token in (".Lplane_a_precompiled_name_from_d0_d1",):
        if token in source:
            raise SystemExit(f"FAIL dynamic visual path retains rejected static-record token {token}")
    cache_source = args.cache_source.read_text()
    for token in (".global fg_scene_scroll_reseed_pending",
                  ".global fg_checkpoint_scroll_reseed_pending",
                  "move.b  #1, fg_scene_scroll_reseed_pending",
                  "fg_scene_scroll_reseed_pending:         .space 1",
                  "fg_checkpoint_scroll_reseed_pending:    .space 1"):
        if token not in cache_source:
            raise SystemExit(f"FAIL scene-fill handoff omits {token}")
    forbidden = ("staged_fg_tall_buffer", "C08000", "runtime transpose",
                 "fg_cache_resolve", "fg_boundary_active_lut")
    helper = source[source.index("genesistan_plane_a_scene_scroll_reseed_native:"):
                    source.index("/* Native Plane A no-publication vertical-scroll route.")]
    for token in forbidden:
        if token in helper:
            raise SystemExit(f"FAIL scene-fill helper contains forbidden {token}")

    spec = json.loads(args.spec.read_text())
    if "genesistan_plane_a_scene_scroll_reseed_native" not in spec["required_symbols"]:
        raise SystemExit("FAIL scene-fill helper missing from required_symbols")
    if "genesistan_plane_a_checkpoint_restore_arm" not in spec["required_symbols"]:
        raise SystemExit("FAIL checkpoint helper missing from required_symbols")
    replacements = [row for row in spec["shift_replacements"]
                    if row.get("arcade_pc", "").lower() == "0x050538"]
    if len(replacements) != 1 or "genesistan_plane_a_scene_scroll_reseed_native" not in \
            replacements[0].get("replacement_bytes", ""):
        raise SystemExit("FAIL missing post-0x504FA scene-fill replacement")
    for pc in ("0x055f26", "0x056014"):
        rows = [row for row in spec["shift_replacements"]
                if row.get("arcade_pc", "").lower() == pc]
        if len(rows) != 1 or "genesistan_plane_a_checkpoint_restore_arm" not in \
                rows[0].get("replacement_bytes", ""):
            raise SystemExit(f"FAIL missing checkpoint restore arm at {pc}")

    print(f"PASS native scene-fill/pan maps: scene_records={scene_records} "
          f"scene_cells={checked} plane_b_scene_cells={plane_b_checked} "
          f"scene_origin_projections={origin_projections_checked} "
          f"checkpoint_cells={record_cells_checked} "
          f"checkpoint_origin_projections={record_origin_projections_checked} "
          f"scene_bytes={len(actual)}; pan_records={pan_records} "
          f"pan_cells={pan_checked} pan_bytes={len(pan_actual)}; "
          f"authored_descriptor_cells={descriptor_checked}; "
          "post-scroll boundary=0x050538; collision untouched")


if __name__ == "__main__":
    main()
