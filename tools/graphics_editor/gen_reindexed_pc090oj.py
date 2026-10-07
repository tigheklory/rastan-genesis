#!/usr/bin/env python3
"""Generate the offline Palette Composer R1/P1 sprite (PC090OJ) reindexed region (TOOLING, build stage).

Produces build/regions/pc090oj_editor.bin: the preconverted Genesis PC090OJ pattern region (4096 cells of
128 bytes) in which every resolved R1/P1 sprite tile code has its pixel nibbles reindexed per the frozen
Test profile's authored per-usage index_map, so each sprite renders correctly against its authored shared
Genesis line. Index 0 stays transparent. All other codes are byte-identical.

COMPLETE (code,bank) VARIANT PIPELINE
-------------------------------------
The COMPLETE R1/P1 semantic corpus is consumed: enemies (r1p1_enemy_semantic_corpus.tsv), the four equipped
weapons (h24_player_weapon_cells.tsv, frame-69 decode artefact excluded), the complete H24 player-body cell
set (Rastan), the destroyable cave block (usage:cave_block:bank0x3C), and the burst/impact effect
(usage:burst:bank0x30, cells derived from the compositor VM = the same decompilation source the Palette
Composer uses). Across the complete corpus some PC090OJ codes are shared by DIFFERENT semantic objects under
DIFFERENT effective palette banks whose authored index_maps produce DIFFERENT transformed bytes; a flat
code->one-cell model cannot represent those.

This generator therefore bakes ONE base cell per code at code*128 (base bank chosen by BASE_PRIORITY), and
APPENDS a distinct 128-byte variant cell for every divergent (code, effective_bank), grouped by code. It
emits a compact, O(1) runtime-consumable index (pc090oj_sprite_variants.inc):
  * pc090oj_variant_group_base[code] (u16, 0xFFFF = not divergent) -> the appended-region cell base for the
    code's variant group;
  * pc090oj_variant_bank_slot[effective_bank] (byte, 0xFF = base / no variant) -> the ordinal of that bank
    within any group; and the runtime selects vi = group_base[code] + bank_slot[bank].
This generalizes the earlier single-contiguous-block selector to ANY number of divergent code blocks (e.g.
0xA73..0xAA2 chimera/lizardman/four_armed AND 0x28E..0x2A8 flying_demon/burst) with no new mechanism.

Divergent (code,bank) entries are NEVER collapsed and NEVER dominant-overwritten. Base cells for every
non-divergent code (all Rastan, all weapons, most enemies) are byte-identical to the code-indexed model.
"""
import argparse, csv, hashlib, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CELL = 128
TILE_MAX = 0x1000
WEAPON_ARTIFACT_FRAME = 69

USAGE_BANK = {"rastan": 0x33, "lizardman": 0x36, "valkyrie": 0x32, "chimera": 0x34,
              "flying_demon": 0x35, "small_bat": 0x3E, "large_bat": 0x3E, "four_armed_insect": 0x3A,
              "cave_block": 0x3C, "burst": 0x30,
              "weapon.sword": 0x33, "weapon.axe": 0x33, "weapon.hammer": 0x33, "weapon.fire_sword": 0x33}

USAGE_UID = {"rastan": "object:player.rastan",
             "lizardman": "usage:lizardman:bank0x36", "valkyrie": "usage:valkyrie:bank0x32",
             "chimera": "usage:chimera:bank0x34", "flying_demon": "usage:flying_demon:bank0x35",
             "four_armed_insect": "usage:four_armed_insect:bank0x3A",
             "small_bat": "usage:small_bat:bank0x3E", "large_bat": "usage:large_bat:bank0x3E",
             "cave_block": "usage:cave_block:bank0x3C", "burst": "usage:burst:bank0x30",
             "weapon.sword": "object:weapon.sword", "weapon.axe": "object:weapon.axe",
             "weapon.hammer": "object:weapon.hammer", "weapon.fire_sword": "object:weapon.fire_sword"}

