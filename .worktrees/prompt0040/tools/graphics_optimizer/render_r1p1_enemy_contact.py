#!/usr/bin/env python3
"""Render the R1/P1 seven-enemy contact sheet from ORIGINAL-ARCADE evidence (analysis only, no production).

Sources of truth:
  - build/regions/pc090oj.bin  : arcade sprite cells (128 B/cell, 16x16, 4bpp Genesis-packed;
                                 format per tools/translation/preconvert_pc090oj_tiles.py).
  - build/regions/maincpu.bin  : arcade program. SPRITE PALETTE LOAD (traced FUN_0003ba20/56/64): the round
                                 index row at 0x3BA88+(round-1)*0x20 gives, for source-buffer bank k (=hw bank
                                 0x30+k), a pool index; palette = pool 0x4FD02 + pool_index*0x20 (16 words 0RGB).
                                 Converter FUN_0003ba64: 5-bit channel = nibble*2. MAME xBGR_555 display:
                                 RGB8 = pal5bit(nibble*2). Validated: bank 0x36 -> pool 13 -> 0x4FEA2 (green
                                 Lizardman, KF-1214). NOT direct-bank indexing. Index 0 = transparent.
  - flying_demon_trace/observations.csv : REAL emitted PC090OJ object records (arcade compositor OUTPUT:
                                 per piece word0/y/code/x). color=word0&0x0F, flipx=0x4000, flipy=0x8000,
                                 effective bank = 0x30 | (word0 & 0x0F). NO base+n, NO screenshots, NO Genesis CRAM.
"""
from __future__ import annotations
import csv, json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
MC = (ROOT / "build/regions/maincpu.bin").read_bytes()
SPR = (ROOT / "build/regions/pc090oj.bin").read_bytes()
CSV = ROOT / "analysis/graphics_optimizer/round1_phase1_corpus/flying_demon_trace/observations.csv"
OUTDIR = ROOT / "analysis/graphics_optimizer/round1_phase1_corpus"
SHEETS = OUTDIR / "contact_sheets"
SHEETS.mkdir(parents=True, exist_ok=True)
# Sprite palette load (traced from arcade FUN_0003ba20/FUN_0003ba56/FUN_0003ba64):
#   source buffer A5+0x1600 bank k (= hardware bank 0x30+k) is filled from ROM pool 0x4FD02 at
#   entry `pool_index`, where pool_index = INDEX_TABLE[(round-1)*0x20 + k]. Pool entries are 0x20 bytes
#   (16 words, 0RGB-nibble). Converter FUN_0003ba64: 5-bit channel = nibble*2; MAME xBGR_555 display uses
#   pal5bit -> RGB8 = pal5bit(nibble*2). Round 1 (round_byte=1) = index row 0. Validated: bank 0x36 -> pool 13.
POOL_BASE = 0x4FD02
INDEX_TABLE = 0x3BA88
ROUND = 1

# Seven R1/P1 enemies. selector = (block, base, mode3e-or-None, min_pieces). identity fields are PROVEN.
ENEMIES = [
    {"key": "lizardman", "name": "LIZARDMAN", "sel": ("actor_2c8", "004B", "00", 4),
     "id": "+0x3E=0 / base 0x004B (ordinary family)"},
    {"key": "four_armed", "name": "FOUR-ARMED INSECT", "sel": ("actor_2c8", "02E8", "03", 4),
     "id": "+0x3E=3 / base 0x02E8 (ordinary family)"},
    {"key": "valkyrie", "name": "VALKYRIE", "sel": ("actor_2c8", "0241", "08", 4),
     "id": "+0x3E=8 / base 0x0241 (ordinary family)"},
    {"key": "chimera", "name": "CHIMERA", "sel": ("actor_2c8", "00D0", "01", 4),
     "id": "+0x3E=1 / base 0x00D0 (ordinary family)"},
    {"key": "flying_demon", "name": "FLYING DEMON", "sel": ("actor_508", "0129", None, 6),
     "id": "special two-slot actor_508 / base 0x0129 (A=body, B=wings)"},
    {"key": "small_bat", "name": "SMALL BAT", "sel": ("actor_748", "0268", None, 1),
     "id": "actor_748 / base 0x0268 (single-cell aux)"},
    {"key": "large_bat", "name": "LARGE BAT", "sel": ("actor_5c8", "03F6", None, 3),
     "id": "actor_5c8 / base 0x03F6 (multi-cell aux)"},
]


