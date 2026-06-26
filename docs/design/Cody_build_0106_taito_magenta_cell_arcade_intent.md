# Cody - Build 0106 TAITO Magenta-Cell Arcade Intent

**Date:** 2026-06-26  
**Type:** Evidence / analysis only  
**Build context:** Build 0106, `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`  
**Build 0106 SHA256:** `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`  
**Scope:** Decode the four exact user-marked magenta cells in the small red `TAITO` logo and compare original arcade intent against Build 0106 handling. No source/spec/tool/ROM/build changes. No bookmarks. No diagnostics inserted into ROM. No fix design.

## Phase 0

Read before evidence work:

- `RULES.md`
- `ARCHITECTURE.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- latest `AGENTS_LOG.md` entries
- `docs/design/Cody_build_0106_correction_taito_arcade_intent_paren_lut.md`
- `docs/design/Cody_build_0106_missing_fixed_tiles_attr_flip_inventory.md`
- `docs/design/Cody_build_0095_arcade_title_tile_usage_audit.md`
- `docs/design/Andy_build_0095_taito_logo_producer_attribution.md`
- Build 0097 origin/scroll-offset evidence in `docs/design/Cody_build_0097_display_origin_bias_impl.md`

Architecture compliance: **PASS**. Arcade code remains the program; Genesis-side code is treated only as helper/opcode-replacement behavior. This task observes existing arcade runtime dumps, existing Build 0106 runtime behavior, and exported PNG evidence.

Address discipline: instruction/code-PC correlation uses `build/rastan-direct/address_map.json`. Hardware tilemap addresses and staged WRAM addresses are labeled separately and are not inferred through PC arithmetic.

## Evidence Artifacts

Primary user-marked screenshot:

- `states/screenshots/build_106_missing_TAITO_logo_tiles_highlighted_in_magenta_hex_code_#ff00ff.png`

Original arcade runtime evidence:

- `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/arcade_pc080sn_fg_after_title.bin`
- `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/arcade_pc080sn_bg_after_title.bin`
- `/home/tighe/.mame/snap/rastan/RASTAN TITLE REFERENCE MAME.png`

Build 0106 runtime evidence:

- `states/traces/build_0106_missing_fixed_tiles_attr_flip_inventory_20260626_111500/staged_fg_at_03ac88.dump`
- `states/traces/build_0106_taito_magenta_cell_arcade_intent_20260626_134949/magenta_cells_watch_trace.log`
- `states/traces/build_0106_taito_magenta_cell_arcade_intent_20260626_134949/magenta_staged_fg_at_03acfe.dump`

Reducer / exports:

- `states/scripts/build0106_taito_magenta_cell_audit.py`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/summary.json`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/build0106_magenta_cells_overlay.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/arcade_reference_same_cells_overlay.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/taito_magenta_cells_ARCADE_vs_BUILD0106_compare.png`

## PC080SN Decode Source

Authoritative local MAME source:

- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp`: standard PC080SN tilemaps are `64x64` cells, `8x8` pixels, with paired attr/code words.
- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp`: `code = word & 0x3fff`; color bank is `attr & 0x01ff`; flip bits come from `(attr & 0xc000) >> 14`.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`: `HW_ADDRESS 0x00C00000..0x00C0FFFF` maps to PC080SN, and `screen_update` draws PC080SN layer 0 then layer 1.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`: PC080SN graphics use `gfx_8x8x4_packed_msb`; palette format is xBGR-555.

## Coordinate Reconciliation

### Build 0106 rendered screen to staged FG

Observable magenta cells in the Build 0106 rendered screenshot:

| Target | Screen cell | Pixel bbox |
|---|---:|---:|
| magenta_A | `15,22` | `x=120..127, y=176..183` |
| magenta_B | `20,22` | `x=160..167, y=176..183` |
| magenta_C | `22,22` | `x=176..183, y=176..183` |
| magenta_D | `18,23` | `x=144..151, y=184..191` |

