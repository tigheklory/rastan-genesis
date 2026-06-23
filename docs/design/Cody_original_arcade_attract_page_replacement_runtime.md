# Cody - Original Arcade Attract Page Replacement Runtime Verification

**Date:** 2026-06-23  
**Type:** Original arcade runtime verification / evidence capture only  
**Target:** Original MAME `rastan` arcade ROM, not Genesis Build 0094  
**MAME romset/driver:** `rastan` - `Rastan (World Rev 1)`  
**ROM verification:** `mame -rompath roms -verifyroms rastan` reported `romset rastan is good`  
**Scope:** Observation only. No source/spec/tool/Makefile/ROM/build/invariant changes. No Genesis implementation. No bookmark cycle. No post-Start exception analysis.

## Phase 0

Classification: **EXTENDING** (OPEN-001). Required architecture/rule files were loaded: `RULES.md` and `ARCHITECTURE.md`. `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Cody_build_0094_fg_clear_boundary_pin.md`, and `docs/design/Andy_build_0094_fg_text_lifecycle_static_map.md` were read before runtime work.

Relevant priors: KF-010, KF-011, KF-013, KF-028, KF-029, KF-030, KF-031. OPEN-001 is active, OPEN-016 is context, and OPEN-015 remains do-not-touch.

Architecture compliance: **CONFIRMED**. This task ran the original arcade ROM only. The Genesis Build 0094 evidence was used only as prior context to identify which boundary needed arcade verification.

## Address Correlation Gate

Authoritative map used: `build/rastan-direct/address_map.json`.

The Genesis-to-arcade reverse mapping succeeded exactly for both required runtime PCs. No `-0x200` arithmetic was used as the authority; the mapping below comes from the JSON segment containment.

| Genesis runtime PC | JSON segment index | Segment kind | JSON segment | Mapped arcade PC |
|---|---:|---|---|---|
| `0x0003AC82` | `27` | `arcade_copy` | `genesis_start=0x03AB20`, `genesis_end_exclusive=0x03AD00`, `arcade_start=0x03A920`, `arcade_end_exclusive=0x03AB00`, `identity_offset=512` | `0x0003AA82` |
| `0x0003ACAE` | `27` | `arcade_copy` | `genesis_start=0x03AB20`, `genesis_end_exclusive=0x03AD00`, `arcade_start=0x03A920`, `arcade_end_exclusive=0x03AB00`, `identity_offset=512` | `0x0003AAAE` |

Candidate clear/fill confirmation against the JSON map:

| Arcade PC | JSON segment index | Segment kind | JSON segment | Genesis mapping |
|---|---:|---|---|---|
| `0x000561B6` | `162` | `patched_site` | `arcade_start=0x0561B6`, `arcade_end_exclusive=0x0561D4`, `genesis_start=0x0563B6`, `genesis_end_exclusive=0x0563D4`, `origin=opcode_replace`, note: replace PC080SN C-window fill loop with `JSR` to Genesis staged-buffer clear hook | `0x000563B6` patched site calling helper `0x000710D8` |

Address mapping gate result: **PASS**.

## Evidence Artifacts

Trace directory: `states/traces/original_arcade_attract_page_replacement_20260623_171701/`

Primary files:
- `mame_original_arcade_attract_page_replacement.cmd`
- `native_debug_trace.log.gz`
- `native_events.log`
- `original_arcade_attract_page_replacement_analysis.json`
- `original_arcade_attract_page_replacement_analysis.md`
- `fg_before_page_start_03aa82.bin`
- `fg_after_page_start_03aa88.bin`
- `fg_before_producer_03aaae.bin`
- `fg_after_producer_03aaf8.bin`
- `fg_after_producer_post_state4_03aafe.bin`
- matching `bg_*` dumps for the same points

Debugger method: MAME native debugger with `QT_QPA_PLATFORM=offscreen`, `-debug -debugger qt -debugscript`, original `rastan` driver, `-rompath roms`. Breakpoints and watchpoints were set for mapped `0x03AA82`, mapped `0x03AAAE`, candidate `0x0561B6`, PC080SN FG `0xC08000..0xC0BFFF`, PC080SN BG `0xC00000..0xC03FFF`, and PC080SN scroll registers `0xC20000/0xC40000` as page-switch corroboration.

## Runtime Event Summary

Event counts:
- `PAGE_START_WRITE_03AA82`: `1`
- `AFTER_PAGE_START_03AA88`: `1`
- `PRODUCER_03AAAE_BEFORE`: `1`
- `PRODUCER_FIRST_RENDER_03AAB6`: `1`
- `PRODUCER_AFTER_BEFORE_STATE4_03AAF8`: `1`
- `AFTER_STATE4_WRITE_03AAFE`: `1`
- `CLEAR_0561B6_ENTRY`: `0`
- `BG_PC080SN_WRITE`: `17,248`
- `FG_PC080SN_WRITE`: `16,324`
- `PC080SN_YSCROLL_WRITE`: `6`
- `PC080SN_XSCROLL_WRITE`: `6`

