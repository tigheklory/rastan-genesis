# Build 0410 Shared Native Finalizer Performance Optimization

**Accepted baseline:** Build 0409  
**Candidate:** Build 0410  
**Target:** average worker below the 128,009-cycle NTSC frame budget  
**Result:** target not reached; the selected finalizer optimization is locally successful  
**Human visual/gameplay acceptance:** required

## Measurement method

Both ROMs used GENESIS NTSC MAME, the established record-2 deterministic
controller route, 1,200 rendered gameplay frames, and debugger-symbol
breakpoints. Breakpoints only read cycle/register state and add no emulated
68000 cycles. The finalizer bracket is
`profile_native_finalizer_entry` through its final RTS, not the older
pre-teardown boundary.

Build 0409 baseline evidence is
`states/traces/build0410_finalizer_baseline_0409/native_cost_summary.tsv`.
Build 0410 evidence is
`states/traces/build0410_native_finalizer_performance/native_cost_summary.tsv`
and
`states/traces/build0410_native_finalizer_frame_timing/`.

## Build 0409 finalizer baseline

- calls/completed worker update: 1
- cycles/call and cycles/update: 53,808.48
- cycles/rendered frame: 39,638.91
- share of Build 0409 graphics average: 70.60%
- median / p95 / maximum: 49,580 / 94,270 / 132,250 cycles
- cycles/finalized-or-rejected piece entry: 1,628.66

The exclusive debugger boundaries measured these principal costs per completed
finalizer call:

| Cost | Cycles/update |
|---|---:|
| fixed setup (unchanged code; Build 0410 exact bracket) | 5,957.81 |
| lane/queue iteration (same 118.62-cycle inter-piece machinery, adjusted to the 0409 piece count) | about 3,919 |
| source/blank identity before geometry | 7,538.81 |
| coordinate/flip/attribute geometry | 3,135.05 |
| opaque clipping plus dynamic variant resolution | 9,181.14 |
| reverse-residency hit path | 2,966.22 |
| reverse-residency miss detection | 387.12 |
| exact first-free victim scan | 5,738.61 |
| allocation/eviction/worklist install | 2,096.84 |
| resident-slot SAT construction/write | 10,831.74 |
| bbox rejection | 1,560.04 |
| allocation rejection | 9.86 |
| count/lane tail (unchanged code; Build 0410 exact bracket) | 257.25 |
| fixed teardown | 210.00 |

The clipping and dynamic-variant operations shared one existing profiler
boundary in the 0409 ROM, so they are reported honestly as one measured bucket
rather than assigned invented sub-costs.

Residency was not blended: Build 0409 measured 19,001 hit completions and 2,539
misses in 884 finalizers, or 21.49 hits and 2.87 misses/update. Miss handling
then spent 5,738.61 cycles/update scanning and 2,096.84 cycles/update installing
or replacing entries.

## Top three actionable costs

1. **Offline-known identity work.** The combined source/blank and
   bbox/variant regions cost 16,719.95 cycles/update. Direct player,
   secondary, and exact Level-B table records already have build-time-proven
   identities. Estimated recoverable cost: 5,000-8,000 cycles/update.
   Correctness risk: low to medium if the dynamic Level-A path is kept intact.
2. **SAT construction.** 10,831.74 cycles/update. A later pass could precompute
   invariant SAT attribute fragments and fuse the remaining writes. Estimated
   recovery: 3,000-5,000 cycles/update. Correctness risk: medium because live
   palette, flip, coordinates, links, and order must remain dynamic.
3. **Victim scan.** 5,738.61 cycles/update. An exact first-free 49-slot summary
   could preserve the current slot order while avoiding the repeated linear
   scan. Estimated recovery: 3,500-4,500 cycles/update. Correctness risk:
   medium because reservation, eviction, and reverse-directory ownership must
   remain identical.

The first target was selected because it was both the largest structurally
removable work and already owned by the existing Python semantic compiler.

## Structural change

The existing ten-byte generated piece record now uses an unused transport bit:

- `0x1000 | source_code`: build-time-proven direct base identity;
- `0x2000 | variant_index`: existing build-time-proven palette variant;
- unmarked identity: genuinely dynamic Level-A actor/base/bank semantics.

The existing Python generator marks player BODY/weapon, player secondary, and
exact Level-B nonvariant records with `0x1000`. The independent frame verifier
requires the marker, validates the original source code, rejects unfinalized
divergent identities, and normalizes it out of residency metadata.

The common finalizer now:

1. consumes marked identities without repeating blank-code validation;
2. skips runtime palette-variant lookup for both direct and prefinalized
   variant records;
3. computes the opaque-bounds pointer once and keeps it live across coordinate
   geometry instead of reconstructing the source a second time;
4. clears the transport marker through the existing residency/DMA
   normalization before artwork addressing.

Unmarked universal/Level-A records still execute the complete Build 0409
dynamic source, blank, bank, variant, clipping, residency, DMA, and SAT path.

No actor special case, sprite suppression, fallback, adapter, SAT reordering,
residency-policy change, or hardware-limit workaround was added.

## Build 0410 finalizer result

- calls/update: 1
- cycles/call and cycles/update: 46,502.94
- cycles/rendered frame: 35,380.98
- median / p95 / maximum: 39,264 / 86,404 / 128,252
- cycles/piece entry: 1,334.21
- reduction from 0409: **7,305.54 cycles/update (13.58%)**
- share of Build 0410 graphics average: 59.78%
- marked direct / still-dynamic entries in the armed interval:
  21,850 / 9,972

