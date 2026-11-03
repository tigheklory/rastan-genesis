# Cody — BG Block Copy Hook Implementation

## Context

This prompt implements `genesistan_hook_tilemap_bg_blockcopy` and the supporting `init_staging_state` dirty-flag fix. See `docs/design/Andy_bg_blockcopy_hook_warm_restart_analysis.md` for the full analysis.

**Why this is needed:** The Title scene's BG tilemap is written by a block copy function at arcade PC `0x05A4E0` that reads per-cell tile codes from a ROM source table and writes them directly to PC080SN BG RAM `[0xC00000, 0xC04000)`. On Genesis this range is the VDP DATA port. These writes bypass `staged_bg_buffer` entirely. The hook intercepts this function, reads the source tile codes, translates them through `genesistan_pc080sn_tile_vram_lut`, and writes the resulting nametable words to `staged_bg_buffer`, making the BG content visible on Plane B.

**Additionally:** The arcade warm-restarts `main_68k` every cycle (via `JMP` to `ROM[0x0004]` after the delay loop). This means `init_staging_state` runs every cycle and currently sets `bg_row_dirty = 0xFFFFFFFF`, causing the checkerboard buffer to flush over any valid BG content at the next VINT. The fix changes `init_staging_state` to start with `bg_row_dirty = 0`.

---

## Preconditions to Verify

Before making any changes, verify all of the following. If any check fails, stop and report.

1. `genesistan_hook_tilemap_bg_fill` exists in `apps/rastan-direct/src/main_68k.s`
2. `genesistan_pc080sn_tile_vram_lut` exists in `apps/rastan-direct/src/main_68k.s`
3. `genesistan_pc080sn_attr_lut` exists in `apps/rastan-direct/src/main_68k.s`
4. `staged_bg_buffer` exists in `apps/rastan-direct/src/main_68k.s`
5. `bg_row_dirty` exists in `apps/rastan-direct/src/main_68k.s`
6. `init_staging_state` contains the line `move.l  #0xFFFFFFFF, bg_row_dirty`
7. ROM bytes at arcade offset `0x05A4E0` in `build/regions/maincpu.bin` are exactly `24 49 32 C2 32 D8 53 40` (8 bytes)
   - Command: `python3 -c "f=open('build/regions/maincpu.bin','rb'); f.seek(0x05A4E0); print(f.read(8).hex())"`
   - Expected: `244932c232d85340`
8. `opcode_replace_count` in `specs/rastan_direct_remap.json` is currently `35`
9. `required_symbols` in `specs/rastan_direct_remap.json` does NOT yet contain `genesistan_hook_tilemap_bg_blockcopy`
10. There is no existing `opcode_replace` entry for `arcade_pc` `"0x05A4E0"` in `specs/rastan_direct_remap.json`

---

## Change 1: Fix `init_staging_state` — `apps/rastan-direct/src/main_68k.s`

In the `init_staging_state` function, find the line:

```asm
    move.l  #0xFFFFFFFF, bg_row_dirty
```

Replace it with:

```asm
    clr.l   bg_row_dirty
```

This is a single-line change. The rest of `init_staging_state` is unchanged.

**Why:** With `bg_row_dirty = 0xFFFFFFFF`, the warm-restart cycle's VINT flushes the entire checkerboard `staged_bg_buffer` to Plane B VRAM every frame, overwriting any BG content written by hooks. With `bg_row_dirty = 0`, only rows dirtied by hooks in the current tick are flushed at VINT.

---

## Change 2: Add Global Symbol — `apps/rastan-direct/src/main_68k.s`

In the `.global` declarations at the top of the file, add immediately after the `.global genesistan_hook_tilemap_bg_fill` line:

```asm
    .global genesistan_hook_tilemap_bg_blockcopy
```

---

## Change 3: Add Hook Function — `apps/rastan-direct/src/main_68k.s`

Place the new function `genesistan_hook_tilemap_bg_blockcopy` in `.text`, immediately after the closing `rts` of `genesistan_hook_tilemap_bg_fill` and before `vdp_commit_tiles_if_dirty`.

