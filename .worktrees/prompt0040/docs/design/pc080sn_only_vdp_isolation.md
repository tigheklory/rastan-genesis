# PC080SN-Only VDP Isolation Patcher

## Purpose

Build-time post-processing tool that disables all non-PC080SN VDP activity by replacing selected functions with RTS (return-immediately). This isolates the PC080SN tilemap rendering pipeline for debugging — any visual output on screen is exclusively from the tilemap commit path.

## Usage

```bash
# Standard isolation (black screen, use VRAM debugger)
python tools/debug/patch_disable_vdp_except_pc080sn.py \
    --input  dist/Rastan_318.bin \
    --output dist/Rastan_318_pc080sn_only.bin \
    [--symbols apps/rastan/out/symbol.txt] \
    [--disable-text]

# Isolation with visible debug palette
python tools/debug/patch_disable_vdp_except_pc080sn.py \
    --input  dist/Rastan_318.bin \
    --output dist/Rastan_318_pc080sn_only_debug_palette.bin \
    --apply-debug-palette \
    [--symbols apps/rastan/out/symbol.txt] \
    [--disable-text]
```

## Functions Disabled (Always)

| Function | Purpose | Effect When Disabled |
|----------|---------|---------------------|
| `genesistan_palette_commit_asm` | CLCS→CRAM palette conversion + write | RTS'd (standard mode) or replaced with debug CRAM writer (debug palette mode) |
| `genesistan_scroll_commit_vdp` | HScroll + VSRAM commit from staging | Scroll registers stay at 0 (no scrolling) |
| `genesistan_sprite_commit_asm` | Sprite attribute table commit | SAT stays empty (no sprites visible) |

## Functions Disabled (--disable-text)

| Function | Purpose | Effect When Disabled |
|----------|---------|---------------------|
| `genesistan_hook_text_writer_3bb48_impl` | Title/attract text writer | No title text in FG nametable |
| `genesistan_hook_text_writer_3c3fe` | Secondary C-window text writer | No secondary text in FG nametable |

## Functions Preserved (Never Patched)

| Function | Purpose |
|----------|---------|
| `genesistan_pc080sn_commit_planes` | WRAM buffer → VRAM tilemap streaming (BG + FG planes) |
| VDP init / display enable-disable | Required for basic Genesis operation |

## Patch Method

For each target function:
1. Locate address via `symbol.txt` (nm-format symbol table)
2. Overwrite first word with `0x4E75` (RTS — immediate return)
3. Fill next 16 bytes with `0x4E71` (NOP — neutralize prologue)

No function sizes or layouts are changed. The RTS causes immediate return before any VDP I/O.

## Expected Visual Outcomes

### Default mode (no --disable-text, no --apply-debug-palette)
- **CRAM**: all black (no palette commit)
- **Sprites**: none visible (no SAT commit)
- **Scroll**: fixed at origin (no scroll commit)
- **Tilemaps**: PC080SN nametable data IS committed to VRAM
- **Screen appearance**: black (tiles present in VRAM but no palette = all colors are black). Use VRAM debugger to inspect tile data.

### With --disable-text
- Same as above, plus title/attract text hooks are disabled
- FG nametable contains only PC080SN tilemap data (no text overlay)

### With --apply-debug-palette
- **CRAM**: filled with fixed diagnostic palette (4 lines, distinct hues)
- **Sprites**: none visible (no SAT commit)
- **Scroll**: fixed at origin (no scroll commit)
- **Tilemaps**: PC080SN nametable data IS committed to VRAM
- **Screen appearance**: tiles visible with diagnostic colors, making nametable population directly observable

---

## Fixed Debug Palette Mode

### Purpose

When `--apply-debug-palette` is used, the palette commit function is replaced with a minimal 68000 routine that writes 64 fixed debug palette entries to CRAM every frame. This makes tile data visible in the emulator's main display without needing the VRAM debugger.

### How It Works

1. The 64-entry debug palette is written into the first 64 entries of `genesistan_palette_rom_table` in the ROM image
2. `genesistan_palette_commit_asm` is replaced with a 34-byte inline routine that streams those 64 words from the ROM table to CRAM via the VDP data port
3. The replacement routine runs every VBlank (same call site), writing the fixed palette each frame

### Exact Palette Table

64 entries, 4 palette lines of 16 entries each. Genesis format: `0000 BBB0 GGG0 RRR0`.

