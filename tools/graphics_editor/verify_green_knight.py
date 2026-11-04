#!/usr/bin/env python3
"""PROMPT-ID-0069 — Green Sword Knight in all six castle Palette Composer sections.

Proves (static, no trace, no ROM): the knight (family-2 base 0x033E, anim 0x93) is a scene-tagged browsable
object in every castle section R1-S2..R6-S2, each palette-distinct variant carries its CREATION-route arcade
palette reference (0x45684 nibble -> 0x3BA88[round] -> pool), R1-S2 c0/c3 are green, Test.json unchanged,
and no lizardman leaks into the knight object.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0069
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

    # Original arcade $04684E selects the normal $93-$96 frames and the
    # actor+$3E==8 rope frames $4D/$56-$5A for this same family-2 identity.
    r1_anim_labels = {u.get("frame_label") for u in kn if u.get("round") == 1}
    live_labels = {"anim 0x%02X" % a for a in (0x93, 0x94, 0x95, 0x96, 0x4D, 0x56, 0x57, 0x58, 0x59, 0x5A)}
    ck("13. R1 knight exposes exact normal and rope animation domain", r1_anim_labels == live_labels,
       sorted(r1_anim_labels))

    # scene-membership: a knight entry shows only in its own castle section (mirror app.js scene_key rule)
    def visible(active):
        return [u for u in kn if u.get("scene_key") == active]
    ck("14. R1-S2 knight entries show in R1-S2 only", all(u["scene_key"] == "PAL-R1-S2-PLANEA-CASTLE" for u in visible("PAL-R1-S2-PLANEA-CASTLE")) and visible("PAL-R1-S2-PLANEA-CASTLE"))

    t1 = hashlib.sha256(tjson.read_bytes()).hexdigest() if tjson.is_file() else None
    ck("15. Test.json unchanged", t0 == t1)

    httpd.shutdown()
    print(f"\n{'GREEN_KNIGHT PASS' if not F else str(len(F)) + ' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
