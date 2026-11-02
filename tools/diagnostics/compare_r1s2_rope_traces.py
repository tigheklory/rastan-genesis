#!/usr/bin/env python3
"""Compare human R1-S2 rope traces by semantic scene state, never raw frame."""
from __future__ import annotations
import argparse, csv
from collections import defaultdict
from pathlib import Path

KEY = ("fg_y", "record", "selector", "completed_selector", "strip", "group", "entering_logical_rows")
COMPARE = ("selection_mode", "entering_physical_rows", "staged_rows", "fg_row_dirty", "dirty_write_count", "vc_write_sequence", "path_events", "plane_a_vlines", "total_vlines")

def load(path: Path):
    with (path / "frames.tsv").open(newline="") as f:
        rows=list(csv.DictReader(f, delimiter="\t"))
    # R1-S2 begins at retained record 0x10/0x11. Exclude title/READY repetition,
    # which has no scene-progression meaning and otherwise dominates common keys.
    return [r for r in rows if int(r.get("record", "0"), 16) >= 0x10]

def key(row): return tuple(row.get(k, "") for k in KEY)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("jump", type=Path, nargs="?", default=Path("states/traces/r1s2_rope_build_0529/jump"))
    ap.add_argument("normal", type=Path, nargs="?", default=Path("states/traces/r1s2_rope_build_0529/normal"))
    ap.add_argument("-o", "--output", type=Path, default=Path("states/traces/r1s2_rope_build_0529/comparison.md"))
    a=ap.parse_args(); jump,normal=load(a.jump),load(a.normal)
    ni=defaultdict(list)
    for r in normal: ni[key(r)].append(r)
    used=defaultdict(int)
    matched=[]
    for j in jump:
        candidates=ni.get(key(j),())
        index=used[key(j)]
        if index < len(candidates):
            matched.append((j,candidates[index]))
            used[key(j)]+=1
    divergences=[]
    for j,n in matched:
        diff=[f for f in COMPARE if j.get(f,"")!=n.get(f,"")]
        if diff: divergences.append((j,n,diff))
    marks=lambda rows:[r["frame"] for r in rows if r.get("marker")=="1"]
    lines=["# R1-S2 rope trace semantic comparison","",f"Jump frames: {len(jump)}; normal frames: {len(normal)}.",
           f"Matched semantic states: {len(matched)}; differing matched states: {len(divergences)}.",
           f"Marker frames — jump: {', '.join(marks(jump)) or 'none'}; normal: {', '.join(marks(normal)) or 'none'}.","",
           "Alignment key: `"+" / ".join(KEY)+"`. Frame numbers are reported only as provenance.",""]
    if divergences:
        j,n,diff=divergences[0]
        lines += ["## Earliest differing matched semantic state","",f"Jump frame {j['frame']}; normal frame {n['frame']}; fields: `{', '.join(diff)}`.","",
                  "| Field | Jump | Normal |","|---|---|---|"]
        for f in KEY+COMPARE: lines.append(f"| `{f}` | `{j.get(f,'')}` | `{n.get(f,'')}` |")
        lines += ["","This is the earliest difference in trace order among states sharing the full alignment key. It is evidence for investigation, not by itself proof of arcade incorrectness."]
    elif matched:
        lines += ["No compared field differs at the matched semantic states. Inspect unmatched progression and user markers before drawing a renderer conclusion."]
    else:
        lines += ["No equivalent semantic states were found. Confirm both captures reached R1-S2 gameplay and completed enough overlapping scene progression."]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text("\n".join(lines)+"\n")
    print(a.output)
    return 0
if __name__=="__main__": raise SystemExit(main())
