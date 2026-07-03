# Cody - Build 0135 Remaining DISPLAY_OFF Budget and PC090OJ Scan-Depth Analysis

**Date:** 2026-07-03
**Type:** Evidence reduction / timing analysis only
**Build context:** Build 0135, `dist/rastan-direct/rastan_direct_video_test_build_0135.bin`, SHA256 `8e00be424f9afefe79d199640096bf99de7b53c4ba49e83ad32b2b491990844e`
**Scope:** Existing evidence only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No diagnostic ROM. No bookmark. No runtime trace gathered.

## Phase 0

Classification: **EXTENDING**. Primary issue context: OPEN-001. Related context: OPEN-024 sprite/cache work, OPEN-015 not touched.

Relevant priors loaded: KF-010, KF-011, KF-013, KF-021/KF-032/KF-038 context, the Build 0132 sprite tile residency cache report, the Build 0133 HV/VCounter diagnostic report, Andy's Build 0134 display-on timing design, and the Build 0135 DISPLAY_ON reorder report.

Contradiction detected: **NO**.

Architecture compliance: **CONFIRMED**. This is reduction of existing timing/sprite evidence only. Arcade code remains the program; Genesis code remains service/helper code. No patches or diagnostics were inserted.

## Evidence Artifacts

New evidence-reduction directory:

- `states/traces/build0135_remaining_display_off_budget_pc090oj_scan_depth_20260703_104442/`
- `remaining_display_off_budget_reduction.json`
- `remaining_display_off_budget_reduction.md`
- `reduce_existing_evidence.py`

Inputs reduced:

- `states/traces/build0133_hv_vcounter_display_on_diagnostic_20260702_215520/`
- `states/traces/build0135_display_on_timing_reorder_20260702_222926/build0135/`
- `states/traces/pc090oj_persistent_sprite_tile_dma_cache_build0132_20260702_210813/sprite_resident_write_analysis.json`

Important reduction note: `latest_by_checkpoint` rows can straddle two VBlanks when the capture lands mid-service. The reducer therefore groups raw ring entries by the same diagnostic frame and uses only internally consistent checkpoint sequences for stage ranking.

## Q1 - Build 0133 Stage Timing Reduction

The Build 0133 diagnostic has overhead and must not be treated as exact production scanline truth. It is still useful for relative ranking.

Across `73` complete raw diagnostic-frame sequences, most non-sprite stages advance only about one or two VCounter lines. The sprite stage is the only normal per-frame stage that usually crosses the VCounter discontinuity/wrap in the same checkpoint sequence.

Classification counts from the reducer:

| Stage | Main observed classifications |
|---|---|
| `display_off_write` | `about_one_vcounter_line` in 58/73; `about_two_vcounter_lines` in 15/73 |
| `tiles` | `about_one_vcounter_line` in 63/73; `about_two_vcounter_lines` in 10/73 |
| `bg_commit` | `about_one_vcounter_line` in 35/73; `about_two_vcounter_lines` in 37/73 |
| `fg_commit` | mostly one line; a few noisy/discontinuity outliers |
| `pre_sprite_gap` | mostly one line |
| `sprite_commit_total` | `crosses_vcounter_discontinuity_or_wrap` in 54/73, with a few non-crossing/outlier samples |
| `palette_or_skip` | mostly one line |
| `scroll_commit` | mostly two lines |
| `display_on_write` | one or two lines |

Representative stable no-input frame from the reduction:

| Stage | From V,H | To V,H | Classification |
|---|---:|---:|---|
| `tiles` | `228,240` | `229,021` | about one line |
| `bg_commit` | `229,021` | `231,134` | about two lines |
| `fg_commit` | `231,134` | `232,097` | about one line |
| `pre_sprite_gap` | `232,097` | `233,147` | about one line |
| `sprite_commit_total` | `233,147` | `212,018` | crosses VCounter discontinuity/wrap |
| `palette_or_skip` | `212,018` | `213,094` | about one line |
| `scroll_commit` | `213,094` | `215,050` | about two lines |
| `display_on_write` | `215,050` | `217,063` | about two lines |

