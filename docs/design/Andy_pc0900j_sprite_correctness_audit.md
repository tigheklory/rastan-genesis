# Andy — PC0900J Sprite Correctness Audit

## 1. Executive Summary

This audit traces the full sprite pipeline from PC090OJ arcade sprite RAM entries through
the Genesis VDP SAT. One root cause is identified: the assembly sprite renderer
(`genesistan_render_sprites_vdp_asm` in `startup_trampoline.s`) constructs VDP DMA write
commands with a defective address encoding that zeroes bits 14–15 of the VRAM destination
address. This causes all sprite tile DMA transfers to target VRAM addresses 0x0000–0x0B80
(tiles 0–87) instead of the intended 0x8000–0x8B80 (tiles 1024–1115). The SAT entries
simultaneously reference tiles 1024–1115, which receive no tile data from the DMA. The
result is that all sprites render as transparent or blank 16×16 regions. All other
translation fields — attribute bits, palette, flip, priority, size, coordinate bias, and
SAT link chain — are correct.

The required correction is a single two-instruction replacement in `.Lspr_dma_tile` inside
`startup_trampoline.s` to correctly extract bits 14–15 of the VRAM destination address
before constructing the VDP DMA command longword.

---

## 2. PC090OJ Sprite Format (Arcade)

**Answer: PC090OJ sprite format defined: YES**

### 2.1 Entry Size and Word Layout

Each sprite entry is **8 bytes (4 words)**, big-endian, written to workram contiguously.

| Byte offset | Word | Field | Content |
|-------------|------|-------|---------|
| +0, +1 | word0 | attr/flags | bit15=flipy, bit14=flipx, bits3:0=palette sub-index |
| +2, +3 | word1 | y_raw | Raw Y coordinate. Value 0x0180 = off-screen sentinel |
| +4, +5 | word2 | tile code | bits13:0 = arcade cell index (`& 0x3FFF`) |
| +6, +7 | word3 | x_raw | Raw X coordinate |

Source evidence: `main.c` lines 1974–1978 (authoritative entry layout comment),
confirmed by arcade disassembly sprite builder at 0x3C902 (writes word0=attr, word1=Y,
word2=code via subroutine 0x3CA12, word3=X to A1 destination buffer).

### 2.2 Sprite Format Source

The PC090OJ arcade ROM (`pc090oj.bin`, 524288 bytes) stores 4096 cells, each 128 bytes.
Each cell is a 16×16 pixel object composed of 16 rows × 8 bytes per row, packed 4bpp
nibble format. The build step `preconvert_pc090oj_tiles.py` converts each cell from the
raw row-major layout into four Genesis 8×8 tiles in column-major order (TL, BL, TR, BR),
writing the result back to `build/regions/pc090oj.bin` before the ROM is assembled. The
in-ROM symbol `rastan_pc090oj` therefore already contains Genesis-compatible tile layout.

### 2.3 Sprite List Structure

- **Two descriptor blocks** in arcade workram (base: `genesistan_arcade_workram_words`):
  - Block A: offset 0x11B2 from workram base, 18 entries (used for title/logo sprites)
  - Block B: offset 0x0170 from workram base, 4 entries (secondary sprites)
- **Total**: 22 entries maximum per frame
- **Termination**: fixed-count scan; per-entry validity checks gate SAT output
- **Validity rules**: skip if y_raw == 0x0180 (sentinel); skip if all four words are zero;
  skip if tile code == 0 after masking
- **No linked-list within arcade entries**: sequential contiguous array, stride = 8 bytes

Source evidence: `startup_trampoline.s` lines 224–238 (block A and B iteration), `main.c`
lines 1963–1969 (sprite_blocks[] table), arcade disassembly 0x41F5E–0x41F8C (block copy
loop writing from arcade workram to legacy D-window staging buffers, confirming entry size
and offsets).

---

## 3. Genesis VDP SAT Format

**Answer: Genesis SAT format defined: YES**

Each SAT entry is **8 bytes (4 words)**:

| Word | Bits | Field |
|------|------|-------|
| Word 0 | 9:0 | Y position (screen Y + 0x80 for 128-pixel Genesis border) |
| Word 1 | 11:8 | Sprite size: bits 11:10 = V tiles–1 (0=1, 1=2, 2=3, 3=4); bits 9:8 = H tiles–1 |
| Word 1 | 6:0 | Link field: index of next SAT entry; 0 = end of chain |
| Word 2 | 15 | Priority (1 = above planes) |
| Word 2 | 14:13 | Palette line (0–3) |
| Word 2 | 12 | Vertical flip |
| Word 2 | 11 | Horizontal flip |
| Word 2 | 10:0 | VRAM tile index (first of the 4 tiles forming the 2×2 sprite) |
| Word 3 | 9:0 | X position (screen X + 0x80 for 128-pixel Genesis border) |

