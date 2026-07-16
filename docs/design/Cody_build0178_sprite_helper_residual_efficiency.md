# Cody - Build 0178 Residual PC090OJ Sprite Helper Efficiency

**Date:** 2026-07-16
**Type:** Analysis-first / bounded implementation / runtime comparison
**Build context:** Build 0177 -> Build 0178, `rastan-direct`
**Baseline ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0177.bin`
**Baseline SHA256:** `b0db30f17a7d0d3453bf3a6c2bca23bd16694e72b7c050a874d3afb3fe921370`
**Candidate ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0178.bin`
**Candidate SHA256:** `998cc3c92b710d79eeaea08e49ea288f4757d03662692797361142bf186cdd96`
**Scope:** PC090OJ helper efficiency and dense-FG timing boundary only. No control/collision/scroll/gameplay-state fix. No FG palette reopen.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-047 (PC090OJ final SAT cap is too late; dirty mirror frames must derive bounded changed-record candidates), KF-046/KF-045 (palette route/FG carrier, not reopened), KF-038 (tall PC080SN BG/FG representation), KF-032 (raw hardware writes route through staging), KF-011 (arcade VBlank owns progression), KF-010 (staging -> VBlank commit). Open issues touched: OPEN-017, OPEN-024, OPEN-001 context. No contradiction of CONFIRMED/STRONG findings detected.

User visual observations recorded as runtime context only: Build 0177 appears slightly faster during Rastan's initial fall; slowdown appears again when denser terrain appears; Rastan remains uncontrollable; no enemies / no enemy interaction visible; FG palette/color remains good; title/story/READY still appear.

## Evidence Artifacts

Trace root: `states/traces/build0178_residual_efficiency_20260716_073844/`

- Build 0177 trace: `states/traces/build0178_residual_efficiency_20260716_073844/build0177/`
- Build 0178 trace: `states/traces/build0178_residual_efficiency_20260716_073844/build0178/`
- Build 0177/0178 comparison: `states/traces/build0178_residual_efficiency_20260716_073844/build0177_vs_build0178_comparison.md`
- Harness scripts: `states/traces/build0178_residual_efficiency_20260716_073844/build0177_phase_timing.lua` and `states/traces/build0178_residual_efficiency_20260716_073844/build0178/build0178_phase_timing.lua`
- Raw CSVs: `events.csv`, `samples.csv`, `enemy_records.csv` under each build subdirectory
- Reduced analyses: `build0177_reduced_analysis.md`, `build0178_reduced_analysis.md`

The timing harness used scripted coin/start input to reach gameplay and ran to frame 1600. It is headless (`-video none`), so it cannot classify black-bar pixels directly. Black-bar/no-black-bar visual buckets are therefore marked as not pixel-visible in this trace.

## Build 0177 Boundary Evidence

Build 0177 validated the earlier candidate reduction, but the residual trace still showed PC090OJ work every serviced frame:

| Window | DISPLAY_OFF rate | DISPLAY_OFF avg | tile-DMA avg | BG dirty bits avg | FG dirty bits avg |
|---|---:|---:|---:|---:|---:|
| initial fall / sparse FG | `35/91 = 0.385/frame` | `8.088 ms` | `24.00` | `0.00` | `0.00` |
| first dense FG/terrain | `65/141 = 0.461/frame` | `2.217 ms` | `18.00` | `0.00` | `0.00` |
| later scrolling window | `90/201 = 0.448/frame` | `2.217 ms` | `18.00` | `0.00` | `0.00` |
| late control window | `89/201 = 0.443/frame` | `2.217 ms` | `18.00` | `0.00` | `0.00` |

This does **not** support dense FG/BG as the measured timing culprit in the headless trace: BG/FG dirty row bits were zero in all sampled gameplay windows. The sprite tile-DMA worklist stayed nonzero (`18..24`) despite represented sprites being stable (`24..30`) and changed tuples already reduced by Build 0177.

## Exact Source Divergence

`apps/rastan-direct/src/pc090oj_hooks.s` still contained a Build 0163 controlled experiment inside `.Lpc090oj_worklist_set`:

```asm
cmpi.b  #PC090OJ_SCENE_GAMEPLAY_ID, genesistan_current_scene_id
beq.s   .Lwls_differ
```

