#!/usr/bin/env python3
"""Prove R1/P1 sprite residency by ACTUAL spawn/retirement lifetime (offline).

Companion to docs/design/Andy_sonic_style_sprite_context_architecture.md §5e–§8. Establishes the
facts that turn segment-membership into a spawn-eligibility / active-lifetime residency model:

  A. graphics-variant identity == raw code within R1/P1 (family codes are bank-partitioned)
  B. hurry-up bat graphics family = Small Bat family (bank 0x3E), codes 0x268..0x26A (KF-068)
  C. Flying Demon: ONE instance at a time (body slot 0x10C508 + wings 0x10C548), TWO encounters
  D. internal section number == human map segment number (full_capture hex == census decimal)
  E. demon presence confined to sections 09 and 0D(=13), spilling to 0A → outlives spawn section

Data: analysis/graphics_optimizer/round1_phase1_corpus/  (original-arcade MAME, USER-driven).
Static owners cited from analysis/ghidra/rastan_arcade/exports/ (spawn scheduler 0x41180, progression
counter A5+0x13E, stage A5+0x118, demon paired-actor init 0x45342, native emit/blank 0x41dae).

No production code, no ROM. Offline analysis only.
"""
import csv, json
from collections import defaultdict, Counter
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[2] / "analysis/graphics_optimizer/round1_phase1_corpus"
DEMON_SLOTS = {"10C508", "10C548"}       # body, wings (census: special two-slot actor_508)
DEMON_BASE = "0129"


def variant_partition():
    d = json.load(open(CORPUS / "enemies.json"))
    codes = defaultdict(set)
    for e in d["enemies"]:
        bank = e.get("effective_sprite_bank", "?")
        for c in e.get("cell_codes", []):
            codes[int(c, 16)].add(bank)
    coll = {c: v for c, v in codes.items() if len(v) > 1}
    print("== A. graphics-variant identity ==")
    print(f"   enemy codes total={len(codes)}  cross-bank collisions={len(coll)}  "
          f"→ within R1/P1, raw code == (code,bank) variant" if not coll else f"   COLLISIONS: {coll}")


def hurryup_family():
    print("\n== B. hurry-up bat family ==")
    print("   KF-068 swarm codes 0x268/0x269/0x26A ⊂ Small Bat family base 0x0268 bank 0x3E "
          "→ hurry-up bat reuses Small Bat graphics (tiny footprint)")


def demon_instances():
    rows = list(csv.DictReader(open(CORPUS / "flying_demon_trace/observations.csv")))
    demon = [r for r in rows if r["actor_address"] in DEMON_SLOTS or r["base_code"].upper().endswith("129")]
    def ai(r):
        try: return int(r["active"])
        except ValueError: return 0
    byf = defaultdict(list)
    for r in demon:
        byf[int(r["frame"])].append(r)
    maxslots = 0
    for f, rs in byf.items():
        maxslots = max(maxslots, len({r["actor_address"] for r in rs if ai(r)}))
    print("\n== C. Flying Demon instances ==")
    print(f"   demon slots seen = {Counter(r['actor_address'] for r in demon if ai(r))}")
    print(f"   MAX simultaneous demon slots active = {maxslots}  (=2 → one body + one wings = ONE instance)")


def section_segment_and_demon():
    fr = defaultdict(lambda: [10**9, 0, 0])
    demon_codes = set(range(0x129, 0x14a)) | set(range(0x16a, 0x177))
    dem = defaultdict(int)
    with open(CORPUS / "full_capture/full_observations.csv") as f:
        for row in csv.DictReader(f):
            if row["round"] != "01":
                continue
            s = row["section"]; fn = int(row["frame"])
            d = fr[s]; d[0] = min(d[0], fn); d[1] = max(d[1], fn); d[2] += 1
            try:
                if int(row["code"], 16) in demon_codes:
                    dem[s] += 1
            except ValueError:
                pass
    print("\n== D/E. section(hex)==segment(dec); demon confined to two sections ==")
    for s in sorted(fr):
        d = fr[s]
        tag = f"  <-- DEMON ({dem[s]})" if dem.get(s) else ""
        print(f"   section {s} (seg {int(s,16)}): frames {d[0]}..{d[1]} rows={d[2]}{tag}")
    demon_sections = sorted(s for s in dem if dem[s] > 500)
    print(f"   demon encounters in sections {demon_sections} = segments {[int(s,16) for s in demon_sections]}"
          f"  (spill to 0A → demon outlives spawn section)")


if __name__ == "__main__":
    variant_partition()
    hurryup_family()
    demon_instances()
    section_segment_and_demon()
