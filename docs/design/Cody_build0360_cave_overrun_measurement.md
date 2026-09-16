# Cody - Build 0360 Cave Overrun Measurement

## Scope

This is a measurement-only continuation from accepted Build 0359. It does not
change or optimize production code, produce a ROM, or consume Build 0360.

- measured ROM: `dist/rastan-direct/rastan_direct_video_test_build_0359.bin`
- SHA-256: `ca3844e6e3d0e175c0c0b5d14dd55bb4c8161d4619f14214e29d2a3d82b819cd`
- ROM size: 1,715,896 bytes
- build counter before and after this audit: 359
- next valid ROM number: 0360

The operator completed the required first-cave Segment 1 no-kill stress
workload. The capture includes large bats, small bats, Lizardmen, a sustained
wait for hurry-up bats, and the hurry-up swarm before exit. This is stronger
coverage than the shallow automated sequence used by earlier global timing
reports.

No change was made to the SAT tail, Plane A capacity, Palette Composer, DPLC
work, sprite recomposition, `D00462`, VBlank/frame architecture, gameplay, or
collision semantics.

## Evidence and method

### Read-only capture

`tools/mame/scripts/build0360_cave_overrun_measurement.lua` attaches debugger
breakpoints to the preserved Build 0359 finalizer. The breakpoints only print
state and immediately continue. They do not write emulated memory, inject
input, or alter the ROM.

The relevant Build 0359 runtime PCs are:

| Event | `runtime_genesis_pc` |
|---|---:|
| back/enemy lane start | `0x073AC8` |
| back/enemy lane end | `0x073AD8` |
| cached emit-entry start | `0x073BE0` |
| bbox/viewport block | `0x073C6A` |
| reverse-index lookup | `0x073CC4` |
| reverse-index miss | `0x073D06` |
| victim-loop iteration | `0x073D0E` |
| no-free drop | `0x073D1A` |
| queue-full drop | `0x073D54` |
| SAT hit/emission path | `0x073E58` |
| emit-entry return | `0x073F00` |
| finalizer return | `0x073F36` |

The raw capture contains 984,474 ordered events. The reducer reconstructed
3,116 complete finalizers, of which 3,114 were gameplay publications.

### Cave interval correction

The first reducer draft inherited a narrow entrance-coordinate filter and
retained only seven frames. That was not the completed stress workload. The
captured arcade-owned map-record field `A5+0x013E` advances from 1 to 2 at
external frame 1301. Record 2 then remains active through the operator-confirmed
no-kill cave wait and hurry-up swarm until MAME exits at external frame 5303.

The preserved `logger_metadata.txt` intentionally still records that original
pre-capture entrance filter. It describes the initial hypothesis, not the final
selection. `cave_overrun_summary.json` and `cave_frames.csv` are the corrected
reduction products and are authoritative for the measurements below.

The authoritative cave interval is therefore:

- arcade state: `A5+0 = 2`, `A5+2 = 3`
- arcade map record: `A5+0x013E = 2`
- external frames: 1301 through 5303
- complete gameplay publications: 2,539

“Segment 1” is the name of the requested route/workload; it is not an assertion
that `A5+0x013E` must numerically equal 1 throughout the cave.

### Physical beam timing

Timing uses the already established Genesis NTSC physical beam model:

```text
physical phase line = (beam_y - 224) mod 262
monotonic stamp = external_frame * (262 * 488)
                + physical_phase_line * 488
                + beam_x
```

Durations are divided by 488 dots per physical scanline. This does not use the
old 8-bit V-counter reconstruction.

The reducer counts every victim-loop breakpoint encounter. It also measures
the exact span between consecutive victim-loop encounters. The latter is a
strict lower bound on total victim-search time because a miss with `N`
iterations has only `N-1` loop-to-loop intervals, and work before the first and
after the last iteration is excluded.

Successful replacements are classified as reverse-index misses that later
reach the SAT hit path. Queue-full and no-free exits are classified separately.
All call-outcome accounting closes exactly.

## Aggregate cave measurements

