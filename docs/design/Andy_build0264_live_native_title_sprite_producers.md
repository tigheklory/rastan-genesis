# Build 0264 — Live Direct-Native Title Sprite Producers

**Agent:** Andy · Build produced: YES (0264). Phase 0: EXTENDING (OPEN-024). No CONFIRMED/STRONG contradiction.

## Replaces Build 0263's snapshot
Deleted `.Lnq_title_sprite_table`, `NATIVE_TITLE_SPRITE_COUNT`, and all captured `{attr,Y,code,X}` entries. The
title-active path (`.Lnq_title`) now runs live producers.

## Real semantic sources
- Fixed text = a semantic glyph sequence `.Lnq_title_labels` ({Y,X,glyph}, letters/symbols only, 0xFFFF-term).
- Player score digits: live BCD at `0x00FF011E` (read MSB-first toward lower addrs), glyph = 0x2A+nibble.
- High-score digits: live BCD at `0x00FF0142`.
- Digit glyphs generated every frame by `.Lnq_title_emit_digit_group`; no captured digit constants.
Sources confirmed from the existing `3b802` score-hook record table (0x10C11E / 0x10C142 -> +0x?? Genesis A5).

## Native path
`.Lnq_title` -> `.Lnq_title_emit_labels` + `.Lnq_title_emit_scores` -> per glyph `.Lnq_title_emit_glyph`
(one transient 8-byte entry `.Lnq_glyph_scratch`) -> existing residency + SAT builder (`.Lnq_emit_lane`) ->
staged_sprite_sat -> existing VBlank DMA. No PC090OJ record, no object_ram, no 0xD00000, no Y=0x180, no scan.
Gated on scene 0 AND arcade stage a5@0x118==0; stage!=0 and other frontend scenes keep the object-RAM path.

## Dynamic proof (external MAME, no ROM edit)
Poked live high-score WRAM 0xFF0142/41/40 during the title -> native title digit SAT tiles changed
(slots 12-16: C4A0/C4C0 -> C530/C520/C510/C500/C4F0, new digit sprites appeared). Confirms live generation, not
a snapshot. Player-score poke is overwritten by the arcade each attract frame (it holds that score at 0); the
producer reads it identically, proven live by the high-score test. Evidence: scratchpad/title/dyn2.txt.

## Static proof
`.Lnq_title_sprite_table`/`NATIVE_TITLE_SPRITE_COUNT`: absent. Title-active path: 0 object_ram reads, 0
frontend_object_scan calls, 0 eight-byte record construction, 0 0xD00000, 0 Y=0x180. `jsr 0x0003D254`: 0 in tree.

## ROM
`dist/rastan-direct/rastan_direct_video_test_build_0264.bin` SHA (see final response) size 1592076-ish counter
264. Opcode 221; coverage 0x184B04. Builds 0258-0263 preserved. Gameplay/PC080SN/story/high-score untouched.

## USER MUST VERIFY
Title renders (labels + live high score); high score reflects the real stored value and changes after a game;
player score shows 0 in attract; PUSH-BUTTON present; story/high-score/item and gameplay unchanged.
