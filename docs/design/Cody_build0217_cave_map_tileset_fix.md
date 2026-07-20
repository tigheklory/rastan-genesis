# Cody - Stage 1 Cave Map/Tileset Selection Fix and Build 0217/0218

**Date:** 2026-07-19  
**Type:** Hybrid targeted analysis / implementation / build continuation  
**Baseline:** Build 0216/256, `dist/rastan-direct/rastan_direct_video_test_build_0216.bin`, SHA256 `6e9ef28d9f44102e8a0312ff27e0efe6d04e5d7cb9d9393417355ae2a443d4a1`  
**Evidence directories:** `states/traces/build0217_cave_map_tileset_fix_20260719_204341/`; `states/traces/build0218_cave_map_tileset_release_20260719_210451/`  
**Scope:** Stage 1 cave PC080SN map/tileset source selection only. No Genesis-owned cave loader, no camera/map replacement, no sprite/enemy/damage/bat/palette implementation, no collision fix, no direct VRAM drawing.

## Phase 0

Classification: **EXTENDING** (OPEN-017 / Stage 1 PC080SN gameplay visual correctness). Relevant priors loaded: KF-010 (BG/FG plane mapping), KF-011 (arcade VBlank owns lifecycle), KF-032 (raw PC080SN writes route through staging), KF-038 (long PC080SN BG/FG row-depth and Stage 1 tall backing/projection), KF-040 (Stage 1 BG producer ownership via `genesistan_hook_itempage_strip_blit`), KF-041 (runtime gameplay tile-preload/LUT source model), KF-045/KF-046 (Stage 1 FG palette context), and KF-068 (Build 0216 IRQ/IPM fix to preserve). Rediscovery Hazard HIGH findings touched: KF-038, KF-040, KF-041, KF-068. No contradiction of CONFIRMED/STRONG findings was found.

Open issues touched: OPEN-017 primary; OPEN-001/OPEN-024 context; OPEN-015 not touched. Closed issues touched: NONE. Deferred appendix entries relevant: NONE.

Architecture compliance: CONFIRMED. The implementation work stays inside Genesis helper/build-time PC080SN translation: arcade producer-owned strip source pointers drive PC080SN tile residency and staging; no Genesis-owned map progression or direct gameplay renderer is introduced.

## Files / Evidence Inspected

