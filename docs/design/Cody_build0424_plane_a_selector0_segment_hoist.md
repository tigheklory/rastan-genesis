# Build 0424 Plane-A selector-0 four-row segment hoist

## Accepted baseline

Tighe played Build 0423 on real Genesis hardware: gameplay PASS, visuals PASS,
and no new defect observed. Build 0423 is the accepted forward baseline. Its
Plane-B generated-record and directional-column implementation is unchanged in
Build 0424.

## Bounded sharing proof

Selector 0 publishes one fixed entering logical column across sixteen aligned
four-row descriptor segments. For the four rows within one segment, accepted
Build 0423 repeated the fused per-cell resolver four times.

Invariant across those four rows:

- live row-segment source-pointer selection;
- fixed entering-column/source-reference adjustment;
- raw descriptor address, relocation, and validation;
- native metatile-record lookup;
- descriptor-wide Plane-A attribute conversion.

Genuinely row/cell-dependent and retained:

- row-within-metatile subcell;
- visual tile identity;
- collision subcell value and collision-map destination;
- dynamic package/residency lookup;
- visible-row projection and Plane-A staging destination;
- final Genesis name-word formation.

The existing rebuilt-pointer validity gate remains once per segment. Build 0424
then selects one live descriptor and one generated `visual[16]/collision[16]`
record, using the distinct fields independently across four row outputs. It
does not derive collision from a Plane-A name word, VRAM slot, palette, flip, or
priority.

For each valid segment, live semantic descriptor selections, relocations, and
native-record lookups change from 4 to 1. Attribute conversions change from 5
to 1: Build 0423 performed four resolver conversions plus one legacy outer
conversion whose result was overwritten; Build 0424 performs the single shared
conversion. Residency lookups remain 4, candidate Plane-A outputs remain 4,
and collision writes remain 4. Across a fully valid sixteen-segment event, the
corresponding maximum counts are descriptor/record 64→16, attribute conversion
80→16, residency 64→64, staged resident Plane-A writes 32→32, and collision
writes 64→64.

## Runtime-selection and boundary proof

The dedicated verifier compares accepted-0423 four independent resolutions
with Build-0424 one shared selection plus four independent outputs. It passes:

- 163,840 selector-0 coordinate/front/group-rollover/source-rebase cases;
- 934,928 descriptor/subcell/dynamic-context cases;
- all row-in-segment values 0/1/2/3;
- all logical front columns and nonzero strip alignments;
- descriptor-range edges, invalid boundary fragments, segment changes, source
  rebases, initial/scroll source states, and row-ring group rollover;
- independent Plane-A visual and collision products.

The accepted horizontal four-column ring-front guard is untouched. This change
groups aligned vertical rows only; it does not repeat the rejected Build-0421
horizontal assumption. Full-span coherence, N/N+32 retention, transition
retention, source rebase, collision/visual independence, and VDP DMA-boundary
gates pass.

## Matched MAME differential

The existing semantic capture reached the same state in Builds 0423 and 0424:
state `2/3/0`, scene 1, player X/Y `0x0081/0x0000`, record 1, Plane-A scroll
`0x0000/0x0149`, strip/group/subcolumn 0, BG walker `0x039534`.

- Plane A: zero differing words;
- Plane B: zero differing words;
- full 64x64 collision ring: zero differing words.

Evidence: `states/traces/build0424_matched_semantics/`.

## Objective performance

The exact selector-0 entry/cleanup bracket was measured on the same deterministic
MAME rope route, with 196 matched calls per build:

| build | min | median | max | mean |
|---|---:|---:|---:|---:|
| 0423 | 108,376 | 112,090 | 112,478 | 112,082.653 |
| 0424 | 46,204 | 49,918 | 50,306 | 49,910.653 |

Median and mean both fall by 62,172 cycles, or 55.466%, per selector-0 event.
Evidence: `states/traces/build0424_selector0_targeted_cycles/`.

The established three-trial start-to-first-rope benchmark is deterministic:

| build | frames | median emulated time |
|---|---|---:|
| 0419 | 878 / 878 / 878 | 14,652.200 ms |
| 0422 | 879 / 879 / 879 | 14,668.888 ms |
| 0423 | 858 / 858 / 858 | 14,318.437 ms |
| 0424 | 817 / 817 / 817 | 13,634.222 ms |

Build 0424 is 41 frames / 684.215 ms / 4.779% faster than accepted Build 0423
on this route. Evidence: `states/traces/build0424_rope_attach_benchmark/`.

## Gates and scope

Canonical, boot, gameplay-entry, selector-0 runtime equivalence, generated
record, full-span background, collision/visual, transition-retention,
VDP-DMA-boundary, mandatory 1,798-frame NTSC trace, and five-ROM-family gates
pass. Gameplay entry reports zero bus, address, illegal-instruction, and crash
handler events. The standing seven-epoch label remains FAIL after its epoch-0
PASS, unchanged from accepted builds.

Plane B, collision semantics, sprites, worker/IRQ6 scheduling, VBlank ownership,
active-display DMA, and Phases D/E are unchanged.

## Remaining-cost decision

Background status is **NOT CLOSED**. One more material background optimization
exists: `genesistan_hook_tilemap_plane_a_selector12_native` still performs live
descriptor/native-record discovery per row across the same sixteen four-row
segments, branching between resident fused visual+collision and nonresident
collision-only leaves. Hoisting descriptor/record discovery once per proven
segment can eliminate up to 48 of 64 selections/lookups per event while keeping
all 64 collision writes and dynamic resident visual/residency work. This is not
implemented in Build 0424. Tiny per-cell residency, final-name, destination,
dirty/publication, and DMA work is genuinely dynamic or already bounded.

Next: one more material background optimization, limited to selector 1/2.

## Artifacts

All five artifacts are 2,698,936 bytes:

| artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0424.bin` | `11ab83be9056d77bd0e79dff0f82ef5afe3600fc711b55c87e9f9e12ddf326ff` |
| `rastan_direct_video_test_build_0424_c.bin` | `b4beede2c6df549105147ec899822dc2067d54cb7dcfaf26a202990f71a4bae1` |
| `rastan_direct_video_test_build_0424_d.bin` | `eb4dd937780b625be27a3c569f0a9894afc7f127b9cec95f2667fed770001f40` |
| `rastan_direct_video_test_build_0424_do.bin` | `4a3da292c6399d717cc27561738927db2c3619d547b3a751d95a51eee44c7b89` |
| `rastan_direct_video_test_build_0424_s.bin` | `26574e4ec7eec7292883b06607191c7eb22bd2b8b68b1b9f18c7fd333e56a70a` |

Counter: 424. Tighe subsequently verified gameplay and visuals on real Genesis
with no new defect observed and accepted Build 0424 as the forward baseline.
