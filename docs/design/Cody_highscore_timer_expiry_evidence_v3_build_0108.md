# Cody - High-Score Timer-Expiry Evidence v3: Arcade vs Build 0108

**Date:** 2026-06-27
**Type:** Runtime evidence / analysis only
**Build:** 0108, `dist/rastan-direct/rastan_direct_video_test_build_0108.bin`
**Build SHA256:** `bd0c7faa187f6d9aded904638e8d7cb8c9e3df6304c5178a36ec02e6c8bbad09`
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build changes. No bookmark cycle. No diagnostic ROM. No fix design or implementation.

## Phase 0

Classification: **EXTENDING**. Relevant context read: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest-first `AGENTS_LOG.md`, `docs/design/real_attract_state_progression_and_coin_audit.md`, `docs/design/Cody_original_arcade_attract_page_replacement_runtime.md`, `docs/design/Cody_build_0094_fg_clear_boundary_pin.md`, and `docs/design/Andy_build_0094_fg_text_lifecycle_static_map.md`.

Address mapping discipline: all arcade-to-Genesis code correlations below were checked through `build/rastan-direct/address_map.json`. No arithmetic offset is used as authority.

Explicit correction from the prompt: prior candidates `runtime_genesis_pc 0x0003AAAC`, `0x0003AAD2`, and `0x0003AE76` are not treated as no-input high-score targets here.

## Evidence Artifacts

Original arcade runtime trace:

- `states/traces/original_arcade_highscore_timer_expiry_v3_20260627_193902/`
- Command file: `mame_arcade_timer_expiry_v3.cmd`
- Reduced event log: `native_events.log`
- Raw trace: `native_debug_trace.log.gz`

Build 0108 runtime trace:

- `states/traces/build_0108_highscore_timer_expiry_v3_20260627_193902/`
- Command file: `mame_build0108_timer_expiry_v3.cmd`
- Reduced event log: `native_events.log`
- Raw trace: `native_debug_trace.log.gz`

Original arcade A5 base observed: `0x0010C000`.

Build 0108 A5 base observed: Genesis WRAM `0x00FF0000`; therefore `FF002C = A5 + 0x2C` is the attract-page countdown timer in the Build 0108 trace.

No coin/start/buttons were scripted in either capture.

## Address Map Anchors

| Meaning | arcade_pc | runtime_genesis_pc | Map kind |
|---|---:|---:|---|
| title-to-story selector write | `0x03AA82` | `0x03AC82` | `arcade_copy` |
| title-to-story timer reload | `0x03AA88` | `0x03AC88` | `arcade_copy` |
| story producer entry | `0x03AAAE` | `0x03ACAE` | `arcade_copy` |
| story timer reload | `0x03AAF2` | `0x03ACF2` | `arcade_copy` |
| story inner-state advance to 2 | `0x03AAF8` | `0x03ACF8` | `arcade_copy` |
| story-expiry/high-score handler entry | `0x03AB00` | `0x03AD00` | `patched_site` |
| high-score clear tail | `0x03AB08` | `0x03AD08` | `arcade_copy`, but skipped in Build 0108 |
| clear helper entry | `0x03AE64` | `0x03B064` | `arcade_copy` |
| clear BG call region | `0x03AE70` | `0x03B070` | `arcade_copy` |
| clear FG call region | `0x03AE80` | `0x03B080` | `arcade_copy` |
| high-score init | `0x03AB0C` | `0x03AD0C` | `arcade_copy` |
| high-score render | `0x03AB12` | `0x03AD12` | `arcade_copy` |
| high-score timer reload | `0x03AB22` | `0x03AD22` | `arcade_copy` |
| high-score master advance | `0x03AB48` | `0x03AD48` | `arcade_copy` |

The mapping for `arcade_pc 0x03AB00..0x03AB08` is the decisive divergence. The original 8 bytes are replaced in Build 0108 by `jsr genesistan_palette_hook_03ab00; rts` at `runtime_genesis_pc 0x03AD00..0x03AD06`.

## Page Selector / Composite State

The no-input attract sequence uses a composite state under master `%a5@(0)=0`:

- Title page is selected by `%a5@(2)=0`.
- At title timer expiry, `0x03AA82` / `0x03AC82` writes `%a5@(2)=1`, beginning the story page family.
- The story producer runs with `%a5@(2)=1`, `%a5@(4)=1`.
- The story producer reloads `%a5@(44)` to `0x00A0` and writes `%a5@(4)=2`.
- The next timer expiry with `%a5@(2)=1`, `%a5@(4)=2` selects the high-score expiry handler at `arcade_pc 0x03AB00` / `runtime_genesis_pc 0x03AD00`.

