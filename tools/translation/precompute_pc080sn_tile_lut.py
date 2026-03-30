#!/usr/bin/env python3
"""Precompute PC080SN tile->VRAM LUT and preload manifest."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

PC080SN_TILE_COUNT = 16384
PC080SN_TILE_BYTES = 32
TILE_CACHE_BASE_A = 20
TILE_CACHE_SIZE_A = 1004
TILE_CACHE_BASE_B = 1280
TILE_CACHE_SIZE_B = 160


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
    table_base = read_u16_be(maincpu, desc_addr + 2)
    return (table_base & 1) == 0 and (table_base + 0x20) < len(maincpu)


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


def collect_tiles_from_tables(maincpu: bytes, table_bases: list[int]) -> set[int]:
    tiles: set[int] = {0}
    for base in table_bases:
        for i in range(16):
            desc_addr = read_u32_be(maincpu, base + (i * 4))
            if not descriptor_valid(maincpu, desc_addr):
                continue
            table_base = read_u16_be(maincpu, desc_addr + 2)
            for strip in range(4):
                for row in range(4):
                    addr = table_base + (strip << 1) + (row << 3)
                    if addr + 1 < len(maincpu):
                        tiles.add(read_u16_be(maincpu, addr) & 0x3FFF)
                for col in range(4):
                    addr = table_base + (strip << 3) + (col << 1)
                    if addr + 1 < len(maincpu):
                        tiles.add(read_u16_be(maincpu, addr) & 0x3FFF)
    return tiles


def build_slot_sequence() -> list[int]:
    slots: list[int] = []
    slots.extend(range(TILE_CACHE_BASE_A, TILE_CACHE_BASE_A + TILE_CACHE_SIZE_A))
    slots.extend(range(TILE_CACHE_BASE_B, TILE_CACHE_BASE_B + TILE_CACHE_SIZE_B))
    return slots


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Precompute PC080SN tile VRAM LUT and preload manifest."
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
        help="Output preload manifest binary path.",
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
    unique_tiles = sorted(collect_tiles_from_tables(maincpu, descriptor_tables))
    nonzero_tiles = [tile for tile in unique_tiles if tile != 0]

    slot_sequence = build_slot_sequence()
    if len(nonzero_tiles) > len(slot_sequence):
        raise SystemExit(
            "pc080sn tile assignment overflow: "
            f"{len(nonzero_tiles)} nonzero tiles > {len(slot_sequence)} slots"
        )

    lut = [0] * PC080SN_TILE_COUNT
    preload_pairs: list[tuple[int, int]] = []
    for idx, tile in enumerate(nonzero_tiles):
        slot = slot_sequence[idx]
        lut[tile] = slot
        preload_pairs.append((tile, slot))

    write_u16_be_bin(Path(args.lut_output), lut)

    preload_words: list[int] = []
    for tile, slot in preload_pairs:
        preload_words.append(tile & 0xFFFF)
        preload_words.append(slot & 0xFFFF)
    preload_words.append(0xFFFF)

    write_u16_be_bin(Path(args.preload_output), preload_words)
    write_words_include(Path(args.lut_include), lut)
    write_words_include(Path(args.preload_include), preload_words)

    count_path = Path(args.count_output)
    count_path.parent.mkdir(parents=True, exist_ok=True)
    count_path.write_text(f"{len(preload_pairs)}\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
