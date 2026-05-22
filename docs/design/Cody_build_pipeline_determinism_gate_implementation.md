# Cody Build Pipeline Determinism Gate Implementation

## Summary

Implemented Andy's gate design from `docs/design/Andy_build_pipeline_determinism_gate_design.md` as production build infrastructure.

- Gate script added: `tools/translation/verify_canonical_rom.py`
- Makefile integration added inside `$(BIN)` after postpatcher/disasm and before numbered copy
- `.DELETE_ON_ERROR:` active in Makefile
- Build counter increment moved to post-gate
- Canonical helper SHA wired as Makefile arg
- Validated against known-good Build 0061, known-bad Build 0060, synthetic regressions, end-to-end failure semantics, and canonical Build 0062 generation

## Failure ID Table

| Check | Failure ID |
|---|---|
| §2.1 Embedded `.incbin` byte-match | `GATE_FAIL_2_1_INCBIN_SHA_MISMATCH` |
| §2.2 Helper integrity | `GATE_FAIL_2_2_HELPER_SHA_MISMATCH` |
| §2.3 Postpatcher invariant delegation | `GATE_FAIL_2_3_POSTPATCHER_INVARIANT` |
| §2.4 ROM naming compliance | `GATE_FAIL_2_4_ROM_NAMING` |
| §2.5 Symbol resolution | `GATE_FAIL_2_5_SYMBOL_RESOLUTION` |
| §2.6 Makefile `.incbin` dependency audit | `GATE_FAIL_2_6_DEPENDENCY_AUDIT` |

## Gate Script Structure

Path: `tools/translation/verify_canonical_rom.py`

Implemented checks per Andy design:

1. §2.1 scans `apps/rastan-direct/src/*.s` for `.incbin`, finds anchor symbol, hashes on-disk artifact vs ROM embedded region at symbol offset.
2. §2.2 checks `genesistan_diag_bookmark` bytes are `60 FE` and SHA256 matches canonical helper SHA.
3. §2.3 parses expected postpatcher invariant constants from `tools/translation/postpatch_startup_rom.py` and validates manifest opcode_replace counts against expected patched-site count.
4. §2.4 validates numbered artifact name format and strict sequential number vs `build_counter.txt` (counter + 1).
5. §2.5 validates symbol-template resolution from `specs/rastan_direct_remap.json` and ROM-bounds for gate-critical symbols.
6. §2.6 audits Makefile dependencies: every `.incbin` in each `.s` must appear in corresponding `.o` rule dependencies.

Notes:
- `.incbin` path resolution is intentionally relative to assembler working directory (`apps/rastan-direct`), matching build behavior.
- Failure output is machine-readable ID first line, then evidence lines.

## Makefile Integration

File: `apps/rastan-direct/Makefile`

Changes:
- Added `CANONICAL_GATE := $(ROOT)/tools/translation/verify_canonical_rom.py`
- Added `HELPER_CANONICAL_SHA ?= 20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb`
- Added `.DELETE_ON_ERROR:`
- In `$(BIN)` recipe:
  - computes `next = counter + 1` and `numbered_name` first
  - runs gate script with all required args
  - only on gate pass: writes updated counter, copies numbered ROM, runs trace capture

Result: failed gate no longer consumes build numbers.

## Phase 3 Unit Tests

### 3.1 Build 0061 pass (known-good baseline)

Command target:
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0061.bin`
- Numbered name checked: `rastan_direct_video_test_build_0062.bin`

Result: `GATE_PASS`

### 3.2 Build 0060 fail (known-bad stale linkage baseline)

Command target:
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0060.bin`

Result:
- `GATE_FAIL_2_1_INCBIN_SHA_MISMATCH`
- Cited mismatch example:
  - Symbol `genesistan_pc080sn_tile_vram_lut`
  - Expected SHA `ca9c3dcf...`
  - Found SHA `9f2f2e8e...`

## Phase 4 Integration Test

Ran gate with the same invocation shape as Makefile recipe on existing `apps/rastan-direct/dist/rastan_direct_video_test.bin` (which matched Build 0061 SHA).

Result: `GATE_PASS`

## Phase 5 Synthetic Regression Matrix

### 5.1 Stale-object scenario (Build 60-class) — REQUIRED

Method used:
- Created temporary ROM copy of Build 0061 at `/tmp/..._stale_sim.bin`
- Overwrote LUT region (`0x0F1EC0`, 32768 bytes) with stale bytes from Build 0060
- Did not modify source-of-truth generated artifacts

Result:
- `GATE_FAIL_2_1_INCBIN_SHA_MISMATCH`
- Mismatch detected on `genesistan_pc080sn_tile_vram_lut` with expected/found SHA divergence.

### 5.2 Helper corruption simulation

Method used:
- Passed intentionally wrong `--helper-canonical-sha` argument (all zeros)

Result:
- `GATE_FAIL_2_2_HELPER_SHA_MISMATCH`
- Report included observed bytes `60FE`, observed helper SHA, expected bogus SHA.

### 5.3 Missing Makefile dependency simulation

Method used:
- Temporarily removed `pc080sn_attr_lut.bin` dependency from `scene_load.o` rule
- Ran gate
- Restored Makefile immediately

Result:
- `GATE_FAIL_2_6_DEPENDENCY_AUDIT`
- Report cited missing dependency and source location (`scene_load.s:105`).

### 5.4 ROM naming violation simulation

Method used:
- Passed invalid numbered name `rastan_direct_video_test_build_0062a.bin`

Result:
- `GATE_FAIL_2_4_ROM_NAMING`

### 5.5 End-to-end failure semantics test (Make path)

Method used:
- Ran full `make -C apps/rastan-direct` with overridden bad helper SHA (`HELPER_CANONICAL_SHA=00...00`) to force gate failure inside `$(BIN)` recipe.

Observed behavior:
- Build reached gate and failed with `GATE_FAIL_2_2_HELPER_SHA_MISMATCH`
- Make aborted with non-zero exit
- `.DELETE_ON_ERROR` removed target `dist/rastan_direct_video_test.bin`
- No numbered `0062` artifact created
- `build/rastan-direct/build_counter.txt` remained `61` (no increment)

All synthetic changes were reverted.

## Phase 6 Canonical Build 0062 Under Gate

Build command:
- `make -C apps/rastan-direct`

Output:
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0062.bin`
- Gate output during build: `GATE_PASS`
- Counter after build: `62`

### Canonical checks

- Build 0062 ROM SHA256: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Build 0061 ROM SHA256: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Relation: byte-identical

Helper:
- Symbol `genesistan_diag_bookmark` resolved at `0x00071C78`
- Bytes at address: `60 FE`
- Helper SHA: `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb`

Postpatch invariants:
- Source assertion unchanged: `total_genesis_bytes_covered=0x17CAEC`, `patched_site=94` (`postpatch_startup_rom.py:1757-1763`)
- Manifest `opcode_replace` entry count: `94`

Embedded region SHAs (`0062` vs on-disk artifacts vs `0061`): all match
- LUT: `ca9c3dcf...`
- Attr LUT: `2614c7b4...`
- Tile ROM: `a33372eb...`
- Title preload: `e0a814f2...`
- Gameplay preload: `462c428c...`
- Endround preload: `690835b8...`

## Outcome

Gate is now active inside the sanctioned ROM-producing path and blocks Build 60-class stale-linkage regressions.

OPEN-010 implementation portion is complete; closure remains a supervisor decision.
