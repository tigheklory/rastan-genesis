# Cody - Build 0135 DISPLAY_ON Timing Reorder

**Date:** 2026-07-02  
**Type:** One narrow production build + visual/runtime evidence  
**Build:** 0135  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0135.bin`  
**SHA256:** `8e00be424f9afefe79d199640096bf99de7b53c4ba49e83ad32b2b491990844e`  
**Baseline:** Build 0134 / Build 0132 byte-identical baseline, SHA256 `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`  
**Scope:** Production reorder only. No diagnostics/instrumentation. No PC090OJ logic change. No PC080SN logic change. No `scene_load.s`, `tilemap_hooks.s`, residency-cache, tool, invariant, or ROM-artifact hand edits.

## Phase 0

Relevant priors: KF-010, KF-011, KF-013, KF-021, KF-032, KF-038 context; OPEN-001 primary; OPEN-024 sprite/cache context; OPEN-015 not touched.

High-rediscovery hazards: arcade VBlank owns progression; Genesis VBlank is servicing-only; Build 0132 sprite residency cache is verified correct; Build 0133 timing diagnostic established DISPLAY_ON late in 15/17 anchors.

Task classification: **EXTENDING** for OPEN-001.

Contradiction detected: **NO**.

Build 0134 baseline: loaded as byte-identical to Build 0132, SHA256 `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`.

Display-on design loaded: **YES**, Andy Option D reorder from `docs/design/Andy_build0134_display_on_timing_fix_design.md`.

Planned file: `apps/rastan-direct/src/vdp_comm.s` only.

STOP conditions acknowledged: **YES**. No PC090OJ/PC080SN/scene/tilemap/cache changes, no diagnostics, no invariant drift, no duplicate DISPLAY_ON, and stop if the band were unchanged/worse or new scroll/palette corruption appeared.

## Implementation

Changed exactly one function: `_vblank_service` in `apps/rastan-direct/src/vdp_comm.s`.

The existing DISPLAY_ON block was moved from after `bsr vdp_commit_scroll` to immediately after `bsr vdp_commit_sprites`:

```asm
    bsr     vdp_commit_tiles_if_dirty
    bsr     vdp_commit_bg_strips_if_dirty
    bsr     vdp_commit_fg_strips_if_dirty
    bsr     vdp_commit_sprites

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg

    tst.b   palette_dirty
    beq.s   .Lvs_skip_palette
    bsr     vdp_commit_palette
    clr.b   palette_dirty
.Lvs_skip_palette:

    bsr     vdp_commit_scroll
```

No DISPLAY_ON duplicate remains. No commit routine was changed.

Generated disassembly confirms the produced order:

```asm
runtime_genesis_pc 0x000700DE: bsrw 0x71FB4   ; vdp_commit_sprites
runtime_genesis_pc 0x000700E2: moveq #1,%d0   ; VDP_REG_MODE2
runtime_genesis_pc 0x000700E4: moveq #0x74,%d1 ; DISPLAY_ON
runtime_genesis_pc 0x000700E6: bsrw 0x7007E  ; vdp_set_reg
runtime_genesis_pc 0x000700EA: tst.b 0xff4000 ; palette dirty gate
runtime_genesis_pc 0x000700FC: bsrw 0x701F0  ; vdp_commit_scroll
```

## Build

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- ROM path: `dist/rastan-direct/rastan_direct_video_test_build_0135.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `8e00be424f9afefe79d199640096bf99de7b53c4ba49e83ad32b2b491990844e`
- Size: `1,561,764` bytes
- Rolling ROM matches numbered ROM: **YES** (`cmp=0`)
- Canonical gate: **GATE_PASS**
- `opcode_replace` count: `133`
- `total_genesis_bytes_covered`: `0x17D4A4`
- Invariant changes: **NONE**
- ROM SHA changed from Build 0134: **YES**
- Release trace artifact: `states/traces/rastan_direct_video_test_build_0135_mame_30s_20260702_222831/`

## Runtime / Visual Evidence

Evidence directory: `states/traces/build0135_display_on_timing_reorder_20260702_222926/`

Captured with host-side MAME/Lua read-only snapshots and WRAM dumps, no ROM instrumentation:

- Build 0134 baseline no-input: `states/traces/build0135_display_on_timing_reorder_20260702_222926/build0134/no_input_contact_sheet.png`
- Build 0134 baseline coin/start: `states/traces/build0135_display_on_timing_reorder_20260702_222926/build0134/coin_start_contact_sheet.png`
- Build 0135 no-input: `states/traces/build0135_display_on_timing_reorder_20260702_222926/build0135/no_input_contact_sheet.png`
- Build 0135 coin/start: `states/traces/build0135_display_on_timing_reorder_20260702_222926/build0135/coin_start_contact_sheet.png`
- Build 0134 vs Build 0135 no-input compare sheet: `states/traces/build0135_display_on_timing_reorder_20260702_222926/no_input_build0134_vs_build0135_compare_sheet.png`
- Build 0134 vs Build 0135 coin/start compare sheet: `states/traces/build0135_display_on_timing_reorder_20260702_222926/coin_start_build0134_vs_build0135_compare_sheet.png`
- Metrics: `states/traces/build0135_display_on_timing_reorder_20260702_222926/runtime_visual_metrics.md`
- Reduced metrics JSON: `states/traces/build0135_display_on_timing_reorder_20260702_222926/runtime_visual_metrics.json`

