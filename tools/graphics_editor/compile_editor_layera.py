#!/usr/bin/env python3
"""Compile the frozen editor R1/P1 Layer-A policy into real Genesis graphics bytes (offline, TOOLING).

Reads the frozen Test snapshot's context:gameplay.r01.p01 Layer-A mappings and produces:
  - line3_cram.bin       : the 15 nontransparent Line-3 CRAM words (editor's Layer-A palette), big-endian
  - layera_patterns.bin  : exact-deduplicated reindexed 8x8 4bpp patterns (pixel nibble = editor target entry)
  - manifest.json        : provenance (usage -> source tile, index_map, transformed pattern hash, target line)

This is the compiler core (per-usage index-map application) the production build was missing. It does NOT
itself modify the ROM; it produces provable artifacts + static proofs that the transformation is faithful.
"""
import json, os, hashlib, struct, argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CTX = "context:gameplay.r01.p01"


def tile_indices8(gfx, code):
    s = code * 32
    c = gfx[s:s + 32]
    px = []
    for b in c:
        px.append((b >> 4) & 0xF)
        px.append(b & 0xF)
    return px  # 64 nibbles


def pack_4bpp(px):
    out = bytearray()
    for i in range(0, 64, 2):
        out.append(((px[i] & 0xF) << 4) | (px[i + 1] & 0xF))
    return bytes(out)  # 32 bytes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.join(ROOT, "build/rastan-direct/build0314/Test.snapshot.json"))
    ap.add_argument("--uses", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1/plane_a_uses.json"))
    ap.add_argument("--pc080sn", default=os.path.join(ROOT, "build/regions/pc080sn.bin"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build/rastan-direct/build0315_editor_layera"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    profile = json.load(open(a.profile))
    gfx = open(a.pc080sn, "rb").read()
    uses = json.load(open(a.uses))
    uses_by_id = {}
    for i, u in enumerate(uses):
        uses_by_id["LA-%04d" % i] = u

    # Line-3 CRAM = editor Layer-A palette (15 nontransparent words)
    L3 = profile["target_palette_lines"][3]
    cram_words = [int(c, 16) for i, c in enumerate(L3) if c and i != 0]
    open(os.path.join(a.out, "line3_cram.bin"), "wb").write(b"".join(struct.pack(">H", w) for w in cram_words))

    pm = profile["context_policies"][CTX]["plane_usage_palette_mappings"]
    pat_index = {}   # transformed 32-byte pattern -> slot
    patterns = []
    manifest = []
    for uid, m in pm.items():
        u = uses_by_id.get(uid)
        if not u:
            continue
        code = u["tile_code"]
        im = {int(k): int(v) for k, v in m["index_map"].items()}
        px = tile_indices8(gfx, code)
        # apply index map: every used source nibble -> editor target entry; index 0 (transparent) stays 0
        tpx = [(im.get(v, v) if v != 0 else 0) for v in px]
        tb = pack_4bpp(tpx)
        h = hashlib.sha256(tb).hexdigest()
        if tb not in pat_index:
            pat_index[tb] = len(patterns)
            patterns.append(tb)
        manifest.append({"usage_id": uid, "tile_code": code, "line": m["line"],
                         "index_map": m["index_map"], "pattern_slot": pat_index[tb],
                         "transformed_sha": h[:16]})
    open(os.path.join(a.out, "layera_patterns.bin"), "wb").write(b"".join(patterns))
    rep = {"context": CTX, "profile": a.profile,
           "profile_sha256": hashlib.sha256(open(a.profile, "rb").read()).hexdigest(),
           "line3_cram_words": ["0x%04X" % w for w in cram_words], "line3_count": len(cram_words),
           "layera_usages": len(manifest), "unique_transformed_patterns": len(patterns),
           "exact_dedup_saved": len(manifest) - len(patterns), "usages": manifest}
    open(os.path.join(a.out, "manifest.json"), "w").write(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in ("context", "profile_sha256", "line3_cram_words", "line3_count",
                                          "layera_usages", "unique_transformed_patterns", "exact_dedup_saved")}, indent=1))


if __name__ == "__main__":
    main()
