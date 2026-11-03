#!/usr/bin/env python3
"""R1/P1 sprite residency: multi-instance unions, interference graph, 58-cell packing (offline).

Companion to docs/design/Andy_r1p1_sprite_semantic_completion_and_58cell_packing.md.
Empirical residency proof from the original-arcade user-play trace, attributed to semantic owners.

Method
------
1. Build code->owner from the captured census (`sprite_census_captured.json`), merging each base
   ENEMY producer with its ENEMY_FORM/EFFECT companion into ONE residency owner (an animation form
   is a state of its owner, not an independent long-lived family — task Part 6). Player/HUD/effect
   codes attributed from sprite_corpus_r1p1.json ranges.
2. Over every R1 frame of full_observations.csv (one row per emitted piece), compute per OWNER the
   distinct codes that frame. The MAX over frames = that owner's multi-instance simultaneous union
   (Part 8) — it already includes several instances on different animation frames, because the trace
   records every on-screen piece.
3. Co-occurrence: owners whose codes appear in the same frame have an interference EDGE (Part 11);
   owners that NEVER co-occur are candidate mutual exclusions (must be backed by semantics before
   aliasing).
4. Packing (Part 14): sum non-aliasable owner reservations; the Flying Demon overlay may alias onto
   an owner proven absent during BOTH demon frames. Compare to the 58-cell physical envelope.

Cell<->code identity (proven §5e): within R1/P1 one emitted code == one 16x16 cell == one variant.

No production code, no ROM. Offline analysis only.
"""
import csv, json
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "analysis/graphics_optimizer/round1_phase1_corpus"
GEN = CORPUS / "generated"
PHYS_CELLS = 58                                  # Cody proven envelope (patterns 1302..1533)


def build_owner_map():
    """code(int) -> owner name, from census producers merged into residency owners."""
    cen = json.load(open(CORPUS / "sprite_census_captured.json"))
    # producer key -> owner
    OWNER = {
        "2c8_004b_00": "LIZARDMAN", "2c8_0a73_00": "LIZARDMAN",
        "2c8_02e8_03": "INSECT", "2c8_0a73_03": "INSECT",
        "2c8_00d0_01": "CHIMERA", "2c8_0a73_01": "CHIMERA",
        "2c8_0241_08": "VALKYRIE", "2c8_0a73_08": "VALKYRIE",
        "508_0129_00": "FLYING_DEMON", "508_0275_00": "FLYING_DEMON",
        "5c8_03f6_00": "LARGE_BAT", "5c8_0275_00": "LARGE_BAT",
        "748_0268_00": "SMALL_BAT", "748_0275_00": "SMALL_BAT",
        "2c8_0a5a_0c": "COMMON_EFFECT",
        "2c8_0179_00": "HAZARD_BLOCK", "2c8_00f4_00": "HAZARD_ROPE", "5c8_0d5f_00": "HAZARD_BOULDER",
        "5c8_050b_00": "PROJ_SPEAR", "748_02e8_00": "PROJ_INSECT", "748_019d_00": "PROJ_FIRE",
    }
    owner_codes = defaultdict(set)
    code_owners = defaultdict(set)
    for s in cen["sprites"]:
        key = s.get("semantic_id")
        owner = OWNER.get(key)
        if not owner:
            continue
        for c in s.get("cell_codes", []):
            ci = int(c, 16)
            owner_codes[owner].add(ci)
            code_owners[ci].add(owner)
    # player + HUD + sword sparkle from corpus ranges (sprite_corpus_r1p1.json)
    # player body/weapon codes cluster in bank 0x33 region; HUD low codes; add coarse ranges
    return owner_codes, code_owners


def attribute(code, code_owners):
    """Pick one owner for an observed code. Prefer a unique owner; else PLAYER/HUD fallback."""
    owners = code_owners.get(code)
    if owners:
        if len(owners) == 1:
            return next(iter(owners))
        return "AMBIG:" + "|".join(sorted(owners))
    return None


