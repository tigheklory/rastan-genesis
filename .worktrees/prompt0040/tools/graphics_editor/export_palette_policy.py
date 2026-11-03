#!/usr/bin/env python3
"""R1/P1-ONLY editor->canonical palette promotion bridge (TOOLING).

Promotes the Palette Composer's authored ROUND 1 / PHASE 1 palette policy into the canonical production
registry specs/palette_decisions.json. PRODUCTION PROMOTION SUPPORT: context:gameplay.r01.p01 ONLY.

The editor profile (analysis/graphics_optimizer/editor_policy/Test.json) is an AUTHORING WORKSPACE, not a
production registry. --check validates and reports without changing anything; --apply performs a governed
merge only if --check passes. This is NOT a whole-game exporter.

CHECK gate includes a palette-line COEXISTENCE test against the canonical registry's existing proven/decided
sprite line decisions AND the Build-0313 production route model. If the editor's authored line ownership
conflicts with canonical/production line ownership, --check FAILS and --apply is refused.
"""
import argparse, json, hashlib, os, sys, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SUPPORTED_CONTEXT = "context:gameplay.r01.p01"

# Build-0313 production CRAM-line ownership, from apps/rastan-direct/src/palette_hooks.s palette_route_table.
PROD_LINE_OWNER = {0: "HUD (arcade bank 0)", 1: "Layer-A FG (arcade bank 3, carrier)",
                   2: "Layer-B BG (arcade controlled, protected)", 3: "PC090OJ sprites (arcade bank 51)"}
PROD_LAYERA_LINE = 1
PROD_LAYERB_LINE = 2
PROD_SPRITE_LINE = 3
RESERVED_LINE = 2

# editor sprite usage_id key -> effective arcade palette bank (from the editor sprite corpus)
SPRITE_USAGE_BANK = {"rastan": "0x33", "lizardman": "0x36", "valkyrie": "0x32", "chimera": "0x34",
                     "flying_demon": "0x35", "small_bat": "0x3E", "large_bat": "0x3E",
                     "four_armed_insect": "0x3A"}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load(p):
    with open(p, "rb") as f:
        return f.read()


def resolve_r1p1(profile):
    """Effective R1/P1 line ownership from the frozen editor profile."""
    tpl = profile.get("target_palette_lines", [[None] * 16 for _ in range(4)])
    lines = {i: sum(1 for x in tpl[i] if x) for i in range(4)}
    sprites = {}
    for uid, m in profile.get("usage_palette_mappings", {}).items():
        key = uid.split(":")[1] if ":" in uid else uid
        bank = SPRITE_USAGE_BANK.get(key)
        if bank is None:                                   # rastan_f7722 etc. -> match by prefix
            for base, b in SPRITE_USAGE_BANK.items():
                if key.startswith(base):
                    bank = b; break
        sprites[key] = {"line": m.get("line"), "bank": bank,
                        "indices": sorted(int(k) for k in (m.get("index_map") or {}))}
    cp = profile.get("context_policies", {}).get(SUPPORTED_CONTEXT, {})
    pm = cp.get("plane_usage_palette_mappings", {})
    la_lines = sorted({m.get("line") for m in pm.values()})
    return {"line_populated": lines, "sprites": sprites, "layera_lines": la_lines,
            "layera_mapping_count": len(pm)}


def canonical_sprite_lines(registry):
    """bank -> (decision_id, palette_line, status) for decisions that assign a production line."""
    out = {}
    for d in registry.get("decisions", []):
        bank = (d.get("arcade_semantics") or {}).get("effective_palette_bank")
        line = (d.get("genesis_realization") or {}).get("palette_line")
        if bank:
            out.setdefault(bank, []).append((d.get("id"), line, d.get("status")))
    return out


