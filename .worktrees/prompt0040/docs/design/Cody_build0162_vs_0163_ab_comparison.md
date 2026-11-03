# Cody - Build 0162 vs Build 0163 Controlled A/B Comparison

**Date:** 2026-07-13  
**Type:** Analysis / documentation only  
**Mode:** No build, no source/spec/tool/ROM behavior changes  
**Comparison:** Build 0162 vs Build 0163 forced gameplay sprite tile-refresh experiment

## Purpose

This note compares Build 0162 and Build 0163 as a controlled A/B pair for the gameplay PC090OJ sprite tile-DMA residency experiment.

Important correction carried into this document:

- Build 0163 is **mechanically successful**.
- Build 0163 is **visually inconclusive / possibly masked**.
- Build 0163 is **preserved**.
- Build 0163 is **not accepted as a fix**.
- Build 0163 is **not rejected as useless**.

No fix is attempted here. No build is produced. The temporary Build 0163 source remains in place.

## Phase 0

Relevant priors read:

- `docs/design/Andy_build0163_force_gameplay_sprite_tile_refresh.md`
- `docs/design/Cody_build0163_visual_result_exodus_scroll_boundary.md`
- `docs/design/Cody_pc090oj_gameplay_tile_dma_vram_residency.md`
- `docs/design/Cody_pc090oj_gameplay_representation_activation.md`
- `docs/design/Cody_build0162_vint_timing_trace_classification.md`
- `AGENTS_LOG.md`
- `OPEN_ISSUES.md`
- `KNOWN_FINDINGS.md`

Task classification: **EXTENDING**. This extends the Build 0162/0163 PC090OJ gameplay sprite path and OPEN-017 / OPEN-024 / OPEN-001 visual bring-up evidence.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. Genesis-side code remains helper/service-only. This task changed no runtime behavior.

Contradiction of CONFIRMED/STRONG prior: **NONE**.

## Baseline ROMs

| Field | Build 0162 | Build 0163 |
|---|---|---|
| ROM | `dist/rastan-direct/rastan_direct_video_test_build_0162.bin` | `dist/rastan-direct/rastan_direct_video_test_build_0163.bin` |
| SHA256 | `7bcb31790b2c6db44425655d486c0b74bf3a286a23e77b912594e7e78a9674b9` | `6f6efa750a004e5f74d365eb0d43119e7e88456ae44abc477237af93725171c5` |
| Size | `1,581,228` bytes | `1,581,240` bytes |
| Counter | `162` | `163` |
| `opcode_replace` | `137` | `137` |
| Coverage | `0x1820AC` | `0x1820B8` |
| Status | Passing candidate, not accepted over Build 0160 | Preserved visual-test candidate, not accepted and not rejected |

Accepted build policy: Build 0160 remains accepted unless Tighe explicitly accepts a later build.

## Source-State Preservation

Current source state: **temporary forced-refresh experiment source present**.

The Build 0163 experiment patch is preserved here for later cleanup/design reference:

- `states/traces/build0163_ab_comparison/build0163_forced_refresh_experiment.patch`

Patch summary:

- Adds `.extern genesistan_current_scene_id`.
- Adds `.equ PC090OJ_SCENE_GAMEPLAY_ID, 1`.
- In `.Lpc090oj_worklist_set`, before the resident-code equality check, branches to `.Lwls_differ` when `genesistan_current_scene_id == 1`, forcing represented gameplay slots to requeue tile DMA.
- Does not alter SAT placement, decode, palette, collision, VINT, PC080SN, player state, camera/scroll, or tile indices.

This is preservation only, not acceptance of the experiment as permanent architecture.

## Mechanical A/B Result

Build 0162 mechanical result:

- `tile_dma_count = 0` across gameplay.
- `0/21` sampled gameplay frames queue gameplay sprite tile DMA.
- The residency cache blocks all gameplay sprite tile refresh.

Build 0163 mechanical result:

- Represented gameplay slots requeue tile DMA during gameplay.
- Peak `tile_dma_count = 6`.
- `12/21` sampled gameplay frames re-DMA represented gameplay slots.
- The experiment mechanism is confirmed active and deterministic.

