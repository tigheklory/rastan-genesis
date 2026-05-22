# Andy — OPEN-011 Implementation Verification Report

**Agent:** Andy (Claude Code)
**Type:** Read-only verification of Cody's OPEN-011 implementation against Andy's design and Chad's explicit-revert-context refinement.
**Date:** 2026-05-12
**Scope:** seven independent verification items per the prompt. Closure decision is Tighe's, not Andy's. Andy reports outcomes with cited evidence and produces an overall recommendation.

---

## Overall recommendation

**OPEN-011 is closeable as CLOSED-009.** All seven verification items PASS with cited evidence. No discrepancies found between Cody's implementation claims and the actual artifacts/source. The diagnostic bookmark postpatch invariant model is correctly implemented and ready for the first real bookmark cycle (BM-001 against `arcade_pc 0x055948` or whatever target Tighe authorizes next).

---

## Item 1 — Spec integrity

**Claim:** `specs/rastan_direct_remap.json` was not permanently modified during Cody's 13-test run.

**Method:** compare current spec SHA256 against Cody's preserved canonical baseline in `build/rastan-direct/open011_test_artifacts/spec_canonical.sha256`.

**Evidence:**
- Current `specs/rastan_direct_remap.json` SHA256: `80d53a526d9f5dea8c3d56ee0075a0712377334254a3f6c06c78b574edaad677`
- Baseline `build/rastan-direct/open011_test_artifacts/spec_canonical.sha256`: `80d53a526d9f5dea8c3d56ee0075a0712377334254a3f6c06c78b574edaad677  specs/rastan_direct_remap.json`
- Bytes match.

**Outcome: PASS.** Cody used isolated synthetic spec files in `open011_test_artifacts/` for tests; the canonical spec was not touched.

---

## Item 2 — Failure ID coverage (tests 4-12)

**Claim:** each of the 9 failure-mode tests emits the correct failure ID on its first line.

**Method:** read the first line of each `test{4..12}_*.log` file in `build/rastan-direct/open011_test_artifacts/` and compare to the expected failure ID per the truth table.

**Evidence (first line of each log, verbatim):**

| Test | Expected failure ID | First line observed | Outcome |
|---|---|---|---|
| 4 (`test4_orphaned_file.log`) | `GATE_FAIL_STATE_ORPHANED_FILE` | `GATE_FAIL_STATE_ORPHANED_FILE` | **PASS** |
| 5 (`test5_orphaned_spec.log`) | `GATE_FAIL_STATE_ORPHANED_SPEC` | `GATE_FAIL_STATE_ORPHANED_SPEC` | **PASS** |
| 6 (`test6_cycle_mismatch.log`) | `GATE_FAIL_STATE_MISMATCH` | `GATE_FAIL_STATE_MISMATCH` | **PASS** |
| 7 (`test7_revert_wrong_cycle.log`) | `GATE_FAIL_STATE_REVERT_CONTEXT_MISMATCH` | `GATE_FAIL_STATE_REVERT_CONTEXT_MISMATCH` | **PASS** |
| 8 (`test8_revert_during_active.log`) | `GATE_FAIL_STATE_REVERT_DURING_ACTIVE_CYCLE` | `GATE_FAIL_STATE_REVERT_DURING_ACTIVE_CYCLE` | **PASS** |
| 9 (`test9_revert_no_cycle.log`) | `GATE_FAIL_STATE_REVERT_NO_CYCLE` | `GATE_FAIL_STATE_REVERT_NO_CYCLE` | **PASS** |
| 10 (`test10_corrupted_state.log`) | `GATE_FAIL_STATE_CORRUPTED` | `GATE_FAIL_STATE_CORRUPTED` | **PASS** |
| 11 (`test11_malformed_activator.log`) | `GATE_FAIL_2_7_ACTIVATOR_INTEGRITY` | `GATE_FAIL_2_7_ACTIVATOR_INTEGRITY` | **PASS** |
| 12 (`test12_tampered_revert.log`) | `GATE_FAIL_2_8_REVERT_NOT_BYTE_IDENTICAL` | `GATE_FAIL_2_8_REVERT_NOT_BYTE_IDENTICAL` | **PASS** |

Each log includes human-readable context on subsequent lines (e.g., test 11 includes `expected_prefix=4EF900071C78` — the activator byte prefix that should embed the resolved helper address at `0x00071C78`).

**Outcome: 9/9 PASS.**

---

## Item 3 — End-to-end BM-001 cycle byte-identity (Build 0066 == Build 0062)

**Claim:** Test 13's revert build (Build 0066) is byte-identical to the canonical baseline (Build 0062).

