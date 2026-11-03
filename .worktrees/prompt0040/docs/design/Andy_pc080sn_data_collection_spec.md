# Andy — PC080SN Data Collection Spec

## 1. Executive Summary

All arithmetic fixes (%d1, %d2, %d7) are applied and correct. Layer B (Plane B, 0xC000) remains pure checkerboard in the Exodus plane viewer while Layer A shows non-checkerboard content. The mapping model — including whether descriptors are valid, what they actually contain, and what screen position each descriptor targets — has never been verified against a reference source. This spec defines the exact data Cody must collect so the correct mapping can be derived without guessing.

No mapping assumptions are made in this document.

---

## 2. Task 1 — Required Dest Trace Data

Cody must instrument `genesistan_hook_tilemap_plane_a` to capture a complete trace of one full hook invocation during Title screen playback. The trace must cover all 16 descriptor iterations.

### 2.1 Per-Hook-Call Header (once per hook invocation)

Capture at hook entry (before any processing):

| Field | Source | Description |
|-------|--------|-------------|
| `hook_call_index` | incremented counter | Sequential call number (0, 1, 2, …) |
| `dest_raw` | `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` | Raw 32-bit value read from WRAM |
| `dest_masked` | `dest_raw & 0x00FFFFFF` | After mask |
| `dest_valid` | `YES/NO` | Did dest pass the CWindow range check? |
| `dest_aligned` | `YES/NO` | Were bits[1:0] zero? |
| `strip_index` | `ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5)` | %d7 value for this call |
| `row_initial` | %d1 after extraction | Initial row (bits[4:0] of (dest-base)/4) |
| `col_initial` | %d2 after extraction | Initial column group (bits[11:6] of (dest-base)/4) |

If `dest_valid = NO`, record header only and stop (hook took `.Lbg_hook_dest_invalid`).

### 2.2 Per-Descriptor Row (16 rows per valid hook call)

Capture at the start of each `.Lbg_hook_desc_loop` iteration:

| Field | Source | Description |
|-------|--------|-------------|
| `desc_index` | 0–15 | Outer loop counter |
| `desc_value` | `(%a0)` before increment | Raw 4-byte descriptor value |
| `desc_valid` | `YES/NO` | Did descriptor pass all three validity checks? |
| `d7_strip` | %d7 | strip_index (constant for hook call) |
| `d1_row` | %d1 at start of iteration | Row index for this descriptor |
| `d2_col` | %d2 at start of iteration | Column group for this descriptor |
| `d2_plus_d7` | %d2 + %d7 | Actual target column |

If `desc_valid = NO`, record above fields, skip tile fields, mark remaining as `—`.

For valid descriptors, additionally capture:

| Field | Source | Description |
|-------|--------|-------------|
| `tile_table_addr` | %a4 after strip offset | ROM address of first tile read |
| `attr_word` | %d4 after parsing | Parsed attribute/control word |
| `tile_0` | `(%a4)` at row_loop iter 0 | Raw tile index from ROM (before masking) |
| `tile_1` | `(%a4+8)` at row_loop iter 1 | Raw tile index, row+1 |
| `tile_2` | `(%a4+16)` at row_loop iter 2 | Raw tile index, row+2 |
| `tile_3` | `(%a4+24)` at row_loop iter 3 | Raw tile index, row+3 |
| `vram_slot_0` | LUT lookup result, iter 0 | VRAM slot index for tile_0 |
| `vram_slot_1` | LUT lookup result, iter 1 | VRAM slot index for tile_1 |
| `vram_slot_2` | LUT lookup result, iter 2 | VRAM slot index for tile_2 |
| `vram_slot_3` | LUT lookup result, iter 3 | VRAM slot index for tile_3 |
| `buf_offset_0` | %d0 at staging write, iter 0 | Byte offset into staged_bg_buffer |
| `buf_offset_1` | %d0 at staging write, iter 1 | Byte offset, row+1 |
| `buf_offset_2` | %d0 at staging write, iter 2 | Byte offset, row+2 |
| `buf_offset_3` | %d0 at staging write, iter 3 | Byte offset, row+3 |
| `nametable_entry_0` | %d3 at staging write, iter 0 | Full nametable word written to buffer |
| `nametable_entry_1` | %d3 at staging write, iter 1 | |
| `nametable_entry_2` | %d3 at staging write, iter 2 | |
| `nametable_entry_3` | %d3 at staging write, iter 3 | |