Key mapped-boundary events:

```text
EVENT PAGE_START_WRITE_03AA82 cyc=1802879 pc=03AA84 sr=2704 a5=0010C000 s0=0000 s2_before=0000 s4=0000 cnt=0000
EVENT AFTER_PAGE_START_03AA88 cyc=1802895 pc=03AA8A sr=2700 a5=0010C000 s0=0000 s2=0001 s4=0000 cnt_before=0000
EVENT PRODUCER_03AAAE_BEFORE cyc=29734451 pc=03AAB0 sr=2704 a5=0010C000 s0=0000 s2=0001 s4=0001 cnt=0000 d0=00000000 d1=00000030 sp=0010DDF6
EVENT PRODUCER_FIRST_RENDER_03AAB6 cyc=29745171 pc=03AAB8 sr=2700 a5=0010C000 s0=0000 s2=0001 s4=0001 cnt=0000 d0=00000011 d1=00000000 sp=0010DDF6
EVENT PRODUCER_AFTER_BEFORE_STATE4_03AAF8 cyc=29753805 pc=03AAFA sr=2700 a5=0010C000 s0=0000 s2=0001 s4_before=0001 cnt=00A0 sp=0010DDF6
EVENT AFTER_STATE4_WRITE_03AAFE cyc=29753821 pc=03AB00 sr=2700 a5=0010C000 s0=0000 s2=0001 s4=0002 cnt=00A0 sp=0010DDF6
```

Note: MAME's logged `pc` for these breakpoints is the post/prefetch-reported PC. The exact instruction PCs are the breakpoint sites named in the event labels and verified against `build/maincpu.disasm.txt`.

## Did `0x0561B6` Fire?

**No.** `arcade_pc 0x0561B6` did not execute during the captured original-arcade attract transition.

- `CLEAR_0561B6_ENTRY`: `0`
- `CLEAR_0561B6_DONE`: `0`
- Caller PCs into `0x0561B6`: none observed because the routine did not fire.

This disproves the specific hypothesis that the mapped `0x03AA82 -> 0x03AAAE` attract replacement boundary uses the game-scene C-window fill routine at `0x0561B6`.

## What Cleared the Arcade Page Instead

The original arcade did clear PC080SN tilemap content, but through a different routine path: `0x03AE64` / `0x03AE74` calling the generic fill loop at `0x03AD44`.

Relevant static code in `build/maincpu.disasm.txt`:

```asm
3ae64:  lea    0xc00100,%a0
3ae6a:  movew  #1900,%d1
3ae6e:  moveq  #32,%d0
3ae70:  bsrw   0x3ad44       ; BG partial C-window blank fill
3ae74:  lea    0xc08100,%a0
3ae7a:  movew  #1900,%d1
3ae7e:  moveq  #32,%d0
3ae80:  bsrw   0x3ad44       ; FG partial C-window blank fill

3ad44:  movel  %d0,%a0@+
3ad46:  subqw  #1,%d1
3ad48:  bnes   0x3ad44
3ad4a:  rts
```

Runtime watchpoints confirm this fill path executes between the page-start state write and the mapped producer.

Window from mapped page-start `0x03AA82` to producer entry `0x03AAAE`:
- FG writes: `3,823`
- FG dominant writer: `0x03AD48` with `3,800` writes
- FG write range: `0x00C08100..0x00C09EAE`
- FG dominant values: `0x0000` and `0x0020` alternating as longword `0x00000020`
- BG writes: `3,800`
- BG dominant writer: `0x03AD48` with `3,800` writes
- BG write range: `0x00C00100..0x00C01EAE`
- BG dominant values: `0x0000` and `0x0020` alternating as longword `0x00000020`

The `0x03AD48` PC is the fill-loop branch/check PC reported by the watchpoint immediately after each `movel %d0,%a0@+` iteration at `0x03AD44`.

## Snapshot Comparison

Blank/default cell is treated as `(attr=0x0000, tile=0x0020)`, matching the arcade fill longword `0x00000020`.

| Snapshot | FG nonblank cells | BG nonblank cells |
|---|---:|---:|
| before page start `0x03AA82` | `69` | `560` |
| after page start `0x03AA88` | `69` | `560` |
| before producer `0x03AAAE` | `7` | `0` |
| after producer `0x03AAF8` | `145` | `168` |
| after state4 write `0x03AAFE` | `145` | `168` |

Comparisons:
- FG before `0x03AA82` -> after `0x03AA88`: changed `0`, cleared `0`, added `0`.
- FG after `0x03AA88` -> before `0x03AAAE`: changed `62`, cleared-to-blank `62`, added `0`.
- FG before `0x03AAAE` -> after `0x03AAF8`: changed `138`, cleared `0`, added-from-blank `138`.
- BG after `0x03AA88` -> before `0x03AAAE`: changed `560`, cleared-to-blank `560`, added `0`.
- BG before `0x03AAAE` -> after `0x03AAF8`: changed `168`, cleared `0`, added-from-blank `168`.

