# Build 0246 Native Plane A Vertical Source Proof

## Scope

Focused analysis only. No production source, remap specification, ROM, build, or counter changes were made.

The question for this checkpoint is whether Build 0246 has proven a native Plane A vertical source that can supply the 32-row Genesis resident ring without relying on PC080SN C-window/name-RAM shadows, projection, or generic compatibility state.

## Baseline

- Current build context: Build 0246 / counter 246.
- Build 0246 ROM previously produced: `dist/rastan-direct/rastan_direct_video_test_build_0246.bin`.
- Build 0246 SHA from AGENTS_LOG: `52919fe447698baf309350217d83ad972d474b96b8f9f7fb361d365c1d97d83e`.
- Task classification: analysis-only continuation of native PC080SN Plane A migration / OPEN-001.

## Inputs Read

- `docs/design/Cody_build0246_plane_a_audit_corrections.md`
- `docs/design/Andy_build0246_initial_plane_a_fill_audit.md`
- `docs/design/Andy_plane_a_selector0_logical_coordinate_proof.md`
- `docs/design/Andy_plane_a_semantic_cut_contract.md`
- `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`
- `docs/arcade_reference/pc080sn/gameplay_control.c`
- `docs/arcade_reference/pc080sn/core_publishers.c`
- `docs/arcade_reference/pc080sn/map_stream_format.md`
- `build/rastan-direct/address_map.json`
- `specs/rastan_direct_remap.json`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- Existing traces under `states/traces/build0245_plane_a_review_20260730_150627/`, `states/traces/build0244_native_selector12_implementation_20260729_131809/`, and `states/traces/rastan_direct_video_test_build_0246_mame_30s_20260730_165612/`.

## Policy Baseline

The native replacement policy requires the final architecture to retain the arcade semantic graphics decision and replace the complete PC080SN chip-specific tail with direct Genesis final output. It forbids final reliance on software chip devices, virtual chip RAM, C-window/name-RAM shadows, generic PC080SN projection, or chip-address translation. Temporary compatibility paths must be identified and isolated.

For Plane A, final output must be:

`semantic map/source decision -> bounded native row/column -> final Plane A staging words -> dirty rows -> VBlank commit`.

`0xC08000` / PC080SN C-window state may be used only as an oracle for proof comparisons, not as production authority.

## Address Map Authority

All arcade-to-Genesis code mappings below came from `build/rastan-direct/address_map.json`.

| Arcade PC | Runtime Genesis PC | Kind | Role |
|---:|---:|---|---|
| `0x0556A6` | `0x0558A6` | `arcade_copy` | selector-1 vertical arm |
| `0x05572E` | `0x05592E` | `arcade_copy` | selector-2 vertical arm |
| `0x0556FC` | `0x0558FC` | `arcade_copy` | selector-1 publication call to dispatcher |
| `0x055788` | `0x055988` | `arcade_copy` | selector-2 publication call to dispatcher |
| `0x055948` | `0x055B48` | `arcade_copy` | publication dispatcher |
| `0x0558A2` | `0x055AA2` | `arcade_copy` | post-publication advance |
| `0x055904` | `0x055B04` | `patched_site` | descriptor rebuild hook site |
| `0x055968` | `0x055B68` | `patched_site` | selector-0 native Plane A route |
| `0x055990` | `0x055B90` | `patched_site` | selector-1/2 native Plane A route |
| `0x0559B2` | `0x055BB2` | `arcade_copy` | original selector-0 cell producer body retained in ROM |
| `0x055A14` | `0x055C14` | `arcade_copy` | original selector-1/2 cell producer body retained in ROM |

## Remap Spec Authority

`specs/rastan_direct_remap.json` contains three relevant `opcode_replace` entries:

| Arcade PC | Replacement intent |
|---:|---|
| `0x055904` | Replaces the descriptor rebuild read-base with `jmp genesistan_hook_pc080sn_descriptor_rebuild`. |
| `0x055968` | Replaces the selector-0 strip-tail body with `jmp genesistan_hook_tilemap_plane_a_selector0_native`, preserving the caller's BSR and returning by RTS to the original continuation. |
| `0x055990` | Replaces the selector-1/2 strip-tail body with `jsr genesistan_hook_tilemap_plane_a_selector12_native`, preserving the caller's BSR and returning by RTS to the original continuation. |

The spec note for `0x055990` explicitly says the helper retains selector state, strip index/group, descriptor pointer/word rebuild tables, and scroll-derived resident window, then replaces the PC080SN C-window/collision tail with final Plane A staging plus collision side-channel.

## Generated Manifest Verification

