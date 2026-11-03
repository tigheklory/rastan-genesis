# Cody - Build 0359 BBox Finalizer Performance

## Scope and baseline

Build 0359 is the focused production experiment requested after the accepted
Build 0357 O(1) sprite reverse-index work. Build 0358 is preserved as a
legitimate, source-equivalent instrumentation/baseline artifact. This task did
not alter the 49-cell sprite residency model, miss/victim path, stage dispatch,
Plane A, gameplay semantics, palette mapping, SAT ordering, lane ordering, or
frame lifecycle.

- baseline: Build 0357
- focused pre-change measurement ROM: Build 0358
- candidate: Build 0359
- Build 0357 SHA-256: `7468ba61394dc807e06e5ad795f9aa69184a197d9453b4fcb443f2c59564b8a2`
- Build 0358 SHA-256: `da0efda6c6e461be6e093fc8a73499df75dbe5567cdd511478b9eb6e3edd867c`
- Build 0359 SHA-256: `ca3844e6e3d0e175c0c0b5d14dd55bb4c8161d4619f14214e29d2a3d82b819cd`
- Build 0359 size: 1,715,896 bytes
- counter after publication: 359
- next valid build: 360

`FINAL_CONSENSUS.md` was not modified.

## Decision-relevant timing bracket

The focused bracket uses the established monotonic physical-beam method with
488 dots per physical scanline. It compares complete normal reverse-index hits
in the same automated gameplay sequence. The Build 0358 capture contains
28,561 complete hits; Build 0359 contains 28,311.

| Median component | Build 0358 | Build 0359 | Delta |
|---|---:|---:|---:|
| pre-bbox entry work | 0.523 lines | 0.535 lines | +0.012 |
| bbox orientation portion | 0.439 lines | 0.408 lines | -0.031 |
| bbox viewport tail | 0.096 lines | 0.088 lines | -0.008 |
| **combined bbox block** | **0.535 lines** | **0.496 lines** | **-0.039 (-7.28%)** |
| reverse-index hit lookup | 0.342 lines | 0.342 lines | unchanged |
| SAT emit tail | 0.963 lines | 0.963 lines | unchanged |
| **complete normal-hit entry** | **2.365 lines** | **2.336 lines** | **-0.029 (-1.21%)** |

The remainder after the bbox block, represented by reverse-index hit lookup
plus SAT emission, is 1.305 lines in both captures. This isolates a real but
small reduction at the intended boundary.

The first candidate probe layout overlapped debugger probes and produced no
complete entry samples. It is retained but explicitly non-authoritative as:

- `candidate_build0359/bbox_hitpath_invalid_overlapping_probes.csv`
- `candidate_build0359/bbox_hitpath_invalid_overlapping_probes_reduction.json`

The authoritative focused captures are the non-`invalid` CSV and reduction
JSON files under `states/traces/build0359_bbox_finalizer_performance/`.

## Implementation

### Exact pre-oriented bbox data

`tools/translation/build_pc090oj_opaque_bbox.py` now emits 16 bytes for every
one of the 4,096 PC090OJ codes. All four legal orientations are represented:

| Orientation index | Horizontal | Vertical |
|---:|---:|---:|
| 0 | no | no |
| 1 | yes | no |
| 2 | no | yes |
| 3 | yes | yes |

The entry is component-major: four `min_row` bytes, four `max_row` bytes, four
`min_col` bytes, then four `max_col` bytes. Runtime rotates the SAT attribute
flip bits into a two-bit orientation index and directly loads the selected
four bounds. The old per-entry `neg`/`addi`/`exg` transforms are gone.

The offline transform is the exact old 16x16-cell operation:

- vertical: `min_row,max_row = 15-max_row,15-min_row`
- horizontal: `min_col,max_col = 15-max_col,15-min_col`

An exhaustive generated-asset check validated all 4,096 codes x four
orientations (16,384 records). Bounds remain ordered and within 0..15. No
approximation, expansion, or clipping-policy change was introduced.