Interpretation from runtime evidence: the state write at `0x03AA82` itself does not clear tilemap contents, but the subsequent setup phase before producer `0x03AAAE` clears the active PC080SN FG and BG page areas. The producer then writes new FG text and BG content into an already cleared page.

## Page-Switch / Scroll Check

Scroll writes were observed, but only as zero writes:
- `PC080SN_YSCROLL_WRITE`: `6` total, `2` in the page-to-producer window, data `0x0000`.
- `PC080SN_XSCROLL_WRITE`: `6` total, `2` in the page-to-producer window, data `0x0000`.

No evidence in this trace supports a page/bank/window/scroll switch as the replacement mechanism for this boundary. The replacement mechanism is direct PC080SN blank-fill followed by redraw.

## Replacement Classification

**Mechanism classification:** `CLEAR`.

**Layer scope:** both FG and BG for the captured transition.

Proven arcade runtime facts:
- The original arcade reaches mapped page-start `arcade_pc 0x03AA82` and mapped producer `arcade_pc 0x03AAAE` in the no-input attract path.
- `arcade_pc 0x0561B6` does not execute during this transition.
- Between `0x03AA82` and `0x03AAAE`, the arcade clears both active PC080SN page regions using `0x03AE64/0x03AE74 -> 0x03AD44`:
  - FG `0x00C08100..0x00C09EAE`
  - BG `0x00C00100..0x00C01EAE`
- The producer then redraws new FG/BG content into the cleared page.

Rejected for this boundary:
- `OVERWRITE` without clear: rejected; a broad blank-fill occurs before producer redraw.
- `PAGE-SWITCH`: rejected for this trace; scroll/page corroboration shows only zero writes.
- `RETAIN`: rejected; old FG/BG cells are cleared before producer.
- `UNKNOWN`: rejected for this captured boundary; the observed behavior is sufficiently classified.

## Recommended Faithful Genesis Translation Action

Recommendation only, no implementation performed:

The Genesis translation should reproduce the arcade's attract setup clear for the corresponding `0x03AA82 -> 0x03AAAE` boundary. Because the original arcade clears both PC080SN page regions before the producer draws, the faithful Genesis behavior is a production staging clear of the corresponding active FG and BG staging regions before the mapped producer page draws.

Important nuance: the clear should not be justified as the `0x0561B6` game-scene clear. For this attract boundary, the proven arcade source mechanism is the `0x03AE64/0x03AE74 -> 0x03AD44` partial C-window clear path. A Genesis implementation should therefore translate that arcade clear intent at the matching attract setup path, rather than blindly reusing the `0x0561B6` lifecycle assumption.

Practical follow-up recommendation:
- Inspect the Genesis translation coverage for the arcade `0x03AE64/0x03AE74 -> 0x03AD44` clear path.
- If missing or not mapped to staging, add a production translation for that arcade clear intent so it clears the active staged FG/BG regions and marks the affected rows dirty before the `0x03AAAE` producer draws.
- Do not implement a producer-local `0x03AAAE` workaround as the primary fix; the arcade clear occurs before the producer, in the setup phase.

## Confidence and Remaining Unknowns

Confidence: **HIGH** for this captured no-input original-arcade attract boundary.

Remaining unknowns:
- This proves the `0x03AA82 -> 0x03AAAE` boundary only. Other attract/page transitions may use the same clear path, another clear path, or different behavior and should be proven before broadening a global policy.
- The trace classifies the clear as both FG and BG for the captured boundary. A Genesis implementation may still need careful row/range translation so it does not over-clear unrelated staged content.
- This task did not analyze the Genesis post-Start exception, OPEN-015 crash fields, sprites, palette, logo/sword art, or real-hardware behavior.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active; arcade intent for one attract replacement boundary is now proven), OPEN-016 (context), OPEN-015 (do-not-touch context).
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: Genesis implementation, other attract boundaries, game-start redraw, Start/C/A exception, OPEN-015 crash-handler defects, sprites/palette/logo/sword/real-hardware work.

## KNOWN_FINDINGS Impact

Option C candidate only. This original-arcade runtime trace establishes a durable behavior candidate: the arcade clears both PC080SN FG/BG active page regions via `0x03AE64/0x03AE74 -> 0x03AD44` before the `0x03AAAE` producer, while `0x0561B6` does not fire for this boundary. `KNOWN_FINDINGS.md` was not edited in this task.

## STOP

STOP triggered: **NO**. Address mapping succeeded exactly, the original arcade ROM ran under MAME, the mapped boundary was captured, `0x0561B6` was disproven for this transition, and the replacement mechanism was classified as CLEAR.
