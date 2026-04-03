# Build 315 — Title/Attract Tilemap Producer Hook

## 1. Executive Summary

Build 315 hooks the real title/attract tilemap producer into the existing WRAM tilemap staging system. The title screen text writers (`genesistan_hook_text_writer_3bb48_impl` and `genesistan_hook_text_writer_3c3fe`) were writing directly to VDP via `VDP_setTileMapXY(BG_A, ...)`, completely bypassing the WRAM buffers. This build redirects `rastan_draw_tile_xy()` to write to `pc080sn_fg_buffer` instead, and removes the mode4 gate so the commit fires every frame.

## 2. Why the Previous Hooks Were Not the Right Producer

The PC080SN tilemap hooks at arcade addresses 0x055968/0x055990 only fire during gameplay (mode4 >= 2). During title/attract mode, the arcade runs through a different code path:

- `genesistan_run_title_init_sequence()` calls arcade `0x03B098` (title_init_block)
- The title_init_block dispatches to text writer functions at `0x03BB48` and `0x03C3FE`
- These are patched to Genesis hooks: `genesistan_hook_text_writer_3bb48_impl()` and `genesistan_hook_text_writer_3c3fe()`
- Both hooks call `rastan_draw_tile_xy()` which was writing directly to VDP

The PC080SN gameplay hooks and the title text writer hooks are completely independent code paths.

## 3. Actual Title/Attract Tilemap Producer Identified

| Function | File | Line | Purpose |
|----------|------|------|---------|
| `genesistan_hook_text_writer_3bb48_impl()` | main.c | 1641 | Primary title text writer |
| `genesistan_hook_text_writer_3c3fe()` | main.c | 1717 | Secondary C-window title text writer |
| `rastan_draw_tile_xy()` | main.c | 1307 | Common output function (was VDP, now WRAM buffer) |

Both text writers ultimately call `rastan_draw_tile_xy(tile_attr, x, y)`.

## 4. Proof It Runs in Title/Attract Mode

MAME headless trace with START injection at frame 120:

| Frame | BG nonzero | FG nonzero |
|-------|------------|------------|
| 200   | 0/2048     | 0/2048     |
| 300   | 0/2048     | 0/2048     |
| 400   | 0/2048     | 0/2048     |
| 500   | 0/2048     | 0/2048     |
| 600   | 0/2048     | 0/2048     |
| 700   | 0/2048     | **50/2048** |
| 800   | 0/2048     | **50/2048** |
| 1000  | 0/2048     | **50/2048** |

FG buffer becomes non-zero at ~frame 700 (during title/attract, before gameplay). The 50 non-zero words correspond to title text entries written by the text writer hooks.

BG buffer remains zero — expected, as the title screen has no BG plane tilemap producer.

## 5. Exact Hook Added

### rastan_draw_tile_xy() (main.c line 1307)

**Before:**
```c
void rastan_draw_tile_xy(u16 tile_attr, int x, int y)
{
    if (x < 0 || x >= 64 || y < 0 || y >= 32)
        return;
    VDP_setTileMapXY(BG_A, tile_attr, (u16)x, (u16)y);
}
```

**After:**
```c
extern u16 pc080sn_fg_buffer[];

void rastan_draw_tile_xy(u16 tile_attr, int x, int y)
{
    if (x < 0 || x >= 64 || y < 0 || y >= 32)
        return;
    pc080sn_fg_buffer[y * 64 + x] = tile_attr;
}
```

### genesistan_pc080sn_commit_planes (startup_trampoline.s)

Removed mode4 gate (`cmpi.w #2, 4(%a0)` / `blt .Lcommit_skip`). Commit now fires unconditionally every VBlank, streaming both buffers regardless of arcade mode state.

## 6. How It Feeds the Existing WRAM Tilemap Buffers

```
Title/Attract Mode:
  text writer hooks
    → rastan_draw_tile_xy(tile_attr, x, y)
      → pc080sn_fg_buffer[y * 64 + x] = tile_attr
        → genesistan_pc080sn_commit_planes (VBlank)
          → streams FG buffer to VRAM 0xE000

Gameplay Mode:
  PC080SN hooks (0x055968/0x055990)
    → assembly buffer writers
      → pc080sn_bg_buffer / pc080sn_fg_buffer
        → genesistan_pc080sn_commit_planes (VBlank)
          → streams both buffers to VRAM
```

Both paths feed the same WRAM buffers. One commit routine serves both modes.

## 7. Buffer Verification Results

- BG buffer non-zero in title/attract: **NO** (no BG producer in title mode)
- FG buffer non-zero in title/attract: **YES** (50/2048 words at frame 700+)

## 8. Build 315 Verification

| Check | Result |
|-------|--------|
| Assembly compiled | YES |
| Link succeeded | YES |
| ROM produced | `dist/Rastan_315.bin` (3,799,266 bytes) |
| Postpatch | 29 warnings (pre-existing) |
| startup_result_code 0→1 | Frame 140 |
| arcade_mode4 changes | YES |
| Exceptions | NONE |
| Hang | NO |
| Frames traced | 1499 |

## 9. Visual Verification Status

Visual correctness: **USER MUST VERIFY**

## 10. Remaining Issues

- BG plane (0xC000) has no producer in title/attract mode — buffer streams zeros. This is expected (title screen uses FG plane only for text).
- The text writers produce only ~50 non-zero tile entries out of 2048 — consistent with title text being sparse.
- Full-plane streaming continues (4096 words per frame) — performance unchanged from Build 313.

## 11. Files Modified

| File | Change |
|------|--------|
| `apps/rastan/src/main.c` | `rastan_draw_tile_xy()` writes to `pc080sn_fg_buffer` instead of VDP |
| `apps/rastan/src/startup_trampoline.s` | Removed mode4 gate from commit routine |
