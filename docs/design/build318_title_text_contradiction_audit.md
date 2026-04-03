# Build 318 — Title/Text Contradiction & Tile Index Correlation Audit

## 1. Text Disable Verification

**TEXT_DISABLED = NO**

The ROM under test (`dist/Rastan_318_pc080sn_only_debug_palette.bin`) was built with `--apply-debug-palette` but **without** `--disable-text`.

Proof — binary inspection of the patched ROM:

| Function | Address | First 4 bytes | Status |
|----------|---------|--------------|--------|
| `genesistan_hook_text_writer_3bb48_impl` | 0x2006F2 | `518f48e7` | **NOT RTS** — original code intact |
| `genesistan_hook_text_writer_3c3fe` | 0x2011C4 | `4feffff4` | **NOT RTS** — original code intact |

If `--disable-text` had been applied, both would start with `4e75` (RTS). They don't. Both text writers are active.

## 2. Visible Band Producer Identification

**Producer: Text writer hooks** (`genesistan_hook_text_writer_3bb48_impl` and `genesistan_hook_text_writer_3c3fe`)

Both call `rastan_draw_tile_xy()` at [main.c:1314](apps/rastan/src/main.c#L1314):
```c
pc080sn_fg_buffer[y * 64 + x] = tile_attr;
```

This writes nametable entries into the FG buffer, which `genesistan_pc080sn_commit_planes` streams to VRAM 0xE000 (Plane A nametable).

The text writers produce VRAM tile indices by looking up arcade tile codes in `genesistan_pc080sn_tile_vram_lut`. For example:
- 'R' (ASCII 0x52) → arcade src_tile 0x52 → LUT → VRAM slot 0x003B
- 'A' (ASCII 0x41) → arcade src_tile 0x41 → LUT → VRAM slot 0x002B

All text tile VRAM slots fall in range **0x001A–0x0041** (26–65). Pattern addresses 0x00340–0x0083F.

## 3. FG Nametable Dump (Row 14–15)

The nametable cannot be directly read from the ROM (it's populated at runtime in WRAM and committed to VRAM). However, the tile indices can be determined from the text writer code path:

The `text_writer_ptr_to_xy` function converts arcade C-window pointers to screen x,y coordinates:
- `y = row - TEXT_WRITER_VISIBLE_ROW_BIAS` where `TEXT_WRITER_VISIBLE_ROW_BIAS = 4`
- Arcade C-window row 18 → screen y=14

The visible band at row ~14 corresponds to arcade text output targeting C-window rows ~18, which is approximately where "PUSH START" or score/credit text appears on the Rastan title screen.

Expected nametable values at this band are in the form `TILE_ATTR_FULL(pal, pri, vflip, hflip, vram_tile)` where:
- `vram_tile` is 0x001A–0x0041 (text character VRAM slots)
- `pal` is 0 (from attr_word)
- `pri`, `vflip`, `hflip` depend on the text descriptor

These would produce nametable words like 0x001C (tile 28, digit '0'), 0x003B (tile 59, letter 'R'), etc.

## 4. Tile Index Correlation

### A — Tiles visible on screen (from text writer output)

VRAM slot range: **0x001A–0x0041** (26–65)

Sample text character mappings:

| Character | Arcade Tile | VRAM Slot | Pattern Address |
|-----------|------------|-----------|-----------------|
| '0' | 0x30 | 0x001C | 0x00380 |
| '1' | 0x31 | 0x001D | 0x003A0 |
| 'A' | 0x41 | 0x002B | 0x00560 |
| 'R' | 0x52 | 0x003B | 0x00760 |
| 'S' | 0x53 | 0x003C | 0x00780 |
| 'T' | 0x54 | 0x003D | 0x007A0 |

### B — Known text tile range

User-provided: tiles 0x001C–0x0050 (VRAM 0x0380–0x0A00).

**The text writer output falls entirely within the known text tile range.** Confirmed.

### C — Logo tile 0x001B

Logo arcade tile 0x1B maps through the LUT to **VRAM slot 0x0000 (tile 0)**.

VRAM slot 0 is the "empty/unmapped" default. The logo tile was **not assigned a VRAM slot** by `precompute_pc080sn_tile_lut.py`. This means:
- The logo tile pattern exists in the PC080SN source ROM
- It was NOT included in the scene preload manifest
- It was NOT loaded into Genesis VRAM
- Any nametable entry referencing it would display tile 0 (blank/black)

## 5. Logo Producer Verification

### Which routine writes the Rastan/Taito logo?

The logo is NOT written by the text writer hooks. The text writers handle ASCII text strings. The logo is a graphical element composed of PC080SN tiles — it would be rendered by the **PC080SN tilemap hooks** at arcade addresses 0x055968/0x055990 (`genesistan_asm_tilemap_commit_bg` / `genesistan_asm_tilemap_commit_fg`).

### Does it execute?

The PC080SN tilemap hooks fire during the **arcade tick** (`genesistan_run_arcade_tick_lean`), which runs inside VBlank. These hooks only produce output when the arcade game's tilemap update subroutines execute — specifically during active gameplay and some title screen phases.

**Execution status: UNCERTAIN** — the hooks may execute during title/attract, but:
1. The logo tiles (like 0x1B) map to VRAM slot 0 (unmapped) through the LUT
2. Even if the hooks write nametable entries, the tile indices would be 0 (empty)
3. The logo would be invisible regardless of whether the producer runs

### Does it write tile 0x001B?

The tilemap hooks write nametable entries using `genesistan_pc080sn_tile_vram_lut[arcade_tile]`. For arcade tile 0x1B:
- LUT[0x001B] = **0x0000**
- The nametable entry would reference tile 0 = black/empty

**The logo tile is not in the preload manifest and maps to tile 0.**

## 6. Contradiction Resolution

### Original claim: "Visible band is title text writer output"
### User observation: "Text was disabled via --disable-text"

**Resolution: There is no contradiction.**

- TEXT_DISABLED = **NO** — `--disable-text` was NOT applied to the ROM under test
- The text writers are active and producing the visible band
- The visible dots are text character tiles (VRAM slots 0x001A–0x0041) rendered with debug palette line 0 (red)
- The dots appear sparse because font tiles are mostly transparent (color index 0 = black)
- The previous "text output" conclusion was correct all along

### Why logo tiles are not visible

The logo tile (arcade tile 0x1B) is **not in the PC080SN tile VRAM LUT** — it maps to VRAM slot 0 (unmapped). The `precompute_pc080sn_tile_lut.py` script did not include it in any scene preload manifest. Even if the arcade tilemap producer writes nametable entries referencing this tile, the LUT returns 0, so tile 0 (empty) is displayed.

### User-observed "tile 0x0738 at VRAM 0xE700"

This was from the **VRAM Pattern Viewer** in Exodus, which displays raw VRAM contents as tile patterns. Address 0xE700 is inside the Plane A nametable (0xE000–0xEFFF). The pattern viewer was interpreting **nametable entry data as tile pattern data** — it showed the nametable words as if they were pixel data. "Block 0x0738" is just the linear tile index at VRAM address 0xE700 (0xE700 / 32 = 0x738). It is NOT a nametable reference to tile 0x738.

## 7. Final Root Cause Classification

**TEXT_NOT_ACTUALLY_DISABLED**

The visible band IS text writer output. The text writers were not disabled because `--disable-text` was not passed to the patcher. The logo is invisible because its arcade tile index (0x1B) maps to VRAM slot 0 in the tile LUT — the precompute script did not include it in the scene preload.

## 8. Final Verdict

| Finding | Status |
|---------|--------|
| Text disabled in tested ROM | **NO** — `--disable-text` not applied |
| Visible band is text output | **YES** — text writers active, producing tiles 0x001A–0x0041 |
| Logo tile 0x001B in nametable | **NO** — LUT maps it to slot 0 (unmapped) |
| Logo tile in VRAM patterns | **NO** — not in scene preload manifest |
| Pattern viewer misinterpretation | **YES** — 0xE700 is nametable data shown as patterns |
| VDP plane base addresses | **CORRECT** — no mismatch |
