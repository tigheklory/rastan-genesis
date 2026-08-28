#!/usr/bin/env python3
"""Palette / Tile-Line Assignment Editor V0.2 — interactive palette composer server (TOOLING ONLY).

Read-only arcade oracle + editable per-profile Genesis policy. Adds real per-USAGE used-color decode,
pixel-based must-remain-distinct (MRD), palette-accurate source/target rendering, and legal Genesis CRAM.
Oracle never written; baseline immutable; bad_item_images_quarantine art never previewed; Build counter 313.
"""
import json, os, struct, zlib, hashlib, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(__file__)
CORP = os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1_corpus")
ORACLE = os.path.join(ROOT, "analysis/graphics_optimizer/arcade_graphics_oracle")
ANALYZER = os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1")
POLICY_DIR = os.path.join(ROOT, "analysis/graphics_optimizer/editor_policy")
os.makedirs(POLICY_DIR, exist_ok=True)
LV3 = [0, 36, 73, 109, 146, 182, 219, 255]
_SPR = None

# ---- CRAM line ownership (Build-0313 capture evidence): Line 2 = accepted Layer-B time-of-day, PROTECTED ----
RESERVED_LINES = [2]
EDITABLE_LINES = [0, 1, 3]
LINE_OWNERS = {
    "0": {"owner": "editable", "control": "editor", "editable": True, "optimizer_available": True},
    "1": {"owner": "editable", "control": "editor", "editable": True, "optimizer_available": True},
    "2": {"owner": "layer_b", "control": "arcade", "editable": False, "optimizer_available": False,
          "label": "LINE 2 — LAYER B — ARCADE CONTROLLED — PROTECTED",
          "note": "Owned by the accepted Layer-B time-of-day palette path in Build 0313; excluded from editor optimization."},
    "3": {"owner": "editable", "control": "editor", "editable": True, "optimizer_available": True}}


def loadj(p, d=None):
    try:
        return json.load(open(p))
    except Exception:
        return d


def spr():
    global _SPR
    if _SPR is None:
        _SPR = open(os.path.join(ROOT, "build/regions/pc090oj.bin"), "rb").read()
    return _SPR


def cell_indices(code):
    s = code * 128
    c = spr()[s:s + 128]
    px = []
    for y in range(16):
        for b in c[y * 8:(y + 1) * 8]:
            px.append((b >> 4) & 0xF)
            px.append(b & 0xF)
    return px  # 256 4-bit indices


def gen_quant(rgb):
    lv = [max(0, min(7, round(c / 255 * 7))) for c in rgb]
    disp = [LV3[n] for n in lv]
    cram = (lv[2] << 9) | (lv[1] << 5) | (lv[0] << 1)
    return disp, "0x%04X" % cram, lv


# ---- sprite bank colors: enemy_palettes (0x32/34/35/3A/3E...) + palette_states (0x33 Rastan, 0x30, 0x36) ----
def sprite_bank_colors():
    banks = {}
    ep = loadj(os.path.join(CORP, "enemy_palettes.json"), {"banks": {}})
    for sid, sb in ep.get("banks", {}).items():
        b = sb.get("effective_sprite_bank")
        rgbs = sb.get("mame_display_rgb8", [])
        if b and rgbs:
            banks[int(b, 16)] = [[int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)] for h in rgbs]
    pstates = loadj(os.path.join(ANALYZER, "palette_states.json"), {"palettes": []})
    for p in pstates.get("palettes", []):
        banks.setdefault(p["bank"], [e["arcade_rgb"] for e in p["entries"]])
    return banks


_CSVROWS = None
def _trace_rows():
    """Real emitted PC090OJ records from the accepted capture (code + x/y + flip) — TRUE composition."""
    global _CSVROWS
    if _CSVROWS is None:
        import csv
        p = os.path.join(CORP, "flying_demon_trace/observations.csv")
        _CSVROWS = list(csv.DictReader(open(p))) if os.path.exists(p) else []
    return _CSVROWS


def _pieces(field):
    out = []
    for p in (field.split("|") if field else []):
        rec, w0, y, code, x = p.split(":")
        w0 = int(w0, 16); y = int(y, 16); code = int(code, 16); x = int(x, 16)
        if code == 0 or x >= 0x180 or y >= 0x180:
            continue
        out.append({"rec": int(rec), "code": code, "x": x, "y": y,
                    "fx": bool(w0 & 0x4000), "fy": bool(w0 & 0x8000)})
    return out


def _best_frame(block, base, m=None, index=None, minp=4):
    best = None
    for r in _trace_rows():
        if r["block"] != block or r["base_code"] != base:
            continue
        if m is not None and r["mode3e"] != m:
            continue
        if index is not None and r["actor_index"] != index:
            continue
        ps = _pieces(r["piece_records"])
        if len(ps) >= minp and (best is None or len(ps) > len(best)):
            best = ps
    return best or []


def _rel_pieces(pieces):
    """Anchor-relative (unwrap PC090OJ 9-bit coords) so a screen-edge actor isn't split; sort high-rec first."""
    if not pieces:
        return []
    pieces = sorted(pieces, key=lambda p: -p["rec"])
    ax, ay = pieces[0]["x"], pieces[0]["y"]
    rel = lambda v, a: ((v - a + 0x100) & 0x1FF) - 0x100
    out = []
    for p in pieces:
        out.append({"code": p["code"], "x": rel(p["x"], ax), "y": rel(p["y"], ay), "fx": p["fx"], "fy": p["fy"]})
    return out


_CAP = None
def _capture_player_pieces(frame):
    """Real Rastan body pieces at a frame from the accepted full capture (records 120-131, bank 0x33)."""
    global _CAP
    if _CAP is None:
        import csv
        p = os.path.join(CORP, "full_capture/full_observations.csv")
        _CAP = list(csv.DictReader(open(p))) if os.path.exists(p) else []
    out = []
    for r in _CAP:
        if int(r["frame"]) != frame:
            continue
        rec = int(r["record"])
        if not (120 <= rec <= 131):
            continue
        w0 = int(r["w0"], 16); y = int(r["y"], 16); code = int(r["code"], 16); x = int(r["x"], 16)
        if code == 0 or x >= 0x180 or y >= 0x180 or (w0 & 0xF) != 3:
            continue
        out.append({"rec": rec, "code": code, "x": x, "y": y, "fx": bool(w0 & 0x4000), "fy": bool(w0 & 0x8000)})
    return out


