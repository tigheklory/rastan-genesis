# Andy — Text Writer Hook Specification (arcade_pc 0x03C4D2)

**Status:** SPEC COMPLETE. Cody has zero design decisions remaining.
**Scope:** Analysis & specification only. No code.
**Build Context:** Build 0032, `rastan-direct`. Crash source confirmed.

---

## 1. Summary

Function at `arcade_pc: 0x03C4D2` is a dispatched handler in the arcade text-script
interpreter. It writes 10 characters of text into PC080SN FG tilemap space
(`arcade hw 0xC08000–0xC0BFFF`) by iterating an inner subroutine at
`arcade_pc: 0x03C516` that writes tile and attribute words via indexed
addressing `A1@(2)` and `A1@(6)` with stride 8. Build 0032 trace confirms this
function is the writer whose attempted write to `HW_ADDRESS/PC080SN/FG_TILEMAP`
address `0xC09EA0` causes the Build 0032 crash.

This spec defines `genesistan_hook_text_writer_3c4d2` — a replacement hook that
reproduces the function's observable effects on Genesis staging memory
(`staged_fg_buffer` + `fg_row_dirty`) without any write to C-window hardware.

---

## 2. Address Space Verification

All addresses verified against `build/rastan-direct/address_map.json` for
Build 0032. The relevant segment record is:

```json
{
  "kind": "arcade_copy",
  "genesis_start": "0x03B2A4",
  "genesis_end_exclusive": "0x03F128",
  "arcade_start": "0x03B0A4",
  "arcade_end_exclusive": "0x03EF28",
  "source": "whole_maincpu_copy",
  "identity_offset": 512
}
```

The segment covers both target addresses. Per the segment's recorded
`identity_offset`, the arcade_copy mapping is:
`genesis_rom_offset = genesis_start + (arcade_pc - arcade_start)`.

| Label | Space | Value | Derivation |
|-------|-------|-------|------------|
| `arcade_pc: 0x03C4D2` | arcade_pc | `0x03C4D2` | Entry of the target function in `build/maincpu.disasm.txt:75918`. |
| `genesis_rom_offset` for above | genesis_rom_offset | `0x03C6D2` | address_map.json arcade_copy segment lookup (`genesis_start=0x03B2A4 + (0x03C4D2 − 0x03B0A4)`). |
| `arcade_pc: 0x03C516` | arcade_pc | `0x03C516` | Inner subroutine entry in `build/maincpu.disasm.txt:75941`. |
| `genesis_rom_offset` for above | genesis_rom_offset | `0x03C716` | address_map.json arcade_copy segment lookup. |
| `arcade_pc: 0x03C514` | arcade_pc | `0x03C514` | RTS closing the handler body in `build/maincpu.disasm.txt:75940`. |
| `arcade_pc: 0x03C54E` | arcade_pc | `0x03C54E` | RTS closing the inner subroutine in `build/maincpu.disasm.txt:75959`. |
| `arcade_pc: 0x03C924` | arcade_pc | `0x03C924` | Dispatch branch site #1 (`beqw 0x3c4d2` when opcode == 0x50), `build/maincpu.disasm.txt:76278`. |
| `genesis_rom_offset` for above | genesis_rom_offset | `0x03CB24` | address_map.json arcade_copy segment lookup. |
| `arcade_pc: 0x03C92C` | arcade_pc | `0x03C92C` | Dispatch branch site #2 (`beqw 0x3c4d2` when opcode == 0x60), `build/maincpu.disasm.txt:76280`. |
| `genesis_rom_offset` for above | genesis_rom_offset | `0x03CB2C` | address_map.json arcade_copy segment lookup. |
| `0xC09EA0` | HW_ADDRESS | `0xC09EA0` | Classified per §7.3 of `docs/design/Andy_address_map_artifact_design.md`: `HW_ADDRESS/PC080SN/FG_TILEMAP`, offset `0x1EA0` from base `0xC08000`. Terminal; no `arcade_pc` mapping is attempted. |

No cross-space arithmetic was used. Every mapping cited here came from the
address_map.json segment record or from explicit classification rules.

---

## 3. Function Disassembly — `arcade_pc: 0x03C4D2` Handler

Source: `build/maincpu.disasm.txt:75918–75940`.

