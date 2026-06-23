# Cody - Build 0094 Text-Clear Boundary Proof

**Date:** 2026-06-23  
**Type:** Runtime diagnostic / boundary proof only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`  
**ROM SHA256:** `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`  
**Scope:** Existing Build 0094 ROM only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No bookmark cycle. No gameplay exception / OPEN-015 work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-028 (input-shim/title-text arc), KF-029 (Build 0094 nonzero FG cell composition), KF-013 (text producer dispatch inside VBlank), KF-011 (arcade VBlank owns lifecycle), KF-010 (FG maps to Plane A), KF-004 (runtime PC equals file offset), KF-006 (identity offset), and KF-001 as context only. Open issues touched: OPEN-001 active, OPEN-016 context, OPEN-015 do-not-touch.

Contradiction detected: **NO**. Architecture compliance: **CONFIRMED**. This task used existing MAME/debugger observation only. No diagnostic ROM, no scaffolding, no source change, and no crash-cause analysis.

## Prior Result Continued

`docs/design/Cody_build_0094_attract_text_clear_lifecycle_diagnostic.md` classified the observed title/attract text transition as **E**: `0x3ACAE` writes persistent `staged_fg_buffer` cells, VBlank commit clears only dirty flags, and the known `cwindow_clear` helper was not reached. Static source/disassembly already proves `genesistan_hook_cwindow_clear` (`runtime_genesis_pc 0x000710D8`) clears both WRAM BG and FG staging and marks full dirty when reached.

This task targeted the two unproven gaps from that prior result:

1. Whether follow-on attract producer `runtime_genesis_pc 0x0003AD08` executes in a reachable attract/title state.
2. Whether the game-start clear path `runtime_genesis_pc 0x000563B6 -> 0x000710D8 -> 0x00071130` can be reached with tuned input timing, allowing post-clear staging/redraw classification.

## Evidence Artifacts

- Trace directory: `states/traces/build_0094_text_clear_boundary_proof_20260623_111454/`
- Debugger scripts: `mame_text_clear_boundary.cmd`, `mame_text_clear_boundary_attempt2.cmd`, `mame_text_clear_boundary_attempt3.cmd`
- Input script/logs: `input_timing.lua`, `input_timing_attempt1.log`, `input_timing_attempt2_no_input.log`, `input_timing_attempt3_late_start.log`
- Native traces: `native_debug_trace.log`, `native_debug_trace_attempt2.log`, `native_debug_trace_attempt3.log`
- Event streams: `native_events_attempt1.log`, `native_events_attempt2.log`, `native_events_attempt3.log`
- Reduced analysis: `text_clear_boundary_analysis.json`, `text_clear_boundary_analysis.md`

The crash-handler halt was used only as a stop boundary. The gameplay exception was not diagnosed.

## Input Timings Tried

| Attempt | Timing | Purpose |
|---|---|---|
| Prior diagnostic | P1 A frames 520-522; P1 Start frames 640-700 | Earlier game-start attempt from previous E diagnostic |
| Attempt 1 | P1 A frames 520-525; P1 Start frames 1080-1140 | Later Start near the user-reported ~18s window |
| Attempt 2 | No P1 A; no P1 Start; interrupted after 2042 VBlank entries | Long no-input attract/title window for `0x3AD08` reachability |
| Attempt 3 | P1 A frames 520-525; P1 Start frames 1800-1880 | Later game-start attempt after a longer attract window |

P1 C was explicitly kept unpressed. The task prompt required coin/start timing adjustment; Start/C/A crash behavior remains out of scope.

## Boundary Observations

| Attempt | VBlank entries | `0x3AD08` | `0x563B6` | `0x710D8` | `0x71130` | Crash halt |
|---|---:|---:|---:|---:|---:|---:|
| Prior diagnostic | 700 | 0 | 0 | 0 | 0 | repeated halt sampling |
| Attempt 1 | 1139 | 0 | 0 | 0 | 0 | 1 |
| Attempt 2 | 2042 | 0 | 0 | 0 | 0 | 0 |
| Attempt 3 | 1859 | 0 | 0 | 0 | 0 | 1 |

Common observed title/attract path across the new attempts:

- `runtime_genesis_pc 0x0003AC54` entry/kick producer: observed once.
- `runtime_genesis_pc 0x0003ACAE`: observed once.
- `runtime_genesis_pc 0x0003ACB6`: observed once.
- `runtime_genesis_pc 0x0003ACF8`: observed once, advancing `%a5@(4)` from `1` to `2`.
- FG staging stores at `runtime_genesis_pc 0x00070794`: observed in attempts 1-3, with the same Build 0094 nonzero-cell behavior as prior evidence.

The follow-on producer `0x0003AD08` did **not** execute in the long no-input window (2042 VBlank entries). The game-start clear caller/helper path did **not** execute in either tuned game-start attempt.

## Required Question Answers

1. **Does `0x3AD08` execute in a reachable attract/title state?**  
   **Not observed.** Attempt 2 supplied a long no-input window with 2042 VBlank entries; `0x3AD08`, `0x3AD12`, and `0x3AD48` remained at zero hits.

2. **Does `0x563B6 -> 0x710D8 -> 0x71130` execute at game start with tuned input timing?**  
   **Not observed.** Timings tried: prior `A 520-522 / Start 640-700`, attempt 1 `A 520-525 / Start 1080-1140`, and attempt 3 `A 520-525 / Start 1800-1880`. Both tuned Start attempts reached the crash halt with state `%a5@(0)/@(2)/@(4)=2/2/4` before any `0x563B6` or `0x710D8` event.

3. **If a visible clear occurs at game start, does WRAM staging still contain old text after the clear?**  
   **Not observed.** The clear path did not execute, so there is no post-clear WRAM interval in this evidence. Static prior remains: if `0x710D8` executes, it clears WRAM `staged_bg_buffer` and `staged_fg_buffer` and marks full dirty.

4. **After that clear, are stale redraw cells recommitted, re-emitted, or only left in VDP?**  
   **Not distinguishable in this task.** No post-clear runtime interval was captured. B-vs-D-vs-already-cleared cannot be classified from these traces.

5. **Correct implementation target: `0x3ACAE`, broader page-boundary set, or separate game-start boundary?**  
   **Proven boundary set is currently `0x3ACAE` only.** `0x3AD08` was not observed and should not be included in a fix yet. The game-start clear/redraw path was **NOT-REPRODUCED** and should not drive implementation placement yet.

## Game-Start Redraw Classification

**Classification: NOT-REPRODUCED.**

The user-visual observation remains: near game start, the screen visibly clears, then stale attract/title text redraws for 1-2 frames before the exception. This task did not reproduce that as runtime events. Specifically, it did not reach the known clear path `0x563B6 -> 0x710D8 -> 0x71130`, so it cannot classify the game-start redraw as SAME-E or SEPARATE-D.

### Addendum - Manual Video Reachability Correction

Later manual MAME video evidence (`states/screenshots/mame_build_94.mp4`, reduced in `states/screenshots/mame_build_94_unique_screens/`) proves the coin-up/start visual path was reachable outside this scripted trace:

- coin accepted prompt at frame `000371` / `12.333s`
- `PUSH 1 OR 2 PLAYER BUTTON` prompt at frame `000411` / `13.667s`
- start clear at frame `000473` / `15.733s`
- stale text redraw at frame `000474` / `15.767s`
- second clear at frame `000477` / `15.867s`
- `ROUND` at frame `000534` / `17.767s`

Therefore, the **NOT-REPRODUCED** result above must be interpreted narrowly: the scripted runtime trace did not reproduce the manual coin-up/start path. It must **not** be used as evidence that the game-start clear/redraw is absent, unreachable, or irrelevant.

The gray arrow-with-line visible in the extracted screenshots/contact sheet is confirmed host overlay contamination and must be ignored. It is not evidence for sprites, VDP output, tilemap contents, cursor graphics, scroll artifacts, or game state.

Before any implementation that claims to address the game-start redraw, a video-anchored runtime trace is still required to prove whether frame `000474` stale text comes from surviving `staged_fg_buffer`, a producer re-emitting old text, VDP residue, or clear/dirty ordering. The exception remains a halt boundary only; do not record on-screen crash PC/address/vector as proven unless independently verified from debugger-side evidence or the WRAM crash record.

What is proven:

- `0x3ACAE` is a title/attract text producer boundary and writes persistent WRAM FG staging.
- VBlank commit clears dirty flags only and does not clear staging.
- `0x3AD08` was not observed in a long no-input window.
- `0x563B6` / `0x710D8` / `0x71130` were not observed under the game-start timings tried.

What is not proven:

- That game-start stale redraw is the same E-class gap.
- That game-start stale redraw is a separate D-like replay after a clear.
- That WRAM staging survives after the user-visible game-start clear.
- That stale cells are recommitted, re-emitted, or only left in VDP after that clear.

## Recommended Implementation Target

Recommended implementation target: **the proven title/attract producer boundary at `runtime_genesis_pc 0x0003ACAE`, and only that boundary unless further runtime evidence proves additional boundaries.**

The production fix should clear the Genesis WRAM tilemap staging at the semantic title/attract page boundary, then mark dirty rows so the VBlank commit reflects the cleared state. It must not clear per frame, must not bypass arcade producers, and must not use the unobserved game-start clear/redraw as placement evidence.

A broader boundary set may be warranted later, but only after observing additional producers such as `0x0003AD08` or reproducing the user-visible game-start clear path. The current evidence does not authorize a separate game-start clear fix.

For game-start redraw specifically, the manual video proves the visual sequence exists, but it does not identify the runtime cause. Any game-start-targeted implementation must first collect a video-anchored trace across the observed frames (`000473`-`000477`) and classify the stale redraw source. The scripted NOT-REPRODUCED result is a limitation of the trace, not a negative proof against the manual video.

## Open / Closed Issues Impact

- OPEN-001: active; this diagnostic narrows the immediately proven clear-boundary target to the title/attract producer at `0x3ACAE`.
- OPEN-016: context; Build 0094 glyph renderer/staging path remains valid context.
- OPEN-015: context only; crash-handler and gameplay exception analysis intentionally untouched.
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: gameplay-start exception, OPEN-015 crash-handler defects, BG artwork producer path, TAITO logo completeness, sprites/palette/scroll, dot rows, broader unhooked-writer survey, real-hardware compatibility.

## KNOWN_FINDINGS Impact

Option A - no `KNOWN_FINDINGS.md` update. This task adds bounded non-observation evidence and preserves the prior candidate refinement from the E diagnostic, but it does not prove a new durable mechanism beyond the already established title/attract staging lifecycle gap.

## STOP

STOP triggered: **NO**. The clear path not being reached is a reported NOT-REPRODUCED result, not a STOP. The gameplay exception was used only as a halt boundary and was not diagnosed.
