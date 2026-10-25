# Cody Build 0502 — Selector-1 castle map candidate (upper-route proof pending)

**Agent / task:** Cody, `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0002`  
**Baseline:** Build 0500, not accepted, source `ef02c3643fc30654335ef3bc427ddf9ccca76a1c`  
**Candidate:** Build 0502, **NOT ACCEPTED**  
**Exact ROM-producing source:** `e8652fc0200ea3adb60d5c268e8295f1e4a935c2`

## Artifact

- Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0502.bin`
- SHA-256: `69c20a117af330f0dfbc9fd8ebbb0231a468610bfb9f939ec38f62e2af613529`
- Size: 3,399,352 bytes
- Counter: 0500 -> 0501 -> 0502. Build 0501 was a failed row-only diagnostic candidate; Build 0502 is the current candidate.
- R1-S2 variant: `dist/rastan-direct/rastan_direct_video_test_build_0502_S1-2.bin`, SHA-256 `91f74f66be29321c80b6707f215e7942bad4f1861e2e5a36d055032536b8750b`
- R2-S2 variant: `dist/rastan-direct/rastan_direct_video_test_build_0502_S2-2.bin`, SHA-256 `6dd609776cc6b97eab29adc67b6ac85e23f9a53e4e596a44c0770b97694fb0d3`
- All 18 `_S1-1` through `_S6-3` variants were generated and passed the established one-selector-byte gate.
- Canonical, gameplay-entry, seven-epoch, boot, and automatic 30-second Genesis NTSC gates passed. The manifest records 228 opcode-replacement sites, canonical coverage delta zero.

## Independent arcade derivation

The selector byte in the stream beginning at original `0x050F6B` selects the arcade scroll producer. Selector 0 is horizontal. Selector 1 is the reverse vertical producer; selector 2 is its forward counterpart.

The exact selector-1 mapping is not a whole-image 90-degree rotation. Original routines `0x050420`, `0x055A14`, `0x055696`, and `0x055990` establish this mapping for a source cell:

```text
source row    = 4*block_row + inner_row
source column = 4*block_column + inner_column

