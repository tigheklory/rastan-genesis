# Cody - Build 0158 Player Death/Fall Boundary Analysis

**Date:** 2026-07-10
**Type:** Analysis-first / no-build stop
**Build context:** Build 0157 accepted as internal PC090OJ SAT prerequisite; Build 0158 not produced
**Baseline branch / HEAD:** `rastan-direct-proposal` / `e4297f4`
**Accepted ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0157.bin`
**Accepted ROM SHA256:** `725c36a27a4ea55a4a99bcbca4bd5dde3bbaf00cffe6b5005b8997b90cdd2c4a`
**Counter:** `157`
**Scope:** Analysis only. No source/spec/tool/Makefile/ROM/build/invariant changes. No new trace. No collision, scroll, continue/game-over, D00298, Exodus, broad sprite, or tilemap work.

## 1. Phase 0 Result

Relevant priors from `KNOWN_FINDINGS.md`:

- `KF-010` - BG maps to Genesis Plane B and FG maps to Plane A.
- `KF-011` - arcade Level-5 VBlank owns frame progression; Genesis VBlank is servicing-only.
- `KF-032` - copied arcade writes into PC080SN/PC090OJ hardware space must route through translated staging, not raw Genesis VDP mirror space.
- `KF-039` - arcade work-RAM absolute pointers map through the A5 base `0x0010C000` to Genesis WRAM `0x00FF0000`.
- `KF-040` / `KF-041` - Stage 1 gameplay BG/producer source-model boundaries are settled for the current pipeline.

Rediscovery Hazard HIGH findings touched:

- `KF-011`, `KF-032`, `KF-039`, `KF-040`, and `KF-041`. None are contradicted.

Task classification: **EXTENDING**. This extends the active gameplay graphics/control bring-up after Build 0157's PC090OJ SAT prerequisite.

Open/Closed issues touched:

- Open: `OPEN-001`, `OPEN-017`, `OPEN-024`; `OPEN-018` context only.
- Closed: none reopened.

Contradiction of CONFIRMED or STRONG finding: **NONE**.

## 2. Baseline

- Branch: `rastan-direct-proposal`
- HEAD: `e4297f4`
- Git status at start included pre-existing generated trace dirt: `build/mame/home/genesistrace/genesis_exec_trace.log`
- Accepted build: `0157`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0157.bin`
- SHA256: `725c36a27a4ea55a4a99bcbca4bd5dde3bbaf00cffe6b5005b8997b90cdd2c4a`
- Counter: `157`

Build 0157 is treated only as internal PC090OJ SAT plumbing evidence. It is **not** treated as proof that visible gameplay sprites are solved.

## 3. Files / Evidence Inspected

Mandatory reads completed:

- `AGENTS.md`
- `RULES.md`
- `ARCHITECTURE.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- Latest relevant `AGENTS_LOG.md` entries

Recent design docs read:

- `docs/design/Andy_build_0157_pc090oj_dirty_candidate_scan.md`
- `docs/design/Cody_build0157_pc090oj_candidate_dirty_handoff.md`
- `docs/design/Andy_build_0156_c08c66_fg_digit_route.md`
- `docs/design/Andy_build_0155_stage1_fg_live_boundary.md`
- `docs/design/Andy_build_0154_runtime_gameplay_tile_model.md`

Trace/evidence inspected:

- `states/traces/build_0157_gameplay_sprites/`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- Existing nearby Stage 1 traces were searched for player/death/floor/collision terms, but no current arcade-vs-Genesis player-state timeline was found.

No exact filename substitutions were needed for the requested Build 0154-0157 design docs.

## 4. SAT Sanity Check Result

Classification: **A - SAT is plausible enough to move to player death/fall.**

Evidence from existing Build 0157 traces:

- `states/traces/build_0157_gameplay_sprites/gen_active.txt`: active gameplay reaches `represented=10..11`, `staged_active=11`, `sat_dirty=0001`, `mirror_dirty=0000` at frames `533..534`.
- `states/traces/build_0157_gameplay_sprites/gen_sat.txt`: staged SAT entries exist at frames `533..534` with nonzero Genesis SAT words.
- Representative Build 0157 entry at frame 534: `slot1: 0088 0506 C404 0128`.

Interpretation of representative entry:

- Y `0x0088` is on-screen/plausible.
- Size/link `0x0506` uses the expected 16x16-size form with a nonzero chain link.
- Attribute `0xC404` has priority/palette/tile bits and a nonzero tile index in the sprite tile region.
- X `0x0128` is on-screen/plausible.
- `pc090oj_hooks.s` shows `staged_sprite_sat` is the SAT DMA source at `.Lvcs_sat_dma` (`move.l #staged_sprite_sat,%d0`) and that SAT DMA is gated by `pc090oj_sat_dirty`.

