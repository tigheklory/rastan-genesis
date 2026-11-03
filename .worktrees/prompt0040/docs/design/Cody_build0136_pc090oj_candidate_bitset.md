# Cody - Build 0136 PC090OJ 256-Bit Candidate Mask

**Date:** 2026-07-03  
**Type:** One narrow production implementation + evidence  
**Build:** 0136  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0136.bin`  
**ROM SHA256:** `23dde0a0516378267f125cde34e0cd6328a21c559bc556d2b82f034d02916bd4`  
**Baseline compared:** Build 0135, SHA `8e00be424f9afefe79d199640096bf99de7b53c4ba49e83ad32b2b491990844e`  
**Scope:** PC090OJ candidate-bitset scan reduction only. No DISPLAY_OFF split, no sprite commit relocation, no DMA timing move, no dirty-bit-only model, no scan cap reduction, no 80-SAT cap change, no PC080SN/tilemap/scene changes.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010, KF-011, KF-032, KF-038 context, OPEN-001, OPEN-017/PC090OJ sprite bring-up context, Build 0132 residency-cache evidence, Build 0135 DISPLAY_ON timing reorder evidence, and Andy/Cody PC090OJ scan-depth notes.

The prompt explicitly selected the candidate-bitset branch first, even though Andy's preferred branch had been DISPLAY_OFF splitting. This implementation followed the prompt's narrower branch and intentionally did not alter VBlank scheduling or sprite DMA timing.

Architecture compliance: **PASS**. Arcade object RAM remains the source of sprite truth. Genesis-side code only maintains a helper-derived candidate mask to avoid scanning records that have never been written or that have been proven full-record code-zero. Full 256-record semantic coverage is preserved.

## Implementation

Added a 32-byte `pc090oj_candidate_bitset`, one bit per PC090OJ record `0..255`, and a `pc090oj_candidate_count` runtime counter.

Candidate-bit set points:

- Legacy mirror bridge inside `.Lpc090oj_emit_slot`, but only when `pc090oj_scan_active == 0`, so scan-generated SAT output does not self-mark candidates.
- PC090OJ word mirror writer `.Lpc090oj_mirror_write_word_a1_d0`.
- PC090OJ byte mirror writer `.Lpc090oj_mirror_write_byte_a1_d0`.
- `genesistan_hook_3ad44_dispatch` PC090OJ long-fill path, for each touched word offset.

Candidate-bit clear point:

- Only during the PC090OJ scan, after decoding a full record and reaching the existing code-zero predicate. Blank, unmapped, offscreen, dropped, or otherwise non-emitted records stay candidates.

Scan behavior:

- The mirror scan still walks record numbers in ascending order and still allows records `0..255`.
- A zero candidate byte skips the corresponding 8-record group by advancing `%a0 += 64` and `%d6 += 8`.
- A set bit falls through to the existing decode path.
- The 80-SAT cap, emitted order, `source_id`, SAT link generation, descriptor semantics, and residency cache path are unchanged.

Boot clear:

- `_bootstrap_clear_staging` now clears `pc090oj_candidate_bitset` and `pc090oj_candidate_count` alongside the existing PC090OJ mirror/counter state.

Files changed for implementation:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/boot/boot.s`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

## Build Verification

First release attempt stopped at the canonical byte-coverage invariant with the expected mechanical code-growth mismatch. Observed value was `0x17D560` with opcode-replace count unchanged at `133`. The invariant was updated in the two canonical verifier files only.

Second release invocation passed:

- Canonical gate: `GATE_PASS`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0136.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `23dde0a0516378267f125cde34e0cd6328a21c559bc556d2b82f034d02916bd4`
- Rolling vs numbered: byte-identical
- ROM size: `1,561,952` bytes
- `opcode_replace` count: `133` unchanged
- `total_genesis_bytes_covered`: `0x17D4A4 -> 0x17D560`
- Mechanical delta: `+0xBC`

Produced symbols:

- `pc090oj_object_ram = 0x00FF67EA`
- `pc090oj_candidate_bitset = 0x00FF6FEA`
- `pc090oj_candidate_count = 0x00FF7010`
- `pc090oj_decoded_count = 0x00FF7012`

## Evidence Artifacts

Trace root:

- `states/traces/build0136_pc090oj_candidate_bitset_20260703_122044/`

Key artifacts:

- `capture_runtime.lua`
- `reduce_candidate_evidence.py`
- `candidate_runtime_reduction.md`
- `candidate_runtime_reduction.json`
- `build0136/no_input/no_input_runtime_capture.log`
- `build0136/no_input/no_input_contact_sheet.png`
- `build0136/coin_start/coin_start_runtime_capture.log`
- `build0136/coin_start/coin_start_contact_sheet.png`
- Per-frame dumps include `*_pc090oj_candidate_bitset_ff6fea.bin`, `*_pc090oj_counts_ff7010.bin`, object RAM, SAT, descriptors, resident-cache, BG/FG staging, state, and dirty/scroll regions.

MAME runs completed with status `0`. No crash occurred.

## Runtime Reduction

### Stable No-Input / Story Window

Build 0136 keeps the emitted sprite set identical to Build 0135 while reducing decoded records from 256 to 42.

