#!/usr/bin/env python3
"""RG-022 export contract: the stable, deterministic interface the native Genesis build consumes
to select per-subround/per-environment palettes.  (Cody implements runtime selection; this is the
data contract so Cody does not invent a competing schema.)

Inputs  (read-only): specs/palette_subround_map.json, specs/palette_decisions.json.
Output  (deterministic): build/palette_export/palette_scene_manifest.json

Manifest schema (v1), one row per environment scene_key:
  {
    "scene_key": "PAL-R1-S2-PLANEA-CASTLE",
    "round": 1, "subround": 2, "env": "CASTLE", "family": "PLANEA",
    "stage_index": 16, "record_band": [16,21],
    "authorable": true,                 # false for PLANEB (Line 2 reserved)
    "native_status": "native_converted",
    "mode": null,                        # mode_a / mode_b for unconverted rounds
    "palette_status": "missing|provisional|approved|mixed",
    "decisions": [ {id, status, genesis_lines, scene_applicability} ],
    "cram_lines": [0,1,3],               # authorable Genesis CRAM lines (Line 2 excluded)
    "cram_asset": null,                  # path to exported CRAM blob when approved (see note)
    "shared_from": null                  # set only when a decision is EXPLICITLY shared from another scene
  }
Rules the build must honor:
  - Line 2 (PLANEB) is arcade-controlled and never authored/overwritten.
  - palette_status=missing/provisional => the build keeps the existing arcade conversion for that
    scene and does NOT apply a Composer palette (no silent substitution).
  - A decision applies to a scene only if that scene_key is in its scene_applicability.scene_keys
    (explicit; cross-round sharing requires the target scene_key to be listed, never inferred).
Deterministic: stable key order; no timestamps; identical inputs -> identical bytes.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "specs/palette_subround_map.json"
REG = ROOT / "specs/palette_decisions.json"
OUT = ROOT / "build/palette_export/palette_scene_manifest.json"


def main() -> int:
    smap = json.loads(MAP.read_text())
    reg = json.loads(REG.read_text())
    fams = smap["families"]

    # index decisions by the scene_keys they declare applicability for
    by_scene: dict[str, list] = {}
    for dec in reg["decisions"]:
        app = dec.get("scene_applicability", {}) or {}
        for sk in app.get("scene_keys", []):
            by_scene.setdefault(sk, []).append(dec)

    rows = []
    for sr in smap["subrounds"]:
        for env in sr["environments"]:
            fam = env["family"]
            sk = env["scene_key"]
            fam_meta = fams.get(fam, {})
            decs = sorted(by_scene.get(sk, []), key=lambda d: d["id"])
            statuses = {d.get("status") for d in decs}
            if not decs:
                pstat = "missing"
            elif statuses <= {"approved", "proven", "decided"}:
                pstat = "approved"
            elif statuses <= {"provisional", "unknown"}:
                pstat = "provisional"
            else:
                pstat = "mixed"
            rows.append({
                "scene_key": sk,
                "round": sr["round"], "subround": sr["subround"], "env": env["env"], "family": fam,
                "stage_index": sr["stage_index"], "record_band": env.get("records", sr["record_band"]),
                "authorable": bool(fam_meta.get("authorable")),
                "native_status": sr["native"], "mode": sr.get("mode"),
                "palette_status": pstat,
                "decisions": [{"id": d["id"], "status": d.get("status"),
                               "genesis_lines": fam_meta.get("genesis_lines", []),
                               "scene_applicability": d.get("scene_applicability", {})} for d in decs],
                "cram_lines": fam_meta.get("genesis_lines", []),
                "cram_asset": None,
                "shared_from": None,
            })

    rows.sort(key=lambda r: r["scene_key"])
    manifest = {
        "schema": "rastan-palette-scene-manifest/v1",
        "source_map": "specs/palette_subround_map.json",
        "source_registry": "specs/palette_decisions.json",
        "reserved_line": {"line": 2, "owner": "arcade Plane B", "authorable": False},
        "contract_rules": [
            "Line 2 is never authored/overwritten.",
            "palette_status in {missing,provisional}: build keeps arcade conversion; no Composer substitution.",
            "A decision applies to a scene only if the scene_key is in its scene_applicability.",
            "Deterministic: identical inputs produce identical bytes.",
        ],
        "scenes": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=1, sort_keys=False) + "\n")
    approved = sum(1 for r in rows if r["palette_status"] == "approved")
    prov = sum(1 for r in rows if r["palette_status"] == "provisional")
    missing = sum(1 for r in rows if r["palette_status"] == "missing")
    print(f"PALETTE_SCENE_MANIFEST_OK scenes={len(rows)} approved={approved} "
          f"provisional={prov} missing={missing} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
