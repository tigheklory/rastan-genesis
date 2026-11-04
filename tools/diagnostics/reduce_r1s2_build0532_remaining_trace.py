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
# Exact Build-0532 native name word for arcade dynamic surface-mark code $25C7.
# This is diagnostic classification only; production still resolves the code through the LUT.
SURFACE_MARK_WORD = 0x02DF

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
    # MAME's Genesis VDP address-space readback is not valid in every build.  A capture in
    # which all 32 rows have one identical hash is a blank/readback artifact, not evidence
    # that all 32 published rows diverged.
    vdp_hashes={r["vdp_hash"] for r in markerrows}
    vdp_readback_valid=len(vdp_hashes)>1
    marker_y=int(marker["fg_y"],16)
    visible_top=((-marker_y+8)&0x1ff)>>3
    # NTSC exposes 28 tile rows.  The remaining four rows of the 32-row plane
    # are the arcade producer's legitimate prefetch margin; their N/N+32 owner
    # need not match a synthetic full-plane camera window.
    expected_by_physical={(visible_top+i)&31:(visible_top+i)&63 for i in range(28)}
    implicated=[]; overlays=[]
    for r in markerrows:
        physical=int(r["physical"])
        tag=int(r["owner"],16); logical=(tag-1)&63 if tag else None
        expected_logical=expected_by_physical.get(physical)
        owner_mismatch=(expected_logical is not None and logical != expected_logical)
        actual=words_bytes(r["staged_words_64"]); matches=[]
        if logical is not None:
            for rec in (16,17,20,21):
                if actual==native_row(rec,logical): matches.append(f"native:r{rec}:l{logical}")
                try:
                    if actual==pan_row(rec,logical): matches.append(f"pan:r{rec}:l{logical}")
                except Exception: pass
        if not matches and logical is not None:
            actual_words=[int.from_bytes(actual[i:i+2],"big") for i in range(0,128,2)]
            for rec in (16,17,20,21):
                expected=native_row(rec,logical)
                expected_words=[int.from_bytes(expected[i:i+2],"big") for i in range(0,128,2)]
                diffs=[i for i,(x,y) in enumerate(zip(actual_words,expected_words)) if x!=y]
                if (len(diffs)==4 and diffs==list(range(diffs[0],diffs[0]+4)) and
                        all(actual_words[i]==SURFACE_MARK_WORD for i in diffs)):
                    overlays.append((r["physical"],logical,rec,diffs[0]))
                    matches.append(f"arcade_surface_mark:native:r{rec}:l{logical}:c{diffs[0]}-{diffs[-1]}")
        if (vdp_readback_valid and r["staged_hash"]!=r["vdp_hash"]) or not matches or owner_mismatch:
            implicated.append((r["physical"],expected_logical,r["owner"],
                                "YES" if owner_mismatch else "no",
                                r["staged_hash"],r["vdp_hash"],
                                ",".join(matches) or "NO_16_17_20_21_MATCH"))
    recent=[w for w in writes if mf-900<=int(w["frame"])<=mf]
    counts=Counter(w["writer"] for w in recent)
    out=td/"reduction_summary.md"
    lines=["# Build 0532 remaining Plane-A trace reduction","",
           f"Marker frame: {mf}",f"State: record {marker['record']}, selector {marker['selector']}, front {marker['front']}",
           f"Camera FG Y: {marker['fg_y']}; visible logical rows: {visible_top}..{(visible_top+27)&63} (wrapped); four physical rows remain prefetch margin",
           f"Ordered staging writes in prior 900 frames: {len(recent)}",f"Provenance writes total: {len(owners)}","",
           f"VDP readback usable: {'yes' if vdp_readback_valid else 'no (all 32 row hashes identical; ignored)'}","",
           "Writer counts near marker:"]
    lines += [f"- {k}: {v}" for k,v in sorted(counts.items())]
    lines += ["","Rows requiring examination (resident-owner mismatch, staged/VDP mismatch, or no exact Build-0532 record 16/17/20/21 asset match):","",
              "| physical | visible logical (or prefetch) | owner tag | visible-owner mismatch | staged hash | VDP hash | exact asset matches |","|---:|---:|---:|:---:|---:|---:|---|"]
    lines += [f"| {p} | {e if e is not None else 'prefetch'} | {o} | {mismatch} | `{s}` | `{v}` | {m} |"
              for p,e,o,mismatch,s,v,m in implicated]
    lines += ["","Arcade-authored dynamic surface-mark overlays:"]
    lines += ([f"- physical {p}, logical {l}, record {rec}, columns {col}-{col+3}: four native `$25C7` / `$02DF` cells"
               for p,l,rec,col in overlays] or ["- none"])
    lines += ["","Use `ordered_writes.tsv`, `provenance_writes.tsv`, and `row_snapshots.tsv` to walk backward from these rows. The writer PC and complete state tuple are recorded on every transition."]
    out.write_text("\n".join(lines)+"\n")
    print(out)
    print(f"marker={mf} recent_writes={len(recent)} implicated_rows={len(implicated)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