The new exact exclusive brackets measure fixed setup 5,957.81,
lane/queue iteration 4,134.15, lane/count tail 257.25, and fixed teardown
210.00 cycles/update. The selected source/bounds regions fell from
16,719.95 to 13,152.12 cycles/update despite the 0410 profiler route processing
more pieces per finalizer. SAT construction remained the largest individual
bucket at 9,808.69 cycles/update.

## Whole-worker performance

| Metric | Build 0409 | Build 0410 | Delta |
|---|---:|---:|---:|
| workers/rendered frame | 0.8358 | 0.8342 | -0.19% |
| worker average/update | 145,921.68 | 146,980.39 | +0.73% |
| worker median | 133,580 | 132,828 | -0.56% |
| worker p95 | 245,488 | 259,818 | +5.84% |
| worker worst | 363,962 | 364,094 | +0.04% |
| IRQ average/update | 151,489.25 | 152,267.67 | +0.51% |
| IRQ median | 137,785 | 136,955 | -0.60% |
| IRQ p95 | 254,929 | 263,359 | +3.31% |
| IRQ worst | 371,183 | 395,331 | +6.51% |
| graphics average/update | 76,211.10 | 77,795.99 | +2.08% |
| graphics median | 68,834 | 73,130 | +6.24% |
| graphics p95 | 112,684 | 115,972 | +2.92% |
| graphics worst | 160,312 | 162,010 | +1.06% |
| finalizer cycles/update | 53,808.48 | 46,502.94 | **-13.58%** |
| finalizer cycles/piece | 1,628.66 | 1,334.21 | **-18.08%** |
| IRQ >128,009 | 72.2% | 86.9% | +14.7 points |
| frames without completed worker | 197 | 199 | +2 |
| DMA words/update | 502.24 | 479.39 | -4.55% |
| frame-timing residency installs/update | 2.08 | 1.72 | -17.22% |

The whole-worker route does **not** show an aggregate speedup even though the
directly bracketed finalizer does. The 0410 sample has a materially different
sprite/actor load distribution (561 samples in the 20-29 bucket and 440 in
30-49, versus 828 and 175 in 0409), so the aggregate comparison includes
gameplay/AI load variation. Static instruction counts are not used to claim a
whole-worker win.

- Average worker below 128,009: **NO**
- Worker deficit: **18,971.39 cycles/update**
- Average IRQ below 128,009: **NO**
- IRQ deficit: **24,258.67 cycles/update**

Per the task stop rule, no second optimization was attempted.

## Regression and architecture gates

The bounded real-scene trace is
`states/traces/build0410_lizardman_regression/`. At frame 1223 the
`back_enemy` queue reaches 43 (>15). Two visible Lizardmen use selectors
`0x1F` and `0x1E`; their expected 10+8 body pieces are all present in the
published SAT, while the independently produced `0x0275` impact/effect also
coexists. This preserves the Build 0409 correction.

- Lizardman back_enemy >15: PASS
- complete visible Lizardman bodies: PASS
- all expected body pieces reach SAT: PASS
- impact/effect coexistence: PASS
- Four-Armed mechanical route: PASS by the shared verified 99-entry linker-end
  context; real-scene visual test required
- player BODY/FRONT/secondary/fire-sword generated coverage: PASS
- reachable player/generic fallback architecture: 0 / 0
- retired adapter: 0
- frame-table verifier: PASS
- direct-dispatch/fast-enqueue/queue-bound verifier: PASS
- canonical ROM gate: PASS
- gameplay-entry gate: PASS
- VDP ownership: PASS
- gameplay-entry address/bus/illegal/crash-handler entries: 0/0/0/0
- modified finalizer emitted-opcode/addressing inspection: PASS; all new
  instructions are base-68000 forms. A whole-file `-m68000` reassembly is not
  claimed because two pre-existing scaled stack-index instructions elsewhere
  in `pc090oj_hooks.s` still require later-CPU assembler syntax.

The pre-existing seven-epoch gate warning remains: its target epoch installed
through the production boundary and full A/B LUT checks passed.

## Artifacts

All five ROMs are 1,998,520 bytes.

| Variant | SHA-256 |
|---|---|
| canonical | `68669fec67a00566f4e4cc4624062c52ac6ac36e5875fdc76161fce700ec923e` |
| `_c` | `24fd5ccb95f557878504bde64e29f9c21d7dc4fe6242af5ec38624236eef2eb2` |
| `_d` | `159d7e113d31fb836d842dea68538803fd037f3488ed40037c1c2923f3ab567a` |
| `_do` | `199e43ca45491445d9244f21404a1d1c7e36249ad5abdc01ab86dd0edab177bd` |
| `_s` | `5f41c682fd2ec7d769687ea800ed58317fb5d02ab8d29fee8d4cc8ff86dacf16` |

Tighe visual/gameplay validation is required.

## Next measured target

SAT construction is now the largest individual finalizer bucket at
9,808.69 cycles/update. A future bounded task should first determine how much of
its palette/flip/priority/tile composition is invariant enough to precompute
without changing live palette selection, links, ordering, or Genesis hardware
sprite-limit behavior.

Phase D: **NO**  
Phase E: **NO**

