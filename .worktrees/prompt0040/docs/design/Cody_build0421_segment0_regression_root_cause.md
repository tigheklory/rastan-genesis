# Build 0421 Segment-0 regression root cause

Build 0419 is the accepted visual baseline. A focused NTSC MAME capture used
the same input schedule and matched semantic state for Builds 0419 and 0421.
At the stable pre-movement state, Plane A, Plane B, the full 8 KiB collision
ring, and descriptor state were byte-identical. At matched player X `0x0081`,
foreground Y `0x0149`, record 1, strip/group `0/0`, the first divergence was:

| field | Build 0419 | Build 0421 |
|---|---:|---:|
| product/cell | Plane A row 1, column 1 | Plane A row 1, column 1 |
| name word | `0x62CA` | `0x6297` |
| source descriptor | `0x01691C` | `0x01695C` |
| generated record | 2997 | 1412 |

The complete matched differential contains 33 Plane-A word differences, zero
Plane-B differences, and zero collision-map differences. Evidence is in
`states/traces/build0421_segment0_semantic_diff/semantic_diff.tsv`.

## Root cause

Build 0421 grouped each aligned four-column Plane-A row block under one source
descriptor. That assumption fails at the live 64-column ring seam. The
authoritative per-cell resolver treats cells after
`front=(A5+0x10CC)*4+(A5+0x10CA)` as belonging to the preceding ring
revolution. With front 0, column 0 correctly uses live descriptor `0x01695C`,
while columns 1–3 must use `0x01691C`. The grouped path reused `0x01695C` for
all four. Record 1412 supplies uniform source tile `0x0020`, explaining the
repeated wrong `0x6297` names.

## Correction

Four-cell batching remains for every block wholly on one side of the live
front. The single block satisfying `start <= front < end` is resolved through
the established per-cell accessor. This is coordinate-general and contains no
segment, tile, or scene special case. Plane B and collision production are
unchanged.

