# Build 0412 Hardware-Grounded Native Performance

**Input baseline:** Build 0411  
**Result:** complete-IRQ average is below the NTSC frame budget; Tighe hardware acceptance remains required.

## Hardware evidence

Tighe's Build 0411 result was **MUCH BETTER, NOT PERFECT**. The source recording is
`states/screenshots/build 411/WIN_20261010_14_48_43_Pro.mp4`: H.264 Main, progressive YUV 4:2:0,
1920x1080, 198.046367 seconds, 5,942 encoded frames, 17.64 Mbit/s, with an average encoded rate of
approximately 29.9997 fps and a 1/30000 stream time base. Windows Recorder sampled the approximately
59.94 Hz Genesis output at 30 fps, so it cannot prove exact workers/rendered-frame or individual
Genesis frame repeats.

Qualitative samples only:

- 18-22 s: initial outdoor Lizardman combat; relatively fluid under light to moderate load.
- 64-68 s: rope/platform traversal with substantial scrolling; continuous motion is visible.
- 106-110 s: several Lizardmen, a winged enemy, and effects; visibly heavier pacing.
- 134-138 s: cave combat with a blue armored humanoid, Lizardman, and impact; the slowest sample.
- 184-188 s: phase-2 fortress scrolling; smoother than the dense combat intervals.

The recording does not identify a Four-Armed enemy with sufficient certainty; its composite-body
check remains `USER TEST REQUIRED`. Exact duplicate-frame analysis is unreliable because of 30 fps
sampling and analog capture noise.

## Build 0411 baseline

On the established 1,200-rendered-frame GENESIS NTSC route, Build 0411 measured 0.9033
workers/rendered frame, 126,786.39 worker cycles/update, 131,589.13 IRQ cycles/update, 56,833.13
graphics cycles/update, and 38,572.31 finalizer cycles per completed update. IRQ average exceeded the
128,009-cycle budget by 3,580.13; 34.1% of complete IRQs exceeded budget and 116 rendered frames had
no completed worker.

## Target 1: identity and HUD queue setup

Zero-byte profiler labels were added around existing finalizer stages. The instrumented ROM was
SHA-identical to canonical Build 0411. The final Build 0411 implementation measured 4,927.02
pre-geometry cycles/rendered frame:

| Path | Entries/frame | Cycles/entry | Cycles/frame |
|---|---:|---:|---:|
| direct/prefinalized | 15.406 | 146.00 | 2,249.25 |
| dynamic Level-A | 8.858 | 302.32 | 2,677.76 |

Exclusive dynamic identity validation was largest at 1,489.99 cycles/frame (168.22/entry). The
fixed P1 HUD projection accounted for nine dynamic entries per completed finalizer even though its
finite glyph set (`0x02A..0x039`, `0x046`, `0x048`) is statically nonblank and has no palette variant.

The HUD producer now transports the existing direct-identity marker. It selects the HUD lane once
and uses the verified fast queue emitter for all pieces. Fixed setup falls from 5,953.90 to 3,633.00
cycles/completed finalizer. Direct/dynamic coordinates, global flip, palette selection, clipping for
non-HUD pieces, residency, DMA, and SAT output remain runtime-owned.

Operation classification:

- build-time invariant: HUD source identity, nonblank status, and absence of a palette variant;
- frame invariant: HUD lane queue base/end/count context;
- actor/frame invariant: generated-frame lane context already handled by the existing fast producer;
- piece-dynamic: current score digit and leading-zero visibility;
- residency-dynamic: resident slot, install/eviction, DMA worklist, and final SAT tile number.

## Target 2: fixed-screen HUD bounds

Target 1's whole-route IRQ average remained above budget under a heavier route, so the next ranked
region was split once. Direct bounds cost 3,143.39 accepted plus 1,056.80 rejected cycles/frame;
dynamic bounds cost only 217.87 accepted plus 46.49 rejected. Direct key normalization cost another
1,219.83 cycles/frame.

