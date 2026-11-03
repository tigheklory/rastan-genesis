# Cody rastan-direct Patcher Reuse and Extension

## 1. Executive Summary
The existing Python postpatch pipeline was reused and extended to support `apps/rastan-direct` without replacing the patcher architecture. The authoritative patch entrypoint remains `tools/translation/postpatch_startup_rom.py`. A new `rastan_direct` spec profile was added and wired into the `rastan-direct` Makefile so builds run relocation and opcode patching automatically.

## 2. Existing Patcher Toolchain Audit
- Authoritative patch entrypoint for ROM post-build patching: `tools/translation/postpatch_startup_rom.py`.
- Parallel lenient variant exists: `tools/translation/postpatch_lenient.py`.
- Shift-table support is integrated into postpatch via `tools/translation/shift_table_patcher.py`.
- Spec consumption is JSON-driven with the same contract style as `specs/startup_title_remap.json`:
  - `policy`
  - `whole_maincpu_copy`
  - `rom_absolute_call_relocation`
  - `opcode_replace` / `rom_opcode_replace`
  - symbol-token replacement syntax `{symbol:name}`.
- Symbol resolution uses symbol table parsing from a linker/nm symbol file and enforces `required_symbols`.
- Existing blocker for `rastan-direct` before this change: hardcoded startup-title assumptions in `postpatch_startup_rom.py` (`genesistan_run_original_startup_common` UI-only branch and mandatory `generated_stubs` handling).

## 3. What Was Reused vs Extended
### Reused
- Existing patch engine (`postpatch_startup_rom.py`) including:
  - whole-maincpu relocation
  - absolute ROM target relocation scan
  - opcode replacement with original-byte guards
  - symbol token expansion and strict symbol resolution
  - checksum update and manifest generation.

### Extended
- Added a spec-driven profile switch (`policy.patcher_profile`) with new `rastan_direct` behavior in the same patcher.
- Added expectation enforcement (`expectations.opcode_replace_count`) to prevent silent patch skips.
- Added direct-execution manifest reporting (`direct_execution.entry_symbol` resolution).
- Added `specs/rastan_direct_remap.json` for direct-branch patch requirements.
- Added `apps/rastan-direct/Makefile` patcher invocation and symbol export wiring.

No replacement patcher was introduced.

## 4. Exact Files Modified
- `tools/translation/postpatch_startup_rom.py`
- `specs/rastan_direct_remap.json` (new)
- `apps/rastan-direct/Makefile`
- `apps/rastan-direct/src/main_68k.s`

### Exact symbols/functions/labels added or changed
- `postpatch_startup_rom.py`
  - Added profile selection: `policy.patcher_profile` with `rastan_direct` branch.
  - Added opcode replacement expectation check (`expectations.opcode_replace_count`).
  - Added direct-execution manifest fields and direct relocation-map mode.
  - Preserved default startup-title flow when profile is not `rastan_direct`.
- `main_68k.s`
  - Added globals for patch resolution:
    - `genesistan_hook_tilemap_plane_a`
    - `genesistan_shadow_input_390001`
    - `genesistan_shadow_input_390003`
    - `genesistan_shadow_input_390005`
    - `genesistan_shadow_input_390007`
    - `genesistan_shadow_dip1`
    - `genesistan_shadow_dip2`
    - `rastan_direct_arcade_tick_entry` (absolute symbol at `0x0003A208`)
  - Added minimal hook stub label:
    - `genesistan_hook_tilemap_plane_a: rts`

## 5. rastan-direct Integration Changes
- `apps/rastan-direct/Makefile` now:
  - exports symbol file via `m68k-elf-nm` (`out/symbol.txt`)
  - runs `tools/build_rastan_regions.py` to produce `build/regions/maincpu.bin`
  - invokes existing `tools/translation/postpatch_startup_rom.py` with:
    - `--spec specs/rastan_direct_remap.json`
    - `--maincpu build/regions/maincpu.bin`
    - `--rom apps/rastan-direct/dist/rastan_direct_video_test.bin`
    - `--symbols apps/rastan-direct/out/symbol.txt`
    - `--manifest build/rastan-direct/rastan_direct_patch_manifest.json`

