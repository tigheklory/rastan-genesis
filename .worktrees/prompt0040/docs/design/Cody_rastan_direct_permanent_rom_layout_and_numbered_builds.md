# Cody rastan-direct permanent ROM layout and numbered builds

## 1. Executive Summary
Implemented a permanent `rastan-direct` ROM layout migration that keeps only bootstrap content in low ROM (`0x000000..0x0003FF`) and moves Genesis wrapper/support code to high ROM (`0x00070000+`). This removes dependence on wrapper code fitting under the low preserved boundary. Numbered build artifacts were restored with monotonic incrementing IDs.

## 2. Root Cause Reference
References:
- `docs/design/Andy_vblank_interrupt_block_diagnosis.md`
- `docs/design/Cody_rastan_direct_final_rom_boot_byte_fix.md`

Root cause class: Genesis wrapper code previously lived in the low ROM overlap zone and crossed past `0x0003FF`, so relocated arcade ROM could overwrite live wrapper instructions.

## 3. Old Fragile ROM Layout
Old layout behavior:
- `link.ld` placed `.text.boot` and `.text` together at ROM base `0x000000`.
- Wrapper routines (`main_68k`, `_VINT_handler`, VDP commit helpers) occupied low addresses around `0x0002xx..0x0004xx`.
- Patcher preserved low ROM `0x000000..0x0003FF` only.
- Any wrapper growth beyond `0x0003FF` was vulnerable to arcade ROM overwrite after relocation copy to `0x000200..`.

## 4. New Permanent ROM Ownership Model
Ownership zones now:
1. Low ROM bootstrap zone (`0x000000..0x0003FF`)
- vectors, header, `_default_handler`, `_start`
- no full wrapper runtime lives here

2. Relocated arcade ROM zone
- unchanged concept: `0x000200..0x060200` via whole-maincpu relocated copy

3. Safe high-ROM Genesis wrapper zone (`0x00070000..`)
- `main_68k`
- `_VINT_handler`
- VDP helpers/commit routines
- input update and hook support routines
- wrapper-side support code

## 5. Exact Addresses / Regions Chosen
- Low bootstrap preserve window: `0x000000..0x0003FF`
- Genesis wrapper base: `0x00070000`
- Observed symbols after migration:
  - `main_68k = 0x00070000`
  - `_VINT_handler = 0x00070024`
  - `genesistan_hook_tilemap_plane_a = 0x00070126`
  - `vdp_commit_scroll = 0x000701AA`

## 6. Exact Files Modified
- `apps/rastan-direct/link.ld`
- `apps/rastan-direct/Makefile`
- `tools/translation/verify_rastan_direct_boot_guard.py`
- `tools/translation/postpatch_startup_rom.py`
- `docs/design/Cody_rastan_direct_permanent_rom_layout_and_numbered_builds.md`
- `AGENTS_LOG.md`

## 7. Bootstrap-to-Wrapper Control Flow
- Reset vector still points to `_start` in low ROM (`0x000202`).
- `_start` executes low bootstrap init and performs `jsr main_68k`.
- `main_68k` now resolves to high ROM (`0x00070000`).
- VBlank vector points directly to high-ROM `_VINT_handler` (`0x00070024`).

## 8. Patcher / Preserve-Region Implications
- Patcher lineage remains unchanged (`postpatch_startup_rom.py` is still authoritative).
- Preserved low ROM region remains deliberate and small: `0x000000..0x0003FF`.
- Manifest now explicitly records low bootstrap ownership (`preserved_low_rom_bootstrap`) for `rastan_direct` while preserving existing manifest compatibility keys.
- Wrapper correctness no longer depends on extending low preserve size, because wrapper code is no longer placed in that zone.

## 9. Numbered Build Artifact Scheme
Canonical latest ROM path:
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

Numbered archive path:
- `dist/rastan-direct/rastan_direct_video_test_build_####.bin`

Monotonic counter path:
- `build/rastan-direct/build_counter.txt`

Rule:
- each successful `rastan-direct` build that executes the `$(BIN)` recipe archives a numbered copy and increments counter monotonically.

Exodus usage:
- use canonical latest ROM for normal iteration: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- use numbered archive artifacts for pinned regression testing.

## 10. Verification Performed
1. Clean build:
- `source tools/setup_env.sh && make -C apps/rastan-direct clean && make -C apps/rastan-direct`
- result: PASS

2. Guard checks:
- prepatch bootstrap guard PASS
- postpatch bootstrap guard PASS

3. Wrapper high-ROM placement:
- symbol table confirms wrapper functions at `0x00070000+`

4. Low-zone overlap class removed:
- low region around old failure addresses (`0x000400+`) no longer hosts wrapper code
- live wrapper bytes verified at high region (`0x00070000`)

5. Numbered artifacts:
- forced rebuild without manual clean: `make -C apps/rastan-direct -B`
- produced `dist/rastan-direct/rastan_direct_video_test_build_0002.bin`
- counter file reports `2`

## 11. Backward Compatibility Impact
- Existing patcher architecture preserved.
- Existing `rastan_direct` spec/profile preserved.
- Startup-title/non-`rastan_direct` behavior unchanged.
- Runtime/gameplay logic was not redesigned in this migration.

## 12. Risks / Known Limitations
- Linker still emits a LOAD-segment RWX warning (existing linker-permissions concern; unrelated to this migration).
- Numbered archive generation occurs when `$(BIN)` is rebuilt; no new numbered archive is emitted when make is fully up-to-date.

## 13. Final Verdict
Permanent layout migration is complete: low ROM now contains only bootstrap ownership, Genesis wrapper/support code moved to safe high ROM, fragile low-ROM wrapper overlap class eliminated, and numbered build artifacts restored.

## 14. Summary
Permanent layout correction and numbered artifact restoration were implemented with no gameplay/runtime redesign.

## 15. Exact Symbols / Functions / Labels Added or Changed
- `link.ld` output sections changed:
  - `.text.boot` remains low at `0x000000`
  - `.text.wrapper` added at `0x00070000`
- Makefile symbols/vars added:
  - `NUMBERED_DIST_DIR`
  - `NUMBERED_COUNTER`
  - `NUMBERED_PREFIX`
- Guard logic changed in `verify_rastan_direct_boot_guard.py` to validate bootstrap invariants and high-wrapper VBlank vector.
- Manifest metadata in patcher includes `preserved_low_rom_bootstrap`.

## 16. Permanent vs Temporary Classification
- PERMANENT:
  - high-ROM wrapper linker placement
  - low-bootstrap-only ownership model
  - bootstrap guard checks
  - numbered build artifact archiving and monotonic counter
- TEMPORARY: none
- DIAGNOSTIC: none
- BRINGUP_ONLY: none

## 17. Scaffolding Inventory
- No temporary or diagnostic scaffolding was added.

## 18. Removal / Revert Plan
- No revert planned; this is a permanent architecture correction.
- If rollback is required, revert linker/Makefile/guard changes together to avoid mixed ownership states.

## 19. Build Artifact Path
- Canonical latest: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Numbered archive: `dist/rastan-direct/rastan_direct_video_test_build_0002.bin` (latest during verification)

## 20. Verification Status
- Build: PASS
- Low bootstrap guard (pre/postpatch): PASS
- High wrapper placement verified: PASS
- Numbered archive output: PASS