| Frame | Label | Candidate bits | Decoded | Drawable | Emitted | Dropped | Build 0135 dec/draw/em/drop | Source/desc/SAT match |
|---:|---|---:|---:|---:|---:|---:|---|---|
| 60 | early_no_input | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | yes |
| 120 | mid_no_input | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | yes |
| 180 | late_no_input | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | yes |
| 240 | pre_story_window | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | yes |
| 282 | story_anchor | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | yes |
| 283 | post_anchor | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | yes |
| 289 | post_anchor_late | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | yes |
| 369 | late_no_input | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | yes |

Candidate bitset at these anchors:

- Count: `42`
- Lowest candidate record: `0`
- Highest candidate record: `47`
- Last candidate records: `38,39,42,43,44,45,46,47`

This is the expected conservative shape: 42 candidates decode to the same 23 drawable/emitted sprites, with 19 false positives and zero drops.

### Coin / Start / ROUND Path

| Frame | Label | Candidate bits | Decoded | Drawable | Emitted | Dropped | Build 0135 dec/draw/em/drop | Notes |
|---:|---|---:|---:|---:|---:|---:|---|---|
| 340 | pre_coin | 42 | 42 | 23 | 23 | 0 | 256/23/23/0 | source/desc/SAT match |
| 371 | coin_accept_window | 239 bitset, 42 decoded | 42 | 23 | 23 | 0 | 256/23/23/0 | transient many-bit set; visual diff 0 vs 0135 |
| 411 | prompt_window | 38 | 38 | 19 | 19 | 0 | 256/19/19/0 | source/desc/SAT match |
| 473 | start_clear_window | 42 bitset, 4 decoded | 4 | 0 | 0 | 0 | 40/24/24/0 | clear-transition timing; visual diff 0 vs 0135 |
| 474 | stale_redraw_window | 46 | 46 | 19 | 19 | 0 | 256/30/30/0 | transient timing; visual diff 0 vs 0135 |
| 477 | second_clear_window | 42 bitset, 46 decoded | 46 | 30 | 30 | 0 | 256/30/30/0 | source/desc/SAT match |
| 534 | round_window | 46 | 46 | 32 | 32 | 0 | 256/32/32/0 | visual diff 0 vs 0135 |
| 560 | post_round_window | 44 bitset, 46 decoded | 46 | 32 | 32 | 0 | 51/32/32/0 | source/desc match; SAT active-count timing differs |
| 620 | late_coin_run | 46 | 46 | 32 | 32 | 0 | 256/32/32/0 | visual diff 0 vs 0135 |

Notes:

- The exact-frame descriptor/SAT hashes differ at some transition frames because the frame-done capture samples different points in the state transition after reducing scan cost. Stable comparable anchors match, and PNG visual diffs for the transition frames listed above are `0` where the sampled rendered output is equivalent.
- No emitted-sprite drop occurred in any captured Build 0136 anchor.
- The one large candidate-bitset transient at coin-accept (`239` bits set) collapses back to normal low candidate counts once code-zero scan clearing runs. This demonstrates the conservative false-positive policy: broad writes are safe, then full-record code-zero clears shrink the set.

### Visual Comparison

Build 0136 does not regress the no-input/title/story visuals. In MAME snapshots, the no-input/story windows show **more visible content** than Build 0135 because the scan reduction moves display-on earlier without any separate DISPLAY_OFF split:

- Build 0136 no-input contact sheet shows TAITO/copyright/credit and later story text/king content substantially more visible than the Build 0135 baseline.
- Coin/start/ROUND sampled frames did not visually regress against Build 0135; key transition PNG diffs are `0` for coin accept, start clear, stale redraw, second clear, ROUND, post-ROUND, and late coin run.

This visual improvement is interpreted as a timing side effect of less VBlank work, not as a replacement for the deferred DISPLAY_OFF budget work.

## Regression Checks

- **Full 256 semantic input preserved:** records `0..255` remain eligible; zero candidate bytes skip work, not address space.
- **80 SAT cap unchanged:** no scan cap reduction or SAT limit change.
- **Order/source preserved:** stable no-input/story anchors and stable coin/prompt/second-clear/post-round anchors match Build 0135 source/descriptor order.
- **Dropped sprites:** `0` in all captured Build 0136 anchors.
- **Title score/story/coin/start/ROUND visuals:** no observed regression in captured MAME evidence.
- **Residency cache:** untouched; resident-cache symbols and behavior retained.
- **PC080SN/BG/FG:** untouched by implementation. The task made no tilemap, scroll, scene, palette, or PC080SN route changes.
- **VBlank timing:** no DISPLAY_OFF split and no `vdp_commit_sprites` move performed.
- **Exceptions:** none during the MAME evidence runs.

## Deferred

- DISPLAY_OFF split / commit scheduling work.
- PC090OJ dirty-bit-only scan model.
- Any scan cap reduction below 256.
- Any 80-SAT cap change.
- BlastEm/Nomad-specific runtime check.
- Gameplay/endround path beyond the reachable coin/start/ROUND automated sequence.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001 remains open.
- PC090OJ sprite bring-up / timing work remains open; this only implements the conservative candidate-mask reduction.
- KNOWN_FINDINGS impact: **Option A - no new finding indexed**. This is an implementation of the approved branch, not a new durable reverse-engineering fact.

## STOP

STOP triggered: **NO**.
