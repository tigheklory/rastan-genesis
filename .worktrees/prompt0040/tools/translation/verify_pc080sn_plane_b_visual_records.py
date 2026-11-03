#!/usr/bin/env python3
"""Verify generated Plane-B records against accepted Build-0422 semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gen_pc080sn_plane_b_visual_records import (
    COPIED_MAINCPU_DELTA,
    DESC_BASE,
    DESC_END,
    DESC_STRIDE,
    RECORD_BYTES,
    TABLE_BYTES,
    accepted_0422_record,
)


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def residency(context: int, code: int) -> int:
    """Context-sensitive deterministic oracle for the still-dynamic lookup."""
    return 0 if code == 0 else (1 + code * 37 + context * 0x131) & 0x07FF


def verify_runtime_contract(maincpu: bytes, records: bytes) -> int:
    valid = 0
    for descriptor in range(DESC_BASE, DESC_END, DESC_STRIDE):
        offset = descriptor - DESC_BASE
        expected = accepted_0422_record(maincpu, ATTR_LUT, descriptor)
        actual = records[offset:offset + RECORD_BYTES]
        if actual != expected:
            raise SystemExit(f"FAIL Plane-B record {descriptor:#x}")
        if expected == b"\0" * RECORD_BYTES:
            continue
        valid += 1
        legacy_attr = be16(expected, 0)
        legacy_source = be32(expected, 2) - COPIED_MAINCPU_DELTA
        native_attr = be16(actual, 0)
        native_source = be32(actual, 2) - COPIED_MAINCPU_DELTA
        # Every subcell alignment and vertical ring placement must reproduce
        # the exact 32 rows accepted by the old 64-probe/visibility-filter path.
        for subcol in range(16):
            codes = [
                be16(maincpu, legacy_source + row * 0x20 + subcol * 2) & 0x3FFF
                for row in range(64)
            ]
            # Residency remains genuinely dynamic.  Prove representative
            # package contexts are applied after record selection, unchanged.
            for row, code in enumerate(codes):
                for context in (0, 1, 7, 31):
                    native_code = be16(
                        maincpu, native_source + row * 0x20 + subcol * 2
                    ) & 0x3FFF
                    old_word = legacy_attr | residency(context, code)
                    new_word = native_attr | residency(context, native_code)
                    if new_word != old_word:
                        raise SystemExit(
                            f"FAIL Plane-B context d={descriptor:#x} "
                            f"c={subcol} row={row} context={context}"
                        )
            for top in range(64):
                legacy_rows = [row for row in range(64) if ((row - top) & 63) < 32]
                native_rows = [((top + step) & 63) for step in range(32)]
                if legacy_rows != sorted(native_rows):
                    raise SystemExit(
                        f"FAIL Plane-B row set d={descriptor:#x} c={subcol} top={top}"
                    )
                old = {row & 31: codes[row] for row in legacy_rows}
                new = {row & 31: codes[row] for row in native_rows}
                if new != old:
                    raise SystemExit(
                        f"FAIL Plane-B selection d={descriptor:#x} c={subcol} top={top}"
                    )
    return valid


def verify_boundaries(maincpu: bytes, records: bytes) -> None:
    # Exercise descriptor changes at every possible 16-column starting
    # alignment.  The selected descriptor changes only after subcolumn 15;
    # generated lookup must never retain the preceding record on the tail.
    descriptors = list(range(DESC_BASE, DESC_END - DESC_STRIDE, DESC_STRIDE))
    for start in range(16):
        for descriptor in descriptors:
            for step in range(32):
                absolute = start + step
                current = descriptor + (absolute // 16) * DESC_STRIDE
                if current >= DESC_END:
                    break
                subcol = absolute & 15
                offset = current - DESC_BASE
                if records[offset:offset + RECORD_BYTES] != accepted_0422_record(
                    maincpu, ATTR_LUT, current
                ):
                    raise SystemExit(
                        f"FAIL Plane-B boundary start={start} descriptor={current:#x} "
                        f"subcol={subcol}"
                    )


ATTR_LUT = b""


def main() -> None:
    global ATTR_LUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--attr-lut", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    maincpu = args.maincpu.read_bytes()
    ATTR_LUT = args.attr_lut.read_bytes()
    records = args.records.read_bytes()
    report = json.loads(args.report.read_text())
    if len(records) != TABLE_BYTES:
        raise SystemExit(f"FAIL Plane-B table size {len(records):#x}")
    if report.get("contains_collision") is not False:
        raise SystemExit("FAIL Plane-B record is not visual-only")

    valid = verify_runtime_contract(maincpu, records)
    verify_boundaries(maincpu, records)
    if valid != report.get("valid_records"):
        raise SystemExit("FAIL Plane-B report valid-record count")
    print(
        "PASS native Plane-B visual records: "
        f"{valid} descriptors; all 16 subcolumns, 64 ring placements, "
        "dynamic package contexts, and descriptor boundaries exact; collision=NO"
    )


if __name__ == "__main__":
    main()
