#!/usr/bin/env python3
"""Generate the offline Palette Composer R1/P1 sprite (PC090OJ) reindexed region (TOOLING, build stage).

Produces build/regions/pc090oj_editor.bin: the preconverted Genesis PC090OJ pattern region (4096 cells of
128 bytes) in which every resolved R1/P1 sprite tile code has its pixel nibbles reindexed per the frozen
Test profile's authored per-usage index_map, so each sprite renders correctly against its authored shared
Genesis line. Index 0 stays transparent. All other codes are byte-identical.

Build 0381 — COMPLETE (code,bank) VARIANT PIPELINE
--------------------------------------------------
The COMPLETE R1/P1 semantic corpus is consumed (analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv
for enemies + h24_player_weapon_cells.tsv for the four equipped weapons + the complete H24 player-body cell
set for Rastan + the cave_block usage). Across the complete corpus a small set of PC090OJ codes are shared by
DIFFERENT enemies under DIFFERENT effective palette banks whose authored index_maps produce DIFFERENT
transformed bytes. A flat code->one-cell model cannot represent those. This generator therefore:

  * bakes ONE base cell per code at code*128 (base bank chosen below), and
  * APPENDS a distinct 128-byte variant cell for every divergent (code, effective_bank) whose transform
    differs from the base, and
  * emits a compact, O(1) runtime-consumable variant index (pc090oj_sprite_variants.inc) describing the
    contiguous divergent code block and the effective_bank -> variant-slot table, plus a machine-readable
    JSON index.

Divergent (code,bank) entries are NEVER collapsed and NEVER dominant-overwritten. Identical transforms are
deduplicated (base only). The base region for every non-divergent code is byte-identical to the code-indexed
Build-0380 output, so accepted-Rastan and every other sprite are preserved exactly.

The frame-69 weapon-table decode artefact (a slot-69 overrun that aliases player-body/enemy codes; HAMMER's
frame 69 is three copies of the blank code 0x0003) is excluded from the weapon corpus mechanically.
"""
import argparse, csv, hashlib, json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CELL = 128
TILE_MAX = 0x1000                 # 4096 PC090OJ codes
WEAPON_ARTIFACT_FRAME = 69        # spurious weapon-table decode overrun; excluded (see module docstring)

# effective palette bank per usage base name (the arcade sprite colbank the runtime resolves at emit time)
USAGE_BANK = {"rastan": 0x33, "lizardman": 0x36, "valkyrie": 0x32, "chimera": 0x34,
              "flying_demon": 0x35, "small_bat": 0x3E, "large_bat": 0x3E, "four_armed_insect": 0x3A,
              "cave_block": 0x3C,
              "weapon.sword": 0x33, "weapon.axe": 0x33, "weapon.hammer": 0x33, "weapon.fire_sword": 0x33}

# authored profile usage-mapping key per usage base name
USAGE_UID = {"rastan": "object:player.rastan",
             "lizardman": "usage:lizardman:bank0x36", "valkyrie": "usage:valkyrie:bank0x32",
             "chimera": "usage:chimera:bank0x34", "flying_demon": "usage:flying_demon:bank0x35",
             "four_armed_insect": "usage:four_armed_insect:bank0x3A",
             "small_bat": "usage:small_bat:bank0x3E", "large_bat": "usage:large_bat:bank0x3E",
             "cave_block": "usage:cave_block:bank0x3C",
             "weapon.sword": "object:weapon.sword", "weapon.axe": "object:weapon.axe",
             "weapon.hammer": "object:weapon.hammer", "weapon.fire_sword": "object:weapon.fire_sword"}

ENEMY_OBJECTS = ("lizardman", "valkyrie", "chimera", "flying_demon",
                 "four_armed_insect", "small_bat", "large_bat")
WEAPON_NAME_TO_BASE = {"SWORD": "weapon.sword", "AXE": "weapon.axe",
                       "HAMMER": "weapon.hammer", "FIRE SWORD": "weapon.fire_sword"}

# For the divergent enemy anim block, the base cell (baked in place at code*128) is lizardman (bank 0x36 =
# Round-1 enemy, the common case that then needs no runtime variant path); the other two banks are variants.
DIVERGENT_BASE_BANK = 0x36
DIVERGENT_VARIANT_BANKS = (0x34, 0x3A)   # chimera, four_armed_insect


def _imap(profile, uid):
    m = profile["usage_palette_mappings"].get(uid) or {}
    return {int(a): int(b) for a, b in (m.get("index_map") or {}).items()}, m.get("line")