- `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, `CURRENT_STATE.md`, and latest `AGENTS_LOG.md` entries.
- `docs/design/Cody_full_arcade_ghidra_disassembly.md` and Ghidra exports under `analysis/ghidra/rastan_arcade/exports/`: `function_inventory.tsv`, `xrefs.tsv`, `call_graph_edges.tsv`, `decompiler_export.c`, `full_listing.tsv`, `linear_disassembly.tsv`, `scalar_constants.tsv`, `hw_refs.tsv`, and `address_correlation_report.json` as available static/reference context.
- `docs/design/Cody_build0215_fg_progression_restoration.md` and `docs/design/Cody_build0216_pc090oj_swarm_stack_fix.md`.
- `apps/rastan-direct/src/tilemap_hooks.s`, `apps/rastan-direct/src/scene_load.s`, `apps/rastan-direct/src/vdp_comm.s`, `tools/translation/precompute_pc080sn_tile_lut.py`, `apps/rastan-direct/Makefile`.
- Build mapping artifacts: `build/rastan-direct/address_map.json`, `specs/rastan_direct_remap.json`, `build/rastan-direct/rastan_direct_patch_manifest.json`, and Ghidra `address_correlation_report.json`.

Mapping/artifact hashes are recorded in `states/traces/build0217_cave_map_tileset_fix_20260719_204341/json_mapping_hashes.txt`. `specs/startup_common_relocations.json` is recorded as MISSING in this workspace.

## Arcade Source-Table / Descriptor Path

The Stage 1 BG strip producer boundary remains the existing item-page strip hook path (KF-040/KF-041): `genesistan_hook_itempage_strip_blit`, installed for the arcade producer at `arcade_pc 0x055C5E` / runtime hook body `genesistan_hook_itempage_strip_blit`.

Static extraction from original `maincpu` data at `arcade_pc/ROM 0x03951C` proves the descriptor table is not only the Build 0154 outdoor attr run:

- Entries `0..55`: attr `0x0002`, source bases `0x00D11C..0x00F11C` (outdoor family).
- Entries `56..111`: attr `0x0003`, source bases `0x00F91C` and `0x01011C` (cave/interior continuation).
- Entry `112` begins attr `0x000A`, intentionally not included in this task.

Evidence files:

- `states/traces/build0217_cave_map_tileset_fix_20260719_204341/arcade_runtime_descriptor_table_3951c_static_extract.tsv`
- `states/traces/build0217_cave_map_tileset_fix_20260719_204341/arcade_descriptor_runs_3951c.tsv`

## Build 0216 / Initial Build 0217 Divergence

Build 0216-era source model and runtime source gate covered only the outdoor family:

- Generator `collect_runtime_gameplay_sources` accepted only attr `0x0002` and stopped before the attr `0x0003` cave run.
- Runtime gate in `genesistan_hook_itempage_strip_blit` used relocated range `[0x0000D31C, 0x0000FB1C)`, which excludes the first relocated cave source `0x0000FB1C` and the second relocated cave source `0x0001031C`.
- Pre-change LUT coverage for cave sources was effectively absent:
  - `arcade_source 0x00F91C`: `404` distinct nonzero codes, `1` mapped.
  - `arcade_source 0x01011C`: `414` distinct nonzero codes, `0` mapped.

Evidence: `states/traces/build0217_cave_map_tileset_fix_20260719_204341/build0216_cave_lut_coverage_before_patch.tsv`.

This is the first proven divergence for the cave interior tile identity path: the arcade producer enters an attr `0x0003` cave source family, but the Genesis PC080SN LUT/residency model and gameplay strip gate exclude it. The wrong repeating brick-like terrain is therefore a source-model / tileset-residency selection defect first, not proven as palette-only, VDP commit, sprite, enemy, or collision behavior.

## Naive Merge Rejected

A direct outdoor+cave merge into the single gameplay PC080SN residency scene is not viable. The generator reported:

```text
scene VRAM budget exceeded: largest scene uses 1422 tiles, budget is 1164
```

Separate measurement shows why:

- Outdoor BG + FG + text: `962` tiles.
- Cave BG + FG + text: `568` tiles.
- Outdoor + cave + FG + text: `1422` tiles.

So the correct translation boundary is not "load all Stage 1 tiles at once". The arcade descriptor/attr transition must select a different PC080SN tile-residency manifest while preserving arcade-owned map progression.

## Source Implementation Staged

The workspace source now contains a split PC080SN residency model, but no corrected numbered ROM has been produced from it.

Implemented source boundary:

- `tools/translation/precompute_pc080sn_tile_lut.py`
  - Adds `SCENE_GAMEPLAY_CAVE = 3`.
  - Maps attr `0x0002 -> SCENE_GAMEPLAY` and attr `0x0003 -> SCENE_GAMEPLAY_CAVE` while walking the same arcade producer-owned table `0x03951C`.
  - Emits `build/pc080sn_scene_preload_gameplay_cave.bin`.
- `apps/rastan-direct/Makefile`
  - Adds missing PC080SN generated-data rules for `rastan-direct` so LUT/preload artifacts are regenerated from the script instead of silently reusing stale binaries.
- `apps/rastan-direct/src/scene_load.s`
  - Adds `genesistan_scene_preload_gameplay_cave`.
  - Allows `load_scene_tiles(3)` to load the cave PC080SN residency manifest while recording logical `genesistan_current_scene_id = 1` so gameplay gates remain intact.
  - Adds `genesistan_current_pc080sn_tileset_id` for PC080SN residency identity.
- `apps/rastan-direct/src/tilemap_hooks.s`
  - Extends the runtime strip source family to `[0x0000D31C, 0x00010B1C)`.
  - Selects tileset `1` for relocated outdoor sources below `0x0000FB1C` and tileset `3` for relocated cave sources at/above `0x0000FB1C`.
  - Continues using the existing tall BG staging route for all gameplay strip sources.

After data-only regeneration, the split model fits:

```text
Title: 845
Gameplay: 962
End-Round: 1067
Gameplay-Cave: 568
VRAM max usage (largest scene): 1067 / 1164
Range overlap check: PASS (disjoint)
```

And cave source LUT coverage becomes complete:

- `0x00F91C`: `404/404` mapped.
- `0x01011C`: `414/414` mapped.

Evidence:

- `states/traces/build0217_cave_map_tileset_fix_20260719_204341/pc080sn_data_regen_split_model_retry.log`
- `states/traces/build0217_cave_map_tileset_fix_20260719_204341/split_model_cave_lut_coverage_after_data_regen.tsv`
- `states/traces/build0217_cave_map_tileset_fix_20260719_204341/split_model_generated_hashes.txt`
- `states/traces/build0217_cave_map_tileset_fix_20260719_204341/assembly_check_after_split_model.log`

Assembly-only verification passed for touched assembly objects:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct out/scene_load.o out/tilemap_hooks.o
```

