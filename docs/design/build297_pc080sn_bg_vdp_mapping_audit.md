# Build 297 PC080SN BG VDP Mapping Audit

**Date:** 2026-03-30
**Build reference:** Build 297

---

## 1. Executive Summary

Build 297 fixed `PC080SN_CWINDOW_BYTES = 0x4000`. BG assembly now fires on every valid frame. The purple-dominant screen is NOT caused by a missing write — BG tiles are being written to the VDP on every frame. The failure is a **mapping error**: `pc080sn_dest_ptr_to_row_col()` computes `dest_col = cell & 0x3F` and `dest_row = cell >> 6`, which is **inverted** for the BG column-major C-window layout. For every valid BG dest_ptr, `dest_col = 0`. The BG assembly writes all tile content to **VDP column 0 only**. The remaining 63 columns of BG_B (VRAM `0xC000`) are never written — they retain zero tiles (transparent). The screen shows FG content over a mostly-blank BG plane, with VDP column 0 (8px wide) continuously cycling through BG tile data.

**Failure classification: MAPPING ERROR — row/column inversion in `pc080sn_dest_ptr_to_row_col()`.**

**BG execution status: YES — continuous.** The arcade's own column-advance routine at `0x560DA` (disasm line 107881) keeps workram[0x10A0] cycling through valid BG column addresses, providing a new valid dest_ptr to each Genesis hook call.

---

## 2. BG Execution Status (Post-Fix)

### Is BG assembly executing continuously?

**YES.**

### Call path

1. Arcade vblank handler calls subroutine at `0x55948` (disasm line 107365).
2. At `0x55948`: if mode==0, BSR to `0x55968` (BG builder). This BSR is spec-patched to call `genesistan_hook_tilemap_plane_a()`.
3. `genesistan_hook_tilemap_plane_a()` reads `workram[0x10A0]`, calls `genesistan_asm_tilemap_commit_bg()`, writes returned dest_ptr back to `workram[0x10A0]`.
4. After the hook returns, the arcade at `0x55954` increments strip_index.

### Why it is continuous

The arcade's own column-advance routine at `0x560DA` (disasm line 107881) runs every 8 ticks of the counter at `workram[0x10EE]`. It:
1. Reads `workram[0x10A0]` into A0 (line 107881: `206d 10a0  moveal %a5@(4256),%a0`)
2. Writes 50 cells of 0x0020 to A0 (50 × `movel #32,%a0@+`)
3. Advances A0 by 256 bytes (`d1fc 0000 0100  addal #256,%a0`, line 107891)
4. Masks: `0280 00c0 3f00  andil #12599040,%d0` — forces A0 within `0xC00000..0xC03F00` (line 107893)
5. Writes wrapped A0 back to `workram[0x10A0]` (line 107895: `2b48 10a0  movel %a0,%a5@(4256)`)

After our hook writes `dest_ptr = 0xC04400` (start 0xC00400 + 0x4000), the arcade's advance routine reads 0xC04400, adds 256+50×4=456...

Exact trace:
- Hook writes back 0xC04400 to workram[0x10A0]
- 0x560DA: A0 = 0xC04400; writes 50 × 4 bytes advancing A0 to 0xC044C8; then A0 += 256 → 0xC045C8; D0 = 0xC045C8 & 0xC03F00 = 0xC00500; writeback 0xC00500
- Next hook call: workram[0x10A0] = 0xC00500 → offset = 0x500 < BYTES 0x4000 → **VALID** → fires → returns 0xC04500
- Next advance: 0xC04500 + advance → masked → 0xC00600 (column 6)
- Pattern: columns 4→5→6→...→63→0→1→...→4 cycling

With `PC080SN_CWINDOW_BYTES = 0x4000`, all values `0xC00100`...`0xC03F00` are within `[0xC00000, 0xC04000)` and are valid. BG assembly fires on every call.

### Call frequency

Once per call to `0x55948`. Strip_index increments at `0x55954` after every BG hook call. BG assembly fires once per strip update, continuously.

---

## 3. Current BG Mapping Formula (Exact)

### C decode: `pc080sn_dest_ptr_to_row_col()` (main.c:1269–1284)

```c
const u32 addr24 = dest_ptr & 0x00FFFFFFUL;
const u32 offset = addr24 - cwindow_base;      // cwindow_base = 0xC00000
const u32 cell   = offset >> 2;                // cell = offset / 4

*out_row = (u16)((cell >> 6) & 0x1FU);         // out_row = cell / 64
*out_col = (u16)(cell & 0x3FU);                // out_col = cell % 64
```

For `dest_ptr = 0xC00400`:
- offset = 0x400 = 1024
- cell = 256
- out_row = (256 >> 6) & 31 = 4
- out_col = 256 & 63 = **0**

