# Cody Slot Reservation Removal Implementation

Date: 2026-05-07  
Task type: implementation (ROM-producing)  
Primary input: `docs/design/Andy_slot_reservation_removal_classification.md`

## Summary

Implemented Andy's classified fix shape with a single constant change:
- `tools/translation/precompute_pc080sn_tile_lut.py`
- `TILE_CACHE_BASE_A = 20` -> `TILE_CACHE_BASE_A = 0`

Then regenerated LUT + scene preload manifests from the same producer and rebuilt a new sequential ROM.

## Phase A — Precheck

### A.1 Andy fact verification

1. Constant location/value confirmed:
- `tools/translation/precompute_pc080sn_tile_lut.py:39` was `TILE_CACHE_BASE_A = 20` pre-edit.

2. `tiles_dirty` set-to-1 writer check:
- `rg -n "tiles_dirty" apps/rastan-direct/src/` showed only:
  - declaration (`vdp_comm.s:16`, label `vdp_comm.s:301`)
  - read (`vdp_comm.s:184`, `crash_handler.s:251`)
  - clear (`boot.s:176`, `vdp_comm.s:196`)
- No `move #1` / `st` / equivalent writer to 1 found.

3. No post-LUT offset in tilemap hooks:
- BG hook uses LUT directly at `tilemap_hooks.s:168-172`.
- LUT base loaded at `tilemap_hooks.s:115` (and corresponding FG path at `tilemap_hooks.s:287`).
- No extra `+0x14` arithmetic applied after LUT fetch.

### A.2 Pre-regeneration LUT baseline

From `build/pc080sn_tile_vram_lut.bin` pre-change:
- tile `0x20 -> 0x14`
- tile `0x23 -> 0x15`
- tile `0x01 -> 0x52`
- sanity sample: tile `0x40 -> 0x2A`

### A.3 Blank-tile sentinel verification (old slot 0x14)

From `build/pc080sn_scene_preload_title.bin` pre-change:
- slot `0x14` pair was `(tile=0x0020, slot=0x0014)`.

From `build/regions/pc080sn.bin`:
- tile `0x0020` bytes at offset `0x400` (`0x20 * 32`) were all zero:
  - `0000000000000000000000000000000000000000000000000000000000000000`

Result:
- Old slot `0x14` tile was confirmed blank/all-zero.

## Phase B — Single-line implementation + regeneration

### B.1 One-line edit

Changed exactly one line:
- `tools/translation/precompute_pc080sn_tile_lut.py:39`
- `TILE_CACHE_BASE_A = 20` -> `TILE_CACHE_BASE_A = 0`

No other edits were made in this file.

### B.2 Tool rerun

Command:
- `python3 tools/translation/precompute_pc080sn_tile_lut.py`

Stdout summary:
- Title tiles: 841
- Gameplay tiles: 829
- End-Round tiles: 1067
- Total unique: 2326
- VRAM max usage: 1067/1164
- Range overlap check: PASS

Expected regenerated artifacts changed:
- `build/pc080sn_tile_vram_lut.bin`
- `build/pc080sn_scene_preload_title.bin`
- `build/pc080sn_scene_preload_gameplay.bin`
- `build/pc080sn_scene_preload_endround.bin`

Scope guard:
- `build/pc080sn_attr_lut.bin` remained untouched
  - pre/post SHA256 both: `2614c7b4c5ba7716fa6cc985f65ad2832c029956243d5570da52975d230fba3b`

### B.3 Post-regeneration LUT checks

From regenerated `build/pc080sn_tile_vram_lut.bin`:
- tile `0x20 -> 0x00` (was `0x14`)
- tile `0x23 -> 0x01` (was `0x15`)
- tile `0x01 -> 0x3E` (was `0x52`)
- sanity sample: tile `0x40 -> 0x16` (was `0x2A`)
- sample sentinel: tile `0x180 -> 0x00`

All checked mappings shifted by `-0x14`.

## Phase B build outcome

Build steps run:
1. `make -C apps/rastan-direct` (produced numbered build `0058`, but ROM remained byte-identical to `0057` due stale `.incbin` object dependency)
2. `make -C apps/rastan-direct clean`
3. `make -C apps/rastan-direct` (full rebuild including `scene_load.o` with regenerated `.incbin` data)

