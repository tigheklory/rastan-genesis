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
# PROMPT-ID-0091 (Cody PROMPT-ID-0090 §Black Backdrop): CRAM Line 0 / index 0 is the BLACK backdrop invariant
# (VDP reg 7 selects it). It is a project-level production invariant (value 0x0000), NOT a Tighe color choice
# needing reapproval. The Composer SHOWS it; it never rewrites Test.json to enforce it (that fix is Cody's).
BACKDROP_INVARIANT = {"line": 0, "index": 0, "required_cram": "0x0000", "label": "Backdrop: Line 0 / Index 0 — BLACK invariant",
                      "note": "Project-level production invariant (VDP reg 7). Cody owns the scene-package fix."}
LINE_OWNERS = {
    "0": {"owner": "editable", "control": "editor", "editable": True, "optimizer_available": True,
          "backdrop_invariant": BACKDROP_INVARIANT},
    "1": {"owner": "editable", "control": "editor", "editable": True, "optimizer_available": True},
    "2": {"owner": "layer_b", "control": "arcade", "editable": False, "optimizer_available": False,
          "label": "LINE 2 — LAYER B — ARCADE CONTROLLED — PROTECTED",
          "animated_indices": [1],  # index 1 = time-of-day sky; verified animated across arcade frames 360/460/700/1000
          "note": "Owned by the accepted Layer-B time-of-day palette path in Build 0313; excluded from editor optimization. Colors are read-only but REUSABLE; index 1 is the animated sky — avoid."},
    "3": {"owner": "editable", "control": "editor", "editable": True, "optimizer_available": True}}


def scene_line_ownership(scene=None):
    """PROMPT-ID-0091 (§Palette line ownership panel / §R1-S3 conditional Line-2): per-scene CRAM line
    ownership. Global LINE_OWNERS with the Line-0 BLACK backdrop invariant, plus the R1-S3 scene-local
    Line-2 status: CONDITIONAL (Plane B still has nonblank data + active publication; visual occlusion not
    proven). Line 2 stays locked/protected globally; this NEVER frees it globally, and only Cody evidence of
    a safe interval would promote it to 'FREE IN THIS SCENE ONLY'."""
    import copy
    owners = copy.deepcopy(LINE_OWNERS)
    if scene == "PAL-R1-S3-PLANEA-BOSS":
        owners["2"] = dict(owners["2"])
        owners["2"].update({
            "owner": "layer_b", "control": "arcade", "editable": False, "optimizer_available": False,
            "scene_local_status": "CONDITIONAL",
            "label": "LINE 2 — LAYER B — CONDITIONAL (R1-S3): visual occlusion NOT proven — locked",
            "note": ("R1-S3 Plane B still has nonblank scene data, active publication, and active scroll "
                     "paths (Cody PROMPT-ID-0090). Tighe observed Layer B visually unused, but occlusion is "
                     "NOT proven, so Line 2 stays locked/protected for R1-S3. If Cody later proves a safe "
                     "scene-local interval the UI can show 'FREE IN THIS SCENE ONLY' with start/end ownership. "
                     "Global Line-2 protection is never changed from this scene badge."),
            "conditional": True, "free_in_scene": False})
    return owners


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


# ---- arcade per-round palette decode (maincpu.bin), matching the Bestiary rom_field_palette ----
_MAINCPU = None
def _maincpu():
    global _MAINCPU
    if _MAINCPU is None:
        _MAINCPU = open(os.path.join(ROOT, "build/regions/maincpu.bin"), "rb").read()
    return _MAINCPU


def _pal5(n):
    v = n * 2
    return (v << 3) | (v >> 2)


def _arcade_round_palette(rnd, nibble):
    """The arcade per-round line palette (0x3BA88 round table -> 0x4FD02 pool). Same math as the Bestiary."""
    mc = _maincpu()
    pidx = mc[0x3BA88 + (rnd - 1) * 32 + nibble]
    b = 0x4FD02 + pidx * 32
    return [[_pal5((int.from_bytes(mc[b + i * 2:b + i * 2 + 2], "big") >> 8) & 0xF),
             _pal5((int.from_bytes(mc[b + i * 2:b + i * 2 + 2], "big") >> 4) & 0xF),
             _pal5(int.from_bytes(mc[b + i * 2:b + i * 2 + 2], "big") & 0xF)] for i in range(16)]


def _pal4(n):
    """Arcade 4-bit nibble -> 8-bit for a boss-specific target table (pal5bit of the raw nibble). This is
    NOT the field convention (_pal5, which doubles the nibble); it reproduces the captured boss CLCS line."""
    return (n << 3) | (n >> 2)


def _rom_boss_target_palette(addr=0x4708C, count=15):
    """Boss-specific ROM 0RGB target table (R1 = 0x4708C). The `count` source words become live palette
    entries 1..count; index 0 is retained black. Decoded from maincpu.bin every call (no RGB stored in the
    tool). Reproduces Cody PROMT-ID-0095's captured final palette (physical arcade line 0x4F)."""
    mc = _maincpu()
    cols = [[0, 0, 0]]
    for i in range(count):
        w = int.from_bytes(mc[addr + i * 2:addr + i * 2 + 2], "big")
        cols.append([_pal4((w >> 8) & 0xF), _pal4((w >> 4) & 0xF), _pal4(w & 0xF)])
    while len(cols) < 16:
        cols.append([0, 0, 0])
    return cols


def _manifest_vm_pieces(base, anim, table):
    """Compositor-VM (decompilation) pieces for a manifest render spec -> anchor-relative {code,x,y,fx,fy}.
    Uses the SAME 0x3D054 route the Bestiary renders with, so the Composer and Bestiary share one source of
    truth (not a gameplay trace). Empty on a special/unsupported program."""
    import sys
    p = os.path.join(ROOT, "tools/graphics_optimizer")
    if p not in sys.path:
        sys.path.insert(0, p)
    try:
        from compositor_vm import ActorRenderState, visible_pieces
        sat = visible_pieces(ActorRenderState(base, anim, table))
    except Exception:
        return []
    if not sat:
        return []
    def s9(v):
        v &= 0x1FF
        return v - 0x200 if v & 0x100 else v
    # PROMPT-ID-0028: preserve EACH piece's own arcade palette bank (the compositor-VM `palette` nibble),
    # so a sprite whose pieces use different banks can be coloured per piece (base 0x0224 anim 0x91 uses
    # nibbles 3 and 12). Single-bank sprites simply have one nibble across all pieces.
    raw = [{"code": q.tile & 0x1FFF, "x": s9(q.x), "y": s9(q.y),
            "fx": bool(q.hflip), "fy": bool(q.vflip), "palette": int(q.palette) & 0xF} for q in sat]
    ox = min(q["x"] for q in raw); oy = min(q["y"] for q in raw)
    return [{"code": q["code"], "x": q["x"] - ox, "y": q["y"] - oy, "fx": q["fx"], "fy": q["fy"],
             "palette": q["palette"]} for q in raw]


def attach_arcade_piece_palettes(pieces, rnd):
    """PROMPT-ID-0028: resolve EACH piece's OWN arcade colours from its `palette` nibble via the per-round
    line palette (same 0x3BA88->0x4FD02 math as the Bestiary). Returns NEW piece dicts each carrying a
    resolved 16-colour `pal`; pieces without a `palette` key are returned unchanged so single-bank callers
    keep the shared-palette path in render_composite. The input list is not mutated."""
    out, cache = [], {}
    for p in pieces:
        q = dict(p)
        nib = p.get("palette")
        if nib is not None:
            if nib not in cache:
                cache[nib] = _arcade_round_palette(rnd, nib)
            q["pal"] = cache[nib]
        out.append(q)
    return out


def _castle_used_colors(pieces, rnd):
    """Distinct source colours painted across a (possibly multi-bank) castle frame, for the SOURCE chips.
    Keyed by (palette nibble, pixel index) so BOTH banks' colours show; synthetic `src_index` keeps the UI
    list unique and `arcade_index`/`palette` preserve provenance. Display only (mapping is PROMPT-ID-0030)."""
    cache, agg = {}, {}
    for p in pieces:
        nib = p.get("palette", 0)
        for v in cell_indices(p["code"]):
            if v:
                agg[(nib, v)] = agg.get((nib, v), 0) + 1
    out = []
    for si, ((nib, v), cnt) in enumerate(sorted(agg.items())):
        if nib not in cache:
            cache[nib] = _arcade_round_palette(rnd, nib)
        pal = cache[nib]
        rgb = pal[v] if v < len(pal) else [0, 0, 0]
        disp, cram, _ = gen_quant(rgb)
        out.append({"src_index": si, "arcade_index": v, "palette": "0x%X" % nib,
                    "arcade_rgb8": rgb, "hex": "#%02X%02X%02X" % tuple(rgb),
                    "pixel_count": cnt, "genesis_rgb8": disp, "genesis_cram": cram})
    return out


_CASTLE_USAGES_CACHE = None
_CASTLE_FRAMES_CACHE = {}

def _castle_frames(base):
    """Distinct static compositor frames for a castle sprite base, deduped by piece signature, ranked so
    route-documented anims (h6/h5) and multi-bank frames surface first. Round-independent geometry (only
    the palette differs per round). Cached per base."""
    if base in _CASTLE_FRAMES_CACHE:
        return _CASTLE_FRAMES_CACHE[base]
    PREFERRED = {0x0224: [0x91, 0x27], 0x00F4: [0x70], 0x033E: [0x93, 0x94, 0x95]}
    distinct = {}
    for anim in range(0x100):
        pcs = _manifest_vm_pieces(base, anim, 0)
        if len(pcs) < 2:
            continue
        sig = tuple((p["code"], p["x"], p["y"], p["fx"], p["fy"], p["palette"]) for p in pcs)
        if sig not in distinct:
            distinct[sig] = (anim, pcs)
    pref = PREFERRED.get(base, [])
    def _rank(item):
        an, pc = item
        nibs = {p["palette"] for p in pc}
        return (0 if an in pref else 1, 0 if len(nibs) > 1 else 1, -len(pc), an)
    ranked = sorted(distinct.values(), key=_rank)
    _CASTLE_FRAMES_CACHE[base] = (ranked, len(distinct))
    return _CASTLE_FRAMES_CACHE[base]


def r1s2_castle_usages():
    """PROMPT-ID-0029 (CORRECTED under PROMPT-ID-0038): the castle marker-driven actors as browsable sprite
    usages, decoded STATICALLY via the compositor VM with PER-PIECE arcade palettes (PROMPT-ID-0028). No
    trace, no fabricated frames; provisional source-derived labels only.

    ROUND ATTRIBUTION reconciled against the source (handler progress guards) and the Bestiary H14:
      - base 0x0224 materializes ONLY in R2 and R4. In R1 the 'E' marker RETIRES — handler 0x44082 has
        `if (progress_13e < 0x18) arcade_4092e()`, and R1-S2 progress is 0x11..0x16 (< 0x18). (My original
        0029 R1-S2 tag was WRONG; corrected.)
      - base 0x00F4 materializes in R4, R5, R6 (absent R1).
      - marker 'M' (0x4d, state 0x1B/0x43ECC) burst IS an R1 actor (H14 R1 prog 0x11) — a 5-child spawner
        whose child identity/graphics are PENDING (coordinate-only), kept INCOMPLETE with no fabricated art.
    Each (base, round) is a separate browsable object so its per-round palette is correct. `scene_key` tags
    each instance for that subround only. Cached module-level (idempotent, additive)."""
    global _CASTLE_USAGES_CACHE
    if _CASTLE_USAGES_CACHE is not None:
        return _CASTLE_USAGES_CACHE
    MAXF = 24
    # (base, round, scene_key, label, provenance) — rounds proven by H14 marker-chain base writes.
    INSTANCES = [
        (0x0224, 2, "PAL-R2-S2-PLANEA-CASTLE", "Castle actor · base $0224 (R2)",
         "marker 'G'(0x47)->state 0x1C / 'E'(0x45)->state 0x18 -> base 0x0224; H14: present in R2"),
        (0x0224, 4, "PAL-R4-S2-PLANEA-CASTLE", "Castle actor · base $0224 (R4)",
         "state 0x18 (high prog) -> base 0x0224; H14: present in R4"),
        (0x00F4, 4, "PAL-R4-S2-PLANEA-CASTLE", "Castle actor · base $00F4 (R4)",
         "state 0x1D -> base 0x00F4; H14: present in R4"),
        (0x00F4, 5, "PAL-R5-S2-PLANEA-CASTLE", "Castle actor · base $00F4 (R5)",
         "state 0x1A/0x1D -> base 0x00F4; H14: present in R5"),
        (0x00F4, 6, "PAL-R6-S2-PLANEA-CASTLE", "Castle actor · base $00F4 (R6)",
         "state 0x21 -> base 0x00F4; H14: present in R6"),
        # PROMPT-ID-0091 (Section 17): preserve $09EA spike/spear/stalagmite in its PROVEN R5 scene (NOT R1).
        (0x09EA, 5, "PAL-R5-S2-PLANEA-CASTLE", "Castle hazard · base $09EA spike/spear/stalagmite (R5)",
         "rec-type 0x1B template + marker-chain 0x43840 (state 0x15)/0x40EDE (state 0x20) -> base 0x09EA; "
         "H14/H21: R5. Floor-spear/wall-spear/stalagmite FORM is marker+band+compositor selected. Tighe "
         "HUMAN IDENTITY (PROMPT-ID-0086)."),
    ]
    out = []
    for base, rnd, scene, name, note in INSTANCES:
        frames, total = _castle_frames(base)
        obj_id = "object:castle.base_0x%04X.r%d" % (base, rnd)
        for order, (anim, pcs) in enumerate(frames[:MAXF]):
            nibs = sorted({p["palette"] for p in pcs})
            xs = [p["x"] for p in pcs]; ys = [p["y"] for p in pcs]
            out.append({
                "usage_id": "usage:castle_0x%04X_r%d:anim0x%02X" % (base, rnd, anim),
                "object_id": obj_id, "map_key": obj_id,
                "frame_category": None, "frame_label": "anim 0x%02X" % anim, "frame_order": order,
                "player_counts": None, "weapon_counts": None,
                "display_name": name, "sprite_bank": "0x%02X" % nibs[0],
                "sprite_banks": ["0x%X" % n for n in nibs], "multi_bank": len(nibs) > 1,
                "scene_key": scene, "round": rnd, "base": "0x%04X" % base,
                "provisional": True, "identity_note": note,
                "pieces": pcs, "n_pieces": len(pcs),
                "bounds": [max(xs) - min(xs) + 16, max(ys) - min(ys) + 16],
                "composite_proven": True, "preview_type": "TRUE ARCADE COMPOSITE",
                "used_colors": _castle_used_colors(pcs, rnd), "mrd_pairs": [],
                "n_used": len({(p["palette"], v) for p in pcs for v in cell_indices(p["code"]) if v}),
                "frames_total_distinct": total,
            })
    # marker 'M' burst: R1-S2 (H14 R1 prog 0x11). Coordinate-only child presentation -> NOT statically
    # decodable as one composite; represented honestly with NO fabricated frames.
    out.append({
        "usage_id": "usage:castle_mburst_r1:info", "object_id": "object:castle.marker_M_burst.r1",
        "map_key": "object:castle.marker_M_burst.r1",
        "frame_category": None, "frame_label": "burst (coordinate-only)", "frame_order": 0,
        "player_counts": None, "weapon_counts": None,
        "display_name": "R1-S2 Castle marker 'M' burst (5-child spawner)",
        "sprite_bank": "0x00", "sprite_banks": [], "multi_bank": False,
        "scene_key": "PAL-R1-S2-PLANEA-CASTLE", "round": 1, "base": None,
        "provisional": True, "incomplete": True,
        "identity_note": ("marker 'M' (0x4d) -> state 0x1B (0x43ECC) burst (arcade_43f4e_burst, 5 children, "
                          "parent anim 0x7a); H14: present in R1 (prog 0x11). Child identity/graphics are "
                          "PENDING (coordinate-only / seeded SAT) — NOT statically decodable; no fabricated art."),
        "pieces": [], "n_pieces": 0, "bounds": [16, 16], "composite_proven": False,
        "preview_type": "INCOMPLETE — coordinate-only burst (no static composite)",
        "used_colors": [], "mrd_pairs": [], "n_used": 0,
    })
    _CASTLE_USAGES_CACHE = out
    return out


