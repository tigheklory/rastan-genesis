# Cody - Build 0355 WRAM Ownership Repair

## Classification and baseline

- Task classification: **EXTENDING / ARCHITECTURE LANDING**.
- Input baseline: Build 0354 diagnostic baseline; counter 354.
- Output: Build 0355, the ownership-only comparison point.
- Architecture compliance: native Motorola 68000 runtime code; Python is used only for offline verification. No runtime C, shadow hardware device, fallback renderer, or gameplay-flow bypass was introduced.

## Prior findings and contradictions

The prior ownership audit correctly reported a structural defect in the linked Build 0354 image:

- `fg_boundary_active_lut` began at Genesis-WRAM `0x00FF619C`.
- Its complete legal 10,240-word range extended through Genesis-WRAM `0x00FFB19B`.
- The crash record claimed fixed Genesis-WRAM `0x00FF6800..0x00FF6863`.
- The physical collision therefore covered LUT codes `0x0332..0x0363`.
- The manually diverted interval was LUT codes `0x031A..0x034B`, so it did not describe the linked collision.

This task did not contradict an arcade-semantic finding. It confirmed that copied WRAM constants had become stale relative to linker placement. The old manual diversion was transitional implementation state, not a semantic contract.

## Root structural issue

Two independent structures claimed the same physical Genesis-WRAM:

1. `fg_boundary_active_lut` was linker allocated but logically treated as a dense 10,240-word array.
2. The crash handler used absolute `.equ` addresses at Genesis-WRAM `0x00FF6800..0x00FF6863`, outside linker ownership.
3. `fg_boundary_conflict_lut` diverted a copied code interval rather than deriving it from linked addresses.

This made the active LUT non-contiguous at the semantic level and still left part of the real physical overlap unprotected.

## Alternatives evaluated

- Retuning `FG_BOUNDARY_CONFLICT_CODE_FIRST/COUNT` was rejected. It would preserve the same stale-magic-constant failure mode.
- Generating a diversion interval from linked symbols was unnecessary once both owners could be linked disjointly.
- Linker-owning both structures and restoring one dense active LUT was selected. It directly enforces the invariant that independent structures cannot silently own the same bytes.

## Implemented repair

### Crash record

`apps/rastan-direct/src/crash_handler.s` now declares the crash record in `.bss.crash_record` and exports labels for every field plus `CRASH_RECORD_END`. The established field offsets and total 100-byte record layout are retained; only ownership changed from fixed absolute addresses to linker allocation.

Linked Build 0355 layout:

| Structure | Genesis-WRAM range | Size |
|---|---:|---:|
| Crash record | `0x00FF6180..0x00FF61E3` | 100 bytes |
| Alignment/free gap | `0x00FF61E4..0x00FF61FF` | 28 bytes |
| `fg_boundary_active_lut` | `0x00FF6200..0x00FFB1FF` | 20,480 bytes / 10,240 words |
| Next linked data | starts at `0x00FFB200` | disjoint |

### Active LUT

`apps/rastan-direct/src/fg_tile_cache.s` now indexes `fg_boundary_active_lut` as one contiguous dense array for every legal code. The alternate `fg_boundary_conflict_lut`, its address-selection branch, and its initialization loop were removed.

The corresponding obsolete constants and assertions were removed from:

- `tools/translation/compile_pc080sn_genesis.py`
- `tools/translation/verify_build0311_transition_retention.py`

No rendering rule, tile mapping, boundary package, selector, or gameplay semantic was changed.

## Ownership verification

`tools/translation/verify_native_wram_ownership.py` now consumes linked symbols rather than fixed crash addresses. It verifies:

- `CRASH_RECORD_BASE` through `CRASH_RECORD_END` is exactly 100 bytes;
- the complete dense LUT has exactly 10,240 words;
- the two physical ranges do not overlap;
- no manual diversion is required.

Machine-readable results:

- `build/rastan-direct/build0355_wram_ownership.json`: `PASS`
- `build/rastan-direct/build0356_wram_ownership.json`: `PASS`

Both reports resolve the same disjoint layout and state `physical_overlap: false`, `manual_diversion_required: false`, and `crash_layout_valid: true`.

Verifier limitation: this focused invariant checks the complete linked crash-record and active-LUT owners. It does not claim to discover arbitrary computed pointers or undocumented fixed owners throughout all WRAM.

## Build 0355

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0355.bin`
- SHA-256: `df73ed51f3ef0abfc0a69667bf75231eedde5aa044115acf4de73d57ffce846e`
- Size: 1,666,744 bytes
- Counter after publication: 355
- Canonical result: `GATE_PASS`
- Mandatory Genesis NTSC MAME smoke: gameplay entry passed; 564 external frames completed without a fatal or unique unmapped-memory error.
- Static transition-retention gate: passed.
- Existing seven-epoch Phase-1 evaluation warning: still present and explicitly outside this ownership repair; it did not block numbered artifact preservation.

## Semantic impact

- Palette behavior: unchanged in Build 0355.
- Plane A mapping and publication: unchanged except that all legal active-LUT indices now use their intended contiguous storage.
- Plane B, sprite emission, residency, scroll, gameplay logic, and CRAM behavior: unchanged.
- Crash handler semantics and record fields: unchanged.
- Manual WRAM conflict diversion: retired.

## Result

The ownership defect is structurally repaired. The crash record and complete active LUT are linked, disjoint, machine-verified owners; no copied exclusion interval remains.

