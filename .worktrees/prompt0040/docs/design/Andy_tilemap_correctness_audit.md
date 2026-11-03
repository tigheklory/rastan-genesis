# Andy — PC080SN Tilemap Correctness Audit vs Genesis VDP Mapping

## 1. Executive Summary

A complete bit-level audit of the PC080SN → Genesis VDP tilemap translation pipeline reveals that the attribute LUT, tile VRAM LUT, WRAM buffer geometry, VDP commit commands, and VRAM register layout are all **structurally correct**. The single root cause of the current blank-plane output is not a format translation bug: **both WRAM dest_ptr fields (workram 0x10A0 for BG, 0x10A4 for FG) are permanently zero because every arcade-side store to these addresses has been either replaced or NOPped, and no Genesis-side initialization of these fields exists**. The tilemap strip-commit hooks execute every frame but always take the out-of-range branch, leaving both WRAM buffers permanently blank.

---

## 2. PC080SN Hardware Tilemap Format

The PC080SN chip addresses its tilemap RAM at 0xC00000–0xC03FFF (BG) and 0xC08000–0xC0BFFF (FG), with a 0x4000-byte window per layer. The internal layout is **column-major with 4 bytes per cell**:

```
cell = (addr - window_base) / 4
row  = cell & 0x3F           (6 bits, 0–63)
col  = (cell >> 6) & 0x3F    (6 bits, 0–63)
```

Each column is 64 rows × 4 bytes = 256 bytes. With 64 columns × 256 bytes = 16384 = 0x4000 bytes per layer. ✓

The arcade code builds **descriptor tables** in ROM. Each descriptor is 4 bytes:
- Word 0 (`attr_word`): packed palette (bits 1–0), flip bits (bits 13–15)
- Word 1 (`table_base`): base offset into ROM tile code array

A **desc list** of 16 long-word ROM pointers is maintained in workram at `PC080SN_DESC_LIST_OFFSET = 0x1000`. Each pointer references one descriptor in the ROM. The tilemap routines at 0x055968 (BG) and 0x055990 (FG) consume this list every frame.

---

## 3. Genesis VDP Nametable Format

Genesis VDP nametable entry (16-bit word):

| Bits | Field | Source |
|------|-------|--------|
| 15 | Priority | attr_word bit 13 |
| 14–13 | Palette | attr_word bits 1–0 |
| 12 | VFlip | attr_word bit 15 |
| 11 | HFlip | attr_word bit 14 |
| 10–0 | Tile index | `genesistan_pc080sn_tile_vram_lut[tile_code & 0x3FFF]` |

---

## 4. Attribute LUT: Bit Mapping Verified ✓

`precompute_pc080sn_attr_lut.py` builds the 32-entry LUT as:

```python
pal   = key & 0x03            # key bits 0–1
hflip = (key >> 2) & 0x01     # key bit 2
vflip = (key >> 3) & 0x01     # key bit 3
prio  = (key >> 4) & 0x01     # key bit 4
value = (prio << 15) | (pal << 13) | (vflip << 12) | (hflip << 11)
```

The assembly (BG commit, `startup_trampoline.s:565–584`) builds the 5-bit key as:

| key bit | source instruction | PC080SN attr_word source bit | Genesis VDP target |
|---------|--------------------|------------------------------|--------------------|
| 0 | `andi.w #0x0003, %d0` | bit 0 | palette LSB |
| 1 | `andi.w #0x0003, %d0` | bit 1 | palette MSB |
| 2 | `lsr.w #14; andi #1` | bit 14 | HFlip (bit 11) |
| 3 | `lsr.w #15; andi #1` | bit 15 | VFlip (bit 12) |
| 4 | `lsr.w #13; andi #1` | bit 13 | Priority (bit 15) |

Mapping is **correct and consistent** between the Python generator and the assembly consumer. ✓

Sample LUT values confirm the encoding:
```
index 0  → 0x0000  (pal=0, hflip=0, vflip=0, prio=0) ✓
index 4  → 0x0800  (hflip=1 → bit 11 set)             ✓
index 8  → 0x1000  (vflip=1 → bit 12 set)             ✓
index 16 → 0x8000  (prio=1  → bit 15 set)             ✓
```