# PROMPT-ID-0069: the castle "Green Sword Knight" (family-2 base 0x033E, anim 0x93) across ALL castle
# sections R1-S2..R6-S2. It is the ONLY scheduled R1-S2 enemy (decode_field_schedule, table 0x4A104) and is
# DIRECTLY-SCHEDULED (not marker-transformed), so its +0x27 palette line (set by creation 0x45684, bit6)
# survives and 0x3C9E8 uses it as the DISPLAY palette (NOT the compositor control-byte nibble, which only
# governs transformed actors). Display line = creation nibble = pal_nib_456ec[variant*18+(round-1)*3+comp_adj]
# -> 0x3BA88[round][nibble] -> pool -> 0x4FD02. Most variants are green (armor); the c4/default is red/blue.
_KNIGHT_SECTIONS_CACHE = None
def _green_knight_sections():
    """Per castle round: list of (variant, creation_nibble, [comps]) palette-distinct knight variants."""
    global _KNIGHT_SECTIONS_CACHE
    if _KNIGHT_SECTIONS_CACHE is not None:
        return _KNIGHT_SECTIONS_CACHE
    mc = _maincpu()
    tbl = [mc[0x456EC + i] for i in range(72)]  # family-2 nibble table (0x45684)
    def nib(rnd, v, c):
        ca = c - 2 if c >= 3 else c
        return tbl[v * 18 + (rnd - 1) * 3 + ca]
    # family-2 0x033E schedule variants/comps per round (decode_field_schedule.py)
    APPEAR = {1: [(0, 0), (0, 3), (0, 4)], 2: [(0, 0), (0, 3), (0, 4), (1, 0)],
              3: [(0, 3), (0, 4), (1, 0), (1, 4)], 4: [(1, 0), (1, 3), (1, 4), (2, 0)],
              5: [(1, 3), (1, 4), (2, 0), (2, 3), (2, 4)], 6: [(1, 3), (2, 0), (2, 3), (2, 4)]}
    out = {}
    for rnd, vcs in APPEAR.items():
        seen = {}
        for (v, c) in vcs:
            n = nib(rnd, v, c)
            seen.setdefault((v, n), []).append(c)
        out[rnd] = [(v, n, cs) for (v, n), cs in seen.items()]
    _KNIGHT_SECTIONS_CACHE = out
    return out


_KNIGHT_USAGES_CACHE = None
def green_knight_usages():
    """Scene-tagged browsable Green Sword Knight objects for every castle section, each palette-distinct
    variant carrying its CREATION-route arcade palette reference (16 pool colors). Cached, additive."""
    global _KNIGHT_USAGES_CACHE
    if _KNIGHT_USAGES_CACHE is not None:
        return _KNIGHT_USAGES_CACHE
    frames, total = _castle_frames(0x033E)
    # COMPLETE same-actor base-$033E animation domain, resolved from the actor state machine, CORRECTED under
    # PROMPT-ID-0091 from Cody PROMPT-ID-0090's independent $4D/$56-$5A re-audit. The "29 programs / 109 codes"
    # claim (PROMPT-ID-0084) COMBINED UNRELATED (base,program) identities and is REMOVED: Cody source-proved
    # $4D->base $0234, $56->base $0241 (family 8), $57/$58->base $01FC, $59/$5A->base $0241(fam8)/$0546. The
    # $4684E family-8 branch selects $56,$59,$5A for the LIVE ACTOR BASE $0241 (the rope climber), never from
    # the $033E sheet. The corrected proven base-$033E domain is 23 PROGRAMS / 97 CODES. The field schedule
    # (0x4A104) spawns the knight family-2 (+$3E == 2). Engines reached via the state dispatcher (0x40BAA)
    # render, from the warrior's own $033E sheet:
    #   * NORMAL      $93-$96 : ground engine 0x47140 (states 3-0C,12) + state-0x11 0x4684E (+$3E==2).
    #   * SHORT REACTION $71-$73 : state-0x0F alt path 0x40E0E (+$03!=0, sfx 0x17, BASE-PRESERVING); a short
    #              mode-driven reaction/effect. NOT proven to be the "crouch/duck" pose Tighe observed -- label
    #              stays "short reaction/effect (crouch visual pending)". $74 EXCLUDED (state-0x20 torch $0DAB).
    #   * AIRBORNE    $20-$23 : airborne engine 0x473B8 (states 0D/0E, fam2) -> $20+tbl[0x47562]; passive/
    #              turning airborne domain (human pose name strongly supported, not individually pinned).
    #   * LOW/WEAPON ACTION A $A1-$A6 : state-$1F engine 0x42EF8, family 2, actor+$21 bit2 == 0; table 0x42FBC
    #              -> $93,$A1-$A6 (+reflect). PROVEN DISPLAYED by the arcade sweep; exact human name unproven.
    #   * LOW/WEAPON ACTION B $97-$9C : state-$1F engine 0x42EF8, family 2, actor+$21 bit2 != 0 (writes +$37=$61);
    #              table 0x42FD4 -> $97-$9C (+reflect). PROVEN DISPLAYED by the arcade sweep; name unproven.
    # The family-8 rope climber ($56,$59,$5A on base $0241) is the SEPARATE object:castle.rope_climber.family8.r1
    # (rope_climber_usages); $4D/$57/$58 ($0234/$01FC) are research-view producers. The embedded sword is an
    # attached piece of these 23 programs (upright $93 = 26B,26C; the state-$1F programs rotate the weapon
    # through the sword artwork 26D-274). It is a warrior sub-context, NOT a separate actor; ZERO pattern-code
    # overlap with Rastan's player weapon tables. Every pose is ONE semantic actor inheriting the SINGLE
    # authored mapping (same object_id per round). See the PROMPT-ID-0091 report for palette provenance.
    KNIGHT_ANIM_STATE = dict(
        [(a, "normal") for a in (0x93, 0x94, 0x95, 0x96)]
        + [(a, "short_reaction") for a in (0x71, 0x72, 0x73)]
        + [(a, "airborne") for a in (0x20, 0x21, 0x22, 0x23)]
        + [(a, "low_action_a") for a in (0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6)]
        + [(a, "low_action_b") for a in (0x97, 0x98, 0x99, 0x9A, 0x9B, 0x9C)])
    # Honest, non-overclaiming UI pose-group headers: the state-$1F and short-reaction names stay provisional
    # until a runtime capture proves the human gameplay meaning. The family-8 "rope" programs $4D,$56-$5A are
    # NOT in this domain (PROMPT-ID-0091): Cody proved they belong to other bases; the rope climber is the
    # separate object:castle.rope_climber.family8.r1 (base $0241).
    POSE_LABEL = {
        "normal": "Normal walk/idle ($93-$96)",
        "short_reaction": "Short reaction/effect — crouch visual pending ($71-$73)",
        "airborne": "Airborne / low pose ($20-$23)",
        "low_action_a": "Low / weapon action A — state $1F ($A1-$A6)",
        "low_action_b": "Low / weapon action B — state $1F ($97-$9C)",
    }
    # Sword sub-context (Cody 0080): attached-piece weapon artwork inside the warrior's own programs.
    SWORD_SUBCONTEXT = "object:castle.green_sword_knight.weapon.sword"
    SWORD_CODES = tuple(range(0x26B, 0x275))                     # complete moving-weapon artwork 26B-274
    SWORD_REPRESENTATIVE_ANIMS = {0x93, 0xA3, 0xA6, 0x99, 0x9C}  # representatives; all codes still covered
    knight_anim_domain = set(KNIGHT_ANIM_STATE)
    knight_frames = [frame for frame in frames if frame[0] in knight_anim_domain]
    if {frame[0] for frame in knight_frames} != knight_anim_domain:
        raise RuntimeError("Green Sword Knight arcade animation domain is incomplete")
    mc = _maincpu()
    # ARMOR palette = the knight program's green control-byte line (line 3 -> pool 0x0C), which renders the
    # green-armored sword knight matching the arcade across all rounds (verified). The creation-table route
    # (0x45684 -> nibbles 4/2/1 -> pools 0x12/0x0F/0x0B) renders flesh/red and does NOT match; and the
    # per-piece body line (line 7) is blue in R1 (pool 0x0B) vs green on screen -> an unresolved castle-CRAM
    # nuance (see the 0069 report). Line 3 (pool 0x0C) is the authorable green-armor reference.
    ARMOR_LINE = 3
    out = []
    for rnd in sorted(_green_knight_sections().keys()):
        scene = "PAL-R%d-S2-PLANEA-CASTLE" % rnd
        for _ignore in (True,):
            nib = ARMOR_LINE
            pal = _arcade_round_palette(rnd, nib)                      # green armor line (pool 0x0C)
            pool = mc[0x3BA88 + (rnd - 1) * 32 + nib]
            ref = []
            for idx, c in enumerate(pal):
                disp, cram, _ = gen_quant(c)
                ref.append({"src_index": idx, "arcade_index": idx, "palette": "0x%X" % nib,
                            "arcade_rgb8": c, "hex": "#%02X%02X%02X" % tuple(c),
                            "pixel_count": 1, "genesis_rgb8": disp, "genesis_cram": cram})
            v = 0
            vlabel = "R%d green armor · line 0x%X pool 0x%02X" % (rnd, nib, pool)
            note = ("family-2 base 0x033E. Green-armor palette = the knight program's line 0x%X control byte "
                    "-> 0x3BA88[R%d] -> pool 0x%02X -> 0x4FD02 (matches the arcade green). Body line 7 is blue "
                    "in R1 per the field table -> an unresolved castle-CRAM nuance; line 3 is the authorable "
                    "green-armor reference." % (nib, rnd, pool))
            # PROMPT-ID-0084 (Cody 0080 requirement #5): preserve BOTH provenance layers, do NOT flatten to one
            # bank. (1) embedded bit-6-clear per-piece program defaults; (2) the preserved R1 arcade sweep's
            # actor creation attribute (+$27) with bit 6 set, which makes 0x3C9E8/0x3C902 override every
            # piece's low byte uniformly. Surface the registry-bank-$33 vs observed-$34/$31 conflict for Tighe.
            palette_provenance = {
                "embedded_defaults": {
                    "note": "bit-6-clear per-piece program control nibbles; effective bank = 0x30 + nibble",
                    "normal_and_state_1F": {"sword_piece": "nibble 3 / bank 0x33", "body_piece": "nibble 7 / bank 0x37"},
                    "airborne_$20_$23": "nibble 7 / bank 0x37",
                    "short_reaction_$71_$73": "nibble C / bank 0x3C",
                },
                "actor_override": {
                    "note": "preserved R1 sweep: every $033E record has creation attr +$27 = 0x44 (960 obs) or "
                            "0x41 (326 obs), bit 6 set; 0x3C9E8/0x3C902 overrides all piece low bytes to one line",
                    "effective_line": "4 (bank 0x34) or 1 (bank 0x31) under the 0x30 colbank",
                },
                "registry_conflict": {
                    "decision_id": "PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001",
                    "registry_records": "authoring reference R1 line 3 -> pool 0x0C, runtime bank 0x33",
                    "observed_in_sweep": "actor attribute selects line 4/bank 0x34 or line 1/bank 0x31",
                    "status": "UNRESOLVED field-CRAM relationship (see 0069); surfaced, not silently redefined",
                },
            }
            for order, (anim, pcs) in enumerate(knight_frames):
                # SINGLE creation-line palette (not per-piece): strip the per-piece "palette" nibble so the
                # render path uses the one pool palette (via used_colors overlay) and honors the authored
                # target mapping, instead of the multi-bank per-piece branch (which showed nibble-7 blue and
                # ignored the mapping). See /api/render usage branch.
                pp = [{k: v for k, v in p.items() if k != "palette"} for p in pcs]
                xs = [p["x"] for p in pp]; ys = [p["y"] for p in pp]
                state = KNIGHT_ANIM_STATE[anim]
                frame_sword_codes = sorted(c for c in (p["code"] for p in pp) if c in SWORD_CODES)
                out.append({
                    "usage_id": "usage:knight_r%d_v%d_n%x:anim0x%02X" % (rnd, v, nib, anim),
                    "object_id": "object:castle.green_sword_knight.r%d.n%x" % (rnd, nib),
                    "map_key": "object:castle.green_sword_knight.r%d.n%x" % (rnd, nib),
                    # The pose-group is the honest UI header (app.js groups by frame_category); the round's
                    # green-armor line label is kept in variant_label.
                    "frame_category": POSE_LABEL[state], "frame_label": "anim 0x%02X" % anim, "frame_order": anim,
                    "anim_state": state, "pose_label": POSE_LABEL[state],
                    "player_counts": None, "weapon_counts": None,
                    "display_name": "Green Sword Knight", "variant_label": vlabel,
                    "sprite_bank": "0x3%X" % nib, "sprite_banks": ["0x3%X" % nib], "multi_bank": False,
                    "scene_key": scene, "round": rnd, "base": "0x033E", "provisional": True,
                    "identity_note": note, "pieces": pp, "n_pieces": len(pp),
                    "bounds": [max(xs) - min(xs) + 16, max(ys) - min(ys) + 16],
                    "composite_proven": True, "preview_type": "ARCADE GREEN-ARMOR (line 3 / pool 0x0C)",
                    "used_colors": ref, "mrd_pairs": [], "n_used": 16, "frames_total_distinct": total,
                    "palette_provenance": palette_provenance,
                    # Sword sub-context evidence (Cody 0080 #6): the attached-piece weapon lives in the SAME
                    # programs and inherits the SAME warrior mapping -- NOT a separate palette identity.
                    "weapon_subcontext": SWORD_SUBCONTEXT,
                    "weapon_sword_codes": ["0x%03X" % c for c in SWORD_CODES],
                    "frame_sword_codes": ["0x%03X" % c for c in frame_sword_codes],
                    "sword_representative": anim in SWORD_REPRESENTATIVE_ANIMS,
                })
    _KNIGHT_USAGES_CACHE = out
    return out


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


