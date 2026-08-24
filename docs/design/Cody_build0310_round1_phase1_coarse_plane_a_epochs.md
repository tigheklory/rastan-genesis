# Build 0310 Round-1 Phase-1 Coarse Plane-A Epochs

## Baseline and result

- Baseline: Build 0309.
- Baseline ROM: `dist/rastan-direct/rastan_direct_video_test_build_0309.bin`.
- Baseline SHA-256: `d7b7bd39ba6c79b276021d344a6a8935c08c8ff7b028c14e793eb9e2b66dbd02`.
- Produced ROM: `dist/rastan-direct/rastan_direct_video_test_build_0310.bin`.
- Build 0310 SHA-256: `998dc6efa7060572120a4b0055c0b71a5301e478718b6dfa17fa47398b7959e8`.
- Size: 1,658,552 bytes.
- Counter: 309 -> 310.
- Rolling ROM is byte-identical to the numbered Build 0310 artifact.

Build 0310 replaces the sixteen complete per-record Plane-A residency packages for
Round-1 Phase 1 with seven complete-residency semantic epochs. Plane B, native
PC090OJ sprite capacity, scrolling, collision, palette behavior, and gameplay logic
are unchanged.

## Architecture boundary

The retained semantic decision is the original arcade progression record at
`A5+0x13E`. The offline compiler maps that record to a graphics epoch. The native
helper installs the compiler-generated exact pattern vocabulary and direct Genesis
code-to-slot LUT for that epoch. This replaces the PC080SN-specific graphics tail;
the arcade still owns record and map progression.

This implementation adds no runtime allocator, search, LRU, miss-triggered DMA,
per-frame residency scan, or software PC080SN ring. It does not add virtual chip
RAM, C-window shadowing, or a generic chip-address translator. Existing native
name-table publication remains separate from the residency change and continues to
follow arcade progression.

## Frozen-data verification

The compiler reconstructed each record's exact physical pattern set from original
arcade ROM/data. It did not derive identities from screenshots or manually listed
codes. The requested unions independently reproduce as:

| Epoch | Records | Sections | Exact patterns | Capacity result |
|---|---:|---:|---:|---|
| A | 0-2 | 1-3 | 282 | PASS |
| B | 3 | 4 | 333 | PASS |
| C | 4-9 | 5-10 | 444 | PASS |
| D | 10 | 11 | 368 | PASS |
| E | 11 | 12 | 483 | PASS |
| F | 12-14 | 13-15 | 433 | PASS |
| G | 15 | 16 | 349 | PASS |

All seven unions fit the 484-slot Plane-A interval, slots 855 through 1338.
Plane-A required drops are zero for every record and epoch.

### Exhaustive minimum proof

An exhaustive dynamic-programming search considered every contiguous partition of
records 0 through 15 whose complete union is at most 484 patterns. The minimum is
seven epochs. No six-epoch partition exists. Exactly two minimum segmentations were
found:

1. `0-2 / 3 / 4-8 / 9-10 / 11 / 12-14 / 15`
2. `0-2 / 3 / 4-9 / 10 / 11 / 12-14 / 15`

Build 0310 selects the second segmentation. It matches the requested visual and
semantic boundaries: Sections 4, 11, and 12 carry major waterfall/special
vocabularies, while Section 16 is the distinct fortress exterior/final pre-castle
approach.

The bridge correction is preserved: the narrow bridge deck is in segments 9-10,
world columns 608-637. It contains 30 exact patterns, 15 already seen and 15 newly
introduced there. Section 16's 319 new patterns are not described as bridge
patterns.

## Transition metrics

The compiler verified the exact adjacent-epoch physical-identity overlap:

| Transition | Previous | Next | Shared/retained | Retired | New |
|---|---:|---:|---:|---:|---:|
| A -> B | 282 | 333 | 33 | 249 | 300 |
| B -> C | 333 | 444 | 38 | 295 | 406 |
| C -> D | 444 | 368 | 171 | 273 | 197 |
| D -> E | 368 | 483 | 197 | 171 | 286 |
| E -> F | 483 | 433 | 160 | 323 | 273 |
| F -> G | 433 | 349 | 30 | 403 | 319 |

Shared physical identities retain their slot where possible at each epoch
transition. This is deterministic offline construction, not a runtime cache.

## Runtime contract

The generated record-to-epoch table is:

`0,0,0,1,2,2,2,2,2,2,3,4,5,5,5,6`

`fg_boundary_install` resolves the requested record to an epoch. If that epoch is
already active, it updates only the semantic active record/variant and returns from
the residency operation before descriptor walking, interrupt masking, display-off,
LUT rebuild, remap, or pattern DMA. Therefore record transitions inside an epoch
have:

- Plane-A pattern DMA: 0.
- Plane-A eviction: 0.
- Plane-A slot reassignment/churn: 0.
- Plane-A residency package replacement: 0.
- Full LUT rebuild due to residency: 0.
- Display-off residency installer: 0.

The sixteen prior packages exposed fifteen record boundaries to residency reloads.
Build 0310 has six true epoch boundaries and removes these nine false boundaries:

- Section 1 -> 2.
- Section 2 -> 3.
- Section 5 -> 6.
- Section 6 -> 7.
- Section 7 -> 8.
- Section 8 -> 9.
- Section 9 -> 10.
- Section 13 -> 14.
- Section 14 -> 15.

The six remaining true transitions are before Sections 4, 5, 11, 12, 13, and 16.
Build 0310 intentionally does not implement no-black Strategy C; those transitions
may still display the existing bounded residency flash.

## Ownership and generated contract

