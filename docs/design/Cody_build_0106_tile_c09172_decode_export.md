# Cody - Build 0106 vs Arcade C09172 Tile Decode + Export

**Date:** 2026-06-26  
**Type:** Evidence / analysis only  
**Build context:** Build 0106, `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`  
**Build 0106 SHA256:** `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`  
**Scope:** Decode and export the tile selected by the confirmed raw write to `HW_ADDRESS 0x00C09172`. No source/spec/tool/ROM/build changes. No bookmark cycle. No diagnostics inserted. No fix design.

## Phase 0

`RULES.md`, `ARCHITECTURE.md`, and latest `AGENTS_LOG.md` context were read before this evidence capture. Architecture compliance: **PASS**. This task observes arcade intent and Build 0106 mapping only; it does not change execution or propose a patch.

Address discipline: all arcade-to-Genesis PC correlation uses `build/rastan-direct/address_map.json`. No global `+0x200` arithmetic is used as authority.

## Prior Watchpoint Context

Build 0106 MAME Genesis-driver watchpoint established:

```asm
runtime_genesis_pc 0x0003ACEA:
    33fc 2749 00c0 9172   movew #0x2749,0x00c09172
```

Effective write: `HW_ADDRESS 0x00C09172`, size word, data `0x2749`.

`address_map.json` segment:

```json
{
  "genesis_start": "0x03AB20",
  "genesis_end_exclusive": "0x03AD00",
  "kind": "arcade_copy",
  "arcade_start": "0x03A920",
  "arcade_end_exclusive": "0x03AB00",
  "source": "whole_maincpu_copy"
}
```

Segment-relative JSON mapping gives `arcade_pc 0x0003AAEA` for `runtime_genesis_pc 0x0003ACEA`.

## PC080SN Decode Source

Authoritative source files used:

- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp`
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`

Relevant MAME source facts:

- `pc080sn.cpp:11-18`: standard layout is two 64x64 tilemaps with 8x8 tiles; `0x8000-0xBFFF` is FG.
- `pc080sn.cpp:79-82`: standard mode creates both tilemaps as `64 x 64`, `8 x 8` tiles.
- `pc080sn.cpp:133-147`: in standard mode, for each tile index, `attr = m_bg_ram[N][2 * tile_index]`; `code = m_bg_ram[N][2 * tile_index + 1] & 0x3fff`; color is `attr & 0x1ff`; flip is `TILE_FLIPYX((attr & 0xc000) >> 14)`.
- `rastan.cpp:318`: `HW_ADDRESS 0xC00000..0xC0FFFF` maps to `pc080sn_device::word_r/word_w`.
- `rastan.cpp:407-408`: PC080SN graphics decode uses `gfx_8x8x4_packed_msb` from the `pc080sn` graphics region.
- `rastan.cpp:455`: palette format is `palette_device::xBGR_555`.
- `rastan.cpp:511-515`: the PC080SN graphics region is the four ROMs `b04-01.40`, `b04-02.67`, `b04-03.39`, `b04-04.66`, locally extracted as `build/regions/pc080sn.bin`.

## Decode of Tilemap Entry

`HW_ADDRESS 0x00C09172` lies in the PC080SN FG tilemap memory region:

- FG tilemap base: `HW_ADDRESS 0x00C08000`.
- Byte offset from FG base: `0x1172`.
- Word index from FG base: `0x08B9`.
- Standard PC080SN tile entry is two words: attr word then code word.
- Since word index `0x08B9` is odd, `0x00C09172` is the **code word** for tile entry index `0x045C`.
- Paired attr word is at `HW_ADDRESS 0x00C09170`.

Original arcade runtime dump from `rastan (World Rev 1)` at the matching producer point:

```text
C09170:  0000 2749 0000 0049 0000 0020 0000 0043  ..'I...I... ...C
```

Decoded fields for tile entry at `HW_ADDRESS 0x00C09170/0x00C09172`:

| Field | Value | Source |
|---|---:|---|
| attr word | `0x0000` | original arcade runtime dump |
| code word | `0x2749` | original arcade runtime dump and Build 0106 watchpoint |
| tile code | `0x2749` | `code & 0x3fff` |
| color / palette bank | `0x000` | `attr & 0x1ff` |
| flip bits | none | `(attr & 0xc000) >> 14 = 0` |
| priority bits | none in PC080SN tile word | Rastan draws FG with fixed draw priority in `screen_update`; no per-tile priority field is decoded by `get_tile_info` |

## Tilemap Position

For standard PC080SN FG:

- Entry index: `0x045C` (`1116` decimal).
- Geometry: 64 columns x 64 rows.
- Column: `28`.
- Row: `17`.
- Unscrolled tilemap pixel origin: `x = 28 * 8 = 224`, `y = 17 * 8 = 136`.

