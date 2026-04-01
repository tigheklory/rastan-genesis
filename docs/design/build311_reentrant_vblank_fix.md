# Build 311 — Re-entrant VBlank Hazard Fix

## 1. Executive Summary

Build 311 removes `SYS_disableInts()` / `SYS_enableInts()` calls from three C functions that execute inside `_VINT_arcade_mode`. These calls were a re-entrant VBlank hazard: `SYS_enableInts()` re-enables interrupts while still inside the VBlank handler, allowing a new VBlank to fire before the current one completes.

## 2. The Hazard

When `_VINT_arcade_mode` calls a C function that internally calls `SYS_enableInts()`, the 68000's interrupt mask is cleared (SR bits 10-8 set to 000). If the next VBlank fires before the current handler returns via `rte`, a second `_VINT_arcade_mode` begins executing on top of the first — corrupting the arcade state machine, doubling VDP writes, and potentially overflowing the stack.

The three functions inherited their `SYS_disableInts()` / `SYS_enableInts()` pairs from when they ran in the main loop or via SGDK's `vintCB` callback, where protecting VDP access from VBlank interruption was necessary. In Build 310's arcade-owned model, these functions only execute *during* VBlank (called from `_VINT_arcade_mode`), so the protection is unnecessary and the re-enable is actively dangerous.

## 3. Functions Modified

### `genesistan_hook_text_writer_3bb48_impl` (main.c)

Text writer for arcade text at hook address 0x03BB48. Writes character tiles to VDP plane A via `rastan_draw_tile_xy()`.

**Removed:** `SYS_disableInts()` before tile loop, `SYS_enableInts()` after loop.

### `genesistan_hook_text_writer_3c3fe` (main.c)

Text writer for arcade text at hook address 0x03C3FE. Writes character tiles to VDP plane A via `rastan_draw_tile_xy()`.

**Removed:** `SYS_disableInts()` before tile loop, `SYS_enableInts()` after loop.

### `genesistan_preload_scene_tiles` (main.c)

Scene tile preloader. DMA-loads tiles into VRAM based on a manifest, then waits for DMA completion.

**Removed:** `SYS_disableInts()` before DMA loop, `SYS_enableInts()` after `VDP_waitDMACompletion()`.

## 4. What Was NOT Changed

- Other `SYS_disableInts()` / `SYS_enableInts()` pairs in launcher-path functions (lines 611/624, 648/651, 660/663, 1066/1074, 1139/1147, 1430/1436, 1849/1851, 1866/1870, 2114) — these only execute in launcher mode, not from `_VINT_arcade_mode`.
- No assembly changes.
- No logic changes to any function — only the interrupt toggle calls removed.

## 5. Build 311 Verification

| Check | Result |
|-------|--------|
| Build succeeded | YES |
| ROM produced | `dist/Rastan_311.bin` (3,932,160 bytes) |
| Postpatch warnings | 28 (pre-existing, applied anyway) |
| Compiler warnings | 5 unused-function (pre-existing) |

## 6. Runtime Verification (MAME Trace, 622 frames)

| Metric | Result |
|--------|--------|
| `startup_result_code` 0→1 | Frame 214 |
| VDP writes begin | Frame 240 (pre-launch init) |
| VDP write frequency | Every frame (every 30-frame sample) |
| `arcade_mode4` reaches 2 | Frame 600 |
| `arcade_page2` set | Frame 598 |
| Hang detected | NO |
| Total frames | 622 |

### Structural Verification

| Check | Result |
|-------|--------|
| `_VINT_arcade_mode` fast path active | YES |
| No SYS_enableInts in arcade VBlank path | YES — all three functions cleaned |
| Arcade state machine progressing | YES — mode4 cycling, page2 set |
| VDP writes continuous | YES — 24,036 VDP port writes across 622 frames |

## 7. Remaining Issues

- Visual verification requires BlastEm or visual MAME run
- 5 retired C functions still defined but unused (pre-existing cleanup candidate)
- Remaining `SYS_disableInts()`/`SYS_enableInts()` pairs in launcher-path functions are correct and necessary for that context
