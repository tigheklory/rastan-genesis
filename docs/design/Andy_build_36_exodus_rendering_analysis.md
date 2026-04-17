# Andy — Build 36 Exodus Rendering Analysis vs Arcade Reference

**Status:** ANALYSIS COMPLETE. Single primary rendering failure identified.
**Build Context:** Build 0036, `rastan-direct`.

---

## 1. Build 36 Baseline

- **Number-renderer hook at `arcade_pc: 0x03C2E2`:** installed (`opcode_replace_count = 56`). Confirmed in `specs/rastan_direct_remap.json`.
- **FG tilemap live writer at `HW_ADDRESS/PC080SN/FG_TILEMAP: 0xC09EA0`:** ELIMINATED. `fg_cwindow_live count=0` in Build 36 trace (`states/traces/rastan_direct_video_test_build_0036_mame_30s_20260416_121207/genesis_exec_summary.txt`).
- **Exodus output:** still incorrect. Red/blue vertical-bar pattern in early frames, transitioning to green hatched fill, then dark-green steady-state. NO arcade text, title screen, score table, or item list visible at any frame.
- **Key difference from Builds 33–35:** Build 36 does NOT go BLACK. No "Error Trigger" console spam. The CPU no longer traps at `runtime_genesis_pc: 0x000010` — execution continues through all 1798 MAME frames. The crash at `0xC09EA0` is resolved.
- **BlastEm now crashes at a different address** (`0xC00328` per user-noted symptom). This is a separate issue — not the focus of this analysis.

---

## 2. Frame Comparison vs Arcade

### Sampled frames

| Build 36 frame | Arcade ref frame | Build 36 VDP Image | Arcade ref output |
|----------------|------------------|--------------------|-------------------|
| 0001 | 0001 | File-open dialog (pre-game). | White fill (power-on). |
| 0090 | 0090 | **Red/blue vertical bars** filling play field. | **"RASTAN" title screen** — gold sword banner, "TAITO 1987" text, white text, colored background. |
| 0180 | 0180 | **Red plane fill** with thin blue band at top. | Continuation of title or transition. |
| 0300 | 0300 | **Green hatched repeating pattern** across entire play field. | **Item list screen** — "AXE", "HAMMER", "FIRE SWORD", "SHIELD" with colored item sprites and white text. |
| 0350 | 0350 | **Bright green hatched fill**, dense uniform pattern. | Item list continuation. |
| 0400 | 0400 | **Dark green fill** with lighter band at top. Console log has entries (not Error Trigger). | Item list / transition. |
| 0500 | 0500 | **Dark green**, stable. Console entries present. | Item list / scrolling text continuation. |
| 0596 | ~0596 | **Dark green**, stable. Unchanged from 0500. | Attract-mode cycling. |

### First meaningful divergence

The divergence is total from the first rendered frame (0090). The arcade shows recognizable multi-colored text and tile art on a dark background. Build 36 shows uniform red/blue vertical bars — a repeating pattern with no text structure, no letter shapes, no score digits. At no sampled frame does Build 36 show ANY content that resembles arcade output.

### Divergence category

The divergence is NOT:
- Wrong palette with correct shapes (which would show letter-shaped tiles in wrong colors).
- Wrong layout with correct tiles (which would show recognizable glyphs in wrong positions).

The divergence IS: **no recognizable tile shapes at all**. The patterns visible are uniform fills and repeating synthetic patterns — consistent with VRAM containing only the bringup `init_staging_state` tile data (checker, hatch, solid fills) and the nametable entries pointing at those tiles regardless of what the hooks write.

---

## 3. Exodus Rendering Interpretation

### Per-frame panel observations

**frame_0090:**
- VDP Image Window: red/blue vertical bars, ~8 bars across width.
- Plane Viewer (Layer A / 0xE000): same bar pattern visible in thumbnail — the plane maps ARE producing this output, not a display glitch.
- Plane Viewer (Layer B / 0xC000): similar vertical bars, slight color difference.
- VRAM Pattern Viewer: top region shows dense random/checker (white-on-black noise — the `init_staging_state` synthetic tile content). Bottom region shows colored bar tiles (red, blue, green palette entries).
- VDP Palette / CRAM: four lines populated. Line 0 has greens, line 1 has reds/blues, lines 2–3 have mixed entries. These are the **greyscale-ramp palette** from the `palette_pre_conversion` step (Build 113 placeholder per `tools/translation/postpatch_startup_rom.py:1093–1132`).
- Console log: clean (no errors).

