#!/usr/bin/env python3
"""Verify the Round-2 scene-tagged Objects rosters (R2-S1 field + R2-S3 boss).

Locks the invariants of server.py r2_field_usages() / r2_boss_usages(): membership is anchored to the
PROVEN dynamic signature capture + field schedule, the composites render, nothing is fabricated, and the
honest provisional/partial/PENDING flags are present. Read-only; no ROM/build/counter change.

Run:  python3 tools/graphics_editor/verify_r2_rosters.py
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIG = ROOT / "analysis/enemy_sprite_lexicon/dynamic_signature_map.json"

_passed = 0
_failed = 0


def ck(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"PASS {name}")
    else:
        _failed += 1
        print(f"FAIL {name}" + (f" — {detail}" if detail else ""))


def _load_server():
    spec = importlib.util.spec_from_file_location("srv_verify", str(Path(__file__).with_name("server.py")))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    srv = _load_server()
    us = srv.build_usages(srv.sprite_bank_colors())
    by_scene: dict[str, list[dict]] = {}
    for u in us:
        sk = u.get("scene_key")
        if sk:
            by_scene.setdefault(sk, []).append(u)

    s1 = by_scene.get("PAL-R2-S1-PLANEA-OUTDOOR", [])
    boss = by_scene.get("PAL-R2-S3-PLANEA-BOSS", [])

    # 1. Both R2 scenes are populated.
    ck("1. R2-S1 OUTDOOR has a roster", len(s1) > 0, f"{len(s1)} usages")
    ck("2. R2-S3 BOSS has a roster", len(boss) > 0, f"{len(boss)} usages")

    # 3. Every R2 usage is scene-tagged to its own subround (never leaks into another scene).
    ck("3. R2-S1 usages all tagged R2-S1", all(u["scene_key"] == "PAL-R2-S1-PLANEA-OUTDOOR" for u in s1))
    ck("4. R2-S3 usages all tagged R2-S3", all(u["scene_key"] == "PAL-R2-S3-PLANEA-BOSS" for u in boss))

    # 5. Field bases match the proven schedule-band families (0/1/3/4/8/11) + comp2 specials.
    s1_bases = {u.get("base") for u in s1}
    want_field = {"0x004B", "0x00D0", "0x02E8", "0x0420", "0x0241", "0x0400", "0x0A5A", "0x0A73"}
    ck("5. R2-S1 bases == proven schedule/capture set", s1_bases == want_field,
       f"got {sorted(s1_bases)}")

    # 6. The dynamically-captured R2-S1 bases (0x004B, 0x0400) expose a frame tagged as the capture.
    cap_bases = {u.get("base") for u in s1 if u.get("dynamic_captured_frame")}
    ck("6. dynamic-captured frames present for 0x004B & 0x0400", cap_bases == {"0x004B", "0x0400"},
       f"got {sorted(cap_bases)}")

    # 7. Renderable field usages have real multi-piece composites (no empty/fake frames among non-incomplete).
    render_ok = all(u["n_pieces"] >= 2 for u in s1 if not u.get("incomplete") and u.get("pieces"))
    ck("7. renderable R2-S1 frames are multi-piece composites", render_ok)

    # 8. Compositor-2 specials are honest incomplete nodes (no fabricated pieces).
    comp2 = [u for u in s1 if u.get("base") in ("0x0A5A", "0x0A73")]
    ck("8. comp2 specials are incomplete with no pieces",
       bool(comp2) and all(u.get("incomplete") and u["n_pieces"] == 0 for u in comp2))

    # 9. Boss body is a proven composite; boss palette is honestly PENDING and not authorable.
    body = next((u for u in boss if u["object_id"] == "object:boss.r2.body"), None)
    ck("9. R2 boss body is a proven composite", bool(body) and body["n_pieces"] >= 8 and body["composite_proven"])
    ck("10. R2 boss palette PENDING + not authorable",
       bool(body) and body.get("authorable") is False
       and "PENDING" in (body.get("palette_status", {}) or {}).get("rgb_status", ""))

    # 11. R2 boss identity is the PROVEN per-round boss body $0753 (NOT the degenerate dynamic-map $061D,
    #     which is the Round-1 body), plus the shared flying-demon wing sprites $0129 (Tighe ground truth).
    boss_bases = {u.get("base") for u in boss}
    ck("11a. R2 boss body base is the proven $0753 (not the R1 body $061D)",
       bool(body) and body.get("base") == "0x0753")
    ck("11b. R2 boss does NOT use the degenerate dynamic-map base $061D/$0275",
       "0x061D" not in boss_bases and "0x0275" not in boss_bases,
       f"roster bases {sorted(boss_bases)}")
    wings = next((u for u in boss if u["object_id"] == "object:boss.r2.wings"), None)
    ck("11c. R2 boss wings reuse the flying-demon sprites $0129 (shared, recolored)",
       bool(wings) and wings.get("base") == "0x0129" and wings.get("authorable") is False)

    # 12. Nothing in the R2 rosters is marked authorable (palettes are Tighe-authored / boss PENDING).
    ck("12. no R2 roster usage auto-claims authorable",
       all(u.get("authorable") is not True for u in s1 + boss))

    print(f"\nR2_ROSTERS {'PASS' if _failed == 0 else 'FAIL'}  (pass={_passed}, fail={_failed})")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
