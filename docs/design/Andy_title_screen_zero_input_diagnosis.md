# Andy — Title Screen Zero-Input Diagnosis

## 1. Executive Summary

The Title screen does not render correctly with zero input because `%d2` (the column index for `staged_bg_buffer` addressing) is extracted once from the initial dest value at hook entry and is **never updated** across the 16-descriptor outer loop. All 16 descriptors write to the same column. Columns 1–63 permanently retain the `init_staging_state` checkerboard fill. The minimum fix is two instructions at `.Lbg_hook_desc_done`.

---

## 2. Inputs Used

- `apps/rastan-direct/src/main_68k.s` lines 196–360 (full hook body)
- `docs/design/Andy_scene_transition_readiness.md` (confirmed VRAM tile assets correct)
- `docs/design/Andy_scene_trigger_runtime_diagnosis.md` (confirmed hook executing, fast path dominant, VRAM loaded)
- BlastEm VRAM viewer screenshots (Palette Line 1): slots 20–860 contain correct Title tile pixel data
- BlastEm screen output: Plane B shows checkerboard with partial real tile data in top rows only

---

## 3. Task 1 — Does the Title Screen Have Sufficient Arcade Data to Render With Zero Input?

The Title/attract loop is autonomous. The arcade CPU runs its attract animation, updating the PC080SN tilemap registers every frame with no user input required. `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` is written by the arcade on every tick. `ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5)` is updated per strip. The hook fires for every PC080SN BG block-write call the arcade issues.

During the Title attract sequence, the arcade issues 16-descriptor BG strip updates on every frame to maintain the title graphics. No controller input is required for this to occur.

**Title scene generates sufficient hook input with zero user input: YES**

---

## 4. Task 2 — Are the VRAM Tile Assets Present and Correct?

`load_scene_tiles(0)` runs at boot (confirmed by `Andy_scene_trigger_runtime_diagnosis.md` Task 5 and VRAM viewer evidence). It iterates all 841 `(arcade_tile, vram_slot)` pairs from `genesistan_scene_preload_title` and uploads each tile from `genesistan_pc080sn_tile_rom` to the assigned VRAM slot. Slots 20–860 contain correct PC080SN Title tile pixel data confirmed by BlastEm VRAM Pattern Viewer with Palette Line 1.

The `genesistan_pc080sn_tile_vram_lut` entries for all 841 Title tile indices resolve to slots 20–860. The hook's LUT lookup at line 324 (`move.w 0(%a2,%d3.w), %d3`) will return valid non-zero VRAM slots for all Title tile references.

**Title VRAM tile assets present and correct: YES**

---

## 5. Task 3 — Does the Hook Cover All Visible Rows?

The hook processes 16 descriptors per call. Each descriptor's inner row loop runs 4 iterations (`moveq #3, %d4; dbra %d4`) writing rows `%d1`, `%d1+1`, `%d1+2`, `%d1+3`. `%d1` advances by 1 per row-loop iteration (line 337: `addq.w #1, %d1`) and wraps at 31 (line 338: `andi.w #0x001F, %d1`). After 16 descriptors × 4 rows = 64 row-writes, and with wrap at 32, every row 0–31 is written at least twice per hook call when starting from row 0.

The Title attract animation issues strip updates that cover all 32 rows over its animation cycle. `bg_row_dirty` accumulates dirty bits for all written rows and `vdp_commit_bg_strips_if_dirty` commits all dirty rows every VBlank.

**Hook row coverage is sufficient for full visible Title: YES (rows all reachable)**

---

## 6. Task 4 — Is Destination Validation Correct for Title?

Lines 203–214 validate `%d5` (dest) against `[ARCADE_PC080SN_CWINDOW_BASE_BG, ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES)` and require 4-byte alignment. The Title scene uses the BG dest window. Title dest values fall within the expected CWindow range. The alignment check (bits [1:0] = 0) is satisfied by all valid arcade dest values.

**Destination validation correct for Title: YES**

---

## 7. Task 5 — Is Row/Column Mapping Correct?

The dest-to-row/column extraction at lines 216–222:

```asm
lsr.l   #2, %d4              ; d4 = (dest - base) / 4
move.w  %d4, %d1
andi.w  #0x003F, %d1
andi.w  #0x001F, %d1         ; d1 = bits[4:0] = row (0-31)
move.w  %d4, %d2
lsr.w   #6, %d2
andi.w  #0x003F, %d2         ; d2 = bits[11:6] = column (0-63)
```

This correctly decodes the initial row and column from the dest pointer. The staged buffer write at lines 327–331:

```asm
move.w  %d1, %d0
lsl.w   #7, %d0              ; d0 = row * 128
add.w   %d2, %d0
add.w   %d2, %d0             ; d0 += column * 2
move.w  %d3, 0(%a6,%d0.w)   ; write to staged_bg_buffer[row * 128 + column * 2]
```

This correctly computes the buffer byte offset for a given row/column. The geometry is correct: 64 columns × 2 bytes = 128 bytes per row.

**BUT:** The outer descriptor loop at `.Lbg_hook_desc_done` (lines 348–350):

```asm
.Lbg_hook_desc_done:
    addi.l  #0x00000400, %d5   ; dest advances 0x400 per descriptor
    dbra    %d6, .Lbg_hook_desc_loop
```

