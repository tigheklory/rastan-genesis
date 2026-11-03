# Cody Build 0248 Native Plane B Direct Staging

## Baseline

- Project: `apps/rastan-direct`
- Accepted input build: Build 0247 / counter 247
- Produced candidate build: Build 0248 / counter 248
- Task type: focused implementation + verification
- Scope: gameplay PC080SN Plane B only
- Build command used: `source tools/setup_env.sh && RASTAN_GAMEPLAY_HUD_SPRITES=2 make -C apps/rastan-direct release`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0248.bin`
- SHA-256: `f6c5c12d0a9beb9d64979e75d122cf9d1392188ef72705b85943c491c3c59332`
- Size: `1590240` bytes

## Authorities Read

- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`
- `docs/design/Andy_build0247_native_plane_b_semantic_boundary.md`
- `docs/design/Andy_build0247_plane_b_destination_trigger_contract.md`
- `docs/design/Cody_build0247_native_plane_a_no_publish_vertical_routing.md`
- `build/rastan-direct/address_map.json`
- `specs/rastan_direct_remap.json`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`

## Architecture Compliance

Build 0248 keeps the original arcade semantic source decision and replaces the PC080SN-specific gameplay Plane B tail with direct Genesis final staging.

- Semantic cut retained: arcade gameplay BG producer at `arcade_pc 0x055C5E`, mapped to `runtime_genesis_pc 0x055E5E`, still enters `genesistan_hook_itempage_strip_blit`.
- Chip-specific tail removed from gameplay authority: gameplay no longer routes through `genesistan_hook_tilemap_bg_fill_tall`, `staged_bg_tall_buffer`, or `vdp_project_bg_tall_if_dirty` as Plane B production authority.
- Final architecture path: Rastan semantic descriptor/source state -> native Plane B row/cell helpers -> `staged_bg_buffer` + `bg_row_dirty` -> existing VBlank Plane B commit.
- Forbidden final inputs avoided in gameplay Plane B production: no `0xC00000` name RAM authority, no `a5@0x10F8` chip-shaped destination authority, no tall-BG projection authority.

Transitional compatibility still present:

- `genesistan_hook_tilemap_bg_fill_tall` remains linked for historical/non-accepted compatibility code, but gameplay Build 0248 routing does not call it.
- `vdp_project_bg_tall_if_dirty` remains linked but is gated off for gameplay scene `1`, so it cannot overwrite native gameplay Plane B output.
- Removal boundary: after gameplay Plane B native output is accepted visually and no non-gameplay caller depends on the tall projector, remove the tall-BG helper/projector/buffer family in a separate retirement task.

## Native Plane B Source Formula

Build 0248 implements Andy's accepted Plane B arbitrary-column formula from arcade semantic state:

```text
tm0idx = a5@0x1386
base = 0x03951C + tm0idx * 0x0C
G_r = (a5@0x10FC - base) / 6
AR = G_r * 16 + a5@0x10F6

for destination column C:
    absC = AR - ((AR - C) & 63)
    source_group = absC >> 4
    source_subcol = C & 15
    descriptor = *(u32)(base + source_group * 6 + 2)
    tile = *(u16)(descriptor + logical_row * 32 + source_subcol * 2)
