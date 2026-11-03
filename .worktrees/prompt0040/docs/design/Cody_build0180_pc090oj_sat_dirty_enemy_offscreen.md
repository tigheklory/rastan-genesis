# Cody - Build 0180 PC090OJ SAT Dirty / Enemy Offscreen Boundary

**Date:** 2026-07-16
**Type:** Analysis-first bounded implementation + runtime validation
**Build context:** Build 0178 / accidental duplicate Build 0179 -> Build 0180, `rastan-direct`
**Baseline ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0178.bin`
**Baseline SHA256:** `998cc3c92b710d79eeaea08e49ea288f4757d03662692797361142bf186cdd96`
**Accidental duplicate baseline:** Build 0179, byte-identical to Build 0178, no semantic change
**Candidate ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0180.bin`
**Candidate SHA256:** `d016cacd6b318c949875bccb992ecff7633def06fc8e57f62c89600967b054bf`
**Scope:** PC090OJ residual SAT dirty / tile-DMA / enemy-offscreen boundary only. No input/control, collision, sky reset, D00298, continue/game-over, Exodus loop, FG palette, or PC080SN work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-047 (PC090OJ pre-SAT budget and resident-code cancellation), KF-046/KF-045 (palette route/FG carrier; not reopened), KF-038 (tall PC080SN BG/FG representation), KF-032 (raw PC080SN/PC090OJ writes route through staging), KF-011 (arcade VBlank owns progression), KF-010 (staging -> VBlank commit). Open issues touched: OPEN-017 and OPEN-024; OPEN-001 context only. No contradiction of CONFIRMED/STRONG findings detected.

Build 0178/0179 status recorded: Build 0178 removed the stale Build 0163 gameplay-only forced tile-DMA requeue and restored `sprite_tile_resident_code[slot] == requested_code` cancellation. Build 0179 was an accidental duplicate produced during documentation and is byte-identical to Build 0178. Accepted build remains unchanged unless Tighe accepts a candidate.

User observations recorded as runtime context only: Build 0178/0179 remains not fully playable; speed may be slightly improved but slowdown remains; Rastan is still not controllable; no enemies appear or interact; FG colours remain good; do not reopen FG palette; do not undo Build 0178.

## Evidence Artifacts

Trace root: `states/traces/build0180_pc090oj_sat_dirty_enemy_20260716_115243/`

- Build 0178 stable event source: `states/traces/build0178_residual_efficiency_20260716_073844/build0178/events.csv`
- Build 0178 frame/worklist samples: `states/traces/build0180_pc090oj_sat_dirty_enemy_20260716_115243/genesis_frame/`
- Build 0180 frame/worklist samples: `states/traces/build0180_pc090oj_sat_dirty_enemy_20260716_115243/build0180_frame/`
- Build 0180 VDP service samples: `states/traces/build0180_pc090oj_sat_dirty_enemy_20260716_115243/build0180_vdp/`
- Arcade matched-state attempt: `states/traces/build0180_pc090oj_sat_dirty_enemy_20260716_115243/arcade/`
- Reduced comparison: `states/traces/build0180_pc090oj_sat_dirty_enemy_20260716_115243/build0178_vs_build0180_reduced.md`

One initial all-in-one Lua trace crashed MAME before writing useful output. A smaller stable trace path was used instead: existing Build 0178 PC/service event evidence, a frame-based worklist/enemy sampler, and a VDP-control write sampler for Build 0180. This is a harness limitation, not game evidence.

## Build 0178 Boundary Evidence

Build 0178 runtime facts preserved:

- DISPLAY_OFF services over the gameplay window: `503`
- `pc090oj_sat_dirty` at DISPLAY_OFF: `1` on `503/503` serviced frames
- Tile-DMA at DISPLAY_OFF: `6` on `502/503` frames, `14` once
- Changed mirror tuples at DISPLAY_OFF: `0` on `503/503` frames
- Frame-sampled SAT dirty: `1` on `94/96` samples
- Frame-sampled full SAT hash changes: `1`
- Frame-sampled active-SAT hash changes: `2`

Interpretation: SAT dirty was asserted almost continuously even though the staged SAT contents were stable across the sampled gameplay window. The residual tile-DMA entries were mostly real animation-code changes, not resident-cache misses.

## Tile-DMA Worklist Classification

Frame-sampled Build 0178 worklist rows:

- Worklist rows: `442`
- `requested_code == resident_before`: `8`
- `requested_code != resident_before`: `434`
- Record tuple changed: `392`

The dominant codes cycle among `0x09D9`, `0x09DA`, and `0x09DB` for records such as `132`, `133`, `134`, `12`, `13`, and `14`. These are not mostly duplicate requests for already-resident tile codes after Build 0178. They are primarily animation/frame changes requiring sprite tile pattern residency updates.

Question 2 classification: **A - legitimate animation/frame changes**. There are a few already-resident samples, but they are not the dominant remaining cost and do not justify another broad tile-DMA cache change.

## SAT Dirty Classification

Source inspection showed `.Lpc090oj_field_update_record` calls `.Lpc090oj_place_record_in_slot` for already represented records. Before Build 0180, `.Lpc090oj_place_record_in_slot` rewrote the slot's four staged SAT words and unconditionally executed:

```asm
move.w  #1, pc090oj_sat_dirty
```

But for animation-only code changes, the Genesis SAT entry can remain byte-identical because the SAT tile index is slot-derived (`SPRITE_TILE_BASE + slot*4`), while the changing arcade sprite code is loaded into that slot's VRAM pattern via tile-DMA. Therefore animation can legitimately require tile-DMA without requiring SAT DMA.

Question 1 classification: **D - represented records are being re-synced every service and marking SAT dirty even when equivalent**.

