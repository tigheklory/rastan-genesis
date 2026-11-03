#!/usr/bin/env python3
"""PROMPT-ID-0006 Req 2/Test D (server + resolution layer): prove per-subround Genesis palette lines
are independent and persist, mirroring the client's effEntry resolution exactly.

What this proves (data/context layer, via the REAL in-process server + /api/policy round-trip):
  - Each subround PLANEA scene_key is a genuine editing context (ctxById-resolvable).
  - A Line-3 edit saved at R1-S2's scope lands in context_policies[R1-S2].tpl and persists over save+reload.
  - R1-S2's effective Line 3 reflects its override; R1-S1's effective Line 3 is UNCHANGED (isolation).
  - Line 2 writes are rejected (reserved).
What it does NOT prove (requires a browser): the DOM event path / Undo-Redo UI. Those are listed as
manual-verification steps in the report.
"""
from __future__ import annotations
import importlib.util, json, threading, time, urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P, F = [], []
def ck(n, c, extra=""):
    (P if c else F).append(n); print(("PASS " if c else "FAIL ") + n + (("  -> " + str(extra)) if extra and not c else ""))

# ----- mirror of app.js context resolution (ctxChain + effEntry) -----
def ctx_by_id(contexts, cid): return next((c for c in contexts if c["id"] == cid), None)
def ctx_chain(contexts, cid):
    out = []; c = ctx_by_id(contexts, cid)
    while c:
        out.insert(0, c); c = ctx_by_id(contexts, c["parent"]) if c.get("parent") else None
    return out
def eff_entry(pol, contexts, scope, line, i):
    tpl = (pol.get("target_palette_lines") or [[None]*16]*4)
    cram = tpl[line][i] if line < len(tpl) and i < len(tpl[line]) else None
    owner = "default"
    cp = pol.get("context_policies") or {}
    for c in ctx_chain(contexts, scope):
        t = (cp.get(c["id"]) or {}).get("tpl", {}).get(str(line))
        if t and str(i) in t:
            cram = t[str(i)]; owner = c["id"]
    return cram, owner


def main() -> int:
    spec = importlib.util.spec_from_file_location("ged_server", ROOT / "tools/graphics_editor/server.py")
    srv = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(srv)
    except SystemExit: pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Hd); port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.3)
    def g(u): return json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}"+u))
    def post(u, obj):
        req = urllib.request.Request(f"http://127.0.0.1:{port}"+u, data=json.dumps(obj).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        return json.load(urllib.request.urlopen(req))

    oracle = g("/api/oracle"); contexts = oracle["contexts"]
    ck("1. R1-S2 castle is a registered editing context",
       ctx_by_id(contexts, "PAL-R1-S2-PLANEA-CASTLE") is not None)
    ck("2. R2-S1 outdoor is a registered editing context",
       ctx_by_id(contexts, "PAL-R2-S1-PLANEA-OUTDOOR") is not None)
    ck("3. subround contexts parent to a neutral gameplay node (independent siblings)",
       (ctx_by_id(contexts, "PAL-R2-S1-PLANEA-OUTDOOR") or {}).get("parent") == "context:gameplay")

    # Build an editable profile: a base Line 3 + a castle-only Line-3 override.
    base_line3 = [None] + ["0x0111"]*15        # shared base
    prof = {"profile_id": "t_indep", "display_name": "t_indep", "parent": "baseline_current",
            "target_palette_lines": [[None]*16, [None]*16, [None]*16, base_line3],
            "usage_palette_mappings": {}, "plane_usage_palette_mappings": {},
            "context_policies": {"PAL-R1-S2-PLANEA-CASTLE": {"tpl": {"3": {"1": "0x0ABC", "2": "0x0DEF"}}}},
            "reserved_lines": [2]}
    r = post("/api/policy", prof); ck("4. save with per-scene context_policies ok", r.get("ok"))
    loaded = g("/api/policy?p=t_indep")
    cp = loaded.get("context_policies", {})
    ck("5. castle Line-3 override persisted over save+reload",
       cp.get("PAL-R1-S2-PLANEA-CASTLE", {}).get("tpl", {}).get("3", {}).get("1") == "0x0ABC", cp)

    # Isolation: castle sees its override; R1-S1 (r01.p01) sees the base, unaffected.
    castle, co = eff_entry(loaded, contexts, "PAL-R1-S2-PLANEA-CASTLE", 3, 1)
    r1s1, ro = eff_entry(loaded, contexts, "context:gameplay.r01.p01", 3, 1)
    ck("6. R1-S2 Line3[1] = its own override", castle == "0x0ABC" and co == "PAL-R1-S2-PLANEA-CASTLE", (castle, co))
    ck("7. R1-S1 Line3[1] = base, UNAFFECTED by the castle edit", r1s1 == "0x0111" and ro == "default", (r1s1, ro))
    # R2-S1 also independent (no override -> base)
    r2, r2o = eff_entry(loaded, contexts, "PAL-R2-S1-PLANEA-OUTDOOR", 3, 1)
    ck("8. R2-S1 independent (base until its own edit)", r2 == "0x0111" and r2o == "default", (r2, r2o))

    # Line 2 protection: server must strip any reserved-line context override.
    bad = dict(prof); bad["profile_id"] = "t_l2"; bad["context_policies"] = {"PAL-R1-S2-PLANEA-CASTLE": {"tpl": {"2": {"1": "0x0FFF"}}}}
    try:
        rr = post("/api/policy", bad); l2ok = not rr.get("ok", True)
    except urllib.error.HTTPError:
        l2ok = True
    ck("9. Line 2 context override rejected (reserved)", l2ok)

    httpd.shutdown()
    print(f"\n{'INDEPENDENT_SCOPES PASS' if not F else str(len(F))+' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    import urllib.error
    raise SystemExit(main())