The SAT base is at VRAM 0xF800, set by VDP register 5 value 0x7C (= 0xF800 / 512).
Confirmed by `main.c` line 2189 (`*ctrl = 0x857C`) and `main.c` line 1447
(`VDP_setSpriteListAddress(TITLE_SAT_VRAM_ADDR)` where TITLE_SAT_VRAM_ADDR = 0xF800).
The SAT write command used in the asm path, 0x78000003, correctly addresses VRAM 0xF800
(decoded: `(0x7800 & 0x3FFF) | ((0x0003 & 3) << 14)` = 0x3800 | 0xC000 = 0xF800).

---

## 4. Current Translation Path

**Answer: Translation path traced: YES**

### 4.1 Active Call Chain

All arcade sprite call sites are patched via `startup_title_remap.json`
`shift_replacements` entries to `JSR genesistan_render_sprites_vdp_bridge`. The active
patch sites include arcade addresses 0x03A20E, 0x03A264, 0x03A640, 0x03A6C4, 0x03A818,
0x03A820, 0x03A854, 0x03A8E4, 0x03A9C6, 0x03A9D4, 0x03B8E8, 0x03B8F0, 0x041DAE,
0x041F5E, and 0x045DFA. The legacy C path
(`genesistan_hook_frontend_sprite_sat_refresh` → `genesistan_render_sprites_vdp`) is
declared `__attribute__((unused))` and is not referenced from any active call site as of
Build 171.

### 4.2 Assembly Renderer Structure (`genesistan_render_sprites_vdp_asm`)

Located in `startup_trampoline.s` lines 211–263. Two-pass design:

**Pass 1 — DMA tile upload** (`.Lspr_dma_tile`, lines 265–338):
- Iterates 18 Block-A entries then 4 Block-B entries
- Reads y_raw from word1 (+2); skips if == 0x0180
- Reads tile code from word2 (+4); masks to 0x0FFF (12-bit index into `rastan_pc090oj`)
- Skips if all-zero entry (both longwords zero)
- Computes DMA source: `rastan_pc090oj + (code & 0x0FFF) * 128`
- DMA length: 64 words (128 bytes = 4 Genesis tiles)
- Intended VRAM destination: `(SPRITE_TILE_BASE + slot*4) * 32` where SPRITE_TILE_BASE = 1024
- Increments D5 (slot index) per accepted entry

**Pass 2 — SAT write** (`.Lspr_write_sat`, lines 340–424):
- Same iteration order and same validity filters as Pass 1
- Writes 4 words directly to VDP data port (A4 = 0xC00000)
- VDP auto-increment = 2 (set at line 218)
- SAT starts at VRAM 0xF800 (command issued at line 243)

### 4.3 Staging Buffer

No WRAM staging buffer is used in the active ASM path. SAT words are written directly to
VDP data port in real time. The legacy C path used SGDK's `vdpSpriteCache` WRAM buffer
with `VDP_setSpriteFull()` / `VDP_updateSprites()`, but that path is inactive.

### 4.4 Tile Pre-conversion

`preconvert_pc090oj_tiles.py` (invoked by `apps/rastan/Makefile` before the ROM build)
converts each 128-byte raw PC090OJ cell into 4 Genesis tiles (32 bytes each) in
column-major order (TL, BL, TR, BR), overwriting `build/regions/pc090oj.bin`. The
in-ROM symbol `rastan_pc090oj` includes this converted data at build time.

---

## 5. Tile Index Verification

**Answer: Sprite tile index mapping correct: NO**

### 5.1 Intended VRAM Allocation

`SPRITE_TILE_BASE = 1024` (defined in `startup_trampoline.s` line 42).

For slot S (0-indexed): VRAM tile index = 1024 + S×4; VRAM byte address = (1024 + S×4) × 32.

For 22 maximum sprites: tile indices 1024–1108, byte range 0x8000–0x8A80.

The SAT word2 tile field applies mask 0x07FF (`andi.w #0x07FF, %d0` at trampoline line 410).
1108 = 0x0454, within the 11-bit mask range. No truncation occurs in the SAT field itself.

### 5.2 DMA Address Encoding Bug

The VDP DMA write command requires encoding the VRAM destination address in a 32-bit
control longword using this formula:

```
cmd = ((addr & 0x3FFF) << 16) | ((addr >> 14) & 0x3) | 0x40000000 | DMA_TRIGGER_BIT
```

