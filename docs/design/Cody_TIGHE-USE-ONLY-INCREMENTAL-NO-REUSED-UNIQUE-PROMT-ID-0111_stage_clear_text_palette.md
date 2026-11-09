# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0111

## Result

Build 0557 is the corrected candidate. It preserves the Round-1 Stage Clear
message-palette fix and corrects the Test 2.0 Rastan pixel-index mapping omitted
from the initial delivery. The retained
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

Build 0557 passed:

- canonical ROM gate and complete same-number family verification;
- gameplay-entry and phase-epoch gates;
- mandatory 30-second USA/NTSC Genesis trace;
- palette-family validation using `Test_2_0` SHA-256
  `eb53bfc119403331f042a0844ed07d2231444b4c1dac13eec029ff6e329e1dec`;
- focused natural Round-1 completion capture through presentation states 9–13,
  Scene Clear command `$27`, READY, and Round 2.

At Stage Clear state 11, staged palette and CRAM were byte-identical. Line 0
was the translated `$04EAF6` bank 0:

`0000 0EEE 000E 0468 08AC 046A 0246 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE`

Line 1 remained the exact figure palette listed above. The focused Build 0557
gate again reached every presentation state, Scene Clear command `$27`, READY,
and Round 2.

The initial 0556 delivery was incomplete and is rejected. It omitted the five
requested direct-start derivatives. It also rebuilt gameplay sprites with the
organized Test 2.0 Line 0 while `object:player.rastan` and two exposed bank-$33
frame usages still carried legacy/empty pixel permutations. This rendered old
pixel indexes against the reorganized colors. Build 0557 applies the authored
permutation to the production player object and all three exposed Rastan frame
usages. The generated asset gate verifies all 344 native player codes with zero
mismatches.

Build 0555 is preserved but rejected as the final candidate: its new focused
semantic gate passed, but its canonical gate failed because the canonical
verifier still expected the superseded 228-site opcode inventory rather than
the existing 232-site inventory. Commit `0169b6fe` aligned that stale invariant;
Build 0556 then passed the canonical gate, but is superseded for the reasons
above.

## Build / SHA-256

- Candidate normal ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0557.bin`
  - size: 3,985,080 bytes
  - SHA-256: `77e3a0371568fe6a8cc85c136a4dbfda1d37b02cc143df80fa9fcda05edbf301`
- Candidate invincible ROM used by the focused natural-path capture:
  `dist/rastan-direct/rastan_direct_video_test_build_0557_invincible.bin`
  - size: 3,985,080 bytes
  - SHA-256: `db7a6e3b439d412251201e895e719e583df2db6e1369aaa2df0b98b56b137802`
- Direct-start derivatives, each 3,985,080 bytes:
  - R1S2 `_S1-2`: `eb3b18eee93391df7f95dc2d8622271ac5d6c77c7b389252a5784b2d05488282`
  - R1S3 `_S1-3`: `b9c50862cdc3b4a618eff43648392b76e335ed7d87d643b20bea25c0c8cc4393`
  - R2S1 `_S2-1`: `e47868abab76049a7885565c6afc0da246f615b628a649c0747938cdcf649f96`
  - R2S2 `_S2-2`: `05f6520e2296bd1bd5ff021ededc3412e5a942adfbf267a66b291c8bae51a852`
  - R2S3 `_S2-3`: `a87148825585591a48dfcb01dc7715f9a4e675ff195998195b377b2574b6ba48`
- Rejected/preserved Build 0556 normal ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0556.bin`
  - size: 3,985,080 bytes
  - SHA-256: `69b6274feba521c458f19f088a67a6493311b998877466e249c757eb3502e8e3`
- Rejected/preserved Build 0555 normal ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0555.bin`
  - size: 3,985,080 bytes
  - SHA-256: `eb5e8c4a5a2789e49310167a8e5c9c11f454bb71c43ec26579d3ebc8c7b1c408`
- Makefile counter after delivery: 557.
- Production commits: `6a0c1bc3`, `9ca0b456`, `0169b6fe`, `17f5b131`.

## Deferred Issues

Unchanged and explicitly outside PROMT-ID-0111:

- torch animation/tile selection;
- Round-2 graphics, palettes, and gameplay work;
- score values and score display;
- Continue-screen text/palette behavior;
- all palette-editor tooling and all non-Rastan Test/Test 2.0 authoring.

## Tighe Acceptance Pending

Automated verification proves the intended palette source, native CRAM words,
unchanged presentation geometry, and preserved progression. Visual acceptance
in BlastEm and on real hardware remains Tighe's decision.
