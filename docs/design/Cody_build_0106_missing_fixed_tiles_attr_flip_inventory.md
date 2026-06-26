# Cody - Build 0106 Missing Fixed Tiles Attr/Flip Inventory

**Date:** 2026-06-26  
**Type:** Evidence / analysis only  
**Build context:** Build 0106, `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`  
**Build 0106 SHA256:** `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`  
**Scope:** Inventory missing/faulting fixed tile cells for punctuation and red TAITO attr/flip status. No source/spec/tool/ROM/build changes. No bookmarks. No inserted diagnostics. No fix design.

## Phase 0

`RULES.md`, `ARCHITECTURE.md`, and latest `AGENTS_LOG.md` context were read before evidence work. Architecture compliance: **PASS**. This task observes arcade intent and the translated Build 0106 runtime only; it does not alter program behavior.

Address discipline: PC correlations use `build/rastan-direct/address_map.json`. No global `+0x200/-0x200` arithmetic is used as authority. Hardware and staging addresses are labeled separately from code PCs.

## Evidence Artifacts

Trace / dump directory:

`states/traces/build_0106_missing_fixed_tiles_attr_flip_inventory_20260626_111500/`

Key files:

- `mame_build0106_inventory.cmd` - Build 0106 MAME debugger script with HW watchpoints and staging dumps.
- `native_debug_trace.log` - trace log for HW watchpoints and boundary dumps.
- `staged_bg_at_03ac88.dump` - Build 0106 `staged_bg_buffer` at the title handler/kick boundary.
- `staged_fg_at_03acfe.dump` - Build 0106 `staged_fg_buffer` after the story/title text producer tail.
- `staged_bg_at_03acfe.dump` - Build 0106 `staged_bg_buffer` after the later story-page replacement.
- `mame_build0106_staging_watch.cmd` - Build 0106 MAME debugger script with selected staging watchpoints.
- `staging_watch_trace.log` - per-cell staging writer evidence.
- `inventory_cells.json` - reduced machine-readable cell table.

Screenshot / PNG evidence:

- `states/screenshots/build_0106_missing_fixed_tiles_attr_flip_inventory/arcade_insert_punctuation_cells.png`
- `states/screenshots/build_0106_missing_fixed_tiles_attr_flip_inventory/build0106_insert_punctuation_staged_cells.png`
- `states/screenshots/build_0106_missing_fixed_tiles_attr_flip_inventory/arcade_red_taito_cells.png`
- `states/screenshots/build_0106_missing_fixed_tiles_attr_flip_inventory/build0106_red_taito_staged_cells.png`

Throwaway reducer/export script:

`states/scripts/build0106_missing_fixed_tiles_inventory.py`

Original arcade runtime sources reused:

- `states/traces/original_arcade_attract_page_replacement_20260623_171701/fg_after_producer_03aaf8.bin`
- `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/arcade_pc080sn_bg_after_title.bin`

## PC080SN Decode Source

Authoritative local MAME source:

- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp:11-18`: standard memory layout has BG at offsets `0x0000..0x3fff` and FG at `0x8000..0xbfff`; standard tilemaps are 64x64, 8x8.
- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp:133-147`: in standard mode, paired words are `attr = bg_ram[N][2*tile_index]`, `code = bg_ram[N][2*tile_index+1] & 0x3fff`, color is `attr & 0x1ff`, and flip is `TILE_FLIPYX((attr & 0xc000) >> 14)`.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:318`: `HW_ADDRESS 0x00C00000..0x00C0FFFF` maps to PC080SN word reads/writes.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:407-408`: PC080SN graphics use `gfx_8x8x4_packed_msb`.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:455`: palette format is xBGR-555.

## Task A/B - INSERT COIN(S) Punctuation

Observable arcade facts from original arcade FG dump after producer `arcade_pc 0x03AAF8`:

`INSERT COIN(S)` occupies FG row `8`; the relevant cells are one tile each:

| Cell | Layer | Row/Col | Attr HW_ADDRESS | Code HW_ADDRESS | Attr | Code | Decoded tile | Color | Flip X/Y | Pixel pos unscrolled |
|---|---|---:|---|---|---:|---:|---:|---:|---|---:|
| left paren | FG | `8,27` | `0x00C0886C` | `0x00C0886E` | `0x0000` | `0x0028` | `0x0028` | `0` | `false/false` | `216,64` |
| `S` | FG | `8,28` | `0x00C08870` | `0x00C08872` | `0x0000` | `0x0053` | `0x0053` | `0` | `false/false` | `224,64` |
| right paren | FG | `8,29` | `0x00C08874` | `0x00C08876` | `0x0000` | `0x0029` | `0x0029` | `0` | `false/false` | `232,64` |

Observable conclusion: **the parens are distinct glyph codes** (`0x0028` and `0x0029`), one tile each. They are not flipped comma copies in the original arcade tilemap data.

Nearby story punctuation / confirmed special comma-like glyph:

| Cell | Layer | Row/Col | Attr HW_ADDRESS | Code HW_ADDRESS | Attr | Code | Decoded tile | Color | Flip X/Y | Pixel pos unscrolled |
|---|---|---:|---|---|---:|---:|---:|---:|---|---:|
| story comma/special glyph | FG | `17,28` | `0x00C09170` | `0x00C09172` | `0x0000` | `0x2749` | `0x2749` | `0` | `false/false` | `224,136` |

Build 0106 comparison:

| Cell | Staged WRAM address | Build 0106 staged word | Expected translated word | Staging writer evidence | Build 0106 status |
|---|---|---:|---:|---|---|
| left paren | `0x00FF5450` | `0x0000` | `0x0000` because tile slot LUT maps `0x0028 -> 0x0000` | `runtime_genesis_pc 0x00070952` store, logged post-PC `0x00070956`, `genesis_only` | routed, but zero/blank due tile mapping/preload gap |
| `S` | `0x00FF5452` | `0x0028` | `0x0028` | `runtime_genesis_pc 0x00070952` store, logged post-PC `0x00070956`, `genesis_only` | routed and present |
| right paren | `0x00FF5454` | `0x0000` | `0x0000` because tile slot LUT maps `0x0029 -> 0x0000` | `runtime_genesis_pc 0x00070952` store, logged post-PC `0x00070956`, `genesis_only` | routed, but zero/blank due tile mapping/preload gap |
| story comma/special glyph | `0x00FF58D2` | `0x0000` | `0x0039` for tile `0x2749`, attr `0x0000` | routed text path writes zero first at `0x00070952`; then raw HW write at `runtime_genesis_pc 0x0003ACEA` writes `0x2749` to `HW_ADDRESS 0x00C09172` | raw/unrouted PC080SN code-word write; mapping exists but is not used by that instruction |

Raw HW watchpoints for the paren/S cells did **not** fire during the Build 0106 capture window. The only selected FG HW watchpoint that fired was the known raw write at `HW_ADDRESS 0x00C09172`.

Address-map classification:

- `runtime_genesis_pc 0x00070952` is in the JSON `genesis_only` wrapper segment.
- `runtime_genesis_pc 0x0003ACEA` is in JSON segment `0x03AB20..0x03AD00`, kind `arcade_copy`, source `whole_maincpu_copy`, mapped exactly to `arcade_pc 0x0003AAEA` by segment-relative JSON mapping.

Interpretation:

- `INSERT COIN(S)` parens are **not** raw/unrouted writes and not attr/flip failures. They are routed to FG staging but stage `0x0000` because the Build 0106 tile LUT does not provide nonzero slots for arcade tile codes `0x0028` and `0x0029`.
- The nearby story comma/special glyph is the already-confirmed raw copied PC080SN write at `runtime_genesis_pc 0x0003ACEA`; its Build 0106 tile mapping exists (`0x2749 -> slot 0x0039`) but the raw instruction bypasses staging.

## Task C/D - Red TAITO Missing Tile Intent

Observable arcade facts from the original arcade title BG dump after title handler:

The audited red TAITO 2x2 cells are in PC080SN BG. These are the same four cells identified by the earlier original-arcade title-art audit from the source/runtime title block.

| Cell | Layer | Row/Col | Attr HW_ADDRESS | Code HW_ADDRESS | Attr | Code | Decoded tile | Color | Flip X/Y | Pixel pos unscrolled |
|---|---|---:|---|---|---:|---:|---:|---:|---|---:|
| red TAITO top-left | BG | `21,23` | `0x00C0155C` | `0x00C0155E` | `0x0001` | `0x22CB` | `0x22CB` | `1` | `false/false` | `184,168` |
| red TAITO top-right | BG | `21,24` | `0x00C01560` | `0x00C01562` | `0x0001` | `0x22CC` | `0x22CC` | `1` | `false/false` | `192,168` |
| red TAITO bottom-left | BG | `22,23` | `0x00C0165C` | `0x00C0165E` | `0x0001` | `0x22CD` | `0x22CD` | `1` | `false/false` | `184,176` |
| red TAITO bottom-right | BG | `22,24` | `0x00C01660` | `0x00C01662` | `0x0001` | `0x22CE` | `0x22CE` | `1` | `false/false` | `192,176` |

Mirror/flip check:

- The four red TAITO cells use four distinct tile codes: `0x22CB`, `0x22CC`, `0x22CD`, `0x22CE`.
- In the original arcade title BG dump, each code appears only at the listed cell.
- Each attr word is `0x0001`; flip X and flip Y are both false for all four cells.
- No visible mirror-source counterpart using the same code with alternate flip bits was identified for these audited cells.

Build 0106 comparison at title boundary `runtime_genesis_pc 0x0003AC88`:

| Cell | Staged WRAM address | Build 0106 staged word | Expected translated word | Staging writer evidence | Build 0106 status |
|---|---|---:|---:|---|---|
| red TAITO top-left | `0x00FF4AC8` | `0x2157` | `0x2157` | exact store `runtime_genesis_pc 0x000707CE`, logged post-PC `0x000707D2`, `genesis_only` | staged correctly |
| red TAITO top-right | `0x00FF4ACA` | `0x2158` | `0x2158` | exact store `runtime_genesis_pc 0x000707CE`, logged post-PC `0x000707D2`, `genesis_only` | staged correctly |
| red TAITO bottom-left | `0x00FF4B48` | `0x2159` | `0x2159` | exact store `runtime_genesis_pc 0x000707CE`, logged post-PC `0x000707D2`, `genesis_only` | staged correctly |
| red TAITO bottom-right | `0x00FF4B4A` | `0x215A` | `0x215A` | exact store `runtime_genesis_pc 0x000707CE`, logged post-PC `0x000707D2`, `genesis_only` | staged correctly |

Later at the story producer boundary `runtime_genesis_pc 0x0003ACFE`, these same BG staged cells are `0x0000`. The staging watchpoint log shows they are cleared by the later BG/FG page replacement path before the story page (`runtime_genesis_pc 0x0007063C/0x00070640` family, logged post-PC `0x00070640`). That later clear is expected page replacement evidence, not evidence that the initial title red TAITO cells failed to stage.

Interpretation:

- The audited red TAITO cells are **not** raw/unrouted in Build 0106 at the title boundary.
- The audited red TAITO cells do **not** require attr flip bits in the original arcade runtime state.
- For these four cells, Build 0106 stages the expected Genesis nametable words. If they are visually absent in a particular capture, this inventory does not support blaming tile preload/mapping, raw write routing, or attr/flip preservation for these exact cells. The remaining visual failure would need to be downstream of staging, timing/window/scroll/commit/palette, or a different set of cells than the four audited here.

## Task E - Routed Attr/Flip Path Check

Relevant Build 0106 generated disassembly / source path:

- `runtime_genesis_pc 0x0003BD48` is the opcode-replaced glyph/string renderer wrapper.
- `runtime_genesis_pc 0x00070D4E` (`genesistan_hook_glyph_renderer_3bd48`) decodes the descriptor and text bytes.
- `runtime_genesis_pc 0x00070D88..0x00070DA6` loads `genesistan_pc080sn_tile_vram_lut`, `genesistan_pc080sn_attr_lut`, and `staged_fg_buffer`, then calls shared store composition.
- `runtime_genesis_pc 0x00070984..0x000709A2` composes `tile_slot | translated_attr`.
- `runtime_genesis_pc 0x000709A4..0x000709DA` range-checks the FG C-window destination and computes row/column.
- `runtime_genesis_pc 0x00070952` stores the composed word to `staged_fg_buffer` and marks `fg_row_dirty`.

What it stages:

- The routed FG text/glyph path stages **code + attr** as one Genesis nametable word.
- The tile component comes from `genesistan_pc080sn_tile_vram_lut` indexed by `code & 0x3fff`.
- The attr component comes from `genesistan_pc080sn_attr_lut` after compressing selected PC080SN attr bits.

Attr/flip bit handling:

`Ltw_translate_attr` / equivalent generated code derives the attr LUT index as:

```text
index bit 0..1 = attr bits 0..1
index bit 2    = attr bit 14
index bit 3    = attr bit 15
index bit 4    = attr bit 13
```

So the routed path does carry the two PC080SN flip bits (`attr & 0xC000`) into the attr LUT lookup. It also carries `attr bit 13`. It does **not** carry the full `attr & 0x01FF` color-bank field; for example, most color bits above low bits are not represented in this 32-entry effective index space. For the audited cells this limitation is not load-bearing because:

- INSERT punctuation attr is `0x0000`.
- Story comma/special attr is `0x0000`.
- Red TAITO attr is `0x0001`.
- All audited flip bits are zero.

Verdict for the asked path: **code + attr are staged; flip bits are mechanically preserved by the routed attr index path, but full color-bank preservation is partial/limited.**

## Task F - Unified Classification Table

| Symptom group | Layer | Row/Col | Attr HW_ADDRESS | Code HW_ADDRESS | Attr | Code | Tile | Color | Flip X/Y | Arcade writer PC | Build writer PC | Map class | Build 0106 staging | Tile mapping/preload | Attr/flip preservation | Defect class |
|---|---|---:|---|---|---:|---:|---:|---:|---|---|---|---|---|---|---|---|
| INSERT left paren | FG | `8,27` | `0x00C0886C` | `0x00C0886E` | `0x0000` | `0x0028` | `0x0028` | `0` | no/no | `arcade_pc 0x03AAAE -> 0x03BB48` routed glyph producer | exact `runtime_genesis_pc 0x00070952` | `genesis_only` | stages `0x0000` | slot is `0x0000` | attr zero; flip none | tile mapping/preload gap |
| INSERT `S` | FG | `8,28` | `0x00C08870` | `0x00C08872` | `0x0000` | `0x0053` | `0x0053` | `0` | no/no | `arcade_pc 0x03AAAE -> 0x03BB48` routed glyph producer | exact `runtime_genesis_pc 0x00070952` | `genesis_only` | stages `0x0028` | slot present `0x0028` | attr zero; flip none | no defect for this control cell |
| INSERT right paren | FG | `8,29` | `0x00C08874` | `0x00C08876` | `0x0000` | `0x0029` | `0x0029` | `0` | no/no | `arcade_pc 0x03AAAE -> 0x03BB48` routed glyph producer | exact `runtime_genesis_pc 0x00070952` | `genesis_only` | stages `0x0000` | slot is `0x0000` | attr zero; flip none | tile mapping/preload gap |
| story comma/special | FG | `17,28` | `0x00C09170` | `0x00C09172` | `0x0000` | `0x2749` | `0x2749` | `0` | no/no | `arcade_pc 0x0003AAEA` absolute write | exact `runtime_genesis_pc 0x0003ACEA` | `arcade_copy` | routed path leaves `0x0000`; raw write bypasses staging | mapping exists: slot `0x0039` | attr zero; flip none | raw copied PC080SN write |
| red TAITO top-left | BG | `21,23` | `0x00C0155C` | `0x00C0155E` | `0x0001` | `0x22CB` | `0x22CB` | `1` | no/no | `arcade_pc 0x05A4DE` block-copy path | exact `runtime_genesis_pc 0x000707CE` | `genesis_only` | stages `0x2157` at title boundary | slot present `0x0157` | attr `0x0001 -> 0x2000`; flip none | no defect for audited cell |
| red TAITO top-right | BG | `21,24` | `0x00C01560` | `0x00C01562` | `0x0001` | `0x22CC` | `0x22CC` | `1` | no/no | `arcade_pc 0x05A4DE` block-copy path | exact `runtime_genesis_pc 0x000707CE` | `genesis_only` | stages `0x2158` at title boundary | slot present `0x0158` | attr `0x0001 -> 0x2000`; flip none | no defect for audited cell |
| red TAITO bottom-left | BG | `22,23` | `0x00C0165C` | `0x00C0165E` | `0x0001` | `0x22CD` | `0x22CD` | `1` | no/no | `arcade_pc 0x05A4DE` block-copy path | exact `runtime_genesis_pc 0x000707CE` | `genesis_only` | stages `0x2159` at title boundary | slot present `0x0159` | attr `0x0001 -> 0x2000`; flip none | no defect for audited cell |
| red TAITO bottom-right | BG | `22,24` | `0x00C01660` | `0x00C01662` | `0x0001` | `0x22CE` | `0x22CE` | `1` | no/no | `arcade_pc 0x05A4DE` block-copy path | exact `runtime_genesis_pc 0x000707CE` | `genesis_only` | stages `0x215A` at title boundary | slot present `0x015A` | attr `0x0001 -> 0x2000`; flip none | no defect for audited cell |

## Unified Verdict

**Verdict:** **MIXED CLASS**.

Observable facts:

- The confirmed `0x00C09172` special-comma cell is a raw copied PC080SN write and bypasses staging.
- The `INSERT COIN(S)` parens are routed through the FG staging path, but stage blank because their tile codes map to slot `0x0000` in Build 0106.
- The audited red TAITO cells stage correctly at the title boundary with expected tile slots and attr words; the arcade attrs contain no flip bits for these cells.

Interpretation:

- One routing/attr-preservation pass cannot fix all confirmed cases. It would address the raw `0x00C09172` writer class, but it would not fix the parens' zero tile-slot mapping, and it is not implicated by the audited red TAITO cells.
- The red TAITO mirror/flip hypothesis is **not supported** for these four cells: they are distinct tile codes, not flipped variants.

What remains unknown:

- Whether a different visual red-TAITO symptom refers to cells outside the four audited `0x22CB..0x22CE` cells.
- Whether current visual absence of those staged red cells, if observed, is caused downstream by VDP commit, scroll/window/origin, palette visibility, timing, or later page clear rather than staging.
- Whether additional punctuation beyond the audited parens and `0x2749` special glyph has missing tile-LUT coverage.

## STOP Status

STOP triggered: **NO**.

All required evidence for the audited cells was obtained:

- PC080SN format confirmed from local MAME source.
- Original arcade runtime tilemap cells identified from arcade runtime dumps.
- Build 0106 staging state inspected via MAME debugger dumps/watchpoints.
- Required raw writer PC `0x0003ACEA` mapped exactly through `address_map.json`.
- No fix design or implementation was performed.

## Non-Actions

- No source changes.
- No spec changes.
- No tool changes.
- No ROM/build changes.
- No bookmark cycle.
- No diagnostics inserted into ROM.
- No issue opened or closed.
- No fix design or implementation.

## Open / Known Findings Impact

- OPEN-017: context extended; raw `0x00C09172` writer remains one class, but parens are a separate tile mapping/preload class.
- OPEN-001: context extended for visible fixed-tile rendering failures.
- OPEN-015: not touched.
- `KNOWN_FINDINGS.md`: no update from this evidence-only task.
