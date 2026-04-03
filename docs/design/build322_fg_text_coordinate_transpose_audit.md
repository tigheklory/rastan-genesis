# Build 322 — FG/Text Tile Write Coordinate Transpose Audit

## 1. Executive Summary

The FG/text write path has a confirmed coordinate transpose. The `text_writer_ptr_to_xy()` function uses a **column-major** decomposition (copied from the PC080SN scene tilemap code) to decode C-window text layer addresses. However, the TC0100SCN C-window text layer uses a **row-major** layout (TILEMAP_SCAN_ROWS), unlike the scene layers (TILEMAP_SCAN_COLS). This causes row and column to be swapped, producing vertical text where horizontal text should appear.

## 2. User Plane-Viewer Evidence

The user inspected Layer A (Plane A, FG nametable at 0xE000) in the BlastEm VDP Plane Viewer and observed:

- Recognizable text content is present (letters, digits, structured words)
- Words like "INSERT", "COIN", "1P", "WARD:", "WARP:", "1ST", "2ND", "3RD", "4TH", "TAITO", "AMERICA", "CORP" are all arranged as **vertical columns**
- These words should appear as horizontal text on the Rastan title screen
- The content is structured and correct — the coordinate mapping is the problem, not the tile data

Two plane viewer frames captured at different moments show the same vertical arrangement, confirming it is stable and systematic (not random corruption).

## 3. `rastan_draw_tile_xy()` Audit

**Location**: `apps/rastan/src/main.c` line 1309

```c
void rastan_draw_tile_xy(u16 tile_attr, int x, int y)
{
    if (x < 0 || x >= 64 || y < 0 || y >= 32)
        return;
    pc080sn_fg_buffer[y * 64 + x] = tile_attr;
}
```

**Findings**:
- Signature: `(tile_attr, x, y)` where x = column, y = row
- Buffer index: `y * 64 + x` — **row-major**, stride 64 columns
- Writes to: `pc080sn_fg_buffer[]` (FG nametable WRAM buffer, committed to VRAM 0xE000)
- Bounds: x ∈ [0, 63], y ∈ [0, 31]
- **This function is correct.** If called with (x=column, y=row), it writes to the correct nametable position

## 4. Text/FG Caller Audit

### 4a. `text_writer_ptr_to_xy()` — The Core Bug

**Location**: `apps/rastan/src/main.c` lines 1340-1393

This function converts an arcade C-window pointer to (x, y) screen coordinates.

**Current decomposition** (lines 1376-1391):

```c
cell = offset >> 2;            /* 4 bytes per cell */
row = cell & 0x3FU;            /* low 6 bits → "row" */
/* ... */
col = (cell >> 6) & 0x3FU;    /* high bits → "col" */
/* ... */
*out_x = (s16)(col - col_bias);           /* col → x */
*out_y = (s16)(row - TEXT_WRITER_VISIBLE_ROW_BIAS);  /* row → y */
```

**The problem**: This decomposition is **column-major** (cell = col × 64 + row → row = cell & 0x3F, col = cell >> 6). This is correct for the PC080SN scene tilemap layers, which use TILEMAP_SCAN_COLS in the Taito hardware.

However, the C-window text layer uses **row-major** layout (TILEMAP_SCAN_ROWS): cell = row × 64 + col. For row-major:
- Low 6 bits = **column** (not row)
- High bits = **row** (not column)

**What the code labels "row" is actually the column. What it labels "col" is actually the row.**

Result:
- `out_x` receives the actual row value (not column)
- `out_y` receives the actual column value (not row)

**Bias misapplication**:
- `col_bias = 32` is applied to the actual ROW (wrong — should be applied to column)
- `TEXT_WRITER_VISIBLE_ROW_BIAS = 4` is applied to the actual COLUMN (wrong — should be applied to row)

### 4b. `genesistan_hook_text_writer_3bb48_impl()`

**Location**: lines 1643-1694

- Calls `text_writer_ptr_to_xy(dst_ptr, &x, &y, &offset)` at line 1670
- Passes `x, y` to `rastan_draw_tile_xy()` at line 1689
- Advances `dst_ptr += 4U` per character (line 1692)

With row-major layout, `dst_ptr += 4` advances column by 1 (moves right). But the swapped decode maps this to incrementing `out_y` (vertical movement) while `out_x` stays fixed. Result: **horizontal text strings are written as vertical columns.**

### 4c. `genesistan_hook_text_writer_3c3fe()`

**Location**: lines 1786-1828

