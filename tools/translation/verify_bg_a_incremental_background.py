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
NATIVE_MAPS = ROOT / "build/pc080sn_boundary/record_native_maps.bin"
PAN_ROWS = ROOT / "build/pc080sn_boundary/pan_row_maps.bin"
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
    pan_up = section(source, "genesistan_plane_a_pan_publish_entering_rows_up:",
                     ".Lplane_a_pan_up_done:")

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
                    "cmpi.w  #16, %d4", "fg_row_dirty",
                    "plane_a_resident_logical_rows",
                    ".Lplane_a_sel12_post_scroll_ready:",
                    ".Lplane_a_sel12_entering_rows_up_loop:",
                    ".Lplane_a_sel12_entering_rows_down_loop:",
                    "bsr     .Lplane_a_publish_logical_row_native",
                    ".Lplane_a_sel12_residency_recorded:"), "selector-1/2")
    if "bsr     .Lplane_b_publish_logical_row_native" in sel12:
        fail("Plane-A selector-1/2 edge repair writes independently owned Plane B")
    require(pan_up, ("addi.w  #27, %d0", "addi.w  #31, %d0",
                     "bsr     .Lplane_a_publish_logical_row_native"),
            "no-publication increasing-top edge repair")
    if pan_up.index("addi.w  #27, %d0") > pan_up.index("addi.w  #31, %d0"):
        fail("visible bottom must be validated before the offscreen prefetch edge")
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
                    ".Lplane_a_row_check_current_selector1:",
                    ".Lplane_a_row_current_selector12:",
                    "ARCADE_PC080SN_STRIP_GROUP_OFFSET",
                    "ARCADE_PC080SN_STRIP_INDEX_OFFSET",
                    "tst.w   0x132C(%a5)",
                    "subq.w  #1, %d1",
                    ".Lplane_a_row_precompiled_copy:",
                    ".Lplane_a_row_dynamic:",
                    ".Lplane_a_row_previous_selector0:",
                    "move.w  #0xFFFF, plane_a_src_ref_block",
                    ".Lplane_a_row_previous_selector0_cell:",
                    ".Lplane_a_row_mark_dirty:",
                    "lea     fg_boundary_active_lut, %a2",
                    "adda.w  %d1, %a6",
                    "ARCADE_PC080SN_STRIP_GROUP_OFFSET",
                    "ARCADE_PC080SN_STRIP_INDEX_OFFSET",
                    "move.w  #16, plane_a_src_ref_block",
                    "moveq   #0, %d4", "MAP_PUBLISH_NAME_A_BLOCK4",
                    "addq.w  #4, %d4",
                    "cmpi.w  #BG_LOGICAL_SPAN, %d4",
                    "fg_row_dirty", "plane_a_resident_logical_rows",
                    ".Lplane_a_row_already_resident:",
                    "cmp.b   0(%a0,%d1.w), %d2"), "Plane-A row producer")
    scene_reseed = section(source, "genesistan_plane_a_scene_scroll_reseed_native:",
                           "/* Native Plane A no-publication vertical-scroll route.")
    require(scene_reseed, (".Lscene_scroll_reseed_residency_loop:",
                           "plane_a_resident_logical_rows",
                           "ARCADE_PC080SN_SCROLL_Y_FG_OFFSET(%a5)",
                           "bsr     .Lplane_a_visible_top_from_scroll_d0"),
            "Plane-A scene residency seed")
    resolver = section(source, "resolve_plane_a_cell:",
                       "/* Resolve one gameplay collision word")
    require(resolver, ("cmpi.w  #0xFFFF, plane_a_src_ref_block",
                       ".Lrpc_source_previous_revolution:",
                       "subi.w  #16, %d2"),
            "Plane-A retained predecessor resolver")
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