`build/rastan-direct/rastan_direct_patch_manifest.json` confirms the generated Build 0246 route:

| Arcade PC | Runtime Genesis PC | Replacement bytes | Target symbol |
|---:|---:|---|---|
| `0x055904` | `0x055B04` | `4ef900071f78` | `genesistan_hook_pc080sn_descriptor_rebuild` |
| `0x055968` | `0x055B68` | `4ef9000704e8...` | `genesistan_hook_tilemap_plane_a_selector0_native` |
| `0x055990` | `0x055B90` | `4eb90007061a...` | `genesistan_hook_tilemap_plane_a_selector12_native` |

`apps/rastan-direct/out/symbol.txt` confirms:

| Symbol | Runtime Genesis PC |
|---|---:|
| `genesistan_hook_tilemap_plane_a_selector0_native` | `0x000704E8` |
| `genesistan_hook_tilemap_plane_a_selector12_native` | `0x0007061A` |
| `genesistan_hook_tilemap_bg_fill_tall` | `0x00070D74` |
| `genesistan_hook_tilemap_fg_fill_tall` | `0x00070E44` |
| `genesistan_hook_cwindow_clear` | `0x00071D44` |
| `genesistan_hook_pc080sn_descriptor_rebuild` | `0x00071F78` |

## Current Plane A Route

The live dispatcher at `arcade_pc 0x055948` / `runtime_genesis_pc 0x055B48` remains copied arcade control flow. It decides between the two patched strip tails:

- selector 0 -> `arcade_pc 0x055968` / `runtime_genesis_pc 0x055B68` -> native selector-0 helper.
- selector 1/2 -> `arcade_pc 0x055990` / `runtime_genesis_pc 0x055B90` -> native selector-1/2 helper.

The original chip-tail bodies at `arcade_pc 0x0559B2` / `0x055A14` remain present as copied ROM bytes, but the patched strip-tail entries bypass them for these Plane A gameplay routes.

## Current Helper Inputs

### Selector 0

`genesistan_hook_tilemap_plane_a_selector0_native` consumes:

- `a5+0x10CC` strip group.
- `a5+0x10CA` strip index.
- `staged_scroll_y_fg` to compute visible-top residency gate.
- `PC080SN_DESC_REBUILD_PTR_TABLE` (`0x10D040` equivalent in mapped WRAM).
- `PC080SN_DESC_REBUILD_WORD_TABLE` (`0x10D080` equivalent in mapped WRAM).
- Original PC080SN source blocks and LUTs for tile/attribute conversion.

The selector-0 logical coordinate proof remains valid: logical column is `(10CC*4 + 10CA) & 63`; logical row is `segment*4 + cell`; source reads are independent of final `0xC08000` authority. This is proven only for selector-0 columns.

### Selector 1/2

`genesistan_hook_tilemap_plane_a_selector12_native` consumes:

- `a5+0x10A8` selector to choose row-subindex reversal behavior.
- `a5+0x10CA` strip index.
- `a5+0x10CC` strip group.
- `staged_scroll_y_fg` for resident-window gate.
- `PC080SN_DESC_REBUILD_PTR_TABLE` (`0x10D040` equivalent in mapped WRAM).
- `PC080SN_DESC_REBUILD_WORD_TABLE` (`0x10D080` equivalent in mapped WRAM).
- Original source blocks and LUTs.

Its implemented formula is:

- source row byte offset: `((selector == 2) ? 10CA : (~10CA & 3)) << 3`.
- logical row: `(10CC*4 + row_subindex) & 63`.
- logical column: `segment*4 + cell`.
- resident gate: `((logical_row - visible_top) & 63) < 32`.
- physical staging row: `logical_row & 31`.

This helper emits final Genesis Plane A words into `staged_fg_buffer`, marks `fg_row_dirty`, and writes the collision side-channel by logical row/column. It does not need final `0xC08000` destination authority for its current publication event.

However, the helper is still fed by the rebuilt descriptor pointer/word tables. It is therefore currently proven only as an event-local native strip realization after the arcade producer path has selected/rebuilt the current publication tables. It is not yet proven to be an arbitrary logical-row source for rows that the arcade did not publish.

## `0x10D000`, `0x10D040`, and `0x10D080` Classification