**Method:** compute SHA256 of both ROMs and compare.

**Evidence:**
- Build 0062 SHA256 (canonical baseline): `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Build 0066 SHA256 (Test 13 Revert): `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- **Match: YES (bytes identical).**
- Build 0065 SHA256 (Test 13 Insert): `501fbce58fc8ee6b2354e6ed8f390500a7895b81a95d7c6d0a95d8d60f2094bb` — differs from canonical, as expected for a diagnostic build with an active activator at `0x055948`.

**Test 13 log corroboration (`test13_revert_make.log` tail):**
- `GATE_PASS`
- `Numbered name verified: rastan_direct_video_test_build_0066.bin`
- `State context: authorized_revert` — gate correctly classified Revert mode

**Test 13 Insert log corroboration (`test13_insert_make.log` tail):**
- `Numbered name verified: rastan_direct_video_test_build_0065.bin`
- `State context: diagnostic` — gate correctly classified diagnostic mode

**Outcome: PASS.** Build 0066 is byte-identical to Build 0062; §2.8 byte-identical check fired and passed.

---

## Item 4 — State file lifecycle

**Claim:** the state file is written during Insert with expected fields, read by gate during Revert, deleted after successful Revert.

**Method:** verify (a) state file currently absent (post-cycle clean-up), (b) preserved snapshot in test artifacts shows expected schema, (c) test 13 logs show Revert classification proceeded.

**Evidence:**
- Current state file location (`build/rastan-direct/active_bookmark_baseline.json`): **absent** (`ls` returns "No such file or directory"). Post-Revert cleanup successful per `verify_canonical_rom.py:835` `state_file_path.unlink()`.
- Preserved snapshot at `build/rastan-direct/open011_test_artifacts/state_valid_bm001.json` contents (verbatim):
  ```json
  {
    "cycle_id": "BM-001",
    "pre_insert_canonical_rom_sha256": "72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc",
    "pre_insert_build_counter": 62,
    "timestamp": "2026-05-12T19:44:48+00:00"
  }
  ```
  All four required fields per design §2.1 present: `cycle_id`, `pre_insert_canonical_rom_sha256`, `pre_insert_build_counter`, `timestamp`.
- Test 13 Revert log confirms `State context: authorized_revert` — gate read the state file and classified the build correctly.

**Outcome: PASS.** State file lifecycle (write → read → delete) confirmed.

---

## Item 5 — Issue ledger compliance

**Claim:** OPEN-011 still open; no closed issues reopened; no closed IDs reused; CLOSED-001 through CLOSED-008 intact.

**Method:** grep `OPEN_ISSUES.md` and `CLOSED_ISSUES.md` for OPEN-011 and CLOSED-* anchors.

**Evidence:**
- `OPEN_ISSUES.md:248`: `## OPEN-011 — Postpatch invariant model + diagnostic symbol allowlist + gate context-awareness` — **OPEN-011 still open** ✓
- `CLOSED_ISSUES.md:115`: `## CLOSED-008 — Build pipeline determinism / Makefile .incbin dependency completeness` — CLOSED-008 present and unchanged ✓
- No `## OPEN-011` in `CLOSED_ISSUES.md` (Cody did not close OPEN-011) ✓
- No `## CLOSED-009` anywhere (no premature closure) ✓
- CLOSED-001 through CLOSED-008 all present per CLOSED_ISSUES.md header structure (preserved verbatim per current file state)

**Outcome: PASS.** Cody correctly left OPEN-011 in implementation-complete-pending-Tighe-verification state.

---

## Item 6 — Implementation source contains design's load-bearing decisions

**Claim:** the postpatcher and gate source code contain the design's load-bearing decisions (context-aware count invariant, hardcoded DIAGNOSTIC_SYMBOLS, cross-reference consistency, §2.7 activator integrity, §2.8 byte-identical revert).

**Method:** read the line ranges Cody cited and confirm the load-bearing logic is present.

### Postpatcher (`tools/translation/postpatch_startup_rom.py`)

**Lines 16-31 — constants and DIAGNOSTIC_SYMBOLS** (verified present):
```python
ACTIVE_BOOKMARK_BASELINE_PATH = PROJECT_ROOT / "build" / "rastan-direct" / "active_bookmark_baseline.json"
...
CANONICAL_OPCODE_REPLACE_COUNT = 94
CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CAEC

# DIAGNOSTIC_SYMBOLS — symbols that are always resolvable for {symbol:NAME}
# template substitution, independent of the spec's required_symbols allowlist.
# ... three-place friction comment block ...
DIAGNOSTIC_SYMBOLS = ("genesistan_diag_bookmark",)
```
Matches design §4 verbatim including the three-place friction comment block. ✓

