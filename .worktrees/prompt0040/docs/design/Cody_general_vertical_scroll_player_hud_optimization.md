# Cody — General vertical-scroll / player / HUD performance optimization

Date: 2026-10-15  
Accepted baseline: **Build 0433**  
Candidate: **Build 0434**  
Classification: **EXTENDING**

## Scope and selection

This task resumed with the bounded player/HUD/vertical-scroll audit already
complete and with a partial vertical-row implementation in the working tree.
The audit was not repeated.

- **Player:** the accepted Build-0428 native player path is already near-minimal
  on reachable normal frames. The remaining three-slot auxiliary scan did not
  justify disturbing the accepted player contract. Player code was not changed.
- **HUD:** the gameplay path still reconstructs six BCD digits and three fixed
  glyphs every frame. This is a material future opportunity, but a change-driven
  implementation would alter persistent queue/finalizer ownership. It was
  deferred in favor of the lower-risk event-correlated target. HUD code was not
  changed.
- **Vertical scroll:** selected. Each crossed logical row regenerated all 64
  Plane-A cells and all 64 Plane-B cells through general scene-aware resolver
  calls, while Plane A also recomputed row-wide source, destination, and live
  ring-front context in each of sixteen four-cell blocks.

No exploratory gameplay trace, new route, new Lua script, or manual MAME play
was used. No arcade function required new decompilation.

## Semantic boundary

The existing semantic cut is unchanged:

```text
arcade camera delta / crossed logical row decision
    -> native logical Plane-A and Plane-B row production
    -> final Genesis staging words and existing dirty-row publication
```

The retired tail remains the PC080SN C-window/name-RAM realization. This change
only optimizes the already-native Genesis row producer; it adds no chip shadow,
projection buffer, fallback architecture, or collision ownership.

## Implementation

Files changed for this optimization:

- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/fg_tile_cache.s`
- the `tilemap_hooks.o` generated-constant dependency in
  `apps/rastan-direct/Makefile`
- the existing gate
  `tools/translation/verify_bg_a_incremental_background.py`

The active gameplay residency LUT is now exported to the row producer. Each
crossed row establishes its invariant context once.

### Plane A

`.Lplane_a_publish_logical_row_native` now hoists:

- the live rebuilt source-row pointer;
- the physical `staged_fg_buffer` row base;
- the active residency-LUT base;
- the current ring-front column.

The sixteen four-cell blocks retain the exact accepted source delta:

```text
(logical_column >> 2) - strip_group
    - 16 when logical_column is beyond the live ring front
