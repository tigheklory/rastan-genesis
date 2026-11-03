# Cody - Lizard Actor-Population Regression and Progression Trace

**Date:** 2026-07-18  
**Type:** Evidence-only runtime analysis  
**Build context:** Original arcade vs Build 0204 vs Build 0205  
**Trace directory:** `states/traces/lizard_actor_population_regression_20260718_220018/`  
**Scope:** Actor-population/progression only. No source/spec/tool/Makefile/gate/invariant/ROM changes. No build. No Build 0206. No palette, visual-Y, collision, SAT, VRAM, black-bar, FG, sky, HUD, record-132, bat, D00298, or continue/game-over work.

## Baseline

Recovered state matched the prompt:

- Build counter: `205`
- Build 0204 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0204.bin`
- Build 0204 SHA256: `0e1925b2934e2d2614bb6c90de82c78ea07bc62819b58fe345fb83f8e5deb083`
- Build 0205 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0205.bin`
- Build 0205 SHA256: `4238d2ffcd226c45f1251ccbe4e7e64fa9b642acb18c4957ab85e1fd888b4aee`
- Rolling ROM: Build 0205/256, byte-identical to Build 0205
- `opcode_replace`: `214`
- Coverage invariant: `0x182950`
- Build 0206: absent

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded:

- KF-060: enemy PC090OJ writers `0x41DAE` / `0x45DFA` were previously misrouted or skipped.
- KF-061: invalid code-zero PC090OJ expansion-engine calls are unsafe.
- KF-062: Genesis does populate enemy actor blocks; the old pure-empty-upstream model is superseded.
- KF-063: relocated engine `runtime_genesis_pc 0x0003D254` is safe on validated actors, and shared writer `runtime_genesis_pc 0x0003CB50` preserves non-C-window PC090OJ tuple writes.
- KF-064: visible first lizards are composite records from actor block `A5+0x02C8`, not record 46.
- KF-065: Build 0205 implements the block `A5+0x02C8` whole-block scratch staging design.

Rediscovery-hazard findings touched: KF-060 through KF-065. No contradiction of a CONFIRMED/STRONG finding was detected. Open issues touched: OPEN-017 and OPEN-024, with OPEN-001 as broad visual context. No issue was closed.

Architecture compliance: **CONFIRMED**. The arcade code remains the program; this task only sampled original arcade and translated Genesis runtime state. No forced actors, no forced records, no helper patch, no diagnostic ROM behavior, and no Genesis-owned gameplay flow were introduced.

## Evidence Inspected

- `RULES.md`
- `ARCHITECTURE.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- Recent `AGENTS_LOG.md`
- `docs/design/Cody_lizard_acceptance_divergence_trace.md`
- `docs/design/Cody_lizard_composite_pc090oj_staging_implementation.md`
- `docs/design/Andy_lizard_composite_pc090oj_staging_design.md`
- `docs/design/Cody_first_lizard_record_ownership_true_vram_trace.md`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`
- Trace artifacts under `states/traces/lizard_actor_population_regression_20260718_220018/`

Trace files produced:

- `lizard_population_trace.lua`
- `arcade_summary.csv`, `arcade_actors.csv`, `arcade_events.log`
- `build0204_summary.csv`, `build0204_actors.csv`, `build0204_events.log`
- `build0205_summary.csv`, `build0205_actors.csv`, `build0205_events.log`
- `reduce_lizard_population.py`
- `lizard_population_reduced.json`
- `lizard_population_reduced.md`

All three MAME runs exited with code `0` and sampled `1800` frames.

## Address Mapping Discipline

Address correlation used `build/rastan-direct/address_map.json` as authority.

- `runtime_genesis_pc 0x0003D254` is inside `arcade_copy` segment `0x03D252..0x03F128`, mapped from `arcade_pc 0x03D052..0x03EF28`.
- `runtime_genesis_pc 0x0003CB50` is a patched site mapped to `arcade_pc 0x0003C950..0x0003CA38`.
- `runtime_genesis_pc 0x00041FAE` is a patched site mapped to `arcade_pc 0x00041DAE..0x00041F0E`.
- `runtime_genesis_pc 0x00072370` and `runtime_genesis_pc 0x00072406` are `genesis_only` helper addresses in the generated helper region, not arcade PCs.

No `+0x200` arithmetic was used as proof.

## Trace Method Limitation

The trace captured per-frame actor-block state and event transitions. It did **not** install debugger write-watchpoints on the actor block. Therefore:

- `ACTOR_BECAME_VALID` and `ACTOR_CLEARED_OR_INVALID` event PCs are frame-sampling PCs and are **not** proven writer PCs.
- The requested "writes to the block" requirement was satisfied only as the closest reliable per-frame sampling equivalent.
- Exact writer PC/source-table provenance remains a STOP-limited follow-up if an implementation patch is considered.

