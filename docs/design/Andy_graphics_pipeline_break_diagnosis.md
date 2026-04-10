# Andy — Graphics Pipeline Break Diagnosis

## 1. Executive Summary

The VDP pattern data displayed on screen is the synthetic checkerboard because PC080SN tile pixel data has never been loaded into Genesis VRAM. The `tile_init_words` table (3 synthetic tiles: solid-1, solid-2, checkerboard-3) is the only tile pixel data ever written to VRAM. The `genesistan_pc080sn_tile_vram_lut` LUT correctly maps arcade tile indices to VRAM slot numbers (slots 20–1342), but no code path exists in the rastan-direct wrapper to read the PC080SN tile ROM data and upload it to VRAM at those slots. The LUT is a dead end: it maps to slots that are empty.

## 2. Inputs Audited

| File | Status |
|------|--------|
| `apps/rastan-direct/src/main_68k.s` | Read in full |
| `specs/rastan_direct_remap.json` | Read in full |
| `apps/rastan-direct/Makefile` | Read in full |
| `apps/rastan-direct/link.ld` | Read in full |
| `tools/translation/postpatch_startup_rom.py` | Read relevant sections |
| `tools/translation/precompute_pc080sn_tile_lut.py` | Read in full |
| `build/pc080sn_tile_vram_lut.bin` | Inspected — 16384 u16 entries, 2326 nonzero (slots 20–1342) |
| `build/pc080sn_attr_lut.bin` | Present — 64 bytes |
| `build/regions/pc080sn.bin` | Present — 524,288 bytes (16384 tiles × 32 bytes, raw 4bpp) |
| `build/regions/pc090oj.bin` | Present — 524,288 bytes |
| `build/regions/maincpu.bin` | Present — 393,216 bytes |
| `docs/design/rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` | Read in full |
| `AGENTS_LOG.md` | Last 150 lines read |

## 3. Graphics Data Presence in ROM

### PC080SN (Background Tile Graphics)

- `build/regions/pc080sn.bin` exists: 524,288 bytes = 16,384 tiles × 32 bytes per tile
- Format: raw 4bpp, Taito PC080SN native encoding (not interleaved, not compressed)
- This file is NOT included in the Genesis ROM binary at any point in the build pipeline.
- The `Makefile` calls `build_rastan_regions.py` (which extracts `pc080sn.bin` from the arcade ROMs) and `postpatch_startup_rom.py` (which copies only `maincpu.bin` into the Genesis ROM). No build step appends or embeds `pc080sn.bin` into the output binary.
- **PC080SN tile ROM data: present on disk, absent from Genesis ROM.**

### PC090OJ (Sprite Graphics)

- `build/regions/pc090oj.bin` exists: 524,288 bytes
- This file is similarly not included in the Genesis ROM by any build step.
- **PC090OJ sprite ROM data: present on disk, absent from Genesis ROM.**

### What IS in the Genesis ROM

The Genesis ROM contains:
1. Genesis boot/vector section (link.ld places wrapper at 0x070000)
2. The rastan-direct wrapper code and data (boot.o, main_68k.o, sound_comm.o, z80_driver.o)
3. The arcade maincpu.bin (393,216 bytes of 68000 program code) copied to ROM offset 0x000200–0x060200 by the patcher
4. The LUT binaries included via `.incbin` in main_68k.s:
   - `genesistan_pc080sn_tile_vram_lut` (32,768 bytes = 16384 u16 VRAM slot assignments)
   - `genesistan_pc080sn_attr_lut` (64 bytes = 32 attribute translation entries)

## 4. Current Tile Upload Path Analysis

### What currently populates `staged_tile_words`

`init_staging_state` (called once at boot) copies the `tile_init_words` ROM table into `staged_tile_words`:

```
lea     tile_init_words, %a0
lea     staged_tile_words, %a1
move.w  #(48 - 1), %d7
.Ltile_init:
move.w  (%a0)+, (%a1)+
dbra    %d7, .Ltile_init
```

`tile_init_words` contains exactly 3 synthetic 8×8 tiles (48 words = 3 × 16 words):
- Tile 1: 16 words of 0x1111 (solid palette-index-1 fill)
- Tile 2: 16 words of 0x2222 (solid palette-index-2 fill)
- Tile 3: 8 words alternating 0x3030 / 0x0303 (checkerboard pattern)

`init_staging_state` also sets `tiles_dirty = 1`, which causes `vdp_commit_tiles_if_dirty` to upload all 48 words to VRAM at address `VRAM_TILE_BASE` (0x00000020 = slot 1) during the first VBlank.

### Does any code path write arcade tile data to `staged_tile_words`?

No. After `init_staging_state` runs, `tiles_dirty` is cleared after the first VBlank commit and is never set again. No hook, no arcade-tick callback, and no initialization step writes to `staged_tile_words` after that point.

There is no mechanism in the wrapper to convert PC080SN 4bpp tile data to Genesis 4bpp tile format and stage it for upload.