There is no new selector write at the second timer expiry before `0x03AB00`; the high-score handler is selected by the already-established `(s0,s2,s4) = (0,1,2)` state and `FF002C == 0`.

## Original Arcade Sequence

The original arcade trace confirms the no-input story-to-high-score transition when the story timer reaches zero.

Event counts:

- `TITLE_TO_STORY_SELECTOR_03AA82`: `1`
- `TITLE_TO_STORY_TIMER_RELOAD_03AA88`: `1`
- `STORY_PRODUCER_03AAAE`: `1`
- `STORY_TIMER_RELOAD_03AAF2`: `1`
- `STORY_INNER_TO_2_03AAF8`: `1`
- `STORY_EXPIRY_HANDLER_03AB00`: `1`
- `HIGH_INIT_CLEAR_CALL_03AB08`: `1`
- `CLEAR_ENTRY_03AE64`: `3`
- `CLEAR_BG_CALL_03AE70`: `3`
- `CLEAR_FG_CALL_03AE80`: `3`
- `HIGH_SCORE_INIT_03AB0C`: `1`
- `HIGH_SCORE_RENDER_03AB12`: `1`
- `HIGH_SCORE_TIMER_RELOAD_03AB22`: `1`
- `HIGH_SCORE_MASTER_ADVANCE_03AB48`: `1`

Key timer-expiry event chain:

```text
EVENT STORY_EXPIRY_HANDLER_03AB00 cyc=51201129 pc=03AB02 sr=2700 a5=0010C000 s0=0000 s2=0001 s4=0002 cnt=0000
EVENT HIGH_INIT_CLEAR_CALL_03AB08 cyc=51201149 pc=03AB0A sr=2700 a5=0010C000 s0=0000 s2=0001 s4=0002 cnt=0000
EVENT CLEAR_ENTRY_03AE64 cyc=51201185 pc=03AE66 sr=2700 a5=0010C000 s0=0000 s2=0001 s4=0002 cnt=0000 a0=0003AA90 d0=00000001 d1=00000046
EVENT CLEAR_BG_CALL_03AE70 cyc=51201209 pc=03AE72 sr=2700 a5=0010C000 a0=00C00100 d0=00000020 d1=0000076C
EVENT CLEAR_FG_CALL_03AE80 cyc=51250665 pc=03AE82 sr=2700 a5=0010C000 a0=00C08100 d0=00000020 d1=0000076C
EVENT HIGH_SCORE_INIT_03AB0C cyc=51301241 pc=03AB0E sr=2704 a5=0010C000 s0=0000 s2=0001 s4=0002 cnt=0000
EVENT HIGH_SCORE_RENDER_03AB12 cyc=51316003 pc=03AB14 sr=2700 a5=0010C000 s0=0000 s2=0001 s4=0002 cnt=0000 d0=0000003C
EVENT HIGH_SCORE_TIMER_RELOAD_03AB22 cyc=51319541 pc=03AB24 sr=2704 a5=0010C000 s0=0000 s2=0001 s4=0002 cnt_before=0000
EVENT HIGH_SCORE_MASTER_ADVANCE_03AB48 cyc=51320553 pc=03AB4A sr=2700 a5=0010C000 s0_before=0000 s2=0001 s4=0002 cnt=00A0
```

Observable facts:

- The original arcade no-input run reaches `arcade_pc 0x03AB00` with `%a5@(0)=0`, `%a5@(2)=1`, `%a5@(4)=2`, and timer `%a5@(44)=0`.
- It then falls through to `0x03AB08`, calls the clear helper, initializes/renders the high-score page, reloads the timer to `0x00A0`, and advances master state at `0x03AB48`.

## Build 0108 Sequence

Build 0108 reaches the same selector state and timer-expiry handler entry, but the original tail is suppressed by the patched site.

Event counts:

- `TITLE_TO_STORY_SELECTOR_03AC82`: `1`
- `TITLE_TO_STORY_TIMER_RELOAD_03AC88`: `1`
- `STORY_PRODUCER_03ACAE`: `1`
- `STORY_TIMER_RELOAD_03ACF2`: `1`
- `STORY_INNER_TO_2_03ACF8`: `1`
- `STORY_EXPIRY_PATCHED_HANDLER_03AD00`: `656`
- `PALETTE_HOOK_0714F4`: `656`
- `PATCHED_SITE_RTS_03AD06`: `656`

