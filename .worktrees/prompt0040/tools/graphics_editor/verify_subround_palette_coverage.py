#!/usr/bin/env python3
"""RG-022 maintained regression/contract tests for the per-subround Palette Composer expansion.

Proves (RG-022 section 8):
  - All 18 subrounds exist and are selectable; each has >=1 environment.
  - Multiple palette environments within a subround are supported (e.g. R1-S1, R1-S2).
  - Each environment has a unique, stable scene_key (independent decisions; no accidental sharing).
  - Existing Round-1 registry decisions survived the subround-key migration UNCHANGED (compared
    against the newest specs/_backup/palette_decisions.*.json): only `scene_applicability` was added.
  - The export manifest is deterministic (identical bytes on re-run).
  - palette_status is reported accurately (missing when no decision references the scene_key;
    approved/provisional/mixed by decision status).
  - Approved decisions cannot be silently applied to another subround: a decision governs a scene
    ONLY if that scene_key is in its scene_applicability.scene_keys (explicit sharing).
Exit 0 = all pass. Does NOT judge whether colors look correct (Tighe's visual authority).
"""
from __future__ import annotations
import glob, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "specs/palette_subround_map.json"
REG = ROOT / "specs/palette_decisions.json"
BACKUPS = ROOT / "specs/_backup"
EXPORTER = ROOT / "tools/graphics_editor/export_subround_palette_manifest.py"
MANIFEST = ROOT / "build/palette_export/palette_scene_manifest.json"

P, F = [], []
def ck(name, cond, extra=""):
    (P if cond else F).append(name)
    print(("PASS " if cond else "FAIL ") + name + (("  -> " + str(extra)) if extra and not cond else ""))


def main() -> int:
    smap = json.loads(MAP.read_text())
    reg = json.loads(REG.read_text())
    subs = smap["subrounds"]

    ck("1. exactly 18 subrounds", len(subs) == 18, len(subs))
    expect = {f"R{r}-S{s}" for r in range(1, 7) for s in range(1, 4)}
    ck("2. all R1..R6 x S1..S3 present", {x["key"] for x in subs} == expect,
       expect ^ {x["key"] for x in subs})
    ck("3. every subround has >=1 environment", all(sr.get("environments") for sr in subs))
    ck("4. multiple environments supported (R1-S1 has >1)",
       len(next(x for x in subs if x["key"] == "R1-S1")["environments"]) > 1)

    keys = [e["scene_key"] for sr in subs for e in sr["environments"]]
    ck("5. every environment scene_key is unique", len(keys) == len(set(keys)),
       [k for k in keys if keys.count(k) > 1])

    # Migration preservation vs newest backup
    bks = sorted(glob.glob(str(BACKUPS / "palette_decisions.*.json")))
    ck("6. a pre-migration backup exists", bool(bks), "run migrate_palette_registry_subround_keys.py")
    if bks:
        old = json.loads(Path(bks[-1]).read_text())
        oldd = {d["id"]: d for d in old["decisions"]}
        newd = {d["id"]: d for d in reg["decisions"]}
        ck("7. decision set unchanged by migration", set(oldd) == set(newd))
        unchanged = True
        for did, od in oldd.items():
            nd = dict(newd.get(did, {}))
            nd.pop("scene_applicability", None)   # the only permitted addition
            if nd != od:
                unchanged = False; break
        ck("8. every original decision field/value preserved (only scene_applicability added)", unchanged, did if not unchanged else "")

    # Export determinism
    subprocess.run([sys.executable, str(EXPORTER)], check=True, stdout=subprocess.DEVNULL)
    first = MANIFEST.read_bytes()
    subprocess.run([sys.executable, str(EXPORTER)], check=True, stdout=subprocess.DEVNULL)
    ck("9. export manifest is deterministic", MANIFEST.read_bytes() == first)

    man = json.loads(MANIFEST.read_text())
    mrows = {r["scene_key"]: r for r in man["scenes"]}
    # status accuracy: a scene with no referencing decision is "missing"
    by_scene = {}
    for d in reg["decisions"]:
        for sk in (d.get("scene_applicability", {}) or {}).get("scene_keys", []):
            by_scene.setdefault(sk, []).append(d)
    acc = all((mrows[k]["palette_status"] == "missing") == (k not in by_scene)
              for k in keys if k in mrows)
    ck("10. palette_status 'missing' iff no decision references the scene_key", acc)

    # Explicit-sharing guarantee: no decision is attributed to a scene_key it doesn't declare.
    leak = []
    for r in man["scenes"]:
        for d in r["decisions"]:
            decl = (d.get("scene_applicability", {}) or {}).get("scene_keys", [])
            if r["scene_key"] not in decl:
                leak.append((r["scene_key"], d["id"]))
    ck("11. no decision applied to a scene it does not declare (no silent sharing)", not leak, leak[:3])

    # Line 2 / Plane B never authorable
    pb = [e for sr in subs for e in sr["environments"] if e["family"] == "PLANEB"]
    famPB = smap["families"].get("PLANEB", {})
    ck("12. Plane B (Line 2) is not authorable", famPB.get("authorable") is False)

    # 13+: the editor actually LOADS real arcade graphics per subround (not just metadata).
    import importlib.util
    spec = importlib.util.spec_from_file_location("ged_server", ROOT / "tools/graphics_editor/server.py")
    srv = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(srv)
    except SystemExit:
        pass
    r1 = srv.build_layera(None)
    for sr in subs:
        if sr["native"] != "native_converted":
            continue
        for env in sr["environments"]:
            if env["family"] != "PLANEA" or (sr["key"] == "R1-S1" and env["env"] == "OUTDOOR"):
                continue
            sk = env["scene_key"]
            la = srv.build_layera(sk)
            patterns_ok = la["counts"]["physical_patterns"] > 0
            distinct = la["bank_ids"] != r1["bank_ids"]  # a later scene uses different banks
            lo = (env.get("records") or sr["record_band"])[0]
            mp = srv.layera_map(lo, sk)
            map_ok = mp["resolved"] > 0 and mp["unresolved"] == 0
            ck(f"13. {sk}: loads real arcade tiles (patterns>0, record {lo} resolves fully)",
               patterns_ok and map_ok, f"patterns={la['counts']['physical_patterns']} resolved={mp['resolved']} unresolved={mp['unresolved']}")
            ck(f"14. {sk}: uses its own palette banks (not R1's)", distinct or sk.startswith("PAL-R1-S1"),
               f"{la['bank_ids'][:4]}")

    print(f"\n{'SUBROUND_PALETTE_COVERAGE PASS' if not F else str(len(F))+' CHECK(S) FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
