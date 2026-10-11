# Build 0411 Native Worker One-Frame Optimization

**Input baseline:** Build 0410  
**Candidate:** Build 0411  
**Primary target:** average worker below the 128,009-cycle NTSC frame budget  
**Result:** achieved on the established deterministic route; human acceptance required

## Method

All comparisons use GENESIS NTSC MAME and the established record-2 controlled
route. The cost profiler measures 1,200 armed gameplay frames with host-only
debugger breakpoints; those breakpoints add no emulated 68000 cycles. Evidence:

- Build 0410 SAT baseline:
  `states/traces/build0411_sat_baseline_0410/native_cost_summary.tsv`
- SAT-only candidate:
  `states/traces/build0411_sat_candidate/` and
  `states/traces/build0411_sat_candidate_timing/`
- final SAT + victim-scan candidate:
  `states/traces/build0411_sat_victim_candidate/` and
  `states/traces/build0411_sat_victim_candidate_timing/`
- displayed Lizardman/SAT regression route:
  `states/traces/build0411_lizardman_regression/`

## SAT baseline and exclusive breakdown

Build 0410 emits 22.004 SAT entries per completed finalizer update. The six
exclusive SAT phases reconcile exactly to 9,808.69 cycles/update:

| Phase | Cycles/update | Cycles/entry |
|---|---:|---:|
| mark resident slot used | 2,068.41 | 94.00 |
| Y word | 792.16 | 36.00 |
| size/link word | 704.14 | 32.00 |
| tile/priority/palette/flip word | 5,363.80 | 243.76 |
| X word | 792.16 | 36.00 |
| output count | 88.02 | 4.00 |
| **total** | **9,808.69** | **445.76** |

The tile-attribute phase was the largest actionable subcost. It rebuilt V/H
bits with two branch trees, shifted the four-valued palette line thirteen
places at runtime, moved the resident slot through two stack round trips, and
performed masks whose later modulo operation or the 49-slot bound already
made redundant. There is no unaccounted SAT cost at these boundaries.

## SAT optimization

The common hit path now retains the resident slot in `D6`, derives both V/H
bits with one shift/mask, selects the invariant Genesis palette fragment from
a four-word table, and removes redundant coordinate/link/tile masks. It still
computes screen X/Y, live palette-map selection, current resident tile,
sequential SAT link, and output count at runtime. SAT order, lane order,
termination, flip meaning, priority, HUD-white selection, residency, and the
80-entry hardware ceiling are unchanged.

The SAT-only candidate measures:

- 21.866 entries/update;
- 333.20 cycles/entry;
- 7,285.71 cycles/update;
- 2,522.98 cycles/update recovered from Build 0410 (25.72%).

The full post-SAT route reaches 0.8700 workers/rendered frame, 136,611.67
worker cycles/update, 141,964.10 IRQ cycles/update, 66,017.27 graphics
cycles/update, and 42,894.64 finalizer cycles/update. The worker remained
8,602.67 cycles over budget, so the task required the next measured target.

## Next target: exact first-free residency scan

After the SAT change, a miss still called a bit-test helper once per candidate
slot, always beginning at slot zero. It cost 4,317.19 cycles/update and
1,840.41 cycles/miss. The replacement scans the six complete used-bit bytes in
ascending order, then their bits in ascending order, followed by the sole
valid bit for slot 48. It therefore returns exactly the same lowest free slot;
reservation, eviction, reverse-directory ownership, worklist capacity, and
staged-frame safety are unchanged.

The final route measures 522.23 cycles/update and 238.51 cycles/miss for this
scan, recovering 3,794.97 local cycles/update (87.90%). No residency policy was
changed.

## Final performance

| Metric | Build 0410 | Build 0411 | Delta |
|---|---:|---:|---:|
| workers/rendered frame | 0.8342 | 0.9033 | +8.28% |
| worker average/update | 146,980.39 | 126,786.39 | -13.74% |
| worker median | 132,828 | 120,618 | -9.19% |
| worker p95 | 259,818 | 228,162 | -12.18% |
| worker worst | 364,094 | 313,722 | -13.84% |
| IRQ average/update | 152,267.67 | 131,589.13 | -13.58% |
| IRQ median | 136,955 | 124,177 | -9.33% |
| IRQ p95 | 263,359 | 233,753 | -11.24% |
| IRQ worst | 395,331 | 339,963 | -14.01% |
| graphics average/update | 77,795.99 | 56,833.13 | -26.95% |
| finalizer cycles/update | 46,502.94 | 38,572.31 | -17.05% |
| SAT cycles/update | 9,808.69 | 7,220.27 | -26.39% |
| IRQ over 128,009 | 86.9% | 34.1% | -52.8 points |
| frames without completed worker | 199 | 116 | -41.71% |
| residency installs/update | 1.72 | 1.16 | -32.56% |
| DMA words/update | 479.39 | 441.39 | -7.93% |

The primary milestone is achieved by 1,222.61 cycles/update. The secondary IRQ
average remains 3,580.13 cycles/update over budget; it was not the campaign's
stop condition. The next largest isolated finalizer regions are pre-geometry
identity/attribute work (about 6,440 cycles/update) and bounds/variant work
(about 6,397 cycles/update), but no third optimization was begun after crossing
the required worker threshold.

## Correctness and architecture gates

The final displayed-SAT route reaches `back_enemy=38`. At frame 1228, both
visible Lizardmen publish complete 8- and 10-piece bodies while the independent
`0x0275` impact entry coexists. Peak load is 14 sprites / 28 cells on a
scanline, below Genesis limits. Four-Armed uses the same verified 99-entry
linker-end path, but its actual visual route was not naturally exercised and
remains a user test.

- player BODY/FRONT/secondary and sword/axe/hammer/fire-sword generated tables:
  verifier PASS;
- completion manifest: 49 `NATIVE_COMPLETE`, 0 `NATIVE_PARTIAL`;
- numbered `_c` full-game closeout reaches all 18 established subrounds with
  player fallback / generic fallback / adapter `0 / 0 / 0`, first fallback
  `NONE`, and crash flag `0000`;
- runtime PC090OJ descriptor/piece parsing: 0 / 0;
- frame generator/verifier, direct dispatch, variable-count reconciliation,
  fast enqueue, exact queue ends, and residency/finalizer/SAT pipeline: PASS;
- modified SAT and first-free paths disassemble entirely as base-MC68000
  instructions: PASS;
- canonical ROM gate and gameplay-entry gate: PASS;
- VDP ownership: PASS on the final 1,200-frame route;
- gameplay-entry address/bus/illegal/crash-handler entries: `0/0/0/0`;
- pre-existing seven-epoch gate remains a labeled FAIL warning; no PC080SN
  source was changed.

Phase D, Phase E, Build 0401, PC080SN, and H25 were not touched.

## Build 0411 artifacts

All artifacts are 1,998,520 bytes.

| Variant | SHA-256 |
|---|---|
| canonical | `5b3941e57e885e13e34772daef211f2ed67557372f95bf4d1855bb6b2cb6a0e8` |
| `_c` | `75b9fe10a5a47f65fe42fd90840c347a5900898e6d394d382d2f74dfa55934c5` |
| `_d` | `25d1f0f0e4e94fceba88cb53aa7e4f39284d951deb4ae9f6300c9e79c9993379` |
| `_do` | `3d60904fcc20ba15bd47ecbceac35efa0e93968c69db993c311bae54d622febc` |
| `_s` | `8d9952e423283f9a19d6d4c3dac64c67613baceb35bc6bf022417dcaa689a96c` |

Tighe visual, gameplay, and subjective performance acceptance is required.
