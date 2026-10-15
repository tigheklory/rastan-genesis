#!/usr/bin/env python3
"""Exhaustively verify generated native metatile records against maincpu."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gen_pc080sn_native_metatiles import MAX_POINTER, RECORD_BYTES, record_for


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    maincpu = args.maincpu.read_bytes()
    index = args.index.read_bytes()
    records = args.records.read_bytes()
    report = json.loads(args.report.read_text())

    if len(index) != MAX_POINTER + 2:
        raise SystemExit(f"FAIL native metatile index size {len(index)}")
    expected_count = report["record_count"]
    if len(records) != expected_count * RECORD_BYTES:
        raise SystemExit("FAIL native metatile record size/count")

    seen: set[int] = set()
    for pointer in range(0, MAX_POINTER + 1, 2):
        record_id = int.from_bytes(index[pointer:pointer + 2], "big")
        if not record_id:
            continue
        if record_id > expected_count or record_id in seen:
            raise SystemExit(f"FAIL native metatile id {record_id} at {pointer:#x}")
        seen.add(record_id)
        begin = (record_id - 1) * RECORD_BYTES
        if records[begin:begin + RECORD_BYTES] != record_for(maincpu, pointer):
            raise SystemExit(f"FAIL native metatile mismatch at {pointer:#x}")

    if len(seen) != expected_count:
        raise SystemExit(f"FAIL indexed {len(seen)} records, expected {expected_count}")
    print(
        "PASS native PC080SN metatiles: "
        f"{expected_count} records; all tile and collision words exact"
    )


if __name__ == "__main__":
    main()
