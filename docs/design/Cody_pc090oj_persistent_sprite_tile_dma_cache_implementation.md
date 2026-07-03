# Cody - PC090OJ Persistent Sprite Tile-DMA Cache Implementation Attempt

**Date:** 2026-07-02  
**Type:** Gate analysis / implementation STOP  
**Baseline:** Build 0130 / rolling ROM  
**Baseline SHA256:** `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`  
**Requested next build:** Build 0131  
**Evidence directory:** `states/traces/pc090oj_persistent_sprite_tile_dma_cache_build0131_gate1_stop_20260702_201213/`

## Phase 0

Classification: **EXTENDING** OPEN-024 / OPEN-001, continuing the PC090OJ sprite bring-up thread from Build 0130.

Read/loaded context:

- `RULES.md`
- `ARCHITECTURE.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- latest `AGENTS_LOG.md`
- `docs/design/Andy_pc090oj_persistent_sprite_tile_dma_cache_design.md`
- `docs/design/Andy_build0130_graphics_timing_budget_analysis.md`
- `docs/design/Cody_build0129_vblank_status_ring_diagnostic.md`
- `docs/design/Cody_pc090oj_3b930_3b802_object_ram_faithful_implementation.md`
- `docs/design/Cody_genesis_sat_link_chain_termination_audit.md`

Relevant priors respected: KF-010, KF-011, KF-021, KF-026, KF-032, KF-036, and OPEN-024. OPEN-015 was not touched.

Architecture compliance: **PASS**. Arcade code remains the program; no Genesis-side behavior change was made.

## Gate 1 - Sprite VRAM Ownership

Requested sprite tile residency range: Genesis VRAM tile slots `1024..1343`, corresponding to byte range `0x8000..0xA7FF`.

### Result: FAIL / STOP

The proposed PC090OJ sprite tile residency range overlaps the current generated PC080SN tile preload/LUT ownership.

Scene preload manifest results:

| Manifest | Entries | Destination min/max | Overlap with `1024..1343` |
|---|---:|---:|---:|
| `build/pc080sn_scene_preload_title.bin` | `845` | `0..844` | `0` |
| `build/pc080sn_scene_preload_gameplay.bin` | `829` | `0..828` | `0` |
| `build/pc080sn_scene_preload_endround.bin` | `1067` | `0..1342` | `63` |
| `build/pc080sn_vram_preload.bin` | `845` | `0..844` | `0` |

The end-round manifest writes destination slots `1280..1342`, which are inside the requested sprite tile residency range.

`build/pc080sn_tile_vram_lut.bin` also maps `63` PC080SN tile entries into that same overlapping range:

- PC080SN tiles `10717..10779` (`0x29DD..0x2A1B`)
- Genesis tile slots `1280..1342`

Tooling source confirms this is not a parser artifact: `tools/translation/precompute_pc080sn_tile_lut.py` defines a second PC080SN tile cache band at `TILE_CACHE_BASE_B = 1280`, `TILE_CACHE_SIZE_B = 160`.

### Gate Interpretation

The current VRAM ownership model does **not** prove tile slots `1024..1343` are exclusively PC090OJ-owned. The per-SAT-slot residency cache would assume a sprite tile remains resident between frames, but PC080SN scene loading can legally overwrite part of the same range during the end-round scene.

Per the task directive, this overlap is a hard STOP before implementation.

## Gate 2 - Cache Cold Start

Not reached. Static inspection did show current boot code explicitly clears existing PC090OJ generated state and mirror state, which suggests a new cache would need explicit boot clear unless a broader BSS zeroing rule were proven. Because Gate 1 failed, no boot change was made.

## Implementation Status

No implementation was applied.

Specifically:

- `sprite_tile_resident_code` was not added.
- `.Lpc090oj_emit_slot` was not changed.
- `.Lvcs_tile_dma` was not changed.
- `boot.s` was not changed.
- No invariant was changed.
- No Build 0131 was produced.

## Required Follow-Up

A safe implementation needs an explicit VRAM ownership decision before the residency cache can exist. The next task should choose and prove one of these project-level directions before code changes:

- move the PC090OJ sprite tile residency range out of all PC080SN preload/LUT ranges;
- change the PC080SN scene allocator so it never assigns tiles inside the sprite range;
- define and prove an invalidation/ownership protocol when PC080SN scene load can overwrite sprite-resident tiles.

This task was not authorized to make that design decision.

## Evidence Artifacts

- `states/traces/pc090oj_persistent_sprite_tile_dma_cache_build0131_gate1_stop_20260702_201213/gate1_pc080sn_sprite_vram_overlap_analysis.md`
- `states/traces/pc090oj_persistent_sprite_tile_dma_cache_build0131_gate1_stop_20260702_201213/gate1_pc080sn_sprite_vram_overlap_analysis.json`

## Non-Actions

- Source changes: NO
- Spec changes: NO
- Tool changes: NO
- Makefile changes: NO
- ROM changes: NO
- Build run: NO
- Runtime probing: NO
- Bookmark cycle: NO
- Issue closure: NO

## OPEN / KNOWN_FINDINGS Impact

- OPEN-024: touched; remains open. The requested sprite tile-DMA residency cache is blocked by PC080SN/PC090OJ VRAM ownership overlap.
- OPEN-001: context only; remains open.
- OPEN-015: not touched.
- KNOWN_FINDINGS impact: Option A. This pass is a pre-implementation gate failure and does not establish a new runtime mechanism.

## STOP

STOP triggered: **YES**.

Reason: Gate 1 found PC080SN scene preload/LUT overlap with the requested PC090OJ sprite tile residency range. Implementation is not safely placeable under the prompt's rules.