| Structure | Current classification | Final-architecture status |
|---|---|---|
| `0x10D000` source base table | Original map/source base structure seeded from scene/segment map data and advanced by ring cycles. | Potential semantic source, but only as current stream bases unless an arbitrary-row formula is proven. |
| `0x10D040` descriptor pointer table | Rebuilt event-local descriptor pointer table consumed by strip producers. | Transitional/current-publication source cache. It may be retained only if classified as semantic source data, not chip-shaped destination state. It does not by itself prove arbitrary-row derivation. |
| `0x10D080` source/control word table | Rebuilt event-local source/control word table consumed by strip producers. | Transitional/current-publication source cache. Same limitation as `0x10D040`. |
| `0x055904` descriptor rebuild | Runtime helper converts current `0x10D000` base entries into descriptor pointers and source words. | Useful bridge for current publications, but not a sufficient final arbitrary-row source proof. |

This preserves the distinction required by the prompt: descriptor pointer/source tables are not PC080SN C-window/name-RAM shadows, but they are also not yet a proven arbitrary-row semantic renderer.

## Compatibility and Legacy Paths

### Plane A Tall-FG Projector

`vdp_project_fg_tall_if_dirty` is explicitly gated out during gameplay. In `apps/rastan-direct/src/vdp_comm.s`, it returns immediately when `genesistan_current_scene_id == 1`, preventing the tall-FG projector from overwriting native gameplay Plane A output.

Therefore, the legacy tall-FG projector is transitional code but is not reachable as the gameplay Plane A authority in Build 0246.

### Plane B Tall-BG Projector

`vdp_project_bg_tall_if_dirty` remains active for gameplay scene 1. This is Plane B, not the Plane A path under analysis. It remains transitional/deferred and should not be generalized into the final Plane A architecture.

### C-Window Clear Helper

`genesistan_hook_cwindow_clear` still clears staged BG/FG buffers and the transitional tall FG buffer. It also clears `fg_native_gameplay_owner`. It is a shared compatibility/helper path, not proof of native vertical row source. It must not be used as an architecture justification for Plane A vertical streaming.

## Existing Runtime Evidence

### Proven: Initial Pan Starvation

Existing Build 0245/0246 evidence shows:

- Initial fill seeds Plane A at `visible_top=1`.
- Gameplay begins after a scripted camera pan at `visible_top=23`.
- During the scripted pan, `10B0` / `staged_scroll_y_fg` changes but `fg_writes=0`.
- The pan path has selector `0`, stable `10CA=0`, stable `10CC=0`, and no cursor writes to `0xFF10A4`.

This proves the current selector-1/2 path is not active during the scripted initial vertical pan. It does not prove the current selector-1/2 helper is wrong for active ordinary vertical publication events.

### Not Proven: Ordinary Down/Up/Reversal Crossings

No inspected trace gives a complete per-crossing table for genuine Build 0246 ordinary vertical movement that includes all of:

- old/new scroll Y;
- old/new `visible_top`;
- selector value;
- `10CA`/`10CC`;
- whether `0x055948` dispatched;
- whether `0x055904` rebuilt descriptor tables;
- whether `0x055B90` / `0x0007061A` executed;
- which logical row was published;
- whether that logical row landed in `staged_fg_buffer[logical_row & 31]`;
- collision side-channel result.

The available `rev.txt` sample is insufficient because it records stable scroll state and no row dirty activity; it does not capture a proven vertical crossing or reversal publication.

## Required Phase Answers

### 1. Current Remap Chain

Verified. The Build 0246 generated route is:

- `arcade_pc 0x055948` / `runtime_genesis_pc 0x055B48`: copied dispatcher.
- `arcade_pc 0x055968` / `runtime_genesis_pc 0x055B68`: patched to native selector-0 helper at `runtime_genesis_pc 0x000704E8`.
- `arcade_pc 0x055990` / `runtime_genesis_pc 0x055B90`: patched to native selector-1/2 helper at `runtime_genesis_pc 0x0007061A`.
- `arcade_pc 0x055904` / `runtime_genesis_pc 0x055B04`: patched to descriptor rebuild helper at `runtime_genesis_pc 0x00071F78`.

### 2. Helper Input Classification

Partial.

- Selector-0 input classification is strong for current column publications.
- Selector-1/2 input classification is only partial: it consumes semantic selector/group/index and source blocks, but depends on current rebuilt descriptor pointer/word tables. That is acceptable for the current publication event, but not sufficient for arbitrary rows that were not published by the arcade.
- No inspected helper consumes `0xC08000` as final output authority for gameplay Plane A, but the semantic source for non-published vertical pan rows remains unresolved.

### 3. Runtime Vertical Crossing Proof

Not proven.

- Scripted initial pan: proven no Plane A publication despite visible-top change.
- Ordinary selector-1 down crossings: not captured with the required alignment table.
- Ordinary selector-2 up crossings: not captured with the required alignment table.
- Reversal: not captured with the required alignment table.
- No-publication ordinary selector-1/2 paths: not proven safe or unsafe against visible-top crossings.

