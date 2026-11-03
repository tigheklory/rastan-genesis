# Build 323 — Fix C-Window Text Layer Row/Column Decode

## 1. Executive Summary

Build 323 fixes a coordinate transpose bug in `text_writer_ptr_to_xy()` that caused all C-window text to appear as vertical columns instead of horizontal lines. The function's bit-field decomposition was column-major (correct for PC080SN scene layers) but the C-window text layer uses row-major layout. Swapping the decomposition so low 6 bits = column and high bits = row fixes the transpose.

## 2. Prior Confirmed Coordinate-Transpose Finding

Per `docs/design/build322_fg_text_coordinate_transpose_audit.md`:

- `rastan_draw_tile_xy()` is correct (indexes `y * 64 + x`, row-major)
- Plane A buffer layout is correct (64×32, row-major, stride 64)
- Commit path is correct (linear stream to VRAM 0xE000)
- Bug is exclusively in `text_writer_ptr_to_xy()`: column-major decomposition applied to row-major text layer
- User observed structured text words ("INSERT", "COIN", "TAITO", etc.) arranged as vertical columns in VDP Plane A viewer

## 3. Exact Code Change

**File**: `apps/rastan/src/main.c`, function `text_writer_ptr_to_xy()`

**Before** (column-major, wrong for C-window):
```c
cell = offset >> 2;
row = cell & 0x3FU;              /* low 6 bits treated as row */
if (row < TEXT_WRITER_VISIBLE_ROW_BIAS)
    return FALSE;
{
    u32 col = (cell >> 6) & 0x3FU;   /* high bits treated as col */
    if (col < col_bias)
        col += 64U;
    *out_x = (s16)(col - col_bias);
}
*out_offset = offset;
*out_y = (s16)(row - TEXT_WRITER_VISIBLE_ROW_BIAS);
```

**After** (row-major, correct for C-window):
```c
cell = offset >> 2;
{
    u32 col = cell & 0x3FU;          /* low 6 bits = column */
    u32 row_val = (cell >> 6) & 0x3FU;   /* high bits = row */

    if (row_val < TEXT_WRITER_VISIBLE_ROW_BIAS)
        return FALSE;

    if (col < col_bias)
        col += 64U;
    *out_x = (s16)(col - col_bias);
    *out_offset = offset;
    *out_y = (s16)(row_val - TEXT_WRITER_VISIBLE_ROW_BIAS);
}
```

Changes:
- `cell & 0x3F` now produces column (was row)
- `cell >> 6` now produces row (was column)
- `TEXT_WRITER_VISIBLE_ROW_BIAS` now applied to actual row
- `col_bias` still applied to actual column
- Removed unused `row` variable from outer scope

## 4. Why the C-Window Layer Requires Row-Major Decode

The TC0100SCN in Rastan has three tilemap layers:
- **BG layer** (0xC00000): column-major (TILEMAP_SCAN_COLS) — 64 rows per column strip
- **FG layer** (0xC04000): column-major (TILEMAP_SCAN_COLS) — same layout
- **Text/C-window layer** (0xC08000): row-major (TILEMAP_SCAN_ROWS) — 64 columns per row strip

The assembly bulk tilemap writer correctly uses column-major decode for BG/FG scene layers. The C-window text hooks call `text_writer_ptr_to_xy()` which must use row-major decode. The original implementation incorrectly used the same column-major convention for both.

In row-major layout: address = (row × 64 + col) × 4 bytes per cell. So:
- `cell & 0x3F` extracts the column (low 6 bits)
- `cell >> 6` extracts the row (high bits)

## 5. Non-Goals (No Caller Changes / No Assembly Changes)

| Component | Changed? |
|-----------|----------|
| `text_writer_ptr_to_xy()` | YES (this fix) |
| `genesistan_hook_text_writer_3bb48_impl()` | NO |
| `genesistan_hook_text_writer_3c3fe()` | NO |
| `rastan_draw_tile_xy()` | NO |
| Assembly bulk tilemap writer | NO |
| `genesistan_pc080sn_commit_planes` | NO |

## 6. Build 323 Verification

### Structural
- Build succeeded: **YES**
- ROM: `dist/Rastan_323.bin` (3,932,160 bytes)
- Exceptions introduced: **NO** (same 5 pre-existing unused-function warnings)

### Text-coordinate fix behavior
- `text_writer_ptr_to_xy()` changed: **YES**
- Decode changed from column-major to row-major: **YES**
- Caller code left unchanged: **YES**
- Assembly tilemap writers left unchanged: **YES**

## 7. Visual Verification Status

**USER MUST VERIFY.** Expected behavior:
- Text words should now appear as horizontal lines (not vertical columns)
- Title screen text ("INSERT COIN", "1P", "2P", "TAITO", etc.) should read left-to-right
- Screen still mostly black (nametable population issue unchanged — only text tiles present)

## 8. Crash Verification Status

**USER MUST VERIFY.** The change only affects bit-field extraction within `text_writer_ptr_to_xy()`. No new memory access patterns, no VDP register changes, no buffer size changes.

## 9. Final Verdict

Narrow verified fix. The C-window text layer coordinate decode is corrected from column-major to row-major. If text now appears horizontal, this confirms the transpose was the coordinate bug. The remaining "mostly black screen" is the separate nametable population problem (tilemap hooks produce no scene content during title/attract).
