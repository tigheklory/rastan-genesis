# Cody - Build 0172 Stage 1 Ground/Floor Foreground Boundary Candidate

**Date:** 2026-07-14
**Type:** Analysis-first runtime evidence + STOP/no-build boundary
**Baseline:** Build 0171 candidate ROM `dist/rastan-direct/rastan_direct_video_test_build_0171.bin`
**Baseline SHA256:** `819a2131a7643135b46c6faaaf00153ac95c37fae2ed357659fed74075d45ab9`
**Scope:** Stage 1 visible ground/floor plane ownership and staging boundary only. No source/spec/tool/ROM/invariant edits. No build. No collision, PC090OJ, D00298, Exodus-loop, continue/game-over, or input fix.

## Phase 0

Classification: **EXTENDING** (OPEN-017 / OPEN-001 graphics bring-up). Relevant priors loaded: KF-010 (BG/FG staging and Plane B/A ownership), KF-032 (PC080SN writes route through staging), KF-038 (long PC080SN BG rows alias / Build 0170-0171 tall BG model), KF-041 (Stage 1 BG source family and `load_scene_tiles(1)`), and OPEN-017 Build 0170/0171 tall-BG projection context.

Rediscovery-hazard findings touched: KF-010, KF-032, KF-038, KF-041. No contradiction detected.

Architecture compliance: **CONFIRMED**. The trace observes arcade-produced PC080SN state and Genesis staging/commit-adjacent state. No Genesis-owned game control flow, no scaffold renderer, no bypass, no state forcing.

## User Visual Baseline Recorded

Tighe's Build 0171 visual observations are carried forward as input evidence:

- The background is now fixed or much closer.
- The sky is mostly correct.
- The mountain/background layout is much closer than Build 0169/0170.
- The left wall appears.
- The floor/ground under Rastan is still missing.
- A large black horizontal playfield gap remains where the floor/playfield should continue.
- Rastan appears to crouch or duck as if down is being held.
- Directional/jump/attack input still appears ineffective.
- The next focus should be the foreground/ground path.

The runtime trace below tests the floor/ground ownership boundary; it does not attempt to fix input or player-state behavior.

## Evidence Artifacts

Trace directory: `states/traces/build0172_stage1_ground_fg_boundary_20260714_215247/`

Key files:

- `ground_boundary_trace.lua`
- `ground_boundary_trace_v1.lua` (superseded; used full BG scroll for staged BG indexing)
- `arcade_zero_ground_samples.csv`
- `arcade_zero_ground_summary.log`
- `genesis_zero_ground_samples_v2.csv`
- `genesis_zero_ground_summary_v2.log`
- `genesis_zero_vram_boundary.csv` (VDP VRAM readback attempt; inconclusive)
- `vram_probe.log` (confirms MAME `:gen_vdp` videoram space readback returned zero in this harness)
- short input-case summaries: `genesis_down_*`, `genesis_up_*`, `genesis_left_*`, `genesis_right_*`, `genesis_jump_*`, `genesis_attack_*`

The original arcade run and Build 0171 run both exited with status `0`.

## Plane Ownership Result

The sampled post-landing floor/playfield band is primarily **BG / PC080SN page 0** owned. Arcade FG/Plane A contains sparse overlay cells and many transparent/blank cells (`0x0020`).

Representative arcade samples:

| Screen sample | Arcade BG attr/code | Arcade FG attr/code | Interpretation |
|---|---:|---:|---|
| `sky_control` `16,2` | `0002/05F5` | `0003/0020` | BG-owned control |
| `mountain_control` `16,8` | `0002/065E` | `0003/0020` | BG-owned control |
| `player_feet` `2,14` | `0002/06AB` | `0003/0420` | BG floor plus sparse FG overlay |
| `left_wall_floor` `4,15` | `0002/06B5` | `0003/0426` | BG floor/wall plus sparse FG overlay |
| `gap_left` `8,16` | `0002/0696` | `0003/0020` | BG-owned floor/gap band |
| `gap_mid` `16,17` | `0002/06A5` | `0003/00BF` | BG-owned plus sparse FG overlay |
| `lower_ground_mid` `20,22` | `0002/06B1` | `0003/00D6` | BG-owned plus sparse FG overlay |

