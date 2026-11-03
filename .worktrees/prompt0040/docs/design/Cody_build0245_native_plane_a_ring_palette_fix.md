# Cody - Build 0246 Native Plane A Ring/Palette Fix

**Date:** 2026-07-30  
**Agent:** Cody  
**Task type:** focused implementation + verification  
**Input baseline:** Build 0245, `dist/rastan-direct/rastan_direct_video_test_build_0245.bin`, SHA `3a6c9bb9731a83ed9c68aa872d36ddb550c6f9175d946232cd9bd28e2d2c057d`, counter `245`  
**Output candidate:** Build 0246, `dist/rastan-direct/rastan_direct_video_test_build_0246.bin`, SHA `52919fe447698baf309350217d83ad972d474b96b8f9f7fb361d365c1d97d83e`, counter `246`

## Phase 0 Baseline

Read before implementation:

- `RULES.md`
- `ARCHITECTURE.md`
- `PROMPT_TEMPLATE.md`
- `AGENTS.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- relevant latest-first `AGENTS_LOG.md` entries
- `docs/design/Andy_build0245_native_plane_a_review.md`
- `docs/design/Cody_build0244_native_selector12_implementation.md`
- `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`

Relevant priors:

- `KF-010`: BG maps to Genesis Plane B; FG maps to Genesis Plane A.
- `KF-011`: original arcade VBlank/progression ownership must remain intact.
- `KF-015`: scroll sign/bias handling is part of the visible-window contract.
- `KF-032`: legacy raw PC080SN writes route through staging, where still present.
- `KF-068` and related native replacement findings: future PC080SN/PC090OJ work must keep the arcade semantic graphics decision and retire chip-specific tails.
- `KF-071`: original native-plane direction proved a full ring model.
- `KF-072`: old compatibility projection cannot be converted piecemeal to full VSRAM without native producer ownership.
- `KF-073`: native Plane A work must prevent transitional projection from overwriting native output.

Classification: `EXTENDING` (`OPEN-001`, native PC080SN Plane A migration).  
Rediscovery hazard: HIGH for `KF-011`, `KF-068`, `KF-071`, `KF-072`, and `KF-073`.  
Contradiction of CONFIRMED/STRONG findings: none.

## Build 0245 Preservation

Before editing, I preserved the Build 0245 source state and artifact hash under:

`states/traces/build0245_native_plane_a_ring_palette_fix_20260730_165141/`

Preserved files include:

- `source_snapshot_0245/src/`
- `source_snapshot_0245/Makefile`
- `source_snapshot_0245/specs/`
- `source_snapshot_0245/translation_tools/`
- `build0245_sha256.txt`
- `pre_edit_production_diff.patch`

No numbered ROM artifact was deleted or overwritten.

## Accepted Review Findings

Andy's Build 0245 review identified two defects in the native Plane A path:

1. **Resident-window placement defect:** selector-0 and selector-1/2 staged Plane A rows using `(logical_row - visible_top) & 31`. That model requires whole-window repaint on vertical camera movement. The native YM7101-compatible model should retain the 64-row logical publication gate but place visible rows into the 32-row Genesis ring at `logical_row & 31`.
2. **Palette-line defect:** native Plane A attributes derived the Genesis palette line from only low bits `word0 & 3`. Stage 1 gameplay FG uses arcade PC080SN bank `3`, whose established route is Genesis CRAM line `1`, not line `3`.

The review also explicitly deferred Plane B. Build 0246 preserves that boundary.

## Implementation

### Selector-0 Ring Placement

`genesistan_hook_tilemap_plane_a_selector0_native` still computes the visible-top logical row and keeps the resident gate:

`((logical_row - visible_top) & 63) < 32`

The physical row written to `staged_fg_buffer` is now:

`logical_row & 31`

Relevant source: `apps/rastan-direct/src/tilemap_hooks.s` lines 182-188 and 249-258.

### Selector-1/2 Ring Placement

`genesistan_hook_tilemap_plane_a_selector12_native` keeps the same 64-to-32 resident gate and now writes the physical row as:

`logical_row & 31`

Relevant source: `apps/rastan-direct/src/tilemap_hooks.s` lines 302-308 and 360-370.

This retains the arcade semantic inputs:

- selector state from `a5+0x10A8`
- strip group/index from `a5+0x10CC` / `a5+0x10CA`
- rebuilt descriptor pointer/word tables
- original source tile/collision words

### Gameplay Plane A VSRAM

`vdp_commit_scroll` now applies full 9-bit gameplay Plane A Y scroll:

`(-staged_scroll_y_fg + VDP_DISPLAY_ORIGIN_Y_BIAS) & 0x01FF`

Relevant source: `apps/rastan-direct/src/vdp_comm.s` lines 467-478.

Plane B remains on the old residual mask:

`(-staged_scroll_y_bg + VDP_DISPLAY_ORIGIN_Y_BIAS) & 0x0007`

Relevant source: `apps/rastan-direct/src/vdp_comm.s` lines 479-486.

### Palette Route

A shared local helper, `.Lplane_a_native_attr_from_word`, now converts native gameplay Plane A descriptor attributes. It extracts the full PC080SN color bank with:

`word0 & 0x01FF`

Then it calls `palette_route_lookup(scene=SCENE_GAMEPLAY_ID, owner=PC080SN_FG, bank)` to select the Genesis CRAM line. Stage 1 gameplay FG bank `3` is routed to Genesis line `1` through the existing palette route table.

Relevant source:

- helper: `apps/rastan-direct/src/tilemap_hooks.s` lines 122-160
- route table: `apps/rastan-direct/src/palette_hooks.s` lines 52-67
- route lookup: `apps/rastan-direct/src/palette_hooks.s` lines 71-85

The helper preserves the proven flip bits:

- PC080SN bit 14 -> Genesis H flip bit `0x0800`
- PC080SN bit 15 -> Genesis V flip bit `0x1000`

Bit 13 was not retained as priority because the local reference material and Andy review marked bit 13 priority as unproven for this path.

Route misses retain the existing low-bank identity behavior for banks not yet represented in the route table. The accepted Stage 1 defect path is bank `3`, which is routed and does not use the miss path.

### Reset/Init Audit

No new reset scaffolding was added. Existing reset/clear points still cover `fg_native_gameplay_owner`:

- boot/bootstrap staging clear
- C-window clear
- `load_scene_tiles` when leaving gameplay logical scene

Relevant source:

- `apps/rastan-direct/src/boot/boot.s`
- `apps/rastan-direct/src/scene_load.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`

## Native-Replacement Policy Check

Semantic cut retained:

- original arcade selector state
- original strip group/index
- original descriptor pointer/word tables
- original source block tile/collision words

Complete chip-specific tail replaced for this scope:

- selector-0 and selector-1/2 do not final-write PC080SN C-window/name-RAM state for gameplay Plane A output
- final output is native Genesis staging plus VBlank Plane A commit

Transitional compatibility still present:

- old tall-FG projection code remains in the binary for non-native/non-gameplay paths
- gameplay native Plane A ownership prevents that transitional projection from overwriting native Plane A output
- Plane B remains transitional and intentionally deferred

Forbidden final architecture introduced: none.

## Build Verification

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result:

- `GATE_PASS`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0246.bin`
- SHA-256: `52919fe447698baf309350217d83ad972d474b96b8f9f7fb361d365c1d97d83e`
- Size: `1588812` bytes
- Counter: `246`
- Rolling artifact `apps/rastan-direct/dist/rastan_direct_video_test.bin` SHA matches the numbered artifact.
- `opcode_replace` patched-site count remains `216`.
- Canonical covered bytes updated to `0x183E4C`; the change is explained in both canonical verification scripts as the consolidation of duplicated native Plane A attr-LUT code into one shared route-table conversion helper.

