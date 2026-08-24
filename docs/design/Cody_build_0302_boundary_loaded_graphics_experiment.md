# Cody Build 0302 Boundary-Loaded Graphics Experiment

Date: 2026-08-21

## Outcome

Build 0302 replaces Build 0301's continuous gameplay PC080SN pattern-residency
management with precompiled Stage-1 packages selected only at an original arcade
semantic progression boundary. Ordinary Plane A and Plane B tile publication now
performs a direct indexed LUT read. It does not scan a plane, mark live patterns,
hash, allocate, evict, maintain an LRU, or load a missing pattern.

This is an empirical architecture build. The ROM and production gate pass, but the
mandatory MAME smoke trace remained in frontend state. Gameplay speed and visual
coverage therefore require Tighe's run and are not claimed as verified here.

## Baseline And Artifact

- Accepted runtime baseline: Build 0301.
- Produced artifact: `dist/rastan-direct/rastan_direct_video_test_build_0302.bin`.
- SHA-256: `990644b2bb2fadefdc20cd03322294caf438754d9b2fd11abdd7666ec12768e6`.
- Size: 2,555,576 bytes.
- Counter: 301 -> 302.
- Rolling and numbered artifacts are byte-identical.
- Canonical gate: PASS.
- Additional numbered builds: none.

## Native Semantic Cut

The retained arcade semantic state is:

- the Stage-1 map record/progression value at `a5+0x013E`;
- the current proven Plane B Y state at `a5+0x10EE` when the boundary executes;
- the original arcade tile codes and attributes produced by the retained map logic.

The native replacement consumes those decisions and directly realizes Genesis
pattern residency plus Plane A/Plane B name-word pattern slots. It does not model a
software PC080SN device.

The retired active gameplay tail is the Build 0301 continuous residency system:

- no VBlank `vdp_commit_streamed_tiles` call;
- no tile-publication `fg_cache_mark_live` call;
- no live-pattern scan;
- no hash-table residency lookup;
- no runtime allocation, eviction, or LRU maintenance;
- no upload-queue drain in the normal VBlank path.

## Boundary Hook

The hook replaces `arcade_pc 0x0558FE`, the
`addq.w #1,a5+0x013E` in `pc080sn_advance_map_group`. This instruction executes only
after the completed 64-publication ring cycle. In Build 0302 it maps to
`runtime_genesis_pc 0x0559D8` and calls `fg_boundary_advance_segment` at
`runtime_genesis_pc 0x072440`.

`fg_boundary_advance_segment` preserves the original increment and then invokes
`fg_boundary_install` exactly once. The following original arcade RTS at
`arcade_pc 0x055902` remains normal shifted arcade flow. The remap is a proper
4-byte to 6-byte shift replacement; no NOP, RTS bypass, or equal-length workaround
was introduced.

Scene entry also calls `fg_cache_reset`, which clears the diagnostic counters and
installs the package for the current Stage-1 state while display is already off.

## Offline Package Model

`tools/translation/compile_pc080sn_genesis.py --boundary-experiment` compiles the
packages from original arcade ROM data. It has zero production trace inputs.

The generated model contains:

- 23 Stage-1 records;
- 8 variants for each ordinary record;
- 1 full-ring variant for each explicit vertical record 17 and 21;
- 170 total packages;
- a 10,240-word (`0x2800`) direct active LUT;
- a 936,116-byte package binary;
- pattern slots 64..1023, or 960 slots total;
- exact-pattern byte deduplication within each package.

Ordinary variants are selected by:

```text
variant = (Plane-B Y & 0x01FF) >> 6
```

The eight base rows are 0, 8, 16, 24, 32, 40, 48, and 56. Each package contains:

- the complete compiled Plane A requirement for that record;
- a 36-row Plane B core;
- two additional source rows before and after the core;
- 40 Plane B source rows total, wrapping in the 64-row ring.

The 36-row core covers all 29-row visible starts within an eight-row Y class. The
four extra rows are the explicit experimental margin. The selected variant is not
reconsidered when Y changes during ordinary movement.

Plane A is allocated first and completely. Plane B core rows are allocated before
margin rows. If a package exceeds 960 unique pattern slots, excess Plane B codes are
deliberately omitted and become visible runtime misses. No package drops Plane A.
Twenty-two packages contain deliberate Plane B drops; the largest drop count is
315. Maximum slot use is 960 of 960.

Generated outputs are:

- `build/pc080sn_boundary/boundary_packages.bin`;
- `build/pc080sn_boundary/boundary_constants.inc`;
- `build/pc080sn_boundary/boundary_report.json`.

The generated report SHA-256 is
`e4f7b473989defa774b1f99333b12bb954984b3cb8dc24490d4face164feeebc`.

## Direct LUT And Miss Contract

The active LUT is indexed directly by arcade tile code. A nonzero mapped entry is
the final Genesis pattern slot. Code zero remains blank. An out-of-range or unmapped
code returns slot zero and increments exactly one plane-specific 32-bit counter.

- Plane A resolver: `fg_boundary_resolve_a` at `runtime_genesis_pc 0x07244A`.
- Plane B resolver: `fg_boundary_resolve_b` at `runtime_genesis_pc 0x072492`.
- Plane A miss counter: `fg_boundary_miss_a` at Genesis-WRAM `0x00FFB1D4`.
- Plane B miss counter: `fg_boundary_miss_b` at Genesis-WRAM `0x00FFB1D8`.

A miss never scans, allocates, evicts, or loads a pattern. It is intentionally
observable as a blank/diagnostic cell.

