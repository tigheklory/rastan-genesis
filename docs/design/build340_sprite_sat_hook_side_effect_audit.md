# Build 340 — Sprite SAT Hook Side-Effect Audit

## 1. Executive Summary
Build 339 keeps `genesistan_hook_frontend_sprite_sat_refresh` active and keeps `genesistan_render_sprites_vdp` executing, but removes the only hardware SAT publish in that path (`VDP_updateSprites(..., DMA)`). `VDP_setSpriteFull(...)` updates only SGDK shadow sprite cache and does not write SAT VRAM. Result: hook logic still runs, but sprite hardware output is no longer committed. The visible output path that was present through this hook disappears, producing a black screen.

## 2. Current Build 339 Hook Body Audit
Function: `genesistan_hook_frontend_sprite_sat_refresh` in `apps/rastan/src/main.c`.

Current body:
```c
void genesistan_hook_frontend_sprite_sat_refresh(void)
{
    genesistan_render_sprites_vdp();
}
```

Audit results:
- No early return present.
- Calls `genesistan_render_sprites_vdp` directly.
- No direct palette helper call in this hook body.
- Returns normally to caller after callee returns.

## 3. Current Build 339 Sprite Renderer Body Audit
Function: `genesistan_render_sprites_vdp` in `apps/rastan/src/main.c`.

Current flow:
1. Reads sprite descriptor blocks from arcade work RAM.
2. Builds per-sprite tile attr and link chain values.
3. Calls `VDP_setSpriteFull(...)` per accepted sprite entry (shadow sprite table build).
4. Calls `refresh_frontend_sprite_palettes_mapped(...)`.
5. Does **not** execute hardware SAT publish or DMA wait at the former commit site.
6. Executes final `SYS_enableInts()` and returns.

Reachability:
- `VDP_setSpriteFull(...)`: reachable.
- `VDP_updateSprites(...)`: not reachable at the renderer commit site (neutralized).
- `VDP_waitDMACompletion()` at the renderer commit site: not reachable (neutralized).
- `SYS_enableInts()`: still executed.

## 4. Non-VDP Side Effects in the Sprite Path
Non-SAT-commit side effects that remain active:
- WRAM/runtime sprite code cache updates via `wram_overlay.launcher.frontend_runtime_sprite_codes[]`.
- Palette bank mapping derivation in local map state.
- SGDK sprite shadow cache writes via `VDP_setSpriteFull(...)`.
- SGDK palette shadow updates via `PAL_setColor(...)` inside `refresh_frontend_sprite_palettes_mapped(...)`.
- Interrupt state toggles via multiple `SYS_disableInts()` / `SYS_enableInts()` sections.
- Normal function return contract preserved.

## 5. Was Build 339 a Clean Two-Call Isolation
NO.

Compared to Build 338 state, Build 339 also restored the hook body from blunt early return to active call-through (`genesistan_hook_frontend_sprite_sat_refresh` now calls `genesistan_render_sprites_vdp`). Build 339 therefore contains:
- hook restoration change, plus
- two renderer-call neutralizations (`VDP_updateSprites`, paired wait).

## 6. Single Black-Screen Cause
`CALLER_EXPECTS_HARDWARE_COMMIT_SIDE_EFFECT`

The active hook path still builds sprite shadow state but no longer publishes SAT to VRAM because `VDP_updateSprites(..., DMA)` is removed. The hardware-visible output side effect previously provided by this hook path is removed.

## 7. Single Next Implementation Target
Implement a VBlank-owned sprite SAT publish step that keeps hook-side sprite preparation active but performs SAT hardware commit in `_VINT_arcade_mode` only.

## 8. Final Verdict
Build 339 did not break hook control flow; it removed the hook path’s hardware SAT publish side effect. That exact side-effect removal explains the black-screen result.