Interpretation: the remaining display-off-critical budget is dominated by the sprite stage, not by palette/scroll after the Build 0135 reorder.

## Q2 - Dominant Remaining DISPLAY_OFF Stage

The dominant remaining stage is **`vdp_commit_sprites`**.

Static source proof in `apps/rastan-direct/src/pc090oj_hooks.s`:

```asm
vdp_commit_sprites:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lvcs_mirror_scan
    bsr     .Lvcs_link_chain_build
    bsr     .Lvcs_tile_dma
    bsr     .Lvcs_sat_dma
    bsr     .Lvcs_clear_dirty
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

So Build 0135 still performs the following while the display is off:

- generated SAT/descriptor clearing
- full PC090OJ mirror scan
- 80-slot Genesis SAT link-chain build
- conditional sprite tile DMA
- fixed SAT DMA
- dirty-flag cleanup

Build 0132 cache evidence narrows the likely culprit inside this block. Runtime tile-DMA cache updates stop after frame 43 in the long sampled run, while the final state still has `decoded=0x0100`, `drawable=0x20`, `emitted=0x20`. Therefore repeated sprite tile DMA is not the steady-state cost. The remaining steady cost is the CPU-side scan/link/build work plus fixed SAT DMA.

Observable fact: Build 0133 sprite stage is the largest remaining timing block.

Inference: after Build 0132 cache warm-up, the full 256-entry mirror scan and associated descriptor/link work are likely the main avoidable display-off CPU cost.

## Q3 - PC090OJ 256-Entry Scan-Depth Audit

Static source proof:

- `.Lvcs_mirror_scan` initializes `%d6=0` as the PC090OJ entry index.
- `.Lvcs_mirror_scan_loop` exits only when `%d6 >= 256`.
- `pc090oj_decoded_count` increments before per-entry reject tests.
- The loop advances `a0 += 8` and `%d6 += 1` every iteration.

Runtime evidence from Build 0135 complete-scan samples:

| Metric | Result |
|---|---:|
| Complete scan samples | 15 |
| Decoded min/max | `256 / 256` |
| Drawable min/max | `19 / 32` |
| Emitted min/max | `19 / 32` |
| Dropped max | `0` |

Complete samples included no-input, coin-accept, prompt, stale redraw, second clear, ROUND, and late coin-run anchors.

Object RAM dump density:

| Metric | Result |
|---|---:|
| Highest nonzero object record index | `239` in all sampled dumps |
| Highest nonzero tile-code index | `45` in all sampled dumps |
| Highest staged descriptor source_id in valid descriptor dumps | `45` |

Interpretation:

- Current runtime always pays for the full 256-entry scan in completed frames, even when only 19-32 sprites are emitted.
- Captured title/story/game-start samples use nonzero sprite tile codes only up through PC090OJ object index `45`.
- However, many records above 45 are still nonzero tuples with zero tile code, reaching index `239`. A naive early exit based on all-zero records would not trigger safely in these samples.
- A hard scan cap around `48` would match these captured screens, but it is not proven safe for gameplay or other attract states.

## Q4 - Arcade / Gameplay Capacity Check

Static capacity facts:

- The active PC090OJ mirror is `0x800` bytes: 256 entries at 8 bytes each.
- `PC090OJ_HW_ACTIVE_END` is `0x00D00800`.
- Current scan depth of 256 matches the full active hardware mirror.

Evidence limitation:

- Existing Build 0135 captures cover title/story/game-start samples, not broad gameplay/demo object stress.
- Existing artifacts do not prove that original arcade gameplay never uses object indices above 45 for meaningful sprites.

Conclusion: reducing scan depth globally is **not safe yet**. A scan-depth cap requires an arcade-vs-Genesis gameplay high-water audit first. Moving or splitting the CPU scan while preserving all 256 entries is safer and better aligned with current evidence.

## Q5 - Build 0135 Implication

Build 0135 was useful and not a dead end.

It proved that moving DISPLAY_ON before palette/scroll is only a small improvement: roughly one extra visible scanline in the sampled title/story frames. That means the remaining hidden-time budget is still before the new DISPLAY_ON location, and the evidence points specifically at `vdp_commit_sprites`.

The next work should not undo Build 0135. It should reduce what must happen before DISPLAY_ON, while preserving the arcade-owned frame lifecycle and the Genesis VDP service contract.

## Q6 - Selected Next Branch

Selected branch: **A**.

> Sprite commit is dominant, and the 256-entry PC090OJ scan is likely the major remaining display-off CPU cost. Next design: split/reduce `vdp_commit_sprites`, likely moving CPU mirror scan/descriptor build outside display-off, keeping only VDP-critical sprite tile DMA and SAT DMA inside.

Important boundary: this branch does **not** approve a scan-depth cap. The scan cap remains unproven for gameplay. The safer branch is to preserve 256-entry semantics but move or split CPU-only work out of the display-off window.

## Q7 - Copy-Ready Next Prompt

```text
[Cody/Andy - Design/Implementation Plan: Split PC090OJ CPU Scan Out of DISPLAY_OFF Window]