That branch forced gameplay slots down the `.Lwls_differ` path even when `sprite_tile_resident_code[slot] == requested_code`, bypassing the resident-code cache and requeuing tile DMA every interval. This was a diagnostic experiment whose purpose had expired; keeping it in Build 0177 made the tile-DMA count remain artificially high.

State causality:

1. The correct state at `.Lpc090oj_worklist_set` is `sprite_tile_resident_code[slot]` reflecting the code last DMA-loaded into the slot.
2. That state is created by `.Lvcs_tile_dma` after the DMA succeeds (`move.w %d6, sprite_tile_resident_code[slot]`).
3. Build 0177 did not use that state in gameplay because the scene-gated experiment branched to `.Lwls_differ` before the resident-code comparison could cancel unchanged worklist entries.

## Fix Applied

Removed only the Build 0163 gameplay-only force-requeue branch/comment. The existing worklist semantics now apply in gameplay again:

- If requested code differs from resident code: reserve/update one worklist entry for that slot.
- If requested code matches resident code and a pending entry exists: cancel it.
- If requested code matches resident code and no pending entry exists: do nothing.

No mirror records were dropped. No SAT path, renderer, tile data, palette, BG/FG, collision, input, or gameplay state was modified.

Mechanical invariant delta:

- `opcode_replace` patched-site count: `151` unchanged
- `total_genesis_bytes_covered`: `0x182694 -> 0x18268C`
- ROM size: `1,582,740 -> 1,582,732`

## Build 0178 Verification

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS** after canonical invariant constants were updated to the observed mechanical `-0x8` byte delta.

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0178.bin`
- Rolling ROM after Build 0178: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `998cc3c92b710d79eeaea08e49ea288f4757d03662692797361142bf186cdd96`
- Size: `1,582,732`
- Boot guard: PASS
- Canonical gate: `GATE_PASS`
- Release trace: `states/traces/rastan_direct_video_test_build_0178_mame_30s_20260716_075107/`

## Procedural Note - Accidental Build 0179

While rewriting this markdown report, an unquoted shell heredoc accidentally executed the fenced release command text. That produced an unintended duplicate numbered Build 0179. No source/spec/tool change was made between Build 0178 and Build 0179.

- Build 0179 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0179.bin`
- Build 0179 SHA256: `998cc3c92b710d79eeaea08e49ea288f4757d03662692797361142bf186cdd96`
- Build 0179 size: `1,582,732`
- `cmp` Build 0178 vs Build 0179: byte-identical
- Current rolling ROM matches Build 0179 and is byte-identical to Build 0178
- Counter is now `179`

This is recorded as a procedural STOP condition, not as a semantic Build 0179 feature/change.

## 0177 vs 0178 Timing Comparison

| Window | Service rate 0177 | Service rate 0178 | DISPLAY_OFF avg 0177 | DISPLAY_OFF avg 0178 | tile-DMA avg 0177 | tile-DMA avg 0178 |
|---|---:|---:|---:|---:|---:|---:|
| initial fall / sparse FG | `0.385/frame` | `0.407/frame` | `8.088 ms` | `5.392 ms` | `24.00` | `6.00` |
| first dense FG/terrain | `0.461/frame` | `0.482/frame` | `2.217 ms` | `1.175 ms` | `18.00` | `6.00` |
| later scrolling | `0.448/frame` | `0.463/frame` | `2.217 ms` | `1.175 ms` | `18.00` | `6.00` |
| late control | `0.443/frame` | `0.463/frame` | `2.217 ms` | `1.175 ms` | `18.00` | `6.00` |

Total serviced gameplay-window DISPLAY_OFF count over traced frames 500..1599 improved from `485` to `503`. The sprite tile-DMA reduction is large and direct; the overall service-rate improvement is real but modest.

## Classification

Primary Build 0177 next safe boundary: **A - residual PC090OJ**. Specifically, a diagnostic gameplay-only force-requeue branch kept sprite tile-DMA work high after Build 0177 had already reduced candidate processing.

Post-Build 0178 remaining slowdown: **D - mixed**. Dense PC080SN FG/BG is not supported by this trace (dirty bits were zero), but PC090OJ still does substantial decode/representation/SAT work and `pc090oj_sat_dirty` remains set every serviced frame. The service cadence also still reflects combined VBlank + arcade/main-loop duration, so the remaining issue is not safely reducible to a single tile-DMA branch anymore.