The asset grows from 16,384 to 65,536 bytes. Canonical generated-ROM coverage
therefore grows by `0xC000`, from `0x196EB8` to `0x1A2EB8`; the canonical opcode
replacement count remains 228.

### `pc090oj_ctrl_shadow` hoist

The gameplay finalizer is one uninterrupted 68000 call. The only inspected
writers to `pc090oj_ctrl_shadow` are arcade control-producer paths outside that
call. Build 0359 therefore reads the word once on `.Lnq_gameplay` entry, stores
it in the upper half of saved A4, and reuses it for all gameplay lane and
game-over entries. A4 is restored before `.Lnq_done_scan`.

Frontend direct callers still use `.Lnq_emit_entry` and read the live control
word per call. Only the proven gameplay-finalizer scope uses
`.Lnq_emit_entry_cached`; no broader lifetime was assumed.

## Comprehensive performance comparison

The Build 0359 full-chain capture contains 1,800 external frames, 1,391
publisher invocations, 1,390 complete chains, and 1,141 complete gameplay
chains. The table compares the same frame ranges and definitions used by the
Build 0357 report.

### Global results

| Measurement | Build 0357 | Build 0359 | Delta |
|---|---:|---:|---:|
| publisher median | 6.205 | 6.205 | unchanged |
| stage-dispatch median | 44.291 | 44.291 | unchanged |
| back/enemy-lane median | 41.641 | 41.078 | -0.563 |
| finalizer median | 91.242 | 91.041 | **-0.201 (-0.22%)** |
| full-chain median | 286.010 | 285.410 | **-0.600 (-0.21%)** |
| emitted entries, median | 26 | 26 | unchanged |
| chains below 262 lines | 41.35% (471/1,139) | 40.93% (467/1,141) | -0.42 percentage point |
| fitted finalizer slope | 3.116 lines/entry | 3.018 lines/entry | -0.098 (-3.14%) |
| emitted/finalizer correlation | 0.909 | 0.917 | comparable strong scaling |

The below-262 fraction did not improve in this run. The small 0.42-point
difference is within differing workload/run composition and is not evidence of
a semantic regression, but it does prove the optimization did not materially
change one-frame completion.

### Representative scenarios

| Scenario | Build 0357 finalizer | Build 0359 finalizer | Build 0357 full chain | Build 0359 full chain | Build 0359 back/enemy | Stage dispatch | Publisher | Median emitted |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| stationary, frames 407-699 | 91.242 | 91.090 | 257.073 | 257.291 | 41.174 | 44.291 | 6.205 | 28 |
| horizontal, frames 700-897 | 143.111 | 142.373 | 356.889 | 353.586 | 87.316 | 75.107 | 6.205 | 45 |
| vertical/jump, frames 1000-1399 | 70.508 | 70.594 | 335.463 | 333.254 | 20.666 | 30.488 | 7.795 | 20 |
| sprite-heavy, >=46 entries | 157.504 | 155.022 | 395.184 | 390.630 | 92.429 | 82.148 | 7.815 | 48 |

The sprite-heavy finalizer median improves by 2.483 lines (1.58%). This is the
clearest workload-sensitive gain, but it remains far below the estimated
19-34-line heavy-scene saving.

The worst observed Build 0359 finalizer occurred at frame 797: 41 emitted
entries, 314.963 finalizer lines, 259.775 back/enemy-lane lines, 80.209
stage-dispatch lines, 6.184 publisher lines, and 510.334 full-chain lines. The
Build 0357 worst-finalizer frame carried a different workload (38 entries), so
the two maxima are not an A/B regression measurement.

No Flying Demon or bat-specific claim is made; those actors were not forced for
this focused experiment.

## Interpretation

### Proven

- Pre-orientation removes the exact runtime bbox flip transforms and preserves
  all four legal orientation results.
- The combined bbox block falls by 0.039 physical line per complete normal hit.
- The normal-hit remainder measured after that block is unchanged.
- The finalizer slope falls from 3.116 to 3.018 lines per emitted entry.
- The global finalizer median falls only 0.201 line, and the full-chain median
  falls only 0.600 line.
- Stage dispatch and publisher medians remain unchanged.
- The requested 11-20-line global saving was not realized.

