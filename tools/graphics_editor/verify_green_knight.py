#!/usr/bin/env python3
"""PROMPT-ID-0069 / 0078 / CORRECTED PROMPT-ID-0084 — Green Sword Knight in the Palette Composer.

Proves (static, no trace, no ROM): the knight (family-2 base 0x033E) is a scene-tagged browsable object in
every castle section R1-S2..R6-S2 carrying its arcade palette reference; R1-S2 c0/c3 are green; no lizardman
leaks into the knight object; and (CORRECTED under PROMPT-ID-0084 from Cody's ORIGINAL ARCADE sweep,
PROMPT-ID-0080) the knight exposes the COMPLETE 29-PROGRAM / 109-CODE family-2 animation domain -- NORMAL
$93-$96, SHORT REACTION $71-$73, AIRBORNE $20-$23, LOW/WEAPON ACTION A $A1-$A6 and B $97-$9C (state-$1F),
ROPE $4D,$56-$5A -- as ONE semantic object whose authored Test.json index transform is applied EXACTLY
(not a color-only check). The old 17-program/77-code claim can NO LONGER pass as complete. Also proves:
$71-$73 is NOT labeled a proven "crouch"; $74 stays excluded; the complete sword artwork 26B-274 is covered;
and both palette-provenance layers (embedded defaults + actor +$27 override) are surfaced. Asserts
Test.json unchanged.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0069
TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0078
TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0084
"""
from __future__ import annotations
import importlib.util, json, threading, time, urllib.request, urllib.parse, struct, zlib, hashlib
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P, F = [], []
def ck(n, c, extra=""):
    (P if c else F).append(n); print(("PASS " if c else "FAIL ") + n + ((" -> " + str(extra)) if extra and not c else ""))


def is_green(pal16):
    for c in pal16:
        r, g, b = c
        if g > r + 0x20 and g > b + 0x10 and g > 0x50:
            return True
    return False


