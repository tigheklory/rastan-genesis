# Cody — Build 0404 vs 0405 Objective Performance Check

Date: 2026-10-07  
Scope: measurement only; no production source change, optimization, ROM build, or counter advance.

## Verdict

Build 0405 is **not measurably slower** in this controlled Round-1 comparison. It completes
9.86% more gameplay workers in the same 1,200 rendered-frame interval, uses 8.89% fewer total
IRQ cycles per completed gameplay update, and uses 12.43% fewer measured native-graphics cycles
per update. Its worst complete IRQ is 3.77% shorter.

The first material difference is the intended one: Lizardman, Large Bat, and Small Bat traffic
moves from the retained fallback interpreter to the generated native path. No subsystem shows a
consistent additional runtime cost attributable to Build 0405.

## Apples-to-apples procedure

- Platform: **GENESIS NTSC**, `/usr/games/mame genesis`, MAME `0.276`.
- ROMs: canonical Build 0404 and canonical Build 0405, each cold-booted independently.
- Identical host input schedule: coin at host frames 120–132; Start at 175–187; walk right from
  frame 360; periodic jump (12/90 frames) and attack (6/30 frames). After the measurement marker,
  scrolling/combat continues for 360 rendered frames and then the player remains in the stress
  area. Energy is held at `A5+0x013A = 0x0030` by the host in both runs to prevent death from
  changing the route. This changes test state equally; it does not add emulated 68000 cycles.
- Common measurement boundary: first gameplay frame with `A5+0x013E == 2`.
- Fixed interval: 1,200 rendered frames from that boundary.
- Build 0404 reached the boundary at host frame 1144; Build 0405 at 1140. That four-frame
  difference is itself consistent with Build 0405's higher pre-boundary throughput. Both runs
  begin measurement at the same retained map-record condition rather than an arbitrary wall-clock
  point.
- Exact debugger-cycle boundaries reused from the repaired Phase-C harness:
  publication `0x070250..0x0702D2`; worker `0x03A208..0x03A27E`.
- Added read-only debugger brackets around the existing runtime code: graphics hooks
  `0x0730E8..0x07310C` / `0x073120..0x073134`, player compositor entry/returns
  `0x073172 -> 0x073242/0x07324A`, generic result `0x07358E`, and build-specific residency-miss
  PCs (`0404: 0x074366`, `0405: 0x0743EC`). No ROM instrumentation was added.

The route exercised all requested families. Runtime tuple totals were:

| Family | Semantic discriminator | Build 0404 | Build 0405 |
|---|---|---:|---:|
| Lizardman | base `0x004B` | 2,066 fallback | 1,932 native hits |
| Large Bat | base `0x03F6`, raw `actor+0x06=0x0A` | 792 fallback | 870 native hits |
| Small Bat | base `0x0268`, raw `actor+0x06=0x0B` | 792 fallback | 870 native hits |

Counts differ because Build 0405 completes more gameplay updates within the fixed display-frame
window; the table is coverage proof, not a direct count comparison.

## Timing results

One NTSC display frame is 128,009 68000 cycles. “Per update” below means one complete serviced
arcade worker. “Per rendered frame” divides completed measured work by the fixed 1,200 display
frames. The latter is almost saturated in both builds, so throughput is the decisive companion
metric.

| Metric | Build 0404 | Build 0405 | 0405 difference |
|---|---:|---:|---:|
| Complete workers / rendered frame | 0.6592 | 0.7242 | **+9.86%** |
| Average worker cycles / update | 186,686.42 | 170,014.79 | **-8.93%** |
| Average IRQ-total cycles / update | 192,783.39 | 175,639.68 | **-8.89%** |
| IRQ work cycles / rendered frame | 127,076.38 | 127,192.40 | +0.09% |
| P95 IRQ-total cycles / update | 289,049 | 280,347 | **-3.01%** |
| Worst IRQ-total cycles / update | 436,389 | 419,945 | **-3.77%** |
| Average publication cycles / update | 5,936.97 | 5,464.89 | **-7.95%** |
| Worst publication cycles | 31,087 | 31,091 | +0.01% |

The +0.09% IRQ-work total per rendered frame is not a slowdown: Build 0405 fits 78 additional
complete workers into the same display interval. Normalized per completed update, both worker and
whole-IRQ cost fall by about 8.9%.

### Deadline/overrun indicators