```

Implementation location:

- `apps/rastan-direct/src/tilemap_hooks.s`: `.Lplane_b_publish_logical_row_native`

Notes:

- The descriptor table root is `arcade_rom/data 0x03951C`.
- Descriptor pointers are converted through the existing relocated descriptor conventions, not through fixed numeric PC relocation assumptions.
- Attribute conversion reuses the existing BG attr LUT path via `.Lplane_b_native_attr_from_word`.

## Gameplay Strip Producer Routing

`genesistan_hook_itempage_strip_blit` now separates gameplay and non-gameplay at the existing producer boundary.

Gameplay path:

- Source pointer inside the gameplay strip-source range marks gameplay (`d6 != 0`).
- Each produced cell routes to `.Lplane_b_stage_gameplay_producer_cell_native`.
- The helper writes final Genesis Plane B words into `staged_bg_buffer` and marks `bg_row_dirty`.
- It applies the required 32-row residency gate before staging.

Non-gameplay/frontend path:

- Non-gameplay strip sources still route to `genesistan_hook_tilemap_bg_fill`.
- This keeps item-page/frontend behavior isolated from the gameplay Plane B migration.

Implementation location:

- `apps/rastan-direct/src/tilemap_hooks.s`: `genesistan_hook_itempage_strip_blit`

## Mandatory Residency Gate

The producer cell helper stages only cells in the currently resident 32-row Genesis Plane B window:

```text
visible_top = visible_top_from_scroll(a5@0x10EE)
resident_delta = (logical_row - visible_top) & 63
if resident_delta >= 32: skip
physical_row = logical_row & 31
physical_col = ((a5@0x10F4 & 3) * 16 + (a5@0x10F6 & 15)) & 63
```

This prevents non-resident 64-row semantic rows from overwriting the 32-row VDP Plane B ring.

Implementation location:

- `apps/rastan-direct/src/tilemap_hooks.s`: `.Lplane_b_stage_gameplay_producer_cell_native`

## Shared Vertical Hooks

The existing Plane A no-publish vertical hooks are extended to also publish Plane B entering rows:

- Down hook: `arcade_pc 0x055704` -> `runtime_genesis_pc 0x055904` -> `genesistan_plane_a_pan_publish_entering_rows_down`
- Up hook: `arcade_pc 0x055790` -> `runtime_genesis_pc 0x055990` -> `genesistan_plane_a_pan_publish_entering_rows_up`

The helpers preserve the displaced `10BA` bookkeeping, call the existing native Plane A row helper, call the new native Plane B row helper, then jump back to the original arcade continuations.

Disassembly evidence:

```text
55904: jmp 0x70804
55990: jmp 0x707ac
707f4: bsrw 0x709c4
70844: bsrw 0x709c4
```

`0x709C4` is the new native Plane B logical-row publisher in the generated ROM.

## Tall Projector Gate

`vdp_project_bg_tall_if_dirty` is gated off for gameplay scene `1`:

```text
70138: cmpib #1,0xffb1d0
70140: beqs 0x701b6
70142: rts
```

This prevents the transitional tall-BG projection path from overwriting native gameplay Plane B output.

Implementation location:

- `apps/rastan-direct/src/vdp_comm.s`: `vdp_project_bg_tall_if_dirty`

## Address Map And Manifest Verification

Address-map / manifest facts:

- `arcade_pc 0x055704` maps to patched `runtime_genesis_pc 0x055904`.
- `arcade_pc 0x055790` maps to patched `runtime_genesis_pc 0x055990`.
- `arcade_pc 0x055C5E` maps to patched `runtime_genesis_pc 0x055E5E`.
- `0x055E5E` jumps to `genesistan_hook_itempage_strip_blit` at `0x7246C`.
- Opcode replacement count: `218`.
- Canonical total Genesis bytes covered: `0x1843E0`.
- Generated ROM size: `1590240` bytes.

Disassembly evidence for the gameplay producer branch:

```text
55e5e: jmp 0x7246c
724e4: tstw %d6
724e6: beqs 0x724ee
724e8: bsrw 0x70af2
724ee: bsrw 0x710d8
```

Interpretation:

- `0x70AF2` is the native gameplay Plane B direct producer-cell helper.
- `0x710D8` is the retained non-gameplay 32-row helper path.
- `0x711AE` (`genesistan_hook_tilemap_bg_fill_tall`) remains linked but is not the gameplay producer branch target.

## Build Verification

Build result:

- `GATE_PASS`
- Numbered ROM exists: `dist/rastan-direct/rastan_direct_video_test_build_0248.bin`
- Rolling ROM exists: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Numbered and rolling ROM SHA-256 match: `f6c5c12d0a9beb9d64979e75d122cf9d1392188ef72705b85943c491c3c59332`
- Size: `1590240` bytes
- Counter: `248`
- HUD mode confirmed in symbols: `RASTAN_GAMEPLAY_HUD_SPRITES = 2`

No numbered build artifact was deleted or overwritten.

## Runtime Smoke Verification

The standard release MAME smoke trace completed:

- Trace directory: `states/traces/rastan_direct_video_test_build_0248_mame_30s_20260802_103944/`
- External frames sampled: `1798`
- VDP live writes: `47197`
- First VDP live frame: `0`
- Last VDP live frame: `1797`
- MAME unmapped-address summary: none reported in the exit summary appended to `AGENTS_LOG.md`.

Scope note:

- This was a no-input release smoke run, not full Stage 1 visual acceptance.
- It proves the candidate boots and continues issuing VDP traffic under the standard release smoke harness.
- It does not prove P1 score visibility, 1UP visibility, parallax correctness, cave/rope correctness, or post-reset behavior.

## User Verification Required

The user must verify on Build 0248:

1. Stage 1 starts.
2. P1 score is visible.
3. `1UP` is visible.
4. Plane B renders coherently during normal horizontal movement.
5. Plane B tracks vertical movement without tall-projector overwrite.
6. No obvious title/frontend regression occurred.
7. The known Genesis-only level-reset vertical-scroll defect remains unchanged unless separately fixed later.

## Known Unresolved / Deferred

Unchanged by this build:

- Build 0247 user-observed Genesis-only level-reset vertical-scroll defect.
- Rope/reset/collision behavior.
- PC090OJ sprite behavior.
- Palette behavior.
- Plane A behavior beyond reusing the already accepted no-publish vertical hook as a shared trigger.
- Cave/rope-specific visual correctness.

## Files Changed

Production source:

- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`

Tooling/canonical verification constants:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Generated/build outputs include updated objects, symbol/disassembly/map/manifest/counter/ROM inventory, and Build 0248 ROM artifacts.

Documentation/logs:

- `docs/design/Cody_build0248_native_plane_b_direct_staging.md`
- `AGENTS_LOG.md`

## Open / Closed Issues Impact

- Open issues touched: OPEN-001-adjacent native PC080SN Plane B migration.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: rope/reset/collision, PC090OJ, palette, cave/rope visual acceptance, Build 0247 reset-scroll defect.

## KNOWN_FINDINGS Impact

Option A: no new finding to index.

This build implements the already documented native Plane B boundary and does not establish a new independent architectural finding.

## STOP Status

STOP not triggered for implementation or build production.

Gameplay visual acceptance remains pending user verification.
