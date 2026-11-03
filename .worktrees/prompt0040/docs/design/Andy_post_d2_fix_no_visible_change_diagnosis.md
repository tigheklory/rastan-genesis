# Andy — Post-%d2-Fix No-Visible-Change Diagnosis

## 1. Executive Summary

The `%d2` column-advance fix is correct and live. It did not produce visible improvement because `%d1` (row index) accumulates a +4 advance per descriptor via the inner loop, but the PC080SN dest-pointer semantics dictate the row must remain constant across all 16 descriptors. The result is a diagonal write pattern: each descriptor writes a different (row, column) pair instead of all 16 descriptors writing the same 4-row group at advancing columns. Each hook call populates only 2 of 64 cells per row, which is visually indistinguishable from full checkerboard. The `%d2` fix is correct but insufficient. The next fix is `subq.w #4, %d1` / `andi.w #0x001F, %d1` at `.Lbg_hook_desc_done`.

---

## 2. Inputs Used

- `apps/rastan-direct/src/main_68k.s` lines 44–48 (constants), 196–362 (full hook body)
- `docs/design/Cody_bg_descriptor_column_advance_fix.md`
- `docs/design/Andy_title_screen_zero_input_diagnosis.md`
- `docs/design/Andy_scene_transition_readiness.md`
- BlastEm screenshot: full checkerboard screen, real tile data visible in VRAM pattern viewer
- Exodus screenshot: scrambled / garbled horizontal-band output in game window

---

## 3. Task 1 — Verify the `%d2` Fix is Live in the Executed Path

From `main_68k.s` lines 348–352:

```asm
.Lbg_hook_desc_done:
    addi.l  #0x00000400, %d5
    addq.w  #4, %d2
    andi.w  #0x003F, %d2
    dbra    %d6, .Lbg_hook_desc_loop
```

The fix is present and placed at the only label both valid and invalid descriptor paths converge on. Valid descriptors reach `.Lbg_hook_desc_done` via `bra.s .Lbg_hook_desc_done` (line 342). Invalid descriptors reach it by fall-through from `.Lbg_hook_invalid_desc` (line 344). The fix is not bypassed by any path.

**`%d2` fix live in executed path: YES**

---

## 4. Task 2 — Verify Column Advance Semantics

The constants confirm:
- `ARCADE_PC080SN_CWINDOW_BASE_BG = 0x00C00000` (line 47)
- `ARCADE_PC080SN_CWINDOW_BYTES = 0x00004000` (line 48)

`%d4 = (dest & 0x00FFFFFF - 0x00C00000) >> 2`. `%d2 = (%d4 >> 6) & 0x3F`.

Per descriptor, `%d5` advances by `0x400`. Corresponding `%d4` advance = `0x400 / 4 = 0x100`. Column advance = `(0x100 >> 6) & 0x3F = 4`. This matches `addq.w #4, %d2`. The mask `&0x003F` matches the initial extraction. The `+4` advance is correct.

**Current `%d2` advance semantics correct: YES**

---

## 5. Task 3 — Verify Dest-Pointer / Row / Column Relationship Across the Outer Loop

`%d5` advances by `0x400` per descriptor. The row-encoding bits of `%d5` are bits[4:0] of `(dest - CWINDOW_BASE) / 4`. `0x400 / 4 = 0x100`; bits[4:0] of `0x100 = 0`. **The row bits do not change as `%d5` advances.** All 16 descriptors in a single hook call correspond to the same row group from the dest-pointer perspective.

However, `%d1` (row index) is modified by the inner row loop (lines 337–338: `addq.w #1, %d1; andi.w #0x001F, %d1`, 4 iterations). After the inner loop, `%d1 = initial_row + 4 (mod 32)`. This advance is NOT reversed at `.Lbg_hook_desc_done`. It carries into the next descriptor iteration.

After the fix, the relationship is:
- `%d5` advance: row bits unchanged → row should be constant
- `%d2` advance: +4 per descriptor → correct
- `%d1` advance: +4 per descriptor (via inner loop) → **contradicts dest semantics**

`%d1` and `%d5` are NOT coherent. `%d2` and `%d5` are coherent.

**Row/column/dest relationship remains coherent: NO**

---

## 6. Task 4 — Verify Descriptor Loop Coverage Model

`Andy_title_screen_zero_input_diagnosis.md` described the post-fix expected behavior as "16 descriptors × 4 cols apart = 64 columns covered with step 4." That model assumed `%d1` would remain constant across descriptors (all 16 writing the same 4-row group at different columns).

The actual post-fix behavior is different. With `%d1` advancing +4 per descriptor:

| Descriptor | Row start | Column |
|-----------|-----------|--------|
| 0 | initial_row | 0 |
| 1 | initial_row + 4 | 4 |
| 2 | initial_row + 8 | 8 |
| ... | ... | ... |
| 7 | initial_row + 28 | 28 |
| 8 | initial_row + 0 (wrap) | 32 |
| ... | ... | ... |
| 15 | initial_row + 28 | 60 |

This is a **diagonal** pattern, not a horizontal sweep. The coverage model assumed by the prior diagnosis was not realized by the code.

