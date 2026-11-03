#!/usr/bin/env python3
"""Generate the one shared native Rastan HUD asset package."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

SPRITE_BASE = 1339
STATIC_LABELS = 11
DYNAMIC_POSITIONS = 19
SAT_RECORDS = STATIC_LABELS + DYNAMIC_POSITIONS

def u16(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off + 2], "big")

def words(values) -> bytes:
    return b"".join((value & 0xffff).to_bytes(2, "big") for value in values)

def template(main: bytes, start: int, count: int):
    return [(main[start + i * 4], u16(main, start + i * 4 + 2), main[start + i * 4 + 1])
            for i in range(count)]

def sat_record(index: int, y: int, x: int, tile: int, visible: bool = True) -> bytes:
    sy = ((y - 8 + 0x80) if visible else 0) & 0x1ff
    # Genesis SAT links are zero-based record numbers: record zero links to one.
    link = index + 1 if index + 1 < SAT_RECORDS else 0
    return words((sy, 0x0500 | link, 0xC000 | tile, (x + 0x80) & 0x1ff))

def build(main: bytes, pc090: bytes):
    main_template = template(main, 0x3B950, 24)
    p1_template = template(main, 0x3B9B0, 9)
    p2_template = template(main, 0x3B9D4, 9)
    labels = sorted(main_template[:5], key=lambda row: row[1]) + p1_template[6:9] + p2_template[6:9]
    glyphs = []
    for _y, _x, code in labels:
        if code not in glyphs:
            glyphs.append(code)
    for code in range(0x2A, 0x34):
        if code not in glyphs:
            glyphs.append(code)
    slots = {code: SPRITE_BASE + index * 4 for index, code in enumerate(glyphs)}
    patterns = bytearray()
    for code in glyphs:
        raw = pc090[code * 128:code * 128 + 128]
        if len(raw) != 128:
            raise ValueError(f"missing PC090OJ glyph 0x{code:02X}")
        for quadrant in range(4):
            patterns += (slots[code] + quadrant).to_bytes(2, "big")
            patterns += raw[quadrant * 32:(quadrant + 1) * 32]
    patterns += b"\xff\xff"

    static = bytearray(80 * 8)
    for index, (y, x, code) in enumerate(labels):
        static[index * 8:(index + 1) * 8] = sat_record(index, y, x, slots[code])
    positions = ([(x, 0) for x in range(8, 0x38, 8)] +
                 [(x, 0) for x in range(0xE8, 0x118, 8)] +
                 [(x, 0x10) for x in range(0x80, 0xB0, 8)] +
                 [(0x128, 0xE8)])
    dynamic = bytearray()
    for index, (x, y) in enumerate(positions, STATIC_LABELS):
        hidden = sat_record(index, y, x, slots[0x2A], False)
        static[index * 8:(index + 1) * 8] = hidden
        dynamic += hidden
        for digit in range(10):
            dynamic += sat_record(index, y, x, slots[0x2A + digit], True)
    return {
        "patterns": bytes(patterns), "static_sat": bytes(static),
        "dynamic_records": bytes(dynamic), "labels": labels,
        "positions": positions, "slots": slots,
    }

def main():
    parser = argparse.ArgumentParser()
    for name in ("maincpu", "pc090oj", "patterns-output", "sat-output",
                 "dynamic-output", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = build(args.maincpu.read_bytes(), args.pc090oj.read_bytes())
    outputs = {
        args.patterns_output: result["patterns"],
        args.sat_output: result["static_sat"],
        args.dynamic_output: result["dynamic_records"],
    }
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    report = {
        "format": "rastan-shared-native-hud-v1",
        "semantic_cut": "arcade HUD state -> final Genesis SAT",
        "modes": {
            "FRONTEND_FULL": ["1UP", "P1", "HIGH SCORE", "HIGH", "2UP", "P2", "CREDIT"],
            "GAMEPLAY_REDUCED_P1": ["1UP", "P1"],
            "GAMEPLAY_FULL_future_supported": True,
        },
        "static_label_records": STATIC_LABELS,
        "dynamic_positions": DYNAMIC_POSITIONS,
        "sat_records": SAT_RECORDS,
        "fixed_residency_cells": len(result["slots"]),
        "sprite_slots": {f"0x{code:02X}": slot for code, slot in result["slots"].items()},
        "performance": {
            "stable_frontend_full_rebuild": 0,
            "generic_glyph_interpretation": 0,
            "pc090oj_record_interpretation": 0,
            "update_granularity": "changed semantic score group or credit record",
        },
        "sha256": {path.name: hashlib.sha256(data).hexdigest() for path, data in outputs.items()},
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

if __name__ == "__main__":
    main()
