#!/usr/bin/env python3
"""Canonical pattern-reuse resolver (TOOLING, normal build stage).

Consumes specs/pattern_reuse_policy.json and resolves every APPROVED reference-substitution against the
real R1/P1 plane-A usage inventory. Emits a resolved (code,bank)->(code,bank) substitution table that the
faithful offline (code,bank) target-pattern compiler applies BEFORE dedup/residency, plus the policy SHA
for build provenance.

This is a pure validating transform of the canonical policy. It never edits arcade authority, never touches
pixels/palettes/index maps, and never runs at runtime. A matching approved entry rewrites one tile REFERENCE
to an existing tile; anything without an entry passes through unchanged.

Hard failure (nonzero exit) if:
  - any approved entry's original (code,bank) is not a real use in its declared segment/record,
  - any approved entry's replacement (code,bank) is not a real existing use,
  - any approved entry is left unresolved.
The build must treat those as fatal so a stale/incorrect policy can never silently ship.
"""
import argparse, hashlib, json, os, sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_uses(path):
    """Map (code,bank) -> set(records) over every plane-A use."""
    uses = json.load(open(path))
    by_key = defaultdict(set)
    for u in uses:
        by_key[(int(u["tile_code"]), int(u["palette_bank"]))].update(int(r) for r in u["records"])
    return by_key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=os.path.join(ROOT, "specs/pattern_reuse_policy.json"))
    ap.add_argument("--uses", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1/plane_a_uses.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build/regions/pattern_reuse_resolved.json"))
    a = ap.parse_args()

    raw = open(a.policy, "rb").read()
    policy = json.loads(raw)
    policy_sha = hashlib.sha256(raw).hexdigest()
    by_key = load_uses(a.uses)

    def h(v):
        return int(v, 0) if isinstance(v, str) else int(v)

    resolved, errors = [], []
    approved = [e for e in policy["entries"] if e.get("status") == "approved"]
    for e in approved:
        seg = int(e["segment"])
        oc, ob = h(e["original_code"]), h(e["original_bank"])
        rc, rb = h(e["replacement_code"]), h(e["replacement_bank"])
        if seg not in by_key.get((oc, ob), set()):
            errors.append("original (code=0x%03X,bank=0x%03X) not a use in segment %d" % (oc, ob, seg))
            continue
        if (rc, rb) not in by_key:
            errors.append("replacement (code=0x%03X,bank=0x%03X) is not an existing use" % (rc, rb))
            continue
        resolved.append({"domain": e["domain"], "round": e["round"], "phase": e["phase"],
                         "segment": seg, "from": [oc, ob], "to": [rc, rb]})

    unresolved = len(approved) - len(resolved)
    if errors or unresolved:
        for m in errors:
            sys.stderr.write("pattern-reuse policy ERROR: %s\n" % m)
        sys.stderr.write("pattern-reuse policy FAILED: %d approved, %d resolved, %d unresolved\n"
                         % (len(approved), len(resolved), unresolved))
        sys.exit(1)

    out = {"policy_sha256": policy_sha, "schema_version": policy["schema_version"],
           "approved_count": len(approved), "resolved_count": len(resolved),
           "unresolved_count": 0, "substitutions": resolved}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("pattern-reuse policy OK: %d approved entries resolved (0 unresolved); policy_sha=%s"
          % (len(resolved), policy_sha[:16]))
    print("  contexts: %s" % ", ".join(sorted({"r%dp%d seg%d" % (r["round"], r["phase"], r["segment"])
                                                for r in resolved})))
    print("  wrote %s" % os.path.relpath(a.out, ROOT))


if __name__ == "__main__":
    main()
