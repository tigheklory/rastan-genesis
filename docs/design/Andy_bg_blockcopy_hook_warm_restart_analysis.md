# Andy — BG Block Copy Hook & Warm-Restart Architecture Analysis

## Ground Truth (inputs to this analysis)

- Plane B shows persistent checkerboard after the RTS fix confirmed in prior session
- `genesistan_hook_tilemap_bg_fill` is dead code for the Title scene: FUNC B only fires with tile_code=32 (BG clear calls), never with Title content
- Exodus trace showed 3-address tight loop cycling: `0x0003A192`, `0x0003A19C`, `0x0003A196`
- Prior diagnosis doc (Andy_bg_fill_hook_post_rts_no_change_diagnosis.md) identified block copy at `0x05A4DC` as next target — **that address was wrong; actual entry is `0x05A4E0`**

---

## Task 1 — Warm Restart Discovery

### The tight loop (Exodus trace addresses)

Genesis ROM addresses minus 0x200 = arcade PCs:
- `0x0003A192` → arcade `0x00039F92`
- `0x0003A196` → arcade `0x00039F96`
- `0x0003A19C` → arcade `0x00039F9C`

Decoded from `build/regions/maincpu.bin` at offset `0x39F90`:

```
0x39F92:  2038 0000     MOVE.L (0x0000).W, D0    ; read ROM[0x0000] into D0 (touching memory)
0x39F96:  0481 0000 0001 SUBI.L #1, D1            ; decrement D1
0x39F9C:  66F4          BNE.S 0x39F92             ; loop while D1 != 0
```

This is a pure countdown delay. D1 ≈ 0x83B69 iterations at boot. When D1 reaches zero, execution falls through to:

```
0x39F9E:  2E78 0000     MOVEA.L (0x0000).W, SP   ; SP = ROM[0x0000] = 0xFF0000
0x39FA2:  2078 0004     MOVEA.L (0x0004).W, A0   ; A0 = ROM[0x0004] = 0x00000202
0x39FA6:  4ED0          JMP (A0)                  ; JMP to 0x00000202 = main_68k
```

`rastan_direct_video_test.prepatch.bin` bytes confirmed:
- `ROM[0x0000]` = `0x00FF0000` (initial SP)
- `ROM[0x0004]` = `0x00000202` (initial PC = `main_68k`)

**The arcade code never RTEs.** Instead it performs a warm restart every game cycle: loads the Genesis ROM's initial SP and PC from the exception vectors and jumps to `main_68k`.

### Architectural consequence

Every cycle, `main_68k` runs:
```
bsr vdp_boot_setup
moveq #0, %d0
bsr load_scene_tiles
bsr init_staging_state     ← called EVERY CYCLE
bsr arcade_tick_logic
```

`init_staging_state` fills `staged_bg_buffer` with checkerboard (tiles 0x0001/0x0002) and sets `bg_row_dirty = 0xFFFFFFFF` every cycle. Any BG content written by a hook during `arcade_tick_logic` is immediately overwritten by the NEXT cycle's `init_staging_state`.

Visible consequence: the VINT within the tick phase can flush the correct BG to Plane B VRAM, but the VINT in the NEXT tick (after init_staging_state again) will flush the checkerboard over it.

---

## Task 2 — Block Copy Function Disassembly

### Caller context at `0x05A370`–`0x05A388`

```
05A370:  MOVEA.L #0x00C00320, A1   ; dest BG RAM base
05A376:  LEA 0x0005A7DA, A0        ; source ROM table (title stone tiles)
05A37C:  MOVE.W #0x001C, D0        ; cols = 28
05A380:  MOVE.W #0x0015, D1        ; rows = 21
05A384:  MOVE.W #0x0001, D2        ; attr/control = 1
05A388:  BSR.W 0x0154              ; → target 0x05A4E0  (PC_after=0x05A38C + 0x0154)
05A38C:  RTS
```

### Second caller at `0x05A38E`–`0x05A3A6`

```
05A38E:  MOVEA.L #0x00C00328, A1   ; dest BG RAM base (offset +8)
05A394:  LEA 0x0005B0B2, A0        ; source ROM table (title logo tiles)
05A39A:  MOVE.W #0x001C, D0        ; cols = 28
05A39E:  MOVE.W #0x0014, D1        ; rows = 20
05A3A2:  MOVE.W #0x0001, D2        ; attr/control = 1
05A3A6:  BSR.W 0x0136              ; → target 0x05A4E0  (PC_after=0x05A3AA + 0x0136)
05A3AA:  RTS
```

