# Build 0400 → 0404 → 0405 direct graphics-cost progression

Date: 2026-10-07  
Scope: read-only measurement. No production source change, ROM build, optimization, scheduling change, or counter advance.

## Purpose and result

This measurement directly brackets the CPU regions that turn retained arcade draw semantics into
Genesis sprite output. It replaces neither the ROM nor gameplay code and does **not** reuse the
historical `worker ≈ 55,600 + 2,609 × emitted sprites` regression as a graphics measurement.
That regression includes all work correlated with sprite load. The direct result is:

- Build 0400: **124,944.25 graphics cycles/complete update**.
- Build 0404: **125,855.55 graphics cycles/complete update**.
- Build 0405: **110,663.64 graphics cycles/complete update**.
- Whole-run Build 0400→0405 graphics average: **-11.43%**; worker average: **-8.72%**;
  completed workers/rendered frame: **+9.58%**.
- Exact emitted-count weighting does not reproduce a 0400→0405 saving: graphics is **+2.26%**,
  worker **+0.75%**, and IRQ **+0.65%**. The whole-run reduction therefore cannot be attributed
  solely to cheaper work at the same emitted count; actor/workload mix still differs inside an
  emitted-count stratum.
- The bounded Build 0404→0405 conversion is independently favorable under equal emitted load:
  graphics **-3.08%**, worker **-4.06%**, and IRQ **-4.19%**.

## Semantic timing boundaries

The measured exclusive union starts after retained gameplay has selected what is to be drawn and
includes mapping interpretation, piece processing, native queue/SAT staging, pattern-residency
handling, and finalization. It excludes AI, collision, movement, actor lifecycle, game-state work,
and Plane A/B work.

| Region | Build 0400 | Builds 0404/0405 | Included semantic work |
|---|---|---|---|
| Generic pass 1 | `0x0730E8→0x07310C` | same | stage dispatch, actor mapping interpretation, residency/enqueue, finalizer |
| Generic pass 2 | `0x073120→0x073134` | same | optional second stage dispatch and finalizer |
| Primary player | `0x05458C→0x05467C/0x054748` | `0x073172→0x073242/0x07324A` | Build-0400 retained primary mapping/piece compositor versus generated whole-frame producer |
| Secondary player | `0x05479A→0x054844` | `0x0547A6→0x054850` | retained secondary/legs mapping and per-piece native enqueue |

Build 0400 ROM disassembly proves that `0x05458C` enters the primary retained compositor, whose
piece loops call `native_player_piece` at `0x073172`, and that `0x05479A` is the secondary
compositor. In 0404/0405 the replacement at the same original primary semantic boundary calls the
generated player-frame producer; its insertion shifts the unchanged secondary compositor by
12 bytes. The generic outer hooks are unchanged. These are the same producer responsibilities,
not copied addresses chosen by proximity, so the comparison classification is **YES — semantically
comparable**.

The earlier 0404/0405 evidence omitted the retained secondary-player interval. Because adding it
changes the graphics subtotal, all three builds were rerun with the final identical union. Nested
regions are not double-counted.

## Deterministic method

- Emulator: GENESIS NTSC, MAME 0.276, debugger `totalcycles()` breakpoints; ROMs are unmodified.
- Cold boot for every build.
- Input schedule: coin host frames 120–132; Start 175–187; Right from 360; jump 12/90 frames;
  attack 6/30 frames.
- Equal host-held energy: `A5+0x013A = 0x0030` during gameplay.
- Common start: first gameplay frame with `A5+0x013E == 2`.
- Fixed duration: 1,200 rendered gameplay frames.
- Common worker: `0x03A208→0x03A27E`; publication: `0x070250→0x0702D2`.
- Exact emitted count is read at worker completion and belongs to that same update.
- All three VDP ownership gates passed; all captures had zero rejected sequences. The one open
  worker at the fixed ending edge is excluded in every build.

Build 0400 armed at host frame 1134 and produced 793 complete workers; Build 0404 armed at 1144
and produced 791; Build 0405 armed at 1140 and produced 869.

Evidence:

- `states/traces/build0400_0404_0405_graphics_cost_progression/final/build0400/`
- `states/traces/build0400_0404_0405_graphics_cost_progression/final/build0404/`
- `states/traces/build0400_0404_0405_graphics_cost_progression/final/build0405/`

ROM identities:

- 0400: `36e0806fb288d38d3b092fb01b2c8a01fe69de1934b206c2a47677b561c02fe5`
- 0404: `5f6585292a60ef3ded5c6a34337eec9137eaa3cae36b9d4dda0fd20d786a3d49`
- 0405: `af0024630475af16c8e784b88050dcf633180db450c57f8da6f44f8e4549e055`

## Complete three-build results

One NTSC frame is 128,009 68000 cycles. Percentages in the last three columns are relative changes;
the raw over-budget rows should also be read as percentage-point rates.