Caveat:

- At the later stable painted-plane sample (`gen_v57b.txt`, frame 601), `represented=6`, `sat_dirty=0`, and the dumped SAT source words are zero. Andy's Build 0157 doc already records this timing split: the active sprite window precedes the plane-paint window because Rastan dies/falls almost immediately. This does not make SAT the first blocker for this task; it reinforces why the next boundary is control/death/fall timing.

## 5. Arcade Player-State Timeline

**Not captured in the existing evidence.**

Existing arcade traces in `states/traces/build_0157_gameplay_sprites/` capture PC090OJ record counts and state words, not the requested player object structure, player X/Y, velocity, action, alive/death/fall flags, life count, collision/floor lookup inputs/outputs, or object/collision routine PCs.

Examples:

- `arc_real.txt` proves `state=2/3/0` and `236` coded PC090OJ records.
- `arc_sprites.txt` captures PC090OJ record snapshots at `round1_ready`, `gameplay_early`, and `gameplay_active`.

These do not identify the player object or collision/floor routine.

## 6. Genesis Player-State Timeline

**Not captured in the existing evidence.**

Existing Genesis traces capture state words, object-RAM counts, candidate/SAT data, and staging state. They do not capture the requested player object structure, player X/Y, world X/Y, velocity, action, alive/death/fall flags, life count, collision/floor lookup inputs/outputs, or object/collision routine PCs.

Examples:

- `gen_v57.txt`: frame `533`, state `2/3/0`, `candidate_bitset_nz=31/32`, `object_coded=205`, `represented_count=10`, `staged_sprite_active_count=11`, `sat_dirty=0001`.
- `gen_v57b.txt`: frame `601`, state `2/3/0`, `staged_bg=2048`, `staged_fg=2020`, but `represented=6`, `sat_dirty=0000`, SAT source dump zero.

These traces establish the SAT timing boundary, not the player death/fall state-causality boundary.

## 7. First Exact Divergence

**Not proven.**

The first exact player death/fall divergence cannot be classified under A-I because the required same-timeline arcade-vs-Genesis player/collision data is absent.

What is proven:

- Build 0157 produces plausible early gameplay SAT entries through the existing PC090OJ path.
- The later visible painted-plane sample occurs after the active SAT window has collapsed/stopped.
- Current user-visible behavior reports immediate fall/death and vertical scroll into black.

What is not proven:

- Whether the player object never initializes.
- Whether player X/Y initializes incorrectly.
- Whether velocity/gravity differs.
- Whether collision/floor lookup reads the wrong table/address.
- Whether collision/floor returns empty/wrong.
- Whether a death/offscreen flag is set incorrectly.
- Whether camera/scroll divergence causes normal player state to appear wrong.

## 8. State-Causality Answers

Patch gate status: **not satisfied**.

1. What state should exist at this PC?
   - Not answerable yet. The relevant PC/player object/collision/floor routine has not been identified.

2. Which earlier code is responsible for creating that state?
   - Not answerable yet. The producer/initializer for the player object's initial gameplay state has not been identified in the current evidence.

3. Why did that state not get created?
   - Not proven. The current evidence does not show whether the player state is missing, wrong, overwritten, or correct but misinterpreted by collision/floor/death logic.

Result: **do not patch**.

## 9. Collision / Floor Lookup Evidence

No current evidence identifies the collision/floor routine PC or its inputs/outputs in both arcade and Genesis.

Existing Build 0154-0157 docs explicitly defer collision/falling:

- Build 0154: gameplay sprites, scroll, controls, collision, and audio remain next boundaries.
- Build 0155: scroll and gameplay sprites remain deferred.
- Build 0156: repeated fall/death is downstream of sprite + scroll + collision.
- Build 0157: player death/fall and scroll/camera are the next focused boundary after SAT handoff.

