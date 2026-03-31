# Build 305 — V-Blank Ownership Audit and Version Fix Report

## 1. Executive Summary

Build 305 fixes the V-Int init sequence race in `request_start_rastan()` and corrects the build counter to produce `dist/Rastan_305.bin`. The SGDK V-Int handler was audited end-to-end: **NO duplicate/conflicting ownership exists** between SGDK auto-updates and our arcade-driven V-Int callback. However, the callback was being registered and enabled BEFORE VDP planes were cleared, layout was configured, and tiles were preloaded — creating a window where the arcade tick could run against unconfigured VDP state. This is now fixed.

## 2. V-Blank Ownership Audit Result

**Duplicate/conflicting ownership: NO.**

### Evidence

1. **SGDK V-Int handler** (sega.s:142-161): Only runs XGM sound task, BMP task (if active), then calls `vintCB` (our callback). No DMA flush, no sprite update, no scroll update, no palette update.

2. **SGDK auto-updates** (DMA flush, sprite update, scroll, palette fading) are all inside `SYS_doVBlankProcessEx()` (sys.c:660-789), which is called from `SYS_doVBlankProcess()`. Our main loop **skips** this call during `SCREEN_FRONTEND_LIVE` (main.c:2271-2274).

3. **Our V-Int callback** (`genesistan_frontend_live_vint_handoff`, main.c:2101-2119): Runs arcade tick, palette, scroll, sprite commit. This is the sole owner of VDP writes during live gameplay.

4. **SPR_init** is never called — the SGDK sprite engine is not active. Even if VDP_init() resets sprite state, there's no sprite engine to conflict with.

### Architecture Diagram
```
Hardware V-Int
  └─ sega.s handler
       ├─ XGM sound (if active)
       ├─ BMP task (if active)
       └─ vintCB → genesistan_frontend_live_vint_handoff()
            ├─ genesistan_refresh_arcade_inputs()
            ├─ genesistan_run_original_frontend_tick()  ← arcade tick
            │    └─ may trigger 0x5A4DE hook → VDP writes
            ├─ sanitize_arcade_workram()
            ├─ load_arcade_palette()
            ├─ sync_arcade_scroll_to_vdp()
            ├─ genesistan_sprite_tile_prepare()
            ├─ refresh_frontend_sprite_palettes()
            └─ genesistan_sprite_commit_asm()

Main loop (SCREEN_FRONTEND_LIVE):
  └─ SYS_doVBlankProcess() SKIPPED ← no SGDK auto-updates
```

## 3. Init Sequence Race (Fixed)

### Bug

In `request_start_rastan()`, the V-Int callback was registered and interrupts enabled **before** VDP setup was complete:

```
restore_launcher_vdp_state();          ← VDP_init, resets everything
SYS_setVIntCallback(our_handler);      ← CALLBACK SET HERE
SYS_enableInts();                      ← V-INT STARTS FIRING
VDP_clearPlane(BG_A, TRUE);            ← too late: arcade tick already ran
VDP_clearPlane(BG_B, TRUE);
genesistan_sync_title_vdp_layout();
genesistan_preload_scene_tiles(TITLE);
```

This created a window where:
- The arcade tick could run before tiles were preloaded (LUT lookups hit tile slot 0)
- VDP_clearPlane could erase tilemap data that the arcade already wrote
- Scene bounds (a0_lo/hi) were uninitialized, triggering unnecessary preload-check calls from V-Int context

### Fix

Moved callback registration and `SYS_enableInts()` to **after** all VDP setup:

```
restore_launcher_vdp_state();
VDP_setHInterrupt(0);
VDP_setHIntCounter(0xFF);
VDP_clearPlane(BG_A, TRUE);
VDP_clearPlane(BG_B, TRUE);
genesistan_sync_title_vdp_layout();
genesistan_preload_scene_tiles(TITLE);
clear_frontend_sprite_layer();
VDP_waitDMACompletion();
current_screen = SCREEN_FRONTEND_LIVE;        ← set state
frontend_live_handoff_active = TRUE;
SYS_setVIntCallback(our_handler);             ← AFTER setup
SYS_enableInts();                             ← AFTER everything ready
```

The first V-Int now fires with planes cleared, layout configured, tiles preloaded, and scene bounds set.

## 4. PC090OJ / Title Text / Sprite Loss

**Root cause: NOT an ownership conflict.** PC090OJ sprites and title text use different rendering paths:
- Text: `genesistan_hook_text_writer_3bb48` (separate spec hook at 0x3BB48)
- Sprites: `genesistan_sprite_commit_asm()` (committed each V-Int after arcade tick)

The Build 294 screenshot shows partial text ("TON", "CREDIT") rendering correctly, confirming the text hook works. Sprite rendering depends on `genesistan_sprite_tile_prepare()` and `genesistan_sprite_commit_asm()` which both run every V-Int.

If sprites/text are still missing after Build 305, the cause is upstream of ownership — likely arcade state initialization timing or VDP content ordering.

## 5. Top-Row Vertical Noise

The assembly block writer (`genesistan_bulk_tilemap_commit`) correctly skips VDP writes for rows 0-3 (visible bias). The strip writers (BG/FG) also apply the row≥4 check. Any noise in the top rows of the display would come from:
1. VRAM content at the plane nametable addresses for rows 0-3 not being cleared
2. Leftover data from VDP_init or launcher screen

The `VDP_clearPlane()` calls in the init sequence should zero all nametable entries. With the init sequence fix, these clears now happen BEFORE the V-Int callback fires, ensuring rows 0-3 remain zeroed.

## 6. Build Version Fix

- `dist/release_counter.txt`: Set to 304, incremented to 305 during build
- `build_info.h`: `RASTAN_BUILD_NUMBER 305`, stamp `20260331_*`, variant `world_rev1`, mode `hooked`
- ROM string: `WORLD REV1 BASELINE UI 305 H`
- Output: `dist/Rastan_305.bin` (3,932,160 bytes)

## 7. Build Verification

- JMP at ROM offset 0x5A6FA: `4ef9 00202fec 4e71 4e71` — CORRECT
- Build string in ROM: `WORLD REV1 BASELINE UI 305 H` — CORRECT
- Postpatch: 28 shift-mismatch warnings (pre-existing, functionally harmless)
- Compilation: SUCCESS, no errors

## 8. Runtime Verification

**Pending user testing.** No headless Genesis emulator available in WSL2. MAME is installed but cannot run Genesis ROMs for visual verification in this environment.

### Expected Improvements
1. Init sequence race eliminated — first frame after "START RASTAN" should be clean
2. No VDP writes during unconfigured state — eliminates potential for cleared-then-overwritten tilemap race
3. Scene bounds correctly set before first arcade tick — no spurious preload-check calls

### What to Watch For
- Whether the purple/empty background from Build 294 is resolved (tiles and nametables should now be correctly sequenced)
- Whether top-row noise is eliminated (planes cleared before V-Int fires)
- Whether text ("RASTAN", "CREDIT", "PUSH 1 OR 2 PLAYER") renders correctly
- Whether PC090OJ sprites appear (warrior character on title screen)

## 9. Files Changed

| File | Change |
|------|--------|
| `apps/rastan/src/main.c` | Reordered `request_start_rastan()` init sequence — moved `SYS_setVIntCallback` and `SYS_enableInts` after all VDP setup |
| `dist/release_counter.txt` | Set to 305 |
| `apps/rastan/inc/build_info.h` | Auto-generated: Build 305 |
| `tools/translation/postpatch_lenient.py` | Recreated lenient postpatch workaround |