### Register contract at hook entry (from arcade caller)
- `A0` = source ROM table pointer (word array of per-cell tile codes)
- `A1` = destination BG RAM base address (e.g., `0xC00320`, `0xC00328`)
- `D0` = columns per row (e.g., 28)
- `D1` = rows (e.g., 21 or 20)
- `D2` = attribute word (1 in all known callers)
- Other registers: caller-saved; hook must preserve everything via `movem.l`

### Hook implementation

```asm
genesistan_hook_tilemap_bg_blockcopy:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    ; --- Range check: A1 must be in [0xC00000, 0xC04000) ---
    movea.l %a1, %a4           ; a4 = copy of dest base
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    cmpi.l  #0x00C00000, %d2
    blo     .Lbc_done
    cmpi.l  #0x00C04000, %d2
    bhs     .Lbc_done

    ; --- Guard: D0 (cols) and D1 (rows) must be non-zero ---
    tst.w   %d0
    beq     .Lbc_done
    tst.w   %d1
    beq     .Lbc_done

    ; --- Precompute genesis_attr from D2 (attr word) ---
    ; Same two-shift extraction as genesistan_hook_tilemap_bg_fill,
    ; but sourced from D2 instead of D0[31:16].
    lea     genesistan_pc080sn_attr_lut, %a3

    move.w  %d2, %d5
    andi.w  #0x0003, %d5           ; palette bits [1:0]

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #6, %d7
    andi.w  #0x0001, %d7
    lsl.w   #2, %d7
    or.w    %d7, %d5               ; hflip from D2[14]

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #7, %d7
    andi.w  #0x0001, %d7
    lsl.w   #3, %d7
    or.w    %d7, %d5               ; vflip from D2[15]

    move.w  %d2, %d7
    lsr.w   #8, %d7
    lsr.w   #5, %d7
    andi.w  #0x0001, %d7
    lsl.w   #4, %d7
    or.w    %d7, %d5               ; priority from D2[13]

    add.w   %d5, %d5               ; index × 2 (word table)
    move.w  0(%a3,%d5.w), %d5      ; d5 = genesis_attr (precomputed, constant per call)

    ; --- Compute start_row and start_col from A1 initial byte offset ---
    ; Uses same mapping as genesistan_hook_tilemap_bg_fill:
    ;   longword_off = byte_off >> 2
    ;   col = longword_off & 0x3F   (0–63)
    ;   row = (longword_off >> 6) & 0x1F   (0–31)
    move.l  %a4, %d2
    andi.l  #0x00FFFFFF, %d2
    subi.l  #0x00C00000, %d2       ; d2 = byte_off
    lsr.l   #2, %d2                ; d2 = longword_off

    move.w  %d2, %d4               ; d4 = start_col = longword_off & 0x3F
    andi.w  #0x003F, %d4

    move.w  %d2, %d3               ; d3 = start_row = (longword_off >> 6) & 0x1F
    lsr.w   #6, %d3
    andi.w  #0x001F, %d3

    ; --- Save loop counts ---
    ; d0 = cols per row (will be used as inner loop down-counter each row)
    ; d1 = rows remaining (outer loop counter)
    ; d6 = saved col count (to restore d0 at start of each row)
    move.w  %d0, %d6               ; d6 = saved col count

    ; --- Preload LUT base ---
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    lea     staged_bg_buffer, %a6

    ; --- Row counter in d1, current row index in d3 ---
    ; d4 = start_col (constant base, col index offsets from 0 per row)
    ; We need: for each row j, for each col i:
    ;   staged_row = d3 + row_j,  staged_col = d4 + col_i
    ; Use d7 as row_j counter (0..D1-1), use d0 as col_i down-counter.
    ; Because we need both row_j and col_i simultaneously, track row_j separately.

    moveq   #0, %d7                ; d7 = current row offset (0-based from start_row)

.Lbc_row_loop:
    move.w  %d6, %d0               ; restore col count for this row

.Lbc_col_loop:
    ; Read source tile code word
    move.w  (%a0)+, %d2            ; d2 = tile_code_word from source ROM
    andi.w  #0x3FFF, %d2           ; mask off top 2 attribute bits
    add.w   %d2, %d2               ; × 2 (word table index)
    move.w  0(%a2,%d2.w), %d2      ; d2 = vram_slot

    or.w    %d5, %d2               ; d2 = nametable_word = vram_slot | genesis_attr

    ; Compute staged_bg_buffer offset:
    ;   staged_row = d3 + d7  (start_row + row_offset)
    ;   staged_col = d4 + (d6 - d0)  (start_col + col_index)
    ;   col_index = d6 - d0  (cols done so far = saved_count - remaining)
    ;   offset = staged_row * 128 + staged_col * 2
    move.w  %d3, %d2
    ; compute staged_row into scratch — but we need d2 for nametable_word already!
    ; Use a different scratch. All d-regs are in use; use the stack carefully.
    ; Register allocation:
    ;   d0 = col down-counter (changes each iter)
    ;   d1 = row down-counter
    ;   d2 = scratch (tile_code / nametable_word / offset)
    ;   d3 = start_row (constant this call)
    ;   d4 = start_col (constant this call)
    ;   d5 = genesis_attr (constant this call)
    ;   d6 = saved col count (constant this call)
    ;   d7 = row offset (increments per outer loop)
    ;   a0 = source pointer (advances)
    ;   a2 = tile vram lut base
    ;   a3 = attr lut base
    ;   a4 = dest base (for range check; not needed after precompute)
    ;   a6 = staged_bg_buffer base
    ;
    ; We already used d2 for nametable_word. Save it before computing offset.
    ; Use a5 as a temp for nametable_word.

    ; NOTE: Rewrite using a5 for nametable_word to free d2 for offset arithmetic.
    ; (The movem saved a5 so it is safe to clobber here.)

    ; Actually, it is simpler to compute offset FIRST, then load nametable into d2.
    ; Re-order: compute offset into a scratch, write nametable_word to that offset.

    ; --- Reordered inner body ---
    ; Compute col_index = d6 - d0  (cols remaining decrements after this: done below)
    ; At start of iteration: d0 = cols remaining BEFORE decrement.
    ; col_index = d6 - d0  (0 when d0=d6, 1 when d0=d6-1, etc.)
    move.w  %d6, %d2
    sub.w   %d0, %d2               ; d2 = col_index = (saved_count - remaining_count)

    add.w   %d4, %d2               ; d2 = staged_col = start_col + col_index

    move.w  %d3, %a5               ; a5.w = start_row (use address reg as scratch word)
    ; staged_row = start_row + row_offset (d7)
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row
    lsl.w   #7, %d2                ; d2 = staged_row * 128

    ; staged_col (temp):
    move.w  %d6, %a5
    sub.w   %d0, %a5               ; a5 = col_index
    add.w   %d4, %a5               ; a5 = staged_col

    add.w   %a5, %d2               ; d2 += staged_col
    add.w   %a5, %d2               ; d2 += staged_col  (×2, each entry 2 bytes)

    ; Now read tile code and build nametable_word
    move.w  -2(%a0), %a5           ; re-read tile code (A0 already advanced above — need to re-read)
    ; Correction: advance A0 AFTER reading, OR read before computing offset.
    ; This re-ordering conflict means we should read the tile code first into a5,
    ; compute the offset into d2, then assemble nametable_word. See corrected version below.
    ; (This note exists to flag the ordering; the clean version follows.)

    move.w  %d2, %d2               ; no-op; placeholder — offset is in d2
    ; Write nametable_word to staged_bg_buffer:
    ; nametable_word = ? — needs to be in a register. Use a5 for it.
    ; This section is getting tangled. Clean version below.

    subq.w  #1, %d0
    bne.s   .Lbc_col_loop

    addq.w  #1, %d7                ; row_offset++
    subq.w  #1, %d1
    bne.s   .Lbc_row_loop

.Lbc_done:
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

**Important:** The inner loop body above has a register conflict (d2 used for both nametable_word and offset arithmetic, and A0 advanced before offset computed). Cody should resolve this by reading the tile code FIRST into a dedicated register, computing the offset second, then writing. Here is the correct clean inner loop body to use instead:

```asm
.Lbc_col_loop:
    ; Step 1: compute staged_col and staged_row → offset in d2
    move.w  %d6, %d2
    sub.w   %d0, %d2               ; d2 = col_index (d6 - d0, d0 not yet decremented)
    add.w   %d4, %d2               ; d2 = staged_col = start_col + col_index

    move.w  %d7, %a5
    add.w   %d3, %a5               ; a5 = staged_row = start_row + row_offset
    move.w  %a5, %d2
    lsl.w   #7, %d2                ; d2 = staged_row * 128

    move.w  %d6, %a5
    sub.w   %d0, %a5               ; a5 = col_index
    add.w   %d4, %a5               ; a5 = staged_col
    add.w   %a5, %d2               ; d2 += staged_col
    add.w   %a5, %d2               ; d2 += staged_col  (×2 for byte offset)

    ; Step 2: read tile code, translate to nametable_word in a5
    move.w  (%a0)+, %a5            ; a5 = tile_code_word (A0 advances)
    move.w  %a5, %a5               ; no-op; a5 holds tile_code_word
    ; mask and LUT lookup via d scratch (d2 is the offset — save it to a4)
    movea.l %d2, %a4               ; a4 = offset (free a4, dest base no longer needed)
    move.w  %a5, %d2
    andi.w  #0x3FFF, %d2           ; d2 = tile_code & 0x3FFF
    add.w   %d2, %d2               ; d2 = code × 2
    move.w  0(%a2,%d2.w), %d2      ; d2 = vram_slot
    or.w    %d5, %d2               ; d2 = nametable_word = vram_slot | genesis_attr

    ; Step 3: write nametable_word to staged_bg_buffer
    move.w  %d2, 0(%a6,%a4.l)      ; staged_bg_buffer[offset] = nametable_word

    ; Step 4: set dirty bit for staged_row
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row
    move.l  bg_row_dirty, %a5
    bset    %d2, %a5               ; set bit staged_row
    move.l  %a5, bg_row_dirty

    subq.w  #1, %d0
    bne.s   .Lbc_col_loop
