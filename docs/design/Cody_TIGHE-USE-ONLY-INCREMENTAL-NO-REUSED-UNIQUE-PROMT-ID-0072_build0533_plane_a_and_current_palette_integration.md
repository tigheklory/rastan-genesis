# Build 0533 Plane-A residency and current-palette integration

Date: 2026-11-04

Agent/task: Cody — `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0072`

Baseline: Tighe-accepted Build 0532

Candidate: Build 0533, awaiting Tighe gameplay/palette acceptance

STOP status: no STOP condition

## Accepted Build-0532 Baseline

Build 0532 remains the accepted integration baseline. Its normal ROM is
`dist/rastan-direct/rastan_direct_video_test_build_0532.bin`, SHA-256
`1682b5409010e4da850d8bc24ebac2877253e5ee8ad5d3e043df36b4fafd6838`; its focused invincible R1-S2 ROM
is `rastan_direct_video_test_build_0532_invincible_S1-2.bin`, SHA-256
`adf3eb18b633f547e21b129ad026c59862a7f921734db9155fe2294c57917879`. ROM-producing source was
`566e9c63e5254be6179a0948a34958c20959c68c`.

The branch was not reset. PROMT-ID-0069 Palette Composer work, Tighe's current profile, repository
cleanup, and the accepted 0525–0532 Plane-A corrections remain intact.

## Current Test.json Provenance

- Authoritative path: `/home/tighe/projects/rastan-genesis/analysis/graphics_optimizer/editor_policy/Test.json`
- SHA-256 at Build 0533: `24914ababc7fab52aac8258dd1f9f7b3d5df230b81421c03d9ce68d1526135ae`
- Size/mtime: 305,510 bytes; 2026-11-03 14:57:29 -0500
- Git state: tracked mode 100644, blob `8a0a45641ff640d9b70b53b6b5294d7cd297e567`, unmodified by Cody
- Build-0532 profile SHA: `86505de8a7566e0a13a083bf6b3715fa61eb9242102091aadb589d7583cde9fb`

The forced normal build proved this production chain:

`Tighe current Test.json -> gen_pc090oj_palsel_lut.py / gen_reindexed_pc090oj.py /
gen_test_palette_cram.py / export_subround_palette_manifest.py / compile_pc080sn_genesis.py /
build_pc090oj_hud_white.py -> generated palette, reindexed PC090OJ, Plane-A and semantic profile data ->
palette_hooks.o / pc090oj_hooks.o / pc090oj_assets.o / tilemap_hooks.o -> linked ROM`.

Generated evidence carries the current profile SHA. Key hashes are:

- `pc090oj_palsel_lut.inc`: `87737f13ae488359dd9dc4a37a92423c002150a4715a270340e34b7bd9956f8d`
- `pc090oj_sprite_variants.inc`: `77a2370d47e0574e50fc2bff187c41f1826cece90be32c81f77868ee1188cd8c`
- `pc090oj_editor.bin`: `c6dfce3893a52e0f45bc27e3b816467df0f1fddba9e37f5e87b95885f794b629`
- semantic PC090OJ profile: `cfff14aada0338903c62dfdd1e188fd43a0eea7cfcdd6d9dc52080ea141a1975`
- R1-S2 CRAM: `281f9f38c8e58101f6c01aa5d5578605313949ea9e32e26f287355a19767c26d`

## Tighe Palette Changes Since 0532

The semantic profile delta remains:

- new `object:castle.green_sword_knight.r1.n3`, destination line 0, with Tighe's complete authored map;
- `object:player.rastan` source indices 7 and 15 exchange destinations (`7->3`, `15->6`);
- `PAL-R1-S2-PLANEA-CASTLE` target line-0 index 6 is `$002C`;
- no plane-usage mapping or target-palette-line policy change.

Only the exact Round-1 knight context is authored. Later-round knight variants remain unresolved and
were not inferred. Line 2 remains reserved and is not generated. Automated checks prove integration,
not visual acceptance.

## Build-0532 Remaining Plane-A Failure

Tighe's focused minimal-jump capture is:

`states/traces/r1s2_minimal_jump_stale_row_build_0532/genesis_20261104_162107/`.

The marker is frame 2106, only two frames after the immediately relevant author event and 115 frames
before capture end. A roughly 0.25-second reaction delay is therefore harmless. The old reducer reported
zero implicated rows because it asked whether each row matched *any* valid record asset. It did not ask
whether that logical row belonged in that physical slot at the current camera position.

At marker FG Y `$0021`, the required 32-row window is logical 60..63,0..27. The corrected reduction finds:

| Physical | Required logical | Actual owner | Actual exact asset |
|---:|---:|---:|---|
| 0 | 0 | 32 (`$21` tag) | record-16 logical 32 |
| 27 | 27 | 59 (`$3C` tag) | record-17 logical 59 |

