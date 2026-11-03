# Cody - Build 0133 HV/VCounter Display-On Timing Diagnostic

**Date:** 2026-07-02  
**Type:** Temporary diagnostic build + runtime evidence + mandatory byte-identical revert  
**Baseline build:** Build 0132, `dist/rastan-direct/rastan_direct_video_test_build_0132.bin`  
**Baseline SHA256:** `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`  
**Diagnostic build:** Build 0133, `dist/rastan-direct/rastan_direct_video_test_build_0133.bin`  
**Diagnostic SHA256:** `e069a96aa1317154d8829e13a275e19133bdc91281aab43880fe5e71fd57b30f`  
**Revert build:** Build 0134, `dist/rastan-direct/rastan_direct_video_test_build_0134.bin`  
**Revert SHA256:** `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`

## Phase 0

Classification: **EXTENDING** (OPEN-001 timing/display evidence; OPEN-024 residency-cache context). Read and applied: `RULES.md`, `ARCHITECTURE.md`, `AGENTS.md`, latest `AGENTS_LOG.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, `docs/design/Andy_build0132_residency_cache_static_review.md`, and `docs/design/Cody_pc090oj_persistent_sprite_tile_dma_cache_build0132.md`.

Architecture compliance: **YES**. The diagnostic sampled VDP status/HV timing from the Genesis VBlank service only. No PC090OJ logic, PC080SN logic, scene loading, residency cache behavior, or gameplay state was changed. The diagnostic was removed before the canonical revert build.

## Temporary Diagnostic Instrumentation

Added only to `apps/rastan-direct/src/vdp_comm.s` for Build 0133, then removed:

- A 512-entry WRAM ring at temporary Build 0133 symbols `vblank_diag_*`.
- HV counter read from `HW_ADDRESS 0x00C00008`.
- VDP status read from `HW_ADDRESS 0x00C00004`.
- Checkpoints `0x01..0x0C` around `_vblank_service`:
  - `0x01` entry after save
  - `0x02` after input update
  - `0x03` after DISPLAY_OFF
  - `0x04` after tile commit
  - `0x05` after BG commit
  - `0x06` after FG commit
  - `0x07` before sprite commit
  - `0x08` after sprite commit
  - `0x09` after palette commit/skip
  - `0x0A` after scroll commit
  - `0x0B` after DISPLAY_ON
  - `0x0C` before arcade VBlank handoff

Each ring entry recorded: frame counter, checkpoint, VDP status, VBlank bit mask, raw HV word, VCounter, HCounter, diagnostic display shadow, `pc090oj_drawable_count`, `pc090oj_emitted_count`, `staged_sprite_active_count`, `%a5@(0)/(2)/(4)` state words, and dirty-row low words.

Temporary invariant for Build 0133 only:

- `opcode_replace` count: `133` unchanged
- `total_genesis_bytes_covered`: `0x17D4A4 -> 0x17D58C`

## Evidence Artifacts

Trace root:

`states/traces/build0133_hv_vcounter_display_on_diagnostic_20260702_215520/`

Key files:

- `capture_build0133_hv_vcounter.lua`
- `reduce_build0133_hv_vcounter.py`
- `build0133_symbol.txt`
- `build0133_genesis_postpatch.disasm.txt`
- `build0133_rastan_direct_patch_manifest.json`
- `build0133_sha256.txt`
- `build0133_size.txt`
- `no_input/build0133_hv_vcounter_analysis.md`
- `no_input/build0133_hv_vcounter_analysis.json`
- `no_input/no_input_contact_sheet.png`
- `coin_start/build0133_hv_vcounter_analysis.md`
- `coin_start/build0133_hv_vcounter_analysis.json`
- `coin_start/coin_start_contact_sheet.png`

Runtime cases captured:

- No-input title/story window: frames `60`, `120`, `180`, `240`, `282`, `283`, `289`, `369`.
- Coin/start path: frames `340`, `371`, `411`, `473`, `474`, `477`, `534`, `560`, `620`.

MAME completed both runs. Reading `HW_ADDRESS 0x00C00008` did **not** fault in MAME for Build 0133.

## Observed Timing

VDP status bit 3 is treated as the VBlank indicator. VCounter is the high byte of the sampled `HW_ADDRESS 0x00C00008` word.

### No-Input Run

| Frame | Label | After Scroll Bit3 | After DISPLAY_ON Bit3 | After DISPLAY_ON VCounter | Notes |
|---:|---|---:|---:|---:|---|
| 60 | early_no_input | `1` | `0` | `0x18` | DISPLAY_ON after VBlank bit cleared |
| 120 | mid_no_input | `1` | `0` | `0xD9` | DISPLAY_ON after VBlank bit cleared |
| 180 | late_no_input | `1` | `0` | `0xD9` | DISPLAY_ON after VBlank bit cleared |
| 240 | pre_story_window | `1` | `0` | `0xD9` | DISPLAY_ON after VBlank bit cleared |
| 282 | story_black_cover_anchor | `1` | `0` | `0x17` | DISPLAY_ON after VBlank bit cleared |
| 283 | post_anchor | `1` | `0` | `0x15` | DISPLAY_ON after VBlank bit cleared |
| 289 | post_anchor_late | `1` | `0` | `0x08` | DISPLAY_ON after VBlank bit cleared |
| 369 | late_no_input | `1` | `0` | `0xD9` | DISPLAY_ON after VBlank bit cleared |

Aggregate: `8/8` captures had checkpoint `0x0A` after-scroll inside VBlank, but checkpoint `0x0B` after-DISPLAY_ON after the VBlank bit had cleared.

### Coin/Start Run

| Frame | Label | After Scroll Bit3 | After DISPLAY_ON Bit3 | After DISPLAY_ON VCounter | Notes |
|---:|---|---:|---:|---:|---|
| 340 | pre_coin | `1` | `0` | `0xD9` | late DISPLAY_ON |
| 371 | coin_accept_window | `1` | `0` | `0xD9` | late DISPLAY_ON |
| 411 | prompt_window | `1` | `0` | `0xCE` | late DISPLAY_ON |
| 473 | start_clear_window | `1` | `0` | `0x6C` | late DISPLAY_ON |
| 474 | stale_redraw_window | `1` | `1` | `0xF7` | same diagnostic frame as 473; capture landed while VBlank bit was set |
| 477 | second_clear_window | `1` | `1` | `0xF7` | same diagnostic frame as 473/474; duplicate ring state |
| 534 | round_window | `1` | `0` | `0x92` | late DISPLAY_ON |
| 560 | post_round_window | `1` | `0` | `0x5D` | late DISPLAY_ON |
| 620 | late_coin_run | `1` | `0` | `0x8F` | late DISPLAY_ON |

Aggregate: `7/9` captures had DISPLAY_ON after the VBlank bit cleared. The two inside-VBlank captures were duplicate reads of the same diagnostic frame (`diag_frame=0x018F`) around the start-clear/stale-redraw interval; they are retained as observations, not treated as independent steady-state timing proof.

## Interpretation

**Observed fact:** The commit body consistently runs while the VBlank status bit is set at checkpoint `0x0A` after scroll commit.

**Observed fact:** DISPLAY_ON at checkpoint `0x0B` usually occurs after the VBlank bit has already cleared. Across both runs, this occurred in `15/17` captured visual anchors.

**Observed fact:** The VCounter value at DISPLAY_ON is not fixed. Examples include `0x08`, `0x15`, `0x17`, `0x18`, `0x5D`, `0x6C`, `0x8F`, `0x92`, `0xCE`, and `0xD9`.

**Interpretation:** The remaining visible horizontal slit / partial reveal behavior is strongly consistent with late and variable DISPLAY_ON timing, not with the Build 0132 residency-cache implementation being wrong. This supports Andy's Branch A direction: the sprite residency cache appears to be functioning, while display re-enable timing remains the live graphics-output problem.

**Non-claim:** This diagnostic does not implement or validate a timing fix. It does not prove the exact visual scanline convention for every emulator/backend. It records MAME Genesis-driver VDP status/HV observations from the temporary Build 0133 ring.

## Build/Revert Proof

Build 0133 diagnostic output:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0133.bin`
- SHA256: `e069a96aa1317154d8829e13a275e19133bdc91281aab43880fe5e71fd57b30f`
- Size: `1561996` bytes
- MAME release trace completed.

