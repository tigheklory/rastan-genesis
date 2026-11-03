# Cody — OPEN-012 Implementation + OPEN-013 Re-Verification

Date: 2026-05-18

## Scope
Implements `docs/design/Andy_OPEN012_bookmark_coordinate_model_design.md` and re-verifies CLOSED-009 behavior under the `bookmarks_v2` schema.

This task is synthetic-validation only. No real BM-003 cycle was run.

## Phase A — OPEN-012 Implementation

### A1. Spec schema
- Updated [specs/rastan_direct_remap.json](/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json):
  - Added/retained top-level `bookmarks_v2`.
  - Removed legacy `diagnostic_bookmarks` field from canonical spec.
  - `opcode_replace` remains `arcade_pc`-based and remains 94 entries.

### A2. Postpatcher `bookmarks_v2` stage
Implemented in [tools/translation/postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py):
- `bookmarks_v2` parser + legacy-field rejection: lines 73-100.
- Legacy `bookmark_cycle` rejection on `opcode_replace`: lines 103-112.
- New activator writer `_apply_bookmarks_v2`: lines 146-242.
- New state-file write source (`bookmarks_v2[0]`): lines 128-143.
- Stage placement after opcode relocation/rewrite flow: lines 1773-1775.

Implemented STOP validations per design + Tighe locks:
- Forbidden `arcade_pc` field in bookmark entry.
- Allowlist enforcement via `DIAGNOSTIC_SYMBOLS`.
- `span_length` validity (`>=6`, `(span-6)%2==0`).
- ROM bounds check.
- `runtime_genesis_pc < 0x00000400` STOP.
- Helper-byte overlap STOP (`genesistan_diag_bookmark` bytes).
- Wider helper/data-adjacent condition implemented as warning (`span_end > 0x000F1DBC`).

### A3. CLOSED-009 ripple revisions + old-path removal
Implemented in [tools/translation/postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py) and [tools/translation/verify_canonical_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/verify_canonical_rom.py):
- Mode detection keyed to `bookmarks_v2` (`is_diagnostic_mode = len(bookmarks_v2) > 0`): postpatcher line 1129.
- Old diagnostic cross-reference path removed.
- `opcode_replace` invariant now strict 94 always: postpatcher lines 1858-1869 and 1985-1994.
- `segment_coverage` invariant now strict `0x17CAEC` always: postpatcher lines 1987-2001.
- Manifest now reports `bookmarks_v2_count` and `bookmarks_v2_applied`: postpatcher lines 2124-2125.
- Legacy `diagnostic_bookmarks` and legacy `bookmark_cycle` now rejected fail-closed in both postpatcher and gate.

### A4. Gate §2.7 replacement
Implemented in [tools/translation/verify_canonical_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/verify_canonical_rom.py):
- Renamed failure ID to `GATE_FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES`: line 20.
- New `bookmarks_v2` parser and legacy schema rejection: lines 230-317.
- New state-context resolver keyed to `bookmarks_v2`: lines 368-437.
- New activator checker `check_bookmark_activator_bytes`: lines 699-735.
- `§2.8` revert check unchanged in semantics: lines 738-759.

### A5. Phase A validation gate
Phase A validation artifacts are under `build/rastan-direct/open013_test_artifacts/`:
1. Canonical build passes with strict invariants:
   - Build 0071 gate PASS, state context `canonical`.
   - `postpatch_expected_opcode_replace_sites=94`
   - `postpatch_expected_total_genesis_bytes_covered=0x17CAEC`
   - ROM SHA matches canonical baseline (`72f9f33d...`).
2. Legacy `diagnostic_bookmarks` field rejection: PASS (`phaseA_legacy_field.log`).
3. Forbidden `arcade_pc` in `bookmarks_v2` rejection: PASS (`phaseA_forbidden_arcade_pc.log`).
4. Valid synthetic `bookmarks_v2` entry path: PASS (`phaseA_valid_insert_postpatch.log`, `phaseA_valid_insert_gate.log`), including activator bytes at runtime PC `0x0003A19C` = `4ef900071c784e71`.
5. Old-path removal grep check completed (`old_path_removal_grep.txt`).

Phase A PASS achieved before entering Phase B.

## Phase B — OPEN-013 Re-Verification Matrix

Artifacts root: `build/rastan-direct/open013_test_artifacts/`.