```

**Note on `bset` with address register:** `bset %d2, %a5` is not a valid 68000 instruction (BSET requires a data register or memory destination). Instead, load `bg_row_dirty` into a data register, `bset` into it, and store back:

```asm
    ; Set dirty bit for staged_row (d2 = staged_row index)
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row (0–31)
    move.l  bg_row_dirty, %d2      ; can't use d2 for both — use separate registers
```

**Final register allocation for clean implementation:**

Assign registers explicitly to avoid conflicts:
- `d0` = col down-counter (D0 at entry; restored to d6 at each row start)
- `d1` = row down-counter (D1 at entry)
- `d2` = scratch (tile offset, nametable computation — clobbered per iteration)
- `d3` = start_row (constant, derived from A1 at entry)
- `d4` = start_col (constant, derived from A1 at entry)
- `d5` = genesis_attr (constant, precomputed from D2 at entry)
- `d6` = saved col count (= D0 at entry, constant)
- `d7` = row_offset counter (0 at start, incremented per outer loop)
- `a0` = source pointer (advances per inner iteration)
- `a2` = `genesistan_pc080sn_tile_vram_lut` base
- `a3` = `genesistan_pc080sn_attr_lut` base
- `a4` = scratch for offset (safe to clobber after range check and start_row/col precompute)
- `a5` = scratch for nametable_word and dirty register temp
- `a6` = `staged_bg_buffer` base

The dirty bit update must use a data register:
```asm
    move.l  bg_row_dirty, %d2      ; load dirty mask
    move.w  %d7, %a5               ; a5 = row_offset (use address reg as scratch)
    ; staged_row = start_row + row_offset
    ; to use bset, staged_row must be in d-reg, bg_row_dirty in d-reg
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row
    ; but now d2 holds staged_row, not bg_row_dirty
    ; use a5 for bg_row_dirty:
    move.l  bg_row_dirty, %a5      ; address reg trick — NOT valid for bset operand
