# Build 0357 O(1) Sprite Reverse-Index Performance

## Scope and Baseline

- Agent: Cody
- Classification: EXTENDING / production performance experiment
- Accepted baseline: Build 0356
- Baseline ROM: `dist/rastan-direct/rastan_direct_video_test_build_0356.bin`
- Baseline SHA-256: `94afa3811b675e43a8e77b12e84b815cca4096617ffc3dd0be0951427fb8b760`
- Intended experiment ROM: Build 0357
- `NATIVE_CELLS`: 49 before and after
- Semantic change authorized: replace only the per-piece 49-slot residency search with an exact O(1) reverse index
- Plane A capacity, Model 4 partitioning, sprite decomposition, DPLC compilation, palette mapping, gameplay logic, collision, and `D00462`: unchanged

Build 0357 is the intended A/B experiment. During post-build verification, a direct Make target was invoked after diagnostic variants had regenerated symbols. The Makefile legitimately published and consumed Build 0358 rather than merely refreshing the rolling artifact. Build 0358 is preserved and is source-equivalent to Build 0357 except for generated build identity. The current counter is therefore 358 and the next valid number is 359. No numbered artifact was deleted, overwritten, renamed, or reused.

## Required Priors and Architecture Compliance

The task was performed after reviewing the required governance and the Build 0354-0356 timing/palette work, including the joint Build 0356 timing investigation and the current Model 4 architecture reports. This implementation preserves shared graphics residency. It does not attempt permanent owner VRAM assignment or any other part of the future hybrid architecture.

The retained semantic path remains:

`native sprite semantic tuple -> viewport/flip/blank validation -> graphics residency -> final Genesis SAT entry`

Only the graphics-residency hit lookup changed. No PC090OJ compatibility object store or scanner was reintroduced.

## Build 0356 Lookup Contract

### Graphics identity

`.Lnq_emit_entry` first computes `d3 & 0x1FFF`, rejects zero, rejects values at or above `0x1000`, and rejects codes marked blank by `pc090oj_blank_code_bitset`. It then reconstructs the resident key as:

- low 12 bits: legal PC090OJ graphics code `0x001..0xFFF`;
- bit 15: the existing HUD-white residency tag, when supplied by the caller.

The exact Build 0356 forward-table identities are therefore:

- normal: `0x0001..0x0FFF`;
- HUD-white: `0x8001..0x8FFF`.

The reverse index normalizes bit 15 to bit 12, producing exact 13-bit keys:

- normal: `0x0001..0x0FFF`;
- HUD-white: `0x1001..0x1FFF`.

`0x0000` is not a legal resident code and remains the empty forward-slot sentinel. Normalized `0x1000` is also unreachable because source code zero is rejected. `0xFF` is the reverse-index NOT_RESIDENT sentinel; valid reverse leaves are even forward-table byte offsets `0..96` for resident slots `0..48`.

### Build 0356 search behavior

The removed `.Lnq_lookup_loop` started at forward-table byte offset zero, compared the complete 16-bit resident key, advanced by two bytes, and searched all 49 slots. A hit used the first equal slot. A miss entered the unchanged `.Lnq_vloop` victim search.

### Writers and reset paths

Every source reference to `sprite_tile_resident_code` was audited. Its writers are:

1. Bootstrap clears the forward residency region beginning at `sprite_tile_resident_code`.
2. The miss/take path installs a newly selected resident code. Build 0357 routes this write through `.Lnq_reverse_replace` so both directions change together.
3. `.Lvcs_tile_dma` reaffirms the same forward slot/code after the corresponding pattern DMA completes. This does not change identity and therefore requires no reverse-map mutation.

No scene or phase path clears only the forward table. Residency persists across scene changes exactly as it did in Build 0356. The only full reset is bootstrap, immediately followed in Build 0357 by `pc090oj_reverse_index_init`.

### Related state

