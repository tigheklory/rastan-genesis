#!/usr/bin/env python3
"""Prove the Round-1/Phase-1 sprite peak simultaneous working set (offline).

Companion to docs/design/Andy_sonic_style_sprite_context_architecture.md §5. Computes, from the
original-arcade user-play corpus, the three numbers that decide the 49-cell capacity question:

  5a. per-segment VOCABULARY sums   (the WRONG metric; proves full-art residency impossible)
  5b. screen-wide per-frame WORKING SET  (the CORRECT metric; distinct emitted codes / frame)
  5c. per-section peak working set  (locates the over-49 tail)
  5d. Flying Demon own working set  (proves DPLC sizing: reserve max single frame, not vocabulary)

Cell<->code identity: the native finalizer keys residency by emitted graphics `code` over
NATIVE_CELLS=49 slots (pc090oj_hooks.s .Lnq_lookup_loop), so one resident code == one cell slot and
distinct emitted codes per frame == distinct resident cells required that frame.

Run:  python3 tools/graphics_optimizer/prove_r1p1_working_set.py
Data: analysis/graphics_optimizer/round1_phase1_corpus/  (original-arcade MAME, USER-driven traces)
No production code, no ROM. Offline analysis only.
"""
import csv, json, math, statistics as st
from collections import defaultdict
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[2] / "analysis/graphics_optimizer/round1_phase1_corpus"
BLANK = {"0000", "FFFF"}          # placeholder / blank sprite codes, excluded
NATIVE_CELLS = 49                 # pc090oj_hooks.s resident-cell budget


def pct(v, p):
    v = sorted(v)
    return v[max(min(len(v) - 1, int(math.ceil(p / 100 * len(v))) - 1), 0)]


def vocab_sums():
    """5a: per-segment coexisting-vocabulary sums from the captured census."""
    d = json.load(open(CORPUS / "sprite_census_captured.json"))
    seg = defaultdict(list)
    for s in d["sprites"]:
        n = len(s.get("cell_codes", []))
        for g in s.get("sections_records", []):
            seg[str(g)].append((s.get("display_name", "?"), n))
    print("== 5a. per-segment VOCABULARY sum (WRONG metric) vs 49 ==")
    worst = 0
    for g in sorted(seg, key=lambda x: int(x)):
        tot = sum(n for _, n in seg[g])
        worst = max(worst, tot)
        print(f"   seg {g:>3}: sum_vocab={tot:4d}")
    print(f"   WORST segment vocabulary sum = {worst} cells  (>= {worst // NATIVE_CELLS}x the budget)\n")


def screenwide_working_set():
    """5b/5c: distinct emitted codes per frame, screen-wide and per section."""
    fcodes = defaultdict(set)
    fsec = {}
    sec_frame = defaultdict(lambda: defaultdict(set))
    with open(CORPUS / "full_capture/full_observations.csv") as f:
        for row in csv.DictReader(f):
            if row["round"] != "01":          # Round 1 only
                continue
            c = row["code"]
            key = row["frame"]
            fsec[key] = row["section"]
            if c not in BLANK:
                fcodes[key].add(c)
                sec_frame[row["section"]][key].add(c)
    dist = [len(v) for v in fcodes.values()]
    over = sum(1 for d in dist if d > NATIVE_CELLS)
    print("== 5b. screen-wide per-frame WORKING SET (CORRECT metric) ==")
    print(f"   frames={len(dist)}  median={st.median(dist):.0f}  mean={st.mean(dist):.1f}  "
          f"P95={pct(dist,95)}  MAX={max(dist)}")
    print(f"   frames > {NATIVE_CELLS}: {over}/{len(dist)} = {100*over/len(dist):.2f}%   "
          f"(> 40: {sum(1 for d in dist if d>40)})\n")
    print("== 5c. per-section MAX working set (locates the over-49 tail) ==")
    for sec in sorted(sec_frame):
        perf = [len(c) for c in sec_frame[sec].values()]
        flag = "  <-- OVER 49" if max(perf) > NATIVE_CELLS else ""
        print(f"   section {sec}: frames={len(perf):4d}  median={st.median(perf):.0f}  "
              f"P95={pct(perf,95):2d}  MAX={max(perf):2d}{flag}")
    print()


def demon_working_set():
    """5d: Flying Demon own per-frame working set from its actor-tagged trace."""
    dc = defaultdict(set)
    owned = defaultdict(int)
    with open(CORPUS / "flying_demon_trace/observations.csv") as f:
        for row in csv.DictReader(f):
            pr = row.get("piece_records", "").strip()
            if not pr or pr in ("[]", "0"):
                continue
            try:
                owned[row["frame"]] = max(owned[row["frame"]], int(row.get("owned_count", 0)))
            except ValueError:
                pass
            for p in pr.split("|"):
                parts = p.strip().split(":")
                if len(parts) >= 5 and parts[4] not in BLANK:
                    dc[row["frame"]].add(parts[4])
    vals = [len(v) for v in dc.values() if v]
    ov = [v for v in owned.values() if v]
    print("== 5d. Flying Demon own working set (proves DPLC sizing) ==")
    print(f"   vocabulary (census body+form)        = 149 cells")
    print(f"   owned pieces/frame   median/P95/MAX  = {st.median(ov):.0f}/{pct(ov,95)}/{max(ov)}")
    print(f"   distinct codes/frame median/P95/MAX  = {st.median(vals):.0f}/{pct(vals,95)}/{max(vals)}"
          f"   <-- reserve MAX ({max(vals)}), not 149")


if __name__ == "__main__":
    vocab_sums()
    screenwide_working_set()
    demon_working_set()
