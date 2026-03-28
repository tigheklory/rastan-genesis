# Rastan Title Translation Layer (Rainbow Template)

## Objective
Implement the first real title-screen graphics translation slice from arcade producer intent to Genesis VDP output, without descriptor hardcoding or branch-target hacks.

Scope in this pass is title/attract pre-exception rendering only.

## First Real Producer Chain (Title Path)
Primary chain validated on `dist/Rastan_259.bin`:

- `0x03BD5E` -> title text dispatch
- `0x202B74` -> semantic wrapper bridge (`genesistan_hook_text_writer_3bb48`)
- `0x20034C` -> text descriptor producer (`genesistan_hook_text_writer_3bb48_impl`)
- `0x200424` -> per-glyph loop body
- `0x2004F2` -> tile-cache path inside text producer
- `0x20052A` -> VDP control write (VRAM command)
- `0x20053E` -> VDP data write (tilemap word)

Supporting title graphics-side paths observed pre-exception:

- `0x200DC2` -> scroll sync (`genesistan_scroll_from_workram_vdp`)
- `0x200E56` -> fixed text/status writer path (`genesistan_hook_text_writer_3c3fe`)
- `0x202B80` / `0x2005C4` -> sprite bridge/renderer entry (no non-zero sprite payload in this window)

## Translation Classes Implemented (Title Slice)

| Arcade intent class | Arcade-side producer PCs | Genesis-side operation | DMA used | VDP resource affected |
|---|---|---|---|---|
| Tilemap/text emission (PC080SN text RAM semantics) | `0x03BD5E -> 0x202B74 -> 0x20034C` | Descriptor decode, per-glyph tile resolution, direct VDP plane-word writes | Tile pattern residency via `tile_cache_get` + `VDP_loadTileData(..., DMA)` | VRAM pattern cache + Plane A name table writes |
| Secondary text/status stream | `0x200E56` | Fixed-count text/tile writes translated to Plane A tile attributes | Tile data path uses cached tiles (DMA on miss) | VRAM + Plane A |
| Sprite intent (PC090OJ -> SAT) | `0x202B80 -> 0x2005C4` | Sprite descriptor block walk and SGDK sprite update path | Yes (`VDP_loadTileData(..., DMA)`, `VDP_updateSprites(..., DMA)`) | VRAM sprite patterns + SAT upload path |
| Palette RAM intent -> CRAM | `load_arcade_palette()` in live frontend loop | CLCS-to-Genesis palette conversion and `PAL_setColors(..., DMA)` | Yes | CRAM |
| Scroll/control | `0x200DC2` | Workram scroll intent mapped to `VDP_setHorizontalScroll/VDP_setVerticalScroll` | No | Scroll registers/VSRAM-facing state |

## Title-Slice Control Ownership Fix Applied
`main.c` changes in this pass:

1. Added `genesistan_sync_title_vdp_layout()` in live title loop and at START handoff:
- `VDP_setPlaneSize(64, 32, FALSE)`
- `VDP_setBGAAddress(0xE000)`
- `VDP_setBGBAddress(0xC000)`
- `VDP_setSpriteListAddress(0xF800)`
- `VDP_setWindowOff()`

This keeps title translation writes targeted at the intended Genesis ownership layout.

2. Updated text destination column mapping for title viewport:
- `text_writer_ptr_to_xy()` now uses a 32-column bias for this title slice (`col_bias=32`) so emitted title text lands in visible columns before exception.

No descriptor constant replacement was used.
No per-branch bypass patch was added.

## Validation (Pre-Exception)
Source: `/tmp/build259_preexception_probe.txt` (run stopped at frame 672, before exception-handler takeover)

### 1) Real producer execution
- `HIT 03BD5E 1`
- `HIT 202B74 1`
- `HIT 20034C 1`
- `HIT 200424 9`
- `HIT 2004F2 9`
- `HIT 20052A 9`
- `HIT 20053E 9`

### 2) VRAM payload activity (non-blank)
- `vram_data(code01)=1026`
- `vram_nonzero=766`

### 3) CRAM payload activity (non-zero)
- `cram_data(code03)=962`
- `cram_nonzero=960`

### 4) SAT/Sprite status in this window
- Sprite renderer path executes (`HIT 202B80 1`, `HIT 2005C4 160`), but sampled sprite cache is zero in this short pre-exception window (`/tmp/build259_spritecache_probe.txt`: `sprite_cache_nonzero_words=0/320`).
- So this title slice is currently text-visible before exception, while sprite payload population remains pending.

### 5) Visible pixels before exception
Artifacts captured from `dist/Rastan_259.bin` timeline:

- `docs/research/artifacts/build259_preexception_credit_step1.png`
- `docs/research/artifacts/build259_preexception_credit_step2.png`
- `docs/research/artifacts/build259_preexception_credit_step3.png`

These frames show real game-path title text progression (`CREDIT`) before exception-handler takeover.

## Result
The first real game title text path now renders visible pre-exception pixels from the game producer chain (`0x03BD5E -> 0x20034C`) through translated Genesis VDP ownership.

## Remaining Gaps (Title Slice)
- Exception-handler takeover still occurs shortly after first title text emission.
- Tilemap plane hooks (`0x200000`, `0x2001A6`) are still not active in this pre-exception started window.
- Sprite payload remains zero in this exact pre-exception sample, so title text is currently the proven visible component.
