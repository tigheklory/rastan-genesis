#!/usr/bin/env python3
"""Audit VRAM tile usage across scenes in the Rastan arcade ROM."""

import struct
import sys
from pathlib import Path

ROM_PATH = Path("build/regions/maincpu.bin")
LUT_PATH = Path("build/pc080sn_tile_vram_lut.bin")

def read_rom():
    return ROM_PATH.read_bytes()

def read_words(rom, offset, count):
    """Read count big-endian 16-bit words from rom at offset."""
    words = []
    for i in range(count):
        w = struct.unpack_from(">H", rom, offset + i * 2)[0]
        words.append(w & 0x3FFF)
    return words

def read_descriptor_table(rom, table_offset, num_entries):
    """Read animation/HUD descriptor table entries.
    Each entry: src_ptr(4 BE), dest_ptr(4 BE), rows_per_col(2 BE), num_cols(2 BE) = 12 bytes.
    Returns list of unique tile indices from all source data."""
    all_tiles = []
    for i in range(num_entries):
        base = table_offset + i * 12
        src_ptr = struct.unpack_from(">I", rom, base)[0]
        rows_per_col = struct.unpack_from(">H", rom, base + 8)[0]
        num_cols = struct.unpack_from(">H", rom, base + 10)[0]
        count = rows_per_col * num_cols
        print(f"    Entry {i}: src=0x{src_ptr:06X}, rows={rows_per_col}, cols={num_cols}, words={count}")
        tiles = read_words(rom, src_ptr, count)
        all_tiles.extend(tiles)
    return all_tiles

