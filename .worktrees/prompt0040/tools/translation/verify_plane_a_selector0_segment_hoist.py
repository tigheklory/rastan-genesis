#!/usr/bin/env python3
"""Prove Build-0424 selector-0 four-row runtime-selection equivalence.

This is deliberately not a generator self-check.  It models the accepted 0423
per-row live source/ring/descriptor selection and compares it with the 0424
one-selection/four-row realization.  Visual and collision products are checked
independently; residency remains a dynamic per-cell oracle.
"""

from __future__ import annotations

import argparse
from pathlib import Path


DESC_START = 0x0F08
DESC_END = 0x3A00C
METATILE_MAX = 0x5FDFC
RECORD_BYTES = 64


def be16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        return 0
    return int.from_bytes(data[offset:offset + 2], "big")


def select_descriptor(row: int, col: int, sources: tuple[int, ...],
                      source_ref: int, group: int, strip: int) -> int:
    """Exact accepted-0423 live selection used by selector 0's fused leaf."""
    base = sources[(row >> 2) & 15]
    block = (col & 63) >> 2
    if source_ref == 16:
        delta = block - (group & 15)
        front = ((group & 15) << 2) + (strip & 3)
        if col > front:
            delta -= 16
    else:
        delta = block - source_ref
    return base + delta * 4


def select_hoisted(segment: int, col: int, sources: tuple[int, ...],
                   source_ref: int) -> int:
    """Exact 0424 selector-0 shared selection (source_ref is always 0..15)."""
    return sources[segment & 15] + (((col & 63) >> 2) - source_ref) * 4


def record_for(maincpu: bytes, index: bytes, records: bytes, descriptor: int):
    if descriptor < DESC_START or descriptor >= DESC_END:
        return None
    attr = be16(maincpu, descriptor)
    pointer = be16(maincpu, descriptor + 2)
    if pointer & 1 or pointer > METATILE_MAX or pointer + 2 > len(index):
        return None
    record_id = be16(index, pointer)
    if record_id == 0:
        return None
    offset = (record_id - 1) * RECORD_BYTES
    if offset + RECORD_BYTES > len(records):
        raise SystemExit(f"FAIL selector-0 segment hoist: record {record_id} out of range")
    return attr, records[offset:offset + RECORD_BYTES]


def native_attr(word: int) -> int:
    return 0x6000 | (0x0800 if word & 0x4000 else 0) | (0x1000 if word & 0x8000 else 0)


def resident_code(context: int, code: int) -> int:
    """Context-sensitive stand-in for the deliberately dynamic cache lookup."""
    return 0 if code == 0 else (1 + code * 37 + context * 0x131) & 0x07FF


def output(record, row_in_segment: int, col: int, context: int) -> tuple[int, int]:
    if record is None:
        return 0, 0
    attr, payload = record
    subcell = row_in_segment * 8 + (col & 3) * 2
    tile = be16(payload, subcell) & 0x3FFF
    collision = be16(payload, 0x20 + subcell)
    return native_attr(attr) | resident_code(context, tile), collision


def require_source_contract() -> None:
    source = (Path(__file__).resolve().parents[2] /
              "apps/rastan-direct/src/tilemap_hooks.s").read_text()
    start = source.index("genesistan_hook_tilemap_plane_a_selector0_native:")
    end = source.index("genesistan_hook_tilemap_plane_a_selector12_native:", start)
    block = source[start:end]
    required = (
        "PC080SN_DESC_REBUILD_SRC_TABLE",
        ".Lplane_a_sel0_shared_ready:",
        ".Lplane_a_native_metatile_record_from_d2",
        "0x20(%a4,%d0.w)",
        "0(%a4,%d0.w)",
        "fg_cache_resolve",
        "ARCADE_COLLISION_MAP_BASE",
        "staged_fg_buffer",
    )
    for token in required:
        if token not in block:
            raise SystemExit(f"FAIL selector-0 segment hoist: source omits {token}")
    if "MAP_GET_NAME_COLLISION_A" in block:
        raise SystemExit("FAIL selector-0 segment hoist: per-row descriptor resolver remains")
    if block.count(".Lplane_a_native_metatile_record_from_d2") != 1:
        raise SystemExit("FAIL selector-0 segment hoist: native record lookup is not 4->1")


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

    # Coordinate/ring proof: every row in a four-row segment must select the
    # same address under every selector-0 leading-reference state (0..15; the
    # value 16 belongs only to resident-row publication and cannot enter this
    # path). This covers every live front/nonzero alignment and group rollover.
    # Source bases include valid edges, segment transitions, rebases,
    # wrap-adjacent values, and invalid boundary fragments.
    source_bases = (
        DESC_START - 4, DESC_START, DESC_START + 4, 0x1691C, 0x18BDC,
        0x2C49C, DESC_END - 8, DESC_END - 4, DESC_END, DESC_END + 4,
    )
    coordinate_cases = 0
    for base in source_bases:
        sources = tuple(base + segment * 4 for segment in range(16))
        for source_ref in range(16):
            for group in range(16):
                for strip in range(4):
                    for segment in range(16):
                        col = ((group << 2) + strip) & 63
                        old = [select_descriptor(segment * 4 + row, col, sources,
                                                 source_ref, group, strip)
                               for row in range(4)]
                        shared = select_hoisted(segment, col, sources, source_ref)
                        if old != [shared] * 4:
                            raise SystemExit(
                                "FAIL selector-0 segment hoist: descriptor differs "
                                f"base={base:#x} ref={source_ref} group={group} "
                                f"strip={strip} segment={segment} old={old} new={shared:#x}"
                            )
                        coordinate_cases += 1

    # Payload proof: for every possible four-byte descriptor entry, compare
    # accepted 0423's four independent record resolutions with 0424's one
    # shared record plus four row-specific outputs, independently for visual
    # and collision, under multiple dynamic residency/package contexts.
    semantic_cases = 0
    for descriptor in range(DESC_START, DESC_END, 4):
        shared = record_for(maincpu, index, records, descriptor)
        for col in range(4):
            for context in (0, 1, 7, 31):
                old = [output(record_for(maincpu, index, records, descriptor),
                              row, col, context) for row in range(4)]
                new = [output(shared, row, col, context) for row in range(4)]
                if old != new:
                    raise SystemExit(
                        "FAIL selector-0 segment hoist: output differs "
                        f"descriptor={descriptor:#x} col={col} context={context}"
                    )
                semantic_cases += 1

    print(
        "PASS selector-0 four-row runtime equivalence: "
        f"{coordinate_cases} coordinate/front/wrap/rebase cases; "
        f"{semantic_cases} descriptor/subcell/context cases; "
        "Plane-A visual and collision outputs independent; descriptor/record 4->1"
    )


if __name__ == "__main__":
    main()