This is wrong provenance with internally valid row contents, explaining why static asset matching passed.

## First Bad State

The first incorrect transition in this record begins at frame 2068:

- record/selector/front/group/strip: `$0011` / 1 / 0 / 0 / 0;
- pre-step FG Y `$0000`, retained delta `+1`; post-step FG Y `$0001`;
- pre-step visible top 1; post-step visible top 0;
- original selector-1 author: logical row 63, physical alias 31;
- writer path: `genesistan_hook_tilemap_plane_a_selector12_native`, captured store PC `$070900`;
- owner before: logical 31 (`$20` tag); staged hash `$4F701A97`;
- owner/content after: logical 63 (`$40` tag), staged hash `$076984EF`, dirty set;
- required post-step physical-31 owner: logical 31, so the logical-63 write is premature;
- simultaneously entering logical row 0 is not materialized because the ordinary author branch bypasses
  the no-publication hooks; physical 0 remains logical 32.

The same destructive prefetch repeats. Immediately before the marker, frame 2104 authors logical 59 while
FG Y is `$001F`; after the retained `+1` step, the required window is 61..28, so logical 59 is still outside
the window. Build 0532 nevertheless replaces physical row 27's required logical 27. By marker frame 2106,
the window is 60..27 and that wrong alias is visible/resident.

Original arcade authority independently supports this distinction. Selector-1 `FUN_00055696` calls
`FUN_00055948/FUN_00055990/FUN_00055A14` before committing `A5+0x10B0 += A5+0x10DA`. The arcade can
pre-author logical N in its 64-row PC080SN name RAM while logical N-32 remains separately resident. A
Genesis 64x32 Plane A cannot publish both aliases simultaneously.

## Second Root Cause

Build 0532 conflated two different retained arcade events:

1. **Authoring/prefetch:** selector-1/2 produces a legal 64-row logical row and collision data before the
   scroll commit. That row may still be outside the Genesis 32-row physical window.
2. **Physical entry:** the scroll commit can move a different logical row into the Genesis window. When an
   ordinary author call occurs on the same step, control bypasses the existing no-publication materializer.

The result is both a destructive off-window N/N+32 overwrite and a missed entering predecessor row. This is
not jump-specific, not incorrect Python row data, and not a palette defect. Jump cadence merely changes
which legal producer/scroll sequences coincide.

## Production Correction

Source commit: `a2f777a8f749a6a9e959e0178b06b8290a4aa3e4`.

`genesistan_hook_tilemap_plane_a_selector12_native` now:

- derives the old and retained post-step camera windows from `A5+0x10B0`, selector 1/2, and `A5+0x10DA`;
- preserves complete 64-column collision publication for every arcade-authored row;
- stages visual words, dirties the row, and changes `plane_a_resident_logical_rows` only if the authored
  logical row is resident in the post-step Genesis window;
- leaves a still-required N-32 alias untouched when the arcade pre-authors off-window N;
- materializes every logical row genuinely entering during the same ordinary selector step, using the
  existing exact-owner/native row materializer for Plane A and established Plane-B row publisher;
- preserves initial scene replay, selector-2/downward movement, wrap, multi-pixel bounded deltas, reversals,
  collision, and the 0525–0532 source-selection rules.

No shadow tilemap, 64-row graphics buffer, coordinate special case, chain special case, input path, or
PC080SN emulator was added. `staged_fg_buffer` remains the sole final 64x32 Plane-A image.

### Native-replacement boundary acknowledgement

- **Semantic cut retained:** original arcade decision to author a logical selector-1/2 row, publish its
  collision semantics, and advance camera Y.
- **Chip-specific tail removed/remaining bypassed:** PC080SN C08000 name-RAM destination walking and 64-row
  physical retention. The native tail emits only resident final Genesis Plane-A/Plane-B words and dirty jobs.
- **Transitional compatibility retained:** existing 32-byte `plane_a_resident_logical_rows` provenance vector
  beside `staged_fg_buffer`; producers are scene seed/selector/pan materializers and consumers are exact-owner
  row publication. It stores no graphics and remains the minimum alias identity needed by the 32-row plane.

## Build 0533 Candidate

