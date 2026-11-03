# Cody - PC080SN Native YM7101 Implementation Result

> **HISTORICAL BUILD REPORT (banner added 2026-07-28):** This is preserved build/failure evidence. Its facts (builds, SHAs, results) are **unchanged**. The graphics architecture it describes is governed and, where it conflicts, **superseded** by the canonical `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (and `RULES.md` §11). Read the policy before using this as an architecture reference.


**Date:** 2026-07-27  
**Type:** Production implementation + candidate build  
**Candidate ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0239.bin`  
**SHA-256:** `f1d6075c801f8a0326084edec79c2850decc26f8569abc2a7eb1328b8677813b`  
**Size:** `1588624` bytes  
**Counter after build:** `239`

## 1. Accepted Baseline And Authority Order

Accepted functional baseline was Build 0235:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`
- SHA-256: `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`
- Pre-edit counter: `238`
- Builds 0235, 0236, 0237, and 0238 were present before editing and remained preserved after Build 0239.

Authority order used:

1. User implementation prompt.
2. `RULES.md` and `ARCHITECTURE.md`.
3. `docs/design/Cody_pc080sn_native_ym7101_global_fill_vertical_streaming_contract.md`.
4. Current `apps/rastan-direct/` production source and Makefile.
5. `specs/rastan_direct_remap.json`.
6. `build/rastan-direct/address_map.json`.
7. `docs/arcade_reference/pc080sn/`.
8. Build 0235 as regression evidence.

Production source and Makefile matched the accepted Build 0235 functional baseline before editing. Existing documentation/log dirtiness from proof passes was preserved.

## 2. Files And Production Paths Changed

Production source changed:

- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/boot/boot.s`

Build/verification tooling changed:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Generated artifacts changed by the normal Makefile:

- `apps/rastan-direct/out/*`
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- `build/genesis_postpatch.disasm.txt`
- `build/rastan-direct/address_map.json`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- `build/rastan-direct/build_counter.txt`
- `build/rastan-direct/startup_common_relocations.json`
- `build/rom_inventory.json`
- `build/mame/home/genesistrace/genesis_exec_trace.log`
- `states/traces/rastan_direct_video_test_build_0239_mame_30s_20260727_212759/`

## 3. Selected Plane A Column Boundary

Selected boundary: `arcade_pc 0x055968 -> runtime_genesis_pc 0x055B68`.

Address-map segment remains an opcode-replace patched site at `runtime_genesis_pc 0x055B68`, mapped exactly to `arcade_pc 0x055968`. The replacement still routes through the existing Genesis helper path, but the gameplay visual subpath now writes final resident Plane A words into `staged_fg_buffer` instead of writing the tall FG backing buffer.

## 4. Selected Plane A Row Boundary

Selected boundary: `arcade_pc 0x055990 -> runtime_genesis_pc 0x055B90`.

Address-map segment remains an opcode-replace patched site at `runtime_genesis_pc 0x055B90`, mapped exactly to `arcade_pc 0x055990`. The implementation uses the same native resident-window helper reached by the active gameplay FG path. Selector-1/selector-2 row-path runtime acceptance remains not fully exercised by the automatic 30-second no-input MAME trace.

## 5. Selected Plane B Boundary

Selected boundary: `arcade_pc 0x055C5E -> runtime_genesis_pc 0x055E5E`.

This preserves the required upstream tilemap0 wrapper/bookkeeping at `arcade_pc 0x055C4A -> runtime_genesis_pc 0x055E4A`, then routes the existing strip blit through a native Plane B resident-window path when the producer source is classified as gameplay. Non-gameplay/item-page compatibility keeps the legacy 32-row path.

## 6. Register, Stack, Return, And Side-Effect Contracts

- `genesistan_stage_fg_src_column` remains `movem.l %d0-%d7/%a0-%a6` wrapped and returns with `rts`.
- The Plane A native helper allocates a 4-byte stack local and releases it before restoring registers.
- The shared PC080SN cell converter preserves `d0/d4-d7/a2-a3`; it intentionally returns the converted Genesis nametable word in `d3`.
- `genesistan_hook_itempage_strip_blit` keeps its existing `d1/d6` preservation contract and still stores the strip cursor before returning.
- `vdp_commit_bg_narrow_strips` and `vdp_commit_fg_narrow_strips` are VBlank-only helpers, preserve `d0-d7/a0-a6`, temporarily set VDP auto-increment to `8`, and restore auto-increment to `2` before returning.
- Arcade control flow remains arcade-owned. Genesis code remains helper/hardware-service code returning to the translated arcade flow.

