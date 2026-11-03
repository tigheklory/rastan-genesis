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
            # Arcade palette = 0RGB nibble-packed (S[8:11]=R, S[4:7]=G, S[0:3]=B) at the startup
            # base 0x4EAF6 + bank*32; convert to rgb8 via _pal5, EXACTLY like the editor's
            # _arcade_round_palette.  Banks < 48 are fixed (scene-independent), which covers every
            # Plane-A bank these subrounds use.
            bank_colors = {}
            for b in banks:
                base = 0x4EAF6 + b * 32
                if b < 48 and base + 32 <= len(mc):
                    cols = []
                    for i in range(16):
                        w = int.from_bytes(mc[base + i * 2:base + i * 2 + 2], "big")
                        cols.append([pal5((w >> 8) & 0xF), pal5((w >> 4) & 0xF), pal5(w & 0xF)])
                    bank_colors[f"0x{b:03X}"] = {"arcade_rgb8": cols, "source": f"startup base @0x{base:05X}"}
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
