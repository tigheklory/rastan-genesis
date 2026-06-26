# Cody - Build 0106 Correction Pass: Red TAITO Arcade Intent + Paren LUT

**Date:** 2026-06-26  
**Type:** Evidence / analysis correction only  
**Build context:** Build 0106, `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`  
**Build 0106 SHA256:** `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`  
**Scope:** Correct the previous staging-only overclaims for red TAITO and `INSERT COIN(S)` parens. No source/spec/tool/ROM/build changes. No bookmarks. No inserted diagnostics. No fix design.

## Phase 0

Read before evidence work:

- `RULES.md`
- `ARCHITECTURE.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- latest `AGENTS_LOG.md` entries
- `docs/design/Cody_build_0106_missing_fixed_tiles_attr_flip_inventory.md`
- `docs/design/Cody_build_0106_tile_c09172_decode_export.md`
- `docs/design/Cody_build_0106_c09172_writer_watchpoint.md`
- `docs/design/Cody_build_0095_arcade_title_tile_usage_audit.md`
- `docs/design/Andy_build_0095_taito_logo_producer_attribution.md`
- `docs/design/Cody_original_arcade_attract_page_replacement_runtime.md`

Architecture compliance: **PASS**. This task observes original arcade runtime/tilemap data and Build 0106 artifacts only. No program behavior was changed.

Address discipline: instruction/code PC correlations use `build/rastan-direct/address_map.json`. Hardware tilemap addresses and staged WRAM addresses are labeled separately and are not inferred through the PC map.

## Ledger / History Search

Search terms included `TAITO`, `PC080SN`, `0xC0`, `C015`, `C016`, `C088`, `C091`, `no-op`, `nop`, `suppress`, `drop`, `bypass`, `raw write`, `VDP mirror`, and `strict crash` across docs, issue ledgers, and `AGENTS_LOG.md`.

Relevant findings:

- Historical PC080SN suppression/NOP evidence exists in the project record. Examples include `AGENTS_LOG.md` entries around old C-window paths where ROM sites such as `0x055968`, `0x055990`, and `0x0560DA` were recorded as NOPped/suppressed in an earlier Build 106-era analysis, and `CLOSED_ISSUES.md` `CLOSED-003` records six NOPs that suppressed screen-flip/DMA-trigger writes rather than palette writes.
- Current Build 0106 evidence also contains a confirmed raw copied PC080SN write: `runtime_genesis_pc 0x0003ACEA` writes `0x2749` to `HW_ADDRESS 0x00C09172`; `address_map.json` maps it exactly to `arcade_pc 0x0003AAEA` in an `arcade_copy` segment.
- The ledger search does **not** prove that the exact user-visible red TAITO missing cells were no-oped or suppressed. It only keeps that hypothesis open until the exact visual cells and their writer PCs are identified.

Prior no-op/suppression evidence found: **YES, historical / class-level.**  
No-op/suppression proven for exact visually missing red TAITO cells: **UNKNOWN**.

## PC080SN Decode Source

Authoritative local MAME source:

- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp:11-18`: standard layout, two 64x64 tilemaps with 8x8 tiles; BG at PC080SN offset `0x0000..0x3fff`, FG at `0x8000..0xbfff`.
- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp:79-82`: standard mode creates 64x64 8x8 tilemaps.
- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp:133-147`: paired words; `code = word & 0x3fff`, color `attr & 0x1ff`, flip `TILE_FLIPYX((attr & 0xc000) >> 14)`.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:318`: `HW_ADDRESS 0x00C00000..0x00C0FFFF` maps to PC080SN.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:407-408`: PC080SN graphics use `gfx_8x8x4_packed_msb`.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:455`: palette format is xBGR-555.

## Address Map Checks

Instruction/code PCs used in this correction:

| runtime_genesis_pc | JSON segment | Segment kind | arcade_pc | Exact? | Notes |
|---:|---|---|---:|---|---|
| `0x0003ACEA` | `0x03AB20..0x03AD00` | `arcade_copy` | `0x0003AAEA` | YES | raw `movew #0x2749,0x00c09172` |
| `0x0003BD48` | `0x03BD48..0x03BD7C` | `patched_site` | `0x0003BB48` | YES | glyph/string renderer wrapper |
| `0x0005A58E` | `0x05A48A..0x05A6DE` | `arcade_copy` | `0x0005A38E` | YES | title BG block producer entry |
| `0x0005A6DE` | `0x05A6DE..0x05A6E8` | `patched_site` | `0x0005A4DE` | YES | title BG block-copy patched site |
| `0x000707CE` | `0x070000..0x17CD68` | `genesis_only` | N/A | YES | BG staging store helper site |
| `0x00070952` | `0x070000..0x17CD68` | `genesis_only` | N/A | YES | FG staging store helper site |

