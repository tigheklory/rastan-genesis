# Build 0413 — Native Tail-Performance Optimization

**Date:** 2026-10-10  
**Input:** Build 0412  
**Result:** Build 0413; Tighe visual/gameplay/performance acceptance required

## Bounded tail diagnosis

The fixed 1,200-rendered-frame Build-0412 route completed 1,084 workers
(0.9033/rendered frame). Its worker average was 120,467.68 cycles and complete
IRQ average was 125,442.49, both below the 128,009-cycle NTSC budget, but IRQ
p95 was 232,627 and 29.0% of IRQs exceeded one frame.

The already-completed histogram proved that the worst tail is not principally
native sprite work:

| IRQ band | Frames | Graphics avg | Non-graphics avg |
|---|---:|---:|---:|
| `<=128,009` | 770 | 47,602.83 | 53,069.64 |
| `128,010–160,000` | 177 | 80,114.52 | 58,578.49 |
| `160,001–200,000` | 70 | 88,594.91 | 72,420.11 |
| `200,001–250,000` | 27 | 69,653.33 | 153,130.37 |
| `>250,000` | 40 | 81,766.75 | 199,090.55 |

The `0x4210E` gameplay split identified `0x51210` as the heavy call: about
17.6K cycles under budget versus 155.1K in the p95 class. Its dominant child is
the `0x055650` scroll-step path, specifically `0x0556CE -> 0x055948 ->
0x0559C8 -> 0x70418/0x70552`. The final two routines are Genesis-native
PC080SN strip/map work. That path is the dominant remaining absolute tail and
was explicitly outside this task. Build 0413 does not modify it.

## Lean-save production change

Andy independently audited the uncommitted change in
`Andy_build0412_tail_optimization_review.md`. Both stage dispatchers already
save and restore the complete external `D0-D7/A0-A6` contract. The common
generated-actor wrapper formerly repeated that full 15-register save, and the
generic and universal probes each repeated a 12-register save.

Build 0413 keeps the outer full save and changes only the private inner
contract:

- `.Lnative_emit_actor_common` preserves loop-live `D5/A1`;
- the generated probes perform no nested `MOVEM`;
- actor pointer `A4` and WRAM base `A5` remain live by non-clobber contract;
- the two inactive/budget-zero exits occur before the lean push;
- every post-push path crosses the single matching pop;
- no CCR dependency crosses the wrapper boundary.

Base-MC68000 instruction timing gives the local fixed recovery:

| Path | Build 0412 preservation | Build 0413 preservation | Saved |
|---|---:|---:|---:|
| inactive/budget-zero actor | 260 | 0 | 260 cycles |
| generic generated hit | 472 | 52 | 420 cycles |
| generic miss + universal probe | 684 | 52 | 632 cycles |

Generated frames, piece counts, lane selection, queue order, residency,
worklists, DMA, SAT construction, and final output are unchanged.

## Verifier hardening

`verify_pc090oj_direct_dispatch.py` now mechanically enforces the real private
contract rather than source formatting alone:

- destination/implicit writes to `A4/A5` are rejected in both probes, fast
  context, fast emitter, and mapping predicate;
- nested `MOVEM` is rejected in both probes and the directly participating
  helpers;
- `bsr`, sized `bsr`, `jsr`, and whitespace variants are counted so each probe
  has exactly one intended caller;
- both pre-save exits and push/pop/return ordering are checked;
- both stage dispatchers must retain full `D0-D7/A0-A6` preservation.

The emitted instructions are base MC68000 legal. The generator, frame-table,
direct-dispatch, variable-count, fast-enqueue, exact queue-bound, and canonical
gates pass. The completion manifest remains 49 `NATIVE_COMPLETE`, zero
`NATIVE_PARTIAL`, with zero reachable generated `UNRESOLVED` inputs.

## Deterministic 1,200-frame measurement