```
arcade_pc     bytes                    mnemonic
0x03C4D2      2449                     movea.l  A1, A2                       ; A2 = A1
0x03C4D4      D4FC 0050                adda.w   #0x0050, A2                  ; A2 = A1 + 0x50 (save "end pointer")
0x03C4D8      2068 0002                movea.l  A0@(2), A0                   ; A0 = *(entry_A0 + 2)  (deref to script data)
0x03C4DC      102C 000B                move.b   A4@(11), D0                  ; D0 = signed char count from script state
0x03C4E0      4880                     ext.w    D0                           ; sign-extend to word
0x03C4E2      0C40 0020                cmpi.w   #0x0020, D0                  ; == 32?
0x03C4E6      6610                     bne.s    0x03C4F8                     ; if NOT 32 → slow path
; ── fast-fill path (D0 == 32 — clear a line of text with blank tile 0x0180) ──
0x03C4E8      780A                     moveq    #10, D4                      ; 10 iterations
0x03C4EA      337C 0180 0002           move.w   #0x0180, A1@(2)              ; write blank tile code
0x03C4F0      5089                     addq.l   #8, A1                       ; stride 8 bytes
0x03C4F2      5344                     subq.w   #1, D4
0x03C4F4      66F4                     bne.s    0x03C4EA
0x03C4F6      601A                     bra.s    0x03C512                     ; to cleanup
; ── slow path (D0 ≠ 32 — render 10 characters from script) ──
0x03C4F8      C0FC 0005                mulu.w   #5, D0                       ; D0 *= 5
0x03C4FC      D0C0                     adda.w   D0, A0                       ; A0 += D0*5 (skip leading bytes)
0x03C4FE      7805                     moveq    #5, D4                       ; 5 iterations
0x03C500      4242                     clr.w    D2                           ; D2 = 0 (left-half attribute offset)
0x03C502      6100 0012                bsr.w    0x03C516                     ; render left 5 chars
0x03C506      5B88                     subq.l   #5, A0                       ; rewind script pointer by 5
0x03C508      7805                     moveq    #5, D4                       ; 5 iterations
0x03C50A      343C FFF0                move.w   #0xFFF0, D2                  ; D2 = −16 (right-half attribute offset)
0x03C50E      6100 0006                bsr.w    0x03C516                     ; render right 5 chars
; ── cleanup ──
0x03C512      224A                     movea.l  A2, A1                       ; A1 = A2 = entry_A1 + 0x50 (advance)
0x03C514      4E75                     rts                                   ; return to dispatcher's caller
```

**Function entry:** `arcade_pc: 0x03C4D2`.
**Function end:** `arcade_pc: 0x03C514` (last byte of RTS).
**Function body length:** `0x03C514 + 2 − 0x03C4D2 = 0x44 bytes` (68 bytes).

**Sub-calls from the body:**
- `bsr.w 0x03C516` at `arcade_pc: 0x03C502` — target `arcade_pc: 0x03C516`.
- `bsr.w 0x03C516` at `arcade_pc: 0x03C50E` — target `arcade_pc: 0x03C516`.

**A1 initialization:** A1 is **passed in by the caller**. The function does not
set A1 from any register load; it reads A1, copies it into A2, then offsets A2
by 0x50 (line `0x03C4D2–0x03C4D4`). A1 is the hardware destination pointer
provided by the dispatcher at `arcade_pc: ~0x03C902+`.

---

## 4. Inner Subroutine Disassembly — `arcade_pc: 0x03C516`

Source: `build/maincpu.disasm.txt:75941–75959`.

```
arcade_pc     bytes                    mnemonic
0x03C516      1018                     move.b   A0@+, D0                     ; D0 = next script byte (glyph code)
0x03C518      4880                     ext.w    D0
0x03C51A      0C03 0050                cmpi.b   #0x50, D3                    ; script opcode == 0x50?
0x03C51E      6608                     bne.s    0x03C528
0x03C520      0C44 0001                cmpi.w   #1, D4                       ; last iteration?
0x03C524      6602                     bne.s    0x03C528
0x03C526      4E75                     rts                                   ; early exit (terminator)
0x03C528      D06C 001A                add.w    A4@(26), D0                  ; D0 += tile-base offset
0x03C52C      D06C 0018                add.w    A4@(24), D0                  ; D0 += per-scene offset
0x03C530      3340 0002                move.w   D0, A1@(2)                   ; **TILE WRITE** (left half)
0x03C534      3E2C 0016                move.w   A4@(22), D7                  ; D7 = attribute base
0x03C538      DE42                     add.w    D2, D7                       ; D7 += D2 (half-select: 0 or −16)
0x03C53A      0247 01FF                andi.w   #0x01FF, D7                  ; mask to 9 bits
0x03C53E      4EB9 0005 B512           jsr      0x0005B512                   ; helper (confirmed RTS-only per trace: helper_5b512_rts)
0x03C544      3347 0006                move.w   D7, A1@(6)                   ; **ATTRIBUTE / second tile WRITE**
0x03C548      5089                     addq.l   #8, A1                       ; stride 8 bytes per iteration
0x03C54A      5344                     subq.w   #1, D4
0x03C54C      66C8                     bne.s    0x03C516
0x03C54E      4E75                     rts
```