# ---------- shared-palette solver ----------
def _de00(a, b):
    def lab(rgb):
        r, g, bl = [c / 255 for c in rgb]
        f = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
        r, g, bl = f(r), f(g), f(bl)
        X = (r * .4124 + g * .3576 + bl * .1805) / .95047
        Y = r * .2126 + g * .7152 + bl * .0722
        Z = (r * .0193 + g * .1192 + bl * .9505) / 1.08883
        import math
        gg = lambda t: t ** (1 / 3) if t > .008856 else 7.787 * t + 16 / 116
        fx, fy, fz = gg(X), gg(Y), gg(Z)
        return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))
    import math
    L1, a1, b1 = lab(a); L2, a2, b2 = lab(b)
    C1 = math.hypot(a1, b1); C2 = math.hypot(a2, b2); Cb = (C1 + C2) / 2
    G = .5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb else 0
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h = lambda x, y: (math.degrees(math.atan2(y, x)) + 360) % 360
    h1, h2 = h(a1p, b1), h(a2p, b2)
    dLp = L2 - L1; dCp = C2p - C1p
    dhp = 0
    if C1p * C2p:
        dhp = h2 - h1
        dhp -= 360 if dhp > 180 else (-360 if dhp < -180 else 0)
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp = (L1 + L2) / 2; Cbp = (C1p + C2p) / 2
    hbp = h1 + h2
    if C1p * C2p and abs(h1 - h2) > 180:
        hbp += 360 if h1 + h2 < 360 else -360
    hbp /= 2
    T = 1 - .17 * math.cos(math.radians(hbp - 30)) + .24 * math.cos(math.radians(2 * hbp)) + .32 * math.cos(math.radians(3 * hbp + 6)) - .20 * math.cos(math.radians(4 * hbp - 63))
    Sl = 1 + (.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + .045 * Cbp; Sh = 1 + .015 * Cbp * T
    Rt = -math.sin(math.radians(2 * 30 * math.exp(-(((hbp - 275) / 25) ** 2)))) * 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


import math
def _oklab(rgb):
    r, g, b = [c / 255 for c in rgb]
    f = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    r, g, b = f(r), f(g), f(b)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, A, B


def _oklch(rgb):
    L, A, B = _oklab(rgb)
    C = math.hypot(A, B)
    h = (math.degrees(math.atan2(B, A)) + 360) % 360
    return L, C, h


_NEUTRAL_C = 0.02   # OKLCH chroma below this = neutral; its hue is ignored in midpoints
def _hue_center(rgbs):
    """Chroma-weighted circular hue mean (shortest-arc); returns (hue_or_None, spread_deg)."""
    xs = ys = 0.0
    hs = []
    for rgb in rgbs:
        L, C, h = _oklch(rgb)
        if C >= _NEUTRAL_C:
            xs += C * math.cos(math.radians(h)); ys += C * math.sin(math.radians(h)); hs.append(h)
    if not hs:
        return None, 0.0
    center = (math.degrees(math.atan2(ys, xs)) + 360) % 360
    def diff(a, b):
        d = abs(a - b) % 360
        return min(d, 360 - d)
    spread = max((diff(a, b) for a in hs for b in hs), default=0.0)
    return center, spread


def _ang(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


_LEGAL = [[LV3[R], LV3[G], LV3[B]] for R in range(8) for G in range(8) for B in range(8)]
def _best_cram(members):
    """target minimizing (max ΔE, then pixel-weighted mean) over legal Genesis colors."""
    best = None
    for rgb in _LEGAL:
        des = [_de00(m[0], rgb) for m in members]
        worst = max(des)
        wmean = sum(d * m[1] for d, m in zip(des, members)) / max(1, sum(m[1] for m in members))
        key = (round(worst, 4), round(wmean, 4))
        if best is None or key < best[0]:
            R = rgb[0] and LV3.index(rgb[0]) or 0
            r = LV3.index(rgb[0]); g = LV3.index(rgb[1]); b = LV3.index(rgb[2])
            best = (key, "0x%04X" % ((b << 9) | (g << 5) | (r << 1)), worst, wmean, rgb)
    return best


def solve_group(usages):
    """Cluster used colors across usages (never two from one usage) into <=15 target entries; best legal CRAM each."""
    nodes = []  # (usage_key, src_index, rgb, pixels, natcram)
    for u in usages:
        for c in u["used_colors"]:
            nodes.append([u["usage_id"], c["src_index"], c["arcade_rgb8"], c["pixel_count"], c["genesis_cram"]])
    # each node its own cluster; greedily merge cross-usage pairs (exact -> natural -> low ΔE), never same-usage in a cluster
    clusters = [[n] for n in nodes]
    def usages_in(cl):
        return set(m[0] for m in cl)

    def try_merge(threshold, only_exact=False, only_nat=False):
        merged = True
        while merged:
            merged = False
            best = None
            for i in range(len(clusters)):
                for jx in range(i + 1, len(clusters)):
                    if usages_in(clusters[i]) & usages_in(clusters[jx]):
                        continue
                    # candidate merge cost = max pairwise ΔE among all members
                    d = max(_de00(a[2], b[2]) for a in clusters[i] for b in clusters[jx])
                    if only_exact and any(a[2] != b[2] for a in clusters[i] for b in clusters[jx]):
                        continue
                    if only_nat and any(a[4] != b[4] for a in clusters[i] for b in clusters[jx]):
                        continue
                    if d <= threshold and (best is None or d < best[0]):
                        best = (d, i, jx)
            if best:
                _, i, jx = best
                clusters[i] += clusters[jx]
                del clusters[jx]
                merged = True

    try_merge(0.01, only_exact=True)
    try_merge(0.01, only_nat=True)
    # if still >15, merge closest cross-usage pairs regardless (perceptual) until <=15
    perceptual = 0.0
    while len(clusters) > 15:
        best = None
        for i in range(len(clusters)):
            for jx in range(i + 1, len(clusters)):
                if usages_in(clusters[i]) & usages_in(clusters[jx]):
                    continue
                d = max(_de00(a[2], b[2]) for a in clusters[i] for b in clusters[jx])
                if best is None or d < best[0]:
                    best = (d, i, jx)
        if best is None:
            break  # cannot merge further without violating MRD
        perceptual = max(perceptual, best[0])
        _, i, jx = best
        clusters[i] += clusters[jx]
        del clusters[jx]
    feasible = len(clusters) <= 15
    entries = []
    for ci, cl in enumerate(clusters):
        members = [(m[2], m[3]) for m in cl]
        _, cram, worst, wmean, rgb = _best_cram(members)
        entries.append({"target_index": ci + 1, "cram": cram, "rgb": rgb, "worst_de": round(worst, 2),
                        "wmean_de": round(wmean, 2), "members": [{"usage_id": m[0], "src_index": m[1],
                        "rgb": m[2], "pixels": m[3], "de": round(_de00(m[2], rgb), 2)} for m in cl]})
    # per-object metrics
    per = {}
    for u in usages:
        des = []
        for e in entries:
            for m in e["members"]:
                if m["usage_id"] == u["usage_id"]:
                    des.append((m["de"], m["pixels"]))
        if des:
            per[u["usage_id"]] = {"worst_de": round(max(d for d, _ in des), 2),
                                  "wmean_de": round(sum(d * p for d, p in des) / max(1, sum(p for _, p in des)), 2)}
    return {"feasible": feasible, "entries_used": len(clusters), "entries": entries, "per_object": per,
            "worst_perceptual_merge": round(perceptual, 2),
            "method": "greedy constrained clustering (exact->natural->nearest cross-usage); BEST SOLUTION FOUND (not proven global optimum)"}


_CHROMA_TOL = 0.10   # target chroma may differ from median source chroma by at most this (OKLCH)
def _natural_cram(rgb):
    r = min(range(8), key=lambda k: abs(LV3[k] - rgb[0]))
    g = min(range(8), key=lambda k: abs(LV3[k] - rgb[1]))
    b = min(range(8), key=lambda k: abs(LV3[k] - rgb[2]))
    return "0x%04X" % ((b << 9) | (g << 5) | (r << 1)), [LV3[r], LV3[g], LV3[b]]


def _best_cram_lh(members, de_limit=20.0, hue_tol=10.0):
    """HUE-SAFE luminance-first target. ADMISSIBILITY FIRST (ΔE<=limit, target hue inside source arc±tol,
    chroma sane), THEN lightness-first ranking. Returns None (NO VALID TARGET) if nothing is admissible.
    A single source always falls back to its own natural quantization (hue-safe by construction)."""
    rgbs = [m[0] for m in members]
    Ls = [_oklch(r)[0] for r in rgbs]
    Cs = sorted(_oklch(r)[1] for r in rgbs)
    desiredC = Cs[len(Cs) // 2]
    chrom = [_oklch(r)[2] for r in rgbs if _oklch(r)[1] >= _NEUTRAL_C]  # hues of chromatic members
    hueC, spread = _hue_center(rgbs)
    best = None
    for rgb in _LEGAL:
        tL, tC, tH = _oklch(rgb)
        des = [_de00(m[0], rgb) for m in members]
        if max(des) > de_limit:                                  # (1) catastrophic ΔE backstop
            continue
        if chrom and not _hue_in_arc(tH, chrom, hue_tol):        # (2) target hue must stay in source family
            continue
        if chrom and abs(tC - desiredC) > _CHROMA_TOL:           # (3) chroma sanity
            continue
        dLs = [abs(l - tL) for l in Ls]
        worstL = max(dLs); meanL = sum(dLs) / len(dLs)
        hueErr = _ang(hueC, tH) if hueC is not None else 0.0
        key = (round(worstL, 4), round(meanL, 4), round(hueErr, 1), round(abs(desiredC - tC), 3),
               round(max(des), 3), round(sum(des) / len(des), 3))   # lightness-first among ADMISSIBLE
        if best is None or key < best[0]:
            best = (key, _natural_cram(rgb)[0], max(des), sum(des) / len(des), rgb, worstL, meanL, hueC, spread, tH)
    if best is None:
        if len(members) == 1:                                     # guaranteed-safe self quantization
            cram, rgb = _natural_cram(rgbs[0])
            tL, tC, tH = _oklch(rgb)
            return ((0, 0, 0, 0, _de00(rgbs[0], rgb), _de00(rgbs[0], rgb)), cram, _de00(rgbs[0], rgb),
                    _de00(rgbs[0], rgb), rgb, abs(Ls[0] - tL), abs(Ls[0] - tL), hueC, spread, tH)
        return None                                               # NO VALID TARGET -> cluster inadmissible
    return best


def _min_hue_arc(hues):
    """Smallest circular arc (deg) covering all hues (correct wrap: 350,5,15 -> 25 not 345)."""
    if len(hues) < 2:
        return 0.0
    hs = sorted(hues)
    gaps = [(hs[(i + 1) % len(hs)] - hs[i]) % 360 for i in range(len(hs))]
    return 360 - max(gaps)


def _cluster(usages, rank, fit_entries=15, legal=None):
    """Constrained clustering: never 2 colors from one domain; merge by `rank` ascending until <=fit.
    `legal(clusterA, clusterB)` may veto a perceptual merge (hue-safety for the luminance/hue solver)."""
    nodes = []
    for u in usages:
        for c in u["used_colors"]:
            nodes.append([u["usage_id"], c["src_index"], c["arcade_rgb8"], c["pixel_count"], c["genesis_cram"]])
    clusters = [[n] for n in nodes]
    usin = lambda cl: set(m[0] for m in cl)
    # exact-RGB + natural first (lossless), then rank-driven merges only as needed to fit (Fidelity)
    def merge_pass(pred):
        changed = True
        while changed:
            changed = False
            best = None
            for i in range(len(clusters)):
                for jx in range(i + 1, len(clusters)):
                    if usin(clusters[i]) & usin(clusters[jx]):
                        continue
                    ok, cost = pred(clusters[i], clusters[jx])
                    if ok and (best is None or cost < best[0]):
                        best = (cost, i, jx)
            if best:
                _, i, jx = best; clusters[i] += clusters[jx]; del clusters[jx]; changed = True
    merge_pass(lambda a, b: (all(x[2] == y[2] for x in a for y in b), 0))
    merge_pass(lambda a, b: (all(x[4] == y[4] for x in a for y in b), 0))
    worst_merge = 0.0
    while len(clusters) > fit_entries:
        best = None
        for i in range(len(clusters)):
            for jx in range(i + 1, len(clusters)):
                if usin(clusters[i]) & usin(clusters[jx]):
                    continue
                if legal and not legal(clusters[i], clusters[jx]):
                    continue
                cost = max(rank(x[2], y[2]) for x in a2(clusters, i) for y in a2(clusters, jx))
                if best is None or cost < best[0]:
                    best = (cost, i, jx)
        if best is None:
            break  # cannot merge further without violating MRD or hue-safety
        worst_merge = max(worst_merge, best[0]); _, i, jx = best; clusters[i] += clusters[jx]; del clusters[jx]
    return clusters, worst_merge


def a2(clusters, i):
    return clusters[i]


def _hue_in_arc(h, hues, tol):
    if not hues:
        return True
    hs = sorted(hues)
    gaps = [(hs[(i + 1) % len(hs)] - hs[i]) % 360 for i in range(len(hs))]
    start = hs[(gaps.index(max(gaps)) + 1) % len(hs)]  # arc begins after the largest gap
    span = 360 - max(gaps)
    off = (h - start) % 360
    return off <= span + tol or off >= 360 - tol


def _collapse_domains(usages):
    """Collapse multiple preview representations of one semantic object (same object_id) into ONE palette domain:
    union used colors (max pixels) + union MRD. Preview frames must not multiply a domain's palette participation."""
    by = {}
    for u in usages:
        d = by.setdefault(u["object_id"], {"usage_id": "domain:" + u["object_id"], "object_id": u["object_id"],
                                           "display_name": u["display_name"].split(" (")[0], "cols": {}, "reps": [],
                                           "sprite_bank": u["sprite_bank"], "pieces": u["pieces"], "bounds": u["bounds"]})
        d["reps"].append(u["usage_id"])
        for c in u["used_colors"]:
            k = tuple(c["arcade_rgb8"])
            if k not in d["cols"] or c["pixel_count"] > d["cols"][k]["pixel_count"]:
                d["cols"][k] = c
    out = []
    for d in by.values():
        uc = list(d["cols"].values())
        # union MRD: every pair of the domain's distinct colors co-occurs somewhere in its representations
        idxs = [c["src_index"] for c in uc]
        mrd = [[a, b] for i, a in enumerate(idxs) for b in idxs[i + 1:]]
        out.append({"usage_id": d["usage_id"], "object_id": d["object_id"], "display_name": d["display_name"],
                    "used_colors": uc, "mrd_pairs": mrd, "n_used": len(uc), "sprite_bank": d["sprite_bank"],
                    "pieces": d["pieces"], "bounds": d["bounds"], "representations": d["reps"]})
    return out


def solve_group(usages, mode="delta_e", fit_entries=15, hue_limit=45.0, de_limit=20.0, hue_tol=10.0):
    """mode='delta_e' (perceptual) or 'luminance_hue' (lightness-first, HUE-SAFE). Collapses preview reps to domains."""
    usages = _collapse_domains(usages)
    if mode == "luminance_hue":
        rank = lambda a, b: abs(_oklch(a)[0] - _oklch(b)[0])
        def legal(ca, cb):
            rgbs = [m[2] for m in (ca + cb)]
            ch = [_oklch(r)[2] for r in rgbs if _oklch(r)[1] >= _NEUTRAL_C]
            if len(ch) >= 2 and _min_hue_arc(ch) > hue_limit:    # cluster hue-span gate
                return False
            best = _best_cram_lh([(m[2], m[3]) for m in (ca + cb)], de_limit, hue_tol)
            return best is not None                              # a hue-safe legal target must exist
    else:
        rank = lambda a, b: _de00(a, b)
        legal = None
    clusters, worst_merge = _cluster(usages, rank, fit_entries, legal)
    feasible = len(clusters) <= fit_entries
    entries = []
    for ci, cl in enumerate(clusters):
        members = [(m[2], m[3]) for m in cl]
        if mode == "luminance_hue":
            res = _best_cram_lh(members, de_limit, hue_tol)
            if res is None:                       # no hue-safe target: keep members as separate safe singletons
                for m in cl:
                    r2 = _best_cram_lh([(m[2], m[3])], de_limit, hue_tol)
                    _, cram, worst, wmean, rgb, worstL, meanL, hueC, spread, tH = r2
                    entries.append(dict(target_index=len(entries) + 1, cram=cram, rgb=rgb, worst_de=round(worst, 2),
                                        wmean_de=round(wmean, 2), worst_dL=round(worstL, 4), mean_dL=round(meanL, 4),
                                        target_hue=round(tH, 1), hue_spread=0.0, src_hue_center=None,
                                        members=[{"usage_id": m[0], "src_index": m[1], "rgb": m[2], "pixels": m[3],
                                                  "de": round(_de00(m[2], rgb), 2),
                                                  "dL": round(abs(_oklch(m[2])[0] - _oklch(rgb)[0]), 4),
                                                  "src_hue": round(_oklch(m[2])[2], 1)}]))
                continue
            _, cram, worst, wmean, rgb, worstL, meanL, hueC, spread, tH = res
            extra = {"worst_dL": round(worstL, 4), "mean_dL": round(meanL, 4),
                     "target_hue": round(tH, 1), "hue_spread": round(spread, 1),
                     "src_hue_center": (round(hueC, 1) if hueC is not None else None)}
        else:
            key, cram, worst, wmean, rgb = _best_cram(members)
            worstL = max(abs(_oklch(m[0])[0] - _oklch(rgb)[0]) for m in members)
            extra = {"worst_dL": round(worstL, 4)}
        entries.append(dict(target_index=ci + 1, cram=cram, rgb=rgb, worst_de=round(worst, 2), wmean_de=round(wmean, 2),
                            members=[{"usage_id": m[0], "src_index": m[1], "rgb": m[2], "pixels": m[3],
                                      "de": round(_de00(m[2], rgb), 2), "dL": round(abs(_oklch(m[2])[0] - _oklch(rgb)[0]), 4),
                                      "src_hue": round(_oklch(m[2])[2], 1)} for m in cl], **extra))
    per = {}
    for u in usages:
        des = []; dls = []
        for e in entries:
            for m in e["members"]:
                if m["usage_id"] == u["usage_id"]:
                    des.append((m["de"], m["pixels"])); dls.append(m["dL"])
        if des:
            per[u["usage_id"]] = {"worst_de": round(max(d for d, _ in des), 2),
                                  "wmean_de": round(sum(d * p for d, p in des) / max(1, sum(p for _, p in des)), 2),
                                  "worst_dL": round(max(dls), 4)}
    feasible = len(entries) <= fit_entries        # recompute: safe splits may raise the entry count
    return {"solver": mode, "feasible": feasible, "entries_used": len(entries), "safe_entries_required": len(entries),
            "one_line_capacity": fit_entries, "entries": entries, "per_object": per,
            "worst_perceptual_merge": round(worst_merge, 2),
            "settings": {"hue_limit": hue_limit, "de_limit": de_limit, "hue_tol": hue_tol, "neutral_c": _NEUTRAL_C},
            "method": ("luminance-first (OKLab ΔL) HUE-SAFE clustering + admissibility-gated legal CRAM" if mode == "luminance_hue"
                       else "perceptual ΔE00 clustering + best-legal CRAM") + "; BEST SOLUTION FOUND"}


def build_usages(banks):
    """One usage per enemy/Rastan: REAL composite pieces (from the accepted trace) + used colors + pixel MRD."""
    BANK = {"LIZARDMAN": 0x36, "FOUR_ARMED_INSECT": 0x3A, "VALKYRIE": 0x32, "CHIMERA": 0x34,
            "FLYING_DEMON": 0x35, "SMALL_BAT": 0x3E, "LARGE_BAT": 0x3E}
    # (key, name, bank, composite pieces, proven)
    defs = []
    defs.append(("lizardman", "Lizardman", 0x36, _rel_pieces(_best_frame("actor_2c8", "004B", "00")), True))
    defs.append(("four_armed_insect", "Four-Armed Insect", 0x3A, _rel_pieces(_best_frame("actor_2c8", "02E8", "03")), True))
    defs.append(("valkyrie", "Valkyrie", 0x32, _rel_pieces(_best_frame("actor_2c8", "0241", "08")), True))
    defs.append(("chimera", "Chimera", 0x34, _rel_pieces(_best_frame("actor_2c8", "00D0", "01")), True))
    defs.append(("small_bat", "Small Bat", 0x3E, _rel_pieces(_best_frame("actor_748", "0268", None, minp=1)), True))
    defs.append(("large_bat", "Large Bat", 0x3E, _rel_pieces(_best_frame("actor_5c8", "03F6", None, minp=3)), True))
    # Flying Demon: two components (body idx0 + wings idx1) from one shared frame
    fd = {}
    for r in _trace_rows():
        if r["block"] == "actor_508" and r["base_code"] == "0129":
            ps = _pieces(r["piece_records"])
            if len(ps) >= 6:
                fd.setdefault(r["frame"], {})[r["actor_index"]] = ps
    shared = {f: d for f, d in fd.items() if "0" in d and "1" in d}
    fd_pieces = []
    if shared:
        frame = max(shared, key=lambda f: len(shared[f]["0"]) + len(shared[f]["1"]))
        fd_pieces = _rel_pieces(shared[frame]["0"] + shared[frame]["1"])
    defs.append(("flying_demon", "Flying Demon (body+wings)", 0x35, fd_pieces, True))
    # Rastan BODY true composites from the accepted full capture (records 120-131, bank 0x33, real x/y/flip)
    for key, frame, label in [("rastan_f7722", 7722, "Rastan body (frame 07722)"),
                              ("rastan_f15828", 15828, "Rastan body (frame 15828)"),
                              ("rastan_f16199", 16199, "Rastan body (frame 16199)")]:
        ps = _capture_player_pieces(frame)
        if ps:
            defs.append((key, label, 0x33, _rel_pieces(ps), True))

    usages = []
    for key, name, bank, pieces, proven in defs:
        pal = banks.get(bank)
        if not pal or not pieces:
            continue
        used = {}
        for p in pieces:
            for v in cell_indices(p["code"]):
                if v:
                    used[v] = used.get(v, 0) + 1
        used_colors = []
        for idx in sorted(used):
            rgb = pal[idx] if idx < len(pal) else [0, 0, 0]
            disp, cram, _ = gen_quant(rgb)
            used_colors.append({"src_index": idx, "arcade_rgb8": rgb, "hex": "#%02X%02X%02X" % tuple(rgb),
                                "pixel_count": used[idx], "genesis_rgb8": disp, "genesis_cram": cram})
        idxs = [u["src_index"] for u in used_colors]
        mrd_pairs = [[a, b] for i, a in enumerate(idxs) for b in idxs[i + 1:]]
        xs = [p["x"] for p in pieces]; ys = [p["y"] for p in pieces]
        bounds = [max(xs) - min(xs) + 16, max(ys) - min(ys) + 16]
        usages.append({"usage_id": "usage:%s:bank0x%02X" % (key, bank),
                       "object_id": ("object:player.rastan" if key.startswith("rastan") else "object:enemy.%s" % key),
                       "display_name": name, "sprite_bank": "0x%02X" % bank,
                       "pieces": pieces, "n_pieces": len(pieces), "bounds": bounds,
                       "composite_proven": proven,
                       "preview_type": "TRUE ARCADE COMPOSITE" if proven else "PROVEN CELL SHEET",
                       "used_colors": used_colors, "mrd_pairs": mrd_pairs, "n_used": len(used_colors)})
    return usages


# ---------- Layer A (PC080SN plane) complete corpus ----------
_PC080 = None
def pc080():
    global _PC080
    if _PC080 is None:
        _PC080 = open(os.path.join(ROOT, "build/regions/pc080sn.bin"), "rb").read()
    return _PC080


def tile_indices8(code):
    """Decode one 8x8 4bpp PC080SN tile (32 bytes @ code*32) -> 64 nibble indices, high-nibble-first.
    Matches the authoritative decoder in tools/audit_round1_phase1_plane_a.py."""
    s = code * 32
    c = pc080()[s:s + 32]
    px = []
    for b in c:
        px.append((b >> 4) & 0xF)
        px.append(b & 0xF)
    return px


def plane_bank_colors():
    """11 Layer-A source palette banks (arcade RGB8), keyed by hex id (0x003..0x01D).

    AUTHORITY: original-arcade palette RAM 0x200000 captured at R1/P1 gameplay
    (plane_a_palette_ram_arcade.json), validated byte-exact (16/16) against KF-788's arcade-runtime
    bank-3 evidence. This SUPERSEDES plane_palette_banks.json, whose Layer-A RGB contents were proven
    wrong (bank 0x003 matched the runtime only 1/16 — green/gray instead of the true purple cave rock)."""
    p = loadj(os.path.join(CORP, "plane_a_palette_ram_arcade.json"), None)
    if p and p.get("banks"):
        return {bid: bb["arcade_rgb8"] for bid, bb in p["banks"].items()}
    # fallback only if the arcade-RAM capture is unavailable
    p = loadj(os.path.join(CORP, "plane_palette_banks.json"), {"banks": {}})
    return {bid: [e["arcade_rgb8"] for e in bb["entries"]] for bid, bb in p.get("banks", {}).items()}


_LAYERA = None
def build_layera():
    """Complete R1/P1 Layer-A corpus: every physical pattern + every logical usage from the frozen census.
    physical_pattern (sha256 of the 32 raw tile bytes) is authoritative identity; ~1:1 with tile_code."""
    global _LAYERA
    if _LAYERA is not None:
        return _LAYERA
    pa = loadj(os.path.join(ANALYZER, "plane_a_uses.json"), [])
    all_banks = plane_bank_colors()
    used_bank_ids = sorted({u["palette_bank_hex"] for u in pa},
                           key=lambda h: int(h, 16))                       # 11 banks actually used by Layer A
    byhash = {}
    for i, u in enumerate(pa):
        byhash.setdefault(u["physical_pattern"], []).append((i, u))
    order = sorted(byhash.items(), key=lambda kv: min(u["tile_code"] for _, u in kv[1]))
    hash2pid = {}
    patterns = []
    for pidx, (h, us) in enumerate(order):
        pid = "A-%04d" % pidx
        hash2pid[h] = pid
        rep = min(u["tile_code"] for _, u in us)
        idx = tile_indices8(rep)
        used_idx = sorted(set(v for v in idx if v))
        pbanks = sorted({u["palette_bank_hex"] for _, u in us}, key=lambda x: int(x, 16))
        segs = sorted({r for _, u in us for r in u.get("records", [])})
        flips = sorted({u.get("flip", 0) for _, u in us})
        codes = sorted({u["tile_code"] for _, u in us})
        patterns.append({
            "pattern_id": pid, "pattern_hash": h, "rep_tile_code": rep, "tile_codes": codes,
            "usage_ids": ["LA-%04d" % i for i, _ in us], "n_uses": len(us),
            "palette_banks": pbanks, "n_palettes": len(pbanks), "multi_palette": len(pbanks) > 1,
            "segments": segs, "flips": flips, "used_indices": used_idx, "n_colors": len(used_idx),
            "animation_status": ("MULTI-PALETTE" if len(pbanks) > 1 else "STATIC")})
    usages = []
    for i, u in enumerate(pa):
        uid = "LA-%04d" % i
        idx = tile_indices8(u["tile_code"])
        used_idx = sorted(set(v for v in idx if v))
        usages.append({
            "usage_id": uid, "pattern_id": hash2pid[u["physical_pattern"]],
            "pattern_hash": u["physical_pattern"], "tile_code": u["tile_code"],
            "tile_code_hex": u["tile_code_hex"], "palette_bank": u["palette_bank_hex"],
            "flip": u.get("flip", 0), "priority_bits": u.get("priority_bits"),
            "segments": u.get("records", []), "map_cell_count": u.get("map_cell_count"),
            "coordinate_samples": u.get("coordinate_samples", [])[:8],
            "source_address": u.get("source_address"),
            "used_indices": used_idx, "n_colors": len(used_idx)})
    _LAYERA = {"patterns": patterns, "usages": usages, "hash2pid": hash2pid,
               "banks": {b: all_banks[b] for b in used_bank_ids if b in all_banks},
               "bank_ids": used_bank_ids,
               "counts": {"physical_patterns": len(patterns), "logical_usages": len(usages),
                          "palette_banks": len(used_bank_ids),
                          "multi_palette_patterns": sum(1 for p in patterns if p["multi_palette"])}}
    return _LAYERA


def layera_pattern_detail(pid):
    """Full detail for one physical pattern: pixels, every logical usage, and every palette variant."""
    la = build_layera()
    pat = next((p for p in la["patterns"] if p["pattern_id"] == pid), None)
    if pat is None:
        return None
    idx = tile_indices8(pat["rep_tile_code"])
    uses = [u for u in la["usages"] if u["pattern_id"] == pid]

    def used_colors_for(bank_id):
        pal = la["banks"].get(bank_id, [[0, 0, 0]] * 16)
        cols = []
        for si in pat["used_indices"]:
            rgb = pal[si] if si < len(pal) else [0, 0, 0]
            disp, cram, _ = gen_quant(rgb)
            cols.append({"src_index": si, "arcade_rgb8": rgb, "hex": "#%02X%02X%02X" % tuple(rgb),
                         "genesis_rgb8": disp, "genesis_cram": cram})
        return cols

    variants = [{"palette_bank": b, "colors": used_colors_for(b),
                 "full_bank": [{"index": k, "arcade_rgb8": (la["banks"].get(b, [[0, 0, 0]] * 16)[k]),
                                "used": k in pat["used_indices"]} for k in range(16)]}
                for b in pat["palette_banks"]]
    # per-usage: used colors (under that usage's bank) + pixel MRD pairs
    detailed_uses = []
    for u in uses:
        cols = used_colors_for(u["palette_bank"])
        ui = u["used_indices"]
        mrd = [[a, b] for j, a in enumerate(ui) for b in ui[j + 1:]]
        detailed_uses.append({**u, "used_colors": cols, "mrd_pairs": mrd})
    return {"pattern": pat, "pixels": idx, "usages": detailed_uses, "palette_variants": variants}


# ---- authoritative R1/P1 Layer-A segment map (reconstructed from arcade maincpu tables, NOT screenshots) ----
_MAP_BASES = (0x1691C, 0x18BDC, 0x1AE9C, 0x1D15C, 0x1F41C, 0x216DC, 0x2399C, 0x25C5C,
              0x27F1C, 0x2A1DC, 0x2C49C, 0x2E75C, 0x30A1C, 0x32CDC, 0x34F9C, 0x3725C)
_MAP_STRIDE = 0x40
_MAP_ROWS, _MAP_COLS = 64, 64          # COMPLETE PC080SN backing tilemap domain per segment (64x64)
_MAP_VIS_ROW0, _MAP_VIS_NROWS = 1, 30  # normal fixed Phase-1 visible viewport (rows 1..30), highlight only
_MAINCPU = None
_MAPCACHE = {}
def _maincpu():
    global _MAINCPU
    if _MAINCPU is None:
        _MAINCPU = open(os.path.join(ROOT, "build/regions/maincpu.bin"), "rb").read()
    return _MAINCPU


def layera_map(seg):
    """Reconstruct one R1/P1 Layer-A segment's COMPLETE assembled backing tilemap (64x64) from the arcade
    maincpu tables. Every nonblank cell resolves to its exact logical usage (tile_code + palette_bank).
    The complete vertical domain is exposed (not just the 30-row screen viewport) so terrain in the lower
    rows is editable; the normal viewport is reported for optional highlight only."""
    if seg in _MAPCACHE:
        return _MAPCACHE[seg]
    m = _maincpu()
    be = lambda o: int.from_bytes(m[o:o + 2], "big")
    la = build_layera()
    bybank = {}
    for u in la["usages"]:
        bybank.setdefault((u["tile_code"], u["palette_bank"]), u)
    cells = []
    codes = set()
    descriptor_cells = blank_cells = 0
    for wr in range(_MAP_ROWS):
        ti, dr = divmod(wr, 4)
        tb = _MAP_BASES[ti] + seg * _MAP_STRIDE
        for sc in range(_MAP_COLS):
            dc, ds = divmod(sc, 4)
            entry = tb + dc * 4
            attr = be(entry); desc = be(entry + 2)
            if desc == 0:
                continue
            descriptor_cells += 1
            code = be(desc + dr * 8 + ds * 2) & 0x3FFF
            if not any(tile_indices8(code)):     # fully-transparent (blank) tile — counted, not emitted
                blank_cells += 1
                continue
            bank = "0x%03X" % (attr & 0x1FF)
            u = bybank.get((code, bank))
            cells.append({"c": sc, "r": wr, "code": code, "bank": bank,
                          "hf": 1 if attr & 0x4000 else 0, "vf": 1 if attr & 0x8000 else 0,
                          "attr": "0x%04X" % attr, "entry": "0x%06X" % entry,
                          "descr": "0x%06X" % (desc + dr * 8 + ds * 2),
                          "uid": (u["usage_id"] if u else None), "pid": (u["pattern_id"] if u else None)})
            codes.add(code)
    tiles = {str(c): tile_indices8(c) for c in codes}
    out = {"seg": seg, "cols": _MAP_COLS, "rows": _MAP_ROWS, "row0": 0, "nrows": _MAP_ROWS,
           "visible_viewport": {"row0": _MAP_VIS_ROW0, "nrows": _MAP_VIS_NROWS},
           "total_cells": _MAP_ROWS * _MAP_COLS, "descriptor_cells": descriptor_cells,
           "blank_cells": blank_cells, "nonblank_cells": len(cells),
           "resolved": sum(1 for c in cells if c["uid"]),
           "unresolved": sum(1 for c in cells if not c["uid"]),
           "tiles": tiles, "cells": cells}
    _MAPCACHE[seg] = out
    return out


def composite_hitmap(pieces):
    """Source-index buffer for a sprite composite using the SAME painter's order/geometry as render_composite.
    Returns (W, H, flat[list]) where each pixel is the topmost visible source index (0 = transparent)."""
    if not pieces:
        return 2, 2, [0, 0, 0, 0]
    minx = min(p["x"] for p in pieces); miny = min(p["y"] for p in pieces)
    W = max(p["x"] for p in pieces) + 16 - minx + 2
    H = max(p["y"] for p in pieces) + 16 - miny + 2
    buf = [0] * (W * H)
    for p in sorted(pieces, key=lambda q: -q.get("rec", 0)):   # high rec first, low rec paints on top
        idx = cell_indices(p["code"])
        ox = p["x"] - minx + 1; oy = p["y"] - miny + 1
        for y in range(16):
            sy = 15 - y if p["fy"] else y
            for x in range(16):
                sx = 15 - x if p["fx"] else x
                v = idx[sy * 16 + sx]
                if v:
                    buf[(oy + y) * W + (ox + x)] = v
    return W, H, buf


def _hungarian(cost):
    """Min-cost perfect assignment on a square matrix (O(n^3)); returns row->col. stdlib only."""
    n = len(cost)
    if n == 0:
        return []
    INF = float("inf")
    u = [0.0] * (n + 1); v = [0.0] * (n + 1); p = [0] * (n + 1); way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i; j0 = 0
        minv = [INF] * (n + 1); used = [False] * (n + 1)
        while True:
            used[j0] = True; i0 = p[j0]; delta = INF; j1 = -1
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur; way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]; j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta; v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]; p[j0] = p[j1]; j0 = j1
    assign = [0] * n
    for j in range(1, n + 1):
        if p[j] > 0:
            assign[p[j] - 1] = j - 1
    return assign


def phase_layera_automap(line, target_colors):
    """Map EVERY R1/P1 Layer-A logical usage onto the fixed populated entries of one Genesis line.
    Per usage: injective (MRD=0) min-cost assignment of its used arcade colors -> populated target entries,
    cost = pixel-weighted CIEDE2000. Target colors are NOT changed. Usages needing more distinct colors than
    the line has populated entries are BLOCKED (never merged)."""
    la = build_layera()
    banks = la["banks"]
    # populated nontransparent target entries (index 1..15) with their RGB
    tgt = []
    for i in range(1, 16):
        c = target_colors[i] if i < len(target_colors) else None
        if c:
            rgb = list(_cram_rgb(c))
            tgt.append((i, rgb))
    proposals = []
    summary = {"considered": 0, "mapped": 0, "blocked": 0, "populated_targets": len(tgt),
               "worst_de": 0.0, "sum_de": 0.0, "de_count": 0}
    worst_list = []
    for u in la["usages"]:
        summary["considered"] += 1
        pal = banks.get(u["palette_bank"], [[0, 0, 0]] * 16)
        idx = tile_indices8(u["tile_code"])
        counts = {}
        for v in idx:
            if v:
                counts[v] = counts.get(v, 0) + 1
        srcs = [(si, pal[si] if si < len(pal) else [0, 0, 0], counts[si]) for si in sorted(counts)]
        if not srcs:
            continue
        if len(srcs) > len(tgt):
            summary["blocked"] += 1
            proposals.append({"usage_id": u["usage_id"], "blocked": True,
                              "reason": "needs %d colors, line has %d" % (len(srcs), len(tgt))})
            continue
        n = len(tgt)
        cost = [[0.0] * n for _ in range(n)]
        for r in range(n):
            for cc in range(n):
                if r < len(srcs):
                    cost[r][cc] = srcs[r][2] * _de00(srcs[r][1], tgt[cc][1])  # pixel-weighted ΔE00
                else:
                    cost[r][cc] = 0.0                                          # dummy source rows
        assign = _hungarian(cost)
        index_map = {}
        des = []
        for r in range(len(srcs)):
            ti, trgb = tgt[assign[r]]
            index_map[srcs[r][0]] = ti
            de = _de00(srcs[r][1], trgb)
            des.append(de)
        worst = max(des); mean = sum(des) / len(des)
        summary["mapped"] += 1
        summary["sum_de"] += mean; summary["de_count"] += 1
        summary["worst_de"] = max(summary["worst_de"], worst)
        proposals.append({"usage_id": u["usage_id"], "line": line, "index_map": index_map,
                          "worst_de": round(worst, 2), "mean_de": round(mean, 2)})
        worst_list.append((worst, u["usage_id"], u["pattern_id"], round(mean, 2)))
    worst_list.sort(reverse=True)
    summary["mean_de"] = round(summary["sum_de"] / max(1, summary["de_count"]), 2)
    summary["worst_de"] = round(summary["worst_de"], 2)
    return {"line": line, "proposals": proposals, "summary": summary,
            "worst": [{"worst_de": round(w, 2), "usage_id": uid, "pattern_id": pid, "mean_de": m}
                      for w, uid, pid, m in worst_list[:20]]}


def _cram_rgb(cram):
    w = int(cram, 16) if isinstance(cram, str) else int(cram)
    R = (w >> 1) & 7; G = (w >> 5) & 7; B = (w >> 9) & 7
    return LV3[R], LV3[G], LV3[B]


def layera_solver_usages(ids):
    """Build solve_group-shaped usage dicts for selected Layer-A logical usages (LA-NNNN).
    Each logical usage is its own palette domain; used_colors + pixel MRD come from the real tile pixels."""
    la = build_layera()
    want = set(ids)
    byid = {u["usage_id"]: u for u in la["usages"]}
    out = []
    for uid in ids:
        u = byid.get(uid)
        if not u:
            continue
        pal = la["banks"].get(u["palette_bank"], [[0, 0, 0]] * 16)
        idx = tile_indices8(u["tile_code"])
        counts = {}
        for v in idx:
            if v:
                counts[v] = counts.get(v, 0) + 1
        used_colors = []
        for si in sorted(counts):
            rgb = pal[si] if si < len(pal) else [0, 0, 0]
            disp, cram, _ = gen_quant(rgb)
            used_colors.append({"src_index": si, "arcade_rgb8": rgb, "hex": "#%02X%02X%02X" % tuple(rgb),
                                "pixel_count": counts[si], "genesis_rgb8": disp, "genesis_cram": cram})
        sidx = [c["src_index"] for c in used_colors]
        mrd = [[a, b] for i, a in enumerate(sidx) for b in sidx[i + 1:]]
        out.append({"usage_id": uid, "object_id": "plane:" + uid, "display_name": "%s %s (bank %s)" %
                    (u["pattern_id"], u["tile_code_hex"], u["palette_bank"]), "sprite_bank": u["palette_bank"],
                    "pieces": [{"code": u["tile_code"], "x": 0, "y": 0, "fx": False, "fy": False}],
                    "bounds": [8, 8], "used_colors": used_colors, "mrd_pairs": mrd, "n_used": len(used_colors)})
    return out


def render_tile8(code, pal, zoom=8):
    """Render one 8x8 tile at integer nearest-neighbor zoom through the supplied 16-color palette."""
    idx = tile_indices8(code)
    W = H = 8 * zoom
    rows = []
    for y in range(8):
        row = []
        for x in range(8):
            v = idx[y * 8 + x]
            c = [30, 30, 38] if v == 0 else (pal[v] if v < len(pal) else [255, 0, 255])
            row.extend(c * zoom)
        for _ in range(zoom):
            rows.append(list(row))
    return png(W, H, rows)


def build_oracle():
    banks = sprite_bank_colors()
    plane = loadj(os.path.join(CORP, "plane_palette_banks.json"), {"banks": {}})
    contexts = loadj(os.path.join(ORACLE, "contexts.json"), {"contexts": [], "context_types": []})
    objects = loadj(os.path.join(ORACLE, "objects.json"), {"objects": []})
    coex = loadj(os.path.join(ORACLE, "coexistence.json"), {})
    usages = build_usages(banks)
    # palette resources (sprite banks + plane banks) with content hashes
    palettes = []
    groups = {}
    def add_pal(pid, selector, domain, colors, source=None):
        entries = []
        for i, rgb in enumerate(colors):
            disp, cram, _ = gen_quant(rgb)
            entries.append({"index": i, "arcade_rgb8": rgb, "hex": "#%02X%02X%02X" % tuple(rgb),
                            "genesis_rgb8": disp, "genesis_cram": cram})
        ch = hashlib.sha1(json.dumps(colors).encode()).hexdigest()[:12]
        groups.setdefault(ch, []).append(pid)
        palettes.append({"palette_id": pid, "arcade_selector": selector, "domain": domain,
                         "content_id": ch, "source": source, "entries": entries})
    for b, cols in sorted(banks.items()):
        add_pal("palette:sprite.bank_0x%02X" % b, "0x%02X" % b, "sprite", cols)
    # Layer-A (11 banks) RGB authority = corrected arcade palette RAM; other plane banks (e.g. Layer-B 0x002)
    # keep plane_palette_banks.json metadata. Never re-expose the superseded Layer-A RGB here.
    layera = plane_bank_colors()
    for bid, cols in sorted(layera.items()):
        add_pal("palette:plane.bank_%s" % bid, bid, "plane", cols, "ORIGINAL ARCADE palette RAM 0x200000 (plane_a_palette_ram_arcade.json)")
    for bid, bb in plane.get("banks", {}).items():
        if bid in layera:
            continue
        add_pal("palette:plane.bank_%s" % bid, bid, "plane", [e["arcade_rgb8"] for e in bb["entries"]], bb.get("source"))
    return {"meta": {"authority": "ORIGINAL ARCADE (read-only)", "editor": "v0.2 palette composer"},
            "contexts": contexts.get("contexts", []), "context_types": contexts.get("context_types", []),
            "objects": objects.get("objects", []), "usages": usages, "palettes": palettes,
            "exact_duplicate_palette_groups": {h: g for h, g in groups.items() if len(g) > 1},
            "coexistence": {"layer_a_active_banks_per_segment": coex.get("layer_a_active_banks_per_segment", {}),
                            "layer_a_legal_banks_union": coex.get("layer_a_legal_banks_union")},
            "genesis_model": {"palette_lines": 4, "entries_per_line": 16, "transparent_index": 0, "levels": LV3}}


# ---------- rendering ----------
def png(w, h, rows):
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    return (b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
            ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b""))


