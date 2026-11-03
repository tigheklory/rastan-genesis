# Build 339 — Disable Only Sprite SAT DMA Commit

## 1. Summary of change
A surgical proof change was applied to keep the per-frame sprite hook and sprite-building logic active while removing only the immediate SAT DMA hardware commit.

## 2. Exact function modified
- `genesistan_render_sprites_vdp`
- File: `apps/rastan/src/main.c`

## 3. Exact lines/calls neutralized
Inside `genesistan_render_sprites_vdp`, only these two calls were neutralized:
- `VDP_updateSprites(sprite_count, DMA);`
- `VDP_waitDMACompletion();`

Current source location:
- `apps/rastan/src/main.c:2058`
- `apps/rastan/src/main.c:2059`

## 4. Confirmation that `genesistan_hook_frontend_sprite_sat_refresh` still executes
Confirmed. `genesistan_hook_frontend_sprite_sat_refresh` remains present and still calls `genesistan_render_sprites_vdp()`.

## 5. Confirmation that `genesistan_render_sprites_vdp` still executes
Confirmed. The function is still called from the hook path and from existing code references.

## 6. Confirmation that `VDP_setSpriteFull` shadow-building remains active
Confirmed. Sprite enumeration and `VDP_setSpriteFull(...)` calls remain active and unchanged.

## 7. Confirmation that `VDP_updateSprites` and `VDP_waitDMACompletion` are no longer reachable
Confirmed for the `genesistan_render_sprites_vdp` commit site: those two calls are neutralized and no longer execute from this path.

## 8. Expected runtime result
- sprite logic path preserved
- SAT DMA write removed from this sprite renderer path
- illegal-instruction crash from blunt hook return avoided
- rolling display may change if sprite SAT DMA was the interfering writer

## 9. Build result
- Build command: `source tools/setup_env.sh && make -C apps/rastan release`
- Build succeeded
- ROM artifact: `dist/Rastan_337.bin`
- New errors: none
- New warnings: none beyond the same pre-existing warning set