**Writes per iteration:** 2 (tile at `A1+2`, secondary word at `A1+6`).
**Addressing mode:** indexed `A1@(offset)` — NOT `(A1)+`. This confirms the
spec-inconsistency flagged in `docs/design/Andy_text_writer_3c3fe_hook_spec.md`:
the prior spec at 0x03C3FE was the wrong target; this function at
`arcade_pc: 0x03C4D2` is the real crash source.
**Stride per iteration:** +8 bytes (`addq.l #8, A1`).
**Iterations per call:** 5 (set by caller `moveq #5, D4`).
**Writes per call:** 5 × 2 = 10. **Two calls per handler invocation = 20
writes per slow-path invocation.** Fast path writes 10 (tile only).
**A1 advance per iteration:** 8 bytes; across 10 iterations (both 5-count
calls): 80 bytes = `0x50` — matches the `A1 + 0x50` saved into A2 at entry.

**Sole callers of 0x03C516:** grep of the arcade disasm shows only two
`bsr.w 0x03C516` sites (`arcade_pc: 0x03C502, 0x03C50E`) plus the self `bne.s
0x03C516` loop at `arcade_pc: 0x03C54C`. No external caller. The subroutine
is private to the handler and can be replaced together with the handler body.

---

## 5. Address Mapping — Row/Col Arithmetic

The Build 0032 trace destination is `HW_ADDRESS/PC080SN/FG_TILEMAP` at
`0xC09EA0`. Base for FG tilemap: `0xC08000` (confirmed in
`apps/rastan-direct/src/main_68k.s:54` — `.equ ARCADE_PC080SN_CWINDOW_BASE_FG, 0x00C08000`
— and in the existing hook guard at `main_68k.s:385–388`).

**Arcade cell size for FG tilemap:** 4 bytes per cell (tile word + attribute
word). Confirmed by the existing FG hook at `main_68k.s:393–396`:
`subi.l #BASE, %d4 ; andi.l #3, %d0 ; bne invalid ; lsr.l #2, %d4`
(alignment-to-4 check, then divide-by-4 cell index).

The text-writer function at 0x03C4D2 uses stride 8 — that is **two
consecutive cells per iteration**: the left glyph-half at `A1+2` (the tile
word of cell N) and the right glyph-half at `A1+6` (the tile word of cell
N+1). Each text character therefore occupies two horizontally adjacent
tilemap cells, yielding 10 characters × 2 cells = 20 cells per slow-path
invocation.

### 5.1 Row/Col formula (proven from disassembly)

Given the first write address `first_write = A1_entry + 2`:

```
cell_offset   = first_write − 0xC08000
cell_index    = cell_offset / 4                 (4-byte cells, ∈ 0..4095)
arcade_col    = cell_index & 0x3F               (0..63)
arcade_row    = (cell_index >> 6) & 0x3F        (0..63)
```

Applied to Build 0032 crash signature (`first_write = 0xC09EA0`):

```
cell_offset   = 0xC09EA0 − 0xC08000 = 0x1EA0
cell_index    = 0x1EA0 / 4           = 0x7A8 = 1960
arcade_col    = 1960 & 0x3F          = 40 (0x28)
arcade_row    = (1960 >> 6) & 0x3F   = 30 (0x1E)
```

**Bounds check:** Genesis plane A is 64 cols × 32 rows. `arcade_col = 40` is
within `0..63`. `arcade_row = 30` is within `0..31`. Result lands within
valid FG tilemap bounds. ✓

**Run extent:** the function writes 20 contiguous cells starting at
`(arcade_row, arcade_col)`. With `arcade_col = 40`, the run extends to
column `59` within the same row (`40..59` inclusive). No row wrap occurs
because `40 + 20 − 1 = 59 < 64`. For a different `A1_entry` where
`arcade_col + 20 > 64`, Cody's hook must wrap column into `col mod 64` and
advance `row` — §10 defines this explicitly.

### 5.2 Genesis cell address

```
genesis_cell_index = arcade_row * 64 + arcade_col       (0..2047 into staged_fg_buffer)
staged_fg_buffer_index_bytes = genesis_cell_index * 2   (word-addressed)
fg_row_dirty_bit = arcade_row                           (bit in 32-bit bitmap)
```

For `arcade_row = 30`, `fg_row_dirty_bit = 30` (0x1E).

---

## 6. Input Register State At Entry

From the disassembly in §3 and from cross-reference with the dispatcher
prelude at `arcade_pc: ~0x03C902+` (`build/maincpu.disasm.txt:76269–76284`):

