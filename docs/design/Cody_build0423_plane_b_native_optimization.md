# Build 0423 Plane-B native optimization

## Baseline status

Tighe verified Build 0422 on real Genesis: the Segment-0 visual regression is
fixed and the destructible block still behaves correctly. Build 0422 is the
accepted forward baseline. Build 0420 remains rejected for illegal `TST.L A0`;
Build 0421 remains rejected because its Plane-A grouping crossed the live ring
front.

## Semantic cut

The retained arcade logic still chooses the live Plane-B descriptor from the
current group/strip state and supplies the live subcolumn, scroll, ring, scene,
package, and residency context. Build 0423 cuts immediately after that dynamic
descriptor selection. It replaces only the invariant PC080SN descriptor tail:
attribute decoding and conversion plus recovery of the copied-maincpu tile
block pointer.

The generated six-byte visual record is:

```text
Genesis native attribute (BE16)
copied-maincpu tile-block pointer (BE32)
```

Records are keyed by the exact selected descriptor's byte offset in the
authoritative `0x03951C..0x03A00C` table. There are 392 valid descriptors in a
2,802-byte table. The record is visual-only and contains no collision field or
collision-derived input. Plane-A architecture and the separate 64x64 gameplay
collision map are unchanged.

## Directional-column change

Build 0422 selected one descriptor, probed all 64 logical rows, read 64 raw
tile-block words, and called the generic Plane-B producer 64 times. The helper
rejected the nonresident half, so only 32 cells were emitted; the resident half
also performed 32 attribute conversions and 32 dynamic package lookups.

Build 0423 looks up the selected generated record once, starts at the live
visible top, and directly emits the 32 resident rows. It performs 32 tile-block
reads, no generic-helper calls, no runtime attribute conversion, and the same
32 dynamic package/residency lookups. Descriptor selection and all 32 final
name-word semantics remain dynamic.

The generated-record verifier reproduces accepted Build-0422 behavior for all
16 subcolumns, all 64 ring-top placements, representative dynamic package
contexts, and descriptor changes at every possible 16-column alignment. Ring
wrap, nonzero alignment, group/segment boundaries, and initial population pass
the existing background verifier suite.

## Objective performance

The focused MAME `totalcycles` measurement used the same deterministic rope
route and matched Plane-B directional-column entry/return boundaries:

| build | samples | min | median | max | mean |
|---|---:|---:|---:|---:|---:|
| 0422 | 66 | 64,564 | 64,578 | 64,690 | 64,577.061 |
| 0423 | 66 | 12,472 | 12,486 | 12,598 | 12,485.061 |

The median and mean both fall by 52,092 cycles, or 80.683%, for this targeted
column operation.

The existing start-to-first-rope benchmark, three trials per build:

| build | frames | median emulated time |
|---|---|---:|
| 0419 | 878 / 878 / 878 | 14,652.200 ms |
| 0422 | 879 / 879 / 879 | 14,668.888 ms |
| 0423 | 858 / 858 / 858 | 14,318.437 ms |

Build 0423 is 21 frames / 350.451 ms / 2.389% faster than Build 0422 on this
route, and 20 frames / 2.278% faster than Build 0419.

## Correctness and gates

Matched NTSC MAME state at frame 564 (player X `0x0081`, player Y `0x0000`,
record 1, Plane-A scroll `0x0000/0x0149`) gives zero differing Plane-A words,
zero differing Plane-B words, and zero differing collision words between Builds
0422 and 0423. Canonical, boot, gameplay-entry, generated-record, full-span
background, collision/visual separation, DMA-boundary, mandatory 30-second
NTSC trace, and complete five-ROM-family gates pass. Gameplay entry records zero
address, bus, illegal-instruction, or crash-handler entries. The standing
seven-epoch label still reports FAIL after its epoch-0 PASS, unchanged from the
accepted baseline.

Evidence:

- `states/traces/build0423_matched_semantics/`
- `states/traces/build0423_plane_b_targeted_cycles/`
- `states/traces/build0419_rope_attach_benchmark/`
- `states/traces/build0422_rope_attach_benchmark/`
- `states/traces/build0423_rope_attach_benchmark/`
- `build/rastan-direct/pc080sn_plane_b_visual_report.json`

## Remaining background cost

Background optimization is not closed. Plane-A selector 0 still repeats live
descriptor selection four times inside each already-proven four-row vertical
segment. Hoisting that selection once per segment, while preserving seam
handling and independent visual/collision products, is the next bounded
material background candidate. It is not implemented in Build 0423.

## Artifacts

All artifacts are 2,698,936 bytes:

| artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0423.bin` | `0891f25fb0872cfa8e6bef1e600fc7f5d9e499eae6cdf2ad76e3b66709cea572` |
| `rastan_direct_video_test_build_0423_c.bin` | `42e1fa9e034120d98755e6ad9ec93ed778ef7b687a0d0956516ef25db20412de` |
| `rastan_direct_video_test_build_0423_d.bin` | `3f871012a711ffd5298c9f81dd4ee7c673cc2d298de46b808557d8821f360e3e` |
| `rastan_direct_video_test_build_0423_do.bin` | `60a0440b60bdfbf0daf1fefc0c8e2a65039c41cf293a22d5929261108985bbb7` |
| `rastan_direct_video_test_build_0423_s.bin` | `d062bc1e35b861a3dcec0aba00caf60a06ba5b2e56ac7a35ff900983b9ea512a` |

Counter: 423. Tighe subsequently verified gameplay and visuals on real Genesis
with no new defect observed and accepted Build 0423 as the forward baseline.
