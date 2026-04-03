# Build 337 Full Per-Frame VDP Write Census

## 1. Executive Summary
The current post-launch runtime path has one VBlank owner (`_VINT_arcade_mode`) and no active tick-phase direct-port/helper/DMA VDP writer. The previously identified tick preload DMA path is disabled (`genesistan_bulk_preload_check` returns immediately). The rolling display is not explained by a second active writer outside the VBlank owner path.

## 2. Full Active VDP Write Site Census
full active VDP write census completed: YES.

### A) Active in current runtime path (`SCREEN_FRONTEND_LIVE`)
1. `_VINT_arcade_mode` — `apps/rastan/src/boot/sega.s`
- Mechanism: direct port write (`0xC00004`)
- Writes: reg1 display OFF/ON each frame
- Active in current runtime path: YES

2. `genesistan_pc080sn_commit_planes` — `apps/rastan/src/startup_trampoline.s`
- Mechanism: direct port writes (`0xC00004` + `0xC00000`)
- Writes: VRAM nametable stream from `pc080sn_bg_buffer`/`pc080sn_fg_buffer`
- Active in current runtime path: YES

3. `genesistan_palette_commit_asm` — `apps/rastan/src/startup_trampoline.s`
- Mechanism: direct port writes (`0xC00004` + `0xC00000`)
- Writes: CRAM entries
- Active in current runtime path: YES

4. `genesistan_scroll_commit_vdp` — `apps/rastan/src/main.c`
- Mechanism: direct port writes (`0xC00004` + `0xC00000`)
- Writes: HScroll table (VRAM 0xF000) + VSRAM entries
- Active in current runtime path: YES

### B) Present in code but not active in current runtime path
5. `genesistan_bulk_preload_check` — `apps/rastan/src/main.c`
- Mechanism: none currently (early return)
- Active in current runtime path: YES (called), VDP-affecting write: NO

6. `genesistan_preload_scene_tiles` — `apps/rastan/src/main.c`
- Mechanism: `VDP_loadTileData(..., DMA)` + `VDP_waitDMACompletion()`
- Active in current runtime path: NO (not reached per-frame; tick caller disabled)

7. `genesistan_render_sprites_vdp_asm` — `apps/rastan/src/startup_trampoline.s`
- Mechanism: direct port writes + DMA path in function body
- Active in current runtime path: NO (immediate `rts` at entry)

8. `genesistan_sprite_commit_asm` (legacy) — `apps/rastan/src/startup_trampoline.s`
- Mechanism: direct port writes
- Active in current runtime path: NO

9. `genesistan_render_sprites_vdp` (C path) — `apps/rastan/src/main.c`
- Mechanism: `VDP_setSpriteFull`, `VDP_updateSprites`, `PAL_*`
- Active in current runtime path: NO

10. `force_clean_vram_init` — `apps/rastan/src/main.c`
- Mechanism: direct port writes
- Active in current runtime path: NO (launch handoff one-shot)

11. `apply_post_reset_test_palette` — `apps/rastan/src/main.c`
- Mechanism: direct port writes
- Active in current runtime path: NO (launch handoff one-shot)

12. Launcher/UI VDP writers in `apps/rastan/src/main.c` (`restore_launcher_vdp_state`, `render_static_layout`, `render_graphics_test_screen`, sound/config menu renderers)
- Mechanism: `VDP_*` / `PAL_*` helpers
- Active in current runtime path: NO

13. Exception renderer writers in `apps/rastan/src/z_qr_exception.c`
- Mechanism: `VDP_*` / `PAL_*`
- Active in current runtime path: NO (exception-only)

## 3. Context Classification for Each Active Writer
all active write paths classified by context: YES.

- `_VINT_arcade_mode` -> `ACTIVE_VBLANK_COMMIT_PATH`
- `genesistan_pc080sn_commit_planes` -> `ACTIVE_VBLANK_COMMIT_PATH`
- `genesistan_palette_commit_asm` -> `ACTIVE_VBLANK_COMMIT_PATH`
- `genesistan_scroll_commit_vdp` -> `ACTIVE_VBLANK_COMMIT_PATH`
- `genesistan_bulk_preload_check` (current early-return form) -> `ARCADE_TICK_PATH` (no VDP write)
- `genesistan_preload_scene_tiles` -> `LAUNCHER_ONLY_PATH` (in present runtime; no tick invocation)
- `genesistan_render_sprites_vdp_asm` -> `UNUSED_OR_DISABLED_PATH`
- `genesistan_sprite_commit_asm` -> `UNUSED_OR_DISABLED_PATH`
- `genesistan_render_sprites_vdp` -> `UNUSED_OR_DISABLED_PATH`
- `force_clean_vram_init` -> `LAUNCHER_ONLY_PATH`
- `apply_post_reset_test_palette` -> `LAUNCHER_ONLY_PATH`
- launcher/UI helper writers -> `LAUNCHER_ONLY_PATH`
- `z_qr_exception.c` writers -> `EXCEPTION_ONLY_PATH`

## 4. Active Per-Frame VDP Writers in Current Runtime
all active per-frame VDP writers identified: YES.

1. `_VINT_arcade_mode` (`boot/sega.s`)
- Per-frame: YES
- In VBlank: YES
- Outside VBlank: NO
- Presentation-state write: direct reg1 display bracket

2. `genesistan_pc080sn_commit_planes` (`startup_trampoline.s`)
- Per-frame: YES
- In VBlank: YES
- Outside VBlank: NO
- Presentation-state write: direct VRAM nametable data

3. `genesistan_palette_commit_asm` (`startup_trampoline.s`)
- Per-frame: YES
- In VBlank: YES
- Outside VBlank: NO
- Presentation-state write: direct CRAM

4. `genesistan_scroll_commit_vdp` (`main.c`)
- Per-frame: YES
- In VBlank: YES
- Outside VBlank: NO
- Presentation-state write: direct HScroll/VSRAM

## 5. Are There Any Writers Outside the 3 Commit Functions
uncounted active writer exists: YES.

Exact function:
- `_VINT_arcade_mode` direct reg1 display OFF/ON writes each frame.

This writer is in the same VBlank owner path and is not a second competing runtime writer path.

## 6. Tick-Path Direct Port / Helper / DMA Writes
direct port writes during arcade tick: NO.
- Responsible function(s): none active.

VDP helper writes during arcade tick: NO.
- Responsible function(s): none active.

PAL helper writes during arcade tick: NO.
- Responsible function(s): none active.

DMA helper writes during arcade tick: NO.
- Responsible function(s): none active (`genesistan_bulk_preload_check` no longer calls `genesistan_preload_scene_tiles`).

## 7. Single Root Cause
`SINGLE_VBLANK_WRITER_PRESENTS_WRONG_STATE_WITH_NO_SECOND_WRITER`

## 8. Single Next Implementation Target
Audit the single-writer state source path feeding `genesistan_pc080sn_commit_planes` (descriptor decode -> LUT translation -> `pc080sn_*_buffer` layout) to isolate the wrong presentation state being committed once per frame.

## 9. Final Verdict
There is no remaining active tick-phase VDP writer. The active per-frame runtime writes are confined to one VBlank owner path. The rolling display is produced by wrong state in that single writer pipeline, not by a second competing writer.
