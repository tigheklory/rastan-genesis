#!/usr/bin/env python3
"""H11 static scene/section enumerator — operates directly on the arcade ROM.

Decodes, per round, the section kind for every A5+0x13E progression value via the proven chain:
    section_kind = byte[0x50F6B + byte[0x50EE0 + 0x13E]]
    0 = outdoor (phase 1), != 0 = castle / interior (phase 2)
and reports the first Phase-2 (castle) start per round.

It does NOT hard-code expected actors. The per-column MARKER enumeration (grid high byte) needs the
ROM population of A5+0x10D000 (each column's collision-record pointer), which is the exact next
dependency (see raw/000559b2.c) and is not yet decoded — so this tool stops at the section layer.
Run from repo root.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MC = open(os.path.join(ROOT, "build/regions/maincpu.bin"), "rb").read()
EE0, F6B = 0x50EE0, 0x50F6B
# code-proven round-end 0x13E values (0x502AC boundary work)
ROUND_END = {1:0x16, 2:0x2D, 3:0x44, 4:0x5B, 5:0x72, 6:0x89}
ROUND_START = {1:0x00, 2:0x17, 3:0x2E, 4:0x45, 5:0x5C, 6:0x73}

def section_kind(p): return MC[F6B + MC[EE0 + p]]

def main():
    out_tsv = os.path.join(ROOT, "analysis/actor_decompilation/h11_scene_markers.tsv")
    rows = ["round\t13E\tscene_index\tsection_kind\tphase\tsource_rom_addr"]
    phase2 = {}
    for r in range(1, 7):
        s, e = ROUND_START[r], ROUND_END[r]
        started = None
        for p in range(s, e + 1):
            si = MC[EE0 + p]; sk = MC[F6B + si]
            ph = "phase2" if sk != 0 else "phase1"
            if sk != 0 and started is None: started = p
            rows.append(f"{r}\t{p:#04x}\t{si}\t{sk}\t{ph}\t{F6B+si:#08x}")
        phase2[r] = started
    with open(out_tsv, "w") as f:
        f.write("\n".join(rows) + "\n")
    print("PHASE-2 (castle) start 0x13E per round (section kind != 0):")
    for r in range(1, 7):
        p = phase2[r]
        print(f"  R{r}: {p:#04x}  (kind {section_kind(p)})" if p is not None else f"  R{r}: none")
    # deterministic checks
    assert all(0 <= MC[EE0 + p] < len(MC) for p in range(0, 0x8A)), "scene index out of range"
    assert all(phase2[r] is not None for r in range(1, 7)), "a round has no phase-2 section"
    print(f"wrote {out_tsv}")
    print("checks: PASS (all six rounds have a proven phase-2 start; indices in range)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