## 7. Selector-0 Scene Fill Implementation

The selector-0 fill continues through the original arcade publication path. The gameplay visual subpath now:

- Reads all 64 arcade logical rows in arcade order.
- Computes native Plane A top row from `staged_scroll_y_fg` using `(-Y + 8) & 0x01FF`.
- Applies `delta = (logical_row - logical_top_row) & 0x003F` and writes only when `delta < 32`.
- Converts PC080SN word/code to final Genesis nametable format through the PC080SN tile and attr LUTs.
- Writes final words into `staged_fg_buffer` at `physical_row = logical_row & 0x001F`.
- Enqueues bounded Plane A narrow descriptors for VBlank commit.

It does not write `staged_fg_tall_buffer` and does not require `vdp_project_fg_tall_if_dirty`.

## 8. Selector-1 Scene Fill Implementation

Selector-1 uses the same Plane A native resident-window staging contract at the `0x055B90` boundary. Static contract says selector-1 scene fill publishes rows 63 -> 0. Build 0239 contains the native conversion/commit support needed for this path, but the automatic 30-second no-input trace did not exercise and prove a live selector-1 fill under Build 0239.

## 9. Selector-2 Non-Fill Handling

Selector 2 remains treated as gameplay vertical-streaming direction, not as a scene-fill specialization. No invented selector-2 scene-fill path was added.

## 10. Plane A Gameplay Column Implementation

`genesistan_stage_fg_src_column` now performs native resident-window final staging:

- Source remains the rebuilt arcade pointer table at `0x00FF1040`.
- Column offset comes from `a5@0x10A0` and `a5@0x10CA`.
- Only resident rows are written into `staged_fg_buffer`.
- Each touched 4-row segment enqueues one `fg_narrow_desc_table` descriptor.
- VBlank commits each descriptor as a 4-row x 16-word strided native operation.

## 11. Plane A Gameplay Row Implementation

Build 0239 provides the same native final-buffer conversion and narrow VBlank commit machinery for Plane A row/vertical-stream publication. Runtime row-path exercise remains a known untested behavior for this build.

## 12. Plane B Scene Fill Implementation

Gameplay-classified tilemap0 strips routed through `genesistan_hook_itempage_strip_blit` now branch to `.Litempage_strip_blit_native_bg`:

- The required `0x055C4A` bookkeeping remains upstream.
- The helper computes Plane B top row from `staged_scroll_y_bg` using `(-Y + 8) & 0x01FF`.
- It applies the resident test before writing final words.
- It writes final Genesis nametable words into `staged_bg_buffer`.
- It enqueues bounded BG narrow descriptors for VBlank commit.

Non-gameplay callers keep the legacy `genesistan_hook_tilemap_bg_fill` route.

## 13. Plane B Gameplay Row Implementation

The current implementation follows the existing `0x055E5E` strip-source/destination convention and resident-filters that publication into Plane B final staging. This is the selected safe boundary because it preserves upstream arcade state and the existing runtime source classification. The exact row/strip nomenclature remains a runtime-acceptance risk: Build 0239 should be treated as a candidate that proves mechanical native ownership, not as final visual acceptance for every vertical-streaming case.

## 14. Collision Preservation

Plane A collision remains independent WRAM state. Build 0239 does not derive collision from visual staging or VRAM. The existing collision side-channel remains in `genesistan_stage_bg_collision_column`; `genesistan_stage_fg_src_column` remains visual-only and explicitly does not author collision.

## 15. Plane A VSRAM Encoding Proof

`vdp_commit_scroll` now commits full native Plane A vertical scroll:

```asm
move.w staged_scroll_y_fg, d0
neg.w d0
addq.w #8,d0
andi.w #0x01FF,d0
move.w d0, VDP_DATA
```

This matches the accepted native equation `A_native_scroll_y = (-A_y + 8) & 0x01FF`. Horizontal scroll remains as before.

## 16. Plane B VSRAM Encoding Proof

`vdp_commit_scroll` now commits full native Plane B vertical scroll:

```asm
move.w staged_scroll_y_bg, d0
neg.w d0
addq.w #8,d0
andi.w #0x01FF,d0
move.w d0, VDP_DATA
```

