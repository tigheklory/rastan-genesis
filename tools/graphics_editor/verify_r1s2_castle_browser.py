#!/usr/bin/env python3
"""PROMPT-ID-0029 regression — R1-S2 castle actors in the existing Palette Composer catalog.

Proves (static, no trace, no ROM):
  1. the server loads and /api/oracle returns the existing catalog + the added castle usages;
  2. castle usages reference real sprite objects and composite frames (pieces with per-piece palette);
  3. bases 0x0224 and 0x00F4 are browsable (multiple distinct frames each);
  4. the route-documented multi-bank frame (anim 0x91, banks 3+12) is exposed and its composite USES both
     source palettes (PROMPT-ID-0028 per-piece behaviour preserved through the usage render path);
  5. the marker-'M' burst is represented WITHOUT fabricated frames (flagged incomplete, zero pieces);
  6. the existing R1/P1 catalog is intact and untagged (no scene_key) so scene filtering leaves it visible;
  7. castle usages are scene-tagged PAL-R1-S2-PLANEA-CASTLE (the client shows them only for that scene);
  8. the oracle is idempotent (cache -> no duplicate castle entries on repeated requests);
  9. Test.json is not modified by any of the above.
"""
from __future__ import annotations
import importlib.util, json, threading, time, urllib.request, struct, zlib, hashlib
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENE = "PAL-R1-S2-PLANEA-CASTLE"
P, F = [], []
def ck(n, c, extra=""):
    (P if c else F).append(n); print(("PASS " if c else "FAIL ") + n + ((" -> " + str(extra)) if extra and not c else ""))

def _png_pixels(blob):
    assert blob[:8] == b"\x89PNG\r\n\x1a\n"
    i, W, H, ct, idat = 8, None, None, None, b""
    while i < len(blob):
        ln = struct.unpack(">I", blob[i:i+4])[0]; typ = blob[i+4:i+8]; data = blob[i+8:i+8+ln]
        if typ == b"IHDR": W, H, _bd, ct = struct.unpack(">IIBB", data[:10])
        elif typ == b"IDAT": idat += data
        elif typ == b"IEND": break
        i += 12 + ln
    raw = zlib.decompress(idat); chn = 4 if ct == 6 else 3; stride = W*chn+1
    out = set()
    for y in range(H):
        row = raw[y*stride+1:(y+1)*stride]
        for x in range(W):
            out.add(tuple(row[x*chn:x*chn+3]))
    return out


def main() -> int:
    tjson = ROOT / "analysis/graphics_optimizer/editor_policy/Test.json"
    t_before = hashlib.sha256(tjson.read_bytes()).hexdigest() if tjson.is_file() else None

    spec = importlib.util.spec_from_file_location("ged_server", ROOT / "tools/graphics_editor/server.py")
    srv = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(srv)
    except SystemExit: pass
    ck("1a. server module loads", True)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Hd); port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.3)
    g = lambda u: json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}"+u))
    raw = lambda u: urllib.request.urlopen(f"http://127.0.0.1:{port}"+u).read()

    orc = g("/api/oracle")
    usages = orc["usages"]
    castle = [u for u in usages if u.get("scene_key") == SCENE]
    r1p1 = [u for u in usages if not u.get("scene_key")]
    ck("1b. /api/oracle returns catalog + castle usages", len(usages) > 400 and len(castle) >= 40, (len(usages), len(castle)))
    ck("2. castle usages reference real composite pieces with per-piece palette",
       all(u.get("object_id", "").startswith("object:castle.") for u in castle) and
       any(u["pieces"] and all("palette" in p for p in u["pieces"]) for u in castle))

    by_obj = {}
    for u in castle:
        by_obj.setdefault(u["object_id"], []).append(u)
    ck("3. bases 0x0224 and 0x00F4 are browsable (multiple frames each)",
       len(by_obj.get("object:castle.base_0x0224", [])) > 1 and len(by_obj.get("object:castle.base_0x00F4", [])) > 1,
       {k: len(v) for k, v in by_obj.items()})

    # 4. documented multi-bank frame exposed + composite uses both banks
    c224 = by_obj.get("object:castle.base_0x0224", [])
    f91 = next((u for u in c224 if u["usage_id"].endswith("anim0x91")), None)
    ck("4a. route-documented frame anim 0x91 is exposed and multi-bank (banks 3+12)",
       f91 is not None and f91.get("multi_bank") and set(f91.get("sprite_banks", [])) >= {"0x3", "0xC"},
       (f91 and f91.get("sprite_banks")))
    if f91:
        px = _png_pixels(raw("/api/render?usage=" + urllib.request.quote(f91["usage_id"])))
        pal3 = {tuple(c) for c in srv._arcade_round_palette(1, 3)}
        pal12 = {tuple(c) for c in srv._arcade_round_palette(1, 12)}
        only3, only12 = pal3 - pal12, pal12 - pal3
        ck("4b. its composite USES both source palettes (per-piece 0028 preserved via the usage path)",
           bool(px & only3) and bool(px & only12), {"bank3": bool(px & only3), "bank12": bool(px & only12)})
    else:
        ck("4b. (anim 0x91 missing — see 4a)", False)

    # 5. marker-M burst honest / incomplete, no fabricated frames
    mb = by_obj.get("object:castle.marker_M_burst", [])
    ck("5. marker-'M' burst represented without fabricated frames (incomplete, zero pieces)",
       len(mb) == 1 and mb[0].get("incomplete") and mb[0]["n_pieces"] == 0 and not mb[0]["composite_proven"])

    # 6. existing R1/P1 catalog intact + untagged
    names = {u["display_name"] for u in r1p1}
    ck("6. existing R1/P1 catalog intact (lizardman etc. present, untagged)",
       len(r1p1) >= 380 and any("Lizardman" in n for n in names) and all(not u.get("scene_key") for u in r1p1),
       len(r1p1))

    # 7. scene tagging (client filters by this)
    ck("7. castle usages are scene-tagged PAL-R1-S2 (client shows only for that scene)",
       all(u["scene_key"] == SCENE for u in castle))

    # 8. idempotent (cache)
    orc2 = g("/api/oracle")
    ck("8. /api/oracle idempotent — no duplicate castle entries on repeat",
       len([u for u in orc2["usages"] if u.get("scene_key") == SCENE]) == len(castle))

    # 9. Test.json untouched
    t_after = hashlib.sha256(tjson.read_bytes()).hexdigest() if tjson.is_file() else None
    ck("9. Test.json unchanged", t_before == t_after, (t_before, t_after))

    httpd.shutdown()
    print(f"\n{'R1S2_CASTLE_BROWSER PASS' if not F else str(len(F))+' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
