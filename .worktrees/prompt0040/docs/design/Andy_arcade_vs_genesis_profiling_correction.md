# Andy — Arcade vs. Genesis Profiling Correction

## 1. Executive Summary

The per-mode VRAM working set profiling plan (Prompt 201, `Andy_per_mode_vram_working_set_profiling_plan.md`) defined a valid VRAM budget analysis but named the wrong instrument for gathering per-mode tile usage data. Sections 6 and 11 of that plan directed Cody to instrument `genesistan_hook_tilemap_plane_a` in the Genesis wrapper with WRAM bitmasks to measure which VRAM slots are written per scene. This is the wrong data source for this phase: the Genesis wrapper is currently broken (SSP corruption, display pipeline incomplete, game modes not progressing correctly) and hook observations under these conditions are not representative of actual arcade game behavior across all modes.

The critical finding of this correction analysis: the 1,067-slot count and per-scene working-set estimates already present in the profiling plan are arcade-derived, not Genesis-derived. They were computed by `precompute_pc080sn_tile_lut.py` via static analysis of `build/regions/maincpu.bin` (the arcade ROM). The VRAM budget conclusion — bulk preload is SAFE — rests on arcade-side data and is already valid. No additional profiling is required to confirm the bulk-preload safety decision.

The Genesis-side instrumentation described in Sections 6 and 11 of the profiling plan should be deferred entirely. It has no role in the current phase. The existing LUT-based analysis is sufficient.

---

## 2. Inputs Audited

| File | Status | Key Finding |
|------|--------|-------------|
| `docs/design/Andy_per_mode_vram_working_set_profiling_plan.md` | Read in full | Sections 6 and 11 incorrectly target Genesis hook as measurement source; VRAM math and per-scene estimates are arcade-derived and already correct |
| `docs/design/Andy_graphics_pipeline_break_diagnosis.md` | Read in full | Genesis wrapper state confirmed broken: SSP corruption, no tile pixel data in VRAM, display shows only synthetic checkerboard; wrapper does not exercise all game modes |
| `AGENTS_LOG.md` | Last 100 lines read | No Cody implementation of Genesis profiling instrumentation has occurred; plan was stated but not executed |
| `apps/rastan-direct/src/main_68k.s` | Searched for profiling symbols | No `genesistan_tile_slot_observed`, `genesistan_sprite_peak_unique`, or `genesistan_sprite_cell_observed` symbols present; no bitmask instrumentation exists |
| `tools/translation/precompute_pc080sn_tile_lut.py` | Read in full | LUT generator reads directly from `maincpu.bin` (arcade ROM) and `pc080sn.bin` (arcade tile ROM) via static analysis of block-write tables and strip descriptor tables; output is entirely arcade-derived |

---

## 3. The Misunderstanding Identified

### What Cody was directed to attempt

Sections 6 and 11 of the profiling plan directed Cody to add WRAM bitmask instrumentation to `genesistan_hook_tilemap_plane_a` in the Genesis wrapper. The mechanism was: at the LUT lookup point inside the hook, after reading the VRAM slot number into `%d3`, set bit `%d3` in one of three 192-byte WRAM bitmasks indexed by the current arcade game mode. After a full traversal — attract cycle, gameplay stage, end-round — dump the three bitmasks and count set bits to determine per-mode unique slot counts.

### Why this is the wrong data source

The Genesis wrapper is not in a state where hook observations represent full arcade game mode coverage:

1. **SSP corruption**: The arcade tick entry uses `rte` but was called via `jsr`, causing stack pointer drift and corrupted PC on the first game frame. This was diagnosed in `Andy_graphics_pipeline_break_diagnosis.md`. Although a fix for the `jsr`/`rte` mismatch was implemented by Cody, the overall display pipeline remains non-functional (no tile pixel data in VRAM).

2. **No tile pixel data in VRAM**: All VRAM tile slots 4–1342 are zero-initialized. The VDP renders transparent tiles for every arcade tile reference. The arcade game cannot visually progress through modes it cannot render.

3. **Game mode coverage is unknown**: Whether the arcade state machine advances correctly through Title/Attract, all Gameplay stages, and End-Round under the Genesis wrapper is unverified. The hook can only observe tile indices for modes the arcade code actually reaches. If the game is stuck in early initialization, hook observations would be an unrepresentative subset of the full tile working set.

4. **Hook observations are conditional on wrapper correctness**: `genesistan_hook_tilemap_plane_a` is only invoked when the PC080SN strip producer fires. If the arcade state machine does not progress to gameplay stages that exercise the strip producer, those tiles are never observed in the hook, even though the arcade ROM references them.

### What the correct data source must be

Tile index references are encoded statically in the arcade ROM. The correct source is the arcade ROM itself, analyzed either statically (parsing block-write tables, strip descriptor tables, and text writer tables in `maincpu.bin`) or dynamically (MAME tracing of actual PC080SN tile index writes per game state). Neither method depends on the Genesis wrapper being functional.

---

## 4. Correct Profiling Target