The field `(addr >> 14) & 0x3` encodes bits 14–15 of the address into bits 1–0 of the
command longword.

The asm at `startup_trampoline.s` lines 330–333 implements this extraction as:

```asm
move.l  %d0, %d2
swap    %d2
andi.w  #0x0003, %d2
```

For any VRAM address in the range 0x0000–0xFFFF (all values that fit in 16 bits, including
all sprite tile addresses 0x8000–0x8B80): `d0` as a 32-bit value has its upper 16 bits
cleared (zero). The `swap` instruction exchanges upper and lower 16-bit halves. After
`swap`, bits 1–0 of the lower word (which were the upper 16-bit half, = 0x0000) are
captured by `andi.w #0x0003, %d2`, yielding `d2 = 0` for all sprite tile addresses.

The correct extraction for VRAM address 0x8000 is `(0x8000 >> 14) & 3 = 2`. The asm
produces 0. The resulting command is `0x40000080` instead of the correct `0x40000082`.

### 5.3 Consequence Per Slot

The VDP interprets the incorrect command as targeting VRAM address `addr & 0x3FFF` instead
of `addr`. For the sprite tile range (0x8000–0x8B80), this strips bit 15, targeting
0x0000–0x0B80 instead:

| Slot | Intended VRAM | Actual DMA target | SAT tile index |
|------|--------------|-------------------|----------------|
| 0 | 0x8000 (tile 1024) | 0x0000 (tile 0) | 1024 |
| 1 | 0x8080 (tile 1028) | 0x0080 (tile 4) | 1028 |
| ... | ... | ... | ... |
| 21 | 0x8A80 (tile 1108) | 0x0A80 (tile 84) | 1108 |

The DMA writes 128 bytes of sprite pixel data per slot to VRAM tiles 0–84 (in increments
of 4 tiles). The SAT entries reference VRAM tiles 1024–1108. These are disjoint. VRAM tiles
1024–1108 (0x8000–0x8B80) are never populated by the sprite DMA and remain at their
initialized state (zeroed or previous content).

---

## 6. Attribute Mapping Verification

**Answer: Attribute mapping correct: YES**

### 6.1 Palette Bits

Computation in `.Lspr_write_sat` (trampoline lines 390–399):

```
color = (word0 & 0x000F) | ((sprite_ctrl & 0x00E0) >> 1)
palette_line = (color >> 4) & 3
```

Placement in SAT word2: `lsl.w #8, d1; lsl.w #5, d1` = shift left by 13.
Genesis SAT word2 bits 14:13 = palette line. `palette_line << 13` is correct.

### 6.2 Flip Bits

VFlip: word0 bit 15 (`andi.w #0x8000, d2`), shifted right 3 (`lsr.w #3, d2`) → bit 12.
Genesis SAT word2 bit 12 = VFlip. Correct.

HFlip: word0 bit 14 (`andi.w #0x4000, d3`), shifted right 3 (`lsr.w #3, d3`) → bit 11.
Genesis SAT word2 bit 11 = HFlip. Correct.

### 6.3 Priority Bit

`ori.w #0x8000, d1` sets bit 15 of SAT word2 unconditionally. Genesis SAT word2 bit 15
= priority. Sprites always rendered above background planes. Correct.

### 6.4 Size Encoding

SAT word1 constant: `ori.w #0x0500, d0`.
Bits 11:8 = 0x05 = 0b0101: V=01 (2 tiles, 16 pixels), H=01 (2 tiles, 16 pixels).
PC090OJ cells are 16×16 pixels. Genesis 2×2 sprite size is 16×16 pixels. Correct.

---

## 7. Position Mapping Verification

**Answer: Position mapping correct: YES**

### 7.1 Y Coordinate

```asm
move.w 2(%a0), %d0      ; y_raw from word1
andi.w #0x01FF, %d0     ; mask to 9 bits
addi.w #0x0080, %d0     ; add Genesis 128-pixel border offset
move.w %d0, (%a4)       ; SAT word0
```

Genesis sprite Y = 0x80 places sprite at screen top. Arcade Y = 0 is screen top. Adding
0x80 correctly maps arcade Y=0 to Genesis SAT Y=0x80. The 9-bit mask (0x01FF) handles
values 0–511; values in the range 0–255 map to visible screen positions after adding 0x80.
Correct for on-screen sprites.

### 7.2 X Coordinate

Identical bias: `andi.w #0x01FF, d0; addi.w #0x0080, d0`. Genesis sprite X = 0x80 places
sprite at screen left. Arcade X = 0 is screen left. Addition of 0x80 is correct.

### 7.3 Coordinate Origin

