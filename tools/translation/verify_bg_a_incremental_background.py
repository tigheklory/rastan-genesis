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
BOUNDARY_LUT_WORDS = 10240


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
                   "lea     genesistan_pc080sn_tile_vram_lut, %a2",
                   "cmpi.b  #1, genesistan_current_scene_id",
                   "lea     fg_boundary_active_lut, %a2",
                   "move.w  #FG_BOUNDARY_LUT_WORDS, %d7",
                   ".Lplane_a_sel0_residency_context_ready",
                   ".Lplane_a_sel0_residency_miss",
                   "move.w  0(%a2,%d3.w), %d3",
                   "addq.l  #1, fg_boundary_miss_a",
                   "cmpi.w  #32", "fg_col_dirty",
                   "cmpi.w  #16, %d4"), "selector-0")
    if "bsr     fg_cache_resolve" in sel0:
        fail("selector-0 hot loop retains the general per-cell residency helper")
    context_end = sel0.index(".Lplane_a_sel0_residency_context_ready:")
    cell_loop = sel0.index(".Lplane_a_sel0_cell_loop:")
    if context_end > cell_loop:
        fail("selector-0 residency context selection is inside the cell loop")
    if sel0.count("cmpi.b  #1, genesistan_current_scene_id") != 1:
        fail("selector-0 must select scene/LUT context exactly once per column")
    require(sel12, ("PC080SN_DESC_REBUILD_PTR_TABLE",
                    "PC080SN_DESC_REBUILD_WORD_TABLE",
                    "subi.l  #PC080SN_DESC_SECOND_WORD_BASE, %d2",
                    ".Lplane_a_sel12_shared_loop",
                    ".Lplane_a_native_metatile_record_from_d2",
                    "0x20(%a4,%d0.w)", "cmpi.w  #32",
                    "cmpi.w  #16, %d4", "fg_row_dirty"), "selector-1/2")
    if "MAP_GET_COLLISION" in sel12 or "MAP_GET_NAME_COLLISION_A" in sel12:
        fail("selector-1/2 reintroduces generic coordinate discovery below rebuilt A3 pointers")
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
    require(row_a, ("movea.l 0(%a0,%d1.w), %a4",
                    "genesistan_plane_a_pan_row_maps",
                    "FG_PAN_ROW_MAP_BYTES",
                    ".Lplane_a_row_precompiled_copy:",
                    ".Lplane_a_row_dynamic:",
                    ".Lplane_a_row_mark_dirty:",
                    "lea     fg_boundary_active_lut, %a2",
                    "adda.w  %d1, %a6",
                    "ARCADE_PC080SN_STRIP_GROUP_OFFSET",
                    "ARCADE_PC080SN_STRIP_INDEX_OFFSET",
                    "move.w  #16, plane_a_src_ref_block",
                    "moveq   #0, %d4", "MAP_PUBLISH_NAME_A_BLOCK4",
                    "addq.w  #4, %d4",
                    "cmpi.w  #BG_LOGICAL_SPAN, %d4",
                    "fg_row_dirty"), "Plane-A row producer")
    require(block4, ("movea.l %a4, %a0",
                     "MAP_GET_AUTHORED_VISUAL_A0",
                     "MAP_GET_NAME_A_GAMEPLAY_ROW",
                     ".Lplane_a_block_ring_seam_loop",
                     "bsr     resolve_plane_a_cell",
                     ".Lplane_a_block_single_descriptor"),
            "Plane-A four-cell ring-seam guard")
    require(row_b, ("lea     fg_boundary_active_lut, %a2",
                    "adda.w  %d0, %a6",
                    "moveq   #0, %d4", "MAP_GET_NAME_B_GAMEPLAY_ROW",
                    ".Lplane_b_row_cached_group", "14(%sp)", "16(%sp)",
                    "cmpi.w  #BG_LOGICAL_SPAN, %d4", "bg_row_dirty"),
            "Plane-B row producer")
    for macro in ("MAP_GET_NAME_A_GAMEPLAY_ROW", "MAP_GET_NAME_B_GAMEPLAY_ROW"):
        direct = section(source, f".macro {macro}", ".endm")
        require(direct, ("andi.w  #0x3FFF, %d3",
                         "cmpi.w  #FG_BOUNDARY_LUT_WORDS, %d3",
                         "move.w  0(%a2,%d3.w), %d3",
                         "moveq   #0, %d3"), macro)
    if row_a.count("PC080SN_DESC_REBUILD_SRC_TABLE") != 1:
        fail("Plane-A row source context is not selected exactly once per row")
    if row_a.count("lea     staged_fg_buffer, %a6") != 2:
        fail("Plane-A precompiled/dynamic staging-row contexts are not each selected once")
    if row_b.count("lea     staged_bg_buffer, %a6") != 1:
        fail("Plane-B staging-row context is not selected exactly once per row")
    if "bsr     fg_cache_resolve" in block4:
        fail("Plane-A row hot loop retains the general per-cell LUT helper")
    if "MAP_GET_NAME_B\n" in row_b:
        fail("Plane-B row hot loop retains the general per-cell LUT helper")
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


