# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0111

## Result

Build 0556 corrects only the Round-1 Stage Clear message palette. The retained
arcade text writer selects physical palette bank 0, so the native Stage Clear
owner now restores the existing converted arcade bank-0 frontend palette to
Genesis Line 0. The large Rastan figure remains on Line 1 with its original
Stage Clear bank-5 colors.

## Build 0554 User-Verified Baseline

Tighe established Build 0554 as correct for the large figure, text geometry,
READY presentation, Scene Clear music, and Round-2 progression. The defect was
limited to the message colors. The Build 0554 runtime capture confirmed that
its Stage Clear Line 0 held converted physical bank 4, while Line 1 already held
the correct figure palette.

## Arcade Stage Clear Palette Source

The original Stage Clear state-9 path begins at maincpu `$055F38` and calls
palette loader `$056128`. That loader reads physical banks 4 and 5 from
`$05649E` and `$0564FE`, respectively, but palette loading alone does not prove
which bank a rendered object consumes.

The retained text selector is `$0561D6`. At `$0561F4` it clears D1 before the
shared PC080SN text writer, producing tile attribute 0. MAME's PC080SN renderer
uses `attr & 0x1ff` directly as the palette selection; therefore this text uses
physical arcade bank 0. Its source is the established frontend bank-0 table at
maincpu `$04EAF6`, converted with the project's xBGR-555 to Genesis CRAM rule.

The large figure is separate: its producer at `$05632A` sets D2 to 5 at
`$056352`, so it consumes physical bank 5 from `$0564FE`. Its converted words
remain:

`0000 0000 08AE 068E 046A 0046 0024 0088 0064 0AAC 0668 002E 004A 0EEE 00CE 008A`

## Continue-Screen Palette Comparison

The Continue panel uses the distinct `$05A3AC` path, palette source `$05A73A`,
and panel source `$05AC72`. `$05A73A` is byte-identical to the Stage Clear
figure palette at `$0564FE`; this proves sharing of the large Rastan/figure
palette only. Stage Clear text does **not** reuse the Continue text palette.

- Shared Continue palette reused for Stage Clear text: **NO**.
- Exact Stage Clear text palette source: physical bank 0 at maincpu `$04EAF6`.
- Large Rastan/Continue figure palette modified: **NO**.

## Stage Clear Text Palette Root Cause

Build 0554 compressed the Stage Clear physical-bank-4 load onto Genesis Line 0.
No visible Stage Clear consumer uses physical bank 4, so that alias destroyed
the bank-0 colors needed by the attribute-0 text. The descriptors and glyphs
were correct; only the CRAM ownership was wrong.

## Genesis Fix

- `apps/rastan-direct/src/scene_load.s`: the Stage Clear owner calls
  `genesistan_stageclear_text_palette_enter` after installing scene 9. The
  helper copies the already-generated `genesistan_frontend_base_palette` bank 0
  to staged Line 0 and requests normal palette publication.
- `apps/rastan-direct/src/palette_hooks.s`: physical bank 4 is ignored only
  while logical scene 2 owns Stage Clear, preventing the unused bank from
  replacing text-owned Line 0. Existing bank-5/Line-1 figure handling is
  unchanged.
- `specs/palette_decisions.json`: added proven decision
  `PAL-FRONTEND-STAGECLEAR-TEXT-BANK0-001`.
- `tools/translation/verify_round1_completion_semantics.py`: now locks the
  original text attribute, figure attribute, exact bank-0 conversion, figure
  conversion, native restore, and bank-4 suppression.

This is a semantic-owner correction at the retained Stage Clear producer; it
does not add a chip shadow, runtime conversion, palette-editor change, or
descriptor rewrite.

## Regression Check

Build 0556 passed:

- canonical ROM gate and complete same-number family verification;
- gameplay-entry and phase-epoch gates;
- mandatory 30-second USA/NTSC Genesis trace;
- palette-family validation using `Test_2_0` SHA-256
  `9b660114ee126383154caf25ffdd8e666fce86ef9754ce4888c22c9b4d37a656`;
- focused natural Round-1 completion capture through presentation states 9–13,
  Scene Clear command `$27`, READY, and Round 2.

At Stage Clear state 11, staged palette and CRAM were byte-identical. Line 0
was the translated `$04EAF6` bank 0:

`0000 0EEE 000E 0468 08AC 046A 0246 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE`

Line 1 remained the exact figure palette listed above. The Build 0556 state-11
Plane A/B snapshots and Round-2 READY Plane A/B snapshots are byte-identical to
the Build 0554 baseline, proving that figure/message geometry and READY content
did not move.

Build 0555 is preserved but rejected as the final candidate: its new focused
semantic gate passed, but its canonical gate failed because the canonical
verifier still expected the superseded 228-site opcode inventory rather than
the existing 232-site inventory. Commit `0169b6fe` aligned that stale invariant;
Build 0556 then passed the canonical gate.

## Build / SHA-256

- Candidate normal ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0556.bin`
  - size: 3,985,080 bytes
  - SHA-256: `69b6274feba521c458f19f088a67a6493311b998877466e249c757eb3502e8e3`
- Candidate invincible ROM used by the focused natural-path capture:
  `dist/rastan-direct/rastan_direct_video_test_build_0556_invincible.bin`
  - size: 3,985,080 bytes
  - SHA-256: `c6857d320a55d16cce4cf9aefcf3904adaa64ccecd103f1207f115520e25df59`
- Rejected/preserved Build 0555 normal ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0555.bin`
  - size: 3,985,080 bytes
  - SHA-256: `eb5e8c4a5a2789e49310167a8e5c9c11f454bb71c43ec26579d3ebc8c7b1c408`
- Makefile counter after delivery: 556.
- Production source commits: `6a0c1bc3`, `9ca0b456`, `0169b6fe`.

## Deferred Issues

Unchanged and explicitly outside PROMT-ID-0111:

- torch animation/tile selection;
- Round-2 graphics, palettes, and gameplay work;
- score values and score display;
- Continue-screen text/palette behavior;
- palette-editor authoring and Test/Test 2.0 content.

## Tighe Acceptance Pending

Automated verification proves the intended palette source, native CRAM words,
unchanged presentation geometry, and preserved progression. Visual acceptance
in BlastEm and on real hardware remains Tighe's decision.
