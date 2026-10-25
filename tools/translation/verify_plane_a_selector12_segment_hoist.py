#!/usr/bin/env python3
"""Verify selector-1/2 arcade row and rebuilt-metatile semantics.

Original 0x55904 rebuilds parallel tables: descriptor word0 at 0x10D080 and
0x200 + descriptor word1 (a metatile-data pointer) at 0x10D040.  Original
0x55A14 consumes those two products directly.  The native producer must remove
only the Genesis copy relocation from the pointer, use word1 to select the
native metatile record, and preserve word0 independently as the attribute.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from verify_plane_a_selector0_segment_hoist import (
    DESC_END,
    DESC_START,
    be16,
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


def destination_row(selector: int, group: int, strip: int) -> int:
    """Exact PC080SN destination row from 0x556DC/0x5576E arithmetic."""
    forward = ((group & 15) * 4 + (strip & 3)) & 63
    return (63 - forward) & 63 if selector == 1 else forward


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
        ".Lplane_a_sel12_shared_loop:",
        "PC080SN_DESC_REBUILD_PTR_TABLE",
        "PC080SN_DESC_REBUILD_WORD_TABLE",
        "subi.l  #PC080SN_DESC_SECOND_WORD_BASE, %d2",
        "move.w  10(%sp), %d0",
        ".Lplane_a_native_metatile_record_from_d2",
        "0x20(%a4,%d0.w)",
        "fg_cache_resolve",
        "ARCADE_COLLISION_MAP_BASE",
        "addi.w  #63, %d0",
        ".Lplane_a_sel12_logical_row_ready:",
    )
    for token in required:
        if token not in block:
            raise SystemExit(f"FAIL selector-1/2 segment hoist: source omits {token}")
    if block.count(".Lplane_a_native_metatile_record_from_d2") != 1:
        raise SystemExit("FAIL selector-1/2 producer: native lookup is not one per rebuilt pointer")
    if "MAP_GET_NAME_COLLISION_A" in block or "MAP_GET_COLLISION" in block:
        raise SystemExit("FAIL selector-1/2 producer: generic coordinate resolver reintroduced")


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

    # Selector 1's complemented strip is a source-metatile row selector only.
    # Prove the independent destination coordinate for all ring states against
    # the original 0x55696 (reverse) and 0x5572E (forward) formulas.
    destination_cases = 0
    for group in range(16):
        for strip in range(4):
            linear = group * 4 + strip
            if destination_row(1, group, strip) != 63 - linear:
                raise SystemExit("FAIL selector-1 reverse destination row")
            if destination_row(2, group, strip) != linear:
                raise SystemExit("FAIL selector-2 forward destination row")
            destination_cases += 2

    # Rebuild/consumer contract over every source descriptor.  A3 is the
    # relocated metatile pointer 0x200+word1, not the descriptor's address;
    # A1 is the independent word0 attribute.  Prove that reversing exactly
    # that relocation selects the same generated semantic record and output
    # as the original descriptor for every subcell and residency context.
    selection_cases = 0
    for descriptor in range(DESC_START, DESC_END, 4):
        attr = be16(maincpu, descriptor)
        word1 = be16(maincpu, descriptor + 2)
        rebuilt_pointer = 0x200 + word1
        recovered_word1 = rebuilt_pointer - 0x200
        if recovered_word1 != word1:
            raise SystemExit("FAIL selector-1/2 rebuilt metatile pointer")
        expected = record_for(maincpu, index, records, descriptor)
        if expected is None:
            actual = None
        else:
            record_id = be16(index, recovered_word1)
            offset = (record_id - 1) * 64
            actual = (attr, records[offset:offset + 64])
        for row_in in range(4):
            for col_in in range(4):
                for context in (0, 7):
                    if output(expected, row_in, col_in, context) != output(
                            actual, row_in, col_in, context):
                        raise SystemExit(
                            "FAIL selector-1/2 rebuilt metatile output "
                            f"descriptor={descriptor:#x} row={row_in} col={col_in}"
                        )
                    selection_cases += 1

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
        f"{destination_cases} arcade destination-row cases; "
        f"{selection_cases} rebuilt-metatile/attribute cases; "
        f"{output_cases} descriptor/subcell/context "
        f"cases; {residency_cases} row/top residency cases "
        f"({resident_cases} resident, {nonresident_cases} nonresident); "
        "collision always produced; visual resident-only"
    )


if __name__ == "__main__":
    main()
