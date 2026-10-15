#!/usr/bin/env python3
"""Generate independently addressed visual/collision fields from authoritative maincpu.

The runtime still selects the live descriptor from arcade-owned camera/ring state.
This generator only expands the invariant payload selected by descriptor word 1:
sixteen masked visual identities followed by sixteen independently sourced
collision words. Co-storage does not make either field authoritative for the other.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


DESC_START = 0x0F08
DESC_END = 0x3A00C
MAX_POINTER = 0x5FDFC
RECORD_BYTES = 64


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def record_for(data: bytes, pointer: int) -> bytes:
    tiles = [be16(data, pointer + i * 2) & 0x3FFF for i in range(16)]
    if be16(data, pointer + 0x20) == 0x00FF:
        collisions = [be16(data, pointer + 0x22)] * 16
    else:
        collisions = [be16(data, pointer + 0x20 + i * 2) for i in range(16)]
    return b"".join(value.to_bytes(2, "big") for value in tiles + collisions)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--index-output", type=Path, required=True)
    parser.add_argument("--records-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    args = parser.parse_args()

    data = args.maincpu.read_bytes()
    if len(data) < MAX_POINTER + 0x40:
        raise SystemExit(f"maincpu image too small: {len(data):#x}")

    pointers: set[int] = set()
    descriptor_slots = 0
    for offset in range(DESC_START, DESC_END, 4):
        descriptor_slots += 1
        pointer = be16(data, offset + 2)
        if pointer <= MAX_POINTER and not (pointer & 1):
            pointers.add(pointer)
            # The copied-maincpu contract historically admits descriptor words
            # whose data target has already received the +0x200 copy base.  Keep
            # that accepted value vocabulary explicit rather than guessing at
            # runtime whether the pointer is original-relative or copy-relative.
            if pointer + 0x200 <= MAX_POINTER:
                pointers.add(pointer + 0x200)

    ordered = sorted(pointers)
    if len(ordered) >= 0x10000:
        raise SystemExit(f"record index exceeds 16-bit ids: {len(ordered)}")

    index = bytearray(MAX_POINTER + 2)
    records = bytearray()
    for record_id, pointer in enumerate(ordered, start=1):
        index[pointer:pointer + 2] = record_id.to_bytes(2, "big")
        records.extend(record_for(data, pointer))

    for output in (args.index_output, args.records_output, args.report_output):
        output.parent.mkdir(parents=True, exist_ok=True)
    args.index_output.write_bytes(index)
    args.records_output.write_bytes(records)

    report = {
        "schema": "pc080sn_native_metatile_v1",
        "authority": str(args.maincpu),
        "authority_sha256": hashlib.sha256(data).hexdigest(),
        "descriptor_scan": {
            "start": DESC_START,
            "end_exclusive": DESC_END,
            "stride": 4,
            "slots": descriptor_slots,
        },
        "pointer_max": MAX_POINTER,
        "index_bytes": len(index),
        "record_bytes": RECORD_BYTES,
        "record_count": len(ordered),
        "record_layout": "tile_code_be16[16], collision_be16[16]",
        "pointer_copy_base_aliases_included": True,
        "index_sha256": hashlib.sha256(index).hexdigest(),
        "records_sha256": hashlib.sha256(records).hexdigest(),
    }
    args.report_output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        "PC080SN native metatiles: "
        f"descriptors={descriptor_slots} records={len(ordered)} "
        f"index={len(index)} bytes payload={len(records)} bytes"
    )


if __name__ == "__main__":
    main()