The measurement question is: which PC080SN tile indices does the arcade game reference in each mode?

This is an arcade ROM question, not a Genesis question.

- The arcade game's tile references are encoded in its block-write tables (`0x5635E`–`0x563A6` for gameplay, `0x5816A`–`0x5822A` for end-round), its static block-write sources (`0x5A7DA`–`0x5B0B2` for title), its strip descriptor tables (discovered by pattern scan of `maincpu.bin`), and its text writer glyph tables (`0x3BB7C`).
- Static analysis of these tables against the arcade ROM yields the definitive per-mode tile working set, independent of Genesis wrapper state.
- Dynamic MAME tracing (Lua script recording PC080SN tile index writes per game state register value) would yield the same data from the running arcade emulation, which is also independent of the Genesis wrapper.
- Genesis hook instrumentation yields only the tiles the Genesis wrapper happens to observe, which is a subset of the arcade's full tile set filtered through the current (broken) wrapper state.

For the purposes of bulk-preload validation, the correct profiling target has already been realized: `precompute_pc080sn_tile_lut.py` performed this exact static analysis, producing the 1,067-slot count. The analysis is already done.

---

## 5. Sufficiency of Existing LUT-Based Analysis

The `precompute_pc080sn_tile_lut.py` tool performs the following arcade-side static analysis:

1. Reads `build/regions/maincpu.bin` (the arcade 68000 ROM, 393,216 bytes).
2. Parses all static block-write source tables for Title/Attract, Gameplay, and End-Round — reading the actual tile index words from the arcade ROM data tables at their exact ROM offsets.
3. Discovers strip descriptor tables by pattern-scanning `maincpu.bin` for 16-entry aligned descriptor arrays, then reads all tile index words from those strip tables.
4. Reads the text writer glyph table from ROM offset `0x3BB7C` and extracts all referenced tile indices.
5. Assigns VRAM slots from the two pools (slots 20–1023 = Pool A, slots 1280–1439 = Pool B) using scene-aware packing to minimize per-scene slot counts.
6. Outputs the complete LUT (`build/pc080sn_tile_vram_lut.bin`), per-scene manifests, and the total unique tile count.

The resulting 1,067-slot count is the union of all tile indices referenced across all three scenes, derived directly from the arcade ROM. The per-scene working sets (Title ~820, Gameplay ~817, End-Round ~1,055 as stated in the profiling plan) are also arcade-derived from this same analysis.

**The VRAM budget conclusion stated in the profiling plan is already valid:**

| Check | Value | Result |
|-------|-------|--------|
| PC080SN bulk preload slot range | 0–1,342 | Fits in 1,535-slot VRAM tile region |
| Remaining slots after bulk preload | 193 (slots 1,343–1,535) | Available for PC090OJ sprites |
| Confirmed worst-case sprite slots | 72 (18 cells × 4 slots) | 72 ≤ 193: PASS |
| Stress-test sprite slots (32 cells) | 128 | 128 ≤ 193: PASS |
| Any single mode requiring all 1,067 tiles | NO — End-Round uses ~1,055 | Bulk preload not definitively wasteful |

No additional profiling is required to confirm that bulk preload is safe. The data backing this conclusion comes from arcade ROM static analysis, which is already complete.

The one remaining open question — whether End-Round actually uses 1,055 or a smaller subset — is immaterial to the safety decision. Even if End-Round used all 1,067 tiles, the budget still passes. The profiling plan's Section 8 correctly identifies that mode-scoped preload would yield at most 12 slots of savings in the best case, which is architecturally insignificant.

---

## 6. Acceptable Profiling Methods (if additional data needed)

If future work requires finer-grained per-mode tile counts beyond what the LUT generator already provides, the acceptable methods in order of preference are:

### Method A — Re-run precompute_pc080sn_tile_lut.py with verbose per-scene output

The LUT generator already computes per-scene tile sets (`scene_tile_sets[SCENE_TITLE]`, `scene_tile_sets[SCENE_GAMEPLAY]`, `scene_tile_sets[SCENE_ENDROUND]`). Its `main()` function prints per-scene counts. Running `python3 tools/translation/precompute_pc080sn_tile_lut.py` against the current `build/regions/maincpu.bin` yields the per-scene tile counts immediately. This is already arcade-derived static analysis with zero additional work.

### Method B — Parse the per-scene preload manifests already on disk

`build/pc080sn_scene_preload_title.bin`, `build/pc080sn_scene_preload_gameplay.bin`, and `build/pc080sn_scene_preload_endround.bin` are already generated. Each is a list of `(tile, slot)` pairs terminated by `0xFFFF`. Counting entries in each file gives the per-scene tile count directly. No re-analysis required.

### Method C — MAME dynamic tracing (if static analysis is disputed)

A MAME Lua script can record PC080SN tile index writes per game state register value during a real arcade emulation run. This would capture runtime behavior including any tile indices from dynamically-computed sources that the static scan may miss. This method is valid but more expensive and should only be used if the static analysis results are disputed or if dynamic tile generation is suspected.

### What is NOT acceptable for this phase

