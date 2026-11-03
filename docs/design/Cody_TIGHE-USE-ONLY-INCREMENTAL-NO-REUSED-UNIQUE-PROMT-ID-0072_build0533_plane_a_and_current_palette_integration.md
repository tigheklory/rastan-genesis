# Build 0533 Plane-A and current-palette integration result

Date: 2026-11-03

Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0072`

## Accepted Build-0532 Baseline

Tighe accepted Build 0532 as the integration baseline while explicitly retaining the later R1-S2
Plane-A defect. The accepted normal ROM is
`dist/rastan-direct/rastan_direct_video_test_build_0532.bin`, SHA-256
`1682b5409010e4da850d8bc24ebac2877253e5ee8ad5d3e043df36b4fafd6838`. The focused manual-test ROM is
`dist/rastan-direct/rastan_direct_video_test_build_0532_invincible_S1-2.bin`, SHA-256
`adf3eb18b633f547e21b129ad026c59862a7f921734db9155fe2294c57917879`. ROM-producing source is
`566e9c63e5254be6179a0948a34958c20959c68c`.

The branch was not reset. Work after 0532, including PROMT-ID-0069 and repository cleanup, remains in
history. The counter and consumed ledger remain 0532; this task did not consume 0533.

## Current Test.json Provenance

- path: `/home/tighe/projects/rastan-genesis/analysis/graphics_optimizer/editor_policy/Test.json`;
- SHA-256: `24914ababc7fab52aac8258dd1f9f7b3d5df230b81421c03d9ce68d1526135ae`;
- size and mtime at integration: 305,510 bytes, 2026-11-03 14:57:29 -0500;
- Git state: tracked mode 100644, blob `8a0a45641ff640d9b70b53b6b5294d7cd297e567`, unmodified by Cody;
- Build-0532 profile SHA: `86505de8a7566e0a13a083bf6b3715fa61eb9242102091aadb589d7583cde9fb`.

The production chain is not one generator:

1. `gen_pc090oj_palsel_lut.py` generates `out/pc090oj_palsel_lut.inc`; `pc090oj_hooks.o` consumes it.
2. `gen_reindexed_pc090oj.py` generates `pc090oj_editor.bin` and
   `out/pc090oj_sprite_variants.inc`; `pc090oj_assets.o` and `pc090oj_hooks.o` consume them.
3. `gen_test_palette_cram.py` generates CRAM lines 0, 1, and 3; `palette_hooks.o` includes them.
4. `export_subround_palette_manifest.py --profile Test` generates the R1-S1/R1-S2 scene CRAM binaries;
   `palette_hooks.o` includes them.
5. `gen_reindexed_region.py` generates the authored PC080SN Layer-A region used by the boundary compiler
   and native Plane-A assets.
6. `build_pc090oj_hud_white.py` generates the semantic PC090OJ profile included by `pc090oj_assets.o`.

Every corresponding Make target directly depends on the live profile. The normal prepatch/link graph
depends on those objects, and the final ROM rule runs `verify_palette_families.py`. No stale snapshot or
parallel palette path is used.

## Tighe Palette Changes Since 0532

The exact semantic delta from the Build-0532 profile is:

- new `object:castle.green_sword_knight.r1.n3`, destination line 0, with Tighe's complete authored
  index map;
- `object:player.rastan`: source indices 7 and 15 exchanged destinations (old `7->6`, `15->3`; current
  `7->3`, `15->6`);
- `PAL-R1-S2-PLANEA-CASTLE` gained target-palette line-0 index 6 = `$002C`;
- no `plane_usage_palette_mappings` or `target_palette_lines` changes.

Only the exact Round-1 knight context is authored. Later-round knight variants remain unresolved and
were not inferred. Canonical registry entry `PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001` records the current
decision without changing Tighe's profile. Existing Rastan decision
`PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001` remains the narrower proven nibble-3/sword route and is not
reinterpreted as a global player-body mapping.

## Generated Palette Integration

Forced Makefile-owned generation exposed that the dependency graph was correct but
`gen_reindexed_pc090oj.py` did not yet enumerate the PROMT-ID-0069 knight semantic object. The generated
manifest therefore omitted Tighe's new mapping. The generator now feeds the exact eight ranked
decompilation/compositor-backed `0x033E` frames used by Palette Composer into the existing
`(code,effective-bank)` variant pipeline. There is no assembly hardcode and no new palette choice.

The result covers 30 knight base codes plus one genuine code/bank variant at code `$030C`; all transformed
cells independently match the authored map. Current generated hashes include:

- `pc090oj_editor.bin`: `c6dfce3893a52e0f45bc27e3b816467df0f1fddba9e37f5e87b95885f794b629`;
- `pc090oj_sprite_variants.inc`: `77a2370d47e0574e50fc2bff187c41f1826cece90be32c81f77868ee1188cd8c`;
- `pc090oj_palsel_lut.inc`: `87737f13ae488359dd9dc4a37a92423c002150a4715a270340e34b7bd9956f8d`;
- R1-S2 CRAM: `281f9f38c8e58101f6c01aa5d5578605313949ea9e32e26f287355a19767c26d`.

The generated reports and includes all carry the current profile SHA. Line 2 remains reserved and is not
among the generated Test CRAM lines.

## Build-0532 Remaining Plane-A Failure

Tighe's Build-0532 test proves that the larger later record-21 corruption survives the corrected
next-to-author formula. Existing Build-0529/0530 captures cannot establish the second Build-0532
transition: they predate exact-owner preservation, current-row rematerialization, and the exclusive
boundary fix, and contain already-proven earlier failures.

The retained semantic cut remains:

`arcade publish/preserve decision -> final Genesis Plane-A resident words`

The retired chip tail remains PC080SN C08000/name-RAM row walking and writes.
`staged_fg_buffer` remains the only final-native 64x32 Plane-A image. No shadow map, 64-row backing store,
or PC080SN emulation was added.

Source inspection confirms that the formula-only verifier is insufficient to diagnose the report. A row
can be staged and tagged by selector-1/2 or the no-publication materializer and then be touched by another
producer or published in a different order. The exact runtime order is not present in existing evidence.

## First Bad State

Not yet established for Build 0532. Claiming one from the earlier traces would conflate different code
semantics. The separate Build-0532 tracer records, for every staging transition:

- frame and total event order;
- record, selector, completed selector, front, group, strip, and camera/player coordinates;
- physical row/column and writer PC/path;
- owner tag and dirty state before the write;
- pre-first-write and post-frame 64-word staged and VDP rows;
- every provenance change;
- all 32 complete staged/VDP rows at Tighe's first-visible-corruption marker.

It is SHA-guarded to the accepted invincible R1-S2 ROM, its exact Build-0532 symbols, and the Build-0532
native/pan row oracles. The historical Build-0530 tracer is unchanged.

## Second Root Cause

Not proven without the Build-0532 ordered failure capture. The remaining discriminating possibilities are:

1. correct row and provenance followed by a later staging overwrite;
2. correct staging followed by missing/reordered VDP publication;
3. wrong current/predecessor source on a path not represented by the formula oracle;
4. logical-row identity proving too weak because the same row has multiple live record/ownership epochs.

The fourth possibility does not authorize metadata yet. The capture must first prove that identical logical
row tags can legally refer to different required contents at the first bad transition.

## Production Correction

No Plane-A production correction was made. There is no proven second cause to correct, and the assignment
explicitly permits a focused Build-0532 diagnostic package when dynamic evidence is genuinely missing.
The valid Build 0525-0532 corrections remain unchanged.

The palette production correction is complete in local commit
`dac22e0d11cfc22032574f079d0e68d5257eb82b`: the established generator now consumes Tighe's exact authored
knight identity, and the existing independent verifier anchors generated pixels and routing to the live
profile.

## Build 0533 Candidate

No Build 0533 ROM was produced. Counter 0532 is unchanged. Consequently there is no Build-0533 normal,
S1-2, or invincible-S1-2 SHA to report, and no claim that the Plane-A defect is fixed by code. Shipping a
palette-only 0533 would not satisfy the Plane-A candidate objective.

## Palette ROM Verification

There is no new ROM to verify. The current authored decisions are verified through every generated
production input and linked-object dependency, but they are not claimed to be present in Build 0532 and
are not yet linked into Build 0533. When the Plane-A cause is corrected, the normal Make build must
regenerate these inputs and the final ROM must be checked at the linked symbols before delivery.

Therefore:

- current authored palette decisions integrated into production generation: **yes**;
- Build 0533 contains Tighe's latest authored decisions: **not applicable; Build 0533 was not produced**;
- palette visually accepted: **no; requires Tighe's eventual candidate test**.

## Automated Regression

Passed:

- forced Makefile-owned current-profile generation;
- `verify_reindexed_pc090oj.py`: 961 `(code,bank)` requirements, 837 unique codes, 124 variants,
  76/76 divergent codes distinct, zero mismatches/incomplete/stray writes, 30 knight codes exact;
- `verify_palette_families.py`: all generated profile SHAs match, Rastan and R1 knight maps exact,
  line 2 reserved/not generated;
- `verify_green_knight.py`: 14/14;
- Python compilation, shell syntax, `git diff --check`;
- five-frame Genesis NTSC MAME tracer smoke run against the exact accepted ROM.

No new Plane-A regression exists yet because the first bad Build-0532 transition has not been captured.
The reducer classifies marker rows against the exact Build-0532 record 16/17/20/21 native/pan assets and
preserves the full ordered evidence needed to write a failing deterministic regression after capture.

## Manual Test for Tighe

Run from the project root:

```bash
tools/diagnostics/run_r1s2_build0532_remaining_trace.sh
```

Reproduce only the later record-21 corruption in the preselected accepted invincible R1-S2 ROM. Press `M`
immediately when corruption first becomes visible, then close MAME. No original-arcade replay is requested.
Reduce the newly printed trace directory with:

```bash
tools/diagnostics/reduce_r1s2_build0532_remaining_trace.py states/traces/r1s2_remaining_build_0532/genesis_<timestamp>
```

This is the minimum remaining input. The next implementation should begin from the first mismatching row's
ordered timeline, add a regression that fails under Build-0532 semantics, make the smallest semantic fix,
then build the unused 0533 family with the current profile.

## Files / Local Commits / Logs

Local source/tooling commit (not pushed):

- `dac22e0d11cfc22032574f079d0e68d5257eb82b` — current palette integration and separate Build-0532
  diagnostic package.

Primary files:

- `tools/graphics_editor/gen_reindexed_pc090oj.py`;
- `tools/graphics_editor/verify_reindexed_pc090oj.py`;
- `tools/graphics_editor/verify_palette_families.py`;
- `specs/palette_decisions.json`;
- `tools/diagnostics/run_r1s2_build0532_remaining_trace.sh`;
- `tools/mame/scripts/r1s2_build0532_remaining_plane_a.lua`;
- `tools/diagnostics/reduce_r1s2_build0532_remaining_trace.py`.

The successful smoke capture is
`states/traces/r1s2_remaining_build_0532/genesis_20261103_220157/`; it is ignored diagnostic output and was
not staged. The preceding `220144` launch exposed an environment-number parsing error, which was corrected
before the successful smoke run. No trace or screenshot is committed. No push was performed.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0072`