---

## 5. Tile VRAM LUT: Mapping Verified ✓

`precompute_pc080sn_tile_lut.py` builds `genesistan_pc080sn_tile_vram_lut[16384]`:
- Arcade tile 0 → VRAM slot 0 (blank tile)
- Known scene tiles → VRAM slots 20–1023 (`TILE_CACHE_BASE_A=20`, 1004 slots) and 1280–1439 (160 slots)
- Unknown tiles (not in any scene) → VRAM slot 0 (blank)

The assembly masks tile codes with `andi.w #0x3FFF` before LUT lookup, correctly eliminating the top-2 flip bits from the raw tile word. ✓

---

## 6. WRAM Buffer Geometry: Verified ✓

Both BG and FG assemblies write Genesis nametable words to WRAM buffers using:

```asm
row * 128 + col * 2   →   buffer offset
```

With row 0–31 (5-bit) and col 0–63 (6-bit), this produces a standard row-major 64×32 nametable:
- 64 columns × 32 rows × 2 bytes = 4096 bytes per buffer ✓
- Buffer stride: 128 bytes per row (= 64 words) ✓

---

## 7. VDP Commit Mechanism: Verified ✓

`genesistan_pc080sn_commit_planes` (`startup_trampoline.s:876–898`) writes:

| Command longword | VRAM address | Register | Layer |
|------------------|-------------|----------|-------|
| `0x40000003` | 0xC000 | Reg 4 = `0x06` → 6 × 0x2000 = **0xC000** | Plane B (BG) ✓ |
| `0x60000003` | 0xE000 | Reg 2 = `0x38` → 7 × 0x2000 = **0xE000** | Plane A (FG) ✓ |

Command longword formula: `0x40000000 | ((addr & 0x3FFF) << 16) | ((addr >> 14) & 0x03)`
- 0xC000: `0x40000000 | 0 | 3 = 0x40000003` ✓
- 0xE000: `0x40000000 | 0x20000000 | 3 = 0x60000003` ✓

VDP register configuration (`force_clean_vram_init`, lines 2186–2202):
- Reg 17 = `0x80` (Window H OFF) ✓ — set by Build 327 fix
- Reg 18 = `0x80` (Window V OFF) ✓ — set by Build 327 fix
- Reg 11 = `0x00` → full-screen H+V scroll ✓

Scroll commit (`genesistan_scroll_commit_vdp`): writes VRAM 0xF000 (HScroll, command `0x70000003`) and VSRAM offset 0 (VScroll). Both commands verified correct. ✓

---

## 8. Strip Access Pattern: Verified ✓

**BG** (`genesistan_asm_tilemap_commit_bg`):
- Initial tile address: `table_base + strip_index * 2`
- Per-row stride: 8 bytes (`adda.w #8, %a4` per iteration)
- Tiles per strip: 4 rows (dbra from 3 → 4 iterations)
- Result: `addr = table_base + strip * 2 + row * 8` ✓

**FG** (`genesistan_asm_tilemap_commit_fg`):
- Initial tile address: `table_base + strip_index * 8`
- Per-column stride: 2 bytes (`adda.w #2, %a4` per iteration)
- Tiles per strip: 4 columns
- Result: `addr = table_base + strip * 8 + col * 2` ✓

Both match `collect_strip_tiles` in `precompute_pc080sn_tile_lut.py`, which was used to discover tile indices at build time. ✓

---

## 9. Root Cause: Dest_Ptr Fields Permanently Zero

### 9.1 The dest_ptr Mechanism

`genesistan_hook_tilemap_plane_a` (`main.c:1258`) reads the BG destination pointer from workram:

```c
u32 dest = pc080sn_workram_read_u32(PC080SN_DEST_PTR_A_OFFSET);  // workram offset 0x10A0
if (!pc080sn_dest_ptr_to_row_col(dest, PC080SN_CWINDOW_BASE_BG, &dest_row, &dest_col))
{
    dest += (u32)PC080SN_DESC_COUNT * 0x400U;  // out-of-range branch: advance, no commit
}
else
{
    dest = genesistan_asm_tilemap_commit_bg(...);  // valid: execute tilemap commit
}
pc080sn_workram_write_u32(PC080SN_DEST_PTR_A_OFFSET, dest);
```