A broader wording, **B - dirty flag asserted too broadly**, is also consistent, but D is the more exact mechanism for this trace.

## Build 0180 Fix

Implemented a bounded production change in `apps/rastan-direct/src/pc090oj_hooks.s` inside `.Lpc090oj_place_record_in_slot`:

- Clear local `.Lscratch_sat_changed` at the start of placement.
- Compare each staged SAT word (`Y`, `size|link`, `attr|tile`, `X`) against the current staged value before storing.
- Set `.Lscratch_sat_changed` only if a word differs.
- Assert `pc090oj_sat_dirty` only if `.Lscratch_sat_changed != 0`.
- Preserve descriptor-table updates, record ownership, represented/used bit updates, and tile-DMA worklist queue/cancel behavior.

No SAT DMA is skipped blindly. The existing VBlank commit still performs SAT DMA whenever `pc090oj_sat_dirty` is set by a real staged-SAT word change.

## Build Verification

First release attempt stopped at the canonical gate before numbered artifact production:

```text
expected total_genesis_bytes_covered=0x18268C and opcode_replace patched_site count=151;
got total_genesis_bytes_covered=0x1826D0 opcode_replace patched_site count=151
```

The paired canonical invariants were updated to the observed mechanical value:

- `opcode_replace` patched-site count: `151` unchanged
- `total_genesis_bytes_covered`: `0x18268C -> 0x1826D0`
- Mechanical delta: `+0x44`

Second release invocation passed:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0180.bin`
- SHA256: `d016cacd6b318c949875bccb992ecff7633def06fc8e57f62c89600967b054bf`
- Size: `1,582,800`
- Counter: `180`
- Boot guard: PASS
- Canonical gate: `GATE_PASS`
- Rolling ROM SHA matches Build 0180
- Release trace: `states/traces/rastan_direct_video_test_build_0180_mame_30s_20260716_115841/`

A comment-only wording correction in `pc090oj_hooks.s` was made after the numbered build to align the function comment with the new gated behavior. It does not affect emitted code, but a future rebuild will naturally include the comment-only source state.

## Runtime Validation

Comparison over the same scripted gameplay window:

| Metric | Build 0178 | Build 0180 |
|---|---:|---:|
| DISPLAY_OFF events | `503` | `523` |
| SAT dirty at DISPLAY_OFF | `503/503` | `1/523` |
| Tile-DMA at DISPLAY_OFF | `6` on `502` frames, `14` once | `4` on `522` frames, `12` once |
| Changed tuples at DISPLAY_OFF | `0/503` nonzero | `0/523` nonzero |
| Frame-sampled SAT dirty | `94/96` | `0/96` |
| Frame-sampled SAT hash changes | `1` | `1` |
| Frame-sampled active-SAT hash changes | `2` | `1` |
| Worklist sampled rows | `442` | `266` |
| Worklist requested==resident | `8` | `2` |

Build 0180 materially reduces unnecessary SAT dirty/SAT DMA. It also reduces sampled tile worklist rows because fewer SAT-field resync side effects cascade through the same sampled windows, but remaining tile-DMA work still exists and is mostly legitimate animation code residency.

Primary timing classification: **A - SAT dirty / SAT DMA** for the Build 0178 -> Build 0180 boundary.

Post-Build 0180 remaining timing classification: not closed. Tile-DMA remains (`4` on most DISPLAY_OFF samples), and broader gameplay/control issues remain outside this task.

## Enemy Offscreen Trace

Genesis Build 0178/0179 sampled enemy-code records:

- Records: `30..43`
- Codes: `0x03E8..0x03F5`
- Raw Y: `0x00E8`
- Decoded signed Y before viewport offset: `232`
- Final Genesis screen Y after `PC090OJ_TO_GENESIS_Y_OFFSET=-8`: `224`
- Current culling reason: `offscreen_y`
- `represented=0`, `waiting=0`, `slot=255`, `tile_resident=FFFF`

Question 3 classification: **H - more evidence needed**.

The Genesis-side rejection boundary is proven: the current decode/opaque-clip path rejects these records at the bottom edge (`screen_y=224`). The arcade comparison attempt reached the same state/player/camera window (`2/3/0`, player `0x0020/0x0070`, camera Y `0x0149`) but produced zero `0x03E8..0x03F5` records in the sampled original PC090OJ hardware RAM. Therefore there is no exact matched arcade equivalent for these specific records in this pass. Do not fix enemy culling or force enemy visibility from this evidence.

## Non-Actions

No input/control, collision, sky reset, D00298, continue/game-over, Exodus loop, FG palette, BG/FG projection, PC080SN, or enemy-spawn logic was changed. Build 0178 resident-cache restoration was preserved. Build 0177 per-record dirty work was preserved. Build 0175 palette route was preserved. Build 0172/0171 FG/BG tall projection was preserved.

Visual validation was not performed in this headless trace beyond MAME running the release trace. Tighe must verify: Rastan visible, FG palette, BG/sky/mountains, foreground, title/story/READY, speed/black bars, and enemies if naturally represented.

## OPEN / KNOWN_FINDINGS Impact

Open issues touched: OPEN-017 and OPEN-024; OPEN-001 context only. No new issue opened. No issue closed.

KNOWN_FINDINGS impact: **Option C - update KF-047**. Build 0180 refines the PC090OJ budget finding: after candidate reduction and resident-code restoration, SAT dirty must also be gated by actual staged-SAT byte changes because animation-only tile-code changes require tile-DMA but not SAT DMA.

## STOP

STOP triggered: **NO** for the bounded Build 0180 candidate. Arcade enemy comparison remains insufficient for an enemy fix, but that is a deferred evidence gap, not a STOP for the SAT dirty boundary.
