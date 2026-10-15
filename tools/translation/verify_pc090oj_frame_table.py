#!/usr/bin/env python3
"""Independent Layer-2 verifier for native player and generic frames."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRAMES, PLAYER_VARIANTS, ORIENTATIONS = 75, 8, 2
SECONDARY_FRAMES, SECONDARY_PHASES = 52, 4
BODY = 0x05BD40
SECONDARY = 0x05C466
WEAPON_TABLE = {1: 0x05CD8A, 2: 0x05D346, 3: 0x05D666, 4: 0x05D068}
FIRE_SUBSTITUTIONS = {0x046E: 0x054688, 0x046F: 0x054690,
                      0x047B: 0x054698, 0x047C: 0x0546A0}
COMPOSITOR_TABLE = {0: 0x03D09E, 1: 0x04771C, 2: 0x03F0CE,
                    3: 0x040004, 4: 0x04002C}
COMPOSITOR_SELECTOR_COUNTS = {0: 253, 1: 246, 2: 131, 3: 167, 4: 167}
INVALID_SPECIAL_SELECTORS = {(3, 0x36), (3, 0x37), (4, 0x91)}
VARIANT_MARK = 0x2000
DIRECT_MARK = 0x1000
ATTR_OVERRIDE, ATTR_EMBEDDED = 1, 2
STATUS_NATIVE, STATUS_SPECIAL = 1, 2
F_YADJ, F_DYNAMIC = 4, 8
F_COND_TRUE, F_COND_FALSE, F_M10_OVERRIDE, F_M10_PLUS1 = 0x10, 0x20, 0x40, 0x80
SPECIAL_DATA = {
    (0x10, 0x03CE30): (32, set(range(32))),
    (0x20, 0x03CD40): (40, set(range(40))),
    (0x30, 0x03CC20): (32, set(range(32))),
    (0x50, 0x03CBF8): (33, set(range(8)) | {0x20}),
    (0x60, 0x03CBF8): (33, set(range(8)) | {0x20}),
    (0x90, 0x03CB18): (32, set(range(32))),
    (0xA0, 0x03CB00): (24, set(range(24))),
    (0xB0, 0x03CABC): (17, set(range(17))),
    (0xC0, 0x03CA38): (22, set(range(22))),
    (0xC0, 0x03CA7A): (22, set(range(22))),
}
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
    cursor = root + signed_word(blob, root + anim * 2)
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
        finalized = DIRECT_MARK | source_code if vi is None else VARIANT_MARK | vi
        if vi is not None:
            flags |= 2
        result.append((x, y, finalized, attr, 5, flags))
    if blob[cursor] != 0xFF:
        raise SystemExit(f"{usage} independent piece-count/terminator mismatch")
    return result


def expected_universal(blob: bytes, compositor: int, anim: int, orientation: int):
    if not 0 <= anim < COMPOSITOR_SELECTOR_COUNTS[compositor]:
        return None
    root = COMPOSITOR_TABLE[compositor]
    cursor = root + signed_word(blob, root + anim * 2)
    if (blob[cursor] & 0xF0) in {key[0] for key in SPECIAL_DATA}:
        return None
    result = []
    for _ in range(20):
        control = blob[cursor]
        cursor += 1
        if control == 0xFF:
            return result
        mode = control & 0xF0
        y = signed_byte(blob[cursor])
        delta = blob[cursor + 1]
        x = signed_byte(blob[cursor + 2])
        cursor += 3
        code_delta = -delta if mode == 0x40 else delta
        attr = 0x4000 if (orientation or (not orientation and mode == 0x80)) else 0
        flags = 8
        if orientation:
            x = -x - 16
        elif mode == 0x70:
            flags |= 4
        result.append((x, y, code_delta & 0xFFFF, attr, 5, flags))
    return result


def special_descriptor(blob: bytes, compositor: int, anim: int):
    if not 0 <= anim < COMPOSITOR_SELECTOR_COUNTS[compositor]:
        return None
    root = COMPOSITOR_TABLE[compositor]
    desc = root + signed_word(blob, root + anim * 2)
    mode = blob[desc] & 0xF0
    pointer = int.from_bytes(blob[desc + 2:desc + 6], "big")
    return (mode, pointer) if (mode, pointer) in SPECIAL_DATA else None


def sp(seed, dx, dy, flags=0):
    return (dx, dy, seed[2], seed[3], seed[4], (seed[5] & ~F_YADJ) | flags)


def expected_special(blob: bytes, compositor: int, anim: int,
                     orientation: int, subframe: int):
    spec = special_descriptor(blob, compositor, anim)
    if spec is None or anim == 0 or subframe not in SPECIAL_DATA[spec][1]:
        return None
    mode, pointer = spec
    seed = expected_universal(blob, compositor, anim - 1, orientation)
    if seed is None:
        return None
    if mode in (0x50, 0x60) and subframe == 0x20:
        return []
    b = lambda at: signed_byte(blob[at])
    out = []
    if mode in (0x50, 0x60):
        if len(seed) != (8 if mode == 0x50 else 10): return None
        vals = [b(pointer + subframe * 5 + i) for i in range(5)]
        vals = vals[:4] if mode == 0x50 else vals
        for dx in (0, -16):
            for value in vals: out.append(sp(seed[len(out)], dx, value, F_YADJ))
    elif mode == 0xA0:
        if len(seed) != 4: return None
        x = b(pointer + subframe)
        out = [sp(seed[i], x + i * 16, 0) for i in range(4)]
    elif mode == 0xC0:
        if len(seed) != 8: return None
        vals = [b(pointer + subframe * 3 + i) for i in range(3)]
        if anim == 6:
            geo = [(0, 0, -1)] + [(vals[i], 0, i) for i in range(3)] + [(0, -16, -1)] + [(vals[i], -16, i) for i in range(3)]
        else:
            geo = [(vals[i], 0, i) for i in range(3)] + [(0, 0, -1)] + [(vals[i], -16, i) for i in range(3)] + [(0, -16, -1)]
        out = [sp(seed[i], x, y) for i, (x, y, src) in enumerate(geo)
               if src < 0 or vals[src] != -1]
    elif mode == 0xB0:
        if len(seed) != 6: return None
        vals = [b(pointer + subframe * 4 + i) for i in range(4)]
        out = [sp(seed[0], 0, 0, F_COND_TRUE), sp(seed[1], -16, 0, F_COND_TRUE)]
        for i, (x, y) in enumerate(((0, vals[0]), (0, vals[1]), (-16, vals[2]), (-16, vals[3]))):
            if y != -1:
                out += [sp(seed[i], x, y, F_COND_FALSE), sp(seed[i + 2], x, y, F_COND_TRUE)]
    elif mode == 0x30:
        if len(seed) != 9: return None
        vals = [b(pointer + subframe * 9 + i) for i in range(9)]
        geo = [(vals[i], -48 + i * 16) for i in range(6)] + [(vals[i], -48) for i in range(6, 9)]
        out = [sp(seed[i], x, y) for i, (x, y) in enumerate(geo) if x != 0]
    elif mode == 0x90:
        if len(seed) != 8: return None
        vals = [b(pointer + subframe * 7 + i) for i in range(7)]
        out = [sp(seed[0], -8, -16)]
        out += [sp(seed[i], x, y) for i, (x, y) in enumerate(zip((-8, 0, -16, -8, -8, -8, -8), vals), 1) if y != -1]
    elif mode == 0x20:
        if len(seed) != 10: return None
        out = [sp(seed[i], *xy) for i, xy in enumerate(((0, -32), (0, -48), (-16, -32), (-16, -48)))]
        vals = [b(pointer + subframe * 6 + i) for i in range(6)]
        out += [sp(seed[i], -8, y) for i, y in enumerate(vals, 4) if y != -1]
    elif mode == 0x10:
        vals = [b(pointer + subframe * 4 + i) for i in range(4)]
        if compositor == 0:
            if len(seed) != 10: return None
            for base, x, plus in ((0, -8, F_M10_PLUS1), (5, -24, 0)):
                out.append(sp(seed[base], x, 0, F_M10_OVERRIDE | plus))
                out += [sp(seed[i], x, y) for i, y in enumerate(vals, base + 1) if y != 0]
        else:
            if len(seed) != 8: return None
            out = [sp(seed[0], 0, 0), sp(seed[1], -16, 0)]
            geo = [(-8, vals[0]), (-8, vals[1]), (-16, vals[2]), (-16, vals[3]), (0, vals[2]), (0, vals[3])]
            out += [sp(seed[i], x, y) for i, (x, y) in enumerate(geo, 2) if y != 0]
    else:
        return None
    return out


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


def expected(blob: bytes, frame: int, player_variant: int, orientation: int):
    pieces = decode_four(blob, BODY, frame)
    body_count = len(pieces)
    if player_variant:
        weapon = min(player_variant, 4)
        extra = decode_four(blob, WEAPON_TABLE[weapon], frame)
        if weapon == 4:
            phase = player_variant - 4
            extra = [(int.from_bytes(blob[FIRE_SUBSTITUTIONS[code] + phase * 2:
                                            FIRE_SUBSTITUTIONS[code] + phase * 2 + 2], "big")
                      if code in FIRE_SUBSTITUTIONS else code, x, y, attr)
                     for code, x, y, attr in extra]
        pieces += extra
    out = []
    for n, (code, x, y, attr) in enumerate(pieces):
        if orientation:
            x = -x - 16
            attr |= 0x4000
        flags = 1 if player_variant and n == body_count else 0
        out.append((x, y + 1, DIRECT_MARK | code, attr, 5, flags))
    return out


def expected_secondary(blob: bytes, frame: int, phase: int, orientation: int):
    pieces = decode_four(blob, SECONDARY, frame)
    out = []
    for code, x, y, attr in pieces:
        if code in FIRE_SUBSTITUTIONS:
            at = FIRE_SUBSTITUTIONS[code] + phase * 2
            code = int.from_bytes(blob[at:at + 2], "big")
        if orientation:
            x = -x - 16
            attr |= 0x4000
        out.append((x, y + 1, DIRECT_MARK | code, attr, 5, 0))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maincpu", default=ROOT / "build/regions/maincpu.bin", type=Path)
    ap.add_argument("--variant-index", default=ROOT / "build/regions/pc090oj_variant_index.json", type=Path)
    ap.add_argument("--table", default=ROOT / "build/pc090oj_frame_table.bin", type=Path)
    ap.add_argument("--index", default=ROOT / "build/pc090oj_frame_index.bin", type=Path)
    ap.add_argument("--secondary-index", default=ROOT / "build/pc090oj_secondary_frame_index.bin", type=Path)
    ap.add_argument("--generic-index", default=ROOT / "build/pc090oj_generic_frame_index.bin", type=Path)
    ap.add_argument("--generic-table", default=ROOT / "build/pc090oj_generic_piece_table.bin", type=Path)
    ap.add_argument("--universal-index", default=ROOT / "build/pc090oj_universal_frame_index.bin", type=Path)
    ap.add_argument("--special-index", default=ROOT / "build/pc090oj_special_frame_index.bin", type=Path)
    ap.add_argument("--generic-base-lut", default=ROOT / "build/pc090oj_generic_base_lut.bin", type=Path)
    ap.add_argument("--generic-usage", default=ROOT / "build/pc090oj_generic_usage_table.bin", type=Path)
    ap.add_argument("--residency", default=ROOT / "build/pc090oj_frame_residency.bin", type=Path)
    ap.add_argument("--coverage", default=ROOT / "build/pc090oj_frame_table.coverage.json", type=Path)
    a = ap.parse_args()
    rom, table, index = a.maincpu.read_bytes(), a.table.read_bytes(), a.index.read_bytes()
    secondary_index = a.secondary_index.read_bytes()
    generic_index = a.generic_index.read_bytes()
    generic_table = a.generic_table.read_bytes()
    universal_index = a.universal_index.read_bytes()
    special_index = a.special_index.read_bytes()
    generic_base_lut = a.generic_base_lut.read_bytes()
    generic_usage = a.generic_usage.read_bytes()
    if len(index) != FRAMES * PLAYER_VARIANTS * ORIENTATIONS * 6:
        raise SystemExit(f"bad index size {len(index)}")
    variant_json = json.loads(a.variant_index.read_text())
    divergent = {int(x, 16) for x in variant_json["group_base"]}
    variants = {(int(v["code"], 16), int(v["bank"], 16)): int(v["vi"])
                for v in variant_json["variants"]}
    native = unresolved = 0
    expected_residency = {}
    for frame in range(FRAMES):
        for player_variant in range(PLAYER_VARIANTS):
            for orientation in range(ORIENTATIONS):
                k = ((frame * PLAYER_VARIANTS + player_variant) * ORIENTATIONS) + orientation
                off, count, status = struct.unpack_from(">IBB", index, k * 6)
                want = expected(rom, frame, player_variant, orientation)
                if status != 1 or count != len(want) or off + count * 10 > len(table):
                    raise SystemExit(f"bad native index key {k}: {(off, count, status)}")
                got = [struct.unpack_from(">hhHHBB", table, off + i * 10) for i in range(count)]
                if got != want:
                    raise SystemExit(f"frame mismatch key {k}: got={got!r} want={want!r}")
                bad = sorted({p[2] & 0x0FFF for p in got} & divergent)
                if bad:
                    raise SystemExit(f"key {k} bakes non-finalized divergent codes {bad}")
                if any(not p[2] & DIRECT_MARK for p in got):
                    raise SystemExit(f"key {k} lacks direct-identity marker")
                expected_residency[k] = sorted({p[2] & 0x0FFF for p in got})
                native += 1

    if len(secondary_index) != SECONDARY_FRAMES * SECONDARY_PHASES * ORIENTATIONS * 6:
        raise SystemExit(f"bad secondary index size {len(secondary_index)}")
    secondary_native = 0
    for frame in range(SECONDARY_FRAMES):
        for phase in range(SECONDARY_PHASES):
            for orientation in range(ORIENTATIONS):
                k = ((frame * SECONDARY_PHASES + phase) * ORIENTATIONS) + orientation
                off, count, status = struct.unpack_from(">IBB", secondary_index, k * 6)
                want = expected_secondary(rom, frame, phase, orientation)
                if status != STATUS_NATIVE or count != len(want) or off + count * 10 > len(table):
                    raise SystemExit(f"bad secondary native index key {k}: {(off, count, status)}")
                got = [struct.unpack_from(">hhHHBB", table, off + i * 10)
                       for i in range(count)]
                if got != want:
                    raise SystemExit(
                        f"secondary frame mismatch {frame}/{phase}/{orientation}: "
                        f"got={got!r} want={want!r}")
                if any(not p[2] & DIRECT_MARK for p in got):
                    raise SystemExit(
                        f"secondary frame {frame}/{phase}/{orientation} lacks direct marker")
                secondary_native += 1

    generic_record_count = sum(len(list(spec[2])) for spec in GENERIC) * ORIENTATIONS
    if len(generic_index) != generic_record_count * 8:
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
                off, count, status, frame_attr = struct.unpack_from(">IBBH", generic_index, record * 8)
                if status != 1:
                    raise SystemExit(f"generic direct index unexpectedly unresolved {record}")
                want = expected_generic(rom, spec, anim, orientation, variants)
                if count != len(want) or off + count * 6 > len(generic_table):
                    raise SystemExit(f"bad generic payload bounds {record}")
                got = [struct.unpack_from(">hhH", generic_table, off + i * 6)
                       for i in range(count)]
                compact_want = [(p[0], p[1], p[2]) for p in want]
                if got != compact_want or any(p[3] != frame_attr for p in want):
                    raise SystemExit(f"generic frame mismatch {usage}/{anim:02x}/{orientation}")
                # Effective-bank identity is independently tied to the exact source
                # program nibble plus the proven bank high bits. Every divergent
                # source must have the canonical offline (code,bank)->vi mapping.
                for piece in want:
                    finalized, attr, flags = piece[2], piece[3], piece[5]
                    if piece[4] != 5 or flags & F_YADJ:
                        raise SystemExit(f"generic compact invariant mismatch {record}")
                    if attr_policy == ATTR_EMBEDDED and (attr & 0x0F) != (bank & 0x0F):
                        raise SystemExit(f"generic low-bank mismatch {record}")
                    if attr_policy == ATTR_OVERRIDE and (attr & 0x0F) == (bank & 0x0F):
                        raise SystemExit(
                            f"generic override test is not independent of embedded attr {record}")
                    if flags & 2:
                        if not finalized & VARIANT_MARK:
                            raise SystemExit(f"generic variant not finalized {record}")
                    else:
                        if not finalized & DIRECT_MARK:
                            raise SystemExit(f"generic direct source lacks marker {record}")
                        if (finalized & 0x0FFF) in divergent:
                            raise SystemExit(f"generic divergent source lacks finalized vi {record}")
                residency_key = FRAMES * PLAYER_VARIANTS * ORIENTATIONS + record
                expected_residency[residency_key] = sorted(
                    {(p[2] & 0x0FFF) if p[2] & DIRECT_MARK else p[2] for p in got})
                generic_native += 1
        next_record += len(selectors) * ORIENTATIONS

    routed_bases = {spec[1] for spec in GENERIC}
    if any(value for base, value in enumerate(generic_base_lut) if base not in routed_bases):
        raise SystemExit("base LUT contains an undeclared native route")

    if len(universal_index) != 5 * 256 * ORIENTATIONS * 6:
        raise SystemExit(f"bad universal index size {len(universal_index)}")
    universal_native = universal_special = universal_unresolved = 0
    for compositor in range(5):
        for anim in range(256):
            for orientation in range(ORIENTATIONS):
                record = ((compositor * 256 + anim) * 2) + orientation
                got_index = struct.unpack_from(">IBB", universal_index, record * 6)
                want = expected_universal(rom, compositor, anim, orientation)
                if want is None:
                    spec = special_descriptor(rom, compositor, anim)
                    if spec is not None:
                        first, span, status = got_index
                        if status != STATUS_SPECIAL or span != SPECIAL_DATA[spec][0]:
                            raise SystemExit(f"bad specialized dispatch record {record}")
                        if first + span * 6 > len(special_index):
                            raise SystemExit(f"specialized index bounds {record}")
                        for subframe in range(span):
                            got_special = struct.unpack_from(">IBB", special_index,
                                                             first + subframe * 6)
                            want_special = expected_special(rom, compositor, anim,
                                                            orientation, subframe)
                            if want_special is None:
                                if got_special != (0xFFFFFFFF, 0xFF, 0):
                                    raise SystemExit(f"illegal specialized subframe resolved {record}/{subframe}")
                                continue
                            off, count, substatus = got_special
                            if (substatus != STATUS_NATIVE or count != len(want_special) or
                                    off + count * 10 > len(table)):
                                raise SystemExit(f"bad specialized payload {record}/{subframe}")
                            got = [struct.unpack_from(">hhHHBB", table, off + i * 10)
                                   for i in range(count)]
                            if got != want_special:
                                raise SystemExit(f"specialized frame mismatch {compositor}/{anim:02x}/{orientation}/{subframe}")
                        universal_special += 1
                        continue
                    if got_index != (0xFFFFFFFF, 0xFF, 0):
                        raise SystemExit(f"unproven universal record {record} resolved")
                    universal_unresolved += 1
                    continue
                off, count, status = got_index
                if status != 1 or count != len(want) or off + count * 10 > len(table):
                    raise SystemExit(f"bad universal payload bounds {record}")
                got = [struct.unpack_from(">hhHHBB", table, off + i * 10)
                       for i in range(count)]
                if got != want:
                    raise SystemExit(f"universal frame mismatch {compositor}/{anim:02x}/{orientation}")
                universal_native += 1

    residency = a.residency.read_bytes()
    magic, version, records = struct.unpack_from(">4sHH", residency)
    total_records = FRAMES * PLAYER_VARIANTS * ORIENTATIONS + generic_record_count
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
    sc = coverage["player_secondary"]
    if sc["entry_count"] != secondary_native or sc["unresolved_entry_count"] != 0:
        raise SystemExit("coverage JSON secondary counts disagree with verified index")
    if len(coverage["generic_native"]) != generic_native:
        raise SystemExit("coverage JSON generic count disagrees with verified index")
    uc = coverage["universal_general_dispatch"]
    if (uc["native_records"], uc["special_records"], uc["unresolved_records"]) != (universal_native, universal_special, universal_unresolved):
        raise SystemExit("coverage JSON universal counts disagree with verified index")
    proven_unreachable = ((5 * 256 - sum(COMPOSITOR_SELECTOR_COUNTS.values())) * 2 +
                          len(INVALID_SPECIAL_SELECTORS) * 2)
    if (universal_unresolved != proven_unreachable or
            uc["reachable_unresolved_records"] != 0 or
            uc["proven_unreachable_records"] != proven_unreachable):
        raise SystemExit("universal static reachability classification mismatch")
    print(f"PASS pc090oj frame table: {native} player native, {secondary_native} player secondary native, {generic_native} generic native, "
          f"{unresolved} player UNRESOLVED, {universal_native} universal general native, "
          f"{universal_special} universal specialized native")


if __name__ == "__main__":
    main()