Scene preload counts from generated manifests:

- Title: `845` tiles
- Gameplay: `962` tiles
- Gameplay cave: `568` tiles
- End-round: `1067` tiles
- Budget: `1164` tiles per residency set
- Result: all active scenes fit the budget.

Note: a stale `build/pc080sn_scene_preload_gameplay_after_rope.bin` artifact exists from rejected earlier work, but Build 0246 `scene_load.s` does not expose or load an after-rope scene.

## Runtime Smoke

The release build ran the standard 30-second MAME Genesis smoke trace:

`states/traces/rastan_direct_video_test_build_0246_mame_30s_20260730_165612/`

Summary:

- external frames: `1798`
- live VDP port writes: `47197`
- live FG C-window writes: `0`
- quick scan found no `Exception`, `ERROR`, `FAIL`, or `GATE_PASS` failure markers in the trace directory.

This smoke trace validates boot/frontend-level execution only. It does not replace the required human Stage 1 visual verification of native Plane A ring behavior and the gameplay FG palette.

## Deferred

- Plane B native conversion and shear correction
- PC090OJ/sprites
- HUD
- input/audio
- rope/progression/collision architecture
- old transitional path retirement outside the gameplay Plane A ownership gate

## Open/Closed Issues Impact

- Open issues touched: `OPEN-001`
- New issues opened: none
- Issues closed: none
- Issues intentionally deferred: Plane B, PC090OJ, HUD, rope/progression/collision, input/audio, broader gameplay visual correctness

## KNOWN_FINDINGS Impact

Option A: no new finding to index. Build 0246 implements the already-reviewed native Plane A ring/palette correction and does not contradict existing CONFIRMED/STRONG findings.

## User Verification Scope

Please test Build 0246 in Stage 1 with a short gameplay run:

1. Start Stage 1 and confirm Plane A foreground rows no longer behave as a vertical resident-window smear during movement/fall/reset.
2. Check that foreground/floor palette uses the expected gameplay FG carrier colors rather than the old wrong line-3 result.
3. Treat Plane B mountain/shear defects as known deferred work, not a Build 0246 acceptance failure unless Plane A regressed independently.
