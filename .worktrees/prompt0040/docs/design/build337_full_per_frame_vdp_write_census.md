# Build 337 — Full Per-Frame VDP Write Census

## 1. Executive Summary

A complete census of every active VDP-affecting write path in the current runtime reveals one uncounted per-frame VDP writer outside the three known commit functions: `genesistan_render_sprites_vdp()`, called every frame via the arcade ROM hook `genesistan_hook_frontend_sprite_sat_refresh`. This function calls `VDP_updateSprites(sprite_count, DMA)` which triggers an immediate DMA from the SGDK sprite shadow table to SAT VRAM at 0xF800. This write path is not counted in the prior commit-trio audit. It is the only uncounted active per-frame VDP writer.

All other VDP-affecting calls outside the commit trio are either:
- One-time arcade handoff init (runs once at launch, not per frame)
- Launcher-only paths (unreachable during arcade mode)
- Shadow-only writes that never reach hardware in arcade mode (e.g., `PAL_setColor` writes SGDK shadow but SGDK VBlank is bypassed, so shadow never commits to CRAM)
- Disabled assembly paths (Build 329 `rts` guard)

---

## 2. Full Active VDP Write Site Census

### 2.1 VBlank commit functions (already counted, excluded from this census)

| Function | File | VDP target |
|----------|------|-----------|
| `genesistan_pc080sn_commit_planes` | startup_trampoline.s:879 | VRAM 0xC000 (BG), VRAM 0xE000 (FG) |
| `genesistan_palette_commit_asm` | startup_trampoline.s:94 | CRAM (64 entries) |
| `genesistan_scroll_commit_vdp` | main.c:1775 | VRAM 0xF000 (HScroll), VSRAM |

### 2.2 Additional write sites found

#### A. `_VINT_arcade_mode` display bracket (sega.s:260, 281)
- `move.w #0x8134, 0x00C00004` — VDP reg 1: display OFF
- `move.w #0x8174, 0x00C00004` — VDP reg 1: display ON
- Mechanism: direct control port write
- Per frame: YES (every VBlank)
- Writes presentation state: NO (display enable/disable bracket only; no VRAM/CRAM/VSRAM data)

#### B. `genesistan_render_sprites_vdp()` (main.c:1957) via hook
- Called from: `genesistan_hook_frontend_sprite_sat_refresh()` (main.c:1951), which is a `.text.patcher` hook replacing arcade ROM SAT-refresh code
- `VDP_setSpriteFull()` × N — writes to SGDK sprite shadow RAM (NOT directly to VDP)
- **`VDP_updateSprites(sprite_count, DMA)`** — triggers immediate DMA from sprite shadow to VRAM 0xF800 (SAT)
- `VDP_waitDMACompletion()` — waits for DMA completion
- `refresh_frontend_sprite_palettes_mapped()` → `PAL_setColor()` × 64 — writes SGDK palette shadow ONLY; does NOT reach CRAM (SGDK VBlank bypassed; `VBlankProcess = 0`)
- Mechanism: SGDK DMA helper → immediate DMA to VDP
- Per frame: YES (every arcade tick via hook)
- Writes presentation state: YES — SAT at VRAM 0xF800

#### C. `force_clean_vram_init()` (main.c:2084)
- Full VRAM clear (32768 words to 0x0000)
- Full CRAM clear (64 words to 0x0000)
- Full VSRAM clear (40 words to 0x0000)
- 19 VDP register writes
- Mechanism: direct port writes (CPU)
- Per frame: NO — called once at arcade handoff only (main.c:2150)

#### D. `apply_post_reset_test_palette()` (main.c:2219)
- CRAM write loop (test palette)
- Mechanism: direct port writes (CPU)
- Per frame: NO — called once at arcade handoff only (main.c:2151)

#### E. `genesistan_sync_title_vdp_layout()` (main.c:1442)
- `VDP_setPlaneSize(64, 32, FALSE)` — VDP reg 16
- `VDP_setBGAAddress()` — VDP reg 2
- `VDP_setBGBAddress()` — VDP reg 4
- `VDP_setSpriteListAddress()` — VDP reg 5
- `VDP_setWindowOff()` — VDP regs 17, 18 (overwritten by `force_clean_vram_init()` immediately after)
- Per frame: NO — called once at arcade handoff only (main.c:2147)

