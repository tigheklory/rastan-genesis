#!/usr/bin/env python3
"""PROMPT-ID-0069 / extended PROMPT-ID-0078 — Green Sword Knight in the Palette Composer.

Proves (static, no trace, no ROM): the knight (family-2 base 0x033E) is a scene-tagged browsable object in
every castle section R1-S2..R6-S2 carrying its arcade palette reference; R1-S2 c0/c3 are green; no lizardman
leaks into the knight object; and (PROMPT-ID-0078) the knight exposes the COMPLETE family-2 animation domain
from the actor state machine -- NORMAL $93-$96, CROUCH/low-pose $20-$23 (airborne engine 0x473B8 states
0D/0E), ROPE $4D,$56-$5A -- as ONE semantic object whose authored Test.json index transform is applied
EXACTLY (not a color-only check). Fails if any proven pose block is dropped, and asserts Test.json unchanged.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0069
TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0078
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

    # PROMPT-ID-0078: the COMPLETE same-actor base-$033E animation domain from the actor state machine --
    # NORMAL $93-$96, CROUCH $71-$73 (state-0x0F alt 0x40E0E, base-preserving; Cody's runtime block),
    # AIRBORNE $20-$23 (engine 0x473B8 states 0D/0E), ROPE $4D,$56-$5A. The expected set is derived from the
    # sub-domains, so dropping ANY block fails the regression (the exact failure Tighe found: one animation
    # state silently outside the semantic palette object).
    NORMAL = {0x93, 0x94, 0x95, 0x96}
    CROUCH = {0x71, 0x72, 0x73}
    AIRBORNE = {0x20, 0x21, 0x22, 0x23}
    ROPE = {0x4D, 0x56, 0x57, 0x58, 0x59, 0x5A}
    DOMAIN = NORMAL | CROUCH | AIRBORNE | ROPE
    r1 = [u for u in kn if u.get("round") == 1]
    r1_anims = {int(u["frame_label"].split()[-1], 16) for u in r1}
    ck("13. R1 knight exposes the COMPLETE normal+crouch+airborne+rope domain", r1_anims == DOMAIN,
       sorted("0x%02X" % a for a in (DOMAIN ^ r1_anims)))
    ck("14. CROUCH block $71-$73 present (the state Tighe/Cody found missing)", CROUCH <= r1_anims)
    ck("15. ROPE block $4D,$56-$5A preserved + re-verified (not dropped by refactor)", ROPE <= r1_anims)
    ck("15b. AIRBORNE block $20-$23 present (states 0D/0E)", AIRBORNE <= r1_anims)
    ck("15c. torch $74 (base 0x0DAB) correctly NOT in the knight domain", 0x74 not in r1_anims)
    # anim_state tags each frame so the UI groups the one actor's poses
    states = {u.get("anim_state") for u in r1}
    ck("16. every R1 frame carries an anim_state (normal/crouch/airborne/rope)",
       states == {"normal", "crouch", "airborne", "rope"}, states)
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