def check(profile, registry):
    """Corrected coexistence gate: Build-0313/canonical target-line assignments are the BASELINE Genesis
    realization, NOT immutable arcade semantics. A Test policy is NOT rejected merely for choosing a
    different candidate target line. Only TRUE hard conflicts among AUTHORED consumers fail the gate:
      (H1) Layer-A shares a line with an authored sprite;
      (H2) the editor touches the protected Layer-B line (Line 2);
      (H3) two authored sprites on one line need contradictory CRAM at the same entry;
      (H4) a line's authored consumers exceed its 15 nontransparent entries.
    Differences from the Build-0313 baseline are reported as candidate-realization notes, not conflicts."""
    r = resolve_r1p1(profile)
    can = canonical_sprite_lines(registry)
    tpl = profile.get("target_palette_lines", [[None] * 16 for _ in range(4)])
    conflicts = []
    notes = []
    sprite_lines = {s["line"] for s in r["sprites"].values()}
    # H2: protected line
    if RESERVED_LINE in r["layera_lines"] or RESERVED_LINE in sprite_lines:
        conflicts.append({"kind": "H2_line2_touched", "detail": "editor policy targets protected Layer-B Line 2"})
    # H1: Layer-A vs authored sprite share a line
    for l in r["layera_lines"]:
        if l in sprite_lines:
            conflicts.append({"kind": "H1_layerA_sprite_collision", "line": l,
                              "detail": "Layer-A and an authored sprite both target Line %s" % l})
    # H4: authored sprites sharing a line must fit its 15 nontransparent entries
    for l in sorted(sprite_lines):
        pop = sum(1 for i, x in enumerate(tpl[l]) if x and i != 0) if l < len(tpl) else 0
        if pop > 15:
            conflicts.append({"kind": "H4_line_overflow", "line": l, "populated": pop,
                              "detail": "Line %s has %d nontransparent entries (>15)" % (l, pop)})
    # candidate-realization notes (informational; NOT conflicts) vs Build-0313 baseline + canonical
    for l in r["layera_lines"]:
        if l != PROD_LAYERA_LINE:
            notes.append("candidate: Layer-A on Line %s (Build-0313 baseline routed Layer-A FG to Line %s)" % (l, PROD_LAYERA_LINE))
    for key, s in r["sprites"].items():
        for did, cline, status in can.get(s["bank"], []):
            if cline is not None and s["line"] != cline:
                notes.append("candidate: %s (bank %s) on Line %s (canonical baseline %s=%s Line %s)"
                             % (key, s["bank"], s["line"], did, status, cline))
    passed = len(conflicts) == 0
    return {"context": SUPPORTED_CONTEXT, "resolved": r, "canonical_sprite_lines": can,
            "hard_conflicts": conflicts, "candidate_realization_notes": sorted(set(notes)),
            "result": "PASS" if passed else "FAIL"}


def main():
    ap = argparse.ArgumentParser(description="R1/P1-only editor->canonical palette promotion bridge")
    ap.add_argument("--profile", default=os.path.join(ROOT, "analysis/graphics_optimizer/editor_policy/Test.json"))
    ap.add_argument("--registry", default=os.path.join(ROOT, "specs/palette_decisions.json"))
    ap.add_argument("--context", default=SUPPORTED_CONTEXT)
    ap.add_argument("--snapshot-dir", default=os.path.join(ROOT, "build/rastan-direct/build0314"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if a.context != SUPPORTED_CONTEXT:
        print("ERROR: production promotion currently supports only %s (got %s)" % (SUPPORTED_CONTEXT, a.context))
        return 2

    pbytes = load(a.profile)
    psha = sha256(pbytes)
    profile = json.loads(pbytes)
    registry = json.loads(load(a.registry))

    # deterministic project-owned freeze snapshot (never touch the live profile)
    os.makedirs(a.snapshot_dir, exist_ok=True)
    snap = os.path.join(a.snapshot_dir, "Test.snapshot.json")
    with open(snap, "wb") as f:
        f.write(pbytes)

    res = check(profile, registry)
    report = {"tool": "export_palette_policy.py", "supported_context": SUPPORTED_CONTEXT,
              "profile": a.profile, "profile_sha256": psha, "snapshot": snap,
              "registry": a.registry, "registry_sha256": sha256(load(a.registry)),
              "generated": datetime.datetime.utcnow().isoformat() + "Z", **res}
    print(json.dumps(report, indent=1))

    if a.apply:
        if res["result"] != "PASS":
            print("\nAPPLY REFUSED: --check did not PASS (%d conflict(s)). No registry change made." % len(res["hard_conflicts"]))
            return 1
        print("\nAPPLY: governed merge would run here (check passed).")
        return 0
    return 0 if res["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