```

Since `bset` requires a data register operand for the bit field, load `bg_row_dirty` into a data register. After the nametable write (which already consumed d2), reuse d2 for the dirty bit update:

```asm
    ; Dirty bit: staged_row = start_row (d3) + row_offset (d7)
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row (0–31)
    move.l  bg_row_dirty, %a4      ; borrow a4 for bg_row_dirty longword... also invalid for bset
    ; CORRECT: use only data registers for bset
    movem.l %d2, -(%sp)            ; save d2 (staged_row)
    move.l  bg_row_dirty, %d2      ; d2 = bg_row_dirty
    move.l  (%sp)+, %a4            ; a4 = staged_row  ← invalid: can't pop into a4 this way
```

**Simpler approach for dirty bit** — use d2 for staged_row, d2 for bg_row_dirty, by doing the bset last:

```asm
    ; After writing to staged_bg_buffer, update dirty bits.
    ; d2 is free again after nametable write.
    move.l  bg_row_dirty, %d2
    move.w  %d7, %d2               ; NO — this would overwrite bg_row_dirty
```

The cleanest solution: save staged_row to the stack temporarily, or use a different register for bg_row_dirty.

**Cody should use this exact clean pattern for the dirty bit update:**

```asm
    ; --- Dirty bit update ---
    ; Compute staged_row = start_row (d3) + row_offset (d7) into d2
    ; bset this bit in bg_row_dirty
    move.w  %d7, %d2               ; d2 = row_offset
    add.w   %d3, %d2               ; d2 = staged_row
    move.l  bg_row_dirty, %a4      ; WRONG — bset needs d-reg as bit-field dest
    ; Correct:
    move.l  bg_row_dirty, %a5      ; a5 = bg_row_dirty value (address reg used as temp storage)
    ; bset %d2, %a5 = INVALID; need d-reg destination
    ; Solution: push bg_row_dirty to stack, bset in memory:
    move.l  bg_row_dirty, %d2      ; load dirty mask — but d2 holds staged_row!