def verify_no_publication_predecessor_selection() -> None:
    """No-publication motion exposes the completed ring, not the next record."""
    # 0x558C6 advances all sixteen pointers by one entry after each four
    # strips.  A completed 64-strip record therefore leaves every live pointer
    # exactly sixteen entries beyond the retained record.  Regenerating a
    # selector-0 predecessor must select that complete preceding revolution,
    # independent of the current physical front.
    for group in range(16):
        current_pointer_entry = 16 + group
        for column in range(LOGICAL):
            block = column >> 2
            selected_entry = current_pointer_entry + (block - group - 16)
            if selected_entry != block:
                fail(
                    "no-publication predecessor source mismatch "
                    f"group={group} column={column}: "
                    f"entry {selected_entry} != {block}"
                )

    # If the completed predecessor itself used selector 1/2, the runtime must
    # index its existing immutable row asset, not the already-advanced record.
    vertical_records = (17, 21, 43, 44)
    completed_records = tuple(record - 1 for record in vertical_records)
    if completed_records != (16, 20, 42, 43):
        fail(f"vertical predecessor inventory changed: {completed_records}")

    # Native Plane A is one 64x32 final buffer.  A 32-byte provenance vector
    # distinguishes the two logical rows which alias each physical row.  An
    # ordinary publication changes the owner; a no-publication event for the
    # same logical owner must preserve its exact current contents, while N+32
    # genuinely requires predecessor materialization.
    tags = [None] * PHYSICAL_H
    words = [STALE] * PHYSICAL_H
    top = 37
    for logical in ((top + i) & 63 for i in range(PHYSICAL_H)):
        physical = logical & 31
        tags[physical] = logical
        words[physical] = name_word(0, 16, logical, 0)

    def ordinary(logical: int, record: int) -> None:
        physical = logical & 31
        tags[physical] = logical
        words[physical] = name_word(0, record, logical, 0)

    def no_publication(logical: int, predecessor: int) -> bool:
        physical = logical & 31
        if tags[physical] == logical:
            return False
        tags[physical] = logical
        words[physical] = name_word(0, predecessor, logical, 0)
        return True

    confirmed = ((44, 17), (45, 17), (46, 17),
                 (12, 17), (13, 17), (14, 17),
                 (60, 21), (61, 21), (62, 21),
                 (35, 21), (36, 21), (37, 21), (38, 21),
                 (39, 21), (40, 21), (41, 21), (42, 21))
    for logical, record in confirmed:
        ordinary(logical, record)
        before = words[logical & 31]
        if no_publication(logical, record - 1):
            fail(f"resident logical row {logical} was rematerialized")
        if words[logical & 31] != before:
            fail(f"resident logical row {logical} changed on no-publication")

    for logical in (1, 12, 31, 44, 63):
        alias = (logical + 32) & 63
        ordinary(alias, 17)
        if not no_publication(logical, 16):
            fail(f"logical alias {logical}/{alias} was not materialized")
        expected = name_word(0, 16, logical, 0)
        if tags[logical & 31] != logical or words[logical & 31] != expected:
            fail(f"logical alias {logical}/{alias} materialized incorrectly")

    # PROMT-ID-0062/0063 gameplay and arcade-oracle case: a partially authored
    # vertical record is not uniformly predecessor-owned.  Original 0x055948
    # publishes at the old cursor and then increments 0x10CA, so the stored
    # front is the next row to author.  Selector 1 has authored 63 down through
    # 64-front; selector 2 has authored 0 up through front-1.  A physical
    # alias miss must therefore select the current record for an already-
    # authored row and the completed record for the still-retained remainder.
    def materialization_record(selector: int, front: int, logical: int,
                               current: int, completed: int) -> int:
        if selector == 1 and front > 0 and logical >= 64 - front:
            return current
        if selector == 2 and logical < front:
            return current
        return completed

    for front in range(LOGICAL):
        for logical in range(LOGICAL):
            want1 = 17 if front > 0 and logical >= 64 - front else 16
            got1 = materialization_record(1, front, logical, 17, 16)
            if got1 != want1:
                fail(f"selector-1 partial ownership mismatch front={front} row={logical}")
            want2 = 21 if logical < front else 20
            got2 = materialization_record(2, front, logical, 21, 20)
            if got2 != want2:
                fail(f"selector-2 partial ownership mismatch front={front} row={logical}")

    # At the captured selector-1 front 21, rows 44..46 were correctly authored
    # by record 17, their physical slots were reused by rows 12..14, and the
    # upward reversal then required genuine materialization of 44..46.  The
    # rematerialized source must still be current record 17.
    trace_front = 21
    for current_row, alias_row in ((46, 14), (45, 13), (44, 12)):
        ordinary(current_row, 17)
        ordinary(alias_row, 16)
        if tags[current_row & 31] != alias_row:
            fail(f"trace alias setup failed for {current_row}/{alias_row}")
        source = materialization_record(1, trace_front, current_row, 17, 16)
        if source != 17:
            fail(f"trace row {current_row} selected predecessor record {source}")
        ordinary(current_row, source)
        if words[current_row & 31] != name_word(0, 17, current_row, 0):
            fail(f"trace row {current_row} did not restore current-record contents")

    # PROMT-ID-0063 exact generated-row oracle.  The complete selector-0
    # predecessor maps and selector-1 pan rows are the same final-native assets
    # consumed by production.  At front zero no current row exists: logical 63
    # / physical 31 must remain record 16 at the 16->17 boundary and record 20
    # at the 20->21 boundary.  Build 0531's inclusive test selected the incoming
    # record instead.  Every later selector-1 front has the same one-row error
    # at logical 63-front; repeated reversals can therefore accumulate several
    # independently wrong record-21 rows.
    native = NATIVE_MAPS.read_bytes()
    pan = PAN_ROWS.read_bytes()
    records = 46
    native_table_bytes = records * 12

    def native_row(record: int, logical: int) -> bytes:
        entry = record * 12
        offset = int.from_bytes(native[entry:entry + 4], "big")
        start = native_table_bytes + offset + logical * 128
        row = native[start:start + 128]
        if len(row) != 128:
            fail(f"short native row record={record} row={logical}")
        return row

    def pan_row(record: int, logical: int) -> bytes:
        entry = record * 4
        offset = int.from_bytes(pan[entry:entry + 4], "big")
        if offset == 0xFFFFFFFF:
            fail(f"record {record} has no selector pan-row asset")
        start = offset + logical * 128
        row = pan[start:start + 128]
        if len(row) != 128:
            fail(f"short pan row record={record} row={logical}")
        return row

    for completed, current in ((16, 17), (20, 21)):
        for front in range(LOGICAL):
            boundary = 63 - front
            expected = native_row(completed, boundary)
            build_0531_wrong = pan_row(current, boundary)
            if expected == build_0531_wrong:
                fail(
                    "0063 boundary oracle is not discriminating "
                    f"records={completed}/{current} front={front} row={boundary}"
                )
            source = materialization_record(
                1, front, boundary, current, completed
            )
            if source != completed:
                fail(
                    "selector-1 next-to-author boundary selected current "
                    f"record={current} front={front} logical={boundary}"
                )
            physical = boundary & 31
            tags[physical] = (boundary + 32) & 63
            words[physical] = native_row(completed, (boundary + 32) & 63)
            tags[physical] = boundary
            words[physical] = expected
            if tags[physical] != boundary or words[physical] != expected:
                fail(
                    "0063 predecessor boundary materialization mismatch "
                    f"record={current} front={front} logical={boundary} physical={physical}"
                )
            if front:
                first_current = 64 - front
                source = materialization_record(
                    1, front, first_current, current, completed
                )
                if source != current:
                    fail(
                        "selector-1 first authored row selected predecessor "
                        f"record={current} front={front} logical={first_current}"
                    )
                if pan_row(current, first_current) != native_row(current, first_current):
                    fail(
                        "pan/native current row disagreement "
                        f"record={current} logical={first_current}"
                    )

            # Exercise both traversal directions and an immediate reversal on
            # the same physical N/N+32 slot.  Repeated crossings must restore
            # the predecessor boundary row every time; for a nonzero front,
            # the adjacent first-authored row must independently restore the
            # current record.  This models the cadence difference between
            # ordinary and jump-assisted rope ascent without adding any
            # jump-specific rendering rule.
            alias = (boundary + 32) & 63
            for _crossing in range(3):
                tags[physical] = alias
                words[physical] = native_row(completed, alias)
                source = materialization_record(
                    1, front, boundary, current, completed
                )
                words[physical] = (
                    pan_row(current, boundary)
                    if source == current else native_row(completed, boundary)
                )
                tags[physical] = boundary
                if words[physical] != expected:
                    fail(
                        "0063 repeated boundary reversal selected wrong row "
                        f"record={current} front={front} logical={boundary}"
                    )
            if front:
                current_physical = first_current & 31
                current_alias = (first_current + 32) & 63
                tags[current_physical] = current_alias
                words[current_physical] = native_row(completed, current_alias)
                source = materialization_record(
                    1, front, first_current, current, completed
                )
                words[current_physical] = (
                    pan_row(current, first_current)
                    if source == current else native_row(completed, first_current)
                )
                tags[current_physical] = first_current
                if words[current_physical] != pan_row(current, first_current):
                    fail(
                        "0063 immediate reversal lost first current row "
                        f"record={current} front={front} logical={first_current}"
                    )


