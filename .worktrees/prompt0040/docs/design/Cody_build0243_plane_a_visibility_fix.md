# Cody - Build 0243 Plane A Visibility Fix

**Agent:** Cody  
**Date:** 2026-07-29  
**Task:** Continue Build 0243 and restore native Plane A visibility  
**Baseline:** Build 0243, ROM `dist/rastan-direct/rastan_direct_video_test_build_0243.bin`, SHA `9c39607a4964fb0f69e9ea91fdcc2a839427a90dbc190fc1a5e2762f55a39155`, counter `243`  
**Candidate produced:** Build 0244, ROM `dist/rastan-direct/rastan_direct_video_test_build_0244.bin`, SHA `939c303b37b21352f693311cd1df19bbbd87810d2a4419c97ac356366fd99a62`, size `1588476`, counter `244`

## Scope

Focused production fix for the Build 0243 native Plane A selector-0 presentation path. This task does not convert selector-1/2, Plane B, PC090OJ, collision/player-state, rope/post-rope, or palette behavior.

## Phase 0 Baseline

- Relevant priors: KF-010 (BG/FG staging + VBlank commit), KF-011 (arcade VBlank owns lifecycle), KF-015 (PC080SN/tile-cache residency limits), KF-038 (PC080SN gameplay replacement remains staged/native VDP work), KF-072 (native PC080SN/PC090OJ replacement policy).
- Rediscovery-hazard HIGH touched: KF-011 and KF-072.
- Deferred appendix relevant: none found for this narrow Plane A ownership gate.
- Classification: EXTENDING, on OPEN-001.
- Open/Closed issues touched: OPEN-001. OPEN-023/OPEN-024 context only.
- Contradiction of CONFIRMED/STRONG finding detected: NONE.

## Preservation

- Build 0243 source snapshot: `states/traces/build0243_plane_a_visibility_fix_20260729_104631/source_snapshot_0243/`
- Build 0243 production diff vs working git baseline: `states/traces/build0243_plane_a_visibility_fix_20260729_104631/build0243_current_production_diff_vs_git.diff`
- Final Build 0244 production diff: `states/traces/build0243_plane_a_visibility_fix_20260729_104631/build0244_planea_visibility_source_diff_final.diff`
- Builds 0241-0244 SHA evidence: `states/traces/build0243_plane_a_visibility_fix_20260729_104631/preserved_builds_0241_0244_sha256.txt`
- Build logs and copied manifests/symbols are in `states/traces/build0243_plane_a_visibility_fix_20260729_104631/`.

No numbered ROM artifact was deleted or overwritten.

## Evidence Inspected

- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/boot/boot.s`
- `apps/rastan-direct/src/scene_load.s`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- Build 0243 route evidence from `docs/design/Cody_build0242_selector0_route_fix.md` and `states/traces/build0242_selector0_route_fix_20260728_173622/`.

## Problem Statement

Build 0243 proved that the byte-neutral selector-0 route executes and that `genesistan_hook_tilemap_plane_a_selector0_native` writes final resident Plane A words into `staged_fg_buffer` while setting `fg_row_dirty`.

However, the VBlank order was still:

1. `vdp_project_fg_tall_if_dirty`
2. `vdp_commit_fg_narrow_strips`
3. `vdp_commit_fg_strips_if_dirty` via tail branch

The transitional tall-FG projector copied `staged_fg_tall_buffer` into `staged_fg_buffer` before the row commit. That creates a stale-overwrite hazard for native selector-0 words.

## Overwrite Proof

Proven Build 0243 route evidence:

- `HELPER_ENTRY_704A4=64`
- `HELPER_RTS_70602=64`
- `RETURN_CONT_55B54=64`
- Helper final Plane A staging writes: `FG_STAGE_WRITE pc=0705D8 count=2048`
- Transitional projector writes into the same `staged_fg_buffer`: `FG_STAGE_WRITE pc=07021A count=47104`
- VBlank commit reads from `staged_fg_buffer` and commits dirty rows to Plane A.

Static Build 0244 disassembly confirms the relevant order remains:

- `_vblank_service` calls `vdp_project_fg_tall_if_dirty` at `runtime_genesis_pc 0x000700DA`.
- `_vblank_service` calls `vdp_commit_fg_narrow_strips` at `runtime_genesis_pc 0x000700DE`.
- `vdp_commit_fg_narrow_strips` tail-branches to `vdp_commit_fg_strips_if_dirty`.
- `vdp_commit_fg_strips_if_dirty` DMA-commits rows from `staged_fg_buffer` to Plane A VRAM.

The native writes were real, but the transitional tall projector still had authority to replay older `staged_fg_tall_buffer` data over `staged_fg_buffer` before the final row commit.

A compact Build 0243 runtime overwrite trace was attempted in `states/traces/build0243_plane_a_visibility_fix_20260729_104631/`; MAME debugger/API limitations and lack of automated gameplay reach prevented a new representative-cell hit. The conclusion does not rely on that failed compact trace alone; it is supported by the already-preserved Build 0243 route trace plus the VBlank ordering in source/disassembly.

## Fix Implemented

Added a bounded native Plane A gameplay ownership flag:

- Symbol: `fg_native_gameplay_owner`, Genesis-WRAM `0x00FF4056` in Build 0244.
- Setter: `genesistan_hook_tilemap_plane_a_selector0_native` sets `fg_native_gameplay_owner=1` at entry after establishing the arcade WRAM base.
- Clearer 1: `_bootstrap_clear_staging` clears it during startup staging reset.
- Clearer 2: `genesistan_hook_cwindow_clear` clears it when arcade clear semantics reset C-window staging.
- Clearer 3: `load_scene_tiles` clears it when the logical scene is not gameplay; cave tileset ID 3 is normalized to gameplay scene ID 1 and keeps the gameplay owner state.
- Consumer: `vdp_project_fg_tall_if_dirty` exits immediately in gameplay when `fg_native_gameplay_owner != 0`.

This isolates the transitional tall-FG compatibility projector from overwriting native selector-0 Plane A output. It does not create a new renderer or shadow path: native output still flows through `staged_fg_buffer -> fg_row_dirty -> VBlank row commit -> Plane A VRAM`.

## Code Locations

- Native owner set: `apps/rastan-direct/src/tilemap_hooks.s` in `genesistan_hook_tilemap_plane_a_selector0_native`.
- Native owner clear: `apps/rastan-direct/src/boot/boot.s` in `_bootstrap_clear_staging`.
- Native owner clear: `apps/rastan-direct/src/tilemap_hooks.s` in `genesistan_hook_cwindow_clear`.
- Native owner scene clear: `apps/rastan-direct/src/scene_load.s` in `load_scene_tiles`.
- Projector guard: `apps/rastan-direct/src/vdp_comm.s` in `vdp_project_fg_tall_if_dirty`.

## Selector-0 Route Verification

Build 0244 postpatch bytes/disassembly:

- `runtime_genesis_pc 0x00055B50`: `bsrw 0x55B68` retained.
- `runtime_genesis_pc 0x00055B68`: `jmp 0x704AC` to `genesistan_hook_tilemap_plane_a_selector0_native`.
- `runtime_genesis_pc 0x000704AC`: native helper entry.
- Helper still avoids using `a5+0x10A0` / `0x00C08000` as the selector-0 final output authority. Mentions remain only in unrelated legacy comments/equates and old compatibility helpers.

## VBlank / Commit Verification

Build 0244 symbols:

- `_vblank_service`: `runtime_genesis_pc 0x000700C2`
- `vdp_project_fg_tall_if_dirty`: `runtime_genesis_pc 0x000701B6`
- `vdp_commit_fg_narrow_strips`: `runtime_genesis_pc 0x00071F86`
- `vdp_commit_fg_strips_if_dirty`: `runtime_genesis_pc 0x000702F0`
- `staged_fg_buffer`: Genesis-WRAM `0x00FF70EC`
- `staged_fg_tall_buffer`: Genesis-WRAM `0x00FF80EC`
- `fg_row_dirty`: Genesis-WRAM `0x00FF404E`

The final row commit still reads from `staged_fg_buffer` and writes Plane A VRAM. The tall projector can no longer copy `staged_fg_tall_buffer` over native gameplay output once selector-0 native ownership is established.

## Plane A VSRAM Audit

No VSRAM change was made. The current gameplay FG Y-scroll residual mask remains in `vdp_commit_scroll`:

- scene gameplay path keeps `staged_scroll_y_fg` to `& 0x0007` after negation/origin bias.

This task did not prove a native coordinate-contract need to change VSRAM, so it was intentionally left intact.

## Selector-1/2 Dependency

Selector-1/2 are not converted in this task. They remain a deferred dependency. Once selector-0 native gameplay ownership is active, the tall-FG compatibility projector is suppressed for gameplay, so selector-1/2 outputs that still depend on tall compatibility may not be complete. That is intentionally not hidden or claimed as fixed.

Removal boundary: after Plane A selector-1/2 and any remaining frontend Plane A semantic tails are replaced natively, remove `fg_native_gameplay_owner`, retire gameplay use of `vdp_project_fg_tall_if_dirty`, and remove the transitional gameplay `staged_fg_tall_buffer` dependency.

## Plane B / Other Systems

Plane B was not changed. PC090OJ, collision/player-state, rope/post-rope, palette behavior, audio, and input were not intentionally changed.

## Canonical Invariant Update

The first Build 0244 attempt failed the strict canonical coverage gate:

- expected coverage: `0x183CDC`
- observed coverage: `0x183CFC`
- opcode_replace patched-site count: `216`

The coverage increase is the exact 32-byte helper/ownership-gate growth. The canonical gate was updated to `0x183CFC` in both postpatch and verify scripts. The opcode replacement count remains `216`; the gate was not weakened.

## Build 0244 Verification

- Build command: `source tools/setup_env.sh && make -C apps/rastan-direct`
- Result: `GATE_PASS`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0244.bin`
- SHA-256: `939c303b37b21352f693311cd1df19bbbd87810d2a4419c97ac356366fd99a62`
- Size: `1588476`
- Counter: `244`
- Rolling artifact matches numbered artifact: YES
- Manifest build context: `canonical`
- Opcode replacement count: `216`
- Address-map coverage: `0x183CFC` (`1588476` decimal), no gaps, no overlaps
- Bookmarks active: NO (`bookmarks_v2_count=0`, `bookmarks_v2_applied=[]`)

## Smoke Trace

Trace: `states/traces/rastan_direct_video_test_build_0244_mame_30s_20260729_105440/`

- Frames: `1798`
- `fg_cwindow_live count=0`
- VDP port live writes present: `47197`
- No live FG C-window writes observed in the 30-second smoke window.

This smoke trace does not reach a manual Stage 1 gameplay visibility test. User verification remains required.

## User Test Scope

1. Boot Build 0244 and confirm frontend/title still reaches normal attract/start flow.
2. Start Stage 1.
3. Check whether the first gameplay Plane A foreground/ground columns are visible after READY.
4. Confirm Plane B background is not newly regressed.
5. Note selector-1/2-dependent gaps separately; those are not claimed fixed by this build.

## Open/Closed Issues Impact

- Open issues touched: OPEN-001.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: selector-1/2 Plane A native tails, Plane B native replacement, PC090OJ, rope/post-rope, collision/player-state, broader gameplay visual correctness.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This is a bounded implementation correction for the current native Plane A migration path and does not establish a new durable system behavior beyond the existing native-replacement policy and VBlank staging findings.

## STOP Status

STOP not triggered. Build 0244 was produced and preserved for user testing.