Mechanical classification: **Build 0163 changed real internal behavior exactly at the intended boundary**.

## Visual A/B Method Limits

No new screenshot/video capture was produced in this task. The visual comparison uses Tighe's reported Build 0163 observation and the existing Build 0162/0163 mechanical traces.

This means visual evidence is **not frame-locked** to the mechanical counters in this document. That limitation matters: Build 0163 may be changing sprite tile residency while other defects hide or erase any visible benefit.

## Target-Moment Comparison

| Target moment | Build 0162 evidence | Build 0163 evidence | A/B visual reading |
|---|---|---|---|
| Initial title screen | Frontend known to work from prior Build 0162 candidate evidence | Andy Build 0163 validation: title F=100 represented=15, palette intact | No known regression |
| Throne/story screen | Frontend path alive in prior candidates | Tighe: mostly intact | No known regression |
| `ROUND 1` / `READY` | Gameplay text/dot artifacts present in current line | Tighe: not meaningfully better | No clear improvement |
| First gameplay frames before quick death/removal | Prior traces show gameplay transition and sprite/collision ambiguity | Tighe: Player/Rastan absent or quickly removed/dies | Inconclusive due player lifecycle/death confounder |
| Stable gameplay/flicker window | Build 0162 VINT good; represented accepted records; tile DMA blocked by residency | Build 0163 forces tile DMA but flickering dots still visible | Inconclusive / masked, not proven no-op |
| Player death/removal moment | Player/floor traces remain unresolved; collision path deferred | Tighe: player appears to die quickly again | Confounder present or likely |
| Return-to-title cycle | Returning-title lifecycle not the Build 0162 tile-DMA experiment target | Tighe: some TAITO/title-logo tiles corrupt | Separate scene-transition/LUT/tile-lifecycle issue |

## Required Observation Matrix

| Observation | Build 0162 | Build 0163 | Notes |
|---|---|---|---|
| Scene/state fields | Stable gameplay state `2/2/6` in prior traces | Gameplay F=560: selector `a5@0x10A8=0x0000`; represented=6 | State fields not fully synchronized with user visual frames |
| Screenshot path | None captured in this task | None captured in this task | Visual side is Tighe observation |
| BG visible | Stage 1 BG path alive by prior builds | Gameplay mountain still appears | BG/palette path alive |
| FG visible | Gameplay FG present but not complete in current line | `ROUND 1` / `READY` not meaningfully better | Forced sprite tile refresh did not solve text/dot symptoms |
| Player/Rastan visible | Unresolved / absent in prior visual state | Absent or quickly removed/dies | Not explained by tile refresh alone |
| Flickering dots | Present | Still present | No clear visible improvement |
| Represented sprite count | Stable Build 0162 trace: 14 represented in frames 637/891/1498; Andy F=560 context has 6 represented | Build 0163 F=560 represented=6 | Count depends on sampled logical window |
| `tile_dma_count` | Peak `0`; `0/21` gameplay frames | Peak `6`; `12/21` gameplay frames | Mechanical difference proven |
| Worklist behavior | Residency cache skips gameplay refresh | Gameplay-gated forced requeue activates | Experiment target works |
| Palette lines 0-3 | Build 0162 all four gameplay CRAM lines populated | Build 0163 gameplay F=560: L0=15, L1=14, L2=15, L3=15 | No palette regression indicated |
| Scroll direction | New user observation not from Build 0162 trace | User observes Genesis scroll direction inverted vs arcade | Requires dedicated arcade-vs-Genesis scroll trace |
| Returning-title corruption | Not part of tile-DMA residency experiment | TAITO/title-logo corruption observed on return cycle | Separate deferred lifecycle issue |

## Visual Classification

Classification: **D - Inconclusive / masked**.

Reasoning:

- Build 0163 definitely changes the intended internal mechanism.
- Tighe did not observe a clear visual improvement in the compared windows.
- The absence of clear improvement is not sufficient to reject the experiment because multiple confounders can hide the effect.
- Build 0163 is therefore neither accepted nor rejected from current evidence.

