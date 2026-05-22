# Cody — BM-001 Revert + BM-002 Insert (Positive-Control Cycle)

## Phase 1 — Pre-flight verification
Verified starting state:
- `active_bookmark_baseline.json` had `cycle_id=BM-001`, `pre_insert_canonical_rom_sha256=72f9f33d...`, `pre_insert_build_counter=66`.
- Spec contained BM-001 coupled entries (`diagnostic_bookmarks[0]` + `opcode_replace[94]` with `bookmark_cycle=BM-001`).
- `build_counter.txt` = 67.

## Phase 2 — BM-001 Revert
Spec edits:
- Removed BM-001 `diagnostic_bookmarks` entry.
- Removed BM-001 `opcode_replace` activator entry.

Build command:
- `BOOKMARK_REVERT=BM-001 make -C apps/rastan-direct release`

Results:
- Build 0068 produced: `dist/rastan-direct/rastan_direct_video_test_build_0068.bin`
- Build 0068 SHA: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Build 0062 SHA: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- SHA match: YES (§2.8 PASS, byte-identical revert)
- Gate state context: `authorized_revert`
- State file deleted after revert: YES
- Canonical invariants restored: patched_site=94, total_genesis_bytes_covered=0x17CAEC
- Helper preserved at 0x00071C78 (`60fe`, SHA `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb`)

BM-001 revert metadata recorded in:
- `dist/rastan-direct/bookmarks/build_0067_pc_0x055948/REVERT_NOTES.md`

## Phase 3 — BM-002 positive-control target derivation
Trace source analyzed:
- `dist/rastan-direct/bookmarks/build_0067_pc_0x055948/mame_run_log.txt`

Candidate PCs observed repeatedly (Build 0067):
- 0x03A196 (17 hits)
- 0x03A19E (16 hits)
- 0x03A198 (11 hits)
- 0x03A19C (7 hits; first at frame 000180)

Chosen target: `arcade_pc = 0x03A19C`

Trace evidence (Build 0067):
- Line 24: `[frame 000180] pc=03a19c exec=frontend_core@000000`
- Additional hits at lines 42, 50, 77, 119, 126, 153.

Disassembly safety evidence (`build/maincpu.disasm.txt`):
- `3a19c: 41fa 000e` (LEA)
- `3a1a0: d0c0` (ADDA.W)
- `3a1a2: 3010` (MOVE.W)
- Exact 8-byte instruction-aligned span at 0x03A19C: `41fa000ed0c03010`
- No branch-target references found to 0x3A19C/0x3A19E via disassembly text search.
- Region is `frontend_core@000000` in trace, not helper/interrupt/NMI instrumentation range.

Rejected candidates (brief):
- 0x03A196, 0x03A198, 0x03A19E: less clean 8-byte instruction-boundary behavior for activator insertion and/or less direct span safety than 0x03A19C.

## Phase 4 — BM-002 Insert
Pre-insert canonical bytes from Build 0068:
- target 0x03A19C (ROM offset 0x03A39C): `41fa000ed0c03010`

Spec edits:
- Added BM-002 `diagnostic_bookmarks` entry.
- Added BM-002 `opcode_replace` entry with `replacement_bytes=4EF9{symbol:genesistan_diag_bookmark}4E71` and `bookmark_cycle=BM-002`.

Build command:
- `make -C apps/rastan-direct release`

Results:
- Build 0069 produced: `dist/rastan-direct/rastan_direct_video_test_build_0069.bin`
- Build 0069 SHA: `e206d3cf3f50639727119ceded4271e95d8f3c1fb93f44eb6607dfc865aaf96a`
- Gate context: `diagnostic`
- Gate checks: PASS (including §2.7 activator integrity)
- patched_site expected/observed: `95` / `95` (MATCH)
- coverage expected/observed: `0x17CAF4` / `0x17CAF4` (MATCH)
- Activator bytes at target: `4ef900071c784e71`
- Helper preserved: `60fe` at 0x00071C78 (canonical SHA)
- State file written with BM-002 metadata: cycle_id=BM-002, baseline SHA=Build 0068 SHA, pre_insert_build_counter=68.

## Phase 5 — BM-002 trace and outcome
Trace source:
- `states/traces/rastan_direct_video_test_build_0069_mame_30s_20260515_181201/genesis_exec_trace.log`
- Copied artifact: `dist/rastan-direct/bookmarks/build_0069_pc_0x03A19C/mame_run_log.txt`

Trace currency verification:
- Same make invocation produced Build 0069 and this trace.
- Trace mtime is newer than Build 0069 ROM mtime.

Outcome:
- **Outcome B — BM-002 did not fire in 30-second trace window.**
- Helper hits (`0x00071C78`): `0`
- Target hits (`0x03A19C`): `7`
- First target hit: line 24 (`[frame 000180] pc=03a19c exec=frontend_core@000000`)

Mechanism-validation framing:
- Positive-control target was still reached in Build 0069 trace, but helper was not reached.
- This indicates a real-runtime bookmark-mechanism problem to investigate before trusting further bookmark-cycle Outcome-B interpretations.

## Outputs
- Build 0068 canonical ROM + Build 0069 diagnostic ROM produced sequentially.
- BM-001 revert notes: `dist/rastan-direct/bookmarks/build_0067_pc_0x055948/REVERT_NOTES.md`
- BM-002 folder:
  - `insert_meta.txt`
  - `mame_run_log.txt`
  - `NOTES.md`