ENEMY_OBJECTS = ("lizardman", "valkyrie", "chimera", "flying_demon",
                 "four_armed_insect", "small_bat", "large_bat")
WEAPON_NAME_TO_BASE = {"SWORD": "weapon.sword", "AXE": "weapon.axe",
                       "HAMMER": "weapon.hammer", "FIRE SWORD": "weapon.fire_sword"}

# Base-bank priority for a divergent code (the bank baked in place at code*128). Enemies/rastan/cave rank
# above the burst effect (0x30), so a primary object always owns the base cell and the burst is a variant;
# lizardman(0x36) owns the shared 0xA73 anim block and flying_demon(0x35) owns the shared 0x28E burst block.
BASE_PRIORITY = [0x36, 0x35, 0x32, 0x3E, 0x34, 0x3A, 0x33, 0x3C, 0x30]

# Burst effect (H16): base actor 0x0275, three proven compositor programs; cells derived from the compositor
# VM (same decompilation source the Palette Composer consumes), NOT a hand-added raw code list.
BURST_BASE = 0x0275
BURST_ANIMS = (0x9E, 0x9F, 0xA0)


def _imap(profile, uid):
    m = profile["usage_palette_mappings"].get(uid) or {}
    return {int(a): int(b) for a, b in (m.get("index_map") or {}).items()}, m.get("line")


def transform(raw, code, imap):
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
    out = {b: set() for b in WEAPON_NAME_TO_BASE.values()}
    p = os.path.join(ROOT, "analysis/actor_decompilation/h24_player_weapon_cells.tsv")
    for r in csv.DictReader(open(p), delimiter="\t"):
        if (r.get("valid_code") or "").strip() != "Y":
            continue
        if int(r["frame_index"]) == WEAPON_ARTIFACT_FRAME:
            continue
        code = int(r["cell_code"], 16) & 0xFFF
        if code < TILE_MAX:
            base = WEAPON_NAME_TO_BASE.get(r["name"].strip())
            if base:
                out[base].add(code)
    return out


def _enemy_cells(corpus_tsv):
    out = {o: set() for o in ENEMY_OBJECTS}
    for r in csv.DictReader(open(corpus_tsv), delimiter="\t"):
        if (r.get("valid") or "").strip() != "Y":
            continue
        obj = r["object"].strip()
        if obj in out:
            code = int(r["cell_code"], 16) & 0xFFF
            if code < TILE_MAX:
                out[obj].add(code)
    return out


def _burst_cells():
    """Burst PC090OJ cell codes across the three proven forms, via the compositor VM (decompilation source)."""
    p = os.path.join(ROOT, "tools/graphics_optimizer")
    if p not in sys.path:
        sys.path.insert(0, p)
    from compositor_vm import ActorRenderState, visible_pieces
    codes = set()
    for anim in BURST_ANIMS:
        for pc in visible_pieces(ActorRenderState(BURST_BASE, anim, 0)):
            c = pc.tile & 0x1FFF
            if c < TILE_MAX:
                codes.add(c)
    if not codes:
        raise SystemExit("burst compositor VM produced no cells")
    return codes


def resolve(profile, corpus_tsv):
    """Resolve the complete (code,bank) requirement set. Returns (cb_map, code_banks)."""
    code_sets = {"rastan": _h24_player_cells()}
    code_sets.update(_weapon_cells())
    code_sets.update(_enemy_cells(corpus_tsv))
    code_sets["cave_block"] = set(range(0x0179, 0x017D))     # proven 2x2 composite (== compositor VM)
    code_sets["burst"] = _burst_cells()

    cb_map = {}
    code_banks = {}
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
    return cb_map, code_banks


