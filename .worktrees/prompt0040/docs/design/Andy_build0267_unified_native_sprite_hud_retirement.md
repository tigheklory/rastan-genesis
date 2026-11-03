# Build 0267 — Unified Native Sprite HUD Retirement (0x3B802 + 0x5A098 producer family)

**Agent:** Andy · Build 0267 · GATE_PASS. Phase 0: EXTENDING (OPEN-024/OPEN-006). No CONFIRMED/STRONG contradiction.

## What changed (producer-family retirement, not a screen gate)
`genesistan_pc090oj_hook_score_digit_3b802` and `genesistan_pc090oj_hook_status_sprite_5a098` are reduced to
**inert stubs (`rts`)**. Both producers, across **all 11 callers** (10 for 0x3B802, 1 for 0x5A098), now write
**zero** PC090OJ object-RAM records. The Build 0266 title-only scene/stage gate is gone (superseded, not
extended). 0x3B802's private leading-zero helper (`.Lhook_3b802_visflag`) and record-destination table
(`.Lhook_3b802_record_table`) are deleted. Shared helpers (`.Lpc090oj_mirror_write_*`, `.Lpc090oj_emit_slot`)
are retained because other, unconverted producers still use them.

## Why this is complete for the family's semantic ownership
The score/HUD digits are produced **natively** by the existing owners:
- **Title / attract:** `.Lnq_title` live-BCD digit producer (Build 0264/0265) via `.Lnq_emit_entry` — the one
  native SAT primitive. Semantic layout = anchor X + digit index * spacing (not a captured record table);
  live values from `0x00FF011E` (player) / `0x00FF0142` (high score); arcade leading-zero suppression.
- **Gameplay:** `.Lnq_project_p1_hud` (native, reads `0x00FF011E`).
So 0x3B802's record production was fully **superseded** — removing it shrinks the legacy without a new gate.

## Architecture
`semantic value -> mapping/glyph expansion -> .Lnq_emit_entry (register-passed) -> staged_sprite_sat -> VBlank
DMA`. No PC090OJ record, no object-RAM scan, no record-shaped scratch, no captured sprite table for this family.

## Validation
- **Title SAT byte-identical** 0266 vs 0267 (native HUD unaffected by the retirement). 
- Genesis 30s smoke: 1798 frames, **0 unmapped/fatal/error**. Gameplay score path unchanged (native).
- Static: 0x3B802/0x5A098 hook bodies contain **0** `mirror_write`/`emit_slot`/`record_table` references; no
  dangling references to the deleted private symbols.

## Measured legacy shrink
- Canonical coverage `0x184B14 -> 0x1849D8` = **316 code bytes removed**.
- PC090OJ record writers eliminated: the 0x3B802 family (10 callers) + 0x5A098 (1 caller) now write nothing.
- Title-frame HUD-record writes: 557 -> 557 (unchanged), because those remaining writes belong to the
  **unconverted** families (workram_block_sprites player block, D00298), NOT to 0x3B802/0x5A098 (which were
  already gated off for the title in 0266 and are now globally inert).

## Remaining PC090OJ frontend producer families (explicitly enumerated, out of scope)
`pc090oj_workram_block_sprites*` (player block), the score-record **positioning** producer, and D00298/D002B0.
Their records are still consumed by `.Lnq_frontend_object_scan` for non-title frontend scenes.

## USER MUST VERIFY (honest limit)
The MAME attract harness reaches only the **title** (scene 0 / stage 0), which is validated. Please verify the
frontend states I could not reach — **high-score table, story pages, ROUND/READY, and any life/status display**:
if any of them previously showed score/HUD or status sprites via 0x3B802/0x5A098 (rendered through the object
scan), those elements now need the native HUD extended to that state. If they use other producers
(workram_block_sprites / D00298 / plane text), they are unaffected. Confirm the title (labels + live score/high
score, correct leading zeros) and gameplay are unchanged.