The arcade uses (0,0) as the top-left of the visible 320×224 display area. Genesis SAT
requires adding 0x80 to both axes to account for the 128-pixel off-screen border. The asm
applies this correctly to both axes.

---

## 8. Sprite Linking / Order Verification

**Answer: Sprite linking/order correct: YES**

### 8.1 Link Chain Construction

The two-pass design computes `d4 = total_visible` in Pass 1, then uses it in Pass 2:

```asm
d0 = d5 + 1               ; candidate next-entry index
if d0 >= d4: link = 0     ; last entry, terminate chain
else: d0 & 0x007F | 0x0500  ; size(2x2) | link=next
```

D5 is incremented only for entries that pass the same visibility filter used in Pass 1.
Since both passes use identical filters and iterate in the same order, d5 values in Pass 2
are synchronised with d5 values from Pass 1. The total valid count (d4) is computed before
Pass 2 begins. This produces a correct sequential link chain from entry 0 to entry d4–1,
with the last entry having link=0.

### 8.2 Sprite Order

Block A (18 entries) is processed before Block B (4 entries) in both passes, maintaining
consistent rendering order. This matches the arcade's Block-A priority expectations
(title/logo sprites in Block A, secondary sprites in Block B).

---

## 9. Root Cause

**One root cause identified: VDP DMA command address encoding drops bits 14–15 of the VRAM
destination address.**

File: `/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_trampoline.s`

Function: `.Lspr_dma_tile` (subroutine within `genesistan_render_sprites_vdp_asm`)

Lines 330–333 (the upper-2-bit extraction):

```asm
move.l  %d0, %d2
swap    %d2
andi.w  #0x0003, %d2
```

For all VRAM addresses in 0x0000–0xFFFF (16-bit range), `d0` as a 32-bit value has its
upper 16 bits zero. After `swap`, the lower word of `d2` is 0x0000 (the original upper 16
bits). `andi.w #0x0003, %d2` yields 0 for all such addresses.

The correct extraction of bits 14–15 from a 16-bit VRAM address requires logical right
shift by 14, not a `swap`:

```asm
move.l  %d0, %d2
lsr.l   #14, %d2
andi.w  #0x0003, %d2
```

This produces `d2 = (vram_addr >> 14) & 3 = 2` for all sprite tile addresses
(0x8000–0x8B80), which is the correct value to place in bits 1–0 of the VDP DMA command
longword.

---

## 10. Required Correction

**Correction type: Tile index correction (DMA address)**

**Scope**: Two-instruction replacement in `startup_trampoline.s`, subroutine `.Lspr_dma_tile`.

**Current (buggy) code** at lines 330–332:
```asm
    move.l  %d0, %d2
    swap    %d2
    andi.w  #0x0003, %d2
```

**Replacement**:
```asm
    move.l  %d0, %d2
    lsr.l   #14, %d2
    andi.w  #0x0003, %d2
```

**Effect**: For VRAM address 0x8000 (slot 0): `d2` changes from 0 to 2. The VDP DMA
command changes from `0x40000080` to `0x40000082`. The DMA correctly targets VRAM 0x8000
(tile 1024). Each subsequent slot follows the same pattern: all DMA transfers land in
VRAM 0x8000–0x8A80, which is the range the SAT entries already reference via tile indices
1024–1108.

**No other changes are required.** The SAT word construction, link chain, attribute bits,
palette, flip, priority, size encoding, and coordinate bias are all correct.

---

## 11. Final Verdict

| Task | Status |
|------|--------|
| PC0900J sprite format defined | YES |
| Arcade sprite write mechanism identified | YES |
| Genesis SAT format defined | YES |
| Translation path traced | YES |
| Sprite tile index mapping correct | NO — DMA writes to wrong VRAM address |
| Attribute mapping correct | YES |
| Position mapping correct | YES |
| Sprite linking/order correct | YES |
| Root cause identified | YES — DMA address upper-bit extraction bug in `.Lspr_dma_tile` |
| Single correction path defined | YES — replace `swap d2` with `lsr.l #14, d2` in trampoline |

**Visual symptoms produced by the root cause:**
1. All sprites render as transparent/blank 16×16 regions (VRAM tiles 1024+ contain no sprite pixel data).
2. Nametable tiles 0–84 are overwritten with sprite pixel data each frame, causing visual corruption of background plane A and plane B content at tile positions 0–84.
3. Sprite screen positions, link counts, palette assignments, and flip states are all faithfully translated — only the tile content is wrong.

**No implementation was performed. All conclusions are based solely on source code evidence in `startup_trampoline.s`, `main.c`, `startup_bridge.c`, `preconvert_pc090oj_tiles.py`, `startup_title_remap.json`, and the arcade disassembly.**