def transform(raw, code, imap):
    """Return the 128-byte reindexed cell for `code` under `imap` (index 0 stays transparent)."""
    s = code * CELL
    out = bytearray(raw[s:s + CELL])
    for i, b in enumerate(out):
        hi = (b >> 4) & 0xF
        lo = b & 0xF
        hi = imap.get(hi, hi) if hi else 0
        lo = imap.get(lo, lo) if lo else 0
        out[i] = (hi << 4) | lo
    return bytes(out)


def _h24_player_cells():
    """Complete H24 player-body cell-code set (torso 0x5BD40 + legs 0x5C466). Codes outside the tile range
    are excluded (decode artefacts / non-player). Same evidence the Palette Composer consumes."""
    codes = set()
    for fn in ("h24_player_frame_cells.tsv", "h24_player_leg_cells.tsv"):
        p = os.path.join(ROOT, "analysis/actor_decompilation", fn)
        if not os.path.exists(p):
            raise SystemExit("missing authoritative H24 player cell evidence: %s" % p)
        for r in csv.DictReader(open(p), delimiter="\t"):
            for c in (r.get("cells") or "").split(";"):
                c = c.strip()
                if c:
                    v = int(c, 16) & 0x1FFF
                    if v < TILE_MAX:
                        codes.add(v)
    if not codes:
        raise SystemExit("H24 player cell evidence produced no codes")
    return codes


def _weapon_cells():
    """{usagebase: set(codes)} for the four equipped weapons from the H24 weapon-cell corpus, EXCLUDING the
    spurious frame-69 decode artefact and invalid codes."""
    out = {b: set() for b in WEAPON_NAME_TO_BASE.values()}
    p = os.path.join(ROOT, "analysis/actor_decompilation/h24_player_weapon_cells.tsv")
    for r in csv.DictReader(open(p), delimiter="\t"):
        if (r.get("valid_code") or "").strip() != "Y":
            continue
        if int(r["frame_index"]) == WEAPON_ARTIFACT_FRAME:
            continue
        code = int(r["cell_code"], 16) & 0xFFF
        if code >= TILE_MAX:
            continue
        base = WEAPON_NAME_TO_BASE.get(r["name"].strip())
        if base:
            out[base].add(code)
    return out


def _enemy_cells(corpus_tsv):
    """{usagebase: set(codes)} for the complete R1/P1 enemy corpus (valid cells only)."""
    out = {o: set() for o in ENEMY_OBJECTS}
    for r in csv.DictReader(open(corpus_tsv), delimiter="\t"):
        if (r.get("valid") or "").strip() != "Y":
            continue
        obj = r["object"].strip()
        if obj not in out:
            continue
        code = int(r["cell_code"], 16) & 0xFFF
        if code < TILE_MAX:
            out[obj].add(code)
    return out


def resolve(profile, corpus_tsv):
    """Resolve the complete (code,bank) requirement set into a base map per code plus divergent variants.

    Returns dict with:
      base[code]      = (usagebase, uid, bank, line, imap)      -- baked at code*128
      variants        = [ {vi, code, usagebase, uid, bank, line, imap} ]  -- appended cells (vi = 0..n-1)
      bank_slot[bank] = variant-slot base for the divergent block (byte, 0xFF = base/no variant)
      block_lo/block_hi = the single contiguous divergent code block
    """
    code_sets = {"rastan": _h24_player_cells()}
    code_sets.update(_weapon_cells())
    code_sets.update(_enemy_cells(corpus_tsv))
    code_sets["cave_block"] = set(range(0x0179, 0x017D))

    # per-(code,bank) authored map, and per-code set of banks
    cb_map = {}          # (code,bank) -> (usagebase, uid, line, imap)
    code_banks = {}      # code -> set(bank)
    for usagebase, cset in code_sets.items():
        uid = USAGE_UID[usagebase]
        imap, line = _imap(profile, uid)
        if not imap:
            raise SystemExit(f"no non-empty authored map for {usagebase} ({uid})")
        bank = USAGE_BANK[usagebase]
        for code in cset:
            key = (code, bank)
            if key in cb_map and cb_map[key][3] != imap:
                raise SystemExit(f"UNRESOLVABLE same-(code,bank) conflict at {hex(code)} bank {hex(bank)}: "
                                 f"{cb_map[key][1]} vs {uid} (different maps, identical runtime identity)")
            cb_map[key] = (usagebase, uid, line, imap)
            code_banks.setdefault(code, set()).add(bank)

    raw = None  # transforms computed by caller; here we only need identity of divergent bytes -> caller passes raw
    return cb_map, code_banks