| Measurement | All lanes | Back/enemy lane |
|---|---:|---:|
| emit-entry calls | 153,765 | 83,836 |
| SAT entries emitted | 135,659 | 81,661 |
| viewport/bbox rejects | 17,803 | 1,881 |
| other early rejects | 0 | 0 |
| reverse-index residency misses | 7,612 | 3,345 |
| victim-loop iterations | 112,763 | 75,698 |
| observed loop-to-loop transitions | 105,151 | 72,353 |
| successful replacements | 7,309 | 3,051 |
| no-free drops | 6 | 6 |
| queue-full drops | 297 | 288 |

Misses are a path classification, not an additional call outcome: most misses
ultimately emit after replacement. The complete outcome equation is:

```text
153,765 calls
= 135,659 emitted
 + 17,803 viewport rejects
 + 6 no-free drops
 + 297 queue-full drops
```

The same equation closes with zero delta for the back/enemy lane. There were
18,106 non-emitting calls overall. Thus calls do exceed emissions, but the
back/enemy excess is not primarily caused by clipping: 81,661 of 83,836 back
calls emitted, while only 1,881 were viewport rejects.

## Timing breakdown

The timing categories below are nested and must not be summed indiscriminately.
For example, a miss-to-hit call includes victim work and the common SAT hit
tail; `residency work` is the narrower miss-to-hit/drop bracket inside it.

| Captured work over 2,539 publications | All lanes | Back/enemy lane |
|---|---:|---:|
| complete finalizer time | 414,198.408 lines | n/a |
| complete back/enemy lane time | n/a | 239,529.982 lines |
| resident-hit calls | 298,678.611 lines | 183,893.910 lines |
| miss-to-hit calls | 59,309.426 lines | 31,813.154 lines |
| miss-drop calls | 2,952.557 lines | 2,894.668 lines |
| viewport rejects | 15,247.074 lines | 1,948.980 lines |
| miss residency-work bracket | 44,752.805 lines | 27,150.816 lines |
| observed victim loop-to-loop span | 31,421.191 lines | 21,620.832 lines |

The measured normal resident-hit cost is 2.327 lines per call overall and
2.339 lines per back/enemy call, consistent with the prior approximately
2.336-line focused measurement. A viewport rejection costs 0.856 line overall
and 1.036 lines in the back lane.

In the back/enemy lane, measured residency work consumed 27,150.816 lines,
13.93 times the 1,948.980 lines spent in viewport rejects. Even the deliberately
conservative loop-to-loop lower bound consumed 21,620.832 lines.

### Per-publication distributions

| Measurement | Median | P95 | Maximum |
|---|---:|---:|---:|
| complete finalizer | 162.514 | 233.340 | 349.449 lines |
| back/enemy lane | 92.436 | 150.154 | 286.057 lines |
| back resident hits | 79.293 | 102.691 | 107.787 lines |
| back miss-to-hit calls | 0.000 | 62.344 | 187.766 lines |
| back viewport rejects | 0.000 | 7.275 | 20.588 lines |
| back residency work | 0.000 | 54.195 | 174.086 lines |
| back loop-to-loop lower bound | 0.000 | 43.617 | 152.377 lines |

## Worst observed back/enemy publication

The worst back/enemy publication was finalizer 1846 at external frame 3123:

- complete back/enemy lane: 286.057 lines
- total/back calls: 72 / 44
- total/back emissions: 65 / 43
- total/back viewport rejects: 6 / 0
- total/back misses: 13 / 13
- total/back victim iterations: 523 / 523
- total/back successful replacements: 12 / 12
- total/back queue-full drops: 1 / 1
- back resident-hit calls: 72.551 lines
- back miss-to-hit calls: 187.766 lines
- back miss-drop call: 15.893 lines
- back residency-work bracket: 174.086 lines
- back observed loop-to-loop lower bound: 152.377 lines

The full miss-related call time is 203.659 lines, or 71.2% of the back/enemy
lane. The narrower residency-work bracket alone is 60.9% of the lane. The
observed victim-loop span, despite being a lower bound, is 53.3%. There were no
back-lane viewport rejects in this worst publication. This directly explains
why 41-65 emitted sprites can coexist with a 90-260-line back/enemy cost:
resident SAT emissions are not the whole workload; bursts of misses repeatedly
scan the 49-slot victim set before replacement or drop.

