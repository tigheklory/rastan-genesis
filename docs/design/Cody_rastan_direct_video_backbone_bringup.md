# Summary
Implemented a first `rastan-direct` video backbone with Rainbow Islands-style phase separation:
- main loop runs logic tick only (`wait VBlank -> arcade tick`)
- `_VINT_handler` is the hardware commit owner for VRAM/CRAM/VSRAM/HScroll
- tilemap/palette/scroll state is staged in WRAM and consumed during VBlank

Implemented required VBlank commit order exactly:
1. display OFF
2. BG commit
3. FG commit
4. palette commit (if dirty)
5. display ON
6. scroll commit
7. frame counter increment

# Exact Files Modified
- `apps/rastan-direct/src/main_68k.s`
- `apps/rastan-direct/src/boot/boot.s`
- `apps/rastan-direct/Makefile`
- `docs/design/Cody_rastan_direct_video_backbone_bringup.md`
- `AGENTS_LOG.md`

# Exact Symbols / Functions / Labels Added or Changed
- `main_68k`
- `_VINT_handler`
- `vdp_boot_setup`
- `vdp_set_reg`
- `vdp_set_vram_write_addr`
- `vdp_commit_tiles_if_dirty`
- `vdp_commit_bg`
- `vdp_commit_fg`
- `vdp_commit_palette`
- `vdp_commit_scroll`
- `arcade_tick_logic`
- `init_staging_state`
- `sprite_dma_addr_high_bits_fix`
- WRAM staging symbols:
  - `frame_counter`
  - `tick_counter`
  - `palette_dirty`
  - `tiles_dirty`
  - `staged_dest_ptr_bg`
  - `staged_dest_ptr_fg`
  - `staged_scroll_x_bg`
  - `staged_scroll_x_fg`
  - `staged_scroll_y_bg`
  - `staged_scroll_y_fg`
  - `staged_bg_buffer`
  - `staged_fg_buffer`
  - `staged_palette_words`
  - `staged_tile_words`
- `boot.s` vector ownership change:
  - level-6 autovector entry points to `_VINT_handler`

# Permanent vs Temporary Classification
- PERMANENT:
  - VBlank-owned staged-commit control flow and WRAM staging backbone in `main_68k.s`
  - Level-6 VBlank vector wiring in `boot.s`
  - DEST_PTR fix integration writes:
    - `0x00FF10A0 = 0x00C00000`
    - `0x00FF10A4 = 0x00C08000`
  - Sprite DMA high-bit fix helper logic equivalent to required `lsr.l #14,%d2` behavior (implemented as `lsr.l #8` + `lsr.l #6` for 68000 immediate-shift legality)
  - Build artifact rename in `Makefile` to `rastan_direct_video_test.bin`
- TEMPORARY:
  - none
- DIAGNOSTIC:
  - none
- BRINGUP_ONLY:
  - synthetic checkerboard BG/FG staging in `init_staging_state`
  - synthetic palette bootstrap table `palette_init_words`
  - synthetic tile bootstrap table `tile_init_words`

# Scaffolding Inventory
1. BRINGUP_ONLY
- exact file: `apps/rastan-direct/src/main_68k.s`
- exact symbol/function/label: `palette_init_words`, `tile_init_words`
- purpose: bootstrap visible video output without full arcade data path
- why it exists: establish first direct-execution VBlank commit proof
- how it is triggered: loaded by `init_staging_state` during startup
- future condition allows removal: arcade-authored tile/palette staging path is integrated
- exact removal method: remove static init tables and replace staging fill with arcade pipeline producer

2. BRINGUP_ONLY
- exact file: `apps/rastan-direct/src/main_68k.s`
- exact symbol/function/label: checkerboard fill and FG stripe fill in `init_staging_state`
- purpose: force deterministic recognizable output for initial backbone validation
- why it exists: prove tilemap+palette+scroll commit ordering path
- how it is triggered: one-time startup staging
- future condition allows removal: attract/title content is sourced from translated arcade logic
- exact removal method: delete checkerboard/stripe fill loops; route buffer population from arcade write hooks

# Removal / Revert Plan
1. Replace `init_staging_state` synthetic tables/fills with real arcade-produced staged buffers.
2. Keep `_VINT_handler` ordering intact while swapping data producers from bring-up scaffolding to translated opcode bridge.
3. Remove BRINGUP_ONLY tile/palette content symbols once real content path is confirmed.
4. Preserve DEST_PTR initialization and VBlank ownership guarantees during migration.

# Build Artifact Path
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

# Verification Status
- Build succeeded: YES
- ROM launches in headless MAME run: YES
- Rainbow model enforced (`wait VBlank -> logic tick`, VBlank commit path): YES
- Single VDP owner for VRAM/CRAM/VSRAM/HScroll in active runtime: YES
- Staging vs commit separation enforced: YES
- Tilemap visible on actual display: USER MUST VERIFY
- Palette correctness on actual display: USER MUST VERIFY
- Scroll staging active (`arcade_tick_logic` updates staged scroll; VBlank commits): YES
- Sprites active: NO
- Mandatory tilemap fix integrated: YES
- Mandatory sprite DMA fix integrated: YES

Phase status:
- Phase 1 (boot + VBlank ownership): COMPLETE
- Phase 2 (tilemap + palette first visible output): IMPLEMENTED, DISPLAY VERIFICATION PENDING
- Phase 3 (scroll staged + VBlank commit): COMPLETE
- Phase 4 (sprites): PARTIAL (DMA fix integrated, sprite publication path not enabled)

# Risks / Known Limitations
- Visual confirmation is pending because this environment used headless validation only.
- Bring-up scaffolding currently uses synthetic content, not translated arcade attract content.
- Sprite bridge remains disabled in this phase; only DMA address-fix logic is integrated.