def pal5bit(v):
    """MAME xBGR_555 5-bit -> 8-bit expansion (palette_device::xBGR_555, rastan.cpp)."""
    v &= 0x1F
    return (v << 3) | (v >> 2)


def palette_source(bank, round_number=ROUND):
    """Traced arcade path (FUN_0003ba20/56/64): round index row -> pool index -> pool palette.
    Returns (rgb8[16], meta). NO direct-bank indexing."""
    k = bank - 0x30
    row = INDEX_TABLE + (round_number - 1) * 0x20
    pool_index = MC[row + k]
    src = POOL_BASE + pool_index * 0x20
    raw = [int.from_bytes(MC[src + i * 2:src + i * 2 + 2], "big") for i in range(16)]  # 0RGB source words
    rgb8 = []
    for w in raw:
        rn, gn, bn = (w >> 8) & 0xF, (w >> 4) & 0xF, w & 0xF   # 0RGB nibbles
        rgb8.append((pal5bit(rn * 2), pal5bit(gn * 2), pal5bit(bn * 2)))  # 5-bit = nibble*2 -> pal5bit
    meta = {"hardware_bank": "0x%02X" % bank, "k": k, "round": round_number,
            "index_table_row": "0x%05X" % row, "pool_index": pool_index,
            "pool_source": "0x%05X" % src, "raw_0rgb_words": ["0x%04X" % w for w in raw]}
    return rgb8, meta


def palette(bank):
    return palette_source(bank)[0]


def palette_words(bank):
    return [int(w, 16) for w in palette_source(bank)[1]["raw_0rgb_words"]]


def cell_pixels(code):
    s = code * 128
    c = SPR[s:s + 128]
    px = []
    for y in range(16):
        for b in c[y * 8:(y + 1) * 8]:
            px.append((b >> 4) & 0xF)
            px.append(b & 0xF)
    return px


def parse_pieces(field):
    out = []
    for p in (field.split("|") if field else []):
        rec, w0, y, code, x = p.split(":")
        w0 = int(w0, 16); y = int(y, 16); code = int(code, 16); x = int(x, 16)
        if code == 0 or x >= 0x180 or y >= 0x180:
            continue
        out.append({"rec": int(rec), "code": code, "x": x, "y": y,
                    "flipx": bool(w0 & 0x4000), "flipy": bool(w0 & 0x8000), "color": w0 & 0xF})
    return out


def best_frame(rows, block, base, mode3e=None, index=None, min_pieces=4):
    best = None
    for r in rows:
        if r["block"] != block or r["base_code"] != base:
            continue
        if mode3e is not None and r["mode3e"] != mode3e:
            continue
        if index is not None and r["actor_index"] != index:
            continue
        ps = parse_pieces(r["piece_records"])
        if len(ps) >= min_pieces and (best is None or len(ps) > len(best[1])):
            best = (r, ps)
    return best if best else (None, None)


def _rel_positions(pieces):
    """Reconstruct each piece's position relative to a shared anchor, unwrapping the PC090OJ 9-bit
    coordinate space (mask 0x1ff) to the nearest offset so an actor near the screen-wrap boundary is
    not split. Composition-faithful (matches how pieces sit together on screen); screen-absolute
    placement is not needed for an isolated contact-sheet sprite."""
    ax, ay = pieces[0]["x"], pieces[0]["y"]

    def rel(v, a):
        return ((v - a + 0x100) & 0x1FF) - 0x100

    return {id(p): (rel(p["x"], ax), rel(p["y"], ay)) for p in pieces}


