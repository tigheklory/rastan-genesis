# Build 319 — Tile Mapping vs Palette Line Analysis

## 1. Executive Summary

Correct scene tiles exist in VRAM but display as sparse dots on screen. The primary root cause is **incomplete palette bank population**: the arcade palette routine writes 16 colors per bank to 4 separate CLCS offsets (blocks 0–3), but during title/early gameplay only block 2 (CLCS[32..47]) is populated. The per-frame commit transfers all 64 CLCS entries to CRAM, so only CRAM palette line 2 has real colors. Tiles referencing palette lines 0, 1, or 3 render as black.

## 2. Screenshot Evidence (Build 319, Exodus)

| Screenshot | Observation |
|------------|-------------|
| **A** | Launcher working, text visible, greyscale palette (ROM table fallback) |
| **B** | Game start, palette all black, VRAM has correct scene tiles loaded |
| **C** | Palette line 2 has real game colors (warm tones), main screen shows sparse dots, VRAM tiles visible in greyscale |
| **D** | Forcing palette line 2 in VRAM Pattern Viewer — full recognizable Rastan scene graphics appear, but in tile-cache order (not screen spatial order) |

## 3. Tile Index Pipeline Audit

The tile index pipeline in `startup_trampoline.s:740-775` is:

```
arcade tile word → mask 14-bit (& 0x3FFF) → tile_vram_lut[tile] → OR with attr_lut[key] → nametable word
```

### Attr LUT Key Construction (lines 743-764)

```
key = pal[1:0] | (hflip << 2) | (vflip << 3) | (prio << 4)
```

Source: arcade `attr_word` (d7), where:
- Bits 0-1: palette index (0–3)
- Bit 14: hflip
- Bit 15: vflip
- Bit 13: priority

### Attr LUT Value (precompute_pc080sn_attr_lut.py:19)

```python
(prio << 15) | (pal << 13) | (vflip << 12) | (hflip << 11)
```

**The arcade palette index maps 1:1 to Genesis palette line.** If the arcade tile specifies `pal=2`, the Genesis nametable word sets bits 13-14 = 0b10 = palette line 2.

### Tile VRAM LUT

- TILE_CACHE_BASE_A = 20, slots 20–1023 (1004 tiles for layer A)
- TILE_CACHE_BASE_B = 1280, slots 1280–1439 (160 tiles for layer B)
- Unmapped arcade tiles → slot 0 (blank)

**Conclusion**: Tile index pipeline is structurally correct. LUT lookup and attr combination follow the intended design.

## 4. Palette Capture Pipeline Audit

### Arcade Palette Writer (0x59AD4)

Disassembly of the arcade palette function at 0x59AD4:

```asm
59ad4: mulu.w  #32, %d1          ; source row offset = d1 * 32
59ad8: adda.w  %d1, %a0          ; source ptr += row offset
59ada: lsl.w   #5, %d0           ; dest block offset = d0 * 32 bytes
59ade: movea.l #0x200000, %a1    ; CLCS base address
59ae4: adda.w  %d0, %a1          ; dest = 0x200000 + (d0 * 32)
       [loop: writes 16 colors to dest]
```

`d0` = palette block (0–3), writes 16 colors (32 bytes) per call:

| Block (d0) | Dest Address | CLCS Entries | Genesis CRAM Line |
|------------|-------------|--------------|-------------------|
| 0 | 0x200000 | [0..15] | Line 0 |
| 1 | 0x200020 | [16..31] | Line 1 |
| 2 | 0x200040 | [32..47] | Line 2 |
| 3 | 0x200060 | [48..63] | Line 3 |

### CLCS Capture Remap (startup_title_remap.json)

```json
{
  "old_start": "0x00200000",
  "old_end_exclusive": "0x00200080",
  "symbol": "genesistan_palette_clcs"
}
```

Arcade writes to `0x200000 + offset` → `genesistan_palette_clcs[offset/2]`. Mapping is correct.

### Per-Frame Commit (startup_trampoline.s:87-123)

```asm
lea     genesistan_palette_clcs, %a0
move.l  #0xC0000000, (%a1)      /* CRAM write addr 0 */
moveq   #63, %d0
.Lpal_clcs_loop:
    [convert xBGR-555 → Genesis]
    move.w  %d2, (%a2)              /* write to CRAM */
    dbra    %d0, .Lpal_clcs_loop
```

