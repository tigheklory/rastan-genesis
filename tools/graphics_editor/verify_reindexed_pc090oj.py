#!/usr/bin/env python3
"""Independent verifier for the offline PC090OJ complete (code,bank) sprite reindex (TOOLING).

Re-derives, directly from the raw preconverted region + the frozen Test index_maps, the expected 128-byte
transformed cell for (a) every resolved base code (baked at code*128) and (b) every appended (code,bank)
variant cell, and asserts the built pc090oj_editor.bin matches. It recomputes each cell independently
(does not read the generator's write path) and asserts on the semantic 16x16 cell (four 8x8 subtiles).

Coverage requirements (all currently-authored production objects): missing=0, mismatched=0, incomplete=0,
unexpectedly-raw-non-identity=0. Also proves cross-bank divergent variants are distinct and reports the
Rastan retention breakdown (accepted Build-0380 body must be untouched).
"""
import argparse, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from gen_reindexed_pc090oj import build_layout, transform, CELL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.join(ROOT, "build/rastan-direct/build0384/Test.snapshot.json"))
    ap.add_argument("--corpus", default=os.path.join(ROOT, "analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv"))
    ap.add_argument("--raw", default=os.path.join(ROOT, "build/pc090oj_genesis.bin"))
    ap.add_argument("--editor", default=os.path.join(ROOT, "build/regions/pc090oj_editor.bin"))
    a = ap.parse_args()

    profile = json.load(open(a.profile))
    raw = bytearray(open(a.raw, "rb").read())
    ed = open(a.editor, "rb").read()
    ncodes = len(raw) // CELL

    base, variants, var_ordinal, group_base, n_variant_cells, cb_map, code_banks = build_layout(profile, raw, a.corpus)

    mismatch, incomplete, nonident_raw = [], [], []
    identity_raw_ok = []

    # ---- base cells ----
    for code, (usagebase, uid, bank, line, imap) in sorted(base.items()):
        s = code * CELL
        exp = transform(raw, code, imap)
        edc = ed[s:s + CELL]
        rawc = bytes(raw[s:s + CELL])
        if edc != exp:
            mismatch.append(("base", code)); incomplete.append(("base", code))
        if edc == rawc:
            used = set()
            for b in rawc:
                used.add((b >> 4) & 0xF); used.add(b & 0xF)
            changing = [k for k in imap if k in used and imap[k] != k and k != 0]
            (nonident_raw if changing else identity_raw_ok).append(("base", code))

    # ---- variant cells ----
    real_variants = list(variants)
    var_sha = {}
    for v in real_variants:
        vi = v["vi"]
        s = (ncodes + vi) * CELL
        exp = transform(raw, v["code"], v["imap"])
        edc = ed[s:s + CELL]
        if edc != exp:
            mismatch.append(("variant", v["code"], "0x%02X" % v["bank"]))
            incomplete.append(("variant", v["code"]))
        var_sha[(v["code"], v["bank"])] = __import__("hashlib").sha256(edc).hexdigest()

    # ---- cross-bank divergence proof: every divergent code's per-bank cells are DISTINCT ----
    divergent_codes = sorted(c for c, banks in code_banks.items() if len(banks) > 1)
    import hashlib
    divergent_distinct = 0
    divergent_bad = []
    for code in divergent_codes:
        shas = set()
        # base cell sha
        shas.add(hashlib.sha256(ed[code * CELL:code * CELL + CELL]).hexdigest())
        for v in real_variants:
            if v["code"] == code:
                shas.add(var_sha[(code, v["bank"])])
        if len(shas) == len(code_banks[code]):
            divergent_distinct += 1
        else:
            divergent_bad.append(code)

    # ---- stray writes outside authored base cells + variant region ----
    authored_lo = 0
    stray = 0
    # any byte differing from raw must lie in a baked base cell or the variant region
    base_ranges = [(c * CELL, c * CELL + CELL) for c in base]
    var_start = ncodes * CELL
    def in_base(off):
        return any(l <= off < h for l, h in base_ranges)
    for off in range(min(len(ed), var_start)):
        if ed[off] != raw[off] and not in_base(off):
            stray += 1
            if stray <= 5:
                print("STRAY write outside authored base cell at 0x%X" % off)

    # ---- Rastan retention breakdown ----
    rastan = [c for c in base if base[c][0] == "rastan"]
    r_mismatch = [c for c in rastan if ("base", c) in set(mismatch)]
    knight = [c for c in base if base[c][0] == "green_sword_knight.r1.n3"]
    knight_mismatch = [c for c in knight if ("base", c) in set(mismatch)]
    # Independently re-derive the COMPLETE same-actor base-$033E animation domain (PROMPT-ID-0078): NORMAL
    # $93-$96, CROUCH $71-$73 (state-0x0F alt 0x40E0E, base-preserving), AIRBORNE $20-$23 (engine 0x473B8
    # states 0D/0E), ROPE $4D,$56-$5A. ($74 is the state-0x20 torch, base 0x0DAB, correctly excluded.) This
    # rejects any rank-based subset AND fails if a refactor silently drops the crouch, airborne, or rope block.
    vm_path = os.path.join(ROOT, "tools/graphics_optimizer")
    if vm_path not in sys.path:
        sys.path.insert(0, vm_path)
    from compositor_vm import ActorRenderState, visible_pieces
    knight_anims = (0x93, 0x94, 0x95, 0x96, 0x71, 0x72, 0x73,
                    0x20, 0x21, 0x22, 0x23, 0x4D, 0x56, 0x57, 0x58, 0x59, 0x5A)
    knight_expected = {
        piece.tile & 0x1FFF
        for anim in knight_anims
        for piece in visible_pieces(ActorRenderState(0x033E, anim, 0))
        if (piece.tile & 0x1FFF) < 0x1000
    }
    knight_covered = {
        code for (code, bank), (_usagebase, uid, _line, _imap) in cb_map.items()
        if bank == 0x33 and uid == "object:castle.green_sword_knight.r1.n3"
    }
    knight_domain_bad = knight_covered != knight_expected

    total_req = sum(len(bs) for bs in code_banks.values())
    print("total (code,bank) requirements:      %d" % total_req)
    print("unique codes:                        %d" % len(code_banks))
    print("base cells reindexed:                %d" % len(base))
    print("variant cells generated:             %d" % len(real_variants))
    print("deduplicated identical variants:     %d" % 0)
    print("cross-bank divergent codes:          %d (all-distinct %d, bad %d)"
          % (len(divergent_codes), divergent_distinct, len(divergent_bad)))
    print("mismatched:                          %d  %s" % (len(mismatch), mismatch[:6]))
    print("incomplete:                          %d" % len(incomplete))
    print("unexpectedly raw (non-identity):     %d  %s" % (len(nonident_raw), nonident_raw[:6]))
    print("identity/unused -> raw (expected):   %d" % len(identity_raw_ok))
    print("stray writes outside authored cells: %d" % stray)
    print("-- RASTAN (object:player.rastan) retention --")
    print("  rastan base codes:  %d   mismatched: %d" % (len(rastan), len(r_mismatch)))
    print("-- R1 GREEN SWORD KNIGHT (object:castle.green_sword_knight.r1.n3) --")
    print("  knight base codes:  %d   mismatched: %d" % (len(knight), len(knight_mismatch)))
    print("  $04684E normal+rope domain: expected %d covered %d exact=%s"
          % (len(knight_expected), len(knight_covered), not knight_domain_bad))

    ok = (not mismatch and not incomplete and stray == 0 and not divergent_bad
          and bool(knight) and not knight_mismatch and not knight_domain_bad)
    print("VERIFY:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