#### F. `genesistan_preload_scene_tiles()` (main.c:1607)
- `VDP_loadTileData()` + `VDP_waitDMACompletion()` — DMA tile data to VRAM
- Per frame: NO — init-time call only; the tick-phase path in `genesistan_bulk_preload_check` was disabled (Build 334)

#### G. Launcher-only paths (unreachable during arcade mode)
- `restore_launcher_vdp_state()` — `VDP_init()`, `PAL_setPalette()` × 4, `VDP_loadFontData()`, `VDP_loadTileSet()`, `VDP_updateSprites()`
- `genesistan_run_title_init_sequence()` — `VDP_drawTextEx()`, `VDP_setTileMapXY()`, `VDP_fillTileMapRect()`, `VDP_clearPlane()`, `PAL_setColors()`, `VDP_loadTileData()`
- `genesistan_sprite_tile_prepare()` — `VDP_loadTileData()`, `PAL_setColor()`
- None of these are reachable once `arcade_vblank_active = 1` and `current_screen = SCREEN_FRONTEND_LIVE`

#### H. `genesistan_render_sprites_vdp_asm` (startup_trampoline.s:212) — DISABLED
- First instruction is `rts` (Build 329 proof guard)
- Entire function body bypassed

#### I. `genesistan_sprite_commit_asm` (startup_trampoline.s:435)
- Direct SAT writes to VRAM 0xF800 via 0xC00000
- Not called from any active code path

---

## 3. Context Classification for Each Active Writer

| Write site | Classification |
|------------|----------------|
| `_VINT_arcade_mode` display bracket (display ON/OFF) | `ACTIVE_VBLANK_COMMIT_PATH` |
| `genesistan_pc080sn_commit_planes` | `ACTIVE_VBLANK_COMMIT_PATH` |
| `genesistan_palette_commit_asm` | `ACTIVE_VBLANK_COMMIT_PATH` |
| `genesistan_scroll_commit_vdp` | `ACTIVE_VBLANK_COMMIT_PATH` |
| `genesistan_render_sprites_vdp()` via hook `genesistan_hook_frontend_sprite_sat_refresh` | `ARCADE_TICK_PATH` |
| `VDP_updateSprites(DMA)` inside above | `ARCADE_TICK_PATH` |
| `PAL_setColor()` × 64 inside above | `ARCADE_TICK_PATH` (shadow only; no hardware write) |
| `force_clean_vram_init()` | `LAUNCHER_ONLY_PATH` (runs once at handoff) |
| `apply_post_reset_test_palette()` | `LAUNCHER_ONLY_PATH` (runs once at handoff) |
| `genesistan_sync_title_vdp_layout()` | `LAUNCHER_ONLY_PATH` (runs once at handoff) |
| `genesistan_preload_scene_tiles()` (handoff) | `LAUNCHER_ONLY_PATH` (runs once at handoff) |
| `restore_launcher_vdp_state()` | `LAUNCHER_ONLY_PATH` |
| `genesistan_run_title_init_sequence()` | `LAUNCHER_ONLY_PATH` |
| `genesistan_sprite_tile_prepare()` | `LAUNCHER_ONLY_PATH` |
| `genesistan_render_sprites_vdp_asm` | `UNUSED_OR_DISABLED_PATH` |
| `genesistan_sprite_commit_asm` (at line 435) | `UNUSED_OR_DISABLED_PATH` |

---

## 4. Active Per-Frame VDP Writers in Current Runtime

Writers that execute every frame during active arcade runtime:

| Function | Executes every frame | In VBlank | Outside VBlank | Writes presentation state |
|----------|---------------------|-----------|----------------|--------------------------|
| `_VINT_arcade_mode` display bracket | YES | YES | NO | NO (reg 1 only) |
| `genesistan_pc080sn_commit_planes` | YES | YES | NO | YES (VRAM nametables) |
| `genesistan_palette_commit_asm` | YES | YES | NO | YES (CRAM) |
| `genesistan_scroll_commit_vdp` | YES | YES | NO | YES (HScroll/VSRAM) |
| `genesistan_render_sprites_vdp()` via hook | YES | YES (inside tick) | NO | YES (SAT VRAM 0xF800 via DMA) |