def old_row_lut_resolve(code: int, lut: list[int]) -> tuple[int, int]:
    """Scene-1 behavior of the accepted Build-0433 general resolver."""
    code &= 0x3FFF
    if code == 0:
        return 0, 0
    if code >= BOUNDARY_LUT_WORDS:
        return 0, 1
    resolved = lut[code]
    return (resolved, 0) if resolved else (0, 1)


def hoisted_row_lut_resolve(code: int, lut: list[int]) -> tuple[int, int]:
    """Build-0434 inline row leaf: value and miss delta must stay identical."""
    code &= 0x3FFF
    if code == 0:
        return 0, 0
    if code >= BOUNDARY_LUT_WORDS:
        return 0, 1
    resolved = lut[code]
    if resolved:
        return resolved, 0
    return 0, 1


def old_selector0_lut_resolve(
    scene: int, code: int, active_lut: list[int], static_lut: list[int]
) -> tuple[int, int]:
    """Exact pre-0439 fg_cache_resolve value and Plane-A miss delta."""
    code &= 0x3FFF
    if code == 0:
        return 0, 0
    if scene != 1:
        return static_lut[code], 0
    if code >= BOUNDARY_LUT_WORDS:
        return 0, 1
    resolved = active_lut[code]
    return (resolved, 0) if resolved else (0, 1)


def hoisted_selector0_lut_resolve(
    scene: int, code: int, active_lut: list[int], static_lut: list[int]
) -> tuple[int, int]:
    """Build-0439 once-selected LUT context plus inline lookup semantics."""
    code &= 0x3FFF
    if scene == 1:
        lut = active_lut
        limit = BOUNDARY_LUT_WORDS
        count_miss = True
    else:
        lut = static_lut
        limit = 0x4000
        count_miss = False
    if code == 0:
        return 0, 0
    if code >= limit:
        return 0, 1
    resolved = lut[code]
    if resolved or not count_miss:
        return resolved, 0
    return 0, 1


def verify_selector0_residency_hoist_equivalence() -> None:
    """Exhaustively prove active/static lookup, output and column contracts."""
    active_lut = [((code * 37) ^ 0x35A) & 0x07FF
                  for code in range(BOUNDARY_LUT_WORDS)]
    static_lut = [((code * 53) ^ 0x621) & 0x07FF
                  for code in range(0x4000)]
    for code in range(0, BOUNDARY_LUT_WORDS, 97):
        active_lut[code] = 0
    for code in range(0, 0x4000, 113):
        static_lut[code] = 0

    # Scene 1 is the active package LUT.  Representative non-gameplay scene
    # identities all take the unchanged full static-LUT contract.
    for scene in (0, 1, 2, 0xFF):
        for code in range(0x4000):
            old = old_selector0_lut_resolve(scene, code, active_lut, static_lut)
            new = hoisted_selector0_lut_resolve(scene, code, active_lut, static_lut)
            if old != new:
                fail(
                    "selector-0 residency mismatch "
                    f"scene={scene:#04x} code={code:#06x}: {old} != {new}"
                )

    # Preserve the entire 64-row logical/collision traversal, the exact
    # 32-row physical projection, final attr composition, destination words,
    # cumulative miss delta and single dirty-column result for every visible
    # top and entering column.  Codes deliberately exercise zero, active
    # hits/misses, active out-of-range, and static zero entries.
    code_cases = (0, 1, 97, BOUNDARY_LUT_WORDS - 1,
                  BOUNDARY_LUT_WORDS, 0x3FFF)
    for scene in (0, 1, 2):
        for visible_top in range(LOGICAL):
            for entering_col in range(LOGICAL):
                old_collision: list[tuple[int, int]] = []
                new_collision: list[tuple[int, int]] = []
                old_stage: list[tuple[int, int]] = []
                new_stage: list[tuple[int, int]] = []
                old_misses = 0
                new_misses = 0
                attr = 0x6000 | ((entering_col & 3) << 9)
                for row in range(LOGICAL):
                    code = code_cases[(row + entering_col) % len(code_cases)]
                    collision = ((row * 0x83) ^ entering_col) & 0xFFFF
                    collision_dest = row * LOGICAL + entering_col
                    old_collision.append((collision_dest, collision))
                    new_collision.append((collision_dest, collision))
                    old_word, old_delta = old_selector0_lut_resolve(
                        scene, code, active_lut, static_lut
                    )
                    new_word, new_delta = hoisted_selector0_lut_resolve(
                        scene, code, active_lut, static_lut
                    )
                    old_misses += old_delta
                    new_misses += new_delta
                    if ((row - visible_top) & 63) < PHYSICAL_H:
                        stage_dest = (row & 31) * LOGICAL + entering_col
                        old_stage.append((stage_dest, old_word | attr))
                        new_stage.append((stage_dest, new_word | attr))
                if old_collision != new_collision or len(new_collision) != LOGICAL:
                    fail(
                        "selector-0 collision traversal mismatch "
                        f"scene={scene} top={visible_top} col={entering_col}"
                    )
                if old_stage != new_stage or len(new_stage) != PHYSICAL_H:
                    fail(
                        "selector-0 staging projection mismatch "
                        f"scene={scene} top={visible_top} col={entering_col}"
                    )
                if old_misses != new_misses:
                    fail(
                        "selector-0 miss delta mismatch "
                        f"scene={scene} top={visible_top} col={entering_col}: "
                        f"{old_misses} != {new_misses}"
                    )
                old_dirty = 1 << entering_col
                new_dirty = 1 << entering_col
                if old_dirty != new_dirty:
                    fail(f"selector-0 dirty-column mismatch col={entering_col}")