The non-numbered candidate is byte-identical to the numbered canonical Build
0413 (`0a3aab0c...`). The same cold boot, record-2 arm point, rendered-frame
window, input sequence, and energy hold were used. The faster candidate
completed eight additional workers and therefore reached a denser later game
state inside the same 1,200 rendered frames. Aggregate tail comparisons must be
read together with the equal-emitted-load result.

| Metric | Build 0412 | Build 0413 |
|---|---:|---:|
| workers/rendered | 0.9033 | 0.9100 |
| frames without completed worker | 116 | 108 |
| worker avg | 120,467.68 | 122,616.38 |
| worker median | 106,696 | 111,940 |
| worker p95 | 223,752 | 228,450 |
| worker worst | 319,882 | 309,574 |
| IRQ avg | 125,442.49 | 128,023.36 |
| IRQ median | 110,619 | 116,951 |
| IRQ p95 | 232,627 | 233,507 |
| IRQ worst | 336,065 | 333,747 |
| IRQ over 128,009 | 29.0% | 34.1% |
| graphics avg | 57,368.46 | 60,862.07 |
| graphics p95 | 93,636 | 90,372 |
| non-graphics avg | 63,099.23 | 61,754.31 |
| non-graphics p95 | 133,428 | 132,112 |

At equal emitted-piece load, median worker cost fell 3.3% for 20–29 pieces,
11.0% for 30–39, and 9.4% for 40–49. Corresponding p95 improvements were
9.5%, 22.9%, and 6.1%. This is the direct recoverable-cost result. The raw
1,200-frame distribution is not uniformly lower because Build 0413 advances
farther into the dense route; notably, worst worker and IRQ costs still fall.

| Complete-IRQ band | Build 0412 | Build 0413 |
|---|---:|---:|
| `<=128,009` | 770 (71.03%) | 720 (65.93%) |
| `128,010–160,000` | 177 (16.33%) | 259 (23.72%) |
| `160,001–200,000` | 70 (6.46%) | 45 (4.12%) |
| `200,001–250,000` | 27 (2.49%) | 23 (2.11%) |
| `>250,000` | 40 (3.69%) | 45 (4.12%) |

The trace tool was also corrected so publication DMA samples are dequeued once
and the reporting-only Pearson calculation cannot overflow. Neither change
alters emulated execution.

## Optional `FUN_000406A4` review

Static code proves `0x055650` tests the four direction bits and invokes only the
active directional routine(s); it does not call all four every update. The
measured Build-0413 route entered actor-coordinate scroll compensation in only
259 of 1,092 completed workers. Meaningful zero-delta calls were not proven, so
the proposed zero-delta guard was not implemented. The non-zero loop and all
camera, actor, collision, and PC080SN semantics remain untouched.

## MODE closeout tooling

The old closeout paced MODE press/release/dwell and its 18,000-frame abort in
display frames. Under coalesced workers, a complete button pulse could occur
between gameplay workers. The tool now counts actual producer-completion
writes, holds its worker-tick cadence across missed updates, records subround
dwell/release in those ticks, and uses `(round, subround, progress)` for a
24,000-display-frame no-progress watchdog plus a 120,000-frame safety ceiling.
Tap objects are held globally for the full MAME run.

Build 0413 `_c` completes all 18 established subrounds in 13,948 display
frames / 11,283 completed workers with 19 MODE presses. Player fallback,
generic fallback, player-piece adapter, and crash flag are all zero. Therefore
the Build-0412 four-subround result was a tooling synchronization failure; no
production regression was found.

## Gates and artifacts

- canonical gate: PASS;
- gameplay-entry gate: PASS;
- VDP ownership gate: PASS;
- address errors / bus errors / illegal instructions / crash entries: `0/0/0/0`;
- existing phase-one seven-epoch gate: labeled FAIL, unchanged and outside this
  PC090OJ optimization;
- full same-number family: canonical, `_d`, `_s`, `_do`, `_c`.

Tighe hardware/emulator visual, gameplay, and performance acceptance remains
required. Four-Armed remains `USER TEST REQUIRED`.

