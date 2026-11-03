# Cody - Build 0169 Player Ground-Contact / Collision Alignment Candidate

**Date:** 2026-07-14
**Type:** Analysis-first runtime evidence; no implementation
**Baseline requested:** Build 0168, `dist/rastan-direct/rastan_direct_video_test_build_0168.bin`, SHA `be2d575256ff72d942055c3477a31b0be4af1c863b9cf114f1c5f3bbd184d993`, counter `168`
**Current workspace note:** branch `rastan-direct-proposal`, HEAD observed as `e0330a0`, with existing dirty Build 0168/generated files from the prior task. Those pre-existing changes were not reverted.
**Scope:** Opening gameplay fall/landing ground-contact alignment only. No source/spec/tool/Makefile/ROM/invariant edits. No build. No D00298, Exodus-loop, sprite-source, LUT, scene-loader, READY/header, continue/game-over, broad tilemap, input, or VBlank fix work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010 (VDP staging/plane mapping), KF-015 (vertical scroll conversion), KF-036/KF-039 (mapped work-RAM discipline), KF-040/KF-041/KF-042 (PC080SN tilemap producer ownership / pass-selection / partial hook replacement), KF-044 (raw work-RAM immediate family context), and OPEN-017 Build 0165-0168 issue history.

Rediscovery-hazard findings touched: collision-map raw-WRAM / PC080SN side-effect chain, mapped work-RAM addressing, and PC080SN producer ownership. No contradiction of CONFIRMED/STRONG findings was found.

Open issues touched: OPEN-017 (active gameplay-entry/collision/death/fall thread); OPEN-001 and OPEN-024 context only. Closed issues touched: none.

Architecture compliance: **CONFIRMED**. The arcade code remains the program; this task used read-only MAME runtime evidence and static source/disassembly inspection. No helper rewrite, second renderer, forced safe ground, death-handler bypass, player-state patch, source/spec/ROM/build change, or Genesis-owned gameplay flow was introduced.

## Evidence Captured

Trace directory: `states/traces/build0169_ground_contact_alignment_20260714_134458/`

Files produced by this analysis-only task:

- `ground_contact_trace.lua` - bounded MAME Lua trace harness for arcade/Genesis comparison.
- `arcade_ground_contact_trace.csv`, `arcade_ground_contact_events.log` - original arcade `rastan` run.
- `genesis0168_ground_contact_trace.csv`, `genesis0168_ground_contact_events.log` - Build 0168 run.
- `genesis0167_ground_contact_trace.csv`, `genesis0167_ground_contact_events.log` - Build 0167 diagnostic contrast only.
- MAME stdout/stderr and exit-code files for each run; all exit codes were `0`.

The trace logs external frames, state words `%a5@(0)/(2)/(4)`, player position, flags/mode fields, camera/scroll words, computed collision-reader row/column/offset, nearby collision-map words, and Genesis staged BG/FG cells at the same row/column.

## User Visual Baseline Preserved

Tighe's visual observations are recorded as runtime/visual context, not as debugger proof:

- Build 0168: Rastan is visible, vertical scroll is corrected, and early type-8 death/drowning is removed in the scripted trace, but correct ground contact/control is not achieved. The player appears high in a sky/wall-walking area and appears uncontrollable.
- Build 0167: diagnostic only; not better overall. Rastan falls lower and can clip partly off bottom; because Genesis vertical resolution is lower, bottom clipping alone is not proof of bad Y. Pressing right moves a few tiles then stops; jump/sword/left did not obviously work.
- Arcade: Rastan does not fall as far as the Build 0167 diagnostic path; after ground contact the ground/platform is visible roughly mid-screen in a sky-heavy view. Genesis still shows mostly mountains/missing ground rows.

Deferred observations remain deferred: BG mountains/sky composition, missing/wrong ground rows, FG palette, READY/header, VBlank/rolling black bar/slowdown, input/down+attack, continue/game-over, D00298, Exodus loop, and PC090OJ records `132..134`.

## Static Context Inspected

Relevant inspected functions/files:

- `apps/rastan-direct/src/tilemap_hooks.s`: `genesistan_stage_fg_src_column` lines around 307-382; collision side-effect writes `ARCADE_COLLISION_MAP_BASE + ((a0 - 0x00C08000) >> 1)`.
- `build/genesis_postpatch.disasm.txt`: collision reader `runtime_genesis_pc 0x053C2E..0x053C6C`; mode-8 dispatch/write region `0x053FA6..0x05400C`.
- `docs/design/Cody_build0168_collision_map_drowning_fix_candidate.md`: Build 0168 implementation notes and validation.
- `docs/design/Andy_build0159_collision_producer_selection.md`: arcade Stage-1 collision map is produced by the BG pass (`a5@0x10A8==0`), not the FG pass; FG semantics are different.
- `docs/design/Andy_build0159_tilemap_staging_collision_producer.md`: FG producer adds solid-above/order-flip semantics and differs from BG collision-map generation.
- `docs/design/Andy_build0159_collision_producer_pipeline_owner.md`: arcade collision producer ownership and BG-store evidence.

Key static facts:

- The collision reader formula is unchanged except for Build 0168's base rebase to mapped Genesis WRAM:
  `A0 = collision_base + (((((-camX)&0x1ff)+x)>>1)+8 + ((((-camY)&0x1ff)+y)<<5) masked) >> 1`.
- Build 0168 correctly points the reader at `0x00FF1E00`, but it populates that buffer from `genesistan_stage_fg_src_column`, a Stage-1 FG_SRC helper.
- Prior arcade evidence says Stage-1 collision intent is the BG producer/pass, not FG_SRC/FG producer semantics.

## Runtime Comparison

### Original Arcade

- First gameplay: frame `307`, state `2/3/0`, player `X=0x0020`, `Y=0x0030`, mode `0x0003`, camera Y `0x0000`, collision row/col `6/6`, collision word `0x0000`.
- First `Y>=0x70`: frame `338`, player `Y=0x0070`, mode `0x0003`, camera Y `0x01FF`, collision row/col `14/6`, collision word `0x0000`.
- First grounded flag bit `0x0004`: frame `400`, player `Y=0x0070`, flags `0x0004`, mode `0x0000`, camera Y `0x0149`, collision row/col `36/6`, current word `0x0000`, lower neighbor `map_down2=0x3400`.
- Stable samples through frames `420/533/560/620/700/760/820`: player remains around `Y=0x0070`, flags `0x0004`, mode `0x0000`, camera Y `0x0149`.

### Genesis Build 0168

- First gameplay: frame `536`, state `2/3/0`, player `X=0x0020`, `Y=0x0030`, mode `0x0003`, camera Y `0x0000`, collision row/col `6/6`, collision word `0x0003`.
- First grounded flag bit `0x0004`: frame `539`, player still `Y=0x0030`, flags `0x0004`, mode `0x0001`, camera Y `0x0000`, collision row/col `6/6`, collision word `0x0003`.
- No `Y>=0x70` event was observed through frame `1120`.
- Later stable samples (`560` through `1120`) stay at player `Y=0x0030`, flags `0x0004`, mode `0x0001`, camera Y `0x0000`, collision row/col around `6/5`, collision word `0x1000`, staged BG word `0x427E`, staged FG word `0x6000`.
- Mapped collision buffer is populated (`nonzero=2016`, `type8=0`), so the early drowning/type-8 symptom is removed, but the map class under the spawn/top rows is now nonzero/solid where arcade is empty.

### Genesis Build 0167 Diagnostic Contrast

- First gameplay: frame `534`, state `2/3/0`, player `X=0x0020`, `Y=0x0030`, mode `0x0003`, camera Y `0x0000`, collision row/col `6/6`, collision word `0x0000`, mapped collision map still empty.
- First `Y>=0x70`: frame `590`, player `Y=0x0070`, mode `0x0003`, camera Y `0x0000`, collision word `0x0000`.
- No grounded flag bit `0x0004` was observed through frame `1120`; player continues falling to `Y=0x0101` by final sample.
- This supports treating Build 0167 only as diagnostic contrast: it does not produce a real landing, but it also does not show Build 0168's immediate early solid collision at row 6.