- `pc090oj_cell_used` is the per-finalizer referenced-slot bitmap. `.Lnq_cell_free` and `.Lnq_vloop` retain their Build 0356 victim semantics.
- `pc090oj_tile_dma_worklist` remains 12 entries of `{word slot, word code}`.
- `worklist_entry_for_slot` remains the VBlank reservation/cancellation bookkeeping table.
- `pc090oj_tile_dma_count` remains bounded at 12. A full queue follows the existing drop path and does not modify either residency direction.
- `.Lvcs_tile_dma` still uploads 64 words / 128 bytes per resident cell and then clears only reservation entries used in that interval.

### Uniqueness proof

Resident keys are unique under the complete reachable writer set:

1. Bootstrap initializes every forward slot empty and every reverse entry NOT_RESIDENT.
2. An insertion can occur only after an exact reverse miss.
3. `.Lnq_reverse_replace` removes the selected slot's old reverse key before installing the new forward and reverse entries.
4. Queue-full exits leave both maps unchanged.
5. The VBlank writer only reaffirms the already-installed slot/code pair.

Therefore a second slot cannot acquire an already resident exact key. Build 0356 first-match behavior is preserved because the reachable state has one canonical slot per key. The runtime invariant capture independently found no duplicate or inconsistent mapping.

## Reverse-Index Representation

The implementation uses a collision-free two-level direct map:

- 512-byte directory indexed by normalized key bits `12..4`;
- up to 49 live leaf pages, each 16 bytes and indexed by key bits `3..0`;
- one byte per leaf result, storing the forward-table byte offset `0,2,...,96`;
- `0xFF` for an absent directory page or absent key;
- 49 one-byte page reference counts;
- 49 one-byte free-page stack;
- one 16-bit free-page count.

Total WRAM cost is 1,396 bytes:

| Symbol | Genesis-WRAM range | Size |
|---|---:|---:|
| `sprite_tile_reverse_directory` | `0x00FFBF56..0x00FFC155` | 512 |
| `sprite_tile_reverse_pages` | `0x00FFC156..0x00FFC465` | 784 |
| `sprite_tile_reverse_page_refcount` | `0x00FFC466..0x00FFC496` | 49 |
| `sprite_tile_reverse_free_pages` | `0x00FFC497..0x00FFC4C7` | 49 |
| alignment | `0x00FFC4C8..0x00FFC4C7` | 0 |
| `sprite_tile_reverse_free_count` | `0x00FFC4C8..0x00FFC4C9` | 2 |

The owned aggregate range is `0x00FFBF56..0x00FFC4C9` inclusive. The immediately preceding allocation, `worklist_entry_for_slot`, ends at `0x00FFBF55`. The immediately following allocation, `pc090oj_dma_test_fired_flag`, starts at `0x00FFC4CA`. The current final linked BSS word is `genesistan_scene_a0_hi` at `0x00FFC55A`, ending at `0x00FFC55B`, leaving `0x3AA4` bytes before the top of Genesis WRAM. No overlap exists.

At most 49 distinct high-key groups can be represented by 49 resident slots, so 49 leaf pages are sufficient without collision handling. Released pages are returned only after their reference count reaches zero, at which point all 16 entries are NOT_RESIDENT.

### Hot path

The normal hit path performs:

1. fixed key normalization;
2. one directory byte read;
3. one leaf byte read;
4. direct branch to `.Lnq_hit`.

It performs no resident-slot loop, no hash collision loop, and no fallback linear scan.

### Replacement ordering

`.Lnq_reverse_replace` executes in this order:

1. read the selected forward slot's old code;
2. invalidate its old reverse leaf;
3. release the old page if its reference count becomes zero;
4. write the new authoritative forward code;
5. allocate or reuse the exact new page;
6. install the new reverse leaf and increment its reference count.

This helper runs synchronously during finalizer construction before the new SAT entry uses the slot. The existing worklist entry is created before replacement, matching Build 0356's order. Queue-full exits before replacement. VBlank pattern DMA then copies the selected code into that same physical slot and reaffirms the forward code.

## Static and Runtime Invariant Validation

The dedicated read-only Build 0357 invariant capture ran for 1,800 external frames. Validation deliberately excludes only the helper's short, intentional remove-old/write-forward/install-new critical section; all quiescent states are checked.

Results:

- validations: 1,765
- forward/reverse violations: 0
- first violation: NONE
- exact lookups: 33,709
- direct hits: 32,268
- misses: 1,441
- successful misses: 1,368
- queue-full drops: 73
- hit rate: 95.7251773%
- miss rate: 4.2748227%
- maximum resident slots observed: 43 of 49
- maximum live reverse pages observed: 12 of 49
- worklist samples: 1,390
- worklist median: 0 entries / 0 bytes
- worklist maximum: 12 entries / 1,536 bytes

The 73 queue-full events are the preserved Build 0356 bounded behavior, not an overflow beyond the 12-entry allocation. The observed maximum never exceeded 12.

Evidence: `states/traces/build0357_sprite_reverse_index_20260915/build0357_reverse_index_invariant.txt`.

## Build and Gate Results

### Intended Build 0357

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0357.bin`
- SHA-256: `7468ba61394dc807e06e5ad795f9aa69184a197d9453b4fcb443f2c59564b8a2`
- size: 1,666,744 bytes
- canonical gate: `GATE_PASS`
- gameplay-entry gate: PASS, 564 frames, credit/start/READY/gameplay/player-control observed, zero address errors, bus errors, illegal instructions, or crash-handler entries, valid SP
- 30-second Genesis NTSC MAME smoke: PASS, 1,798 frames, no unique unmapped-memory address
- seven-epoch publication gate: did not complete its known input/coverage sequence; this is recorded as a coverage limitation, not claimed as a pass

### Preserved incidental Build 0358

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0358.bin`
- SHA-256: `da0efda6c6e461be6e093fc8a73499df75dbe5567cdd511478b9eb6e3edd867c`
- size: 1,666,744 bytes
- source implementation: same reverse-index implementation as Build 0357; generated build identity differs
- canonical gate: `GATE_PASS`
- gameplay-entry gate: PASS with the same 564-frame contract and zero fatal counters
- 30-second Genesis NTSC MAME smoke: PASS, 1,798 frames, no unique unmapped-memory address

The current test-build counter is 358. The next valid test build is 359.

## Physical-Beam Timing Method

All reported durations use monotonic physical beam position from the established MAME method. Event endpoints are converted to dot positions using physical scanline and horizontal beam coordinates, with frame carry where required. No raw 8-bit V-counter modulo-262 arithmetic is used.

The Build 0356 comparison was re-reduced from the corrected physical-beam capture. That capture contains 383 complete gameplay chains and predates emitted-count markers, so its emitted count fields are zero/stale and no new Build 0356 slope is inferred from them. Build 0357 contains 1,139 complete gameplay chains with live emitted counts.

### Global observed medians

| Measurement | Build 0356 | Build 0357 | Delta |
|---|---:|---:|---:|
| publisher | 6.205 lines | 6.205 lines | effectively unchanged |
| native stage dispatch | 44.309 lines | 44.291 lines | -0.018 |
| native sprite finalizer | 137.910 lines | 91.242 lines | **-46.668 (-33.840%)** |
| full IRQ6/continuation chain | 310.494 lines | 286.010 lines | -24.484 |

The prompt cited an older approximately 334.652-line full-chain figure. The corrected Build 0356 physical-beam reduction used here measures 310.494 lines. The finalizer reference remains 137.910 lines.

### Controlled stationary interval

Comparable screen-frame range 407-699:

| Measurement | Build 0356, n=260 | Build 0357, n=268 |
|---|---:|---:|
| publisher | 6.203 | 6.205 |
| stage dispatch | 44.291 | 44.291 |
| back/enemy lane | 57.543 | 41.641 |
| finalizer | 109.234 | 91.242 |
| full chain | 272.612 | 257.073 |
| Build 0357 emitted entries | unavailable | 28 median |

Controlled finalizer saving: **17.992 lines / 16.471%**.

### Controlled horizontal interval

Comparable screen-frame range 700-897:

| Measurement | Build 0356, n=123 | Build 0357, n=143 |
|---|---:|---:|
| publisher | 6.205 | 6.221 |
| stage dispatch | 75.432 | 75.109 |
| back/enemy lane | 142.002 | 88.289 |
| finalizer | 197.514 | 143.111 |
| full chain | 410.117 | 356.889 |
| Build 0357 emitted entries | unavailable | 45 median |

