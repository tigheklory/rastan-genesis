# Build 337 Full Per-Frame VDP Write Census

## 1. Executive Summary
The full census of VDP-affecting write paths confirms that the current runtime path has exactly four active per-frame writers, all localized within the Level-6 VBlank interrupt handler (`_VINT_arcade_mode`). The previously active tick-phase DMA writer (`genesistan_preload_scene_tiles`) has been disabled, and the sprite renderer remains suppressed. No direct port writes or SGDK VDP/PAL/DMA helper calls occur during the arcade tick. The rolling display is not caused by competing writers but by the single-writer VBlank commit pipeline presenting incorrect state.

## 2. Full Active VDP Write Site Census
full active VDP write census completed: YES.

| Function | File | Mechanism | Active in Runtime Path |
| :--- | :--- | :--- | :--- |
| `_VINT_arcade_mode` | `sega.s` | direct port write (`0xC00004`) | YES |
| `genesistan_pc080sn_commit_planes` | `startup_trampoline.s` | direct port write (`0xC00004`/`0xC00000`) | YES |
| `genesistan_palette_commit_asm` | `startup_trampoline.s` | direct port write (`0xC00004`/`0xC00000`) | YES |
| `genesistan_scroll_commit_vdp` | `main.c` | direct port write (`0xC00004`/`0xC00000`) | YES |
| `genesistan_bulk_tilemap_commit` | `startup_trampoline.s` | none (buffer-only writes) | YES |
| `genesistan_bulk_preload_check` | `main.c` | none (early return) | YES |
| `genesistan_preload_scene_tiles` | `main.c` | DMA helper (`VDP_loadTileData`) | NO |
| `genesistan_render_sprites_vdp_asm`| `startup_trampoline.s` | direct port / DMA | NO |
| `force_clean_vram_init` | `main.c` | direct port write | NO |
| `apply_post_reset_test_palette` | `main.c` | direct port write | NO |
| Launcher UI Renderers | `main.c` | `VDP_*` / `PAL_*` helpers | NO |
| Exception Handlers | `z_qr_exception.c` | `VDP_*` / `PAL_*` helpers | NO |

## 3. Context Classification for Each Active Writer
all active write paths classified by context: YES.

* `_VINT_arcade_mode` -> `ACTIVE_VBLANK_COMMIT_PATH`
* `genesistan_pc080sn_commit_planes` -> `ACTIVE_VBLANK_COMMIT_PATH`
* `genesistan_palette_commit_asm` -> `ACTIVE_VBLANK_COMMIT_PATH`
* `genesistan_scroll_commit_vdp` -> `ACTIVE_VBLANK_COMMIT_PATH`
* `genesistan_bulk_tilemap_commit` -> `ARCADE_TICK_PATH` (VDP-affecting: NO)
* `genesistan_bulk_preload_check` -> `ARCADE_TICK_PATH` (VDP-affecting: NO)
* `genesistan_preload_scene_tiles` -> `LAUNCHER_ONLY_PATH` (Disabled in tick)
* `genesistan_render_sprites_vdp_asm` -> `UNUSED_OR_DISABLED_PATH` (Suppressed)
* `force_clean_vram_init` -> `LAUNCHER_ONLY_PATH`
* `apply_post_reset_test_palette` -> `LAUNCHER_ONLY_PATH`
* Launcher UI Renderers -> `LAUNCHER_ONLY_PATH`
* Exception Handlers -> `EXCEPTION_ONLY_PATH`

## 4. Active Per-Frame VDP Writers in Current Runtime
all active per-frame VDP writers identified: YES.

1. `_VINT_arcade_mode` (reg 1 Display OFF/ON) — every frame, in VBlank, direct.
2. `genesistan_pc080sn_commit_planes` (Nametables) — every frame, in VBlank, direct.
3. `genesistan_palette_commit_asm` (CRAM) — every frame, in VBlank, direct.
4. `genesistan_scroll_commit_vdp` (HScroll/VSRAM) — every frame, in VBlank, direct.

## 5. Are There Any Writers Outside the 3 Commit Functions
uncounted active writer exists: YES.

Exact function: `_VINT_arcade_mode` in `apps/rastan/src/boot/sega.s`. It writes to VDP port `0xC00004` to toggle Display OFF before the tick and Display ON after the commit sequence.

## 6. Tick-Path Direct Port / Helper / DMA Writes
direct port writes during arcade tick: NO.
direct `0xC00004` writes: NO.
direct `0xC00000` writes: NO.
`VDP_*` helper calls: NO.
`PAL_*` helper calls: NO.
DMA helper calls: NO.

## 7. Single Root Cause
`SINGLE_VBLANK_WRITER_PRESENTS_WRONG_STATE_WITH_NO_SECOND_WRITER`

## 8. Single Next Implementation Target
audit the state-source path feeding `genesistan_pc080sn_commit_planes` (descriptor/LUT/buffer mapping)

## 9. Final Verdict
The census proves there are no VDP-affecting writers remaining in the arcade tick path. All per-frame VDP activity is synchronized within the VBlank interrupt handler. The rolling display is a consequence of incorrect data being committed by the single-writer pipeline, not a race condition or second writer.