### 2.3 Minimum Required

- At minimum 4 consecutive hook calls for the Title scene (consecutive = no intervening hook-dest-invalid calls)
- Each call must include all 16 descriptors
- At least 2 calls where `dest_valid = YES` and at least one `desc_valid = YES` per call

---

## 3. Task 2 — Required MAME PC080SN Source Data

Cody must extract the following from the MAME source tree, specifically `src/mame/taito/pc080sn.cpp` (or equivalent path in the version used for Rastan).

### 3.1 Tilemap RAM Layout

Required from the chip's RAM read/write handlers:

- The base address of the PC080SN BG tilemap RAM in the arcade address space (the physical RAM range that the arcade CPU writes tile data to)
- The size of the tilemap RAM in bytes
- The RAM organization: is it byte-addressed, word-addressed, or longword-addressed?
- Whether there is interleaving between BG layer and FG layer

### 3.2 Tile Index Fetch

Required from the tilemap draw/render function (typically `get_tile_info` or equivalent callback):

- The exact formula used to compute the tile index from a given screen (col, row) position
- Specifically: which bits of the RAM word contain the tile number?
- Which bits contain palette, priority, flip attributes?
- Whether tile number is subject to any bank/offset adjustment before use

### 3.3 Screen Position to RAM Address

Required: the exact formula that maps screen tile (col, row) to a RAM word address. This must be expressed as a concrete arithmetic formula, not pseudocode:

```
ram_word_address = f(col, row)
```

Include:
- Whether row-major or column-major order
- Any stride multipliers
- Any bit reversal, interleaving, or XOR present in the addressing
- Whether (0,0) is top-left or some other origin

### 3.4 Strip Write Mechanism (if present)

If MAME's PC080SN emulation uses a "strip" or "column" DMA write mechanism distinct from individual tile writes:

- The function that handles strip writes from the arcade CPU to the chip's tilemap RAM
- The strip write address calculation
- How the strip index maps to the destination column or row
- The size of one strip (bytes, tiles, or rows)

### 3.5 Any Non-Obvious Transformations

Document any of the following if present:
- Address mirroring
- Read-modify-write patterns during rendering
- Tile index offsets applied during draw vs during write
- Layer-specific addressing differences (BG vs FG)

---

## 4. Task 3 — Required Arcade Memory View

Cody must extract the following from arcade ROM/RAM using MAME's debugger or memory viewer at a known state during the Title screen attract sequence.

### 4.1 PC080SN Tilemap RAM Dump

Required: a hex dump of the complete PC080SN BG tilemap RAM at a moment when the Title screen is fully drawn (attract mode, first few seconds).

Format:
```
address: word word word word word word word word
```
- Start at the base of the BG tilemap RAM
- Include all bytes up to the end of the 32-row × 64-column nametable
- Take the dump AFTER the arcade's first complete frame render (not at boot before first draw)
- Record the exact MAME simulation time or frame counter at the dump

### 4.2 Screen Tile Ground Truth

For a 4×4 block of tiles at screen position (col=0, row=0) through (col=3, row=3), extract:

For each (col, row) pair in that block:

| Field | Description |
|-------|-------------|
| `col` | Screen column (0-based) |
| `row` | Screen row (0-based) |
| `arcade_ram_address` | Byte address in arcade RAM of this tile's data word |
| `arcade_ram_word` | Raw 16-bit word at that address |
| `arcade_tile_number` | Tile number extracted per MAME's get_tile_info formula |
| `arcade_palette` | Palette bits |
| `arcade_flip_h` | H-flip bit |
| `arcade_flip_v` | V-flip bit |
| `arcade_priority` | Priority bit |

Minimum: 16 entries (4 columns × 4 rows), top-left corner of Title screen.

### 4.3 Strip Write Address Observation

Using MAME's debugger, place a write breakpoint on the PC080SN BG tilemap RAM. Record:

- The arcade CPU address at which each strip write begins
- The value of the "dest" pointer register in the PC080SN's internal registers at the time of the write (if accessible via MAME debugger)
- The number of words written per strip call
- The stride between consecutive writes within one strip

---

## 5. Task 4 — Required Correlation Data

Cody must produce a correlation table that allows direct comparison between arcade tile position and Genesis staging buffer position.