Conclusion: the missing visible floor/black gap should not be treated as a simple FG-only ownership failure. FG contributes some details, but the main terrain/floor band is BG-owned.

## Genesis BG Floor Cells

At Build 0171 frame `820` and again at frame `1400`, the sampled BG floor/playfield cells match arcade BG intent through `genesistan_pc080sn_tile_vram_lut`.

Representative Build 0171 frame `820` results:

| Screen sample | Arcade BG code -> LUT slot | Genesis staged BG slot | Tall BG slot | Result |
|---|---:|---:|---:|---|
| `sky_control` | `05F5 -> 01BB` | `01BB` | `01BB` | MATCH |
| `mountain_control` | `065E -> 0224` | `0224` | `0224` | MATCH |
| `player_feet_left` | `07DC -> 03A2` | `03A2` | `03A2` | MATCH |
| `player_feet` | `06AB -> 0271` | `0271` | `0271` | MATCH |
| `left_wall_floor` | `06B5 -> 027B` | `027B` | `027B` | MATCH |
| `gap_left` | `0696 -> 025C` | `025C` | `025C` | MATCH |
| `gap_mid` | `06A5 -> 026B` | `026B` | `026B` | MATCH |
| `gap_right` | `0676 -> 023C` | `023C` | `023C` | MATCH |
| `lower_ground_mid` | `06B1 -> 0277` | `0277` | `0277` | MATCH |
| `bottom_mid` | `0686 -> 024C` | `024C` | `024C` | MATCH |

Frame `1400` repeated the same 14/14 sampled BG matches. Frame `751` was partially mismatched, consistent with the previously documented Build 0171 frame-boundary caveat where post-frame sampling can see the next scroll value before the projection base updates.

## Genesis FG Floor Cells

FG is mostly transparent/blank in the sampled floor band. The FG staging result is mixed but not enough to explain the whole black floor gap as FG-only:

- Arcade FG blank `0x0020` maps to LUT slot `0x0000`; Build 0171 FG cells are generally `0x6000` (attribute with slot `0`) or `0x0000`, which is consistent with transparent/blank output for many samples.
- Sparse overlay samples differ or are absent, e.g. arcade `player_feet` FG `0x0420 -> slot 0x0060`, while Build 0171 has `0x0000`; `left_wall_floor` at frame `820` matches (`0x0426 -> 0x0065`, Build `0x6065`).
- The missing sparse FG overlays may affect visual detail, but the main floor/terrain cells are proven BG-owned and present in Build 0171 staging.

Conclusion: a tall-FG or FG-source expansion may still be needed later for overlay correctness, but this trace does **not** prove it as the smallest safe fix for the missing floor/black-gap symptom.

## Commit / VDP Readback

`fg_row_dirty` and `bg_row_dirty` are clear by the sampled steady frames, which is consistent with rows having been committed before sampling. The normal VBlank path calls:

- `vdp_project_bg_tall_if_dirty`
- `vdp_commit_bg_strips_if_dirty`
- `vdp_commit_fg_narrow_strips`
- `vdp_commit_fg_strips_if_dirty`

An attempted readback from MAME's `:gen_vdp` `videoram` address space in `-video none` returned zero for all probed regions, including regions that should be visibly populated. This is therefore recorded as **MAME VDP VRAM readback inconclusive**, consistent with the older OPEN-003 class of MAME/VDP readback caution. It is not used as evidence that VBlank commit failed.

## Tile Residency / Palette / Priority

Tile residency is not proven bad:

- Every sampled arcade BG floor code has a nonzero LUT slot in `build/pc080sn_tile_vram_lut.bin`.
- `load_scene_tiles(1)` directly uploads gameplay scene tile patterns to VDP VRAM from `genesistan_scene_preload_gameplay`; the sampled floor slots are in the same mapped gameplay tile family.
- Runtime VDP pattern readback was inconclusive because MAME's VDP videoram space returned zero in this harness.

Priority/palette is not proven bad:

- Sampled BG floor/playfield cells use arcade attr `0x0002`, mapping through existing PC080SN attr logic to the same Genesis plane line family used by other visible terrain.
- No source-side evidence in this trace shows priority hiding the floor behind FG/Window/SAT.

## Collision Relationship

The collision side-channel is adjacent but not the first divergence here. Several sampled lower rows have nonzero collision words (`0x0001`, `0x0020`, `0x3400`), but the visual BG floor cells are already staged and mapped correctly at frame `820+`. Collision may still explain player/control/landing behavior, but it does not explain missing BG floor staging in this trace because BG floor staging is present.

## Crouch / Input Classification

The short MAME input-case traces did not produce distinct shadow changes across the attempted directional/button cases (`0x43/0x77/0x43/0x68` remained the observed steady shadow tuple), so this task does **not** prove down-held input, input polarity, or control-lock. The crouch/duck visual remains user-observed and should be treated as unresolved: possible causes still include input mapping, player state/control-lock, collision/terrain state, animation state, or script-input limitations.

No input fix is supported by this task.

## Classification

**STOP for Build 0172 implementation.**

The requested safe boundary is not proven. Specifically:

- Ground/floor plane ownership: **BG-primary**, sparse FG overlays.
- Arcade floor cells: **present** in BG and sparse FG.
- Genesis BG floor cells: **present and matching arcade via LUT** in sampled steady frames.
- Genesis FG floor cells: **mostly blank/transparent; sparse overlays incomplete**, but not the main floor owner.
- Tile residency: **expected by LUT/preload; VDP readback inconclusive**.
- FG staging: **not the primary floor-band failure in this trace**.
- FG commit: **no dirty-stuck evidence; VDP readback inconclusive**.
- Priority/palette: **not proven as the fix locus**.
- Tall-FG/row-alias: **not proven as the smallest safe floor fix**.
- Remaining BG-floor result: **staged/projected/mapped correctly at frame 820+**.
- Black horizontal gap result: **real user-visible symptom, but not explained by BG/FG staging ownership in this trace**.

Because the measured floor cells are already correct in BG staging/projection, a Build 0172 source change would be speculative and would violate the state-causality rule.

## Recommended Next Diagnostic

Recommended next task, still no implementation first: capture an emulator-side visual/VDP correlation where screenshots and plane data are sampled from the exact same rendered frame/window. The next diagnostic should use an Exodus-side capture or a MAME mode that can reliably read VDP VRAM/CRAM, and should correlate:

- rendered screen pixels in the black-gap band,
- Plane B nametable words at the exact displayed rows,
- Plane B pattern bytes for slots `0x01BB`, `0x0224`, `0x0271`, `0x027B`, `0x025C`, `0x026B`, `0x0277`,
- CRAM line used by attr `0x0002`,
- VDP display/window/plane registers,
- Window/Plane A/SAT coverage at those pixels.

This would decide whether the black gap is a VDP pattern residency/readback issue, palette issue, display/window masking issue, frame mismatch, or a visual-observation mismatch with the sampled post-landing state.

## Non-Actions

No source edits. No spec edits. No tool edits outside disposable trace scripts under `states/traces`. No ROM/build/invariant changes. No collision fix. No input fix. No PC090OJ work. No D00298/Exodus-loop work.

## Open / Closed Issues Impact

Open issues touched: OPEN-017, OPEN-001 context, OPEN-003 context for MAME VDP readback caution. New issues opened: none. Issues closed: none. Intentionally deferred: exact black-gap VDP/pixel attribution, sparse FG overlay completeness, input/crouch/control-lock, collision byte-equivalence, real Genesis behavior, PC090OJ/READY/header, VBlank/rolling bar/slowdown, continue/game-over, D00298, Exodus loop, records `132..134`.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed. This trace narrows a candidate but does not establish a durable new mechanism. It also does not contradict KF-038; Build 0171 tall-BG projection is reinforced for the sampled steady floor rows.

## STOP

STOP triggered: **YES for implementation/build**. Evidence supports documentation and next diagnostic only; Build 0172 was not produced.