Context:
Build 0135 moved DISPLAY_ON before palette/scroll and produced only a one-scanline visual improvement. Cody's Build 0135 remaining DISPLAY_OFF budget analysis reduced Build 0133/0135 evidence and selected Branch A: `vdp_commit_sprites` is the dominant remaining display-off-critical block.

Key evidence:
- Build 0133 checkpoint reduction: most non-sprite stages are about 1-2 VCounter lines; `sprite_commit_total` is the only regular stage that usually crosses the VCounter discontinuity/wrap.
- Build 0135 complete-scan samples: every completed sprite scan decodes 256 PC090OJ entries, but emits only 19-32 sprites with dropped=0.
- Build 0135 object dumps: highest nonzero tile-code/source_id in sampled title/story/game-start states is 45, but nonzero records reach index 239, so a naive all-zero early exit is unsafe.
- Build 0132 cache: sprite tile DMA residency warms by frame 43; steady-state tile-DMA updates stop while 32 sprites still emit, so repeated tile DMA is not the steady-state cost.

Objective:
Design, then implement only if the design is mechanically safe, a production split of `vdp_commit_sprites` so CPU-only PC090OJ work (`.Lvcs_mirror_scan`, descriptor generation, and link-chain build if safe) is moved out of the DISPLAY_OFF critical window, while preserving full 256-entry PC090OJ semantics and keeping VDP-critical tile DMA/SAT DMA inside the VBlank service as required.

Mandatory constraints:
- Do not reduce PC090OJ scan depth yet.
- Do not cap at 48/64 entries.
- Do not remove sprites, bypass SAT, or use NOP/RTS hacks.
- Do not change arcade control flow ownership.
- Preserve Build 0132 residency-cache behavior.
- Preserve Build 0135 DISPLAY_ON ordering unless a proven conflict is found.
- No diagnostic ROM unless explicitly authorized.

Required state-causality answers before patching:
1. What sprite staging state should exist when DISPLAY_OFF begins?
2. Which earlier code will create that state if mirror scan moves earlier?
3. Why is that ordering equivalent to the current arcade/Genesis service contract?
4. What remains inside DISPLAY_OFF and why is it VDP-critical?

Deliverables:
- Design note documenting the split boundary.
- Implementation if and only if the split is proven safe.
- Build artifact and static/runtime evidence.
- OPEN-001 / OPEN-024 impact; no issue closure unless separately authorized.
```

## KNOWN_FINDINGS / OPEN Issues

KNOWN_FINDINGS impact: **Option A - no update**. This task reduces timing evidence and selects a next branch, but does not establish a new durable mechanism beyond existing Build 0132/0133/0135 findings.

Open issues touched:

- OPEN-001: active; evidence narrows remaining title/attract visibility failure to sprite commit timing budget.
- OPEN-024: context; Build 0132 residency cache is preserved and remains relevant.
- OPEN-015: not touched.

Issues opened: NONE.
Issues closed: NONE.

## STOP

STOP triggered: **NO**.

No source/spec/tool/Makefile/ROM/invariant files were modified. No build or runtime trace was run. Evidence reduction used existing artifacts only.
