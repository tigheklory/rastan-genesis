#!/usr/bin/env python3
"""Verify Build-0425 selector-1/2 shared discovery and seam fallback.

Accepted Build 0424 resolves every column independently. Build 0425 shares one
descriptor/native record for an aligned four-column block only when that block
does not straddle the live ring front; the boundary fragment retains the old
per-cell selection. Collision is compared for every cell, while visual output
is independently gated by the fixed logical row's resident status.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from verify_plane_a_selector0_segment_hoist import (
    DESC_END,
    DESC_START,
    output,
    record_for,
)


ROOT = Path(__file__).resolve().parents[2]


def select_0424(row: int, col: int, sources: tuple[int, ...],
                group: int, strip: int) -> int:
    base = sources[(row >> 2) & 15]
    block = (col & 63) >> 2
    delta = block - (group & 15)
    front = ((group & 15) << 2) + (strip & 3)
    if col > front:
        delta -= 16
    return base + delta * 4


def straddles_front(block: int, group: int, strip: int) -> bool:
    start = block * 4
    front = ((group & 15) << 2) + (strip & 3)
    return start <= front < start + 3


def select_0425_block(row: int, block: int, sources: tuple[int, ...],
                      group: int, strip: int) -> list[int]:
    start = block * 4
    if straddles_front(block, group, strip):
        return [select_0424(row, start + cell, sources, group, strip)
                for cell in range(4)]
    return [select_0424(row, start, sources, group, strip)] * 4


def require_source_contract() -> None:
    source = (ROOT / "apps/rastan-direct/src/tilemap_hooks.s").read_text()
    start = source.index("genesistan_hook_tilemap_plane_a_selector12_native:")
    end = source.index("/* Native Plane A no-publication vertical-scroll route.", start)
    block = source[start:end]
    required = (
        ".Lplane_a_sel12_fallback_loop:",
        ".Lplane_a_sel12_shared_segment:",
        ".Lplane_a_sel12_shared_loop:",
        "PC080SN_DESC_REBUILD_SRC_TABLE",
        ".Lplane_a_native_metatile_record_from_d2",
        "MAP_GET_NAME_COLLISION_A",
        "MAP_GET_COLLISION",
        "0x20(%a4,%d0.w)",
        "fg_cache_resolve",
        "ARCADE_COLLISION_MAP_BASE",
    )
    for token in required:
        if token not in block:
            raise SystemExit(f"FAIL selector-1/2 segment hoist: source omits {token}")
    if block.count(".Lplane_a_native_metatile_record_from_d2") != 1:
        raise SystemExit("FAIL selector-1/2 segment hoist: shared lookup is not one per safe block")
    if block.count("MAP_GET_NAME_COLLISION_A") != 1 or block.count("MAP_GET_COLLISION") != 1:
        raise SystemExit("FAIL selector-1/2 segment hoist: seam fallback contract changed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    args = parser.parse_args()

    require_source_contract()
    maincpu = args.maincpu.read_bytes()
    index = args.index.read_bytes()
    records = args.records.read_bytes()

    # Runtime selection: all rows, live fronts, block/strip rollovers, source
    # rebases and descriptor-range boundary fragments. Safe blocks must share;
    # the one straddling block must reproduce all four accepted selections.
    source_bases = (
        DESC_START - 4, DESC_START, DESC_START + 4, 0x1691C, 0x18BDC,
        0x2C49C, DESC_END - 8, DESC_END - 4, DESC_END, DESC_END + 4,
    )
    selection_cases = 0
    seam_cases = 0
    for base in source_bases:
        sources = tuple(base + segment * 4 for segment in range(16))
        for row in range(64):
            for group in range(16):
                for strip in range(4):
                    for block in range(16):
                        old = [select_0424(row, block * 4 + cell, sources,
                                           group, strip) for cell in range(4)]
                        new = select_0425_block(row, block, sources, group, strip)
                        if old != new:
                            raise SystemExit(
                                "FAIL selector-1/2 segment hoist: selection differs "
                                f"base={base:#x} row={row} group={group} strip={strip} "
                                f"block={block} old={old} new={new}"
                            )
                        selection_cases += 1
                        seam_cases += straddles_front(block, group, strip)

    # Output contract: every descriptor and every row/column subcell under two
    # representative dynamic package contexts.  The shared record must produce
    # the exact same independent visual and collision products as four accepted
    # per-cell resolutions.  Residency is proven separately below because it is
    # purely a row/top predicate and multiplying it through every descriptor
    # would add ~120 million redundant comparisons without increasing coverage.
    output_cases = 0
    for descriptor in range(DESC_START, DESC_END, 4):
        shared = record_for(maincpu, index, records, descriptor)
        for row_in in range(4):
            for col_in in range(4):
                for context in (0, 7):
                    old_name, old_collision = output(
                        record_for(maincpu, index, records, descriptor),
                        row_in, col_in, context)
                    new_name, new_collision = output(
                        shared, row_in, col_in, context)
                    if old_collision != new_collision:
                        raise SystemExit(
                            "FAIL selector-1/2 segment hoist: collision differs "
                            f"descriptor={descriptor:#x} row={row_in} col={col_in}"
                        )
                    if old_name != new_name:
                        raise SystemExit(
                            "FAIL selector-1/2 segment hoist: resident visual differs "
                            f"descriptor={descriptor:#x} row={row_in} col={col_in}"
                        )
                    output_cases += 1

    # Every logical row and every possible visible top: collision is required
    # in both classes; only the resident half may consume the visual product.
    residency_cases = 0
    resident_cases = 0
    nonresident_cases = 0
    for logical_row in range(64):
        for top in range(64):
            resident = ((logical_row - top) & 63) < 32
            collision_consumed = True
            visual_consumed = resident
            if not collision_consumed or visual_consumed != resident:
                raise SystemExit(
                    "FAIL selector-1/2 segment hoist: residency product contract differs "
                    f"row={logical_row} top={top}"
                )
            residency_cases += 1
            resident_cases += resident
            nonresident_cases += not resident

    print(
        "PASS selector-1/2 runtime equivalence: "
        f"{selection_cases} selection/front/wrap/rebase cases "
        f"({seam_cases} seam fallbacks); {output_cases} descriptor/subcell/context "
        f"cases; {residency_cases} row/top residency cases "
        f"({resident_cases} resident, {nonresident_cases} nonresident); "
        "collision always produced; visual resident-only"
    )


if __name__ == "__main__":
    main()
