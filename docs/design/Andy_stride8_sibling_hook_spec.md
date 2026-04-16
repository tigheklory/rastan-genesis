# Andy — Stride-8 Sibling Hook Spec Set (Build 0033)

**Status:** SPEC COMPLETE. Ready for Cody. 7 handlers specced; default path `0x03C950` **out of scope** and not included in any form.
**Scope:** Analysis & specification only. No implementation.

---

## Address-Space Conventions

All `arcade_pc` values are offsets into `build/regions/maincpu.bin`. All
`genesis_rom_offset` values are obtained by looking up the enclosing
`arcade_copy` segment in `build/rastan-direct/address_map.json`
(`[0x03B0A4, 0x03EF28) → [0x03B2A4, 0x03F128)`, `identity_offset = 512`)
and applying the segment's recorded offset. No cross-space arithmetic is
performed outside the segment record.

`HW_ADDRESS/PC080SN/FG_TILEMAP` base: `0xC08000` (confirmed in
`apps/rastan-direct/src/main_68k.s:54` and guard at `main_68k.s:385–388`).
Arcade FG cell convention: 4-byte cells (tile word + attribute word),
64-col × 32-row visible. Every handler in this set uses the same 8-byte
iteration stride with writes at `A1@(2)` (tile word of cell N) and
`A1@(6)` (tile word of cell N+1) — i.e. each iteration fills **two
adjacent cells** (the left-half and right-half of a glyph pair). The
`A1@(0)` and `A1@(4)` slots are the arcade attribute words, which are
composed by the 0x03C4D2 / sibling handlers as a parallel byte stream
at `A1@(6)` (not `A1@(4)`) per the disassembly evidence below. This is
an arcade-internal cell-record artifact; Cody's hooks MUST emit into
`staged_fg_buffer` using the **4-byte-cell** row/col formula from
`docs/design/Andy_text_writer_3c4d2_hook_spec.md` §5.1.

The patched Genesis ROM (`apps/rastan-direct/dist/rastan_direct_video_test.bin`)
was verified at build time by the existing build pipeline
(`tools/translation/postpatch_startup_rom.py`). For each handler span in
this spec, the bytes currently at the mapped `genesis_rom_offset` are
the **verbatim arcade bytes** (the arcade_copy segment covers the whole
range, and no existing `opcode_replace` overlaps any of the 7 handler
bodies — confirmed by grep of `specs/rastan_direct_remap.json` against
the 7 handler address ranges).

---

## Handler 1 — `arcade_pc: 0x03C550` (opcode top-nibble 0xA0)

- **`genesis_rom_offset`:** `0x03C750` (address_map.json segment lookup).
- **Hook name:** `genesistan_hook_text_writer_3c550`.

### H1 — Full disassembly (`build/maincpu.disasm.txt:75960–75978`)

```
0x03C550   2068 0002        movea.l  A0@(2), A0
0x03C554   102C 000B        move.b   A4@(11), D0
0x03C558   4880             ext.w    D0
0x03C55A   D0C0             adda.w   D0, A0
0x03C55C   4244             clr.w    D4
0x03C55E   7604             moveq    #4, D3                 ; 5 iterations (D3 ranges 4..0)
0x03C560   1210             move.b   A0@, D1                ; read glyph byte without post-inc (same byte reused)
0x03C562   4881             ext.w    D1
0x03C564   3001             move.w   D1, D0
0x03C566   D06C 0016        add.w    A4@(22), D0            ; attribute base
0x03C56A   D044             add.w    D4, D0                 ; + per-iteration offset (0, 16, 32, 48, 64)
0x03C56C   3340 0006        move.w   D0, A1@(6)             ; ATTRIBUTE word (NOT tile)
0x03C570   336C 001A 0002   move.w   A4@(26), A1@(2)        ; TILE word = A4@(26) base tile literal
0x03C576   5089             addq.l   #8, A1
0x03C578   0644 0010        addi.w   #16, D4
0x03C57C   5343             subq.w   #1, D3
0x03C57E   66E4             bne.s    0x03C564
0x03C580   D2FC 0030        adda.w   #48, A1                ; post-loop A1 advance
0x03C584   4E75             rts
```

### H2 — Patch span

`0x03C550..0x03C585` inclusive = **0x36 bytes (54)**. No overlap with
other handlers (next is `0x03C586`). Verified present and unmodified in
the Genesis ROM at `genesis_rom_offset: 0x03C750..0x03C785` (arcade_copy
segment coverage).

### H3 — Input register contract

| Reg | Role | Source |
|-----|------|--------|
| A0 | Descriptor pointer; function dereferences `A0@(2)` into A0. | Dispatcher. |
| A1 | HW dest in FG tilemap. | Dispatcher. |
| A4 | Script state; reads `A4@(11).b`, `A4@(22).w`, `A4@(26).w`. | Dispatcher. |
| A4@(11).b | "Char count" — sign-extended and added to A0 as a prefix skip. | Script state. |
| A4@(22).w | Attribute base. | Script state. |
| A4@(26).w | Tile literal (the same tile used for all 5 cells). | Script state. |
| D3 | Terminator-check carrier (not read in this handler). | Dispatcher. |

### H4 — Write shape

Stride +8 confirmed. **Ordering differs from 0x03C4D2:** this handler
writes attribute FIRST (`A1@(6)`) then tile (`A1@(2)`). The tile value
is a literal `A4@(26).w` (constant for every iteration). The attribute
varies per iteration by `D4` increments of 16 (0, 16, 32, 48, 64).

- Prefix skip: `A0 += sign_ext_w(A4@(11).b)` (no multiplier).
- Iterations: 5 (`D3` from 4 down to 0).
- Writes per iteration: 2 (one to each cell pair half).
- Post-loop A1 advance: +48 on top of the +40 produced by the 5
  iterations — total **A1 advance = 0x48 bytes** from entry.

### H5 — Output contract

- **Cells written per call: 10** (5 iterations × 2 cells).
- Starting cell index: `first_write = A1 + 2`; `cell_idx = (first_write - 0xC08000) / 4`; `arcade_row = (cell_idx >> 6) & 0x3F`; `arcade_col = cell_idx & 0x3F`. Same formula as 0x03C4D2 §5.1. Row/col wrapping as in the 0x03C4D2 hook.
- Per iteration `i ∈ {0..4}`:
  - **Left cell** (occupies `(row, col + 2*i)`): tile = LUT[`A4@(26).w` masked to 14 bits]; attribute = LUT[`(glyph_byte + A4@(22).w + 16*i) & 0x1FF` raw attr]. (Note: **left-cell gets the varying attribute**, not the right.)
  - **Right cell** (occupies `(row, col + 2*i + 1)`): tile = LUT[`A4@(26).w`]; attribute = LUT[`(glyph_byte + A4@(22).w + 16*i) & 0x1FF`]. Same as left cell because both cells share the same data in this handler — the arcade's `A1@(6)` receives the attribute-product and `A1@(2)` receives the tile literal, and both are the left-half and right-half of a single glyph-pair. Cody's hook emits the identical Genesis word to both `staged_fg_buffer[row*64 + col + 2*i]` and `staged_fg_buffer[row*64 + col + 2*i + 1]`.
- `fg_row_dirty`: set bits for every row that any of the 10 cells land on (if the 10-cell run does not span a row wrap, this is a single row).