Exodus layer-separated capture: **not available from this automated WSL/MAME capture pass**. This report uses MAME final composite snapshots plus WRAM staging/SAT dumps.

### Visual Answers

1. Horizontal slit/band: **reduced, but only narrowly** in MAME. Build 0135 exposes one additional scanline of the existing bottom-band content in sampled no-input/story frames. It is not gone.
2. Mostly/full visible final composite: **NO** for the no-input title/story band symptom. Some coin/start frames still show full story/prompt content, matching Build 0134 behavior.
3. Plane A / Plane B intact: **not directly layer-viewed in Exodus here**; WRAM staging counts remain sane and match Build 0134 at sampled anchors.
4. Title score sprites still present: **no regression observed in MAME smoke**. Sprite counters and SAT/descriptor counts match Build 0134 at sampled anchors; visible top score row fragments remain equivalent in coin/start frames.
5. New scroll seam / horizontal tear / HScroll corruption: **NO new issue observed** in the sampled MAME snapshots. Existing band/slit remains.
6. Palette flash/color corruption: **NO new palette corruption observed** in sampled snapshots.
7. Sprite/SAT regression: **NO**. Build 0135 counters match Build 0134 for active/drawable/emitted/dropped samples.
8. Coin/start without crash: **YES**, MAME smoke window reached frame 650 and exited normally.
9. ROUND/start at least as well as Build 0134: **YES** by state/counter equivalence; visual output at sampled ROUND frame remains black in MAME final composite, same as Build 0134.

### Visual Metrics Summary

Build 0134 vs Build 0135 pixel differences were small and localized:

| mode | frame | label | diff pixels | diff bbox |
|---|---:|---|---:|---|
| no_input | 60 | early_no_input | 69 | `(56,205)-(261,206)` |
| no_input | 282 | story_anchor | 62 | `(39,205)-(128,206)` |
| coin_start | 340 | pre_coin | 62 | `(39,205)-(128,206)` |
| coin_start | 371 | coin_accept_window | 0 | none |
| coin_start | 411 | prompt_window | 63 | `(111,194)-(200,195)` |
| coin_start | 473 | start_clear_window | 0 | none |
| coin_start | 534 | round_window | 0 | none |

Interpretation: the reorder changes the visible boundary by roughly one scanline at some anchors. It does not produce a full-frame restoration in MAME, but it is also not unchanged/worse.

## Frame Sanity

Representative Build 0135 runtime values:

| frame | label | state `%a5@(0/2/4)` | BG nz | FG nz | SAT nz | drawable | emitted | producer OOB | resident nz |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 282 | story_anchor | `0/1/2` | 168 | 146 | 0 | 23 | 23 | 0 | 27 |
| 371 | coin_accept_window | `1/1/0` | 168 | 72 | 68 | 23 | 23 | 0 | 27 |
| 411 | prompt_window | `1/1/0` | 168 | 72 | 0 | 19 | 19 | 0 | 27 |
| 473 | start_clear_window | `2/2/6` | 0 | 8 | 96 | 24 | 24 | 0 | 27 |
| 474 | stale_redraw_window | `2/2/6` | 0 | 8 | 120 | 30 | 30 | 0 | 30 |
| 477 | second_clear_window | `2/2/6` | 0 | 8 | 120 | 30 | 30 | 0 | 30 |
| 534 | round_window | `2/2/7` | 0 | 11 | 128 | 32 | 32 | 0 | 32 |
| 620 | late_coin_run | `2/2/7` | 0 | 11 | 125 | 32 | 32 | 0 | 32 |

Build 0134 and Build 0135 frame-state logs are identical at the sampled anchors, except for the expected final image timing differences. This supports that the reorder did not perturb gameplay state, PC080SN staging, or PC090OJ SAT/cache accounting in the smoke windows.

Residency-cache writes in steady state were not separately watchpointed in this task, but resident slot count remains warm (`27..32`) and no per-frame sprite tile-DMA churn is implied by the sampled counters. The Build 0132 residency-cache proof remains the controlling evidence.

## Classification

**Production reorder implemented; visual result = narrowly reduced band, not full fix.**

The change is mechanically correct and build-clean. In MAME final-composite evidence it reveals one additional scanline of content at several anchors, so the band is **reduced** rather than unchanged/worse. However, the frame is still not mostly/full visible in no-input title/story samples. This means Build 0135 is a valid narrow production timing reorder, but further graphics-output work remains necessary for OPEN-001.

## Non-Actions

No changes were made to:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/scene_load.s`
- PC090OJ logic
- PC080SN logic
- residency cache logic
- tools or invariants
- `KNOWN_FINDINGS.md`
- open/closed issue status

No diagnostic ROM or instrumentation was added.

## Open / Closed Issues Impact

- OPEN-001: touched; remains open. Build 0135 narrowly improves timing visibility but does not complete graphics output.
- OPEN-024: context only; no sprite/cache regression observed; remains open.
- OPEN-015: not touched.
- Issues opened: NONE.
- Issues closed: NONE.

## KNOWN_FINDINGS Impact

Option A - no update. This task produced a production reorder and smoke evidence, but the durable mechanism remains the prior Build 0133 timing finding plus Andy's design. Build 0135 did not fully resolve the visual-output failure.

## STOP

STOP triggered: **NO**.

Rationale: build passed, gate passed, invariant/coverage unchanged, no duplicate DISPLAY_ON, no unauthorized source areas touched, no new scroll seam/palette corruption observed, and the band was narrowly reduced rather than unchanged/worse in the MAME evidence.