**Descriptor coverage model for title correct: NO**

---

## 7. Task 5 — Why Checkerboard Still Dominates

With the diagonal write pattern and initial_row=0, initial_col=0:

Each of the 32 rows gets exactly **2 real-tile entries** per hook call:
- Row 0: col 0, col 32
- Row 4: col 4, col 36
- Row 8: col 8, col 40
- etc.

The other **62 columns of every row** retain the `init_staging_state` checkerboard fill.

`bg_row_dirty` receives set bits for all 32 rows (every row is touched at least once per call). `vdp_commit_bg_strips_if_dirty` commits all 32 rows to Plane B VRAM. But each committed row is 62/64 = 97% checkerboard. The 2 real-tile entries per row are visually swamped.

The checkerboard does NOT persist because of convergence lag, wrong committed region, or commit path failure. It persists because diagonal writes populate only 3.1% of the nametable (64/2048 cells) per hook call, and each row's committed 128 bytes is almost entirely checkerboard.

**Checkerboard persistence explained by a different cause: YES**
**Cause: diagonal writes yield 2 real-tile cells per row out of 64; committed rows are 97% checkerboard**

---

## 8. Task 6 — BlastEm vs Exodus Difference

Both emulators are running the same post-fix ROM. The staged_bg_buffer state is identical in both: 32 rows each with 2 real-tile entries and 62 checkerboard entries committed to Plane B.

**BlastEm** renders Plane B from the live nametable. With 2 real-tile entries per row (at specific columns), and those tiles using the debug rainbow palette (`palette_init_words`), the handful of real-tile cells appear as small colored rectangles against the dominant red/green checkerboard. At the emulator's display scale, these isolated cells are visually absorbed into the checkerboard grid and are not distinguishable. BlastEm renders what looks like full checkerboard.

**Exodus** shows scrambled horizontal-band output because the scattered real-tile data at diagonal nametable positions creates visible artifacts in the plane viewer rendering. Exodus's image browser or plane view layout makes the sparse but non-zero real-tile data appear as garbled bands rather than a clean checkerboard. The patterns correspond to the diagonal cell distribution from the hook writes.

Both outputs arise from the same underlying nametable state: mostly checkerboard with real-tile cells at diagonal positions. The visual difference is rendering presentation, not a different hardware state.

**Both emulator outputs consistent with same root cause: YES**

---

## 9. Task 7 — Root Cause (Single)

**`%d1` (row index) accumulates +4 per descriptor via the inner loop, but the PC080SN dest-pointer semantics (0x400 advance has zero row bits) require `%d1` to remain constant across all 16 descriptors.**

All 16 descriptors should write rows initial_row through initial_row+3 at columns initial_col, initial_col+4, ..., initial_col+60. Instead, both `%d1` and `%d2` advance by +4 per descriptor, producing a diagonal pattern where each descriptor targets a unique (row, column) position. Per hook call, only 64 of 2048 nametable cells receive real tile data, and only 2 cells per row are populated. The VDP commit fires for all 32 rows but each row is 97% checkerboard. No visible improvement results.

The `%d2` fix is correct. It is insufficient because the row advance is the dominant remaining bug.

---

## 10. Task 8 — Next Fix (Single)

At `.Lbg_hook_desc_done`, after the existing `andi.w #0x003F, %d2` (line 351), insert:

```asm
subq.w  #4, %d1
andi.w  #0x001F, %d1
```

**Why `subq.w #4`:** The inner loop increments `%d1` exactly 4 times. Subtracting 4 restores `%d1` to `initial_row` regardless of the starting value.

**Why `andi.w #0x001F`:** Necessary for wrapping. Example: initial_row=28 → inner loop leaves `%d1=0` (32 & 0x1F). After `subq.w #4`: `0xFFFC`. After `andi.w #0x001F`: `0x001C = 28`. ✓

**Coverage for invalid descriptor path:** `.Lbg_hook_invalid_desc` does `addq.w #4, %d1; andi.w #0x001F, %d1` then falls through to `.Lbg_hook_desc_done`. The `subq.w #4, %d1; andi.w #0x001F, %d1` at `.Lbg_hook_desc_done` will undo the +4. Net effect on `%d1` for invalid descriptors: unchanged (restored to initial_row). ✓

After this fix, combined with the existing `%d2` advance, all 16 descriptors will write rows initial_row–initial_row+3 at columns 0, 4, 8, ..., 60. One hook call populates a full horizontal band of 4 rows across all 16 column groups. Over time (or over multiple hook calls per frame for strip_index 0–3), all columns converge correctly.

---

## 11. Note on Prior Diagnosis

`Andy_title_screen_zero_input_diagnosis.md` correctly identified that `%d2` never advanced. Its "next fix" recommendation was correct and minimal. However, it did not identify the row accumulation issue as a co-dependent bug. The %d2 fix alone was architecturally insufficient because fixing only column advance while row advance remains unconstrained produces a diagonal rather than a horizontal sweep. The %d2 fix must remain in place; the `%d1` reset fix must be added to it.
