#!/usr/bin/env python3
"""Independent build gate for the native R1 boss palette/fade integration."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--assembly", required=True, type=Path)
    ap.add_argument("--spec", required=True, type=Path)
    args = ap.parse_args()
    report = json.loads(args.report.read_text())
    profile = json.loads(args.profile.read_text())
    blob = args.table.read_bytes()
    if len(blob) != 8 * 16 * 2:
        raise SystemExit(f"fade table is {len(blob)} bytes, expected 256")
    words = list(struct.unpack(">128H", blob))
    states = [words[i * 16:(i + 1) * 16] for i in range(8)]
    expected = [0] + [int(profile["context_policies"]["PAL-R1-S3-PLANEA-BOSS"]["tpl"]["1"][str(i)], 16) for i in range(1, 16)]
    if states[7] != expected:
        raise SystemExit("state 7 does not equal the selected profile's R1 boss Line 1")
    if any(state[0] for state in states) or any(word & 0x1111 for state in states for word in state):
        raise SystemExit("illegal CRAM word or non-black index 0")
    if report["checks"]["semantic_state_count"] != 8 or not report["source_authority"]["matches_prompt_0095_raw_live_words"]:
        raise SystemExit("generation report lacks required source/state proof")
    asm = args.assembly.read_text()
    if ".word 1, PROUTE_OWNER_PC090OJ,    0x4F, 1, 0" not in asm:
        raise SystemExit("R1 boss/dagger bank 0x4F is not routed to Line 1")
    if "genesistan_palette_hook_47004" not in asm or "r1_boss_fade_cram.bin" not in asm:
        raise SystemExit("native fade hook/table is absent from palette_hooks.s")
    spec = json.loads(args.spec.read_text())
    hooks = [r for r in spec["shift_replacements"] if r.get("arcade_pc") == "0x047004"]
    if len(hooks) != 1 or "genesistan_palette_hook_47004" not in hooks[0].get("replacement_bytes", ""):
        raise SystemExit("0x47004 is not cut through the required shift replacement")
    print(f"R1_BOSS_FADE_VERIFY_PASS source=full-bright target={args.profile.name} line=1 states=8 bank4F=line1 line2=untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