| Line | Entries | Dominant Hue | Purpose |
|------|---------|-------------|---------|
| 0 | 0-15 | Red → warm | Identify palette line 0 usage |
| 1 | 16-31 | Green → cyan | Identify palette line 1 usage |
| 2 | 32-47 | Blue → purple | Identify palette line 2 usage |
| 3 | 48-63 | Yellow → orange | Identify palette line 3 usage |

Entry 0 of each line is black (transparent). Entry 15 of each line is white. Intermediate entries ramp through the line's hue.

**Line 0 — Red/Warm (entries 0-15):**

| Index | R | G | B | Genesis Word | Color |
|-------|---|---|---|-------------|-------|
| 0 | 0 | 0 | 0 | 0x0000 | Black |
| 1 | 1 | 0 | 0 | 0x0002 | Dark red |
| 2 | 2 | 0 | 0 | 0x0004 | |
| 3 | 3 | 0 | 0 | 0x0006 | |
| 4 | 4 | 0 | 0 | 0x0008 | |
| 5 | 5 | 0 | 0 | 0x000A | |
| 6 | 6 | 0 | 0 | 0x000C | |
| 7 | 7 | 0 | 0 | 0x000E | Bright red |
| 8 | 7 | 1 | 0 | 0x002E | Red-orange |
| 9 | 7 | 2 | 0 | 0x004E | |
| 10 | 7 | 3 | 0 | 0x006E | |
| 11 | 7 | 4 | 0 | 0x008E | |
| 12 | 7 | 5 | 1 | 0x02AE | |
| 13 | 7 | 6 | 2 | 0x04CE | |
| 14 | 7 | 7 | 3 | 0x06EE | |
| 15 | 7 | 7 | 7 | 0x0EEE | White |

**Line 1 — Green/Cyan (entries 16-31):**

| Index | R | G | B | Color |
|-------|---|---|---|-------|
| 0 | 0 | 0 | 0 | Black |
| 1-7 | 0 | 1-7 | 0 | Dark→bright green |
| 8-14 | 0-4 | 7 | 1-7 | Green→cyan→white |
| 15 | 7 | 7 | 7 | White |

**Line 2 — Blue/Purple (entries 32-47):**

| Index | R | G | B | Color |
|-------|---|---|---|-------|
| 0 | 0 | 0 | 0 | Black |
| 1-7 | 0 | 0 | 1-7 | Dark→bright blue |
| 8-14 | 1-7 | 0-4 | 7 | Blue→purple→white |
| 15 | 7 | 7 | 7 | White |

**Line 3 — Yellow/Orange (entries 48-63):**

| Index | R | G | B | Color |
|-------|---|---|---|-------|
| 0 | 0 | 0 | 0 | Black |
| 1-7 | 1-7 | 1-7 | 0 | Dark→bright yellow |
| 8-14 | 7-5 | 6-1 | 0-1 | Yellow→orange |
| 15 | 7 | 7 | 7 | White |

### Why This Palette

- **Hue separation by line**: Red/green/blue/yellow makes it immediately obvious which palette line a tile is using
- **Brightness ramp within each line**: Shows whether tiles use low or high color indices
- **Entry 0 = black**: Transparent tiles remain invisible (standard Genesis behavior)
- **Entry 15 = white in all lines**: Provides a common reference point
- **No grayscale ambiguity**: Every non-black color has a clear hue

### What This Mode Can Prove

- Whether PC080SN tilemap data is reaching VRAM nametables
- Which palette lines tiles are assigned to
- Whether tile indices are in valid ranges
- Whether nametable population covers the expected screen area
- Whether corruption is in tile data vs. palette vs. nametable layout

### What This Mode Cannot Prove

- Correctness of actual game palette colors (this is a synthetic diagnostic palette)
- Correctness of scroll behavior (scroll commit is disabled)
- Correctness of sprite rendering (sprite commit is disabled)
- Correctness of palette conversion logic (CLCS→Genesis path is bypassed)
- Visual fidelity compared to the arcade original

---

## Notes

- This is a build-time ROM patching tool — no runtime source files are modified
- The patched ROM is a separate file; the original is not changed
- `rastan_draw_tile_xy` is a static (non-exported) function and cannot be patched via this tool; use `--disable-text` to disable its callers instead