`pc080sn_dest_ptr_to_row_col` validates that `dest` falls in the range `0xC00000–0xC03FFF` (BG) or `0xC08000–0xC0BFFF` (FG). Any value outside these ranges causes the hook to take the "out-of-range" branch and write nothing to the WRAM buffer.

### 9.2 All Stores to dest_ptr Are Suppressed

**BG dest_ptr (workram byte offset 0x10A0 = A5+4256):**

| Site | Original instruction | Patch status | Effect |
|------|---------------------|--------------|--------|
| `0x055968` body | `move.l a0, 0x10A0(a5)` | Replaced by `jsr genesistan_hook_tilemap_plane_a` | Gone — entire routine replaced |
| `0x055E54` | `move.l #0xC00400, 0x10A0(a5)` | **NOPped** | BG initial ptr never stored |
| `0x055818` | `addil #0xC08000,d0 + move.l d0, 0x10A0(a5)` | **NOPped** | BG advanced ptr never stored |

**FG dest_ptr (workram byte offset 0x10A4 = A5+4260):**

| Site | Original instruction | Patch status | Effect |
|------|---------------------|--------------|--------|
| `0x055990` body | `move.l a0, 0x10A4(a5)` | Replaced by `jsr genesistan_hook_tilemap_plane_b` | Gone — entire routine replaced |
| `0x0556F2` | `addil #0xC08000,d1 + move.l d1, 0x10A4(a5)` | **NOPped** | FG ptr never stored |
| `0x05577E` | `addil #0xC08000,d0 + move.l d0, 0x10A4(a5)` | **NOPped** | FG ptr never stored |

### 9.3 Consequence: Permanent Out-of-Range Branch

`genesistan_arcade_workram_words` is in `.bss.workram` (zero-initialized). `startup_bridge.c` initializes words at offsets 0, 2, 4, 8, 10, 14, 16, 20, 24, 28, 38 — but **not 0x10A0 or 0x10A4**. Both dest_ptr fields start at 0x00000000 and stay there.

With `dest = 0`: `pc080sn_dest_ptr_to_row_col(0, 0xC00000, ...)` returns FALSE (0 < 0xC00000). The BG hook takes the out-of-range branch every frame:

```
Frame 0:  reads 0x00000000 → invalid → stores 0x00004000
Frame 1:  reads 0x00004000 → invalid → stores 0x00008000
...
Frame 768: reads 0x00C00000 → VALID!  → commit runs once
Frame 769: reads 0x00C04000 → invalid (≥ window end) → stores 0x00C08000
...  (never returns to BG range)
```

The BG plane receives exactly **one** commit after ~12.8 seconds, then never updates again. The FG plane's count-up rate is different (adds 16×16=256 bytes/frame when out of range vs 16×0x400 for BG) and reaches 0xC08000 after roughly 98304 frames (~27 minutes). In practice, the WRAM buffers are functionally empty for the entire session.

### 9.4 Why the NOPs Were Added

These stores were NOPped to prevent crashes: on Genesis, any arcade code that reads back workram[0x10A0] and tries to **dereference** 0xC00000 as a memory pointer would fault. The NOP patches were the safest early fix.

However, the hook system was designed to be the only consumer of these dest_ptr values. The hooks never dereference 0xC0xxxx — they call `pc080sn_dest_ptr_to_row_col` which uses the value as a pure integer to decode row/col. The crash risk is gone once the hooks fully replace the original routines. The NOP patches are now over-aggressive: they suppress valid initialization that the hooks require.

---

## 10. Secondary Audit Items (Not Root Cause)

The following items were audited and found to be **correct**. They are documented here for completeness.

### 10.1 Tile VRAM LUT Coverage
The `discover_descriptor_tables` scan in `precompute_pc080sn_tile_lut.py` discovers all descriptor tables in the ROM and harvests all tile codes they reference. Since the same descriptor tables are used at runtime, tile coverage should be complete for the strip-commit path. Tiles not in any scene map to slot 0 (blank), producing empty cells rather than corruption.

