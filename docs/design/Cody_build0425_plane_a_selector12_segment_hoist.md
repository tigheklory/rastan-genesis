# Build 0425 Plane-A selector-1/2 segment hoist

## Accepted baseline

Tighe played Build 0424 on real Genesis hardware: gameplay PASS, visuals PASS,
and no new defect observed. Build 0424 is the accepted forward baseline. Its
selector-0 implementation and Build-0423 Plane-B implementation are unchanged
in Build 0425.

## Exact structure and safe sharing cut

Static inspection corrects one premise in the task description: selector 1/2
publishes **one fixed logical row across 64 columns**, arranged as sixteen
aligned four-column metatile blocks. It is not four varying rows. Within a
four-column block, row-group source selection, descriptor relocation and
validation, native-record discovery, and descriptor attribute are invariant.
The four visual/collision subcells and destinations remain independent.

The live horizontal ring front is the only exception. When an aligned block
has `block_start <= front < block_end`, its columns can belong to two descriptor
revolutions. Build 0425 retains the accepted per-cell fused/collision-only
resolver for that one block. The other fifteen blocks share one descriptor and
one native record. This is the same seam that invalidated the rejected
Build-0421 unconditional grouping assumption.

The fixed logical row is either resident or nonresident for the event. In the
resident case each cell consumes independent visual and collision fields,
performs its dynamic package/residency lookup, stages its Plane-A name, and
writes collision. In the nonresident case every cell still reads and writes
collision but does no visual read, residency lookup, or Plane-A write.
Collision is never derived from the visual name, VRAM slot, palette, priority,
or flip bits.

For a fully valid resident event, accepted Build 0424 versus Build 0425:

| work | 0424 | 0425 |
|---|---:|---:|
| descriptor selection/relocation/validation | 64 | 19 (15 shared + 4 seam fallback) |
| native-record lookup | 64 | 19 |
| attribute conversion | 80 (16 redundant outer + 64 cell) | 19 |
| collision subcell reads/writes | 64 / 64 | 64 / 64 |
| visual subcell reads | 64 | 64 |
| dynamic residency lookups | 64 | 64 |
| Plane-A staging writes | 64 | 64 |

For a nonresident event, collision reads/writes remain 64/64 while visual,
residency, and Plane-A writes remain zero. Attribute conversions fall 16→0.
The exact safe count is therefore 19, not the unsafe unconditional target of
16. Invalid rebuilt-pointer segments retain the accepted skip behavior.

## Runtime equivalence and boundary proof

`verify_plane_a_selector12_segment_hoist.py` compares the accepted Build-0424
per-cell selection with the Build-0425 shared selection plus seam fallback. It
passes:

- 655,360 selection/front/wrap/rebase cases, including 30,720 seam fallbacks;
- 1,869,856 descriptor/subcell/dynamic-context output cases;
- all 4,096 logical-row/visible-top placements: 2,048 resident and 2,048
  nonresident;
- every row group, column block, strip alignment, group rollover, descriptor
  range edge, source rebase, and N/N+32 projection class.

The full-span background, collision/visual independence, generated-record,
transition-retention, and DMA-boundary gates also pass. All 64 collision writes
remain unconditional; visual work remains resident-only.

## Matched MAME differential

Builds 0424 and 0425 reached the same stable semantic state at frame 533:
state `2/3/0`, scene 1, player X/Y `0x0081/0x0000`, record 1, Plane-A scroll
`0x0000/0x0149`, and strip/group/subcolumn zero.

- Plane A: zero differing words;
- Plane B: zero differing words;
- full 64x64 collision ring: zero differing words.

Evidence: `states/traces/build0425_matched_semantics/`.

## Objective performance

The normal rope/climb routes do not naturally execute this retained selector
hook. The exact entry/RTS bracket was therefore measured with 50 matched,
controlled invocations from the same stable gameplay state in each ROM:

| build | samples | min | median | max | mean |
|---|---:|---:|---:|---:|---:|
| 0424 | 50 | 122,672 | 122,672 | 122,672 | 122,672.000 |
| 0425 | 50 | 33,984 | 33,984 | 63,634 | 35,170.000 |

Median cost falls by 88,688 cycles (72.297%); mean falls by 87,502 cycles
(71.330%). Evidence:
`states/traces/build0425_selector12_targeted_cycles/`.

The established natural three-trial start-to-first-rope benchmark is unchanged:

| build | trials | median frames | median emulated time |
|---|---|---:|---:|
| 0419 | 878 / 878 / 878 | 878 | 14,652.200 ms |
| 0422 | 879 / 879 / 879 | 879 | 14,668.888 ms |
| 0423 | 858 / 858 / 858 | 858 | 14,318.437 ms |
| 0424 | 817 / 817 / 817 | 817 | 13,634.222 ms |
| 0425 | 817 / 817 / 817 | 817 | 13,634.222 ms |

This is expected because the natural rope route does not execute selector 1/2.
Evidence: `states/traces/build0425_rope_attach_benchmark/`.

## Gates and scope

Canonical, boot, gameplay-entry, runtime-equivalence, generated-record,
full-span background, collision/visual, transition-retention, DMA-boundary,
mandatory NTSC trace, and complete five-ROM-family gates pass. Gameplay entry
reports zero bus errors, address errors, illegal instructions, and crash-handler
entries. The standing seven-epoch label still reports its historical warning
after the production-boundary epoch-0 PASS, unchanged from accepted builds.

Selector 0, Plane B, collision semantics, sprites, IRQ6 scheduling, worker
placement, VBlank ownership, active-display DMA, and Phases D/E are unchanged.

## Background closure audit

**BACKGROUND GRAPHICS CLOSED FOR CURRENT PERFORMANCE PHASE.** The identified
material descriptor/native-record costs are now generated, cached, or shared:
Plane-B rows/directional columns, Plane-A selector 0, and Plane-A selector 1/2.
The remaining per-cell work is genuinely dynamic or bounded: tile residency,
final name formation, independent collision values/destinations, staging dirty
state, publication, and DMA. No additional named background path with a
material repeated cost is presently proven.

Next: **short final sprite closure audit**. No Phase D/E work begins here.

## Artifacts

All five artifacts are 2,698,936 bytes:

| artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0425.bin` | `a2d174ba81ef7776f2b80b6fc4dafcd1b803907c0dcb2b424ce377a2e73641cb` |
| `rastan_direct_video_test_build_0425_c.bin` | `669c9be65312bca3faccb745effbc79e72f990990f381aacad9b456e4ef68aeb` |
| `rastan_direct_video_test_build_0425_d.bin` | `deb22c912e08de325b86d30bee677d27b23271624c8afdd8f841b60ee8044702` |
| `rastan_direct_video_test_build_0425_do.bin` | `27e7715d16d64ef61ca4e232519e862c82e888379f0d9bced28551b44d35d211` |
| `rastan_direct_video_test_build_0425_s.bin` | `d0741a79ad10b38322d41e12bb606feae1253007d41c5cb102610c71a7506daa` |

Counter: 425. Real-Genesis validation of normal and `_do` remains Tighe's gate.