def build_layout(profile, raw, corpus_tsv):
    """Compute the base map and appended variant list from the resolved requirement set + raw pixels."""
    cb_map, code_banks = resolve(profile, corpus_tsv)

    divergent = sorted(c for c, banks in code_banks.items() if len(banks) > 1)
    # Verify divergent codes are exactly one contiguous block under the expected banks (else fail loudly:
    # the compact runtime index assumes a single contiguous block).
    if divergent:
        lo, hi = divergent[0], divergent[-1]
        if divergent != list(range(lo, hi + 1)):
            raise SystemExit(f"divergent codes are not contiguous: {[hex(c) for c in divergent]}")
        expect = {DIVERGENT_BASE_BANK, *DIVERGENT_VARIANT_BANKS}
        for c in divergent:
            if not code_banks[c].issubset(expect) or DIVERGENT_BASE_BANK not in code_banks[c]:
                raise SystemExit(f"divergent code {hex(c)} banks {sorted(code_banks[c])} outside expected "
                                 f"{sorted(expect)} (base {hex(DIVERGENT_BASE_BANK)} required)")
    else:
        lo, hi = 0, -1

    # base map: one owner per code; for divergent block, base = DIVERGENT_BASE_BANK owner.
    base = {}
    for code, banks in code_banks.items():
        bank = DIVERGENT_BASE_BANK if len(banks) > 1 else next(iter(banks))
        usagebase, uid, line, imap = cb_map[(code, bank)]
        base[code] = (usagebase, uid, bank, line, imap)

    # variants: for each divergent code, one appended cell per non-base bank whose transform differs from base.
    variants = []
    bank_slot = {}   # bank -> slot base (index into variant region)
    slot = 0
    for vb in DIVERGENT_VARIANT_BANKS:
        bank_slot[vb] = slot
        for code in range(lo, hi + 1):
            if vb not in code_banks.get(code, set()):
                raise SystemExit(f"divergent code {hex(code)} missing expected bank {hex(vb)}")
            usagebase, uid, line, imap = cb_map[(code, vb)]
            base_bytes = transform(raw, code, base[code][4])
            var_bytes = transform(raw, code, imap)
            if var_bytes == base_bytes:
                # identical transform: dedup -> point at base (no appended cell); still record for the index.
                variants.append({"vi": None, "code": code, "usagebase": usagebase, "uid": uid,
                                 "bank": vb, "line": line, "imap": imap, "dedup": True})
                continue
            variants.append({"vi": slot + (code - lo), "code": code, "usagebase": usagebase, "uid": uid,
                             "bank": vb, "line": line, "imap": imap, "dedup": False})
        slot += (hi - lo + 1)
    return base, variants, bank_slot, (lo, hi), cb_map, code_banks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.join(ROOT, "build/rastan-direct/build0381/Test.snapshot.json"))
    ap.add_argument("--corpus", default=os.path.join(ROOT, "analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv"))
    ap.add_argument("--pc090oj", default=os.path.join(ROOT, "build/pc090oj_genesis.bin"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build/regions/pc090oj_editor.bin"))
    ap.add_argument("--manifest", default=os.path.join(ROOT, "build/regions/pc090oj_editor_manifest.json"))
    ap.add_argument("--variants-inc", default=os.path.join(ROOT, "apps/rastan-direct/out/pc090oj_sprite_variants.inc"))
    ap.add_argument("--variants-index", default=os.path.join(ROOT, "build/regions/pc090oj_variant_index.json"))
    a = ap.parse_args()

    profile_bytes = open(a.profile, "rb").read()
    profile = json.loads(profile_bytes)
    profile_sha = hashlib.sha256(profile_bytes).hexdigest()
    raw = bytearray(open(a.pc090oj, "rb").read())
    ncodes = len(raw) // CELL

    base, variants, bank_slot, (lo, hi), cb_map, code_banks = build_layout(profile, raw, a.corpus)

    # ---- bake base region in place ----
    out = bytearray(raw)
    manifest = {"profile_sha256": profile_sha, "source": os.path.relpath(a.pc090oj, ROOT),
                "cell_model": {"offset": "code*128", "size_bytes": CELL, "subtiles": 4},
                "base_reindexed_codes": 0, "variant_cells": 0, "entries": []}
    for code, (usagebase, uid, bank, line, imap) in sorted(base.items()):
        s = code * CELL
        if s + CELL > len(out):
            raise SystemExit(f"code {hex(code)} out of region range")
        out[s:s + CELL] = transform(raw, code, imap)
    manifest["base_reindexed_codes"] = len(base)

    # ---- append variant cells (only non-dedup, in vi order) ----
    real_variants = sorted((v for v in variants if not v["dedup"]), key=lambda v: v["vi"])
    n_variant_cells = (len(real_variants) and (max(v["vi"] for v in real_variants) + 1)) or 0
    variant_region = bytearray(n_variant_cells * CELL)
    for v in real_variants:
        cell = transform(raw, v["code"], v["imap"])
        variant_region[v["vi"] * CELL:(v["vi"] + 1) * CELL] = cell
        manifest["entries"].append({
            "kind": "variant", "vi": v["vi"], "region_cell": ncodes + v["vi"],
            "code": v["code"], "bank": "0x%02X" % v["bank"], "usage": v["uid"], "line": v["line"],
            "cell_sha256": hashlib.sha256(cell).hexdigest()})
    out += variant_region
    manifest["variant_cells"] = n_variant_cells
    manifest["divergent_block"] = {"lo": "0x%03X" % lo, "hi": "0x%03X" % hi,
                                   "base_bank": "0x%02X" % DIVERGENT_BASE_BANK,
                                   "variant_banks": ["0x%02X" % b for b in DIVERGENT_VARIANT_BANKS]}
    manifest["region_cells_total"] = ncodes + n_variant_cells

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "wb").write(bytes(out))
    json.dump(manifest, open(a.manifest, "w"), indent=1)

    # ---- runtime-consumable O(1) variant index (.inc) ----
    #   residency variant key = SPRITE_VARIANT_KEY_MARK | vi  (bit13 marker; bit15 hud stays clear)
    #   normalized reverse key = SPRITE_VARIANT_KEY_NORM + vi (a free 512-directory range, no resize)
    #   variant DMA source cell = SPRITE_VARIANT_REGION_CELL + vi
    #   pc090oj_variant_bank_slot[effective_bank & 0x7f] = slot base (0xFF = base cell / no variant)
    bs = [0xFF] * 128
    for bnk, sl in bank_slot.items():
        bs[bnk & 0x7F] = sl
    lines = []
    lines.append("/* GENERATED by tools/graphics_editor/gen_reindexed_pc090oj.py -- do not hand-edit. */")
    lines.append("/* Build 0381 complete (code,bank) sprite variant index. profile_sha256=%s */" % profile_sha)
    lines.append(".equ SPRITE_VARIANT_LO, 0x%04X" % lo)
    lines.append(".equ SPRITE_VARIANT_HI, 0x%04X" % hi)
    lines.append(".equ SPRITE_VARIANT_SPAN, 0x%04X" % (hi - lo if hi >= lo else 0))
    lines.append(".equ SPRITE_VARIANT_REGION_CELL, %d" % ncodes)
    lines.append(".equ SPRITE_VARIANT_REGION_OFF, %d   /* ncodes*128 bytes */" % (ncodes * CELL))
    lines.append(".equ SPRITE_VARIANT_KEY_MARK, 0x2000")
    lines.append(".equ SPRITE_VARIANT_KEY_NORM, 0x1080")
    lines.append(".equ SPRITE_VARIANT_CELLS, %d" % n_variant_cells)
    lines.append("    .section .rodata")
    lines.append("    .align 2")
    lines.append("    .global pc090oj_variant_bank_slot")
    lines.append("pc090oj_variant_bank_slot:")
    for i in range(0, 128, 16):
        lines.append("    .byte " + ", ".join("0x%02X" % b for b in bs[i:i + 16]))
    lines.append("    .section .text,\"ax\"")
    os.makedirs(os.path.dirname(a.variants_inc), exist_ok=True)
    open(a.variants_inc, "w").write("\n".join(lines) + "\n")

    # machine-readable index (dedup entries recorded too)
    idx = {"profile_sha256": profile_sha, "block": {"lo": lo, "hi": hi},
           "base_bank": DIVERGENT_BASE_BANK, "variant_banks": list(DIVERGENT_VARIANT_BANKS),
           "region_cell_base": ncodes, "bank_slot": {("0x%02X" % b): s for b, s in bank_slot.items()},
           "variants": [{"code": v["code"], "bank": "0x%02X" % v["bank"], "vi": v["vi"],
                         "region_cell": (ncodes + v["vi"]) if v["vi"] is not None else None,
                         "dedup": v["dedup"]} for v in variants]}
    json.dump(idx, open(a.variants_index, "w"), indent=1)

    asset_sha = hashlib.sha256(bytes(out)).hexdigest()
    print("pc090oj_editor.bin: base %d codes, %d variant cells (block 0x%03X..0x%03X); "
          "region %d cells; profile_sha=%s asset_sha=%s"
          % (len(base), n_variant_cells, lo, hi, ncodes + n_variant_cells, profile_sha[:16], asset_sha[:16]))


if __name__ == "__main__":
    main()