This matches `B_native_scroll_y = (-B_y + 8) & 0x01FF`. Plane B horizontal/parallax source ownership remains unchanged.

## 17. Plane A Residency And Physical Mapping

Plane A native staging uses:

- `logical_top_row = (((-staged_scroll_y_fg + 8) & 0x01FF) >> 3) & 0x003F`
- `delta = (logical_row - logical_top_row) & 0x003F`
- resident iff `delta < 32`
- `physical_row = logical_row & 0x001F`
- `physical_col = logical_col & 0x003F`

Modulo row placement is used only after the residency test succeeds.

## 18. Plane B Residency And Physical Mapping

Plane B native staging uses:

- `logical_top_row = (((-staged_scroll_y_bg + 8) & 0x01FF) >> 3) & 0x003F`
- `delta = (logical_row - logical_top_row) & 0x003F`
- resident iff `delta < 32`
- `physical_row = logical_row & 0x001F`
- `physical_col = logical_col & 0x003F`

Modulo row placement is used only after the residency test succeeds.

## 19. Native / Legacy Ownership And Setters / Clearers

Native gameplay ownership:

- Plane A gameplay writes final words to `staged_fg_buffer` and enqueues `fg_narrow_desc_count`.
- Plane B gameplay-classified tilemap0 writes final words to `staged_bg_buffer` and enqueues `bg_narrow_desc_count`.
- `_vblank_service` commits BG narrow jobs and FG narrow jobs; it no longer calls either tall projector.

Clearers:

- Boot clears `bg_narrow_desc_count`, `fg_narrow_desc_count`, and legacy dirty/project metadata.
- `genesistan_hook_cwindow_clear` clears both narrow descriptor counts and both tall buffers, preserving frontend/transition cleanup.

Legacy compatibility ownership:

- Title/frontend/text/HUD/score/high-score/glyph/number/block-copy/unconverted paths retain the existing 32-row staging routes.
- Tall helper definitions remain in the binary for compatibility and rollback safety, but no live disassembly call reference to `vdp_project_bg_tall_if_dirty`, `vdp_project_fg_tall_if_dirty`, `genesistan_hook_tilemap_bg_fill_tall`, or `genesistan_hook_tilemap_fg_fill_tall` was found in Build 0239.

## 20. VBlank Job Formats And Capacities

Job formats:

- `fg_narrow_desc_table`: two bytes per descriptor: physical row base and column byte offset.
- `bg_narrow_desc_table`: two bytes per descriptor: physical row base and column byte offset.
- Each narrow descriptor commits 4 rows x 16 words with VDP auto-increment 8, then the helper restores auto-increment 2.

Capacities:

- FG descriptors: `64`.
- BG descriptors: `64`.
- No unbounded queue was added.
- Descriptor counts are cleared after successful VBlank commit.

## 21. Initial-Fill Transfer Cost

Scene fill can populate final 32-row native staging before display and then use existing final-row dirty commits and/or narrow descriptors. Build 0239 does not introduce display-disable bracketing or active-display writes outside VBlank.

## 22. Ordinary Worst-Case VBlank Cost

Per narrow descriptor:

- VDP address/control setup: one `vdp_set_vram_write_addr` per row, 4 rows.
- Data words: 4 x 16 = 64 words.
- Auto-increment writes: set to 8 once per nonempty helper, restore to 2 once.

Ordinary intended case is one Plane A narrow publication and one Plane B narrow publication in a frame. The current BG implementation can enqueue multiple descriptors for one gameplay-classified strip; this remains the principal runtime-acceptance and VBlank-budget risk for Build 0239.

## 23. Scaffolding Retired From Gameplay

Retired from live gameplay/VBlank in Build 0239:

- `vdp_project_bg_tall_if_dirty` live call path.
- `vdp_project_fg_tall_if_dirty` live call path.
- Gameplay visual writes through `genesistan_hook_tilemap_fg_fill_tall` from `genesistan_stage_fg_src_column`.
- Gameplay-classified BG writes through `genesistan_hook_tilemap_bg_fill_tall` from the tilemap0 strip path.

## 24. Scaffolding Retained For Compatibility

Retained:

- `staged_bg_tall_buffer` and `staged_fg_tall_buffer`: compatibility/transition cleanup; not removed without full producer-and-consumer proof.
- `vdp_project_bg_tall_if_dirty` and `vdp_project_fg_tall_if_dirty`: definitions retained, no live call reference found.
- `genesistan_hook_tilemap_bg_fill_tall` and `genesistan_hook_tilemap_fg_fill_tall`: definitions retained, no live call reference found.
- `genesistan_stage_fg_src_column`: retained as the native Plane A gameplay producer helper.
- `genesistan_hook_itempage_strip_blit`: retained as shared legacy/native dispatcher.
- `staged_bg_buffer` and `staged_fg_buffer`: required final native staging buffers and legacy compatibility buffers.

## 25. Before / After Performance Counts

Before Build 0239 / Build 0235:

- `_vblank_service` called both tall projectors.
- Gameplay FG visual path wrote tall FG backing and depended on projection to final staging.
- Gameplay-classified BG path wrote tall BG backing and depended on projection to final staging.
- Gameplay vertical scroll was residual-only (`& 0x0007`) in VBlank.

After Build 0239:

- `_vblank_service` calls `vdp_commit_bg_narrow_strips` and `vdp_commit_fg_narrow_strips`; tall projector calls are absent from live disassembly references.
- Native VSRAM commits full `(-Y + 8) & 0x01FF` for both planes.
- `address_map.segment_coverage.total_genesis_bytes_covered = 0x183D90` (`1588624`) with opcode_replace count still `216`.
- Coverage delta from previous canonical value: `+0xB8` bytes.

## 26. Build Artifact

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0239.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA-256: `f1d6075c801f8a0326084edec79c2850decc26f8569abc2a7eb1328b8677813b`
- Size: `1588624` bytes
- Counter: `239`
- Rolling and numbered SHA match.

## 27. Canonical Gate Result

The normal Makefile printed `GATE_PASS` and verified numbered name `rastan_direct_video_test_build_0239.bin`.

A standalone re-run of `verify_canonical_rom.py` with a temporary pre-build counter also printed `GATE_PASS`.

## 28. Automatic MAME Trace Result

Makefile automatic trace completed:

- Directory: `states/traces/rastan_direct_video_test_build_0239_mame_30s_20260727_212759/`
- Frames: `1798`
- Summary file: `genesis_exec_summary.txt` (`3778` bytes)
- Trace file: `genesis_exec_trace.log` (`6306` bytes)
- Unique unmapped memory addresses: none reported in the appended MAME exit summary.
- Final PC from MAME exit summary: `0x072EC4`.

## 29. MAME Genesis Runtime Verification

Automatic MAME Genesis trace ran for approximately 30 seconds with no trace-command failure and no unmapped address report. This is a mechanical boot/frontend/no-input trace, not a complete gameplay visual acceptance run.

## 30. Original Arcade Comparison

No new original-arcade runtime trace was run in this implementation turn. The implementation comparison is against the accepted original-arcade PC080SN contract and reference documents, especially the global-fill/vertical-streaming contract and `docs/arcade_reference/pc080sn/`.

## 31. Build 0235 Regression Comparison

Build 0235 was verified as the accepted baseline before editing. Build 0239 preserves the fixed VDP layout and keeps legacy frontend/unconverted staging paths. Functional gameplay comparison to Build 0235 still requires user/runtime testing because the automatic MAME run did not drive Stage 1 movement or rope/cave/wrap cases.

## 32. Known Untested Behavior

Known untested or partially tested in Build 0239:

- Selector-1/selector-2 Plane A row-path runtime exercise.
- Plane B vertical-streaming acceptance under active Stage 1 movement.
- Physical row 31 -> 0 reuse under natural gameplay.
- Logical row 63 -> 0 wrap under natural gameplay.
- Death/restart, stage transition, frontend return, and item-page compatibility after the native ownership change.
- Visual parity versus original arcade during Stage 1 after user-controlled movement.
- Cycle-budget sufficiency for worst-case BG narrow descriptor bursts.

## 33. Architecture Compliance Statement

Build 0239 keeps the arcade code as the program. Genesis code remains helper/hardware-service code. No Genesis scheduler, 64x64 VDP mode, C-window shadow, display-disable bracketing, active-display VDP writes, SAT/Hscroll relocation, or NOP/RTS bypass was introduced.

Numbered builds 0235-0238 were preserved; Build 0239 was produced by the normal Makefile and canonical gate.

## Final Classification

Build 0239 is a mechanically successful candidate for native PC080SN YM7101 presentation ownership. It is **not yet visually accepted**: the remaining gameplay/wrap/cycle cases must be tested before treating the native Plane A/Plane B migration as complete.
