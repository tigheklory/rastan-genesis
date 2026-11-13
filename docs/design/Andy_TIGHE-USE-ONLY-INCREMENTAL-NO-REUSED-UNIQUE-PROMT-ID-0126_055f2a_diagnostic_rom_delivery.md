# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0126 — `$055F2A` lifecycle diagnostic ROM delivery

**Author:** Andy · **Date:** 2026-11-11 · **Type:** DIAGNOSTIC ONLY — NOT a gameplay candidate. Build 0564
remains the accepted throne/frontend baseline (untouched). No production attract fix attempted.

## Instrumentation (isolated, removable)

- **Location:** `apps/rastan-direct/src/tilemap_hooks.s`, in `genesistan_gameplay_scene_restore_after_teardown`
  (the Genesis helper the Build-0549 `$055F2A` splice calls — ROM `0x70BD0` in Build 0565), immediately after the
  entry `movem.l` save and **before** `move.b #1, fg_scene_scroll_reseed_pending` / the native reseed.
- **Gate:** one `.if RASTAN_DIAG_055F2A_CAPTURE … .endif` block (new flag, default **0**). Removable in one edit.
  With the flag 0 the block is excluded by the assembler, so the production path is byte-identical to Build 0564.
- **Flag plumbing:** `RASTAN_DIAG_055F2A_CAPTURE ?= 0` in the Makefile; emitted into the generated
  `pc090oj_config.inc` as `.equ RASTAN_DIAG_055F2A_CAPTURE, <v>` (alongside the other RASTAN_* flags). It is NOT
  in `CANONICAL_BUILD_FLAGS`, so canonical/family builds default it to 0.
- **Behavior when enabled:** captures the retained lifecycle state into registers + `A0=$FF1000`, then
  `trap #0` into the existing crash/diagnostic display, which **halts**. The native reseed and the production
  invariant `.Lscene_scroll_reseed_rebuild_bad_ptr` do NOT execute on this path when the flag is set.
  Binary-verified in Build 0565: XOR loop at `0x70BEA`, `trap #0` at `0x70C52`, reseed `bsr 0x70A34` at `0x70C5C`
  (the trap precedes the reseed).

## Captured fields → crash-screen register map

The diagnostic reuses the existing crash screen (register + STATE rendering). Read the screenshot with this map:

| Reg | Value |
|---|---|
| D0 | word `[A5+$13AA]` (substate) |
| D1 | word `[A5+$013E]` (current record) |
| D2 | word `[A5+$13B8]` (saved record) |
| D3 | word `[A5+$1242]` (stage/record ctx) |
| D4 | `(genesistan_current_scene_id << 8) | fg_native_gameplay_owner` |
| D5 | long `[A5+$0002]` (= word$0002 : word$0004) |
| D6 | `(word[A5+$0014] << 16) | word[A5+$0118]` |
| D7 | `word[A5+$013A] << 16` (low word 0) |
| A0 | `$00FF1000` → STATE rows `+00/+02/+04/+34/+200` show the first `$FF1000` descriptor longwords |
| A1 | long `[A5+$0214]` (= word$0214 : word$0216) |
| A2 | long `[A5+$0218]` (= word$0218 : word$021A) |
| A3 | 32-bit XOR checksum of the 16 `$FF1000` descriptor longwords |
| A4 | `(valid_count << 16) | invalid_count` over `$FF1000` (legal range `$0F08..$3A00C`, **diagnostic only**) |
| A5 | `$00FF0000` (fixed) |
| GEN PC | the diagnostic trap address inside `genesistan_gameplay_scene_restore_after_teardown` |

All required fields (`$13AA/$013E/$13B8/$1242`, `scene_id`, `fg_native_gameplay_owner`) and all nine 0125
candidate fields (`$0002,$0004,$0014,$0118,$013A,$0214,$0216,$0218,$021A`) are present, plus the `$FF1000`
descriptor signature. Descriptor validity is **diagnostic output only**, never control flow.

### Candidate-field coverage note
A narrow look at the Taito input path (`$390001/$390007`) did not surface an additional clearly-named retained
credited-play/attract/input-source A5 field within the budget; the nine 0125 candidates (the highest-referenced
game-flow offsets) are what's captured. The attract-vs-natural diff will reveal which one is the discriminator.
No new semantic names were assigned.

## Diagnostic build 0565 (DIAGNOSTIC ONLY)

Built with `RASTAN_DIAG_055F2A_CAPTURE=1 RASTAN_INVINCIBLE=1` (invincibility so the natural R1-S2 route is
survivable; irrelevant to attract). Numbered 0565; does NOT overwrite Build 0564.

- **ROM A — ATTRACT:** `dist/rastan-direct/rastan_direct_video_test_build_0565_DIAG_attract.bin`
  SHA-256 `5dcf7fcd520dd6d8fe8634e85302b95d2a0adf7ee864c676c71ca1056c4a02ab` (= the Build-0565 normal ROM).
- **ROM B — NATURAL R1-S2→R1-S3:** `dist/rastan-direct/rastan_direct_video_test_build_0565_DIAG_natural_r1s2.bin`
  SHA-256 `ff12afc045fce0d3792f227060d72eebb878fecdab757c90c89e19f8bafbf613` (R1-S2 direct-start of the 0565
  diag+invincible ROM, via `build_subround_variant.py`, authentic retained lifecycle — the record is not faked).
- (Base numbered ROM `rastan_direct_video_test_build_0565.bin` is identical to ROM A.)

## Tighe procedures

### Capture A — attract
1. Boot `..._0565_DIAG_attract.bin` in BlastEm.
2. Press nothing.
3. Let the title/attract sequence naturally enter the gameplay demo.
4. The screen halts at the `$055F2A` capture (a crash-style screen; GEN PC inside
   `genesistan_gameplay_scene_restore_after_teardown`).
5. Screenshot it (the full register + STATE grid).

### Capture B — natural R1-S2→R1-S3
1. Boot `..._0565_DIAG_natural_r1s2.bin` in BlastEm (starts directly in R1-S2, invincible).
2. Play through R1-S2 to its end and let the real R1-S2→R1-S3 transition occur (do NOT force a record).
3. The screen halts at the same `$055F2A` capture.
4. Screenshot it.

Send both screenshots. The next task diffs A vs B (expected: a low A5 game-mode/attract byte differs, with the
`$FF1000` signature valid in B / invalid in A) to identify the retained semantic discriminator, then implements
the production attract fix.

## Confirmations
- Instrumentation executes **before** the reseed, captures before modification, and **halts** so the production
  reseed never runs on this path — binary-verified (`trap #0` @0x70C52 precedes reseed `bsr` @0x70C5C).
- Flag default 0 ⇒ `.if` block excluded ⇒ production path unchanged (Build-0564 behavior).
- **Build 0564 untouched** (SHA `869054a3…` unchanged).
- **Throne/frontend fix present** (the three `SCENE_GAMEPLAY_ID`-gated BG producers intact).
- **`.Lscene_scroll_reseed_rebuild_bad_ptr` intact** (not weakened/removed; the diagnostic halts before it).
- No R2/LUT/scratch/audio/torch/boss/score work; no production attract fix implemented.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0126`