For `dest_ptr = 0xC00500` (column 5):
- offset = 0x500 = 1280
- cell = 320
- out_row = (320 >> 6) & 31 = 5
- out_col = 320 & 63 = **0**

For **every column-start dest_ptr** of the form `0xC00N00` (N = 0..63):
- cell = N × 64 (a multiple of 64)
- out_col = (N × 64) & 63 = **0 always**
- out_row = N & 31

**dest_col is always 0 for all valid column-start dest_ptr values.**

### Assembly VDP formula (startup_trampoline.s:247–268)

```asm
move.w  %d1, %d0          ; d0 = dest_row (D1)
cmpi.w  #4, %d0
blo     .Lpc080sn_bg_skip_write

subi.w  #4, %d0           ; vdp_row = dest_row - 4
lsl.w   #7, %d0           ; vdp_row * 128
add.w   %d2, %d0          ; + dest_col
add.w   %d2, %d0          ; + dest_col  (adds twice = dest_col * 2)
addi.w  #0xC000, %d0      ; + BG_B VRAM base
```

Fully expanded:
```
vdp_addr = 0xC000 + (D1 - 4) * 128 + D2 * 2
         = 0xC000 + (dest_row - 4) * 128 + dest_col * 2
```

With `dest_col = D2 = 0` always:
```
vdp_addr = 0xC000 + (dest_row - 4) * 128
```

**All BG VDP writes target column 0** (byte offset `D2 * 2 = 0` within each row). Rows 0..27 are written (D1 cycles 4..31 across 7 descriptors, then wraps and repeats for descriptors 8..14).

---

## 4. Arcade vs Genesis Mapping Comparison

### PC080SN BG C-window layout: column-major

The PC080SN BG C-window is organized column-major: cell(col, row) occupies offset `(col × 64 + row) × 4` from base `0xC00000`. This gives:
- Column c, row 0: offset `c × 256` bytes from base
- Column c starts at `0xC00000 + c × 0x100`
- Adjacent rows within a column: 4 bytes apart (contiguous)
- Adjacent columns of the same row: 256 bytes apart

Evidence:
- `55e54: movel #12583936,%a5@(4256)` initializes dest_ptr = `0xC00400` = `0xC00000 + 4 × 0x100` → column 4, row 0 in column-major ✓
- Arcade column-advance at `0x560FE`: `addal #256,%a0` then `andil #0xC03F00,%d0` — advances by exactly 256 bytes (= one column stride) and wraps column index to 0..63 ✓
- `0xC03F00` = `0xC00000 + 63 × 0x100` = last column base address. The mask `& 0xC03F00` enforces 64-column wrap ✓

### Correct column-major cell decode

For a column-major 64×64 cell layout, cell at (col, row) = col × 64 + row:
- column index = cell / 64 = `cell >> 6`
- row within column = cell % 64 = `cell & 0x3F`

### Current decode vs correct decode

| Field | Current code | Correct for column-major |
|-------|-------------|--------------------------|
| `out_row` = D1 (assembly) | `cell >> 6` = **column index** | should be `cell & 0x3F` = row within column |
| `out_col` = D2 (assembly) | `cell & 0x3F` = **row within column** | should be `cell >> 6` = column index |

**The names `out_row` and `out_col` are semantically inverted relative to the column-major C-window geometry.** D1 holds the column index; D2 holds the row-within-column (= 0 for all column-start addresses).

### What arcade writes vs what Genesis writes

| | Arcade PC080SN hardware | Genesis VDP (current) | Genesis VDP (correct) |
|--|--|--|--|
| Which column | C-window col = `dest_ptr offset / 256` | **Always VDP column 0** | VDP col = col index from dest_ptr |
| Which rows | C-window rows 4..31 (visible) | VDP rows 0..27 (correct rows, wrong column) | VDP rows 0..27 at correct column |

---

## 5. Row Offset Analysis (`dest_row - 4`)

### What the `-4` offset does

The BG assembly guard at `startup_trampoline.s:248–249`:
```asm
cmpi.w  #4, %d0
blo     .Lpc080sn_bg_skip_write
```
skips writes when D1 < 4. The formula then applies `D1 - 4` as the VDP row.

### What D1 actually is

In the **current (wrong) decode**: D1 = `cell >> 6` = column index = 4 for dest_ptr=0xC00400. The guard fires when column index < 4 (first 4 columns skip all writes). This is semantically wrong — it skips writing to VDP columns 0-3 when they become the current column, not rows.

In the **correct (column-major) decode**: D1 = `cell & 0x3F` = row within column = 0 for all column-start dest_ptrs. The guard correctly skips the first 4 rows (0..3) of each column update. These correspond to the top 32px (4 tiles × 8px) of the 240px arcade display, which lie above the 224px Genesis visible window. This is the correct 240→224px crop.

