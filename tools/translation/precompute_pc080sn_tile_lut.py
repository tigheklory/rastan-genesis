#!/usr/bin/env python3
"""Precompute PC080SN tile/scene data.

Binary outputs (big-endian):
- pc080sn_tile_vram_lut.bin:
    u16 lut[16384] where lut[arcade_tile] -> Genesis VRAM slot (0 means unmapped).
- pc080sn_vram_preload.bin (legacy compatibility):
    repeated (u16 tile, u16 slot), terminated by u16 0xFFFF.
    This legacy preload is emitted from the Title/Attract scene manifest.
- pc080sn_scene_preload_{title,gameplay,endround}.bin:
    repeated (u16 tile, u16 slot), terminated by u16 0xFFFF.
- pc080sn_source_scene_map.bin:
    u32 magic ('S2MP' = 0x53324D50)
    u16 map_count
    u16 range_count
    map_count records of:
        u32 source_addr
        u8  scene_id
        u8  reserved0
        u16 reserved1
    range_count records of:
        u8  scene_id
        u8  reserved0
        u16 reserved1
        u32 min_source_addr
        u32 max_source_addr
"""

from __future__ import annotations

import argparse
import struct
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

PC080SN_TILE_COUNT = 16384
PC080SN_TILE_BYTES = 32
TILE_CACHE_BASE_A = 0
TILE_CACHE_SIZE_A = 1004
TILE_CACHE_BASE_B = 1280
TILE_CACHE_SIZE_B = 160
PC080SN_TILEMAP_WIDTH = 64
PC080SN_TABLE_TILE_OFFSET = 0x14
PC080SN_FG_STRIP_RANGE = 4
MAX_STRIP_RANGE = PC080SN_TILEMAP_WIDTH

SCENE_TITLE = 0
SCENE_GAMEPLAY = 1
SCENE_ENDROUND = 2
SCENE_IDS = (SCENE_TITLE, SCENE_GAMEPLAY, SCENE_ENDROUND)
SCENE_NAMES = {
    SCENE_TITLE: "Title",
    SCENE_GAMEPLAY: "Gameplay",
    SCENE_ENDROUND: "End-Round",
}

# Static one-shot block-write sources (0x5A38E/0x5A370/0x5A3AC/0x5A3DE/0x5A442 family).
TITLE_STATIC_BLOCKS = (
    (0x5B0B2, 28, 20, "title_logo"),
    (0x5A7DA, 28, 21, "title_alt"),
    (0x5AC72, 12, 10, "insert_coin"),
    (0x5AF62, 12, 14, "game_over_continue"),
    (0x5AD62, 16, 16, "stage_intro"),
)

# Table-driven block-write descriptors (12-byte entries: src32, dst32, rows16, cols16).
GAMEPLAY_TABLE_START = 0x5635E
GAMEPLAY_TABLE_END = 0x563A6
ENDROUND_TABLE_RANGES = (
    (0x5816A, 0x581A6, "endround_init"),
    (0x581A6, 0x581CA, "endround_anim_a"),
    (0x581CA, 0x581FA, "endround_anim_b"),
    (0x581FA, 0x5822A, "endround_anim_c"),
)

# Text writer ROM data sources.
# 0x3BB48 uses a PC-relative table at 0x3BB7C in the original maincpu ROM.
# (runtime-shifted addresses used in translated C hooks are not valid here)
TEXT_WRITER_3BB48_TABLE_SOURCE = 0x003BB7C
TEXT_WRITER_3BB48_TABLE_ENTRIES = 128
TEXT_TRANSLATE_FUNC_START = 0x563CE
TEXT_TRANSLATE_FUNC_END = 0x5643E

TEXT_SPECIAL_GLYPH_MAP = {
    0x21: 0x2744,  # '!'
    0x22: 0x2745,  # '"'
    0x27: 0x2746,  # '\''
    0x28: 0x2747,  # '('
    0x29: 0x2748,  # ')'
    0x2C: 0x2749,  # ','
    0x2D: 0x274A,  # '-'
    0x3F: 0x274B,  # '?'
}

