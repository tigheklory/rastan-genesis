# Cody - Build 0129 TEMP VBlank Status-Ring Diagnostic

**Date:** 2026-07-02  
**Type:** Temporary diagnostic build + runtime evidence + mandatory revert verification  
**Baseline:** Build 0128, `dist/rastan-direct/rastan_direct_video_test_build_0128.bin`  
**Baseline SHA256:** `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`  
**Baseline size:** `1,561,724` bytes  
**Diagnostic Build:** Build 0129, `dist/rastan-direct/rastan_direct_video_test_build_0129.bin`  
**Diagnostic SHA256:** `156b59a88267ca88b39d4e4683342efe9dc707560daab95ce0fcd28d48e5e0f8`  
**Diagnostic size:** `1,561,956` bytes  
**Revert Build:** Build 0130, `dist/rastan-direct/rastan_direct_video_test_build_0130.bin`  
**Revert SHA256:** `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`  
**Revert size:** `1,561,724` bytes  
**Evidence directory:** `states/traces/build0129_vblank_status_ring_diagnostic_20260702_155842/`

## Phase 0

Relevant priors loaded: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Cody_pc090oj_3b930_3b802_object_ram_faithful_implementation.md`, `docs/design/Cody_genesis_sat_link_chain_termination_audit.md`, `docs/design/Cody_temp_sprite_sat_suppression_black_cover_test.md`, `docs/design/Cody_pc090oj_blank_bitset_unmapped_guard_implementation.md`, and `docs/design/Cody_pc090oj_object_ram_phase1_implementation.md`.

Classification: **EXTENDING OPEN-001 / OPEN-024 with user-authorized temporary diagnostic instrumentation**. This was not a production fix and not canonical behavior.

Architecture compliance: the diagnostic observed the Genesis VBlank helper/servicing path only. It did not alter arcade state flow, did not patch PC080SN/PC090OJ behavior, and did not implement a fix.

## Temporary Instrumentation

Added a temporary VBlank status ring in `apps/rastan-direct/src/vdp_comm.s`, all blocks labeled exactly:

`TEMP DIAGNOSTIC ONLY - REMOVE BEFORE NEXT CANONICAL BUILD`

Ring symbols in Build 0129:

| Symbol | Address |
|---|---:|
| `_vblank_service` | `runtime_genesis_pc 0x000700C2` |
| `vblank_diag_reset` | `runtime_genesis_pc 0x00070166` |
| `vblank_diag_checkpoint` | `runtime_genesis_pc 0x00070192` |
| `vblank_diag_ring_index` | `Genesis-WRAM 0x00FF60FA` |
| `vblank_diag_display_state` | `Genesis-WRAM 0x00FF60FE` |
| `vblank_diag_frame_counter` | `Genesis-WRAM 0x00FF6100` |
| `vblank_diag_ring` | `Genesis-WRAM 0x00FF6104` |

Entry layout, 16 bytes each:

`frame_low, checkpoint, VDP status, diagnostic display shadow, pc090oj_drawable_count, pc090oj_emitted_count, pc090oj_producer_write_count, pc090oj_scan_active`

Checkpoint IDs:

| ID | Meaning |
|---:|---|
| `0x01` | entry after VBlank register save |
| `0x02` | after `rastan_direct_update_inputs` |
| `0x03` | after display-off register write |
| `0x04` | after tile commit |
| `0x05` | after BG commit |
| `0x06` | after FG commit |
| `0x07` | before sprite commit |
| `0x08` | after sprite commit |
| `0x09` | after palette commit or skip |
| `0x0A` | after scroll commit |
| `0x0B` | after display-on register write |
| `0x0C` | before arcade VBlank handoff |

Intentional limitation: the diagnostic did **not** read `HW_ADDRESS 0x00C00008` / HV counter. It only read VDP control/status at `HW_ADDRESS 0x00C00004` to avoid expanding the strict-port/HV question.

A temporary invariant adjustment was required for Build 0129 only:

- `opcode_replace` patched-site count: `133` unchanged
- `total_genesis_bytes_covered`: `0x17D47C -> 0x17D564`

## Build 0129

First release invocation stopped before numbered artifact production at the expected invariant gate:

```text
expected total_genesis_bytes_covered=0x17D47C and opcode_replace patched_site count=133;
got total_genesis_bytes_covered=0x17D564 opcode_replace patched_site count=133
```

After temporarily marking the diagnostic invariant, the second release invocation produced Build 0129.

- Build produced: YES
- Build number: `0129`
- ROM SHA256: `156b59a88267ca88b39d4e4683342efe9dc707560daab95ce0fcd28d48e5e0f8`
- ROM size: `1,561,956`
- Canonical gate: `GATE_PASS`
- Automatic release trace: `states/traces/rastan_direct_video_test_build_0129_mame_30s_20260702_155754/`

## Evidence Artifacts

Evidence directory:

`states/traces/build0129_vblank_status_ring_diagnostic_20260702_155842/`

Core files:

- `capture_vblank_ring.lua`
- `symbols_build0129.txt`
- `no_input_capture.log`
- `coin_start_capture.log`
- `reduce_vblank_ring.py`
- `vblank_status_ring_analysis.json`
- `vblank_status_ring_analysis.md`
- `build0129_vblank_status_snapshots_contact.png`

Representative snapshots:

| Run | MAME frame | Label | Snapshot |
|---|---:|---|---|
| no input | 60 | early no-input | `no_input_0000.png` |
| no input | 120 | mid no-input | `no_input_0001.png` |
| no input | 180 | late no-input | `no_input_0002.png` |
| no input | 282 | black-cover/story anchor | `no_input_0004.png` |
| no input | 369 | late no-input | `no_input_0007.png` |
| coin/start | 340 | pre-coin | `coin_start_0000.png` |
| coin/start | 371 | coin accepted / story visible | `coin_start_0001.png` |
| coin/start | 473 | start clear window | `coin_start_0003.png` |
| coin/start | 474 | stale redraw window | `coin_start_0004.png` |
| coin/start | 477 | second clear window | `coin_start_0005.png` |
| coin/start | 534 | ROUND window | `coin_start_0006.png` |
| coin/start | 620 | late coin run | `coin_start_0008.png` |

## Runtime Capture Summary

No-input run:

| MAME frame | State `%a5@(0/2/4)` | BG nonzero | FG nonzero | Drawable / emitted | Visual note |
|---:|---|---:|---:|---:|---|
| 60 | `0/1/0` | `560` | `66` | `23 / 23` | sparse title/logo fragments |
| 120 | `0/1/0` | `560` | `66` | `23 / 23` | sparse title/logo fragments |
| 180 | `0/1/0` | `560` | `66` | `23 / 23` | mostly black / tiny visible fragments |
| 240 | `0/1/0` | `560` | `66` | `8 / 7` | mostly black / transition |
| 282 | `0/1/2` | `168` | `146` | `9 / 8` | story-frame anchor / black-cover class |
| 283 | `0/1/2` | `168` | `146` | `5 / 5` | post-anchor |
| 289 | `0/1/2` | `168` | `146` | `23 / 23` | story text/art fragments |
| 369 | `0/1/2` | `168` | `146` | `23 / 23` | late no-input sparse output |

A no-input mostly-complete story/title frame was **not** reproduced in this run. The run captured black/sparse frames and partial story/title fragments.

Coin/start run:

| MAME frame | State `%a5@(0/2/4)` | BG nonzero | FG nonzero | Drawable / emitted | Visual note |
|---:|---|---:|---:|---:|---|
| 340 | `0/1/2` | `168` | `146` | `5 / 5` | pre-coin story context |
| 371 | `1/0/0` | `168` | `61` | `23 / 23` | coin accepted; mostly complete story/king frame visible |
| 411 | `1/1/0` | `168` | `72` | `19 / 19` | 1P/2P prompt class |
| 473 | `2/2/6` | `0` | `8` | `30 / 30` | start clear window |
| 474 | `2/2/6` | `0` | `8` | `30 / 30` | stale redraw window |
| 477 | `2/2/6` | `0` | `8` | `30 / 30` | second clear window |
| 534 | `2/2/7` | `0` | `11` | `32 / 32` | ROUND window |
| 560 | `2/2/7` | `0` | `11` | `32 / 32` | post-ROUND |
| 620 | `2/2/7` | `0` | `11` | `32 / 32` | late coin run |

The coin/start script used real controller fields only (`P1 A` pulse then `P1 Start` hold); no state or memory was forced.

## VBlank Status / Display Timing Findings

Observed VDP status bit 3 behavior:

- At checkpoint `0x03` after display-off and through checkpoints `0x04..0x0A`, `status_bit3_vblank` was consistently `1` in the captured windows.
- Diagnostic display shadow was consistently `0` from checkpoint `0x03` through `0x0A`.
- At checkpoint `0x0B` after display-on and checkpoint `0x0C` before handoff, diagnostic display shadow was consistently `1`.
- `status_bit3_vblank` at checkpoints `0x0B/0x0C` was often `0`, but sometimes still `1` when the capture caught the service late within VBlank.

Interpretation:

- The diagnostic supports the normal service sequence: display off, commit work, display on, handoff.
- It does **not** show an obvious extra display-off/display-on churn loop.
- It does **not** show the commit block running outside VBlank in the sampled windows; the body from display-off through scroll was observed with VBlank bit 3 set.
- The occasional bit-3-high readings after display-on are interpreted as timing within the same VBlank interval, not as an independent fault mechanism.

## Graphics/State Observations

- The no-input run remains visually incomplete: mostly black or sparse fragments, no complete stable title proof.
- The coin/start run reproduced a visible story/king frame at frame 371 and then the start/ROUND transition class.
- Around start clear/stale redraw/second clear (`2/2/6`), BG staging was `0` nonzero words while FG contained only `8` nonzero words.
- Around ROUND (`2/2/7`), BG staging remained `0` and FG rose to `11` nonzero words.
- These observations keep the graphics problem focused on real staged content / layer composition / sprite-window interactions, not on a proven VBlank refresh-frequency failure.

## Immediate Revert

After evidence capture, all temporary diagnostic code/data/symbols/comments and invariant changes were removed.

Post-revert checks:

- `rg "TEMP DIAGNOSTIC ONLY|vblank_diag|17D564" apps/rastan-direct/src tools/translation` returned no hits.
- `CANONICAL_OPCODE_REPLACE_COUNT = 133` restored in both canonical tools.
- `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17D47C` restored in both canonical tools.
- `git diff -- apps/rastan-direct/src/vdp_comm.s apps/rastan-direct/src/boot/boot.s tools/translation/postpatch_startup_rom.py tools/translation/verify_canonical_rom.py` returned zero bytes.

## Revert Build 0130

Build 0130 was produced after removing the diagnostic.

- Build produced: YES
- Build number: `0130`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0130.bin`
- SHA256: `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`
- Size: `1,561,724` bytes
- Canonical gate: `GATE_PASS`
- Rolling ROM SHA matches Build 0130: YES
- Automatic release trace: `states/traces/rastan_direct_video_test_build_0130_mame_30s_20260702_160308/`

Byte-identical proof:

| Build | SHA256 | Size |
|---:|---|---:|
| 0128 | `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f` | `1,561,724` |
| 0130 | `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f` | `1,561,724` |
| rolling | `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f` | `1,561,724` |

`cmp -s dist/rastan-direct/rastan_direct_video_test_build_0128.bin dist/rastan-direct/rastan_direct_video_test_build_0130.bin` returned `0`.

`cmp -s dist/rastan-direct/rastan_direct_video_test_build_0130.bin apps/rastan-direct/dist/rastan_direct_video_test.bin` returned `0`.

Verdict: **PASS. Build 0130 is byte-identical to Build 0128.**

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: touched as graphics-output evidence; not closed.
- OPEN-024: touched as sprite/VBlank composition context; not closed.
- OPEN-015: not touched.
- New issues opened: none.
- Issues closed: none.
- `KNOWN_FINDINGS.md`: Option A, no update. This is a temporary diagnostic/evidence pass and does not establish a durable new root cause.

## STOP Status

STOP triggered: **NO**.

The diagnostic artifact was produced and measured, the temporary instrumentation was fully removed, and the revert ROM was proven byte-identical to the Build 0128 baseline.
