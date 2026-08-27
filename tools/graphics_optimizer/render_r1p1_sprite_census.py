#!/usr/bin/env python3
"""R1/P1 complete sprite census from the CAPTURED original-arcade trace (analysis only, no production).

Closes every sprite producer present in the saved trace's 5 actor blocks (actor_2c8/508/5c8/748/8c8),
using the accepted arcade pipeline: pc090oj.bin cells + REAL emitted PC090OJ records + round-1 index
table 0x3BA88 -> pool 0x4FD02 (FUN_0003ba64) + MAME xBGR_555 pal5bit; PC090OJ priority = lower record on top.

NOT covered here (not in the saved trace; require an armed capture of A5+0x11B2 player block, records 0-45
HUD, and item/weapon blocks): PLAYER, WEAPONS (sword/Flame Sword/Flail), AXE/ITEMS, HUD. See design doc.

Category/name classification is by actor block + rendered appearance; visual NAMES are flagged user_verify.
"""
from __future__ import annotations
import csv, json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
MC = (ROOT / "build/regions/maincpu.bin").read_bytes()
SPR = (ROOT / "build/regions/pc090oj.bin").read_bytes()
CORP = ROOT / "analysis/graphics_optimizer/round1_phase1_corpus"
CSV = CORP / "flying_demon_trace/observations.csv"
SHEETS = CORP / "contact_sheets"
INDEX_TABLE, POOL, RND = 0x3BA88, 0x4FD02, 1

# Classification of CAPTURED trace producers. key = (block, base, mode3e-or-"*").
# cat: ENEMY (accepted 7), ENEMY_FORM (anim form of a named enemy), HAZARD, PROJECTILE, EFFECT.
CLASS = {
    ("actor_2c8", "004B", "*"): ("ENEMY", "Lizardman", False),
    ("actor_2c8", "02E8", "03"): ("ENEMY", "Four-armed insect", False),
    ("actor_2c8", "0241", "08"): ("ENEMY", "Valkyrie", True),
    ("actor_2c8", "00D0", "01"): ("ENEMY", "Chimera", False),
    ("actor_508", "0129", "*"): ("ENEMY", "Flying Demon", False),
    ("actor_748", "0268", "*"): ("ENEMY", "Small Bat", True),
    ("actor_5c8", "03F6", "*"): ("ENEMY", "Large Bat", True),
    ("actor_2c8", "0A73", "00"): ("ENEMY_FORM", "Lizardman (anim form)", False),
    ("actor_2c8", "0A73", "03"): ("ENEMY_FORM", "Four-armed insect (anim form)", False),
    ("actor_2c8", "0A73", "01"): ("ENEMY_FORM", "Chimera (anim form)", False),
    ("actor_2c8", "0A73", "08"): ("EFFECT", "Valkyrie burst/hit effect", True),
    ("actor_508", "0275", "*"): ("ENEMY_FORM", "Flying Demon (anim form)", False),
    ("actor_5c8", "0275", "*"): ("ENEMY_FORM", "Large Bat (anim form)", True),
    ("actor_2c8", "00F4", "00"): ("HAZARD", "Animated swinging rope/chain", True),
    ("actor_2c8", "0179", "00"): ("HAZARD", "Destroyable cave-entrance block (SPRITE)", False),
    ("actor_5c8", "0D5F", "00"): ("HAZARD", "Boulder", True),
    ("actor_5c8", "050B", "00"): ("PROJECTILE", "spear/harpoon projectile", True),
    ("actor_748", "019D", "00"): ("PROJECTILE", "fireball/orb projectile", True),
    ("actor_748", "02E8", "00"): ("PROJECTILE", "projectile (four-armed?)", True),
    ("actor_2c8", "0A5A", "0C"): ("EFFECT", "glow orb effect", True),
    ("actor_748", "0275", "00"): ("EFFECT", "burst effect", True),
}
CAT_ORDER = ["ENEMY", "ENEMY_FORM", "HAZARD", "PROJECTILE", "EFFECT"]


def pal5(v):
    v &= 0x1F
    return (v << 3) | (v >> 2)