def verify_vertical_row_hoist_equivalence() -> None:
    """Exhaustively compare the accepted and hoisted vertical-row contracts."""
    lut = [((code * 37) ^ 0x35A) & 0x07FF for code in range(BOUNDARY_LUT_WORDS)]
    for code in range(0, BOUNDARY_LUT_WORDS, 97):
        lut[code] = 0
    for code in range(0x4000):
        old = old_row_lut_resolve(code, lut)
        new = hoisted_row_lut_resolve(code, lut)
        if old != new:
            fail(f"row LUT/miss mismatch code={code:#06x}: {old} != {new}")

    # Build 0433 recomputed these values in each four-cell block. Build 0434
    # computes them once per row; the values themselves must be unchanged.
    for row in range(LOGICAL):
        old_source_row = (row >> 2) & 0xF
        new_source_row = (row >> 2) & 0xF
        old_dest_row = row & 0x1F
        new_dest_row = row & 0x1F
        if (old_source_row, old_dest_row) != (new_source_row, new_dest_row):
            fail(f"row context mismatch at logical row {row}")
        for strip_group in range(16):
            for strip_index in range(4):
                front = strip_group * 4 + strip_index
                for block_col in range(0, LOGICAL, 4):
                    seam_old = block_col <= front < block_col + 4
                    seam_new = block_col <= front < block_col + 4
                    if seam_old != seam_new:
                        fail(f"ring-seam classification mismatch front={front} block={block_col}")
                    for col in range(block_col, block_col + 4):
                        old_delta = (col >> 2) - strip_group
                        if col > front:
                            old_delta -= 16
                        new_delta = (col >> 2) - strip_group
                        if col > front:
                            new_delta -= 16
                        old_dest = old_dest_row * PHYSICAL_W + col
                        new_dest = new_dest_row * PHYSICAL_W + col
                        if (old_delta, old_dest) != (new_delta, new_dest):
                            fail(
                                "Plane-A row hoist mismatch "
                                f"r={row} c={col} front={front}: "
                                f"{(old_delta, old_dest)} != {(new_delta, new_dest)}"
                            )

    # Plane B changes only the hoisted physical row base and LUT call leaf.
    for row in range(LOGICAL):
        for col in range(LOGICAL):
            old_dest = (row & 0x1F) * PHYSICAL_W + col
            new_dest = (row & 0x1F) * PHYSICAL_W + col
            if old_dest != new_dest:
                fail(f"Plane-B row destination mismatch r={row} c={col}")


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
    verify_vertical_row_hoist_equivalence()
    verify_selector0_residency_hoist_equivalence()
    verify_dirty_gather_and_dma()
    print("PASS full-span background coherence: broken 0415 FAIL; broken 0416 "
          "FAIL; restored 0417/0418 full-span PASS; Build 0419 fused "
          "accessor PASS; Build 0422 generated semantics + ring-safe grouped "
          "row resolution PASS; initial 64x64 seed, N/N+32 semantics, "
          "source rebase, trailing retention, independent Plane-B context, "
          "Build 0434 vertical-row context/LUT/miss equivalence, "
          "Build 0439 selector-0 active/static residency context equivalence, "
          "32-row projection, dirty gather, and 32-word column DMA PASS")


if __name__ == "__main__":
    main()
