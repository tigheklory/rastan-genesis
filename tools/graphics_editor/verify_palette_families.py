#!/usr/bin/env python3
"""Verify current-Test profile provenance and semantic production consumers."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "analysis/graphics_optimizer/editor_policy/Test.json"
REGISTRY = ROOT / "specs/palette_decisions.json"
LUT_INC = ROOT / "apps/rastan-direct/out/pc090oj_palsel_lut.inc"
EDITOR_MANIFEST = ROOT / "build/regions/pc090oj_editor_manifest.json"
SEMANTIC_REPORT = ROOT / "build/rastan-direct/pc090oj_semantic_profile_report.json"
CRAM_REPORT = ROOT / "build/rastan-direct/test_palette_cram_report.json"
SPRITE_SOURCE = ROOT / "apps/rastan-direct/src/pc090oj_hooks.s"
MAKEFILE = ROOT / "apps/rastan-direct/Makefile"

SEMANTIC = {
    "object:attract.game_over": (
        "PAL-PC090OJ-ATTRACT-GAMEOVER-001", "PC090OJ_GAMEOVER_PROFILE_LINE"
    ),
    "object:hud.p1_label": (
        "PAL-PC090OJ-HUD-P1-LABEL-001", "PC090OJ_HUD_P1_PROFILE_LINE"
    ),
    "object:hud.score_digits": (
        "PAL-PC090OJ-HUD-SCORE-DIGITS-001", "PC090OJ_HUD_SCORE_PROFILE_LINE"
    ),
}
CHANGED_EXISTING = ("usage:small_bat:bank0x3E", "usage:large_bat:bank0x3E")


def fail(message: str) -> None:
    raise SystemExit(f"PALETTE_FAMILY_VERIFY_FAIL: {message}")


def main() -> int:
    profile_bytes = PROFILE.read_bytes()
    profile_sha = hashlib.sha256(profile_bytes).hexdigest()
    profile = json.loads(profile_bytes)
    mappings = profile["usage_palette_mappings"]
    registry = {entry["id"]: entry for entry in json.loads(REGISTRY.read_text())["decisions"]}
    lut = LUT_INC.read_text()
    editor = json.loads(EDITOR_MANIFEST.read_text())
    semantic = json.loads(SEMANTIC_REPORT.read_text())
    cram = json.loads(CRAM_REPORT.read_text())
    source = SPRITE_SOURCE.read_text()
    makefile = MAKEFILE.read_text()

    sha_sources = {
        "palette-line LUT": re.search(r"palette_tool_profile_sha256=([0-9a-f]{64})", lut),
        "reindexed graphics": editor.get("profile_sha256"),
        "semantic graphics": semantic.get("profile_sha256"),
        "CRAM asset": cram.get("profile_sha256"),
    }
    for name, value in sha_sources.items():
        found = value.group(1) if hasattr(value, "group") else value
        if found != profile_sha:
            fail(f"{name} profile SHA {found!r} != current Test {profile_sha}")

    if "build0400/Test.snapshot.json" in makefile:
        fail("production Makefile still consumes stale Build-0400 Test snapshot")
    if "analysis/graphics_optimizer/editor_policy/Test.json" not in makefile:
        fail("production Makefile does not consume the live Test profile")

    # Every bank-keyed authored line must survive to the scene-1 generated LUT.
    emitted = []
    started = False
    for raw_line in lut.splitlines():
        if raw_line.strip() == "pc090oj_palsel_lut:":
            started = True
            continue
        text = raw_line.strip()
        if started and text.startswith(".byte"):
            emitted.extend(int(value.strip()) for value in text[5:].split(","))
        elif started and text.startswith(".section") and emitted:
            break
    if len(emitted) != 4 * 128:
        fail(f"generated palette LUT has {len(emitted)} entries, expected 512")
    lut_lines = {bank: emitted[128 + bank] for bank in range(128)}
    for uid, mapping in mappings.items():
        match = re.search(r":bank0x([0-9A-Fa-f]{2})$", uid)
        if match and lut_lines.get(int(match.group(1), 16)) != int(mapping["line"]):
            fail(f"authored line for {uid} did not survive generated LUT")

    # Object identities with shared bank 0x30 must match both generated semantic
    # pixels and generated line constants, independently of burst.
    decisions = {entry["id"]: entry for entry in registry.values()}
    for uid, (decision_id, symbol) in SEMANTIC.items():
        authored = mappings.get(uid)
        generated = semantic.get("families", {}).get(uid)
        if authored is None or generated is None:
            fail(f"missing authored/generated semantic family {uid}")
        if int(generated["line"]) != int(authored["line"]):
            fail(f"generated line mismatch for {uid}")
        if generated["index_map"] != authored["index_map"]:
            fail(f"generated index_map mismatch for {uid}")
        constant = re.search(rf"\.equ\s+{symbol},\s*(\d+)", lut)
        if not constant or int(constant.group(1)) != int(authored["line"]):
            fail(f"generated line constant mismatch for {uid}")
        decision = decisions.get(decision_id)
        if not decision or decision["genesis_realization"]["palette_line"] != authored["line"]:
            fail(f"canonical decision mismatch for {uid}")

    # The only pre-existing usages changed since Build 0458 are the two bat
    # mappings; both must appear exactly in the current reindexed-region manifest.
    produced = editor.get("usage_decisions", {})
    for uid in CHANGED_EXISTING + ("usage:flying_demon:bank0x35",):
        authored = mappings[uid]
        generated = produced.get(uid)
        if generated is None:
            fail(f"reindexed graphics omit {uid}")
        if int(generated["line"]) != int(authored["line"]):
            fail(f"reindexed line mismatch for {uid}")
        if generated["index_map"] != authored["index_map"]:
            fail(f"reindexed index_map mismatch for {uid}")

    required_source = (
        "PC090OJ_GAMEOVER_PROFILE_LINE",
        "PC090OJ_HUD_P1_PROFILE_LINE",
        "PC090OJ_HUD_SCORE_PROFILE_LINE",
        "rastan_pc090oj_semantic_profile",
    )
    if any(token not in source for token in required_source):
        fail("runtime lacks generated semantic object consumers")
    if "moveq   #3, %d7" in source[source.index("profile_native_sat_attr"):source.index("profile_native_sat_x")]:
        fail("hard-coded gameplay HUD palette line remains")

    print("PALETTE_FAMILY_VERIFY_PASS")
    print(f"profile_sha256={profile_sha}")
    print("generated_profile_sha=lut,pc090oj_editor,semantic_profile,cram:match")
    print("gameover=semantic_object,no_burst_fallback")
    print("hud_p1=semantic_object hud_score=semantic_object")
    print("changed_existing=small_bat,large_bat:exact")
    print("demon=current_line_and_index_map:exact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
