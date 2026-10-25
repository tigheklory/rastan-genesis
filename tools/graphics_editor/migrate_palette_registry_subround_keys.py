#!/usr/bin/env python3
"""RG-022 safe migration: add authentic subround `scene_applicability` keys to the palette
registry WITHOUT altering any existing decision content, status, or approval.

`specs/palette_decisions.json` stays the sole palette-decision registry (CLAUDE.md). This migration:
  1. Backs up the registry to specs/_backup/palette_decisions.<utc>.json.
  2. Adds, to each decision, an additive `scene_applicability` list of subround scene_keys
     (from specs/palette_subround_map.json) describing which scenes the decision governs.
     Nothing else changes: id/status/context/arcade_semantics/genesis_realization/evidence are
     byte-identical.
  3. Bumps schema_version to 2 and records the key scheme.
  4. Self-verifies: every original decision field/value is preserved; only `scene_applicability`
     (and the top-level schema bump) is added. Deterministic; re-running is idempotent.

Run from repo root:  python3 -I tools/graphics_editor/migrate_palette_registry_subround_keys.py
"""
from __future__ import annotations
import copy, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "specs/palette_decisions.json"
BACKUP_DIR = ROOT / "specs/_backup"

# Deterministic classification of the existing R1 decisions -> authentic scene_applicability.
# These are all Stage-1 gameplay PC090OJ (or frontend) decisions today; we stamp their proven
# authored scope. Cross-scene candidates are marked for EXPLICIT sharing (never auto-applied).
def applicability(dec: dict) -> dict:
    did = dec["id"]
    scene = (dec.get("context", {}) or {}).get("scene", "") or ""
    s = scene.lower()
    if "frontend" in s or "scene 0" in s or did.startswith("PAL-FRONTEND"):
        return {"scene_keys": ["FRONTEND"], "cross_scene_candidate": False}
    # PC090OJ sprite families authored in Stage-1 gameplay:
    keys = ["PAL-R1-S1-PC090OJ"]
    # "all scenes" / HUD / generic-death entries are legitimate cross-round SHARE CANDIDATES,
    # surfaced for explicit opt-in sharing by Tighe -- never auto-applied to another subround.
    cross = ("all scenes" in s) or ("hud" in s) or ("death" in did.lower()) or ("attract" in s)
    return {"scene_keys": keys, "cross_scene_candidate": bool(cross)}


def main() -> int:
    reg = json.loads(REG.read_text())
    original = copy.deepcopy(reg)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup = BACKUP_DIR / f"palette_decisions.{stamp}.json"
    backup.write_text(json.dumps(original, indent=1) + "\n")

    for dec in reg["decisions"]:
        # Idempotent: only add if missing; never overwrite an existing (possibly edited) value.
        dec.setdefault("scene_applicability", applicability(dec))

    reg["schema_version"] = 2
    reg["subround_key_scheme"] = {
        "doc": "scene_applicability.scene_keys reference specs/palette_subround_map.json scene_keys.",
        "map": "specs/palette_subround_map.json",
        "added_by": "RG-022 migrate_palette_registry_subround_keys.py",
    }

    # ---- self-verification / regression guard: nothing existing may change ----
    def without_added(d: dict) -> dict:
        d = copy.deepcopy(d)
        d.pop("schema_version", None)
        d.pop("subround_key_scheme", None)
        for x in d.get("decisions", []):
            x.pop("scene_applicability", None)
        return d

    ob = copy.deepcopy(original); ob.pop("schema_version", None)
    if without_added(reg) != ob:
        raise SystemExit("MIGRATION ABORTED: an existing field/value would change (only additive "
                         "scene_applicability + schema bump are allowed).")
    if len(reg["decisions"]) != len(original["decisions"]):
        raise SystemExit("MIGRATION ABORTED: decision count changed.")

    REG.write_text(json.dumps(reg, indent=1) + "\n")
    print(f"PALETTE_REGISTRY_MIGRATION_OK backup={backup.name} decisions={len(reg['decisions'])} "
          f"schema_version={reg['schema_version']}")
    for dec in reg["decisions"]:
        a = dec["scene_applicability"]
        print(f"  {dec['id'][:46]:46} -> {a['scene_keys']} share_candidate={a['cross_scene_candidate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
