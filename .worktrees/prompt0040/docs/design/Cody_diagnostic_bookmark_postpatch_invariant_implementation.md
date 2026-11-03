# Cody — Diagnostic Bookmark Postpatch Invariant Implementation

## Scope
Implemented Andy's design in `docs/design/Andy_diagnostic_bookmark_postpatch_invariant_design.md` with Chad's refinement: Revert context is explicit and never inferred from state-file presence alone.

## Files Changed
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `apps/rastan-direct/Makefile`
- `OPEN_ISSUES.md`

## Revert Context Mechanism Choice
Chosen mechanism: **Makefile variable + gate argument**.
- User/build invocation: `BOOKMARK_REVERT=BM-001 make -C apps/rastan-direct ...`
- Makefile passes explicit context into gate via `--bookmark-revert "$(BOOKMARK_REVERT)"`.
- Gate never infers Revert from state-file presence + empty spec alone.

Rationale:
- Explicit and auditable in command history / CI logs.
- Works with existing `$(BIN)` recipe integration.
- Avoids heuristics and satisfies fail-closed truth table.

## Postpatcher Implementation
Reference lines in `tools/translation/postpatch_startup_rom.py`:
- Constants and lifecycle paths: lines 15-31
  - `ACTIVE_BOOKMARK_BASELINE_PATH`
  - `CANONICAL_OPCODE_REPLACE_COUNT = 94`
  - `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CAEC`
  - `DIAGNOSTIC_SYMBOLS = ("genesistan_diag_bookmark",)`
- Spec parsing + cross-reference validation helpers: lines 74-230
- Mode detection and cross-ref call in `main()`: lines 1130-1134
- Required symbol + diagnostic symbol merge: lines 1204-1218
- `bookmark_cycle` propagated into rewrite log entry: line 1603
- Context-aware expectation count check (`expectations.opcode_replace_count`): lines 1845-1858
- Context-aware coverage/count invariant + build_context label: lines 1998-2026
- Diagnostic-mode state-file write (Insert): lines 2201-2203

### Context-aware invariants
- Canonical:
  - `patched_site == 94`
  - `total_genesis_bytes_covered == 0x17CAEC`
- Diagnostic:
  - `patched_site == 94 + N`
  - `total_genesis_bytes_covered == 0x17CAEC + Σ`
  - `N = len(diagnostic_bookmarks)`
  - `Σ = sum(len(original_bytes) for bookmark_cycle-tagged activators)`

## Gate Implementation
Reference lines in `tools/translation/verify_canonical_rom.py`:
- Failure IDs: lines 13-33
- Cross-reference validator: lines 255-369
- State-file parser: lines 372-410
- State-context truth-table resolver: lines 420-489
- Context-aware §2.3 verification against manifest/address_map: lines 492-565
- §2.7 activator integrity: lines 730-813
- §2.8 byte-identical revert + atomic delete: lines 816-837
- CLI args for explicit revert and state file: lines 840-857
- Main execution flow with conditional §2.7/§2.8: lines 860-922

## State File Lifecycle
Path: `build/rastan-direct/active_bookmark_baseline.json`

Write (Insert): postpatcher writes atomically with:
- `cycle_id`
- `pre_insert_canonical_rom_sha256`
- `pre_insert_build_counter`
- `timestamp`

Read (every gate run): gate parses once at entry, validates structure.

Delete (successful authorized Revert only): gate deletes state file only after §2.8 SHA match passes.

## Failure ID Table
### State model failures
- `GATE_FAIL_STATE_ORPHANED_SPEC`
- `GATE_FAIL_STATE_ORPHANED_FILE`
- `GATE_FAIL_STATE_MISMATCH`
- `GATE_FAIL_STATE_REVERT_CONTEXT_MISMATCH`
- `GATE_FAIL_STATE_REVERT_DURING_ACTIVE_CYCLE`
- `GATE_FAIL_STATE_REVERT_NO_CYCLE`
- `GATE_FAIL_STATE_CORRUPTED`

