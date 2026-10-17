# Cody Build 0439 — Plane-A horizontal residency optimization

Date: 2026-10-17
Baseline: Build 0438, commit `29412437861ea5e7fb046fc6d0b1c1bb58d73b2a`
Candidate: Build 0439
Candidate source commit: `033795e327a70b2cb79b94ed2632cb2630ed628b`
Acceptance: pending Tighe real-hardware testing

## Scope and semantic boundary

The only production path changed is
`genesistan_hook_tilemap_plane_a_selector0_native`, the already-native Plane-A
selector-0 entering-column producer. The semantic cut is unchanged: arcade code
owns the scroll/camera state, entering-column decision, source data, and collision
meaning; this native producer consumes the generated four-row records and creates
the collision-map and Genesis Plane-A staging outputs. No additional arcade
PC080SN tail was translated or retained.

Plane B, selector 1/2, vertical-row publication, destination arithmetic, collision
representation, DMA publication, sprites, HUD, damage, and Phase D/E were not
changed.

## `fg_cache_resolve` contract

At entry, `D3.W` is the visual tile code. The helper preserves `D0`, `D2`, and
`A0`, masks the code to 14 bits, and returns the resolved Genesis pattern in
`D3.W`:

- code zero returns zero without a miss;
- scene ID 1 uses `fg_boundary_active_lut`, accepts only codes below
  `FG_BOUNDARY_LUT_WORDS` (`0x2800`), and counts either an out-of-range code or a
  zero LUT entry in `fg_boundary_miss_a` before returning zero;
- all other scene IDs use the complete 0x4000-word
  `genesistan_pc080sn_tile_vram_lut`; a zero entry returns zero without changing
  the miss counter;
- an ordinary nonzero LUT entry is returned directly.

The selector composes the returned word with its already-hoisted attribute. It
does not consume resolver condition codes. Scene identity and therefore the LUT
base, exclusive limit, and miss policy are invariant over one complete entering
column.

## Implementation

Before the 16-by-4 traversal, selector 0 now selects one register-held context:

- `A2`: static LUT or active LUT base;
- `D7.W`: `0x4000` for the static LUT or `FG_BOUNDARY_LUT_WORDS` for the active
  LUT.

Both registers were already protected by the selector's outer `MOVEM`. The
per-cell `bsr fg_cache_resolve` was replaced by its exact bounded leaf semantics:
zero test, selected-limit test, indexed word load, and the original active-only
miss accounting. No RAM context, scheduler state, translation table, or
replacement helper was introduced.

The original traversal and publication contracts remain:

- 16 four-row descriptor/native-record groups;
- 64 logical rows and 64 collision writes;
- independent visual and collision fields;
- exactly 32 resident visual staging outputs;
- N/N+32 logical-to-physical coherence and physical-row wrap;
- one fixed entering column, with no grouping across the live ring front;
- one dirty-column mark and the existing gathered 32-word VDP DMA.

## Static equivalence

`tools/translation/verify_bg_a_incremental_background.py` was extended rather
than creating a new harness. It now rejects a selector-0 resolver call or
per-cell scene selection and proves old-versus-new behavior for:

- every 14-bit code in scene IDs 0, 1, 2, and `0xFF`, including injected zero
  active/static LUT entries;
- every visible top, entering column, and all 64 logical rows for active and
  static scenes;
- zero, resident-hit, active-zero, active-out-of-range, and static-zero cases;
- collision values/destinations, the 32 staging values/destinations, cumulative
  miss deltas, and the dirty-column result.

The existing selector-0 generated-record verifier also passed 163,840 coordinate,
front, wrap, and rebase cases plus 934,928 descriptor/subcell/context cases. The
selector-1/2 verifier and independent collision/visual verifier passed unchanged.

Result: **PASS**.

## Assembled hot-path proof

The saved Build-0438 selector-0 object has a `R_68K_PC16 fg_cache_resolve`
relocation inside the cell loop. Build 0439 has no such relocation within the
selector. Its disassembly establishes `genesistan_pc080sn_tile_vram_lut`,
`genesistan_current_scene_id`, and (when applicable)
`fg_boundary_active_lut` before `.Lplane_a_sel0_cell_loop`; the loop directly
indexes `0(A2,D3.W)` and owns the `fg_boundary_miss_a` update.