### H6 — Caller analysis

Single caller: `arcade_pc: 0x03C93C` (`genesis_rom_offset: 0x03CB3C`),
`beqw 0x3c550`. One `opcode_replace` at the handler entry is sufficient.

### H7 — Hook name

`genesistan_hook_text_writer_3c550`.

### Differences from 0x03C4D2

- Attribute-first / tile-literal ordering (§H1 lines `0x03C56C/0x03C570`).
- Only ONE script byte is read (no post-increment); every cell shares
  the same glyph byte.
- `A1` advance = `0x48`, not `0x50`.
- No inner subroutine; single inline loop.
- Post-loop `A1 += 48` instead of `A1 = A2 = entry_A1 + 0x50`.

---

## Handler 2 — `arcade_pc: 0x03C586` (opcode top-nibble 0xC0)

- **`genesis_rom_offset`:** `0x03C786` (address_map.json).
- **Hook name:** `genesistan_hook_text_writer_3c586`.

### H1 — Full disassembly (`build/maincpu.disasm.txt:75979–76018`; inner sub `0x03C606` at `76019–76034`; shared helper `0x03C742` documented under H4)

```
0x03C586   2068 0002        movea.l  A0@(2), A0
0x03C58A   102C 000B        move.b   A4@(11), D0
0x03C58E   4880             ext.w    D0
0x03C590   C0FC 0003        mulu.w   #3, D0                   ; prefix multiplier: 3
0x03C594   D0C0             adda.w   D0, A0
0x03C596   0C2C 0006 0001   cmpi.b   #6, A4@(1)
0x03C59C   6732             beq.s    0x03C5D0                  ; A4@(1).b == 6 → alt path
; ── primary path (A4@(1).b != 6) ──
0x03C59E   7603             moveq    #3, D3                   ; 4 iterations of 0x03C606
0x03C5A0   4242             clr.w    D2
0x03C5A2   6100 0062        bsr.w    0x03C606
0x03C5A6   4247             clr.w    D7
0x03C5A8   4246             clr.w    D6
0x03C5AA   6100 0196        bsr.w    0x03C742                 ; ONE extra cell via helper
0x03C5AE   D2FC 0008        adda.w   #8, A1                   ; advance over the helper cell
0x03C5B2   90FC 0003        suba.w   #3, A0                   ; rewind 3 bytes
0x03C5B6   7603             moveq    #3, D3
0x03C5B8   343C FFF0        move.w   #-16, D2                 ; right-half attribute bias
0x03C5BC   6100 0048        bsr.w    0x03C606                 ; 4 more cells
0x03C5C0   4247             clr.w    D7
0x03C5C2   3C3C FFF0        move.w   #-16, D6
0x03C5C6   6100 017A        bsr.w    0x03C742                 ; one more helper cell
0x03C5CA   D2FC 0018        adda.w   #24, A1
0x03C5CE   4E75             rts
; ── alt path (A4@(1).b == 6) ──
0x03C5D0   4247             clr.w    D7
0x03C5D2   4246             clr.w    D6
0x03C5D4   6100 016C        bsr.w    0x03C742                 ; helper cell
0x03C5D8   D2FC 0008        adda.w   #8, A1
0x03C5DC   7603             moveq    #3, D3
0x03C5DE   4242             clr.w    D2
0x03C5E0   6100 0024        bsr.w    0x03C606                 ; 4 cells
0x03C5E4   90FC 0003        suba.w   #3, A0
0x03C5E8   4247             clr.w    D7
0x03C5EA   3C3C FFF0        move.w   #-16, D6
0x03C5EE   6100 0152        bsr.w    0x03C742
0x03C5F2   D2FC 0008        adda.w   #8, A1
0x03C5F6   7603             moveq    #3, D3
0x03C5F8   343C FFF0        move.w   #-16, D2
0x03C5FC   6100 0008        bsr.w    0x03C606
0x03C600   D2FC 0010        adda.w   #16, A1
0x03C604   4E75             rts
; ── inner subroutine 0x03C606 (stride-8 `A1@(2)` + `A1@(6)`) ──
0x03C606   1018             move.b   A0@+, D0
0x03C608   4880             ext.w    D0
0x03C60A   0C00 00FF        cmpi.b   #-1, D0                   ; 0xFF sentinel → blank tile
0x03C60E   6608             bne.s    0x03C618
0x03C610   337C 0180 0002   move.w   #0x0180, A1@(2)           ; blank tile
0x03C616   6016             bra.s    0x03C62E
0x03C618   D06C 0016        add.w    A4@(22), D0               ; attribute base
0x03C61C   3340 0006        move.w   D0, A1@(6)                ; attribute at right-half
0x03C620   3E2C 001A        move.w   A4@(26), D7               ; tile base
0x03C624   DE42             add.w    D2, D7
0x03C626   0247 01FF        andi.w   #0x01FF, D7
0x03C62A   3347 0002        move.w   D7, A1@(2)                ; tile at left-half
0x03C62E   5089             addq.l   #8, A1
0x03C630   5343             subq.w   #1, D3
0x03C632   66D2             bne.s    0x03C606
0x03C634   4E75             rts
```

Shared helper 0x03C742 behavior (`build/maincpu.disasm.txt:76122–76128`):
writes one cell pair — tile = `D6 + A4@(26).w (mask 0x1FF)` at `A1@(2)`;
attribute = `D7 + A4@(22).w (mask 0x1FF)` at `A1@(6)`. Does NOT advance
A1 (caller responsible).

### H2 — Patch span

`0x03C586..0x03C605` inclusive = **0x80 bytes (128)**. The inner sub
`0x03C606..0x03C635` (48 bytes) becomes dead code after the patch (no
external callers per grep — only the two `bsr.w 0x03C606` sites inside
0x03C586 itself). The shared helper `0x03C742` remains callable by
other handlers but since all 7 handlers in this set are being patched
and the default path is out of scope, `0x03C742` becomes **dead once
all 7 patches are installed** (open question 1 at end of doc).

Patch span present and unmodified in ROM at `genesis_rom_offset:
0x03C786..0x03C805`.

### H3 — Input register contract

| Reg | Role | Source |
|-----|------|--------|
| A0 | Descriptor; `A0@(2)` deref'd → A0. | Dispatcher. |
| A1 | FG hw dest. | Dispatcher. |
| A4 | Script state. Reads: `A4@(1).b` (path selector), `A4@(11).b` (char count), `A4@(22).w` (attr base), `A4@(26).w` (tile base). | Dispatcher + script. |
| D2, D3, D6, D7 | Clobbered. | — |

### H4 — Write shape

Stride +8, writes at `A1@(2)` (tile) and `A1@(6)` (attr). Path-selected:

- **Primary path** (A4@(1).b != 6):
  - 4 iterations via 0x03C606 (left half of glyph pair, D2=0): 8 cells
  - 1 cell via 0x03C742 helper: 2 cells
  - post A1 += 8
  - 4 iterations via 0x03C606 (right half, D2=-16): 8 cells
  - 1 cell via 0x03C742 helper: 2 cells
  - post A1 += 24
  - **Total: 20 cells written; A1 advance = 4×8 + 8 + 4×8 + 24 = 96 = 0x60 bytes**