**frame_0300:**
- VDP Image Window: green hatched repeating pattern — the entire play field shows the same ~4 tile shapes repeated in a grid.
- Plane Viewer: Layer A shows green hatch filling the plane. Layer B shows different content but also synthetic.
- VRAM Pattern Viewer: now contains MORE tile entries than frame 0090 — the hatch tiles in the lower portion are denser. This could indicate `load_scene_tiles` ran and loaded *some* tile data, but the loaded tiles are hatch/checker patterns, NOT recognizable arcade glyphs.
- VDP Palette: unchanged from frame 0090 — still the greyscale-ramp placeholder.

**frame_0400–0596:**
- VDP Image Window: dark green with a lighter green band at the top (possibly the visible-row region of Plane A vs Plane B layering). Stable across frames 400–596.
- VRAM Pattern: same synthetic tile data — no arcade font glyphs, no sprite tiles, no item icons visible at any point.
- Palette: unchanged placeholder ramp.
- Console log: has entries (warnings/notes, not crash-level Error Trigger). System is running.

### What the bars and green fill mean

The red/blue vertical bars (frame 0090) are the result of:
- Layer A nametable entries pointing at VRAM tile positions that contain the synthetic checker/fill content from `init_staging_state`.
- The palette's greyscale-ramp entries produce alternating red/blue when the synthetic tile patterns' pixel values index into those palette positions.
- As the attract mode progresses and hooks write new nametable indices into `staged_fg_buffer`, the plane content changes (from bars → hatched green) because the newly-written nametable indices point to DIFFERENT synthetic tiles — but those tiles are still from the bringup set, not arcade glyphs.

The green hatched pattern (frames 300+) likely results from:
- The text-script hooks and/or number-renderer hook writing translated tile indices into `staged_fg_buffer`.
- Those indices, after LUT translation, point to VRAM tile positions that were populated by the bringup scene-preload system with green hatched patterns (the `pc080sn_scene_preload_*.bin` data, which may be mapping to scene-0 default tiles).

### Tilemap-to-pattern correlation

The tiles in the VRAM Pattern Viewer ARE being correctly referenced by the nametable. The planes ARE rendering. The VDP IS displaying. The pipeline from `staged_fg_buffer → vdp_commit_fg_strips_if_dirty → VRAM Plane A` is functional. **The problem is that the tile GRAPHICS in VRAM do not contain the correct arcade character/glyph shapes.**

---

## 4. Trace Correlation

### VDP activity

`vdp_ports_live count=26468` (up from 26336 in Builds 33–35). The wrapper continues writing VDP registers every frame across all 1798 frames. The slightly higher count (26468 vs 26336 = +132 extra VDP register writes) is consistent with the system running longer without crashing — more frames of active VDP register updates occur because execution no longer dies at frame ~270.

### fg_cwindow_live = 0

Confirmed: no FG C-window writes in the entire 30-second trace. The crash source is gone.

### Intended content production

The trace does NOT directly report whether hooks are writing to `staged_fg_buffer` (that's an internal WRAM operation, not a hardware-address write that the trace's memory-write taps monitor). However:
- The Plane Viewer in Exodus frames 0300+ shows CHANGED content (green hatch) that differs from the frame 0090 content (red/blue bars). Something IS writing to `staged_fg_buffer` and triggering `fg_row_dirty` bits, causing `vdp_commit_fg_strips_if_dirty` to update VRAM plane maps.
- The content change from bars → hatch aligns with the attract-mode timer progression (arcade code transitioning between scenes/states).

**Conclusion: hooks ARE producing nametable index writes into `staged_fg_buffer` and those writes ARE being committed to VRAM. But the nametable indices point to VRAM tile positions whose graphics content is WRONG.**

### Symbol/window signature evidence

`wram_ff0000 changes=13 first_change=60 last_change=420` — arcade WRAM state changes 13 times, last change at frame 420. This is consistent with the arcade state machine progressing through attract-mode phases. `arcade_flag_34` changes twice (frame 7 and 391), `arcade_mode4` changes once (frame 391). The arcade code IS advancing its state machine.

---

## 5. Primary Rendering Failure