## Build 0217 Artifact Status / STOP Boundary

A numbered Build 0217 artifact was produced before the PC080SN generated-data gap was discovered:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0217.bin`
- SHA256: `c74adc58b3852c5c3a1a39699de26fd6e41ebbb42cbe379e32c08c9b08dcd369`
- Size: `1,583,868`
- Counter after build: `217`
- Rolling ROM was byte-identical to numbered Build 0217 at production time.
- Gate result: `GATE_PASS`.
- Config: `PC090OJ_MIRROR_RECORDS=256 RASTAN_GAMEPLAY_HUD_SPRITES=0`.

However, immediate post-build evidence showed Build 0217 still used stale PC080SN LUT data for the cave sources. It is therefore **not** a valid cave-fix acceptance artifact. It must be preserved and must not be deleted, overwritten, reconstructed, or reused.

Because Build 0217 is already consumed, the corrected split-model source cannot be released as Build 0217 without violating numbered-artifact preservation. No Build 0218 was produced in this task because the prompt authorized Build 0217, and Build 0217 had already been consumed. The next ROM-producing task should explicitly authorize the next build number.

## Build 0218 Continuation / Artifact Production

Follow-up authorization explicitly preserved Build 0217 as consumed/rejected and released the staged split-residency correction as Build 0218.

Pre-build verification:

- Build 0217 remained present and byte-identical: SHA256 `c74adc58b3852c5c3a1a39699de26fd6e41ebbb42cbe379e32c08c9b08dcd369`, size `1,583,868`, mtime `2026-07-19 20:44:45 -0400`.
- Pre-build counter was `217`.
- PC080SN generated data was regenerated/checked through the new Makefile dependencies.
- Generated data timestamps were newer than the PC080SN region inputs and generator/Makefile edits.
- Cave source LUT coverage remained complete:
  - `0x00F91C`: `404/404` mapped.
  - `0x01011C`: `414/414` mapped.
- Outdoor/cave/end-round residency remained in budget:
  - Gameplay: `3,850` bytes / `962` tiles.
  - Gameplay-Cave: `2,274` bytes / `568` tiles.
  - End-Round: `4,270` bytes / `1067` tiles.
  - Max scene usage: `1067/1164`.

Evidence:

- `states/traces/build0218_cave_map_tileset_release_20260719_210451/prebuild_preservation_hashes_timestamps.txt`
- `states/traces/build0218_cave_map_tileset_release_20260719_210451/prebuild_pc080sn_coverage_budget.tsv`

The first release invocation stopped before numbered artifact production at the canonical invariant gate:

```text
expected total_genesis_bytes_covered=0x182AFC and opcode_replace patched_site count=216;
got total_genesis_bytes_covered=0x183408 opcode_replace patched_site count=216
```

No Build 0218 artifact existed at that point and the counter remained `217`. The paired canonical invariants were updated to the observed mechanical value `0x183408`; opcode_replace count remained `216`.

The second release invocation passed:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0218.bin`
- SHA256: `30a84f86cc34e8dc9861f945138e7aafabe6f072b466fa6d161b8b0e8ed60a95`
- Size: `1,586,184`
- Counter after build: `218`
- Rolling ROM: byte-identical to numbered Build 0218 (`cmp` result `0`)
- Config: `PC090OJ_MIRROR_RECORDS=256`, `RASTAN_GAMEPLAY_HUD_SPRITES=0`
- Gate result: `GATE_PASS`
- opcode_replace count: `216`
- Total Genesis bytes covered: `0x183408`
- Active bookmark count: `0`

Evidence:

- `states/traces/build0218_cave_map_tileset_release_20260719_210451/build0218_release_attempt2.log`
- `states/traces/build0218_cave_map_tileset_release_20260719_210451/build0218_artifact_hashes.txt`
- `states/traces/build0218_cave_map_tileset_release_20260719_210451/build0218_manifest_summary.txt`

Build 0218 materializes the corrected split PC080SN source/residency data:

- Copied generated data artifacts:
  - `states/traces/build0218_cave_map_tileset_release_20260719_210451/pc080sn_tile_vram_lut_build0218.bin`
  - `states/traces/build0218_cave_map_tileset_release_20260719_210451/pc080sn_scene_preload_gameplay_build0218.bin`
  - `states/traces/build0218_cave_map_tileset_release_20260719_210451/pc080sn_scene_preload_gameplay_cave_build0218.bin`
  - `states/traces/build0218_cave_map_tileset_release_20260719_210451/pc080sn_source_scene_map_build0218.bin`