- **Alt path** (A4@(1).b == 6):
  - 1 helper + 4 iter 0x03C606 (D2=0) + 1 helper + 4 iter 0x03C606 (D2=-16) + post A1 += 16
  - **Total: 18 cells written (1+8+1+8); A1 advance = 8+8+32+8+32+16 = 104 = 0x68 bytes**

Note: iteration count D3=3 gives 4 iterations of dbra, each producing 2 cells = 8 cells per call.

### H5 — Output contract

Per iteration of 0x03C606 (both paths): write at cell `N` (left-half)
and cell `N+1` (right-half) → 2 `staged_fg_buffer` writes. Terminator
sentinel `0xFF` → blank tile `0x0180` at left-half only (but Cody's hook
must still emit the LUT-translated 0x0180 at `staged_fg_buffer[N]` AND
SKIP writing cell N+1 for that iteration per the `bra.s 0x03C62E`).

Helper 0x03C742 writes two cells unconditionally (no sentinel check).

### H6 — Caller analysis

Single caller: `arcade_pc: 0x03C94C` (`genesis_rom_offset: 0x03CB4C`).
`beqw 0x3c586`. One `opcode_replace` at the handler entry is sufficient.

### H7 — Hook name

`genesistan_hook_text_writer_3c586`.

### Differences from 0x03C4D2

- Two distinct paths gated on `A4@(1).b == 6`.
- 0xFF sentinel handling in inner sub (0x03C4D2's terminator was a
  different `D3==0x50 && D4==1` check).
- A1 advance is 0x60 or 0x68 depending on path (not a constant 0x50).
- Inner sub writes attr at `A1@(6)` and tile at `A1@(2)` (same sides as
  0x03C4D2), but the tile is computed from A4@(26)+D2 (a constant base
  biased per-half) rather than from a script byte read.
- Uses helper `0x03C742` for single-cell inserts between loop blocks.

---

## Handler 3 — `arcade_pc: 0x03C636` (opcode top-nibble 0xB0)

- **`genesis_rom_offset`:** `0x03C836` (address_map.json).
- **Hook name:** `genesistan_hook_text_writer_3c636`.

### H1 — Full disassembly (`build/maincpu.disasm.txt:76035–76087`; includes private inner sub `0x03C6AC`)

```
0x03C636   2068 0002        movea.l  A0@(2), A0
0x03C63A   102C 000B        move.b   A4@(11), D0
0x03C63E   4880             ext.w    D0
0x03C640   E548             lsl.w    #2, D0                   ; prefix multiplier: ×4 (shift-left by 2)
0x03C642   D0C0             adda.w   D0, A0
; ── game-state test block ──
0x03C644   0C2D 0002 0118   cmpi.b   #2, A5@(280)
0x03C64A   6712             beq.s    0x03C65E
0x03C64C   0C6D 0062 013E   cmpi.w   #98, A5@(318)
0x03C652   6520             bcs.s    0x03C674                  ; if A5@(318) < 98 → skip prelude
0x03C654   0C6D 0064 013E   cmpi.w   #100, A5@(318)
0x03C65A   6502             bcs.s    0x03C65E
0x03C65C   6016             bra.s    0x03C674                  ; skip prelude
; ── prelude: 2 helper cells ──
0x03C65E   4246             clr.w    D6
0x03C660   4247             clr.w    D7
0x03C662   6100 00DE        bsr.w    0x03C742                 ; 1 cell pair
0x03C666   5089             addq.l   #8, A1
0x03C668   4246             clr.w    D6
0x03C66A   3E3C FFF0        move.w   #-16, D7
0x03C66E   6100 00D2        bsr.w    0x03C742                 ; 1 cell pair
0x03C672   5089             addq.l   #8, A1
; ── main loop ──
0x03C674   7602             moveq    #2, D3                   ; 3 iterations
0x03C676   4242             clr.w    D2
0x03C678   6100 0032        bsr.w    0x03C6AC                 ; 3 cells
0x03C67C   7602             moveq    #2, D3
0x03C67E   343C FFF0        move.w   #-16, D2
0x03C682   6100 0028        bsr.w    0x03C6AC                 ; 3 cells
; ── epilogue game-state test ──
0x03C686   0C2D 0002 0118   cmpi.b   #2, A5@(280)
0x03C68C   6712             beq.s    0x03C6A0
0x03C68E   0C6D 0062 013E   cmpi.w   #98, A5@(318)
0x03C694   6510             bcs.s    0x03C6A6
0x03C696   0C6D 0064 013E   cmpi.w   #100, A5@(318)
0x03C69C   6502             bcs.s    0x03C6A0
0x03C69E   6006             bra.s    0x03C6A6
0x03C6A0   D2FC 0020        adda.w   #32, A1                   ; path A
0x03C6A4   4E75             rts
0x03C6A6   D2FC 0030        adda.w   #48, A1                   ; path B
0x03C6AA   4E75             rts
; ── private inner sub 0x03C6AC (stride-8) ──
0x03C6AC   1018             move.b   A0@+, D0
0x03C6AE   4880             ext.w    D0
0x03C6B0   0C00 00FF        cmpi.b   #-1, D0
0x03C6B4   6608             bne.s    0x03C6BE
0x03C6B6   337C 0180 0002   move.w   #0x0180, A1@(2)           ; blank tile
0x03C6BC   6008             bra.s    0x03C6C6
0x03C6BE   D06C 001A        add.w    A4@(26), D0               ; tile base
0x03C6C2   3340 0002        move.w   D0, A1@(2)                ; tile
0x03C6C6   3E2C 0016        move.w   A4@(22), D7
0x03C6CA   DE42             add.w    D2, D7
0x03C6CC   0247 01FF        andi.w   #0x01FF, D7
0x03C6D0   3347 0006        move.w   D7, A1@(6)                ; attribute
0x03C6D4   5089             addq.l   #8, A1
0x03C6D6   5343             subq.w   #1, D3
0x03C6D8   66D2             bne.s    0x03C6AC
0x03C6DA   4E75             rts
```

### H2 — Patch span

`0x03C636..0x03C6AB` inclusive = **0x76 bytes (118)**. Inner sub
`0x03C6AC..0x03C6DB` becomes dead after patch (no external callers).
Present and unmodified in ROM at `0x03C836..0x03C8AB`.

### H3 — Input register contract

| Reg | Role | Source |
|-----|------|--------|
| A0 | Descriptor; `A0@(2)` deref. | Dispatcher. |
| A1 | FG hw dest. | Dispatcher. |
| A4 | Script state; reads `A4@(11).b`, `A4@(22).w`, `A4@(26).w`. | Script. |
| **A5** | Arcade workram. Reads `A5@(280).b` and `A5@(318).w` for game-state branches. | Runtime game state. |
| D2, D3, D6, D7 | Clobbered. | — |

### H4 — Write shape

Stride +8. Prefix `A0 += lsl_w(A4@(11).b, 2)`. Two sub-paths per
game-state tests:

- **Prelude skipped (game state path):** 3 + 3 = 6 cell pairs = 6 iterations of 0x03C6AC + post A1 adjust.
- **Prelude included:** 2 helper cells + 6 iterations of 0x03C6AC + post A1 adjust (32 or 48).

### H5 — Output contract

- Cells per call: 6 or 8 (depending on prelude inclusion). Both paths
  write via `A1@(2)` tile + `A1@(6)` attribute stride-8.