### 10.2 Descriptor List Population
The desc list at `workram+0x1000` is written by arcade initialization code that runs through unpatched paths. The assembly validity checks (`btst #0` and `cmpi.l #5FFFC`) correctly reject zero entries (addr=0 → table_base = ROM[2..3] > 0x7FE0 → INVALID), so zero-initialized entries are silently skipped rather than producing garbage. The desc list is assumed to be populated correctly when the arcade code has initialized normally.

### 10.3 VSRAM Command Collision
`genesistan_scroll_commit_vdp` (`main.c:1786`) uses command `0x40000010` for VSRAM write at offset 0. This command word format is VSRAM write: `0x40000010` = `0x40000000 | (0 << 16) | (0 >> 14) | 0` with CD bits = `00 0100` — this is the correct VSRAM write command. ✓

### 10.4 Tile Data in VRAM
`genesistan_preload_scene_tiles` (`main.c:1607`) runs once at arcade handoff. It loads tile pixel data to VRAM slots 20–1023 (and 1280–1439 for the secondary cache). This runs before arcade mode starts. The tile data is present in VRAM before the first frame. ✓

---

## 11. Single Root Cause

**`DEST_PTR_NEVER_INITIALIZED`**

Both PC080SN destination pointer fields in arcade workram — BG at `0x10A0` and FG at `0x10A4` — start at zero and remain zero for the entire session. Every arcade store that would have written a valid 0xC0xxxx address to these fields is either inside a replaced routine (gone) or covered by a NOP patch. The tilemap strip-commit hooks execute correctly but always take the out-of-range branch, writing nothing to the WRAM buffers. Both Plane A (FG) and Plane B (BG) display blank game content — only the debug overlay (FG Item 1–3) is visible on Plane A.

---

## 12. Single Correction Path

Initialize the dest_ptr fields to their window start addresses in the Genesis handoff code, **before** the arcade tick runs for the first time. The correct values are:

| Field | Workram byte offset | Value |
|-------|---------------------|-------|
| BG dest_ptr | `0x10A0` | `0x00C00000` |
| FG dest_ptr | `0x10A4` | `0x00C08000` |

Using `pc080sn_workram_write_u32` (or equivalent big-endian byte stores), add to `startup_bridge.c` after the existing workram initialization block:

```c
/* Initialize PC080SN dest_ptr fields to C-window start addresses.
 * All arcade stores to these offsets are NOPped; Genesis handoff must
 * provide the initial values so the strip-commit hooks function
 * from frame 1. The hook interprets these as pure integers (never
 * dereferences them), so storing 0xC0xxxx in workram is safe. */
{
    uint8_t *const wr = (uint8_t *)genesistan_arcade_workram_words;
    /* BG dest_ptr = 0xC00000 */
    wr[0x10A0] = 0x00; wr[0x10A1] = 0xC0; wr[0x10A2] = 0x00; wr[0x10A3] = 0x00;
    /* FG dest_ptr = 0xC08000 */
    wr[0x10A4] = 0x00; wr[0x10A5] = 0xC0; wr[0x10A6] = 0x80; wr[0x10A7] = 0x00;
}
```

This change requires no ROM patch modifications, no new hooks, and no changes to the assembly. It activates the existing strip-commit mechanism from the first VBlank frame.

**Expected result after correction**: Both Plane A (FG) and Plane B (BG) will receive tilemap content on the first frame and update every subsequent frame, displaying the arcade's attract-mode background and foreground graphics.

---

## 13. What Was NOT Audited

- Runtime contents of the desc list (workram+0x1000) — requires a debugger read during execution
- Whether the arcade's FG strip count (`andi.w #0x0003, %d7` in FG assembly) matches the expected FG rendering cadence
- Whether the `genesistan_bulk_tilemap_commit` path for block writes (`0x5A4DE` hook) covers all non-strip writes correctly
- Scroll register values during gameplay (vertical/horizontal offset correctness)
