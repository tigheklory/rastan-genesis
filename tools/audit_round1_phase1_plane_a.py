#!/usr/bin/env python3
"""Clean-room Round-1 Phase-1 PC080SN tilemap1 pattern audit.

This tool reconstructs the original arcade map directly from maincpu tables and
decodes the original PC080SN graphics region. It intentionally has no imports
from the Genesis translation/compiler pipeline.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PHASE_SEGMENTS = range(0, 16)
ALL_OFF_PHASE_SEGMENTS = range(16, 139)
SOURCE_TABLE_BASES = (
    0x1691C, 0x18BDC, 0x1AE9C, 0x1D15C,
    0x1F41C, 0x216DC, 0x2399C, 0x25C5C,
    0x27F1C, 0x2A1DC, 0x2C49C, 0x2E75C,
    0x30A1C, 0x32CDC, 0x34F9C, 0x3725C,
)
SEGMENT_STRIDE = 0x40
TILES_PER_SEGMENT = 64
ROWS_PER_SEGMENT = 64
VISIBLE_ROWS = range(1, 31)  # Rastan visarea y=8..247 at fixed Phase-1 Y scroll 0.

FAMILIES = (
    (range(0, 4), "outside_source_bank_0"),
    (range(4, 8), "outside_source_bank_1"),
    (range(8, 12), "outside_source_bank_2"),
    (range(12, 16), "outside_source_bank_3"),
)

BRIDGE_FIRST_COLUMN = 608
BRIDGE_LAST_COLUMN = 637


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def family_for_segment(segment: int) -> str:
    for segments, name in FAMILIES:
        if segment in segments:
            return name
    return "outside_phase1"


def tile_bytes(gfx: bytes, code: int) -> bytes:
    start = code * 32
    end = start + 32
    if end > len(gfx):
        raise ValueError(f"tile 0x{code:04X} exceeds graphics region")
    return gfx[start:end]


def flip_h(raw: bytes) -> bytes:
    rows = []
    for row in range(8):
        pixels = []
        for value in raw[row * 4:row * 4 + 4]:
            pixels.extend((value >> 4, value & 0x0F))
        pixels.reverse()
        rows.extend((pixels[x] << 4) | pixels[x + 1] for x in range(0, 8, 2))
    return bytes(rows)


def flip_v(raw: bytes) -> bytes:
    return b"".join(raw[row * 4:row * 4 + 4] for row in reversed(range(8)))


def normalized_hash(raw: bytes) -> str:
    variants = (raw, flip_h(raw), flip_v(raw), flip_v(flip_h(raw)))
    return min(sha256(value) for value in variants)


def pixels(raw: bytes) -> list[int]:
    out = []
    for value in raw:
        out.extend((value >> 4, value & 0x0F))
    return out


@dataclass(frozen=True)
class Cell:
    segment: int
    segment_column: int
    world_column: int
    world_row: int
    attr: int
    descriptor: int
    descriptor_offset: int
    tile_code: int
    source_address: int
    exact_hash: str
    normalized_hash: str
    category: str
    family: str


def reconstruct_segment(maincpu: bytes, gfx: bytes, segment: int, category: str) -> list[Cell]:
    result = []
    for world_row in range(ROWS_PER_SEGMENT):
        table_index, descriptor_row = divmod(world_row, 4)
        table_base = SOURCE_TABLE_BASES[table_index] + segment * SEGMENT_STRIDE
        for segment_column in range(TILES_PER_SEGMENT):
            descriptor_column, descriptor_subcolumn = divmod(segment_column, 4)
            entry = table_base + descriptor_column * 4
            attr = be16(maincpu, entry)
            descriptor = be16(maincpu, entry + 2)
            if descriptor == 0:
                continue
            descriptor_offset = descriptor + descriptor_row * 8 + descriptor_subcolumn * 2
            tile_word = be16(maincpu, descriptor_offset)
            code = tile_word & 0x3FFF
            raw = tile_bytes(gfx, code)
            result.append(Cell(
                segment=segment,
                segment_column=segment_column,
                world_column=segment * TILES_PER_SEGMENT + segment_column,
                world_row=world_row,
                attr=attr,
                descriptor=descriptor,
                descriptor_offset=descriptor_offset,
                tile_code=code,
                source_address=code * 32,
                exact_hash=sha256(raw),
                normalized_hash=normalized_hash(raw),
                category=category if world_row in VISIBLE_ROWS else "B",
                family=family_for_segment(segment),
            ))
    return result


def intervals(columns: list[int]) -> list[tuple[int, int]]:
    values = sorted(set(columns))
    if not values:
        return []
    out = []
    start = previous = values[0]
    for value in values[1:]:
        if value != previous + 1:
            out.append((start, previous))
            start = value
        previous = value
    out.append((start, previous))
    return out


def load_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def render_tile(raw: bytes, scale: int = 4) -> Image.Image:
    palette = (
        (0, 0, 0), (35, 35, 35), (70, 70, 70), (105, 105, 105),
        (140, 140, 140), (175, 175, 175), (210, 210, 210), (245, 245, 245),
        (64, 32, 0), (104, 56, 8), (144, 80, 16), (184, 112, 24),
        (24, 72, 112), (32, 112, 152), (48, 160, 184), (96, 216, 224),
    )
    image = Image.new("RGB", (8, 8))
    image.putdata([palette[value] for value in pixels(raw)])
    return image.resize((8 * scale, 8 * scale), Image.Resampling.NEAREST)


def make_atlas(path: Path, hashes: list[str], representative: dict[str, bytes], labels: dict[str, str]) -> None:
    columns = 16
    cell_w, cell_h = 64, 52
    rows = (len(hashes) + columns - 1) // columns
    image = Image.new("RGB", (columns * cell_w, max(1, rows) * cell_h), (24, 24, 24))
    draw = ImageDraw.Draw(image)
    font = load_font(9)
    for index, pattern_hash in enumerate(hashes):
        x = (index % columns) * cell_w
        y = (index // columns) * cell_h
        image.paste(render_tile(representative[pattern_hash]), (x + 16, y + 2))
        draw.text((x + 2, y + 35), labels[pattern_hash], fill=(240, 240, 240), font=font)
        draw.text((x + 2, y + 44), pattern_hash[:8], fill=(150, 200, 255), font=font)
    image.save(path)


def make_map_previews(out_dir: Path, cells: list[Cell], gfx: bytes) -> None:
    by_position = {(cell.world_column, cell.world_row): cell for cell in cells}
    palette = [
        (0, 0, 0), (42, 42, 42), (78, 78, 78), (114, 114, 114),
        (150, 150, 150), (186, 186, 186), (222, 222, 222), (255, 255, 255),
        (72, 36, 0), (112, 60, 8), (152, 84, 16), (192, 116, 24),
        (20, 76, 116), (28, 116, 156), (44, 164, 188), (92, 220, 228),
    ]
    for first_segment in range(0, 16, 4):
        first_col = first_segment * 64
        width = 4 * 64 * 8
        image = Image.new("RGB", (width, 64 * 8))
        rendered = {}
        for row in range(64):
            for column in range(first_col, first_col + 256):
                cell = by_position[(column, row)]
                cache_key = (cell.tile_code, cell.attr & 0xC000)
                tile = rendered.get(cache_key)
                if tile is None:
                    tile_pixels = pixels(tile_bytes(gfx, cell.tile_code))
                    rows = [tile_pixels[r * 8:r * 8 + 8] for r in range(8)]
                    if cell.attr & 0x4000:
                        rows = [values[::-1] for values in rows]
                    if cell.attr & 0x8000:
                        rows.reverse()
                    tile = Image.new("RGB", (8, 8))
                    tile.putdata([palette[p] for values in rows for p in values])
                    rendered[cache_key] = tile
                image.paste(tile, ((column - first_col) * 8, row * 8))
        image.save(out_dir / f"map_segments_{first_segment:02d}_{first_segment + 3:02d}.png")


def write_map_usage(path: Path, cells: list[Cell], usage_by_hash: dict[str, list[Cell]]) -> None:
    fieldnames = (
        "category", "record", "segment_column", "world_column", "world_x_start",
        "world_row", "arcade_tile_code", "source_address", "map_attr", "palette_index",
        "priority", "h_flip", "v_flip", "descriptor", "descriptor_offset",
        "exact_pattern_hash", "flip_normalized_hash", "first_use_column",
        "last_use_column", "use_intervals", "usage_family",
    )
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for cell in cells:
            uses = usage_by_hash[cell.exact_hash]
            columns = [use.world_column for use in uses]
            writer.writerow({
                "category": cell.category,
                "record": cell.segment,
                "segment_column": cell.segment_column,
                "world_column": cell.world_column,
                "world_x_start": cell.world_column * 8,
                "world_row": cell.world_row,
                "arcade_tile_code": f"0x{cell.tile_code:04X}",
                "source_address": f"0x{cell.source_address:06X}",
                "map_attr": f"0x{cell.attr:04X}",
                "palette_index": cell.attr & 0x1FF,
                "priority": "none_in_pc080sn_tile_info",
                "h_flip": 1 if cell.attr & 0x4000 else 0,
                "v_flip": 1 if cell.attr & 0x8000 else 0,
                "descriptor": f"0x{cell.descriptor:04X}",
                "descriptor_offset": f"0x{cell.descriptor_offset:06X}",
                "exact_pattern_hash": cell.exact_hash,
                "flip_normalized_hash": cell.normalized_hash,
                "first_use_column": min(columns),
                "last_use_column": max(columns),
                "use_intervals": ";".join(f"{a}-{b}" for a, b in intervals(columns)),
                "usage_family": cell.family,
            })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, default=Path("build/regions/maincpu.bin"))
    parser.add_argument("--gfx", type=Path, default=Path("build/regions/pc080sn.bin"))
    parser.add_argument("--out", type=Path, default=Path("analysis/cody_round1_phase1_plane_a_independent"))
    args = parser.parse_args()

    maincpu = args.maincpu.read_bytes()
    gfx = args.gfx.read_bytes()
    args.out.mkdir(parents=True, exist_ok=True)

    legal_cells = []
    for segment in PHASE_SEGMENTS:
        legal_cells.extend(reconstruct_segment(maincpu, gfx, segment, "A"))
    off_phase_codes = set()
    off_phase_hashes = set()
    castle_cells = []
    for segment in ALL_OFF_PHASE_SEGMENTS:
        segment_cells = reconstruct_segment(maincpu, gfx, segment, "D")
        off_phase_codes.update(cell.tile_code for cell in segment_cells)
        off_phase_hashes.update(cell.exact_hash for cell in segment_cells)
        if segment in range(16, 22):
            castle_cells.extend(segment_cells)

    usage_by_hash = defaultdict(list)
    codes_by_hash = defaultdict(set)
    attrs_by_hash = defaultdict(set)
    raw_by_hash = {}
    for cell in legal_cells:
        usage_by_hash[cell.exact_hash].append(cell)
        codes_by_hash[cell.exact_hash].add(cell.tile_code)
        attrs_by_hash[cell.exact_hash].add(cell.attr)
        raw_by_hash.setdefault(cell.exact_hash, tile_bytes(gfx, cell.tile_code))

    write_map_usage(args.out / "map_usage.csv", legal_cells, usage_by_hash)

    normalized_groups = defaultdict(list)
    for exact_hash, raw in raw_by_hash.items():
        normalized_groups[normalized_hash(raw)].append(exact_hash)

    first_use = {key: min(cell.world_column for cell in uses) for key, uses in usage_by_hash.items()}
    exact_hashes = sorted(raw_by_hash, key=lambda key: (first_use[key], key))
    exact_labels = {
        key: f"{min(codes_by_hash[key]):04X} C{first_use[key]:04d}" for key in exact_hashes
    }
    make_atlas(args.out / "exact_patterns_atlas.png", exact_hashes, raw_by_hash, exact_labels)

    normalized_representative = {}
    normalized_labels = {}
    for norm_hash, exact_group in normalized_groups.items():
        exact = min(exact_group, key=lambda key: (first_use[key], key))
        normalized_representative[norm_hash] = raw_by_hash[exact]
        normalized_labels[norm_hash] = f"{min(codes_by_hash[exact]):04X} C{first_use[exact]:04d}"
    normalized_hashes = sorted(
        normalized_representative,
        key=lambda key: (min(first_use[exact] for exact in normalized_groups[key]), key),
    )
    make_atlas(
        args.out / "flip_normalized_patterns_atlas.png",
        normalized_hashes,
        normalized_representative,
        normalized_labels,
    )
    make_map_previews(args.out, legal_cells, gfx)

    physical_fields = (
        "exact_pattern_hash", "representative_tile_code", "source_address", "logical_tile_codes",
        "logical_code_count", "map_attrs", "palette_indices", "h_flip_used", "v_flip_used",
        "flip_normalized_hash", "first_use_column", "last_use_column", "use_intervals",
        "records", "families", "cell_reference_count",
    )
    with (args.out / "physical_patterns.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=physical_fields)
        writer.writeheader()
        for key in exact_hashes:
            uses = usage_by_hash[key]
            columns = [cell.world_column for cell in uses]
            representative_code = min(codes_by_hash[key])
            writer.writerow({
                "exact_pattern_hash": key,
                "representative_tile_code": f"0x{representative_code:04X}",
                "source_address": f"0x{representative_code * 32:06X}",
                "logical_tile_codes": ";".join(f"0x{code:04X}" for code in sorted(codes_by_hash[key])),
                "logical_code_count": len(codes_by_hash[key]),
                "map_attrs": ";".join(f"0x{attr:04X}" for attr in sorted(attrs_by_hash[key])),
                "palette_indices": ";".join(str(attr & 0x1FF) for attr in sorted(attrs_by_hash[key])),
                "h_flip_used": int(any(cell.attr & 0x4000 for cell in uses)),
                "v_flip_used": int(any(cell.attr & 0x8000 for cell in uses)),
                "flip_normalized_hash": normalized_hash(raw_by_hash[key]),
                "first_use_column": min(columns),
                "last_use_column": max(columns),
                "use_intervals": ";".join(f"{a}-{b}" for a, b in intervals(columns)),
                "records": ";".join(str(value) for value in sorted({cell.segment for cell in uses})),
                "families": ";".join(sorted({cell.family for cell in uses})),
                "cell_reference_count": len(uses),
            })

    column_sets = defaultdict(set)
    column_codes = defaultdict(set)
    for cell in legal_cells:
        column_sets[cell.world_column].add(cell.exact_hash)
        column_codes[cell.world_column].add(cell.tile_code)
    with (args.out / "column_usage.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("world_column", "world_x_span", "record", "cell_count", "unique_tile_codes", "unique_patterns"))
        for column in sorted(column_sets):
            writer.writerow((
                column, f"{column * 8}-{column * 8 + 7}", column // 64, ROWS_PER_SEGMENT,
                len(column_codes[column]), len(column_sets[column]),
            ))

    max_window_count = 0
    max_window_start = 0
    for start in range(0, 1024 - 64 + 1):
        patterns = set()
        for column in range(start, start + 64):
            patterns.update(column_sets[column])
        if len(patterns) > max_window_count:
            max_window_count = len(patterns)
            max_window_start = start

    family_patterns = defaultdict(set)
    family_cells = defaultdict(int)
    family_spans = defaultdict(list)
    for cell in legal_cells:
        family_patterns[cell.family].add(cell.exact_hash)
        family_cells[cell.family] += 1
        family_spans[cell.family].append(cell.world_column)

    legal_codes = {cell.tile_code for cell in legal_cells}
    legal_hashes = set(usage_by_hash)
    bridge_cells = [
        cell for cell in legal_cells
        if BRIDGE_FIRST_COLUMN <= cell.world_column <= BRIDGE_LAST_COLUMN
    ]
    bridge_hashes = {cell.exact_hash for cell in bridge_cells}
    earlier_hashes = {
        cell.exact_hash for cell in legal_cells
        if cell.world_column < BRIDGE_FIRST_COLUMN
    }
    castle_hashes = {cell.exact_hash for cell in castle_cells}

    summary = {
        "inputs": {
            "maincpu": str(args.maincpu), "maincpu_sha256": sha256(maincpu),
            "pc080sn": str(args.gfx), "pc080sn_sha256": sha256(gfx),
        },
        "scope": {
            "segments": list(PHASE_SEGMENTS), "world_columns": [0, 1023],
            "legal_rows": [0, 63], "visible_rows_at_fixed_y_scroll": [1, 30],
        },
        "counts": {
            "legal_cells": len(legal_cells),
            "visible_category_a_cells": sum(cell.category == "A" for cell in legal_cells),
            "offscreen_category_b_cells": sum(cell.category == "B" for cell in legal_cells),
            "unique_tile_codes": len(legal_codes),
            "unique_exact_patterns": len(legal_hashes),
            "unique_flip_normalized_patterns": len(normalized_groups),
            "duplicate_logical_code_excess": sum(max(0, len(codes) - 1) for codes in codes_by_hash.values()),
            "flip_pattern_savings": len(legal_hashes) - len(normalized_groups),
            "pattern_groups_with_multiple_attrs": sum(len(attrs) > 1 for attrs in attrs_by_hash.values()),
            "attribute_variant_excess": sum(max(0, len(attrs) - 1) for attrs in attrs_by_hash.values()),
            "pattern_groups_with_multiple_palette_indices": sum(
                len({attr & 0x1FF for attr in attrs}) > 1 for attrs in attrs_by_hash.values()
            ),
            "priority_aliases": 0,
            "off_phase_unique_codes_not_in_phase1": len(off_phase_codes - legal_codes),
            "off_phase_unique_patterns_not_in_phase1": len(off_phase_hashes - legal_hashes),
            "source_table_only_codes": 0,
            "unreachable_row_codes": 0,
            "padding_or_zero_pointer_cells": 16 * 4096 - len(legal_cells),
        },
        "simultaneous": {
            "map_ring_columns": 64,
            "max_exact_patterns_in_any_64_column_window": max_window_count,
            "max_window_start": max_window_start,
            "max_window_end": max_window_start + 63,
        },
        "families": {
            name: {
                "segments": sorted({cell.segment for cell in legal_cells if cell.family == name}),
                "world_columns": [min(family_spans[name]), max(family_spans[name])],
                "cells": family_cells[name], "patterns": len(patterns),
            }
            for name, patterns in sorted(family_patterns.items())
        },
        "brick_bridge": {
            "segments": [9, 10],
            "world_columns": [BRIDGE_FIRST_COLUMN, BRIDGE_LAST_COLUMN],
            "world_x_span": [BRIDGE_FIRST_COLUMN * 8, BRIDGE_LAST_COLUMN * 8 + 7],
            "patterns": len(bridge_hashes),
            "bridge_only_vs_earlier": len(bridge_hashes - earlier_hashes),
            "shared_with_earlier": len(bridge_hashes & earlier_hashes),
            "continues_into_castle": len(bridge_hashes & castle_hashes),
        },
    }
    (args.out / "independent_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
