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
import argparse, json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "specs/palette_subround_map.json"
REG = ROOT / "specs/palette_decisions.json"
OUT = ROOT / "build/palette_export/palette_scene_manifest.json"
CRAM_DIR = ROOT / "build/palette_export/cram"
ORACLE = ROOT / "analysis/graphics_optimizer/arcade_graphics_oracle/contexts.json"
POLICY_DIR = ROOT / "analysis/graphics_optimizer/editor_policy"
AUTHORABLE_LINES = (0, 1, 3)   # Line 2 is reserved (arcade Plane B) and never exported

# scene_key -> editing context id (R1-S1 outdoor authors on the existing r01.p01 context)
def scene_context(scene_key):
    return "context:gameplay.r01.p01" if scene_key == "PAL-R1-S1-PLANEA-OUTDOOR" else scene_key

def _ctx_chain(contexts, cid):
    by = {c["id"]: c for c in contexts}
    out = []; c = by.get(cid)
    while c:
        out.insert(0, c); c = by.get(c["parent"]) if c.get("parent") else None
    return out

def _eff_cram(pol, contexts, scope, line, i):
    tpl = pol.get("target_palette_lines") or [[None]*16]*4
    cram = tpl[line][i] if line < len(tpl) and i < len(tpl[line]) else None
    for c in _ctx_chain(contexts, scope):
        t = (pol.get("context_policies", {}).get(c["id"]) or {}).get("tpl", {}).get(str(line))
        if t and str(i) in t:
            cram = t[str(i)]
    return cram

def full_contexts(smap):
    """The raw oracle contexts PLUS the subround scene contexts (mirrors server build_oracle), so the
    exporter resolves per-scene overrides exactly as the editor does."""
    base = json.loads(ORACLE.read_text()).get("contexts", []) if ORACLE.is_file() else []
    ids = {c["id"] for c in base}
    extra = []
    for sr in smap.get("subrounds", []):
        for env in sr.get("environments", []):
            if env.get("family") != "PLANEA":
                continue
            sk = env["scene_key"]
            if sk == "PAL-R1-S1-PLANEA-OUTDOOR" or sk in ids:
                continue
            parent = "context:gameplay.r01.p01" if sr["key"] == "R1-S1" else "context:gameplay"
            extra.append({"id": sk, "parent": parent})
    return base + extra

def _emit_cram(scene_key, pol, contexts):
    """Write build/palette_export/cram/<scene_key>.bin, ONLY when the scene has its OWN authored
    lines (context_policies[scope].tpl non-empty) — never from inherited/shared base alone, so one
    scene's palette is never substituted for another. Returns the relative path, or None (arcade
    fallback). Format: lines {0,1,3} x 16 big-endian CRAM words (unauthored entry -> 0x0000)."""
    scope = scene_context(scene_key)
    own = (pol.get("context_policies", {}).get(scope) or {}).get("tpl") or {}
    if not any(own.get(str(l)) for l in AUTHORABLE_LINES):
        return None
    words = []
    for line in AUTHORABLE_LINES:
        for i in range(16):
            v = _eff_cram(pol, contexts, scope, line, i)
            words.append(int(v, 16) & 0xFFFF if v is not None else 0)
    CRAM_DIR.mkdir(parents=True, exist_ok=True)
    (CRAM_DIR / f"{scene_key}.bin").write_bytes(b"".join(struct.pack(">H", w) for w in words))
    return f"build/palette_export/cram/{scene_key}.bin"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=None,
                    help="editor_policy profile id whose authored per-scene Lines 0/1/3 become CRAM blobs")
    args = ap.parse_args()
    smap = json.loads(MAP.read_text())
    reg = json.loads(REG.read_text())
    fams = smap["families"]

    pol = None
    contexts = []
    if args.profile:
        pfile = POLICY_DIR / f"{args.profile}.json"
        if pfile.is_file():
            pol = json.loads(pfile.read_text())
            contexts = full_contexts(smap)

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
                "cram_asset": (_emit_cram(sk, pol, contexts) if (pol is not None and fam_meta.get("authorable")) else None),
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