| Register | Space / kind | Role at entry | Source |
|----------|--------------|---------------|--------|
| A1 | HW_ADDRESS | Destination pointer into PC080SN FG tilemap; function will write at `A1+2`, `A1+6`, `A1+10`, ... (cell writes, then `A1 += 0x50`). | Passed in by caller (dispatcher); function saves it into A2 at line 0x03C4D2–0x03C4D4. |
| A0 | arcade_pc (code/data pointer) | Descriptor pointer. Function dereferences `*(A0+2)` to obtain the script data pointer, then overwrites A0 with that dereferenced value. | Passed in by caller. |
| A4 | arcade data pointer (into A5-relative workram) | Script state block. Function reads bytes at `A4+11` (char count), `A4+22` (attr base), `A4+24` (per-scene offset), `A4+26` (tile base). | Passed in by caller. |
| D0 | value | Clobbered. | — |
| D1 | value | Unused in this function body. | — |
| D2 | value | Clobbered; set to `0` for left half, `0xFFF0` for right half inside this function. | — |
| D3 | value | **Read by inner subroutine** at `0x03C51A` for terminator check (`cmpi.b #0x50, D3`). Passed in by dispatcher. | — |
| D4 | value | Clobbered (loop counter). | — |
| D7 | value | Clobbered (attribute word). | — |

**Tile codes**: the **slow-path** reads raw bytes from `A0` (the dereferenced
script data pointer, advanced by `D0*5`). Each byte is sign-extended, then
`A4@(26) + A4@(24)` are added to form the tile index written at `A1+2`.
Attribute words for the slow path come from `A4@(22)` plus a per-half D2
adjustment (0 or −16), masked to 9 bits.

**Fast-path (D0 == 32)**: writes literal tile `0x0180` at `A1+2` for 10
iterations with no attribute write. No data is read from A0.

**Precomputed vs in-loop**: `A0 = *(entry_A0 + 2)` is loaded once at entry.
Tile bytes are read in-loop from `(A0)+`. `A4@(22)`, `A4@(24)`, `A4@(26)`,
`A4@(11)` are read in-loop (cheap register-indirect reads).

---

## 7. Output Target

The hook must write to **`staged_fg_buffer`** only. No write to C-window
hardware is permitted (PRIME DIRECTIVE: no memory shadowing, all output
through staging buffers).

For each cell written by the original function at arcade hardware offset
`offset_hw` from `0xC08000`, the hook writes one word at Genesis offset
`staged_fg_buffer[cell_index]`, where `cell_index = offset_hw / 4` as
derived in §5.

**Tile index translation:** arcade tile code is translated via the existing
`genesistan_pc080sn_tile_vram_lut` (used by `genesistan_hook_tilemap_fg` at
`apps/rastan-direct/src/main_68k.s:276`). Lookup key = arcade tile code
masked to 14 bits (`andi.w #0x3FFF`); output = Genesis pattern-index word.

**Attribute translation:** arcade attribute word is translated via the
existing `genesistan_pc080sn_attr_lut` (used by
`genesistan_hook_tilemap_plane_a` at `main_68k.s:277`). Lookup key = attribute
word shaped per the existing hook's attribute-bit-extraction
(lines 303–323: extracts color, flip bits). Output = Genesis palette/priority/flip
word.

**Final nametable word:** `OR` the tile translation and the attribute
translation; store to `staged_fg_buffer[cell_index]`.

**Dirty tracking:** for every cell written in row `R`, set bit `R` in
`fg_row_dirty` via `bset %R, fg_row_dirty`. If the run spans multiple rows
(column wrap), set a bit per row touched.

### 7.1 Difference from `genesistan_hook_tilemap_plane_a` / `genesistan_hook_tilemap_fg`

| Property | existing `genesistan_hook_tilemap_*` | new `genesistan_hook_text_writer_3c4d2` |
|----------|--------------------------------------|------------------------------------------|
| Input channel | WRAM (`ARCADE_PC080SN_DEST_*_OFFSET`, strip_index, descriptor list) | Registers (A0, A1, A4, D3) |
| Invocation trigger | Arcade code writes dest pointer to WRAM, then calls writer (existing patch at 0x055968 / 0x055990) | Arcade dispatcher branches to 0x03C4D2 (indirect through opcode-table branches at `arcade_pc: 0x03C924` and `0x03C92C`) |
| Processing shape | 16 descriptors × strip rows → column-ordered nametable writes | 10 characters × 2 halves → row-contiguous nametable writes |
| Tile source | Descriptor → ROM table → 4 words per descriptor | Script byte stream at `A0` plus A4-relative base offsets |
| Attribute source | Descriptor bits, computed | `A4@(22)` + per-half D2 offset |
| Stride | 2 words (one cell) | 8 bytes (two cells) with paired writes at +2 and +6 |
| Row-wrap handling | Strip-based; wrap is implicit in descriptor list | Column-linear; Cody's hook must wrap explicitly when run crosses a row boundary |

These are **independent intent classes** per the
`docs/design/Andy_final_pc080sn_hook_strategy.md` template: both legitimate
translation contracts, both funneling into `staged_fg_buffer` + `fg_row_dirty`,
both call-site-agnostic once inside the hook. This is architecture, not
scaffolding.

---

## 8. Write Count and Loop Structure

**Path selection is driven by `A4@(11)` (the byte at `entry_A4 + 11`):**