```

The single block that can straddle the live ring front still resolves its four
cells with `resolve_plane_a_cell`. All other blocks retain generated native
metatile selection, attribute/palette/flip composition, and four exact final
name words, but perform the active-LUT lookup inline. The private block helper
now saves only the two values its row caller needs preserved instead of saving
and restoring the full register set sixteen times.

### Plane B

`.Lplane_b_publish_logical_row_native` now hoists:

- the physical `staged_bg_buffer` row base;
- the active residency-LUT base.

Its descriptor-group cache, source selection, tile attributes, 64-cell loop,
and final words are unchanged. The scene-aware helper call is replaced by the
same inline active-LUT/miss semantic used by Plane A.

### Dynamic work deliberately retained

- all 64 logical cells on Plane A;
- all 64 logical cells on Plane B;
- live descriptor/metatile and source-group decisions;
- the authoritative four-cell ring-seam fallback;
- exact zero/out-of-range/unresident miss behavior and separate A/B counters;
- one dirty bit for each affected physical row on each plane;
- existing publication order and two 64-word row DMAs;
- residency and pattern-install ownership;
- collision-map ownership (untouched).

No visible-cell pruning, skipped row work, reduced DMA, or special-case route
was introduced.

## Objective code-level reduction

For every paired Plane-A/Plane-B row crossing:

- Build 0433 entered general residency resolver helpers **128 times**.
- Build 0434 enters them **zero times** on Plane B and **zero times** on the 60
  normal Plane-A cells. Only the existing seam block, when present, retains four
  authoritative Plane-A resolver entries. Therefore **124–128 general helper
  entries per paired row are removed**.
- Fifteen of sixteen repeated Plane-A source-row, destination-row, active-LUT,
  and ring-front setups are removed.
- Sixteen full private-helper register save/restore sets become one outer row
  save plus two-register block-local preservation.
- Sixty-four repeated Plane-B destination-row-base calculations are replaced by
  one row calculation.
- The combined affected `.text` region is 30 bytes smaller (Plane-A row/block
  region 54 bytes smaller; Plane-B row region 24 bytes larger because its hot
  lookup is inline).

No new gameplay instrumentation was authorized, so no cycle percentage is
claimed. The deterministic rope route is a global-regression check, not a
localized crossed-row microbenchmark.

## Static equivalence and gates

The existing full-span background verifier was narrowly extended rather than
creating a parallel framework. It now checks the new assembly contracts and
exhaustively compares accepted and hoisted behavior for:

- all 16,384 masked tile codes, including identical miss deltas;
- all 64 logical rows and columns;
- all 64 live ring-front positions;
- Plane-A source deltas and seam classification;
- Plane-A and Plane-B physical staging destinations.

Results:

- full-span/background vertical-row equivalence: **PASS**;
- selector-0 equivalence: **PASS** — 163,840 coordinate cases and 934,928
  descriptor/subcell/context cases;
- selector-1/2 equivalence: **PASS** — 655,360 selection cases and 1,869,856
  descriptor/subcell/context cases;
- collision/visual separation: **PASS**;
- native PC080SN metatiles and Plane-B visual records: **PASS**;
- VDP DMA boundary gate: **PASS**;
- canonical gate: **PASS**;
- gameplay-entry gate: **PASS**, zero exceptions;
- phase-one seven-epoch gate: **FAIL**, matching the recent established result
  after observing only target record/epoch 0; the target epoch checks passed.
- standard fixed 30-second trace: **PASS**, 1,798 frames.

The standard trace is stored under
`states/traces/rastan_direct_video_test_build_0434_mame_30s_20261015_195841/`.

## Build 0434 family

All artifacts are 2,698,936 bytes.

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0434.bin` | `178838c4eed65f920a78718c63fe1086e55ab0aeb567177f2918898b0ac1d5ca` |
| `rastan_direct_video_test_build_0434_d.bin` | `ea5cf2a4af6db675afa25cd33b2f5a20a5794a0dfa5d82cafd146f2f4616eaac` |
| `rastan_direct_video_test_build_0434_s.bin` | `51f47ff0d6cbb44c8e87d7f8b65a920d08e2311f5f66fdb632b8c4f253f6455c` |
| `rastan_direct_video_test_build_0434_do.bin` | `fc4e7759147c2ab17e887cc2408ecbdb7a05a9fe87e8f93b7e290fbda6b14d8b` |
| `rastan_direct_video_test_build_0434_c.bin` | `3ec86db1bb87c76921a9e9e8c7f61b906f69832c1252293fb954ff7ef46b0beb` |

The Makefile verified the complete canonical/`_d`/`_s`/`_do`/`_c` set.

## Deterministic rope benchmark

The existing unchanged GENESIS NTSC benchmark produced:

```text
trial 1: 803 frames / 13,400.588 ms
trial 2: 803 frames / 13,400.588 ms
trial 3: 803 frames / 13,400.588 ms
deterministic: YES
```

Median: **803 frames / 13,400.588 ms**. Delta versus accepted Build 0433:
**0 frames / 0.000 ms / 0.000%**. Remaining arcade Silver Standard gap:
**32 frames / 550.588 ms** versus 771 frames / 12,850.000 ms.

Evidence: `states/traces/build0434_rope_attach_benchmark/`.

Interpretation: **NO GLOBAL REGRESSION**. The route does not isolate the opening
vertical row-crossing cost, so real-Genesis `_do` bar height/duration remains
the relevant localized acceptance.

## Acceptance

- Real Genesis vertical-scroll/background/HUD/player acceptance: **USER MUST
  VERIFY**.
- Build 0434 is a candidate, not accepted by this report.
- If it fails visual/gameplay acceptance, Build 0433 remains accepted.
- Phase D started: **NO**.
- Phase E started: **NO**.