Build 0134 revert output:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0134.bin`
- SHA256: `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`
- Size: `1561764` bytes
- `cmp -s dist/rastan-direct/rastan_direct_video_test_build_0132.bin dist/rastan-direct/rastan_direct_video_test_build_0134.bin`: `0`
- `cmp -s dist/rastan-direct/rastan_direct_video_test_build_0134.bin apps/rastan-direct/dist/rastan_direct_video_test.bin`: `0`

Revert checks:

- `TEMP DIAGNOSTIC ONLY` markers in source/tools/symbols: none
- `vblank_diag` symbols in final `apps/rastan-direct/out/symbol.txt`: none
- Temporary invariant `0x17D58C`: removed
- Canonical invariant restored: `opcode_replace=133`, `total_genesis_bytes_covered=0x17D4A4`

## Scope / Non-Actions

- No timing fix implemented.
- No PC090OJ logic changed permanently.
- No PC080SN logic changed permanently.
- No `scene_load.s` change.
- No `tilemap_hooks.s` change.
- No residency-cache behavior change.
- No permanent diagnostic code/data/symbols left behind.
- No bookmarks.

## Open / Closed Issues Impact

- OPEN-001: touched. Evidence supports keeping graphics-output focus on VBlank/display-on timing.
- OPEN-024: touched as context. Build 0132 cache remains supported by this diagnostic; no cache defect found here.
- OPEN-015: not touched.
- New issues opened: none.
- Issues closed: none.

## KNOWN_FINDINGS Impact

Option A: no immediate `KNOWN_FINDINGS.md` update. This is strong runtime evidence for late DISPLAY_ON timing, but it was gathered via a temporary diagnostic build and should be promoted only if Claude/Tighe want this timing mechanism canonicalized after review.

## STOP

STOP triggered: **NO**.