### 4. Arbitrary Logical Row Source

Not proven.

`0x10D000` and the original map/descriptor structures are plausible semantic source candidates, but this checkpoint did not prove a formula that derives any arbitrary logical Plane A row, its 64 cells, collision values, and palette/attribute words independent of PC080SN C-window/name-RAM authority.

### 5. Architecture Classification

**D. No safe semantic boundary proven yet.**

Reason: The current active routes are mechanically verified and native for event-local published strips, but the requested final vertical source proof is incomplete. The evidence still leaves multiple architectures possible:

- shared semantic row renderer for scripted pan and ordinary movement;
- separate scripted-pan semantic producer plus ordinary selector-1/2 producer;
- bounded resident-ring initialization/reseed at a proven state boundary plus ordinary entering-row producers.

Because arbitrary-row derivation and ordinary vertical crossing alignment are both unresolved, selecting among those architectures now would be premature.

## STOP Conditions

STOP is triggered for implementation, not for documentation, because:

- selector-1/2 ordinary crossings are not aligned with `visible_top` in current runtime evidence;
- arbitrary logical row source is unresolved;
- multiple architectures remain plausible;
- final reliance on `0xC08000`, a C-window/name-RAM shadow, or projection would violate the native replacement policy.

## Smallest Safe Next Task

A narrow proof task, not implementation:

1. Trace Build 0246/next accepted build through real vertical movement and reversal with breakpoints/events at JSON-mapped `0x0558A6`, `0x05592E`, `0x0558FC`, `0x055988`, `0x055B48`, `0x055B04`, `0x055B90`, and helper `0x0007061A`.
2. For each 8-pixel `visible_top` crossing, record old/new scroll Y, selector, `10CA`, `10CC`, dispatch/no-dispatch, descriptor rebuild/no-rebuild, helper entry/no-entry, logical row, physical row, and row dirty result.
3. In parallel, prove or reject an arbitrary-row source formula from `0x10D000` seed tables, map segment state, descriptor/source blocks, and original map stream data, using `0xC08000` only as an oracle.

Implementation is safely placeable only after that proof selects one architecture.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: Plane B native migration, PC090OJ, rope/collision/progression, palettes/HUD, audio/input, and broad gameplay visual correctness.

## KNOWN_FINDINGS Impact

Option A: no new finding to index. This document tightens the Build 0246 native Plane A proof boundary under existing native replacement findings.

## Architecture Compliance

Confirmed for this analysis task:

- No production source changed.
- No remap spec changed.
- No ROM built.
- No counter changed.
- No compatibility layer proposed or extended.
- C08000/name-RAM projection remains forbidden as final authority.

## Runtime Replay Completion Attempt - 2026-07-31

This section completes the requested follow-up attempt without changing production source, remap specs, ROMs, or the build counter.

### Additional Trace Artifacts

- Primary trace harness: `states/traces/build0246_vertical_runtime_proof_20260731_140816/build0246_vertical_frame.lua`.
- Debugger command artifact: `states/traces/build0246_vertical_runtime_proof_20260731_140816/build0246_vertical_debug.cmd`.
- Headless debugger run: `states/traces/build0246_vertical_runtime_proof_20260731_140816/`.
- Real-time interactive MAME run: `states/traces/build0246_vertical_runtime_proof_20260731_140816_manual_realtime/`.

The oversized debugger trace artifact `states/traces/build0246_vertical_runtime_proof_20260731_140816/debug_trace.log` is preserved as evidence. It was not deleted or truncated.

### Replay Methods Attempted

1. A headless debugger run with breakpoints/watch-style logging at the JSON-mapped selector-1/2 arms, dispatcher, descriptor rebuild, helper, post-publication advance, source-pointer advance, map-group advance, scroll update, FG commit, and staging/dirty writes.
2. A Lua frame/write-tap harness that records external frame crossings, visible-top changes, descriptor/cursor writes, FG staging/dirty writes, and source-cell samples when selector-1/2 helper context is observed.
3. A real-time interactive MAME Genesis run using Build 0246 ROM `dist/rastan-direct/rastan_direct_video_test_build_0246.bin`, with trace output under `states/traces/build0246_vertical_runtime_proof_20260731_140816_manual_realtime/`.
4. A local search for usable replay state. The repository only contained `states/exodus-debug-savestates/78_save.sram` and `states/exodus-debug-savestates/59.test.mode.exs`; no Build 0246 gameplay MAME savestate capable of starting from a genuine vertical movement/reversal state was found.

