#!/usr/bin/env python3
"""Verify the Round-2 arcade Plane-A palette provenance (PROMT-ID-0110).

Proves the per-round palette source chain statically and that the regenerated subround corpus uses it:

  round counter a5+0x118 -> per-round base pointer table 0x59C9A ((round-1)*4) -> per-round palette base
  (loader FUN_00059c54 into 0x10D600) -> fade FUN_00045d7c into visible palette RAM 0x200000.

  round 1 -> 0x4EAF6 (== the startup/fixed base, so Round 1 is unchanged)
  round 2 -> 0x4EEF8   (was wrongly 0x4EAF6 -> teal foliage / black boss-room bank 2)

Read-only against build/regions/maincpu.bin + the generated corpus. No ROM/build/counter change.
"""
from __future__ import annotations
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MC = (ROOT / "build/regions/maincpu.bin").read_bytes()
CORPUS = ROOT / "analysis/graphics_optimizer/subround_corpus"
PTR = 0x59C9A

_p = _f = 0


def ck(name, cond, detail=""):
    global _p, _f
    if cond:
        _p += 1; print("PASS " + name)
    else:
        _f += 1; print("FAIL " + name + (" — " + detail if detail else ""))


def u16(a): return struct.unpack(">H", MC[a:a + 2])[0]
def u32(a): return struct.unpack(">I", MC[a:a + 4])[0]


def conv(word):  # arcade 0RGB -> xBGR555, then to rgb8 (same as the corpus pal5 path)
    R = (word >> 8) & 0xF; G = (word >> 4) & 0xF; B = word & 0xF
    def e(n): return ((n * 2) << 3) | ((n * 2) >> 2)
    return (e(R), e(G), e(B))


def round_base(rnd): return u32(PTR + (rnd - 1) * 4)
def bank(base, n): return [conv(u16(base + n * 32 + i * 2)) for i in range(16)]


def corpus_bank(scene, bid):
    p = CORPUS / scene / "plane_palette_banks.json"
    b = json.loads(p.read_text())["banks"].get(bid)
    return b


def main():
    # 1. The per-round pointer table resolves to the documented bases.
    expect = {1: 0x4EAF6, 2: 0x4EEF8, 3: 0x4F15A, 4: 0x4F51C, 5: 0x4F85E, 6: 0x4FA80}
    got = {r: round_base(r) for r in range(1, 7)}
    ck("1. per-round palette base table @0x59C9A resolves", got == expect, f"got {{{','.join('%d:0x%05X'%(r,got[r]) for r in got)}}}")

    # 2. Round 1 base IS the fixed startup base (why R1 is unchanged).
    ck("2. round 1 base == fixed startup base 0x4EAF6", round_base(1) == 0x4EAF6)

    # 3. Round 2 base differs from round 1 (a genuine per-round palette).
    ck("3. round 2 base != round 1 base", round_base(2) != round_base(1))

    # 4. Round-2 foliage banks (4,5) are GREEN (G dominant), not R1 teal (G==B, R low).
    def greenish(cols):
        # count entries where green clearly dominates both red and blue
        return sum(1 for (r, g, b) in cols if g > r + 24 and g > b + 24)
    def tealish(cols):
        return sum(1 for (r, g, b) in cols if abs(g - b) <= 16 and g > r + 40 and b > r + 40)
    r2b4 = bank(round_base(2), 4); r2b5 = bank(round_base(2), 5)
    r1b4 = bank(round_base(1), 4)
    ck("4. round-2 bank 4 is green (foliage), not teal", greenish(r2b4) >= 2 and tealish(r2b4) == 0,
       f"green={greenish(r2b4)} teal={tealish(r2b4)}")
    ck("5. round-1 bank 4 WAS teal (confirms the old bug source)", tealish(r1b4) >= 2)
    ck("6. round-2 bank 5 is green (foliage)", greenish(r2b5) >= 2)

    # 7. R2-S3 boss-room bank 2 is NOT all-black (the fixed base had it zero).
    r2s3_b2 = bank(round_base(2), 2)
    ck("7. round-2 bank 2 (boss room) is not all black", any(c != (0, 0, 0) for c in r2s3_b2))

    # 8. The regenerated corpus matches the per-round ROM data (source + colors).
    cb = corpus_bank("PAL-R2-S1-PLANEA-OUTDOOR", "0x004")
    ck("8. R2-S1 corpus bank 4 == round-2 ROM bank 4", cb is not None and [tuple(c) for c in cb["arcade_rgb8"]] == r2b4,
       "corpus not regenerated from the per-round base")
    ck("9. R2-S1 corpus bank 4 source cites the per-round r2 base", cb is not None and "r2" in cb["source"] and "4EEF8" in cb["source"].upper(),
       cb["source"] if cb else "missing")
    cb3 = corpus_bank("PAL-R2-S3-PLANEA-BOSS", "0x002")
    ck("10. R2-S3 corpus bank 2 is not all black", cb3 is not None and any(tuple(c) != (0, 0, 0) for c in cb3["arcade_rgb8"]))

    # 11. Round-1 corpus is unchanged (its base is still 0x4EAF6): colors equal the ROM round-1 bank.
    c1 = corpus_bank("PAL-R1-S2-PLANEA-CASTLE", "0x003")
    ck("11. R1 corpus colors preserved (round-1 base)", c1 is not None and [tuple(c) for c in c1["arcade_rgb8"]] == bank(round_base(1), 3))

    # 12. The generator sources the per-round base (not a hardcoded fixed base).
    gen = (ROOT / "tools/graphics_editor/gen_subround_layera_corpus.py").read_text()
    ck("12. generator uses the per-round base table 0x59C9A", "0x59C9A" in gen and "_per_round_palette_base" in gen
       and "base = 0x4EAF6 + b * 32" not in gen)

    print(f"\nR2_ARCADE_PALETTE {'PASS' if _f == 0 else 'FAIL'}  (pass={_p}, fail={_f})")
    return 1 if _f else 0


if __name__ == "__main__":
    sys.exit(main())
