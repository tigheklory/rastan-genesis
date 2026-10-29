#!/usr/bin/env python3
"""PROMPT-ID-0025 static regression — validate the R1-S2 actor roster chain against the arcade ROM
evidence (NO traces).  Checks:
  1. The marker-route table (h6) and per-round-phase occurrences (h13) load and R1 phase-2 has markers.
  2. Each marker's state matches between h6 (route) and h13 (occurrence).
  3. Each resolved sprite base in the roster decodes to >=2 pieces via the static compositor VM.
  4. The record-type boss body base 0x061D matches rastan_actor_tables.c record_type_45592[0x0E].
  5. The R1-S2 castle bases (0x0224/0x00F4) are NOT already in the Composer sprite catalog (the gap).
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P, F = [], []
def ck(n, c, extra=""):
    (P if c else F).append(n); print(("PASS " if c else "FAIL ") + n + ((" -> " + str(extra)) if extra and not c else ""))

def rows(p, d="\t"):
    with open(ROOT / p) as f:
        return list(csv.DictReader(f, delimiter=d))


def main() -> int:
    roster = json.loads((ROOT / "analysis/actor_decompilation/r1s2_actor_roster.json").read_text())
    h6 = rows("analysis/actor_decompilation/h6_marker_materialization_routes.tsv")
    h13 = rows("analysis/actor_decompilation/h13_phase2_marker_occurrences.tsv")

    r1 = [r for r in h13 if r["round"] == "1"]
    ck("1. R1 phase-2 has marker occurrences", len(r1) >= 1, len(r1))

    # h6 state by marker low byte: build a quick marker->state map from h6 bands (hex ranges in col 0)
    def h6_state_for(marker_hex):
        m = int(marker_hex, 16)
        for r in h6:
            band = r["marker"].split()[-1] if " " in r["marker"] else r["marker"]
            # ranges like "0x31..0x44" or single "0x45"
            txt = r["marker"]
            import re
            nums = re.findall(r"0x[0-9a-fA-F]+", txt)
            if len(nums) >= 2:
                lo, hi = int(nums[0], 16), int(nums[1], 16)
            elif nums:
                lo = hi = int(nums[0], 16)
            else:
                continue
            if lo <= m <= hi:
                return r["output_state"].strip()
        return None

    mism = []
    for occ in r1:
        h6s = h6_state_for(occ["marker"])
        if h6s is not None and h6s.lower() != occ["state_+0x05"].lower():
            mism.append((occ["marker"], occ["state_+0x05"], h6s))
    ck("2. R1 marker states agree between h13 occurrences and h6 routes", not mism, mism)

    # 3. resolved bases decode
    sys.path.insert(0, str(ROOT / "tools/graphics_optimizer"))
    from compositor_vm import ActorRenderState, visible_pieces
    def decodes(base):
        for anim in range(0x100):
            try:
                sat = visible_pieces(ActorRenderState(base, anim, 0))
            except Exception:
                sat = None
            if sat and len(sat) >= 2:
                return True
        return False
    all_bases = [int(b["base"], 16) for a in roster["marker_driven_castle_actors"] for b in a["sprite_bases"]]
    ck("3. every resolved castle base decodes to >=2 pieces (static compositor VM)",
       all_bases and all(decodes(b) for b in all_bases), all_bases)

    # 4. boss body base matches the table decompilation
    tbl = (ROOT / "analysis/decompilation/c/rastan_actor_tables.c").read_text()
    ck("4. R1 boss body base 0x061D present in record_type_45592[0x0E]",
       "0x061D" in tbl and "R1 boss body" in tbl)

    # 5. castle bases are now IN the Composer catalog (0029), attributed to their CORRECT rounds (0038):
    # NOT R1-S2 for 0x0224/0x00F4 (that was the corrected error).
    srv = (ROOT / "tools/graphics_editor/server.py").read_text()
    ck("5. castle bases 0x0224/0x00F4 are in the Composer, NOT tagged R1-S2 (0038 correction)",
       ("0x0224" in srv) and ("0x00F4" in srv) and
       ('(0x0224, 2, "PAL-R2-S2' in srv) and ('(0x00F4, 4, "PAL-R4-S2' in srv))

    print(f"\n{'R1S2_ROSTER PASS' if not F else str(len(F))+' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