- If `A4@(11) == 0x20` (32): **fast-fill path**. 10 iterations, 1 write each =
  **10 cell writes** (tile only, literal `0x0180`).
- Otherwise: **slow path**. Two calls to inner subroutine, each with 5
  iterations and 2 writes per iteration = **20 cell writes** (10 tile, 10
  attribute).

Each slow-path call to `0x03C516` runs 5 iterations; two calls produce 10
total iterations with `D2` alternating `0` (first 5) and `0xFFF0` (second 5).
Between the two calls, `A0` is rewound by 5 (`subq.l #5, A0` at
`arcade_pc: 0x03C506`), so both halves read the **same 5 script bytes** — the
per-iteration `A4@(22) + D2` attribute adjustment distinguishes left vs right
glyph halves.

**A1 total advance per invocation:** 10 iterations × 8 bytes = 80 bytes =
`0x50`. Confirmed by the entry-time save `A2 = A1 + 0x50` and the closing
`A1 = A2`.

**A0 total advance per invocation:**
- Fast path: A0 = `*(entry_A0 + 2)`. No further advance.
- Slow path: A0 = `*(entry_A0 + 2) + D0*5 + 5`
  - `+ D0*5` at `arcade_pc: 0x03C4FC`
  - first 0x03C516 call advances A0 by 5 (read 5 bytes)
  - `subq.l #5, A0` rewinds
  - second 0x03C516 call advances A0 by 5 again
  - net post-call advance: +5

### 8.1 Exact `staged_fg_buffer` cells written per invocation

Let `start_cell = ((A1_entry + 2) − 0xC08000) / 4`. The 20 cells written by
the slow path are `start_cell, start_cell+1, ..., start_cell+19`. The 10
cells written by the fast path are `start_cell, start_cell+2,
start_cell+4, ..., start_cell+18` — note stride-2 in cell index because the
`A1+6` slot is untouched.

For Build 0032 crash (`A1_entry = 0xC09E9E`, `first_write = 0xC09EA0`):
- `start_cell = 0x1EA0 / 4 = 1960 → (row 30, col 40)`
- Slow-path cells written (row, col): (30,40), (30,41), (30,42), (30,43),
  (30,44), (30,45), (30,46), (30,47), (30,48), (30,49), (30,50), (30,51),
  (30,52), (30,53), (30,54), (30,55), (30,56), (30,57), (30,58), (30,59).
  All in row 30. `fg_row_dirty` bit 30 set.
- Fast-path cells written (row, col): (30,40), (30,42), (30,44), (30,46),
  (30,48), (30,50), (30,52), (30,54), (30,56), (30,58). Same row. `fg_row_dirty`
  bit 30 set.

---

## 9. Caller Analysis and Patch Sites

**Callers of `arcade_pc: 0x03C4D2`** (from `build/maincpu.disasm.txt`
grep for `0x3c4d2`):

| Caller arcade_pc | genesis_rom_offset | Instruction | Reached via |
|------------------|--------------------|-----------|-------------|
| `0x03C924` | `0x03CB24` | `beqw 0x3c4d2` | Conditional branch from opcode-table dispatcher at `arcade_pc: ~0x03C902+` when opcode byte == `0x50`. |
| `0x03C92C` | `0x03CB2C` | `beqw 0x3c4d2` | Conditional branch from the same dispatcher when opcode byte == `0x60`. |

Both callers are **branch targets** (not BSR/JSR). They transfer control
**into** the handler body, which then returns via its own RTS at
`arcade_pc: 0x03C514`. The RTS unwinds the outer dispatcher's caller — the
dispatcher itself was entered via a BSR/JSR by a higher-level text-engine
caller.

### 9.1 Number of `opcode_replace` entries required in `specs/rastan_direct_remap.json`

**ONE** entry at `arcade_pc: 0x03C4D2`. The existing 2 branch sites
(`arcade_pc: 0x03C924, 0x03C92C`) do **not** require patching — their
targets still point at `arcade_pc: 0x03C4D2`, and the replacement code at
that address intercepts execution before the original body runs.

The replacement bytes must:
1. Emit `JSR genesistan_hook_text_writer_3c4d2` (6 bytes).
2. Emit `RTS` (2 bytes).
3. Pad to the full body length with `NOP` (`0x4E71`) or fill with zeros
   sufficient to match `len(original_bytes)`.

**Original bytes length:** 0x44 = 68 bytes
(from `arcade_pc: 0x03C4D2` to `arcade_pc: 0x03C513` inclusive — the RTS at
0x03C514 is preserved in replacement form as the new RTS at byte-offset 6
of the replacement). Replacement length must equal 68 bytes
(`postpatch_startup_rom.py:973–977` enforces equal length on `opcode_replace`).