Representative shapes:

| Case | Build 0438 | Build 0439 |
|---|---|---|
| resident | outer BSR, helper MOVEM, scene/range work, inner active-address BSR/RTS, load, helper RTS | zero/range branches, indexed load, continue |
| zero | outer BSR, helper MOVEM, duplicate mask/zero branch, restore/RTS | one local zero branch |
| active miss | outer BSR, helper frame, scene/range/address work, counter, restore/RTS | local limit/zero-entry branch, same counter and blank result |

There is no per-cell helper, scene-selection branch, or RAM context access.
Descriptor grouping remains 16-by-4; the collision store remains inside the
64-cell loop; the physical-window test still admits exactly 32 staging stores.

Result: **PASS**.

## Static work accounting

Using standard 68000 instruction timings, an ordinary nonzero gameplay resident
lookup changes from approximately 240 cycles (including the selector's outer
BSR, helper save/restore, and nested active-LUT-address BSR/RTS) to approximately
48 cycles inline. The active-context setup added once per entering column is
approximately 68 cycles; the static-context setup is approximately 50 cycles.

For a maximum 64-hit gameplay column this is approximately:

- helper calls removed: 64 outer resolver calls and 64 nested active-address
  calls;
- BSR/RTS work removed: 4,352 cycles (the previously established floor);
- helper register save/restore removed: 4,352 cycles;
- repeated mask, scene test, active range setup, and LUT-address setup removed;
- one active-context setup added: about 68 cycles;
- ordinary-hit net static reduction: about 12,220 cycles per full 64-hit event.

Path-dependent savings remain substantial and semantically exact: roughly 110
cycles per zero code, 152 per active out-of-range miss, 186 per active zero-entry
miss, 134 per static hit, and 108 per static zero entry, before amortizing the
single column setup. These are static path costs, not predicted rope frames.

## Build and validation

The Makefile-owned normal six-ROM family completed and verified for Build 0439.
Canonical and gameplay-entry gates passed; the existing non-blocking phase-epoch
warning remained. The standard fixed 30-second Genesis NTSC MAME trace passed at
1,798 frames and wrote:

`states/traces/rastan_direct_video_test_build_0439_mame_30s_20261017_154726/`

Canonical artifact:

- path: `dist/rastan-direct/rastan_direct_video_test_build_0439.bin`
- size: 2,698,936 bytes
- SHA-256: `4d149b3cb5b37a61815aeff4767c479fece41168b279bf3e352326dd6ef4438f`
- counter: 439
- opcode-replacement sites: 231

The unchanged deterministic rope benchmark produced:

- trials: `798 / 798 / 798`
- deterministic: **YES**
- median: 13,317.147 ms
- versus Build 0438 (`803`, 13,400.588 ms): **-5 frames**, **-83.441 ms**,
  **-0.623%**
- versus arcade silver standard (`771`, 12,850.000 ms): **+27 frames**,
  **+467.147 ms**

Evidence is under `states/traces/build0439_rope_attach_benchmark/`.

## Genesis-shape assessment

The resulting path is:

`arcade entering-column decision -> generated native four-row Plane-A records -> once-selected bounded residency LUT -> collision + native staging -> existing dirty-column/gathered VDP DMA publication`.

Remaining work is classified as follows:

- genuine arcade semantics: entering-column selection, scroll/source state, and
  collision meaning;
- necessary Genesis work: residency lookup, 32-row projection, staging, dirty
  marking, and gathered DMA;
- residual translation overhead: repeated per-cell destination/physical-row
  arithmetic and the surrounding nested 16-by-4 loop structure;
- optional future work: only separately proven address-progression improvements
  or the independently scoped Plane-B lookup optimization.

Neither optional area was changed here.

## Tool and evidence reuse

Reused without modification:

- `tools/mame/run_genesis_trace_wsl.sh` through the Makefile-owned fixed trace;
- `tools/mame/run_rope_attach_performance_benchmark.sh`;
- `tools/mame/scripts/rope_attach_performance_benchmark.lua`;
- `tools/mame/summarize_rope_attach_benchmark.py`;
- the existing generated native-metatile and background verification tools.

No new gameplay route, save state, trace script, runtime probe, or exploratory
instrumentation was created. Plane B optimization, HUD/framing, player-damage
work, Phase D, and Phase E were not started.