### Real-Time Build 0246 Capture Summary

`states/traces/build0246_vertical_runtime_proof_20260731_140816_manual_realtime/`:

- MAME exit code: `0`.
- Captured external-frame rows: `372`.
- Captured Lua event rows: `8`.
- Captured selector-1/2 source sample rows: `0`.
- Visible-top crossings: `22`.
- First visible-top crossing: frame `400`, `visible_top 1 -> 2`, selector `0x0000`, `fg_dirty=0x00000000`, state `2/3/0`.
- Last visible-top crossing: frame `466`, `visible_top 22 -> 23`, selector `0x0000`, `fg_dirty=0x00000000`, state `2/3/0`.
- All visible-top crossing selectors in this capture: `0x0000` only.
- All visible-top crossing dirty masks in this capture: `0x00000000` only.
- Post-settle frames after frame `466`: `296`, stable `visible_top=23`, selector `0x0000`, `fg_dirty=0x00000000`.

### Runtime Result

The additional real-time replay again captured the scripted initial settling pan, not genuine ordinary vertical gameplay publication.

Proven by this completion attempt:

- Build 0246 reaches gameplay state `2/3/0`.
- During the captured camera settling window, `visible_top` advances from `1` to `23`.
- During all 22 captured visible-top crossings, selector `a5+0x10A8` remains `0x0000`.
- During all 22 captured visible-top crossings, `fg_row_dirty` remains `0x00000000`.
- No selector-1/2 helper source samples were produced.
- No staged selector-1/2 row publication was observed.

Not proven by this completion attempt:

- Selector-1 downward publication.
- Selector-2 upward publication.
- Direction reversal.
- Ordinary selector-1/2 no-publication scroll behavior.
- Selector-1 logical-row formula at runtime.
- Selector-2 logical-row formula at runtime.
- Selector-1/2 source-tile formula at runtime.
- Arbitrary-row semantic source chain from `0x10D000`/stage map state independent of current event-local descriptor rebuild.

### Per-Crossing Coverage Status

| Required case | Captured? | Evidence status |
|---|---:|---|
| Selector-1 downward publication | No | No selector `1` helper/staging/source samples in completed replay. |
| Selector-2 upward publication | No | No selector `2` helper/staging/source samples in completed replay. |
| Direction reversal | No | No selector transition/reversal state captured. |
| Ordinary selector-1/2 no-publication path | No | Only selector `0` scripted pan with no publication was captured. |
| Scripted no-publication starvation | Yes | `visible_top 1 -> 23`, selector `0`, dirty `0` throughout captured crossings. |

### Formula Status

The source formulas implemented in `genesistan_hook_tilemap_plane_a_selector12_native` remain statically identified but not runtime-proven by this completion attempt:

- Selector-1 logical-row formula: `((a5+0x10CC)&0xF)*4 + ((~(a5+0x10CA))&3)` remains unproven at runtime.
- Selector-2 logical-row formula: `((a5+0x10CC)&0xF)*4 + ((a5+0x10CA)&3)` remains unproven at runtime.
- Logical-column formula: `segment*4 + cell` remains unproven for selector-1/2 runtime publications.
- Source-tile formula: `descriptor_source + row_sub*8 + cell*2` remains unproven for selector-1/2 runtime publications.

No `0xC08000` production dependency was introduced. The C-window oracle columns added to the trace harness produced no rows because no selector-1/2 source samples were captured.

### Architecture Decision After Completion Attempt

Architecture remains **D: no safe semantic boundary proven yet**.

Reason: this follow-up produced additional real runtime evidence for the scripted no-publication starvation path, but did not capture the genuine selector-1/2 publication/reversal cases needed to prove a final native vertical source. The first unresolved fact is now narrower:

> No captured genuine Build 0246 runtime state has yet shown selector `1` or selector `2` vertical publication entering `runtime_genesis_pc 0x0007061A` with matching descriptor rebuild, source sample, staged row write, dirty bit, and VBlank commit.

Until that state is captured, implementation is not safely placeable. A vertical publisher or reseed would still risk selecting the wrong semantic source boundary.

### Smallest Safe Implementation Boundary

No implementation boundary is safe yet.

The smallest next evidence boundary is a user- or debugger-controlled Build 0246 gameplay state that already has ordinary vertical movement/reversal available, then a short trace window proving one complete selector-1/2 publication chain:

`selector arm -> dispatcher 0x055B48 -> descriptor rebuild 0x055B04 -> helper 0x0007061A -> staged row -> dirty bit -> VBlank commit`

with source samples from multiple segments/cells and a matching arbitrary-row semantic source derivation.