def render(pieces, bank, bg=(28, 28, 34)):
    pal = palette(bank)
    # PC090OJ draw order (rastan non-priority: offs high->low; painter's algo -> lowest record on top).
    # Reproduce by painting HIGHER records first, LOWER records last (on top). One shared anchor keeps
    # multi-actor composites (Flying Demon A+B) aligned.
    pieces = sorted(pieces, key=lambda p: -p["rec"])
    coords = _rel_positions(pieces)
    xs = [coords[id(p)][0] for p in pieces]; ys = [coords[id(p)][1] for p in pieces]
    min_x, min_y = min(xs), min(ys)
    w = max(xs) + 16 - min_x; h = max(ys) + 16 - min_y
    img = Image.new("RGB", (w, h), bg)
    px = img.load()
    for p in pieces:
        p_x, p_y = coords[id(p)]
        cp = cell_pixels(p["code"])
        for ty in range(16):
            sy = 15 - ty if p["flipy"] else ty
            for tx in range(16):
                sx = 15 - tx if p["flipx"] else tx
                v = cp[sy * 16 + sx]
                if v:
                    ox = p_x - min_x + tx; oy = p_y - min_y + ty
                    if 0 <= ox < w and 0 <= oy < h:
                        px[ox, oy] = pal[v]
    return img


def cellhash(code):
    return hashlib.sha1(SPR[code * 128:code * 128 + 128]).hexdigest()[:12]


def _font(sz, bold=True):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    return ImageFont.truetype(p, sz) if Path(p).exists() else ImageFont.load_default()


def main():
    rows = list(csv.DictReader(open(CSV)))
    scale = 4
    panels = []
    enemies_json = []
    palettes_json = {}
    patterns_json = {}
    fd_solo = None

    for e in ENEMIES:
        block, base, m, minp = e["sel"]
        if e["key"] == "flying_demon":
            # two components from a shared frame + solo cleanest frames
            fdf = {}
            for r in rows:
                if r["block"] == "actor_508" and r["base_code"] == "0129":
                    ps = parse_pieces(r["piece_records"])
                    if len(ps) >= minp:
                        fdf.setdefault(r["frame"], {})[r["actor_index"]] = ps
            shared = {f: d for f, d in fdf.items() if "0" in d and "1" in d}
            frame = max(shared, key=lambda f: len(shared[f]["0"]) + len(shared[f]["1"]))
            A = shared[frame]["0"]; B = shared[frame]["1"]; allp = A + B
            bank = 0x30 | A[0]["color"]
            img = render(allp, bank)
            imgS = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
            imgS.save(SHEETS / "enemy_flying_demon_combined.png")
            # solo components from the SAME clean shared frame so they read clearly
            ia = render(A, bank); ib = render(B, bank)
            fd_solo = (ia.resize((ia.width * scale, ia.height * scale), Image.NEAREST),
                       ib.resize((ib.width * scale, ib.height * scale), Image.NEAREST), imgS)
            fd_solo[0].save(SHEETS / "enemy_flying_demon_componentA.png")
            fd_solo[1].save(SHEETS / "enemy_flying_demon_componentB.png")
            codes = sorted(set(p["code"] for p in allp))
            meta = {"semantic_id": "FLYING_DEMON", "display_name": e["name"], "category": "ENEMY_HOSTILE",
                    "identity": e["id"], "actor_block": "actor_508 (special two-slot)", "base_code": "0x0129",
                    "actor_3e": "0x00 (special path; +0x38=0,+0x752=0,+0x27=0x80)",
                    "componentA": {"addr": "0x0010C508", "obj_records": "57-69", "role": "BODY (proven by render)"},
                    "componentB": {"addr": "0x0010C548", "obj_records": "70-82", "role": "WINGS (proven by render)"},
                    "compositor": "REAL emitted PC090OJ records; frame=%s" % frame,
                    "effective_sprite_bank": "0x%02X" % bank, "emitted_word0_nibble": "0x%X" % A[0]["color"]}
            enemies_json.append(meta); panels.append((e, imgS, bank))
            patterns_json["FLYING_DEMON"] = {"cell_codes": ["0x%03X" % c for c in codes],
                                             "physical_pattern_sha1_12": {"0x%03X" % c: cellhash(c) for c in codes}}
            palettes_json["FLYING_DEMON"] = pal_entry(bank)
            continue

        r, ps = best_frame(rows, block, base, m, min_pieces=minp)
        bank = 0x30 | ps[0]["color"]
        img = render(ps, bank)
        imgS = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        imgS.save(SHEETS / ("enemy_%s.png" % e["key"]))
        codes = sorted(set(p["code"] for p in ps))
        sid = e["name"].replace(" ", "_").replace("-", "_")
        enemies_json.append({
            "semantic_id": sid, "display_name": e["name"], "category": "ENEMY_HOSTILE",
            "identity": e["id"], "actor_block": block, "base_code": "0x" + base,
            "compositor": "REAL emitted PC090OJ records; frame=%s record=%s" % (r["frame"], r["record"]),
            "piece_count": len(ps), "cell_codes": ["0x%03X" % c for c in codes],
            "effective_sprite_bank": "0x%02X" % bank, "emitted_word0_nibble": "0x%X" % ps[0]["color"],
        })
        patterns_json[sid] = {"cell_codes": ["0x%03X" % c for c in codes],
                              "physical_pattern_sha1_12": {"0x%03X" % c: cellhash(c) for c in codes}}
        palettes_json[sid] = pal_entry(bank)
        panels.append((e, imgS, bank))

    build_primary(panels, SHEETS / "r1p1_enemies.png")
    if fd_solo:
        build_diagnostic(fd_solo, SHEETS / "r1p1_enemies_diagnostic.png")
    write_json(enemies_json, palettes_json, patterns_json)
    build_html(SHEETS / "r1p1_enemies.html", panels)
    print("wrote 7-enemy sheet + json (%d panels)" % len(panels))