def render_composite(pieces, pal, boundaries=False):
    """TRUE composite: place each 16x16 cell at its relative (x,y) with flips; bbox-normalize + 1px pad.
    Same geometry regardless of palette (source vs target differ only in `pal`)."""
    if not pieces:
        return png(2, 2, [[30, 30, 38] * 2 for _ in range(2)])
    minx = min(p["x"] for p in pieces); miny = min(p["y"] for p in pieces)
    W = max(p["x"] for p in pieces) + 16 - minx + 2
    H = max(p["y"] for p in pieces) + 16 - miny + 2
    rows = [[30, 30, 38] * W for _ in range(H)]
    for p in sorted(pieces, key=lambda q: -q.get("rec", 0)):  # painter's: high rec first, low on top
        idx = cell_indices(p["code"])
        ox = p["x"] - minx + 1; oy = p["y"] - miny + 1
        for y in range(16):
            sy = 15 - y if p["fy"] else y
            for x in range(16):
                sx = 15 - x if p["fx"] else x
                v = idx[sy * 16 + sx]
                if v:
                    c = pal[v] if v < len(pal) else [255, 0, 255]
                    px = (ox + x) * 3
                    rows[oy + y][px:px + 3] = list(c)
        if boundaries:
            for x in range(16):
                for yy in (0, 15):
                    r = rows[oy + yy]; r[(ox + x) * 3:(ox + x) * 3 + 3] = [90, 90, 110]
    return png(W, H, rows)


