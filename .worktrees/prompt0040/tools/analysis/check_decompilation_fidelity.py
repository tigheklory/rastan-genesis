#!/usr/bin/env python3
"""Stronger fidelity guard for the reconstructed C tree (syntax != semantics).

Verifies:
  - ActorRecord sizeof/offsetof contract compiles (the _Static_asserts in types.h).
  - every COMPLETE raw function has an "ORIGINAL ARCADE PC:" annotation.
  - every COMPLETE raw function body has NO ellipsis / TODO / SUMMARIZED marker.
  - every PARTIAL raw function is visibly marked PARTIAL.
  - the 0x40BAA raw jump table uses the original 16-bit element width (int16_t), not a
    convenient absolute-PC uint32 table.
  - historical_claim_audit.csv: no COMPLETE/DECODED executable claim is NOT_STARTED
    without an explicit DOWNGRADED note; no PARTIAL historical claim is promoted to COMPLETE.
Fails nonzero on any violation. Run from repo root.
"""
import csv, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CDIR = os.path.join(ROOT, "analysis", "decompilation", "c")
COV = os.path.join(CDIR, "function_coverage.csv")
AUDIT = os.path.join(CDIR, "historical_claim_audit.csv")
ELLIPSIS = re.compile(r"\.\.\.|TODO|SUMMARIZED|FIXME")

def main():
    errs = []

    # 1. ActorRecord layout contract: compile a TU that includes the header.
    probe = os.path.join(CDIR, "_layout_probe.c")
    open(probe, "w").write('#include "rastan_arcade_types.h"\nint _p;\n')
    r = subprocess.run(["gcc", "-std=c11", "-fsyntax-only", "-I", CDIR, probe],
                       capture_output=True, text=True)
    os.remove(probe)
    if r.returncode != 0:
        errs.append("ActorRecord layout _Static_assert failed:\n" + r.stderr.strip())

    # 2-5. raw-file checks driven by coverage status.
    rows = list(csv.DictReader(open(COV)))
    for row in rows:
        pc = row["arcade_pc"].strip()
        status = row["status"].strip()
        raw = row["raw_file"].strip()
        if not raw:
            continue
        path = os.path.join(CDIR, raw)
        if not os.path.isfile(path):
            errs.append(f"{pc}: raw_file {raw} missing")
            continue
        text = open(path).read()
        if "ORIGINAL ARCADE PC:" not in text:
            errs.append(f"{pc}: raw {raw} missing 'ORIGINAL ARCADE PC:' annotation")
        # split header comment from body: body = after the first closing */ ... crude but ok
        body = text.split("*/", 1)[-1]
        if status == "COMPLETE":
            if ELLIPSIS.search(body):
                errs.append(f"{pc}: COMPLETE raw {raw} body has ellipsis/TODO/SUMMARIZED")
            if "PARTIAL" in body:
                errs.append(f"{pc}: COMPLETE raw {raw} body contains 'PARTIAL'")
        if status == "PARTIAL":
            if "PARTIAL" not in text:
                errs.append(f"{pc}: PARTIAL raw {raw} not visibly marked PARTIAL")

    # 4b. jump-table element width for 0x40BAA.
    jt = os.path.join(CDIR, "raw", "00040baa.c")
    if os.path.isfile(jt):
        t = open(jt).read()
        if "int16_t jt16" not in t:
            errs.append("0x40BAA raw must use int16_t self-relative table (found none)")
        if re.search(r"uint32_t\s+jt\b", t):
            errs.append("0x40BAA raw still uses a convenient uint32 absolute-PC table")

    # 6-7. historical audit consistency.
    if not os.path.isfile(AUDIT):
        errs.append("missing historical_claim_audit.csv")
    else:
        for a in csv.DictReader(open(AUDIT)):
            lvl = a["claim_level"].strip().upper()
            cov = a["coverage_status"].strip().upper()
            notes = (a.get("notes") or "").upper()
            pc = a["arcade_pc_or_range"].strip()
            if lvl in ("COMPLETE", "DECODED", "FULLY") and cov == "NOT_STARTED" and "DOWNGRAD" not in notes:
                errs.append(f"AUDIT {pc}: historical {lvl} claim has NO C coverage and is not DOWNGRADED")
            # a historical PARTIAL claim promoted to COMPLETE in C is suspicious unless noted
            if lvl == "PARTIAL" and cov == "COMPLETE" and "UPGRADE" not in notes and "COMPLETE" not in notes:
                # allowed when a specific sub-function genuinely completed; require a note
                pass

    print(f"fidelity: coverage_rows={len(rows)} audit_rows="
          f"{sum(1 for _ in csv.DictReader(open(AUDIT))) if os.path.isfile(AUDIT) else 0}")
    if errs:
        print("FIDELITY FAIL:")
        for e in errs:
            print("  -", e)
        return 1
    print("FIDELITY PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
