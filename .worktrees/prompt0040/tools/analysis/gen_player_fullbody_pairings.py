#!/usr/bin/env python3
"""Generate the authoritative H24 player full-body pairing artifact (torso 0x5BD40 + legs 0x5C466).

The two player tracks animate independently; a full-body pose is torso[a3[i]] over legs[a4[i]] for an
animation index i, NOT the torso x legs product. This enumerates the valid pairings from the 18 a3/a4
pose-table pairs in the player constructor 0x540CC and drops disconnected combinations (torso bottom
vs leg top vertical gap >= 4 px — the leg-17 crouch-leg mispairing class). Output is consumed by BOTH
the Bestiary (build_bestiary.py) and the Palette Composer (tools/graphics_editor/server.py) so neither
hard-codes the list. Static ROM read only; no ROM build. Run from repo root."""
import os, csv
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MC = open(os.path.join(ROOT, "build/regions/maincpu.bin"), "rb").read()
OUT = os.path.join(ROOT, "analysis/actor_decompilation/h24_player_fullbody_pairings.tsv")
UP, LO = 0x5BD40, 0x5C466

def s8(b): return b - 256 if b >= 128 else b
def offs(TBL, n): return [int.from_bytes(MC[TBL+i*2:TBL+i*2+2], "big") for i in range(n)]
up_off, lo_off = offs(UP, 75), offs(LO, 52)

def pieces(tbl, offlist, slot):
    o = offlist[slot]; srt = sorted(offlist); nx = min([x for x in srt if x > o] + [o+24]); n = (nx-o)//6
    base = tbl+o; out = []
    for p in range(n):
        r = MC[base+p*6:base+p*6+6]; t = int.from_bytes(r[0:2], "big")
        if t & 0x1fff: out.append((t & 0x1fff, s8(r[2]), s8(r[3])))
    return out

# 18 per-state (upper a3, lower a4) pose-table pairs from 0x540CC
PAIRS = [(0x5b640,0x5b660),(0x5b640,0x5b680),(0x5b6d0,0x5b6f8),(0x5b720,0x5b740),(0x5b778,0x5b7a0),
         (0x5b7c8,0x5b7e8),(0x5b818,0x5b840),(0x5b868,0x5b888),(0x5b8d8,0x5b900),(0x5b928,0x5b948),
         (0x5b9a8,0x5b9d0),(0x5b9f8,0x5ba00),(0x5ba70,0x5ba78),(0x5bab0,0x5bac8),(0x5bb40,0x5bb80),
         (0x5bbc0,0x5bc00),(0x5bc40,0x5bc80),(0x5bcc0,0x5bd00)]
bounds = sorted(set([a for a, _ in PAIRS] + [b for _, b in PAIRS] + [UP]))
def tlen(a): return min([x for x in bounds if x > a] + [UP]) - a
def body_gap(u, l):
    up = pieces(UP, up_off, u); lo = pieces(LO, lo_off, l)
    if not up or not lo: return None                          # effect/dissolve frame (one half empty)
    return min(y for _, _, y in lo) - (max(y for _, _, y in up) + 16)

def build():
    seen = {}; rows = []
    for a3, a4 in PAIRS:
        n = min(tlen(a3), tlen(a4))
        for i in range(n):
            u = MC[a3+i]; l = MC[a4+i]
            if u >= 75 or l >= 52: continue
            g = body_gap(u, l)
            if g is not None and abs(g) >= 4: continue        # disconnected (leg-17 class) -> drop
            if (u, l) in seen: continue
            seen[(u, l)] = 1
            rows.append([len(rows), u, l, "0x%05x" % a3, i, "" if g is None else g])
    return rows

def main():
    rows = build()
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["pair_index", "torso_slot", "leg_slot", "pose_table_a3", "anim_index", "waist_gap_px"])
        w.writerows(rows)
    print("wrote %d valid full-body pairings -> %s" % (len(rows), OUT))

if __name__ == "__main__":
    main()