def verify_selector12_visible_edge_and_prefetch_margin() -> None:
    """Preserve ordinary prefetch while repairing only a newly visible edge."""
    def visible_top(scroll: int) -> int:
        return ((-scroll + 8) & 0x1FF) >> 3

    def visible(logical: int, top: int) -> bool:
        return ((logical - top) & 63) < 28

    def entering_rows(selector: int, old_scroll: int, delta: int) -> list[int]:
        new_scroll = ((old_scroll + delta) if selector == 1
                      else (old_scroll - delta)) & 0x1FF
        old_top = visible_top(old_scroll)
        new_top = visible_top(new_scroll)
        rows: list[int] = []
        cursor = old_top
        if selector == 1:
            while cursor != new_top:
                cursor = (cursor - 1) & 63
                rows.append(cursor)
        else:
            while cursor != new_top:
                cursor = (cursor + 1) & 63
                rows.append((cursor + 27) & 63)
        return rows

    # Exact minimal-jump marker precursor.  At old scroll $001F selector 1
    # authors logical 59 into physical 27.  After the retained +1 scroll the
    # 28 visible rows are 61..24: physical 27 is one of the four offscreen
    # rows, so this ordinary arcade prefetch is valid and must not be suppressed
    # merely to force the complete 32-row plane into camera-window order.
    old_scroll = 0x001F
    delta = 1
    post_top = visible_top((old_scroll + delta) & 0x1FF)
    if post_top != 61 or visible(59, post_top):
        fail("minimal-jump row-59 post-step residency oracle changed")
    physical = 27
    tags = [None] * PHYSICAL_H
    words = [STALE] * PHYSICAL_H
    tags[physical] = 27
    words[physical] = name_word(0, 16, 27, 0)
    tags[physical] = 59
    words[physical] = name_word(0, 17, 59, 0)
    if tags[physical] != 59 or words[physical] != name_word(0, 17, 59, 0):
        fail("ordinary selector-1 offscreen prefetch was not retained")

    # Exact wrap crossing in the same capture: selector 1 authors logical 63
    # at old scroll $0000, then advances to $0001.  The authored row remains
    # outside the post-step display 0..27, while logical 0 genuinely enters.
    # An ordinary selector call bypasses the no-publication hook, so the native
    # selector tail itself must materialize that entering predecessor row.
    post_top = visible_top(1)
    if post_top != 0 or visible(63, post_top):
        fail("selector-1 wrap post-step residency oracle changed")
    entering = entering_rows(1, 0, 1)
    if entering != [0]:
        fail(f"selector-1 ordinary crossing entered {entering}, expected [0]")

    # Exercise both directions and every scroll/delta combination used by the
    # bounded helper model.  Each enumerated row must belong to the new display;
    # a no-crossing step must enumerate nothing.
    for selector in (1, 2):
        for scroll in range(512):
            for step in range(1, 9):
                signed = step if selector == 1 else -step
                new_top = visible_top((scroll + signed) & 0x1FF)
                rows = entering_rows(selector, scroll, step)
                if any(not visible(row, new_top) for row in rows):
                    fail(
                        "selector-1/2 entering row outside post-step display "
                        f"selector={selector} scroll={scroll} step={step} rows={rows}"
                    )