def main() -> int:
    tjson = ROOT / "analysis/graphics_optimizer/editor_policy/Test.json"
    t0 = hashlib.sha256(tjson.read_bytes()).hexdigest() if tjson.is_file() else None
    spec = importlib.util.spec_from_file_location("ged_server", ROOT / "tools/graphics_editor/server.py")
    srv = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(srv)
    except SystemExit: pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Hd); port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.3)
    us = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/oracle"))["usages"]

    kn = [u for u in us if (u.get("object_id") or "").startswith("object:castle.green_sword_knight")]
    ck("1. Green Sword Knight object exists", bool(kn), len(kn))
    ck("2. all entries display as 'Green Sword Knight'", kn and all(u["display_name"] == "Green Sword Knight" for u in kn))
    ck("3. base is 0x033E (not lizardman 0x004B / not 0x0A73)",
       all(u.get("base") == "0x033E" for u in kn) and not any("Lizardman" in u.get("display_name", "") for u in kn))

    # appears in every castle section
    scenes = {u.get("scene_key") for u in kn}
    need = {"PAL-R%d-S2-PLANEA-CASTLE" % r for r in range(1, 7)}
    ck("4. knight present in ALL six castle sections R1..R6-S2", need <= scenes, sorted(scenes))

    # the knight's reference palette renders GREEN (armor line 3 / pool 0x0C), not blue/flesh
    def pixels(blob):
        i, W, H, ct, idat = 8, None, None, None, b""
        while i < len(blob):
            ln = struct.unpack(">I", blob[i:i+4])[0]; t = blob[i+4:i+8]; d = blob[i+8:i+8+ln]
            if t == b"IHDR": W, H, _, ct = struct.unpack(">IIBB", d[:10])
            elif t == b"IDAT": idat += d
            elif t == b"IEND": break
            i += 12 + ln
        raw = zlib.decompress(idat); chn = 4 if ct == 6 else 3; stride = W*chn+1
        return [tuple(raw[y*stride+1+x*chn:y*stride+1+x*chn+3]) for y in range(H) for x in range(W)]
    r1u = next(u for u in kn if u["round"] == 1)
    png = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/render?usage=" + urllib.parse.quote(r1u["usage_id"])).read()
    cols = pixels(png)
    grn = sum(1 for r, g, b in cols if g > r + 0x20 and g > b + 0x10 and g > 0x50)
    blu = sum(1 for r, g, b in cols if b > g + 0x20 and b > r + 0x20)
    ck("5. R1-S2 knight renders GREEN (armor), not blue", grn > 20 and blu == 0, "green=%d blue=%d" % (grn, blu))

    # R1-S2 creation nibbles: c0->4, c3->2, c4->1 (from 0x45684 table); c0/c3 green, c4 not
    secs = srv._green_knight_sections()
    r1 = {nib: comps for (v, nib, comps) in secs[1]}
    ck("6. R1-S2 creation nibbles are 0x4/0x2/0x1 (0x45684)", set(r1.keys()) == {0x4, 0x2, 0x1}, sorted(hex(n) for n in r1))
    ck("7. R1-S2 c0 (nibble 0x4) palette is GREEN", is_green(srv._arcade_round_palette(1, 0x4)))
    ck("8. R1-S2 c3 (nibble 0x2) palette is GREEN", is_green(srv._arcade_round_palette(1, 0x2)))
    ck("9. R1-S2 c4 (nibble 0x1) palette is the red/blue default (not green)", not is_green(srv._arcade_round_palette(1, 0x1)))

    # each variant carries a 16-colour reference + knight frames
    one = kn[0]
    ck("10. variant carries a 16-colour arcade reference palette", len(one.get("used_colors", [])) == 16)
    ck("11. variant carries knight frames (pieces)", bool(one.get("pieces")) and one.get("n_pieces", 0) >= 2)
    ck("12. preview uses the green-armor line (pool 0x0C)", one.get("preview_type", "").startswith("ARCADE GREEN-ARMOR"))

    # CORRECTED PROMPT-ID-0084 from Cody's ORIGINAL ARCADE sweep (PROMPT-ID-0080): the COMPLETE same-actor
    # base-$033E animation domain is 29 PROGRAMS, re-stated here independently (NOT imported from the server/
    # generator). The old 17-program set is now a FAILING subset. Dropping ANY block fails the regression.
    NORMAL = {0x93, 0x94, 0x95, 0x96}
    SHORT_REACTION = {0x71, 0x72, 0x73}                         # state-0x0F alt 0x40E0E (NOT a proven crouch)
    AIRBORNE = {0x20, 0x21, 0x22, 0x23}                         # engine 0x473B8 states 0D/0E
    LOW_ACTION_A = {0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6}         # state-$1F table 0x42FBC (NEW: was omitted)
    LOW_ACTION_B = {0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9C}         # state-$1F table 0x42FD4 (NEW: was omitted)
    ROPE = {0x4D, 0x56, 0x57, 0x58, 0x59, 0x5A}                 # shared-sheet family-8 climb
    DOMAIN = NORMAL | SHORT_REACTION | AIRBORNE | LOW_ACTION_A | LOW_ACTION_B | ROPE
    assert len(DOMAIN) == 29
    OLD_17 = NORMAL | SHORT_REACTION | AIRBORNE | ROPE          # PROMPT-ID-0078's incomplete set
    r1 = [u for u in kn if u.get("round") == 1]
    r1_anims = {int(u["frame_label"].split()[-1], 16) for u in r1}
    ck("13. R1 knight exposes the COMPLETE 29-program domain (normal+reaction+airborne+1F-A+1F-B+rope)",
       r1_anims == DOMAIN and len(r1_anims) == 29, sorted("0x%02X" % a for a in (DOMAIN ^ r1_anims)))
    ck("13b. the old 17-program set is NO LONGER complete (0084 regression)", r1_anims != OLD_17 and OLD_17 < r1_anims)
    ck("14. SHORT-REACTION block $71-$73 present", SHORT_REACTION <= r1_anims)
    ck("15. ROPE block $4D,$56-$5A preserved + re-verified (not dropped by refactor)", ROPE <= r1_anims)
    ck("15b. AIRBORNE block $20-$23 present (states 0D/0E)", AIRBORNE <= r1_anims)
    ck("15c. state-$1F LOW/WEAPON ACTION A $A1-$A6 present (Cody 0080 missing programs)", LOW_ACTION_A <= r1_anims)
    ck("15d. state-$1F LOW/WEAPON ACTION B $97-$9C present (Cody 0080 missing programs)", LOW_ACTION_B <= r1_anims)
    ck("15e. torch $74 (base 0x0DAB) correctly NOT in the knight domain", 0x74 not in r1_anims)
    # anim_state tags each frame so the UI groups the one actor's poses -- labels must be HONEST: $71-$73 is a
    # "short_reaction", NOT a proven "crouch"; state-$1F sequences are provisional "low_action_a/b".
    states = {u.get("anim_state") for u in r1}
    ck("16. anim_state tags are the 6 honest pose groups (no false 'crouch')",
       states == {"normal", "short_reaction", "airborne", "low_action_a", "low_action_b", "rope"}, states)
    sr_labels = {u.get("pose_label", "") for u in r1 if u.get("anim_state") == "short_reaction"}
    ck("16b. NO frame is a proven 'crouch'; $71-$73 label keeps it pending (0084 honesty requirement)",
       not any(u.get("anim_state") == "crouch" for u in r1)
       and all("pending" in lbl.lower() for lbl in sr_labels) and sr_labels)
    # ONE semantic actor: every R1 pose inherits a SINGLE authored object_id (not pose-specific identities)
    r1_objs = {u.get("object_id") for u in r1}
    ck("17. all R1 poses are ONE semantic object (single authored mapping)", len(r1_objs) == 1, r1_objs)

    # PROMPT-ID-0078 (no color-based PASS): prove the EXACT source-index -> authored-destination-index
    # transform from the LIVE Test.json, using the real production reindex transform. A uniform-nibble
    # probe cell must reindex to the authored index_map value (index 0 stays transparent).
    import importlib.util as _ilu
    gspec = _ilu.spec_from_file_location("genre", ROOT / "tools/graphics_editor/gen_reindexed_pc090oj.py")
    genre = _ilu.module_from_spec(gspec); gspec.loader.exec_module(genre)
    prof = json.loads(tjson.read_bytes())
    imap, line = genre._imap(prof, "object:castle.green_sword_knight.r1.n3")
    ck("18. live Test.json carries the authored R1 knight index_map (line 0)", bool(imap) and line == 0, (bool(imap), line))
    exact = imap and all(
        (lambda cell: all((cell[k] >> 4) == (0 if i == 0 else imap.get(i, i)) for k in range(len(cell))))(
            genre.transform(bytes([(i << 4) | i]) * genre.CELL, 0, imap))
        for i in range(16))
    ck("19. authored index transform is EXACT for every source index (not just 'green')", bool(exact))

    # 0084: the complete domain re-derives to 109 codes (independent compositor VM) and covers the complete
    # moving-weapon sword artwork 26B-274. Re-derived here, NOT read from the generator's constant.
    import sys as _sys
    vm_path = str(ROOT / "tools/graphics_optimizer")
    if vm_path not in _sys.path:
        _sys.path.insert(0, vm_path)
    from compositor_vm import ActorRenderState, visible_pieces
    domain_codes = {p.tile & 0x1FFF for a in DOMAIN for p in visible_pieces(ActorRenderState(0x033E, a, 0))
                    if (p.tile & 0x1FFF) < 0x1000}
    ck("19b. complete domain re-derives to 109 distinct pattern codes", len(domain_codes) == 109, len(domain_codes))
    sword = set(range(0x26B, 0x275))
    ck("19c. complete sword artwork 26B-274 is covered by the warrior domain",
       sword <= domain_codes, sorted("0x%03X" % c for c in (sword - domain_codes)))
    # 0084 requirement #5: both palette-provenance layers are surfaced (embedded defaults + actor override)
    pp = one.get("palette_provenance") or {}
    ck("19d. palette provenance surfaces embedded defaults AND actor +$27 override (not flattened to $33)",
       bool(pp.get("embedded_defaults")) and bool(pp.get("actor_override")) and bool(pp.get("registry_conflict")))
    # 0084 requirement #6: sword exposed as a warrior sub-context (not a separate palette identity)
    ck("19e. sword exposed as warrior sub-context inheriting the same object", all(
        u.get("weapon_subcontext") == "object:castle.green_sword_knight.weapon.sword"
        and u.get("object_id") != u.get("weapon_subcontext") for u in r1))

    # scene-membership: a knight entry shows only in its own castle section (mirror app.js scene_key rule)
    def visible(active):
        return [u for u in kn if u.get("scene_key") == active]
    ck("20. R1-S2 knight entries show in R1-S2 only", all(u["scene_key"] == "PAL-R1-S2-PLANEA-CASTLE" for u in visible("PAL-R1-S2-PLANEA-CASTLE")) and visible("PAL-R1-S2-PLANEA-CASTLE"))

    t1 = hashlib.sha256(tjson.read_bytes()).hexdigest() if tjson.is_file() else None
    ck("21. Test.json unchanged (mapping not modified by this task)", t0 == t1)

    httpd.shutdown()
    print(f"\n{'GREEN_KNIGHT PASS' if not F else str(len(F)) + ' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
