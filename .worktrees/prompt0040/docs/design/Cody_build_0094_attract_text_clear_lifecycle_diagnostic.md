# Cody - Build 0094 Attract Text-Clear Lifecycle Diagnostic

**Date:** 2026-06-22  
**Type:** Runtime diagnostic / evidence capture only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`  
**ROM SHA256:** `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`  
**Scope:** Existing Build 0094 ROM only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No bookmark cycle. No gameplay exception / OPEN-015 work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-028 (input-shim/title-text arc through Build 0094), KF-013 (text dispatch inside VBlank), KF-011 (arcade VBlank owns lifecycle; Genesis helpers service hardware), KF-010 (FG maps to Plane A), KF-004 (runtime PC equals file offset), KF-006 (identity offset), and KF-001 as watchdog context only. Open issues touched: OPEN-001 active, OPEN-016 context, OPEN-015 do-not-touch.

Contradiction detected: **NO**. Architecture compliance: **CONFIRMED**. This task used the existing MAME/debugger workflow as read-only runtime observation and did not alter the ROM or add instrumentation.

## Evidence Artifacts

- Trace directory: `states/traces/build_0094_attract_text_clear_lifecycle_20260622_231814/`
- Debugger script: `mame_attract_text_clear_lifecycle.cmd`
- Input pulse script/log: `input_pulse.lua`, `input_pulse.log`
- Native trace: `native_debug_trace.log`
- Extracted event stream: `native_events.log`
- Reduced analysis: `attract_text_clear_lifecycle_analysis.json`, `attract_text_clear_lifecycle_analysis.md`

MAME was run against Build 0094. The input script pulsed P1 A at frames 520-522 and held P1 Start at frames 640-700. The trace was stopped at the crash-handler halt boundary; the gameplay exception was not diagnosed.

## Static Lifecycle Anchors

- `runtime_genesis_pc 0x0003ACAE` is the title text producer for the `%a5@(4)==1` title sub-state. It calls the glyph renderer at `0x0003ACB6`, `0x0003ACBC`, `0x0003ACC2`, `0x0003ACC8`, and subsequent sites, then advances `%a5@(4)=2` at `0x0003ACF8`.
- `runtime_genesis_pc 0x0003AD08` is the next attract producer block. It was watched but not observed in this run.
- `runtime_genesis_pc 0x000563B6` calls `genesistan_hook_cwindow_clear` at `runtime_genesis_pc 0x000710D8`. This caller was watched but not observed in this run.
- `genesistan_hook_cwindow_clear` is a real WRAM staging clear when reached: it clears `staged_bg_buffer` at `WRAM 0x00FF401A`, clears `staged_fg_buffer` at `WRAM 0x00FF501A`, then writes `0xFFFFFFFF` to `bg_row_dirty` and `fg_row_dirty`.
- `_vblank_service` calls `vdp_commit_fg_strips_if_dirty`; the FG commit copies dirty rows from `staged_fg_buffer` and clears dirty flags. It does **not** clear the staging buffer.

Therefore the known `cwindow_clear` path, if reached, clears WRAM staging and marks full dirty. It is not a visible-VDP-only clear.

## Runtime Results

Reduced event counts:

| Event | Count |
|---|---:|
| `VBLANK_ENTRY` | 700 |
| `VBLANK_EXIT_HANDOFF` | 700 |
| `PRODUCER_3ACAE` | 1 |
| `PRODUCER_3ACB6_FIRST_RENDER` | 1 |
| `FG_STORE_70794` | 401 |
| `FG_DIRTY_WRITE` | 856 |
| `FG_COMMIT_ENTRY_70182` | 700 |
| `FG_COMMIT_ROW_START_701AA` | 26 |
| `FG_COMMIT_ROW_DONE_701BE` | 26 |
| `CWINDOW_CLEAR_CALLER_563B6` | 0 |
| `CWINDOW_CLEAR_ENTRY_710D8` | 0 |
| `CWINDOW_CLEAR_DONE_71130` | 0 |
| `PRODUCER_3AD08_ATTRACT_NEXT` | 0 |
| `STATE0_WRITE_2_SITE_3AD48` | 0 |

Key observed events:

- At frame 211, `0x0003ACAE` executed with state `%a5@(0)/@(2)/@(4) = 0/1/1`.
- At frame 211, first render call `0x0003ACB6` executed with `d0=0x11`.
- The FG staging store at `0x00070794` executed 401 times, with 313 nonzero cell values and `%a6=0x00FF501A`, proving writes went into `staged_fg_buffer`.
- No clear caller (`0x000563B6`) and no clear helper entry/done point (`0x000710D8` / `0x00071130`) executed before the input-driven halt.
- The trace reached the crash-handler halt at frame 699 with state `%a5@(0)/@(2)/@(4) = 2/2/4`; this was used only as a stop boundary, not as crash-cause evidence.

## Two-Transition Comparison

| Transition target | Runtime evidence | Clear observed? | Backing-state result |
|---|---|---|---|
| Title/attract text entry (`0x3ACAE -> 0x3ACB6`) | Producer and first render call observed once; FG staging stores observed and committed | **NO** | Text is written into persistent WRAM `staged_fg_buffer`; commit clears dirty flags only |
| Input-driven game-start attempt | A/Start input was sent; trace halted at crash-handler boundary before `0x563B6` / `0x710D8` | **NO before halt** | No evidence of the known WRAM staging clear before the stop boundary; gameplay exception deliberately not analyzed |

Tighe's user-visual observation says a visible clear occurs near game start and stale title/attract text can redraw afterward. This trace does not identify that visible clear source. It does prove that the known `cwindow_clear` helper did not execute in the captured pre-halt window, and that the known helper would clear WRAM staging if it did execute.

## Classification

**Classification: E - no arcade clear exists at the title/attract text transition; the correct fix target is a translation-layer WRAM staging clear at the semantic transition point.**

Decisive evidence:

- The title text producer runs and emits cells into `staged_fg_buffer`.
- The VBlank commit path commits dirty rows but only clears dirty flags, leaving staging contents persistent by design.
- No `cwindow_clear` event occurs at the observed title/attract text transition.
- The known `cwindow_clear` helper clears WRAM staging, not only the visible VDP layer, so B is not supported for that helper.
- C is not supported for the known helper because its static range covers both 2048-word BG and FG staging buffers.
- D is not proven: no clear was observed before a later producer/staging replay in this run.
- A is true at the observed transition, but E is the tighter classification because the absent clear is a Genesis translation-layer lifecycle obligation with no direct arcade staging-buffer equivalent.

## Recommended Next Fix Target

Recommended next target: add a production translation-layer clear of the Genesis WRAM tilemap staging at the exact arcade semantic boundary where a new title/attract text page begins and prior page text should stop existing. The candidate boundary must be proven before implementation; likely candidates are the one-shot title/attract producer entry path(s), beginning with `runtime_genesis_pc 0x0003ACAE` for the observed text page and then the follow-on producer path around `0x0003AD08` if separately observed.

The fix should clear WRAM staging and mark dirty rows, not only clear the visible VDP layer. It must not clear per frame, must not bypass producers, and must preserve arcade-owned state progression.

## BG Relevance

The same lifecycle gap could affect BG artwork because `genesistan_hook_cwindow_clear` clears both BG and FG staging when reached. This diagnostic did not investigate BG producer correctness, TAITO logo completeness, sprite/palette paths, or dot rows.

## Open / Closed Issues Impact

- OPEN-001: active; this diagnostic supports keeping the next task focused on graphics lifecycle/staging, not gameplay exception handling.
- OPEN-016: context; Part 2 hook writes FG staging correctly, but lifecycle clearing remains open graphics work.
- OPEN-015: context only; no crash-handler work performed.
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.

## KNOWN_FINDINGS Impact

Option C candidate only; `KNOWN_FINDINGS.md` was not edited. The durable candidate refinement is that Build 0094 title/attract text producers can populate persistent Genesis FG staging without a semantic translation-layer clear at the title/attract text transition; the known `cwindow_clear` helper is WRAM-backed but was not reached in the observed transition.

## STOP

STOP triggered: **NO**. Scope boundary honored: the gameplay exception was used only as a halt boundary and was not diagnosed. Measurement limitation: the user-visual game-start clear/redraw was not reproduced as a reached `0x563B6` / `0x710D8` event in this run, so that visible clear source remains unidentified.
