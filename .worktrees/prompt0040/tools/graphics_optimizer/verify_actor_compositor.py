#!/usr/bin/env python3
"""Reproduce the actor-render verification JSON from durable arcade evidence."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compositor_vm import (  # noqa: E402
    ActorRenderState, COMPOSITOR_TABLES, program_address, run_general,
)

MAINCPU = (ROOT / "build/regions/maincpu.bin").read_bytes()
SAMPLES = ROOT / "analysis/actor_render_verification/original_arcade_actor_samples.csv"
OUTPUT = ROOT / "docs/design/Cody_actor_render_verified.json"


def s9(value: int) -> int:
    value &= 0x1FF
    return value - 0x200 if value & 0x100 else value


def parse_records(text: str):
    result = []
    for encoded in text.split("|"):
        if not encoded:
            continue
        _, word0, y, tile, x = encoded.split(":")
        record = tuple(int(value, 16) for value in (word0, y, tile, x))
        if record[0] == 0 and record[2] == 0:
            continue
        result.append(record)
    return result


def relative(records):
    first_y, first_x = records[0][1], records[0][3]
    return [(word0, s9(y - first_y), tile & 0x1FFF, s9(x - first_x))
            for word0, y, tile, x in records]


def palette_words_to_rgb(words):
    """Decode live arcade xBGR-555 palette RAM words to RGB8."""
    result = []
    for word in words:
        red = word & 0x1F
        green = (word >> 5) & 0x1F
        blue = (word >> 10) & 0x1F
        result.append([
            (red << 3) | (red >> 2),
            (green << 3) | (green >> 2),
            (blue << 3) | (blue >> 2),
        ])
    return result


with SAMPLES.open() as source:
    samples = {row["label"]: row for row in csv.DictReader(source)}

CASES = [
    dict(label="lizardman", technical_id="field_3e_0_lizardman",
         semantic_identity="PROVEN: Lizardman", family=0, budget=19),
    dict(label="chimera", technical_id="field_3e_1_chimera",
         semantic_identity="PROVEN: Chimera", family=1, budget=10),
    dict(label="four_armed", technical_id="field_3e_3_four_armed",
         semantic_identity="PROVEN: Four-Armed Swordsman", family=3, budget=10),
    dict(label="valkyrie", technical_id="field_3e_8_valkyrie",
         semantic_identity="PROVEN: Valkyrie (existing user-verified name)", family=8, budget=10),
    dict(label="serpent_base_0400", technical_id="field_3e_11_serpent",
         semantic_identity="PROPOSED: Serpent", family=11, budget=10),
    dict(label="family5_base_01cb", technical_id="field_3e_5_base_01cb",
         semantic_identity="UNKNOWN: field family 5; former Small Crawler label rejected", family=5, budget=10),
    dict(label="round1_boss_type14", technical_id="boss_record_type_14_base_061d",
         semantic_identity="PROVEN: Round-1 boss BODY record family; boss name not assigned", family=None, budget=20),
    dict(label="round5_boss_type16", technical_id="boss_record_type_16_base_0988",
         semantic_identity="PROVEN: Round-5 boss BODY record family; boss name not assigned", family=None, budget=20),
]

actors = []
for case in CASES:
    row = samples[case["label"]]
    observed = parse_records(row["sat_records"])
    base = int(row["base_1e"], 16)
    anim = int(row["anim_01"], 16)
    selector = int(row["compositor_38"], 16)
    attr = int(row["attr_27"], 16)
    state = ActorRenderState(
        base, anim, selector,
        facing_02=int(row["facing_02"], 16),
        mirror_control_20=int(row["mirror_20"], 16),
        state_03=int(row["state_03"], 16),
        palette_attr_27=attr, piece_budget=case["budget"],
    )
    emulated = [(piece.word0, piece.y, piece.tile, piece.x) for piece in run_general(state)]
    match = relative(observed) == relative(emulated)
    if not match:
        raise SystemExit(f'SAT mismatch for {case["technical_id"]}')

    line = int(row["palette_line"], 16)
    pool = int(row["palette_pool_index"])
    words = [int(word, 16) for word in row["palette_words"].split("|")]
    rom_words = [int(word, 16) for word in row["rom_palette_words"].split("|")]
    if words != rom_words or row["palette_ram_matches_rom"] != "true":
        raise SystemExit(f'palette RAM mismatch for {case["technical_id"]}')
    rgb = palette_words_to_rgb(words)
    palette_source = (
        "live palette RAM bank 0x30|line equals 0RGB ROM pool selected by "
        "maincpu[0x3BA88+(round-1)*32+line], after 0x3BA64 xBGR-555 transform"
    )

    rel = relative(observed)
    pieces = [{
        "tile": f"0x{tile:04X}", "x": x, "y": y,
        "hflip": bool(word0 & 0x4000), "vflip": bool(word0 & 0x8000),
        "palette": word0 & 0xF, "word0": f"0x{word0:04X}",
    } for word0, y, tile, x in rel]
    actors.append({
        "technical_id": case["technical_id"],
        "source_actor_slot": f'A5+0x{int(row["actor_address"], 16) - 0x10C000:03X}',
        "render_slot": f'A5+0x{int(row["actor_address"], 16) - 0x10C000:03X}',
        "raw_actor_record_00_3F": row["raw_00_3f"],
        "base_graphics": f'0x{base:04X}',
        "family": None if case["family"] is None else f'0x{case["family"]:02X}',
        "record_type": f'0x{int(row["record_type_06"], 16):02X}',
        "variant_source": f'parallel per-slot byte A4+0x752 = 0x{row["variant_parallel_752"]} (not a 0x40-byte actor member)',
        "compositor_selector": f'0x{selector:02X}',
        "compositor_table": f'0x{COMPOSITOR_TABLES[selector]:06X}',
        "program_pointer": f'0x{program_address(anim, selector):06X}',
        "anim_index": f'0x{anim:02X}',
        "subframe_index_0B": f'0x{int(row["subframe_0b"], 16):02X}',
        "round": int(row["round"]),
        "progression_13E": f'0x{row["progression_13e"]}',
        "palette_line": f'0x{line:X}',
        "effective_palette_bank": f'0x{int(row["effective_palette_bank"], 16):02X}',
        "palette_pool_index": pool,
        "palette_rgb": rgb,
        "palette_words_arcade_xbgr555": [f'0x{word:04X}' for word in words],
        "palette_ram_matches_rom": True,
        "palette_source": palette_source,
        "pieces": pieces,
        "arcade_sat_match": True,
        "sat_match_scope": "exact word0/tile/order/piece-count and relative X/Y; absolute translation is actor position",
        "semantic_identity": case["semantic_identity"],
        "notes": "Same-frame original-arcade actor/SAT/palette-RAM evidence; no Genesis runtime evidence used.",
    })

result = {
    "schema_version": 1,
    "evidence_class": "original arcade static proof plus ORIGINAL ARCADE MAME corroboration",
    "A5_base_verified": "0x10C000",
    "A5_plus_752_actual_semantics": "(0x752,A4): parallel per-slot variant byte, initialized from spawn byte2 high nibble; not a member of the 0x40-byte actor record",
    "actor_record_layout": "0x40-byte records in A5-relative blocks; 0x3D054 consumes the record directly",
    "render_record_layout": "no distinct copied render record for these paths; A5+0x2C8/0x508/0x5C8/0x748/0x8C8 are actor blocks consumed directly",
    "tile_decoder": "PASS: code&0x1FFF, code*128, 16x16, 4bpp packed MSB/high nibble first, pen 0 transparent",
    "palette_decoder": "PASS: all eight live effective banks (0x30|line) exactly match the round/line ROM pool after the 0x3BA64 xBGR-555 transform",
    "coordinate_model": "FIXED: +0x1A is Y, +0x16 is X, control 0x70 adds +0x18 to Y",
    "flip_model": "FIXED: facing selects 0x3C960/0x3C9A6; control 0x40 negates tile delta; control 0x80 sets HFLIP; general path emits no VFLIP",
    "compositor_modes_verified": ["general 0x00", "general 0x40", "general 0x70", "general 0x80"],
    "andy_assumptions_wrong": [
        "all field actors use compositor table 0",
        "base-table initialization byte is a representative current frame",
        "control 0x40 directly means displayed horizontal flip",
        "A4+0x752 is a member of each 0x40-byte actor",
        "A5+0x5C8/0x748/0x8C8 are copied render records distinct from actors",
        "0x061D is a Centaur and 0x0988 is a field Serpent/Dragon based on raw tile appearance",
    ],
    "actors": actors,
}

OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
print(f"PASS: {len(actors)} original-arcade SAT matches; wrote {OUTPUT}")
