#!/usr/bin/env python3
"""RG-022: generate the per-subround Layer-A authoring corpus from the ARCADE SOURCE.

Reuses the committed arcade decoders (no Genesis map assembly, which Cody is still correcting under
RG-023):
  - tools/graphics_optimizer/analyze_graphics.py `decode_plane_a(mc, gfx, segments)` -> the exact
    plane_a_uses rows (tile_code, palette_bank = attr & 0x1FF, flip, map_cell_count, records) the
    Palette Composer already consumes for Round 1.
  - tools/translation/compile_pc080sn_genesis.py `decode_arcade_palette_bank(mc, bank, scene)` ->
    the arcade-loaded colors for each Plane-A color bank in that scene (so later-round banks show
    their real per-scene colors, not Round-1 colors).

For each subround environment in specs/palette_subround_map.json whose family is PLANEA, it emits:
  analysis/graphics_optimizer/subround_corpus/<scene_key>/plane_a_uses.json
  analysis/graphics_optimizer/subround_corpus/<scene_key>/plane_palette_banks.json
  analysis/graphics_optimizer/subround_corpus/index.json   (scene_key -> record band + counts)

The editor loads these when a subround is selected.  Round-1 outdoor (records 0-15) keeps the existing
round1_phase1 corpus untouched.
"""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/graphics_optimizer/subround_corpus"
MAINCPU = ROOT / "build/regions/maincpu.bin"
PC080SN = ROOT / "build/regions/pc080sn.bin"
MAP = ROOT / "specs/palette_subround_map.json"


def pal5(n):  # 4-bit arcade channel -> 8-bit, identical to the editor's _pal5
    v = n * 2
    return (v << 3) | (v >> 2)


# Per-round Plane-A palette base pointer table (arcade FUN_00059c54 reads *(0x59C9A + (round-1)*4)).
PER_ROUND_PALETTE_PTR = 0x59C9A


def _per_round_palette_base(mc: bytes, rnd: int) -> int:
    """Resolve the active per-round Plane-A palette base address from the arcade pointer table at
    0x59C9A (round 1 -> 0x4EAF6, round 2 -> 0x4EEF8, ...). This is the authoritative background-palette
    source that the arcade fades into visible palette RAM 0x200000; NOT the fixed startup base."""
    off = PER_ROUND_PALETTE_PTR + (rnd - 1) * 4
    return int.from_bytes(mc[off:off + 4], "big")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ag = _load(ROOT / "tools/graphics_optimizer/analyze_graphics.py", "ag_graphics")
    comp = _load(ROOT / "tools/translation/compile_pc080sn_genesis.py", "pc080sn_comp")
    mc = MAINCPU.read_bytes()
    gfx = PC080SN.read_bytes()
    smap = json.loads(MAP.read_text())

    OUT.mkdir(parents=True, exist_ok=True)
    index = {}
    for sr in smap["subrounds"]:
        # Only subrounds whose native graphics exist are generatable from the arcade source.
        if sr["native"] != "native_converted":
            continue
        for env in sr["environments"]:
            if env["family"] != "PLANEA":
                continue
            sk = env["scene_key"]
            lo, hi = env.get("records", sr["record_band"])
            segments = list(range(lo, hi + 1))
            # Round-1 outdoor already has the canonical corpus; skip to avoid divergence.
            if sr["key"] == "R1-S1" and env["env"] == "OUTDOOR":
                index[sk] = {"records": [lo, hi], "source": "round1_phase1 (canonical)", "usages": None}
                continue
            cells, uses = ag.decode_plane_a(mc, gfx, segments)
            banks = sorted({u["palette_bank"] for u in uses})
            # Arcade Plane-A palette is PER-ROUND. The active background palette is loaded from a
            # per-round base pointer table at 0x59C9A (loader FUN_00059c54, indexed by (round-1)*4),
            # into the fade buffer 0x10D600, then faded into visible palette RAM 0x200000 (FUN_00045d7c).
            #   round 1 -> 0x4EAF6 (== the startup/fixed base, so R1 is unchanged)
            #   round 2 -> 0x4EEF8,  round 3 -> 0x4F15A,  round 4 -> 0x4F51C,
            #   round 5 -> 0x4F85E,  round 6 -> 0x4FA80
            # Using the fixed 0x4EAF6 base for every round was WRONG for round 2+ (it reproduced the
            # Round-1 colors: teal foliage, black boss-room bank 2). Each bank is base + bank*32, 0RGB
            # nibble-packed (S[8:11]=R, S[4:7]=G, S[0:3]=B) converted to rgb8 via pal5. See
            # specs/palette_subround_map (round) and docs/design/Andy_*PROMT-ID-0110*.
            rnd = sr["round"]
            round_base = _per_round_palette_base(mc, rnd)
            bank_colors = {}
            for b in banks:
                base = round_base + b * 32
                if b < 48 and base + 32 <= len(mc):
                    cols = []
                    for i in range(16):
                        w = int.from_bytes(mc[base + i * 2:base + i * 2 + 2], "big")
                        cols.append([pal5((w >> 8) & 0xF), pal5((w >> 4) & 0xF), pal5(w & 0xF)])
                    bank_colors[f"0x{b:03X}"] = {"arcade_rgb8": cols,
                                                 "source": f"per-round base r{rnd} @0x{round_base:05X} + bank*32 (@0x{base:05X})"}
                else:
                    bank_colors[f"0x{b:03X}"] = {"arcade_rgb8": None, "source": "scene-selected bank (>=48): unresolved"}
            d = OUT / sk
            d.mkdir(parents=True, exist_ok=True)
            (d / "plane_a_uses.json").write_text(json.dumps(uses, indent=1) + "\n")
            (d / "plane_palette_banks.json").write_text(json.dumps({"banks": bank_colors}, indent=1) + "\n")
            index[sk] = {"records": [lo, hi], "segments": segments, "usages": len(uses),
                         "nonblank_cells": sum(u["map_cell_count"] for u in uses),
                         "palette_banks": [f"0x{b:03X}" for b in banks]}
            print(f"{sk:28} records {lo}-{hi}: usages={len(uses):4d} cells={sum(u['map_cell_count'] for u in uses):6d} banks={[f'0x{b:03X}' for b in banks]}")
    (OUT / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    print(f"SUBROUND_LAYERA_CORPUS_OK scenes={len([k for k,v in index.items() if v.get('usages')])} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