Final produced ROM artifact:
- `dist/rastan-direct/rastan_direct_video_test_build_0059.bin`
- Makefile output line: `numbered build artifact: ../../dist/rastan-direct/rastan_direct_video_test_build_0059.bin`

SHA256:
- `0057`: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16`
- `0058`: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16` (intermediate stale-object rebuild)
- `0059`: `1135e1aaa2e2c39d64a8390c024dd8e67a998b53f829f2cd7e4eabea2d02ec23` (first ROM containing this fix)

## Phase C — Verification gates

### Gate 1: postpatcher pass
- PASS (postpatch step completed successfully in build log).
- No invariant update required in `postpatch_startup_rom.py` (guard remained satisfied).
- ROM size remained `1559272` bytes pre/post; functional change is in content, not length.

### Gate 2: D00778 verification unchanged/pass
- PASS (unchanged from baseline for this scope).
- 30s trace artifact created by Makefile:
  - `states/traces/rastan_direct_video_test_build_0059_mame_30s_20260507_091617/`
- No new faults introduced in startup trace summary; build/trace completed normally.

### Gate 3: VRAM roundtrip self-test
- PASS (unchanged path).
- `boot.s:165` still invokes `genesistan_pc090oj_dma_self_test`; this implementation did not touch that subsystem.

### Gate 4: tile data now starts at slot 0
- PASS (artifact-level proof).
- Regenerated preload manifests now have `slot_min = 0x0`:
  - title: min `0x0`, max `0x348`
  - gameplay: min `0x0`, max `0x33C`
  - endround: min `0x0`, max `0x53E`
- Title first pair now `(tile=0x20, slot=0x00)` instead of slot `0x14`.
- User visual verification in Exodus Pattern Viewer remains pending for issue closure.

### Gate 5: LUT examples
- PASS
- Verified post-change:
  - `0x20 -> 0x00`
  - `0x23 -> 0x01`
  - `0x01 -> 0x3E`
  - `0x40 -> 0x16`
  - `0x180 -> 0x00`

### Gate 6: Build 55a palette helper patch sites intact
- PASS
- ROM byte-compare (`0057` vs `0059`) at runtime addresses:
  - `0x59CD4` (helper 59ad4 site): unchanged `4eb9000711e24e75`
  - `0x03AD00` (helper 03ab00 site): unchanged `4eb9000712484e75`
  - `0x045FB8` (helper 45db8 site): unchanged `4eb90007126c526d`

### Gate 7: active palette writer hook intact
- PASS
- ROM byte-compare (`0057` vs `0059`) at runtime `0x03BC64` (36-byte replacement span) unchanged:
  - `4eb9000712a04e75` + trailing NOP span remained identical.

### Gate 8: blank-tile sentinel preserved at new slot 0
- PASS
- Post-change title preload pair at slot `0x00` is `(tile=0x0020, slot=0x0000)`.
- Tile `0x0020` pattern bytes are all zero in `build/regions/pc080sn.bin`.
- Old behavior "slot 0 fallback appears blank" is preserved naturally after shift.

## Phase D — Issue linkage

### OPEN-009

Implementation landed with lockstep regeneration and verification pass.
Closure status remains pending user visual verification in Exodus Pattern Viewer.

### OPEN-002

Sequential naming policy preserved (no suffix).  
This task's final ROM is `0059` and constitutes one clean ROM-producing build under the extended policy tracking.

## Files changed by this implementation

- `tools/translation/precompute_pc080sn_tile_lut.py` (1-line edit)
- `build/pc080sn_tile_vram_lut.bin` (regenerated)
- `build/pc080sn_scene_preload_title.bin` (regenerated)
- `build/pc080sn_scene_preload_gameplay.bin` (regenerated)
- `build/pc080sn_scene_preload_endround.bin` (regenerated)
- `dist/rastan-direct/rastan_direct_video_test_build_0059.bin` (new sequential ROM)
- `OPEN_ISSUES.md` (evidence append only)
- `AGENTS_LOG.md` (append only)

No source/spec modifications were made outside the single constant edit.