def pal_entry(bank):
    rgb, meta = palette_source(bank)
    conv_words = []
    for w in [int(x, 16) for x in meta["raw_0rgb_words"]]:
        rn, gn, bn = (w >> 8) & 0xF, (w >> 4) & 0xF, w & 0xF
        conv_words.append("0x%04X" % (((bn * 2) << 10) | ((gn * 2) << 5) | (rn * 2)))  # xBGR555
    return {"effective_sprite_bank": "0x%02X" % bank, "round": meta["round"], "k": meta["k"],
            "index_table_row": meta["index_table_row"], "pool_index": meta["pool_index"],
            "pool_source": meta["pool_source"],
            "provenance": "PROVEN (arcade loader FUN_0003ba20/56/64): effective bank = emitted word0 nibble | "
                          "colbank 0x30; round-%d index row %s selects pool index %d at pool 0x4FD02; "
                          "validated vs KF-1214 bank 0x36 (green Lizardman)." % (
                              meta["round"], meta["index_table_row"], meta["pool_index"]),
            "transparent_index": 0,
            "format": "0RGB nibble source -> xBGR555 (5-bit channel = nibble*2, FUN_0003ba64); "
                      "display RGB8 = MAME pal5bit(nibble*2) = ((n*2)<<3)|((n*2)>>2)",
            "raw_0rgb_words": meta["raw_0rgb_words"],
            "converted_xbgr555_words": conv_words,
            "mame_display_rgb8": ["#%02X%02X%02X" % c for c in rgb]}


