# R1-S2 records 16–21 native streaming — Build 0508 candidate

Date: 2026-10-26  
Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0012`  
Status: **candidate only; NOT ACCEPTED pending Tighe's visual/gameplay test**

## Result

Build 0508 fixes the first proven post-initialization graphics failure.  Record 16 was already
correct because the post-`0x0504FA` scene reseed selected the final Y=$0100 window.  Build 0505 then
corrupted each newly exposed row in record 17: the no-publication camera route reused the selector-0
row-source formula even though selector 1 swaps the source block axes.  The corruption therefore
grew with vertical travel while the initial screen remained exact.

The correction precompiles the immutable selector-1/2 logical rows as final Genesis name words and
copies only the requested 64-word entering row.  It does not reconstruct an arcade descriptor,
transpose a map, resolve a tile code, or allocate a cache slot at runtime.  Selector-0 records retain
the established native dynamic producer.  Collision production is unchanged.

The ROM-producing source is exact commit
`d1ad940452dfa2ba31f67e826807582fbbb379b4`.  The implementation series is:

- `2a152ea9` — precompile selector-1 pan rows and final physical scene images;
- `2ee49835` — teach the row-coherence gate about the precompiled path;
- `4eb1d2bd` — record consumed 0506 and align exact postpatch coverage;
- `d1ad9404` — declare the pan-row asset as a real Make dependency.

Concurrent Palette Composer commits after `d1ad9404` were preserved and are not part of the ROM's
source identity.

## Semantic cut and removed chip tail

The cut remains:

`arcade record/selector/camera semantic decision -> final native Genesis Plane-A words`

Offline generation consumes the original record source tables, metatile pointer, attribute word,
selector transform, stable package assignment, and code-to-native-slot map.  It emits:

- `scene_fill_maps.bin`: six final physical 64x32 Plane-A images, 24,760 bytes;
- `pan_row_maps.bin`: four selector-1/2 final logical 64x64 maps for records 17, 21, 43, and 44,
  32,952 bytes.

The runtime scene helper is a bounded 4 KiB copy.  The selector-1/2 pan helper is a bounded 128-byte
row copy followed by the existing dirty-row mark.  The retired tail is the runtime descriptor walk,
axis transform, tile-code lookup, residency lookup, attribute conversion, and 2,048-cell scene
conversion.  There is no PC080SN RAM image, C-window shadow, tall buffer, generic arcade-map
reconstruction, runtime rotation/transposition, framebuffer, or gameplay workaround.

Native metatile records and their collision halves were already preconverted by the build.  This
change does not alter those records or collision consumers.  It removes runtime processing compared
with Build 0505; it introduces no new per-frame translation.

## First proven divergence

The first bad Build 0505 cell after leaving the exact initial window was record 17, selector 1,
camera/Plane-A Y=$012D, visible top logical row 27, physical row 27, column 6:

| Evidence | Value |
|---|---:|
| original logical coordinate | row 27, column 6 |
| independently reconstructed arcade code | `$0841` |
| expected native slot / final word | `$0311` / `$6311` |
| expected pattern prefix | `33333333333334443333333333334444` |
| Build 0505 staged and VDP word | `$6460` |
| incorrectly displayed slot/code | `$0460` / `$08F2` |
| incorrect pattern prefix | `94383333943733341437333331833443` |

The staged word equalled the VDP word, and slot `$0460` contained the correct bytes for code `$08F2`.
Thus publication and residency were internally coherent; the wrong semantic source coordinate was
selected before staging.  Build 0505 mismatch growth was 116/1,953 cells at Y=$012D, 328/1,953 at
Y=$014F, and 487/1,953 at Y=$0166.  This distinguishes the failure from a bad physical ring row,
VDP DMA, missing slot, or corrupt resident pattern.

## Record coverage

The selector values are decoded from source data, not inferred:

| Record | Selector | Native path | Verification |
|---:|---:|---|---|
| 16 | 0 | precompiled post-scroll scene image | actual Genesis initial capture matches arcade: 0 Plane-A/B identity, orientation, VDP, resident-pattern, and collision mismatches |
| 17 | 1 | precompiled entering rows | all 4,096 logical cells statically exact; actual Genesis at three scrolled positions is exact |
| 18 | 0 | established dynamic native selector-0 producer | exhaustive selector-0 coordinate/front/wrap/rebase and descriptor/subcell gates pass; package remains 5 |
| 19 | 0 | established dynamic native selector-0 producer | same exhaustive proof; package remains 5 |
| 20 | 0 | established dynamic native selector-0 producer | same exhaustive proof; package remains 5 |
| 21 | 1 | precompiled entering rows | all 4,096 logical cells statically exact; package remains 5 |

Records 16–21 all map to stable package 5.  Consequently these boundaries require neither a package
transition nor slot churn.  The selector-0 gate covers 163,840 coordinate/front/wrap/rebase cases and
934,928 descriptor/subcell/context cases.  The selector-1/2 gate covers 128 destination-row cases,
1,869,856 rebuilt-pointer/attribute cases, 1,869,856 output cases, and every one of 4,096 row/top
residency combinations.  The independent asset gate checks 12,288 scene cells and all 16,384
selector pan-map cells against original arcade reconstruction.

The existing bounded controller did not reach records 18–21 in 6,000 frames.  Those four attempts
ended with `capture_failed.txt`; no state was injected and no playthrough is claimed.  Record 21
therefore has full static source-to-native proof but not the requested multiple-position runtime
capture.  Records 18–20 have exhaustive producer proof but not a natural runtime transition capture.
These are explicit manual-test items below, not silently promoted to gameplay proof.

## Actual Genesis NTSC runtime proof

Initial record-16 window (`states/traces/rg0012_build0508_r16_initial`): state matches original arcade
at record cursor 17, selector 1, A/B Y=$0100.  Of 1,953 scored Plane-A and 2,048 Plane-B cells:

- tile identity mismatches: 0;
- orientation mismatches: 0;
- LUT misses: 0;
- staged-to-VDP mismatches: 0;
- resident VRAM pattern mismatches: 0;
- collision word mismatches: 0.

Record-17 scrolling used the actual Build 0508 R1-S2 ROM and Genesis NTSC MAME:

| Capture | A/B Y | visible top | final-word mismatches | staged↔VDP | resident-pattern mismatches |
|---|---:|---:|---:|---:|---:|
| `rg0012_build0508_r17_y120` | `$0131` | 26 | 0/1,953 | 0 | 0/1,953 |
| `rg0012_build0508_r17_y140` | `$014E` | 23 | 0/1,953 | 0 | 0/1,953 |
| `rg0012_build0508_r17_y160` | `$0166` | 20 | 0/1,953 | 0 | 0/1,953 |

The frames show coherent castle wall, floor, window, pillar/fire opening, and brazier identities with
no progressive selector-0 smear.  The real VDP pattern bytes were compared, not merely name indices.
At Y=$0166 the collision map SHA-256 is
`222d7169aa03dfa0f7d84f44c208c8970cd629cfe511279b692d16ec50689a9f`, byte-identical to Build 0505.

Canonical Build 0508 results recorded by the Makefile-owned ledger are
`canonical=PASS entry=PASS epoch=PASS`; the mandatory 30-second NTSC trace reports no unmapped memory
addresses.  The selector-0, full-span background-coherence, 64-row/residency, and scene/pan asset
gates all pass.  This preserves Build 0500's 64-row publication contract rather than replacing it.

## R1-S2 performance

Host-only MAME debugger `totalcycles` probes were paired at matching helper boundaries.  They do not
modify the ROM or emulated game state.

| Operation | Build 0505 | Build 0508 | Change |
|---|---:|---:|---:|
| one post-scroll scene reseed | 119,056 cycles | 31,154 cycles | -87,902 (-73.8%) |
| one selector-1 entering row before dirty mark | 26,252 cycles | 1,412 cycles | -24,840 (-94.6%) |

The record-16 scene reseed invoked once.  Thirteen observed record-17 entering rows were each exactly
1,412 cycles.  Records 16–21 remain in package 5, so no package-upload cost was introduced at their
boundaries.  VBlank work is unchanged: scene entry sets the same 32-row dirty mask, and each entering
row sets the same one-row bit and publishes the same 64 words.  Therefore the correction adds zero
VDP words/DMA commands relative to Build 0505 and substantially reduces main-loop producer cost.
Natural 17→18→19→20→21 transition cycle samples remain unmeasured because the bounded route did not
reach them.

## Artifacts

Both files are 3,432,120 bytes:

- normal: `dist/rastan-direct/rastan_direct_video_test_build_0508.bin`  
  SHA-256 `6cd134226f82cfb6d4c7c3929f7297d1fefd2bd998eb36a7b6780603b136674a`
- direct R1-S2: `dist/rastan-direct/rastan_direct_video_test_build_0508_S1-2.bin`  
  SHA-256 `96f63e694874622818763a62b33881ec07a106b7c611a8d4edeff33e67fc508c`

Build 0506 was consumed and deleted after the exact coverage gate rejected the guessed coverage
constant; it has no numbered artifact.  Build 0507 is preserved but rejected because the new asset
was initially absent from the dependency audit.  Build 0508 contains the dependency fix and passes.

## Manual acceptance checklist / remaining observations

Tighe must still perform the authoritative interaction run.  In particular, this agent has **not**
confirmed a complete castle playthrough or fourth-chain attachment on Build 0508.  The correction
does not touch player movement, object logic, chain visual records, attachment logic, or collision;
the matched collision dump proves no change at the tested record-17 state, and Tighe previously
confirmed those behaviors on Build 0503.  That is regression evidence, not a substitute for testing.

Please verify on Build 0508:

1. natural transitions 17→18→19→20→21, including reverse travel and ring wrap;
2. multiple camera positions in record 21 and the upper-castle walls/windows/floors;
3. all earlier chains, the fourth chain's visual, collision, and actual attachment interaction;
4. vertical progression into R1-S3 and boss entry/playability;
5. selector-0 stages outside R1-S2 and subjective gameplay speed.

Audio routing and the post-boss freeze remain separate and were not changed.  Build 0508 must not be
marked accepted until Tighe completes this checklist.