| Indicator | Build 0404 | Build 0405 | Difference |
|---|---:|---:|---:|
| Worker updates over one-frame budget | 96.71% | 89.99% | **-6.72 percentage points** |
| IRQ totals over one-frame budget | 99.37% | 94.25% | **-5.12 percentage points** |
| Display frames without a completed worker | 409 | 331 | **-19.07%** |
| Maximum worker frame-wrap count | 3 | 3 | unchanged |

The last row/count is consistent with the established one-pending IRQ/VBlank coalescing model; it
is not a direct VINT-assertion tap. It is still an objective completed-deadline/throughput measure.

## Graphics, native/fallback, residency, and DMA

| Metric (per complete update unless stated) | Build 0404 | Build 0405 | 0405 difference |
|---|---:|---:|---:|
| Native graphics cycles, average | 122,271.55 | 107,079.64 | **-12.43%** |
| Native graphics cycles, worst | 220,554 | 225,140 | +2.08% |
| Player compositor cycles, average | 3,903.36 | 3,912.29 | +0.23% |
| Player compositor cycles, worst | 3,944 | 3,944 | unchanged |
| Generic hit rate | 3.37% | 77.06% | **+73.69 points** |
| Generic fallbacks / update | 6.751 | 1.323 | **-80.40%** |
| Residency misses / update | 2.885 | 2.346 | **-18.67%** |
| Pattern installs / update | 2.694 | 2.146 | **-20.34%** |
| Evictions / update | 2.685 | 2.137 | **-20.42%** |
| Pattern-DMA words / update | 172.42 | 137.35 | **-20.34%** |
| All DMA words / update | 544.20 | 506.84 | **-6.87%** |
| All DMA words / rendered frame | 358.72 | 367.04 | +2.32% |
| Worst all-DMA words / update | 3,136 | 3,136 | unchanged |
| SAT DMA words / update | 320 | 320 | unchanged |

The 2.32% rise in DMA words per rendered frame is caused by the 9.86% increase in completed
updates. Per completed update, DMA work is 6.87% lower; pattern work specifically is 20.34% lower.

To control for the different emitted-sprite distribution, exact emitted-count strata common to
both runs were weighted by the smaller sample count at each count (540 matched samples). Build
0405 remained faster: worker cycles **-4.06%**, IRQ-total cycles **-4.19%**, native-graphics
cycles **-3.17%**, DMA words **-6.64%**, and residency misses **-13.41%**. Thus the result is not
only a consequence of Build 0405's lower whole-run mean emitted count.

## Attribution

The changed subsystem is cheaper, not more expensive:

1. Build 0404 performs an eight-record generic scan and then the complete fallback interpreter
   for the three enemy families.
2. Build 0405 uses bounded direct classification and emits those proven families natively.
3. Generic fallbacks fall 80.40% per update and measured native-graphics cost falls 12.43% per
   update (3.17% under equal emitted-count weighting).
4. Publication, residency, and DMA cost per update also fall. The unchanged player compositor's
   +0.23% average variation has an identical maximum and is not a material regression.

Therefore there is no measured Build-0405 slowdown and no “first additional-cost subsystem” to
fix. Tighe's subjective observation is not reproduced by this controlled workload.

## Evidence and tool accounting

- Build 0404 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0404.bin`, SHA-256
  `5f6585292a60ef3ded5c6a34337eec9137eaa3cae36b9d4dda0fd20d786a3d49`, 1,793,720 bytes.
- Build 0405 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0405.bin`, SHA-256
  `af0024630475af16c8e784b88050dcf633180db450c57f8da6f44f8e4549e055`, 1,801,912 bytes.
- Build 0404 trace: `states/traces/build0404_vs_0405_objective_performance/build0404/`.
- Build 0405 trace: `states/traces/build0404_vs_0405_objective_performance/build0405/`.

Existing project tools reused: repaired `frame_timing_trace.lua`,
`run_frame_timing_trace_wsl.sh`, established debugger-cycle boundaries, real-time VC publication
bracket, VDP write tap, standard Genesis input field names, and GENESIS NTSC MAME.

New tooling created: none. The durable frame-timing harness was extended with an optional
deterministic route, existing-code timing brackets, generic result counters, residency-worklist
accounting, and DMA-length accounting.

Why the extension was necessary: the prior harness measured worker/publication timing but did not
measure native hits versus fallback, residency misses/installs/evictions, or DMA words, all of
which this task explicitly requires.

No build was produced. Counter remains 405.