- Terminator: `0xFF` byte in script → write blank tile `0x0180` at
  left-half only, skip writing right-half (`bra.s 0x03C6C6`).
- Row/col derivation: same 4-byte-cell formula (§5.1 of 0x03C4D2 spec).

### H6 — Caller analysis

Single caller: `arcade_pc: 0x03C944` (`genesis_rom_offset: 0x03CB44`).
`beqw 0x3c636`. One `opcode_replace` at handler entry sufficient.

### H7 — Hook name

`genesistan_hook_text_writer_3c636`.

### Differences from 0x03C4D2

- **Game-state branches on `A5@(280).b` and `A5@(318).w`** control
  prelude inclusion and post-loop A1 advance. Cody's hook MUST read the
  same A5 fields and replicate the four possible outcomes.
- `A0` prefix-skip uses `lsl.w #2, D0` (×4), not `muluw #5`.
- Variable-count output (6 or 8 cell-pairs depending on game state).
- Uses shared helper `0x03C742` for two prelude cells.
- Post-loop `A1 += 32` (path A) or `A1 += 48` (path B).

---

## Handler 4 — `arcade_pc: 0x03C6DC` (opcode top-nibble 0x30)

- **`genesis_rom_offset`:** `0x03C8DC` (address_map.json).
- **Hook name:** `genesistan_hook_text_writer_3c6dc`.

### H1 — Full disassembly (`build/maincpu.disasm.txt:76088–76121`; private inner sub `0x03C70A`)

```
0x03C6DC   2068 0002        movea.l  A0@(2), A0
0x03C6E0   102C 000B        move.b   A4@(11), D0
0x03C6E4   4880             ext.w    D0
0x03C6E6   C0FC 0009        mulu.w   #9, D0                    ; prefix multiplier: 9
0x03C6EA   D0C0             adda.w   D0, A0
0x03C6EC   323C FFD0        move.w   #-48, D1                  ; D1 = -48 (initial column offset)
0x03C6F0   383C 0010        move.w   #16, D4                   ; D4 = 16 (per-iter D1 increment)
0x03C6F4   7606             moveq    #6, D3                    ; 7 iterations
0x03C6F6   6100 0012        bsr.w    0x03C70A
0x03C6FA   323C FFD0        move.w   #-48, D1
0x03C6FE   4244             clr.w    D4                        ; D4 = 0 (no D1 increment in 2nd call)
0x03C700   7603             moveq    #3, D3                    ; 4 iterations
0x03C702   6100 0006        bsr.w    0x03C70A
0x03C706   5089             addq.l   #8, A1                    ; post +8
0x03C708   4E75             rts
; ── private inner 0x03C70A (stride-8 with jsr helper_5b512_rts) ──
0x03C70A   1418             move.b   A0@+, D2
0x03C70C   4882             ext.w    D2
0x03C70E   4A42             tst.w    D2
0x03C710   6608             bne.s    0x03C71A
0x03C712   337C 0180 0002   move.w   #0x0180, A1@(2)            ; blank tile on zero-terminator
0x03C718   6020             bra.s    0x03C73A
0x03C71A   3001             move.w   D1, D0
0x03C71C   D06C 001A        add.w    A4@(26), D0
0x03C720   3340 0002        move.w   D0, A1@(2)                 ; tile
0x03C724   3E2C 0016        move.w   A4@(22), D7
0x03C728   DE42             add.w    D2, D7
0x03C72A   0247 01FF        andi.w   #0x01FF, D7
0x03C72E   4EB9 0005 B512   jsr      0x0005B512                 ; helper_5b512_rts (no-op)
0x03C734   3347 0006        move.w   D7, A1@(6)                 ; attribute
0x03C738   D244             add.w    D4, D1                     ; D1 += D4 each iter (0 or 16)
0x03C73A   5089             addq.l   #8, A1
0x03C73C   5343             subq.w   #1, D3
0x03C73E   66CA             bne.s    0x03C70A
0x03C740   4E75             rts
```

### H2 — Patch span

`0x03C6DC..0x03C709` inclusive = **0x2E bytes (46)**. Private inner
`0x03C70A..0x03C741` becomes dead. Present and unmodified in ROM at
`0x03C8DC..0x03C909`.

### H3 — Input register contract

| Reg | Role | Source |
|-----|------|--------|
| A0 | Descriptor; `A0@(2)` deref. | Dispatcher. |
| A1 | FG hw dest. | Dispatcher. |
| A4 | `A4@(11).b`, `A4@(22).w`, `A4@(26).w`. | Script. |
| D1, D3, D4 | Clobbered. | — |

### H4 — Write shape

Stride +8 via inner 0x03C70A, with per-iteration D1 biased by D4 (0 or 16):

- 1st call: D3=6 (7 iterations), D1=−48 increments by 16 per iter → tile offsets −48,−32,−16,0,+16,+32,+48.
- 2nd call: D3=3 (4 iterations), D1=−48 no increment (D4=0) → constant tile offset −48 for all 4 iterations.
- Terminator: **zero byte** (`tst.w D2; beq 0x03C71A` triggers blank-tile branch when D2==0). NOT 0xFF sentinel.

### H5 — Output contract

- Total cells per call: 11 iterations × 2 cells = **22 cells**, with any
  iteration whose script byte sign-extends to zero emitting blank tile
  at left-half only.
- Post-loop A1 += 8 extra (total A1 advance = 11×8 + 8 = 96 = 0x60).

### H6 — Caller analysis

Single caller: `arcade_pc: 0x03C91C` (`genesis_rom_offset: 0x03CB1C`).
`beqw 0x3c6dc`. One `opcode_replace` sufficient.

### H7 — Hook name

`genesistan_hook_text_writer_3c6dc`.

### Differences from 0x03C4D2