**Both BSRs target `0x05A4E0`.** Prior Andy doc's reference to `0x05A4DC` was wrong — the actual function entry is `0x05A4E0`. The 4 bytes at `0x05A4DC`–`0x05A4DF` are `4E 75 38 00` (RTS + padding/data from previous function).

### Function disassembly at `0x05A4E0`

```
05A4E0:  2449          MOVEA.L A1, A2            ; A2 = row base (one-time init)

; ← outer loop (row) enters here:
05A4E2:  32C2          MOVE.W D2, (A1)           ; write attr/control byte to PC080SN port
05A4E4:  32D8          MOVE.W (A0)+, (A1)        ; write tile_code_word from source to port; A0 advances
05A4E6:  5340          SUBQ.W #1, D0             ; D0-- (column counter)
05A4E8:  0C400000      CMPI.W #0, D0
05A4EC:  66F4          BNE.S 0x05A4E2            ; inner col loop

05A4EE:  D5FC00000100  ADDA.L #0x100, A2         ; A2 += 256 (next row in BG RAM)
05A4F4:  224A          MOVEA.L A2, A1            ; A1 = new row base
05A4F6:  3004          MOVE.W D4, D0             ; D0 = D4 (col count from calling context)
05A4F8:  5341          SUBQ.W #1, D1             ; D1-- (row counter)
05A4FA:  0C410000      CMPI.W #0, D1
05A4FE:  66E2          BNE.S 0x05A4E2            ; outer row loop (back to col init)
05A500:  4E75          RTS
```

**Register contract at entry:**
- `A0` = source ROM table pointer (word array of tile codes)
- `A1` = destination BG RAM base address (e.g., `0xC00320`)
- `D0` = columns per row (e.g., 28)
- `D1` = rows (e.g., 21)
- `D2` = attribute word / control value (1 in both known callers)
- `D4` = column count (must equal D0; set by calling context, not this function)

The hook replaces this entire function. It uses D0 directly and does not need D4.

### How A1 maps to staged_bg_buffer position

The `FUNC B` hook maps a longword write at byte_offset from 0xC00000 using:
```
longword_index = byte_offset >> 2
col = longword_index & 0x3F           (0–63)
row = (longword_index >> 6) & 0x1F   (0–31)
staged_bg_buffer[row*128 + col*2] = nametable_word
```

Row stride: 64 longwords × 4 bytes = 256 bytes = 0x100 ← **matches `ADDA.L #0x100, A2`**

Each PC080SN cell is one longword (4 bytes): 2 writes to the PC080SN port (D2=attr + source=tile_code). The block copy hook should use this same mapping, computing start_row and start_col from A1's initial byte offset, then iterating with explicit row/col counters.

**Example — first call (A1=0xC00320):**
- byte_off = 0x320 = 800
- longword_off = 800 / 4 = 200
- start_col = 200 & 63 = 8
- start_row = (200 >> 6) & 31 = 3

**Example — second call (A1=0xC00328):**
- byte_off = 0x328 = 808
- longword_off = 808 / 4 = 202
- start_col = 202 & 63 = 10
- start_row = (202 >> 6) & 31 = 3

Both calls land in row 3 with slightly different column starts. They represent the two PC080SN BG planes (stone background layer and logo overlay layer). On Genesis both are merged into Plane B; the second call partially overwrites the first for overlapping columns, which is the intended display compositing.

---

## Task 3 — init_staging_state Fix Required

`init_staging_state` line 700:
```asm
move.l  #0xFFFFFFFF, bg_row_dirty
```

This marks all 32 rows dirty every cycle. The next VINT flushes the entire checkerboard `staged_bg_buffer` to Plane B VRAM, overwriting any block copy hook writes from the previous cycle.

**Fix:** Change to `clr.l bg_row_dirty` (= `move.l #0x00000000, bg_row_dirty`).

Effect: after init_staging_state, no rows are dirty. Only rows written by hooks (`genesistan_hook_tilemap_bg_fill`, `genesistan_hook_tilemap_bg_blockcopy`) in the current tick will have dirty bits set. VINT flushes only those rows. Rows not written this tick retain their previous VRAM content from the last time they were flushed.