### What VRAM content exists after boot

VRAM tiles after the first VBlank (at `VRAM_TILE_BASE` = 0x0020, which is slot 1):
- Slot 1 at VRAM 0x0020: solid palette-index-1
- Slot 2 at VRAM 0x0040: solid palette-index-2
- Slot 3 at VRAM 0x0060: checkerboard 3/0

All other VRAM tile slots (including slots 4–1342 where the LUT points) contain zero-initialized data (transparent tiles).

## 5. PC080SN BG Nametable Path Analysis

### What VRAM tile indices are written to `staged_bg_buffer`

`genesistan_hook_tilemap_plane_a` performs the following nametable word construction:

1. It reads descriptor entries from the arcade WRAM descriptor table at `0xFF1000` (16 descriptors, 4 bytes each).
2. For each valid descriptor, it reads the raw arcade nametable word from maincpu ROM at the descriptor's strip table.
3. It masks to 14 bits: `andi.w #0x3FFF, %d3` — this is the arcade tile index (0–16383).
4. It doubles the index and looks up the VRAM slot: `move.w 0(%a2,%d3.w), %d3` where `%a2 = genesistan_pc080sn_tile_vram_lut`.
5. It combines the VRAM slot with the attribute word from `genesistan_pc080sn_attr_lut` and writes the Genesis nametable word to `staged_bg_buffer`.

The tile indices written to the nametable correctly point to VRAM slots 20–1342 as assigned by the LUT. The nametable path is structurally sound.

### Do those VRAM tile indices have pixel data?

No. VRAM slots 20–1342 are zero-initialized at boot. The LUT assigns these slot numbers but nothing uploads the corresponding PC080SN tile pixel data to them. When the VDP renders Plane B using these nametable entries, it reads transparent (all-zero) tile data. The display shows the background color, not the arcade graphics.

### Is `staged_bg_buffer` being populated correctly otherwise?

The hook correctly:
- Validates the destination pointer against the c_window range (0xC00000–0xC04000)
- Decodes strip position into buffer row/column coordinates
- Applies attribute bits (priority, palette, flip) via `genesistan_pc080sn_attr_lut`
- Writes nametable words to the correct `staged_bg_buffer` offsets
- Sets `bg_row_dirty` bits for committed rows

The nametable side of the pipeline is functionally correct. The display problem is entirely on the tile pixel data side.

## 6. Tile Pixel Data Source Analysis

### What mechanism is supposed to upload PC080SN tile data?

The LUT generator (`precompute_pc080sn_tile_lut.py`) produces:
- `pc080sn_tile_vram_lut.bin`: arcade_tile_index → VRAM_slot (16384 entries)
- `pc080sn_scene_preload_title.bin`, `pc080sn_scene_preload_gameplay.bin`, `pc080sn_scene_preload_endround.bin`: scene-scoped (tile, slot) pair lists for preloading

The scene preload manifests explicitly list which tiles need to be loaded before each scene is displayable. They consume `pc080sn.bin` pixel data and require a runtime loader that:
1. Reads the scene preload manifest
2. For each (tile, slot) pair, reads 32 bytes of pixel data from `pc080sn.bin` at offset `tile × 32`
3. Converts from PC080SN 4bpp format to Genesis 4bpp tile format
4. Writes the 32 converted bytes to VRAM at `slot × 32 + VRAM_TILE_BASE`

**No such loader exists in the rastan-direct wrapper.** The wrapper contains `vdp_commit_tiles_if_dirty` which uploads `staged_tile_words` (3 synthetic tiles, 48 words), but there is no:
- Scene preload reader
- PC080SN-to-Genesis 4bpp format converter
- Bulk VRAM tile uploader for arcade tile data

### What tiles are in Genesis VRAM

| VRAM Slot | VRAM Address | Content | Source |
|-----------|-------------|---------|--------|
| 0 | 0x0000 | Transparent (all-zero) | Zero init |
| 1 | 0x0020 | Solid palette index 1 | `tile_init_words` |
| 2 | 0x0040 | Solid palette index 2 | `tile_init_words` |
| 3 | 0x0060 | Checkerboard 3/0 | `tile_init_words` |
| 4–1342 | 0x0080–0xA7C0 | Transparent (all-zero) | Zero init |
| 1343+ | 0xA7E0+ | Transparent | Zero init |

### Format note

PC080SN 4bpp format stores pixels differently from Genesis 4bpp. The Genesis VDP expects each tile row as 4 bytes with 2 pixels per nibble in big-endian order. The PC080SN format is planar (4 bitplanes). A format conversion step is required in addition to the upload step.

## 7. Rainbow Islands Strategy Validation

The Rainbow Islands Genesis port establishes the principle: on Genesis, tile pixel data from arcade tile ROMs must be explicitly pre-loaded into VDP VRAM before the nametable can reference it. The 68000 performs this upload, either at scene initialization or incrementally.