Build 0097 origin evidence establishes the current Genesis-side display bias:

- Committed Plane A/FG HScroll is `0xFFF0` (`-16`), moving content left `16 px`.
- Committed Plane A/FG VScroll is `0x0008` (`+8`), moving content up `8 px`.
- Therefore, for the title steady-state visual frame, Build 0106 rendered screen cell maps back to staged cell as: `staged_col = screen_col + 2`; `staged_row = screen_row + 1`.

Resulting Build 0106 staged FG coordinates:

| Target | Screen cell | Build staged FG row/col | Staged WRAM |
|---|---:|---:|---:|
| magenta_A | `15,22` | `23,17` | `0x00FF5BBC` |
| magenta_B | `20,22` | `23,22` | `0x00FF5BC6` |
| magenta_C | `22,22` | `23,24` | `0x00FF5BCA` |
| magenta_D | `18,23` | `24,20` | `0x00FF5C42` |

### Original arcade rendered screen to PC080SN FG

Original MAME Rastan driver evidence:

- Visible area is X `0..319`, Y `8..247`, so visible tile row `0` corresponds to PC080SN tilemap row `1`.
- PC080SN standard `set_scrolldx` includes `-16`, so the visible X origin is shifted by two 8x8 cells relative to the PC080SN tilemap.
- Title-state raw scroll writes were previously measured as zero; this transform is the fixed PC080SN display-origin behavior, not a dynamic title scroll value.

Original arcade screen cell maps to PC080SN FG as: `pc080sn_col = screen_col + 2`; `pc080sn_row = screen_row + 1`.

Resulting arcade PC080SN FG coordinates match the Build 0106 staged coordinates above: row/col `23,17`, `23,22`, `23,24`, and `24,20`.

### Anchor validation

Visible anchor cells around the magenta gaps line up in both contexts. Build 0106 has visible red pixels at the anchor cells, and the original arcade reference has the same red-pixel counts for those screen cells. Build 0106 staged words for these anchors are nonzero.

| Anchor | Screen cell | FG row/col | Arcade code | Build staged word | Build red px | Arcade red px |
|---|---:|---:|---:|---:|---:|---:|
| anchor_A | `16,22` | `23,18` | `0x0023` | `0x0001` | `44` | `44` |
| anchor_B | `17,22` | `23,19` | `0x0024` | `0x0002` | `25` | `25` |
| anchor_C | `18,22` | `23,20` | `0x0025` | `0x0003` | `39` | `39` |
| anchor_D | `19,22` | `23,21` | `0x0026` | `0x0004` | `29` | `29` |
| anchor_E | `21,22` | `23,23` | `0x002B` | `0x0005` | `44` | `44` |
| anchor_F | `23,22` | `23,25` | `0x002F` | `0x0007` | `34` | `34` |
| anchor_G | `16,23` | `24,18` | `0x003C` | `0x0014` | `42` | `42` |
| anchor_H | `17,23` | `24,19` | `0x003E` | `0x0015` | `35` | `35` |

Transform confidence: **HIGH**. The target cells are now exact, not substituted from the earlier BG-cell audit.

## The 4 Exact Cells

All four magenta-marked cells are PC080SN **FG** glyph/symbol cells, not the earlier audited PC080SN BG block-copy cells.

| Target | Layer | FG row/col | Attr HW_ADDRESS | Code HW_ADDRESS | Attr | Code | Tile code | Color bank | Flip X/Y |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| magenta_A | FG | `23,17` | `0x00C09744` | `0x00C09746` | `0x0000` | `0x0022` | `0x0022` | `0` | no/no |
| magenta_B | FG | `23,22` | `0x00C09758` | `0x00C0975A` | `0x0000` | `0x0027` | `0x0027` | `0` | no/no |
| magenta_C | FG | `23,24` | `0x00C09760` | `0x00C09762` | `0x0000` | `0x002C` | `0x002C` | `0` | no/no |
| magenta_D | FG | `24,20` | `0x00C09850` | `0x00C09852` | `0x0000` | `0x003F` | `0x003F` | `0` | no/no |

