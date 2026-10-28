#!/usr/bin/env python3
"""PROMPT-ID-0028 regression — per-piece arcade palette in the PC090OJ compositor.

Proves, for the chosen case base 0x0224 anim 0x91 (pieces span arcade palette nibbles 3 and 12):
  1. _manifest_vm_pieces preserves EACH piece's palette bank (both 3 and 12 present).
  2. attach_arcade_piece_palettes resolves each piece's OWN arcade colours (nibble 3 pal != nibble 12 pal).
  3. The composite actually USES both palettes (pixels coloured from the nibble-3 palette AND from the
     nibble-12 palette both appear in the rendered PNG) — not one shared palette, no invented colours.
  4. Single-bank behaviour is preserved: a frame with one nibble renders, and render_composite still
     honours a shared palette for pieces that carry no per-piece `pal`.
Static only (compositor VM + ROM palette math). No traces.
"""
from __future__ import annotations
import importlib.util, struct, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P, F = [], []
def ck(n, c, extra=""):
    (P if c else F).append(n); print(("PASS " if c else "FAIL ") + n + ((" -> " + str(extra)) if extra and not c else ""))

spec = importlib.util.spec_from_file_location("ged_server", ROOT / "tools/graphics_editor/server.py")
srv = importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(srv)
except SystemExit: pass


def png_pixels(blob):
    """Decode a truecolor (RGB) PNG from server.png into a flat set of (r,g,b) tuples present."""
    assert blob[:8] == b"\x89PNG\r\n\x1a\n"
    i, W, H, ct, idat = 8, None, None, None, b""
    while i < len(blob):
        ln = struct.unpack(">I", blob[i:i+4])[0]; typ = blob[i+4:i+8]; data = blob[i+8:i+8+ln]
        if typ == b"IHDR": W, H, _bd, ct = struct.unpack(">IIBB", data[:10])
        elif typ == b"IDAT": idat += data
        elif typ == b"IEND": break
        i += 12 + ln
    raw = zlib.decompress(idat); ch = 4 if ct == 6 else 3; stride = W*ch+1
    out = set()
    for y in range(H):
        row = raw[y*stride+1:(y+1)*stride]
        for x in range(W):
            out.add(tuple(row[x*ch:x*ch+3]))
    return out, W, H


def main() -> int:
    BASE, ANIM, RND = 0x0224, 0x91, 1
    pieces = srv._manifest_vm_pieces(BASE, ANIM, 0)
    nibs = sorted({p.get("palette") for p in pieces})
    ck("1. _manifest_vm_pieces preserves per-piece palette banks (nibbles 3 and 12 present)",
       pieces and 3 in nibs and 12 in nibs, nibs)

    pp = srv.attach_arcade_piece_palettes(pieces, RND)
    pal3 = srv._arcade_round_palette(RND, 3)
    pal12 = srv._arcade_round_palette(RND, 12)
    ck("2a. the two banks resolve to DIFFERENT arcade colours", pal3 != pal12)
    ck("2b. each piece carries its own resolved pal matching its nibble",
       all(pc.get("pal") == srv._arcade_round_palette(RND, pc["palette"]) for pc in pp))

    # colours that are UNIQUE to each bank (exclude shared entries so the test is unambiguous)
    set3 = {tuple(c) for c in pal3}; set12 = {tuple(c) for c in pal12}
    only3 = set3 - set12; only12 = set12 - set3
    px, W, H = png_pixels(srv.render_composite(pp, [[0, 0, 0]]*16))
    used3 = bool(px & only3); used12 = bool(px & only12)
    ck("3. composite USES both source palettes (pixels unique to bank 3 AND to bank 12 appear)",
       used3 and used12 and only3 and only12, {"used_bank3": used3, "used_bank12": used12,
                                                "n_only3": len(only3), "n_only12": len(only12)})

    # 4a. single-bank frame still renders with per-piece palettes (0x00F4 anim 0x70 -> single nibble 12)
    sp = srv.attach_arcade_piece_palettes(srv._manifest_vm_pieces(0x00F4, 0x70, 0), RND)
    sbpx, _, _ = png_pixels(srv.render_composite(sp, [[0, 0, 0]]*16))
    ck("4a. single-bank frame renders (non-empty, non-trivial)", len(sbpx) >= 3, len(sbpx))
    # 4b. render_composite still honours a SHARED pal for pieces with no per-piece `pal` (legacy path)
    legacy = [{"code": p["code"], "x": p["x"], "y": p["y"], "fx": p["fx"], "fy": p["fy"]} for p in pieces]
    shared = [[0, 0, 0]] + [[200, 50, 50]]*15
    lpx, _, _ = png_pixels(srv.render_composite(legacy, shared))
    ck("4b. shared-palette (single-bank) path unchanged: only the shared colour + backdrop appear",
       (200, 50, 50) in lpx and all(c in {(200, 50, 50), (30, 30, 38)} for c in lpx), sorted(lpx)[:4])

    print(f"\n{'PER_PIECE_PALETTE PASS' if not F else str(len(F))+' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