### Is `-4` correct?

**YES — the formula `(D1 - 4) * 128` is correct IF AND ONLY IF D1 = row_within_column.** With the correct decode (D1 = row_within_column = 0 for column-start dest_ptrs):
- Rows 0..3 → D1 < 4 → skipped (32px top crop)
- Row 4 → D1 - 4 = 0 → VDP row 0 ✓
- Row 31 → D1 - 4 = 27 → VDP row 27 ✓

The row bias of `-4` and the `< 4` skip guard are **architecturally correct**. They implement the 4-tile top crop. The problem is that D1 currently receives the column index (not the row), making the guard fire on the wrong axis.

---

## 6. Tile Write Coverage Pattern

### Current coverage (with D2 = 0 always)

Per BG assembly call:
- D2 (dest_col) = 0 → all writes at VDP column 0
- D1 cycles: 4,5,6,7 (desc 0) | 8..11 (desc 1) | ... | 28..31 (desc 6) | wrap+skip 0..3 (desc 7) | 4..7 overwrite (desc 8) | ... | 28..31 overwrite (desc 14) | skip (desc 15)
- **VDP rows 0..27 at column 0** are written — twice per call (descriptors 0-6 first, then 8-14 overwrite)
- **VDP columns 1..63**: NEVER WRITTEN

Genesis screen coverage: **1 of 64 columns = 8 pixels of 512px horizontal span has any BG tile content**. The other 504 pixels (columns 1-63) are zero tiles = transparent/blank.

### What should be covered

