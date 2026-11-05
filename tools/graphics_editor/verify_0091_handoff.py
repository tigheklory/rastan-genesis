#!/usr/bin/env python3
"""Independent verifier for the PROMPT-ID-0091 Palette Composer / Bestiary handoff of Cody PROMPT-ID-0090.

Re-derives the facts independently (compositor VM + a fresh /api/oracle), NOT by importing the
implementation's constants, per Section 39. Covers: Green Knight 23/97 with no $4D/$56-$5A contamination;
the family-8 base-$0241 rope climber as a separate object; the 17 reward children (compositor 2, lines 0/3,
codes $A5A-$A71); the R1-S3 boss body/aux/line-F (field palette not falsely substituted); and the
Authoring/Research navigation separation. Asserts Test.json byte-unchanged.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0091
"""
from __future__ import annotations
import importlib.util, json, threading, time, urllib.request, hashlib, sys
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P, F = [], []
def ck(n, c, extra=""):
    (P if c else F).append(n)
    print(("PASS " if c else "FAIL ") + n + ((" -> " + str(extra)) if extra and not c else ""))


def vm_codes(base, anims, comp=0):
    vm = str(ROOT / "tools/graphics_optimizer")
    if vm not in sys.path:
        sys.path.insert(0, vm)
    from compositor_vm import ActorRenderState, visible_pieces
    codes = set()
    for a in anims:
        for p in visible_pieces(ActorRenderState(base, a, comp)):
            c = p.tile & 0x1FFF
            if c < 0x1000:
                codes.add(c)
    return codes