def palette(bank, rnd=RND):
    k = bank - 0x30
    pi = MC[INDEX_TABLE + (rnd - 1) * 0x20 + k]
    a = POOL + pi * 0x20
    out = []
    for i in range(16):
        w = int.from_bytes(MC[a + i * 2:a + i * 2 + 2], "big")
        out.append((pal5(((w >> 8) & 0xF) * 2), pal5(((w >> 4) & 0xF) * 2), pal5((w & 0xF) * 2)))
    return out, pi, a


def cell(c):
    s = c * 128
    d = SPR[s:s + 128]
    px = []
    for y in range(16):
        for b in d[y * 8:(y + 1) * 8]:
            px.append((b >> 4) & 0xF)
            px.append(b & 0xF)
    return px


def parse(f):
    o = []
    for p in (f.split("|") if f else []):
        rec, w0, y, code, x = p.split(":")
        w0 = int(w0, 16); y = int(y, 16); code = int(code, 16); x = int(x, 16)
        if code == 0 or x >= 0x180 or y >= 0x180:
            continue
        o.append({"rec": int(rec), "code": code, "x": x, "y": y,
                  "fx": bool(w0 & 0x4000), "fy": bool(w0 & 0x8000), "col": w0 & 0xF})
    return o


def render(ps, bank):
    pal = palette(bank)[0]
    ps = sorted(ps, key=lambda p: -p["rec"])
    ax, ay = ps[0]["x"], ps[0]["y"]
    rel = lambda v, a: ((v - a + 0x100) & 0x1FF) - 0x100
    pos = {id(p): (rel(p["x"], ax), rel(p["y"], ay)) for p in ps}
    xs = [pos[id(p)][0] for p in ps]; ys = [pos[id(p)][1] for p in ps]
    mnx, mny = min(xs), min(ys); w = max(xs) + 16 - mnx; h = max(ys) + 16 - mny
    im = Image.new("RGB", (w, h), (30, 30, 38)); pix = im.load()
    for p in ps:
        rx, ry = pos[id(p)]; cp = cell(p["code"])
        for ty in range(16):
            sy = 15 - ty if p["fy"] else ty
            for tx in range(16):
                sx = 15 - tx if p["fx"] else tx
                v = cp[sy * 16 + sx]
                if v:
                    ox = rx - mnx + tx; oy = ry - mny + ty
                    if 0 <= ox < w and 0 <= oy < h:
                        pix[ox, oy] = pal[v]
    return im


def classify(block, base, m):
    for key in ((block, base, m), (block, base, "*")):
        if key in CLASS:
            return CLASS[key]
    return ("UNCLASSIFIED", "%s/%s 3e=%s" % (block, base, m), True)


def font(sz):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", sz)