### New diagnostic integrity failures
- `GATE_FAIL_2_5_LEGACY_CROSS_REFERENCE_MISMATCH` (historical CLOSED-009-era identifier; later retired)
- `GATE_FAIL_2_7_ACTIVATOR_INTEGRITY`
- `GATE_FAIL_2_8_REVERT_NOT_BYTE_IDENTICAL`

### Existing gate failures retained
- `GATE_FAIL_2_1_INCBIN_SHA_MISMATCH`
- `GATE_FAIL_2_2_HELPER_SHA_MISMATCH`
- `GATE_FAIL_2_3_POSTPATCHER_INVARIANT`
- `GATE_FAIL_2_4_ROM_NAMING`
- `GATE_FAIL_2_5_SYMBOL_RESOLUTION`
- `GATE_FAIL_2_6_DEPENDENCY_AUDIT`

## 13-Test Matrix Results
Artifacts live under `build/rastan-direct/open011_test_artifacts/`.

1. Canonical build context (`state absent + spec empty + no revert`): **PASS**
   - Gate on Build 0062: `GATE_PASS`, context `canonical`.

2. BM-001 Insert synthetic (full make pipeline): **PASS**
   - Build 0063 produced with synthetic insert spec.
   - Gate context `diagnostic`.
   - Manifest confirms `postpatch_expected_opcode_replace_sites=95`, `postpatch_expected_total_genesis_bytes_covered=0x17CAF4`.
   - State file written with BM-001 metadata.

3. BM-001 Revert synthetic (full make pipeline, explicit context): **PASS**
   - Build 0064 produced with canonical spec + `BOOKMARK_REVERT=BM-001`.
   - Gate context `authorized_revert`.
   - §2.8 SHA match PASS; state file deleted.
   - Build 0064 SHA equals Build 0062 SHA.

4. Orphaned file (state present, spec empty, no revert): **PASS**
   - `GATE_FAIL_STATE_ORPHANED_FILE`.

5. Orphaned spec (state absent, spec non-empty, no revert): **PASS**
   - `GATE_FAIL_STATE_ORPHANED_SPEC`.

6. Cycle mismatch (state BM-001, spec BM-002, no revert): **PASS**
   - `GATE_FAIL_STATE_MISMATCH`.

7. Revert wrong cycle (state BM-001, spec empty, revert BM-002): **PASS**
   - `GATE_FAIL_STATE_REVERT_CONTEXT_MISMATCH`.

8. Revert during active cycle (state present, spec non-empty, revert present): **PASS**
   - `GATE_FAIL_STATE_REVERT_DURING_ACTIVE_CYCLE`.

9. Revert no cycle (state absent, spec empty, revert present): **PASS**
   - `GATE_FAIL_STATE_REVERT_NO_CYCLE`.

10. Corrupted state file: **PASS**
    - `GATE_FAIL_STATE_CORRUPTED`.

11. Malformed activator (diagnostic context): **PASS**
    - `GATE_FAIL_2_7_ACTIVATOR_INTEGRITY`.

12. Tampered revert baseline SHA: **PASS**
    - `GATE_FAIL_2_8_REVERT_NOT_BYTE_IDENTICAL`.

13. End-to-end synthetic BM-001 cycle (fresh full cycle): **PASS**
    - Insert: Build 0065 diagnostic PASS.
    - Revert: Build 0066 authorized-revert PASS with explicit context.
    - Final SHA check: Build 0066 == Build 0062 (`72f9f33d...`).
    - State file deleted after successful Revert.

## Spec Mutation Handling
Synthetic tests used isolated spec files in `build/rastan-direct/open011_test_artifacts/`.
Canonical `specs/rastan_direct_remap.json` remained unchanged during test execution.

## OPEN-011 Status
Implementation complete; pending Tighe independent verification.
Closure decision remains with Tighe.
