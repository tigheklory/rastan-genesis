#!/usr/bin/env python3
"""Full-span logical background coherence and incremental-publication gate.

Builds 0415/0416 incorrectly equated the immediately visible 40x28/41x29
viewport with the logical maintenance domain. The current runtime resolves
cells through moving source/segment/package contexts, so every producer must
retain the established 64-cell coordinate model even though Genesis VRAM is a
64x32 physical plane. This gate keeps those contracts separate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "apps/rastan-direct/src/tilemap_hooks.s"
VDP_SOURCE = ROOT / "apps/rastan-direct/src/vdp_comm.s"
LOGICAL = 64
PHYSICAL_W = 64
PHYSICAL_H = 32
STALE = 0xDEAD


def fail(message: str) -> None:
    raise SystemExit(f"FAIL full-span background coherence: {message}")


def section(source: str, begin: str, end: str) -> str:
    try:
        start = source.index(begin)
        return source[start:source.index(end, start)]
    except ValueError as exc:
        fail(f"missing source boundary {begin!r} -> {end!r}: {exc}")


def require(block: str, tokens: tuple[str, ...], owner: str) -> None:
    for token in tokens:
        if token not in block:
            fail(f"{owner} omits {token!r}")


def static_contract() -> None:
    source = SOURCE.read_text()
    vdp = VDP_SOURCE.read_text()
    sel0 = section(source, "genesistan_hook_tilemap_plane_a_selector0_native:",
                   "genesistan_hook_tilemap_plane_a_selector12_native:")
    sel12 = section(source, "genesistan_hook_tilemap_plane_a_selector12_native:",
                    "/* Native Plane A no-publication vertical-scroll route.")
    row_a = section(source, ".Lplane_a_publish_logical_row_native:",
                    ".Lplane_a_strip_src_table:")
    block4 = section(source, ".Lplane_a_publish_name_block4_native:",
                     ".Lplane_a_strip_src_table:")
    row_b = section(source, ".Lplane_b_publish_logical_row_native:",
                    ".Lplane_b_stage_gameplay_producer_cell_native:")
    column_b = section(source, ".Ldirectional_publish_column_native:",
                       ".Ldirectional_bad_pointer:")
    bg_dma = section(source, "vdp_commit_bg_columns_if_dirty:",
                     "/* Build 0350/0415:")
    fg_dma = section(source, "vdp_commit_fg_columns_if_dirty:",
                     "vdp_commit_fg_narrow_strips:")

    require(source, (".equ BG_LOGICAL_SPAN,                    64",
                     ".macro MAP_GET_NAME_A", ".macro MAP_GET_NAME_B",
                     ".macro MAP_GET_COLLISION",
                     ".macro MAP_GET_NAME_COLLISION_A",
                     ".macro MAP_PUBLISH_NAME_A_BLOCK4"), "logical/accessor seam")
    if "BG_A_RESIDENT_ROWS" in source or "BG_A_RESIDENT_COLS" in source:
        fail("rejected viewport-local maintenance constants remain")

    require(sel0, (".Lplane_a_sel0_shared_ready", "PC080SN_DESC_REBUILD_SRC_TABLE",
                   ".Lplane_a_native_metatile_record_from_d2", "0x20(%a4,%d0.w)",
                   "fg_cache_resolve", "cmpi.w  #32", "fg_col_dirty",
                   "cmpi.w  #16, %d4"), "selector-0")
    if sel0.index("fg_cache_resolve") > sel0.index("cmpi.w  #32"):
        fail("selector-0 semantic resolution is behind physical projection")
    require(sel12, ("MAP_GET_COLLISION", "MAP_GET_NAME_COLLISION_A",
                    ".Lplane_a_sel12_fallback_loop",
                    ".Lplane_a_sel12_shared_segment",
                    ".Lplane_a_sel12_shared_loop",
                    ".Lplane_a_native_metatile_record_from_d2",
                    "0x20(%a4,%d0.w)", "cmpi.w  #32",
                    "cmpi.w  #16, %d4", "fg_row_dirty"), "selector-1/2")
    if "MAP_GET_NAME_COLLISION_A" in sel0:
        fail("selector-0 retains per-row fused descriptor discovery")
    if sel0.count(".Lplane_a_native_metatile_record_from_d2") != 1:
        fail("selector-0 must select one native record per four-row segment")
    if "\n    MAP_GET_COLLISION " in sel0 or "\n    MAP_GET_NAME_A " in sel0:
        fail("selector-0 retains a duplicate standalone semantic access")
    fused = section(source, "resolve_plane_a_name_collision_cell:",
                    "/* Resolve one gameplay collision word")
    require(fused, ("PC080SN_DESC_REBUILD_SRC_TABLE", "plane_a_src_ref_block",
                    ".Lplane_a_native_metatile_record_from_d2", "0x20(%a0",
                    ".Lplane_a_native_attr_from_word", "fg_cache_resolve"),
            "fused Plane-A name/collision accessor")
    require(row_a, ("moveq   #0, %d4", "MAP_PUBLISH_NAME_A_BLOCK4",
                    "addq.w  #4, %d4",
                    "cmpi.w  #BG_LOGICAL_SPAN, %d4"), "Plane-A row producer")
    require(block4, ("ARCADE_PC080SN_STRIP_GROUP_OFFSET",
                     "ARCADE_PC080SN_STRIP_INDEX_OFFSET",
                     ".Lplane_a_block_ring_seam_loop",
                     "bsr     resolve_plane_a_cell",
                     ".Lplane_a_block_single_descriptor"),
            "Plane-A four-cell ring-seam guard")
    require(row_b, ("moveq   #0, %d4", "MAP_GET_NAME_B",
                    ".Lplane_b_row_cached_group", "14(%sp)", "16(%sp)",
                    "cmpi.w  #BG_LOGICAL_SPAN, %d4"), "Plane-B row producer")
    native_leaf = section(source, ".Lplane_a_native_metatile_record_from_d2:",
                          "/* in: D0.W = logical row 0..63")
    require(native_leaf, ("genesistan_pc080sn_native_metatile_index",
                          "genesistan_pc080sn_native_metatile_records",
                          "lsl.l   #6", "cmpa.l  #0, %a0"),
            "generated Plane-A semantic leaf")
    if "tst.l   %a" in source:
        fail("illegal 68000 TST.L address-register form remains")
    require(column_b, ("genesistan_pc080sn_plane_b_visual_records",
                       "first resident logical row", "move.w  #31, %d6",
                       "MAP_GET_NAME_B", "plane_b_column_mode", "bg_col_dirty"),
            "Plane-B column producer")

    for name, block, gather, plane in (
        ("Plane B", bg_dma, "bg_col_gather", "VRAM_PLANE_B_BASE"),
        ("Plane A", fg_dma, "fg_col_gather", "VRAM_PLANE_A_BASE"),
    ):
        require(block, ("move.w  #0x80, %d1", gather,
                        "adda.w  #128, %a0", "move.w  #32, %d1",
                        "bsr     dma_words_to_vram_noai", plane,
                        "moveq   #0x02, %d1"), f"{name} column DMA")
        if block.index(gather) > block.index("bsr     dma_words_to_vram_noai"):
            fail(f"{name} gather is not regenerated before DMA")
    require(source, ("fg_col_dirty:\n    .long 0, 0",
                     "bg_col_dirty:\n    .long 0, 0",
                     "fg_col_gather:\n    .space (32 * 2)",
                     "bg_col_gather:\n    .space (32 * 2)"), "column storage")
    require(vdp, ("vdp_commit_bg_strips_if_dirty:\n    bsr     vdp_commit_bg_columns_if_dirty",
                  "move.l  bg_row_dirty, %d6"), "combined Plane-B publication")


def name_word(layer: int, context: int, row: int, col: int) -> int:
    """Context-sensitive semantic word; N and N+32 remain distinct."""
    return (1 + layer * 0x2000 + context * 0x311 + row * 0x83 + col * 0x11) & 0xFFFF


@dataclass(frozen=True)
class Model:
    name: str
    column_rows: int
    row_columns: int


BROKEN_0415 = Model("0415 40x28", 28, 40)
BROKEN_0416 = Model("0416 41x29", 29, 41)
RESTORED_0417 = Model("0417 full-span", 64, 64)


def logical_column_visits(model: Model, start: int = 0) -> list[int]:
    return [((start + i) & 63) for i in range(model.column_rows)]


def logical_row_visits(model: Model, start: int = 0) -> list[int]:
    return [((start + i) & 63) for i in range(model.row_columns)]


def logical_model_passes(model: Model) -> bool:
    for start in (0, 1, 17, 61, 63):
        if set(logical_column_visits(model, start)) != set(range(LOGICAL)):
            return False
        if set(logical_row_visits(model, start)) != set(range(LOGICAL)):
            return False
    return True


def verify_rejected_models_fail() -> None:
    if logical_model_passes(BROKEN_0415):
        fail("rejected Build 0415 model unexpectedly has full coherence")
    if logical_model_passes(BROKEN_0416):
        fail("rejected Build 0416 model unexpectedly has full coherence")
    if not logical_model_passes(RESTORED_0417):
        fail("restored Build 0417 model lacks full coherence")


def verify_initial_seed_and_projection() -> None:
    resolved: set[tuple[int, int]] = set()
    physical = [[STALE] * PHYSICAL_W for _ in range(PHYSICAL_H)]
    top = 19
    context = 3
    for col in range(LOGICAL):
        for row in logical_column_visits(RESTORED_0417):
            resolved.add((row, col))
            delta = (row - top) & 63
            if delta < PHYSICAL_H:
                physical[row & 31][col] = name_word(0, context, row, col)
    if len(resolved) != LOGICAL * LOGICAL:
        fail(f"initial seed resolved {len(resolved)} cells, expected 4096")
    for delta in range(PHYSICAL_H):
        row = (top + delta) & 63
        for col in range(LOGICAL):
            if physical[row & 31][col] != name_word(0, context, row, col):
                fail(f"initial physical projection mismatch r{row} c{col}")


def verify_n_n32_semantics() -> None:
    for row in range(PHYSICAL_H):
        if name_word(0, 4, row, 23) == name_word(0, 4, row + 32, 23):
            fail(f"test oracle aliases logical rows {row}/{row + 32}")
    visits = logical_column_visits(RESTORED_0417, 13)
    if any(row not in visits or row + 32 not in visits for row in range(32)):
        fail("full column producer omits an N/N+32 logical pair")


def verify_source_rebase_and_trailing_retention() -> None:
    for axis, visit in (("column", logical_column_visits),
                        ("row", logical_row_visits)):
        state = {i: name_word(0, 1, i if axis == "column" else 7,
                              7 if axis == "column" else i)
                 for i in range(LOGICAL)}
        for i in visit(RESTORED_0417, 0):
            state[i] = name_word(0, 2, i if axis == "column" else 7,
                                 7 if axis == "column" else i)
        for i in range(LOGICAL):
            want = name_word(0, 2, i if axis == "column" else 7,
                             7 if axis == "column" else i)
            if state[i] != want:
                fail(f"{axis} source rebase retained stale index {i}")

    ring = [name_word(0, 8, 12, col) for col in range(LOGICAL)]
    leading = 2
    before = ring.copy()
    ring[leading] = name_word(0, 9, 12, leading)
    for col in range(LOGICAL):
        want = name_word(0, 9, 12, col) if col == leading else before[col]
        if ring[col] != want:
            fail(f"trailing retention changed column {col}")


def verify_plane_b_independent_context() -> None:
    cases = ((4, 7), (5, 7), (5, 8))
    for a_context, b_context in cases:
        for row in logical_column_visits(RESTORED_0417, 61):
            if name_word(0, a_context, row, 17) == name_word(1, b_context, row, 17):
                fail("Plane-B column context collapsed into Plane A")
        for col in logical_row_visits(RESTORED_0417, 59):
            if name_word(0, a_context, 27, col) == name_word(1, b_context, 27, col):
                fail("Plane-B row/package context collapsed into Plane A")


def verify_dirty_gather_and_dma() -> None:
    staged = [[name_word(0, 6, row, col) for col in range(PHYSICAL_W)]
              for row in range(PHYSICAL_H)]
    vram = [[STALE] * PHYSICAL_W for _ in range(PHYSICAL_H)]
    dirty = (2, 3, 37, 63)
    scratch = [0] * PHYSICAL_H
    for col in dirty:
        for row in range(PHYSICAL_H):
            scratch[row] = staged[row][col]
        for row, word in enumerate(scratch):
            vram[row][col] = word
    for col in dirty:
        for row in range(PHYSICAL_H):
            if vram[row][col] != staged[row][col]:
                fail(f"gather/DMA mismatch r{row} c{col}")


def main() -> None:
    static_contract()
    verify_rejected_models_fail()
    verify_initial_seed_and_projection()
    verify_n_n32_semantics()
    verify_source_rebase_and_trailing_retention()
    verify_plane_b_independent_context()
    verify_dirty_gather_and_dma()
    print("PASS full-span background coherence: broken 0415 FAIL; broken 0416 "
          "FAIL; restored 0417/0418 full-span PASS; Build 0419 fused "
          "accessor PASS; Build 0422 generated semantics + ring-safe grouped "
          "row resolution PASS; initial 64x64 seed, N/N+32 semantics, "
          "source rebase, trailing retention, independent Plane-B context, "
          "32-row projection, dirty gather, and 32-word column DMA PASS")


if __name__ == "__main__":
    main()
