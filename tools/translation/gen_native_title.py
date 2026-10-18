#!/usr/bin/env python3
"""Generate the first attract TITLE as final Genesis presentation data.

The retained arcade sources are authoritative:
  * 0x5B0B2: 28x20 RASTAN/logo Plane-B block used by 0x5A356/0x5A38E
  * 0x3BB7C: frontend string descriptor table used by 0x3BB48
  * 0x5A6FA: title palette row used by 0x5A356
  * 0x3B950/0x3B9B0/0x3B9D4: frontend HUD glyph templates

Outputs contain final Genesis name words/CRAM words, never PC080SN C-window
records.  They are consumed once by genesistan_title_present_once.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PLANE_WORDS = 64 * 32
TITLE_BLOCK = 0x5B0B2
TITLE_COLS = 28
TITLE_ROWS = 20
TITLE_BG_DEST = 0x00C00328
BG_BASE = 0x00C00000
FG_BASE = 0x00C08000
TEXT_TABLE = 0x3BB7C
TITLE_PALETTE = 0x5A6FA
BLANK_CODE = 0x0020
CLEAR_FIRST_CELL = 0x100 // 4
CLEAR_CELLS = 1900
TITLE_TEXT_IDS = (2, 30, 32, 18, 19)
NO_HIT_TEXT_ID = 29
TEXT_SPECIAL_GLYPH_MAP = {
    0x21: 0x2744,
    0x22: 0x2745,
    0x27: 0x2746,
    0x28: 0x2747,
    0x29: 0x2748,
    0x2C: 0x2749,
    0x2D: 0x274A,
    0x3F: 0x274B,
}


def be16(data: bytes, off: int) -> int:
    return int.from_bytes(data[off : off + 2], "big")


def be32(data: bytes, off: int) -> int:
    return int.from_bytes(data[off : off + 4], "big")


def words_be(words: list[int]) -> bytes:
    return b"".join((word & 0xFFFF).to_bytes(2, "big") for word in words)


def attr_key(attr: int) -> int:
    return (
        (attr & 0x0003)
        | (((attr >> 14) & 1) << 2)
        | (((attr >> 15) & 1) << 3)
        | (((attr >> 13) & 1) << 4)
    )


def name_word(code: int, attr: int, tile_lut: bytes, attr_lut: bytes) -> int:
    tile = be16(tile_lut, (code & 0x3FFF) * 2)
    mapped_attr = be16(attr_lut, attr_key(attr) * 2)
    # The arcade blank glyph (0x20) intentionally resolves to Genesis tile 0.
    if code and code != BLANK_CODE and tile == 0:
        raise ValueError(f"title tile {code & 0x3FFF:#06x} has no resident LUT slot")
    return tile | mapped_attr


def apply_text(
    plane: list[int], text_id: int, maincpu: bytes, tile_lut: bytes, attr_lut: bytes
) -> list[dict[str, int]]:
    desc = be32(maincpu, TEXT_TABLE + ((text_id & 0x7F) * 4))
    dest = be32(maincpu, desc)
    attr = be16(maincpu, desc + 4)
    if not (FG_BASE <= dest < FG_BASE + 0x4000):
        raise ValueError(f"title text {text_id} destination {dest:#x} is not Plane A")
    cell = (dest - FG_BASE) // 4
    pos = desc + 6
    touched: list[dict[str, int]] = []
    while True:
        code = maincpu[pos]
        pos += 1
        if code == 0:
            break
        mapped_code = TEXT_SPECIAL_GLYPH_MAP.get(code, code)
        word = name_word(mapped_code, attr, tile_lut, attr_lut)
        plane[cell] = word
        touched.append(
            {"cell": cell, "code": code, "mapped_code": mapped_code, "attr": attr, "word": word}
        )
        cell += 1
    return touched


def convert_title_palette(maincpu: bytes) -> list[int]:
    out: list[int] = []
    for idx in range(16):
        raw = be16(maincpu, TITLE_PALETTE + idx * 2)
        # Exact 0RGB-444 -> xBGR-555 -> Genesis conversion used by 0x59AD4.
        xbgr = ((raw & 0x0F00) >> 7) | ((raw & 0x00F0) << 2) | ((raw & 0x000F) << 11)
        red = ((xbgr & 0x001F) >> 2) << 1
        green = (((xbgr >> 5) & 0x001F) >> 2) << 5
        blue = (((xbgr >> 10) & 0x001F) >> 2) << 9
        out.append(red | green | blue)
    return out


def decode_template(maincpu: bytes, start: int, count: int) -> list[tuple[int, int, int]]:
    return [
        (maincpu[start + i * 4], be16(maincpu, start + i * 4 + 2), maincpu[start + i * 4 + 1])
        for i in range(count)
    ]


def static_sat_labels(maincpu: bytes) -> list[tuple[int, int, int]]:
    main = decode_template(maincpu, 0x3B950, 24)
    p1 = decode_template(maincpu, 0x3B9B0, 9)
    p2 = decode_template(maincpu, 0x3B9D4, 9)
    # Preserve the accepted native title ordering. Numeric 0x2A..0x33 glyphs
    # remain live semantic producers. Credit label records are parked exactly
    # as the accepted native path parks them on the zero-credit title.
    labels = sorted(main[:5], key=lambda item: item[1]) + main[5:13]
    labels += [(y | 0x0100, x, code) for y, x, code in main[14:17]]
    labels += p1[6:9] + p2[6:9]
    if any(0x2A <= code <= 0x33 for _, _, code in labels):
        raise ValueError("static SAT label set contains a dynamic digit glyph")
    return labels


def build(maincpu: bytes, tile_lut: bytes, attr_lut: bytes) -> dict[str, object]:
    if len(tile_lut) != 0x8000 or len(attr_lut) != 64:
        raise ValueError("unexpected PC080SN LUT size")
    blank = name_word(BLANK_CODE, 0, tile_lut, attr_lut)
    bg = [blank] * PLANE_WORDS
    fg = [blank] * PLANE_WORDS

    bg_first = (TITLE_BG_DEST - BG_BASE) // 4
    for row in range(TITLE_ROWS):
        for col in range(TITLE_COLS):
            code = be16(maincpu, TITLE_BLOCK + 2 * (row * TITLE_COLS + col))
            bg[bg_first + row * 64 + col] = name_word(code, 1, tile_lut, attr_lut)

    text_evidence: dict[str, list[dict[str, int]]] = {}
    for text_id in TITLE_TEXT_IDS:
        text_evidence[str(text_id)] = apply_text(fg, text_id, maincpu, tile_lut, attr_lut)
    fg_invincible = list(fg)
    text_evidence[str(NO_HIT_TEXT_ID)] = apply_text(
        fg_invincible, NO_HIT_TEXT_ID, maincpu, tile_lut, attr_lut
    )

    return {
        "bg": bg,
        "fg": fg,
        "fg_invincible": fg_invincible,
        "palette": convert_title_palette(maincpu),
        "labels": static_sat_labels(maincpu),
        "text_evidence": text_evidence,
        "blank_word": blank,
        "bg_first_cell": bg_first,
    }


def write_inc(path: Path, labels: list[tuple[int, int, int]]) -> None:
    lines = ["/* Generated by gen_native_title.py; {Y, X, glyph}. */"]
    lines += [f"    .word 0x{y:04X},0x{x:04X},0x{code:04X}" for y, x, code in labels]
    lines.append("    .word 0xFFFF,0x0000,0x0000")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maincpu", type=Path, required=True)
    ap.add_argument("--tile-lut", type=Path, required=True)
    ap.add_argument("--attr-lut", type=Path, required=True)
    ap.add_argument("--bg-output", type=Path, required=True)
    ap.add_argument("--fg-output", type=Path, required=True)
    ap.add_argument("--fg-invincible-output", type=Path, required=True)
    ap.add_argument("--palette-output", type=Path, required=True)
    ap.add_argument("--sat-include", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    maincpu = args.maincpu.read_bytes()
    tile_lut = args.tile_lut.read_bytes()
    attr_lut = args.attr_lut.read_bytes()
    result = build(maincpu, tile_lut, attr_lut)
    outputs = {
        args.bg_output: words_be(result["bg"]),
        args.fg_output: words_be(result["fg"]),
        args.fg_invincible_output: words_be(result["fg_invincible"]),
        args.palette_output: words_be(result["palette"]),
    }
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    args.sat_include.parent.mkdir(parents=True, exist_ok=True)
    write_inc(args.sat_include, result["labels"])

    report = {
        "format": "rastan-native-title-v1",
        "semantic_cut": "arcade 0x03AA54 title presentation entry",
        "authoritative_sources": {
            "plane_b_logo": "maincpu 0x05B0B2 28x20",
            "plane_a_strings": [f"0x{x:02X}" for x in TITLE_TEXT_IDS],
            "invincible_no_hit_string": f"0x{NO_HIT_TEXT_ID:02X}",
            "palette": "maincpu 0x05A6FA row 0",
            "static_sat": "maincpu 0x03B950/0x03B9B0/0x03B9D4",
        },
        "dimensions": {"plane_words": PLANE_WORDS, "logo_cols": TITLE_COLS, "logo_rows": TITLE_ROWS},
        "blank_word": f"0x{result['blank_word']:04X}",
        "logo_first_cell": result["bg_first_cell"],
        "static_sat_count": len(result["labels"]),
        "text_cells": result["text_evidence"],
        "sha256": {path.name: hashlib.sha256(data).hexdigest() for path, data in outputs.items()},
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
