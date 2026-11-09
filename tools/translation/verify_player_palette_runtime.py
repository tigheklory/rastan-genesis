#!/usr/bin/env python3
"""PROMT-ID-0112 player-palette runtime gate.

Proves the §6 four-link player-palette contract from one or more GENESIS NTSC captures produced by
tools/mame/scripts/genesis_player_palette_probe.lua (run via run_genesis_player_palette_probe.sh,
which resolves staging symbols dynamically from the current symbol.txt -- no hard-coded WRAM):

  1. SAT palette-line selection: the player sprites (far-left Rastan cluster) select the intended
     CRAM line (0).
  2. Publication: actual VDP CRAM line 0 == staged CRAM shadow line 0 (publisher committed the shadow).
  3. CRAM contents: actual VDP CRAM line 0 == the authored player palette (test_palette_line0.bin).
  4. Cross-scene: every provided scene (R1-S1, R1-S2, R1-S3) carries the same correct player line 0.

Usage: verify_player_palette_runtime.py <authored_line0.bin> <label:capture_dir> [<label:capture_dir> ...]
"""
from __future__ import annotations
import struct, sys
from pathlib import Path

PLAYER_LINE = 0


def rd(p):
    b = Path(p).read_bytes()
    return list(struct.unpack(">%dH" % (len(b) // 2), b))


def player_sat_lines(sat_tsv):
    """Return the set of palette lines used by the far-left player cluster (Genesis X 150-195, Y 185-250)."""
    lines = []
    for ln in Path(sat_tsv).read_text().splitlines()[1:]:
        idx, y, sl, attr, x, pal, tile, pri = ln.split("\t")
        Y = int(y, 16); X = int(x, 16)
        if Y == 0:
            continue
        if 150 <= X <= 195 and 185 <= Y <= 250:
            lines.append(int(pal))
    return lines


def main():
    if len(sys.argv) < 3:
        print(__doc__); return 2
    authored = rd(sys.argv[1])[:16]
    failed = []
    passed = []

    def ck(name, cond, detail=""):
        (passed if cond else failed).append(name)
        print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -- " + detail))

    first_line0 = None
    for arg in sys.argv[2:]:
        label, cdir = arg.split(":", 1)
        cdir = Path(cdir)
        staged = rd(cdir / "staged_cram.bin")
        actual = rd(cdir / "actual_cram.bin")
        s0 = staged[PLAYER_LINE * 16:PLAYER_LINE * 16 + 16]
        a0 = actual[PLAYER_LINE * 16:PLAYER_LINE * 16 + 16]
        plines = player_sat_lines(cdir / "sat.tsv")

        ck(f"[{label}] player sprites present in SAT", len(plines) > 0, "no far-left player cluster found")
        ck(f"[{label}] player sprites select CRAM line {PLAYER_LINE}",
           len(plines) > 0 and all(p == PLAYER_LINE for p in plines), f"lines seen: {sorted(set(plines))}")
        ck(f"[{label}] CRAM publication consistent (actual line0 == staged line0)", a0 == s0)
        ck(f"[{label}] actual CRAM line0 == authored player palette", a0 == authored,
           "actual=%s authored=%s" % ([("%04X" % w) for w in a0], [("%04X" % w) for w in authored]))
        if first_line0 is None:
            first_line0 = a0
        else:
            ck(f"[{label}] player line0 matches first scene (cross-scene consistency)", a0 == first_line0)

    print("\nPLAYER_PALETTE_RUNTIME %s  (pass=%d, fail=%d)" % (
        "PASS" if not failed else "FAIL", len(passed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
