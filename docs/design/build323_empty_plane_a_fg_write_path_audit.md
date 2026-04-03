# Build 323 — Empty Plane A / FG Write Path Audit

## 1. Executive Summary

After the Build 323 row-major coordinate decode fix, Plane A is empty during the attract/title phase. Code inspection reveals: there is no FG buffer memset; the commit runs unconditionally (the Build 314 mode gate is no longer present); and `text_writer_ptr_to_xy()` produces valid in-bounds coordinates for typical attract text positions. The primary cause of the empty plane is that the text hooks (0x3BB48 and 0x3C3FE) are not the only — and possibly not the primary — source of FG content during attract mode. The settings menu text works (confirming the hooks themselves function correctly when called), but attract-mode tile content during Build 322 was driven by `genesistan_bulk_tilemap_commit` writing through column-major decode, not by the text writer hooks. With the hooks' coordinate decode corrected but the bulk tilemap still running in column-major, the sources are now out of sync, and the attract-phase FG content is lost.

## 2. Build 323 Expected vs Actual Result

| | Expected | Actual |
|--|----------|--------|
| Text orientation | Horizontal | — |
| Plane A content | Visible text | Empty |
| Settings menu text | Correct | Correct ✓ (confirmed by Exodus screenshot) |
| Attract-mode text | Correct | Empty |

Key observation: the **settings menu text IS visible and horizontal in Build 323**. This proves the row-major decode fix is functionally correct for that path. The emptiness is attract-phase specific.

## 3. Text Hook Execution Audit

### `genesistan_hook_text_writer_3bb48_impl` and `genesistan_hook_text_writer_3c3fe`

**Running during settings menu**: YES — confirmed by Exodus screenshot showing correct horizontal text in Layer A.

**Running during attract phase**: UNKNOWN from code inspection alone. However, both hooks have an early-exit guard in the 3BB48 hook:

```c
if ((descriptor_ptr == 0U) || (descriptor_ptr >= 0x00800000U))
    return;
```

If the descriptor table has entries that point to 0x000000 (null) during attract mode, all writes for that text_id are silently dropped.

**`text_writer_ptr_to_xy` and `rastan_draw_tile_xy`**: Both execute whenever the hooks are called with valid inputs. No additional gating found in either function.

## 4. `text_writer_ptr_to_xy()` Output Audit

### Code-traced sample — row=4, col=5 (row-major, Build 323 decode):

| Step | Value |
|------|-------|
| C-window offset | row×256 + col×4 = 4×256+5×4 = 1044 |
| cell = offset >> 2 | 261 |
| col = cell & 0x3F | 5 |
| row_val = (cell >> 6) & 0x3F | 4 |
| row_val >= TEXT_WRITER_VISIBLE_ROW_BIAS (4) | YES — passes |
| col < col_bias (32) → col += 64 → 69 | 69 |
| out_x = col - 32 | 37 |
| out_y = row_val - 4 | 0 |
| rastan_draw_tile_xy bounds (x∈[0,63], y∈[0,31]) | IN BOUNDS ✓ |

**Producing in-bounds coordinates**: YES — for text at rows 4-35, cols 0-63, the new decode produces valid (x, y) pairs in all cases.

### Effect of row-visibility filter (Build 323, before disabled):

The filter `row_val < 4` rejects rows 0-3. These correspond to C-window offsets 0x000-0x3FF (above the hardware viewport). For text intended to appear on screen (rows 4-35), the filter correctly passes. The filter does NOT explain an empty plane for properly positioned text.

**Build 324 (filter disabled) test**: Build 324 removed the filter. If the plane remains empty in Build 324, this confirms the filter was not the cause — the writes simply aren't happening.

## 5. `rastan_draw_tile_xy()` Write Audit

`rastan_draw_tile_xy()` is correct:
```c
pc080sn_fg_buffer[y * 64 + x] = tile_attr;
```
Bounds check: `x < 0 || x >= 64 || y < 0 || y >= 32`. For valid (x,y) from `text_writer_ptr_to_xy()`, this writes.

Whether tile_attr is non-zero depends on `text_writer_build_tile_attr()`. This function looks up `glyph_code` in `rastan_font_glyphs[]`, falls back to `arcade_tile = glyph_code`, then calls `genesistan_pc080sn_tile_vram_lut[arcade_tile]`. If the LUT entry is 0 (unmapped tile), `TILE_ATTR_FULL(palette, priority, 0, 0, 0)` is written — which renders as blank tile 0. However, known glyphs (0x30-0x5A digits/letters) have valid VRAM LUT entries.

## 6. FG Buffer State Before Commit

**No memset/clear of `pc080sn_fg_buffer` found anywhere in the codebase.** The buffer is in BSS (zero-initialized at startup) and written only by:
- `genesistan_bulk_tilemap_commit` (for addresses 0xC08000-0xC0BFFF via assembly)
- `rastan_draw_tile_xy()` (via text writer hooks)