## Questions answered

### 1. Emit-entry calls versus SAT emissions

There were 153,765 calls and 135,659 SAT emissions. The back/enemy lane had
83,836 calls and 81,661 emissions. Outcome accounting has zero unexplained
calls.

### 2. Rejected/clipped calls

There were 17,803 viewport/bbox rejects overall but only 1,881 in the
back/enemy lane. No additional early-reject class was observed. Rejection is a
real aggregate cost, but it does not explain the bad back/enemy frames.

### 3. Residency misses

There were 7,612 misses overall and 3,345 in the back/enemy lane. Most misses
succeeded after replacement: 7,309 overall and 3,051 in the back lane.

### 4. Victim-loop expense in bad frames

The cave interval executed 112,763 victim iterations, including 75,698 in the
back/enemy lane. The measured back loop-to-loop lower bound totals 21,620.832
lines, reaches P95 43.617 lines per publication, and reaches 152.377 lines in
the worst publication. The complete back residency-work bracket reaches P95
54.195 and maximum 174.086 lines.

### 5. Primary source of excess back/enemy time

The primary source is the **residency miss/victim path**, not viewport rejection
and not the normal emitted-hit SAT tail. Miss bursts are uncommon relative to
all calls, but each miss can perform up to a 49-slot victim scan. Their
concentrated cost dominates the bad cave publications.

## Proven, inferred, and unsupported

### Proven

- The operator completed the requested high-live-enemy cave workload and also
  waited for a hurry-up swarm.
- Exact per-call outcome accounting closes with zero delta.
- The normal resident-hit cost remains approximately 2.33 lines.
- Back/enemy viewport rejection is small relative to residency work.
- The worst measured back/enemy publication has 13 misses, 523 victim-loop
  iterations, zero back viewport rejects, and 174.086 lines in the measured
  residency-work bracket.
- `RESIDENCY MISS PATH` is the measurement-supported next target.

### Inference

- Reducing or eliminating repeated victim scans should materially reduce the
  worst cave black-band extent. The exact visual gain requires a later
  implementation and the same user stress route.
- The observed loop-to-loop span is a conservative lower bound on removable
  search work, not a promise that every measured line can be eliminated.

### Unsupported by this task

- This audit does not prove a particular replacement algorithm or authorize
  one.
- It does not attribute all visual differences between Builds 0357 and 0359 to
  bbox optimization.
- It does not claim the residual overrun problem is solved.
- It does not characterize later rounds or a frame-identical arcade workload.

## Next implementation target

**RESIDENCY MISS PATH**

The measured target is the repeated `.Lnq_vloop` victim search on reverse-index
misses. A future implementation should be judged against the same first-cave
Segment 1 no-kill/high-live-enemy route, not global medians alone. The measured
payoff envelope is the back residency-work distribution (P95 54.195 lines,
maximum 174.086 lines), with an exact observed victim loop-to-loop lower bound
of P95 43.617 and maximum 152.377 lines. Replacement bookkeeping and the
mandatory SAT emission tail remain outside that lower-bound saving.

No optimization is implemented or recommended beyond identifying this measured
hotspot.

## Artifacts and validation

- capture/reducer tools:
  - `tools/mame/scripts/build0360_cave_overrun_measurement.lua`
  - `tools/mame/scripts/reduce_build0360_cave_overrun.py`
- authoritative capture:
  - `states/traces/build0360_cave_overrun_measurement_20260916_140256/build0359_cave_overrun_events.csv`
  - `states/traces/build0360_cave_overrun_measurement_20260916_140256/logger_metadata.txt`
  - `states/traces/build0360_cave_overrun_measurement_20260916_140256/cave_frames.csv`
  - `states/traces/build0360_cave_overrun_measurement_20260916_140256/cave_overrun_summary.json`
- initial unattended idle attempt preserved under:
  - `states/traces/build0360_cave_overrun_measurement_20260916_140256/idle_attempt/`
- reducer Python syntax: PASS
- reduced summary JSON parse: PASS
- call accounting: PASS, zero delta overall and in back/enemy lane
- production source changed: NO
- ROM produced: NO
- ROM/counter changed: NO; counter remains 359
