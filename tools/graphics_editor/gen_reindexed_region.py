#!/usr/bin/env python3
"""Generate the offline Palette Composer Layer-A pattern region (TOOLING, build stage).

Produces build/regions/pc080sn_editor_layera.bin: a copy of the arcade PC080SN region in which ONLY the
R1/P1 editor-authored Layer-A tile codes have their pixel nibbles reindexed per the frozen Test snapshot's
per-usage index maps. Layer-B tile codes are disjoint from Layer-A codes and are left byte-identical, so
Layer B is unaffected. The raw arcade region is NOT modified in place.

(code,bank) uniquely resolves every editor index map (0 hard ambiguities). This region is code-indexed, so
for the small set of tile codes that carry bank-dependent variants the most-frequent variant is emitted; the
per-usage/(code,bank) exact identity is preserved in compile_editor_layera.py's manifest for the later
epoch-variant path. This is a documented Build-0315 checkpoint limitation, not a Layer-B risk.
"""
import argparse, json, os
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.join(ROOT, "build/rastan-direct/build0314/Test.snapshot.json"))
    ap.add_argument("--uses", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1/plane_a_uses.json"))
    ap.add_argument("--pc080sn", default=os.path.join(ROOT, "build/regions/pc080sn.bin"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build/regions/pc080sn_editor_layera.bin"))
    a = ap.parse_args()

    raw = bytearray(open(a.pc080sn, "rb").read())
    profile = json.load(open(a.profile))
    uses = json.load(open(a.uses))
    pm = profile["context_policies"]["context:gameplay.r01.p01"]["plane_usage_palette_mappings"]

    code_maps = defaultdict(Counter)
    for i, u in enumerate(uses):
        m = pm.get("LA-%04d" % i)
        if not m:
            continue
        key = tuple(sorted((int(k), int(v)) for k, v in m["index_map"].items()))
        code_maps[u["tile_code"]][key] += 1

    changed = 0
    for code, ctr in code_maps.items():
        imap = dict(ctr.most_common(1)[0][0])
        s = code * 32
        for off in range(32):
            b = raw[s + off]
            hi = (b >> 4) & 0xF
            lo = b & 0xF
            hi = imap.get(hi, hi) if hi != 0 else 0
            lo = imap.get(lo, lo) if lo != 0 else 0
            raw[s + off] = (hi << 4) | lo
        changed += 1

    with open(a.out, "wb") as f:
        f.write(bytes(raw))
    print("pc080sn_editor_layera.bin: %d Layer-A tile codes reindexed (%d bytes)" % (changed, len(raw)))


if __name__ == "__main__":
    main()