SOURCE_SCENE_MAP_MAGIC = 0x53324D50  # 'S2MP'


@dataclass(frozen=True)
class BlockWriteSource:
    scene_id: int
    source_addr: int
    rows: int
    cols: int
    origin: str


def read_u16_be(blob: bytes, offset: int) -> int:
    return (blob[offset] << 8) | blob[offset + 1]


def read_u32_be(blob: bytes, offset: int) -> int:
    return (
        (blob[offset] << 24)
        | (blob[offset + 1] << 16)
        | (blob[offset + 2] << 8)
        | blob[offset + 3]
    )


def descriptor_valid(maincpu: bytes, desc_addr: int) -> bool:
    if (desc_addr & 1) != 0:
        return False
    if desc_addr + 3 >= len(maincpu):
        return False
    attr_word = read_u16_be(maincpu, desc_addr)
    if (attr_word & 0x1FFC) != 0:
        return False
    table_base = read_u16_be(maincpu, desc_addr + 2)
    if (table_base & 1) != 0:
        return False
    max_bg_addr = table_base + ((MAX_STRIP_RANGE - 1) << 1) + (3 << 3) + 1
    return max_bg_addr < len(maincpu)


def discover_descriptor_tables(maincpu: bytes) -> list[int]:
    tables: list[int] = []
    limit = len(maincpu) - (16 * 4)
    for base in range(0, limit, 2):
        valid = 0
        for i in range(16):
            ptr = read_u32_be(maincpu, base + (i * 4))
            if descriptor_valid(maincpu, ptr):
                valid += 1
        if valid >= 14:
            tables.append(base)
    return tables


def collect_strip_tiles(maincpu: bytes, table_bases: list[int]) -> set[int]:
    tiles: set[int] = {0}
    for base in table_bases:
        for i in range(16):
            desc_addr = read_u32_be(maincpu, base + (i * 4))
            if not descriptor_valid(maincpu, desc_addr):
                continue
            table_base = read_u16_be(maincpu, desc_addr + 2)
            for strip in range(MAX_STRIP_RANGE):
                for row in range(4):
                    addr = table_base + (strip << 1) + (row << 3)
                    if addr + 1 < len(maincpu):
                        tiles.add(read_u16_be(maincpu, addr) & 0x3FFF)
            for strip in range(PC080SN_FG_STRIP_RANGE):
                for col in range(4):
                    addr = table_base + (strip << 3) + (col << 1)
                    if addr + 1 < len(maincpu):
                        tiles.add(read_u16_be(maincpu, addr) & 0x3FFF)
    return tiles


def collect_table_block_sources(
    maincpu: bytes,
    table_start: int,
    table_end: int,
    scene_id: int,
    origin: str,
) -> list[BlockWriteSource]:
    if table_end <= table_start:
        raise SystemExit(f"invalid table range for {origin}: {table_start:#x}-{table_end:#x}")
    table_bytes = table_end - table_start
    if (table_bytes % 12) != 0:
        raise SystemExit(
            f"table {origin} size must be 12-byte records: got {table_bytes} bytes"
        )
    sources: list[BlockWriteSource] = []
    for addr in range(table_start, table_end, 12):
        src = read_u32_be(maincpu, addr)
        rows = read_u16_be(maincpu, addr + 8)
        cols = read_u16_be(maincpu, addr + 10)
        sources.append(
            BlockWriteSource(
                scene_id=scene_id,
                source_addr=src,
                rows=rows,
                cols=cols,
                origin=origin,
            )
        )
    return sources


