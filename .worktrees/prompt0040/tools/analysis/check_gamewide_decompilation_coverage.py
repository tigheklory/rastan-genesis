#!/usr/bin/env python3
"""Game-wide 68000 decompilation coverage guard (H20).
Verifies the generated census is internally consistent and honest. Run from repo root."""
import os, csv, json, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INV = os.path.join(ROOT,"analysis/decompilation/gamewide_function_inventory.csv")
SUB = os.path.join(ROOT,"analysis/decompilation/gamewide_subsystem_coverage.csv")
SUM = os.path.join(ROOT,"analysis/decompilation/gamewide_coverage_summary.json")
COV = os.path.join(ROOT,"analysis/decompilation/c/function_coverage.csv")
GHI = os.path.join(ROOT,"analysis/ghidra/rastan_arcade/exports/function_inventory.tsv")

def fail(m): print("GAME-WIDE COVERAGE GUARD: FAIL -",m); sys.exit(1)

inv=list(csv.DictReader(open(INV)))
sub=list(csv.DictReader(open(SUB)))
summ=json.load(open(SUM))
n_ghidra=sum(1 for _ in open(GHI))-1

# 1. every Ghidra function is classified (present in inventory)
if len(inv)!=n_ghidra: fail(f"inventory {len(inv)} != Ghidra {n_ghidra} functions")
# 2. no duplicate primary owner (each function one row / one subsystem)
pcs=[r["pc"] for r in inv]
if len(pcs)!=len(set(pcs)): fail("duplicate function PC (double-counted)")
for r in inv:
    if r["subsystem"] not in {x["subsystem"] for x in sub}: fail("unknown subsystem "+r["subsystem"])
    if r["status"] not in ("COMPLETE","PARTIAL","STUB","NOT_DECOMPILED"): fail("bad status "+r["status"])
# 3. subsystem byte totals equal game-wide totals (no negative/overlap double count in the per-func sum)
tot_bytes=sum(int(r["span_bytes"]) for r in inv)
sub_bytes=sum(int(r["total_code_bytes"]) for r in sub)
if tot_bytes!=sub_bytes: fail(f"subsystem bytes {sub_bytes} != inventory span sum {tot_bytes}")
if tot_bytes!=summ["total_code_bytes_spansum"]: fail("summary spansum mismatch")
# 4. per-status byte partition sums to total
part=sum(int(r["complete_code_bytes"])+int(r["partial_code_bytes"])+int(r["stub_code_bytes"])+int(r["not_decompiled_code_bytes"]) for r in sub)
if part!=tot_bytes: fail("status byte partition != total")
# 5. percentage arithmetic
c=summ["complete_code_bytes"]
exp=round(100.0*c/tot_bytes,1)
if abs(exp-summ["overall_fully_decompiled_pct"])>0.05: fail("overall pct arithmetic")
# 6. COMPLETE functions satisfy durable-C evidence (entry is a COMPLETE row in the tracker with raw+semantic files)
covc={}
for r in csv.DictReader(open(COV)):
    covc[int(r["arcade_pc"],16)]=(r["status"].strip(), (r["raw_file"] or "").strip(), (r["semantic_file"] or "").strip())
for r in inv:
    if r["status"]=="COMPLETE":
        pc=int(r["pc"],16); bmin=int(r["body_min"],16)
        rec=covc.get(pc) or covc.get(bmin)
        if not rec or rec[0]!="COMPLETE": fail(f"COMPLETE func {r['pc']} not COMPLETE in tracker")
        if not rec[1] or not rec[2]: fail(f"COMPLETE func {r['pc']} missing raw/semantic durable-C artifact")
# 7. NOT_DECOMPILED remain visible (present and counted)
nd=sum(1 for r in inv if r["status"]=="NOT_DECOMPILED")
if nd!=summ["not_decompiled_functions"]: fail("NOT_DECOMPILED count mismatch")
if nd==0: fail("no NOT_DECOMPILED functions -> denominator suspiciously complete")
print(f"GAME-WIDE COVERAGE GUARD: PASS  ({len(inv)} funcs, {tot_bytes} code bytes, "
      f"fully={summ['overall_fully_decompiled_pct']}%, touched={summ['overall_touched_pct']}%, "
      f"NOT_DECOMPILED={nd})")
