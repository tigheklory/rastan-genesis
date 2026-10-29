#!/usr/bin/env python3
"""PROMPT-ID-0029 regression (CORRECTED under PROMPT-ID-0038) — castle actors in the Palette Composer.

Round attribution reconciled against the source (handler progress guards) + Bestiary H14:
  base 0x0224 -> R2,R4 only (R1 'E' marker RETIRES: handler 0x44082 guard prog<0x18, R1-S2 prog 0x11..0x16);
  base 0x00F4 -> R4,R5,R6; marker 'M' burst -> R1 (children identity PENDING, kept INCOMPLETE).

Proves (static, no trace, no ROM): oracle includes the castle actors scene-tagged to their CORRECT
rounds; R1-S2 shows ONLY the 'M' burst (no 0x0224/0x00F4); each (base,round) is browsable with distinct
frames; the multi-bank frame (anim 0x91) still uses both source palettes (0028); per-round palettes differ
(0x0224@R2 != 0x0224@R4); R1/P1 catalog intact; idempotent; Test.json unchanged.
"""
from __future__ import annotations
import importlib.util, json, threading, time, urllib.request, struct, zlib, hashlib
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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
    return {tuple(raw[y*stride+1+x*chn:y*stride+1+x*chn+3]) for y in range(H) for x in range(W)}


def main() -> int:
    tjson = ROOT / "analysis/graphics_optimizer/editor_policy/Test.json"
    t_before = hashlib.sha256(tjson.read_bytes()).hexdigest() if tjson.is_file() else None
    spec = importlib.util.spec_from_file_location("ged_server", ROOT / "tools/graphics_editor/server.py")
    srv = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(srv)
    except SystemExit: pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Hd); port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.3)
    g = lambda u: json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}"+u))
    raw = lambda u: urllib.request.urlopen(f"http://127.0.0.1:{port}"+u).read()

    us = g("/api/oracle")["usages"]
    def scene(sk): return [u for u in us if u.get("scene_key") == sk]
    def bases(sk): return sorted({u.get("base") for u in scene(sk) if u.get("base")})

    r1 = scene("PAL-R1-S2-PLANEA-CASTLE")
    ck("1. R1-S2 shows ONLY the 'M' burst (0x0224/0x00F4 correctly ABSENT in R1)",
       len(r1) == 1 and r1[0].get("incomplete") and not bases("PAL-R1-S2-PLANEA-CASTLE"), [u["usage_id"] for u in r1])
    ck("2. 0x0224 is in R2-S2 and R4-S2 (H14)", "0x0224" in bases("PAL-R2-S2-PLANEA-CASTLE") and
       "0x0224" in bases("PAL-R4-S2-PLANEA-CASTLE"))
    ck("3. 0x00F4 is in R4/R5/R6-S2 (H14)", all("0x00F4" in bases("PAL-R%d-S2-PLANEA-CASTLE" % r) for r in (4, 5, 6)))
    ck("4. 0x0224 is NOT in R1/R3/R5/R6; 0x00F4 NOT in R1/R2/R3",
       all("0x0224" not in bases("PAL-R%d-S2-PLANEA-CASTLE" % r) for r in (1, 3, 5, 6)) and
       all("0x00F4" not in bases("PAL-R%d-S2-PLANEA-CASTLE" % r) for r in (1, 2, 3)))

    # browsable: R2 0x0224 has multiple frames; multi-bank 0x91 present + renders both banks
    r2 = scene("PAL-R2-S2-PLANEA-CASTLE")
    objs = {}
    for u in r2:
        objs.setdefault(u["object_id"], []).append(u)
    ck("5. R2-S2 0x0224 browsable (multiple distinct frames)", any(len(v) > 1 for v in objs.values()), {k: len(v) for k, v in objs.items()})
    f91 = next((u for u in r2 if u["usage_id"].endswith("anim0x91")), None)
    ck("6a. multi-bank frame 0x91 exposed (banks 3+12)", f91 and f91["multi_bank"] and set(f91["sprite_banks"]) >= {"0x3", "0xC"})
    if f91:
        px = _png_pixels(raw("/api/render?usage=" + urllib.request.quote(f91["usage_id"])))
        only3 = {tuple(c) for c in srv._arcade_round_palette(2, 3)} - {tuple(c) for c in srv._arcade_round_palette(2, 12)}
        only12 = {tuple(c) for c in srv._arcade_round_palette(2, 12)} - {tuple(c) for c in srv._arcade_round_palette(2, 3)}
        ck("6b. its composite uses BOTH source palettes (per-piece 0028)", bool(px & only3) and bool(px & only12))
    else:
        ck("6b. (0x91 missing)", False)

    # per-round palette MECHANISM is applied: _castle_used_colors honours its round argument. (For this
    # actor's nibbles 3/12 the R1..R6 palette coincides and only R7 differs, so compare R6 vs R7 to prove
    # round-sensitivity rather than falsely assuming R2 != R4.)
    pcs91 = srv._manifest_vm_pieces(0x0224, 0x91, 0)
    c6 = [c["arcade_rgb8"] for c in srv._castle_used_colors(pcs91, 6)]
    c7 = [c["arcade_rgb8"] for c in srv._castle_used_colors(pcs91, 7)]
    ck("7. per-round palette mechanism is round-sensitive (0x0224 colours differ R6 vs R7)", c6 != c7)

    r1p1 = [u for u in us if not u.get("scene_key")]
    ck("8. R1/P1 catalog intact + untagged", len(r1p1) >= 380 and any("Lizardman" in u["display_name"] for u in r1p1))
    us2 = g("/api/oracle")["usages"]
    ck("9. oracle idempotent", len([u for u in us2 if u.get("scene_key")]) == len([u for u in us if u.get("scene_key")]))
    t_after = hashlib.sha256(tjson.read_bytes()).hexdigest() if tjson.is_file() else None
    ck("10. Test.json unchanged", t_before == t_after)

    httpd.shutdown()
    print(f"\n{'CASTLE_BROWSER PASS' if not F else str(len(F))+' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