## Three-Way Actor Population Result

| Runtime | Max valid actors in `A5+0x02C8` | First max frame | Max actor shells | Max composite windows | Max composite records |
|---|---:|---:|---:|---:|---:|
| Original arcade | `5` | `966` | `6` | `5` | `48` |
| Build 0204 | `1` | `525` | `6` | `0` | `0` |
| Build 0205 | `1` | `563` | `6` | `1` | `10` |

Primary result: **Build 0204 and Build 0205 both reach only one valid lizard actor.** Build 0205 did not introduce the one-lizard actor-population ceiling. Build 0205 changed output behavior by staging the one valid actor that already existed; Build 0204 had the same one-actor population limit but did not stage the block-`0x02C8` composites.

## First Valid Actor Timeline

Original arcade progressively activates additional actor entries:

- Frame `372`: entry `8` becomes valid.
- Frame `421`: entry `7` becomes valid.
- Frame `502`: entry `6` becomes valid.
- Frame `567`: entry `5` becomes valid.
- Frame `966`: entry `4` becomes valid.

Build 0204:

- Frame `525`: entry `8` becomes valid.
- No entries `4..7` become valid in the captured window.

Build 0205:

- Frame `563`: entry `8` becomes valid.
- No entries `4..7` become valid in the captured window.

## Matched State Fields

The best exact-score frame pairs in the reducer are early pre-encounter frames and should not be interpreted as lizard-encounter identity. For the lizard boundary, the relevant comparison is by gameplay state, player/camera setup, stage/subphase, and actor-entry contents.

Representative first multi-lizard arcade state, original arcade frame `421`:

- State: `2/3/0`
- Player: `x=0x0020`, `y=0x0070`
- Scroll/camera/velocity: `scroll_x=0x0000`, `camera_10b8=0x0000`, `scroll_vel_10d8=0x0000`
- Stage/subphase/wave/trigger: `0x0100 / 0x0001 / 0x0000 / 0x0000`
- `A5+0x0214`: `0x0009`
- Valid actors: `2` (`idx7`, `idx8`)
- Entries `4..8`: actor shells exist, and entries `7` and `8` have `b5 != 0`

Comparable Build 0204 state, frame `567`:

- State: `2/3/0`
- Player: `x=0x0020`, `y=0x0070`
- Scroll/camera/velocity: `scroll_x=0x0000`, `camera_10b8=0x0000`, `scroll_vel_10d8=0x0000`
- Stage/subphase/wave/trigger: `0x0100 / 0x0001 / 0x0000 / 0x0000`
- `A5+0x0214`: `0x0009`
- Valid actors: `1` (`idx8`)
- Entries `4..7`: actor shells exist (`b0=0x01`, codes present) but `b5=0x00`, so they remain invalid.

Comparable Build 0205 state, frame `567`:

- State: `2/3/0`
- Player: `x=0x0020`, `y=0x0070`
- Scroll/camera/velocity: `scroll_x=0x0000`, `camera_10b8=0x0000`, `scroll_vel_10d8=0x0000`
- Stage/subphase/wave/trigger: `0x0100 / 0x0001 / 0x0000 / 0x0000`
- `A5+0x0214`: `0x0009`
- Valid actors: `1` (`idx8`)
- Entries `4..7`: actor shells exist but `b5=0x00`, so they remain invalid.
- Build 0205 additionally stages one composite window from the one valid actor.

Comparable scrolled state, original arcade frame `966`:

- Player: `x=0x00A0`, `y=0x0070`
- Camera/velocity: `camera_10b8=0x003C`, `scroll_vel_10d8=0x0002`
- Valid actors: `5` (`idx4..idx8`)

Comparable scrolled Genesis states:

- Build 0204 frame `900`: player `x=0x00A0`, `y=0x0070`; `camera_10b8=0x0083`; `scroll_vel_10d8=0x0002`; valid actors `1` (`idx8`).
- Build 0205 frame `966`: player `x=0x00A0`, `y=0x0070`; `camera_10b8=0x005B`; `scroll_vel_10d8=0x0002`; valid actors `1` (`idx8`).

This rules against Build 0205 as the first actor-population regression and points to an upstream Genesis actor-eligibility/progression boundary already present in Build 0204.

## First Build 0204 vs Build 0205 Divergence

Frame-aligned fields differ in timing because the two translated runs are not cycle/frame-identical:

- First `mode` divergence: frame `535` (`0204=0`, `0205=3`).
- First `valid_actors` divergence: frame `525` (`0204=1`, `0205=0`), later converging to one valid actor.
- First `composite_windows` divergence: frame `564` (`0204=0`, `0205=1`), expected because Build 0205 introduced block-`0x02C8` staging.