def _h24_player_tsv(name):
    """Read a generated H24 player-frame cell TSV (authoritative static source, not a hand list)."""
    import csv
    p = os.path.join(ROOT, "analysis/actor_decompilation", name)
    if not os.path.exists(p):
        return []
    rows = []
    for r in csv.DictReader(open(p), delimiter="\t"):
        cells = [c for c in (r.get("cells") or "").split(";") if c]
        if not cells:
            continue
        xs = (r.get("x_offsets") or "").split(";"); ys = (r.get("y_offsets") or "").split(";")
        pieces = [{"code": int(c, 16), "x": int(xs[i]), "y": int(ys[i]), "fx": False, "fy": False}
                  for i, c in enumerate(cells)]
        rows.append({"slot": int(r["slot"]), "pieces": pieces})
    return rows


def enemy_complete_usages():
    """Complete R1/P1 enemy corpus from the authoritative census (r1p1_enemy_semantic_corpus.tsv):
    every proven cell code per enemy under its effective bank. Returns one complete-coverage usage per
    enemy (all cells -> the full source palette) so mapping the enemy ONCE covers its entire animation
    vocabulary, not just a representative frame. Returns (out, counts). Each enemy keeps ONE object_id
    /map_key so it stays a single semantic palette object."""
    import csv
    p = os.path.join(ROOT, "analysis/actor_decompilation", "r1p1_enemy_semantic_corpus.tsv")
    if not os.path.exists(p):
        return [], {}
    by = {}   # object -> (bank, set(codes))
    for r in csv.DictReader(open(p), delimiter="\t"):
        obj = r["object"]; bank = int(r["effective_bank"], 16); code = int(r["cell_code"], 16)
        d = by.setdefault(obj, [bank, set()]); d[1].add(code)
    NAMES = {"lizardman": "Lizardman", "valkyrie": "Valkyrie", "four_armed_insect": "Four-Armed Insect",
             "chimera": "Chimera", "flying_demon": "Flying Demon", "small_bat": "Small Bat",
             "large_bat": "Large Bat"}
    out = []; counts = {}
    for obj, (bank, codes) in by.items():
        cs = sorted(codes); counts[obj] = len(cs)
        pieces = [{"code": c, "x": (i % 12) * 16, "y": (i // 12) * 16, "fx": False, "fy": False}
                  for i, c in enumerate(cs)]
        disp = NAMES.get(obj, obj)
        out.append(("enemyfull_%s" % obj, "%s - complete corpus (%d cells)" % (disp, len(cs)),
                    pieces, bank, "object:enemy.%s" % obj))
    return out, counts


def h24_weapon_frames():
    """The 4 equipped weapons as first-class Palette Composer objects (SWORD/AXE/HAMMER/FIRE SWORD).
    Each is a separate PC090OJ overlay (0x5CD8A/0x5D346/0x5D666/0x5D068), 42 genuine frames (the frame-69
    decode artefact is excluded), its own shared map_key object:weapon.<name>. Source: generated
    h24_player_weapon_cells.tsv. Rendered in the sprite
    palette space (bank 0x33) from the arcade pc090oj.bin; Tighe authors each weapon's target mapping.
    Returns (out, counts) where out items = (key, label, pieces, category, order, map_key)."""
    import csv
    p = os.path.join(ROOT, "analysis/actor_decompilation", "h24_player_weapon_cells.tsv")
    if not os.path.exists(p):
        return [], {}
    # group cells by (weapon_id, frame) preserving x/y. Frame 69 is a weapon-table decode artefact
    # (player-slot overrun; HAMMER frame 69 = 0x0003x3; aliases body/enemy codes) — excluded to match the
    # Build-0383 generator and the Bestiary weapon section (single source of truth).
    WEAPON_ARTIFACT_FRAME = 69
    frames = {}
    for r in csv.DictReader(open(p), delimiter="\t"):
        if r.get("valid_code") != "Y":
            continue
        if int(r["frame_index"]) == WEAPON_ARTIFACT_FRAME:
            continue
        wid = r["weapon_id"]; fi = int(r["frame_index"])
        frames.setdefault((wid, fi), []).append(
            {"code": int(r["cell_code"], 16), "x": int(r["x_off"]), "y": int(r["y_off"]),
             "fx": r.get("flip") == "H", "fy": False})
    names = {"object:weapon.sword": "Sword", "object:weapon.axe": "Axe",
             "object:weapon.hammer": "Hammer", "object:weapon.fire_sword": "Fire Sword"}
    out = []; counts = {}
    for wid, disp in names.items():
        wf = sorted((fi for (w, fi) in frames if w == wid))
        counts[wid] = len(wf)
        for n, fi in enumerate(wf):
            key = "%s_f%02d" % (wid.split(":")[1].replace(".", "_"), fi)
            out.append((key, "%s frame %d" % (disp, fi), frames[(wid, fi)], "weapon", n, wid))
    return out, counts


def _h24_reference_map():
    """torso slot -> provenance label (normal / weapon-variant / attack / weapon-swing companion)."""
    import csv
    p = os.path.join(ROOT, "analysis/actor_decompilation", "h24_player_frame_reference_map.tsv")
    out = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p), delimiter="\t"):
            out[int(r["torso_slot"])] = (r.get("referencing_tables") or "").replace(";", ", ")
    return out


def _h24_fullbody_pairings():
    """Authoritative valid full-body pairings (torso_slot, leg_slot) — generated artifact, NOT a hand
    list. See tools/analysis/gen_player_fullbody_pairings.py."""
    import csv
    p = os.path.join(ROOT, "analysis/actor_decompilation", "h24_player_fullbody_pairings.tsv")
    out = []
    if os.path.exists(p):
        for r in csv.DictReader(open(p), delimiter="\t"):
            out.append((int(r["torso_slot"]), int(r["leg_slot"])))
    return out