`genesis_rom_offset` is equal to `runtime_genesis_pc` in this port context, per KF-004; no arcade-to-Genesis proof depends on arithmetic offset assumptions.

## TAITO Correction

### Task 1 - Exact Visually Missing Cells

Result: **PARTIAL / UNKNOWN**.

Current workspace evidence for Build 0106 includes:

- original arcade title BG dump: `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/arcade_pc080sn_bg_after_title.bin`
- Build 0106 staging dumps and staging watch traces: `states/traces/build_0106_missing_fixed_tiles_attr_flip_inventory_20260626_111500/`
- staged-cell comparison image: `states/screenshots/build_0106_missing_fixed_tiles_attr_flip_inventory/build0106_red_taito_staged_cells.png`

Those artifacts verify **four audited red TAITO cells** at the title boundary, but they do not contain a Build 0106 rendered full-screen image/VDP output with the exact user-visible red TAITO missing cells marked. Therefore this correction pass cannot prove that the four audited cells are the exact four visually missing cells reported by the user.

STOP for the TAITO visual-identification subtask: the exact visually missing Build 0106 red TAITO cells are **not identified from current evidence**.

### Audited Cells Preserved As Evidence, Not Closure

The previous four audited cells remain valid evidence, but only for those coordinates:

| Cell | Layer | Row/Col | Attr HW_ADDRESS | Code HW_ADDRESS | Attr | Code | Decoded tile | Color | Flip X/Y | Build staged WRAM | Build staged word |
|---|---|---:|---|---|---:|---:|---:|---:|---|---|---:|
| red TAITO audited TL | BG | `21,23` | `0x00C0155C` | `0x00C0155E` | `0x0001` | `0x22CB` | `0x22CB` | `1` | false/false | `0x00FF4AC8` | `0x2157` |
| red TAITO audited TR | BG | `21,24` | `0x00C01560` | `0x00C01562` | `0x0001` | `0x22CC` | `0x22CC` | `1` | false/false | `0x00FF4ACA` | `0x2158` |
| red TAITO audited BL | BG | `22,23` | `0x00C0165C` | `0x00C0165E` | `0x0001` | `0x22CD` | `0x22CD` | `1` | false/false | `0x00FF4B48` | `0x2159` |
| red TAITO audited BR | BG | `22,24` | `0x00C01660` | `0x00C01662` | `0x0001` | `0x22CE` | `0x22CE` | `1` | false/false | `0x00FF4B4A` | `0x215A` |

Observable facts for these audited cells:

- They are four distinct tile codes: `0x22CB`, `0x22CC`, `0x22CD`, `0x22CE`.
- Attr is `0x0001` for all four, so color bank is `1` and flip bits are clear.
- No visible mirror-source counterpart using the same tile code with alternate flip bits was found in the original arcade title BG dump for these audited coordinates.
- Build 0106 stages these four cells at title boundary through the `genesis_only` BG staging path, with expected words `0x2157..0x215A`.
- Later story-page replacement clears these staged cells, but that is a later page transition and not evidence of title-boundary staging failure.

Interpretation bounded to audited cells only:

- These four audited cells do **not** support a mirror/flip explanation.
- These four audited cells do **not** support a raw/unrouted or no-op/suppression explanation at title-boundary staging.
- This does **not** close the user-visible red TAITO issue, because the exact missing visual cells remain unidentified.

### TAITO Writer Classification Status

For the audited four cells, the mapped site is:

- title block-copy producer entry: `runtime_genesis_pc 0x0005A58E`, JSON segment `0x05A48A..0x05A6DE`, kind `arcade_copy`, exact mapped `arcade_pc 0x0005A38E`.
- block-copy patched site: `runtime_genesis_pc 0x0005A6DE`, JSON segment `0x05A6DE..0x05A6E8`, kind `patched_site`, exact mapped `arcade_pc 0x0005A4DE`.
- Build staging store evidence: `runtime_genesis_pc 0x000707CE`, JSON segment `0x070000..0x17CD68`, kind `genesis_only`.

Mapped-site classification for audited cells: **opcode_replace / genesis_only routed staging**, not raw/unrouted, not no-op/suppressed.

Mapped-site classification for exact visually missing TAITO cells: **UNKNOWN**, because the exact cells are not identified.

Corrected TAITO defect class: **UNKNOWN / PARTIAL**. Prior statement “audited cells stage correctly” remains true for audited cells, but it must not be applied to the exact visually missing red TAITO symptom until those cells are identified from Build 0106 rendered evidence.

## Paren Correction

### Original Arcade Intent

From original arcade FG dump after producer `arcade_pc 0x03AAF8`, the `INSERT COIN(S)` parens are distinct low tile codes:

| Cell | Layer | Row/Col | Attr HW_ADDRESS | Code HW_ADDRESS | Attr | Code | Decoded tile | Color | Flip X/Y |
|---|---|---:|---|---|---:|---:|---:|---:|---|
| left paren | FG | `8,27` | `0x00C0886C` | `0x00C0886E` | `0x0000` | `0x0028` | `0x0028` | `0` | false/false |
| right paren | FG | `8,29` | `0x00C08874` | `0x00C08876` | `0x0000` | `0x0029` | `0x0029` | `0` | false/false |

They are not flipped comma copies.

### Build 0106 LUT / Preload / Pattern Evidence

Direct LUT and preload facts:

| Arcade tile code | Direct LUT result | Direct title preload pair | Byte-identical preloaded alias | Alias slot | Pattern present in title preload? |
|---:|---:|---|---:|---:|---|
| `0x0028` | `0x0000` | none | `0x2747` | `0x0037` | YES, by byte-identical alias |
| `0x0029` | `0x0000` | none | `0x2748` | `0x0038` | YES, by byte-identical alias |

Raw PC080SN tile bytes:

- `0x0028` bytes equal `0x2747` bytes: **YES**.
- `0x0029` bytes equal `0x2748` bytes: **YES**.
- `0x2747` is present in `build/pc080sn_scene_preload_title.bin` as `(tile 0x2747, slot 0x0037)`.
- `0x2748` is present in `build/pc080sn_scene_preload_title.bin` as `(tile 0x2748, slot 0x0038)`.

Evidence export:

- `states/screenshots/build_0106_correction_taito_arcade_intent_paren_lut/build0106_paren_alias_lut_evidence.png`
- `states/screenshots/build_0106_correction_taito_arcade_intent_paren_lut/paren_alias_summary.txt`
- `states/scripts/build0106_correction_paren_alias_lut.py`

### Why Build 0106 Stages Blank For Parens

The routed FG text path indexes `genesistan_pc080sn_tile_vram_lut` by the arcade tile code in the descriptor/text stream.

- For left paren `0x0028`, the direct LUT entry is `0x0000`, so the composed staged word is `0x0000`.
- For right paren `0x0029`, the direct LUT entry is `0x0000`, so the composed staged word is `0x0000`.
- `0x0000` is a legitimate Genesis tile slot in the project, but here it is the blank tile slot; the previous inventory also shows `S` stages as nonzero `0x0028` while parens stage zero at adjacent cells.
- Because byte-identical paren glyph patterns are already present in the title preload under aliases `0x2747/0x2748`, direct preload absence for `0x0028/0x0029` is **not** sufficient to classify the visual failure as a pattern preload gap.

Corrected paren defect class:

- Tile pattern present in title preload / likely VRAM after title preload: **YES, by byte-identical preloaded aliases `0x2747/0x2748`**.
- Direct tile LUT maps `0x0028/0x0029` to nonzero slots: **NO**.
- Staging writes nonzero word for parens: **NO**.
- Preload gap proven: **NO**.
- Corrected class: **tile-code-to-slot alias/LUT omission for low paren codes `0x0028/0x0029`**. The existing tile patterns are present under alias codes, but the routed text path has no direct LUT mapping from the low paren codes to those slots.

## Cross-Check Of Prior Staging-Only Conclusions

| Prior conclusion | Basis | Correction status |
|---|---|---|
| “Audited red TAITO cells stage correctly.” | Staging + original arcade tilemap for four audited cells | Still true for those audited cells only; not proven for exact user-visible missing cells. |
| “Audited red TAITO cells prove red TAITO issue is not attr/flip/raw/no-op.” | Staging only applied too broadly | Corrected: not enough to classify exact visual symptom. Exact missing cells remain unknown. |
| “Parens stage zero, therefore tile mapping/preload gap.” | Staging + direct LUT zero | Corrected: direct LUT zero is real, but preload absence is not proven because byte-identical glyph patterns are preloaded under aliases. |
| “Story `0xC09172` glyph is raw/unrouted.” | HW watchpoint + address_map + mapping evidence | Confirmed; accepted prior finding unchanged. |

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-017, OPEN-015 context only.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: exact Build 0106 rendered red TAITO missing-cell identification, any fix design, raw `0xC09172` routing fix, paren LUT repair, OPEN-015 crash-handler work.

## KNOWN_FINDINGS Impact

Option A: no `KNOWN_FINDINGS.md` update. This is a correction/evidence note. Durable canonicalization should wait until exact visual TAITO cells are identified and the paren alias/LUT finding is accepted into a broader graphics finding.

## STOP Status

STOP triggered for TAITO visual-cell identification: **YES / PARTIAL**. The exact visually missing Build 0106 red TAITO cells cannot be identified from current workspace evidence.

Overall correction deliverable completed: **YES**. Paren classification corrected; audited TAITO evidence bounded; no implementation or fix design performed.

## Non-Actions

- No source changes.
- No spec changes.
- No tool changes.
- No ROM/build changes.
- No bookmark cycle.
- No diagnostics inserted into ROM.
- No fix design.
- No implementation.