> **Wrong tile graphics / VRAM content.**
>
> The Genesis VRAM Pattern data does not contain the arcade game's tile
> graphics (font glyphs, score digits, title art, item sprites) at any
> sampled frame. It contains only the synthetic bringup tiles from
> `init_staging_state` (checker, hatch, solid fill patterns) and
> scene-preload data that does not match the attract-mode's visual
> requirements. The hooks are writing translated nametable indices into
> `staged_fg_buffer`, and those writes ARE being committed to VRAM
> plane maps, but the VRAM tile graphics at the indexed positions are
> the wrong shapes. The result is uniform repeating patterns (bars,
> hatched fills) instead of readable text and game art.

### Evidence

1. **VRAM Pattern Viewer** across all sampled frames (0090, 0180, 0300, 0350, 0400, 0500, 0596) shows only synthetic/placeholder tile patterns. No recognizable arcade font characters (A–Z, 0–9), no item sprites, no title art shapes are visible in the Pattern Viewer at any point.

2. **Plane Viewer** shows the planes ARE populated and ARE referencing tiles. The patterns change across frames (bars → hatch → dark fill), proving that nametable writes from hooks are reaching VRAM plane maps. But the rendered shapes are all from the synthetic bringup set.

3. **VDP Palette / CRAM** shows the Build-113 greyscale-ramp placeholder (from `palette_pre_conversion` in `postpatch_startup_rom.py`). This is a secondary contributing factor (wrong colors), but even with correct palette the tile shapes would still be wrong — there are no letter-shaped tiles in VRAM to display.

4. **Arcade comparison** at the same attract phase shows dense multi-colored text on a dark background — "RASTAN" title, "1UP", "HIGH SCORE", "CREDIT", score digits, item names with colored sprites. All of this requires specific tile graphics (font glyphs, sprite tiles) to be loaded into the VDP's pattern area. Build 36 has none of this tile data in VRAM.

### Why each other category is NOT primary

- **Wrong tilemap / nametable mapping:** Refuted. The Plane Viewer shows the planes ARE referencing tiles, and the content changes across frames (proving hooks are writing and commits are running). The mapping pipeline works — the indices just point to wrong graphics.

- **Wrong palette / CRAM usage:** Present as a secondary issue (greyscale ramp instead of correct arcade colors). But even with correct palette, the visible tiles would be checker/hatch shapes, not arcade text. Wrong palette produces discolored but shape-correct output; Build 36's output has NO correct shapes. Palette is secondary, not primary.

- **Wrong plane/layer composition:** Refuted. Both Layer A and Layer B are visible in the Plane Viewer. The VDP Image Window reflects what the planes show. No layer is missing or misconfigured — the display OFF/ON bracket is working, plane bases are set (`vdp_boot_setup` initializes Plane A at `0xE000`, Plane B at `0xC000`).

- **Intended content never produced:** Partially refuted. The hooks DO produce nametable writes (evidenced by plane content changing across frames). What was never produced is the TILE GRAPHICS in VRAM — the `load_scene_tiles` / tile-preload system has not delivered correct arcade tile pattern data to VRAM for the attract-mode scenes. The hooks produce tilemap intent; the tile data pipeline has not produced the corresponding tile graphics.

### Secondary issue

The VDP palette (CRAM) is the Build-113 greyscale-ramp placeholder. Even after VRAM tile graphics are fixed, colors will be wrong until the arcade palette-write path is hooked to translate Taito xRGB-444 palette entries to Genesis CRAM format in real time (or the scene-preload system includes correct palette data).

---

## 6. Next-Step Recommendation (Analysis Only)

The tile-graphics gap is the next target. Two sub-systems are involved:

1. **Scene tile preload** (`load_scene_tiles` at `apps/rastan-direct/src/main_68k.s` + the `pc080sn_scene_preload_*.bin` data files built by `tools/translation/precompute_pc080sn_tile_lut.py`). Investigation: are the scene-preload binaries loading the correct tile graphics for the attract-mode scene IDs? Are the tile indices from the LUT consistent with the VRAM positions where scene tiles are placed?

2. **Runtime tile loading** — does the arcade code expect to load additional tile graphics at runtime (e.g., via DMA or direct VRAM writes from ROM data), and if so, is that path hooked/translated? The attract mode may require tiles beyond what the scene preloader covers.

No implementation. The next Andy prompt should audit the tile-loading pipeline to determine whether the gap is in the scene-preload data, the LUT mapping, or a missing runtime tile-load path.