Reads CLCS[0..63], converts, writes to CRAM[0..63]. No offset, no reordering. **The mapping is 1:1: CLCS block N → CRAM line N.**

## 5. Root Cause: Why Only Palette Line 2 Has Data

### Evidence

Screenshot C shows: CRAM lines 0, 1, 3 are all black. Only CRAM line 2 (entries 32–47) has real game colors.

### Cause

During title/early gameplay, the arcade only calls 0x59AD4 with `d0=2`, populating CLCS entries 32–47. Blocks 0, 1, 3 remain zero-initialized.

The callers at 0x599F0–0x59A80 invoke 0x59AD4 with different block indices depending on game state:

```asm
59a18: d1 = (d1>>3)+3, andi #3  → block varies
59a48: d1 = (d1>>3)+2, andi #3  → block varies
59a78: d1 = (d1>>3)+1, andi #3  → block varies
```

The block index depends on runtime state. During title/attract, only the block=2 caller executes.

### Effect on Display

| Tile Palette Ref | CRAM Line | Data Present? | Visible? |
|-----------------|-----------|---------------|----------|
| pal=0 | Line 0 | NO (all black) | **NO** — renders as black |
| pal=1 | Line 1 | NO (all black) | **NO** — renders as black |
| pal=2 | Line 2 | YES (game colors) | **YES** — sparse dots visible |
| pal=3 | Line 3 | NO (all black) | **NO** — renders as black |

Most PC080SN scene tiles reference palette 0 (the default/primary palette). Since CRAM line 0 is black, most tiles are invisible. Only the subset of tiles that happen to reference palette 2 appear as the "sparse dots" in screenshot C.

## 6. VRAM Viewer "Incorrect Layout" Explanation

Screenshot D shows recognizable Rastan graphics when forcing palette line 2 in the VRAM Pattern Viewer. The graphics appear "incorrectly assembled" because the VRAM viewer displays tiles in **linear VRAM slot order** (cache allocation order), not in screen spatial arrangement. This is expected behavior — the tiles are correctly loaded into their assigned VRAM slots, but the viewer shows them as a flat grid.

**The tile data in VRAM is correct.** The nametable entries reference valid tile slots. The only issue is palette.

## 7. Secondary Observations

### `load_arcade_palette()` (main.c:627-664) — Startup Path

This C function scans for the first non-zero 64-entry block and converts it. Since CLCS[32] is non-zero, it finds block 0 (entries 0–63), converts all 64 entries (including the zeros in entries 0–31 and 48–63), and writes to CRAM. Same outcome as the assembly commit: only line 2 has real colors.

### Palette Timing

Palette banks are populated progressively as the arcade game runs. At title screen, only bank 2 may be active. During full gameplay, all 4 banks may eventually be populated. The Genesis commit captures whatever is in CLCS at VBlank time.

## 8. Primary Root Cause

**PALETTE_BANK_INCOMPLETE**: The arcade populates palette block 2 during title/early gameplay, mapping to Genesis CRAM line 2. Tiles referencing palette lines 0, 1, or 3 render as black because those CRAM lines contain zeros. The tile index pipeline, VRAM loading, nametable generation, and VDP configuration are all correct.

## 9. Single Next Implementation Target

**Investigate and fix palette bank population.** Two approaches:

1. **Preferred — Palette bank remapping**: Determine which palette bank the arcade uses as the "primary" 16-color set for PC080SN scene tiles. Copy that bank's 16 entries into ALL 4 CRAM lines during the commit routine, so tiles render correctly regardless of which palette line the attr_lut selects. This is a targeted fix to the commit loop in `genesistan_palette_commit_asm`.

2. **Alternative — Full bank capture audit**: Trace all callers of 0x59AD4 to determine the complete palette bank population sequence during each game phase (title, gameplay, boss, etc.). Ensure the Genesis side captures and commits all 4 banks. This requires deeper arcade reverse-engineering but produces a more faithful reproduction.

**Recommendation**: Approach 1 (palette bank remapping) is the single lowest-risk fix. Replicate CLCS[32..47] into all 4 CRAM lines during commit. If arcade tiles use multiple distinct palettes across banks, approach 2 will be needed later.

## 10. Verification Checklist

After implementing the palette fix:

| Check | Expected |
|-------|----------|
| CRAM lines 0-3 all have colors | YES |
| Full scene graphics visible on main screen | YES |
| Tile layout matches expected Rastan title screen | YES (if tile pipeline is correct) |
| No new regressions in other game phases | Verify |