Approximate on-screen position is not asserted as exact here. MAME applies PC080SN scroll state and `set_scrolldx(-16 + x_offset, -16 - x_offset)`; this capture did not dump the live scroll registers at the exact render frame. Without that synchronized scroll state, only the tilemap row/column is proven.

## Arcade Tile Export

Arcade graphics source:

- Region: `build/regions/pc080sn.bin`.
- MAME decode: `gfx_8x8x4_packed_msb`.
- Tile code: `0x2749`.
- Color bank: `0x000`.
- Palette RAM source: original arcade MAME runtime dump `states/traces/build_0106_c09172_tile_palette_arcade_dump_20260626_100941/arcade_palette_after_c09172.dump`.
- Palette words for color bank 0:

```text
0000 7BDE 001E 29D0 4298 29D4 194C 7BDE 7BDE 7BDE 7BDE 7BDE 7BDE 7BDE 7BDE 7BDE
```

Arcade PNG:

`states/screenshots/tile_c09172_ARCADE_code2749_color000.png`

## Build 0106 Mapping Export

Build 0106 tile/palette sources:

- `apps/rastan-direct/src/scene_load.s:100-109`: `genesistan_pc080sn_tile_vram_lut`, `genesistan_pc080sn_attr_lut`, and `genesistan_pc080sn_tile_rom` are incbinned from build artifacts.
- `genesistan_pc080sn_tile_rom` source: `build/regions/pc080sn.bin`.
- `build/pc080sn_tile_vram_lut.bin`: arcade tile `0x2749` maps to Genesis VRAM slot `0x0039`.
- `build/pc080sn_scene_preload_title.bin`: contains pair `(tile 0x2749, slot 0x0039)`.
- `build/pc080sn_attr_lut.bin`: attr index `0x00` maps to Genesis nametable attr word `0x0000`.
- `apps/rastan-direct/src/palette_hooks.s:11-36`: Build palette conversion is xBGR-555 to Genesis CRAM `0000_BBB0_GGG0_RRR0`.

Build-side converted CRAM words for the same arcade palette bank 0:

```text
0000 0EEE 000E 0468 08AC 046A 0246 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE
```

Build 0106 currently stages this entry? **NO for the confirmed write path.** The confirmed Build 0106 operation at `runtime_genesis_pc 0x0003ACEA` is a raw absolute write to `HW_ADDRESS 0x00C09172`, not a staging-buffer write. This report does not claim whether some separate future/duplicate path could independently stage the same cell.

Build 0106 mapped tile PNG:

`states/screenshots/tile_c09172_BUILD0106_code2749_color000.png`

## Side-by-Side Export

Comparison PNG:

`states/screenshots/tile_c09172_COMPARE.png`

Throwaway export script:

`states/scripts/export_c09172_tile.py`

Export summary:

`states/screenshots/tile_c09172_export_summary.txt`

## Match / Difference

**Verdict:** DIFFER, but narrowly.

Observable facts:

- The tile graphic/shape matches: Build 0106 incbins the same `build/regions/pc080sn.bin` bytes, and the ROM tile chunk at `genesistan_pc080sn_tile_rom + 0x2749 * 32` matches the source tile bytes exactly.
- The Build 0106 mapping is present: tile `0x2749 -> slot 0x0039`, attr `0x0000 -> 0x0000`.
- The visual difference in the exported PNGs is palette quantization only: arcade xBGR-555 white-ish color `0x7BDE` expands to full 5-bit RGB, while Build conversion maps it to Genesis CRAM `0x0EEE` (3-bit-per-channel effective output).
- No flip difference: attr flip bits are zero.
- Not blank/missing: the tile is present and preloaded in the title scene manifest.

Interpretation:

- The original arcade intent at `HW_ADDRESS 0x00C09172` is to place tile code `0x2749`, color bank `0`, at FG row `17`, column `28`. The tile is the small comma/special-glyph shape associated with tile `0x2749` in the title text/special glyph set.
- Build 0106 has a valid tile/palette mapping for that arcade tile, but the confirmed runtime write is raw/unrouted, so that mapping is not used by this specific instruction yet.

## STOP Status

STOP triggered: **NO**.

Required sources were identified:

- PC080SN tilemap format: confirmed from MAME source.
- Arcade graphics region: confirmed from MAME `rastan.cpp` and local extracted region.
- Build 0106 tile/palette mapping: confirmed from project LUT/preload/palette conversion artifacts.
- Address mapping: confirmed through `address_map.json`.

## Non-Actions

- No source changes.
- No spec changes.
- No tool changes.
- No ROM/build changes.
- No bookmark cycle.
- No diagnostics inserted.
- No fix design or implementation.
- No issue opened or closed.

## Open / Known Findings Impact

- OPEN-017: context extended with arcade-intent evidence for the raw `0xC09172` writer.
- OPEN-001: context only.
- OPEN-015: not touched.
- `KNOWN_FINDINGS.md`: no update in this task.