def h24_player_frames():
    """The complete H24 static player inventory as ONE shared-palette object with a browsable frame set.
    Rastan is two independent tracks: torso 0x5BD40 (75 slots) + legs 0x5C466 (52 slots), both on
    palette line 3 -> sprite bank 0x33. Returns browsable reps (each with category + frame label +
    shared map_key) plus one internal complete-coverage aggregate diagnostic. Source: generated
    h24_player_frame_cells.tsv / h24_player_leg_cells.tsv / h24_player_fullbody_pairings.tsv /
    h24_player_frame_reference_map.tsv. Every rep of the Rastan object shares map_key
    'object:player.rastan', so mapping the player palette ONCE covers every torso/leg frame."""
    torso = _h24_player_tsv("h24_player_frame_cells.tsv")
    legs = _h24_player_tsv("h24_player_leg_cells.tsv")
    tmap = {r["slot"]: r["pieces"] for r in torso}
    lmap = {r["slot"]: r["pieces"] for r in legs}
    refmap = _h24_reference_map()
    MAPKEY = "object:player.rastan"
    out = []  # (key, label, pieces, category, order, map_key)
    # 1) valid full-body pairings (torso over legs at shared origin) — the animation-proven combinations.
    #    A few pair with the blank leg slot / an effect half; those render the non-blank half (still a
    #    valid frame in the vocabulary), so all pairings are browsable.
    for pi, (u, l) in enumerate(_h24_fullbody_pairings()):
        pcs = tmap.get(u, []) + lmap.get(l, [])
        if pcs:
            out.append(("rastan_fb_%02d" % pi, "Full Body %02d (torso %d + legs %d)" % (pi, u, l),
                        pcs, "fullbody", pi, MAPKEY))
    # 2) every torso frame (0x5BD40), annotated with its positive provenance
    for s in range(75):
        if s in tmap:
            prov = refmap.get(s, "referenced")
            out.append(("rastan_torso_%02d" % s, "Torso %d/75 (%s)" % (s, prov),
                        tmap[s], "torso", s, MAPKEY))
    # 3) every leg frame (0x5C466); blank slots (e.g. 34) carry no cells and are noted, not rendered
    for s in range(52):
        if s in lmap:
            out.append(("rastan_leg_%02d" % s, "Legs %d/52" % s, lmap[s], "legs", s, MAPKEY))
    # 4) internal complete-coverage aggregate (diagnostic): every distinct cell across all frames, so a
    #    single palette mapping over the Rastan object provably covers the whole player vocabulary.
    seen = {}; agg = []
    for src in (tmap, lmap):
        for pieces in src.values():
            for p in pieces:
                if p["code"] not in seen:
                    seen[p["code"]] = 1
                    agg.append({"code": p["code"], "x": (len(agg) % 8) * 16, "y": (len(agg) // 8) * 16,
                                "fx": False, "fy": False})
    out.append(("rastan_body_complete", "Rastan palette coverage (all %d torso + %d leg cells)" %
                (len(tmap), len(lmap)), agg, "diagnostic", 999, MAPKEY))
    counts = {"fullbody": len(_h24_fullbody_pairings()), "torso": len(tmap), "legs": 52,
              "legs_nonblank": len(lmap)}
    return out, counts


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


def _comp_pieces(base, anim, comp, minp=1):
    """Compositor-VM pieces for a (base, anim, compositor_selector), anchored to (0,0), keeping each piece's
    own palette nibble. Like _manifest_vm_pieces but with an explicit compositor selector and a configurable
    minimum piece count (rewards are a single authentic tile). Empty if fewer than `minp` pieces."""
    import sys
    p = os.path.join(ROOT, "tools/graphics_optimizer")
    if p not in sys.path:
        sys.path.insert(0, p)
    try:
        from compositor_vm import ActorRenderState, visible_pieces
        sat = visible_pieces(ActorRenderState(base, anim, comp))
    except Exception:
        return []
    if len(sat) < minp:
        return []
    def s9(v):
        v &= 0x1FF
        return v - 0x200 if v & 0x100 else v
    raw = [{"code": q.tile & 0x1FFF, "x": s9(q.x), "y": s9(q.y),
            "fx": bool(q.hflip), "fy": bool(q.vflip), "palette": int(q.palette) & 0xF} for q in sat]
    ox = min(q["x"] for q in raw); oy = min(q["y"] for q in raw)
    return [{"code": q["code"], "x": q["x"] - ox, "y": q["y"] - oy, "fx": q["fx"], "fy": q["fy"],
            "palette": q["palette"]} for q in raw]


_ROPE_USAGES_CACHE = None
def rope_climber_usages():
    """PROMPT-ID-0091 (Cody PROMPT-ID-0090): the family-8 ROPE CLIMBER, split OUT of the Green Sword Knight.
    Cody source-proved base $0241, family 8, state $11 (handler $4684E family-8 branch), programs $56,$59,$5A
    (comp 0). This is a DISTINCT (base, program) identity -- NOT the $033E knight. Human visual label is only
    Tighe-visual (PARTIAL); the technical actor identity is PROVEN. Its mapping is INDEPENDENT of the knight
    (the current $033E-generated mapping does not apply). R1-S2 scene usage; per-piece arcade palettes."""
    global _ROPE_USAGES_CACHE
    if _ROPE_USAGES_CACHE is not None:
        return _ROPE_USAGES_CACHE
    out = []
    obj = "object:castle.rope_climber.family8.r1"
    note = ("base $0241, family 8, state $11; handler $4684E family-8 branch selects $56,$59,$5A for the LIVE "
            "actor base $0241 (Cody PROMPT-ID-0090). SEPARATE from the $033E Green Sword Knight; a program "
            "number is not a global sprite identity. Human identity 'Rope Climber' is Tighe-visual (PARTIAL).")
    for order, anim in enumerate((0x56, 0x59, 0x5A)):
        pcs = _comp_pieces(0x0241, anim, 0, minp=2)
        if not pcs:
            continue
        xs = [p["x"] for p in pcs]; ys = [p["y"] for p in pcs]
        nibs = sorted({p["palette"] for p in pcs})
        out.append({
            "usage_id": "usage:rope_climber_r1:anim0x%02X" % anim, "object_id": obj, "map_key": obj,
            "frame_category": "Rope climb (family 8)", "frame_label": "program 0x%02X" % anim, "frame_order": order,
            "player_counts": None, "weapon_counts": None,
            "display_name": "Rope Climber", "variant_label": "family-8 base $0241 (R1-S2)",
            "sprite_bank": "0x3%X" % nibs[0], "sprite_banks": ["0x3%X" % n for n in nibs], "multi_bank": len(nibs) > 1,
            "scene_key": "PAL-R1-S2-PLANEA-CASTLE", "round": 1, "subround": "R1-S2", "base": "0x0241",
            "family": 8, "provisional": True, "identity_note": note,
            "view": "authoring", "authorable": True, "membership": "scene",
            "hardware_class": "PC090OJ sprite", "human_identity_status": "partial",
            "human_identity_label": "Rope Climber (Tighe visual)",
            "mapping_scope": "scene", "confidence": "technical PROVEN · human PARTIAL",
            "pieces": pcs, "n_pieces": len(pcs),
            "bounds": [max(xs) - min(xs) + 16, max(ys) - min(ys) + 16],
            "composite_proven": True, "preview_type": "ARCADE COMPOSITE (family-8 $0241)",
            "used_colors": _castle_used_colors(pcs, 1), "mrd_pairs": [],
            "n_used": len({(p["palette"], v) for p in pcs for v in cell_indices(p["code"]) if v}),
        })
    _ROPE_USAGES_CACHE = out
    return out


# Cody PROMPT-ID-0090 exact reward census: kind -> (anim, code, identity_byte, value, embedded_line).
# All 17 are family-12 base $0A5A under compositor 2 (one authentic tile per kind); +$27 override is clear.
# kinds 1-13 -> embedded palette line 0; kinds 14-17 -> embedded palette line 3. Exact human item names are
# PENDING (do NOT guess axe/hammer/etc from silhouette). Reward identity table 0x40C2E, score table 0x40C40.
_REWARD_TABLE = [
    (1, 0x13, 0xA5A, 0x17, 0x0010, 0), (2, 0x14, 0xA5B, 0x18, 0x0020, 0), (3, 0x15, 0xA5C, 0x19, 0x0030, 0),
    (4, 0x16, 0xA5D, 0x12, 0x0100, 0), (5, 0x17, 0xA5E, 0x13, 0x0200, 0), (6, 0x18, 0xA5F, 0x14, 0x0010, 0),
    (7, 0x19, 0xA60, 0x15, 0x0020, 0), (8, 0x1A, 0xA61, 0x1D, 0x0020, 0), (9, 0x1B, 0xA62, 0x1C, 0x0020, 0),
    (10, 0x1C, 0xA63, 0x16, 0x0010, 0), (11, 0x1D, 0xA65, 0x1B, 0x0010, 0), (12, 0x1E, 0xA67, 0x1A, 0x0050, 0),
    (13, 0x1F, 0xA69, 0x11, 0x0030, 0), (14, 0x20, 0xA6E, 0x0D, 0x0010, 3), (15, 0x21, 0xA6F, 0x0E, 0x0015, 3),
    (16, 0x22, 0xA70, 0x0F, 0x0020, 3), (17, 0x23, 0xA71, 0x10, 0x0025, 3),
]
_REWARD_USAGES_CACHE = None
def gameplay_reward_usages():
    """PROMPT-ID-0091 (Cody PROMPT-ID-0090): the 17 gameplay rewards as ONE parent object with 17 individual
    children. The false three-bank model ($30/$31/$37) is removed. Source path: schedule +$36 ->
    $40CCC/$40D32 -> family 12, base $0A5A -> compositor 2 -> anim $13-$23 -> embedded palette line 0 (kinds
    1-13) or 3 (kinds 14-17). One reward child = ONE source record = ONE authentic tile. NOTHING is
    auto-mapped to a Genesis line (Tighe authors targets)."""
    global _REWARD_USAGES_CACHE
    if _REWARD_USAGES_CACHE is not None:
        return _REWARD_USAGES_CACHE
    parent = "object:item.gameplay_rewards"
    out = []
    for kind, anim, code, ident, value, line in _REWARD_TABLE:
        pcs = _comp_pieces(0x0A5A, anim, 2, minp=1)
        # Fall back to the exact source tile code if the single-piece composite is empty.
        if not pcs:
            pcs = [{"code": code, "x": 0, "y": 0, "fx": False, "fy": False, "palette": line}]
        pal = _arcade_round_palette(1, line)
        used = {}
        for p in pcs:
            for v in cell_indices(p["code"]):
                if v:
                    used[v] = used.get(v, 0) + 1
        used_colors = []
        for idx in sorted(used):
            rgb = pal[idx] if idx < len(pal) else [0, 0, 0]
            disp, cram, _ = gen_quant(rgb)
            used_colors.append({"src_index": idx, "arcade_rgb8": rgb, "hex": "#%02X%02X%02X" % tuple(rgb),
                                "pixel_count": used[idx], "genesis_rgb8": disp, "genesis_cram": cram})
        xs = [p["x"] for p in pcs]; ys = [p["y"] for p in pcs]
        child = "object:item.reward.kind%02d" % kind
        out.append({
            "usage_id": "usage:reward_kind%02d:anim0x%02X" % (kind, anim),
            "object_id": parent, "map_key": child, "child_id": child,
            "group_label": "Gameplay Rewards",
            "frame_category": ("Kinds 1-13 · embedded line 0" if line == 0 else "Kinds 14-17 · embedded line 3"),
            "frame_label": "Kind %d · code $%03X" % (kind, code), "frame_order": kind,
            "player_counts": None, "weapon_counts": None,
            "display_name": "Gameplay Rewards", "variant_label": "Kind %d (identity $%02X)" % (kind, ident),
            "sprite_bank": "0x3%X" % line, "sprite_banks": ["0x3%X" % line], "multi_bank": False,
            "scene_key": None, "round": None, "subround": None, "base": "0x0A5A", "family": 12,
            "provisional": True, "membership": "shared", "view": "authoring", "authorable": True,
            "hardware_class": "PC090OJ sprite", "human_identity_status": "pending",
            "human_identity_label": "Reward kind %d — item name PENDING" % kind,
            "mapping_scope": "shared", "confidence": "source PROVEN · human name PENDING",
            "reward_meta": {"kind": kind, "identity_byte": "0x%02X" % ident, "value": "0x%04X" % value,
                            "anim": "0x%02X" % anim, "code": "0x%03X" % code, "compositor": 2,
                            "embedded_line": line},
            "identity_note": ("family-12 base $0A5A, compositor 2, anim $%02X, code $%03X; embedded palette "
                              "line %d; +$27 override clear. Human item name PENDING (no silhouette guessing)."
                              % (anim, code, line)),
            "pieces": pcs, "n_pieces": len(pcs),
            "bounds": [max(xs) - min(xs) + 16, max(ys) - min(ys) + 16],
            "composite_proven": True, "preview_type": "ARCADE REWARD (comp 2 · line %d)" % line,
            "used_colors": used_colors, "mrd_pairs": [], "n_used": len(used_colors),
        })
    _REWARD_USAGES_CACHE = out
    return out


_BOSS_USAGES_CACHE = None
def r1_boss_usages():
    """PROMPT-ID-0091 (Cody PROMPT-ID-0090): the Round 1 boss as a scene-local GROUP under R1-S3 / Sub-Round
    3, NOT a field enemy. Body: base $061D, rec type $0E, slot A5+$0708, compositor 1, anim $00, program
    $47908, embedded line F, +$27=0. Auxiliary (type-15): base $061D, rec type $0F, creator $457B2/$457D0,
    compositor 1, anim $14, program $47E54, embedded line F, +$27=0 (role/count/lifetime PARTIAL). Death/
    effect: PARTIAL until the phase inventory is complete. Palette: SOURCE LINE F is PROVEN; the exact staged
    RGB content is PARTIAL -- do NOT apply ordinary family-2 field-palette logic or invent colors, so these
    groups are NOT authorable yet."""
    global _BOSS_USAGES_CACHE
    if _BOSS_USAGES_CACHE is not None:
        return _BOSS_USAGES_CACHE
    scene = "PAL-R1-S3-PLANEA-BOSS"
    # NORMAL-STATE boss palette is PROVEN (Cody PROMT-ID-0095): the boss-specific ROM target table at
    # 0x4708C (15 words -> live physical line 0x4F) faded in by 0x47004. This is the body+dagger source
    # palette and is decoded from the ROM here, NOT the field pool 0x3BA88->0x4FD02 (0x4FE62 is rejected).
    BOSS_ROM_ADDR = 0x4708C
    palF = _rom_boss_target_palette(BOSS_ROM_ADDR, 15)
    DAGGER_INDICES = [0, 3, 4, 5, 6, 8, 10, 11, 13]   # dagger pixel-index subset (Cody PROMT-ID-0095)
    def _used(pcs, restrict=None):
        used = {}
        for p in pcs:
            for v in cell_indices(p["code"]):
                if v:
                    used[v] = used.get(v, 0) + 1
        uc = []
        for idx in sorted(used):
            if restrict is not None and idx not in restrict:
                continue
            rgb = palF[idx] if idx < len(palF) else [0, 0, 0]
            disp, cram, _ = gen_quant(rgb)
            uc.append({"src_index": idx, "arcade_rgb8": rgb, "hex": "#%02X%02X%02X" % tuple(rgb),
                       "pixel_count": used[idx], "genesis_rgb8": disp, "genesis_cram": cram,
                       "arcade_palette_line": "0x4F", "rom_source": "0x%05X" % BOSS_ROM_ADDR})
        return uc
    # Body uses the full source domain; the Flying Daggers share the SAME source palette (index subset).
    SPECS = [
        ("object:boss.r1.body", "Round 1 Boss — Body", 0x00, 0x47908, 0x0E,
         "slot A5+$0708, rec type $0E, base $061D, comp 1, anim $00, program $47908, +$27=0; embedded line F "
         "-> physical line $4F; normal-state palette PROVEN (ROM $4708C, Cody PROMT-ID-0095).",
         "proven", None),
        ("object:boss.r1.flying_daggers", "Round 1 Boss — Flying Daggers", 0x14, 0x47E54, 0x0F,
         "rec type $0F via $457B2/$457D0, base $061D, comp 1, anim $14 (flight $1A-$1F), programs "
         "$47E54/$47E7A/$47E7F/$47E84/$47E8D/$47E92/$47E97, pattern $67B,$67C,$683-$689, +$27=0; embedded "
         "line F -> physical line $4F. SHARES R1 BOSS PALETTE (Cody PROMT-ID-0095).", "proven", DAGGER_INDICES),
    ]
    out = []
    for order, (obj, name, anim, prog, rectype, note, idstat, restrict) in enumerate(SPECS):
        pcs = _comp_pieces(0x061D, anim, 1, minp=1)
        if not pcs:
            continue
        xs = [p["x"] for p in pcs]; ys = [p["y"] for p in pcs]
        is_dagger = restrict is not None
        out.append({
            "usage_id": "usage:boss_r1_%s:anim0x%02X" % (obj.split(".")[-1], anim),
            "object_id": obj, "map_key": obj, "group_label": "Round 1 Boss",
            "frame_category": "Round 1 Boss", "frame_label": name, "frame_order": order,
            "player_counts": None, "weapon_counts": None,
            "display_name": name, "variant_label": "R1-S3 · program $%05X · physical line $4F" % prog,
            "sprite_bank": "0x3F", "sprite_banks": ["0x3F"], "multi_bank": False,
            "scene_key": scene, "round": 1, "subround": "R1-S3", "base": "0x061D",
            "record_type": "0x%02X" % rectype, "compositor": 1, "program": "0x%05X" % prog,
            # Palette RGB is PROVEN (ROM-sourced). Authoring stays gated on Tighe's final Genesis line
            # mapping (one shared context for body + daggers); the tool never auto-assigns a Genesis line.
            "provisional": False, "membership": "scene", "view": "authoring", "authorable": False,
            "hardware_class": "PC090OJ sprite", "human_identity_status": idstat,
            "human_identity_label": name,
            "flying_daggers": is_dagger,
            "shares_boss_palette": True,
            "shared_palette_context": "R1 Boss + Flying Daggers",
            "palette_line_requirement": "1 line (normal body+dagger presentation)",
            "mapping_scope": "scene", "confidence": "normal-state palette ROM-source PROVEN (Cody PROMT-ID-0095)",
            "palette_status": {"source_line": "F", "source_line_proven": True,
                               "physical_line": "0x4F",
                               "rgb_status": "PROVEN — ROM 0x4708C boss target table (Cody PROMT-ID-0095)",
                               "rom_source": "0x4708C-0x470A9", "count": 15, "index0": "black",
                               "fade_writer": "0x47004", "fade_lut": "0x46F84",
                               "note": "Boss-specific ROM target faded to physical line 0x4F; NOT the field pool "
                                       "0x3BA88->0x4FD02 (0x4FE62 and master line 0x4EE16 both rejected)."},
            "identity_note": note,
            "pieces": pcs, "n_pieces": len(pcs),
            "bounds": [max(xs) - min(xs) + 16, max(ys) - min(ys) + 16],
            "composite_proven": True,
            "preview_type": "R1 BOSS — ROM $4708C palette PROVEN (physical line $4F)",
            "used_colors": _used(pcs, restrict), "mrd_pairs": [], "n_used": 0,
        })
    # Death / post-boss effect group: PARTIAL phase inventory, no fabricated art, not authorable.
    out.append({
        "usage_id": "usage:boss_r1_effect_death:info", "object_id": "object:boss.r1.effect.death",
        "map_key": "object:boss.r1.effect.death", "group_label": "Round 1 Boss",
        "frame_category": "Round 1 Boss", "frame_label": "Death / post-boss effect", "frame_order": 90,
        "player_counts": None, "weapon_counts": None,
        "display_name": "Round 1 Boss — Death / Effect", "variant_label": "R1-S3 · phase inventory PARTIAL",
        "sprite_bank": "0x00", "sprite_banks": [], "multi_bank": False,
        "scene_key": scene, "round": 1, "subround": "R1-S3", "base": "0x061D",
        "provisional": True, "incomplete": True, "membership": "scene", "view": "authoring",
        "authorable": False, "hardware_class": "PC090OJ sprite", "human_identity_status": "partial",
        "human_identity_label": "Boss death/effect (phase inventory PARTIAL)",
        "mapping_scope": "scene", "confidence": "PARTIAL — full phase sequence not enumerated",
        "identity_note": ("boss behavior later activates death/effect records; the exact R1 phase sequence is "
                          "NOT enumerated. No fabricated art; disabled for authoring until proven."),
        "pieces": [], "n_pieces": 0, "bounds": [16, 16], "composite_proven": False,
        "preview_type": "PARTIAL — phase inventory pending (no static composite)",
        "used_colors": [], "mrd_pairs": [], "n_used": 0,
    })
    _BOSS_USAGES_CACHE = out
    return out


# PROMPT-ID-0091 (Cody PROMPT-ID-0090 §R1-S2 Trap/Hazard Audit): the visible R1-S2 hazards are PLANE-A (or
# mixed tile/palette-animation) graphics whose exact source (tile,bank,flip) subset is PENDING. They are NOT
# the PC090OJ actor bases $0224 (pit flame = R2/R4) or $09EA (spike/spear/stalagmite = R5). Each is shown as
# a disabled candidate ("SOURCE SUBSET PENDING") so it can never be authored against fabricated source codes.
_R1S2_HAZARD_CANDIDATES = [
    ("floor_spikes", "Floor Spikes", "Plane A", "Static/animated floor spike tiles; not R1 $09EA."),
    ("moving_spiked_trap", "Suspended / Moving Spike Trap", "Plane A / mixed",
     "Separate object; never merge with floor spikes."),
    ("moving_wood_gate", "Moving Wooden Gate", "Plane A / mixed",
     "Not automatically the collision-$7E exit; separate gate art."),
    ("falling_water", "Falling Water", "Plane A + palette animation (PARTIAL)",
     "Likely tile + palette animation; not proven the R1-S1 $59AD4 mechanism."),
    ("pit_flame_animation", "Pit Flame Animation", "Plane A / palette animation",
     "NOT base $0224 ($0224 = R2/R4). Separate from static lava."),
    ("static_lava", "Static Lava / Pit Field", "Plane A scene map",
     "Scene-environment group; raw Layer-A tiles exist, semantic subset pending."),
    ("rope_chain_terrain", "Rope / Chain Terrain", "Plane A + collision",
     "Map/collision traversal; player-state owner, not a sprite."),
]
def r1s2_hazard_candidates():
    """PROMPT-ID-0091: disabled R1-S2 Plane-A hazard candidate groups (SOURCE SUBSET PENDING). Human name +
    round/sub-round + hardware class + what-is-known only; NO pieces, NO source codes, NOT authorable."""
    out = []
    for order, (key, name, hw, note) in enumerate(_R1S2_HAZARD_CANDIDATES):
        obj = "object:hazard.r1s2.%s" % key
        out.append({
            "usage_id": "usage:hazard_r1s2_%s:info" % key, "object_id": obj, "map_key": obj,
            "frame_category": "Hazards / Traps (Plane A — pending)", "frame_label": name, "frame_order": order,
            "player_counts": None, "weapon_counts": None,
            "display_name": name, "variant_label": "R1-S2 · SOURCE SUBSET PENDING",
            "sprite_bank": "0x00", "sprite_banks": [], "multi_bank": False,
            "scene_key": "PAL-R1-S2-PLANEA-CASTLE", "round": 1, "subround": "R1-S2", "base": None,
            "provisional": True, "incomplete": True, "hazard_pending": True,
            "membership": "scene", "view": "authoring", "authorable": False,
            "hardware_class": hw, "human_identity_status": "partial",
            "human_identity_label": "%s (Tighe visual)" % name,
            "mapping_scope": "scene", "confidence": "hardware class known · source (tile,bank,flip) subset PENDING",
            "identity_note": ("R1-S2 hazard, %s. %s Exact source (tile,bank,flip) subset is PENDING — not "
                              "authorable against fabricated codes. $0224=R2/R4, $09EA=R5 are excluded." % (hw, note)),
            "pieces": [], "n_pieces": 0, "bounds": [16, 16], "composite_proven": False,
            "preview_type": "SOURCE SUBSET PENDING (Plane-A candidate)",
            "used_colors": [], "mrd_pairs": [], "n_used": 0,
        })
    return out


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
    # Rastan BODY: complete H24 static player inventory (two-half torso 0x5BD40 + legs 0x5C466, all on
    # palette line 3 -> bank 0x33). Consumes generated authoritative H24 data, NOT a hand-written frame
    # list, so mapping the player palette ONCE covers every torso/leg frame that uses it.
    h24_frames, _h24_counts = h24_player_frames()
    _player_meta = {}
    for key, label, pieces, category, order, map_key in h24_frames:
        if pieces:   # H24 pieces are already anchor-relative {code,x,y,fx,fy}
            _player_meta[key] = {"category": category, "order": order, "map_key": map_key,
                                 "frame_label": label.split(" (")[0]}
            defs.append((key, label, 0x33, pieces, True))
    # Equipped weapons (SWORD/AXE/HAMMER/FIRE SWORD) as first-class authorable overlay objects.
    weap_frames, _weap_counts = h24_weapon_frames()
    for key, label, pieces, category, order, map_key in weap_frames:
        if pieces:
            _player_meta[key] = {"category": category, "order": order, "map_key": map_key,
                                 "frame_label": label, "object_id": map_key, "counts": _weap_counts}
            defs.append((key, label, 0x33, pieces, True))
    # Complete enemy corpora: one complete-coverage usage per enemy (full census cell set / effective
    # bank) so authoring the enemy once covers its ENTIRE animation vocabulary, not just a representative
    # frame. Shares the enemy's object_id, so it collapses into the same palette domain as the
    # representative composite. Marked a cell-sheet (not a shaped composite).
    enemy_full, _enemy_counts = enemy_complete_usages()
    for key, label, pieces, ebank, obj_id in enemy_full:
        if pieces:
            ename = obj_id.split(".")[-1]
            # share the SAME map_key as the existing representative usage (usage:<name>:bank0x<bank>)
            # so the enemy's already-authored Test.json mapping applies to the complete corpus too.
            _player_meta[key] = {"category": "complete", "order": 900,
                                 "map_key": "usage:%s:bank0x%02X" % (ename, ebank),
                                 "frame_label": label, "object_id": obj_id, "counts": _enemy_counts,
                                 "cellsheet": True}
            defs.append((key, label, ebank, pieces, False))

    # Decompilation-proven non-enemy objects, rendered via the SAME compositor VM the Bestiary uses (manifest
    # render specs), so identity is static/decompiled — never trace-derived. Local banks copy so injecting the
    # arcade source palettes never mutates the caller's dict.
    banks = dict(banks)
    # (a) Destroyable cave-entrance block (H17, hazard). Reuses the EXISTING authored Test mapping
    #     usage:cave_block:bank0x3C (control 0xC -> line 0xC -> bank 0x3C; arcade R1 pool-35 palette).
    banks.setdefault(0x3C, _arcade_round_palette(1, 12))
    cave_pieces = _manifest_vm_pieces(0x0179, 0x70, 0)
    if cave_pieces:
        _player_meta["cave_block"] = {"category": "hazard", "order": 950,
                                      "map_key": "usage:cave_block:bank0x3C",
                                      "frame_label": "Cave Entrance Block",
                                      "object_id": "object:hazard.cave_block"}
        defs.append(("cave_block", "Cave Entrance Block", 0x3C, cave_pieces, True))
    # (b) Burst / impact effect (H16, base 0x0275): three proven forms 0x9E/0x9F/0xA0 that SHARE one palette
    #     identity (compositor control nibble 0 -> arcade R1 line 0 -> bank 0x30). No Test.json mapping exists
    #     -> naturally shown UNAUTHORED; this task never authors/saves it.
    banks[0x30] = _arcade_round_palette(1, 0)
    for aid, lbl in ((0x9E, "0x9E (8 pieces)"), (0x9F, "0x9F (9 pieces)"), (0xA0, "0xA0 (10 pieces)")):
        bp = _manifest_vm_pieces(0x0275, aid, 0)
        if bp:
            k = "burst_%02x" % aid
            _player_meta[k] = {"category": "effect", "order": 960 + aid,
                               "map_key": "usage:burst:bank0x30",
                               "frame_label": "Burst / Impact %s" % lbl,
                               "object_id": "object:effect.burst"}
            defs.append((k, "Burst / Impact Effect frame %s" % lbl, 0x30, bp, True))
    # (c) GAMEPLAY HUD + ATTRACT GAME OVER PC090OJ sprite families (Cody provenance
    #     docs/design/Cody_gameover_1up_palette_provenance.md). All three share effective bank 0x30
    #     with the burst effect (round-1 nibble-0 pool entry 11 -> arcade palette 0x4FE62), but they are
    #     DIFFERENT semantic graphic/pattern families and must be independently authorable. They are keyed
    #     by their own object_id (NOT usage:...:bank0x30), so the bank-keyed palette-line LUT generator
    #     (gen_pc090oj_palsel_lut.py, regex :bank0xNN) does not collapse them into usage:burst:bank0x30;
    #     their per-object index_map is the color-ownership route (gen_reindexed_pc090oj.py, keyed by uid).
    #     Raw PC090OJ pattern codes laid out as a left-to-right row for authoring preview.
    def _raw_row(codes):
        return [{"code": c, "x": i * 16, "y": 0, "fx": 0, "fy": 0} for i, c in enumerate(codes)]
    banks[0x30] = _arcade_round_palette(1, 0)
    _hud_gameover = [
        ("attract_game_over", "Attract GAME OVER (large flashing)",
         [0x37, 0x38, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44],
         "object:attract.game_over", "attract", 980),
        ("hud_p1_label", "Gameplay P1 / 1UP label",
         [0x39, 0x46, 0x48],
         "object:hud.p1_label", "hud", 981),
        ("hud_score_digits", "Gameplay SCORE digits",
         [0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33],
         "object:hud.score_digits", "hud", 982),
    ]
    for key, label, codes, obj_id, cat, order in _hud_gameover:
        pieces = _raw_row(codes)
        _player_meta[key] = {"category": cat, "order": order, "map_key": obj_id,
                             "frame_label": label, "object_id": obj_id}
        defs.append((key, label, 0x30, pieces, True))
    # (d) DEATH / EFFECT families (H25 taxonomy; rastan_actor_behavior.c + raw/00040ccc + raw/00042abc;
    #     palette nibbles from the compositor VM control byte, H15 rule). Effective bank = 0x30 | control.
    #     - bat_death: base 0x0275 anim 0xA8 (0x42ABC A8 branch) = ONE frame, Small(0x0268)+Large(0x03F6)
    #       bats share it; distinct pattern cell from the burst 0x9D-0xA0; shares burst palette (bank 0x30).
    #     - specialized_death_019d: base 0x019D (0x42ABC type<8), bank 0x34; reachable (actor 0x019D
    #       rec_type 0/3). specialized_death_09dc: base 0x09DC (0x42ABC type5, +0x3D bit7), bank 0x33.
    #   GAMEPLAY REWARDS are NOT here any more: the false three-bank model (kinds 1-4 -> 0x30, 5-13 -> 0x31,
    #   14-17 -> 0x37) is DISPROVEN (Cody PROMPT-ID-0090). All 17 reward kinds are one family-12 base $0A5A
    #   actor under compositor 2; embedded palette line = 0 (kinds 1-13) / 3 (kinds 14-17); modeled below as
    #   one parent object + 17 individual children (gameplay_reward_usages).
    banks.setdefault(0x31, _arcade_round_palette(1, 1))
    banks.setdefault(0x33, _arcade_round_palette(1, 3))
    banks.setdefault(0x34, _arcade_round_palette(1, 4))
    banks.setdefault(0x37, _arcade_round_palette(1, 7))
    _death_families = [
        ("bat_death", "Bat death (one-frame, Small+Large)", 0x0275, 0xA8, 0x30, "object:effect.bat_death", "death", 990),
        ("specialized_death_019d", "Specialized enemy death (base 0x019D, rec_type<8)", 0x019D, 0x2A, 0x34,
         "object:effect.specialized_death_019d", "death", 994),
        ("specialized_death_09dc", "Specialized enemy death (base 0x09DC, type5)", 0x09DC, 0xC2, 0x33,
         "object:effect.specialized_death_09dc", "death", 995),
    ]
    for key, label, base, anim, bank, obj_id, cat, order in _death_families:
        pieces = _manifest_vm_pieces(base, anim, 0)
        if pieces:
            _player_meta[key] = {"category": cat, "order": order, "map_key": obj_id,
                                 "frame_label": label, "object_id": obj_id}
            defs.append((key, label, bank, pieces, True))

    usages = list(green_knight_usages())  # PROMPT-ID-0069: Green Sword Knight, all castle sections (cached)
    usages += list(r1s2_castle_usages())  # PROMPT-ID-0029: scene-tagged R1-S2 castle actors (cached)
    usages += list(rope_climber_usages())        # PROMPT-ID-0091: family-8 base $0241 rope climber (split)
    usages += list(gameplay_reward_usages())     # PROMPT-ID-0091: 17 reward children (comp 2; lines 0/3)
    usages += list(r1_boss_usages())             # PROMPT-ID-0091: R1-S3 boss body + type-15 aux + death
    usages += list(r1s2_hazard_candidates())     # PROMPT-ID-0091: R1-S2 Plane-A hazard candidates (disabled)
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
        meta = _player_meta.get(key)
        # All frames of one object share ONE palette-mapping key (map_key) so a single mapping covers
        # every frame; enemies key by their own usage_id.
        map_key = meta["map_key"] if meta else ("usage:%s:bank0x%02X" % (key, bank))
        if meta and meta.get("object_id"):
            obj_id = meta["object_id"]                       # weapon objects
        elif key.startswith("rastan"):
            obj_id = "object:player.rastan"
        else:
            obj_id = "object:enemy.%s" % key
        usages.append({"usage_id": "usage:%s:bank0x%02X" % (key, bank),
                       "object_id": obj_id,
                       "map_key": map_key,
                       "frame_category": (meta["category"] if meta else None),
                       "frame_label": (meta["frame_label"] if meta else name),
                       "frame_order": (meta["order"] if meta else 0),
                       "player_counts": (_h24_counts if key.startswith("rastan") else None),
                       "weapon_counts": (meta.get("counts") if meta and meta.get("object_id") else None),
                       "display_name": name, "sprite_bank": "0x%02X" % bank,
                       "pieces": pieces, "n_pieces": len(pieces), "bounds": bounds,
                       "composite_proven": proven,
                       "preview_type": "TRUE ARCADE COMPOSITE" if proven else "PROVEN CELL SHEET",
                       # PROMPT-ID-0038 §10: scene-membership class so the editor does not show field
                       # enemies in the castle. Enemies are FIELD (Phase-1/S1) actors (field schedule
                       # 0x4A02A -> family table); player/weapons/items/effects/hazards are SHARED.
                       "membership": "field_phase1" if obj_id.startswith("object:enemy.") else "shared",
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


SUBROUND_CORPUS = os.path.join(ROOT, "analysis/graphics_optimizer/subround_corpus")
def _scene_corpus_dir(scene):
    """Return the per-subround corpus dir for a PLANEA scene_key, or None (-> R1-P1 default)."""
    if not scene:
        return None
    d = os.path.join(SUBROUND_CORPUS, scene)
    return d if os.path.isfile(os.path.join(d, "plane_a_uses.json")) else None


def plane_bank_colors(scene=None):
    """Layer-A source palette banks (arcade RGB8), keyed by hex id. For a subround scene with its
    own corpus, load that scene's arcade banks (records 16-45 castle/boss/R2); else Round-1 P1."""
    sd = _scene_corpus_dir(scene)
    if sd:
        p = loadj(os.path.join(sd, "plane_palette_banks.json"), {"banks": {}})
        return {bid: bb["arcade_rgb8"] for bid, bb in p.get("banks", {}).items() if bb.get("arcade_rgb8")}
    return _plane_bank_colors_r1p1()


def _plane_bank_colors_r1p1():
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


_LAYERA = {}
def build_layera(scene=None):
    """Layer-A corpus for a scene: every physical pattern + every logical usage.  Default (scene=None)
    is the frozen Round-1 Phase-1 census; a subround scene_key loads its per-subround arcade corpus
    (RG-022).  physical_pattern (sha256 of the 32 raw tile bytes) is authoritative identity."""
    key = scene or "__r1p1__"
    if key in _LAYERA:
        return _LAYERA[key]
    sd = _scene_corpus_dir(scene)
    pa = loadj(os.path.join(sd, "plane_a_uses.json") if sd else os.path.join(ANALYZER, "plane_a_uses.json"), [])
    all_banks = plane_bank_colors(scene)
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
    _LAYERA[key] = {"patterns": patterns, "usages": usages, "hash2pid": hash2pid,
               "banks": {b: all_banks[b] for b in used_bank_ids if b in all_banks},
               "bank_ids": used_bank_ids, "scene": scene,
               "counts": {"physical_patterns": len(patterns), "logical_usages": len(usages),
                          "palette_banks": len(used_bank_ids),
                          "multi_palette_patterns": sum(1 for p in patterns if p["multi_palette"])}}
    return _LAYERA[key]


def layera_pattern_detail(pid, scene=None):
    """Full detail for one physical pattern: pixels, every logical usage, and every palette variant."""
    la = build_layera(scene)
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


_PC080SN = None
_PA_DEC = None
_PA_COMP = None
def _pc080sn():
    global _PC080SN
    if _PC080SN is None:
        _PC080SN = open(os.path.join(ROOT, "build/regions/pc080sn.bin"), "rb").read()
    return _PC080SN
def _plane_a_modules():
    """Cody's canonical, selector-aware arcade Plane-A decoder + the record-selector lookup.
    Reused verbatim so the editor's map display matches the native Genesis assembly (never a JS rotation)."""
    global _PA_DEC, _PA_COMP
    if _PA_DEC is None:
        import importlib.util, sys as _sys
        def _ld(rel, name):
            sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
            m = importlib.util.module_from_spec(sp); _sys.modules[name] = m
            sp.loader.exec_module(m); return m
        _PA_DEC = _ld("tools/audit_round1_phase1_plane_a.py", "pa_dec")
        _PA_COMP = _ld("tools/translation/compile_pc080sn_genesis.py", "pa_comp")
    return _PA_DEC, _PA_COMP


def layera_map(seg, scene=None):
    """Reconstruct one Layer-A record's COMPLETE 64x64 backing tilemap from the arcade tables using
    Cody's SELECTOR-AWARE canonical decoder (reconstruct_segment): selector-0 records keep source
    coordinates; selector-1 (vertical) records apply the arcade block-coordinate transpose, so the
    editor map matches the real arcade orientation (records 17/21/43/44). Every nonblank cell resolves
    to its logical usage (tile_code + palette_bank)."""
    _ckey = (seg, scene)
    if _ckey in _MAPCACHE:
        return _MAPCACHE[_ckey]
    la = build_layera(scene)
    bybank = {}
    for u in la["usages"]:
        bybank.setdefault((u["tile_code"], u["palette_bank"]), u)
    dec, comp = _plane_a_modules()
    mc = _maincpu(); gfx = _pc080sn()
    selector = comp.decode_record_selector(mc, seg)
    src = dec.reconstruct_segment(mc, gfx, seg, "visible", selector=selector)
    cells = []
    codes = set()
    descriptor_cells = len(src)
    blank_cells = 0
    for cell in src:
        code = cell.tile_code
        if not any(tile_indices8(code)):     # fully-transparent (blank) tile — counted, not emitted
            blank_cells += 1
            continue
        attr = cell.attr
        bank = "0x%03X" % (attr & 0x1FF)
        u = bybank.get((code, bank))
        cells.append({"c": cell.segment_column, "r": cell.world_row, "code": code, "bank": bank,
                      "hf": 1 if attr & 0x4000 else 0, "vf": 1 if attr & 0x8000 else 0,
                      "attr": "0x%04X" % attr, "entry": "0x%06X" % 0,
                      "descr": "0x%06X" % cell.descriptor_offset,
                      "uid": (u["usage_id"] if u else None), "pid": (u["pattern_id"] if u else None)})
        codes.add(code)
    tiles = {str(c): tile_indices8(c) for c in codes}
    out = {"seg": seg, "selector": selector, "cols": _MAP_COLS, "rows": _MAP_ROWS, "row0": 0, "nrows": _MAP_ROWS,
           "visible_viewport": {"row0": _MAP_VIS_ROW0, "nrows": _MAP_VIS_NROWS},
           "total_cells": _MAP_ROWS * _MAP_COLS, "descriptor_cells": descriptor_cells,
           "blank_cells": blank_cells, "nonblank_cells": len(cells),
           "resolved": sum(1 for c in cells if c["uid"]),
           "unresolved": sum(1 for c in cells if not c["uid"]),
           "tiles": tiles, "cells": cells}
    _MAPCACHE[_ckey] = out
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


def phase_layera_automap(line, target_colors, scene=None):
    """Map EVERY Layer-A logical usage OF THE REQUESTED SCENE onto the fixed populated entries of one
    Genesis line.  scene=None uses the R1/P1 phase corpus; a PAL-* scene_key uses that subround's own
    per-scene corpus (PROMPT-ID-0009).  Per usage: injective (MRD=0) min-cost assignment of its used
    arcade colors -> populated target entries, cost = pixel-weighted CIEDE2000.  Target colors are NOT
    changed.  Usages needing more distinct colors than the line has populated entries are BLOCKED.
    The response echoes the scene identity so the client can verify before applying."""
    la = build_layera(scene)
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
    return {"line": line, "scene": scene, "proposals": proposals, "summary": summary,
            "worst": [{"worst_de": round(w, 2), "usage_id": uid, "pattern_id": pid, "mean_de": m}
                      for w, uid, pid, m in worst_list[:20]]}


def _cram_rgb(cram):
    w = int(cram, 16) if isinstance(cram, str) else int(cram)
    R = (w >> 1) & 7; G = (w >> 5) & 7; B = (w >> 9) & 7
    return LV3[R], LV3[G], LV3[B]


def _nearest_cram(rgb, taken=None):
    """Closest legal Genesis CRAM to rgb by CIEDE2000; if `taken` (a set of cram strings) is given,
    skip those so a tile's distinct source colors stay distinct (MRD=0)."""
    best = None
    for B in range(8):
        for G in range(8):
            for R in range(8):
                cram = "0x%04X" % ((B << 9) | (G << 5) | (R << 1))
                if taken is not None and cram in taken:
                    continue
                d = _de00(rgb, [LV3[R], LV3[G], LV3[B]])
                if best is None or d < best[1]:
                    best = (cram, d)
    return best[0] if best else "0x0000"


def derive_scene_palette(scene, lines=(0, 1, 3), skip_usages=(), only_bank=None):
    """Derive the scene's closest-possible Genesis palette and per-usage mappings onto the CHOSEN target
    line(s), honoring Plane-A semantics (each tile/usage draws from exactly ONE palette line).

    Method:
      - Each Layer-A usage uses one arcade bank; collect, per bank, the distinct arcade colors its
        usages actually use, each quantized to its nearest legal CRAM (distinct within the bank, so a
        bank never self-merges -> MRD 0).
      - Pack the banks into the requested line(s), each line holding <=15 CRAMs, merging banks that share
        colors; a bank that cannot fit is BLOCKED (its usages are reported, never dropped/substituted).
      - Emit each line's palette (index 1..15) and, per usage, line + index_map onto those entries.
    `skip_usages` enables ONE-LINE-AT-A-TIME use: any bank that already has a mapped usage is treated as
    already placed and excluded, so running again on another line fills the REMAINING banks instead of
    re-deriving everything. Target CRAM colors are proposed, not written, until the client applies.
    Line 2 is never a target.
    """
    la = build_layera(scene)
    banks = la["banks"]
    usages = la["usages"]
    lines = [l for l in lines if l not in RESERVED_LINES]
    skip = set(skip_usages)
    # banks already placed on another line (any of their usages already mapped) -> excluded this pass.
    # With only_bank (remap a single bank), ignore prior placements and consider just that bank.
    placed_banks = set() if only_bank is not None else {u["palette_bank"] for u in usages if u["usage_id"] in skip}

    # bank -> {src_index: nearest distinct CRAM} (distinct within the bank); skip already-placed banks
    bank_used = {}
    for u in usages:
        if only_bank is not None and u["palette_bank"] != only_bank:
            continue
        if u["palette_bank"] in placed_banks:
            continue
        bank_used.setdefault(u["palette_bank"], set()).update(u.get("used_indices", []))
    bank_colors = {}
    for b, idxs in bank_used.items():
        pal = banks.get(b, [[0, 0, 0]] * 16)
        taken, cmap = set(), {}
        for si in sorted(idxs):
            rgb = pal[si] if si < len(pal) else [0, 0, 0]
            c = _nearest_cram(rgb, taken)
            taken.add(c); cmap[si] = c
        bank_colors[b] = cmap
    bank_cramset = {b: set(cmap.values()) for b, cmap in bank_colors.items()}

    # PROMPT-ID-0010 fix: prioritize banks by how much of the scene they actually COVER (summed
    # map_cell_count = screen area), so ubiquitous structure (grey stone, green) wins the limited 15
    # slots and localized accents (flames) are the ones blocked — not the reverse. Tie-break: fewer
    # colors (easier to fit).
    bank_area = {}
    for u in usages:
        b = u["palette_bank"]
        if b in placed_banks:
            continue
        bank_area[b] = bank_area.get(b, 0) + (u.get("map_cell_count") or 1)

    # greedy pack banks (most-covering first) into line-bins of capacity 15, preferring the least growth
    bins = [{"line": ln, "crams": set(), "banks": []} for ln in lines]
    blocked_banks = []
    for b in sorted(bank_cramset, key=lambda x: (-bank_area.get(x, 0), len(bank_cramset[x]))):
        cs = bank_cramset[b]
        if len(cs) > 15:
            blocked_banks.append(b); continue
        best = None
        for bn in bins:
            union = bn["crams"] | cs
            if len(union) <= 15:
                growth = len(union) - len(bn["crams"])
                if best is None or growth < best[1]:
                    best = (bn, growth, union)
        if best is None:
            blocked_banks.append(b)
        else:
            bn, _, union = best
            bn["crams"] = union; bn["banks"].append(b)

    # stable ordered line palettes + index lookup
    line_pal, cram_index, bank_line = {}, {}, {}
    for bn in bins:
        arr = [None] * 16
        for i, c in enumerate(sorted(bn["crams"]), start=1):
            arr[i] = c; cram_index[(bn["line"], c)] = i
        line_pal[bn["line"]] = arr
        for b in bn["banks"]:
            bank_line[b] = bn["line"]

    mappings, blocked_usages = {}, []
    for u in usages:
        b = u["palette_bank"]
        if only_bank is not None and b != only_bank:
            continue
        if b in placed_banks:
            continue                       # already mapped on another line (prior pass) — leave as-is
        if b not in bank_line:
            blocked_usages.append(u["usage_id"]); continue
        ln, cmap, im = bank_line[b], bank_colors[b], {}
        for si in u.get("used_indices", []):
            c = cmap.get(si)
            if c is None:
                continue
            idx = cram_index.get((ln, c))
            if idx is not None:
                im[str(si)] = idx
        if im:
            mappings[u["usage_id"]] = {"line": ln, "index_map": im}
    return {
        "scene": scene,
        "lines": {str(ln): line_pal.get(ln, [None] * 16) for ln in lines},
        "mappings": mappings,
        "blocked_banks": sorted(blocked_banks, key=lambda x: int(x, 16)),
        "blocked_usages": blocked_usages,
        "summary": {
            "banks_total": len(bank_cramset), "banks_placed": len(bank_line),
            "banks_blocked": len(blocked_banks), "banks_already_placed": len(placed_banks),
            "usages_total": len(usages), "usages_mapped": len(mappings),
            "usages_blocked": len(blocked_usages),
            "line_fill": {str(ln): sum(1 for x in line_pal.get(ln, []) if x) for ln in lines},
        },
    }


def reuse_line2_mapping(scene, skip_usages=(), only_bank=None):
    """Bulk-map Plane-A tiles onto Line 2's EXISTING arcade Layer-B colors (reuse, never author).
    Per usage: injective (MRD=0) min-cost ΔE assignment of its used arcade colors onto the populated
    Line-2 entries. Default: the scene's REMAINING banks (skip_usages' banks left as-is). With
    `only_bank` (a bank hex like "0x014"): remap ONLY that bank's usages, ignoring skip — used to MOVE
    one bank (e.g. the flame bank) from whatever line it is on to Line 2. A usage needing more distinct
    colors than Line 2 has populated is BLOCKED. No colors are created/changed — only line==2 mappings."""
    la = build_layera(scene)
    banks = la["banks"]
    usages = la["usages"]
    skip = set(skip_usages)
    placed_banks = set() if only_bank is not None else {u["palette_bank"] for u in usages if u["usage_id"] in skip}
    lb = _layer_b_display() or {}
    lb_cram = lb.get("cram") or []
    tgt = [(i, list(_cram_rgb(lb_cram[i]))) for i in range(1, 16)
           if i < len(lb_cram) and lb_cram[i] and lb_cram[i] != "0x0000"]
    mappings, blocked_usages, mapped_banks = {}, [], set()
    considered_banks = ({only_bank} if only_bank is not None
                        else {u["palette_bank"] for u in usages if u["palette_bank"] not in placed_banks})
    for u in usages:
        b = u["palette_bank"]
        if only_bank is not None and b != only_bank:
            continue
        if b in placed_banks:
            continue
        pal = banks.get(b, [[0, 0, 0]] * 16)
        counts = {}
        for v in tile_indices8(u["tile_code"]):
            if v:
                counts[v] = counts.get(v, 0) + 1
        srcs = [(si, pal[si] if si < len(pal) else [0, 0, 0], counts[si]) for si in sorted(counts)]
        if not srcs:
            continue
        if len(srcs) > len(tgt):
            blocked_usages.append(u["usage_id"]); continue
        n = len(tgt)
        cost = [[(srcs[r][2] * _de00(srcs[r][1], tgt[cc][1]) if r < len(srcs) else 0.0)
                 for cc in range(n)] for r in range(n)]
        assign = _hungarian(cost)
        mappings[u["usage_id"]] = {"line": 2, "index_map": {str(srcs[r][0]): tgt[assign[r]][0]
                                                            for r in range(len(srcs))}}
        mapped_banks.add(b)
    return {
        "scene": scene, "reuse_line2": True, "lines": {}, "mappings": mappings,
        "blocked_banks": [], "blocked_usages": blocked_usages,
        "summary": {
            "banks_total": len(considered_banks), "banks_placed": len(mapped_banks), "banks_blocked": 0,
            "banks_already_placed": len(placed_banks), "usages_total": len(usages),
            "usages_mapped": len(mappings), "usages_blocked": len(blocked_usages),
            "line_fill": {"2": len(tgt)},
        },
    }


def layera_solver_usages(ids, scene=None):
    """Build solve_group-shaped usage dicts for selected Layer-A logical usages (LA-NNNN).
    Each logical usage is its own palette domain; used_colors + pixel MRD come from the real tile pixels.
    PROMPT-ID-0009: LA-NNNN ids are scene-relative, so the SOURCE corpus must be the SAME scene the
    client is viewing — never the R1/P1 default for a subround scene."""
    la = build_layera(scene)
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


import re as _re
_SCENE_RE = _re.compile(r"PAL-R(\d)-S(\d)-")
def _normalize_usages(usages):
    """PROMPT-ID-0091: give every usage the human-oriented UI fields (view/authorable/scope/identity/round/
    sub-round/hardware) with safe defaults, without disturbing usages that already set them. This is the
    single place that distinguishes AUTHORING assets from RESEARCH/diagnostic objects and controllers."""
    for u in usages:
        oid = u.get("object_id") or ""
        sk = u.get("scene_key")
        if sk and (u.get("round") is None or not u.get("subround")):
            m = _SCENE_RE.search(sk)
            if m:
                u.setdefault("round", int(m.group(1)))
                u["subround"] = u.get("subround") or ("R%s-S%s" % (m.group(1), m.group(2)))
        is_controller = oid.startswith("controller:")
        is_research_producer = oid.startswith("usage:") and ":" in oid  # raw producer keys, not object:*
        u.setdefault("hardware_class", "controller" if is_controller else "PC090OJ sprite")
        if "view" not in u:
            u["view"] = "research" if (is_controller or is_research_producer) else "authoring"
        if "authorable" not in u:
            u["authorable"] = not (is_controller or u.get("hazard_pending") or u.get("incomplete"))
        u.setdefault("human_identity_status", "proven")
        u.setdefault("human_identity_label", u.get("display_name"))
        u.setdefault("mapping_scope", "scene" if sk else "shared")
        u.setdefault("group_label", None)
        u.setdefault("confidence", None)
    return usages


def _round_nav(usages):
    """Round -> Sub-Round navigation derived from the subround map + the scene-tagged usages, so the UI can
    present Round 1 -> {Sub-Round 1, Sub-Round 2, Sub-Round 3 / Boss} instead of a flat environment list."""
    smap = loadj(os.path.join(ROOT, "specs/palette_subround_map.json"), {"subrounds": []})
    nav = {}
    for sr in smap.get("subrounds", []):
        key = sr.get("key", "")
        m = _re.match(r"R(\d)-S(\d)", key)
        if not m:
            continue
        rnd = int(m.group(1))
        envs = [{"scene_key": e.get("scene_key"), "env": e.get("env"), "family": e.get("family")}
                for e in sr.get("environments", [])]
        boss = key in ("R1-S3",) or any("BOSS" in (e.get("scene_key") or "") for e in sr.get("environments", []))
        nav.setdefault(rnd, []).append({"subround": key, "label": key + (" / Boss" if boss else ""),
                                        "boss": boss, "environments": envs})
    return [{"round": r, "subrounds": nav[r]} for r in sorted(nav)]


def build_oracle():
    banks = sprite_bank_colors()
    plane = loadj(os.path.join(CORP, "plane_palette_banks.json"), {"banks": {}})
    contexts = loadj(os.path.join(ORACLE, "contexts.json"), {"contexts": [], "context_types": []})
    # RG-022/PROMPT-0006: register each subround PLANEA environment as a genuine, independent editing
    # context so Genesis Lines 0/1/3 can be authored per subround (context_policies[scene_key].tpl).
    # Parent = context:gameplay (a neutral node with no overrides) so scenes are independent siblings;
    # R1-S1 outdoor keeps the existing context:gameplay.r01.p01 (preserving approved work), and the
    # R1-S1 caves nest under it.
    ctx_ids = {c["id"] for c in contexts.get("contexts", [])}
    smap = loadj(os.path.join(ROOT, "specs/palette_subround_map.json"), {"subrounds": []})
    added = []
    for sr in smap.get("subrounds", []):
        for env in sr.get("environments", []):
            if env.get("family") != "PLANEA":
                continue
            sk = env["scene_key"]
            if sk == "PAL-R1-S1-PLANEA-OUTDOOR" or sk in ctx_ids:
                continue  # outdoor R1-S1 == existing r01.p01; don't duplicate
            parent = "context:gameplay.r01.p01" if sr["key"] == "R1-S1" else "context:gameplay"
            disp = f"{sr['key']} {env['env']} (Plane A)"
            added.append({"id": sk, "display": disp, "parent": parent, "type": "GAMEPLAY_SUBROUND",
                          "subround": sr["key"], "env": env["env"], "records": env.get("records"),
                          "native": sr["native"]})
    contexts["contexts"] = contexts.get("contexts", []) + added
    objects = loadj(os.path.join(ORACLE, "objects.json"), {"objects": []})
    coex = loadj(os.path.join(ORACLE, "coexistence.json"), {})
    usages = _normalize_usages(build_usages(banks))
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
            "round_nav": _round_nav(usages), "backdrop_invariant": BACKDROP_INVARIANT,
            "scene_group_order": ["Scene/ownership summary", "Layer A", "Layer B", "Player", "Player Weapons",
                                  "Scene Enemies", "Boss", "Hazards / Traps", "Rewards / Pickups",
                                  "Projectiles", "Effects / Deaths", "HUD / Truly Shared"],
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
    PROMPT-ID-0028: each piece may carry its OWN resolved 16-colour `pal` (per-piece arcade palette bank);
    pieces without one fall back to the shared `pal`, preserving single-bank behaviour."""
    if not pieces:
        return png(2, 2, [[30, 30, 38] * 2 for _ in range(2)])
    minx = min(p["x"] for p in pieces); miny = min(p["y"] for p in pieces)
    W = max(p["x"] for p in pieces) + 16 - minx + 2
    H = max(p["y"] for p in pieces) + 16 - miny + 2
    rows = [[30, 30, 38] * W for _ in range(H)]
    for p in sorted(pieces, key=lambda q: -q.get("rec", 0)):  # painter's: high rec first, low on top
        idx = cell_indices(p["code"])
        ppal = p.get("pal") or pal                            # per-piece palette, else shared
        ox = p["x"] - minx + 1; oy = p["y"] - miny + 1
        for y in range(16):
            sy = 15 - y if p["fy"] else y
            for x in range(16):
                sx = 15 - x if p["fx"] else x
                v = idx[sy * 16 + sx]
                if v:
                    c = ppal[v] if v < len(ppal) else [255, 0, 255]
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
            scene = (q.get("scene", [""])[0] or None)
            la = build_layera(scene)
            return self._s(200, json.dumps({
                "counts": la["counts"], "bank_ids": la["bank_ids"], "banks": la["banks"],
                "reserved_lines": RESERVED_LINES, "editable_lines": EDITABLE_LINES,
                "line_owners": scene_line_ownership(scene), "backdrop_invariant": BACKDROP_INVARIANT,
                "patterns": la["patterns"], "scene": scene}).encode())
        if u.path == "/api/layera_pattern":
            scene = (q.get("scene", [""])[0] or None)
            d = layera_pattern_detail(q.get("pid", [""])[0], scene)
            return self._s(200 if d else 404, json.dumps(d or {"error": "pattern not found"}).encode())
        if u.path == "/api/layera_map":
            try:
                scene = (q.get("scene", [""])[0] or None)
                seg = max(0, min(138, int(q.get("seg", ["0"])[0])))   # records 0-138 (castle/boss/R2)
                return self._s(200, json.dumps(layera_map(seg, scene)).encode())
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
                    # scene-aware bank palette: a subround scene's bank ids live in ITS corpus, not R1/P1,
                    # so without the scene they fall back to all-black (the "black Tile Library" bug).
                    scene = (q.get("scene", [""])[0] or None)
                    pal = build_layera(scene)["banks"].get(q.get("bank", ["0x003"])[0], [[0, 0, 0]] * 16)
                z = max(1, min(32, int(q.get("z", ["8"])[0])))
                return self._s(200, render_tile8(code, pal, z), "image/png")
            except Exception as e:
                return self._s(500, json.dumps({"error": str(e)}).encode())
        if u.path == "/api/profiles":
            return self._s(200, json.dumps(loadj(os.path.join(POLICY_DIR, "profile_manifest.json"), {"profiles": []})).encode())
        if u.path == "/api/subrounds":
            # RG-022: the 18-subround / per-environment palette model + authentic scene keys,
            # enriched with per-scene palette status from the canonical registry. Read-only.
            smap = loadj(os.path.join(ROOT, "specs/palette_subround_map.json"), {"subrounds": [], "families": {}})
            reg = loadj(os.path.join(ROOT, "specs/palette_decisions.json"), {"decisions": []})
            by_scene = {}
            for dec in reg.get("decisions", []):
                for sk in (dec.get("scene_applicability", {}) or {}).get("scene_keys", []):
                    by_scene.setdefault(sk, []).append({"id": dec["id"], "status": dec.get("status"),
                        "cross_scene_candidate": (dec.get("scene_applicability", {}) or {}).get("cross_scene_candidate", False)})
            def pstatus(sk):
                decs = by_scene.get(sk, [])
                if not decs:
                    return "missing", []
                st = {d["status"] for d in decs}
                if st <= {"approved", "proven", "decided"}:
                    return "approved", decs
                if st <= {"provisional", "unknown"}:
                    return "provisional", decs
                return "mixed", decs
            for sr in smap.get("subrounds", []):
                for env in sr.get("environments", []):
                    env["palette_status"], env["decisions"] = pstatus(env.get("scene_key"))
                    env["authorable"] = bool(smap.get("families", {}).get(env.get("family"), {}).get("authorable"))
            return self._s(200, json.dumps(smap).encode())
        if u.path == "/api/per_round_evidence":
            # PROMPT-ID-0006 Req 1: honest disclosure of the per-round arcade palette derivation so
            # the UI never claims a "verified" R2+ palette it could not capture. Read-only; the file
            # is produced by tools/graphics_editor/derive_per_round_palette.py.
            ev = loadj(os.path.join(ROOT, "analysis/graphics_optimizer/per_round_palette_evidence.json"),
                       {"status": "unavailable"})
            return self._s(200, json.dumps(ev).encode())
        if u.path == "/api/scene_sprite_coverage":
            # PROMPT-ID-0006 Req 4: honest per-scene sprite/enemy coverage so the Objects tab never
            # silently presents the R1/Phase-1 corpus as another scene's roster. Read-only; produced
            # by tools/graphics_editor/scene_sprite_coverage.py.
            cov = loadj(os.path.join(ROOT, "build/palette_export/scene_sprite_coverage.json"),
                        {"scenes": {}})
            sk = (q.get("scene", [""])[0] or None)
            if sk:
                return self._s(200, json.dumps(cov.get("scenes", {}).get(sk, {"coverage_status": "unknown"})).encode())
            return self._s(200, json.dumps(cov).encode())
        if u.path == "/api/policy":
            pid = q.get("p", ["baseline_current"])[0]
            pol = loadj(os.path.join(POLICY_DIR, pid + ".json"), default_profile(pid))
            return self._s(200, json.dumps(_backfill_policy(pol)).encode())
        if u.path == "/api/render":
            try:
                banks = sprite_bank_colors()
                # PROMPT-ID-0028: direct per-piece arcade render of a base/anim — EACH piece keeps its own
                # arcade palette bank (resolved from its `palette` nibble via the per-round line palette).
                # `round` selects the per-round palette (default R1). `target` (a 16-colour array) overrides
                # to a single mapped palette for all pieces (single-bank preview path).
                if "base" in q:
                    base = int(str(q["base"][0]), 16)
                    anim = int(str(q.get("anim", ["0"])[0]), 16)
                    rnd = int(q.get("round", ["1"])[0])
                    bnd = q.get("boundaries", ["0"])[0] == "1"
                    pieces = _manifest_vm_pieces(base, anim, 0)
                    if "target" in q:
                        return self._s(200, render_composite(pieces, json.loads(q["target"][0]), bnd), "image/png")
                    pieces = attach_arcade_piece_palettes(pieces, rnd)
                    return self._s(200, render_composite(pieces, [[0, 0, 0]] * 16, bnd), "image/png")
                uid = q.get("usage", [None])[0]
                usage = next((x for x in build_usages(banks) if x["usage_id"] == uid), None) if uid else None
                if usage is None:
                    return self._s(404, b'{"error":"usage not found"}')
                pal = [list(x) for x in banks.get(int(usage["sprite_bank"], 16), [[0, 0, 0]] * 16)]
                # Overlay the usage's OWN resolved arcade colors so the composite is never all-black when
                # its bank is absent from sprite_bank_colors() (e.g. reward/pickup banks 0x31/0x37): these
                # per-index arcade_rgb8 values are the authoritative colors the editor already shows.
                for c in usage.get("used_colors", []):
                    si = c.get("src_index")
                    if isinstance(si, int) and 0 <= si < len(pal) and c.get("arcade_rgb8"):
                        pal[si] = list(c["arcade_rgb8"])
                if "target" in q:
                    pal = json.loads(q["target"][0])
                bnd = q.get("boundaries", ["0"])[0] == "1"
                pieces = usage["pieces"]
                if q.get("mode", [""])[0] == "cells":  # CELL SHEET debug (grid)
                    pieces = [{"code": p["code"], "x": (i % 6) * 18, "y": (i // 6) * 18, "fx": False, "fy": False}
                              for i, p in enumerate(pieces)]
                # PROMPT-ID-0029: R1-S2 castle actors are (possibly) multi-bank — render EACH piece with its
                # own arcade palette (PROMPT-ID-0028). Authored Genesis mapping is PROMPT-ID-0030, so the
                # unmapped target preview also shows the per-piece arcade source.
                elif usage.get("round") is not None and any("palette" in p for p in pieces):
                    pp = attach_arcade_piece_palettes(pieces, usage["round"])
                    return self._s(200, render_composite(pp, [[0, 0, 0]] * 16, bnd), "image/png")
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
            # PROMPT-ID-0009: a scene-specific request MUST resolve to that scene's own corpus. An
            # unknown or corpus-less scene FAILS SAFE (never falls back to the R1/P1 corpus).
            scene = body.get("scene") or None
            if scene is not None:
                if not isinstance(scene, str) or not scene.startswith("PAL-"):
                    return self._s(400, json.dumps({"error": "invalid scene key: %r" % scene}).encode())
                if _scene_corpus_dir(scene) is None:
                    return self._s(404, json.dumps({"error": "no Layer-A corpus for scene %s — auto-map "
                                   "disabled for this scene (R1/P1 is NOT substituted)" % scene}).encode())
            return self._s(200, json.dumps(phase_layera_automap(line, tcs, scene)).encode())
        if u.path == "/api/scene_palette":
            # PROMPT-ID-0010: derive the whole scene's closest Genesis palette + per-usage mappings in
            # one pass. Same fail-safe scene rule as auto-map (unknown/corpus-less -> error, no R1/P1).
            scene = body.get("scene") or None
            if scene is not None:
                if not isinstance(scene, str) or not scene.startswith("PAL-"):
                    return self._s(400, json.dumps({"error": "invalid scene key: %r" % scene}).encode())
                if _scene_corpus_dir(scene) is None:
                    return self._s(404, json.dumps({"error": "no Layer-A corpus for scene %s — derive "
                                   "disabled for this scene (R1/P1 is NOT substituted)" % scene}).encode())
            req_lines = [int(x) for x in (body.get("lines") or [0, 1, 3])]
            skip = body.get("skip_usages") or []
            only_bank = body.get("only_bank") or None   # remap ONLY this bank (move it to the line)
            # Line 2 request = REUSE mode: map banks onto existing Layer-B colors (never author).
            if req_lines == [2]:
                return self._s(200, json.dumps(reuse_line2_mapping(scene, skip, only_bank)).encode())
            lines = [x for x in req_lines if x not in RESERVED_LINES and x in (0, 1, 3)]
            if not lines:
                return self._s(400, json.dumps({"error": "no editable target lines (0/1/3)"}).encode())
            return self._s(200, json.dumps(derive_scene_palette(scene, tuple(lines), skip, only_bank)).encode())
        if u.path == "/api/solve":
            idlist = body.get("usage_ids", [])
            ids = set(idlist)
            plane_ids = [i for i in idlist if i.startswith("LA-")]
            scene = body.get("scene") or None                 # LA source corpus scene (PROMPT-ID-0009)
            if scene is not None and (not isinstance(scene, str) or not scene.startswith("PAL-")):
                return self._s(400, json.dumps({"error": "invalid scene key: %r" % scene}).encode())
            us = [x for x in build_usages(sprite_bank_colors()) if x["usage_id"] in ids]
            us += layera_solver_usages(plane_ids, scene)   # Layer-A logical usages participate too
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
            # LINE-2 PROTECTION (server-authoritative): a mapping may REUSE an existing arcade Layer-B
            # color (reference an occupied Line-2 index) but may NEVER author/overwrite a Line-2 color.
            # So reserved-line mappings are allowed only when every target index is a populated Layer-B
            # entry; the Line-2 colors themselves are still forced empty (never serialized over Layer B).
            lb = _layer_b_display() or {}
            lb_cram = lb.get("cram") or []
            l2_pop = {i for i in range(1, 16) if i < len(lb_cram) and lb_cram[i] and lb_cram[i] != "0x0000"}
            def _bad_reuse(mp):
                if not mp or mp.get("line") not in RESERVED_LINES:
                    return None
                tgts = [int(v) for v in (mp.get("index_map") or {}).values()]
                bad = [t for t in tgts if t not in l2_pop]
                return (sorted(set(bad)) or ["(none)"]) if (bad or not tgts) else None
            for coll in ("usage_palette_mappings", "plane_usage_palette_mappings"):
                for k, mp in (body.get(coll) or {}).items():
                    bad = _bad_reuse(mp)
                    if bad is not None:
                        return self._s(403, json.dumps({"error": "LINE 2 (Layer B) is read-only: mapping %s may only "
                                        "REUSE existing Layer-B colors (indices %s), not target empty/created indices %s"
                                        % (k, sorted(l2_pop), bad)}).encode())
            tpl = body.get("target_palette_lines")
            if isinstance(tpl, list):
                for ln in RESERVED_LINES:
                    if ln < len(tpl):
                        tpl[ln] = [None] * 16      # Line 2 is never editable/serialized as a replacement palette
            # context overrides may never AUTHOR a reserved line; context mappings may REUSE it.
            for cid, cp in (body.get("context_policies") or {}).items():
                for ln in list((cp.get("tpl") or {}).keys()):
                    if int(ln) in RESERVED_LINES:
                        return self._s(403, json.dumps({"error": "LINE 2 is protected; context %s may not override a "
                                        "reserved line" % cid}).encode())
                for k, mp in (cp.get("plane_usage_palette_mappings") or {}).items():
                    bad = _bad_reuse(mp)
                    if bad is not None:
                        return self._s(403, json.dumps({"error": "LINE 2 (Layer B) is read-only: context %s plane mapping "
                                        "%s may only REUSE existing Layer-B colors, not target empty indices %s"
                                        % (cid, k, bad)}).encode())
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
    pol["line2_display"] = _layer_b_display()      # read-only arcade Layer-B colors for Line 2 display
    return pol


_LB_DISPLAY = None
def _layer_b_display():
    """Read-only arcade Layer-B (Line 2) colors for DISPLAY only (the profile stores Line 2 as null because
    it is arcade-runtime/time-of-day). Captured arcade palette RAM 0x200000 bank 0x001 via
    tools/mame/scripts/arcade_layera_palette_dump.lua. Returns {cram:[16], animated_indices:[...]} or None."""
    global _LB_DISPLAY
    if _LB_DISPLAY is None:
        d = loadj(os.path.join(CORP, "layer_b_display_palette.json"), None)
        _LB_DISPLAY = ({"cram": d.get("cram"), "rgb8": d.get("rgb8"),
                        "animated_indices": d.get("animated_indices", []),
                        "frames": d.get("frames"), "cram_by_frame": d.get("cram_by_frame")}
                       if d and d.get("cram") else False)
    return _LB_DISPLAY or None


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