## Classification

**F - Build 0168 collision fix overcorrected.**

Build 0168 fixed the raw-ROM type-8 failure mode by populating and reading mapped collision WRAM, but it populated the map from the wrong production model for this landing boundary. The first exact divergence is at Build 0168 gameplay entry: the same spawn/top collision cell where arcade reads `0x0000` at row/col `6/6` reads `0x0003` in Build 0168, causing grounded/contact state at `Y=0x0030` by frame `539` instead of allowing the arcade fall to `Y=0x0070` and camera Y `0x0149` before stable ground contact.

This is also observably an A-like spatial/content mismatch (populated collision map but misaligned/mis-sourced for the player), but the primary classification is **F** because the mismatch was introduced by the Build 0168 collision-side-effect candidate: it emits from `genesistan_stage_fg_src_column` / FG_SRC while prior arcade-intent evidence says Stage-1 collision is BG-pass owned.

## Clear Non-Causes / Non-Implications

- Not the old raw-ROM type-8 reader: Build 0168 reads mapped `0x00FF1E00` and no type-8 was observed in this sampled window.
- Not a death-handler fix boundary: `runtime_genesis_pc 0x05400C` remains the faithful copied mode-8 writer and is not implicated by the Build 0168 immediate stuck/grounded state.
- Not a pure empty-map failure: Build 0168's mapped collision buffer is populated.
- Not a proven input bug: player control still appears bad, but the first divergence occurs before meaningful control analysis, at initial ground-contact/collision classification.
- Not a visible-ground tile proof: staged BG/FG values at the collision row are logged, but the trace does not prove a complete visible tilemap/plane composition fix.

## Smallest Proposed Implementation Boundary

**Do not build from this task.** The smallest safe boundary is not a player/Y/camera/death patch. It is a PC080SN collision-production boundary:

1. Preserve Build 0168's coordinated collision-buffer rebase concept only as the reader-side endpoint.
2. Replace or revise the collision-map population side-effect so Stage 1 uses arcade-equivalent BG-pass collision semantics rather than the FG_SRC helper's row/content model.
3. Prove the corrected producer creates an arcade-equivalent map at the player landing cells before revalidating ground contact.

The immediate code area to inspect first is `genesistan_stage_fg_src_column` in `apps/rastan-direct/src/tilemap_hooks.s`, specifically the collision write block around the descriptor collision read and `move.w %d0,0(%a1,%d6.w)`. The companion design evidence to keep open beside it is `docs/design/Andy_build0159_collision_producer_selection.md` sections 3-7, because the fix depends on BG-vs-FG producer semantics, not just row arithmetic.

## Build Decision

Build 0169 was **not** produced. The trace proves the Build 0168 collision candidate overcorrected, but not a one-line/single-site safe replacement. A build here would risk guessing the BG collision producer semantics or forcing safe ground. That would violate state-causality and the no-bypass rules.

Implementation is **not safely placeable yet**. A bounded next task should design and verify the arcade-equivalent BG collision-map production side-effect, then decide whether a Build 0169 implementation is safe.

## Open / Closed Issues Impact

Open issues touched: OPEN-017. OPEN-001 and OPEN-024 are context only. New issues opened: none. Issues closed: none.

OPEN-017 should record that Build 0168 removes the early type-8/raw-ROM failure but introduces/uncovers immediate early solid collision at the spawn/top row. Deferred issues remain deferred: BG/FG composition, missing/wrong ground tiles, gameplay palette, READY/header flicker, VBlank/rolling bar/slowdown, input/down+attack, continue/game-over, D00298, Exodus loop, and records `132..134`.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed. This evidence refines the active OPEN-017 collision-map implementation thread and reinforces existing KF-040/KF-041/KF-042 PC080SN producer-ownership priors. A durable KNOWN_FINDINGS update should wait until the corrected BG collision-production boundary is implemented or definitively specified.

## STOP

STOP triggered: **YES (bounded-fix gate)**. Evidence is sufficient to classify the Build 0168 failure as overcorrection/mis-sourced collision production, but insufficient to implement safely without a dedicated BG-pass collision producer design.
