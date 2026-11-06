#!/usr/bin/env python3
"""Generate the native R1-boss eight-state Genesis CRAM fade.

The arcade ROM remains the source/behavior authority.  Test.json remains the
Genesis endpoint authority.  This script deliberately creates only a generated
runtime representation; it is not a palette-decision registry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

SOURCE = 0x4708C
LUT = 0x46F84
STEPS = 8
CONTEXT = "PAL-R1-S3-PLANEA-BOSS"
BODY = "object:boss.r1.body"
DAGGERS = "object:boss.r1.flying_daggers"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def effective_line1(profile: dict) -> list[int]:
    base = profile["target_palette_lines"][1]
    words = [int(v, 16) if v is not None else 0 for v in base]
    overrides = profile["context_policies"][CONTEXT]["tpl"]["1"]
    for index, value in overrides.items():
        words[int(index)] = int(value, 16)
    words[0] = 0
    return words


def components_0rgb(word: int) -> tuple[int, int, int]:
    return (word >> 8) & 15, (word >> 4) & 15, word & 15


def arcade_live_word(rom: bytes, source: int, step: int) -> int:
    r, g, b = components_0rgb(source)
    r = rom[LUT + r * STEPS + step]
    g = rom[LUT + g * STEPS + step]
    b = rom[LUT + b * STEPS + step]
    return (b << 11) | (g << 6) | (r << 1)


def genesis_word(rom: bytes, source: int, step: int) -> int:
    r, g, b = components_0rgb(source)
    r = rom[LUT + r * STEPS + step] >> 1
    g = rom[LUT + g * STEPS + step] >> 1
    b = rom[LUT + b * STEPS + step] >> 1
    return (b << 9) | (g << 5) | (r << 1)


def channels(word: int) -> tuple[int, int, int]:
    return (word >> 1) & 7, (word >> 5) & 7, (word >> 9) & 7


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maincpu", required=True, type=Path)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--evidence", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    args = ap.parse_args()

    rom = args.maincpu.read_bytes()
    profile = json.loads(args.profile.read_text())
    evidence = json.loads(args.evidence.read_text())
    source = [0] + [struct.unpack_from(">H", rom, SOURCE + i * 2)[0] for i in range(15)]
    target = effective_line1(profile)

    evidence_source = [int(v.split("(")[0], 16) for v in evidence["palette"]["source_0rgb"]]
    if source != evidence_source:
        raise SystemExit("R1 boss ROM source does not match PROMT-ID-0095 evidence")
    live = [0] + [arcade_live_word(rom, word, 7) for word in source[1:]]
    evidence_live = [int(v, 16) for v in evidence["palette"]["final_live_words"]]
    if live != evidence_live:
        raise SystemExit("full-bright ROM/LUT decode does not match raw live palette evidence")

    for object_id in (BODY, DAGGERS):
        if profile["usage_palette_mappings"][object_id]["line"] != 1:
            raise SystemExit(f"{object_id} is not authored on Genesis Line 1")

    states = []
    for step in range(7):
        states.append([0] + [genesis_word(rom, word, step) for word in source[1:]])
    states.append(target)

    for state in states:
        if state[0] != 0 or any(word & 0x1111 for word in state):
            raise SystemExit("generated state violates Genesis CRAM format/index-0 black")
    for index in range(16):
        for channel in range(3):
            values = [channels(state[index])[channel] for state in states]
            if values != sorted(values):
                raise SystemExit(f"non-monotonic fade at index {index}, channel {channel}: {values}")
    if states[7] != target:
        raise SystemExit("fade state 7 differs from the authored Test.json endpoint")

    blob = b"".join(struct.pack(">H", word) for state in states for word in state)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    report = {
        "schema": "rastan-r1-boss-native-fade/v1",
        "prompt_id": "TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0101",
        "source_authority": {
            "maincpu_sha256": sha256(args.maincpu),
            "source_address": "0x4708C-0x470A9",
            "component_lut": "0x46F84 (16x8 bytes)",
            "source_0rgb": [f"{word:04X}" for word in source],
            "full_brightness_live_xbgr555": [f"{word:04X}" for word in live],
            "matches_prompt_0095_raw_live_words": True,
            "half_brightness_decode_used": False,
        },
        "target_authority": {
            "profile": str(args.profile),
            "profile_sha256": sha256(args.profile),
            "context": CONTEXT,
            "genesis_line": 1,
            "words": [f"{word:04X}" for word in target],
        },
        "translation": "states 0-6: arcade LUT nibble at semantic step, reduced f>>1 and packed as Genesis CRAM; state 7: exact authored target",
        "cadence_owner": "retained boss actor +0x09 and A5+0x270; states 0-6 each eight actor updates, state 7 final/held",
        "states": [[f"{word:04X}" for word in state] for state in states],
        "checks": {
            "semantic_state_count": len(states),
            "all_legal_cram": True,
            "all_index0_black": True,
            "all_channels_monotonic": True,
            "state7_exact_test_json": True,
            "body_line1": True,
            "daggers_line1": True,
            "second_dagger_line": False,
        },
    }
    args.report.write_text(json.dumps(report, indent=1) + "\n")
    print(f"R1_BOSS_FADE_GEN_OK states=8 bytes={len(blob)} target_sha={sha256(args.profile)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
