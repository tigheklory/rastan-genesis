#!/usr/bin/env python3
"""Verify the bounded generated PC090OJ generic-frame dispatcher."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ATTR_OVERRIDE, ATTR_EMBEDDED = 1, 2
EXPECTED = (
    ("cave_block", 0x0179, 0x70, 1, 0, 0x3C, 0x05, 0x1E, ATTR_EMBEDDED),
    ("burst", 0x0275, 0x9E, 3, 0, 0x30, 0x05, 0x0F, ATTR_EMBEDDED),
    ("lizardman", 0x004B, 0x17, 9, 0, 0x36, 0x3E, 0x00, ATTR_OVERRIDE),
    ("large_bat", 0x03F6, 0xB6, 3, 0, 0x3E, 0x06, 0x0A, ATTR_EMBEDDED),
    ("small_bat", 0x0268, 0xB9, 3, 0, 0x3E, 0x06, 0x0B, ATTR_EMBEDDED),
)


def dispatch(base_lut: bytes, usage_blob: bytes, index: bytes, actor: dict,
             orientation: int) -> int | None:
    base = actor[0x1E]
    if base > 0x0FFF:
        return None
    usage_id = base_lut[base]
    if usage_id == 0:
        return None
    off = (usage_id - 1) * 10
    disc_off, disc_val, first, count, comp, bank, policy, reserved, frame_base = \
        struct.unpack_from(">BBBBBBBBH", usage_blob, off)
    if reserved or actor.get(disc_off) != disc_val or actor[0x38] != comp:
        return None
    override = bool(actor[0x27] & 0x40)
    if override != (policy == ATTR_OVERRIDE):
        return None
    effective_bank = actor["ctrl_high"] | ((actor[0x27] & 0x0F) if override else bank & 0x0F)
    if effective_bank != bank:
        return None
    normalized = actor[0x01] - first
    if normalized < 0 or normalized >= count:
        return None
    record = frame_base + normalized * 2 + orientation
    _table_off, _pieces, status = struct.unpack_from(">IBB", index, record * 6)
    return record if status == 1 else None


def actor_for(spec: tuple) -> dict:
    _name, base, first, _count, comp, bank, disc_off, disc_val, policy = spec
    attr = (0x40 | (bank & 0x0F)) if policy == ATTR_OVERRIDE else 0
    return {0x1E: base, 0x01: first, 0x38: comp, 0x27: attr,
            disc_off: disc_val, "ctrl_high": bank & 0x70}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-lut", default=ROOT / "build/pc090oj_generic_base_lut.bin", type=Path)
    ap.add_argument("--usage", default=ROOT / "build/pc090oj_generic_usage_table.bin", type=Path)
    ap.add_argument("--index", default=ROOT / "build/pc090oj_generic_frame_index.bin", type=Path)
    ap.add_argument("--assembly", default=ROOT / "apps/rastan-direct/src/pc090oj_hooks.s", type=Path)
    args = ap.parse_args()
    base_lut, usage, index = args.base_lut.read_bytes(), args.usage.read_bytes(), args.index.read_bytes()
    if len(base_lut) != 0x1000 or len(usage) != len(EXPECTED) * 10:
        raise SystemExit("FAIL malformed direct-dispatch artifacts")

    next_record = 0
    for usage_id, spec in enumerate(EXPECTED, 1):
        name, base, first, count, comp, bank, disc_off, disc_val, policy = spec
        if base_lut[base] != usage_id:
            raise SystemExit(f"FAIL {name}: wrong base route")
        desc = struct.unpack_from(">BBBBBBBBH", usage, (usage_id - 1) * 10)
        if desc != (disc_off, disc_val, first, count, comp, bank, policy, 0, next_record):
            raise SystemExit(f"FAIL {name}: descriptor mismatch")
        actor = actor_for(spec)
        for selector in range(first, first + count):
            actor[0x01] = selector
            for orientation in (0, 1):
                expected_record = next_record + (selector - first) * 2 + orientation
                if dispatch(base_lut, usage, index, actor, orientation) != expected_record:
                    raise SystemExit(f"FAIL {name}: valid selector/orientation rejected")
        actor = actor_for(spec)
        mutations = (
            ("wrong semantic discriminator", disc_off, disc_val ^ 0xFF),
            ("wrong compositor", 0x38, (comp + 1) & 0xFF),
            ("selector below", 0x01, (first - 1) & 0xFF),
            ("selector above", 0x01, (first + count) & 0xFF),
            ("wrong attribute policy", 0x27, actor[0x27] ^ 0x40),
            ("wrong bank", "ctrl_high", (actor["ctrl_high"] ^ 0x10) & 0x70),
        )
        for label, field, value in mutations:
            bad = dict(actor)
            bad[field] = value
            if dispatch(base_lut, usage, index, bad, 0) is not None:
                raise SystemExit(f"FAIL {name}: {label} did not reject")
        next_record += count * 2

    unknown = {0x1E: 0x0123, 0x01: 0, 0x38: 0, 0x27: 0, "ctrl_high": 0}
    if dispatch(base_lut, usage, index, unknown, 0) is not None:
        raise SystemExit("FAIL UNKNOWN base did not fall back")

    source = args.assembly.read_text()
    start = source.index(".Lnative_generic_frame_try:")
    end = source.index(".Lnative_mapping_branch_is_normal:", start)
    dispatcher = source[start:end]
    forbidden = (".Lngft_find", ".Lngft_next", "dbra")
    if any(token in dispatcher for token in forbidden):
        raise SystemExit("FAIL generic dispatcher still contains a linear record scan")
    for token in ("pc090oj_generic_base_lut", "pc090oj_generic_usage_table",
                  "pc090oj_generic_frame_index"):
        if token not in dispatcher:
            raise SystemExit(f"FAIL dispatcher does not consume {token}")
    print(f"PASS PC090OJ direct dispatch: {len(EXPECTED)} usages, {next_record} direct records; "
          "wrong usage/state/selector/bank/attribute and UNKNOWN all fall back; no linear scan")


if __name__ == "__main__":
    main()
