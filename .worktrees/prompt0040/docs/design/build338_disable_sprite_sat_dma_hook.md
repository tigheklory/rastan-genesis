# Build 338 Disable Sprite SAT DMA Hook

## 1. Summary of Change
`genesistan_hook_frontend_sprite_sat_refresh` was changed to return immediately at function entry, preventing the sprite SAT refresh path from running.

## 2. Exact Function Modified
- File: `apps/rastan/src/main.c`
- Function: `genesistan_hook_frontend_sprite_sat_refresh`

## 3. Exact Line Where Early Return Added
- `apps/rastan/src/main.c:1953`
- Added statement: `return;`

## 4. Confirmation That `VDP_updateSprites` Is No Longer Reachable
From `genesistan_hook_frontend_sprite_sat_refresh`: `VDP_updateSprites` is no longer reachable because control returns before calling `genesistan_render_sprites_vdp()`.

## 5. Confirmation No Other Code Paths Modified
No other function behavior was modified in this prompt. Only the hook early return was added.

## 6. Expected Runtime Effect
- Sprite SAT DMA from this hook path is eliminated.
- Commit trio remains as the active per-frame presentation path:
  - `genesistan_pc080sn_commit_planes`
  - `genesistan_palette_commit_asm`
  - `genesistan_scroll_commit_vdp`

## 7. Build Result
- Build command: `source tools/setup_env.sh && make -C apps/rastan release`
- Build succeeded.
- ROM artifact: `dist/Rastan_336.bin`
- No new build errors.
- No new warnings versus current baseline (same 6 warnings currently present).
