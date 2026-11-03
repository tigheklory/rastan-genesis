# Cody - Build 0303 Boundary Coherence and Castle Native Edge Publication

Date: 2026-08-21  
Classification: EXTENDING  
Baseline: Build 0302  
Produced candidate: Build 0303

## Outcome

Build 0303 retains the accepted Build-0302 boundary-loaded performance architecture and fixes the
three defects established by the independent forensic review:

1. packages now use graph-aware, cross-package stable slot assignment based on exact decoded
   pattern identity;
2. every package install atomically remaps and recommits both staged name tables before display is
   enabled;
3. event/reseed records 16 and 22 defer package selection until scene-fill completion, and the
   gameplay directional PC080SN family now publishes directly into native Plane-B staging.

No per-frame residency mechanism was added. There is no mark-live pass, residency hash, allocator,
LRU, eviction, plane scan, package selection, or miss-triggered load in normal frames.

## Phase 0

- Relevant priors: KF-010 (BG -> Plane B, FG -> Plane A), KF-014 (O(1) PC080SN LUT), KF-015
  (scroll convention), KF-032 (raw PC080SN writes route through Genesis staging), KF-037
  (replacement control-flow preservation), and the native-replacement policy in `RULES.md` section
  11 and `ARCHITECTURE.md`.
- Rediscovery hazard: HIGH for the already-proven stale-slot defect and raw directional writer;
  Andy's Build-0302 forensic review was accepted rather than repeated.
- Task classification: EXTENDING.
- Issues touched: the continuing PC080SN/native gameplay rendering effort; no issue was opened or
  closed.
- Contradiction of a CONFIRMED or STRONG finding: NONE.

## Evidence Inspected

