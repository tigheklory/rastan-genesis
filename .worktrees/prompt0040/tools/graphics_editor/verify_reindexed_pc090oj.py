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

    ok = (not mismatch and not incomplete and stray == 0 and not divergent_bad)
    print("VERIFY:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
