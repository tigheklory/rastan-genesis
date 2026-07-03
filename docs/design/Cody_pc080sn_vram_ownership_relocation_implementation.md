# Cody - Phase 1 PC080SN VRAM Ownership Relocation

**Date:** 2026-07-02  
**Type:** Narrow generator/data relocation + build/evidence  
**Build produced:** Build 0131  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0131.bin`  
**SHA256:** `da5c4492602e643679df4a3fee176eb531ccd2ab64023edf097066dfc921bd7f`  
**Baseline:** Build 0130, SHA `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`  
**Scope:** Move PC080SN cache-B ownership from Genesis VRAM tile slots `1280..1439` to `1344..1503`, leaving PC090OJ sprite tile slots `1024..1343` exclusive. No PC090OJ sprite cache implementation, no PC090OJ logic edits, no scene loader edits, no tilemap runtime logic edits.

## Phase 0

Classification: **EXTENDING** OPEN-024 / OPEN-001 with a narrow generator/data relocation. Relevant priors loaded: KF-010, KF-011, KF-014, KF-021, KF-026, KF-032, KF-036, plus OPEN-001 and OPEN-024 context. High rediscovery hazard: the PC080SN cache-B overlap with the intended PC090OJ sprite tile slot range.

Primary design loaded: `docs/design/Andy_pc080sn_pc090oj_vram_ownership_design.md`.

No contradiction detected. Address-map discipline was preserved; no arithmetic arcade-to-Genesis mapping was used as proof. This task does not touch OPEN-015.

## Implementation

Changed exactly one source constant in `tools/translation/precompute_pc080sn_tile_lut.py`:

```python
TILE_CACHE_BASE_B = 1344
```

`TILE_CACHE_SIZE_B` remains `160`, so the new PC080SN cache-B range is `1344..1503`. The PC080SN cache-A range remains `0..1003`. This leaves the PC090OJ sprite-reserved range `1024..1343` untouched by PC080SN generated assignments.

No edits were made to:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/scene_load.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `specs/rastan_direct_remap.json`

## Regeneration

Command sequence:

```bash
source tools/setup_env.sh && python3 tools/build_rastan_regions.py --variant world_rev1 && python3 tools/translation/precompute_pc080sn_tile_lut.py
```

Generator output:

- Title unique tiles: `845`
- Gameplay unique tiles: `829`
- End-round unique tiles: `1067`
- Total unique tile indices: `2330`
- VRAM max scene usage: `1067 / 1164`
- Disjoint range check: **PASS**

Generated artifacts compared against the Build 0130 baseline under `states/traces/pc080sn_vram_ownership_relocation_build0131_20260702_202000/`.

Changed generated artifacts:

- `build/pc080sn_tile_vram_lut.bin`
- `build/pc080sn_tile_vram_lut_words.inc`
- `build/pc080sn_scene_preload_endround.bin`

Unchanged generated artifacts:

- `build/pc080sn_scene_preload_title.bin`
- `build/pc080sn_scene_preload_gameplay.bin`
- `build/pc080sn_vram_preload.bin`
- `build/pc080sn_vram_preload_words.inc`
- `build/pc080sn_source_scene_map.bin`
- `build/pc080sn_unique_tile_count.txt`

## Static Validation

Evidence files:

- `states/traces/pc080sn_vram_ownership_relocation_build0131_20260702_202000/static_validation.md`
- `states/traces/pc080sn_vram_ownership_relocation_build0131_20260702_202000/static_validation.json`
- `states/traces/pc080sn_vram_ownership_relocation_build0131_20260702_202000/generated_sha256.diff`

Manifest summary:

| Manifest | Entries | Destination ranges | Overlap `1024..1343` | Dest `>=1536` | Byte-identical to Build 0130 |
|---|---:|---|---:|---:|---|
| title | `845` | `0..844` | `0` | `0` | `True` |
| gameplay | `829` | `0..828` | `0` | `0` | `True` |
| endround | `1067` | `0..1003, 1344..1406` | `0` | `0` | `False` |
| vram_preload | `845` | `0..844` | `0` | `0` | `True` |

LUT summary:

- Entries: `16384`
- Nonzero entries: `2331`
- Assigned slot ranges: `1..1003, 1344..1406`
- Overlap with `1024..1343`: `0`
- Destinations `>=1536`: `0`
- Byte-identical to Build 0130: `False`

Note: the LUT summary reports nonzero assigned slots, so slot `0` is not visible in that nonzero-only range listing. The manifests confirm slot `0` remains used where expected.

Acceptance:

- PC080SN generated destinations are constrained to `0..1003` or `1344..1503`: **PASS**
- No PC080SN manifest destination overlaps the PC090OJ sprite range `1024..1343`: **PASS**
- No PC080SN manifest destination exceeds `1535`: **PASS**
- LUT contains no destination in `1024..1343`: **PASS**
- LUT contains no destination `>=1536`: **PASS**

## Build 0131

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

Build outputs:

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0131.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `da5c4492602e643679df4a3fee176eb531ccd2ab64023edf097066dfc921bd7f`
- Size: `1,561,724` bytes
- Numbered/rolling ROM byte-identical: **YES**
- Canonical gate: **GATE_PASS**
- `address_map.json` total covered bytes: `1561724` (`0x17D47C`)
- Patch manifest expected covered bytes: `0x17D47C`

No invariant source edits were required.

## Runtime Smoke Evidence

Evidence root:

`states/traces/pc080sn_vram_ownership_relocation_build0131_20260702_202000/`

Reduced runtime evidence:

- `runtime_capture_summary.md`
- `runtime_capture_summary.json`
- `build0131_runtime_contact_sheet.png`
- `no_input_runtime_capture.log`
- `coin_start_runtime_capture.log`

The no-input capture exited normally at frame `390`; the coin/start capture exited normally at frame `650`. No crash occurred in either MAME smoke run.

No-input representative frames:

| Frame | Label | State `%a5@(0/2/4)` | BG nz | FG nz | Sprite SAT nz | Emitted | Prod OOB |
|---:|---|---|---:|---:|---:|---:|---:|
| 60 | `early_no_input` | `0000/0001/0000` | 560 | 66 | 92 | 23 | 0 |
| 120 | `mid_no_input` | `0000/0001/0000` | 560 | 66 | 92 | 23 | 0 |
| 240 | `pre_story_window` | `0000/0001/0000` | 560 | 66 | 92 | 23 | 0 |
| 282 | `story_anchor` | `0000/0001/0002` | 168 | 146 | 92 | 23 | 0 |
| 369 | `late_no_input` | `0000/0001/0002` | 168 | 146 | 32 | 7 | 0 |

Coin/start representative frames:

| Frame | Label | State `%a5@(0/2/4)` | BG nz | FG nz | Sprite SAT nz | Emitted | Prod OOB |
|---:|---|---|---:|---:|---:|---:|---:|
| 340 | `pre_coin` | `0000/0001/0002` | 168 | 146 | 92 | 23 | 0 |
| 371 | `coin_accept_window` | `0001/0001/0000` | 168 | 72 | 68 | 23 | 0 |
| 411 | `prompt_window` | `0001/0001/0000` | 168 | 72 | 0 | 19 | 0 |
| 473 | `start_clear_window` | `0002/0002/0006` | 0 | 8 | 64 | 16 | 0 |
| 474 | `stale_redraw_window` | `0002/0002/0006` | 0 | 8 | 120 | 30 | 0 |
| 477 | `second_clear_window` | `0002/0002/0006` | 0 | 8 | 120 | 30 | 0 |
| 534 | `round_window` | `0002/0002/0007` | 0 | 11 | 118 | 29 | 0 |
| 620 | `late_coin_run` | `0002/0002/0007` | 0 | 11 | 125 | 32 | 0 |

Interpretation: the PC080SN relocation did not introduce a MAME crash in the sampled no-input or coin/start windows. The `round_window` sample is a useful smoke point for the start path, but this task does not claim full end-round gameplay coverage or PC090OJ sprite-cache correctness.

## Phase 2 Readiness

The intended Phase 2 PC090OJ sprite range `1024..1343` is now exclusive with respect to PC080SN generated tile-cache assignments. The Phase 2 sprite tile-DMA residency cache should be able to use that range without PC080SN preload/LUT collision.

This task did **not** implement Phase 2. It also did not change PC090OJ logic, SAT construction, sprite descriptors, scene loading, or tilemap runtime code.

## Open / Closed Issues Impact

- OPEN-024: advanced; the PC080SN side of the VRAM ownership split is relocated.
- OPEN-001: context; graphics bring-up remains active.
- OPEN-015: not touched.
- New issues opened: none.
- Issues closed: none.

## KNOWN_FINDINGS Impact

Option A: no `KNOWN_FINDINGS.md` update. This is an implementation/evidence step for a planned ownership split, not a new durable root-cause finding.

## STOP

STOP triggered: **NO**.