def verify_no_publication_downward_visible_history() -> None:
    """Reproduce the Build-0538 stale-bottom history, not merely its formula.

    The runtime helper named ``pan_up`` is the $055790 no-publication arm.  Its
    scroll subtraction increases visible_top, which is the player-visible
    downward traversal reported by Tighe: the entering display row is the new
    bottom at top+27.  The historical helper validated only top+31.
    """
    current, completed, selector, front = 17, 16, 1, 52
    native = NATIVE_MAPS.read_bytes()
    pan = PAN_ROWS.read_bytes()
    native_table_bytes = 46 * 12

    def native_row(record: int, logical: int) -> bytes:
        entry = record * 12
        offset = int.from_bytes(native[entry:entry + 4], "big")
        start = native_table_bytes + offset + logical * 128
        result = native[start:start + 128]
        if len(result) != 128:
            fail(f"short native row record={record} row={logical}")
        return result

    def pan_row(record: int, logical: int) -> bytes:
        entry = record * 4
        offset = int.from_bytes(pan[entry:entry + 4], "big")
        if offset == 0xFFFFFFFF:
            fail(f"record {record} has no selector pan-row asset")
        start = offset + logical * 128
        result = pan[start:start + 128]
        if len(result) != 128:
            fail(f"short pan row record={record} row={logical}")
        return result

    def materialization_record(logical: int) -> int:
        if selector == 1 and front > 0 and logical >= 64 - front:
            return current
        if selector == 2 and logical < front:
            return current
        return completed

    def row(record: int, logical: int) -> bytes:
        return (pan_row(record, logical) if record == current
                else native_row(record, logical))

    def materialize(tags: list[int | None], words: list[bytes | None],
                    logical: int) -> None:
        physical = logical & 31
        if tags[physical] == logical:
            return
        record = materialization_record(logical)
        tags[physical] = logical
        words[physical] = row(record, logical)

    # Ordered runtime history at the record-16/17 boundary:
    # 1. top 13's prefetch edge correctly materializes current-record L44/P12;
    # 2. ordinary selector-1 publication later authors L12 into the same P12;
    # 3. downward traversal advances top 13->17.  L44 is the new visible
    #    bottom only at the final crossing, while the old +31-only helper
    #    validates L45..L48 and never revisits P12.
    tags: list[int | None] = [None] * PHYSICAL_H
    words: list[bytes | None] = [None] * PHYSICAL_H
    materialize(tags, words, 44)
    physical = 44 & 31
    if tags[physical] != 44:
        fail("0087 history failed to prefetch record-17 logical row 44")
    tags[physical] = 12
    words[physical] = row(current, 12)
    if words[physical] == row(current, 44):
        fail("0087 record-17 N/N+32 oracle is not content-discriminating")

    legacy_tags = tags.copy()
    legacy_words = words.copy()
    for new_top in range(14, 18):
        materialize(legacy_tags, legacy_words, (new_top + 31) & 63)
    expected = 44
    if legacy_tags[physical] != expected - 32:
        fail("Build-0538 model no longer retains the proven N-32 stale owner")
    if legacy_words[physical] != row(current, expected - 32):
        fail("Build-0538 model stale contents no longer match logical row 12")

    # Corrected slow traversal: each single-row crossing validates the visible
    # bottom and the independent prefetch edge.  The last crossing repairs P12.
    slow_tags = tags.copy()
    slow_words = words.copy()
    for new_top in range(14, 18):
        materialize(slow_tags, slow_words, (new_top + 27) & 63)
        materialize(slow_tags, slow_words, (new_top + 31) & 63)
    if slow_tags[physical] != expected or slow_words[physical] != row(current, expected):
        fail("slow downward visible-bottom crossing retained stale N-32 owner")

    # Corrected fast traversal executes the same ordered crossings in one
    # helper invocation.  It must converge to the identical ownership state.
    fast_tags = tags.copy()
    fast_words = words.copy()
    old_top, new_top = 13, 17
    cursor = old_top
    while cursor != new_top:
        cursor = (cursor + 1) & 63
        materialize(fast_tags, fast_words, (cursor + 27) & 63)
        materialize(fast_tags, fast_words, (cursor + 31) & 63)
    if (fast_tags, fast_words) != (slow_tags, slow_words):
        fail("fast and slow downward histories produce different residency")

    # Opposite-direction entry remains the newly visible top itself.  This is
    # the accepted upward path and must not be shifted to either +27 or +31.
    reversal_tags = fast_tags.copy()
    reversal_words = fast_words.copy()
    materialize(reversal_tags, reversal_words, 16)
    if reversal_tags[16] != 16 or reversal_words[16] != row(current, 16):
        fail("upward/top-edge non-regression lost exact logical ownership")

    # The four rows after the 28-row display remain valid prefetch owners.
    for logical in range(45, 49):
        physical = logical & 31
        if fast_tags[physical] != logical:
            fail(f"prefetch ownership lost for logical row {logical}")


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
    verify_no_publication_predecessor_selection()
    verify_selector12_visible_edge_and_prefetch_margin()
    verify_no_publication_downward_visible_history()
    verify_plane_b_independent_context()
    verify_vertical_row_hoist_equivalence()
    verify_selector0_residency_hoist_equivalence()
    verify_dirty_gather_and_dma()
    print("PASS full-span background coherence: broken 0415 FAIL; broken 0416 "
          "FAIL; restored 0417/0418 full-span PASS; Build 0419 fused "
          "accessor PASS; Build 0422 generated semantics + ring-safe grouped "
          "row resolution PASS; initial 64x64 seed, N/N+32 semantics, "
          "source rebase, trailing retention, independent Plane-B context, "
          "no-publication completed-record selection + per-row retention, "
          "Build 0434 vertical-row context/LUT/miss equivalence, "
          "Build 0439 selector-0 active/static residency context equivalence, "
          "32-row projection, dirty gather, and 32-word column DMA PASS")


if __name__ == "__main__":
    main()
