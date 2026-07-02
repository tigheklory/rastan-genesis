# Cody - PC090OJ Blank Sprite-Code Filtering Evidence and Design

**Date:** 2026-07-01
**Type:** Evidence / design only
**Build context:** Build 0123 PC090OJ object-RAM mirror phase, ROM SHA `3a678621d2f71f4a0ce08d7a07d1a55e90e3b9a77cca62d601d4a9cbeb9b3a41`
**Scope:** PC090OJ blank/unmapped sprite-code filtering design. No source/spec/tool/Makefile/ROM/build/invariant changes. No implementation. No rebuild. No bookmark. No runtime probing.

## PHASE 0

Classification: **EXTENDING** OPEN-024 / OPEN-001 with evidence and design only.

Relevant priors loaded:

- KF-010: Genesis BG/FG/SAT mapping context.
- KF-011: arcade code owns game progression; Genesis code is helper/hardware-service only.
- KF-016: title sprite-RAM clear pattern context.
- KF-021: sprite renderer/SAT suppression and stale-SAT hazard context.
- KF-026: PC090OJ write coverage is high-risk.
- KF-032: raw PC090OJ writes route to Genesis staging/mirror.
- KF-036: mapped work-RAM/base discipline.
- KF-038: context only; unrelated BG row aliasing issue.

HIGH-hazard findings touched: KF-011, KF-021, KF-026, KF-032, KF-036.

Open issues touched: OPEN-024 primary; OPEN-001 and OPEN-006 context; OPEN-023 context only; OPEN-015 not touched.

Contradiction detected: **NO**. The prior Build 0123 transparent-pen evidence refuted pen-0 conversion loss for emitted sprites. This pass does not re-blame transparency; it evaluates blank/unmapped sprite-code filtering before Genesis SAT emission.

## ARCHITECTURAL RULE

**Rule:** PC090OJ object RAM must remain a faithful mirror of arcade state. Blank filtering belongs only at the Genesis SAT emission/compaction boundary.

Interpretation:

- Mirror every arcade PC090OJ active object-RAM entry, including entries whose tile code is blank or later filtered.
- Do not mutate, suppress, or rewrite mirrored object RAM as a fix.
- The Genesis helper may skip blank, unmapped, offscreen, or overflow entries when compacting arcade entries into the 80-entry Genesis SAT.
- Skipping at SAT emission is a hardware-service translation step, not arcade gameplay logic.

## BLANK-CODE INVENTORY

Evidence artifacts:

- Inventory directory: `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/`
- Script: `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/inventory_pc090oj_blank_codes.py`
- JSON: `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/pc090oj_blank_inventory.json`
- Markdown summary: `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/pc090oj_blank_inventory.md`
- CSV: `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/pc090oj_blank_inventory.csv`

Inspected assets:

- Arcade/source PC090OJ blob: `build/regions/pc090oj.bin`
- Genesis converted PC090OJ blob: `build/pc090oj_genesis.bin`
- Both files are `524288` bytes.
- Cell size: `128` bytes.
- Inspected converted asset range: `4096` cells, `0x0000..0x0FFF`.
- MAME PC090OJ runtime code mask is `0x1FFF`, so hardware-visible code space is wider than the current converted asset.

Blank inventory result:

- Blank codes: `22`
- Nonblank codes: `4074`
- Blank codes:
  - `0x000`
  - `0x002`
  - `0x004`
  - `0x045`
  - `0x0A8..0x0AB`
  - `0x0F3`
  - `0x100`
  - `0x178`
  - `0x1D8`
  - `0x4FF`
  - `0x5B0`
  - `0x5D6..0x5D9`
  - `0x5DB`
  - `0x9FD`
  - `0xAA3`
  - `0xAC2`

Current Build 0123 code only has a hardcoded skip for code `0`, so the other 21 blank nonzero codes are not filtered by content today.

## SOURCE VS CONVERTED CONSISTENCY

PC090OJ format sources:

- MAME `pc090oj.cpp` uses `gfx_16x16x4_packed_msb` for the PC090OJ graphics decode.
- MAME `pc090oj.cpp` decodes sprite code as `word2 & 0x1FFF`, X/Y as 9-bit signed-wrap coordinates, color from word0 low bits plus sprite colbank, and draws with transparent pen `0`.
- MAME `rastan.cpp` derives `sprite_colbank = (sprite_ctrl & 0xe0) >> 1` and uses `pri_mask = 0`, so sprites draw over the PC080SN tile layers.

Project conversion source:

- `tools/translation/preconvert_pc090oj_tiles.py` converts each 16x16 source cell into four Genesis 8x8 tiles in `TL, BL, TR, BR` order.
- The conversion is a byte/nibble rearrangement only; it does not perform palette or transparency math.

Inventory consistency result:

- Blank-flag mismatches between `build/regions/pc090oj.bin` and `build/pc090oj_genesis.bin`: `0`
- Full recomposed 16x16 pixel mismatches: `0`

Conclusion: source and converted PC090OJ assets agree exactly for this inventory. Blank filtering can be based on the converted asset or on a generated table from the source asset without changing classification.

## BUILD 0123 EMITTED ENTRY CHECK

Build 0123 runtime evidence source:

- `states/traces/build_0123_pc090oj_object_ram_phase1_20260701_133359/postcommit_pc090oj_phase1_summary.json`
- `states/traces/build_0123_pc090oj_object_ram_phase1_20260701_133359/postcommit_pc090oj_object_ram_ff674a.txt`

Captured Build 0123 mirror/SAT summary:

- Decoded PC090OJ mirror entries: `256`
- Drawable entries: `4`
- Emitted SAT entries: `4`
- Dropped entries: `0`
- `pc090oj_ctrl_shadow = 0x0001`
- `pc090oj_sprite_ctrl_shadow = 0x0060`
- Derived sprite colbank: `0x0030`
- SAT link chain: `[0, 1, 2, 3]`

Emitted entries:

| Genesis SAT slot | PC090OJ source entry | Code | Blank? | Valid converted range? |
|---:|---:|---:|---|---|
| 0 | 4 | `0x0001` | no | yes |
| 1 | 14 | `0x0110` | no | yes |
| 2 | 16 | `0x0080` | no | yes |
| 3 | 17 | `0x0080` | no | yes |

Mirror classification for the captured Build 0123 frame:

- Current code-0 skip: `252`
- Drawable emitted candidates: `4`
- Nonzero blank-code candidates in this frame: `0`
- Invalid/unmapped high-code candidates in this frame: `0`

Conclusion: a blank-code filter would not change the four emitted Build 0123 sprites in this captured frame. It would, however, make the SAT compactor generally correct for all 22 known blank codes instead of only code `0`.

## INVALID / UNMAPPED CODE HANDLING

MAME PC090OJ decodes code as `word2 & 0x1FFF`, but the current converted Genesis sprite asset contains only `0x0000..0x0FFF`.

Current Build 0123 tile DMA path loads descriptor code and masks it with `0x0FFF` before computing the DMA source from `rastan_pc090oj`:

```asm
move.w  8(%a0), %d2
andi.w  #0x0FFF, %d2
```

That means a mirrored PC090OJ code in `0x1000..0x1FFF` would not be rejected; it would wrap to a lower converted asset code during tile DMA. That behavior is not arcade-accurate evidence of a real sprite and could display the wrong nonblank tile.

Design requirement:

- Preserve the mirrored 13-bit PC090OJ code in object RAM / descriptor evidence.
- At Genesis SAT emission or before tile DMA, reject or classify codes outside the converted asset range `0x0000..0x0FFF` as **unmapped**, not as `code & 0x0FFF` fallback.
- Do not use lower-12-bit wrap as a final rendering rule unless a future asset conversion proves that higher PC090OJ codes intentionally alias. No such proof exists in this task.

## STALE SAT SAFETY

Current Build 0123 safety facts from `pc090oj_hooks.s`:

- `vdp_commit_sprites` calls mirror scan, link-chain build, tile DMA, SAT DMA, and dirty clear once per sprite commit.
- Mirror scan starts by clearing all 80 generated SAT slots and all 80 descriptor records.
- Link-chain build links only descriptor-valid slots.
- SAT DMA copies the full 80-entry staged SAT table to Genesis VRAM SAT.

Implications:

- If emitted sprite count decreases, stale generated WRAM SAT entries should be removed because the generated SAT table is cleared before scan and fully DMAed afterward.
- If zero sprites are emitted, the generated SAT source remains cleared and the full SAT DMA should make no prior generated slots reachable.
- This proves the intended WRAM staging source behavior, but it is still not the same as a direct true-VRAM SAT dump. If a future visual artifact persists after source-side clearing, capture true VDP SAT/VRAM to rule out DMA or viewer-state divergence.

## PERFORMANCE DESIGN

The blank/unmapped filtering design should be cheap and deterministic:

1. Build-time generate a compact blank-code bitset or byte table for the converted valid range `0x0000..0x0FFF`.
2. At SAT emission/compaction, after `code = word2 & 0x1FFF`:
   - If `code >= 0x1000`, classify as unmapped and skip emission.
   - Else look up `pc090oj_blank_code_table[code]`.
   - If blank, skip emission.
   - Else continue with signed-coordinate/global-flip/offscreen tests and emit if drawable.
3. Keep the full PC090OJ mirror unfiltered for diagnostics and arcade-state fidelity.
4. Keep counters or debug evidence optional and build-time/report-only; no diagnostic ROM behavior is needed for this task.

A 4096-entry byte table is simple but costs 4KB ROM. A 4096-bit table costs 512 bytes ROM and is the likely better production shape. Either is acceptable as a future implementation design choice; this task does not implement either.

## CLASSIFICATION

**Classification: BLANK-CODE FILTERING NEEDED AT SAT EMISSION, WITH UNMAPPED-CODE GUARD.**

Observed facts:

- Pen-0 transparency failure is already refuted for emitted Build 0123 sprites.
- The PC090OJ source and Genesis-converted sprite assets match exactly.
- There are 22 truly blank PC090OJ codes in the converted asset range.
- Build 0123 currently skips only code `0` during mirror scan.
- The captured Build 0123 frame emits only nonblank valid codes, so this filter does not explain those four specific emitted sprites.
- The wider PC090OJ code mask (`0x1FFF`) versus converted asset range (`0x0FFF`) exposes an additional unmapped-code hazard: current tile DMA lower-12-bit masking would wrap high codes instead of rejecting them.

Design conclusion:

- Mirror all PC090OJ object RAM entries faithfully.
- Filter blank and unmapped codes only when compacting the mirror into Genesis SAT.
- Do not modify arcade object RAM or suppress mirror writes.
- Do not treat blank-code filtering as a fix for transparent-pen black overdraw. It is a separate correctness/safety filter for SAT output.

## Issues / Files / STOP

Files created:

- `docs/design/Cody_pc090oj_blank_sprite_code_filtering_evidence_design.md`
- `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/inventory_pc090oj_blank_codes.py`
- `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/pc090oj_blank_inventory.json`
- `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/pc090oj_blank_inventory.md`
- `states/traces/pc090oj_blank_sprite_code_filtering_20260701_152409/pc090oj_blank_inventory.csv`

Files intentionally not changed:

- Source files
- Specs
- Tools
- Makefiles
- ROM/build/invariant artifacts
- Bookmark artifacts

Open / closed issue impact:

- OPEN-024: advanced with blank/unmapped-code filtering evidence; remains open.
- OPEN-001: context only; visual/rendering remains open.
- OPEN-006: context only; sprite palette/color context unaffected.
- OPEN-023: context only; Window not touched.
- OPEN-015: not touched.
- No issue opened or closed.

KNOWN_FINDINGS impact: **Option A - no update**. This task produces a bounded design/evidence result, but no implementation or validated visible-runtime behavior change.

STOP status: **NO**.
