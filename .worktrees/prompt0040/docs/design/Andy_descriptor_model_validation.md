# Andy — Descriptor Model Validation

## 1. Executive Summary

Both the `%d2` column-advance fix and the `%d1` row-reset fix are correct and live. The descriptor model arithmetic is now correct. The cause of persistent near-checkerboard output is that the strip_index register (`%d7`) offsets the **source** tile selection but is never applied to the **destination** column in the staging write. The arcade issues 4 hook calls per frame (one per strip_index 0–3), each targeting a different sub-column of every 4-column group. But all 4 calls write to the same destination columns (`%d2 = 0, 4, 8, …, 60`), overwriting each other with the wrong tile content and leaving sub-columns 1, 2, 3 of every group as permanent checkerboard. The fix is two instructions added inside the inner row loop.

---

## 2. Inputs Used

- `apps/rastan-direct/src/main_68k.s` lines 44–48 (constants), 196–360 (full hook body, both fixes applied)
- `docs/design/Cody_bg_descriptor_column_advance_fix.md`
- `docs/design/Cody_bg_descriptor_row_reset_fix.md`
- `docs/design/Andy_post_d2_fix_no_visible_change_diagnosis.md`
- BlastEm screenshot: full checkerboard game screen, VRAM pattern viewer showing valid Title tile graphics, CRAM showing color palette
- Exodus VDP Image Window: vertical stripes repeating at 4-column intervals, spanning full screen height

---

## 3. Task 1 — Descriptor Count

`ARCADE_PC080SN_CWINDOW_BYTES = 0x4000` (line 48). Each descriptor advances `%d5` by `0x400`. `0x4000 / 0x400 = 16` descriptors covers the full CWindow. The hook initializes `moveq #15, %d6` + `dbra` = exactly 16 iterations. After 16 descriptors, `%d5` has advanced from `CWINDOW_BASE` to `CWINDOW_BASE + 0x4000`, covering the complete window.

**Descriptor count correct: YES**

---

## 4. Task 2 — Row Grouping

The inner row loop runs exactly 4 iterations (`moveq #3, %d4; dbra %d4`). Each iteration advances the source pointer by 8 bytes (`adda.w #8, %a4`). With the `%d1` reset fix applied (lines 352–353), all 16 descriptors use the same initial `%d1` (initial row). One hook call writes a horizontal band of 4 rows across 16 column groups. The 8-byte source stride (4 entries × 2 bytes) is consistent with 4 sub-columns per row entry.

The Exodus screenshot shows vertical stripes spanning the **full screen height** — confirming that all 32 rows have been populated across frames. If row grouping were incorrect, stripes would only appear at specific rows. The full-height coverage confirms 4-row grouping is correct and the `%d1` reset correctly delivers all rows over multiple arcade hook calls.

**Row grouping correct: YES**

---

## 5. Task 3 — Dest Pointer Interpretation

Constants: `ARCADE_PC080SN_CWINDOW_BASE_BG = 0x00C00000`, `ARCADE_PC080SN_CWINDOW_BYTES = 0x00004000`.

`%d4 = ((dest & 0x00FFFFFF) - 0x00C00000) >> 2`. Range: `0x000` to `0xFFF`.

- `%d1 = %d4 & 0x1F`: row 0–31. Bits[4:0] of `%d4`. ✓ (bit 5 is discarded by the second `andi.w #0x001F`; this correctly excludes the extended-row region beyond row 31.)
- `%d2 = (%d4 >> 6) & 0x3F`: column group. Bits[11:6] of `%d4`. Values for valid calls: multiples of 4 (0, 4, 8, …, 60). ✓

The extraction of row and column group from `%d4` is **correct**. However, `%d2` encodes the column **group** (the multiple-of-4 base column), not the individual nametable column. The individual column = `%d2 + strip_index`. The extraction produces a valid group-level column but is incomplete without the strip_index contribution from `%d7`.

**Dest→row/column extraction correct: NO** — `%d2` encodes column group correctly, but individual column requires `%d2 + %d7`; `%d7` is absent from the destination calculation.

---

## 6. Task 4 — Descriptor Sweep Model

The hook sweeps horizontally across 16 column groups per call, maintaining a constant 4-row band (after both fixes). This horizontal sweep direction is correct. The arcade issues 4 hook calls per frame:

| Strip call | `%d7` | Source sub-column | Dest columns (current) | Dest columns (correct) |
|-----------|-------|-------------------|----------------------|----------------------|
| 0 | 0 | sub-col 0 | 0, 4, 8, …, 60 | 0, 4, 8, …, 60 |
| 1 | 1 | sub-col 1 | 0, 4, 8, …, 60 ← WRONG | 1, 5, 9, …, 61 |
| 2 | 2 | sub-col 2 | 0, 4, 8, …, 60 ← WRONG | 2, 6, 10, …, 62 |
| 3 | 3 | sub-col 3 | 0, 4, 8, …, 60 ← WRONG | 3, 7, 11, …, 63 |

Strip calls 1, 2, and 3 overwrite the column-0 group with wrong source tiles (tiles intended for sub-columns 1, 2, 3 written to sub-column 0 positions). Sub-columns 1, 2, 3 of every group never receive any writes. 

The horizontal sweep model is structurally correct but the column targeting is incomplete.

