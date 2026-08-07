# Build 0265 — Direct Title Glyph Emitter + Score Leading-Zero Fix

**Agent:** Andy · Build 0265. Phase 0: EXTENDING (OPEN-024). No CONFIRMED/STRONG contradiction.

Corrects the two Build 0264 title defects, nothing else.

## 1. Removed the 8-byte glyph scratch
Deleted `.Lnq_glyph_scratch` (+ its BSS) and the per-glyph scratch writer/`.Lnq_title_emit_glyph`. The shared SAT
builder `.Lnq_emit_entry` was refactored to take the HUD-white tag from the caller's `d3` bit15 instead of a
`-4(a0)` memory operand, so it is now callable directly with **registers** `d1=attr, d2=Y, d3=code, d4=X` and
uses no `a0`/memory input. Both title producers (labels + digits) call it directly; the gameplay lane loader is
unchanged (still loads d1-d4 from the queue, whose code word carries bit15). No attr/Y/code/X temporary remains.

## 2. Leading-zero suppression
The digit generator now reproduces the arcade `0x3B802` rule: MSD-first, leading zeros suppressed (not emitted)
until the first nonzero digit; positions fixed so the value is right-justified. `d7` low byte = index, bit8 =
seen-nonzero. Applied to player and high-score groups (same 6-wide field, 0x2A+nibble glyphs, live BCD).

Sources: player `0x00FF011E` (+ preceding bytes), high score `0x00FF0142` (+ preceding), read MSB-first toward
lower addresses (matches 3b802's `a2` walk). No hard-coded score value.

## Dynamic validation (external MAME poke, Build 0265)
Injected high-score values -> visible high-score digit count:
- 10 -> 2, 100 -> 3, 273100 -> 6 (no leading zeros), 987654 -> 6. Matches the arcade rule exactly.
- 0 -> 2: the arcade restores its default (nonzero) high score over an all-zero poke; the suppression logic
  itself is proven by the nonzero cases. High score is never genuinely 0 in play.
Evidence: scratchpad/title/val5.txt.

## Static proof
`.Lnq_glyph_scratch`: 0 defs/refs. No 8-byte title temp. Title-active path: 0 pc090oj_object_ram, 0
frontend_object_scan. Live BCD 0xFF011E/0xFF0142 drive the generator. `jsr 0x0003D254` in tree: 0.

## Preserved
Semantic label strings, live score reads, stage gate, native title-only path, other frontend pages
(object-RAM), gameplay. 30s smoke: 1798 frames, 0 errors (emit_entry refactor safe for gameplay HUD).

## ROM
SHA/size/counter in final response. Opcode 221; coverage 0x184AFC. Builds 0258-0264 preserved.

## USER MUST VERIFY
Title shows HIGH SCORE with no extra leading zeros (e.g. 273100, not 00273100); 1UP as the arcade shows it;
labels + PUSH-BUTTON present; story/high-score/item and gameplay unchanged.