Controlled finalizer saving: **54.404 lines / 27.544%**.

### Build 0357 vertical/jump interval

Screen frames 1000-1399, 315 complete chains:

- publisher: 7.807 lines median
- stage dispatch: 30.488 lines median
- back/enemy lane: 20.906 lines median
- finalizer: 70.508 lines median
- full chain: 335.463 lines median
- emitted entries: 20 median

The corrected Build 0356 run ended at screen frame 897 because it progressed more slowly, so there is no honest same-capture Build 0356 vertical/finalizer comparison. The prior Build 0356 publisher-only vertical representative was 17.924 total lines with 13.162 Plane A and 2.037 sprite lines; that is a different measurement domain and is not substituted for a full-chain A/B result.

### Build 0357 sprite-heavy interval

Top emitted-count decile (`>=46` entries), 119 chains:

- publisher: 10.992 lines median
- stage dispatch: 80.193 lines median
- back/enemy lane: 93.936 lines median
- finalizer: 157.504 lines median
- full chain: 395.184 lines median
- emitted entries: 48 median

The prior Build 0356 publisher-only sprite-heavy representative was 22.203 total lines, 18.039 sprite lines, and 16.152 pattern-DMA lines. It is retained as context but is not a matched full-chain comparison.

### Worst observed representatives

Build 0357's worst finalizer was screen frame 796:

- publisher: 6.184 lines
- stage dispatch: 80.227 lines
- back/enemy lane: 232.510 lines
- finalizer: 305.559 lines
- full chain: 500.549 lines
- emitted entries: 38

The worst full-chain outlier was screen frame 1646 at 1,802.594 lines, but its finalizer was only 56.213 lines with 12 emitted entries. It is an externally delayed continuation/outlier, not the reverse-index worst workload and is not used to estimate residency cost.

### Emitted-entry scaling

For 1,139 Build 0357 gameplay chains:

- finalizer/emitted-count correlation: 0.909359
- fitted finalizer slope: 1,520.408 dots / **3.116 physical lines per emitted entry**
- prior Build 0356 representative estimate: approximately 1,751 dots / 3.588 lines per entry
- indicative slope reduction: approximately 0.472 lines / 13.2%

The slope comparison is supporting evidence rather than a controlled regression because the Build 0356 count markers were unavailable in the corrected capture. The controlled stationary and horizontal medians are the stronger A/B results.

### One-frame completion question

- Build 0356: 113 of 383 complete gameplay chains below 262 lines, 29.50%
- Build 0357: 471 of 1,139 below 262 lines, 41.35%

Therefore the full gameplay chain does **not usually** complete inside one 262-line Genesis frame; fewer than half of observed Build 0357 chains do. The rate improved by 11.85 percentage points, but the one-frame threshold is not yet the majority case.

## Correctness Coverage

### Proven by automation

- stationary gameplay execution: PASS
- horizontal movement and scrolling execution: PASS
- vertical movement/jumping execution: PASS
- gameplay entry and player control: PASS
- forward/reverse residency coherence: PASS, zero violations
- resident-slot uniqueness: PASS in all validated quiescent states
- worklist capacity: PASS, maximum 12
- new address/bus/illegal/crash failure: none observed
- unique unmapped memory address: none observed
- new structural SAT/residency corruption detectable by the invariant harness: none observed

### Coverage limits

- Lizardman: normal early Stage 1 execution was exercised, but color and exact art remain USER MUST VERIFY visually.
- Large Bat: NOT REPRODUCED in the bounded automated capture.
- Flying Demon: NOT REPRODUCED.
- Hurry-up/Small-Bat swarm: NOT REPRODUCED.
- Items/projectiles/effects: not independently forced or visually classified.
- New palette corruption: none structurally indicated; USER MUST VERIFY visually.
- New SAT corruption/flicker: none structurally indicated; USER MUST VERIFY visually.
- `D00462`: UNCHANGED and not investigated.

No claim is made for an actor that the bounded capture did not reach.