### CLOSED-009-analog matrix (13 tests)
1. Canonical build: PASS (Build 0071).
2. Synthetic Insert (BM-901) full make: PASS (Build 0072, diagnostic context, strict 94/0x17CAEC retained).
3. Synthetic Revert (BM-901) full make + `BOOKMARK_REVERT`: PASS (Build 0073, authorized_revert, §2.8 PASS, state file deleted).
4. Orphaned file: PASS (`GATE_FAIL_STATE_ORPHANED_FILE`).
5. Orphaned spec: PASS (`GATE_FAIL_STATE_ORPHANED_SPEC`).
6. Cycle mismatch: PASS (`GATE_FAIL_STATE_MISMATCH`).
7. Revert wrong cycle: PASS (`GATE_FAIL_STATE_REVERT_CONTEXT_MISMATCH`).
8. Revert during active cycle: PASS (`GATE_FAIL_STATE_REVERT_DURING_ACTIVE_CYCLE`).
9. Revert no cycle: PASS (`GATE_FAIL_STATE_REVERT_NO_CYCLE`).
10. Corrupted state file: PASS (`GATE_FAIL_STATE_CORRUPTED`).
11. Tampered activator bytes (diagnostic): PASS (`GATE_FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES`).
12. Tampered revert baseline SHA: PASS (`GATE_FAIL_2_8_REVERT_NOT_BYTE_IDENTICAL`).
13. Fresh end-to-end synthetic cycle (BM-902): PASS (Insert Build 0074, Revert Build 0075, final SHA equals canonical baseline).

### New OPEN-012-specific failure tests
14. Out-of-bounds `runtime_genesis_pc`: PASS (postpatcher STOP).
15. Forbidden `arcade_pc` field: PASS (postpatcher STOP).
16. Legacy `diagnostic_bookmarks` field present: PASS (postpatcher STOP).
17. `runtime_genesis_pc < 0x00000400`: PASS (postpatcher STOP).
18. Activator span overlaps helper bytes: PASS (postpatcher STOP).
19. `helper_symbol` outside allowlist: PASS (postpatcher STOP).
20. Invalid `span_length`: PASS (postpatcher STOP).

## Failure-ID Table (current)
- `GATE_FAIL_STATE_ORPHANED_SPEC`
- `GATE_FAIL_STATE_ORPHANED_FILE`
- `GATE_FAIL_STATE_MISMATCH`
- `GATE_FAIL_STATE_REVERT_CONTEXT_MISMATCH`
- `GATE_FAIL_STATE_REVERT_DURING_ACTIVE_CYCLE`
- `GATE_FAIL_STATE_REVERT_NO_CYCLE`
- `GATE_FAIL_STATE_CORRUPTED`
- `GATE_FAIL_LEGACY_BOOKMARK_SCHEMA` (legacy `diagnostic_bookmarks` field or legacy `opcode_replace[].bookmark_cycle` tag rejection)
- `GATE_FAIL_2_5_BOOKMARK_SCHEMA_VALIDATION` (`bookmarks_v2` schema-validation failures; each emission cites the specific failing field/constraint)
- `GATE_FAIL_2_7_BOOKMARK_ACTIVATOR_BYTES`
- `GATE_FAIL_2_8_REVERT_NOT_BYTE_IDENTICAL`
- Existing unchanged gate IDs retained: `2.1`, `2.2`, `2.3`, `2.4`, `2.5`, `2.6`.

Record-correction note:
- The initial OPEN-012/OPEN-013 implementation summary under-described the old cross-reference-labeled failure-ID reuse as legacy-only.
- Source inspection showed it also covered the live `bookmarks_v2` schema-validation bucket.
- Hygiene split now makes the two meanings explicit and non-overlapping.

## bookmarks_v2 Workflow Checklist (including PC-relative screening)
1. Choose target from runtime trace as literal `runtime_genesis_pc` (no cross-space arithmetic).
2. Confirm target bytes from canonical ROM at file offset `runtime_genesis_pc`.
3. Screen first instruction for PC-relative opcodes (`LEA/JMP PC-relative` etc.); reject target if first instruction is PC-relative.
4. Select `span_length` valid for `JMP_LONG_ABS + NOP-word padding`.
5. Populate `bookmarks_v2` entry with canonical bytes + canonical SHA.
6. Build Insert; verify gate diagnostic context + `§2.7` pass.
7. Revert with explicit `BOOKMARK_REVERT=BM-NNN`; verify `§2.8` pass + state file deletion.

## Final State Checks
- Canonical spec restored and unchanged from task-start canonical fixture:
  - `bookmarks_v2` empty
  - no `diagnostic_bookmarks` field
  - `opcode_replace` count 94
  - diff vs `spec_canonical.json` is empty
- Build 0075 SHA: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc` (matches Build 0070 baseline)
- Helper preserved (`0x00071C78` bytes `60fe`, helper SHA `20825b...fecb`)

## OPEN-012 / OPEN-013 status
Implementation complete and matrix passed; both remain OPEN pending BM-003 positive-control Outcome A.