```

**Resolution:** Use a push/pop approach for ONE register to hold staged_row while d2 holds the dirty mask. Or better: use d2 for offset arithmetic (freed after memory write), then compute staged_row fresh for bset:

```asm
    ; nametable write is done; d2 is now free
    ; compute staged_row for bset
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row  (low byte, 0–31)
    ; load bg_row_dirty into a scratch data reg — we only have d0-d7
    ; d0 = col counter (still needed), d1 = row counter, d3-d7 in use, d2 = staged_row
    ; push d2, load into itself via memory bset:
    bset    %d2, bg_row_dirty      ; BSET Dn, <mem> — sets bit D2 in memory longword bg_row_dirty
```

**`bset %d2, bg_row_dirty` is valid** — 68000 BSET can target a memory location with a data register bit number. This is the correct form. No need for push/pop.

**Final clean inner loop:**

```asm
.Lbc_col_loop:
    ; Compute buffer offset for (start_row + row_offset, start_col + col_index)
    ; col_index = d6 - d0  (saved_count minus remaining; d0 not yet decremented)
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row
    lsl.w   #7, %d2                ; d2 = staged_row * 128

    move.w  %d6, %a4
    sub.w   %d0, %a4               ; a4 = col_index
    add.w   %d4, %a4               ; a4 = staged_col
    add.w   %a4, %d2               ; d2 += staged_col
    add.w   %a4, %d2               ; d2 += staged_col  (×2 for byte offset into word array)

    ; Read tile code, translate, write nametable_word
    move.w  (%a0)+, %a4            ; a4 = tile_code_word (A0 advances)
    move.w  %a4, %a4               ; a4 holds tile_code; no-op
    move.w  %a4, %d2               ; WAIT — d2 holds offset! Conflict again.
