#!/usr/bin/env python3
"""PROMPT-ID-0009 regression: scene-specific Layer-A auto-map targets ONLY the selected scene.

Proven through the REAL in-process server + /api/phase_automap + /api/policy round-trip, mirroring the
client apply exactly (fill unmapped into context_policies[scene].plane_usage_palette_mappings):

  A  R1-S2 auto-map echoes scene=PAL-R1-S2-PLANEA-CASTLE and its proposals are R1-S2 corpus usages.
  B  R2-S2 auto-map echoes its own scene; proposals are R2-S2 corpus usages (not R1-S2, not R1/P1).
  C  Applying + save + reload stores mappings under the scene context; R1-S1 (r01.p01) is byte-identical.
  E  Unknown scene / corpus-less scene / Line 2 / invalid scene all FAIL (no R1/P1 substitution).
  F  scene=None (R1/P1 phase) still works and differs from the subround corpus.

Not covered (browser): DOM confirm dialog text, Undo/Redo UI, stale-async abort — manual steps in report.
"""
from __future__ import annotations
import importlib.util, json, threading, time, urllib.request, urllib.error, copy
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P, F = [], []
def ck(n, c, extra=""):
    (P if c else F).append(n); print(("PASS " if c else "FAIL ") + n + ((" -> " + str(extra)) if extra and not c else ""))

CASTLE1 = "PAL-R1-S2-PLANEA-CASTLE"
CASTLE2 = "PAL-R2-S2-PLANEA-CASTLE"
R1S1 = "context:gameplay.r01.p01"
LINE = 3
COLORS = [None] + ["0x0%03X" % (0x111 + k) for k in range(15)]   # 15 populated Line-3 colors


