# Cody - Build 0091 Helper Crash Fix Part 2 Artifact Production

**Date:** 2026-06-20
**Type:** Build artifact production only
**Scope:** Re-invoke the release target once after the prior task's STOP, using the already-applied Build 0091 helper-crash source fix and already-corrected canonical invariants. No source/spec/tool/invariant edits. No bookmark cycle. No OPEN-015 or Start-C-A work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-028 (Build 0091 helper-crash diagnosis and source fix), KF-013 (text dispatch inside VBlank), KF-010 (FG maps to Plane A), KF-004 (runtime PC = ROM file offset), and KF-006 (identity offset `0x200`). HIGH-hazard prior touched: KF-028.

Open issues touched: OPEN-016 (active), OPEN-015 and OPEN-001 (context only). No issues opened or closed. Contradiction detected: **NO**. STOP not triggered in Phase 0.

## Phase 1 - Pre-build Verification

Pre-build counter: `91`.

Verified before release invocation:

- `apps/rastan-direct/src/tilemap_hooks.s` contains the three required `.Lgr_store_cell` base-register loads after the `movem.l` save:
  - `lea genesistan_pc080sn_tile_vram_lut,%a3`
  - `lea genesistan_pc080sn_attr_lut,%a5`
  - `lea staged_fg_buffer,%a6`
- `tools/translation/postpatch_startup_rom.py` invariant: `CANONICAL_OPCODE_REPLACE_COUNT = 95`, `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CB58`.
- `tools/translation/verify_canonical_rom.py` invariant: `CANONICAL_OPCODE_REPLACE_COUNT = 95`, `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CB58`.

Acceptance: **PASS**.

## Phase 2 - Single Release Invocation

Command run exactly once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

Release output:

- Canonical gate: `GATE_PASS`
- Counter advanced: `91 -> 92`
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0092.bin`
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Release trace artifact: `states/traces/rastan_direct_video_test_build_0092_mame_30s_20260620_003542/`

## Phase 3 - Counter-safe Determinism

SHA256:

- Numbered ROM: `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`
- Rolling ROM: `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`

`cmp` result: `0` (byte-identical).

Build 0091 SHA comparison: differs from `942dcb1aefebec7cbd808d016ff41f4bc22ec9ffd92c98be8a423297a56590cc`.

## Phase 4 - Static Verification

Generated disassembly confirms the Build 0091 helper-crash fix is present in the produced artifact:

```asm
70bc8: 48e7 ff3e       moveml %d0-%d7/%a2-%fp,%sp@-
70bcc: 47f9 000f 1f2c  lea 0xf1f2c,%a3
70bd2: 4bf9 000f 9f2c  lea 0xf9f2c,%a5
70bd8: 4df9 00ff 501a  lea 0xff501a,%fp
70bde: 2449            moveal %a1,%a2
70be6: 6100 fbd4       bsrw 0x707bc
```

Symbol verification:

- `genesistan_pc080sn_tile_vram_lut = 0x000F1F2C`
- `genesistan_pc080sn_attr_lut = 0x000F9F2C`
- `staged_fg_buffer = 0x00FF501A`

Shared helper remains at `0x707BC` and retains the expected staging path through `0x707C6` and `0x707E4`. Existing text-writer hooks remain present at `0x70BF4` (`genesistan_hook_text_writer_3c550`) and `0x70C44` (`genesistan_hook_text_writer_3c586`) and still load the same LUT/staging bases.

OPEN-016 Part 1 descriptor-table relocation is preserved: ROM bytes at `0x03BE80` are `0003c446`, so `table[65] = 0x0003C446`.

## Non-Actions

No source, spec, tool, invariant, Makefile, crash-handler, bookmark, or runtime-observation code was intentionally modified in this task. No issue was opened or closed. No `KNOWN_FINDINGS.md` update was made.

## OPEN-016 / KNOWN_FINDINGS Impact

KNOWN_FINDINGS impact: Option A - no new finding indexed. KF-028 already records the Build 0091 helper-crash diagnosis; this task only produced the numbered artifact from the already-applied fix.

OPEN-016 remains open pending Tighe runtime testing and the broader deferred surveys.

## STOP

STOP triggered: **NO**.
