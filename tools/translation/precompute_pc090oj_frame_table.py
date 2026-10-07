#!/usr/bin/env python3
"""Precompute proven native PC090OJ semantic frames.

The retained player selector at arcade 0x54326 owns A5+0x1244.  The dedicated
compositor at 0x54492 indexes one 75-entry primary-body table and, independently,
one weapon table selected by A5+0x12FA.  This Task-1 pilot resolves weapon values
0 (none), 1 (sword), 2 (axe), and 3 (hammer), for both compositor orientations.
Fire sword (4) is deliberately UNRESOLVED because codes 0x46e/0x46f/0x47b/
0x47c are dynamically substituted from A5+0x1308.

Index entry (6 bytes, big endian): u32 table_offset, u8 piece_count, u8 status.
UNRESOLVED is {0xffffffff, 0xff, 0}.  Native status is 1.
Piece entry (10 bytes): s16 dx, s16 dy, u16 finalized_vi/residency key,
u16 attr, u8 Genesis size, u8 flags.  flags bit0 marks the weapon anchor,
bit1 marks an offline-finalized palette variant, and bit2 requests the retained
actor+0x18 Y adjustment.  Variant pieces store ``0x2000 | vi`` so the accepted
O(1) reverse-residency path consumes the finalized identity directly.

Generic dispatch is O(1) and consists of three generated artifacts:

* a 4096-byte ``base_tile -> usage_id`` LUT (zero means UNRESOLVED);
* one 10-byte descriptor per usage: discriminator offset/value, selector
  minimum/count, compositor, effective bank, attribute policy, reserved byte,
  and first direct-frame-index record;
* a direct 6-byte frame index for every (normalized selector, orientation),
  using the same ``{u32 offset,u8 count,u8 status}`` format as player frames.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRAME_COUNT = 75
WEAPON_COUNT = 5
ORIENTATION_COUNT = 2
INDEX_COUNT = FRAME_COUNT * WEAPON_COUNT * ORIENTATION_COUNT
INDEX_ENTRY_SIZE = 6
PIECE_SIZE = 10
STATUS_NATIVE = 1
SIZE_16X16 = 5
FLAG_WEAPON_ANCHOR = 1
FLAG_FINALIZED_VARIANT = 2
FLAG_ACTOR_Y_ADJUST = 4
VARIANT_KEY_MARK = 0x2000
GENERIC_BASE_LUT_COUNT = 0x1000
USAGE_DESCRIPTOR_SIZE = 10
ATTR_REQUIRE_OVERRIDE = 1
ATTR_REQUIRE_EMBEDDED = 2

BODY_TABLE = 0x05BD40
WEAPON_TABLES = {1: 0x05CD8A, 2: 0x05D346, 3: 0x05D666}
COMPOSITOR_TABLES = {0: 0x03D09E, 1: 0x04771C, 2: 0x03F0CE,
                     3: 0x040004, 4: 0x04002C}

# Static arcade provenance closes these exact retained-state domains.  The
# discriminator is deliberately raw (offset/value) where a stronger semantic
# field name is not proven.  Everything outside these selector ranges remains
# explicit UNRESOLVED fallback.
GENERIC_USAGES = (
    {"usage": "cave_block", "base": 0x0179, "selectors": range(0x70, 0x71),
     "compositor": 0, "bank": 0x3C, "disc_offset": 0x05, "disc_value": 0x1E,
     "attr_policy": ATTR_REQUIRE_EMBEDDED, "residency": "scene/family resident",
     "status": "NATIVE_COMPLETE"},
    {"usage": "burst", "base": 0x0275, "selectors": range(0x9E, 0xA1),
     "compositor": 0, "bank": 0x30, "disc_offset": 0x05, "disc_value": 0x0F,
     "attr_policy": ATTR_REQUIRE_EMBEDDED, "residency": "shared transient",
     "status": "NATIVE_COMPLETE"},
    {"usage": "lizardman", "base": 0x004B, "selectors": range(0x17, 0x20),
     "compositor": 0, "bank": 0x36, "disc_offset": 0x3E, "disc_value": 0x00,
     "attr_policy": ATTR_REQUIRE_OVERRIDE, "residency": "scene/family resident",
     "status": "NATIVE_PARTIAL"},
    {"usage": "large_bat", "base": 0x03F6, "selectors": range(0xB6, 0xB9),
     "compositor": 0, "bank": 0x3E, "disc_offset": 0x06, "disc_value": 0x0A,
     "attr_policy": ATTR_REQUIRE_EMBEDDED, "residency": "shared transient",
     "status": "NATIVE_PARTIAL"},
    {"usage": "small_bat", "base": 0x0268, "selectors": range(0xB9, 0xBC),
     "compositor": 0, "bank": 0x3E, "disc_offset": 0x06, "disc_value": 0x0B,
     "attr_policy": ATTR_REQUIRE_EMBEDDED, "residency": "shared transient",
     "status": "NATIVE_PARTIAL"},
)

PROVEN_PROGRAMS = {
    ("cave_block", 0x70): (0x03E1C0, 4),
    ("burst", 0x9E): (0x03E732, 8),
    ("burst", 0x9F): (0x03E753, 9),
    ("burst", 0xA0): (0x03E778, 10),
    ("lizardman", 0x17): (0x03D5EB, 8),
    ("lizardman", 0x18): (0x03D60C, 8),
    ("lizardman", 0x19): (0x03D62D, 8),
    ("lizardman", 0x1A): (0x03D64E, 8),
    ("lizardman", 0x1B): (0x03D66F, 8),
    ("lizardman", 0x1C): (0x03D690, 10),
    ("lizardman", 0x1D): (0x03D6B9, 8),
    ("lizardman", 0x1E): (0x03D6DA, 8),
    ("lizardman", 0x1F): (0x03D6FB, 10),
    ("large_bat", 0xB6): (0x03E932, 4),
    ("large_bat", 0xB7): (0x03E943, 2),
    ("large_bat", 0xB8): (0x03E94C, 4),
    ("small_bat", 0xB9): (0x03E95D, 1),
    ("small_bat", 0xBA): (0x03E962, 1),
    ("small_bat", 0xBB): (0x03E967, 1),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def s16(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off + 2], "big", signed=True)


def u16(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off + 2], "big")


def s8(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def generic_program_address(data: bytes, anim: int, compositor: int) -> int:
    table = COMPOSITOR_TABLES[compositor]
    return table + u16(data, table + (anim & 0xFF) * 2)


def decode_generic(data: bytes, usage: dict, anim: int, mirrored: bool,
                   finalized_variants: dict[tuple[int, int], int]) -> list[tuple[int, ...]]:
    """Compile the exact general 0x3C902 program for one proven semantic key."""
    cursor = generic_program_address(data, anim, usage["compositor"])
    wanted_program, wanted_count = PROVEN_PROGRAMS[(usage["usage"], anim)]
    if cursor != wanted_program:
        raise SystemExit(f"{usage['usage']} selector/program mismatch: 0x{cursor:06x}")
    out = []
    for _ in range(wanted_count):
        control = data[cursor]
        cursor += 1
        if control == 0xFF:
            raise SystemExit(f"{usage['usage']} terminates before proven piece count")
        mode = control & 0xF0
        if mode not in (0x00, 0x40, 0x70, 0x80):
            raise SystemExit(f"{usage['usage']} uses unresolved mode 0x{mode:02x}")
        dy = s8(data[cursor])
        delta = data[cursor + 1]
        dx = s8(data[cursor + 2])
        cursor += 3
        code = usage["base"] + (-delta if mode == 0x40 else delta)
        attr = control | (0x4000 if mirrored or (not mirrored and mode == 0x80) else 0)
        if mirrored:
            dx = -dx - 16
        flags = 0
        if not mirrored and mode == 0x70:
            flags |= FLAG_ACTOR_Y_ADJUST
        vi = code
        variant = finalized_variants.get((code, usage["bank"]))
        if variant is not None:
            vi = VARIANT_KEY_MARK | variant
            flags |= FLAG_FINALIZED_VARIANT
        out.append((dx, dy, vi, attr, SIZE_16X16, flags))
    if data[cursor] != 0xFF:
        raise SystemExit(f"{usage['usage']} proven piece count does not reach terminator")
    return out


def decode_stream(data: bytes, table: int, selector: int) -> list[tuple[int, int, int, int]]:
    """Reproduce the compositor's sticky-blank four-iteration descriptor loop."""
    pos = table + s16(data, table + selector * 2)
    pieces: list[tuple[int, int, int, int]] = []
    for _ in range(4):
        code = u16(data, pos)
        if code == 0:
            # Original 0x54492 does not advance A0 after a zero descriptor.
            continue
        x = int.from_bytes(data[pos + 2:pos + 3], "big", signed=True)
        y = int.from_bytes(data[pos + 3:pos + 4], "big", signed=True)
        attr = u16(data, pos + 4)
        pieces.append((code, x, y, attr))
        pos += 6
    return pieces