def main() -> int:
    spec = importlib.util.spec_from_file_location("ged_server", ROOT / "tools/graphics_editor/server.py")
    srv = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(srv)
    except SystemExit: pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Hd); port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.3)
    base = f"http://127.0.0.1:{port}"
    def g(u): return json.load(urllib.request.urlopen(base + u))
    def post(u, obj):
        req = urllib.request.Request(base + u, data=json.dumps(obj).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try: return json.load(urllib.request.urlopen(req)), 200
        except urllib.error.HTTPError as e: return json.load(e), e.code

    # corpus usage-id sets per scene (authoritative: the server's own build_layera)
    def usage_ids(scene):
        return {u["usage_id"] for u in srv.build_layera(scene)["usages"]}
    c1_ids, c2_ids, r1p1_ids = usage_ids(CASTLE1), usage_ids(CASTLE2), usage_ids(None)

    # --- A: R1-S2 auto-map is scene-identified and uses R1-S2 corpus ---
    a, code = post("/api/phase_automap", {"line": LINE, "target_colors": COLORS, "scene": CASTLE1})
    ck("A1. R1-S2 auto-map returns 200", code == 200, (code, a))
    ck("A2. response echoes scene=PAL-R1-S2-PLANEA-CASTLE", a.get("scene") == CASTLE1, a.get("scene"))
    prop_ids = {p["usage_id"] for p in a.get("proposals", [])}
    ck("A3. proposals are drawn from the R1-S2 corpus", prop_ids and prop_ids <= c1_ids, len(prop_ids))

    # --- F: R1/P1 phase corpus (scene=None) works and differs from the subround corpus ---
    f, fc = post("/api/phase_automap", {"line": LINE, "target_colors": COLORS, "scene": None})
    ck("F1. scene=None (R1/P1 phase) returns 200 with scene null", fc == 200 and f.get("scene") is None, f.get("scene"))
    fp = {p["usage_id"] for p in f.get("proposals", [])}
    ck("F2. R1/P1 proposals come from R1/P1 corpus and differ from R1-S2",
       fp and fp <= r1p1_ids and fp != prop_ids, (len(fp), len(prop_ids)))

    # --- B: R2-S2 is its own scene ---
    b, bc = post("/api/phase_automap", {"line": LINE, "target_colors": COLORS, "scene": CASTLE2})
    bp = {p["usage_id"] for p in b.get("proposals", [])}
    ck("B1. R2-S2 echoes its own scene", bc == 200 and b.get("scene") == CASTLE2, b.get("scene"))
    ck("B2. R2-S2 proposals come from R2-S2 corpus", bp and bp <= c2_ids, len(bp))

    # --- E: failures never fall back to R1/P1 ---
    _, e1 = post("/api/phase_automap", {"line": LINE, "target_colors": COLORS, "scene": "PAL-R9-S9-PLANEA-NOPE"})
    ck("E1. unknown scene fails (404), no R1/P1 fallback", e1 == 404, e1)
    _, e2 = post("/api/phase_automap", {"line": LINE, "target_colors": COLORS, "scene": "PAL-R1-S1-PLANEA-OUTDOOR"})
    ck("E2. recognized but corpus-less scene fails (404)", e2 == 404, e2)
    _, e3 = post("/api/phase_automap", {"line": 2, "target_colors": COLORS, "scene": CASTLE1})
    ck("E3. protected Line 2 rejected (403)", e3 == 403, e3)
    _, e4 = post("/api/phase_automap", {"line": LINE, "target_colors": COLORS, "scene": "not-a-pal-key"})
    ck("E4. invalid scene key rejected (400)", e4 == 400, e4)

    # --- C: apply (fill) into the scene context, save, reload -> isolation ---
    prof = {"profile_id": "t_automap", "display_name": "t_automap", "parent": "baseline_current",
            "target_palette_lines": [[None]*16, [None]*16, [None]*16, [None]*16],
            "usage_palette_mappings": {}, "plane_usage_palette_mappings": {},
            # pre-existing R1-S1 mapping that must remain untouched
            "context_policies": {R1S1: {"plane_usage_palette_mappings": {"LA-0000": {"line": 3, "index_map": {"5": 7}}}}},
            "reserved_lines": [2]}
    before_r1s1 = copy.deepcopy(prof["context_policies"][R1S1])
    # client-style fill: only unmapped usages written to context_policies[CASTLE1]
    dest = prof["context_policies"].setdefault(CASTLE1, {}).setdefault("plane_usage_palette_mappings", {})
    for p in a["proposals"]:
        if p.get("blocked"): continue
        dest[p["usage_id"]] = {"line": p["line"], "index_map": p["index_map"]}
    r, _ = post("/api/policy", prof); ck("C1. save profile with scene mappings ok", r.get("ok"))
    loaded = g("/api/policy?p=t_automap")
    cp = loaded.get("context_policies", {})
    ck("C2. mappings stored under the R1-S2 scene context",
       bool(cp.get(CASTLE1, {}).get("plane_usage_palette_mappings")), list(cp.keys()))
    ck("C3. R1-S1 (r01.p01) mappings byte-identical (unaffected)",
       cp.get(R1S1) == before_r1s1, cp.get(R1S1))
    ck("C4. no auto-map mappings leaked into the global plane map",
       not loaded.get("plane_usage_palette_mappings"), loaded.get("plane_usage_palette_mappings"))
    ck("C5. target CRAM colors unchanged by auto-map (all lines still empty)",
       all(all(x is None for x in ln) for ln in loaded.get("target_palette_lines", [])),
       loaded.get("target_palette_lines"))

    # --- G: scene derive (/api/scene_palette) targets the CHOSEN line, scene-scoped + isolated ---
    d, dc = post("/api/scene_palette", {"scene": CASTLE1, "lines": [3]})
    ck("G1. derive to Line 3 echoes scene + 200", dc == 200 and d.get("scene") == CASTLE1, (dc, d.get("scene")))
    dmap = d.get("mappings", {})
    ck("G2. derive mappings ⊆ R1-S2 corpus", dmap and set(dmap) <= c1_ids, len(dmap))
    ck("G3. only Line 3 is filled (≤15 CRAM strings, idx0 empty); no other line returned",
       set(d["lines"]) == {"3"} and d["lines"]["3"][0] is None and
       1 <= sum(1 for x in d["lines"]["3"] if x) <= 15 and
       all(isinstance(x, str) and x.startswith("0x") for x in d["lines"]["3"] if x),
       {k: sum(1 for x in v if x) for k, v in d["lines"].items()})
    ck("G4. every mapped usage lands on the chosen line (3)",
       all(m["line"] == 3 for m in dmap.values()))
    # incremental: run again on Line 0 skipping the already-mapped usages -> places REMAINING banks on L0
    if d["summary"]["banks_blocked"]:
        d2, _ = post("/api/scene_palette", {"scene": CASTLE1, "lines": [0], "skip_usages": list(dmap)})
        ck("G5. incremental pass reports the first pass's banks as already-placed",
           d2["summary"]["banks_already_placed"] >= 1, d2["summary"])
        ck("G6. incremental mappings are NEW usages on Line 0 (no overlap with pass 1)",
           set(d2["mappings"]) <= c1_ids and not (set(d2["mappings"]) & set(dmap)) and
           all(m["line"] == 0 for m in d2["mappings"].values()),
           (len(d2["mappings"]), len(set(d2["mappings"]) & set(dmap))))
    else:
        ck("G5. (single line held all banks — incremental not exercised)", True)
        ck("G6. (single line held all banks — incremental not exercised)", True)
    _, g7 = post("/api/scene_palette", {"scene": "PAL-R9-S9-PLANEA-NOPE", "lines": [3]})
    ck("G7. unknown scene derive fails (404), no R1/P1", g7 == 404, g7)
    _, g8 = post("/api/scene_palette", {"scene": CASTLE1, "lines": [2]})
    ck("G8. Line 2 rejected as a derive target (400)", g8 == 400, g8)

    # apply like the client (colors -> cp[scene].tpl, mappings -> cp[scene].plane map) and prove isolation
    prof2 = {"profile_id": "t_derive", "display_name": "t_derive", "parent": "baseline_current",
             "target_palette_lines": [[None]*16, [None]*16, [None]*16, [None]*16],
             "usage_palette_mappings": {}, "plane_usage_palette_mappings": {},
             "context_policies": {R1S1: {"plane_usage_palette_mappings": {"LA-0000": {"line": 3, "index_map": {"5": 7}}}}},
             "reserved_lines": [2]}
    tgt = prof2["context_policies"].setdefault(CASTLE1, {})
    tpl = tgt.setdefault("tpl", {})
    for ln, arr in d["lines"].items():
        for i, c in enumerate(arr):
            if i and c: tpl.setdefault(ln, {})[str(i)] = c
    tgt.setdefault("plane_usage_palette_mappings", {}).update({k: v for k, v in dmap.items()})
    r, _ = post("/api/policy", prof2); ck("G9. save derived scene profile ok", r.get("ok"))
    L2 = g("/api/policy?p=t_derive")
    ck("G10. derived colors stored as per-scene override (cp[scene].tpl), base still empty",
       bool(L2["context_policies"][CASTLE1].get("tpl")) and
       all(all(x is None for x in ln) for ln in L2["target_palette_lines"]),
       L2["target_palette_lines"])
    ck("G11. R1-S1 mappings untouched by derive",
       L2["context_policies"][R1S1] == {"plane_usage_palette_mappings": {"LA-0000": {"line": 3, "index_map": {"5": 7}}}},
       L2["context_policies"][R1S1])
    ck("G12. only the chosen line (3) written; Line 2 never written",
       set((L2["context_policies"][CASTLE1].get("tpl") or {}).keys()) == {"3"},
       (L2["context_policies"][CASTLE1].get("tpl") or {}).keys())

    # --- H: Clear Line isolation (mirror of app.js clearLine) ---
    def clear_line(pol, scope, line):
        cp = pol.setdefault("context_policies", {})
        if scope in cp and "tpl" in cp[scope]:
            cp[scope]["tpl"].pop(str(line), None)
        tpl_base = pol["target_palette_lines"][line]
        for i in range(1, 16):
            tpl_base[i] = None
        for holder in [cp.get(scope, {}).get("plane_usage_palette_mappings", {}),
                       pol.get("plane_usage_palette_mappings", {}),
                       pol.get("usage_palette_mappings", {})]:
            for k in [k for k, m in holder.items() if m and m.get("line") == line]:
                del holder[k]
    prof3 = {"profile_id": "t_clear", "target_palette_lines": [[None]*16, [None]*16, [None]*16,
             [None] + ["0x0111"]*15],           # base Line 3 populated (legacy/shared)
             "context_policies": {
                CASTLE1: {"tpl": {"3": {"1": "0x0ABC"}}, "plane_usage_palette_mappings": {"LA-0005": {"line": 3, "index_map": {"4": 1}}}},
                R1S1: {"tpl": {"3": {"2": "0x0DEF"}}, "plane_usage_palette_mappings": {"LA-0000": {"line": 3, "index_map": {"5": 2}}}}},
             "usage_palette_mappings": {}, "plane_usage_palette_mappings": {}, "reserved_lines": [2]}
    clear_line(prof3, CASTLE1, 3)
    ck("H1. clearing R1-S2 Line 3 removed its tpl override",
       not prof3["context_policies"][CASTLE1].get("tpl", {}).get("3"), prof3["context_policies"][CASTLE1].get("tpl"))
    ck("H2. clearing R1-S2 Line 3 removed its plane mapping on that line",
       not prof3["context_policies"][CASTLE1]["plane_usage_palette_mappings"])
    ck("H3. R1-S1's own Line 3 override is UNTOUCHED",
       prof3["context_policies"][R1S1]["tpl"].get("3") == {"2": "0x0DEF"}, prof3["context_policies"][R1S1]["tpl"])
    ck("H4. R1-S1's own plane mapping on Line 3 is UNTOUCHED",
       prof3["context_policies"][R1S1]["plane_usage_palette_mappings"] == {"LA-0000": {"line": 3, "index_map": {"5": 2}}})
    ck("H5. shared base Line 3 cleared", all(x is None for x in prof3["target_palette_lines"][3]))
    ck("H6. profile with cleared line still saves", post("/api/policy", prof3)[0].get("ok"))

    # --- I: Line-2 REUSE mapping allowed; Line-2 color authoring still rejected ---
    base_prof = {"profile_id": "t_l2reuse", "parent": "baseline_current",
                 "target_palette_lines": [[None]*16, [None]*16, [None]*16, [None]*16],
                 "usage_palette_mappings": {}, "plane_usage_palette_mappings": {}, "reserved_lines": [2]}
    reuse = dict(base_prof); reuse["context_policies"] = {
        CASTLE1: {"plane_usage_palette_mappings": {"LA-0479": {"line": 2, "index_map": {"9": 5, "12": 11}}}}}
    ck("I1. Plane-A mapping that REUSES existing Line-2 colors is accepted", post("/api/policy", reuse)[0].get("ok"))
    empty = dict(base_prof); empty["profile_id"] = "t_l2empty"; empty["context_policies"] = {
        CASTLE1: {"plane_usage_palette_mappings": {"LA-0479": {"line": 2, "index_map": {"9": 0}}}}}
    ck("I2. mapping onto an EMPTY Line-2 index is rejected (no color creation)", post("/api/policy", empty)[1] == 403)
    author = dict(base_prof); author["profile_id"] = "t_l2author"; author["context_policies"] = {
        CASTLE1: {"tpl": {"2": {"5": "0x0FFF"}}}}
    ck("I3. authoring a Line-2 COLOR (tpl override) is still rejected", post("/api/policy", author)[1] == 403)
    got = g("/api/policy?p=t_l2reuse")
    ck("I4. reused Line-2 mapping persisted; Line-2 base stays empty",
       got["context_policies"][CASTLE1]["plane_usage_palette_mappings"]["LA-0479"]["line"] == 2 and
       all(x is None for x in got["target_palette_lines"][2]),
       got["target_palette_lines"][2])

    httpd.shutdown()
    print(f"\n{'SCENE_AUTOMAP PASS' if not F else str(len(F))+' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    raise SystemExit(main())
