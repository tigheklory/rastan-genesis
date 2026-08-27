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


def _best_cram_lh(members):
    """Luminance-FIRST legal-CRAM target: lexicographic (worst ΔL, mean ΔL, hue err, chroma err, worst ΔE, mean ΔE)."""
    Ls = [_oklch(m[0])[0] for m in members]
    desiredL = sum(Ls) / len(Ls)                    # equal-source mean lightness
    Cs = sorted(_oklch(m[0])[1] for m in members)
    desiredC = Cs[len(Cs) // 2]                       # median chroma (stable vs outliers)
    hueC, spread = _hue_center([m[0] for m in members])
    best = None
    for rgb in _LEGAL:
        tL, tC, tH = _oklch(rgb)
        dLs = [abs(_oklch(m[0])[0] - tL) for m in members]
        des = [_de00(m[0], rgb) for m in members]
        worstL = max(dLs); meanL = sum(dLs) / len(dLs)
        hueErr = _ang(hueC, tH) if hueC is not None else 0.0
        chErr = abs(desiredC - tC)
        key = (round(worstL, 4), round(meanL, 4), round(hueErr, 1), round(chErr, 3), round(max(des), 3), round(sum(des) / len(des), 3))
        if best is None or key < best[0]:
            r = LV3.index(rgb[0]); g = LV3.index(rgb[1]); b = LV3.index(rgb[2])
            best = (key, "0x%04X" % ((b << 9) | (g << 5) | (r << 1)), max(des), sum(des) / len(des), rgb, worstL, meanL, hueC, spread, tH)
    return best


def _cluster(usages, rank, fit_entries=15):
    """Generic constrained clustering: never 2 colors from one usage; merge by `rank(a,b)` ascending until <=fit."""
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
                cost = max(rank(x[2], y[2]) for x in a2(clusters, i) for y in a2(clusters, jx))
                if best is None or cost < best[0]:
                    best = (cost, i, jx)
        if best is None:
            break
        worst_merge = max(worst_merge, best[0]); _, i, jx = best; clusters[i] += clusters[jx]; del clusters[jx]
    return clusters, worst_merge


def a2(clusters, i):
    return clusters[i]


def solve_group(usages, mode="delta_e", fit_entries=15):
    """mode='delta_e' (perceptual) or 'luminance_hue' (lightness-first + between-hue)."""
    rank = (lambda a, b: abs(_oklch(a)[0] - _oklch(b)[0])) if mode == "luminance_hue" else (lambda a, b: _de00(a, b))
    clusters, worst_merge = _cluster(usages, rank, fit_entries)
    feasible = len(clusters) <= fit_entries
    entries = []
    for ci, cl in enumerate(clusters):
        members = [(m[2], m[3]) for m in cl]
        if mode == "luminance_hue":
            _, cram, worst, wmean, rgb, worstL, meanL, hueC, spread, tH = _best_cram_lh(members)
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
    return {"solver": mode, "feasible": feasible, "entries_used": len(clusters), "entries": entries,
            "per_object": per, "worst_perceptual_merge": round(worst_merge, 2),
            "method": ("luminance-first (OKLab ΔL) clustering + between-hue legal CRAM" if mode == "luminance_hue"
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
    for bid, bb in plane.get("banks", {}).items():
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
        if u.path == "/api/profiles":
            return self._s(200, json.dumps(loadj(os.path.join(POLICY_DIR, "profile_manifest.json"), {"profiles": []})).encode())
        if u.path == "/api/policy":
            pid = q.get("p", ["baseline_current"])[0]
            return self._s(200, json.dumps(loadj(os.path.join(POLICY_DIR, pid + ".json"), default_profile(pid))).encode())
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
        if u.path == "/api/solve":
            ids = set(body.get("usage_ids", []))
            us = [x for x in build_usages(sprite_bank_colors()) if x["usage_id"] in ids]
            if len(us) < 1:
                return self._s(400, b'{"error":"select 1+ usages"}')
            mode = body.get("mode", "delta_e")
            return self._s(200, json.dumps(solve_group(us, mode)).encode())
        if u.path == "/api/policy":
            pid = (body.get("profile_id") or "").strip()
            if not pid or pid == "baseline_current":
                return self._s(400, b'{"error":"immutable baseline cannot be overwritten"}')
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
    # V0.2 policy: 4 target lines (16 legal-CRAM entries each) + usage->{line, index_map}
    return {"profile_id": pid, "display_name": pid if pid != "baseline_current" else "Baseline (immutable)",
            "parent": None if pid == "baseline_current" else "baseline_current",
            "immutable": pid == "baseline_current", "schema": "v0.2",
            "target_palette_lines": [[None] * 16 for _ in range(4)],  # each entry = "0xNNN" CRAM or None
            "usage_palette_mappings": {},  # usage_id -> {line, index_map:{src_index: target_index}}
            "object_labels": {}}


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