def collect_block_write_sources(maincpu: bytes) -> list[BlockWriteSource]:
    sources: list[BlockWriteSource] = []

    for src, rows, cols, origin in TITLE_STATIC_BLOCKS:
        sources.append(
            BlockWriteSource(
                scene_id=SCENE_TITLE,
                source_addr=src,
                rows=rows,
                cols=cols,
                origin=origin,
            )
        )

    sources.extend(
        collect_table_block_sources(
            maincpu,
            GAMEPLAY_TABLE_START,
            GAMEPLAY_TABLE_END,
            SCENE_GAMEPLAY,
            "gameplay_table",
        )
    )

    for start, end, origin in ENDROUND_TABLE_RANGES:
        sources.extend(
            collect_table_block_sources(
                maincpu,
                start,
                end,
                SCENE_ENDROUND,
                origin,
            )
        )

    return sources


def extract_tiles_from_source(maincpu: bytes, source: BlockWriteSource) -> set[int]:
    if source.rows <= 0 or source.cols <= 0:
        raise SystemExit(
            f"invalid dimensions for source {source.source_addr:#x} ({source.origin}): "
            f"rows={source.rows}, cols={source.cols}"
        )

    total_words = source.rows * source.cols
    end = source.source_addr + (total_words * 2)
    if source.source_addr < 0 or end > len(maincpu):
        raise SystemExit(
            f"source {source.source_addr:#x} ({source.origin}) overflows ROM: "
            f"rows={source.rows}, cols={source.cols}, bytes={total_words * 2}"
        )

    out: set[int] = set()
    addr = source.source_addr
    for _ in range(total_words):
        out.add(read_u16_be(maincpu, addr) & 0x3FFF)
        addr += 2
    return out


def collect_block_scene_tiles_and_source_map(
    maincpu: bytes,
    sources: list[BlockWriteSource],
) -> tuple[dict[int, set[int]], dict[int, int]]:
    scene_tiles: dict[int, set[int]] = {
        SCENE_TITLE: set(),
        SCENE_GAMEPLAY: set(),
        SCENE_ENDROUND: set(),
    }
    source_scene_map: dict[int, int] = {}

    for source in sources:
        scene_tiles[source.scene_id].update(extract_tiles_from_source(maincpu, source))

        if source.source_addr in source_scene_map:
            existing = source_scene_map[source.source_addr]
            if existing != source.scene_id:
                raise SystemExit(
                    "source address mapped to multiple scenes: "
                    f"addr={source.source_addr:#x} scenes={existing}/{source.scene_id}"
                )
        else:
            source_scene_map[source.source_addr] = source.scene_id

    return scene_tiles, source_scene_map


def extract_text_writer_tiles(maincpu: bytes) -> set[int]:
    glyph_codes: set[int] = set()

    table_end = TEXT_WRITER_3BB48_TABLE_SOURCE + (TEXT_WRITER_3BB48_TABLE_ENTRIES * 4)
    if table_end > len(maincpu):
        raise SystemExit(
            "3BB48 descriptor table exceeds maincpu ROM: "
            f"{TEXT_WRITER_3BB48_TABLE_SOURCE:#x}-{table_end:#x}"
        )

    for index in range(TEXT_WRITER_3BB48_TABLE_ENTRIES):
        desc_ptr = read_u32_be(maincpu, TEXT_WRITER_3BB48_TABLE_SOURCE + (index * 4))
        if (
            desc_ptr == 0
            or desc_ptr < TEXT_WRITER_3BB48_TABLE_SOURCE
            or desc_ptr >= len(maincpu)
        ):
            continue
        if desc_ptr + 6 >= len(maincpu):
            continue

        src = desc_ptr + 6
        consumed = 0
        while src < len(maincpu):
            glyph = maincpu[src]
            src += 1
            consumed += 1
            if glyph == 0x00:
                break
            if glyph == 0xFF:
                continue
            glyph_codes.add(glyph)
            if consumed > 512:
                raise SystemExit(
                    f"3BB48 descriptor at {desc_ptr:#x} exceeded 512 bytes without terminator"
                )

    # Apply the original 0x563CE punctuation mapping and keep identity for other glyph bytes.
    text_tiles: set[int] = set()
    for glyph in glyph_codes:
        mapped = TEXT_SPECIAL_GLYPH_MAP.get(glyph, glyph)
        text_tiles.add(mapped & 0x3FFF)

    # Also include explicit punctuation tile constants recovered from the 0x563CE mapping routine.
    for addr in range(TEXT_TRANSLATE_FUNC_START, TEXT_TRANSLATE_FUNC_END - 3, 2):
        op = read_u16_be(maincpu, addr)
        if op == 0x303C:  # movew #imm,%d0
            imm = read_u16_be(maincpu, addr + 2)
            if 0x2700 <= imm <= 0x27FF:
                text_tiles.add(imm & 0x3FFF)

    # Space is used explicitly by text writer fill behavior.
    text_tiles.add(0x0020)

    return text_tiles