Note: All five execute within `_VINT_arcade_mode`. The hook fires during `genesistan_run_arcade_tick_lean`, which runs with display OFF between the display-OFF write and the three commit functions.

---

## 5. Are There Any Writers Outside the 3 Commit Functions?

**YES.**

`genesistan_render_sprites_vdp()` (main.c:1957) is an active per-frame VDP writer outside the three commit functions.

- Called by: `genesistan_hook_frontend_sprite_sat_refresh()` (main.c:1951)
- Hook fires: Every arcade tick via patched arcade ROM SAT-refresh codepath
- Active hardware writes:
  - `VDP_updateSprites(sprite_count, DMA)` → immediate DMA from sprite shadow to VRAM 0xF800
  - `VDP_waitDMACompletion()` confirms DMA completes synchronously

- NOT in commit trio
- NOT gated or disabled
- Executes every frame during arcade runtime

**No other uncounted per-frame VDP hardware writes exist.** `PAL_setColor()` calls inside the same function write only to SGDK's internal palette shadow. That shadow is never committed to CRAM during arcade mode because `VBlankProcess = 0` and the SGDK VBlank handler is bypassed by `arcade_vblank_active`.

---

## 6. Tick-Path Direct Port / Helper / DMA Writes

Inside `genesistan_run_arcade_tick_lean` (i.e., during the arcade tick proper, called from `_VINT_arcade_mode`):

| Category | Active | Responsible function(s) |
|----------|--------|-------------------------|
| Direct `0xC00004` writes | NO | None confirmed during tick itself |
| Direct `0xC00000` writes | NO | None confirmed during tick itself |
| `VDP_*` helper calls | YES | `VDP_setSpriteFull()` × N (shadow write, no hardware), `VDP_updateSprites(DMA)` (DMA to SAT) via `genesistan_hook_frontend_sprite_sat_refresh` |
| `PAL_*` helper calls | YES | `PAL_setColor()` × 64 via `refresh_frontend_sprite_palettes_mapped()` inside the hook — shadow write only, does NOT reach CRAM |
| DMA helper calls | YES | `VDP_updateSprites(DMA)` → `VDP_waitDMACompletion()` — immediate DMA to VRAM 0xF800 |

---

## 7. Single Root Cause

**`UNCOUNTED_ACTIVE_VDP_WRITER_OUTSIDE_COMMIT_TRIO`**

`genesistan_render_sprites_vdp()` executes every frame via `genesistan_hook_frontend_sprite_sat_refresh`, triggering `VDP_updateSprites(sprite_count, DMA)` → an immediate DMA from the SGDK sprite shadow table to SAT VRAM 0xF800. This is a per-frame VDP hardware write that is not part of the three audited commit functions and was not counted in the prior commit-count audit. It is the only uncounted per-frame VDP hardware writer.

---

## 8. Single Next Implementation Target

Disable `genesistan_hook_frontend_sprite_sat_refresh` as a proof test by adding a guard at the top of the function (e.g., `return` before `genesistan_render_sprites_vdp()`) to eliminate the uncounted DMA write path. This matches the proof pattern used in Build 329 (disabled `genesistan_render_sprites_vdp_asm`) and Build 334 (disabled `genesistan_bulk_preload_check` DMA path). If rolling display stops with the hook disabled, the uncounted sprite DMA is the cause. If rolling continues, the single remaining writer path (commit trio + display brackets) is presenting changing content from the arcade ROM, and the root must be traced to the FG/BG buffer population path inside the tick.

---

## 9. Final Verdict

The census is complete. Four functions write to VDP hardware every frame: the three commit functions plus `genesistan_render_sprites_vdp()` via `genesistan_hook_frontend_sprite_sat_refresh`. This fourth writer (DMA to SAT VRAM 0xF800) was not counted in prior audits. It is the single uncounted active per-frame VDP writer. `PAL_setColor()` calls in the same hook write only to SGDK shadow and do not reach CRAM. All other write paths are init-only or launcher-only.