If neither writes non-zero values before VBlank, the buffer remains all zeros from the previous frame's state (or startup zero-init).

## 7. FG Buffer Clear/Overwrite Audit

**No explicit clear path found.** However, there is a critical indirect clear mechanism:

**`sanitize_arcade_workram()`** runs during VBlank (after arcade tick, before commit). It scans all arcade workram words and zeros any long-word value where `(v & 0x00FF0000) == 0x00C00000`. This targets C-window pointer values stored in workram. It does NOT touch `pc080sn_fg_buffer` directly.

**`genesistan_bulk_tilemap_commit`** writes to `pc080sn_fg_buffer` when the arcade code performs memory writes to 0xC08000-0xC0BFFF. If the arcade code writes zeros to the entire C-window text layer (e.g., a clear loop that runs each frame during attract), those zero writes go through the bulk tilemap commit and overwrite any text that was written. Several C-window access paths ARE blocked by RTS+NOP patches (0x052858, 0x052974, 0x0575CE), but it's not confirmed that ALL zero-write loops are blocked.

**FG buffer overwritten/cleared before commit**: CANNOT CONFIRM OR DENY FROM CODE ALONE. This requires runtime observation.

## 8. FG Commit Audit

**The Build 314 mode gate has been removed.** `genesistan_pc080sn_commit_planes` (lines 872-894 of startup_trampoline.s) now runs unconditionally every VBlank:

```asm
genesistan_pc080sn_commit_planes:
    movem.l %d0-%d1/%a0-%a1, -(%sp)
    movea.l #0xC00004, %a1
    move.w  #0x8F02, (%a1)
    ; BG plane → VRAM 0xC000 (2048 words)
    ; FG plane → VRAM 0xE000 (2048 words)
    movem.l (%sp)+, %d0-%d1/%a0-%a1
    rts
```

**FG commit IS happening every frame.** There is no skip path. The commit writes whatever is in `pc080sn_fg_buffer` to VRAM 0xE000. If the buffer is zero, VRAM 0xE000 is set to all zeros → empty Plane A.

## 9. Current Visible Content Source

Based on the Exodus screenshots:
- **Settings menu phase** (Build 323, Exodus screenshot 1): Layer A shows correct horizontal text. Source: text writer hooks writing via `rastan_draw_tile_xy()`.
- **Attract phase** (Build 323, Exodus screenshot 2): Layer A is empty. Plane B also appears empty. The VRAM Pattern Viewer in Build 322 screenshots showed tiles present in VRAM, but no nametable content during attract.

The currently visible content (dots in BlastEm from Build 322 and earlier) came from **Plane A** — but driven by `genesistan_bulk_tilemap_commit` writing column-major C-window tile data, not the text writer hooks. In Build 323, those bulk tilemap writes (if they still run) now land at DIFFERENT positions in the buffer (because the bulk tilemap commit is still column-major), and may also be writing zero-value tiles.

**Primary visible content source in Build 322**: Plane A (FG buffer), populated by column-major bulk tilemap writes from C-window text layer data.

## 10. Single Most Likely Root Cause

**TEXT_HOOKS_NOT_RUNNING** during the attract phase for the content that was previously visible.

Evidence:
- Settings menu text works correctly in Build 323 (text hooks run for settings menu text_ids)
- Attract-mode text is empty in Build 323 (text hooks either not called, or called with null descriptors)
- The attract-mode tile content in Build 322 was produced by `genesistan_bulk_tilemap_commit` (column-major writes from C-window), NOT by the text writer hooks — this is why the content was "column-major" transposed
- The settings menu uses text_ids that map to valid descriptors in the patched table; attract-mode text may use different text_ids or paths

Supporting evidence: the remap spec has 3 RTS+NOP patches blocking `movea.l #0xC08000, A0` base-load paths (0x052858, 0x052974, 0x0575CE). These prevent the direct C-window tile-write loops that normally populate the text layer during attract. With those loops blocked, and the text hooks not firing for attract content, the FG buffer gets no writes.

## 11. Single Next Implementation Target

**Identify which arcade code path writes attract-mode text content to the C-window** and determine whether it is routed through the text writer hooks, blocked by an existing NOP patch, or bypassing all hooks entirely.

Specifically: trace what happens after `jsr 0x3BB48` and `jsr 0x3C3FE` are replaced — do other C-window write paths still execute for attract-mode content, and are they being silenced by the RTS patches?

The goal is to find the one unhooked (or over-silenced) path and add the appropriate hook or remove the blocking patch.

## 12. Final Verdict

Build 323's row-major decode fix is correct and works for settings menu text. Plane A is empty during attract because the previously visible attract-mode tile content came from the bulk tilemap commit (column-major direct C-window writes), not from the text writer hooks. The text writer hooks either don't fire for attract content, or fire but write zero-tile results. The fix is to identify the attract-mode content write path and ensure it routes through the corrected FG write pipeline.