These are timing/output differences, not proof that Build 0205 caused the population ceiling. The load-bearing population maximum is identical: `1` valid actor in both Build 0204 and Build 0205.

## First Arcade vs Genesis Divergence

The first proven arcade-vs-Genesis population divergence is the actor-entry secondary active/eligibility gate at `A5+0x02C8 + entry*0x40 + 5` (`a4@(5)` in the static design language):

- Arcade progressively sets `b5` nonzero for entries `8`, `7`, `6`, `5`, and `4`.
- Build 0204 and Build 0205 populate actor shells for entries `4..8`, but only entry `8` receives nonzero `b5` in the captured window.
- Entries `4..7` are not absent: their shells and code-like fields exist. They are held invalid because `b5` remains zero.

This is more precise than "missing lizard staging": Build 0205 stages the lizard actor that exists. The missing additional lizards are upstream of PC090OJ representation/SAT/tile residency.

## Field-Specific Questions

### A5+0x214 Result

At comparable lizard setup frames, original arcade, Build 0204, and Build 0205 all show `A5+0x0214 = 0x0009`. Later maxima differ (`arcade max 0x000B`, Genesis max `0x001C`), but this trace does not prove `A5+0x0214` is the root. No Build-0205-only corruption of `A5+0x0214` was observed.

### Spawn Dispatcher Result

Not directly PC-hit captured in this task. Per-frame actor data proves some spawn/preprocessor path runs in both Genesis builds, because entries `0`, `4`, `5`, `6`, `7`, and `8` become actor shells. The precise dispatcher/writer PC that decides `b5` for entries `4..7` remains unresolved.

### Spawn Source/Table Result

Not directly captured. Stage/subphase/wave/trigger fields are comparable at the first lizard boundary (`stage=0x0100`, `subphase=0x0001`, `wave=0`, `trigger=0`). This trace does not prove or disprove source-table selection as the root of the missing `b5` activations.

### Actor-Slot Allocation Result

Actor-slot allocation is **partially working**, not absent. Both Genesis builds populate shells in the same visible block range that arcade uses. The divergence is not "no slots allocated"; it is that only entry `8` becomes valid while entries `4..7` remain shells with `b5=0`.

### Premature Clearing Result

Premature clearing is not the first proven cause for the missing additional lizards. Entries `4..7` never become valid in the captured Genesis windows, so the first gap is missing activation, not post-valid clearing. Entry `8` does later clear in both Genesis builds (`Build 0204` frame `913`, `Build 0205` frame `1089`), but that does not explain why entries `4..7` never activate.

## Classification

Primary outcome: **B - Pre-existing Genesis spawn/progression divergence.**

Build 0205 did **not** introduce the one-lizard limitation. The limitation predates the Build 0205 composite staging helper and is already present in Build 0204.

Root cause confirmed: **NO**, not to exact writer-PC/source-table level. Boundary confirmed: **YES**, at actor-entry activation/eligibility for entries `4..7` in block `A5+0x02C8`, especially `a4@(5)` staying zero in Genesis while arcade sets it nonzero.

## Smallest Fix Boundary

No fix is authorized or safely placeable from this evidence alone.

Smallest next implementation-relevant boundary to investigate:

- Watch writes to the block `A5+0x02C8..A5+0x0508`, focusing on entry offsets `+5` for entries `4..8`.
- Capture the exact writer PC that sets arcade entries `7`, `6`, `5`, and `4` valid, and compare whether the same translated path executes/writes in Build 0205.
- Only after that writer/source is known should a fix be considered.

A direct patch in `pc090oj_stage_block2c8` would be too late and would force actor validity; that would violate architecture because the arcade actor/progression state did not exist.

## OPEN / CLOSED Issues Impact

- Open issues touched: OPEN-017, OPEN-024; OPEN-001 context only.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: palette bank `0x36`, visual-Y/feet alignment, combat/damage, SAT/VRAM/tile residency, black bar/VBlank, FG/sky/HUD, record 132, bat behavior, D00298, continue/game-over.

OPEN-017 should retain this evidence as a refinement: the lizard count problem is an upstream actor-population/eligibility issue predating Build 0205, not a Build 0205 composite-staging regression.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This pass refines the live OPEN-017 boundary but stops short of the exact durable writer/root mechanism needed for a new KNOWN_FINDINGS entry. KF-062/KF-064/KF-065 remain valid.

## STOP

STOP triggered: **YES, limited**. The trace resolved the Build 0204 vs Build 0205 regression question and pinned the boundary to actor-entry activation/eligibility, but did not capture exact writer PCs or source-table provenance. No implementation is safe from this evidence alone.