Composition class per cell: **unique low-code punctuation/symbol glyph**, not horizontal flip, not vertical flip, not both. No byte-identical preloaded alias was found for any of `0x0022`, `0x0027`, `0x002C`, or `0x003F` in `build/regions/pc080sn.bin` / `build/pc080sn_scene_preload_title.bin`.

## Tile PNG Exports

Arcade tile PNGs:

- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/magenta_A_ARCADE_code0022_color000.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/magenta_B_ARCADE_code0027_color000.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/magenta_C_ARCADE_code002C_color000.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/magenta_D_ARCADE_code003F_color000.png`

Build 0106 direct-mapped tile PNGs:

- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/magenta_A_BUILD0106_direct_slot0000.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/magenta_B_BUILD0106_direct_slot0000.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/magenta_C_BUILD0106_direct_slot0000.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/magenta_D_BUILD0106_direct_slot0000.png`

Side-by-side compare:

- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/taito_magenta_cells_ARCADE_vs_BUILD0106_compare.png`

Overlay PNGs:

- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/build0106_magenta_cells_overlay.png`
- `states/screenshots/build_0106_taito_magenta_cell_arcade_intent/arcade_reference_same_cells_overlay.png`

Arcade vs Build PNG verdict: **DIFFER**. Arcade tiles are nonblank red punctuation/symbol shapes; Build 0106 direct slot is `0x0000` / blank for all four cells.

## Build 0106 Handling

The exact cells are routed through the opcode-replaced glyph renderer, but the direct tile LUT maps their tile codes to slot `0x0000`, so the staging helper writes blank cells.

| Target | Tile code | Direct LUT slot | Attr LUT word | Expected staged word | Runtime title write evidence | Build 0106 handling |
|---|---:|---:|---:|---:|---|---|
| magenta_A | `0x0022` | `0x0000` | `0x0000` | `0x0000` | `post-PC 0x070956`, data `0x0000`, staged `0x00FF5BBC` | routed, staged zero |
| magenta_B | `0x0027` | `0x0000` | `0x0000` | `0x0000` | `post-PC 0x070956`, data `0x0000`, staged `0x00FF5BC6` | routed, staged zero |
| magenta_C | `0x002C` | `0x0000` | `0x0000` | `0x0000` | `post-PC 0x070956`, data `0x0000`, staged `0x00FF5BCA` | routed, staged zero |
| magenta_D | `0x003F` | `0x0000` | `0x0000` | `0x0000` | `post-PC 0x070956`, data `0x0000`, staged `0x00FF5C42` | routed, staged zero |

Notes:

- `post-PC 0x070956` is the debugger-reported PC after the store instruction. The actual store is `runtime_genesis_pc 0x00070952: move.w %d1,(%a6,%d2.w)`.
- The adjacent anchor cells are written by the same path and receive nonzero data, proving the renderer/hook/store path is active for this logo region.
- The exact cells are not `raw-unrouted`; they are `opcode_replace routed -> genesis_only staging`, with a zero tile slot.

## Writer-PC / Address-Map Classification

Original arcade glyph renderer:

```asm
arcade_pc 0x0003BB66: movew %d2,%a1@+   ; attr word
arcade_pc 0x0003BB68: movew %d0,%a1@+   ; code word
```

JSON-derived Build 0106 mapping:

| runtime_genesis_pc / genesis_rom_offset | JSON segment | Segment kind | mapped arcade_pc | Exact? | Classification |
|---:|---|---|---:|---|---|
| `0x0003BD48` | `0x03BD48..0x03BD7C` | `patched_site` | `0x0003BB48` | YES | glyph renderer wrapper calls hook |
| `0x0003BD66` | `0x03BD48..0x03BD7C` | `patched_site` | `0x0003BB66` | YES | original attr-store location is inside replaced span |
| `0x0003BD68` | `0x03BD48..0x03BD7C` | `patched_site` | `0x0003BB68` | YES | original code-store location is inside replaced span |
| `0x00070952` | `0x070000..0x17CD68` | `genesis_only` | N/A | YES | actual FG staging store helper |

The `0x0003BD66/0x0003BD68` bytes are NOP padding in the replaced span, but this is not no-op suppression of these cells: the wrapper at `runtime_genesis_pc 0x0003BD48` calls `genesistan_hook_glyph_renderer_3bd48`, and the runtime watchpoint proves the hook writes the target/anchor staged WRAM cells.

## No-Op / Suppression Cross-Check

Historical no-op/suppression sites from the prior correction pass and AGENTS_LOG context include `0x055968`, `0x055990`, and `0x0560DA`, plus CLOSED-003's six-NOP record. None match the exact writer PCs for these four cells.

- Exact original arcade writer PCs: `arcade_pc 0x0003BB66/0x0003BB68` inside the glyph renderer.
- Exact Build 0106 mapped site: `runtime_genesis_pc 0x0003BD48..0x0003BD7C` `patched_site` wrapper.
- Exact Build 0106 runtime store: `runtime_genesis_pc 0x00070952` `genesis_only`.

No-op/suppression for the exact magenta cells: **DISPROVEN**.

## Attr / Flip Preservation

All four exact cells use attr `0x0000`:

- color bank = `0`
- flip X = false
- flip Y = false

Therefore these exact cells do **not** test nontrivial color-bank or flip preservation. Their failure is not attr/flip-related. Prior routed-path evidence still applies: the hook mechanically carries flip bits into its attr LUT index, while full `attr & 0x01ff` color-bank preservation remains limited, but that limitation is not load-bearing for these cells.

## Corrected TAITO Defect Class

Observable facts:

- The user-marked magenta cells are exact screen cells `(15,22)`, `(20,22)`, `(22,22)`, `(18,23)`.
- Both Build 0106 and original arcade coordinate transforms validate these as PC080SN FG row/col `23,17`, `23,22`, `23,24`, and `24,20`.
- Original arcade runtime FG tilemap contains nonblank glyph codes `0x0022`, `0x0027`, `0x002C`, and `0x003F` at those cells.
- Build 0106 routes those cells through the glyph renderer hook and writes staged word `0x0000` for each because direct LUT slots for the four low tile codes are `0x0000`.
- Adjacent visible anchors go through the same path and stage nonzero words.

Interpretation:

**Corrected TAITO defect class for the magenta-marked cells:** low-code punctuation/symbol tile LUT / title-preload coverage gap in the FG glyph path. It is not the earlier audited BG `0x22CB..0x22CE` block-copy case, not the raw `0x00C09172` writer, not attr/flip loss, and not no-op/suppression.

## Open / Closed Issues Impact

- OPEN-001: context extended; exact Build 0106 visible TAITO holes now classified.
- OPEN-017: context only; raw `0x00C09172` remains a separate class.
- OPEN-015: not touched.
- New issues opened: NONE.
- Issues closed: NONE.

## KNOWN_FINDINGS Impact

Option A: no `KNOWN_FINDINGS.md` update in this evidence-only task. This is a precise evidence correction/classification for the exact magenta-marked cells; canonicalization can be handled after the team accepts the classification.

## STOP Status

STOP triggered: **NO**.

Both coordinate transforms were validated against visible anchors, original arcade title tilemap source was available, required writer PCs were exactly mapped through `address_map.json`, and no fix design or implementation was performed.

## Non-Actions

- No source changes.
- No spec changes.
- No tool changes.
- No ROM/build changes.
- No bookmark cycle.
- No diagnostics inserted into ROM.
- No fix design.
- No implementation.
