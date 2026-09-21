#!/usr/bin/env python3
"""Guard: every actor function claimed COMPLETE must have a raw .c and a semantic .c
artifact; every H5 handler PC must be covered. Fails nonzero otherwise.

This guard exists because the decompilation process failed once by letting Markdown
"complete" claims run ahead of preserved C source. Run from repo root.
"""
import csv, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CDIR = os.path.join(ROOT, "analysis", "decompilation", "c")
CSV_PATH = os.path.join(CDIR, "function_coverage.csv")

# The ten H5 dedicated-state handler PCs (0x40BAA states 0x13..0x22).
H5_PCS = {"0004375c", "00043840", "00043ae6", "00043f88", "00044082",
          "0004396a", "00043b32", "00043ecc", "0004415a", "00043636"}

def main():
    errors = []
    if not os.path.isfile(CSV_PATH):
        print("FAIL: missing", CSV_PATH); return 1
    rows = list(csv.DictReader(open(CSV_PATH)))
    seen = set()
    for r in rows:
        pc = (r["arcade_pc"] or "").strip().lower()
        seen.add(pc)
        status = (r["status"] or "").strip()
        raw = (r["raw_file"] or "").strip()
        sem = (r["semantic_file"] or "").strip()
        if status == "COMPLETE":
            if not raw:
                errors.append(f"{pc}: COMPLETE but no raw_file")
            elif not os.path.isfile(os.path.join(CDIR, raw)):
                errors.append(f"{pc}: raw_file '{raw}' missing on disk")
            if not sem:
                errors.append(f"{pc}: COMPLETE but no semantic_file")
            elif not os.path.isfile(os.path.join(CDIR, sem)):
                errors.append(f"{pc}: semantic_file '{sem}' missing on disk")
    # H5: every handler PC must be present, and must have raw + semantic artifacts.
    for pc in sorted(H5_PCS):
        if pc not in seen:
            errors.append(f"H5 handler {pc}: no coverage row")
            continue
        r = next(x for x in rows if x["arcade_pc"].strip().lower() == pc)
        raw = (r["raw_file"] or "").strip(); sem = (r["semantic_file"] or "").strip()
        if not (raw and os.path.isfile(os.path.join(CDIR, raw))):
            errors.append(f"H5 handler {pc}: missing raw .c artifact")
        if not (sem and os.path.isfile(os.path.join(CDIR, sem))):
            errors.append(f"H5 handler {pc}: missing semantic .c artifact")

    # Historical audit: an old COMPLETE/DECODED executable-code claim must have C
    # coverage or an explicit DOWNGRADED note. (This is why the process failed once.)
    audit_path = os.path.join(CDIR, "historical_claim_audit.csv")
    audit_rows = 0
    if os.path.isfile(audit_path):
        for a in csv.DictReader(open(audit_path)):
            audit_rows += 1
            lvl = (a.get("claim_level") or "").strip().upper()
            cov = (a.get("coverage_status") or "").strip().upper()
            notes = (a.get("notes") or "").upper()
            if lvl in ("COMPLETE", "DECODED", "FULLY") and cov in ("NOT_STARTED", ""):
                if "DOWNGRAD" not in notes:
                    errors.append(f"AUDIT {a['arcade_pc_or_range']}: old {lvl} claim "
                                  f"has no C coverage and is not DOWNGRADED")
    else:
        errors.append("missing historical_claim_audit.csv")

    total = len(rows)
    complete = sum(1 for r in rows if r["status"].strip() == "COMPLETE")
    partial = sum(1 for r in rows if r["status"].strip() == "PARTIAL")
    stub = sum(1 for r in rows if r["status"].strip() == "STUB_ONLY")
    print(f"coverage rows={total} COMPLETE={complete} PARTIAL={partial} STUB_ONLY={stub}")
    print(f"historical audit rows={audit_rows}")
    print(f"H5 handler PCs covered={len(H5_PCS & seen)}/10")
    if errors:
        print("GUARD FAIL:")
        for e in errors:
            print("  -", e)
        return 1
    print("GUARD PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