This task does not have the collision/floor routine identity needed for a bounded implementation.

## 10. Camera / Scroll Evidence

No Build 0157 same-window arcade-vs-Genesis camera/scroll comparison was captured for the death/fall boundary.

Relevant prior evidence:

- Build 0155 plane-composition traces include arcade scroll writes during `2/3/0`, but those are not synchronized against Build 0157 player death/fall state.
- Build 0157 gameplay sprite traces do not capture `staged_scroll_*` or arcade camera/scroll fields at frames 10/30/60 after active gameplay.

Therefore camera/scroll cannot be ruled in or out as the first death/fall divergence.

## 11. Implementation Boundary Or No-Build Reason

No Build 0158 was produced.

No-build reason:

- The task requires same-timeline arcade and Genesis player-state comparison through first life loss.
- The current evidence does not locate the player object structure in both arcade and Genesis.
- The current evidence does not identify the collision/floor routine PC or its lookup inputs/outputs.
- The state-causality rule cannot be answered.
- Any patch now would risk hardcoded survival, hardcoded floor/collision, Genesis-owned gameplay control, or another forbidden workaround.

Minimum specific additional evidence needed later:

- A short, bounded arcade-vs-Genesis runtime trace from Stage 1 setup through first life-loss transition that logs the player object structure address, player X/Y/world/velocity/action/death flags/lives, camera/scroll values, and collision/floor routine PC plus lookup inputs/outputs at the required frames.
- The trace must identify the player object and collision/floor routine before implementation. It should not broaden into continue/game-over, D00298, Exodus, or broad sprite work.

## 12. Visible Acceptance Result

Not applicable. No build was produced.

Build 0158 visible acceptance criteria were not tested:

- No 3-second BlastEm survival test was run.
- No Kega Fusion test was run.
- No real Genesis test was run.
- No Exodus test was run.

## 13. Regression Results

No build was produced, so no regression validation was run.

Accepted prior results remain as priors only:

- Build 0152 C08C62 route remains accepted.
- Build 0154 BG plane model remains accepted.
- Build 0155 FG plane restoration remains accepted.
- Build 0156 C08C66 route remains accepted.
- Build 0157 PC090OJ dirty/candidate/SAT handoff remains accepted as internal plumbing.

## 14. Architecture Compliance

CONFIRMED.

This analysis does not modify execution flow. No Genesis-owned gameplay lifecycle, hardcoded player position, forced floor/collision result, forced survival, NOP/RTS bypass, equal-length workaround, second renderer, second SAT path, state-specific gameplay hack, or screenshot-based fix was introduced.

The no-build stop follows `RULES.md` and `ARCHITECTURE.md`: arcade code remains the program, and Genesis-side code remains helper/hardware-service only.

## 15. Open / Closed Issues Impact

Open issues touched:

- `OPEN-001` - gameplay visual/control bring-up context.
- `OPEN-017` - current ledger location for Stage 1 gameplay progression notes.
- `OPEN-024` - PC090OJ sprite subsystem context; SAT sanity classified as plausible enough to move on.
- `OPEN-018` - context only; raw C08C62/C08C66 routes remain accepted.

New issues opened: NONE.

Issues closed: NONE.

Issues intentionally deferred:

- Continue-screen garbling.
- Game-over garbling.
- Post-game-over title/story garbling.
- Attract-loop D00298.
- Exodus black screen and palette differences.
- PC080SN sky/seam/static X-scroll unless later proven to directly cause death/fall.
- Audio.
- Broad sprite rendering beyond SAT sanity.

## 16. KNOWN_FINDINGS Impact

Option A - no new finding to index.

Rationale: this task produced a bounded no-build stop and did not prove a durable player/collision/death/fall mechanism.

## STOP

STOP triggered: **YES**.

Stop reason:

- The player object state could not be located in both arcade and Genesis from the existing evidence.
- The collision/floor routine could not be identified from the existing evidence.
- The first death/fall divergence is not proven.
- The mandatory state-causality rule cannot be answered.

No source, build, ROM, bookmark, runtime trace, or implementation change was made.