Genesis hook instrumentation (`genesistan_tile_slot_observed` bitmask in main_68k.s) is not acceptable for measuring arcade tile working sets while the Genesis wrapper is in a non-functional display state. It may be valid as a post-implementation correctness check (see Section 7) but not as the primary data source.

---

## 7. Future Genesis Profiling Role

Genesis-side profiling instrumentation is not useless — it has legitimate future roles, but those roles are distinct from measuring arcade tile working sets:

### Role 1 — Post-implementation correctness check

After `init_arcade_tile_vram` is implemented and the tile preload pipeline is working, hook instrumentation can verify that the tiles the Genesis wrapper actually commits to VRAM during a play session match the expected subset from the LUT. This is a validation check, not a design input.

### Role 2 — Performance timing

Measuring how long `init_arcade_tile_vram` takes in VBlank time, or whether the per-frame tile commit path stays within the VBlank budget, requires Genesis-side timing. This is a performance concern, not a data content concern.

### Role 3 — Sprite working set verification

The `genesistan_sprite_peak_unique` peak unique cell count per frame is legitimately a Genesis-side measurement because sprite selection is driven by the arcade's sprite object list, which the Genesis wrapper processes. Once the sprite pipeline is functional, recording peak unique cell counts per frame is a valid Genesis-side check to verify the 18-cell assumption. This is a post-implementation activity, not a pre-implementation design input.

---

## 8. Single Root Issue

The profiling plan's Section 6 directed Cody to measure arcade tile working sets by observing what the Genesis hook sees at runtime, but the Genesis wrapper is currently non-functional as a display system and cannot produce representative observations of the arcade game's full tile usage across all modes; the arcade tile working set data is already fully available from the static analysis that generated the LUT.

---

## 9. Single Corrected Next Step

No additional profiling is needed for the bulk-preload safety decision. The correct next step is to confirm that the existing arcade-derived data already in `build/pc080sn_scene_preload_*.bin` and the 1,067-slot LUT are sufficient inputs for implementing `init_arcade_tile_vram`, and to proceed with that implementation as the primary remaining unimplemented pipeline stage — without adding any WRAM bitmask instrumentation to `main_68k.s`.

Specifically: confirm by running `python3 tools/translation/precompute_pc080sn_tile_lut.py` that per-scene tile counts match the estimates in the profiling plan (Title ~820, Gameplay ~817, End-Round ~1,055), then direct Cody to implement `init_arcade_tile_vram` using the already-generated LUT and arcade tile ROM data.

---

## 10. What Must Not Be Changed Yet

All constraints from `Andy_per_mode_vram_working_set_profiling_plan.md` Section 12 remain in force:

- `genesistan_hook_tilemap_plane_a` — nametable translation logic is correct; no WRAM bitmask instrumentation should be added
- `genesistan_pc080sn_tile_vram_lut` and its `.incbin` directive — LUT is correct and must not be regenerated
- `staged_bg_buffer` / `vdp_commit_bg_strips_if_dirty` — nametable staging and commit path is correct
- `_VINT_handler` structure — display-disable bracketing and commit order must not change
- `vdp_commit_tiles_if_dirty` — synthetic tile upload for slots 1–3 must remain
- `init_staging_state` internal logic — must not change
- All 34 `opcode_replace` entries in `specs/rastan_direct_remap.json`
- `rom_absolute_call_relocation` configuration
- A5 initialization to `0xFF0000`
- `VRAM_TILE_BASE = 0x00000020` constant
- All existing build outputs in `build/`
- The patcher (`postpatch_startup_rom.py`)
- Step 6 checkerboard removal must NOT happen yet
- Sprite pipeline base address must NOT be ported until `init_arcade_tile_vram` is implemented and verified

Additionally: no WRAM profiling symbols (`genesistan_tile_slot_observed`, `genesistan_sprite_cell_observed`, `genesistan_sprite_peak_unique`) should be added to `main_68k.s` BSS at this time.

---

## 11. Final Verdict

The per-mode VRAM working set profiling plan's VRAM budget analysis and architecture direction (Option A: bulk preload) are correct and remain valid. The plan's methodology for gathering the per-mode tile data is where the misunderstanding exists: it directed Genesis hook instrumentation when the data was already available from the arcade ROM static analysis that built the LUT.

The 1,067-slot count is arcade-derived. The per-scene working-set estimates are arcade-derived. The VRAM budget math (72 sprite slots needed vs. 193 available) is correct. The conclusion — bulk preload is safe, sprite base address must be 1,343 — is correct.

No additional profiling of any kind is required before implementing `init_arcade_tile_vram`. The Genesis-side profiling described in the original plan's Section 6 should be deferred until after the tile preload pipeline is working, at which point it may serve as a post-implementation correctness check but has no role as a design input.

The implementation path is clear: embed `pc080sn.bin` in the Genesis ROM, implement `init_arcade_tile_vram` iterating the existing LUT, call it between `vdp_boot_setup` and `init_staging_state`, and verify that tiles appear correctly in emulator VRAM inspection.