This is the correct behavior: the Title BG block copy hook writes rows 3–23 (for 21-row title), marks them dirty, VINT flushes them to VRAM, and the warm-restart init_staging_state does NOT re-dirty those rows in the next cycle (since no block copy fires in the attract loop's non-Title frames). Plane B VRAM holds the Title BG stably.

---

## Task 4 — Attribute Derivation for Block Copy

For `genesistan_hook_tilemap_bg_fill`, the attr word comes from D0[31:16]. The block copy equivalent is D2 (the constant attr/control value written to the PC080SN port before each cell). Both known callers pass D2=1.

The attr LUT index is computed the same way as in the bg_fill hook:
- palette bits [1:0] = D2[1:0]
- hflip = D2[14]
- vflip = D2[15]
- priority = D2[13]

D2=1 → palette=1, hflip=0, vflip=0, priority=0 → attr_index=1 → genesis_attr = genesistan_pc080sn_attr_lut[1*2].

Precompute genesis_attr from D2 once before the cell loop, using the same two-shift extraction code as the bg_fill hook but sourced from D2 instead of D0[31:16].

---

## Task 5 — Complete Fix Summary

### Change 1: `init_staging_state` in `apps/rastan-direct/src/main_68k.s`

Line 700: `move.l  #0xFFFFFFFF, bg_row_dirty`  
→ `clr.l   bg_row_dirty`

### Change 2: New symbol and hook function in `apps/rastan-direct/src/main_68k.s`

- `.global genesistan_hook_tilemap_bg_blockcopy` (after `.global genesistan_hook_tilemap_bg_fill`)
- New function `genesistan_hook_tilemap_bg_blockcopy` placed in `.text` after `genesistan_hook_tilemap_bg_fill`

Register contract at hook entry:
- A0 = source ROM table pointer
- A1 = destination BG RAM base (e.g., 0xC00320)
- D0 = cols per row
- D1 = rows
- D2 = attr word

Hook behavior:
1. `movem.l` save all registers
2. Mask A1 to 24 bits, range-check A1 ∈ [0xC00000, 0xC04000); if out of range, restore and RTS
3. Precompute genesis_attr from D2 using two-shift extraction (same as bg_fill hook, sourced from D2 not D0[31:16])
4. Compute start_col and start_row from A1's initial byte offset:
   - `byte_off = (A1_masked − 0xC00000)`
   - `longword_off = byte_off >> 2`
   - `start_col = longword_off & 0x3F`
   - `start_row = (longword_off >> 6) & 0x1F`
5. Save D0 (col count) as inner loop counter; D1 is outer loop counter
6. Outer row loop (D1 times):
   - Inner col loop (D0 times):
     - Read `tile_code_word` from `(A0)+`
     - `code = tile_code_word & 0x3FFF`
     - `vram_slot = genesistan_pc080sn_tile_vram_lut[code * 2]`
     - `nametable_word = vram_slot | genesis_attr`
     - Compute `offset = (start_row + row_counter) * 128 + (start_col + col_counter) * 2`
     - Write `nametable_word` to `staged_bg_buffer + offset`
     - `bset (start_row + row_counter), bg_row_dirty`
   - Increment row_counter, decrement D1
7. `movem.l` restore, `rts`

### Change 3: `specs/rastan_direct_remap.json`

- Add `genesistan_hook_tilemap_bg_blockcopy` to `required_symbols`
- Add `opcode_replace` entry:
  - `arcade_pc`: `"0x05A4E0"` ← correct address (NOT `0x05A4DC`)
  - `original_bytes`: `"244932C232D85340"` (first 8 bytes of function: MOVEA.L A1,A2; MOVE.W D2,(A1); MOVE.W (A0)+,(A1); SUBQ.W #1,D0)
  - `replacement_bytes`: `"4eb9{symbol:genesistan_hook_tilemap_bg_blockcopy}4e75"`
  - `note`: "Title/attract BG block copy -> rastan-direct BG block copy hook symbol."
- Update `opcode_replace_count` from 35 to 36

---

## Task 6 — Expected Outcome

After both changes:

1. `init_staging_state` no longer pre-dirtying all rows → warm restart does not re-flush checkerboard
2. During Title scene: arcade calls `0x05A4E0` → hook intercepts → writes Title stone + logo tiles to `staged_bg_buffer` rows 3–23, marks them dirty → VINT flushes those rows to Plane B VRAM → Title BG visible
3. In subsequent cycles (attract loop): arcade does not call `0x05A4E0` → no rows dirtied → VINT flushes nothing → Plane B VRAM retains Title BG from last flush ← correct stable display
4. When scene changes: `genesistan_hook_tilemap_plane_a` fires, `load_scene_tiles` loads new tile data, and the next block copy call (for whatever scene) updates the appropriate `staged_bg_buffer` rows

The checkerboard in `staged_bg_buffer` post-init is no longer flushed to VRAM because `bg_row_dirty=0`. Plane B VRAM shows Title BG until explicitly overwritten.