## Answer to the Primary Performance Question

Replacing the 49-slot per-piece linear search with the exact O(1) reverse index removes:

- **46.668 physical scanlines / 33.840%** from the global observed median native sprite finalizer (`137.910 -> 91.242`);
- **17.992 lines / 16.471%** in the controlled stationary interval;
- **54.404 lines / 27.544%** in the controlled horizontal interval.

Publisher and stage-dispatch medians remain effectively unchanged in the global comparison, which localizes the measured reduction to the intended native finalizer/residency boundary. The full-chain median improves but remains above one physical frame globally.

## A-13 Impact

Status: **PARTIALLY RESOLVED**.

The controlled Build 0356-to-0357 delta isolates a substantial portion of the per-emitted-entry resident workload: removing the 49-way exact search cuts the finalizer median by 33.84% globally and 16.47-27.54% in controlled overlap intervals. It does not decompose the remaining coordinate, blank/bounds, SAT composition, lane setup, or miss/replacement costs. Additional instrumentation is still needed only if A-13 requires those residual components separated.

## Deferred Future Optimization

Genesis-native actor-frame recomposition into larger hardware sprites is recorded as a future offline optimization. It may reduce SAT entries and per-piece CPU cost, but it can increase pattern use through transparent rectangular padding or duplication. It was not designed or implemented here.

## Files and Evidence

Production source changed by this task:

- `apps/rastan-direct/src/boot/boot.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`

Documentation changed by this task:

- `docs/design/Cody_build0357_sprite_reverse_index_performance.md`
- `AGENTS_LOG.md`

Makefile-generated tracked outputs changed during Builds 0357-0358:

- `apps/rastan-direct/out/boot.o`
- `apps/rastan-direct/out/crash_build.inc`
- `apps/rastan-direct/out/diag_patch_manifest.json`
- `apps/rastan-direct/out/dma.o`
- `apps/rastan-direct/out/do_patch_manifest.json`
- `apps/rastan-direct/out/palette_hooks.o`
- `apps/rastan-direct/out/pc090oj_config.inc`
- `apps/rastan-direct/out/pc090oj_hooks.o`
- `apps/rastan-direct/out/rastan_direct_video_test.elf`
- `apps/rastan-direct/out/score_patch_manifest.json`
- `apps/rastan-direct/out/symbol.txt`
- `apps/rastan-direct/out/vdp_comm.o`
- `build/genesis_postpatch.disasm.txt`
- `build/mame/home/genesistrace/genesis_exec_trace.log`
- `build/rastan-direct/build_counter.txt`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- `build/rom_inventory.json`

Primary trace evidence:

- `states/traces/build0357_sprite_reverse_index_20260915/`
- `states/traces/build0357_gameplay_entry_gate_20260915_203823/`
- `states/traces/build0358_gameplay_entry_gate_20260915_203932/`
- `states/traces/rastan_direct_video_test_build_0357_mame_30s_20260915_203826/`
- `states/traces/rastan_direct_video_test_build_0358_mame_30s_20260915_203935/`

Pre-existing unrelated dirty and untracked files were not modified or removed as part of this implementation.

## Project State

- Model 4 hybrid direction: unchanged
- `NATIVE_CELLS`: 49
- Plane A capacity: unchanged
- animation-frame extraction: deferred
- DPLC compiler: deferred
- Palette Composer expansion: deferred
- `D00462`: separate and unchanged
- `docs/design/joint_build0356_frame_timing_investigation/FINAL_CONSENSUS.md`: unmodified; SHA-256 remains `c251d66d2a2cfb2cb07d1e7d72e6621de06759c70ae4f96a495fa68a35791b18`
- current test-build counter: 358
- next valid test build: 359

## Conclusion

The experiment is complete. The exact O(1) reverse index preserves the 49-cell shared-pool identity, bounded miss path, 12-entry DMA worklist, and replacement policy while eliminating the normal-hit resident-slot scan. The global finalizer median falls by 46.668 physical lines (33.840%), with zero observed map-coherence violations. Visual acceptance for actor families not reproduced by automation remains with the user; no complete Model 4 work was mixed into this build.