## 6. Symbol Resolution Strategy Chosen
Chosen strategy: **reuse legacy SGDK-era symbol names for compatibility**.

Implemented by defining compatible symbol names directly in `apps/rastan-direct/src/main_68k.s` so existing spec/token conventions continue to work without introducing a separate naming model.

## 7. Supported rastan-direct Patch Use Cases
Implemented in `specs/rastan_direct_remap.json`:
- Arcade ROM relocation: full `maincpu` copy to `0x000200`.
- Symbol-resolved TC0040IOC shadow-input rewrites:
  - `0x03A4A2`, `0x03A4A8`, `0x03A778`, `0x03A77E`
  - `0x03A0A8`, `0x03A0B2`, `0x03A0C0`
  - `0x03A490`, `0x03AC04`
- BG hook patch symbol at `0x055968`:
  - `JSR genesistan_hook_tilemap_plane_a` with size-preserving NOP pad.
- Direct-execution symbol resolution report:
  - `rastan_direct_arcade_tick_entry` resolved via symbol file.
- Guard behavior retained:
  - original-bytes verification for each `opcode_replace` entry.

## 8. Verification Performed
- Built `rastan-direct` with integrated patch pipeline:
  - `make -C apps/rastan-direct`
- Verified patch artifacts generated:
  - `apps/rastan-direct/dist/rastan_direct_video_test.bin`
  - `build/rastan-direct/rastan_direct_patch_manifest.json`
  - `build/rastan-direct/startup_common_relocations.json`
- Verified manifest fields:
  - `patcher_profile = rastan_direct`
  - `opcode_replace_and_rom_opcode_replace = 10`
  - `expectations.opcode_replace_count = 10`
  - `direct_execution.entry_symbol_address = 0x0003A208`
- Verified patched ROM bytes at relocated offsets include expected symbol-resolved targets.

## 9. Backward Compatibility Impact
- Existing startup-title behavior remains default when `policy.patcher_profile` is absent or not `rastan_direct`.
- No existing startup-title spec fields were removed.
- No existing patch entrypoint was replaced.
- `postpatch_lenient.py` was not altered in this task; primary compatibility was preserved in the authoritative `postpatch_startup_rom.py` path.

## 10. Risks / Known Limitations
- This task integrates patcher capability and wiring only; it does not implement full arcade gameplay correctness in `rastan-direct`.
- `genesistan_hook_tilemap_plane_a` is currently a symbol-resolvable stub; full BG producer behavior is outside this task.
- TC0040IOC shadow symbols are wired for patch resolution; full runtime input update behavior remains outside this task.

## 11. Final Verdict
The existing Python patcher lineage was successfully reused and extended for `rastan-direct` with integrated build wiring, strict symbol-resolved patch application, guarded opcode replacement, and verified output artifacts.

## Permanent vs Temporary Classification
- PERMANENT:
  - `postpatch_startup_rom.py` `rastan_direct` profile support
  - `specs/rastan_direct_remap.json`
  - `apps/rastan-direct/Makefile` patcher wiring
  - `main_68k.s` compatibility symbol exports required by the patch spec
- TEMPORARY: none added
- DIAGNOSTIC: none added
- BRINGUP_ONLY: none added in this task

## Scaffolding Inventory
- No temporary scaffolding/helpers were added.

## Removal / Revert Plan
- No revert planned for patcher profile and wiring; this is foundational integration.
- If rollback is required, remove `rastan_direct` profile branch from `postpatch_startup_rom.py`, remove `specs/rastan_direct_remap.json`, and remove patcher invocation from `apps/rastan-direct/Makefile`.

## Build Artifact Path
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

## Verification Status
- Patcher run: PASS
- Symbol resolution: PASS
- Output ROM generation: PASS