| Metric | 0400 | 0404 | 0405 | 0400→0404 | 0404→0405 | 0400→0405 |
|---|---:|---:|---:|---:|---:|---:|
| Workers/rendered frame | 0.6608 | 0.6592 | 0.7242 | -0.25% | +9.86% | +9.58% |
| Worker avg/update | 186,259.02 | 186,686.42 | 170,014.79 | +0.23% | -8.93% | -8.72% |
| Worker median | 184,422 | 188,958 | 160,118 | +2.46% | -15.26% | -13.18% |
| Worker p95 | 291,364 | 278,056 | 272,706 | -4.57% | -1.92% | -6.40% |
| Worker worst | 431,580 | 423,588 | 407,144 | -1.85% | -3.88% | -5.66% |
| IRQ avg/update | 192,420.73 | 192,783.39 | 175,639.68 | +0.19% | -8.89% | -8.72% |
| IRQ median | 189,271 | 194,083 | 166,167 | +2.54% | -14.38% | -12.21% |
| IRQ p95 | 297,711 | 289,049 | 280,347 | -2.91% | -3.01% | -5.83% |
| IRQ worst | 444,371 | 436,389 | 419,945 | -1.80% | -3.77% | -5.50% |
| Graphics avg/update | 124,944.25 | 125,855.55 | 110,663.64 | +0.73% | -12.07% | -11.43% |
| Graphics median | 125,530 | 132,842 | 106,816 | +5.82% | -19.59% | -14.91% |
| Graphics p95 | 179,756 | 182,308 | 157,018 | +1.42% | -13.87% | -12.65% |
| Graphics worst | 239,646 | 224,138 | 228,724 | -6.47% | +2.05% | -4.56% |
| Graphics/rendered frame | 82,567.33 | 82,959.78 | 80,138.92 | +0.48% | -3.40% | -2.94% |
| Graphics % of worker | 67.08% | 67.42% | 65.09% | +0.34 pp | -2.32 pp | -1.99 pp |
| Publication avg/update | 6,001.71 | 5,936.97 | 5,464.89 | -1.08% | -7.95% | -8.94% |
| Publication median | 3,831 | 3,831 | 3,033 | 0.00% | -20.83% | -20.83% |
| Publication p95 | 13,565 | 12,677 | 12,647 | -6.55% | -0.24% | -6.77% |
| Publication worst | 31,177 | 31,087 | 31,091 | -0.29% | +0.01% | -0.28% |
| Worker updates >128,009 | 92.31% | 96.71% | 89.99% | +4.41 pp | -6.72 pp | -2.32 pp |
| IRQ updates >128,009 | 94.20% | 99.37% | 94.25% | +5.17 pp | -5.12 pp | +0.05 pp |
| Frames without worker | 407 | 409 | 331 | +0.49% | -19.07% | -18.67% |

## Equal-emitted-load control

For each pair, exact emitted-count strata common to both captures are weighted by the smaller
sample population in each stratum. This is the established 0404/0405 method. It controls emitted
count, but not which actor families comprise that count.

| Pair | Matched weight | Common counts | Worker | IRQ | Graphics |
|---|---:|---:|---:|---:|---:|
| 0400→0404 | 494 | 22–61 (39 strata) | +2.96% | +2.95% | +4.39% |
| 0404→0405 | 540 | 23–55 (32 strata) | **-4.06%** | **-4.19%** | **-3.08%** |
| 0400→0405 | 484 | 23–55 (31 strata) | +0.75% | +0.65% | +2.26% |

The 0400→0405 whole-run mean is lower because the completed-update population and actor mix differ.
It is valid as observed route throughput, but not proof that an equal-emitted Build-0405 update is
cheaper than Build 0400. Conversely, the 0404→0405 result remains cheaper both whole-run and under
the specified control, directly supporting the direct-dispatch/enemy-conversion improvement.

## Budget and next measured target

Build 0405 still averages **175,639.68 IRQ cycles/update**, or **47,630.68 cycles** above the
128,009-cycle frame budget. Build 0400's average excess was 64,411.73 cycles, so the observed route
has removed 16,781.05 cycles, **26.05% of the original average excess**, while still missing the
deadline on 94.25% of completed IRQ updates.

Build 0405 measured cost centers are:

1. Generic graphics dispatch/interpreter/residency/finalizer subtotal: **103,167.34 cycles/update**
   (total graphics minus the separately bracketed player compositor; 60.68% of worker cost).
2. Non-graphics worker remainder: **59,351.15 cycles/update** (34.91% of worker cost).
3. Primary + secondary player compositor: **7,496.29 cycles/update** (4.41% of worker cost).

Publication averages another 5,464.89 cycles outside the worker. Graphics therefore remains the
dominant measured CPU cost. The largest measured next optimization target is the generic graphics
producer subtotal. This trace does not isolate enough subregions to choose between its remaining
fallback interpretation, residency, and finalizer costs; selecting one of those without further
bounded evidence would overstate the measurement.

No optimization was performed. Build-0401 ownership, IRQ6 scheduling, residency architecture, and
the Build 0405 production ROM were not changed. Counter remains 405.