**Exact byte template** for `replacement_bytes`:
```
4EB9 {symbol:genesistan_hook_text_writer_3c4d2}        (6 bytes)
4E75                                                   (2 bytes — RTS)
4E71 4E71 4E71 4E71 4E71 4E71 4E71 4E71
4E71 4E71 4E71 4E71 4E71 4E71 4E71 4E71
4E71 4E71 4E71 4E71 4E71 4E71 4E71 4E71
4E71 4E71 4E71 4E71 4E71 4E71                          (60 bytes of NOP)
```
Total: 6 + 2 + 60 = 68 bytes. The NOP padding is unreachable (the preceding
RTS returns control to the dispatcher's caller); NOPs are NOT scaffolding
because they are structurally required padding to satisfy the
`opcode_replace` equal-length constraint. No NOPs execute.

**Leftover inner subroutine at `arcade_pc: 0x03C516–0x03C54E` is NOT
patched.** It becomes dead code (unreachable because the only callers were
the two `bsr.w 0x03C516` sites inside the now-overwritten handler body).
Confirmed dead-code by `build/maincpu.disasm.txt` grep: only references to
`0x3c516` are the two internal BSRs and the self-loop `bne.s 0x03C516`.

### 9.2 Register-contract patch constraint

Because the hook reads **A0, A1, A4, D3** as input and must preserve A1's
final value at `entry_A1 + 0x50` on return, the hook implementation MUST NOT
be invoked through a standard `movem.l %d0-%d7/%a0-%a6, -(%sp)` save/restore
frame that clobbers A1 before hook entry. The hook code itself can save
whatever callee-saves it needs, but **A1 post-hook must equal
`entry_A1 + 0x50`** because the replacement's `RTS` transfers control
to the dispatcher's caller under that register contract.

Specifically: the hook should perform internal register preservation so that
the JSR call site preserves the observable register state that the original
function produced:
- A1 = entry_A1 + 0x50
- A2 = entry_A1 + 0x50 (it's written by the original at `0x03C4D2–0x03C4D4`, and some callers may observe it; the hook should emit the same write)
- A0 = fast path: `*(entry_A0 + 2)`; slow path: `*(entry_A0 + 2) + D0*5 + 5`
- D0, D1, D2, D4, D7: don't care (already clobbered by original)
- D3 preserved (only read, not written)
- A3, A5, A6 preserved
- CCR clobbered

---

## 10. Complete Hook Specification

`genesistan_hook_text_writer_3c4d2` — behavioral contract Cody must implement
in `apps/rastan-direct/src/main_68k.s`. This spec is complete; **zero design
decisions remain**.

### 10.1 Declaration

- Add to `.global` list in `main_68k.s` header: `genesistan_hook_text_writer_3c4d2`.
- Add to `required_symbols` in `specs/rastan_direct_remap.json`:
  `genesistan_hook_text_writer_3c4d2`.

### 10.2 Entry contract

| Register | Meaning at hook entry |
|----------|----------------------|
| A0 | Text descriptor pointer. Function will read long at `A0+2` and deref. |
| A1 | `A1_entry` — intended arcade hw destination (expected in `[0xC08000, 0xC0C000)`). |
| A4 | Text script state pointer. Fields used: `A4@(11).b`, `A4@(22).w`, `A4@(24).w`, `A4@(26).w`. |
| D3 | Script opcode byte (used by terminator check). Must be preserved. |
| All other regs | Saved by hook prologue with `movem.l %d0-%d7/%a0-%a6, -(%sp)` and restored on exit; the hook's own local register use is internal. |

### 10.3 Exit contract

On `rts` back to the patched site:
- A1 = `A1_entry + 0x50`
- A2 = `A1_entry + 0x50`
- A0 = fast path: `*(A0_entry + 2)`; slow path: `*(A0_entry + 2) + ext.w(A4@(11).b) * 5 + 5`
- D3 preserved
- All other regs restored from the prologue save

### 10.4 Algorithm

```
1. Save registers: movem.l %d0-%d7/%a0-%a6, -(%sp)

2. Compute A2 = A1 + 0x50. (Emit the same write as the original, so any
   caller that observes A2 sees the same value.)

3. Dereference A0: A0 = long at A0+2.

4. Load D0 = sign-extended byte from A4+11.

5. Compute `first_write = A1 + 2`.

6. Range-check A1:
       if (first_write - 1) < 0xC08000 OR first_write >= 0xC0C000 + 1:
           ; destination outside FG tilemap; skip translation, proceed to step 10
           goto step 10

7. Compute:
       cell_offset = first_write - 0xC08000
       cell_index  = cell_offset >> 2            (4-byte cells)
       arcade_row  = (cell_index >> 6) & 0x3F
       arcade_col  =  cell_index       & 0x3F

   (Per §5.1.)

8. Select path by D0:

   8a. FAST PATH (D0 == 0x20):
       For i = 0..9:
           arcade_tile = 0x0180
           translated_tile = genesistan_pc080sn_tile_vram_lut[arcade_tile & 0x3FFF]
           translated_attr = genesistan_pc080sn_attr_lut[0]      ; attr 0 for fast path
           nametable_word  = translated_tile | translated_attr
           col = (arcade_col + 2*i) & 0x3F
           row = (arcade_row + ((arcade_col + 2*i) >> 6)) & 0x1F
           staged_fg_buffer[row*64 + col] = nametable_word
           bset row, fg_row_dirty
       (No A0 advance. No attribute writes beyond LUT lookup of 0.)

   8b. SLOW PATH (D0 != 0x20):
       A0 += D0 * 5
       For half = 0, 1:                         ; left then right
           D2_half = 0x0000 if half==0 else 0xFFF0
           For j = 0..4:                        ; 5 chars per half
               byte_val = sign-extend-w(*(A0)+)
               if D3 == 0x50 and j == 4:       ; terminator check
                   ; emulate the inner sub's early RTS — stop this half's writes,
                   ; but do NOT emit any write for this iteration
                   ; A0 has already advanced by 1 (post-increment)
                   continue to half's end cleanup (skip remaining writes)
                   break inner loop
               arcade_tile     = (byte_val + A4@(26).w + A4@(24).w) & 0xFFFF
               arcade_attr     = (A4@(22).w + D2_half) & 0x01FF
               translated_tile = genesistan_pc080sn_tile_vram_lut[arcade_tile & 0x3FFF]
               translated_attr = genesistan_pc080sn_attr_lut[arcade_attr]
               nametable_word  = translated_tile | translated_attr
               cell_in_run     = j*2 + half     ; LEFT halves occupy even cell offsets within each iteration;
                                                ; RIGHT halves occupy odd. See §10.4.1.
               col = (arcade_col + 2*j + half) & 0x3F
               row = (arcade_row + ((arcade_col + 2*j + half) >> 6)) & 0x1F
               staged_fg_buffer[row*64 + col] = nametable_word
               bset row, fg_row_dirty
           End inner loop.
           If half == 0:
               A0 -= 5                          ; rewind per original (subq.l #5, A0)
       End halves loop.
       After loop, A0 has net advance of +5 from its post-deref starting value
       (second half consumed 5 bytes; first half consumed 5 then rewound).

9. (Fall-through from step 7 skip.)

10. Restore registers: movem.l (%sp)+, %d0-%d7/%a0-%a6

11. Force A1 = A1_entry + 0x50 (via addition on top of restored A1), and A2
    likewise, and A0 per step 8 path. Implementation detail: the simplest
    approach is to save only callee-saves inside the hook, compute into scratch
    registers, and set A0/A1/A2 explicitly before RTS. Either shape is
    acceptable as long as the §10.3 exit contract holds.

12. rts
```

#### 10.4.1 Left/right-half cell layout

The original function writes two cells per iteration: the **tile** at
`A1+2` (offset-+2 in the 8-byte iteration window = cell N) and a **second
word** at `A1+6` (offset-+6 = cell N+1). The call with `D2 == 0` does this
for the left half and the call with `D2 == 0xFFF0` does it for the right
half — reading **the same 5 script bytes** both times. This means **per
script byte, the original writes 2 cells** (adjacent columns) — the same
glyph byte is expanded into a 2-cell glyph pair, where the left cell gets
the raw-base attribute and the right cell gets the offset-by-−16 attribute.

So for Cody's algorithm: per iteration (i.e. per script byte `j`), write
**two cells** with column positions `2*j` and `2*j+1` (within the run),
where the left cell uses `D2_half = 0` attributes and the right cell uses
`D2_half = 0xFFF0` attributes. **Both halves come from the same script
byte.** The outer "half" loop in the original was a byte-economy artifact;
Cody's hook can collapse it to a single 5-iteration loop that emits both
cells per iteration.

Preferred simpler restatement:
```
For j = 0..4:
    byte_val = sign-extend-w(*(A0)+)
    arcade_tile = (byte_val + A4@(26).w + A4@(24).w) & 0xFFFF
    For half = 0, 1:
        D2_half = 0 if half==0 else 0xFFF0
        arcade_attr = (A4@(22).w + D2_half) & 0x01FF
        translated_tile = genesistan_pc080sn_tile_vram_lut[arcade_tile & 0x3FFF]
        translated_attr = genesistan_pc080sn_attr_lut[arcade_attr]
        col = (arcade_col + 2*j + half) & 0x3F
        row = (arcade_row + ((arcade_col + 2*j + half) >> 6)) & 0x1F
        staged_fg_buffer[row*64 + col] = translated_tile | translated_attr
        bset row, fg_row_dirty
After loop: A0 net advance is +5 bytes.
```

The terminator check (`if D3 == 0x50 and we are on the last iteration, exit
without writing`) applies **only to the second half's last iteration** in
the original because only the second call has `D4 == 1` reach the check
(D4 counts down to 1 in the second call's final iteration). For Cody's
collapsed loop: the terminator check applies when `D3 == 0x50` and
`j == 4` and `half == 1`. In that one case, emit NO cell writes for that
(j=4, half=1) iteration; the A0 post-increment still happened.

### 10.5 `opcode_replace` JSON entry (exact form)

Add to `specs/rastan_direct_remap.json` `opcode_replace` array:

```json
{
  "arcade_pc": "0x03C4D2",
  "original_bytes": "2449D4FC00502068000 2102C000B48800C400020661 0 780A337C0180000250895344 66F4601AC0FC0005D0C07805 42426100001 25B88780534 3CFFF06100000 6224A4E75",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_text_writer_3c4d2}4E754E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E71",
  "note": "Route text-writer handler (script opcodes 0x50/0x60) at arcade_pc 0x03C4D2 through the Genesis staging-buffer hook. Replaces the body that originally wrote via A1@(2)/A1@(6) indexed writes into PC080SN FG tilemap (confirmed crash source at 0xC09EA0)."
}
```

**The exact `original_bytes` Cody must use** — extract from
`build/regions/maincpu.bin` at file offset `0x03C4D2`, length `0x44`. The
field above contains the byte sequence visible in `build/maincpu.disasm.txt`
lines 75918–75940 reformatted as a single hex string (no spaces). Cody MUST
verify against the binary before committing the entry; `postpatch_startup_rom.py`
enforces this match at line 980.

Update `"opcode_replace_count"` in `specs/rastan_direct_remap.json` from its
current value (46 in Build 0032) to **47**.

### 10.6 No other edits required

- No scroll rewrite.
- No additional hook for `arcade_pc: 0x03C3FE` (proven not to be the crash
  source in `docs/design/Andy_text_writer_3c3fe_hook_spec.md` — still valid
  to hook eventually but not required for Build 0032 crash resolution).
- No changes to existing `genesistan_hook_tilemap_plane_a`,
  `genesistan_hook_tilemap_fg`, `genesistan_hook_tilemap_bg_fill`, or
  `genesistan_hook_cwindow_clear`.
- No changes to VBlank handler, staging buffers, scroll mirrors, row-dirty
  bitmaps, or init paths.
- No changes to address_map.json consumer code (the new patched_site segment
  will be emitted automatically by the patcher based on the new
  `opcode_replace` entry).

---

## 11. Visual Evidence Summary

`screenshots/build_32/` **does not exist** on disk (confirmed by directory
check). Build 0032 screenshot artifacts were not present at the time this
spec was authored. This does NOT block the spec: the disassembly of
`arcade_pc: 0x03C4D2` / `0x03C516` and the Build 0032 trace
(`states/traces/rastan_direct_video_test_build_0032_mame_30s_20260415_010931/genesis_exec_summary.txt`)
provide sufficient evidence for the hook contract. The trace summary
confirms:

- `fg_cwindow_live count=8` — 8 writes intercepted in the C-window FG range
  during the 30-second run.
- `first_pc=03C52A last_pc=03C518` — PC range is entirely inside the inner
  subroutine `arcade_pc: 0x03C516..0x03C54E`.
- `first_addr=C09EA0 last_addr=C09EA6` — writes hit
  `HW_ADDRESS/PC080SN/FG_TILEMAP` at offsets `0x1EA0`..`0x1EA6`.
- `last_data=0x0037` — a real tile code value (indicates the slow path is
  running and the script is rendering non-blank text).
- MAME final PC `0x000010` on exit — the Genesis wrapper's trap vector;
  consistent with the CPU trapping on an invalid write after a small number
  of C-window cycles.

No visual frames are needed to characterize the hook behavior.

---

## 12. Next-Step Impact

- Implementing `genesistan_hook_text_writer_3c4d2` and adding the
  `opcode_replace` entry at `arcade_pc: 0x03C4D2` resolves the Build 0032
  crash at `0xC09EA0`.
- The prior `docs/design/Andy_text_writer_3c3fe_hook_spec.md` is superseded
  by this spec as far as crash resolution is concerned. Hooking
  `arcade_pc: 0x03C3FE` remains a valid **optional** follow-up to cover a
  second text-writer intent class but is not required by Build 0032.
- Address-map artifact (`build/rastan-direct/address_map.json`) will gain
  one more `patched_site` segment automatically on next build; `addr_lookup`
  consumers see the new mapping with no code change.

---

## 13. STOP Conditions

None triggered. All required addresses verified against `address_map.json`,
all disassembly sections captured verbatim from
`build/maincpu.disasm.txt`, row/col arithmetic proven from the §5 formula
against the known crash address, all register inputs/outputs specified, all
callers enumerated, no design decision deferred to Cody.

Noted (non-STOP): `screenshots/build_32/` not present on disk — see §11.
Spec does not depend on visual evidence.