def orient_piece(piece: tuple[int, int, int, int], mirrored: bool) -> tuple[int, int, int, int]:
    code, x, y, attr = piece
    dx = -x - 16 if mirrored else x
    dy = y + 1
    if mirrored:
        attr |= 0x4000
    return dx, dy, code, attr


def key(frame: int, weapon: int, orientation: int) -> int:
    return ((frame * WEAPON_COUNT + weapon) * ORIENTATION_COUNT) + orientation


def load_body_evidence(path: Path) -> dict[int, tuple[list[int], list[int], list[int]]]:
    out = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            slot = int(row["slot"])
            out[slot] = (
                [int(v, 16) for v in row["cells"].split(";") if v],
                [int(v) for v in row["x_offsets"].split(";") if v],
                [int(v) for v in row["y_offsets"].split(";") if v],
            )
    return out


def load_semantic_codes(path: Path) -> dict[str, set[int]]:
    result: dict[str, set[int]] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["valid"] != "Y":
                continue
            result.setdefault(row["object"], set()).add(int(row["cell_code"], 16))
    return result


def validate_generic_evidence(burst_path: Path, manifest_path: Path) -> None:
    with burst_path.open(newline="") as fh:
        rows = [row for row in csv.DictReader(fh, delimiter="\t")
                if row["base"] == "0x0275" and row["program"] != "-"]
    got = {(int(r["anim"], 16), int(r["selector"]), int(r["program"], 16),
            int(r["pieces"]), int(r["child_state"], 16)) for r in rows}
    burst = next(u for u in GENERIC_USAGES if u["usage"] == "burst")
    want = {(anim, burst["compositor"], *PROVEN_PROGRAMS[("burst", anim)],
             burst["disc_value"]) for anim in burst["selectors"]}
    if got != want:
        raise SystemExit(f"burst corpus mismatch: got={got!r} want={want!r}")

    manifest = json.loads(manifest_path.read_text())
    cave = next((actor for actor in manifest["actors"]
                 if actor.get("technical_id") == "hazard_r1_cave_block_0x0179"), None)
    if cave is None:
        raise SystemExit("cave-block semantic actor missing from graphics manifest")
    render = cave["render"]
    cave_tuple = (render["base"], render["anim"], render["compositor_table"],
                  int(cave["live_state"], 16), len(cave["cells"]))
    if cave_tuple != (0x0179, 0x70, 0, 0x1E, 4):
        raise SystemExit(f"cave-block corpus mismatch: {cave_tuple!r}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maincpu", default=ROOT / "build/regions/maincpu.bin", type=Path)
    ap.add_argument("--variant-index", default=ROOT / "build/regions/pc090oj_variant_index.json", type=Path)
    ap.add_argument("--body-evidence", default=ROOT / "analysis/actor_decompilation/h24_player_frame_cells.tsv", type=Path)
    ap.add_argument("--weapon-evidence", default=ROOT / "analysis/actor_decompilation/h24_player_weapon_cells.tsv", type=Path)
    ap.add_argument("--profile", default=ROOT / "build/rastan-direct/build0400/Test.snapshot.json", type=Path)
    ap.add_argument("--palette-decisions", default=ROOT / "specs/palette_decisions.json", type=Path)
    ap.add_argument("--burst-evidence", default=ROOT / "analysis/actor_decompilation/h16_burst_child_render.tsv", type=Path)
    ap.add_argument("--actor-manifest", default=ROOT / "docs/design/rastan_actor_graphics_manifest.json", type=Path)
    ap.add_argument("--enemy-corpus", default=ROOT / "analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv", type=Path)
    ap.add_argument("--table-output", default=ROOT / "build/pc090oj_frame_table.bin", type=Path)
    ap.add_argument("--index-output", default=ROOT / "build/pc090oj_frame_index.bin", type=Path)
    ap.add_argument("--generic-index-output", default=ROOT / "build/pc090oj_generic_frame_index.bin", type=Path)
    ap.add_argument("--generic-base-lut-output", default=ROOT / "build/pc090oj_generic_base_lut.bin", type=Path)
    ap.add_argument("--generic-usage-output", default=ROOT / "build/pc090oj_generic_usage_table.bin", type=Path)
    ap.add_argument("--residency-output", default=ROOT / "build/pc090oj_frame_residency.bin", type=Path)
    ap.add_argument("--report-output", default=ROOT / "build/pc090oj_frame_table.report.txt", type=Path)
    ap.add_argument("--coverage-output", default=ROOT / "build/pc090oj_frame_table.coverage.json", type=Path)
    args = ap.parse_args()

    rom = args.maincpu.read_bytes()
    if len(rom) < 0x05DA60:
        raise SystemExit("maincpu region is too short for proven player tables")
    variants = json.loads(args.variant_index.read_text())
    divergent = {int(code, 16) for code in variants["group_base"]}
    finalized_variants = {
        (int(item["code"], 16), int(item["bank"], 16)): int(item["vi"])
        for item in variants["variants"]
    }
    body_evidence = load_body_evidence(args.body_evidence)
    semantic_codes = load_semantic_codes(args.enemy_corpus)
    validate_generic_evidence(args.burst_evidence, args.actor_manifest)

    body_frames = []
    for frame in range(FRAME_COUNT):
        decoded = decode_stream(rom, BODY_TABLE, frame)
        body_frames.append(decoded)
        expected = body_evidence.get(frame)
        if expected is None:
            raise SystemExit(f"missing body evidence for selector {frame}")
        got = ([p[0] for p in decoded], [p[1] for p in decoded], [p[2] for p in decoded])
        if got != expected:
            raise SystemExit(f"body evidence mismatch selector {frame}: ROM={got}, TSV={expected}")

    weapon_frames = {
        weapon: [decode_stream(rom, table, frame) for frame in range(FRAME_COUNT)]
        for weapon, table in WEAPON_TABLES.items()
    }
    all_codes = {p[0] for frame in body_frames for p in frame}
    all_codes.update(p[0] for frames in weapon_frames.values() for frame in frames for p in frame)
    bad = sorted(all_codes & divergent)
    if bad:
        raise SystemExit("pilot contains palette-divergent codes requiring another runtime identity: " +
                         ", ".join(f"0x{x:03x}" for x in bad))

    indexes = [(0xFFFFFFFF, 0xFF, 0) for _ in range(INDEX_COUNT)]
    table_blob = bytearray()
    dedup: dict[bytes, int] = {}
    native_keys = []
    frame_residency: dict[int, list[int]] = {}

    for frame in range(FRAME_COUNT):
        for weapon in range(4):
            for orientation in range(ORIENTATION_COUNT):
                source = list(body_frames[frame])
                weapon_source = weapon_frames.get(weapon, [])[frame] if weapon else []
                source.extend(weapon_source)
                packed = bytearray()
                weapon_start = len(body_frames[frame])
                for n, raw_piece in enumerate(source):
                    dx, dy, vi, attr = orient_piece(raw_piece, bool(orientation))
                    flags = FLAG_WEAPON_ANCHOR if weapon and n == weapon_start else 0
                    packed += struct.pack(">hhHHBB", dx, dy, vi, attr, SIZE_16X16, flags)
                packed_bytes = bytes(packed)
                offset = dedup.get(packed_bytes)
                if offset is None:
                    offset = len(table_blob)
                    dedup[packed_bytes] = offset
                    table_blob += packed_bytes
                k = key(frame, weapon, orientation)
                indexes[k] = (offset, len(source), STATUS_NATIVE)
                native_keys.append(k)
                frame_residency[k] = sorted({p[0] for p in source})

    generic_indexes = []
    usage_descriptors = []
    base_lut = bytearray(GENERIC_BASE_LUT_COUNT)
    generic_coverage = []
    for usage_id, usage in enumerate(GENERIC_USAGES, 1):
        if base_lut[usage["base"]] != 0:
            raise SystemExit(f"duplicate direct-dispatch base 0x{usage['base']:04x}")
        base_lut[usage["base"]] = usage_id
        selectors = list(usage["selectors"])
        first_record = len(generic_indexes)
        usage_descriptors.append((usage["disc_offset"], usage["disc_value"], selectors[0],
                                  len(selectors), usage["compositor"], usage["bank"],
                                  usage["attr_policy"], 0, first_record))
        for anim in selectors:
            for orientation in range(ORIENTATION_COUNT):
                pieces = decode_generic(rom, usage, anim, bool(orientation), finalized_variants)
                if len({piece[2] for piece in pieces}) > 12:
                    raise SystemExit(f"{usage['usage']}/{anim:02x} exceeds 12-item DMA worklist")
                if usage["usage"] in semantic_codes:
                    source_codes = {
                        (piece[2] if not piece[2] & VARIANT_KEY_MARK else
                         next(code for (code, bank), vi in finalized_variants.items()
                              if bank == usage["bank"] and vi == (piece[2] & 0x0FFF)))
                        for piece in pieces
                    }
                    missing = sorted(source_codes - semantic_codes[usage["usage"]])
                    if missing:
                        raise SystemExit(f"{usage['usage']}/{anim:02x} codes absent from semantic corpus: {missing}")
                packed_bytes = b"".join(struct.pack(">hhHHBB", *piece) for piece in pieces)
                offset = dedup.get(packed_bytes)
                if offset is None:
                    offset = len(table_blob)
                    dedup[packed_bytes] = offset
                    table_blob += packed_bytes
                generic_indexes.append((offset, len(pieces), STATUS_NATIVE))
                residency_key = INDEX_COUNT + len(generic_indexes) - 1
                frame_residency[residency_key] = sorted({piece[2] for piece in pieces})
                program, _ = PROVEN_PROGRAMS[(usage["usage"], anim)]
                generic_coverage.append({
                    "usage": usage["usage"], "usage_id": usage_id,
                    "base_tile": f"0x{usage['base']:04X}",
                    "animation_selector": f"0x{anim:02X}",
                    "normalized_selector": anim - selectors[0],
                    "compositor_selector": usage["compositor"],
                    "program": f"0x{program:06X}",
                    "effective_bank": f"0x{usage['bank']:02X}",
                    "discriminator": {"offset": f"0x{usage['disc_offset']:02X}",
                                      "value": f"0x{usage['disc_value']:02X}"},
                    "attribute_policy": ("actor+0x27 bit6 set; low byte replaces program control"
                                         if usage["attr_policy"] == ATTR_REQUIRE_OVERRIDE else
                                         "actor+0x27 bit6 clear; embedded program control retained"),
                    "orientation": orientation, "piece_count": len(pieces),
                    "table_offset": offset, "status": usage["status"],
                    "pattern_identity": "offline-finalized (code,effective_bank) vi",
                    "residency": usage["residency"],
                    "residency_record": residency_key,
                })

    index_blob = bytearray()
    for offset, count, status in indexes:
        index_blob += struct.pack(">IBB", offset, count, status)

    generic_index_blob = bytearray()
    for record in generic_indexes:
        generic_index_blob += struct.pack(">IBB", *record)
    usage_blob = b"".join(struct.pack(">BBBBBBBBH", *record) for record in usage_descriptors)

    # Future-compatible finalized-vi requirement metadata. Each fixed record is
    # {u32 list_offset,u16 count,u16 min,u16 max}; lists are sorted u16 values.
    residency_count = INDEX_COUNT + len(generic_indexes)
    residency_header = struct.pack(">4sHH", b"P9RS", 2, residency_count)
    residency_records = bytearray()
    residency_lists = bytearray()
    record_bytes = residency_count * 10
    for k in range(residency_count):
        vis = frame_residency.get(k)
        if vis is None:
            residency_records += struct.pack(">IHHH", 0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
            continue
        off = len(residency_header) + record_bytes + len(residency_lists)
        lo = min(vis) if vis else 0xFFFF
        hi = max(vis) if vis else 0xFFFF
        residency_records += struct.pack(">IHHH", off, len(vis), lo, hi)
        for vi in vis:
            residency_lists += struct.pack(">H", vi)
    residency_blob = residency_header + residency_records + residency_lists

    for path in (args.table_output, args.index_output, args.generic_index_output,
                 args.generic_base_lut_output, args.generic_usage_output, args.residency_output,
                 args.report_output, args.coverage_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.table_output.write_bytes(table_blob)
    args.index_output.write_bytes(index_blob)
    args.generic_index_output.write_bytes(generic_index_blob)
    args.generic_base_lut_output.write_bytes(base_lut)
    args.generic_usage_output.write_bytes(usage_blob)
    args.residency_output.write_bytes(residency_blob)

    inputs = {str(p.resolve().relative_to(ROOT)): sha256(p) for p in (
        args.maincpu, args.variant_index, args.body_evidence, args.weapon_evidence,
        args.profile, args.palette_decisions, args.burst_evidence, args.actor_manifest,
        args.enemy_corpus
    )}
    outputs = {
        str(args.table_output.resolve().relative_to(ROOT)): hashlib.sha256(table_blob).hexdigest(),
        str(args.index_output.resolve().relative_to(ROOT)): hashlib.sha256(index_blob).hexdigest(),
        str(args.generic_index_output.resolve().relative_to(ROOT)): hashlib.sha256(generic_index_blob).hexdigest(),
        str(args.generic_base_lut_output.resolve().relative_to(ROOT)): hashlib.sha256(base_lut).hexdigest(),
        str(args.generic_usage_output.resolve().relative_to(ROOT)): hashlib.sha256(usage_blob).hexdigest(),
        str(args.residency_output.resolve().relative_to(ROOT)): hashlib.sha256(residency_blob).hexdigest(),
    }
    readiness = {
        "player": {"status": "NATIVE_PARTIAL", "native": "selectors 0..74 x none/sword/axe/hammer x both orientations", "fallback": "fire sword and out-of-range selectors", "palette_status": "proven", "pattern_identity": "direct finalized vi", "residency": "shared transient"},
        "lizardman": {"status": "NATIVE_PARTIAL", "native": "family +0x3E=0 / base 0x004B / selectors 0x17..0x1F / compositor 0 / both orientations", "fallback": "wrong family/base/compositor/bank/attribute policy and every selector outside 0x17..0x1F", "palette_status": "proven 0x36", "pattern_identity": "offline-finalized (code,0x36) vi", "residency": "scene/family resident"},
        "valkyrie": {"status": "GRAPHICS_KNOWN_SELECTOR_UNKNOWN", "native": [], "fallback": "all", "palette_status": "proven 0x32", "pattern_identity": "unresolved", "residency": "existing fallback"},
        "chimera": {"status": "GRAPHICS_KNOWN_SELECTOR_UNKNOWN", "native": [], "fallback": "all", "palette_status": "proven 0x34", "pattern_identity": "unresolved", "residency": "existing fallback"},
        "flying_demon": {"status": "PALETTE_COMPLETE_FRAME_PARTIAL", "native": [], "fallback": "all", "palette_status": "proven 0x35", "pattern_identity": "unresolved selector binding", "residency": "existing fallback"},
        "four_armed_insect": {"status": "GRAPHICS_KNOWN_SELECTOR_UNKNOWN", "native": [], "fallback": "all", "palette_status": "proven 0x3A", "pattern_identity": "unresolved", "residency": "existing fallback"},
        "small_bat": {"status": "NATIVE_PARTIAL", "native": "raw +0x06=0x0B / base 0x0268 / selectors 0xB9..0xBB / compositor 0 / both orientations", "fallback": "other creation routes, wrong tuple, and every selector outside 0xB9..0xBB", "palette_status": "proven 0x3E", "pattern_identity": "offline-finalized (code,0x3E) vi", "residency": "shared transient"},
        "large_bat": {"status": "NATIVE_PARTIAL", "native": "raw +0x06=0x0A / base 0x03F6 / selectors 0xB6..0xB8 / compositor 0 / both orientations", "fallback": "other creation routes, wrong tuple, and every selector outside 0xB6..0xB8", "palette_status": "proven 0x3E", "pattern_identity": "offline-finalized (code,0x3E) vi", "residency": "shared transient"},
        "cave_block": {"status": "NATIVE_COMPLETE", "native": "base 0x0179 / anim 0x70 / compositor 0 / both orientations", "fallback": "every other base-0x0179 semantic", "palette_status": "proven 0x3C", "pattern_identity": "direct finalized vi", "residency": "scene/family resident"},
        "burst": {"status": "NATIVE_COMPLETE", "native": "base 0x0275 / anim 0x9E..0xA0 / compositor 0 / both orientations", "fallback": "inherited and all other selectors", "palette_status": "proven 0x30", "pattern_identity": "direct finalized vi", "residency": "shared transient"},
    }
    coverage = {
        "schema": "pc090oj-native-frame-coverage-v3",
        "key": "((effective_body_selector * 5 + weapon_selector) * 2 + orientation)",
        "orientation": {"0": "A5+0x1114 == 2", "1": "A5+0x1114 != 2"},
        "native": {"body_selectors": [0, FRAME_COUNT - 1], "weapon_selectors": [0, 1, 2, 3],
                   "orientations": [0, 1], "entry_count": len(native_keys)},
        "unresolved": {"weapon_selector": 4, "entry_count": FRAME_COUNT * 2,
                       "reason": "fire-sword pattern substitution depends on A5+0x1308"},
        "generic_native": generic_coverage,
        "generic_dispatch": {
            "kind": "direct base LUT -> usage descriptor -> normalized selector/orientation index",
            "base_lut_entries": GENERIC_BASE_LUT_COUNT,
            "usage_count": len(GENERIC_USAGES),
            "frame_index_records": len(generic_indexes),
            "unresolved": "base LUT zero or any descriptor validation/index status failure",
        },
        "readiness_matrix": readiness,
        "gen_ku_1": {"cave_block": "static base 0x0179", "burst": "static base 0x0275", "lizardman": "static base 0x004B within the proven family-0 selector domain", "large_bat": "static base 0x03F6 within raw record-type 0x0A", "small_bat": "static base 0x0268 within raw record-type 0x0B", "unresolved_families": "UNKNOWN; retained fallback"},
        "gen_ku_4": "base LUT is only coarse classification; exact identity additionally validates raw discriminator, selector range, compositor, effective bank, and actor+0x27 policy",
        "finalized_identity": "generic pieces store direct source vi or offline-finalized 0x2000|variant_vi keyed by (code,effective_bank)",
        "inputs_sha256": inputs,
        "outputs_sha256": outputs,
    }
    args.coverage_output.write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    report = [
        "PC090OJ native frame coverage Phase B",
        f"native index entries: {len(native_keys)}",
        f"UNRESOLVED index entries: {INDEX_COUNT - len(native_keys)}",
        f"unique native frame payloads: {len(dedup)}",
        f"generic direct index entries: {len(generic_indexes)}",
        f"generic usage descriptors: {len(usage_descriptors)}",
        f"generic base LUT bytes: {len(base_lut)}",
        f"frame table bytes: {len(table_blob)}",
        f"frame index bytes: {len(index_blob)}",
        f"residency metadata bytes: {len(residency_blob)}",
        "native coverage: body selectors 0..74; weapons none/sword/axe/hammer; both orientations",
        "UNRESOLVED: fire sword (weapon 4; dynamic A5+0x1308 code substitutions)",
        "mode-9/facing-3 selector decrement remains dynamic and is applied by the native emitter",
        "generic native coverage: cave 0x70, burst 0x9E..0xA0, lizardman 0x17..0x1F, large bat 0xB6..0xB8, small bat 0xB9..0xBB; both orientations",
        "generic unresolved coverage: Flying Demon/four-armed/Chimera/Valkyrie and every tuple outside the exact generated domains retain fallback",
        "generic lookup: O(1) base LUT + one descriptor + one normalized direct index; no native-record scan",
        "finalized pattern identity: offline (code,effective_bank) variant vi where required",
        "weapon TSV note: rows following a leading zero descriptor are not compositor output;",
        "the authoritative 0x54492 sticky-blank behavior does not advance the descriptor pointer.",
    ]
    args.report_output.write_text("\n".join(report) + "\n")
    print(f"PC090OJ player frame table: {len(native_keys)} native, "
          f"{INDEX_COUNT - len(native_keys)} UNRESOLVED, {len(dedup)} unique payloads")


if __name__ == "__main__":
    main()