class Hd(BaseHTTPRequestHandler):
    def _s(self, code, body, ct="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            return self._s(200, open(os.path.join(HERE, "index.html"), "rb").read(), "text/html")
        if u.path.endswith(".js"):
            return self._s(200, open(os.path.join(HERE, "app.js"), "rb").read(), "application/javascript")
        if u.path.endswith(".css"):
            return self._s(200, open(os.path.join(HERE, "style.css"), "rb").read(), "text/css")
        if u.path == "/api/oracle":
            return self._s(200, json.dumps(build_oracle()).encode())
        if u.path == "/api/layera":
            la = build_layera()
            return self._s(200, json.dumps({
                "counts": la["counts"], "bank_ids": la["bank_ids"], "banks": la["banks"],
                "reserved_lines": RESERVED_LINES, "editable_lines": EDITABLE_LINES,
                "line_owners": LINE_OWNERS, "patterns": la["patterns"]}).encode())
        if u.path == "/api/layera_pattern":
            d = layera_pattern_detail(q.get("pid", [""])[0])
            return self._s(200 if d else 404, json.dumps(d or {"error": "pattern not found"}).encode())
        if u.path == "/api/layera_map":
            try:
                seg = max(0, min(15, int(q.get("seg", ["0"])[0])))
                return self._s(200, json.dumps(layera_map(seg)).encode())
            except Exception as e:
                return self._s(500, json.dumps({"error": str(e)}).encode())
        if u.path == "/api/hitmap":
            uid = q.get("usage", [None])[0]
            usage = next((x for x in build_usages(sprite_bank_colors()) if x["usage_id"] == uid), None) if uid else None
            if usage is None:
                return self._s(404, b'{"error":"usage not found"}')
            W, H, buf = composite_hitmap(usage["pieces"])
            return self._s(200, json.dumps({"w": W, "h": H, "idx": buf}).encode())
        if u.path == "/api/render_tile":
            try:
                code = int(q["code"][0])
                if "pal" in q:
                    pal = json.loads(q["pal"][0])
                else:
                    pal = build_layera()["banks"].get(q.get("bank", ["0x003"])[0], [[0, 0, 0]] * 16)
                z = max(1, min(32, int(q.get("z", ["8"])[0])))
                return self._s(200, render_tile8(code, pal, z), "image/png")
            except Exception as e:
                return self._s(500, json.dumps({"error": str(e)}).encode())
        if u.path == "/api/profiles":
            return self._s(200, json.dumps(loadj(os.path.join(POLICY_DIR, "profile_manifest.json"), {"profiles": []})).encode())
        if u.path == "/api/policy":
            pid = q.get("p", ["baseline_current"])[0]
            pol = loadj(os.path.join(POLICY_DIR, pid + ".json"), default_profile(pid))
            return self._s(200, json.dumps(_backfill_policy(pol)).encode())
        if u.path == "/api/render":
            try:
                banks = sprite_bank_colors()
                uid = q.get("usage", [None])[0]
                usage = next((x for x in build_usages(banks) if x["usage_id"] == uid), None) if uid else None
                if usage is None:
                    return self._s(404, b'{"error":"usage not found"}')
                pal = banks.get(int(usage["sprite_bank"], 16), [[0, 0, 0]] * 16)
                if "target" in q:
                    pal = json.loads(q["target"][0])
                bnd = q.get("boundaries", ["0"])[0] == "1"
                pieces = usage["pieces"]
                if q.get("mode", [""])[0] == "cells":  # CELL SHEET debug (grid)
                    pieces = [{"code": p["code"], "x": (i % 6) * 18, "y": (i // 6) * 18, "fx": False, "fy": False}
                              for i, p in enumerate(pieces)]
                return self._s(200, render_composite(pieces, pal, bnd), "image/png")
            except Exception as e:
                return self._s(500, json.dumps({"error": str(e)}).encode())
        return self._s(404, b'{"error":"nf"}')

    def do_POST(self):
        u = urlparse(self.path)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if u.path == "/api/phase_automap":
            line = int(body.get("line", -1))
            if line in RESERVED_LINES or line not in (0, 1, 2, 3):
                return self._s(403, json.dumps({"error": "LINE %d is not an editable target (Line 2 is "
                               "protected)" % line}).encode())
            tcs = body.get("target_colors") or []
            if not any(tcs[1:] if len(tcs) > 1 else []):
                return self._s(400, json.dumps({"error": "selected line has no populated colors"}).encode())
            return self._s(200, json.dumps(phase_layera_automap(line, tcs)).encode())
        if u.path == "/api/solve":
            idlist = body.get("usage_ids", [])
            ids = set(idlist)
            plane_ids = [i for i in idlist if i.startswith("LA-")]
            us = [x for x in build_usages(sprite_bank_colors()) if x["usage_id"] in ids]
            us += layera_solver_usages(plane_ids)         # Layer-A logical usages participate too
            if len(us) < 1:
                return self._s(400, b'{"error":"select 1+ usages"}')
            mode = body.get("mode", "delta_e")
            sol = solve_group(us, mode, hue_limit=float(body.get("hue_limit", 45)),
                              de_limit=float(body.get("de_limit", 20)), hue_tol=float(body.get("hue_tol", 10)))
            sol["palette_domains"] = sorted(set(x["object_id"] for x in us))
            sol["preview_representations"] = [x["usage_id"] for x in us]
            return self._s(200, json.dumps(sol).encode())
        if u.path == "/api/policy":
            pid = (body.get("profile_id") or "").strip()
            if not pid or pid == "baseline_current":
                return self._s(400, b'{"error":"immutable baseline cannot be overwritten"}')
            # LINE-2 PROTECTION (server-authoritative): reject any mapping that targets a reserved line,
            # and force the protected line back to empty so the editor can never serialize over Layer B.
            for coll in ("usage_palette_mappings", "plane_usage_palette_mappings"):
                for k, mp in (body.get(coll) or {}).items():
                    if mp and mp.get("line") in RESERVED_LINES:
                        return self._s(403, json.dumps({"error": "LINE 2 is protected (Layer B / arcade controlled); "
                                        "mapping %s may not target a reserved line" % k}).encode())
            tpl = body.get("target_palette_lines")
            if isinstance(tpl, list):
                for ln in RESERVED_LINES:
                    if ln < len(tpl):
                        tpl[ln] = [None] * 16      # Line 2 is never editable/serialized as a replacement palette
            # context overrides may never touch a reserved line either
            for cid, cp in (body.get("context_policies") or {}).items():
                for ln in list((cp.get("tpl") or {}).keys()):
                    if int(ln) in RESERVED_LINES:
                        return self._s(403, json.dumps({"error": "LINE 2 is protected; context %s may not override a "
                                        "reserved line" % cid}).encode())
                for k, mp in (cp.get("plane_usage_palette_mappings") or {}).items():
                    if mp and mp.get("line") in RESERVED_LINES:
                        return self._s(403, json.dumps({"error": "LINE 2 is protected; context %s plane mapping %s may "
                                        "not target a reserved line" % (cid, k)}).encode())
            body["reserved_lines"] = list(RESERVED_LINES)
            body["line_owners"] = LINE_OWNERS
            json.dump(body, open(os.path.join(POLICY_DIR, pid + ".json"), "w"), indent=1)
            man = loadj(os.path.join(POLICY_DIR, "profile_manifest.json"), {"profiles": []})
            m = {p["profile_id"]: p for p in man["profiles"]}
            m[pid] = {"profile_id": pid, "display_name": body.get("display_name", pid),
                      "parent": body.get("parent", "baseline_current"),
                      "modified": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "revision": m.get(pid, {}).get("revision", 0) + 1}
            man["profiles"] = list(m.values())
            json.dump(man, open(os.path.join(POLICY_DIR, "profile_manifest.json"), "w"), indent=1)
            return self._s(200, json.dumps({"ok": True, "profile_id": pid}).encode())
        return self._s(404, b'{"error":"nf"}')

    def log_message(self, *a):
        pass


def default_profile(pid):
    # V0.4 policy: 4 target lines (16 legal-CRAM entries each); Line 2 reserved for Layer B (arcade controlled).
    return {"profile_id": pid, "display_name": pid if pid != "baseline_current" else "Baseline (immutable)",
            "parent": None if pid == "baseline_current" else "baseline_current",
            "immutable": pid == "baseline_current", "schema": "v0.4",
            "target_palette_lines": [[None] * 16 for _ in range(4)],  # each entry = "0xNNN" CRAM or None
            "usage_palette_mappings": {},  # sprite usage_id -> {line, index_map:{src_index: target_index}}
            "plane_usage_palette_mappings": {},  # Layer-A usage_id (LA-NNNN) -> {line, index_map}
            "context_palette_packages": {},  # segment/context -> package metadata
            "context_policies": {},  # stable context id -> {tpl:{line:{index:cram}}} context-scoped color overrides
            "reserved_lines": list(RESERVED_LINES),  # editor-protected CRAM lines
            "line_owners": LINE_OWNERS,             # ownership/protection (NOT a replacement Layer-B palette)
            "object_labels": {}}


def _backfill_policy(pol):
    """Backward-compatible load: inject V0.4 protection/plane fields into an older saved profile in memory only
    (never rewrites the stored file). Preserves all existing sprite work (Line 0, usage_palette_mappings)."""
    pol.setdefault("plane_usage_palette_mappings", {})
    pol.setdefault("context_palette_packages", {})
    pol.setdefault("context_policies", {})
    pol["reserved_lines"] = list(RESERVED_LINES)   # protection is server-authoritative, always enforced
    pol["line_owners"] = LINE_OWNERS
    return pol


def ensure_baseline():
    p = os.path.join(POLICY_DIR, "profile_manifest.json")
    if not os.path.exists(p):
        json.dump({"active": "baseline_current",
                   "profiles": [{"profile_id": "baseline_current", "display_name": "Baseline (immutable)",
                                 "parent": None, "immutable": True, "revision": 0}]}, open(p, "w"), indent=1)


if __name__ == "__main__":
    import sys
    ensure_baseline()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
    print("Palette Composer v0.2 -> http://localhost:%d  (oracle READ-ONLY, Build 313)" % port)
    ThreadingHTTPServer(("127.0.0.1", port), Hd).serve_forever()
