# Test 2.0 — Global Line 0 / Full Body 00 palette reorganization

**Agent:** Cody  
**Date:** 2026-11-06  
**Task type:** Palette Composer authoring-profile edit; no ROM produced

## Result

Created the separate editable profile
`analysis/graphics_optimizer/editor_policy/Test_2_0.json` with display name
**Test 2.0** and parent **Test**. The source `Test.json` was not edited by this
operation.

- Source `Test.json` SHA-256:
  `ab13104780289fc1f7455a4f2ab94502ef3d6ba6757fe4d147d71e97ad7ec98e`
- Output `Test_2_0.json` SHA-256:
  `044c5dab39a46e041a7200d789a937b2f6054fb0d2e9b22aa14dbc4cb6197cbc`
- Palette Composer manifest entry: `Test_2_0`, revision 1, parent `Test`

## Line 0 construction

Line 0 entry 0 is the required transparent/backdrop black `0x0000`. Entries
1-15 are the 15 colors used by the authoritative **Full Body 00 (torso 0 +
legs 0)** source. Each arcade RGB value was quantized with the Palette
Composer's existing `gen_quant()` Genesis conversion, then ordered by arcade
source HSL key `(hue, saturation, lightness)`.

| L0 index | Full Body source | Arcade RGB | Genesis CRAM |
|---:|---:|---:|---:|
| 1 | i1 | `#101010` | `0x0000` |
| 2 | i13 | `#636363` | `0x0666` |
| 3 | i12 | `#949494` | `0x0888` |
| 4 | i2 | `#E7E7E7` | `0x0CCC` |
| 5 | i7 | `#630000` | `0x0006` |
| 6 | i6 | `#940000` | `0x0008` |
| 7 | i15 | `#F70000` | `0x000E` |
| 8 | i4 | `#A55242` | `0x044A` |
| 9 | i3 | `#F7A584` | `0x08AE` |
| 10 | i5 | `#634231` | `0x0246` |
| 11 | i9 | `#F77300` | `0x006E` |
| 12 | i8 | `#F7F700` | `0x00EE` |
| 13 | i14 | `#004200` | `0x0040` |
| 14 | i11 | `#006300` | `0x0060` |
| 15 | i10 | `#009400` | `0x0080` |

The production Rastan map key `object:player.rastan` and the retained legacy
Full Body key `usage:rastan_f7722:bank0x33` both receive the corresponding
direct source-index-to-new-index mapping. This makes Full Body 00 use the exact
newly organized palette rather than preserving its former target colors.

## Preservation of other Line 0 consumers

Every other saved sprite/object mapping already targeting Line 0 was translated
from its old **Test target CRAM color** to the perceptually closest color in the
new Line 0 using the Palette Composer's existing CIEDE2000 metric. This does not
re-derive those objects from arcade colors. Existing mappings to target index 0
remain index 0 so transparent pixels do not become opaque.

Thirteen non-Rastan mappings changed indices:

- Valkyrie, Chimera, Small Bat, Large Bat, and Cave Entrance Block
- Green Sword Knight
- sword, axe, hammer, and fire-sword weapon objects
- GAME OVER, HUD P1/1UP, and HUD score digits

All global and context-local Plane-A mappings targeting Line 0 were evaluated
by the same old-color rule. The existing mappings did not require changed
indices. Lines 1, 2, and 3 are byte-for-byte unchanged.

To make Line 0 genuinely consistent across rounds/subrounds, all three
context-local Line-0 color overlays were removed from the new profile while
leaving every non-Line-0 context entry intact:

- `context:gameplay.r01.p01`
- `PAL-R1-S2-PLANEA-CASTLE`
- `PAL-R1-S3-PLANEA-BOSS`

This removes only the overrides currently saved in Test 2.0. The Palette
Composer's context/stage override mechanism is unchanged, so a later deliberate
stage-specific Line-0 palette can still be authored normally.

## Flying Demon explanation

The Flying Demon survives Line-0 edits because its saved mapping is
`usage:flying_demon:bank0x35 -> Line 1`, with a complete 14-entry index map.
That is consistent with the boss-room work only in the sense that Line 1 has
recently been actively authored there; it is not evidence that the Flying
Demon depends on the boss mapping. Test 2.0 leaves both Line 1 and the Flying
Demon mapping exactly unchanged.

## Canonical palette registry

`specs/palette_decisions.json` was consulted. This change creates a candidate
authoring profile and does not promote or alter a canonical palette decision,
so the registry was not modified. Relevant existing decision IDs include:

- `PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001` (`decided`)
- `PAL-PC090OJ-STAGE1-VALKYRIE-001` (`provisional`)
- `PAL-PC090OJ-STAGE1-CHIMERA-001` (`provisional`)
- `PAL-PC090OJ-GAMEPLAY-SMALL-BAT-001` (`provisional`)
- `PAL-PC090OJ-GAMEPLAY-LARGE-BAT-001` (`provisional`)
- `PAL-PC090OJ-STAGE1-CAVE-BLOCK-001` (`decided`)
- `PAL-PC090OJ-ATTRACT-GAMEOVER-001` (`provisional`)
- `PAL-PC090OJ-HUD-P1-LABEL-001` (`provisional`)
- `PAL-PC090OJ-HUD-SCORE-DIGITS-001` (`provisional`)
- `PAL-PC090OJ-STAGE1-FLYING-DEMON-001` (`provisional`, unchanged Line 1)

## Verification

- Identity, parent, source SHA, sorted Line 0, Full Body maps, unchanged Lines
  1/2/3, removed local Line-0 overlays, and unchanged Flying Demon map: **PASS**.
- `gen_test_palette_cram.py` against Test 2.0: **PASS**.
  - Line 0 payload SHA-256:
    `af2db4bccdbcaa9b396d2eb55d9350ae2dce6236b7f2999003fdcffc31dc4502`
  - Line 1 payload SHA-256:
    `3cb995de81b06aa89d9ae3408a6953736c2b8e7437f0c134a222cf47afe2f4d5`
  - Line 3 payload SHA-256:
    `637a34db76429fc7c88917b1b7b0ef07da575f2d728238907aa0923d73f3714f`
- `gen_reindexed_pc090oj.py` against Test 2.0: **PASS**; 904 base codes,
  123 variant cells, 75 divergent codes in two blocks.
- `gen_pc090oj_palsel_lut.py --verify` against Test 2.0: **PASS**; 512 LUT
  combinations, 16,777,216 SAT word-2 cases, zero mismatches.
- No ROM or runtime visual test was produced in this task.

Existing project tools reused:

- Palette Composer validated `/api/policy` save path
- Palette Composer source oracle and its `gen_quant()` / CIEDE2000 behavior
- `tools/graphics_editor/gen_test_palette_cram.py`
- `tools/graphics_editor/gen_reindexed_pc090oj.py`
- `tools/translation/gen_pc090oj_palsel_lut.py`

New tooling created: none.

Why new tooling was necessary: not applicable.

## User must verify in the eventual Test 2.0 build

- Rastan Full Body 00 and the complete player pose vocabulary use the organized
  grayscale/red/warm/yellow/green Line-0 order without missing pixels.
- Green Sword Knight, Valkyrie, Chimera, bats, weapons, cave block, GAME OVER,
  P1/1UP, and score digits remain acceptably close to their former **Test**
  appearance.
- R1-S1, R1-S2, and R1-S3 no longer change Line-0 colors merely because a
  subround context is selected.
- Flying Demon remains unchanged on Line 1.

**STOP status:** No blocker. Profile authoring and static/build-input validation
are complete; gameplay acceptance requires a later numbered Test 2.0 ROM.
