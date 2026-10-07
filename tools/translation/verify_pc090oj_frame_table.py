#!/usr/bin/env python3
"""Independent Layer-2 verifier for native player and generic frames."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRAMES, WEAPONS, ORIENTATIONS = 75, 5, 2
BODY = 0x05BD40
WEAPON_TABLE = {1: 0x05CD8A, 2: 0x05D346, 3: 0x05D666}
COMPOSITOR_TABLE = {0: 0x03D09E, 1: 0x04771C, 2: 0x03F0CE,
                    3: 0x040004, 4: 0x04002C}
VARIANT_MARK = 0x2000
ATTR_OVERRIDE, ATTR_EMBEDDED = 1, 2
GENERIC = (
    ("cave_block", 0x0179, range(0x70, 0x71), 0, 0x3C, 0x05, 0x1E, ATTR_EMBEDDED),
    ("burst", 0x0275, range(0x9E, 0xA1), 0, 0x30, 0x05, 0x0F, ATTR_EMBEDDED),
    ("lizardman", 0x004B, range(0x17, 0x20), 0, 0x36, 0x3E, 0x00, ATTR_OVERRIDE),
    ("large_bat", 0x03F6, range(0xB6, 0xB9), 0, 0x3E, 0x06, 0x0A, ATTR_EMBEDDED),
    ("small_bat", 0x0268, range(0xB9, 0xBC), 0, 0x3E, 0x06, 0x0B, ATTR_EMBEDDED),
)
PROGRAMS = {
    ("cave_block", 0x70): (0x03E1C0, 4),
    ("burst", 0x9E): (0x03E732, 8), ("burst", 0x9F): (0x03E753, 9),
    ("burst", 0xA0): (0x03E778, 10),
    ("lizardman", 0x17): (0x03D5EB, 8), ("lizardman", 0x18): (0x03D60C, 8),
    ("lizardman", 0x19): (0x03D62D, 8), ("lizardman", 0x1A): (0x03D64E, 8),
    ("lizardman", 0x1B): (0x03D66F, 8), ("lizardman", 0x1C): (0x03D690, 10),
    ("lizardman", 0x1D): (0x03D6B9, 8), ("lizardman", 0x1E): (0x03D6DA, 8),
    ("lizardman", 0x1F): (0x03D6FB, 10),
    ("large_bat", 0xB6): (0x03E932, 4), ("large_bat", 0xB7): (0x03E943, 2),
    ("large_bat", 0xB8): (0x03E94C, 4),
    ("small_bat", 0xB9): (0x03E95D, 1), ("small_bat", 0xBA): (0x03E962, 1),
    ("small_bat", 0xBB): (0x03E967, 1),
}


def signed_word(blob: bytes, at: int) -> int:
    return int.from_bytes(blob[at:at + 2], "big", signed=True)


def signed_byte(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def expected_generic(blob: bytes, spec: tuple, anim: int, orientation: int,
                     variants: dict[tuple[int, int], int]):
    usage, base, _selectors, compositor, bank, _disc_off, _disc_val, _attr_policy = spec
    wanted_program, count = PROGRAMS[(usage, anim)]
    root = COMPOSITOR_TABLE[compositor]
    cursor = root + int.from_bytes(blob[root + anim * 2:root + anim * 2 + 2], "big")
    if cursor != wanted_program:
        raise SystemExit(f"{usage} independent program mismatch")
    result = []
    for _ in range(count):
        control = blob[cursor]
        mode = control & 0xF0
        if control == 0xFF or mode not in (0x00, 0x40, 0x70, 0x80):
            raise SystemExit(f"{usage} independent general-program decode failed")
        y = signed_byte(blob[cursor + 1])
        delta = blob[cursor + 2]
        x = signed_byte(blob[cursor + 3])
        cursor += 4
        source_code = base + (-delta if mode == 0x40 else delta)
        attr = control
        flags = 0
        if orientation:
            x = -x - 16
            attr |= 0x4000
        elif mode == 0x80:
            attr |= 0x4000
        if not orientation and mode == 0x70:
            flags |= 4
        vi = variants.get((source_code, bank))
        finalized = source_code if vi is None else VARIANT_MARK | vi
        if vi is not None:
            flags |= 2
        result.append((x, y, finalized, attr, 5, flags))
    if blob[cursor] != 0xFF:
        raise SystemExit(f"{usage} independent piece-count/terminator mismatch")
    return result


def decode_four(blob: bytes, root: int, selector: int):
    cursor = root + signed_word(blob, root + selector * 2)
    result = []
    for _ in range(4):
        code = int.from_bytes(blob[cursor:cursor + 2], "big")
        if code == 0:
            continue
        x = int.from_bytes(blob[cursor + 2:cursor + 3], "big", signed=True)
        y = int.from_bytes(blob[cursor + 3:cursor + 4], "big", signed=True)
        attr = int.from_bytes(blob[cursor + 4:cursor + 6], "big")
        result.append((code, x, y, attr))
        cursor += 6
    return result


def expected(blob: bytes, frame: int, weapon: int, orientation: int):
    pieces = decode_four(blob, BODY, frame)
    body_count = len(pieces)
    if weapon:
        pieces += decode_four(blob, WEAPON_TABLE[weapon], frame)
    out = []
    for n, (code, x, y, attr) in enumerate(pieces):
        if orientation:
            x = -x - 16
            attr |= 0x4000
        flags = 1 if weapon and n == body_count else 0
        out.append((x, y + 1, code, attr, 5, flags))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maincpu", default=ROOT / "build/regions/maincpu.bin", type=Path)
    ap.add_argument("--variant-index", default=ROOT / "build/regions/pc090oj_variant_index.json", type=Path)
    ap.add_argument("--table", default=ROOT / "build/pc090oj_frame_table.bin", type=Path)
    ap.add_argument("--index", default=ROOT / "build/pc090oj_frame_index.bin", type=Path)
    ap.add_argument("--generic-index", default=ROOT / "build/pc090oj_generic_frame_index.bin", type=Path)
    ap.add_argument("--generic-base-lut", default=ROOT / "build/pc090oj_generic_base_lut.bin", type=Path)
    ap.add_argument("--generic-usage", default=ROOT / "build/pc090oj_generic_usage_table.bin", type=Path)
    ap.add_argument("--residency", default=ROOT / "build/pc090oj_frame_residency.bin", type=Path)
    ap.add_argument("--coverage", default=ROOT / "build/pc090oj_frame_table.coverage.json", type=Path)
    a = ap.parse_args()
    rom, table, index = a.maincpu.read_bytes(), a.table.read_bytes(), a.index.read_bytes()
    generic_index = a.generic_index.read_bytes()
    generic_base_lut = a.generic_base_lut.read_bytes()
    generic_usage = a.generic_usage.read_bytes()
    if len(index) != FRAMES * WEAPONS * ORIENTATIONS * 6:
        raise SystemExit(f"bad index size {len(index)}")
    variant_json = json.loads(a.variant_index.read_text())
    divergent = {int(x, 16) for x in variant_json["group_base"]}
    variants = {(int(v["code"], 16), int(v["bank"], 16)): int(v["vi"])
                for v in variant_json["variants"]}
    native = unresolved = 0
    expected_residency = {}
    for frame in range(FRAMES):
        for weapon in range(WEAPONS):
            for orientation in range(ORIENTATIONS):
                k = ((frame * WEAPONS + weapon) * ORIENTATIONS) + orientation
                off, count, status = struct.unpack_from(">IBB", index, k * 6)
                if weapon == 4:
                    if (off, count, status) != (0xFFFFFFFF, 0xFF, 0):
                        raise SystemExit(f"fire-sword key {k} is not explicit UNRESOLVED")
                    unresolved += 1
                    continue
                want = expected(rom, frame, weapon, orientation)
                if status != 1 or count != len(want) or off + count * 10 > len(table):
                    raise SystemExit(f"bad native index key {k}: {(off, count, status)}")
                got = [struct.unpack_from(">hhHHBB", table, off + i * 10) for i in range(count)]
                if got != want:
                    raise SystemExit(f"frame mismatch key {k}: got={got!r} want={want!r}")
                bad = sorted({p[2] for p in got} & divergent)
                if bad:
                    raise SystemExit(f"key {k} bakes non-finalized divergent codes {bad}")
                expected_residency[k] = sorted({p[2] for p in got})
                native += 1

    generic_record_count = sum(len(list(spec[2])) for spec in GENERIC) * ORIENTATIONS
    if len(generic_index) != generic_record_count * 6:
        raise SystemExit(f"bad generic index size {len(generic_index)}")
    if len(generic_base_lut) != 0x1000 or len(generic_usage) != len(GENERIC) * 10:
        raise SystemExit("bad generic direct-dispatch metadata size")
    generic_native = 0
    next_record = 0
    for usage_id, spec in enumerate(GENERIC, 1):
        usage, base, selectors_range, compositor, bank, disc_off, disc_val, attr_policy = spec
        selectors = list(selectors_range)
        if generic_base_lut[base] != usage_id:
            raise SystemExit(f"bad base-LUT route for {usage}")
        desc = struct.unpack_from(">BBBBBBBBH", generic_usage, (usage_id - 1) * 10)
        if desc != (disc_off, disc_val, selectors[0], len(selectors), compositor, bank,
                    attr_policy, 0, next_record):
            raise SystemExit(f"bad usage descriptor for {usage}: {desc!r}")
        for anim in selectors:
            for orientation in range(ORIENTATIONS):
                record = next_record + (anim - selectors[0]) * 2 + orientation
                off, count, status = struct.unpack_from(">IBB", generic_index, record * 6)
                if status != 1:
                    raise SystemExit(f"generic direct index unexpectedly unresolved {record}")
                want = expected_generic(rom, spec, anim, orientation, variants)
                if count != len(want) or off + count * 10 > len(table):
                    raise SystemExit(f"bad generic payload bounds {record}")
                got = [struct.unpack_from(">hhHHBB", table, off + i * 10)
                       for i in range(count)]
                if got != want:
                    raise SystemExit(f"generic frame mismatch {usage}/{anim:02x}/{orientation}")
                # Effective-bank identity is independently tied to the exact source
                # program nibble plus the proven bank high bits. Every divergent
                # source must have the canonical offline (code,bank)->vi mapping.
                for piece in got:
                    finalized, attr, flags = piece[2], piece[3], piece[5]
                    if attr_policy == ATTR_EMBEDDED and (attr & 0x0F) != (bank & 0x0F):
                        raise SystemExit(f"generic low-bank mismatch {record}")
                    if attr_policy == ATTR_OVERRIDE and (attr & 0x0F) == (bank & 0x0F):
                        raise SystemExit(
                            f"generic override test is not independent of embedded attr {record}")
                    if flags & 2:
                        if not finalized & VARIANT_MARK:
                            raise SystemExit(f"generic variant not finalized {record}")
                    elif (finalized & 0x0FFF) in divergent:
                        raise SystemExit(f"generic divergent source lacks finalized vi {record}")
                residency_key = FRAMES * WEAPONS * ORIENTATIONS + record
                expected_residency[residency_key] = sorted({p[2] for p in got})
                generic_native += 1
        next_record += len(selectors) * ORIENTATIONS

    routed_bases = {spec[1] for spec in GENERIC}
    if any(value for base, value in enumerate(generic_base_lut) if base not in routed_bases):
        raise SystemExit("base LUT contains an undeclared native route")

    residency = a.residency.read_bytes()
    magic, version, records = struct.unpack_from(">4sHH", residency)
    total_records = FRAMES * WEAPONS * ORIENTATIONS + generic_record_count
    if (magic, version, records) != (b"P9RS", 2, total_records):
        raise SystemExit("bad residency header")
    for k in range(records):
        off, count, lo, hi = struct.unpack_from(">IHHH", residency, 8 + k * 10)
        if k not in expected_residency:
            if (off, count, lo, hi) != (0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFFFF):
                raise SystemExit(f"UNRESOLVED residency record {k} is populated")
            continue
        got = [struct.unpack_from(">H", residency, off + i * 2)[0] for i in range(count)]
        want = expected_residency[k]
        if got != want or lo != min(want) or hi != max(want):
            raise SystemExit(f"bad residency record {k}")
    coverage = json.loads(a.coverage.read_text())
    if coverage["native"]["entry_count"] != native or coverage["unresolved"]["entry_count"] != unresolved:
        raise SystemExit("coverage JSON counts disagree with verified index")
    if len(coverage["generic_native"]) != generic_native:
        raise SystemExit("coverage JSON generic count disagrees with verified index")
    print(f"PASS pc090oj frame table: {native} player native, {generic_native} generic native, "
          f"{unresolved} player UNRESOLVED")


if __name__ == "__main__":
    main()
