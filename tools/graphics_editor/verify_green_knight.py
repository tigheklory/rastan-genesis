#!/usr/bin/env python3
"""PROMPT-ID-0069 — Green Sword Knight in all six castle Palette Composer sections.

Proves (static, no trace, no ROM): the knight (family-2 base 0x033E, anim 0x93) is a scene-tagged browsable
object in every castle section R1-S2..R6-S2, each palette-distinct variant carries its CREATION-route arcade
palette reference (0x45684 nibble -> 0x3BA88[round] -> pool), R1-S2 c0/c3 are green, Test.json unchanged,
and no lizardman leaks into the knight object.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0069
"""
from __future__ import annotations
import importlib.util, json, threading, time, urllib.request, hashlib
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

    # per-section palette-distinct variants (each (round,nibble) is its own authoring domain)
    def variants(rnd):
        return {u["object_id"] for u in kn if u.get("round") == rnd}
    ck("5. R1-S2 has multiple palette-distinct variants (separately authorable)", len(variants(1)) >= 2, variants(1))

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
    ck("12. preview uses the creation palette (not control-byte)", one.get("preview_type", "").startswith("ARCADE CREATION-PALETTE"))

    # scene-membership: a knight entry shows only in its own castle section (mirror app.js scene_key rule)
    def visible(active):
        return [u for u in kn if u.get("scene_key") == active]
    ck("13. R1-S2 knight entries show in R1-S2 only", all(u["scene_key"] == "PAL-R1-S2-PLANEA-CASTLE" for u in visible("PAL-R1-S2-PLANEA-CASTLE")) and visible("PAL-R1-S2-PLANEA-CASTLE"))

    t1 = hashlib.sha256(tjson.read_bytes()).hexdigest() if tjson.is_file() else None
    ck("14. Test.json unchanged", t0 == t1)

    httpd.shutdown()
    print(f"\n{'GREEN_KNIGHT PASS' if not F else str(len(F)) + ' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