- `docs/design/Andy_build_0302_independent_forensic_review.md`
- `docs/design/Cody_build_0302_boundary_loaded_graphics_experiment.md`
- `docs/design/Andy_pc080sn_plane_b_static_decoder.md`
- `tools/translation/compile_pc080sn_genesis.py`
- `apps/rastan-direct/src/fg_tile_cache.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `specs/rastan_direct_remap.json`
- `build/rastan-direct/address_map.json`
- `build/genesis_postpatch.disasm.txt`
- `build/pc080sn_boundary/boundary_report.json`
- `apps/rastan-direct/out/symbol.txt`

## Native Replacement Boundary

Semantic state retained:

- arcade Stage-1 record `a5+0x013E`;
- authoritative Plane-B Y `a5+0x10EE`;
- direction/gate word `a5+0x10D0`;
- camera accumulators and descriptor/source state at `a5+0x10EC..0x10FC`;
- the original tile code and attribute decisions.

Chip-specific tail removed from the gameplay directional caller:

`FUN_00055AD6 -> FUN_00055B28/FUN_00055B32/FUN_00055B3C/FUN_00055BB6 ->
FUN_00055C4A/FUN_00055C7A -> raw PC080SN C-window destination`.

Native realization:

`genesistan_pc080sn_directional_dispatch_native` preserves the gates, camera accumulation,
descriptor/source selection, and progression, then calls the existing O(1)-LUT Plane-B native cell
publisher. It creates final Genesis name words in `staged_bg_buffer` and marks the affected physical
row dirty. It contains no C-window cursor, software PC080SN RAM, or raw `0xC00000/0xC08000`
destination.

Transitional compatibility still present:

- copied historical arcade routine bodies remain in ROM but the gameplay call at arcade PC
  `0x05109C` no longer reaches them;
- the scene-fill path still calls the previously converted shared semantic writer at runtime PC
  `0x055D2C`, whose chip write sub-tail already jumps to native helpers. This is separate from the
  retired directional caller and was not broadened in this task;
- frontend/non-gameplay compatibility rendering remains outside this task.

## Stable Package Allocation

### Identity and graph

The compiler canonicalizes every decoded 8x8 pattern by its exact 32-byte pattern data. It found
2,708 distinct identities. Package assignment uses the legal runtime graph, not package file order:
self edges and all adjacent-record/Y-variant edges, totaling 1,354 legal transition edges.

For each package, predecessor votes prefer the same slot for a surviving identity. Same-Y
predecessors receive the strongest weight; other legal predecessors retain influence. Capacity is
still local to the active package: slots 64..1023, 960 slots. No slot is globally dedicated for the
whole stage.

### Package metrics

- records: 23
- packages: 170
- ordinary variants per record: 8
- vertical full-row records: 17 and 21
- exact identities: 2,708
- maximum package occupancy: 960 / 960
- packages with intentional Plane-B drops: 22
- maximum Plane-B drop count: 315
- maximum/total deliberate Plane-A drops: 0
- compiled package data: 1,402,544 bytes
- production trace dependencies: 0

### Representative transitions

| Transition | Build-0302 dense slots changing identity | Build-0303 slots changing identity | Shared identities retained in same slot | Patterns uploaded | Old slots blank after exact remap |
|---|---:|---:|---:|---:|---:|
| record 0 variant 0 -> record 1 variant 0 | 819 | 0 | 816 | 100 | 4 |
| record 1 variant 0 -> record 2 variant 0 | 882 | 110 | 806 | 154 | 110 |
| record 15 variant 0 -> record 16 variant 0 | 840 | 330 | 511 | 330 | 449 |
| record 21 variant 0 -> record 22 variant 0 | 778 | 16 | 622 | 198 | 156 |

`slots changing identity` includes slots whose old identity leaves residency; every shared identity
shown above stays in the same slot. Upload counts are the patterns that cannot reuse an identical
pattern already present in the same slot.

## Boundary Name-Table Coherence

Package data now includes `{slot, canonical_pattern_identity}` pairs. At a transition the runtime:

1. builds exact `new identity -> new slot` lookup data;
2. builds `old slot -> old identity -> new slot` translation data;
3. remaps all 2,048 final Genesis words in staged Plane A;
4. remaps all 2,048 final Genesis words in staged Plane B;
5. clears and installs the new direct `arcade code -> Genesis slot` LUT;
6. uploads only patterns not retained at the same slot;
7. DMA-commits the full staged Plane-B name table to VRAM `0xC000`;
8. DMA-commits the full staged Plane-A name table to VRAM `0xE000`;
9. activates the new record/variant/package state and re-enables display.

The transition executes with SR interrupt mask 7 and VDP register 1 set to display off. Display is
not re-enabled until pattern ownership and both hardware name tables are coherent.

Genesis name-word handling is exact:

- pattern index: `word & 0x07FF`;
- attributes: `word & 0xF800`;
- output: preserved attributes OR translated pattern index;
- identity absent from new package: translated pattern index 0 (defined blank), with the original
  priority/palette/H-flip/V-flip bits preserved.

The remap never allocates or loads a missing pattern. Intentional package misses remain blank and
continue to be distinguishable from the Build-0302 valid-but-wrong texture defect.

## Event and Reseed Timing

Ordinary progression remains at arcade PC `0x0558FE`, exactly mapped to runtime Genesis PC
`0x0559DE`. `fg_boundary_advance_segment` first performs the original increment of `a5+0x013E`, then
installs the new package for ordinary records.

For records 16 and 22, the generated semantic reseed mask is `0x00410000`. The progression helper
sets `fg_boundary_reseed_pending` and does not install a package. The exact scene-fill completion
return is replaced as follows:

| Owner | arcade PC | runtime Genesis PC | Build-0303 action |
|---|---:|---:|---|
| scene-fill completion | `0x050482` | `0x050682` | `jsr fg_boundary_install_post_reseed` at `0x072632`, then preserve original `rts` |

At this point the scene fill has established the post-event descriptor cursor, Plane-B Y, tm0, and
published scene state. `fg_boundary_install_post_reseed` consumes the pending byte once and selects
the package variant from post-reseed `a5+0x10EE`. There is no wrong-first/install-again sequence and
no frame-time polling.

## Directional Family Address Mapping

All correlations below are exact generated mappings from `address_map.json`.

| Semantic owner | arcade PC | copied runtime Genesis PC | Build-0303 owner |
|---|---:|---:|---|
| gameplay dispatcher call site | `0x05109C` | `0x0512A8` | `jsr 0x070A8A` |
| `FUN_00055AD6` dispatcher | `0x055AD6` | `0x055BB8` | retired from gameplay caller |
| `FUN_00055B28` direction arm | `0x055B28` | `0x055C0A` | bit-0 gate and `10B0 -> 10EE` in native dispatcher |
| `FUN_00055B32` direction arm | `0x055B32` | `0x055C14` | bit-1 gate and `10B0 -> 10EE` in native dispatcher |
| `FUN_00055B3C` forward arm | `0x055B3C` | `0x055C1E` | native forward accumulator and column publication |
| `FUN_00055BB6` reverse arm | `0x055BB6` | `0x055C98` | native reverse accumulator |
| `FUN_00055C4A` shared writer | `0x055C4A` | `0x055D2C` | descriptor/source native publication and progression |
| raw column loop | `0x055C7A` | `0x055D5C` | not reached by the converted gameplay caller |

The original copied `FUN_00055B3C` still contains its historical `add.l #0x00C00000` bytes at
runtime PC `0x055C66`, but the sole gameplay dispatch call now targets `0x070A8A`. Static disassembly
of helper range `0x070A8A..0x070C14` contains no `0xC00000`, `0xC08000`, or `0xC0ABE0` literal/store.
Thus `FUN_00055C4A`'s raw hardware tail is not reachable from this gameplay directional family.

The bounded audit found no remaining raw `0xC00000/0xC08000` gameplay store in this converted
semantic family. VDP data-port stores elsewhere are expected Genesis VDP commit operations, not
arcade PC080SN name-table destinations.

No NOP or RTS bypass was introduced. The `rts` at the scene-fill replacement is the original return
semantics expanded by a proper 2-to-8-byte shift-table replacement.