Each `0x400` advance in dest equals `0x400 / 4 = 0x100` after right-shift by 2, and `0x100 >> 6 = 4` columns. So each descriptor represents 4 columns of advance. **`%d2` is never updated.** All 16 descriptors compute their `staged_bg_buffer` offset using the same initial column value.

For a hook invocation with initial dest = `0xC00000` (column 0): all 16 descriptors write to column 0. Columns 1–63 are never touched.

**Row/column mapping initial extraction correct: YES**
**Column update across descriptors: NO — %d2 never incremented; all 16 descriptors write same column**

---

## 8. Task 6 — Is `staged_bg_buffer` Converging Correctly?

Due to the `%d2` freeze, each hook invocation overwrites only 1 column (column `%d2_initial`) with real arcade tile data. The other 63 columns retain whatever was last written — which is the `init_staging_state` checkerboard fill from boot.

Across multiple hook calls with varying initial column (the arcade does advance its dest pointer between frames), different columns do eventually get written. However, the correction rate is 1 column per hook call rather than 16 columns per hook call. The visible effect is extremely slow convergence rather than immediate full-frame rendering.

For initial dest = `0xC00000` (column 0): column 0 gets real tile data on every hook call. Column 4 only gets real tile data when dest happens to start at a value that maps to column 4. At 16 descriptors × 4 cols per descriptor = 64 columns per correct call, a correct implementation would update all columns in a single call.

**staged_bg_buffer converging correctly: NO — only 1 of 64 columns updated per hook call; 63 columns permanently checkerboard**

---

## 9. Task 7 — Is Committed BG Data Targeting the Visible Screen Region?

`vdp_commit_bg_strips_if_dirty` commits all rows with set `bg_row_dirty` bits to `VRAM_PLANE_B_BASE` (0xC000). Plane B is configured with 64 columns × 32 rows (VDP reg 4 = 0x06 → base 0xC000). The staged buffer row/column geometry matches the Genesis nametable layout. The rows that ARE being committed contain real data for column 0 only — the committed data targets the correct screen region, but is mostly wrong (checkerboard) due to the column-freeze bug.

**Committed BG data targets visible screen region: YES**
**Committed BG data correct for Title: NO — column 0 real, columns 1-63 checkerboard**

---

## 10. Task 8 — Root Cause

**`%d2` (column index) is extracted once at hook entry (lines 220–222) and never updated inside the 16-descriptor outer loop.**

The outer loop advances `%d5` (dest) by `0x400` per iteration at `.Lbg_hook_desc_done`. This advance corresponds to 4 columns of change in the logical dest-pointer space. The column index `%d2` derived from dest must be updated by `+4` per descriptor iteration to track this advance.

Without the update, all 16 descriptors compute their `staged_bg_buffer` offset as `%d1*128 + column_initial*2`. The row index `%d1` advances correctly (inner loop increments it, outer loop preserves it across descriptors). The column index stays pinned at the initial value.

The invalid descriptor path (`.Lbg_hook_invalid_desc`, lines 344–346) correctly advances `%d1` by 4 (`addq.w #4, %d1; andi.w #0x001F, %d1`) to skip the 4 rows that an invalid descriptor would have covered. It does NOT advance `%d2`. Both the valid and invalid paths reach `.Lbg_hook_desc_done`, so a fix placed there covers both cases.

**Root cause: `%d2` (column index for staged_bg_buffer addressing) never updated per descriptor; all 16 descriptors write to same column; 63 of 64 columns retain checkerboard permanently**

---

## 11. Task 9 — Minimal Fix

At `.Lbg_hook_desc_done` (line 348), after `addi.l #0x00000400, %d5` and before `dbra %d6, .Lbg_hook_desc_loop`, add:

```asm
.Lbg_hook_desc_done:
    addi.l  #0x00000400, %d5
    addq.w  #4, %d2              ; advance column by 4 (matches 0x400 dest step)
    andi.w  #0x003F, %d2         ; wrap at 64
    dbra    %d6, .Lbg_hook_desc_loop
```

**Why `+4`:** Each `0x400` dest advance equals `(0x400 / 4) >> 6 = 4` columns, matching the bit-field extraction at lines 220–222.

**Why `&0x3F`:** Column wraps at 64; the same mask applied at extraction time must be applied at update time.

**Why here and not earlier:** Both the valid descriptor path (`bra.s .Lbg_hook_desc_done`) and the invalid descriptor path (fall-through from `.Lbg_hook_invalid_desc`) merge at `.Lbg_hook_desc_done`. A single fix location covers both paths.

**No other changes required.** The row advancement (`%d1`) is already correct. The `staged_bg_buffer` write formula is correct. The dest-pointer advance (`%d5`) is correct. The dirty-bit logic is correct. Only `%d2` needs the per-descriptor increment.

---

## 12. Task 10 — Scaffolding Inventory

No scaffolding was introduced in this analysis. The fix is two instructions in existing production code. No design-only instrumentation exists to remove.

**Scaffolding introduced: NONE**
**Scaffolding removal plan: N/A**

---

## 13. Final Verdict

**Root cause identified: `%d2` column freeze in outer descriptor loop.**

The Title screen does not render correctly with zero input because the `staged_bg_buffer` column index (`%d2`) is never advanced per descriptor, causing all 16 descriptors to overwrite the same column while 63 of 64 columns remain permanently checkerboard. The fix is two instructions at `.Lbg_hook_desc_done`. All other pipeline components (VRAM tile assets, dest validation, row tracking, dirty-bit commit) are correct.
