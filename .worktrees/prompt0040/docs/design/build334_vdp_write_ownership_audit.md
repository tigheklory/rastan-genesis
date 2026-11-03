# Build 334 VDP Write Ownership Audit

## Scope
Determine whether active runtime has VDP writes outside `_VINT_arcade_mode` and whether multiple writer paths exist.

## Task 1: All VDP Write Sites

### Direct port writers (`0xC00004`, `0xC00000`)
- `apps/rastan/src/boot/sega.s`:
  - `_VINT_arcade_mode` (display OFF/ON register writes).
- `apps/rastan/src/startup_trampoline.s`:
  - `genesistan_palette_commit_asm` (CRAM writes).
  - `genesistan_render_sprites_vdp_asm` (contains direct VDP writes; current entry has early `rts`).
  - `genesistan_sprite_commit_asm` (legacy SAT commit; not on active hot path).
  - `genesistan_pc080sn_commit_planes` (VRAM plane streaming from buffers).
- `apps/rastan/src/main.c`:
  - `genesistan_scroll_commit_vdp` (HScroll table + VSRAM).
  - `force_clean_vram_init` (VRAM/CRAM/VSRAM clear + register baseline).
  - `apply_post_reset_test_palette` (CRAM write).

### SGDK VDP helper writers (`VDP_*`, `PAL_*`)
- `apps/rastan/src/main.c`:
  - launcher/config/title setup and UI render functions (`restore_launcher_vdp_state`, `render_static_layout`, `render_graphics_test_screen`, `leave_graphics_test`, `enter_sound_test`, `render_sound_test_screen`, `leave_sound_test`, `genesistan_sync_title_vdp_layout`, `request_start_rastan`).
  - runtime scene preload: `genesistan_preload_scene_tiles` (`VDP_loadTileData(..., DMA)` + `VDP_waitDMACompletion()`).
  - optional/unused sprite C path: `genesistan_render_sprites_vdp` (uses `VDP_setSpriteFull`, `VDP_updateSprites`, palette writes).
- `apps/rastan/src/z_qr_exception.c`:
  - crash/exception screen rendering (`VDP_*`, `PAL_*`, tilemap writes).

## Task 2: Classification by Execution Context

### Inside `_VINT_arcade_mode` (active VBlank writer)
- `_VINT_arcade_mode` (`boot/sega.s`) display OFF/ON writes.
- `genesistan_pc080sn_commit_planes` (`startup_trampoline.s`) direct VRAM nametable writes.
- `genesistan_palette_commit_asm` (`startup_trampoline.s`) direct CRAM writes.
- `genesistan_scroll_commit_vdp` (`main.c`) HScroll/VSRAM writes.

### Inside arcade tick (`genesistan_run_arcade_tick_lean` call chain)
- `genesistan_bulk_tilemap_commit` itself: buffer-only writes (no direct VDP port writes).
- `genesistan_bulk_tilemap_commit` range-miss branch -> `genesistan_bulk_preload_check` -> `genesistan_preload_scene_tiles` (`VDP_loadTileData(..., DMA)` + wait).
- `genesistan_render_sprites_vdp_bridge` is tick-hooked, but target `genesistan_render_sprites_vdp_asm` returns immediately at entry (Build 329 suppression), so current active behavior writes nothing.

### Outside VBlank entirely
- launcher/config/UI VDP helpers in `main.c` before handoff.
- handoff one-shot reset/palette writes in `request_start_rastan` (`force_clean_vram_init`, `apply_post_reset_test_palette`).
- exception UI writers in `z_qr_exception.c`.

## Task 3: Out-of-VBlank Writes
any VDP writes outside VBlank: YES.

Exact functions responsible:
- `restore_launcher_vdp_state`
- `render_static_layout`
- `render_graphics_test_screen`
- `leave_graphics_test`
- `enter_sound_test`
- `render_sound_test_screen`
- `leave_sound_test`
- `genesistan_sync_title_vdp_layout`
- `force_clean_vram_init`
- `apply_post_reset_test_palette`
- `genesistan_preload_scene_tiles` (when called through tick-side `genesistan_bulk_preload_check`, this path writes during tick phase)
- exception display functions in `z_qr_exception.c`

## Task 4: Multiple Writers
multiple competing VDP writers: YES.

Writer split:
- VBlank writer: `_VINT_arcade_mode` -> `genesistan_pc080sn_commit_planes` + `genesistan_palette_commit_asm` + `genesistan_scroll_commit_vdp`.
- Competing non-commit writer path: tick-side `genesistan_bulk_preload_check` -> `genesistan_preload_scene_tiles` (`VDP_loadTileData(..., DMA)`), separate from final commit trio.

## Task 5: `genesistan_bulk_tilemap_commit`
- direct VRAM writes: NO.
- direct VDP operations: NO.
- buffer writes: YES (`pc080sn_bg_buffer` / `pc080sn_fg_buffer`).
- indirect VDP trigger: YES, on scene-range miss via `genesistan_bulk_preload_check` calling `genesistan_preload_scene_tiles`.

## Single Root Cause
`MULTIPLE_COMPETING_VDP_WRITERS`

## Single Next Implementation Target
instrument VDP writes with frame markers to distinguish commit-path writes from tick-side preload DMA writes in the same frame ownership path.

## Verdict
The codebase has VDP writers outside VBlank and also has multiple runtime writer paths. The active tilemap block writer is buffer-only, but its range-miss branch invokes a separate DMA writer path, creating multi-writer ownership in the active frame pipeline.