Per call: one specific BG column (determined by dest_ptr's column index, cycling 4→5→...→63→0→...→3 over 60 frames). All 28 visible rows within that column.

Over 60 frames: all 64 columns updated. Full 64×28 visible BG plane refreshed.

---

## 7. Palette vs Position Diagnosis

**Classification: POSITION ERROR (column targeting wrong), NOT palette error.**

Evidence:
- BG_B plane (VRAM `0xC000`) has tile content only at VDP column 0 (8px wide)
- Columns 1-63 contain zero words = tile index 0 = blank tile. Blank tiles are transparent on Genesis.
- BG_A plane (FG): `genesistan_hook_tilemap_plane_b()` is confirmed continuously active and correctly writing to VDP `0xE000`. FG plane content dominates the screen.

The "purple-dominant" screen is caused by:
1. **BG_A (FG)**: the FG tilemap assembly writes to BG_A. FG tiles are rendered using the attribute LUT and tile VRAM LUT. The purple color comes from whatever tile content and palette the FG assembly writes. The FG plane is the PRIMARY visual source for most of the screen.
2. **BG_B (BG)**: transparent (blank) for columns 1-63. Column 0 (8px) has cycling BG tiles — not visible against FG content.

The purple is **not** from wrong tile indices, wrong palette entries, or BG overwriting FG. It is from FG content (correct FG path) rendering with whatever arcade palette is active at this point in the attract sequence. Rastan's attract sequence palettes include purple-dominant color entries used for certain title screen or background elements.

The BG plane contributes zero visible content to the current visual output because its tile writes target an invisible column while the FG plane covers the visible area.

---

## 8. FG vs BG Interaction

### FG status

**Continuously active. Correct.** Confirmed from prior audits (Build 295 and 296 analyses) and unchanged in Build 297. `genesistan_hook_tilemap_plane_b()` fires on every call. FG dest_ptr values `[0xC08000, 0xC0BFFF]` all satisfy `PC080SN_CWINDOW_BASE_FG = 0xC08000` check.

FG VDP writes target VRAM `0xE000` (BG_A plane). FG inner loop correctly advances D2 (dest_col) by 1 per cell (`addq.w #1, %d2`), covering all 64 columns of each FG row. FG plane updates are live and correctly distributed across columns.

### BG vs FG interaction

**No collision.** BG writes to VRAM `0xC000` (BG_B). FG writes to VRAM `0xE000` (BG_A). Separate planes, no overwrite.

**Z-order**: BG_A (FG) renders on top of BG_B (BG) in the Genesis VDP layer priority scheme. BG_B column 0 tiles are underneath FG content — if the FG tile at that position is non-transparent, the BG_B tile is not visible anyway.

**BG is not clobbering FG.** The planes are independent.

---

## 9. Confirmed Root Cause(s)

### Root Cause (SOLE) — out_row / out_col inverted in `pc080sn_dest_ptr_to_row_col()`

**Evidence grade: CONFIRMED. Zero ambiguity.**

**Source:** `main.c:1282–1283`.

```c
*out_row = (u16)((cell >> 6) & 0x1FU);   // ← WRONG: gives column index
*out_col = (u16)(cell & 0x3FU);           // ← WRONG: gives row-within-column
```

The PC080SN BG C-window is column-major. Cell at address offset `O` from `0xC00000`:
- column index = `(O/4) / 64` = `(O/4) >> 6`
- row within column = `(O/4) % 64` = `(O/4) & 0x3F`

The BG assembly expects D1 = row_within_column (cycles 0..31 across inner loop), D2 = column index (constant per call, targets specific VDP column). The decode provides the opposite: D1 = column index, D2 = row_within_column.

For all column-start dest_ptrs (`0xC00N00`, N = 0..63): row_within_column = cell & 63 = 0. D2 = 0 always. VDP column = D2 × 2 = 0. All BG writes permanently target VDP column 0.

**Observable effect:** BG_B VRAM column 0 (8px) contains continuously-cycling tile data. Columns 1-63 are blank. Background layer is visually absent except for an 8px left-edge stripe. FG plane dominates the visible output, appearing purple during attract due to Rastan's title/attract palette state.

**Fix scope:** Swap `*out_row` and `*out_col` in `pc080sn_dest_ptr_to_row_col()`. No changes to the BG assembly formula are required. After the swap:
- D1 = `cell & 0x3F` = row_within_column = 0 for column-start addresses → guard `< 4` correctly skips rows 0-3 → VDP rows 0-27 written
- D2 = `(cell >> 6) & 0x3F` = column index = 4 for `0xC00400`, 5 for `0xC00500`, etc. → VDP column cycles through all 64 columns ✓

---

## 10. Rejected Hypotheses

| Hypothesis | Why Rejected |
|------------|--------------|
| BG still stops after fix | REJECTED: arcade advance routine at `0x560DA` (disasm line 107881) wraps workram[0x10A0] into `[0xC00000, 0xC03F00]` range every 8 ticks. BG fires continuously. |
| Palette error causes purple | REJECTED: BG_B columns 1-63 are blank/transparent. FG (BG_A) dominates screen. Purple comes from FG tile content with current arcade palette, not wrong palette indices or wrong BG palette. |
| VDP formula `(D1-4)*128` is wrong | REJECTED: formula is correct for D1 = row_within_column. The formula is wrong only because D1 receives the column index (wrong input), not because the arithmetic is incorrect. |
| Row skip guard `< 4` is wrong | REJECTED: skipping rows 0-3 (= 32px = 4 tiles) is the correct 240→224px vertical crop. Guard logic is sound with the correct D1 value. |
| BG overwrites FG plane | REJECTED: BG writes to VRAM `0xC000` (BG_B), FG writes to VRAM `0xE000` (BG_A). No overlap. |
| FG stopped working in Build 297 | REJECTED: FG path unchanged. No code touching `genesistan_hook_tilemap_plane_b()` was modified in Build 297. |
| Wrong tile indices from LUT | REJECTED: the LUT lookup `pc080sn_tile_vram_lut[arcade_tile]` is correct per Build 295 analysis. Tiles ARE written to VDP — at the wrong VDP column (0 always), not with wrong indices. |

---

## 11. Remaining Unknowns

### UNKNOWN A — Descriptor overwrite within one BG call

**Status:** STRUCTURAL CONCERN — low impact, not the cause of purple screen.

With D1 starting at 0 (after the decode fix) and 16 descriptors × 4 rows = 64 row-slots:
- Descriptors 1-7: write VDP rows 0-27 (7 × 4 = 28 rows, filling visible area)
- Descriptor 8: D1 wraps to 0, rows 0-3 skipped
- Descriptors 9-15: write VDP rows 0-27 again (overwrite descs 1-7)

Only descriptors 9-15 (7 of 16) produce the final visible content per call. Descriptors 0, 1-7, 8 are either skipped or overwritten. Whether this produces wrong-tile content depends on whether the 16 descriptors carry different tile data for the same column. If descriptors 1-7 and 9-15 use the same tile tables for the same rows, the overwrite is harmless. Requires empirical observation after the row/col swap fix.

### UNKNOWN B — Effect of arcade 0x560DA writing to Genesis VDP region

**Status:** MINOR, probably harmless.

When our hook writes `0xC04400` to workram[0x10A0], the arcade's `0x560DA` routine reads it and executes 50 × `movel #32,%a0@+` starting at that address. In Genesis memory map, `0xC04400` is in the VDP I/O mirror range `0xC00000-0xCFFFFF`. Writing to `0xC04400` targets the VDP H/V counter region. Writes to that range are typically ignored or benign. No visual corruption observed, but this is unverified.

### UNKNOWN C — Number of BG builder calls per frame

**Status:** NOT CRITICAL for current fix.

The exact call count per frame (how many times `0x55948` is invoked per vblank) is not confirmed by disasm reading. Each call fires one strip_index. Whether all 64 columns are refreshed within one frame or spread across multiple frames depends on call frequency. After the row/col fix, correct output can be observed regardless of frequency.
