# Build 0263 — Direct-Native Title-Screen Sprites

**Agent:** Andy · **Build produced: YES (0263).** (Intermediate 0262 = same table, no stage gate; preserved.)

## Phase 0
EXTENDING (OPEN-024 PC090OJ frontend retirement). KF-067 (BACK_ENEMY bias, untouched). No CONFIRMED/STRONG
contradiction.

## What was converted
The title-active HUD (scene_id 0 + arcade stage a5@0x118==0): 1UP/HIGH SCORE labels, player+high-score digits,
credit line, and PUSH-BUTTON text — 42 pieces / 15 visible sprites. Captured from Build 0261's own attract
title (original-arcade-faithful) via runtime trace `scratchpad/title/*`.

## Semantic cut
Retained: title-active visibility (gated on arcade stage a5@0x118==0), text/digit/artwork identity, X/Y,
palette (0), order. Cut before: PC090OJ record band selection, attr/Y/code/X record stores, Y=0x180 park,
0xD00000, object-RAM scan/decode. Path: native title sprite table -> `.Lnq_emit_lane` (existing residency +
SAT builder) -> staged_sprite_sat -> existing VBlank DMA. No intermediate PC090OJ record.

## Implementation (pc090oj_hooks.s only + canonical coverage constant)
- Finalizer dispatch: scene 1 -> gameplay; scene 0 AND a5@0x118==0 -> `.Lnq_title` (native table);
  else -> `.Lnq_frontend_object_scan` (unchanged, for stage!=0 title sub-states + other frontend scenes).
- `.Lnq_title`: builds the SAT directly from `.Lnq_title_sprite_table` (42 {attr,Y,code,X} words) via the
  existing gameplay lane->SAT machinery. NATIVE_TITLE_SPRITE_COUNT=42.
- No object-RAM read in the title-active path; scene-0 title-active never reaches the object scan.

## Deletions / retained compatibility
No code deleted (the object-RAM scan is retained for the stage!=0 title sub-states and other frontend scenes,
which still use it — a documented, isolated compatibility path, not a converted-sprite double path).

## Validation (Genesis MAME, attract; title reachable without input)
- Title-active (scene 0, stage 0): native SAT == 0261 scan SAT for all 15 visible sprites; slots 0-13
  byte-identical, slot 14 differs only in the SAT link terminator (0x050F vs 0x0500) — same 15 visible sprites,
  no visual difference (trailing slot is empty/off-screen). Evidence: scratchpad/title/a0261_active vs a0263.
- Attract advanced (stage!=0): 0263 defers to the scan; SAT identical to 0261.
- 30s smoke: 1798 frames, 0 unmapped/fatal/error; gameplay (scene 1) and PC080SN paths untouched.

## Static proof
Title-active path (`.Lnq_title`) contains: 0 PC090OJ record writers, 0 object-RAM reads, 0 eight-byte record
construction, 0 Y=0x180, 0 0xD00000. `jsr 0x0003D254` count in source tree: 0.

## ROM
`dist/rastan-direct/rastan_direct_video_test_build_0263.bin` SHA 79cf89c7e26bfc235ede4744cd906f6fb37cc56c0231d8bb21a08a1e53a0f44c
size 1592076 counter 263. Opcode 221; coverage 0x184B0C. Builds 0258-0262 preserved.

## USER MUST VERIFY
Title screen renders identically (1UP/HIGH SCORE/score/credit/PUSH-BUTTON); PUSH-BUTTON toggles off correctly
when the attract advances (handled by the retained scan for stage!=0); story/high-score/item screens unchanged;
gameplay unchanged.

## Limitations / next
The native table is the static title-active snapshot; dynamic score/high-score digit values and blink are still
handled by the scan for stage!=0. Sourcing the digits from WRAM (0xFF011E/0xFF0142) to make the native table
fully dynamic, then converting the remaining frontend scenes, is the next increment.