def build_primary(panels, path):
    title_f, name_f, small_f = _font(22), _font(18), _font(11, False)
    n = len(panels); colw = 210
    W = 20 + n * colw; H = 70 + 250 + 120
    im = Image.new("RGB", (W, H), (16, 16, 20)); d = ImageDraw.Draw(im)
    d.text((16, 16), "ROUND 1 / PHASE 1 ENEMIES  -  original-arcade composites; TRUE arcade palettes via round-1 index table 0x3BA88 -> pool 0x4FD02 (MAME xBGR_555)",
           font=title_f, fill=(235, 235, 240))
    for i, (e, img, bank) in enumerate(panels):
        x0 = 18 + i * colw
        d.text((x0, 58), e["name"], font=name_f, fill=(255, 220, 120))
        maxw, maxh = colw - 24, 240
        s = min(maxw / img.width, maxh / img.height, 1.0)
        disp = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.NEAREST)
        im.paste(disp, (x0, 84))
        ty = 84 + 250
        d.text((x0, ty), "bank %s" % ("0x%02X" % bank), font=small_f, fill=(200, 200, 210))
        # 16 swatches (8x2)
        pal = palette(bank); sw = 16
        for c in range(16):
            cx = x0 + (c % 8) * (sw + 2); cy = ty + 16 + (c // 8) * (sw + 2)
            d.rectangle([cx, cy, cx + sw, cy + sw], fill=pal[c],
                        outline=(90, 90, 90) if c else (200, 60, 60))
        d.text((x0, ty + 16 + 2 * (sw + 2) + 2), "idx0=transparent", font=small_f, fill=(180, 180, 190))
        d.text((x0, ty + 16 + 2 * (sw + 2) + 16), e["id"][:40], font=small_f, fill=(170, 170, 180))
    im.save(path)


def build_diagnostic(fd_solo, path):
    name_f, small_f = _font(18), _font(12, False)
    imgA, imgB, imgC = fd_solo
    cols = [("component_A @0x10C508 (rec 57-69) = BODY", imgA),
            ("component_B @0x10C548 (rec 70-82) = WINGS", imgB),
            ("A + B combined = one Flying Demon", imgC)]
    colw = 360; W = 24 + len(cols) * colw; H = 460
    im = Image.new("RGB", (W, H), (16, 16, 20)); d = ImageDraw.Draw(im)
    d.text((24, 14), "FLYING DEMON diagnostic - two co-located actor_508 components, true arcade palette bank 0x35",
           font=name_f, fill=(235, 235, 240))
    for i, (cap, img) in enumerate(cols):
        x0 = 24 + i * colw
        d.text((x0, 48), cap, font=small_f, fill=(255, 220, 120))
        s = min((colw - 30) / img.width, 320 / img.height, 1.5)
        disp = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.NEAREST)
        im.paste(disp, (x0, 74))
    d.text((24, H - 34), "PROVEN BY RENDER: component_A draws the body/legs/sword; component_B draws the two wings. "
           "Neutral component_A/B identifiers retained.", font=small_f, fill=(200, 200, 210))
    im.save(path)


def build_html(path, panels):
    cells = ""
    for e, img, bank in panels:
        src = "enemy_flying_demon_combined.png" if e["key"] == "flying_demon" else "enemy_%s.png" % e["key"]
        cells += '<figure><img src="%s"><figcaption>%s<br>bank 0x%02X</figcaption></figure>' % (src, e["name"], bank)
    path.write_text("""<!doctype html><meta charset=utf8><title>R1/P1 Enemies</title>
<style>body{background:#12121a;color:#eee;font:14px sans-serif}figure{display:inline-block;margin:12px;text-align:center;vertical-align:top}
img{image-rendering:pixelated;background:#1c1c22;height:220px}figcaption{color:#ffd070;margin-top:6px}</style>
<h2>Round 1 / Phase 1 &mdash; seven enemies with TRUE arcade palettes</h2>
<p>Rendered from pc090oj.bin + real emitted PC090OJ records; palettes via arcade round-1 index table 0x3BA88 -> pool 0x4FD02 (converter FUN_0003ba64, MAME xBGR_555). PC090OJ draw order: lower record on top. No base+n, no screenshots, no Genesis evidence.</p>
""" + cells + '<h3>Flying Demon diagnostic</h3><img src="r1p1_enemies_diagnostic.png" style="height:auto;max-width:100%">')


def write_json(enemies_json, palettes_json, patterns_json):
    (OUTDIR / "enemies.json").write_text(json.dumps({
        "task": "R1/P1 seven-enemy graphics + palette corpus (analysis only)",
        "source_of_truth": "pc090oj.bin + real emitted records + arcade palette loader (round index 0x3BA88 -> pool 0x4FD02, FUN_0003ba64, MAME xBGR_555); PC090OJ draw order lower-record-on-top",
        "enemies": enemies_json,
        "note": "7/7 identities proven; effective banks + exact 16-color palettes proven from arcade ROM. "
                "No base+n, no screenshot colors, no Genesis-CRAM colors.",
    }, indent=1))
    (OUTDIR / "enemy_patterns.json").write_text(json.dumps(patterns_json, indent=1))
    (OUTDIR / "enemy_palettes.json").write_text(json.dumps({
        "palette_source": "arcade round-specific index table 0x3BA88+(round-1)*0x20 selects a pool index; "
                          "palette = pool 0x4FD02 + pool_index*0x20 (FUN_0003ba20/56/64); NOT direct-bank; "
                          "validated vs KF-1214 bank 0x36 (round-1 pool index 13 @ 0x4FEA2, green Lizardman).",
        "banks": palettes_json,
    }, indent=1))


if __name__ == "__main__":
    main()
