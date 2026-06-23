# Cody - Build 0094 Additive FG Text Replacement Classification

**Date:** 2026-06-23  
**Type:** Runtime diagnostic / evidence capture only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`  
**ROM SHA256:** `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`  
**Scope:** Existing Build 0094 ROM only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No bookmark cycle. No exception analysis.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010 (FG -> Plane A), KF-011 (arcade VBlank owns lifecycle), KF-013 (text producers fire inside VBlank), KF-028 (input/text arc), KF-029 (Build 0094 nonzero FG cell composition), KF-030, and KF-031. Issues touched: OPEN-001 active, OPEN-016 context, OPEN-015 do-not-touch.

Architecture compliance: **CONFIRMED**. This task used MAME/debugger observation against the existing Build 0094 ROM. No production code or ROM artifact was changed.

## Evidence Artifacts

Trace directory: `states/traces/build_0094_additive_fg_text_replacement_20260623_140821/`

Primary no-input artifacts:
- `mame_additive_fg_text_replacement.cmd`
- `native_events.log`
- `native_debug_trace.log.gz`
- `fg_before_3acae.bin`
- `fg_after_3acae.bin`

Secondary coin/start artifacts:
- `input_coin_start_manual_timing.lua`
- `input_coin_start_manual_timing_trace.log`
- `mame_additive_fg_coin_start_trace.cmd`
- `secondary_events.log`
- `secondary_debug_trace.log.gz`
- `secondary_fg_before_3acae.bin`
- `secondary_fg_after_3acae.bin`
- `secondary_fg_at_game_start_state0_write.bin`
- `secondary_fg_at_crash_halt.bin`

Reduced analysis:
- `additive_fg_text_replacement_analysis.json`
- `additive_fg_text_replacement_analysis.md`
- `analyze_additive_fg.py`

## Captured Transition

**Primary captured transition:** earliest proven no-input FG replacement boundary: pre-existing title/attract FG state -> `0x3ACAE` story/insert-coin producer.

Reason: the requested no-input ranking/high-score producer (`0x3AD08`) was not reached, but the earlier no-input boundary was sufficient. Before `0x3ACAE`, `staged_fg_buffer` already contained `62` nonzero cells. At `0x3ACAE`, the story/insert-coin producer ran once, then `0x3ACB6` first render ran once, and the buffer after the producer contained `191` nonzero cells.

## WRAM Staging Evidence

Primary no-input comparison (`fg_before_3acae.bin` -> `fg_after_3acae.bin`):

| Measure | Count |
|---|---:|
| Before nonzero cells | `62` |
| After nonzero cells | `191` |
| Pre-existing nonzero cells still nonzero after | `62` |
| Pre-existing cells retained with same value | `56` |
| Added nonzero offsets | `129` |
| Cleared offsets | `0` |
| Changed/overwritten offsets | `6` |

Representative retained old cells:
- `0x0BA4: 0x0001 -> 0x0001`
- `0x0C24: 0x0014 -> 0x0014`
- `0x0C26: 0x0015 -> 0x0015`
- `0x0D12: 0x0016 -> 0x0016`

Representative added cells:
- `0x0420 = 0x001F`
- `0x0422 = 0x0024`
- `0x0424 = 0x0028`
- `0x06A6 = 0x001F`

Interpretation: the later producer did **not** replace the prior FG layout. It accumulated new cells into the same persistent `staged_fg_buffer` while retaining the earlier cells.

## Clear / Dirty / Commit Behavior

Primary event counts:
- `PRODUCER_3ACAE_BEFORE`: `1`
- `PRODUCER_3ACB6_FIRST_RENDER`: `1`
- `FG_STORE_70794`: `258`
- `FG_STAGING_WRITE`: `2306`
- `FG_DIRTY_WRITE`: `550`
- `FG_COMMIT_ROW_START_701AA`: `16`
- `CWINDOW_CLEAR_CALLER_563B6`: `0`
- `CWINDOW_CLEAR_ENTRY_710D8`: `0`
- `CWINDOW_CLEAR_DONE_71130`: `0`

The producer writes cells to `staged_fg_buffer` and marks dirty rows. VBlank commits dirty rows to Plane A and clears dirty flags. No `0x563B6 -> 0x710D8 -> 0x71130` WRAM staging clear fired at the boundary.

This rules out R3 and R4 for this captured boundary: WRAM staging itself retained the old cells; the issue is not only VDP nametable residue or a clear/commit ordering race.

## Secondary Coin/Start Corroboration

The secondary trace used P1 A as the coin edge and P1 Start as Start, matching the input shim mapping. It proves scripted input acceptance:

- `START_GATE_3AB1A`: `216` hits with `credits=0001`.
- Last Start gate sample had `input_ff60ff=F7`, proving P1 Start was seen active-low.
- `CREDIT_SUBTRACT_3AB5E`: `1` hit, `credits_before=0001`.
- `GAME_START_STATE0_WRITE_3ABDE`: `1` hit, `credits=0000`, `s0_before=0001`.

Secondary staging comparison:

| Boundary | Before nonzero | After nonzero | Retained nonzero | Added | Cleared |
|---|---:|---:|---:|---:|---:|
| story after `0x3ACAE` -> game-start accept | `191` | `216` | `189` | `27` | `2` |
| game-start accept -> halt marker | `216` | `218` | `208` | `10` | `8` |
| story after `0x3ACAE` -> halt marker | `191` | `218` | `181` | `37` | `10` |

No clear fired in the secondary capture either:
- `CWINDOW_CLEAR_CALLER_563B6`: `0`
- `CWINDOW_CLEAR_ENTRY_710D8`: `0`
- `CWINDOW_CLEAR_DONE_71130`: `0`

Game-start note: the scripted secondary captured game-start acceptance, but it did not hit the watched `ROUND_RENDER_3ADCA` or `STATE0_WRITE_3_SITE_3ADD6` points before the halt marker. Therefore this trace does not prove a complete game-start text block in staging. It does prove partial/additive post-start staging changes over retained attract/story cells.

The exception/halt event is used only as an end-of-window marker. No crash PC/address/vector analysis was performed.

## Classification

**R1 - staging never cleared between states.**

Decisive WRAM evidence:
- Before `0x3ACAE`, `staged_fg_buffer` contained `62` nonzero cells.
- After `0x3ACAE`, all `62` previous nonzero cells were still nonzero, `56` unchanged, and `129` new nonzero offsets had been added.
- No WRAM clear path (`0x563B6`, `0x710D8`, `0x71130`) fired at the boundary.
- VBlank commit activity occurred, but it cleared dirty flags only; it did not clear staging contents.

Not R2: no clear fired, so there is no post-clear re-emission to explain the primary boundary.  
Not R3: WRAM staging itself retained old cells.  
Not R4: no clear/commit ordering interaction occurred at the captured boundary.

## Recommended Target

Recommended next fix target: add/route a production translation-layer WRAM FG staging clear at the semantic title/attract FG layout replacement boundary, beginning with the proven no-input `0x3ACAE` boundary. The clear must operate on WRAM staging and mark dirty rows for commit; it must not be a visible-VDP-only clear, per-frame clear, producer bypass, or exception/Start workaround.

If the same mechanism is later confirmed for BG, extend only with separate BG evidence. This task classifies Plane A / FG text only.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-016, OPEN-015 context only
- Closed issues touched: NONE
- New issues opened: NONE
- Issues closed: NONE
- Issues intentionally deferred: gameplay exception triage, OPEN-015 crash-handler fix, BG/logo/sword/sprite/palette/CRAM/VRAM/scroll analysis

## KNOWN_FINDINGS Impact

Option C candidate: KF-029/KF-028 could be refined later to record that Build 0094 nonzero FG cells persist across title/attract FG layout replacement because no WRAM staging clear fires at the boundary. `KNOWN_FINDINGS.md` was not edited in this diagnostic task.

## STOP

STOP triggered: **NO**. The secondary trace timed out after the halt marker because the debugger did not exit on `quit`, but the required events and snapshots were captured. The exception was not analyzed.