Expected-but-not-hit events:

- `SHOULD_BE_HIGH_INIT_CLEAR_CALL_03AD08`: `0`
- `HIGH_SCORE_INIT_03AD0C`: `0`
- `HIGH_SCORE_RENDER_03AD12`: `0`
- `HIGH_SCORE_TIMER_RELOAD_03AD22`: `0`
- `HIGH_SCORE_MASTER_ADVANCE_03AD48`: `0`

Key Build 0108 event chain:

```text
EVENT STORY_EXPIRY_PATCHED_HANDLER_03AD00 cyc=54155942 pc=03AD02 sr=2700 a5=00FF0000 s0=0000 s2=0001 s4=0002 cnt=0000
EVENT PALETTE_HOOK_0714F4 cyc=54155962 pc=0714F6 sr=2700 a5=00FF0000 s0=0000 s2=0001 s4=0002 cnt=0000 palette_dirty=00
EVENT PATCHED_SITE_RTS_03AD06 cyc=54156346 pc=03AD08 sr=2700 a5=00FF0000 s0=0000 s2=0001 s4=0002 cnt=0000 palette_dirty=01
```

The same three-event sequence repeats every VBlank because the timer remains `0`, `%a5@(2)` remains `1`, and `%a5@(4)` remains `2`.

The `PATCHED_SITE_RTS_03AD06` event displays `pc=03AD08` because of debugger post-instruction PC reporting; the explicit breakpoint at `runtime_genesis_pc 0x03AD08` did not fire. Therefore the mapped high-score clear tail at `0x03AD08` was not executed.

## No-Op / Suppression Check

Build 0108 patched site:

- `arcade_pc 0x03AB00..0x03AB08`
- `runtime_genesis_pc 0x03AD00..0x03AD08`
- Original bytes: `33fc03ff00200022`
- Replacement behavior: `jsr genesistan_palette_hook_03ab00; rts`

Original arcade behavior at `0x03AB00`:

- Writes palette/control data, then falls through to `0x03AB08`.
- `0x03AB08` begins the high-score clear/init/render/timer-reload/master-advance tail.

Build 0108 behavior at `0x03AD00`:

- Calls `genesistan_palette_hook_03ab00` at `runtime_genesis_pc 0x0714F4`.
- Sets `palette_dirty`.
- Returns via RTS at `0x03AD06` before executing the mapped tail at `0x03AD08`.

Does the replacement block high-score page progression? **YES.** It preserves the palette side effect but suppresses the original fall-through tail that clears, initializes, renders, reloads the timer, and advances state.

## Classification

### **B - ENTERED BUT INIT SUPPRESSED**

Build 0108 reaches the same no-input story-expiry selector state as original arcade: `%a5@(0)=0`, `%a5@(2)=1`, `%a5@(4)=2`, and `FF002C == 0`. The story-expiry handler entry at `runtime_genesis_pc 0x03AD00` fires repeatedly, and the palette hook runs repeatedly.

However, the opcode replacement for arcade `0x03AB00..0x03AB08` returns immediately after the palette hook, so Build 0108 never executes the mapped high-score clear/init/render/timer-reload/master-advance tail at `runtime_genesis_pc 0x03AD08+`. This matches Tighe's observation: story timer expiry causes a palette-visible change, but the story is not cleared, high score is not rendered, and the timer remains zero.

This is not A (state never entered), because `0x03AD00` is reached repeatedly in the correct selector state. It is not C (different selector), because the arcade and Build 0108 selector state at expiry match. It is not D, because the suppressing site is pinned.

## OPEN / KNOWN_FINDINGS Impact

- Open issues touched: OPEN-001 context, OPEN-018 / Class B context, OPEN-015 not touched.
- Issues opened: NONE.
- Issues closed: NONE.
- `KNOWN_FINDINGS.md` impact: no update in this evidence-only task. A follow-up canonicalization may be appropriate if the team wants this Build 0108 suppression mechanism recorded before implementation.

## STOP

STOP triggered: **NO**.

No source, spec, tool, Makefile, ROM, build artifact, bookmark artifact, or runtime diagnostic ROM was modified.