Not A: no clear visual improvement was reported.  
Not B: no clear regression beyond known temporary experiment risks was proven.  
Not C: "no visible change" is too strong because the visual result is not frame-locked and several confounders are active/unknown.  
D is the responsible classification.

## Confounder Checklist

| Confounder | Status | Notes |
|---|---|---|
| Quick player death/removal | Present / likely | Tighe reports Player/Rastan absent or quickly removed/dies |
| Player sprite identity unknown | Present | No arcade-vs-Genesis player record identity trace yet |
| Accepted represented records may be non-player | Present | Records `0x0512/0x0513` have not been proven to be Rastan/player |
| Scroll direction inverted | Present as user observation | Needs dedicated trace |
| Collision WRAM/raw reader unresolved | Present | Collision path remains deferred |
| Exodus stuck in `0x3A346` loop | Present | Exodus not a fair verifier for this result |
| Returning-title tile wipe | Present as user observation | Separate title/LUT/lifecycle issue |
| VDP-visible VRAM/SAT readback unavailable | Present | MAME Lua `videoram` readback invalid in Cody trace |
| Title/logo LUT lifecycle issue | Present / suspected | Returning-title corruption may involve tile lifecycle/reload |

## Exodus Status

Exodus should be treated separately from BlastEm for this A/B result.

Current note:

- Exodus appears stuck in the previously identified `runtime_genesis_pc 0x0003A346` loop.
- Exodus does not reach the same final gameplay/palette state as BlastEm.
- Exodus is therefore not a fair visual verifier for Build 0163's gameplay sprite tile-refresh experiment.
- No Exodus fix was attempted.

## Scroll Observation

Tighe reports that during the original arcade Round 1 fall, BG/FG tiles move upward on screen, while Genesis tested behavior appears inverted with tiles moving downward.

No cause is assigned here. Candidate causes remain:

1. Genesis scroll sign/convention mismatch.
2. PC080SN-to-Genesis scroll conversion sign error.
3. Bad or missing player/camera state.
4. Player death/removal causing camera divergence.
5. Wrong scroll source field routed.
6. Timing/state mismatch during the fall.
7. Correct committed values but inverted VDP interpretation.
8. Arcade/Genesis compared at different logical moments.

## Returning-Title Tile Wipe

Tighe reports that returning to title can corrupt TAITO/title-logo tiles.

This is documented as a separate scene-transition/LUT/tile-lifecycle issue and is not evidence for or against the Build 0163 forced gameplay sprite tile-refresh mechanism.

No returning-title fix was attempted.

## Decision Outcome

Decision: **Build 0163 should remain a live comparison candidate**.

It is:

- preserved;
- mechanically successful;
- visually inconclusive / possibly masked;
- not accepted as a fix;
- not rejected as useless;
- not permanent architecture without further proof.

## Recommended Next Boundary

Preferred next boundary:

> PC090OJ Arcade-vs-Genesis Player Sprite Identity / Lifecycle Trace

Reason: before more sprite rendering fixes, identify whether Genesis ever has the same player/Rastan PC090OJ record that arcade has during early `ROUND 1`, and whether quick death/removal hides the player before the sampled stable gameplay frame.

Secondary boundary:

> PC080SN Arcade-vs-Genesis Gameplay Scroll Direction Trace

Reason: BG/FG scroll direction appears inverted versus arcade during the fall and may share causality with camera/player state.

## Open / Closed Issues Impact

Open issues touched:

- OPEN-001: incomplete/incorrect graphics output context.
- OPEN-017: gameplay bring-up / Build 0163 visual-test candidate context.
- OPEN-024: PC090OJ sprite subsystem incomplete / garbage context.

New issues opened: NONE.  
Issues closed: NONE.  
Issues intentionally deferred: Exodus `0x3A346` loop, scroll-direction trace, returning-title tile lifecycle, collision/player death, VINT, PC080SN/FG_SRC, palette, hardcoded sprites/SAT, second renderer.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. Build 0163's mechanical effect is already documented by Andy; the visual classification remains inconclusive/masked and should not be canonicalized as a durable mechanism until the player identity/lifecycle or scroll trace resolves the masking confounders.

## STOP

STOP triggered: **NO**. The A/B comparison and patch preservation were completed without source/build changes.