**Lines 74-207 — `_diagnostic_bookmarks` parser + cross-reference consistency validator** (verified present):
- Line 74: `def _diagnostic_bookmarks(spec)` parser ✓
- Line 101+: validator that returns `(is_diagnostic, len(diagnostic_bookmarks), sigma)` ✓
- Line 106-108: single-entry constraint enforced (rejects multi-entry per design §10 Ambiguity 6) ✓
- Lines 130-204: cross-reference consistency checks (cycle_id matching between `diagnostic_bookmarks` and `bookmark_cycle`-tagged opcode_replace entries; target_arcade_pc consistency; orphan detection in both directions) ✓
- Line 207: returns Σ computed from activator span lengths (no static drift surface per design §3, Ambiguity 3) ✓

**Lines 211-230 — state file write during Insert** (verified present):
- `_atomic_write_json(ACTIVE_BOOKMARK_BASELINE_PATH, payload)` writes state file atomically with required fields ✓

**Lines 1845-1858 — context-aware count invariant** (verified present):
```python
if expected_opcode_replace_count is not None:
    expected_count = int(expected_opcode_replace_count)
    if is_diagnostic_mode:
        expected_count += diagnostic_count
    ...
    if applied_count != expected_count:
        raise RuntimeError(f"Expected {expected_count} opcode replacements but applied {applied_count}.")
```
Canonical baseline preserved as constant; diagnostic mode adds `diagnostic_count` (N) per design §3.1 formula. ✓

### Gate (`tools/translation/verify_canonical_rom.py`)

**Lines 13-29 — all failure IDs present** (verified present):
- Lines 13-21: original six checks (FAIL_2_1 through FAIL_2_8) plus FAIL_2_5_CROSS_REF ✓
- Lines 23-29: seven new state-mode failure IDs (FAIL_STATE_ORPHANED_SPEC, FAIL_STATE_ORPHANED_FILE, FAIL_STATE_MISMATCH, FAIL_STATE_REVERT_CONTEXT_MISMATCH, FAIL_STATE_REVERT_DURING_ACTIVE, FAIL_STATE_REVERT_NO_CYCLE, FAIL_STATE_CORRUPTED) ✓

All 10 new failure IDs Cody claimed (per implementation doc) match the actual constants in source.

**Lines 372+ — state file parser** (verified present):
- `read_state_file(path: Path) -> StateFile | None` at line 372 ✓

**Lines 436-479 — truth-table resolver** (verified present):
- Line 436: ORPHANED_SPEC condition
- Line 444: STATE_MISMATCH condition (cycle_id mismatch)
- Line 453: ORPHANED_FILE — `"active_bookmark_baseline.json exists but diagnostic_bookmarks is empty and no explicit revert context provided."` — **explicit revert context language confirms Chad's refinement** ✓
- Line 461: REVERT_CONTEXT_MISMATCH
- Line 479: REVERT_NO_CYCLE

**Lines 823-842 — §2.8 byte-identical revert + atomic delete** (verified present):
- Line 823: `def check_revert_byte_identical(rom, state, state_file_path)` ✓
- Line 829: error message `"Authorized revert failed byte-identical check."` ✓
- Line 835: `state_file_path.unlink()` — state file deleted after successful Revert ✓
- Line 841: failure-to-delete error message ✓

**Lines 860-920 — CLI args, state file resolution, main flow** (verified present):
- Line 860: `parser.add_argument("--bookmark-revert", default="")` — explicit revert context arg ✓
- Lines 876-879: state file path resolution (configurable via `--state-file` or default) ✓
- Line 897: state file read in main flow ✓
- Line 920: `check_revert_byte_identical` invocation in main flow ✓

**Outcome: PASS.** All design §2-§6 load-bearing decisions are present in source with correct intent.

---

## Item 7 — Revert context mechanism explicit (not inferred)