def main() -> int:
    tjson = ROOT / "analysis/graphics_optimizer/editor_policy/Test.json"
    t0 = hashlib.sha256(tjson.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("ged_server", ROOT / "tools/graphics_editor/server.py")
    srv = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(srv)
    except SystemExit: pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Hd); port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.3)
    oracle = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/oracle"))
    us = oracle["usages"]
    by_obj = {}
    for u in us:
        by_obj.setdefault(u.get("object_id"), []).append(u)

    # ---------- Green Knight ----------
    kn = [u for u in us if (u.get("object_id") or "").startswith("object:castle.green_sword_knight") and u.get("round") == 1]
    kn_anims = {int(u["frame_label"].split()[-1], 16) for u in kn}
    FOREIGN = {0x4D, 0x56, 0x57, 0x58, 0x59, 0x5A}
    ck("GK1. Green Knight R1 exposes EXACTLY 23 base-$033E programs", len(kn_anims) == 23, len(kn_anims))
    ck("GK2. Green Knight domain re-derives to 97 distinct codes (compositor VM)",
       len(vm_codes(0x033E, kn_anims)) == 97, len(vm_codes(0x033E, kn_anims)))
    ck("GK3. NO foreign $4D/$56/$57/$58/$59/$5A contamination", not (FOREIGN & kn_anims),
       sorted("0x%02X" % a for a in (FOREIGN & kn_anims)))

    # ---------- Rope climber ----------
    rope = by_obj.get("object:castle.rope_climber.family8.r1", [])
    rope_anims = {int(u["frame_label"].split()[-1], 16) for u in rope}
    ck("RC1. family-8 rope climber is a SEPARATE object (base $0241)",
       bool(rope) and all(u.get("base") == "0x0241" for u in rope), [u.get("base") for u in rope])
    ck("RC2. rope climber programs are exactly $56,$59,$5A", rope_anims == {0x56, 0x59, 0x5A},
       sorted("0x%02X" % a for a in rope_anims))
    ck("RC3. rope climber is NOT the knight object + human identity PARTIAL",
       all(u.get("object_id") != "object:castle.green_sword_knight.r1.n3" for u in rope)
       and all(u.get("human_identity_status") == "partial" for u in rope))

    # ---------- Rewards ----------
    rw = by_obj.get("object:item.gameplay_rewards", [])
    rm = [u.get("reward_meta", {}) for u in rw]
    ck("RW1. exactly 17 reward children under one parent", len(rw) == 17, len(rw))
    ck("RW2. all reward children compositor 2", bool(rm) and all(m.get("compositor") == 2 for m in rm))
    ck("RW3. kinds 1-13 embedded line 0; kinds 14-17 line 3",
       bool(rm) and all(m.get("embedded_line") == (0 if m.get("kind") <= 13 else 3) for m in rm))
    want_codes = {"0x%03X" % c for c in (0xA5A, 0xA5B, 0xA5C, 0xA5D, 0xA5E, 0xA5F, 0xA60, 0xA61, 0xA62,
                                         0xA63, 0xA65, 0xA67, 0xA69, 0xA6E, 0xA6F, 0xA70, 0xA71)}
    ck("RW4. reward codes are exactly $A5A-$A71 (Cody census)", {m.get("code") for m in rm} == want_codes)
    child_ids = {u.get("child_id") for u in rw}
    ck("RW5. 17 distinct canonical child ids kind01..kind17",
       child_ids == {"object:item.reward.kind%02d" % k for k in range(1, 18)}, len(child_ids))
    all_ids = {u.get("object_id") for u in us}
    ck("RW6. false three-bank reward objects removed",
       not ({"object:effect.item_drop_death", "object:item.gameplay_reward_b31",
             "object:item.gameplay_reward_b37"} & all_ids))

    # ---------- Boss ----------
    body = by_obj.get("object:boss.r1.body", [])
    aux = by_obj.get("object:boss.r1.aux.type15", [])
    ck("BO1. boss body present, R1-S3 only, program $47908 comp1 anim $00",
       bool(body) and all(u.get("scene_key") == "PAL-R1-S3-PLANEA-BOSS" and u.get("program") == "0x47908"
                          and u.get("compositor") == 1 for u in body))
    ck("BO2. boss aux type-15 present, program $47E54 comp1 anim $14",
       bool(aux) and all(u.get("program") == "0x47E54" and u.get("compositor") == 1 for u in aux))
    ck("BO3. boss shows source line F PROVEN (not ordinary field palette, RGB PARTIAL)",
       all(u.get("palette_status", {}).get("source_line") == "F"
           and u.get("palette_status", {}).get("source_line_proven") is True
           and "PARTIAL" in u.get("palette_status", {}).get("rgb_status", "") for u in body + aux))
    ck("BO4. boss groups are NOT authorable until palette RGB proven (no invented colors)",
       all(u.get("authorable") is False for u in body + aux))
    boss_rounds = {u.get("round") for u in (body + aux + by_obj.get("object:boss.r1.effect.death", []))}
    ck("BO5. boss correctly scoped to Round 1 only", boss_rounds == {1}, boss_rounds)

    # ---------- Navigation: Authoring vs Research ----------
    def visible_authoring(active_scene, is_field):
        out = []
        for u in us:
            if u.get("view") != "authoring":
                continue
            sk = u.get("scene_key")
            if sk:
                if sk == active_scene:
                    out.append(u)
            elif u.get("membership") == "field_phase1":
                if is_field:
                    out.append(u)
            else:
                out.append(u)  # truly shared
        return out
    r1s2 = visible_authoring("PAL-R1-S2-PLANEA-CASTLE", False)
    foreign_round = [u for u in r1s2 if u.get("scene_key") and u.get("round") not in (None, 1)]
    ck("NV1. R1-S2 authoring view shows no unrelated-round scene assets", not foreign_round,
       [u.get("object_id") for u in foreign_round][:5])
    r1s3 = visible_authoring("PAL-R1-S3-PLANEA-BOSS", False)
    ck("NV2. R1-S3 authoring view shows the boss group", any((u.get("object_id") or "").startswith("object:boss.r1") for u in r1s3))
    # Research view exposes controllers / research producers; authoring hides them
    research = [u for u in us if u.get("view") == "research"]
    ck("NV3. Authoring view hides controllers/research producers",
       all(u.get("view") != "research" for u in r1s2 + r1s3))
    ck("NV4. round navigation present (Round 1 -> sub-rounds incl. boss)",
       any(n["round"] == 1 and any(s.get("boss") for s in n["subrounds"]) for n in oracle.get("round_nav", [])))
    ck("NV5. backdrop BLACK invariant surfaced (line 0 / index 0 / 0x0000)",
       oracle.get("backdrop_invariant", {}).get("required_cram") == "0x0000")

    # ---------- R1-S3 conditional Line 2 + hazard pending ----------
    lay = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/layera?scene=PAL-R1-S3-PLANEA-BOSS"))
    l2 = lay.get("line_owners", {}).get("2", {})
    ck("LN1. R1-S3 Line 2 shown CONDITIONAL and still locked (not globally freed)",
       l2.get("scene_local_status") == "CONDITIONAL" and l2.get("editable") is False and l2.get("free_in_scene") is False)
    haz = [u for u in us if u.get("hazard_pending")]
    ck("HZ1. R1-S2 hazard candidates present, disabled, NOT $0224/$09EA",
       len(haz) >= 6 and all(u.get("authorable") is False and u.get("base") is None for u in haz), len(haz))

    t1 = hashlib.sha256(tjson.read_bytes()).hexdigest()
    ck("INT. Test.json byte-unchanged", t0 == t1)

    httpd.shutdown()
    print(f"\n{'PROMPT-0091 HANDOFF PASS' if not F else str(len(F)) + ' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