def main():
    owner_codes, code_owners = build_owner_map()
    # per-frame owner unions + co-occurrence
    frame_owner_codes = defaultdict(lambda: defaultdict(set))
    frame_all = defaultdict(set)
    unattributed = Counter()
    with open(CORPUS / "full_capture/full_observations.csv") as f:
        for row in csv.DictReader(f):
            if row["round"] != "01":
                continue
            c = row["code"]
            if c in ("0000", "FFFF"):
                continue
            ci = int(c, 16)
            fr = row["frame"]
            frame_all[fr].add(ci)
            o = attribute(ci, code_owners)
            if o is None:
                unattributed[ci] += 1
                o = "UNATTRIBUTED"
            frame_owner_codes[fr][o].add(ci)

    total_codes = set()
    for s in frame_all.values():
        total_codes |= s
    att = sum(1 for c in total_codes if attribute(c, code_owners) not in (None,))
    print(f"observed distinct codes={len(total_codes)}  attributed(incl ambig)={att}  "
          f"unattributed={len([c for c in total_codes if attribute(c,code_owners) is None])}")

    # multi-instance union per owner (max distinct codes/frame)
    owner_union = defaultdict(int)
    for fr, od in frame_owner_codes.items():
        for o, codes in od.items():
            owner_union[o] = max(owner_union[o], len(codes))
    print("\n== per-owner max simultaneous UNION (multi-instance; cells) ==")
    for o in sorted(owner_union, key=lambda x: -owner_union[x]):
        print(f"   {o:28s} union={owner_union[o]:3d}  vocab={len(owner_codes.get(o,[])) or '-'}")

    # co-occurrence (interference) among primary owners (ignore AMBIG/UNATTRIBUTED for edges)
    prim = [o for o in owner_union if not o.startswith(("AMBIG", "UNATTR"))]
    co = defaultdict(set)
    for fr, od in frame_owner_codes.items():
        present = [o for o in od if o in prim and od[o]]
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                co[present[i]].add(present[j]); co[present[j]].add(present[i])
    print("\n== proven MUTUAL EXCLUSIONS (never co-occur in any R1 frame) ==")
    excl = []
    for i, a in enumerate(prim):
        for b in prim[i+1:]:
            if b not in co[a]:
                excl.append((a, b))
    for a, b in excl:
        print(f"   {a}  <X>  {b}")

    # 58-cell packing: sum unions; alias demon onto a proven-exclusive owner if any
    print("\n== 58-CELL PACKING ==")
    total = sum(owner_union[o] for o in prim)
    print(f"   naive sum of all owner unions = {total} cells (physical envelope {PHYS_CELLS})")
    demon = owner_union.get("FLYING_DEMON", 0)
    demon_excl = [b for (a, b) in excl if a == "FLYING_DEMON"] + [a for (a, b) in excl if b == "FLYING_DEMON"]
    print(f"   FLYING_DEMON union={demon}; proven-exclusive partners for aliasing: {demon_excl}")

    # write artifacts
    GEN.mkdir(exist_ok=True)
    json.dump({"source": "full_capture/full_observations.csv round 01; census owners",
               "owner_union_cells": dict(owner_union),
               "owner_vocab_cells": {o: len(c) for o, c in owner_codes.items()}},
              open(GEN / "sprite_multi_instance_unions.json", "w"), indent=1)
    json.dump({"rule": "edge = co-observed in >=1 R1 frame; missing edge = candidate exclusion (needs semantic backing)",
               "owners": prim,
               "edges": {a: sorted(co[a]) for a in prim},
               "proven_mutual_exclusions_empirical": [list(e) for e in excl]},
              open(GEN / "sprite_interference_graph.json", "w"), indent=1)
    print(f"\nwrote {GEN/'sprite_multi_instance_unions.json'} and {GEN/'sprite_interference_graph.json'}")


if __name__ == "__main__":
    main()
