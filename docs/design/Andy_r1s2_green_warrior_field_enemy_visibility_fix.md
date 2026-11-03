# R1-S2 "green warrior" now authorable — field-enemy castle-visibility fix

**Author:** Andy · **Date:** 2026-11-03 · Direct request from Tighe (add the R1-S2 green warriors to the
Palette Composer so their colors can be authored). Editor tooling only — no production ROM/ASM/C, no
`Test.json`/authored-palette change, no `specs/palette_decisions.json` change.

## Problem
Tighe's arcade-vs-Genesis screenshots proved the R1-S2 castle "green warriors" **render in the Genesis
build with correct geometry/placement but the wrong palette** (arcade = green-armored, Genesis = red/orange).
They were **absent from the R1-S2 Palette Composer**, so their palette could not be authored.

## Root cause (two parts)
1. **Identity (now resolved from PROVEN data):** the green warrior is the **lizardman**, base `0x004B`,
   effective bank `0x36`, `word0_nibble 0x6` — from `analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv`
   (the PROVEN_COMPLETE R1/P1 corpus). Nibble 6 is a GREEN arcade palette; bank `0x36` is one of the
   PC090OJ palsel LUT's green (line-1) banks. It is a **field enemy that also appears in the castle**
   (family-0 base `0x004B` is in the R1-S2 subround-2 roster). Earlier guesses (`0x0A73` "armored man") were
   **disproven**: `0x0A73`'s R1 palette (nibble 0) is the red/orange flame palette, so it is red in both
   arcade and Genesis — not the green warrior.
2. **Why it was hidden:** the PROMPT-0038 §10 membership filter (`app.js`) showed `field_phase1` enemies
   **only in S1/field scenes, explicitly hiding them from the S2 castle**. That assumption was wrong — the
   field enemies reappear in the castle — so the filter was actively hiding the exact enemy Tighe needed.

## Fix
`tools/graphics_editor/app.js`: field enemies (`membership==='field_phase1'`) now show in the gameplay
**field AND castle** scenes (`/-S[12]-/`), still hidden from the S3 boss scene. Scene-tagged marker-chain
castle actors still show only in their own subround; shared assets always show; "All Assets" unchanged.

`tools/graphics_editor/verify_r1s2_castle_browser.py`: tests 12/12b/13 updated — R1-S2 castle now SHOWS
field enemies (Lizardman present), R1-S3 boss still hides them, R1-S1 still shows them. **16/16 PASS.**
`Test.json` hash-unchanged (test 14).

## Why red → how to make it green (for authoring)
In the Genesis palsel LUT, only "scene 1" (R1-S1) has authored sprite→line mappings, where bank `0x36` →
**line 1 (green)**. R1-S2's PC090OJ palette is unauthored, so bank `0x36` falls to a default line carrying
reds → the warrior renders red. With the lizardman now visible in the R1-S2 scope, its arcade green source
colors (per-round `0x3BA88[1][6] → 0x4FD02`) can be mapped to a Genesis sprite line (0/1/3; **line 2 is
Plane-B/arcade-protected**), updating `specs/palette_decisions.json`, after which the palsel LUT regen routes
bank `0x36` → the authored green line for R1-S2.

## Honest limits
- The lizardman is the proven green-humanoid field enemy and the match for the warrior's bank/color; whether
  every on-screen castle pose is base `0x004B` vs a sibling family base is not individually proven, but the
  palette-authoring unit is the **bank (`0x36`)**, which is correct regardless of pose.
- This makes the enemy **authorable**; it does not itself change any color. Authoring + palsel-LUT regen +
  a build are the subsequent (separate) steps.