## PC090OJ Helper Answers

1. **Does `vdp_prepare_sprites` still run?** Yes; it runs in the gameplay VBlank service path.
2. **Does `pc090oj_scan_active` remain active?** Yes; sampled value stayed `1`.
3. **Does mirror tracking remain full 256 records?** Yes; no mirror shrink or record suppression was introduced.
4. **Does Build 0177 still compare all 256 lightweight tuples?** Yes, when `pc090oj_mirror_dirty` is set; that is the Build 0177 bounded candidate derivation from KF-047.
5. **Was candidate processing still full-256?** No; candidate counts are bounded by live/diff candidates, and at DISPLAY_OFF they are consumed back to zero.
6. **Why was tile-DMA still high in Build 0177?** The Build 0163 gameplay-only branch forced `.Lwls_differ` before the resident-code equality check.
7. **Did Build 0178 eliminate all tile-DMA?** No. It reduced the steady gameplay count to about `6` per serviced frame; remaining entries need a separate slot/code-level trace before more pruning.
8. **Does SAT DMA still fire?** Yes; `pc090oj_sat_dirty` remains `1` at sampled DISPLAY_OFF points and SAT DMA still runs in serviced frames.
9. **Is `.Lpc090oj_set_all_candidates` reintroduced?** No; no full-candidate fallback was added.
10. **Did dense FG/BG dominate the measured windows?** No; BG/FG dirty row bits sampled as zero in all four gameplay windows.
11. **Is a no-black-bar/control distinction proven here?** No; the trace is headless, so visual black-bar frames are not pixel-classified.
12. **Smallest next safe boundary after 0178?** Prove why SAT dirty and the remaining six tile-DMA entries persist per service: slot/code-level worklist trace plus staged SAT byte-diff trace. Do not skip SAT DMA broadly without proving staged SAT stability.

## Enemy Records

The 14 enemy-code records (`0x03E8..0x03F5`) remain present in `pc090oj_object_ram`, but every sampled record decodes to `offscreen_y` with `y_screen=224`, `represented=0`, `waiting=0`, `slot=255`, and `tile_resident=FFFF`.

Classification for enemy absence in this trace: current PC090OJ decode rejects them as offscreen, not as missing tile-DMA or missing SAT residency. This does not prove arcade enemy behavior is correct; it only says the sampled Genesis records are not drawable by the current viewport/opaque-geometry gate.

## Dense FG Slowdown Check

The user-observed visual slowdown around denser terrain is real runtime context, but this headless scripted trace did not show PC080SN dirty-row work in the corresponding sampled windows. The trace therefore does **not** justify reopening FG palette or FG/BG projection as the next fix. If visual dense-terrain slowdown remains after Build 0178, the next proof should synchronize video-visible frames with VBlank timing and dirty-row counters; do not infer from this headless run alone.

## Recommended Next Task

Evidence-only, not a fix: trace Build 0178 per service for:

- exact six tile-DMA worklist entries: slot, old resident code, requested code, producer path;
- whether `staged_sprite_sat` bytes changed since the previous SAT DMA;
- why `pc090oj_sat_dirty` remains asserted every serviced frame;
- whether remaining `decode_record`/`field_update` calls are strictly necessary for unchanged represented records.

If staged SAT and resident tile codes are unchanged across services, a bounded next candidate is possible: skip SAT DMA and/or skip the remaining unchanged tile-DMA entries only at the proven dirty boundary. Do not broad-disable sprite updates.

## OPEN / KNOWN_FINDINGS Impact

Open issues touched: OPEN-017 and OPEN-024; OPEN-001 context only. No issues closed. No new issue opened.

KNOWN_FINDINGS impact: **Option C - update KF-047**. Build 0178 refines KF-047 with a durable lesson: after bounded candidate derivation, stale diagnostic worklist forcing can still defeat the resident tile-DMA cache; resident-code equality must be allowed to cancel unchanged sprite tile work.

## STOP

STOP triggered: **YES (procedural)**. Build 0178 itself was produced and validated as a bounded performance candidate, but an unintended duplicate Build 0179 was also produced during documentation writing due an unquoted heredoc. Visual/hardware acceptance remains USER MUST VERIFY.