- Source-scene map proof carries `0x00F91C` and `0x01011C` as tileset `3`: `states/traces/build0218_cave_map_tileset_release_20260719_210451/pc080sn_source_scene_map_build0218_xxd.txt`.
- Representative cave cells map to non-`0xffff` LUT slots and Genesis cell words such as `0x606C` and `0x6078`: `states/traces/build0218_cave_map_tileset_release_20260719_210451/cave_representative_cell_mapping.tsv`.

## Build 0218 Runtime Validation Result

Runtime validation did **not** reach a matched Genesis cave state automatically, so cave visual acceptance is not claimed from this task.

What was proven:

- Build 0218 switches into gameplay tileset `1` at frame `326` for the outdoor Stage 1 source family, while preserving logical gameplay scene `1`.
- The long Build 0218 run stayed on outdoor source `0x0000D31C` / tileset `1` through frame `12005`.
- Original arcade MAME with the same input envelope reached a cave-entrance/drop visual by frame `900`.
- Therefore the automated input envelope is not matched between arcade and Genesis for the cave transition. This is a separate progression/combat/input/placement delta, not a proven defect in the split PC080SN cave-residency implementation.

Runtime evidence:

- `states/traces/build0218_cave_map_tileset_release_20260719_210451/build0218_long_cave_runtime_probe.csv`
- `states/traces/build0218_cave_map_tileset_release_20260719_210451/build0218_long_f900.png`
- `states/traces/build0218_cave_map_tileset_release_20260719_210451/build0218_long_f12000.png`
- `states/traces/build0218_cave_map_tileset_release_20260719_210451/arcade_reference_snapshots.csv`
- `states/traces/build0218_cave_map_tileset_release_20260719_210451/arcade_reference_f900.png`

Because Build 0218 did not reach the cave source family during automated runtime validation, there was no concrete bounded Build 0218 cave implementation defect to correct. No Build 0219 was produced.

Build 0218 status: **CANDIDATE / USER MUST VERIFY**. It is mechanically correct for the staged split-residency data and preserves Build 0217, but cave visual acceptance requires a human/manual or better-matched runtime path that actually reaches the cave source family.

## Missing Cave-Cover Ownership Classification

Not proven in this task. The supplied observations about lizards falling into the exposed cave opening and the missing arcade destroyable cover block were recorded, but the cave-cover ownership was not safely classified as tilemap vs destructible actor vs sprite. It should remain deferred until a matched runtime trace can inspect that specific cover cell/object at the cave entrance.

## Validation Not Performed

The required matched-state runtime cave traces and screenshots for original arcade, Genesis Build 0216, and corrected Genesis candidate were not completed because the corrected source was not released to a valid numbered ROM. Runtime claims about corrected cave visuals, camera progression beyond the cave, lizard behavior, bat-swarm regression, collision, BlastEm/Exodus/Nomad behavior, and VBlank boundedness are therefore **not claimed** from this task.

Superseding note after Build 0218: a corrected numbered ROM was produced, but automated Genesis validation still did not reach the cave. Runtime cave visuals, camera progression beyond the cave, lizard behavior at the cave, collision, BlastEm/Exodus/Nomad behavior, and VBlank boundedness therefore remain **not accepted** from automation and require user/manual verification.

## OPEN / CLOSED Issues Impact

- Open issues touched: OPEN-017 primary; OPEN-001 and OPEN-024 context; OPEN-015 not touched.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: matched runtime cave validation, cave-cover ownership, lizard cave fall/damage, bat palette, death splat/dropped-item palettes, item scroll, collision/layout, VBlank/black-bar, and hardware/emulator acceptance.

## KNOWN_FINDINGS Impact

Option C recommended/applied: refine KF-041 with the Build 0217 cave continuation evidence and STOP boundary. The durable lesson is that the Stage 1 runtime producer source model has an attr `0x0003` cave continuation that cannot be merged into the single gameplay PC080SN residency scene; it requires producer-source-selected residency rather than a global outdoor+cave preload.

## STOP

STOP triggered for Build 0217: **YES** for artifact acceptance. Root boundary was proven and source implementation was staged/assemble-checked, but the only produced numbered Build 0217 artifact did not include the corrected generated PC080SN cave data.

STOP triggered for Build 0218 continuation: **NO**. Build 0218 was produced and preserved. No later sequential build was produced because runtime validation did not expose a concrete correctable implementation defect inside the cave tileset/source-selection boundary.
