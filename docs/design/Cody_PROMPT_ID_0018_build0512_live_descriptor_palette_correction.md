# PROMPT-ID-0018 — Build 0512 live-descriptor palette correction

Date: 2026-10-27  
Author: Cody  
Status: **candidate, not accepted; Tighe gameplay verification remains required**

> **Superseded R1-S2 validation note (PROMPT-ID-0022):** the Build 0512 R1-S2 statement below did
> not validate Plane B with the final camera-selected 32-row ring. The verifier used a special
> pre-camera Plane-B physical-row model and therefore blessed the same half-ring error visible in
> gameplay. Corrected scoring finds 2,048/2,048 Plane-B pattern cells wrong at entry. Build 0513
> corrects that defect and proves Plane A and Plane B independently. The Build 0512 artifact remains
> preserved and unaccepted; see the PROMPT-ID-0022 report.

## Delivered artifacts

The exact ROM-producing source commit is
`c8fd3e5d4e8b9bce73a45233aa078b761b57a5f0` (`Fix authored Plane-A visuals at live descriptor boundary`).

| Artifact | Size | SHA-256 |
|---|---:|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0512.bin` | 3,792,568 | `d56fd9a1580bce57fb1b700bb1c850573a4bef31098587e4efc03a1c3764e574` |
| `dist/rastan-direct/rastan_direct_video_test_build_0512_S1-2.bin` | 3,792,568 | `b35adc88ae00a50041c728d28ce3820a7ad9d1d9cf78138342d2dc26fa0096e1` |

The Makefile-owned counter is 512 and the consumed ledger records 0512 as
`canonical=PASS entry=PASS epoch=PASS`. The normal build's mandatory Genesis NTSC MAME run completed
1,798 frames; its execution summary reports live VDP writes and no live writes to an arcade C-window.
The normal and S1-2 release files compare byte-for-byte equal to the final candidate pair used for the
runtime captures below, so the captures apply to the delivered ROMs.

## First regression and root cause

Build 0508 was used as the geometry authority. Build 0509 was the first broken binary; 0510 and 0511
retained the same defect.

The first bad transformation in the matched R1-S1 trace occurs at scroll offset 40. Camera, record,
selector, strip/group and retained live descriptor state still agree with 0508, but 0509 substitutes a
cell from its new full static `record_native_maps.bin` product (including blank logical code `0x00AD` at
the observed divergence) instead of publishing the visual selected by the live `a5+0x1000` descriptor
and ring coordinates. The resulting staged name word, resident slot/pattern and final Plane-A word are
therefore wrong even though the scene palette is correct.

The 0509 palette integration crossed the semantic boundary in the wrong direction: its runtime
full-record lookup was keyed by `(active record,row,column)` and bypassed the working 0508 selector-0
descriptor/ring producer. The same substitution also assembled R1-S2 castle records incorrectly. This
was one shared geometry defect, not a collision or chain-attachment defect and not a color-selection
failure.

## Correction and semantic boundary

The corrected cut is:

`retained arcade gameplay chooses the live descriptor and logical cell -> direct lookup of an
offline-authored native visual pair -> existing native cache resolves the logical code -> final Genesis
name word is staged/published`.

The retained gameplay producer remains responsible only for the dynamic facts that cannot be known at
build time: current scene, live descriptor pointer, camera/ring coordinate, row/column, and collision
selection. The retired PC080SN tail remains retired. There is no PC080SN address-space/device model,
C-window shadow, framebuffer, rotation/transposition, full-map projection, or general arcade map
reconstruction.

The compiler now emits `build/pc080sn_boundary/authored_descriptor_visuals.bin`:

- two authored scene contexts (R1-S1 and R1-S2);
- 35,584 exact descriptor entries per context over `0x1691C..0x3951C`;
- a 284,672-byte direct-offset index and 55,424-byte deduplicated payload;
- 866 unique prepared records, 340,096 bytes total;
- SHA-256 `d1f2d0b35502e3446e27d553ef32cd8c8e275a697cbda3db214bb5691656d201`.

Each payload is sixteen `{synthetic logical code, final Genesis attribute}` pairs. Palette reindexing,
pixel transformation, scene ownership, flip/attribute preparation, pattern allocation and package
construction are all build-time work. The authored profile SHA-256 is
`3a9ed339a9989b4f94921aed82f4a75b6b22af107368cafa0ba4fcbcbde18cb2`;
2,093 usages are mapped, eight remain unmapped, and 1,721 synthetic patterns are generated. The user
profile was consumed, not rewritten by this correction.

`record_native_maps.bin` remains a compiler/verifier intermediate and is no longer included or queried
by production runtime code. Native metatile records remain preconverted and keep their independent
visual and collision halves. The runtime does not dereference an already rebuilt descriptor a second
time. Selector 1/2 consumes the rebuilt native metatile pointer and its exact parallel attribute/source
entry; the authored visual lookup is a direct indexed load, not descriptor reconstruction. The only new
hot-path work relative to 0508 is the bounded O(1) context-index/payload fetch followed by the already
established logical-code-to-resident-slot resolution.

R1-S1 and R1-S2 CRAM assets are selected once from an offline stage-to-asset table. Lines 0, 1 and 3
come from the scene's 96-byte authored asset. Line 2 is deliberately absent from those assets and
continues to be owned and updated by the arcade palette producer; R1-S2 flame mappings remain on Line 2.

## Static and runtime validation

The exhaustive build gates passed:

- 1,138,688 authored descriptor payload cells;
- 12,288 scene-fill cells and 16,384 selector-1/2 pan-row cells;
- 163,840 selector-0 coordinate cases and 934,928 descriptor/subcell cases;
- 1,869,856 selector-1/2 rebuilt-pointer/attribute/output cases plus 4,096 residency cases;
- full-span background publication, including Build 0500's 64-row contract;
- native collision semantics and transition-retention/package-capacity gates.

### R1-S1 geometry

Matched Build-0508 versus Build-0512 hardware captures cover offsets 0 through 120 in 10-pixel steps,
then 240, 360, 480, 600, 720 and 840. After normalizing intentional palette and physical-slot changes,
all 19 captures have zero Plane-A identity/orientation/occupancy mismatches. The comparison uses the
actual VDP name words and the pattern bytes resident in the referenced slots, not two compiler-side map
products. Camera/ring states agree. Screens cover outdoor horizontal scroll, cave transitions and ring
wraparound and retain the 0508 walls/ground/cave geometry.

The R1-S1 hardware CRAM capture's Lines 0, 1 and 3 exactly equal
`PAL-R1-S1-PLANEA-OUTDOOR.bin`; hardware Line 2 is nonzero and was not installed by the authored asset.

### R1-S2 geometry, palette, and collision

At matched castle states, normalized Plane-A output has zero mismatches from Build 0508. At record 17
and vertical scroll `0x0166`, the final VRAM Plane-A geometry matches the 0508 capture and the 8,192-byte
collision map is byte-identical, SHA-256
`222d7169aa03dfa0f7d84f44c208c8970cd629cfe511279b692d16ec50689a9f`. Runtime screens show coherent
castle walls, columns, windows, floors and brazier/flame placement through the tested vertical range.

The R1-S2 hardware CRAM capture's Lines 0, 1 and 3 exactly equal
`PAL-R1-S2-PLANEA-CASTLE.bin`; hardware Line 2 remains nonzero and arcade-owned. The two authored CRAM
assets have distinct hashes (`fa7147...65ebe` for R1-S1 and `281f9f...c26d` for R1-S2), proving that
the independent scene selection survived the geometry fix.

The established R1-S2 climb harness reached record 17/selector 1, logged 9,809 head-probe results, and
observed a real `CLIMB_BLOCKED` interaction at frame 4094 using the unchanged collision map. No collision
or attachment workaround was added.

### Performance

| Path | Build 0508 | Build 0512 | Result |
|---|---:|---:|---|
| selector-1 precompiled pan-row event | 1,412 cycles | 1,412 cycles | unchanged (13 samples) |
| scene reseed | 31,154 cycles | 31,154 cycles | unchanged |
| selector-0 entering-column event, mean of 181 | 37,841.6 cycles | 44,094.0 cycles | +6,252.4 (+16.5%) |

Selector-0 medians are 37,830 and 44,102 cycles; ranges are 37,810–38,218 and 40,530–44,490. This is a
measurable bounded main-loop cost when crossing an 8-pixel entering-column boundary (about 4.9% of one
NTSC frame budget at the mean delta), not an every-frame or VBlank cost. DMA/VBlank publication and the
selector-1/2 fast path are unchanged. The final direct 32-bit payload-offset format avoids a runtime
search and reduced the corrected selector-0 event by about 605 cycles from the preceding candidate.

## Unverified gameplay and acceptance boundary

This work does **not** claim a completed R1-S2 playthrough or verified fourth-chain attachment. Automated
runtime coverage stopped in record 17. Tighe still needs to verify on the delivered S1-2 ROM:

- earlier chain attachment/release behavior;
- the fourth chain's complete visual, collision and attachment interaction;
- later records 18–21 and the remainder of R1-S2 traversal;
- broader selector-0 manual traversal and later selector-0 stages;
- R1-S3/boss and any other selector-0 regression observations.

Build 0512 is therefore a correction candidate only. It must not be marked accepted until Tighe's final
gameplay test.