**Claim:** the gate requires an explicit `--bookmark-revert BM-NNN` argument for any Revert classification; presence of state file plus empty `diagnostic_bookmarks` alone does not auto-classify as Revert (Chad's refinement).

**Method:** read Makefile + gate script + truth-table resolver and confirm the mechanism is explicit.

**Evidence:**

**Makefile (`apps/rastan-direct/Makefile`):**
- Line 20: `BOOKMARK_REVERT ?=` — Makefile variable, default empty ✓
- Line 158: `--bookmark-revert "$(BOOKMARK_REVERT)" \` — passed through to gate invocation ✓

When `make` is invoked without `BOOKMARK_REVERT=BM-NNN`, the gate receives an empty `--bookmark-revert` value, which the truth-table resolver interprets as "no explicit revert context."

**Gate (`tools/translation/verify_canonical_rom.py`):**
- Line 860: `parser.add_argument("--bookmark-revert", default="")` — accepts the empty default ✓
- Lines 436-489 (truth-table resolver): the four state-context branches handle:
  - empty `diagnostic_bookmarks` + state file present + no `--bookmark-revert` → `GATE_FAIL_STATE_ORPHANED_FILE` (line 453 message: `"active_bookmark_baseline.json exists but diagnostic_bookmarks is empty and no explicit revert context provided."`) — **the gate refuses to silently classify as Revert without explicit context** ✓
  - empty `diagnostic_bookmarks` + state file present + `--bookmark-revert` matches state's cycle_id → authorized Revert (line 461 mismatch error confirms the equality check is performed) ✓
  - empty `diagnostic_bookmarks` + no state file + `--bookmark-revert` provided → `GATE_FAIL_STATE_REVERT_NO_CYCLE` (line 479) ✓
  - non-empty `diagnostic_bookmarks` + `--bookmark-revert` provided → `GATE_FAIL_STATE_REVERT_DURING_ACTIVE_CYCLE` — Revert context cannot apply during an active Insert ✓

**Test artifact corroboration:**
- Test 4 log first line: `GATE_FAIL_STATE_ORPHANED_FILE` followed by `active_bookmark_baseline.json exists but diagnostic_bookmarks is empty and no explicit revert context provided.` — confirms the gate explicitly refuses to infer Revert from state-file presence alone ✓
- Test 13 Revert log: `State context: authorized_revert` only after the Makefile passed `BOOKMARK_REVERT=BM-001` through to the gate (per Cody's test setup; the build counter advance from 65 to 66 confirms the build succeeded) ✓

**Chad's refinement confirmed:** "Revert must be explicit. The gate must not infer an authorized Revert solely from state-file presence plus empty `diagnostic_bookmarks`." The implementation enforces exactly this: the empty `--bookmark-revert` default results in `GATE_FAIL_STATE_ORPHANED_FILE`, which is the safe failure mode if someone removes the activator from spec without authorizing the Revert.

**Outcome: PASS.** Revert context is explicit at every layer (Makefile → gate CLI arg → truth-table resolver). No inference path exists.

---

## Summary table

| Item | Verification subject | Outcome |
|---|---|---|
| 1 | Spec integrity (SHA match) | PASS |
| 2 | Failure ID coverage (9 tests) | PASS (9/9) |
| 3 | Build 0066 == Build 0062 (byte-identical) | PASS |
| 4 | State file lifecycle | PASS |
| 5 | Issue ledger compliance | PASS |
| 6 | Implementation alignment with design | PASS |
| 7 | Revert context explicit (not inferred) | PASS |

**All seven items PASS. No discrepancies found.**

---

## What this verification does NOT prove

- Behavioral correctness when targeting a REAL arcade address (BM-001 against `0x055948` as a research task): Test 13 used a synthetic target. Behavioral evidence (whether MAME/Exodus actually reaches the helper) comes from real bookmark cycles.
- Long-term stability under repeated cycles: the test matrix exercises insert/revert once each. Compounded usage (multiple BM-NNN cycles in succession) is unproven here but architecturally supported (single-entry constraint per cycle, byte-identical revert returns ROM to baseline ready for next cycle).
- That `genesistan_diag_bookmark` is actually reached: that's exactly what BM-001 as a research task is designed to test, after OPEN-011 closes.

These are out-of-scope for OPEN-011 closure. They're operational concerns for the bookmark-cycle research phase that follows OPEN-011's closure.

---

## Recommendation to Tighe

OPEN-011 is closeable as CLOSED-009. The diagnostic bookmark postpatch invariant mechanism is implemented per Andy's design with Chad's explicit-revert-context refinement. All test artifacts and source align with the design's load-bearing decisions. The canonical invariant remains strict for canonical builds; diagnostic builds get context-aware treatment via the `diagnostic_bookmarks` spec field; `required_symbols` allowlist remains principled via the hardcoded `DIAGNOSTIC_SYMBOLS` tuple with three-place friction; Revert context is explicit at every layer.

After closure, the next operational task is the first real bookmark cycle (BM-001 Insert at the chosen target arcade_pc, evidence collection in MAME and/or Exodus, BM-001 Revert producing a canonical ROM byte-identical to the most-recent canonical baseline). That research task is separate from OPEN-011 closure.