Counter/ledger advanced 0532 -> 0533. Every artifact is 3,792,568 bytes.

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0533.bin` | `3e43bee4bc652980826a4e67bc6cee005d035c934620c4d6fc7b2a77812bcf2b` |
| `rastan_direct_video_test_build_0533_S1-2.bin` | `b293bf72001c629f69e9d53ceb157b5f38bca3fc9954c0724e4599fb4602b341` |
| `rastan_direct_video_test_build_0533_invincible_S1-2.bin` | `34aff3f4f6ef91cba70ccb018f48cb3c8747d068e6512ae58a37d96055a4e2cd` |
| `rastan_direct_video_test_build_0533_invincible.bin` | `c6dc0d03648fd73ba72b82392f73fd9f02425eb34acd8b740a8236b66da33e92` |
| `rastan_direct_video_test_build_0533_d.bin` | `de432cf4aac252cde1414f324c465586c1db0f58e3d3ecd4ae77a732cc0687c2` |
| `rastan_direct_video_test_build_0533_s.bin` | `264ee1d606fdc29f06737174e0a885fca72b4432417d245eb186cb095bf8e800` |
| `rastan_direct_video_test_build_0533_do.bin` | `9b95ed694623fc7c2686e455a5c789130826285deddbf182cebf8f9578450b4e` |
| `rastan_direct_video_test_build_0533_c.bin` | `2e9e5ca5db7d2f61e653d213e9f5cc7afedf382f06229308f44965085df2a24c` |
| `rastan_direct_video_test_build_0533_full_hud.bin` | `23895293914b42659ce3a26f5f76a8fda22a25fc440a8397a5e580c99f659fb6` |

The canonical manifest reports 228 expected opcode-replacement sites and `$39DEB8` expected Genesis bytes
covered. This source change is inside the established native helper; it adds no remap site.

## Palette ROM Verification

Build 0533 was built only after forced generation from current `Test.json`. The Makefile's
`verify_palette_families.py` reports the live profile SHA on LUT, PC090OJ editor, semantic profile, and CRAM
outputs; Rastan and Round-1 green-knight maps are exact; Line 2 is reserved. Therefore Build 0533 contains
Tighe's latest authored decisions. Their appearance is not claimed visually accepted.

## Automated Regression

Passed:

- corrected trace reducer: marker 2106 reports the two resident-owner mismatches above;
- deterministic selector-1/2 post-step residency model, exact frame-2104 off-window row-59 case, ordinary
  wrap-entry row-0 case, both directions, every 9-bit scroll, and deltas 1..8;
- assembly and `git diff --check`;
- native row/source, scene/checkpoint/pan, collision separation, selector equivalence, boot guards;
- canonical gate: 228/228 replacement sites and expected coverage;
- Genesis NTSC gameplay-entry gate and all six Round-1 epoch/package cases;
- mandatory 30-second Genesis NTSC MAME trace with no address/bus/illegal/crash-handler errors;
- normal and invincible R1-S2 direct starts: frame 412, stage `$0010`, record `$0011`, package 5, both
  planes 2048/2048 nonzero, zero map misses;
- complete configured family and invincibility contract;
- current-profile palette-family, reindex, green-knight, and Line-2 protections.

The exact traced defect is **PROVEN FIXED BY CODE**. Static/automated evidence cannot establish visual
gameplay acceptance or prove that no separate later R1-S2 defect exists.

## USER MUST VERIFY

Primary ROM:

`dist/rastan-direct/rastan_direct_video_test_build_0533_invincible_S1-2.bin`

SHA-256: `34aff3f4f6ef91cba70ccb018f48cb3c8747d068e6512ae58a37d96055a4e2cd`

1. Climb R1-S2 with only the three required chain jumps and inspect the former one-row strip at record 16/17.
2. Continue through record 21 and inspect the previously larger corrupt area.
3. Reverse vertical direction, then repeat with aggressive jump-assisted climbing.
4. Confirm Tighe's latest player and R1-S2 green-knight palette choices; visual palette acceptance remains his.
5. Note any remaining corruption with record/area and minimal versus aggressive route; no new trace is requested
   unless a distinct defect remains.

## Files / Local Commits / Logs

Production/test commit:

- `a2f777a8f749a6a9e959e0178b06b8290a4aa3e4` — Plane-A ordinary-scroll residency correction,
  deterministic regression, and owner-aware Build-0532 trace reduction.

Existing project tools reused:

- Build-0532 SHA-guarded minimal-jump tracer and reducer;
- original arcade Ghidra export and disassembly;
- native row/pan assets and full-span verifier;
- Makefile canonical/gameplay/epoch/MAME gates;
- subround generator, static verifier, and Genesis NTSC functional verifier.

New tooling created: none. The existing reducer and verifier were extended because asset identity alone did
not test physical-slot ownership.

Files changed in the source commit:

- `apps/rastan-direct/src/tilemap_hooks.s`;
- `tools/translation/verify_bg_a_incremental_background.py`;
- `tools/diagnostics/reduce_r1s2_build0532_remaining_trace.py`.

Documentation/log changes are committed separately. Numbered ROMs and normal generated build products remain
preserved outside Git according to project policy. No GitHub push was performed.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0072`
