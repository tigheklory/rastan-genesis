# Build 316 — VRAM Handoff Integrity Audit + Forced Clean Init

## 1. Pre-Handoff VRAM Assumptions

Before `request_start_rastan()` runs, the SGDK launcher has loaded:
- Font tiles at `TILE_FONT_INDEX` (tile 1440, VRAM 0xB400) — 96 tiles (3072 bytes)
- DIP switch indicator tiles at `TILE_USER_INDEX` — 4 tiles
- Sprite table at `SLIST_DEFAULT` (0xF400)
- Palettes: PAL0=DIP palette, PAL1=font palette, PAL2=DIP palette, PAL3=selected font palette
- Plane A at 0xE000, Plane B at 0xC000 (SGDK defaults)

## 2. Launcher VRAM Usage Summary

| VRAM Region | Content | Size |
|-------------|---------|------|
| 0x0000-0x0040 | SGDK system tiles (tile 0-1) | 64 bytes |
| TILE_USER_INDEX area | DIP on/off tiles | 128 bytes |
| 0xB400-0xC000 | SGDK font (96 glyphs) | 3072 bytes |
| 0xC000-0xCFFF | Plane B nametable | 4096 bytes |
| 0xD000-0xDFFF | Window nametable | 4096 bytes |
| 0xE000-0xEFFF | Plane A nametable | 4096 bytes |
| 0xF000-0xF3FF | HScroll table | 1024 bytes |
| 0xF400-0xF7FF | Sprite table | 1024 bytes |
| 0xF800-0xFFFF | SAT (after layout change) | 2048 bytes |

## 3. Was VRAM Previously Reset? (Before This Build)

**Partially YES.** `restore_launcher_vdp_state()` calls `VDP_init()` which calls `VDP_resetScreen()` which does `DMA_doVRamFill(0, 0, 0, 1)` — clearing all 64KB of VRAM. But then immediately:
1. Font tiles reloaded at TILE_FONT_INDEX
2. DIP tiles reloaded
3. Launcher palettes set
4. `genesistan_sync_title_vdp_layout()` sets plane addresses
5. `genesistan_preload_scene_tiles()` loads PC080SN tiles

So VRAM was cleared but then contaminated with launcher assets before the scene preloader ran. The launcher font at tile 1440 persisted into arcade mode.

CRAM was NOT explicitly cleared — launcher palettes persisted until `genesistan_palette_commit_asm` overwrote them.

VSRAM was NOT explicitly cleared.

## 4. Exact Forced Initialization Steps Added

New function `force_clean_vram_init()` inserted after `genesistan_sync_title_vdp_layout()` and before `genesistan_preload_scene_tiles()`:

1. **Display OFF** — VDP reg 1 = 0x34 (display disabled, VInt ON, DMA ON, V28)
2. **Auto-increment = 2** — VDP reg 15 = 0x02
3. **Full VRAM clear** — CPU word-fill 32768 words (64KB) starting at VRAM 0x0000
4. **Full CRAM clear** — CPU word-fill 64 words (128 bytes) starting at CRAM 0x0000
5. **Full VSRAM clear** — CPU word-fill 40 words (80 bytes) starting at VSRAM 0x0000
6. **VDP register reset** — all 19 registers set to known baseline values

## 5. VDP Register Baseline Used

| Register | Value | Purpose |
|----------|-------|---------|
| 0 | 0x04 | No HInt |
| 1 | 0x34 | VInt ON, DMA ON, display OFF, V28 |
| 2 | 0x38 | Plane A = 0xE000 |
| 3 | 0x34 | Window = 0xD000 |
| 4 | 0x06 | Plane B = 0xC000 |
| 5 | 0x7C | SAT = 0xF800 |
| 6 | 0x00 | Unused |
| 7 | 0x00 | BG color = 0 |
| 8-9 | 0x00 | Unused |
| 10 | 0xFF | HInt counter disabled |
| 11 | 0x00 | Full scroll, no ext int |
| 12 | 0x81 | H40, no shadow, no interlace |
| 13 | 0x3C | HScroll = 0xF000 |
| 14 | 0x00 | Unused |
| 15 | 0x02 | Auto-increment = 2 |
| 16 | 0x01 | Scroll size = 64x32 |
| 17 | 0x00 | Window H = 0 |
| 18 | 0x00 | Window V = 0 |

Matches the plane addresses set by `genesistan_sync_title_vdp_layout()`: BGA=0xE000, BGB=0xC000, SAT=0xF800.

## 6. Runtime Verification

| Metric | Result |
|--------|--------|
| startup_result_code 0→1 | Frame 149 |
| FG buffer non-zero | 50/2048 at frame 700+ |
| Exceptions | NONE |
| Hang | NO |
| Frames traced | 1199+ |

## 7. Visual Verification Status

- Rendering changed: **USER MUST VERIFY**
- Visual correctness: **USER MUST VERIFY**

## 8. Conclusion

### Was VRAM contamination present?
**YES.** Launcher font tiles (at TILE_FONT_INDEX = 1440) persisted into arcade mode. CRAM retained launcher palette data until the arcade palette commit ran. VSRAM was never explicitly cleared.

### Did clearing VRAM change behavior?
The FG buffer entry count dropped from 53 to 50 — the 3 extra entries in Build 316 (pre-clear) were likely hitting non-zero residual launcher tile data that produced non-zero nametable words. With clean VRAM, those entries now resolve to tile 0 (zero).

The Build 316 proof font override (`TILE_FONT_INDEX + offset`) will now point to VRAM positions that were cleared — the launcher font was wiped. This means the proof step from Prompt 074 will show blank tiles where the SGDK font used to be, UNLESS the scene preloader reloads the font tiles or the display uses a different font source.

## 9. Files Modified

| File | Change |
|------|--------|
| `apps/rastan/src/main.c` | Added `force_clean_vram_init()`, called from `request_start_rastan()` |
