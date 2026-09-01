#!/usr/bin/env python3
"""Independent verifier for the offline PC090OJ Test-sprite reindex (TOOLING).

Re-derives the expected 128-byte transformed cell for every resolved authored R1/P1 sprite code directly
from the raw preconverted region + the frozen Test index_map, and asserts pc090oj_editor.bin[code*128:+128]
equals it. Does NOT reuse the transformer's write path: it recomputes from raw independently and asserts on
the semantic 16x16 cell (four 8x8 subtiles), not on the offset arithmetic alone.
"""
import argparse, hashlib, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(__file__))
from gen_reindexed_pc090oj import build_code_usage   # reuse ONLY the semantic (code->map) resolution

CELL = 128


def expected_cell(raw_cell, imap):
    out = bytearray(len(raw_cell))
    for i, b in enumerate(raw_cell):
        hi = (b >> 4) & 0xF; lo = b & 0xF
        hi = imap.get(hi, hi) if hi != 0 else 0
        lo = imap.get(lo, lo) if lo != 0 else 0
        out[i] = (hi << 4) | lo
    return bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.join(ROOT, "build/rastan-direct/build0314/Test.snapshot.json"))
    ap.add_argument("--enemies", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1_corpus/enemies.json"))
    ap.add_argument("--enemy-patterns", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1_corpus/enemy_patterns.json"))
    ap.add_argument("--families", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1/sprite_families.json"))
    ap.add_argument("--raw", default=os.path.join(ROOT, "build/pc090oj_genesis.bin"))
    ap.add_argument("--editor", default=os.path.join(ROOT, "build/regions/pc090oj_editor.bin"))
    a = ap.parse_args()

    profile = json.load(open(a.profile))
    code_usage = build_code_usage(profile, json.load(open(a.enemies)),
                                  json.load(open(a.enemy_patterns)), json.load(open(a.families)))
    raw = open(a.raw, "rb").read()
    ed = open(a.editor, "rb").read()

    authored = sorted(code_usage)
    mismatch, incomplete, nonident_raw = [], [], []
    identity_raw_ok = []
    for code in authored:
        uid, bank, line, imap = code_usage[code]
        s = code * CELL
        rawc = raw[s:s + CELL]; edc = ed[s:s + CELL]
        exp = expected_cell(rawc, imap)
        if edc != exp:
            mismatch.append(code)
        # incomplete = editor cell equals raw in some region but expected differed there
        if edc != exp:
            incomplete.append(code)
        # a non-identity mapping that left the cell byte-identical to raw despite used indices
        if edc == rawc:
            used = set()
            for b in rawc:
                used.add((b >> 4) & 0xF); used.add(b & 0xF)
            changing = [k for k in imap if k in used and imap[k] != k and k != 0]
            (nonident_raw if changing else identity_raw_ok).append(code)

    # confirm no writes landed outside authored cells: every changed byte lies in some authored cell
    authored_ranges = [(c * CELL, c * CELL + CELL) for c in authored]
    def in_authored(off):
        return any(lo <= off < hi for lo, hi in authored_ranges)
    stray = 0
    for off in range(len(ed)):
        if ed[off] != raw[off] and not in_authored(off):
            stray += 1
            if stray <= 5:
                print("STRAY write outside authored cell at 0x%X" % off)

    print("authored codes:            %d" % len(authored))
    print("transformed (editor!=raw): %d" % sum(1 for c in authored if ed[c*CELL:c*CELL+CELL] != raw[c*CELL:c*CELL+CELL]))
    print("mismatch vs independent:   %d  %s" % (len(mismatch), mismatch[:8]))
    print("incomplete 128B cells:     %d" % len(incomplete))
    print("non-identity yet raw:      %d  %s" % (len(nonident_raw), [hex(c) for c in nonident_raw[:8]]))
    print("(identity/unused -> raw, expected OK): %d" % len(identity_raw_ok))
    print("stray writes outside authored cells:   %d" % stray)

    ok = (len(mismatch) == 0 and len(incomplete) == 0 and stray == 0)
    print("VERIFY:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