destination row    = 4*(15-block_column) + inner_row
destination column = 4*block_row + inner_column
```

It is a transpose plus reversal of the 4x4 **metatile-block** axes while preserving the inner 4x4 cell orientation. Selector 1's destination row is `63-(group*4+strip)`; its complemented strip selects the source row within a metatile and is not the destination row. Selector 2 uses `group*4+strip`.

The canonical offline interface is now:

- `tools/audit_round1_phase1_plane_a.py::arcade_plane_a_destination()`
- `tools/audit_round1_phase1_plane_a.py::reconstruct_segment(..., selector=...)`
- `tools/graphics_optimizer/analyze_graphics.py::decode_plane_a()`
- `tools/translation/compile_pc080sn_genesis.py::decode_record_selector()` and selector-aware `record_map()`

This applies to R1-S2 records 17 and 21 and R2-S2 records 43 and 44. Selector-0 records retain identity.

## Native producer correction

The retained arcade selector-1/2 routine already rebuilds sixteen exact descriptor pointers in `A5+0x1040` and passes them to original `0x055990` in destination column-block order. The native helper loaded each pointer and then discarded it, reconstructing a descriptor with selector-0-style logical coordinates and a native ring-front heuristic.

Build 0502 consumes the exact rebuilt pointer directly, maps its descriptor to the maintained native metatile record, and publishes the four independent visual/collision subcells. It also restores the arcade selector-1 destination-row expression. Visual and collision output therefore share the same retained arcade semantic producer.

Semantic cut: retained arcade record/selector/strip/group state and rebuilt descriptor pointers remain authoritative; the native helper emits final Genesis Plane-A words and the retained gameplay collision side effect. The retired tail remains the PC080SN C-window/name-RAM write path. No framebuffer, PC080SN shadow, collision bypass, gameplay shortcut, NOP, RTS bypass, fallback, or per-frame map transformation was added.

Legacy code intentionally remaining: the retained arcade scene, scroll, player movement, collision decision, and descriptor-rebuild logic. No additional legacy chip execution was introduced or removed.

## Causal result and correction to the prior hypothesis

Andy's editor finding is valid for the selector-unaware offline corpus, but the stronger claim that the known `FG Y ~= 0x0166` automated stop itself proves the Genesis map/collision defect is false.

The maintained direct-start route reaches player `X/Y=0x0122/0x003E`, state 4, foreground `X/Y=0x0160/0x0166`, then reads collision words 1 and 2 at the head probes. Build 0502 still reaches that state. Crucially, the retained **original arcade MAME** direct-start trace reaches the same `X=0x0122`, selector 1, `FG Y=0x0167` state and reads the same words 1 and 2 from original collision addresses `0x10E9F6/0x10EA74`. It also stops under Up-only input. That early ceiling is therefore not a Genesis divergence and is not a valid upper-route success oracle.

The prior human third-chain trace is a later ring epoch: it begins at `FG Y=0x01DA`, player `X=0x0121`, and continues through wrap to `0x0028` while strip/group reaches `2/1`. Pairing it with the direct-start `0x0100 -> 0x0166`, group `0/0` ceiling conflates two different route epochs. The user screenshot also does not match the automated ceiling frame: the captured automated ceiling image is retained at `states/traces/rg0002_build0502_s1_2_upper_left_experiment/climb_blocked.png`.

Consequently, Build 0502 has a proven selector-aware map producer, but the required claim that it reaches the user's authentic upper route is **not yet proven**. This report does not call the climb defect closed.

## Validation

Static selector gate:

- 128 arcade destination-row cases pass.
- 160 rebuilt-pointer/order/boundary cases pass.
- 1,869,856 descriptor/subcell/context cases pass.
- 4,096 row/top residency cases pass; collision is always produced and visual output is resident-only.

Original arcade MAME versus Genesis USA/NTSC MAME initial spatial gate:

| Variant | Active record/selector | Plane A | Plane B | Collision | Result |
|---|---:|---:|---:|---:|---|
| R1-S1 | 1 / 0 | 0 mismatches | 0 | 0 | PASS |
| R1-S2 | 17 / 1 | 0 mismatches | 0 | 0 | PASS |
| R1-S3 | 23 / 7 | 0 mismatches | 0 | 0 | PASS |
| R2-S1 | 24 / 0 | 0 mismatches | 0 | 0 | PASS |
| R2-S2 | 40 / 0 | 0 mismatches | 0 | 0 | PASS |
| R2-S3 | 46 / 7 | 0 mismatches | 0 | 0 | PASS |

Each comparison also has zero orientation, LUT, and staged-to-final-VRAM mismatches after the established 95 Plane-A HUD/off-screen exclusions. This preserves Build 0500's 64-row identity/live-window correction and selector-0 layouts.

Performance regression check on Genesis USA/NTSC MAME using Build 0502 `_invincible`:

```text
795 / 795 / 795 frames
median 13,267.083 ms
deterministic YES
```

This equals Build 0500 and accepted Build 0472 on the established route; it is not a universal CPU-cycle measurement.

## Files and coordination

ROM-producing commits:

- `e0601a26` — selector-aware offline decoder and selector-1 destination-row correction.
- `e8652fc0200ea3adb60d5c268e8295f1e4a935c2` — exact rebuilt-pointer consumption; exact Build 0502 source.

Production/source tools changed:

- `apps/rastan-direct/src/tilemap_hooks.s`
- `tools/audit_round1_phase1_plane_a.py`
- `tools/graphics_optimizer/analyze_graphics.py`
- `tools/translation/compile_pc080sn_genesis.py`
- selector/native verification scripts
- maintained bounded climb diagnostic

Palette Composer, palette decisions, palette identities, and authored mappings were not modified. Andy should regenerate the existing Layer-A corpus, especially records 17, 21, 43, and 44, with:

```text
python3 tools/graphics_editor/gen_subround_layera_corpus.py
```

The regeneration should consume the canonical selector-aware decoder above; palette identities require no migration from this coordinate change.

Concurrent audio decision-profile changes and Andy's Palette Composer work were preserved and excluded from these commits.

## Unresolved limitation and USER MUST VERIFY

The automated route supplied for this task reaches an arcade-authentic earlier ceiling, not the later user-reported upper-chain epoch. A deterministic input fixture for the exact screenshot route does not exist, and no save state accompanies the report. Therefore Tighe must test Build 0502 `_S1-2` on the exact route shown in the screenshots and report:

1. whether Rastan passes the previously reported on-screen stopping point;
2. whether the camera enters each subsequent vertical window and reaches the authentic upper route;
3. whether solid walls/floors, chain attachment/detachment, and stage boundaries remain correct;
4. whether R1-S1, R1-S3, R2-S1, R2-S2, and R2-S3 remain visually and collision-correct.

If the exact route still fails, capture player X/Y, foreground X/Y, strip/group, and a paused frame at that user-visible stop. The maintained probe now records the required movement and collision decisions without altering gameplay.

## STOP status

- Selector-aware arcade map construction: **IMPLEMENTED AND VALIDATED**.
- Records 17/21/43/44 offline convention: **CORRECTED; Andy corpus regeneration pending**.
- Performance regression: **NONE observed**.
- Authentic upper-route traversal: **NOT PROVEN; hardware/user-route verification required**.
- Build 0502 accepted: **NO**.
- Task completion: **PARTIAL — do not close the climb defect**.