- Same pattern: calls `text_writer_ptr_to_xy()` at line 1820, passes `x, y` to `rastan_draw_tile_xy()` at line 1823
- Same `dst_ptr += 4U` stride (line 1826)
- Same transpose bug via shared `text_writer_ptr_to_xy()`

### 4d. PC080SN Bulk Tilemap Writer (assembly)

**Location**: `startup_trampoline.s` lines 792-797

Uses the SAME column-major decode: `cell & 0x3F = row`, `cell >> 6 = column`. This is **correct** for the PC080SN scene layers (BG/FG), which ARE column-major in the Taito hardware. The bug is that `text_writer_ptr_to_xy()` borrowed this decomposition for the C-window text layer, which has a different layout.

## 5. Plane A Buffer Layout Verification

| Property | Value |
|----------|-------|
| Buffer | `pc080sn_fg_buffer[]` (BSS, 4096 bytes = 2048 words) |
| Layout | Row-major, 64 columns × 32 rows |
| Index formula | `row * 64 + col` |
| Commit path | `genesistan_pc080sn_commit_planes` streams 2048 words sequentially to VRAM 0xE000 |
| VDP Plane A size | 64×32 (VDP register setting confirmed) |

The write helper `rastan_draw_tile_xy()` and the commit path **agree** on row-major layout with stride 64. The buffer layout assumption is correct.

## 6. Coordinate-Transpose Interpretation

The vertical text arrangement observed in the Plane A viewer is **fully consistent with X/Y transposition in `text_writer_ptr_to_xy()`**.

**Proof by tracing "INSERT" (6 characters)**:

Assume the arcade descriptor starts at C-window address for (row=10, col=5) in row-major:
- cell = 10 × 64 + 5 = 645

Current (wrong) decode:
- "row" = 645 & 0x3F = 5 → out_y receives 5 (but 5 is the COLUMN)
- "col" = 645 >> 6 = 10 → out_x receives 10 (but 10 is the ROW)

Character 'I' written to: `rastan_draw_tile_xy(tile, 10, 5)` → buffer[5 * 64 + 10] = buffer[330]

Next character 'N': dst_ptr += 4, cell = 646
- "row" = 646 & 0x3F = 6 → out_y = 6
- "col" = 646 >> 6 = 10 → out_x = 10

Character 'N' written to: buffer[6 * 64 + 10] = buffer[394]

Result: 'I' at screen (col=10, row=5), 'N' at screen (col=10, row=6) — **vertical column**.

Correct decode would give:
- col = cell & 0x3F = 5, then 6, then 7...
- row = cell >> 6 = 10 (fixed)
- Characters at (5, 10), (6, 10), (7, 10)... — **horizontal row** ✓

## 7. Single Most Likely Root Cause

**`text_writer_ptr_to_xy()` INDEXES_SWAPPED_COORDINATES**

The function applies column-major bit-field decomposition (low bits = row, high bits = col) to a row-major text layer (low bits = col, high bits = row). This swaps the meaning of row and column, causing all text to appear transposed.

The callers (`genesistan_hook_text_writer_3bb48_impl` and `genesistan_hook_text_writer_3c3fe`) correctly pass `x, y` from `text_writer_ptr_to_xy()` to `rastan_draw_tile_xy()`. The bug is entirely inside `text_writer_ptr_to_xy()`.

`rastan_draw_tile_xy()` itself is correct. The PC080SN bulk tilemap writer is also correct (it handles scene layers which ARE column-major).

## 8. Single Next Implementation Target

**Fix `text_writer_ptr_to_xy()` bit-field extraction to use row-major decomposition for the C-window text layer.**

Swap the decomposition:
```c
/* Correct for row-major text layer: */
u32 col = cell & 0x3FU;           /* low 6 bits = column */
u32 row = (cell >> 6) & 0x3FU;    /* high bits = row */
```

And apply biases to the correct dimensions:
- `TEXT_WRITER_VISIBLE_ROW_BIAS` (4) to `row`
- `col_bias` (32) to `col`

No changes needed to `rastan_draw_tile_xy()`, the text writer hooks, or the PC080SN assembly code.

## 9. Final Verdict

**Confirmed transpose.** The C-window text layer uses row-major layout but `text_writer_ptr_to_xy()` applies column-major decomposition. This swaps every X/Y coordinate, causing all text to appear as vertical columns instead of horizontal lines. The fix is a single function change: swap the bit-field extraction in `text_writer_ptr_to_xy()`.