The rastan-direct wrapper partially implements this strategy:

| Component | Rainbow Islands Strategy | rastan-direct Current State |
|-----------|-------------------------|---------------------------|
| VRAM slot assignment (LUT) | Pre-computed offline | PRESENT — `genesistan_pc080sn_tile_vram_lut` (correct, 2326 tiles mapped) |
| Nametable translation (hook) | Runtime hook reads arcade nametable, translates to Genesis | PRESENT — `genesistan_hook_tilemap_plane_a` (correct) |
| Tile pixel data upload | Explicit VRAM preload before scene display | ABSENT — no loader, no uploader |
| Scene-scoped preload manifests | Offline-generated per-scene tile lists | PRESENT on disk (`pc080sn_scene_preload_*.bin`) but not included in ROM or read at runtime |
| BG nametable staging | WRAM staging buffer, VBlank commit | PRESENT — `staged_bg_buffer`, `vdp_commit_bg_strips_if_dirty` |
| Display-disable bracketing | VDP display off during VRAM writes | PRESENT — `_VINT_handler` disables/re-enables display |

The architecture is aligned with the Rainbow Islands strategy on 4 of 6 points. The missing element is exclusively the tile pixel data upload step.

## 8. Exact Break Point

The exact missing component is a **tile preload function** that:

1. Is called from `init_staging_state` (or from a first-frame hook) before any nametable content is committed
2. Reads the scene preload manifest from ROM (the `(tile, slot)` pair lists generated by `precompute_pc080sn_tile_lut.py`)
3. For each pair, reads 32 bytes of PC080SN pixel data from the arcade tile ROM (which must be present in the Genesis ROM image)
4. Converts the PC080SN 4bpp planar format to Genesis 4bpp chunky format
5. Writes the 32 converted bytes to VRAM at `(slot * 32) + VRAM_TILE_BASE`

Neither this function nor any equivalent exists anywhere in the rastan-direct codebase. Additionally, the PC080SN tile ROM data (`pc080sn.bin`, 524,288 bytes) is not embedded in the Genesis ROM image and therefore cannot be read at runtime.

The break point is at **two coupled sub-steps**:
1. `pc080sn.bin` is not included in the Genesis ROM (no `.incbin` for tile pixel data in `main_68k.s`, no patcher step to append it)
2. No tile upload function exists to read, convert, and write tile data to VRAM

## 9. Single Root Cause

The PC080SN tile pixel ROM data is never embedded in the Genesis ROM and no code path exists to upload it to VRAM, so all VRAM tile slots referenced by the nametable LUT remain zero-initialized; the VDP renders transparent tiles for every arcade tile reference, and only the three synthetic tiles loaded at boot are ever visible.

## 10. Single Next Correction

Embed the PC080SN tile ROM data in the Genesis ROM (via a `.incbin "../../build/regions/pc080sn.bin"` in main_68k.s rodata section, or appended by the patcher) and implement a single init-time tile preload function that iterates the `genesistan_pc080sn_tile_vram_lut` or the scene preload manifest, converts each PC080SN planar tile to Genesis chunky 4bpp format, and writes the tile data to VRAM before the first nametable commit.

## 11. What Must Not Be Changed Yet

- All 34 `opcode_replace` entries in `specs/rastan_direct_remap.json`
- `genesistan_hook_tilemap_plane_a` — nametable translation is correct
- `genesistan_pc080sn_tile_vram_lut` and `genesistan_pc080sn_attr_lut` — LUT assignments are correct
- `staged_bg_buffer` / `vdp_commit_bg_strips_if_dirty` — nametable staging and commit path is correct
- `_VINT_handler` structure (display-disable bracketing, commit order)
- `vdp_commit_tiles_if_dirty` — synthetic tile upload still needed for slot 1–3 which may be referenced by other paths
- `rom_absolute_call_relocation` configuration
- A5 initialization to 0xFF0000
- `VRAM_TILE_BASE` = 0x00000020 (slot 1)
- All existing LUT generator outputs in `build/`

## 12. Final Verdict

The VDP checkerboard pattern is caused by a single absent pipeline stage: tile pixel data upload. The nametable translation path (`genesistan_hook_tilemap_plane_a` → `staged_bg_buffer` → `vdp_commit_bg_strips_if_dirty`) is architecturally correct and aligned with the Rainbow Islands strategy. The LUT correctly maps 2,326 arcade tile indices to VRAM slots 20–1342. However, those VRAM slots contain only zeros because:

1. The PC080SN tile ROM (`pc080sn.bin`, 524,288 bytes) is never embedded in the Genesis binary
2. No runtime function reads, converts, or uploads PC080SN tile pixel data to VRAM

The nametable tells the VDP to look at slot 82 for tile 1, but slot 82 is empty. The correction requires embedding the tile ROM and implementing one initialization-time upload function. All other pipeline components are correct and should not be modified.