def build_slot_sequence() -> list[int]:
    slots: list[int] = []
    slots.extend(range(TILE_CACHE_BASE_A, TILE_CACHE_BASE_A + TILE_CACHE_SIZE_A))
    slots.extend(range(TILE_CACHE_BASE_B, TILE_CACHE_BASE_B + TILE_CACHE_SIZE_B))
    return slots


def assign_scene_aware_slots(
    scene_tiles: dict[int, set[int]],
    text_tiles: set[int],
) -> tuple[dict[int, int], dict[int, set[int]]]:
    slot_sequence = build_slot_sequence()
    max_slots = len(slot_sequence)

    scene_tile_sets: dict[int, set[int]] = {
        scene_id: {tile for tile in tiles if tile != 0}
        for scene_id, tiles in scene_tiles.items()
    }

    largest_scene = max(len(scene_tile_sets[scene]) for scene in SCENE_IDS)
    if largest_scene > max_slots:
        raise SystemExit(
            f"scene VRAM budget exceeded: largest scene uses {largest_scene} tiles, "
            f"budget is {max_slots}"
        )

    memberships: dict[int, set[int]] = defaultdict(set)
    for scene_id in SCENE_IDS:
        for tile in scene_tile_sets[scene_id]:
            memberships[tile].add(scene_id)

    used_slots_per_scene: dict[int, set[int]] = {scene_id: set() for scene_id in SCENE_IDS}
    assigned: dict[int, int] = {}

    def assign_tile(tile: int) -> None:
        if tile in assigned:
            return
        membership = memberships[tile]
        for slot in slot_sequence:
            conflict = False
            for scene_id in membership:
                if slot in used_slots_per_scene[scene_id]:
                    conflict = True
                    break
            if conflict:
                continue
            assigned[tile] = slot
            for scene_id in membership:
                used_slots_per_scene[scene_id].add(slot)
            return
        raise SystemExit(
            f"failed to allocate slot for tile {tile:#06x}; scene-aware budget exhausted"
        )

    prioritized_text_tiles = sorted(t for t in text_tiles if t in memberships and t != 0)
    for tile in prioritized_text_tiles:
        assign_tile(tile)

    remaining_tiles = sorted(
        (tile for tile in memberships if tile not in assigned),
        key=lambda tile: (-len(memberships[tile]), tile),
    )
    for tile in remaining_tiles:
        assign_tile(tile)

    return assigned, scene_tile_sets


