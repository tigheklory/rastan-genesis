# R1-S2 Plane A scrolling placement correction — Build 0526

Date: 2026-11-01

Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0053`

Reference: Build 0525

Candidate: Build 0526, **not accepted pending Tighe's gameplay test**

## Result

A specific source-selection error is proven at the R1-S2 record-17 to record-18 transition.
Record 17 uses selector 1, whose arcade producer transposes the source block axes and reverses the
destination block-row axis. Record 18 uses selector 0. While record 18 is replacing the 64-column
ring, columns after the live ring front still contain record-17 selector-1 cells. The original
PC080SN retains those exact cells. Build 0525's Genesis entering-row helper instead reconstructed
the retained columns through selector-0 geometry. The selected patterns and palette could therefore
be valid while architectural cells appeared in the wrong positions. As the ring was replaced, the
bad retained region shrank, accounting for the reported later realignment.

Build 0526 keeps the existing native renderer and corrects only that retained-side calculation.
During a selector-1/2 to selector-0 transition, the dynamic row helper now takes columns after the
live front from the preceding record's existing final-native selector row. Columns through the
front continue to use the live selector-0 resolver. The row is still written to `logical_row & 31`
and published through the existing one-row dirty bit.

No new map, buffer, translation layer, PC080SN state, DMA, VRAM allocation, scene special case,
coordinate offset, collision change, or gameplay change was introduced.

## Original arcade authority

The hardware ownership is:

| Work-RAM field | Arcade commit | Meaning |
|---|---|---|
| `A5+$10EE` | `$055AB4 -> $C20000` | tilemap-0 Y |
| `A5+$10EC` | `$055ABC -> $C40000` | tilemap-0 X |
| `A5+$10B0` | `$055AC4 -> $C20002` | tilemap-1 / Plane-A Y |
| `A5+$10AE` | `$055ACC -> $C40002` | tilemap-1 / Plane-A X |

This agrees with the PC080SN register groups in MAME: `$C20000/$C20002` are the two Y-scroll
registers and `$C40000/$C40002` are the two X-scroll registers. It also agrees with the Ghidra
hardware-reference export, which identifies `$C20000/2` as `PC080SN_yscroll` and `$C40000/2` as
`PC080SN_xscroll`. The maintained arcade documentation in
`docs/arcade_reference/pc080sn/gameplay_control_assembly.md` has the same ownership. The conflicting
field table in Andy PROMPT-ID-0050 is not consistent with the original instructions or hardware
register groups and was not used.

The relevant original control flow is:

1. `$055696/$05572E` change Plane-A Y (`A5+$10B0`) and publish selector-1/2 rows when that selector
   owns the crossing.
2. `$0557BA/$055854` change Plane-A X (`A5+$10AE`) for the selector-0/opposite-X paths.
3. `$055948` publishes the strip and then increments `A5+$10CA`.
4. `$0558A2` advances the sixteen descriptor-source pointers after four strips; after sixteen
   groups `$0558E0` saves the old selector in `A5+$132C`, loads the next selector, and increments
   record `A5+$013E`.
5. Selector 1's destination is
   `63 - (group*4 + strip)` and its source block axes are transposed; selector 0 is direct-axis.

Therefore, immediately after the 17→18 handoff, the arcade ring is intentionally mixed. If
`front = (A5+$10CC)*4 + (A5+$10CA)`, columns through `front` have been replaced by the current
selector-0 record and columns after `front` retain the preceding selector-1 record. Vertical camera
motion does not rewrite or reinterpret that retained PC080SN content.

## Build 0525 discrepancy

Build 0525's `.Lplane_a_publish_logical_row_native` correctly computes the entering logical row,
physical row, current descriptor pointer, live front, and dirty-row publication. Its dynamic
selector-0 resolver also correctly handles selector-0 to selector-0 ring history.

The demonstrated mismatch is narrower: the resolver's preceding-revolution pointer walk always
uses selector-0 axes. At 17→18, that preceding revolution is selector 1. Thus the Genesis result for
the retained side was:

```text
record-17 descriptor data + selector-0 coordinate interpretation
```

while the original retained ring contains:

```text
record-17 descriptor data + selector-1 transpose/reversal
```

This is why scene initialization and record-17 scrolling can be exact, collision can remain correct,
and the first mixed selector boundary can still display correctly decoded tiles at wrong locations.
It also explains why rebuilding every column from the current selector was not equivalent to the
arcade's retained ring.

## Small correction

Changed only `apps/rastan-direct/src/tilemap_hooks.s`, inside
`.Lplane_a_publish_logical_row_native`.

After the existing selector-0 row resolver finishes:

- require current selector 0;
- require a nonzero preceding selector in `A5+$132C`;
- select record `A5+$013E - 1` from the already-existing
  `genesistan_plane_a_pan_row_maps` table;
- if that preceding record has a selector-1/2 row asset, copy only columns `front+1..63` from its
  requested logical row over the dynamically reconstructed row;
- retain columns `0..front`, the physical `logical_row&31` placement, and the existing dirty bit.

The asset is not new: records 17, 21, 43, and 44 were already present for the selector-1/2
no-publication row path. The correction is data-general and activates only where the previous
record actually has such an asset. A selector-0 to selector-0 transition remains byte-for-byte on
the prior dynamic route.

The semantic cut remains `arcade record/selector/ring-front decision -> final Genesis Plane-A name
words`. The removed chip tail remains the PC080SN C-window/name-RAM realization. Collision, player
movement, scene initialization, checkpoint state, Plane B, PC090OJ, palettes, audio, and VDP scroll
publication are unchanged.

Exact ROM-producing source commit:
`f0b7218c53af3488bd1d5276e71ba617be2f584d`.

## Static and build verification

No diagnostic trace, instrumentation, first-divergence capture, gameplay automation, or new test
tool was created. The normal Makefile's mandatory 30-second MAME run still executed because it is a
required release gate.

Existing deterministic checks passed, including:

- full-span Plane-A/Plane-B background coherence and ring-seam checks;
- selector-0: 163,840 coordinate/front/wrap/rebase cases and 934,928 descriptor/subcell/context cases;
- selector-1/2: 128 destination-row cases, 1,869,856 rebuilt-metatile/attribute cases,
  1,869,856 output cases, and 4,096 row/top residency cases;
- scene/pan assets: 24,576 Plane-A scene cells, 3,072 scene-origin projections, 16,384 pan cells,
  and 1,138,688 authored descriptor cells;
- native metatile, collision/visual independence, boot guards, selector-stream relocation, final-life,
  canonical, gameplay-entry, and seven-epoch/package gates;
- required standard variant-set verification;
- mandatory Genesis NTSC 30-second run: final PC `$03B2C8`, SP `$00FEFFFC`, no unique unmapped
  memory addresses reported.

The build adds only bounded CPU copies on affected entering-row events: at most the unreplaced
suffix of one 64-word row. It adds no VDP words or DMA commands because the same complete row was
already published.

## Build 0526 artifacts

Counter and consumed ledger: `0526`, `canonical=PASS entry=PASS epoch=PASS`.

| Artifact | Size | SHA-256 |
|---|---:|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0526.bin` | 3,792,568 | `d6eca7393cd22f178cd313ee4afec9f221232755b75f711ef8cfd8446f56efda` |
| `dist/rastan-direct/rastan_direct_video_test_build_0526_S1-2.bin` | 3,792,568 | `f1c0a126bd1028014c1f4da1beea1f13a5e56dc39a087d273ea5740dba8a407b` |

The direct-start variant retains the established R1-S2 selector (`$DF`) and command `$27` audio
initialization patch. No music data was duplicated.

## Remaining uncertainty and required gameplay test

The source discrepancy and correction are established, but this assignment deliberately did not
generate a matched runtime capture of the natural 17→18 transition. Build 0526 is therefore a
candidate, not an acceptance claim.

Tighe must test the `_S1-2` ROM through the complete natural climb and specifically verify:

1. record-17 scenery remains correct before the handoff;
2. architecture remains correctly placed as record 18 begins replacing record 17;
3. reverse movement across the same mixed-ring interval does not regress;
4. records 19–21 and the reported near-end realignment remain coherent;
5. R1-S2 checkpoint restoration still displays the correct initial scenery;
6. R1-S1 checkpoint restoration remains unchanged;
7. collision, traversal, Plane B, actors, palettes, Re-In-Carnation, and boss entry remain unchanged.

The gray border, missing R1-S3 Composer contexts, armored-man sprite corruption, boss music, and rope
benchmark remain separate issues and were not modified.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0053`