def main():
    rom = read_rom()
    lut_data = LUT_PATH.read_bytes()

    print(f"ROM size: {len(rom)} bytes (0x{len(rom):X})")
    print(f"LUT size: {len(lut_data)} bytes ({len(lut_data)//2} entries)")
    print()

    # =========================================================================
    # SCENE: Title/Attract
    # =========================================================================
    print("=" * 70)
    print("SCENE: Title/Attract")
    print("=" * 70)

    title_tables = {
        "Title screen (0x5B0B2, 28x20)":       (0x5B0B2, 28 * 20),
        "Insert coin (0x5AC72, 12x10)":         (0x5AC72, 12 * 10),
        "Game over/continue (0x5AF62, 12x14)":  (0x5AF62, 12 * 14),
        "Stage intro/boss (0x5AD62, 16x16)":    (0x5AD62, 16 * 16),
        "Possible dead code (0x5A7DA, 28x21)":  (0x5A7DA, 28 * 21),
    }

    title_all_tiles = []
    for name, (offset, count) in title_tables.items():
        tiles = read_words(rom, offset, count)
        unique = sorted(set(tiles))
        # Filter out tile 0 for reporting? No, include all.
        print(f"  {name}: {count} words, {len(unique)} unique indices")
        title_all_tiles.extend(tiles)

    title_unique = sorted(set(title_all_tiles))
    print(f"\n  Title/Attract union: {len(title_unique)} unique tile indices")
    print(f"  Range: 0x{min(title_unique):04X} - 0x{max(title_unique):04X}")
    # Count non-zero
    title_nonzero = sorted(t for t in title_unique if t != 0)
    print(f"  Non-zero unique: {len(title_nonzero)}")
    print()

    # =========================================================================
    # SCENE: End-Round
    # =========================================================================
    print("=" * 70)
    print("SCENE: End-Round")
    print("=" * 70)

    endround_block_tables = {
        "Quadrant 1/2 (0x5822A, 32x16)":  (0x5822A, 32 * 16),
        "Quadrant 3 (0x5862A, 32x16)":    (0x5862A, 32 * 16),
        "Quadrant 4 (0x58A2A, 32x16)":    (0x58A2A, 32 * 16),
        "FG overlay (0x5919C, 10x14)":     (0x5919C, 10 * 14),
    }

    endround_all_tiles = []
    for name, (offset, count) in endround_block_tables.items():
        tiles = read_words(rom, offset, count)
        unique = sorted(set(tiles))
        print(f"  {name}: {count} words, {len(unique)} unique indices")
        endround_all_tiles.extend(tiles)

    # Animation descriptor tables
    print("\n  Animation descriptor tables:")

    print("  Table 0x581A6 (3 entries):")
    anim_tiles_1 = read_descriptor_table(rom, 0x581A6, 3)
    endround_all_tiles.extend(anim_tiles_1)

    print("  Table 0x581CA (4 entries):")
    anim_tiles_2 = read_descriptor_table(rom, 0x581CA, 4)
    endround_all_tiles.extend(anim_tiles_2)

    print("  Table 0x581FA (3 entries):")
    anim_tiles_3 = read_descriptor_table(rom, 0x581FA, 3)
    endround_all_tiles.extend(anim_tiles_3)

    endround_unique = sorted(set(endround_all_tiles))
    print(f"\n  End-Round union: {len(endround_unique)} unique tile indices")
    print(f"  Range: 0x{min(endround_unique):04X} - 0x{max(endround_unique):04X}")
    endround_nonzero = sorted(t for t in endround_unique if t != 0)
    print(f"  Non-zero unique: {len(endround_nonzero)}")
    print()

    # =========================================================================
    # SCENE: Gameplay
    # =========================================================================
    print("=" * 70)
    print("SCENE: Gameplay")
    print("=" * 70)

    print("  HUD descriptor table 0x5635E (6 entries):")
    gameplay_all_tiles = read_descriptor_table(rom, 0x5635E, 6)

    gameplay_unique = sorted(set(gameplay_all_tiles))
    print(f"\n  Gameplay union: {len(gameplay_unique)} unique tile indices")
    if gameplay_unique:
        print(f"  Range: 0x{min(gameplay_unique):04X} - 0x{max(gameplay_unique):04X}")
    gameplay_nonzero = sorted(t for t in gameplay_unique if t != 0)
    print(f"  Non-zero unique: {len(gameplay_nonzero)}")
    print()

    # =========================================================================
    # SHARED: Strip Builder Tiles (LUT)
    # =========================================================================
    print("=" * 70)
    print("SHARED: Strip Builder Tiles (LUT)")
    print("=" * 70)

    lut_entries = len(lut_data) // 2
    strip_tiles = set()
    for i in range(lut_entries):
        val = struct.unpack_from(">H", lut_data, i * 2)[0]
        if val != 0:
            strip_tiles.add(i)

    print(f"  LUT entries: {lut_entries}")
    print(f"  Non-zero (assigned) slots: {len(strip_tiles)}")
    if strip_tiles:
        print(f"  Tile index range: 0x{min(strip_tiles):04X} - 0x{max(strip_tiles):04X}")
    print()

    # =========================================================================
    # CROSS-SCENE ANALYSIS
    # =========================================================================
    print("=" * 70)
    print("CROSS-SCENE ANALYSIS")
    print("=" * 70)

    title_set = set(title_unique)
    endround_set = set(endround_unique)
    gameplay_set = set(gameplay_unique)

    # Cross-scene overlap (tiles in more than one scene)
    title_endround = title_set & endround_set
    title_gameplay = title_set & gameplay_set
    endround_gameplay = endround_set & gameplay_set
    all_three = title_set & endround_set & gameplay_set

    cross_scene = (title_endround | title_gameplay | endround_gameplay)
    print(f"\n  Title & End-Round overlap: {len(title_endround)} tiles")
    if title_endround:
        print(f"    {sorted(title_endround)[:30]}{'...' if len(title_endround) > 30 else ''}")
    print(f"  Title & Gameplay overlap: {len(title_gameplay)} tiles")
    if title_gameplay:
        print(f"    {sorted(title_gameplay)[:30]}{'...' if len(title_gameplay) > 30 else ''}")
    print(f"  End-Round & Gameplay overlap: {len(endround_gameplay)} tiles")
    if endround_gameplay:
        print(f"    {sorted(endround_gameplay)[:30]}{'...' if len(endround_gameplay) > 30 else ''}")
    print(f"  All three scenes overlap: {len(all_three)} tiles")
    if all_three:
        print(f"    {sorted(all_three)[:30]}{'...' if len(all_three) > 30 else ''}")
    print(f"  Total cross-scene overlap: {len(cross_scene)} tiles")

    # Overlap with strip builder
    print()
    blockwrite_all = title_set | endround_set | gameplay_set
    blockwrite_strip_overlap = blockwrite_all & strip_tiles
    print(f"  Block-write tiles total (all scenes union): {len(blockwrite_all)}")
    print(f"  Block-write & strip builder overlap: {len(blockwrite_strip_overlap)} tiles")
    if blockwrite_strip_overlap:
        bso = sorted(blockwrite_strip_overlap)
        print(f"    {bso[:40]}{'...' if len(bso) > 40 else ''}")

    # Per-scene vs strip builder
    title_strip = title_set & strip_tiles
    endround_strip = endround_set & strip_tiles
    gameplay_strip = gameplay_set & strip_tiles
    print(f"\n  Title & strip builder overlap: {len(title_strip)} tiles")
    print(f"  End-Round & strip builder overlap: {len(endround_strip)} tiles")
    print(f"  Gameplay & strip builder overlap: {len(gameplay_strip)} tiles")

    # =========================================================================
    # BUDGET SUMMARY
    # =========================================================================
    print()
    print("=" * 70)
    print("BUDGET SUMMARY")
    print("=" * 70)

    SLOT_LIMIT = 1164

    print(f"\n  Title/Attract unique tiles:  {len(title_unique):5d}  (non-zero: {len(title_nonzero)})")
    print(f"  End-Round unique tiles:      {len(endround_unique):5d}  (non-zero: {len(endround_nonzero)})")
    print(f"  Gameplay unique tiles:       {len(gameplay_unique):5d}  (non-zero: {len(gameplay_nonzero)})")
    print(f"  Strip builder assigned:      {len(strip_tiles):5d}")
    print()

    worst_case = max(len(title_unique), len(endround_unique), len(gameplay_unique))
    print(f"  Worst-case single scene (block-write only): {worst_case}")
    print(f"  Slot limit: {SLOT_LIMIT}")

    # Worst case = scene tiles + strip builder tiles (minus overlap)
    for scene_name, scene_set in [("Title", title_set), ("End-Round", endround_set), ("Gameplay", gameplay_set)]:
        overlap = scene_set & strip_tiles
        combined = len(scene_set) + len(strip_tiles) - len(overlap)
        exceeds = "EXCEEDS" if combined > SLOT_LIMIT else "OK"
        print(f"  {scene_name:12s} + strip builder = {len(scene_set)} + {len(strip_tiles)} - {len(overlap)} overlap = {combined}  [{exceeds}]")

    print()
    for scene_name, scene_set in [("Title", title_set), ("End-Round", endround_set), ("Gameplay", gameplay_set)]:
        if len(scene_set) > SLOT_LIMIT:
            print(f"  WARNING: {scene_name} alone ({len(scene_set)}) exceeds {SLOT_LIMIT} slots!")

    any_exceeds = any(len(s) > SLOT_LIMIT for s in [title_set, endround_set, gameplay_set])
    if not any_exceeds:
        print(f"  No single scene exceeds {SLOT_LIMIT} slots (block-write only).")

    # Print full sorted unique lists (compact)
    print()
    print("=" * 70)
    print("FULL UNIQUE TILE INDEX LISTS")
    print("=" * 70)
    for scene_name, tiles in [("Title/Attract", title_unique), ("End-Round", endround_unique), ("Gameplay", gameplay_unique)]:
        print(f"\n  {scene_name} ({len(tiles)} tiles):")
        # Print in hex, 16 per line
        for i in range(0, len(tiles), 16):
            chunk = tiles[i:i+16]
            print("    " + " ".join(f"{t:04X}" for t in chunk))

if __name__ == "__main__":
    main()
