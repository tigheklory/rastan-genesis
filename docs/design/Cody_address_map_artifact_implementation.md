# Cody — Address Map Artifact Implementation (Build 0029)

## 1. Summary
Implemented address-map artifact emission in `tools/translation/postpatch_startup_rom.py` for `rastan-direct`, producing `build/rastan-direct/address_map.json` with canonical segment coverage, mapping kinds, and invariants. Existing manifest output remained byte-for-byte unchanged.

## 2. Phase 1 Verification Results
- Phase 1 complete: YES
- All emission points identified: YES
- Coverage invariant confirmed: YES (with correction noted in section 8)
- Emission model understood: YES
- Safe to proceed: YES

Design doc verification highlights:
- Transformation classes listed: 19
- Mapping-affecting classes (emit segment records): 11
- Top-level artifact fields: `schema_version`, `build_inputs`, `genesis_rom_size_bytes`, `relocation_delta`, `arcade_source_start`, `arcade_source_end_exclusive`, `wrapper_region`, `segments`, `segment_coverage`, `shift_deltas`
- Segment-kind field sets matched §3.1 exactly.

Patcher state verification:
- `rom_path.write_bytes(rom_bytes)`: line 1688
- `manifest_path.write_text(...)`: line 1921
- Finalization pass executes between those calls.
- `shift_replacements` in `specs/rastan_direct_remap.json`: absent
- `rom_opcode_replace` in `specs/rastan_direct_remap.json`: present, count 0

## 3. Emission Model Confirmation
Confirmed and implemented as two-phase:
1. Raw segment records emitted at source transformation points as transformations execute.
2. Canonical interval assembly/carve/final validation done in finalization pass before artifact write.

No reconstruction from unrelated artifacts was used.

## 4. Files Modified
- `tools/translation/postpatch_startup_rom.py`
- `docs/design/Cody_address_map_artifact_implementation.md` (this report)
- `AGENTS_LOG.md` (append-only entry)

## 5. Emission Point Implementation (11 mapping-affecting transformations)
Implemented `_append_segment(...)` at these lines in `postpatch_startup_rom.py`:

1. `shift_replacements` (patched_site origin=shift_replacement): line 1036
2. `whole_maincpu_copy` (arcade_copy): line 1079
3. `copied_ranges` identity (arcade_copy): line 1130
4. `shim_jumps` (genesis_only tag=shim_jump): line 1303
5. `opcode_replace` (patched_site origin=opcode_replace): line 1391
6. `rom_opcode_replace` (genesis_only tag=rom_patch): line 1441
7. `palette_pre_conversion` (genesis_only tag=palette_table): line 1557
8. `workram_anchor` (genesis_only tag=workram_anchor): line 1586
9. `generated_stubs` normal/test (genesis_only tag=generated_stub): lines 1642, 1653
10. `preserved_genesis_vectors` restore (preserved_vectors): non-direct line 1109, direct line 1675
11. wrapper region (genesis_only tag=wrapper): line 1692

## 6. Finalization Pass Implementation Summary
Added helpers and finalizer:
- `_append_segment`, `_slice_segment`, `_overlay_segment`, `_merge_adjacent_segments`, `_validate_segment_keys`, `_finalize_address_map_segments`

Finalization flow:
- Start from emitted `arcade_copy` base intervals.
- Overlay `patched_site` segments.
- Overlay wrapper, then other `genesis_only`, then `preserved_vectors`.
- Fill uncovered intervals with `genesis_only` tag `padding`.
- Validate continuity/invariants.
- Emit canonical ordered `segments`.

Execution point:
- After `rom_path.write_bytes(...)`, before manifest write.
- Writes artifact via `manifest_path.with_name("address_map.json")`.

## 7. Invariant Enforcement
Enforced with `RuntimeError` on failure:
- Segment ordering and adjacency.
- First segment starts at `0x000000`.
- Last segment ends at ROM size.
- `size_bytes` matches segment bounds.
- No gaps / no overlaps.
- `segment_coverage.total_genesis_bytes_covered == genesis_rom_size_bytes`.
- `arcade_copy` identity-offset consistency.
- `patched_site` byte-length consistency.
- Wrapper lower-bound guard (`0x00070000`).
- Build-0029 checks:
  - `opcode_replace` patched_site count = 46
  - 1:1 key correspondence with `rewrite_log` entries where `kind=="opcode_replace"`
  - total coverage check uses observed Build 0029 ROM size (`0xFB7C4`), see section 8.

## 8. Validation Results
V1 Build verification:
- `source tools/setup_env.sh && make -C apps/rastan-direct`: PASS
- `build/rastan-direct/address_map.json`: exists

V2 schema/coverage:
- Top-level fields present: PASS
- `segment_coverage.total_genesis_bytes_covered = 1030084 (0xFB7C4)`
- `gaps = []`, `overlaps = []`
- `patched_site` segments = 46
- `segments[0].genesis_start = 0x000000`
- `segments[-1].genesis_end_exclusive = 0x0FB7C4` equals ROM size

V3 spot check (`arcade_start 0x055968`):
- `kind = patched_site`
- `genesis_start = 0x055B68`
- `original_bytes` matches spec entry
- `replacement_bytes` matches spec entry after symbol-token resolution

V4 spot check (`genesis_rom_offset 0x000100`):
- segment `kind = preserved_vectors`

V5 spot check (`genesis_rom_offset 0x00070000`):
- segment `kind = genesis_only`, `tag = wrapper`

V6 arcade_copy + identity_offset:
- `identity_offset` present and validated
- sample check: first arcade_copy `genesis_start == arcade_start + identity_offset` -> TRUE

V7 regression check:
- `build/rastan-direct/rastan_direct_patch_manifest.json` byte-for-byte identical to pre-implementation snapshot: PASS
- MAME 30s trace final PC (from run summary): `0x000010` (unmapped addresses: none).

Note on coverage constant in Andy design:
- Design doc states `1030084 bytes = 0xFB944`; this hex conversion is incorrect.
- Correct conversion is `1030084 = 0xFB7C4`.
- Implementation uses the mathematically correct value from built ROM size.

## 9. Manifest Regression Confirmation
Confirmed unchanged:
- pre: `/tmp/rastan_direct_patch_manifest.pre_impl.json`
- post: `build/rastan-direct/rastan_direct_patch_manifest.json`
- `cmp` exit code: 0
- SHA256 identical.

## 10. Next-Step Impact
`address_map.json` is now available as build output for rastan-direct and can be consumed by lookup tooling without deriving mappings from manifest rewrite logs.

## Post-Implementation Verification

* command run: YES
* exact output:
```text
total_covered: 0xfb7c4
gaps: []
overlaps: []
patched_site count: 46
arcade_copy count: 40
preserved_vectors count: 1
genesis_only count: 2
first segment start: 0x000000
last segment end: 0x0FB7C4
rom size: 0xfb7c4
```
* invariant table:

| Invariant | Required value | Observed value | Pass/Fail |
|---|---|---|---|
| total_covered | 0xFB7C4 | 0xfb7c4 | PASS |
| gaps | [] | [] | PASS |
| overlaps | [] | [] | PASS |
| patched_site count | 46 | 46 | PASS |
| first segment start | 0x000000 | 0x000000 | PASS |
| last segment end | must equal rom size | 0x0FB7C4 == 0xfb7c4 | PASS |

* all invariants pass: YES
