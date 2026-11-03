# Cody — BM-003 Revert

Date: 2026-05-19

## Phase 1 — Pre-flight Verification
- `build/rastan-direct/active_bookmark_baseline.json` present with:
  - `cycle_id: BM-003`
  - `pre_insert_canonical_rom_sha256: 72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
  - `pre_insert_build_counter: 75`
- `specs/rastan_direct_remap.json` contained BM-003 `bookmarks_v2` entry:
  - `cycle_id: BM-003`
  - `runtime_genesis_pc: 0x0003A19C`
- `build/rastan-direct/build_counter.txt` = `76`

## Phase 2 — Spec Canonicalization
- Removed BM-003 from `bookmarks_v2` in `specs/rastan_direct_remap.json`.
- Post-change checks:
  - `bookmarks_v2` length = 0
  - `opcode_replace` length = 94
  - no residual `BM-003` reference in spec

## Phase 3 — Authorized Revert Build and Gate
Command executed:
- `BOOKMARK_REVERT=BM-003 make -C apps/rastan-direct release`

Build and gate outcome:
- `GATE_PASS`
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0077.bin`
- Gate state context: `authorized_revert`
- Patch manifest checks:
  - `build_context: canonical`
  - `postpatch_expected_opcode_replace_sites: 94`
  - `postpatch_expected_total_genesis_bytes_covered: 0x17CAEC`
  - `bookmarks_v2_count: 0`
- §2.8 byte-identical revert: PASS

Byte-identity verification:
- Build 0077 SHA256: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Build 0070 SHA256: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Result: byte-identical

State file lifecycle:
- `build/rastan-direct/active_bookmark_baseline.json` deleted by gate after §2.8 PASS.

Helper integrity:
- Build 0077 bytes at `0x00071C78`: `60fe`
- Canonical helper SHA for `60fe`: `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb`

## Phase 4 — OPEN-014 Ledger Entry
- Added OPEN-014 to `OPEN_ISSUES.md`:
  - Title: MAME tracer does not reliably sample a parked diagnostic-bookmark helper
  - Scope: track-only issue from BM-003 evidence
  - No tracer-gap fix attempted in this task

## Phase 5 — Documentation
- Added `dist/rastan-direct/bookmarks/build_0076_pc_0x0003A19C/REVERT_NOTES.md`:
  - BM-003 cycle closure metadata
  - Outcome-A confirmation record (Exodus direct observation + MAME exit-summary corroboration)
  - OPEN-014 cross-reference
- Added this implementation document.
- Appended `AGENTS_LOG.md`.

## Integrity Summary
- Revert ROM built with explicit `BOOKMARK_REVERT=BM-003`: YES
- Gate §2.8 PASS and state file deleted: YES
- Build 0077 SHA equals Build 0070 canonical SHA: YES
- Helper preserved: YES
- OPEN-014 opened (track-only): YES
- Existing BM-003 evidence files (`insert_meta.txt`, `mame_run_log.txt`, `NOTES.md`) unchanged: YES