- Plane B: unchanged fixed 854-pattern Level-1 vocabulary in slots 1-854.
- Plane-A residency: slots 855-1338, capacity 484.
- Native PC090OJ: unchanged base slot 1339, 49 16x16 cells / 196 patterns.
- Maximum owned pattern slot: 1535.
- Plane-A required drops: 0.
- Plane-B required drops: 0.
- Plane/sprite overlap: 0.
- Runtime allocator/search/LRU: absent.

Generated Build 0310 package data:

- `build/pc080sn_boundary/boundary_packages.bin`: 39,336 bytes, SHA-256
  `553889f37733ca13231659cbc72105a35020b306625fbde7510c4dc84ccae4bb`.
- `build/pc080sn_boundary/boundary_report.json`: 8,351 bytes, SHA-256
  `b3fb4b9c86c3117ed437fa352b8e93edc2ef1977a49ec57fcf685160a50fda7c`.
- `build/pc080sn_boundary/boundary_constants.inc`: 987 bytes, SHA-256
  `e63c677bb9d0f6bc2b09e41f7f9642df022001f0754bb21e00dacf7c87ad00fc`.

The seven-package representation shrinks generated package data by `0x5000` bytes
relative to Build 0309. Canonical complete Genesis coverage changes consistently
from `0x199EB8` to `0x194EB8`; the opcode-replacement count remains 227.

## Build-0309 crash-fix preservation

Build 0310 preserves:

- explicit `-m68000` assembly for `fg_tile_cache.s`;
- 68000-safe large-offset pointer construction;
- generated package alignment and range assertions;
- runtime record, descriptor, package, map, and fixed-B span guards;
- the required READY-to-gameplay gate.

No bypass, NOP workaround, RTS bypass, fallback graphics, slot-0 substitution, or
drop path was introduced.

## Validation

### Static compiler validation

PASS. The compiler verifies the exhaustive minimum partition, all seven exact
unions, every record's containment in its epoch, stable legal slot ownership,
zero Plane-A and Plane-B drops, no B/sprite overlap, no duplicate physical
ownership, and no within-epoch pattern operation.

### Canonical gate

PASS (`GATE_PASS`). Opcode replacement count is 227 and complete Genesis coverage
is `0x194EB8` in both postpatch and independent verification.

### Gameplay-entry gate

PASS: `states/traces/build0310_gameplay_entry_gate_20260823_161702/`.

- External frames: 563.
- Credit, Start, READY, fixed-B install, record-0 Plane-A install, gameplay entry,
  and player control: PASS.
- Post-entry frames: 240.
- Observed active record/epoch: record 1 / epoch A.
- Address errors: 0.
- Bus errors: 0.
- Illegal instructions: 0.
- Crash-handler entries: 0.
- Stack valid: YES.

### Seven-epoch runtime gate

PASS: `states/traces/build0310_phase1_epoch_gate_20260823_161704/`.

The deterministic project-owned MAME Genesis harness first reaches gameplay
normally, then invokes the real production `fg_boundary_install` boundary for
representative records 0, 3, 4, 10, 11, 12, and 15. It validates the complete
active Plane-A LUT against every compiler-generated pair and all 854 fixed Plane-B
LUT entries.

| Epoch | Probe record | Required patterns | Full A LUT | Full fixed B LUT |
|---|---:|---:|---|---|
| A | 0 | 282 | PASS | PASS |
| B | 3 | 333 | PASS | PASS |
| C | 4 | 444 | PASS | PASS |
| D | 10 | 368 | PASS | PASS |
| E | 11 | 483 | PASS | PASS |
| F | 12 | 433 | PASS | PASS |
| G | 15 | 349 | PASS | PASS |

Epoch A additionally reinvokes record 0 while A is already active. Residency and
pattern-DMA counters remain at one, proving the same-epoch call performs no second
package install or pattern DMA. All seven runs report zero exceptions and valid
stack state.

### Frontend smoke

PASS: `states/traces/rastan_direct_video_test_build_0310_mame_30s_20260823_161715/`.
The standard MAME Genesis smoke ran 1,798 frames and reported no unique unmapped
memory address. Final PC was `0x0739E4`; SP was `0x00FEFF6A`.

## Files changed for Build 0310

- `tools/translation/compile_pc080sn_genesis.py`
- `apps/rastan-direct/src/fg_tile_cache.s`
- `apps/rastan-direct/Makefile`
- `tools/mame/run_build0310_epoch_gate.sh`
- `tools/mame/scripts/build0310_epoch_gate.lua`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `docs/design/Cody_build0310_round1_phase1_coarse_plane_a_epochs.md`
- `AGENTS_LOG.md`
- Makefile-generated build, manifest, trace, and ROM outputs.

The working tree already contains unrelated in-progress and generated changes from
earlier tasks. They were not reverted or attributed to Build 0310.

## User verification

1. Start Round 1 and verify Plane B remains good.
2. Progress through Sections 1-3 and confirm no residency flash between them.
3. Observe the Section 4 waterfall transition.
4. Progress through Sections 5-10 and confirm no residency flash within the span.
5. Observe the Section 11 and Section 12 transitions.
6. Progress through Sections 13-15 and confirm no residency flash within the span.
7. Observe the Section 16 fortress exterior/final-approach transition.
8. Report any of the six true transition flashes and any Plane-A pattern corruption.
9. Treat known scrolling/map-position issues as separate unless clearly caused by
   residency.

## Next boundary

Build 0311 may remove black frames at only the six true epoch transitions using a
bounded deterministic prepare/commit scheme. Build 0310 intentionally does not
pre-implement that optimization.
