# Cody — BM-001 Bookmark Insert (Research Cycle)

## Scope
Real BM-001 insert cycle using operational bookmark infrastructure from CLOSED-009.

## Phase 1 — Activator Representation Derivation
Sources consulted:
- `docs/design/Andy_diagnostic_bookmark_postpatch_invariant_design.md` (§2.1, §2.2, §5.1)
- `tools/translation/postpatch_startup_rom.py` (`_validate_bookmark_cross_reference`)
- `tools/translation/verify_canonical_rom.py` (`validate_bookmark_cross_reference`, `check_activator_integrity`)
- `specs/rastan_direct_remap.json` current schema

Derived coupled entries:
- Top-level `diagnostic_bookmarks` entry with fields: `cycle_id`, `target_arcade_pc`, `pre_insert_canonical_bytes`, `pre_insert_canonical_rom_sha256`, `linked_opcode_replace_index`.
- `opcode_replace` activator entry with `arcade_pc`, `original_bytes`, `replacement_bytes`, and `bookmark_cycle`.

Pre-insert canonical bytes evidence:
- Build 0062 ROM offset for `arcade_pc 0x055948` is `0x055B48` (`+0x200` relocation window).
- Observed bytes in Build 0062: `0c6d000010a8660a`.

Cross-reference consistency:
- `diagnostic_bookmarks[0].cycle_id = BM-001`
- `diagnostic_bookmarks[0].linked_opcode_replace_index = 94`
- `opcode_replace[94].bookmark_cycle = BM-001`

## Phase 2 — Spec Modification
Two entries added in `specs/rastan_direct_remap.json`:
1. `diagnostic_bookmarks[0]` for BM-001
2. `opcode_replace[94]` activator at `arcade_pc 0x055948`

No other spec fields changed.

## Phase 3 — Build 0067 Under Gate
Build command:
- `source tools/setup_env.sh && make -C apps/rastan-direct release`

Results:
- Build succeeded.
- Gate output: `GATE_PASS`, `State context: diagnostic`.
- Numbered ROM emitted: `dist/rastan-direct/rastan_direct_video_test_build_0067.bin`.
- ROM SHA256: `501fbce58fc8ee6b2354e6ed8f390500a7895b81a95d7c6d0a95d8d60f2094bb`.

Postpatch/gate invariants:
- Manifest `build_context`: `diagnostic`
- Expected patched sites (manifest): `95`
- Observed patched sites (address_map): `95`
- Expected coverage (manifest): `0x17CAF4`
- Observed coverage (address_map): `0x17CAF4`

Helper integrity:
- Build 0067 bytes at `0x00071C78`: `60fe`
- Helper SHA256: `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb` (canonical match)

Activator placement:
- Build 0067 bytes at target (`0x055B48`): `4ef900071c784e71`
- Expected pattern: `4EF9 <helper-address> 4E71`

State file:
- `build/rastan-direct/active_bookmark_baseline.json` exists.
- Contains `cycle_id=BM-001`, canonical SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`, `pre_insert_build_counter=66`, timestamp.

## Phase 4 — MAME Trace and Reachability Classification
Trace mechanism:
- Makefile `$(BIN)` recipe auto-runs 30-second trace command and saves to `states/traces/...`.

Trace artifact used:
- Source: `states/traces/rastan_direct_video_test_build_0067_mame_30s_20260513_121320/genesis_exec_trace.log`
- Copied to required location: `dist/rastan-direct/bookmarks/build_0067_pc_0x055948/mame_run_log.txt`

Trace currency verification:
- Same make invocation produced Build 0067 and trace artifacts.
- Trace log mtime is newer than Build 0067 ROM mtime.

Outcome:
- **Outcome B — Helper not reached within trace window.**
- Evidence:
  - 30-second window used by Makefile command.
  - `frames=1798` in `genesis_exec_summary.txt`.
  - No occurrences of `0x00071C78` / `071c78` in trace log.

## Phase 5 — Output Artifacts
Created:
- `dist/rastan-direct/bookmarks/build_0067_pc_0x055948/insert_meta.txt`
- `dist/rastan-direct/bookmarks/build_0067_pc_0x055948/mame_run_log.txt`
- `dist/rastan-direct/bookmarks/build_0067_pc_0x055948/NOTES.md`

This task intentionally does not perform Revert. Immediate next ROM-producing task must be BM-001 Revert.