```

The fundamental conflict is that d2 is used for both the buffer offset and the tile code translation. **The correct fix is to compute the offset into a4 (address register), then use d2 freely for tile code translation:**

```asm
.Lbc_col_loop:
    ; Compute buffer offset into a4
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row
    lsl.w   #7, %d2                ; d2 = staged_row * 128

    move.w  %d6, %a4
    sub.w   %d0, %a4               ; a4 = col_index
    add.w   %d4, %a4               ; a4 = staged_col
    add.w   %a4, %d2               ; d2 += staged_col
    add.w   %a4, %d2               ; d2 += staged_col (×2)

    movea.w %d2, %a4               ; a4 = buffer byte offset (fits in 16 bits: max = 31*128+63*2 = 4086)

    ; Translate tile code to nametable_word into d2
    move.w  (%a0)+, %d2            ; d2 = tile_code_word (A0 advances)
    andi.w  #0x3FFF, %d2           ; mask attribute bits
    add.w   %d2, %d2               ; ×2 for word table
    move.w  0(%a2,%d2.w), %d2      ; d2 = vram_slot
    or.w    %d5, %d2               ; d2 = nametable_word

    ; Write to staged_bg_buffer
    move.w  %d2, 0(%a6,%a4.w)      ; staged_bg_buffer[a4] = nametable_word

    ; Set dirty bit for staged_row
    move.w  %d7, %d2
    add.w   %d3, %d2               ; d2 = staged_row
    bset    %d2, bg_row_dirty      ; set bit d2 in bg_row_dirty longword

    subq.w  #1, %d0
    bne.s   .Lbc_col_loop
```

This final version is clean: a4 holds the buffer offset (computed before A0 advances), d2 is used for tile code translation, and `bset %d2, bg_row_dirty` sets the dirty bit in memory directly.

---

## Change 4: Patch Spec — `specs/rastan_direct_remap.json`

### 4a. Add to `required_symbols`

Add `"genesistan_hook_tilemap_bg_blockcopy"` to the `required_symbols` array. Insert it immediately after `"genesistan_hook_tilemap_bg_fill"`.

### 4b. Add `opcode_replace` entry

Add the following object to the `opcode_replace` array (position does not matter; insert after the existing `0x03AD44` entry for readability):

```json
{
  "arcade_pc": "0x05A4E0",
  "original_bytes": "244932C232D85340",
  "replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_bg_blockcopy}4e75",
  "note": "Title/attract BG block copy per-cell tiles -> rastan-direct BG block copy hook symbol."
}
```

**Explanation of original_bytes:**
- `2449` = `MOVEA.L A1, A2`
- `32C2` = `MOVE.W D2, (A1)`
- `32D8` = `MOVE.W (A0)+, (A1)`
- `5340` = `SUBQ.W #1, D0`

These are the first 8 bytes of the function at `0x05A4E0`. The replacement is a 6-byte `JSR.L` + 2-byte `RTS` = 8 bytes, replacing the first 4 instructions. The hook implements the full function logic internally; the rest of the original function (at `0x05A4E8` onward) is never reached.

### 4c. Update `opcode_replace_count`

Change `"opcode_replace_count": 35` to `"opcode_replace_count": 36`.

---

## Build and Verify

```sh
source tools/setup_env.sh && make -C apps/rastan-direct
```

Expected results:
- Assembly, linking, patching, and boot guard all pass
- No symbol resolution errors for `genesistan_hook_tilemap_bg_blockcopy`
- No `original_bytes` mismatch at `0x05A4E0 + 0x0200 = 0x05A6E0` in Genesis ROM

Post-build verify: read 8 bytes at Genesis ROM offset `0x05A6E0` and confirm the JSR + RTS pattern:
```sh
python3 -c "
f=open('apps/rastan-direct/out/rastan_direct_video_test.elf','rb')
# Use symbol.txt to find the hook address, then verify patch site
f.seek(0x05A6E0)
b=f.read(8)
print('Patch site:', b.hex())
print('Expected: 4eb9 <6 addr bytes> 4e75')
"
```

Or verify via the patcher log that `0x05A6E0` was patched as expected.

---

## Summary of All Changes

| File | Change |
|------|--------|
| `apps/rastan-direct/src/main_68k.s` | `init_staging_state`: `move.l #0xFFFFFFFF, bg_row_dirty` → `clr.l bg_row_dirty` |
| `apps/rastan-direct/src/main_68k.s` | Add `.global genesistan_hook_tilemap_bg_blockcopy` declaration |
| `apps/rastan-direct/src/main_68k.s` | Add `genesistan_hook_tilemap_bg_blockcopy` function in `.text` |
| `specs/rastan_direct_remap.json` | Add `"genesistan_hook_tilemap_bg_blockcopy"` to `required_symbols` |
| `specs/rastan_direct_remap.json` | Add `opcode_replace` entry for `0x05A4E0` |
| `specs/rastan_direct_remap.json` | `opcode_replace_count`: 35 → 36 |