## Diagnostics

| Symbol | Genesis WRAM address |
|---|---:|
| `fg_boundary_name_remap_a` | `0x00FFB1E0` |
| `fg_boundary_name_remap_b` | `0x00FFB1E4` |
| `fg_boundary_name_unmapped_a` | `0x00FFB1E8` |
| `fg_boundary_name_unmapped_b` | `0x00FFB1EC` |
| `fg_boundary_slots_retained` | `0x00FFB1F0` |
| `fg_boundary_slots_reassigned` | `0x00FFB1F4` |
| `fg_boundary_reseed_pending` | `0x00FFB204` |

These counters are touched only during package transitions. They add no per-frame logging or scan.

## Validation

### Deterministic compiler validation

- all 1,354 legal graph transitions simulated: PASS;
- ordinary record 0/0 -> 1/0 coherence: PASS;
- second ordinary record 1/0 -> 2/0 coherence: PASS;
- event record 15/0 -> 16/0 coherence: PASS;
- later event/castle record 21/0 -> 22/0 coherence: PASS;
- exact old slot -> identity -> new slot invariant: PASS;
- absent identity -> slot 0 invariant: PASS;
- priority/palette/H/V mask `0xF800` preservation: PASS;
- only pattern mask `0x07FF` changes: PASS;
- simulated full Plane-A and Plane-B post-commit equality: PASS.

### Static runtime validation

- generated address mapping exact with no gaps/overlaps: PASS;
- patched scene-fill completion disassembles to `jsr 0x072632; rts`: PASS;
- patched gameplay directional call disassembles to `jsr 0x070A8A`: PASS;
- native directional helper contains no raw arcade PC080SN destination: PASS;
- native directional helper calls the existing final Plane-B staged publisher: PASS;
- Python syntax and JSON parsing: PASS;
- `git diff --check` for task production files: PASS.

### Build and emulator gate

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0303.bin`
- SHA-256: `8f92d69bbe9437e71b05b3cbb05867711440a14539e79c254fe9eb05ae56911c`
- size: 3,022,520 bytes
- counter: 302 -> 303
- rolling/numbered ROM equality: PASS (same SHA-256 and size)
- canonical gate: PASS
- opcode replacements: 227
- canonical covered bytes: `0x2E1EB8`
- mandatory MAME trace:
  `states/traces/rastan_direct_video_test_build_0303_mame_30s_20260821_221647/`
- MAME external frames: 1,798
- unique unmapped memory addresses: none
- average speed reported by MAME build run: 485.10%

The mandatory MAME smoke did not reach the castle vertical area or package transitions. Dynamic
castle and visual claims are therefore intentionally not made. Tighe must verify the former castle
path, boundary visuals, and retained gameplay speed.

## Production Changes

- `tools/translation/compile_pc080sn_genesis.py`: stable exact-identity graph allocator, transition
  metadata, and deterministic coherence tests.
- `apps/rastan-direct/src/fg_tile_cache.s`: boundary-only dual-plane remap, retained upload skip,
  atomic full name-table commits, event defer/install point, and counters.
- `apps/rastan-direct/src/tilemap_hooks.s`: complete native gameplay directional dispatcher and
  Plane-B semantic column publisher.
- `specs/rastan_direct_remap.json`: exact scene-fill post-reseed and gameplay directional call-site
  replacements plus required symbols.
- `tools/translation/postpatch_startup_rom.py` and
  `tools/translation/verify_canonical_rom.py`: canonical coverage updated from `0x26FEB8` to
  `0x2E1EB8` for the larger compiler-emitted package metadata.
- generated package data, objects, manifests, map, disassembly, numbered ROM, and MAME trace.

PC090OJ source, SAT logic, sprite palettes, and sprite residency were not changed.

## Remaining Limitations and User Test

Known and intentionally retained:

- 22 packages may render blank Plane-B cells because their conservative working sets exceed 960
  slots; the largest deliberate drop count is 315;
- missing package identities remain blank rather than triggering runtime loads;
- the smoke trace does not cover castle climbing;
- frontend/non-gameplay compatibility rendering remains transitional.

Focused Tighe test:

1. confirm Build-0302's speed improvement is retained;
2. walk across several Stage-1 progression/package boundaries and distinguish eliminated
   valid-but-wrong texture explosions from permitted blank misses;
3. exercise event/reseed boundaries around records 16 and 22 if reachable;
4. climb through the former castle `HW_ADDRESS 0x00C0ABE0` failure area and confirm directional
   edge tiles update without the raw PC080SN write freeze;
5. briefly confirm Rastan, lizard men, bats, Axe item, and frontend remain at Build-0302 behavior.

## Ledger Impact

- KNOWN_FINDINGS: no new indexed finding; this implements the accepted Build-0302 forensic result.
- OPEN_ISSUES: no new issue and none closed before user visual/castle verification.
- CLOSED_ISSUES: unchanged.