### Inference

- Visible black overrun bands are not expected to shrink materially from this
  change alone. Heavy scenes may receive a slight reduction, but the global
  frame-budget result is effectively unchanged.
- Stage dispatch is not yet the largest measured cost. The sprite finalizer
  remains about 91.0 lines globally versus 44.3 for stage dispatch, and 155.0
  versus 82.1 in the heavy subset. Within the finalizer, the back/enemy lane is
  still the dominant lane. The next measured hotspot therefore remains
  per-entry/finalizer work; prior Build 0354 evidence identifies palette
  routing/fixup as important historical context, but this task did not open a
  new optimization.

### Not proven by automation

- Pixel-identical appearance across every actor and flip combination still
  requires user visual verification.
- No claim is made for forced Flying Demon, bat, or later-scene coverage.

### Tighe visual stress test

Tighe subsequently traversed the first cave in Segment 1 without killing
enemies, deliberately preserving a high live-enemy population. Black overrun
bands remained, but were markedly smaller than in the prior Build 0357 cave
test. The captured Build 0359 internal bands were generally approximately
9-21 pixels, while the prior Build 0357 cave capture included approximately
25-pixel and 87-pixel bands.

This is a visually meaningful improvement under a sprite-heavy gameplay stress
case. It does not, however, establish that the Build 0359 bbox optimization is
the sole cause: the Build 0357 and Build 0359 runs were not frame-identical A/B
captures and therefore may differ in actor count, placement, animation state,
dirty publication work, or other per-frame load. The result is accepted as
positive user-observed Build 0359 behavior, not as a controlled causal
measurement of bbox-only savings.

#### Performance-test methodology

Global automated medians are not sufficient acceptance criteria for the visible
overrun problem. The black-band failure is strongly workload-dependent and may
not be represented by the automated median. Future performance builds should
therefore evaluate both global timing statistics and a repeatable first-cave
Segment 1 stress scenario in which Tighe traverses the cave without killing
enemies, preserving a high live-enemy population. Optimization decisions should
consider the bad cave frames directly rather than relying only on global median
improvement. A controlled frame-identical capture remains preferable when
assigning causality to one optimization.

## Validation

- generated bbox exhaustive check: PASS (16,384 orientation records)
- Python syntax checks for generator/reducer: PASS
- canonical ROM gate: PASS
- gameplay-entry gate: PASS, 564 frames, 240 post-entry frames, player control
  observed, zero address/bus/illegal/crash-handler events
- required seven-epoch Phase-1 gate: known FAIL, unchanged from Builds 0357 and
  0358 and recorded by the Makefile release ledger
- 30-second Genesis NTSC MAME smoke: PASS, 1,798 frames, no unique unmapped
  memory address
- new crash: none detected
- new graphics corruption, clipping error, palette issue, or SAT issue: none
  detected by static/gate/smoke checks; user visual verification remains required
- user cave stress test: IMPROVED - materially reduced black-band extent
  relative to the prior Build 0357 cave capture; residual approximately
  9-21-pixel bands remain; the comparison is not frame-identical, so bbox-only
  causality is not established
- `D00462`: unchanged

Build 0359 is preserved at
`dist/rastan-direct/rastan_direct_video_test_build_0359.bin`; the rolling ROM is
byte-identical. No Build 0360 was produced.

## Files changed for Build 0359

Production/build inputs:

- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `tools/translation/build_pc090oj_opaque_bbox.py`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Read-only measurement and durable evidence:

- `tools/mame/scripts/build0359_bbox_hitpath_audit.lua`
- `tools/mame/scripts/reduce_build0359_bbox_hitpath.py`
- `states/traces/build0359_bbox_finalizer_performance/`
- `docs/design/Cody_build0359_bbox_finalizer_performance.md`
- `AGENTS_LOG.md`

Normal Makefile-generated objects, maps, manifests, disassembly, ROM, counter,
and trace outputs were regenerated. Pre-existing unrelated dirty-tree changes,
including `apps/rastan-direct/src/boot/boot.s`, were not modified by this task.
