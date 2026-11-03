#!/usr/bin/env python3
"""Reduce one PROMT-ID-0072 Build-0532 capture without modifying it."""
from __future__ import annotations
import argparse, csv, hashlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "build/pc080sn_boundary/record_native_maps.bin"
PAN = ROOT / "build/pc080sn_boundary/pan_row_maps.bin"
EXPECTED_NATIVE = "823c200a7fafd73fb29d21672252b9124b268e46f49ae98da6fba56bcc285900"
EXPECTED_PAN = "d88893fcd9bdf927bb39599bbbdd7b9a768bd9511dba7d2ff03dca4c619c6910"

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path: Path):
    with path.open(newline="") as f: return list(csv.DictReader(f, delimiter="\t"))
def words_bytes(text: str) -> bytes:
    return b"".join(int(w,16).to_bytes(2,"big") for w in text.split(","))

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("trace",type=Path); a=ap.parse_args()
    td=a.trace.resolve()
    if sha(NATIVE)!=EXPECTED_NATIVE or sha(PAN)!=EXPECTED_PAN:
        raise SystemExit("Build-0532 row oracle hashes changed; refusing ambiguous reduction")
    writes=load(td/"ordered_writes.tsv"); owners=load(td/"provenance_writes.tsv")
    markers=load(td/"markers.tsv"); markerrows=load(td/"marker_rows.tsv")
    if not markers: raise SystemExit("capture has no M marker")
    marker=markers[-1]; mf=int(marker["frame"])
    native=NATIVE.read_bytes(); pan=PAN.read_bytes(); table_bytes=46*12
    def native_row(rec,row):
        e=rec*12; off=int.from_bytes(native[e:e+4],"big"); s=table_bytes+off+row*128
        return native[s:s+128]
    def pan_row(rec,row):
        off=int.from_bytes(pan[rec*4:rec*4+4],"big"); s=off+row*128
        return pan[s:s+128]
    implicated=[]
    for r in markerrows:
        tag=int(r["owner"],16); logical=(tag-1)&63 if tag else None
        actual=words_bytes(r["staged_words_64"]); matches=[]
        if logical is not None:
            for rec in (16,17,20,21):
                if actual==native_row(rec,logical): matches.append(f"native:r{rec}:l{logical}")
                try:
                    if actual==pan_row(rec,logical): matches.append(f"pan:r{rec}:l{logical}")
                except Exception: pass
        if r["staged_hash"]!=r["vdp_hash"] or not matches:
            implicated.append((r["physical"],r["owner"],r["staged_hash"],r["vdp_hash"],",".join(matches) or "NO_16_17_20_21_MATCH"))
    recent=[w for w in writes if mf-900<=int(w["frame"])<=mf]
    counts=Counter(w["writer"] for w in recent)
    out=td/"reduction_summary.md"
    lines=["# Build 0532 remaining Plane-A trace reduction","",
           f"Marker frame: {mf}",f"State: record {marker['record']}, selector {marker['selector']}, front {marker['front']}",
           f"Ordered staging writes in prior 900 frames: {len(recent)}",f"Provenance writes total: {len(owners)}","",
           "Writer counts near marker:"]
    lines += [f"- {k}: {v}" for k,v in sorted(counts.items())]
    lines += ["","Rows requiring examination (staged/VDP mismatch or no exact Build-0532 record 16/17/20/21 asset match):","",
              "| physical | owner tag | staged hash | VDP hash | exact asset matches |","|---:|---:|---:|---:|---|"]
    lines += [f"| {p} | {o} | `{s}` | `{v}` | {m} |" for p,o,s,v,m in implicated]
    lines += ["","Use `ordered_writes.tsv`, `provenance_writes.tsv`, and `row_snapshots.tsv` to walk backward from these rows. The writer PC and complete state tuple are recorded on every transition."]
    out.write_text("\n".join(lines)+"\n")
    print(out)
    print(f"marker={mf} recent_writes={len(recent)} implicated_rows={len(implicated)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