**Horizontal sweep model correct: NO** — sweeps correctly but only addresses every 4th column; 75% of columns are never written because strip_index is not applied to the destination.

---

## 7. Task 5 — Visible Plane Coverage

The staging write (lines 327–331) computes `offset = row*128 + %d2*2` and writes to `staged_bg_buffer`. `vdp_commit_bg_strips_if_dirty` commits dirty rows to `VRAM_PLANE_B_BASE = 0xC000`. Plane B is the visible background plane (VDP reg 4 = 0x06). All written cells fall within `staged_bg_buffer`'s valid range (rows 0–31, columns 0–63). The commits land on the visible screen region.

**Writes land in visible region: YES**

---

## 8. Task 6 — Coherent Output Explanation

**Why VRAM tiles are correct:** `load_scene_tiles(0)` ran at boot, uploading all 841 Title manifest `(arcade_tile, vram_slot)` pairs from `genesistan_pc080sn_tile_rom` to VRAM. The BlastEm VRAM debugger confirms slots 20–860 contain readable Title tile graphics (characters, sprites, numerals). This is unrelated to the descriptor loop and is not affected by any of the recent fixes.

**Why BlastEm still shows full checkerboard:** `init_staging_state` fills all 2048 nametable entries with checkerboard references. After both fixes, each hook call correctly writes 4 rows × 16 column groups = 64 cells at columns 0, 4, 8, …, 60. But strip calls 1, 2, 3 overwrite those same 64 cells with wrong tile data (source tiles for sub-columns 1, 2, 3 written to sub-column 0 positions). The 1536 cells at columns 1, 2, 3, 5, 6, 7, … remain `init_staging_state` checkerboard. Plane B is committed with 75% checkerboard per row. At display scale, the dominant checkerboard pattern absorbs the garbled data at every 4th column. The screen appears fully checkerboard.

**Why Exodus shows vertical stripes:** The Exodus VDP Image Window renders the complete Plane B nametable. The 4-column periodic structure (1 column group with data, 3 column groups of checkerboard) produces visible vertical stripe bands. The stripes span the full screen height because all 32 rows have been populated across multiple hook calls over many frames (each with a different initial `%d1` row). The stripe period of approximately 4 columns visible in the screenshot directly corresponds to the column group stride.

Both outputs are consistent with the same nametable state: columns at multiples of 4 carry garbled (wrong sub-column) tile data; all other columns carry checkerboard.

---

## 9. Task 7 — Root Cause (Single)

**`%d7` (strip_index) is used to offset the source tile selection (`adda.w %d7*2, %a4`, lines 291–293) but is NOT applied to the destination column in the staging write (lines 327–330). The arcade issues 4 hook calls per frame with strip_index 0–3, each call loading source tiles for a different sub-column of each 4-column group. But all 4 calls compute `dest_offset = row*128 + %d2*2` (no `%d7` term), writing to the same 16 columns (0, 4, 8, …, 60). Strip calls 1–3 overwrite those columns with tiles intended for sub-columns 1, 2, 3. Sub-columns 1, 2, 3 of every group receive no writes. 48 of 64 columns remain as permanent checkerboard init fill.**

---

## 10. Task 8 — Next Fix (Single)

Inside `.Lbg_hook_row_loop`, after the existing column offset computation (`add.w %d2, %d0; add.w %d2, %d0`, lines 329–330) and before the staging write (`move.w %d3, 0(%a6,%d0.w)`, line 331), insert:

```asm
add.w   %d7, %d0
add.w   %d7, %d0         ; +strip_index * 2
```

The resulting offset: `row*128 + (%d2 + strip_index)*2`.

**Why `%d7` twice:** The column byte offset requires `column * 2`. Adding `%d7` twice produces `strip_index * 2`. Same pattern used for `%d2`.

**Bounds check:** `%d2` takes values 0, 4, 8, …, 60. `%d7` takes values 0, 1, 2, 3 (four sub-columns of the 8-byte tile group). `%d2 + %d7` max = 60 + 3 = 63. Max byte offset = 31*128 + 63*2 = 4094. `staged_bg_buffer` is 4096 bytes. ✓

**`%d7` register invariance:** `%d7` is loaded once at line 200 (`move.w ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d7`) and is not modified anywhere in the hook body. It is the same value for all 64 row-loop iterations across 16 descriptors. ✓

**After this fix:** Strip call 0 (`%d7=0`) writes cols 0, 4, 8, …, 60 with correct sub-column 0 source tiles. Strip call 1 (`%d7=1`) writes cols 1, 5, 9, …, 61 with correct sub-column 1 source tiles. Together, all 4 strip calls per frame write all 64 columns with correct tile content.

---

## 11. Why Prior Diagnoses Did Not Catch This

`Andy_title_screen_zero_input_diagnosis.md` identified `%d2` not advancing (fixed), and `Andy_post_d2_fix_no_visible_change_diagnosis.md` identified `%d1` not resetting (fixed). Both were real bugs. After both fixes, the row/column group arithmetic is correct. The strip_index destination issue is structurally independent and only becomes the dominating failure once the arithmetic bugs are resolved. The Exodus vertical stripe pattern (4-column period) is the first clear visual confirmation that the remaining issue is specifically the 4-sub-column distribution.