def build_layout(profile, raw, corpus_tsv):
    """Compute the base map + appended variant list + the O(1) runtime index tables.

    Returns: base[code]=(usagebase,uid,bank,line,imap); variants=[{vi,code,uid,bank,line,imap}];
             var_ordinal{bank->ordinal}; group_base{code->cell-base}; n_variant_cells; cb_map; code_banks.
    Generalizes to ANY number of divergent code blocks."""
    cb_map, code_banks = resolve(profile, corpus_tsv)
    divergent = sorted(c for c, banks in code_banks.items() if len(banks) > 1)

    def base_bank_of(banks):
        for b in BASE_PRIORITY:
            if b in banks:
                return b
        return min(banks)

    # Consistent global ordinal per variant bank (position within its group's sorted variant set).
    var_ordinal = {}
    for c in divergent:
        vbanks = sorted(code_banks[c] - {base_bank_of(code_banks[c])})
        for i, b in enumerate(vbanks):
            if b in var_ordinal and var_ordinal[b] != i:
                raise SystemExit(f"variant bank {hex(b)} ordinal conflict ({var_ordinal[b]} vs {i}); the "
                                 f"compact group index requires each variant bank at a consistent ordinal")
            var_ordinal[b] = i

    base = {}
    for code, banks in code_banks.items():
        bank = base_bank_of(banks) if len(banks) > 1 else next(iter(banks))
        usagebase, uid, line, imap = cb_map[(code, bank)]
        base[code] = (usagebase, uid, bank, line, imap)

    variants = []
    group_base = {}
    cursor = 0
    for c in divergent:
        banks = code_banks[c]
        vbanks = sorted(banks - {base_bank_of(banks)})
        group_base[c] = cursor
        base_bytes = transform(raw, c, base[c][4])
        for b in vbanks:
            usagebase, uid, line, imap = cb_map[(c, b)]
            if transform(raw, c, imap) == base_bytes:
                raise SystemExit(f"divergent variant {hex(c)} bank {hex(b)} transforms identical to base; the "
                                 f"compact per-bank ordinal scheme assumes every listed variant differs")
            variants.append({"vi": cursor + var_ordinal[b], "code": c, "usagebase": usagebase, "uid": uid,
                             "bank": b, "line": line, "imap": imap})
        cursor += (max(var_ordinal[b] for b in vbanks) + 1)
    return base, variants, var_ordinal, group_base, cursor, cb_map, code_banks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.join(ROOT, "build/rastan-direct/build0384/Test.snapshot.json"))
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

    base, variants, var_ordinal, group_base, n_variant_cells, cb_map, code_banks = build_layout(profile, raw, a.corpus)

    out = bytearray(raw)
    manifest = {"profile_sha256": profile_sha, "source": os.path.relpath(a.pc090oj, ROOT),
                "cell_model": {"offset": "code*128", "size_bytes": CELL, "subtiles": 4},
                "base_reindexed_codes": 0, "variant_cells": 0, "divergent_blocks": [], "entries": []}
    for code, (usagebase, uid, bank, line, imap) in sorted(base.items()):
        s = code * CELL
        if s + CELL > len(out):
            raise SystemExit(f"code {hex(code)} out of region range")
        out[s:s + CELL] = transform(raw, code, imap)
    manifest["base_reindexed_codes"] = len(base)

    variant_region = bytearray(n_variant_cells * CELL)
    for v in sorted(variants, key=lambda v: v["vi"]):
        cell = transform(raw, v["code"], v["imap"])
        variant_region[v["vi"] * CELL:(v["vi"] + 1) * CELL] = cell
        manifest["entries"].append({"kind": "variant", "vi": v["vi"], "region_cell": ncodes + v["vi"],
                                    "code": v["code"], "bank": "0x%02X" % v["bank"], "usage": v["uid"],
                                    "line": v["line"], "cell_sha256": hashlib.sha256(cell).hexdigest()})
    out += variant_region
    manifest["variant_cells"] = n_variant_cells
    manifest["region_cells_total"] = ncodes + n_variant_cells
    # summarize divergent blocks (contiguous runs) for the report
    div = sorted(group_base)
    if div:
        runs = [[div[0], div[0]]]
        for c in div[1:]:
            if c == runs[-1][1] + 1:
                runs[-1][1] = c
            else:
                runs.append([c, c])
        for lo, hi in runs:
            manifest["divergent_blocks"].append({"lo": "0x%03X" % lo, "hi": "0x%03X" % hi,
                                                 "base_bank": "0x%02X" % base[lo][2],
                                                 "banks": ["0x%02X" % b for b in sorted(code_banks[lo])]})

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "wb").write(bytes(out))
    json.dump(manifest, open(a.manifest, "w"), indent=1)

    # ---- runtime O(1) variant index (.inc) ----
    grp = [0xFFFF] * TILE_MAX
    for c, gb in group_base.items():
        grp[c] = gb
    bslot = [0xFF] * 128
    for b, o in var_ordinal.items():
        bslot[b & 0x7F] = o
    # Inverse identity for native frames that already carry finalized vi.  The
    # finalizer still needs the source artwork code for the existing opaque-bbox
    # cull, then keeps the pre-finalized vi for O(1) residency and DMA.
    vi_source = [0xFFFF] * n_variant_cells
    for v in variants:
        vi_source[v["vi"]] = v["code"]
    lines = ["/* GENERATED by tools/graphics_editor/gen_reindexed_pc090oj.py -- do not hand-edit. */",
             "/* Complete (code,bank) sprite variant index. profile_sha256=%s */" % profile_sha,
             ".equ SPRITE_VARIANT_REGION_CELL, %d" % ncodes,
             ".equ SPRITE_VARIANT_REGION_OFF, %d   /* ncodes*128 bytes */" % (ncodes * CELL),
             ".equ SPRITE_VARIANT_KEY_MARK, 0x2000",
             ".equ SPRITE_VARIANT_KEY_NORM, 0x1080",
             ".equ SPRITE_VARIANT_CELLS, %d" % n_variant_cells,
             "    .section .rodata", "    .align 2",
             "    .global pc090oj_variant_group_base",
             "pc090oj_variant_group_base:   /* u16 per code: 0xFFFF = not divergent, else variant-region group base */"]
    for i in range(0, TILE_MAX, 16):
        lines.append("    .word " + ", ".join("0x%04X" % g for g in grp[i:i + 16]))
    lines += ["    .align 2", "    .global pc090oj_variant_bank_slot",
              "pc090oj_variant_bank_slot:    /* byte per effective_bank: 0xFF = base, else ordinal within group */"]
    for i in range(0, 128, 16):
        lines.append("    .byte " + ", ".join("0x%02X" % b for b in bslot[i:i + 16]))
    lines += ["    .align 2", "    .global pc090oj_variant_source_code",
              "pc090oj_variant_source_code: /* u16 source code per finalized vi; bbox provenance only */"]
    for i in range(0, n_variant_cells, 16):
        lines.append("    .word " + ", ".join("0x%04X" % c for c in vi_source[i:i + 16]))
    lines.append("    .section .text,\"ax\"")
    os.makedirs(os.path.dirname(a.variants_inc), exist_ok=True)
    open(a.variants_inc, "w").write("\n".join(lines) + "\n")

    idx = {"profile_sha256": profile_sha, "region_cell_base": ncodes,
           "bank_ordinal": {("0x%02X" % b): o for b, o in var_ordinal.items()},
           "group_base": {("0x%03X" % c): gb for c, gb in group_base.items()},
           "variants": [{"code": "0x%03X" % v["code"], "bank": "0x%02X" % v["bank"], "vi": v["vi"],
                         "region_cell": ncodes + v["vi"]} for v in sorted(variants, key=lambda v: v["vi"])]}
    json.dump(idx, open(a.variants_index, "w"), indent=1)

    asset_sha = hashlib.sha256(bytes(out)).hexdigest()
    print("pc090oj_editor.bin: base %d codes, %d variant cells, %d divergent codes in %d block(s); region %d "
          "cells; profile_sha=%s asset_sha=%s"
          % (len(base), n_variant_cells, len(group_base), len(manifest["divergent_blocks"]),
             ncodes + n_variant_cells, profile_sha[:16], asset_sha[:16]))


if __name__ == "__main__":
    main()
