# Cody - Build 0123 PC090OJ Transparent-Pen / Black Overdraw Attribution

**Date:** 2026-07-01  
**Type:** Evidence / attribution only  
**Build:** 0123  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0123.bin`  
**ROM SHA256:** `3a678621d2f71f4a0ce08d7a07d1a55e90e3b9a77cca62d601d4a9cbeb9b3a41`  
**Evidence directory:** `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/`

## Phase 0

Relevant priors:

- KF-010 applies because this task separates real Plane A/B rendering from sprite overdraw in the final composite.
- KF-011 applies because Genesis-side sprite work is helper/hardware-service translation; arcade code remains the program.
- KF-016 applies because title-state PC090OJ clears are part of the object lifecycle context.
- KF-021 applies because stale/suppressed/generated SAT evidence can be misread as sprite absence or correctness.
- KF-026 applies because PC090OJ write coverage and object-RAM mirroring remain high-risk sprite subsystem territory.
- KF-032 applies because raw PC090OJ writes must be routed to staging/mirror rather than Genesis VDP aliases.
- KF-036 applies as address/data-base discipline for helper-side reads and writes.
- KF-038 is context only; row aliasing is not the sprite transparency mechanism under test.

High-rediscovery hazards:

- KF-011 HIGH: easy to accidentally reason as if Genesis owned gameplay/frame lifecycle.
- KF-021 HIGH: staged SAT, true VDP SAT, and linked SAT can diverge and create false visual attribution.
- KF-026 HIGH: partial PC090OJ coverage has caused repeated under-scoping.
- KF-032 HIGH: raw hardware writes can look like rendering bugs.
- KF-036 HIGH: prior helper bugs were caused by wrong address/data bases.

Task classification:

- EVIDENCE / EXTENDING / OPEN-024.
- OPEN-001 and OPEN-006 are context.
- OPEN-023 is out-of-scope Window context.
- OPEN-015 is not touched; no crash/D00298 evidence is used.

Contradiction check:

- CONTRADICTION DETECTED: NO.
- MAME reference behavior agrees with the task premise: PC090OJ sprites are 16x16x4, use `code = word2 & 0x1fff`, draw over PC080SN layers, and use transparent pen 0.

Open/Closed Issues pre-check:

- OPEN-024 primary.
- OPEN-001 context.
- OPEN-006 context.
- OPEN-023 context only; no Window analysis performed.
- OPEN-015 not touched.
- Closed issues: none reopened.

## User Visual Evidence

User observations accepted as visual context:

- Plane A and Plane B are rendering in separated Exodus views.
- The remaining issue is not simply missing PC080SN Plane A/B output.
- Build 0123 shows less black overdraw than Build 0121.
- Some screens show only about 1-3 visible sprites in the Sprite layer.
- The item-scroll Sprite layer includes a 16x16 Genesis sprite boundary with only a small purple/brown visible shape inside it.
- The suspected mechanism is sprite transparency loss, not XOR unless proven.

This report does not use a new screenshot capture; it correlates the existing Build 0123 post-commit PC090OJ evidence with sprite graphics/palette data.

## MAME PC090OJ Reference Model

Verified from in-repo MAME references:

- `docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:97-99`: PC090OJ graphics decode is `gfx_16x16x4_packed_msb`.
- `docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:184-193`: each sprite entry uses word0 color/flip, word1 Y, word2 code, word3 X; `code = word2 & 0x1fff`.
- `docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:210-228`: both priority and non-priority draw paths pass transparent pen `0` to `prio_transpen` / `transpen`.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:227-232`: Rastan derives `sprite_colbank = (sprite_ctrl & 0xe0) >> 1`; priority mask is `0`, meaning sprites over everything.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:249-259`: screen update draws PC080SN layer 0 opaque, layer 1, then PC090OJ sprites.

## Evidence Artifacts

Generated / captured artifacts:

- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/mame_go80_postcommit_palette.cmd`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/postcommit_pc090oj_object_ram_ff674a.txt`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/postcommit_staged_sprite_sat_ff6104.txt`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/postcommit_staged_sprite_descriptor_table_ff6384.txt`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/postcommit_sprite_counts_ctrl_ff6f4a.txt`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/postcommit_state_ff0000_0080.txt`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/postcommit_staged_palette_ff601a.txt`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/analyze_pc090oj_transparency.py`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/pc090oj_transparency_analysis.json`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/pc090oj_transparency_analysis.md`
- `states/traces/build_0123_pc090oj_transparent_pen_black_overdraw_20260701_143334/pc090oj_emitted_slots_source_genesis_mask_contact.png`

Per-slot PNGs were also exported for source pixels, Genesis palette rendering, and opacity masks.

## Black Overdraw Candidates

Ranked by current evidence:

1. **True VDP SAT/VRAM divergence or stale hardware SAT entries**: still plausible because this task captured generated WRAM SAT and descriptor state, not raw VDP VRAM `0xF800..0xFA7F`. If true VDP SAT contains stale reachable entries, large black coverage could happen even when generated SAT reports only four sprites.
2. **Final composite is covered by high-priority sprite output, but not via transparent-pen conversion failure in the four emitted sprites**: possible only if true VDP uses additional/stale sprites or a different SAT/VRAM state than the captured generated WRAM SAT.
3. **Palette makes some nonzero sprite pens very dark**: supported narrowly. Palette line 3 has no exact-black nonzero pens in the emitted sprite cells, but some nonzero pens map to near-black/dark purple-red values. This can create dark sprite pixels, not full-cell transparent-area cover.
4. **Sprite transparent pen conversion failure**: not supported for the four emitted Build 0123 sprites. Source pen 0 remains Genesis index 0.
5. **Code-to-tile stride/bank error**: not supported for the emitted sprites. DMA source uses PC090OJ object code times 128 bytes, and source-vs-converted 16x16 pixels match exactly.
6. **Window layer**: not supported here and out of scope; prior Window work remains context only.
7. **XOR**: not supported; no evidence of XOR blending is present.

Leading hypothesis after this evidence: **the large black cover, if still present in final composite, is more likely stale/true-VDP SAT or another composited layer/state mismatch than transparent-pen loss in the four generated Build 0123 sprites.**

What would disprove the leading hypothesis: a true VDP SAT/VRAM dump at the visible frame matching generated WRAM SAT exactly, plus a sprite-disabled composite proving the black cover persists.

## Emitted Slot Correlation

Build 0123 post-commit facts reused from `states/traces/build_0123_pc090oj_object_ram_phase1_20260701_133359/postcommit_pc090oj_phase1_summary.json` and reproduced in this task:

- Decoded entries: `256`
- Drawable entries: `4`
- Emitted entries: `4`
- Dropped entries: `0`
- `pc090oj_ctrl_shadow = 0x0001`
- `pc090oj_sprite_ctrl_shadow = 0x0060`
- `pc090oj_scan_colbank = 0x0030`
- SAT link chain: `[0, 1, 2, 3]`

| Slot | Source entry | Source words | Code | PC090OJ x/y | Genesis SAT x/y | Screen bbox | SAT tile base | Palette line | Priority | Link | Match class |
|---:|---:|---|---:|---|---|---|---:|---:|---|---:|---|
| 0 | 4 | `0000 0000 0001 0000` | `0x0001` | `(0,0)` | `(0x0080,0x0080)` | `(0,0)-(15,15)` | `0x0400` | 3 | yes | 1 | POSSIBLE MATCH |
| 1 | 14 | `0000 0000 0110 002A` | `0x0110` | `(42,0)` | `(0x00AA,0x0080)` | `(42,0)-(57,15)` | `0x0404` | 3 | yes | 2 | POSSIBLE MATCH, strongest small-shape candidate |
| 2 | 16 | `0000 0080 0080 0000` | `0x0080` | `(0,128)` | `(0x0080,0x0100)` | `(0,128)-(15,143)` | `0x0408` | 3 | yes | 3 | UNKNOWN/POSSIBLE if visual object is at lower screen |
| 3 | 17 | `0000 0080 0080 0001` | `0x0080` | `(1,128)` | `(0x0081,0x0100)` | `(1,128)-(16,143)` | `0x040C` | 3 | yes | 0 | UNKNOWN/POSSIBLE if visual object is at lower screen |

The strongest correspondence to the user-described small purple/brown shape is slot 1, because it has the largest nonzero pixel count and uses palette line 3 dark/purple/brown colors. Without an exact visible-frame coordinate, none of the slots can be promoted to VISIBLE MATCH.

## Transparent Pen Test

Transparent pen test inputs:

- Source PC090OJ graphics: `build/regions/pc090oj.bin`.
- Converted Genesis sprite graphics: `build/pc090oj_genesis.bin`.
- Runtime palette source for color classification: `postcommit_staged_palette_ff601a.txt`.
- Conversion script reference: `tools/translation/preconvert_pc090oj_tiles.py`.

Near-black threshold recorded for evidence: all Genesis 3-bit RGB channels <= 1. Exact black requires CRAM word `0x0000`.

| Slot | Code | Index-0 transparent pixels | Nonzero pixels | Exact-black nonzero pixels | Near-black nonzero pixels | Colored/dark-colored nonzero pixels | Source==converted 16x16 |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | `0x0001` | 210 | 46 | 0 | 0 | 46 | true |
| 1 | `0x0110` | 171 | 85 | 0 | 24 | 61 | true |
| 2 | `0x0080` | 202 | 54 | 0 | 12 | 42 | true |
| 3 | `0x0080` | 202 | 54 | 0 | 12 | 42 | true |

Quadrant-level highlights:

- Slot 0 / code `0x0001`: TR and BR quadrants are entirely index 0; TL/BL contain 46 nonzero colored pixels total.
- Slot 1 / code `0x0110`: TL/TR are entirely index 0; BL/BR contain 85 nonzero pixels, 24 of which are near-black by the recorded threshold.
- Slots 2 and 3 / code `0x0080`: BL/BR mostly empty; nonzero pixels are concentrated in TR plus one TL near-black pixel.

Transparent pen verdict:

- **Transparent pen is preserved for the four emitted Build 0123 sprites.**
- The visually empty/background area is index 0, not nonzero black.
- The large black cover behavior is therefore **not explained** by PC090OJ source pen 0 becoming opaque Genesis black pixels in these emitted sprites.

## PC090OJ Source Graphics Comparison

The source and converted pixels were compared as full 16x16 composed objects:

- Source layout: 16 rows x 8 bytes per PC090OJ 16x16 cell from `build/regions/pc090oj.bin`.
- Converted layout: four Genesis 8x8 tiles per cell in TL, BL, TR, BR order from `build/pc090oj_genesis.bin`.
- For codes `0x0001`, `0x0110`, and `0x0080`, the composed 16x16 converted Genesis cell exactly matches the source PC090OJ nibble-index cell.

Source pen-0 behavior:

- Code `0x0001`: 210/256 pixels are pen 0.
- Code `0x0110`: 171/256 pixels are pen 0.
- Code `0x0080`: 202/256 pixels are pen 0.

Converted Genesis behavior:

- The same counts are preserved.
- The converted quadrants are coherent for the same PC090OJ object.
- No quadrant swap, off-by-one 8x8 tile, off-by-one 16x16 object, or wrong bank is visible in these cell comparisons.

## Code-to-Tile Mapping

The Build 0123 runtime uses a cache-slot style SAT tile base and object-code based DMA source:

- SAT tile base: `SPRITE_TILE_BASE + emitted_slot * 4` in `.Lpc090oj_emit_slot`.
- DMA source: `rastan_pc090oj + code * 128` in `.Lvcs_tile_dma`.
- DMA destination: `(SPRITE_TILE_BASE + emitted_slot * 4) * 32` bytes in VRAM.

Therefore the SAT tile base is slot-local, but the graphics loaded into that slot are source-object-code based.

| Code | Emitted slots | DMA source | Genesis tile destination(s) | Mapping verdict |
|---:|---|---|---|---|
| `0x0001` | slot 0 | `rastan_pc090oj + 0x0001*128` | `0x0400..0x0403` | CORRECT |
| `0x0110` | slot 1 | `rastan_pc090oj + 0x0110*128` | `0x0404..0x0407` | CORRECT |
| `0x0080` | slots 2 and 3 | `rastan_pc090oj + 0x0080*128` | `0x0408..0x040B`, `0x040C..0x040F` | CORRECT and consistent |

Overall mapping verdict: **CORRECT for these emitted sprites.** It is object-code based for the DMA source and four-8x8-tile based for the Genesis SAT destination slot.

## True VDP SAT / VRAM

True VDP SAT captured: **NO**.

What was captured:

- Generated WRAM `staged_sprite_sat` at `Genesis-WRAM 0x00FF6104..0x00FF6383`.
- Generated WRAM `staged_sprite_descriptor_table` at `Genesis-WRAM 0x00FF6384..0x00FF6743`.
- PC090OJ active mirror at `Genesis-WRAM 0x00FF674A..0x00FF6F49`.
- Staged palette at `Genesis-WRAM 0x00FF601A..0x00FF6099`.

Limitation:

- Raw VDP VRAM `0xF800..0xFA7F` was not safely dumped by this workflow. The MAME debugger dump command used here reads CPU-visible memory; direct VDP VRAM introspection was not established without broadening into a new emulator/debugger workflow.

Consequence:

- If true VDP SAT matches generated WRAM SAT, then large black coverage is not explained by Build 0123's four generated sprites unless another layer/composite issue is involved.
- If true VDP SAT differs from generated WRAM SAT, stale hardware SAT or SAT DMA divergence becomes the leading cause of large sprite cover.

## Visual / Layer Check

Sprite-disabled comparison: **not captured in this task**.

Does black coverage disappear with sprites disabled: **UNKNOWN**.

Available visual context remains user-provided:

- Plane A/B are visible in separated views.
- Sprite layer has a small number of visible objects.
- The item-scroll sprite candidate is a 16x16 boundary with a small purple/brown shape inside.

No ROM modification, emulator layer toggle capture, or source-level diagnostic was performed.

## Classification

Final classification: **Transparent-pen conversion failure is refuted for the four emitted Build 0123 PC090OJ sprites in the captured evidence frame.**

Confidence: HIGH for the pixel-index/conversion conclusion; MEDIUM for full visual-overdraw attribution because true VDP SAT/VRAM and sprite-disabled composite were not captured.

Likely mechanism:

- If large black cover persists, the current evidence points first to **true VDP SAT/VRAM divergence, stale reachable SAT, or another composited layer/state mismatch**, not source-to-Genesis transparent-pen loss in the four generated sprites.
- Palette line 3 includes near-black/dark nonzero pens, so real sprite pixels can look dark/purple/brown. That explains small dark shapes, not full-cell transparent-area black cover.

Not the mechanism:

- Not PC090OJ pen 0 becoming nonzero Genesis black for the emitted Build 0123 sprites.
- Not an object-code-to-tile stride/bank error for codes `0x0001`, `0x0110`, or `0x0080`.
- Not XOR based on current evidence.
- Not Window based on this evidence; Window remains out of scope.

Recommended next implementation target: **none yet**. This was evidence-only.

Recommended next evidence target: capture true VDP SAT/VRAM `0xF800..0xFA7F` at the same visible frame, or use Exodus layer toggles to prove whether disabling sprites removes the large black cover. That is a diagnostic recommendation only, not a fix.

## Open / Closed Issues Impact

- Open issues touched: OPEN-024 (primary), OPEN-001 (graphics context), OPEN-006 (sprite palette context), OPEN-023 (Window context only), OPEN-015 (not used).
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: true VDP SAT/VRAM dump, sprite-disabled visual comparison, D00298, Window, Plane A/B changes, any PC090OJ implementation fix.

## Non-Actions

No source, spec, tool, Makefile, ROM, build artifact, invariant, or bookmark artifact was modified. No build was run. No fix was designed or implemented.

## STOP

STOP triggered: NO.

Limited evidence gap: true VDP SAT/VRAM and sprite-disabled composite were not captured. The transparent-pen and code-to-tile mapping portions are resolved from existing Build 0123 assets plus read-only WRAM/palette dumps.