def main():
    rows = list(csv.DictReader(open(CSV)))
    prod = {}
    for r in rows:
        ps = parse(r["piece_records"])
        if not ps:
            continue
        k = (r["block"], r["base_code"], r["mode3e"])
        cur = prod.get(k)
        # collect all cell codes across the whole trace; keep best (max-piece) frame for render
        entry = prod.setdefault(k, {"best": None, "codes": set(), "records": set(), "sections": set()})
        for p in ps:
            entry["codes"].add(p["code"]); entry["records"].add(p["rec"])
        entry["sections"].add(r["record"])
        if entry["best"] is None or len(ps) > len(entry["best"][1]):
            entry["best"] = (r, ps)

    sprites = []
    for k, e in prod.items():
        block, base, m = k
        cat, name, uv = classify(block, base, m)
        r, ps = e["best"]
        bank = 0x30 | ps[0]["col"]
        pal, pool_idx, pool_src = palette(bank)
        img = render(ps, bank)
        key = ("%s_%s_%s" % (block.replace("actor_", ""), base, m)).lower()
        img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(SHEETS / ("census_%s.png" % key))
        sprites.append({
            "semantic_id": key, "display_name": name, "category": cat, "user_verify_name": uv,
            "actor_block": block, "base_code": "0x" + base, "mode3e": "0x" + m,
            "sections_records": sorted(e["sections"], key=lambda v: int(v)),
            "emitted_records": sorted(e["records"]),
            "cell_codes": ["0x%03X" % c for c in sorted(e["codes"])],
            "physical_pattern_sha1_12": {"0x%03X" % c: hashlib.sha1(SPR[c * 128:c * 128 + 128]).hexdigest()[:12]
                                         for c in sorted(e["codes"])},
            "emitted_word0_nibble": "0x%X" % ps[0]["col"], "effective_sprite_bank": "0x%02X" % bank,
            "round": RND, "pool_index": pool_idx, "pool_source": "0x%05X" % pool_src,
            "mame_display_rgb8": ["#%02X%02X%02X" % c for c in pal],
            "compositor": "REAL emitted PC090OJ records (frame %s); PC090OJ priority lower-record-on-top" % r["frame"],
            "render": "contact_sheets/census_%s.png" % key,
        })

    # ---- categorized contact sheet ----
    by = {c: [s for s in sprites if s["category"] == c] for c in CAT_ORDER}
    by["UNCLASSIFIED"] = [s for s in sprites if s["category"] == "UNCLASSIFIED"]
    build_sheet(by)

    # ---- machine-readable ----
    (CORP / "sprite_census_captured.json").write_text(json.dumps({
        "scope": "CAPTURED R1/P1 trace producers only (5 actor blocks). PLAYER/WEAPONS/AXE-ITEMS/HUD NOT captured.",
        "pipeline": "pc090oj.bin + real emitted records + round-1 index 0x3BA88 -> pool 0x4FD02 + FUN_0003ba64 + MAME xBGR_555 pal5bit; lower-record-on-top",
        "counts": {c: len(by.get(c, [])) for c in CAT_ORDER + ["UNCLASSIFIED"]},
        "sprites": sprites,
        "not_captured_pending_armed_trace": ["PLAYER (A5+0x11B2, rec120-137)", "HUD (rec0-45)",
                                             "WEAPONS: normal sword / Flame Sword / Flail", "AXE + item pickups"],
    }, indent=1))
    print("census: %d producers; categories %s" % (len(sprites), {c: len(by.get(c, [])) for c in CAT_ORDER}))
    for c in CAT_ORDER + ["UNCLASSIFIED"]:
        for s in by.get(c, []):
            print("  [%s] %-30s %s bank %s%s" % (c, s["display_name"], s["semantic_id"],
                  s["effective_sprite_bank"], "  (USER VERIFY)" if s["user_verify_name"] else ""))


def build_sheet(by):
    tf, nf, sf = font(20), font(13), font(10)
    colw, rowh = 200, 168
    cats = [c for c in CAT_ORDER + ["UNCLASSIFIED"] if by.get(c)]
    maxcols = max(len(by[c]) for c in cats)
    W = 40 + maxcols * colw
    H = 60 + len(cats) * rowh
    im = Image.new("RGB", (W, H), (16, 16, 20)); d = ImageDraw.Draw(im)
    d.text((16, 16), "ROUND 1 / PHASE 1 CAPTURED SPRITES (real arcade palettes) - world objects; PLAYER/WEAPONS/ITEMS/HUD pending armed capture",
           font=tf, fill=(235, 235, 240))
    for ri, c in enumerate(cats):
        y0 = 56 + ri * rowh
        d.text((10, y0), c, font=nf, fill=(255, 200, 90))
        for ci, s in enumerate(by[c]):
            x0 = 40 + ci * colw
            img = Image.open(SHEETS / s["render"].split("/")[-1])
            sc = min((colw - 20) / img.width, (rowh - 54) / img.height, 3.0)
            disp = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.NEAREST)
            im.paste(disp, (x0, y0 + 16))
            label = s["display_name"][:26] + ("*" if s["user_verify_name"] else "")
            d.text((x0, y0 + rowh - 34), label, font=sf, fill=(230, 220, 140))
            d.text((x0, y0 + rowh - 22), "bank %s  %s" % (s["effective_sprite_bank"], s["base_code"]), font=sf, fill=(180, 180, 190))
    d.text((16, H - 14), "* = semantic name is a visual ID (USER MUST VERIFY)", font=sf, fill=(200, 160, 120))
    im.save(SHEETS / "r1p1_all_sprites.png")


if __name__ == "__main__":
    main()