## Boundary Installation

`fg_boundary_install` at `runtime_genesis_pc 0x0724DA` performs all residency work:

1. Require gameplay scene 1 and a Stage-1 record below 23.
2. Read Plane B Y once and select the precompiled variant.
3. Clear and populate the active direct LUT from generated `(code, slot)` pairs.
4. Disable display for package installation.
5. DMA each precompiled pattern from `genesistan_pc080sn_tile_rom` to its assigned
   Genesis VRAM slot through `vdp_dma_words_to_vram`.
6. Re-enable display and return to retained arcade flow.

No normal-frame path calls the installer. No ordinary tile miss calls the installer.

## Instrumentation

All counters are 32-bit and are reset on scene entry:

| Meaning | Symbol | Genesis-WRAM |
|---|---|---:|
| Graphics epoch transitions | `fg_boundary_epoch_transitions` | `0x00FFB1CC` |
| Plane B variant selections | `fg_boundary_variant_selections` | `0x00FFB1D0` |
| Unmapped Plane A publications | `fg_boundary_miss_a` | `0x00FFB1D4` |
| Unmapped Plane B publications | `fg_boundary_miss_b` | `0x00FFB1D8` |
| Pattern DMA transitions | `fg_boundary_pattern_dma_transitions` | `0x00FFB1DC` |

Current selection state is also exposed:

- `fg_boundary_active_record`: Genesis-WRAM `0x00FFB1E0`;
- `fg_boundary_active_variant`: Genesis-WRAM `0x00FFB1E2`.

## Explicit Vertical Records

Records 17 and 21 use one full 64-row Plane B package each rather than a narrow
Y-band. Both fit the fixed plane region without runtime compatibility fallback:

- record 17: 70 Plane A plus 663 Plane B unique patterns, 733 slots, zero drops;
- record 21: 116 Plane A plus 663 Plane B unique patterns, 778 slots, zero drops.

The Build 0301 global per-frame residency manager is not reactivated for these
records.

## PC090OJ And Compatibility Boundaries

The Build 0301 native PC090OJ gameplay runtime and fixed sprite pattern region
1024..1535 are preserved. This task does not alter sprite queues, SAT finalization,
sprite palette decisions, or unresolved bat/item/four-armed-enemy palette policy.

Remaining transitional compatibility is isolated:

- non-gameplay/frontend tile resolution continues to use the existing static LUT
  and frontend compatibility paths;
- existing scene-load pattern setup still runs before the gameplay boundary package
  overwrites the native plane pattern region;
- the old cave-residency helper body remains present but its active gameplay call
  was removed;
- the 23-record package model is Stage-1-only and disables itself outside that range.

These paths are not claimed as final native PC080SN architecture. Their removal
boundary is a later frontend conversion and multi-stage boundary compiler, not this
Stage-1 performance experiment.

## Production Changes

Task production inputs changed:

- `apps/rastan-direct/Makefile`;
- `apps/rastan-direct/src/fg_tile_cache.s`;
- `apps/rastan-direct/src/tilemap_hooks.s`;
- `apps/rastan-direct/src/vdp_comm.s`;
- `specs/rastan_direct_remap.json`;
- `tools/translation/compile_pc080sn_genesis.py`;
- `tools/translation/postpatch_startup_rom.py`;
- `tools/translation/verify_canonical_rom.py`.

The canonical covered-byte invariant changed from `0x18AEB8` to `0x26FEB8`, an
exact `0x0E5000` increase caused by the generated package data. The opcode-replace
count remains 227. The shift-table patcher applied 68 shift replacements and rebased
7,213 branches plus 630 absolute long references.

## Validation

- Normal production build: PASS.
- Canonical gate: PASS.
- Numbered artifact exists: PASS.
- Rolling/numbered SHA equality: PASS.
- Counter exactly 302: PASS.
- Mandatory MAME trace: PASS, 1,798 external frames.
- MAME average reported speed: 467.90%.
- Unique unmapped memory addresses: none.
- Fatal/error/exception evidence in trace: none.
- Trace path:
  `states/traces/rastan_direct_video_test_build_0302_mame_30s_20260821_210542/`.

The smoke trace did not enter gameplay: Stage-1 record, selector, scene, and tile
instrumentation watches did not change. It therefore validates boot/frontend and
the absence of a trace-detected fatal, but does not validate gameplay rendering,
gameplay speed, package transitions, or miss behavior.

## Known Experimental Limitations

- The selected Y variant remains fixed until the next semantic record boundary.
- Movement outside its 40-row source band can expose Plane B misses.
- Twenty-two packages intentionally omit some Plane B codes under slot pressure.
- A boundary can perform up to 960 individual pattern DMAs with display disabled;
  transition pause/blanking duration requires empirical evaluation.
- The Stage-1 package model does not establish a whole-game residency solution.
- Frontend PC080SN compatibility remains transitional.
- Gameplay speed, Rastan/lizard/bat/axe visibility, scrolling, and localized miss
  behavior require Tighe's visual/speed test.

## Test Questions For Tighe

1. Is gameplay approximately normal speed relative to Build 0300 and materially
   faster than Build 0301?
2. Does Plane A remain generally coherent through Stage 1?
3. Is Plane B coherent near each selected Y band, with failures appearing as local
   blank cells rather than systemic corruption?
4. Do Rastan, lizard men, bats, and the axe item retain Build 0301 behavior?
5. Are boundary transitions acceptably brief?
6. After a visible failure, record the five counters and active record/variant so
   the next build can widen or repartition the exact package without restoring a
   runtime cache.