### 5.1 Genesis Side: Current staged_bg_buffer Content

After running the ROM for at least 60 frames on BlastEm or Exodus with the latest build (all three fixes applied), dump:

- The full `staged_bg_buffer` (4096 bytes, as 2048 × 16-bit words)
- For each word: its buffer offset, decoded row, decoded column, and nametable entry value
- Identify which entries are the init_staging_state checkerboard (0x0001 or 0x0002) vs real tile data (any other value)

Format:
```
buf_offset | row | col | nametable_word | content_type
```
Where `content_type` is: `CHECKERBOARD_1`, `CHECKERBOARD_2`, or `REAL_DATA`.

### 5.2 Comparison Table

Using the arcade tile ground truth from Task 3 and the Genesis staging buffer content from above, produce a direct comparison for the same 4×4 block:

| `screen_col` | `screen_row` | `arcade_tile_number` | `genesis_buf_offset` | `genesis_nametable_word` | `match` |
|-------------|-------------|---------------------|---------------------|--------------------------|---------|
| 0 | 0 | (from Task 3) | (from staged_bg_buffer) | (from staged_bg_buffer) | YES/NO |
| ... | ... | ... | ... | ... | ... |

The `genesis_buf_offset` for a given (col, row) is `row * 128 + col * 2`. The `genesis_nametable_word` at that offset encodes: `vram_slot | attr_bits`.

The `match` field is YES if `genesis_nametable_word` references a VRAM slot that contains the tile pixel data for `arcade_tile_number`.

---

## 6. Task 5 — Output Format

### 6.1 Dest Trace Output

File: `docs/design/Cody_pc080sn_dest_trace.md`

Section 1: Summary table — one row per hook call header:
```
call# | dest_raw  | dest_masked | valid | strip_idx | row_init | col_init
------|-----------|-------------|-------|-----------|----------|--------
0     | 00C00000  | 00C00000    | YES   | 0         | 0        | 0
```

Section 2: Descriptor detail — one row per descriptor per valid hook call:
```
call# | desc# | desc_val | valid | d1_row | d2_col | d7+d2 | tile_0 | vslot_0 | buf_off_0 | nmt_0
------|-------|----------|-------|--------|--------|-------|--------|---------|-----------|------
0     | 0     | 00012345 | YES   | 0      | 0      | 0     | 0x0042 | 0x0015  | 0x0000    | 0x0015
```

### 6.2 MAME PC080SN Extraction Output

File: `docs/design/Cody_mame_pc080sn_extract.md`

Must include:
1. Verbatim source excerpts (function bodies, not summaries) of `get_tile_info` and any `strip_write` handler
2. Annotated formula showing exactly how `(col, row) → RAM address` is computed
3. Annotated formula showing exactly how `RAM word → tile number` is computed

### 6.3 Arcade Memory Dump Output

File: `docs/design/Cody_arcade_tilemap_ram_dump.md`

Must include:
1. Hex dump of full BG tilemap RAM (see Task 3.1 format)
2. Ground truth tile table (see Task 3.2 format) — minimum 16 rows
3. Strip write observation log (see Task 3.3) — minimum 4 strip write events

### 6.4 Correlation Output

File: `docs/design/Cody_genesis_staged_buffer_dump.md`

Must include:
1. staged_bg_buffer content summary: total REAL_DATA entries vs CHECKERBOARD entries
2. Correlation table (see Task 4.2) — minimum 16 rows
3. For each REAL_DATA entry in the 4×4 block: confirm whether it maps to the correct arcade tile

### 6.5 Minimum Entry Counts

| Output | Minimum entries |
|--------|----------------|
| Hook call headers | 4 |
| Descriptor rows (valid calls only) | 32 (2 calls × 16 descs) |
| Arcade ground truth tile table | 16 (4×4 block) |
| Strip write events | 4 |
| Staged buffer correlation rows | 16 |

---

## 7. Collection Constraints

- All arcade data must be from Title scene only (attract mode, first 5 seconds)
- Genesis data must be from the same build that applies all three fixes (%d1, %d2, %d7)
- BlastEm or Exodus WRAM viewer may be used to dump staged_bg_buffer
- MAME debugger required for arcade RAM dump and strip write breakpoints
- No data may be inferred or approximated — all fields must come from actual observed values
