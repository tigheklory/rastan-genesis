# Build 335 Disable Tick-Phase DMA VDP Writer

## Summary
This change disables the tick-phase preload DMA writer by stopping `genesistan_bulk_preload_check()` from calling `genesistan_preload_scene_tiles()`.

## Exact Change
- File: `apps/rastan/src/main.c`
- Function: `genesistan_bulk_preload_check`
- Behavior: immediate return after `(void)source_addr;`

## Scope Confirmation
- `genesistan_preload_scene_tiles()` remains present and callable from other paths (for example launch-time preload in `request_start_rastan`).
- No VBlank commit path changes.
- No scroll/palette/input/tilemap-buffer logic changes.
- No sprite path changes.

## Build Verification
- Build command: `source tools/setup_env.sh && make -C apps/rastan release`
- Artifact: `dist/Rastan_334.bin`
- Build succeeded.
- No new build errors.
- One additional compiler warning appears because `genesistan_scene_id_from_source_addr` becomes unused after disabling the tick preload call.

## Expected Runtime Result
- Tick-phase DMA VDP writer path from `genesistan_bulk_tilemap_commit -> genesistan_bulk_preload_check -> genesistan_preload_scene_tiles` is disabled.
- Rolling/instability is expected to stop if that path was the active conflicting writer.
- Missing tiles are possible because dynamic preload during tick is now off.
