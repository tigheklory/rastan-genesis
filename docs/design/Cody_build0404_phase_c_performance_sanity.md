# Cody — Build 0404 Phase-C Performance Sanity Check

## Decision

**REGRESSION.** Build 0404 is the accepted Phase-B gameplay baseline, but its
whole-worker producer is measurably slower than Build 0400 at comparable
emitted-sprite loads. Phase D must not begin until the generic native-miss path
is corrected so that unresolved actors do not repeatedly pay an eight-record
linear native lookup before running the complete retained interpreter.

This task changed no production game source, built no ROM, and did not touch
Build-0401 ownership or scheduling.

## Measurement method and compatibility

The accepted canonical Build 0404 ROM was measured unchanged:

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0404.bin`
- SHA-256: `5f6585292a60ef3ded5c6a34337eec9137eaa3cae36b9d4dda0fd20d786a3d49`
- machine: Genesis NTSC MAME
- debugger cycle source and event pairing: unchanged Build-0400 exact method
- publication boundaries: `0x070250` entry, `0x0702D2` RTS
- worker boundaries: `0x03A208` entry, `0x03A27E` pre-RTE
- emitted count: the same `w@FFBED4` value captured at the worker-end event
- interval: first `M` press during Scene-1 gameplay

Only the external trace scripts were generalized to accept a build label,
output directory, and resolved timing PCs. The smoke run confirmed all four
breakpoints installed and produced debugger-exact output. No emulated
instruction or production counter was added.

Evidence:

- Build 0400: `build/mame/home/frame_timing/`
- Build 0404: `states/traces/build0404_phase_c_heavy/`

The method is compatible. The gameplay workload is not identical: Build 0400
contains 60–79 emitted-sprite samples while Build 0404 stops at 50–59.
Therefore overall medians and tick/display ratios describe each complete human
run but are not a like-for-like speed gate. The shared emitted-count buckets
are the direct comparison.

## Samples and whole-run results

| Metric | Build 0400 | Build 0404 | Delta | Delta % |
|---|---:|---:|---:|---:|
| Armed display frames | 5,721 | 4,777 | -944 | -16.50% |
| Complete worker pairs | 3,573 | 3,363 | -210 | -5.88% |
| Publication median | 3,831 | 3,033 | -798 | -20.83% |
| Publication p95 | 12,631 | 11,867 | -764 | -6.05% |
| Worker median | 208,746 | 171,256 | -37,490 | -17.96% |
| Worker p95 | 257,488 | 233,014 | -24,474 | -9.50% |
| IRQ-total median | 214,063 | 176,481 | -37,582 | -17.56% |
| IRQ-total p95 | 265,169 | 238,119 | -27,050 | -10.20% |
| Worker over 128,009 cycles | 85.1% | 89.6% | +4.5 points | +5.29% relative |
| IRQ total over 128,009 cycles | 86.5% | 91.5% | +5.0 points | +5.78% relative |
| Worker wraps median / p95 / max | 2 / 2 / 3 | 1 / 2 / 3 | -1 / 0 / 0 | — |
| Worker pairs / display frame | 0.6245 | 0.7040 | +0.0795 | +12.73% |

Build 0404 had 3,363 complete pairs, zero rejected sequences, one final open
worker at process exit, and a passing VDP-ownership gate. The apparently better
whole-run median and tick/display ratio are explained by the lighter load mix;
they do not override the shared-bucket result below.

## Like-for-like emitted-sprite buckets

All five shared buckets have at least 200 samples in each build. Their worker
medians are consistently higher in Build 0404.

| Emitted sprites | Samples 0400 / 0404 | Median 0400 | Median 0404 | Median delta | Median delta % | p95 0400 / 0404 |
|---|---:|---:|---:|---:|---:|---:|
| 10–19 | 261 / 215 | 95,606 | 96,656 | +1,050 | +1.10% | 237,710 / 242,418 |
| 20–29 | 441 / 337 | 117,378 | 126,450 | +9,072 | +7.73% | 269,050 / 261,368 |
| 30–39 | 217 / 1,061 | 146,242 | 156,818 | +10,576 | +7.23% | 290,182 / 201,638 |
| 40–49 | 267 / 1,409 | 177,340 | 184,886 | +7,546 | +4.26% | 215,968 / 225,582 |
| 50–59 | 749 / 341 | 201,044 | 218,592 | +17,548 | +8.73% | 235,336 / 246,060 |

The 30–39 p95 difference also shows that actor/scene composition within a broad
emitted-count bucket is not identical. It does not erase the consistent median
increase across every shared bucket. Pearson is not used as an acceptance gate.

Build 0404 has no 60–69 or 70–79 samples, so those Build-0400 buckets are not
compared.

## One bounded attribution: generic native miss then fallback

Build 0404 inserts `.Lnative_generic_frame_try` at the start of every active
generic actor handled by `.Lnative_emit_actor_common` in
`apps/rastan-direct/src/pc090oj_hooks.s`. A miss then falls through to the
complete accepted Build-0403 descriptor/interpreter path.

The final Build-0404 object disassembly proves the sequence:

1. worker calls the generic actor helper at object offset `0x490`;
2. that helper calls the Phase-B native lookup at object offset `0x630`;
3. the lookup evaluates the orientation predicate and linearly scans exactly
   eight 12-byte semantic records;
4. on no match it returns zero;
5. the caller resumes the complete retained interpreter at object offset
   `0x4B0`.

For an ordinary unresolved actor with no attribute-bit-6 override and with a
base tile unequal to all eight records, standard MC68000 instruction timings
give **832–856 extra cycles per active actor**. The range is the retained
three-field orientation-predicate branch variation. It includes the lookup
call/return, ten-register save/restore, orientation predicate, eight
base-identity comparisons, eight table advances/DBRA iterations, and the
caller miss test. It excludes the unchanged fallback interpreter. A partial
key match that fails at a later field costs more.

The generic worker visits at most 17 active slots (six enemy, six effect, five
middle). Thus the common base-miss gate alone can add approximately
**14,144–14,552 cycles per worker** when all 17 are active, about 11% of one
128,009-cycle frame budget. That scale is consistent with the observed central
bucket median increases of 7,546–10,576 cycles and demonstrates a material
contribution. It does not assert that the gate is the sole source of every
cycle difference in two non-identical human routes.

No new runtime counters were added. Generic native hits, generic fallback
attempts, and player-native hits were therefore not separately counted.

## Known visual defects retained

- **New in accepted Build 0404:** the first displayed demon-burst frame uses
  the demon palette instead of the intended red burst palette. Cause remains
  **UNKNOWN**; ordering is only a hypothesis. This task did not fix it.
- **Pre-existing:** Rastan has a one-frame tile glitch at one Segment-1
  location. It predates Build 0404 and is not attributed to Phase B.

## Recommendation

Before Phase D, make one small corrective implementation: replace the repeated
eight-record generic eligibility scan with a bounded direct dispatch/rejection
that cheaply rejects unresolved families and preserves the exact generated-key
validation for the eight accepted cave/burst tuples. Do not remove fallback or
broaden native coverage as part of that correction. Re-measure with the same
exact boundaries afterward.

Phase D ownership, Build 0401, IRQ6, and scheduling remain untouched.