def write_u16_be_bin(path: Path, words: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for value in words:
            f.write(struct.pack(">H", value & 0xFFFF))


def write_words_include(path: Path, words: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for idx, word in enumerate(words):
            sep = "," if idx != len(words) - 1 else ""
            f.write(f"    0x{word:04X}{sep}\n")


def write_scene_manifest(path: Path, pairs: list[tuple[int, int]]) -> None:
    words: list[int] = []
    for tile, slot in pairs:
        words.append(tile & 0xFFFF)
        words.append(slot & 0xFFFF)
    words.append(0xFFFF)
    write_u16_be_bin(path, words)


def write_source_scene_map(
    path: Path,
    source_scene_map: dict[int, int],
    scene_ranges: dict[int, tuple[int, int]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    map_items = sorted(source_scene_map.items())
    range_items = sorted(scene_ranges.items())

    with path.open("wb") as f:
        f.write(struct.pack(">IHH", SOURCE_SCENE_MAP_MAGIC, len(map_items), len(range_items)))

        for source_addr, scene_id in map_items:
            f.write(struct.pack(">IBBH", source_addr & 0xFFFFFFFF, scene_id & 0xFF, 0, 0))

        for scene_id, (min_addr, max_addr) in range_items:
            f.write(
                struct.pack(
                    ">BBHII",
                    scene_id & 0xFF,
                    0,
                    0,
                    min_addr & 0xFFFFFFFF,
                    max_addr & 0xFFFFFFFF,
                )
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Precompute PC080SN tile LUT, scene manifests, and source-scene map."
    )
    parser.add_argument(
        "--maincpu",
        default="build/regions/maincpu.bin",
        help="Input maincpu ROM path.",
    )
    parser.add_argument(
        "--pc080sn",
        default="build/regions/pc080sn.bin",
        help="Input PC080SN tile ROM path.",
    )
    parser.add_argument(
        "--lut-output",
        default="build/pc080sn_tile_vram_lut.bin",
        help="Output LUT binary path.",
    )
    parser.add_argument(
        "--preload-output",
        default="build/pc080sn_vram_preload.bin",
        help="Legacy preload manifest path.",
    )
    parser.add_argument(
        "--count-output",
        default="build/pc080sn_unique_tile_count.txt",
        help="Output unique tile count path.",
    )
    parser.add_argument(
        "--lut-include",
        default="build/pc080sn_tile_vram_lut_words.inc",
        help="Output LUT C include path.",
    )
    parser.add_argument(
        "--preload-include",
        default="build/pc080sn_vram_preload_words.inc",
        help="Output preload C include path.",
    )
    parser.add_argument(
        "--scene-title-output",
        default="build/pc080sn_scene_preload_title.bin",
        help="Output title scene preload manifest path.",
    )
    parser.add_argument(
        "--scene-gameplay-output",
        default="build/pc080sn_scene_preload_gameplay.bin",
        help="Output gameplay scene preload manifest path.",
    )
    parser.add_argument(
        "--scene-endround-output",
        default="build/pc080sn_scene_preload_endround.bin",
        help="Output end-round scene preload manifest path.",
    )
    parser.add_argument(
        "--source-scene-map-output",
        default="build/pc080sn_source_scene_map.bin",
        help="Output source->scene map path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maincpu = Path(args.maincpu).read_bytes()
    pc080sn = Path(args.pc080sn).read_bytes()

    if len(maincpu) < 0x10000:
        raise SystemExit(f"maincpu ROM unexpectedly small: {len(maincpu)} bytes")
    if len(pc080sn) != PC080SN_TILE_COUNT * PC080SN_TILE_BYTES:
        raise SystemExit(
            f"pc080sn ROM size mismatch: got {len(pc080sn)}, expected "
            f"{PC080SN_TILE_COUNT * PC080SN_TILE_BYTES}"
        )

    descriptor_tables = discover_descriptor_tables(maincpu)
    strip_tiles = collect_strip_tiles(maincpu, descriptor_tables)

    block_sources = collect_block_write_sources(maincpu)
    block_scene_tiles, source_scene_map = collect_block_scene_tiles_and_source_map(
        maincpu,
        block_sources,
    )

    text_tiles = extract_text_writer_tiles(maincpu)

    # Scene sets used for preload manifests and slot assignment.
    scene_tiles: dict[int, set[int]] = {
        SCENE_TITLE: set(block_scene_tiles[SCENE_TITLE]) | set(text_tiles),
        SCENE_GAMEPLAY: set(block_scene_tiles[SCENE_GAMEPLAY]) | set(strip_tiles) | set(text_tiles),
        SCENE_ENDROUND: set(block_scene_tiles[SCENE_ENDROUND]) | set(strip_tiles) | set(text_tiles),
    }

    assigned_slots, scene_tile_sets = assign_scene_aware_slots(scene_tiles, text_tiles)

    lut = [0] * PC080SN_TILE_COUNT
    for tile, slot in assigned_slots.items():
        if tile <= 0 or tile >= PC080SN_TILE_COUNT:
            raise SystemExit(f"tile index out of LUT range: {tile:#x}")
        lut[tile] = slot

    scene_manifest_pairs: dict[int, list[tuple[int, int]]] = {}
    for scene_id in SCENE_IDS:
        scene_manifest_pairs[scene_id] = [
            (tile, assigned_slots[tile])
            for tile in sorted(scene_tile_sets[scene_id])
            if tile in assigned_slots
        ]

    # Legacy preload remains for compatibility with existing runtime code.
    legacy_preload_pairs = scene_manifest_pairs[SCENE_TITLE]

    scene_ranges: dict[int, tuple[int, int]] = {}
    for scene_id in SCENE_IDS:
        scene_sources = sorted(
            source for source, mapped_scene in source_scene_map.items() if mapped_scene == scene_id
        )
        if not scene_sources:
            raise SystemExit(f"scene {scene_id} has no block-write sources")
        scene_ranges[scene_id] = (scene_sources[0], scene_sources[-1])

    # Validate disjoint source ranges.
    ordered_ranges = sorted((scene_ranges[scene], scene) for scene in SCENE_IDS)
    for idx in range(len(ordered_ranges) - 1):
        (lo_a, hi_a), scene_a = ordered_ranges[idx]
        (lo_b, hi_b), scene_b = ordered_ranges[idx + 1]
        if hi_a >= lo_b:
            raise SystemExit(
                "scene source ranges overlap: "
                f"scene {scene_a} [{lo_a:#x}-{hi_a:#x}] vs "
                f"scene {scene_b} [{lo_b:#x}-{hi_b:#x}]"
            )

    max_scene_usage = max(len(scene_tile_sets[scene]) for scene in SCENE_IDS)
    max_slots = len(build_slot_sequence())
    if max_scene_usage > max_slots:
        raise SystemExit(
            f"scene VRAM usage overflow: largest scene={max_scene_usage}, budget={max_slots}"
        )

    write_u16_be_bin(Path(args.lut_output), lut)
    write_words_include(Path(args.lut_include), lut)

    preload_words: list[int] = []
    for tile, slot in legacy_preload_pairs:
        preload_words.append(tile & 0xFFFF)
        preload_words.append(slot & 0xFFFF)
    preload_words.append(0xFFFF)
    write_u16_be_bin(Path(args.preload_output), preload_words)
    write_words_include(Path(args.preload_include), preload_words)

    write_scene_manifest(Path(args.scene_title_output), scene_manifest_pairs[SCENE_TITLE])
    write_scene_manifest(Path(args.scene_gameplay_output), scene_manifest_pairs[SCENE_GAMEPLAY])
    write_scene_manifest(Path(args.scene_endround_output), scene_manifest_pairs[SCENE_ENDROUND])

    write_source_scene_map(Path(args.source_scene_map_output), source_scene_map, scene_ranges)

    count_path = Path(args.count_output)
    count_path.parent.mkdir(parents=True, exist_ok=True)
    count_path.write_text(f"{len(assigned_slots)}\n", encoding="utf-8")

    print("Tile counts per scene:")
    print(f"  Title: {len(scene_tile_sets[SCENE_TITLE])}")
    print(f"  Gameplay: {len(scene_tile_sets[SCENE_GAMEPLAY])}")
    print(f"  End-Round: {len(scene_tile_sets[SCENE_ENDROUND])}")
    print(f"Total unique tile indices: {len(assigned_slots)}")
    print(f"VRAM max usage (largest scene): {max_scene_usage} / {max_slots}")
    for scene_id in SCENE_IDS:
        lo, hi = scene_ranges[scene_id]
        print(f"{SCENE_NAMES[scene_id]} range: 0x{lo:05X} - 0x{hi:05X}")
    print("Range overlap check: PASS (disjoint)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
