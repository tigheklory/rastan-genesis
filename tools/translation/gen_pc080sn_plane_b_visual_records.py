#!/usr/bin/env python3
"""Generate visual-only native records for the live Plane-B descriptor table.

The runtime remains authoritative for descriptor selection, subcolumn, scroll,
ring position, scene/package, and residency.  Each six-byte generated record
only replaces invariant interpretation after selection:

    native Genesis attribute word, copied-maincpu tile-block pointer

There is deliberately no collision field or collision-derived input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


DESC_BASE = 0x3951C
DESC_END = 0x3A00C
DESC_STRIDE = 6
SOURCE_MIN = 0x0F08
SOURCE_END = 0x3A00C
COPIED_MAINCPU_DELTA = 0x200
RECORD_BYTES = 6
TABLE_BYTES = ((DESC_END - DESC_BASE + DESC_STRIDE - 1) // DESC_STRIDE) * DESC_STRIDE


def be16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def be32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def attr_key(word: int) -> int:
    return (
        (word & 0x0003)
        | (((word >> 14) & 1) << 2)
        | (((word >> 15) & 1) << 3)
        | (((word >> 13) & 1) << 4)
    )


def accepted_0422_record(maincpu: bytes, attr_lut: bytes, descriptor: int) -> bytes:
    """Reproduce the accepted 0422 descriptor validation and interpretation."""
    attr = be16(maincpu, descriptor)
    source = be32(maincpu, descriptor + 2)
    if source & 1 or not SOURCE_MIN <= source < SOURCE_END:
        return b"\0" * RECORD_BYTES
    key = attr_key(attr)
    native_attr = be16(attr_lut, key * 2)
    # PROMT-ID-0131: gameplay Plane B is the semantic owner of Genesis CRAM Line 2 in EVERY round.
    # The shared attr LUT maps the arcade palette-select field (attr&3) straight into the Genesis
    # palette-line bits (physical bank N -> line N): R1 Plane-B descriptors carry attr&3==2 (-> Line
    # 2, already correct) while R2 descriptors carry attr&3==3 (-> Line 3, the leak Tighe sees on
    # vertically refreshed R2-S1 rows via .Lplane_b_publish_logical_row_native). This Plane-B-specific
    # generated artifact must encode Line 2 for every real tile, independent of the physical arcade
    # bank, so the row/vertical-pan producer matches the other gameplay Plane-B producers. Priority
    # (bit15), V flip (bit12) and H flip (bit11) are preserved from the proven LUT entry; only the
    # palette-line field (bits 14:13) is forced to 2. R1 stays byte-identical because its LUT entry
    # already selects Line 2. The shared LUT itself is NOT modified (it has other owners), and Plane
    # A is untouched.
    native_attr = (native_attr & 0x9FFF) | (0x2 << 13)
    return native_attr.to_bytes(2, "big") + (source + COPIED_MAINCPU_DELTA).to_bytes(4, "big")


def build_records(maincpu: bytes, attr_lut: bytes) -> tuple[bytes, int]:
    records = bytearray()
    valid = 0
    for descriptor in range(DESC_BASE, DESC_END, DESC_STRIDE):
        record = accepted_0422_record(maincpu, attr_lut, descriptor)
        records.extend(record)
        valid += record != b"\0" * RECORD_BYTES
    if len(records) != TABLE_BYTES:
        raise AssertionError((len(records), TABLE_BYTES))
    return bytes(records), valid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maincpu", type=Path, required=True)
    parser.add_argument("--attr-lut", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    maincpu = args.maincpu.read_bytes()
    attr_lut = args.attr_lut.read_bytes()
    if len(maincpu) < DESC_END or len(attr_lut) != 64:
        raise SystemExit("invalid Plane-B generator input size")

    records, valid = build_records(maincpu, attr_lut)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(records)
    report = {
        "schema": "pc080sn_plane_b_visual_record_v1",
        "authority": str(args.maincpu),
        "authority_sha256": hashlib.sha256(maincpu).hexdigest(),
        "attr_lut_sha256": hashlib.sha256(attr_lut).hexdigest(),
        "descriptor_base": DESC_BASE,
        "descriptor_end_exclusive": DESC_END,
        "descriptor_stride": DESC_STRIDE,
        "record_layout": "genesis_attr_be16, copied_maincpu_tile_block_ptr_be32",
        "record_bytes": RECORD_BYTES,
        "table_bytes": len(records),
        "valid_records": valid,
        "contains_collision": False,
        "records_sha256": hashlib.sha256(records).hexdigest(),
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(
        "PC080SN Plane-B visual records: "
        f"valid={valid} bytes={len(records)} collision=NO"
    )


if __name__ == "__main__":
    main()