- Prefix multiplier ×9 (`muluw #9`), not ×5.
- Two 0x03C70A calls with different parameters (D4=16 then D4=0).
- Terminator is **zero byte**, not 0xFF.
- Inner-sub calls `jsr helper_5b512_rts` between tile and attr writes
  (same as 0x03C4D2's 0x03C516).
- Tile code uses `A4@(26).w + D1 (−48..+48)`, varying per iteration.
- Post-loop `A1 += 8` (not `A1 = A2 = entry + 0x50`).

---

## Handler 5 — `arcade_pc: 0x03C75C` (opcode top-nibble 0x90)

- **`genesis_rom_offset`:** `0x03C95C` (address_map.json).
- **Hook name:** `genesistan_hook_text_writer_3c75c`.

### H1 — Full disassembly (`build/maincpu.disasm.txt:76129–76151`; calls shared helpers `0x03C742` and `0x03C7D2`)

```
0x03C75C   2068 0002        movea.l  A0@(2), A0
0x03C760   102C 000B        move.b   A4@(11), D0
0x03C764   4880             ext.w    D0
0x03C766   C0FC 0007        mulu.w   #7, D0                    ; prefix multiplier: 7
0x03C76A   D0C0             adda.w   D0, A0
0x03C76C   3C3C FFF0        move.w   #-16, D6
0x03C770   3E3C FFF8        move.w   #-8, D7
0x03C774   61CC             bsr.s    0x03C742                  ; prelude helper cell pair
0x03C776   5089             addq.l   #8, A1
0x03C778   7601             moveq    #1, D3                    ; 2 iterations
0x03C77A   343C FFF8        move.w   #-8, D2
0x03C77E   6100 0052        bsr.w    0x03C7D2
0x03C782   7601             moveq    #1, D3                    ; 2 iterations
0x03C784   4242             clr.w    D2
0x03C786   6100 004A        bsr.w    0x03C7D2
0x03C78A   7601             moveq    #1, D3                    ; 2 iterations
0x03C78C   343C FFF0        move.w   #-16, D2
0x03C790   6100 0040        bsr.w    0x03C7D2
0x03C794   7604             moveq    #4, D3                    ; 5 iterations
0x03C796   343C FFF8        move.w   #-8, D2
0x03C79A   6100 0036        bsr.w    0x03C7D2
0x03C79E   D2FC 0010        adda.w   #16, A1                   ; post +16
0x03C7A2   4E75             rts
; ── shared inner 0x03C7D2 (used by 0x03C75C and 0x03C7A4; stride-8; 0xFF sentinel) ──
0x03C7D2   4240             clr.w    D0
0x03C7D4   1018             move.b   A0@+, D0
0x03C7D6   4880             ext.w    D0
0x03C7D8   0C00 00FF        cmpi.b   #-1, D0
0x03C7DC   6608             bne.s    0x03C7E6
0x03C7DE   337C 0180 0002   move.w   #0x0180, A1@(2)
0x03C7E4   6008             bra.s    0x03C7EE
0x03C7E6   D06C 001A        add.w    A4@(26), D0
0x03C7EA   3340 0002        move.w   D0, A1@(2)                 ; tile
0x03C7EE   3E2C 0016        move.w   A4@(22), D7
0x03C7F2   DE42             add.w    D2, D7
0x03C7F4   0247 01FF        andi.w   #0x01FF, D7
0x03C7F8   3347 0006        move.w   D7, A1@(6)                 ; attribute
0x03C7FC   5089             addq.l   #8, A1
0x03C7FE   5343             subq.w   #1, D3
0x03C800   66D0             bne.s    0x03C7D2
0x03C802   4E75             rts
```

### H2 — Patch span

`0x03C75C..0x03C7A3` inclusive = **0x48 bytes (72)**. Shared inner subs
`0x03C742` and `0x03C7D2` have callers from multiple handlers — they
become dead only after all 7 handlers are patched (open question 1).

Present and unmodified in ROM at `0x03C95C..0x03C9A3`.

### H3 — Input register contract

| Reg | Role | Source |
|-----|------|--------|
| A0, A1, A4 | As 0x03C4D2. | Dispatcher. |
| D2, D3, D6, D7 | Clobbered. | — |

### H4 — Write shape

Prefix ×7 (`muluw #7`). One 0x03C742 prelude + four 0x03C7D2 calls with
varying D2 and D3 (D2 ∈ {−8, 0, −16, −8}; D3 ∈ {1, 1, 1, 4} → iterations
2, 2, 2, 5). Writes: 1 + 2+2+2+5 = **12 iterations × 2 cells = 24 cells**.

Terminator: 0xFF (sentinel branch in 0x03C7D2).

### H5 — Output contract

- 24 cells per call + 1 prelude helper cell pair = **26 cells** across
  multiple rows if wrapping, via standard `staged_fg_buffer` layout.
- Post-loop A1 += 16 (so total A1 advance = 8 prelude + 12×8 + 16 = 120 = 0x78).

### H6 — Caller analysis

Single caller: `arcade_pc: 0x03C934` (`genesis_rom_offset: 0x03CB34`).
`beqw 0x3c75c`. One `opcode_replace` sufficient.

### H7 — Hook name

`genesistan_hook_text_writer_3c75c`.

### Differences from 0x03C4D2

- Prefix ×7.
- Four inner-sub calls with different (D2, D3) tuples.
- Prelude helper cell pair via 0x03C742.
- 0xFF sentinel (different from 0x03C4D2's `D3==0x50 && D4==1`).
- Post A1 += 16.

---

## Handler 6 — `arcade_pc: 0x03C7A4` (opcode top-nibble 0x20)

- **`genesis_rom_offset`:** `0x03C9A4` (address_map.json).
- **Hook name:** `genesistan_hook_text_writer_3c7a4`.

### H1 — Full disassembly (`build/maincpu.disasm.txt:76152–76197`; private inner sub `0x03C804` + shared `0x03C7D2`)

```
0x03C7A4   2068 0002        movea.l  A0@(2), A0
0x03C7A8   102C 000B        move.b   A4@(11), D0
0x03C7AC   4880             ext.w    D0
0x03C7AE   C0FC 0006        mulu.w   #6, D0                   ; prefix multiplier: 6
0x03C7B2   D0C0             adda.w   D0, A0
0x03C7B4   7602             moveq    #2, D3                   ; 3 iterations
0x03C7B6   4242             clr.w    D2
0x03C7B8   6100 004A        bsr.w    0x03C804                 ; synth-literal cell pairs
0x03C7BC   7602             moveq    #2, D3                   ; 3 iterations
0x03C7BE   343C FFF0        move.w   #-16, D2
0x03C7C2   6100 0040        bsr.w    0x03C804
0x03C7C6   7606             moveq    #6, D3                   ; 7 iterations
0x03C7C8   343C FFF8        move.w   #-8, D2
0x03C7CC   6100 0004        bsr.w    0x03C7D2                 ; script-byte cell pairs
0x03C7D0   4E75             rts
; ── private inner 0x03C804 (stride-8; synthesized D0 from D3) ──
0x03C804   303C FFE0        move.w   #-32, D0                   ; D0 = -32 by default
0x03C808   0C43 0002        cmpi.w   #2, D3
0x03C80C   6704             beq.s    0x03C812
0x03C80E   303C FFD0        move.w   #-48, D0                   ; D0 = -48 for D3 != 2
0x03C812   D06C 001A        add.w    A4@(26), D0                ; tile = A4@(26) + D0
0x03C816   3340 0002        move.w   D0, A1@(2)                 ; tile
0x03C81A   3E2C 0016        move.w   A4@(22), D7
0x03C81E   DE42             add.w    D2, D7
0x03C820   0247 01FF        andi.w   #0x01FF, D7
0x03C824   3347 0006        move.w   D7, A1@(6)                 ; attribute
0x03C828   5089             addq.l   #8, A1
0x03C82A   5343             subq.w   #1, D3
0x03C82C   66D6             bne.s    0x03C804
0x03C82E   4E75             rts
```

### H2 — Patch span

`0x03C7A4..0x03C7D1` inclusive = **0x2E bytes (46)**. Private inner
`0x03C804..0x03C82F` becomes dead after patch. Shared inner `0x03C7D2`
shared with 0x03C75C (dies when both handlers patched).

Present in ROM at `0x03C9A4..0x03C9D1`.

### H3 — Input register contract

Same as 0x03C4D2 (A0, A1, A4; D2, D3, D7 clobbered).

### H4 — Write shape

Prefix ×6 (`muluw #6`). Three inner calls:

- 0x03C804 with D3=2 → 3 iterations × 2 cells = 6 cells. Tile derived from D3 (−32 or −48) + A4@(26), NOT from script byte.
- 0x03C804 with D3=2, D2=−16 → 3 iterations × 2 cells = 6 cells.
- 0x03C7D2 with D3=6 → 7 iterations × 2 cells = 14 cells, tile from script byte + A4@(26).

**Total: 26 cells per call.** No post A1 adjust — rts immediately.

Terminator (for 0x03C7D2 portion only): 0xFF sentinel.

### H5 — Output contract

26 cells; row/col formula same. Mix of **synthesized-tile** cells (first
two 0x03C804 calls — tile based on D3 count not script content) and
**script-byte** cells (last 0x03C7D2 call).

### H6 — Caller analysis

Single caller: `arcade_pc: 0x03C914` (`genesis_rom_offset: 0x03CB14`).
`beqw 0x3c7a4`. One `opcode_replace` sufficient.

### H7 — Hook name

`genesistan_hook_text_writer_3c7a4`.

### Differences from 0x03C4D2

- Prefix ×6.
- Mixed inner sub flavors: synthesized-tile (0x03C804) + script-byte (0x03C7D2).
- **No post-loop A1 adjust** — rts directly after last inner call.
- Total cells = 26 (largest of the set).

---

## Handler 7 — `arcade_pc: 0x03C830` (opcode top-nibble 0x10)

- **`genesis_rom_offset`:** `0x03CA30` (address_map.json).
- **Hook name:** `genesistan_hook_text_writer_3c830`.

### H1 — Full disassembly (`build/maincpu.disasm.txt:76198–76264`; private inner subs `0x03C85E` and `0x03C89A`; branch continuation at `0x03C8BE`)

```
0x03C830   2068 0002        movea.l  A0@(2), A0
0x03C834   102C 000B        move.b   A4@(11), D0
0x03C838   4880             ext.w    D0
0x03C83A   E548             lsl.w    #2, D0                    ; prefix multiplier: ×4
0x03C83C   D0C0             adda.w   D0, A0
0x03C83E   4A2C 0038        tst.b    A4@(56)                   ; A4@(56).b test
0x03C842   6600 007A        bne.w    0x03C8BE                  ; alt path (non-zero)
; ── primary path (A4@(56).b == 0) ──
0x03C846   7605             moveq    #5, D3                    ; 6 iterations
0x03C848   343C FFF8        move.w   #-8, D2
0x03C84C   6100 0010        bsr.w    0x03C85E
0x03C850   5988             subq.l   #4, A0                    ; rewind 4 bytes
0x03C852   7605             moveq    #5, D3
0x03C854   343C FFE8        move.w   #-24, D2
0x03C858   6100 0004        bsr.w    0x03C85E
0x03C85C   4E75             rts
; ── private inner 0x03C85E (stride-8; special-case via 0x03C89A) ──
0x03C85E   4240             clr.w    D0
0x03C860   0C43 0005        cmpi.w   #5, D3                    ; first iteration (D3==5)?
0x03C864   6606             bne.s    0x03C86C
0x03C866   6100 0032        bsr.w    0x03C89A                  ; special-case: maybe write attribute at A1@(4)
0x03C86A   6010             bra.s    0x03C87C
0x03C86C   1018             move.b   A0@+, D0
0x03C86E   4880             ext.w    D0
0x03C870   4A40             tst.w    D0
0x03C872   6608             bne.s    0x03C87C
0x03C874   337C 0180 0002   move.w   #0x0180, A1@(2)            ; blank tile on zero-terminator
0x03C87A   6008             bra.s    0x03C884
0x03C87C   D06C 001A        add.w    A4@(26), D0                ; tile offset
0x03C880   3340 0002        move.w   D0, A1@(2)                 ; tile
0x03C884   3E2C 0016        move.w   A4@(22), D7
0x03C888   DE42             add.w    D2, D7
0x03C88A   0247 01FF        andi.w   #0x01FF, D7
0x03C88E   3347 0006        move.w   D7, A1@(6)                 ; attribute
0x03C892   5089             addq.l   #8, A1
0x03C894   5343             subq.w   #1, D3
0x03C896   66C6             bne.s    0x03C85E
0x03C898   4E75             rts
; ── sub-sub 0x03C89A (special first-iteration cell) ──
0x03C89A   0C2D 0003 0118   cmpi.b   #3, A5@(280)
0x03C8A0   661A             bne.s    0x03C8BC                   ; no-op unless game state matches
0x03C8A2   3E3C 0A0D        move.w   #0x0A0D, D7                ; pre-seeded attribute
0x03C8A6   0C02 00F8        cmpi.b   #-8, D2
0x03C8AA   6602             bne.s    0x03C8AE
0x03C8AC   5247             addq.w   #1, D7
0x03C8AE   0C6D 003F 013E   cmpi.w   #63, A5@(318)
0x03C8B4   6502             bcs.s    0x03C8B8
0x03C8B6   5E47             addq.w   #7, D7
0x03C8B8   3347 0004        move.w   D7, A1@(4)                 ; WRITE TO A1@(4) — new offset, NOT +2 or +6
0x03C8BC   4E75             rts
; ── alt path 0x03C8BE (A4@(56).b != 0) ──
0x03C8BE   4246             clr.w    D6
0x03C8C0   4247             clr.w    D7
0x03C8C2   6100 FE7E        bsr.w    0x03C742                   ; 1 helper cell pair
0x03C8C6   5089             addq.l   #8, A1
0x03C8C8   4246             clr.w    D6
0x03C8CA   3E3C FFF0        move.w   #-16, D7
0x03C8CE   6100 FE72        bsr.w    0x03C742                   ; 1 helper cell pair
0x03C8D2   5089             addq.l   #8, A1
0x03C8D4   7602             moveq    #2, D3                    ; 3 iterations
0x03C8D6   343C FFF8        move.w   #-8, D2
0x03C8DA   6182             bsr.s    0x03C85E
0x03C8DC   7602             moveq    #2, D3
0x03C8DE   343C FFF0        move.w   #-16, D2
0x03C8E2   6100 FF7A        bsr.w    0x03C85E
0x03C8E6   5588             subq.l   #2, A0
0x03C8E8   7602             moveq    #2, D3
0x03C8EA   4242             clr.w    D2
0x03C8EC   6100 FF70        bsr.w    0x03C85E
0x03C8F0   D2FC 0010        adda.w   #16, A1
0x03C8F4   4E75             rts
```

### H2 — Patch span

`0x03C830..0x03C85D` inclusive = **0x2E bytes (46)**. This patches only
the primary-path entry block. The alt path at `0x03C8BE..0x03C8F5` is
reached only via `bne.w 0x3c8be` at the patched instruction, which
becomes NOP-ed out after the patch. Once the patch is installed,
execution enters the JSR at 0x03C830 and returns via the RTS at
0x03C832+6 — the `bne.w` byte is unreachable.

**However, the hook MUST implement both paths internally** (primary AND
alt), because the path choice is game-state-dependent via `A4@(56).b`.
The hook is not "patching out" the alt path — it is replicating it into
`staged_fg_buffer`.

Present in ROM at `0x03CA30..0x03CA5D`. The downstream body
`0x03C85E..0x03C8F5` (including the private inner sub `0x03C85E`, the
sub-sub `0x03C89A`, and the alt path at `0x03C8BE`) remains in ROM but
is unreachable after the patch.

### H3 — Input register contract

| Reg | Role | Source |
|-----|------|--------|
| A0, A1, A4 | As 0x03C4D2. | Dispatcher. |
| **A4@(56).b** | Path selector (primary vs alt). | Script state. |
| **A5@(280).b** | Read by sub-sub `0x03C89A` for first-iteration special attribute. | Runtime game state. |
| **A5@(318).w** | Read by sub-sub `0x03C89A` for special-attribute adjustment. | Runtime game state. |
| D2, D3, D6, D7 | Clobbered. | — |

### H4 — Write shape

Prefix ×4 (`lsl.w #2, D0`). Two paths:

- **Primary (A4@(56).b == 0):**
  - 2 calls to 0x03C85E with D3=5 (6 iterations each) and D2 ∈ {−8, −24}.
  - Between calls: `subq.l #4, A0` rewinds A0 by 4 bytes.
  - First iteration (D3==5) does NOT read script byte; instead calls
    sub-sub 0x03C89A which may write at `A1@(4)` (only when
    A5@(280).b==3). **This is the only place in the whole dispatcher
    that writes at `A1@(4)`, not `A1@(2)` or `A1@(6)`.** Cody must
    emit the Genesis equivalent to `staged_fg_buffer` at the cell
    whose arcade slot is A1+4 — which corresponds to the **same cell
    as A1+2 + 2 bytes** in the 4-byte-cell mapping (i.e., the attribute
    word of the same cell whose tile word is at A1+2). Cody MUST map
    this write as an **attribute component** into the cell's Genesis
    nametable word.
  - Subsequent iterations (D3 != 5) read script byte via `(A0)+`, with
    zero-byte terminator.
  - **Total primary-path cells: 2 calls × 6 iterations × 2 cells = 24 cells**,
    plus one optional special-attr write on the first iteration of the
    first call (A5@(280).b == 3 gate).
- **Alt (A4@(56).b != 0):**
  - 2 helper cell pairs via 0x03C742 (4 cells).
  - 3 calls to 0x03C85E with D3=2 and varying D2 ∈ {−8, −16, 0}.
  - `subq.l #2, A0` between 2nd and 3rd call (rewind 2 bytes).
  - Each 0x03C85E call: 3 iterations × 2 cells = 6 cells. Three calls = 18 cells.
  - Post-loop A1 += 16.
  - **Total alt-path cells: 4 + 18 = 22 cells.**

### H5 — Output contract

Variable cell count (24 + optional special-attr, or 22). Terminator:
zero byte (primary) and zero byte (alt, same inner sub 0x03C85E).

### H6 — Caller analysis

Single caller: `arcade_pc: 0x03C90C` (`genesis_rom_offset: 0x03CB0C`).
`beqw 0x3c830`. One `opcode_replace` at the handler entry sufficient.

### H7 — Hook name

`genesistan_hook_text_writer_3c830`.

### Differences from 0x03C4D2

- **Dual-path gated on A4@(56).b** (most complex of the set).
- **Reads A5@(280).b and A5@(318).w** for the first-iteration special
  attribute write.
- **Writes at `A1@(4)` on one conditional path** — unique in this
  dispatcher. Cody must map this to the attribute half of the
  corresponding cell in `staged_fg_buffer`.
- Prefix multiplier ×4 (`lsl.w #2`), not ×5.
- Inner sub `0x03C85E` is structurally unique (different first-iteration
  behavior via D3==5 check).
- Uses shared helper `0x03C742` in alt path.
- Variable A0 advance including mid-call rewinds.

---

## H8 — Cross-Handler Consistency Analysis

Fields compared across all 7 handlers (and 0x03C4D2 as reference).

### Fields IDENTICAL across all 7 handlers

- **First instruction:** `movea.l A0@(2), A0` — all 7 handlers begin
  with this exact opcode. Proof: H1 first-line citations for all 7,
  and 0x03C4D2's entry in `docs/design/Andy_text_writer_3c4d2_hook_spec.md` §3.
- **Second instruction:** `move.b A4@(11), D0; ext.w D0` — all 7
  read `A4@(11).b` as the prefix-skip byte, sign-extend to word.
- **Output register: A1** is the destination pointer for all 7; the
  destination is always inside `HW_ADDRESS/PC080SN/FG_TILEMAP`
  (confirmed by common arcade cell format).
- **Write pair slot offsets:** `A1@(2)` for tile, `A1@(6)` for
  attribute, inside the 8-byte iteration record — for all iterations
  of all handlers **except** 0x03C830's sub-sub 0x03C89A which writes
  at `A1@(4)`.
- **Stride:** `addq.l #8, A1` per iteration of every inner loop.
- **Attribute base:** `A4@(22).w`, masked to 0x01FF (9 bits) after
  per-handler D2 bias.
- **Tile base:** `A4@(26).w` — used as either the tile literal
  (0x03C550) or the tile-code base added to script byte or `D1`.
- **Blank-tile sentinel literal:** `#0x0180` at `A1@(2)` — all
  handlers' inner subs use this exact word on terminator.
- **Hook-entry symbol convention:** the existing `0x03C4D2` uses
  `genesistan_hook_text_writer_3c4d2`; this set extends to
  `genesistan_hook_text_writer_3cXXX`.

### Fields that DIFFER — per-handler table

| Field | 0x03C4D2 (ref) | 0x03C550 | 0x03C586 | 0x03C636 | 0x03C6DC | 0x03C75C | 0x03C7A4 | 0x03C830 |
|-------|----------------|----------|----------|----------|----------|----------|----------|----------|
| Prefix multiplier | ×5 | +D0 (×1) | ×3 | ×4 (lsl #2) | ×9 | ×7 | ×6 | ×4 (lsl #2) |
| Terminator sentinel | `D3==0x50 && D4==1` | none | 0xFF | 0xFF | zero byte | 0xFF | 0xFF (only 0x03C7D2 portion) | zero byte |
| Game-state reads | none | none | `A4@(1).b` | `A5@(280).b`, `A5@(318).w` | none | none | none | `A4@(56).b`, `A5@(280).b`, `A5@(318).w` |
| A0 rewinds | 1 (`subq.l #5, A0`) | 0 | 1 (`suba.w #3, A0`) | 0 | 0 | 0 | 0 | 2 (`subq.l #4, A0`; `subq.l #2, A0` in alt path) |
| Cells written per call | 10 or 20 (paths) | 10 | 20 or 18 | 6 or 8 | 22 | 26 | 26 | 22–24 |
| Post-loop A1 advance | +0x50 | +0x48 | +0x60 or +0x68 | +0x20 or +0x30 | +0x60 | +0x78 | 0 | +0x10 or 0 |
| Inner-sub helper shared? | private (0x03C516) | none | private (0x03C606) + shared (0x03C742) | private (0x03C6AC) + shared (0x03C742) | private (0x03C70A) | shared (0x03C742, 0x03C7D2) | private (0x03C804) + shared (0x03C7D2) | private (0x03C85E, 0x03C89A) + shared (0x03C742) |
| Writes at `A1@(4)`? | NO | NO | NO | NO | NO | NO | NO | YES (one conditional write per call in primary path) |
| Tile source | script byte + A4@(26) + A4@(24) | A4@(26) literal | script byte + A4@(22) or sentinel | script byte + A4@(26) or sentinel | script byte + D1 + A4@(26) or zero-terminator | script byte + A4@(26) or sentinel | synthesized D3→D0 (0x03C804) and script-byte (0x03C7D2) | script byte + A4@(26) or zero-terminator, plus 0x0A0D special for first iter |
| Attribute source | A4@(22) + D2 (0, −16) | A4@(22) + D4 (0,16,32,48,64) | A4@(22) + D2 (0, −16) | A4@(22) + D2 (0, −16) | A4@(22) + D2 (script byte) | A4@(22) + D2 (−8, 0, −16, −8) | A4@(22) + D2 (0, −16, −8) | A4@(22) + D2 (−8, −24) primary; A4@(22) + D2 (0, −8, −16) alt |

### Shared-helper viability assessment

A single internal helper inside Cody's per-handler hooks that accepts
the per-handler parameters (prefix multiplier, inner-sub selector,
iteration counts, D2 schedule, A0 rewind schedule, terminator kind,
post-loop A1 adjust, game-state read list, special-attribute path) is
viable **as a library-style helper internal to the per-handler hook
file**, but NOT viable as a single-hook substitute (the concern from
`docs/design/Andy_dispatcher_map_analysis.md` §6). Each handler's
parameter set is unique; a shared helper simply factors out the common
`staged_fg_buffer[row*64+col] = LUT[tile] | LUT[attr]` + `bset row,
fg_row_dirty` write step (which is 4 instructions at most). Cody MAY
implement such a helper; this spec does not require it.

Conclusion: **shared helper viable at the write-step granularity only**
(factor out the LUT-translate-and-store step). NOT viable at the
handler-level.

---

## Set Summary

- **Total handlers specced: 7 of 7.** All complete.
- **STOPs triggered: NONE.** All entry points confirmed in disasm; all
  `genesis_rom_offset` values resolved via address_map.json; no span
  overlap; no cross-space arithmetic; no handler required the default
  path 0x03C950 for correctness.
- **Handlers with output contract differences from 0x03C4D2:**
  - `0x03C550` — attribute-first ordering, single glyph byte shared across iterations.
  - `0x03C586` — dual path via `A4@(1).b == 6`; uses shared helper 0x03C742.
  - `0x03C636` — game-state branches on A5@(280)/A5@(318) affect prelude and post-advance.
  - `0x03C6DC` — zero-byte terminator; D1-biased tile; `jsr helper_5b512_rts` inside inner sub.
  - `0x03C75C` — 4-call inner-sub chain with varied (D2, D3) tuples; uses shared 0x03C742 and 0x03C7D2.
  - `0x03C7A4` — mixed synthesized (0x03C804) + script-byte (0x03C7D2) inner subs; zero post-A1 adjust.
  - `0x03C830` — dual path via `A4@(56).b`; writes at `A1@(4)` on a
    game-state-conditional first iteration; reads A5@(280) and A5@(318)
    for the special-attribute write.
- **Implementation readiness: READY FOR CODY.** Each handler has an
  independent H1–H7 record, cross-handler consistency is mapped in H8,
  and each hook has a well-defined entry/exit contract. Cody implements
  7 new hook functions (one per handler), adds 7 new `opcode_replace`
  entries in `specs/rastan_direct_remap.json`, and bumps
  `opcode_replace_count` from 47 to 54.

Per-handler `opcode_replace` template (Cody fills in `original_bytes`
from `build/regions/maincpu.bin` at each `arcade_pc` and sizes the NOP
padding to the patch-span length):

```jsonc
{
  "arcade_pc": "0x03CXXXX",
  "original_bytes": "<hex from maincpu.bin[arcade_pc : arcade_pc+span]>",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_text_writer_3cXXX}4E75<NOPs to fill span>",
  "note": "Route text-writer handler (script opcode 0xNN) to Genesis FG staging hook; prevent direct C-window writes."
}
```

Patch-span summary (bytes, arcade entry, genesis entry):

| arcade_pc | genesis_rom_offset | bytes | Required symbol |
|-----------|--------------------|-------|-----------------|
| 0x03C550 | 0x03C750 | 0x36 (54) | genesistan_hook_text_writer_3c550 |
| 0x03C586 | 0x03C786 | 0x80 (128) | genesistan_hook_text_writer_3c586 |
| 0x03C636 | 0x03C836 | 0x76 (118) | genesistan_hook_text_writer_3c636 |
| 0x03C6DC | 0x03C8DC | 0x2E (46) | genesistan_hook_text_writer_3c6dc |
| 0x03C75C | 0x03C95C | 0x48 (72) | genesistan_hook_text_writer_3c75c |
| 0x03C7A4 | 0x03C9A4 | 0x2E (46) | genesistan_hook_text_writer_3c7a4 |
| 0x03C830 | 0x03CA30 | 0x2E (46) | genesistan_hook_text_writer_3c830 |

Symbol additions required in `specs/rastan_direct_remap.json`
`required_symbols` list: all 7 hook names above.

`opcode_replace_count` change: **47 → 54**. The patcher invariant in
`tools/translation/postpatch_startup_rom.py` (previously bumped to 47
per AGENTS_LOG) will need to be bumped to 54 with corresponding
`total_genesis_bytes_covered` updated to the new ROM size. This is a
mechanical follow-up analogous to the prior `46 → 47` bump.

---

## Open Questions

1. **Shared inner subs 0x03C742 and 0x03C7D2 reachability after all 7
   patches.** Both helpers are called only from sibling handlers within
   this dispatcher. Once all 7 handlers are patched, the helpers
   become dead code. Recommend NOT patching them (they are dead and
   harmless); no `opcode_replace` entry needed. Confirmation by grep
   after Cody's patches is straightforward.
2. **Default path 0x03C950.** Explicitly out of scope of this spec
   (per prompt). The BlastEm crash in Build 0033 may or may not also
   originate from the default path. After the 7 new handler hooks are
   installed, a new Build 0034 trace will identify whether
   `fg_cwindow_live` writes persist — if they do, the default path
   handles the remaining opcodes.
3. **Row/col wrap semantics when a run spans row boundaries.** The
   0x03C4D2 hook (`main_68k.s:681–691`) implements col-wrap with row
   increment. The sibling hooks must use the same wrap pattern.
   Consider Cody refactoring shared wrap/store logic into a private
   helper internal to `main_68k.s`, but this is an implementation
   detail — not a spec requirement.

---

## Implementation Status — Build 0034

- Implemented handlers:
  - `0x03C550` → `genesistan_hook_text_writer_3c550`
  - `0x03C586` → `genesistan_hook_text_writer_3c586`
  - `0x03C636` → `genesistan_hook_text_writer_3c636`
  - `0x03C6DC` → `genesistan_hook_text_writer_3c6dc`
  - `0x03C75C` → `genesistan_hook_text_writer_3c75c`
  - `0x03C7A4` → `genesistan_hook_text_writer_3c7a4`
  - `0x03C830` → `genesistan_hook_text_writer_3c830`
- Spec/source fit: YES — all 7 handler entry spans and caller sites matched the source/disassembly locations defined in this spec.
- Anomalies observed after implementation:
  - Build 0034 completes, but `fg_cwindow_live` remains non-zero (`count=8`) and still reports writes at `HW_ADDRESS/PC080SN/FG_TILEMAP` (`first_addr=C09EA0`, `last_addr=C09EA6`) in the 30s trace summary.
  - This indicates additional remaining writer path behavior beyond the implemented 7-handler set still contributes to live C-window writes in runtime trace evidence.
- Tracking artifact pointer:
  - `docs/design/handler_translation_coverage.md`