The removable portion was the fixed HUD layout. Leading zeroes had been queued at an intentionally
off-screen Y and rejected later; they are now omitted at the semantic producer. Visible HUD glyphs
carry a fixed-screen-bounds marker, so only those known coordinates skip opaque-bounds pointer and
viewport work. Actor, enemy, player, effect, and dynamic Level-A records retain the clipping path.

Across both targets, the shared finalizer falls from 38,572.31 to 32,408.16 cycles per completed
update, recovering 6,164.15 cycles (15.98%). Final pre-geometry is 3,342.83 cycles/rendered frame on
its captured route, and fixed setup is 2,577.00 cycles/completed finalizer.

## Final performance

The final route completed the same 1,084 workers as Build 0411 while processing a heavier average
displayed load (24.77 versus 20.58 emitted sprites/update).

| Metric | Build 0411 | Build 0412 | Delta |
|---|---:|---:|---:|
| workers/rendered frame | 0.9033 | 0.9033 | unchanged |
| worker average | 126,786.39 | 120,467.68 | -4.98% |
| worker median | 120,618 | 106,696 | -11.54% |
| worker p95 | 228,162 | 223,752 | -1.93% |
| worker worst | 313,722 | 319,882 | +1.96% |
| IRQ average | 131,589.13 | 125,442.49 | -4.67% |
| IRQ median | 124,177 | 110,619 | -10.92% |
| IRQ p95 | 233,753 | 232,627 | -0.48% |
| IRQ worst | 339,963 | 336,065 | -1.15% |
| graphics average | 56,833.13 | 57,368.46 | +0.94% (heavier load) |
| finalizer/completed update | 38,572.31 | 32,408.16 | -15.98% |
| IRQ over 128,009 | 34.1% | 29.0% | -5.1 points |
| frames without worker | 116 | 116 | unchanged |

Worker average is 7,541.32 cycles below budget. IRQ average first crosses below budget here, with a
2,566.51-cycle margin. The tail remains the largest visible issue: 29.0% of completed IRQs exceed one
frame and worker/rendered remains 0.9033.

## Correctness and gates

- frame generator/verifier: PASS (1,200 player, 416 secondary, 38 generic, 1,898 universal-general,
  24 specialized; zero player UNRESOLVED);
- direct dispatch, variable-count reconciliation, fast enqueue, and exact queue ends: PASS;
- canonical ROM gate and gameplay-entry gate: PASS;
- gameplay-entry address/bus/illegal/crash counts: `0/0/0/0`;
- VDP ownership on the performance route: PASS;
- modified code disassembles as base-MC68000 instructions: PASS;
- known phase-1 epoch gate remains a labeled FAIL warning; the independent transition-retention gate
  passes and no PC080SN source was changed.

The numbered `_c` closeout recorded player fallback, generic fallback, adapter, and crash as
`0/0/0/0`, but MODE automation reached only four established subrounds before `MAX_FRAMES`; the same
invocation completes all 18 on Build 0411. Full-game Build 0412 coverage is therefore not claimed by
this run and Tighe's hardware gameplay validation is required. No canonical-ROM exception or
fallback was observed.

## Artifacts

All Build 0412 artifacts are 1,998,520 bytes.

| Variant | SHA-256 |
|---|---|
| canonical | `235b617b7ed923435b42f22016e4669de58dd32a5afc06f6f456bebeb198237c` |
| `_c` | `f581dad0c013d271630ffe670611a8c8411dd2c2696864d712eb4d3554f261e8` |
| `_d` | `7c3a87211458001e79aa0e8cb1f646a20fd771da9fde49637482bbd9369a3e55` |
| `_do` | `85c4e323e81dd332eaba63e8311c5f07d7067750b67dda36bb1ff66ad73d0176` |
| `_s` | `f1cc55b7ea0ff45c325135004176578f8706509aa06076fd04cde71c0a59d762` |

Evidence is under `states/traces/build0412_pregeometry_baseline_0411/`,
`states/traces/build0412_bounds_breakdown/`, `states/traces/build0412_final_cost/`, and
`states/traces/build0412_final_candidate_timing/`.

Phase D, Phase E, Build 0401, PC080SN, and H25 were not touched. Tighe hardware visual, gameplay,
and subjective performance acceptance is required.
