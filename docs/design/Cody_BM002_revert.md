# Cody — BM-002 Revert

## Scope
Bookmark-cycle Revert task only. Restores canonical state after BM-002 Insert.

## Phase 1 — Pre-flight verification
Verified expected BM-002 mid-flight state before edits:
- `build/rastan-direct/active_bookmark_baseline.json` present with:
  - `cycle_id = BM-002`
  - `pre_insert_canonical_rom_sha256 = 72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
  - `pre_insert_build_counter = 68`
- `specs/rastan_direct_remap.json` contained BM-002 entries:
  - one `diagnostic_bookmarks` entry for BM-002
  - one `opcode_replace` entry tagged `bookmark_cycle: BM-002`
- `build_counter.txt = 69`

## Phase 2 — Spec canonicalization
Removed BM-002 entries from `specs/rastan_direct_remap.json`:
- `diagnostic_bookmarks` set to empty array
- BM-002 `opcode_replace` entry removed

Post-edit checks:
- JSON valid
- `diagnostic_bookmarks` empty
- `opcode_replace` count returned to 94
- no residual BM-002 references

## Phase 3 — Build with explicit Revert context
Command:
- `BOOKMARK_REVERT=BM-002 make -C apps/rastan-direct release`

Observed behavior:
- Build succeeded
- Gate output: `GATE_PASS`
- Gate state context: `authorized_revert`
- Numbered artifact emitted: `dist/rastan-direct/rastan_direct_video_test_build_0070.bin`

Manifest/address-map verification:
- `build_context: canonical`
- expected patched sites: 94, observed: 94
- expected coverage: `0x17CAEC`, observed: `0x17CAEC`

§2.8 revert identity verification:
- Build 0070 SHA256: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Build 0068 SHA256: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Build 0062 SHA256: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Result: byte-identical match (PASS)

State lifecycle:
- `build/rastan-direct/active_bookmark_baseline.json` deleted by gate after §2.8 PASS (confirmed absent)

Helper integrity:
- bytes at `0x00071C78`: `60 FE`
- helper SHA256 (2 bytes): `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb`

## Phase 4 — Revert documentation
Added:
- `dist/rastan-direct/bookmarks/build_0069_pc_0x03A19C/REVERT_NOTES.md`

Build 0069 preservation check:
- Build 0069 ROM and BM-002 evidence files (`insert_meta.txt`, `mame_run_log.txt`, `NOTES.md`, `EXODUS_OBSERVATION.md`) left unchanged.

## Result
BM-002 cycle closed cleanly per Rule 10. Canonical baseline restored at Build 0070.
Build 0069 remains frozen for the post-Revert Andy investigation.
