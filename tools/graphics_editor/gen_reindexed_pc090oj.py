#!/usr/bin/env python3
"""Generate the offline Palette Composer R1/P1 sprite (PC090OJ) reindexed region (TOOLING, build stage).

Produces build/regions/pc090oj_editor.bin: a copy of the preconverted Genesis PC090OJ pattern region in
which every resolved R1/P1 sprite tile code has its pixel nibbles reindexed per the frozen Test profile's
authored per-usage index_map, so each sprite renders correctly against its authored shared Genesis line
(Line 0 or Line 1). Index 0 stays transparent. All other codes are byte-identical.

The reindex is CODE-INDEXED and unambiguous: across the seven authored R1/P1 source banks there are zero
cross-bank code collisions (proven in Andy_r1p1_test_sprite_semantic_resolution.md), and the only
same-bank multi-map case (bank 0x3E: large_bat vs small_bat) uses DISJOINT codes, so (code) alone selects
exactly one authored (usage, index_map). No runtime transform; no invented colors; no dominant collapse.
"""
import argparse, hashlib, json, os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def I(x):
    return int(str(x), 0) if isinstance(x, str) else int(x)


def build_code_usage(profile, enemies, enemy_patterns, families):
    """Return {code: (usage_id, bank, line, index_map)} for every resolved live R1/P1 sprite code."""
    um = profile["usage_palette_mappings"]
    # usage key base -> effective source bank
    USAGE_BANK = {"rastan": 0x33, "lizardman": 0x36, "valkyrie": 0x32, "chimera": 0x34,
                  "flying_demon": 0x35, "small_bat": 0x3E, "large_bat": 0x3E, "four_armed_insect": 0x3A}
    # semantic_id -> code set (corpus cell_codes/base_code + proven family vocabulary)
    en = {e["semantic_id"]: e for e in enemies["enemies"]}
    fam = {f["id"]: f for f in families}

    def codes(name, fams=()):
        c = set(); e = en.get(name, {})
        if e.get("base_code") is not None: c.add(I(e["base_code"]))
        for x in (e.get("cell_codes") or []): c.add(I(x))
        for x in (enemy_patterns.get(name, {}).get("cell_codes") or []): c.add(I(x))
        for fid in fams:
            for x in fam.get(fid, {}).get("codes", []): c.add(I(x))
        return c

    code_sets = {
        "rastan": codes("RASTAN", ["rastan_player_body", "player_auxiliary"]),
        "lizardman": codes("LIZARDMAN", ["stage1_lizardman"]),
        "valkyrie": codes("VALKYRIE"), "chimera": codes("CHIMERA"),
        "flying_demon": codes("FLYING_DEMON"), "four_armed_insect": codes("FOUR_ARMED_INSECT"),
        "small_bat": codes("SMALL_BAT"), "large_bat": codes("LARGE_BAT"),
    }

    # authoritative authored map per usage base name; rastan uses the sole non-empty (f7722) entry.
    def map_for(usagebase):
        best = None
        for uid, m in um.items():
            key = uid.split(":")[1] if ":" in uid else uid
            if key == usagebase or key.startswith(usagebase + "_") or (usagebase == "rastan" and key.startswith("rastan")):
                imap = m.get("index_map") or {}
                if imap and best is None:
                    best = (uid, m.get("line"), {int(a): int(b) for a, b in imap.items()})
        return best

    out = {}
    for usagebase, cset in code_sets.items():
        info = map_for(usagebase)
        if info is None:
            raise SystemExit(f"no non-empty authored map for {usagebase}")
        uid, line, imap = info
        bank = USAGE_BANK[usagebase]
        for code in cset:
            if code in out and out[code][3] != imap:
                raise SystemExit(f"code {hex(code)} conflict: {out[code][0]} vs {uid}")
            out[code] = (uid, bank, line, imap)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.join(ROOT, "build/rastan-direct/build0314/Test.snapshot.json"))
    ap.add_argument("--enemies", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1_corpus/enemies.json"))
    ap.add_argument("--enemy-patterns", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1_corpus/enemy_patterns.json"))
    ap.add_argument("--families", default=os.path.join(ROOT, "analysis/graphics_optimizer/round1_phase1/sprite_families.json"))
    ap.add_argument("--pc090oj", default=os.path.join(ROOT, "build/pc090oj_genesis.bin"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build/regions/pc090oj_editor.bin"))
    ap.add_argument("--manifest", default=os.path.join(ROOT, "build/regions/pc090oj_editor_manifest.json"))
    a = ap.parse_args()

    profile = json.loads(open(a.profile, "rb").read())
    profile_sha = hashlib.sha256(open(a.profile, "rb").read()).hexdigest()
    enemies = json.load(open(a.enemies)); enemy_patterns = json.load(open(a.enemy_patterns))
    families = json.load(open(a.families))
    code_usage = build_code_usage(profile, enemies, enemy_patterns, families)

    raw = bytearray(open(a.pc090oj, "rb").read())
    ncodes = len(raw) // 32
    manifest = {"profile_sha256": profile_sha, "source": os.path.relpath(a.pc090oj, ROOT),
                "reindexed_codes": 0, "entries": []}
    # Native PC090OJ code identity = ONE 16x16 cell = four Genesis 8x8 tiles = 128 bytes; the runtime
    # uploads a sprite pattern from rastan_pc090oj + code*128 (pc090oj_hooks.s). The index_map applies to
    # every pixel nibble across all four 8x8 subtiles of the cell; index 0 stays transparent.
    CELL = 128
    changed = 0
    for code, (uid, bank, line, imap) in sorted(code_usage.items()):
        s = code * CELL
        if s + CELL > len(raw):
            raise SystemExit(f"code {hex(code)} out of region range")
        for off in range(CELL):
            b = raw[s + off]
            hi = (b >> 4) & 0xF; lo = b & 0xF
            hi = imap.get(hi, hi) if hi != 0 else 0
            lo = imap.get(lo, lo) if lo != 0 else 0
            raw[s + off] = (hi << 4) | lo
        changed += 1
        manifest["entries"].append({
            "code": code, "bank": "0x%03X" % bank, "usage": uid, "line": line,
            "index_map": {str(k): v for k, v in sorted(imap.items())},
            "source_offset": s, "source_size": CELL,
            "cell_sha256": hashlib.sha256(bytes(raw[s:s + CELL])).hexdigest()})
    manifest["reindexed_codes"] = changed
    manifest["cell_model"] = {"offset": "code*128", "size_bytes": 128, "subtiles": 4,
                              "note": "PC090OJ code = one 16x16 cell = four Genesis 8x8 tiles"}

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "wb").write(bytes(raw))
    json.dump(manifest, open(a.manifest, "w"), indent=1)
    asset_sha = hashlib.sha256(bytes(raw)).hexdigest()
    print("pc090oj_editor.bin: %d sprite codes reindexed (%d total codes); profile_sha=%s asset_sha=%s"
          % (changed, ncodes, profile_sha[:16], asset_sha[:16]))


if __name__ == "__main__":
    main()
