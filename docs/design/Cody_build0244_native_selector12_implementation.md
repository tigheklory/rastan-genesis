# Cody - Build 0244 Native Selector-1/2 Implementation

**Agent:** Cody  
**Date:** 2026-07-29  
**Task type:** Prove and implement native PC080SN Plane A selector-1/2 from Build 0244  
**Input build:** Build 0244, `dist/rastan-direct/rastan_direct_video_test_build_0244.bin`, SHA-256 `939c303b37b21352f693311cd1df19bbbd87810d2a4419c97ac356366fd99a62`  
**Output build:** Build 0245, `dist/rastan-direct/rastan_direct_video_test_build_0245.bin`, SHA-256 `3a6c9bb9731a83ed9c68aa872d36ddb550c6f9175d946232cd9bd28e2d2c057d`, size `1588848`, counter `245`  
**Build 0244 source/artifact preservation:** `states/traces/build0244_native_selector12_implementation_20260729_131809/`

## Phase 0 Baseline

- **Task classification:** EXTENDING, OPEN-001 native PC080SN Plane A migration.
- **Architecture rule:** arcade semantic decisions remain authoritative; Genesis replaces only the PC080SN chip-specific tail with final YM7101 Plane A staging and VBlank row DMA.
- **Native replacement policy:** final architecture may not depend on software PC080SN devices, C-window/name-RAM shadows, tall projection, or generic chip-address translation. Transitional code must be isolated and prevented from overwriting native output.
- **Relevant known findings:** KF-010/KF-011 rendering through staging and VBlank commit; KF-032 raw PC080SN writes must route through staging; KF-036 mapped work-RAM base; KF-041 Stage 1 PC080SN producer-source scene identity; KF-068/KF-071/KF-072/KF-073 native Plane A and VBlank coordinate-model findings.
- **Highest rediscovery hazards:** resident-window row model from KF-072, address mapping discipline, no chip-shaped final output, no numbered artifact deletion.
- **Open issues touched:** OPEN-001. OPEN-002/Plane B, PC090OJ, rope, collision, palette/HUD, audio, input, and gameplay progression are intentionally out of scope.
- **Contradiction check:** no contradiction of CONFIRMED or STRONG findings detected.

## Files And Evidence Inspected

- `RULES.md`, `ARCHITECTURE.md`, `AGENTS.md`, `PROMPT_TEMPLATE.md`
- `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`
- `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest relevant `AGENTS_LOG.md`
- `docs/design/Cody_build0244_complete_native_gameplay_plane_a.md`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/maincpu.disasm.txt`
- `build/rastan-direct/address_map.json`
- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

## Address Mapping

Address mapping was resolved through `build/rastan-direct/address_map.json`, not by arithmetic.

| Address | Mapped runtime Genesis PC | Kind |
| --- | ---: | --- |
| `arcade_pc 0x055948` | `runtime_genesis_pc 0x055B48` | `arcade_copy` |
| `arcade_pc 0x055950` | `runtime_genesis_pc 0x055B50` | `arcade_copy` |
| `arcade_pc 0x055968` | `runtime_genesis_pc 0x055B68` | `patched_site` |
| `arcade_pc 0x055990` | `runtime_genesis_pc 0x055B90` | `patched_site` |
| `arcade_pc 0x0559B2` | `runtime_genesis_pc 0x055BB2` | `arcade_copy` |
| `arcade_pc 0x055A14` | `runtime_genesis_pc 0x055C14` | `arcade_copy` |

## Original Arcade Selector Flow

Observable from `build/maincpu.disasm.txt`:

- `arcade_pc 0x055948` is the shared dispatcher.
- If `a5@(0x10A8) == 0`, it calls selector-0 driver `arcade_pc 0x055968`, then increments `a5@(0x10CA)` and calls `0x0558A2`.
- If `a5@(0x10A8) != 0`, it calls selector-1/2 driver `arcade_pc 0x055990`, then increments `a5@(0x10CA)` and calls `0x0558A2`.

Selector-0 driver facts:

- `0x055968` loads `a0 = a5@(0x10A0)`, `d1 = 16`, `a1 = 0x0010D080`, `a3 = 0x0010D040`.
- It calls `0x0559B2` for each descriptor segment and writes back the advanced `a0` to `a5@(0x10A0)`.
- Inner `0x0559B2` emits a vertical column: four cells with row progression and constant logical column.

Selector-1/2 driver facts:

- `0x055990` loads `a0 = a5@(0x10A4)`, `d1 = 16`, `a1 = 0x0010D080`, `a3 = 0x0010D040`.
- It calls `0x055A14` for each descriptor segment and does **not** write back the advanced `a0` to `a5@(0x10A4)`.
- Inner `0x055A14` starts with `move.w #1,a5@(0x1330)`.
- Inner `0x055A14` emits a horizontal row: four adjacent cells per segment, with logical column `segment * 4 + cell`.
- For both collision and tile-source reads, `0x055A14` uses `a5@(0x10CA)` directly when `a5@(0x10A8) == 2`, else uses `(~a5@(0x10CA)) & 3`.
- If `block+32 == 0x00FF`, collision value is read from `block+34`; otherwise collision value is read from `block+20 + row_in_group*8 + cell*2`.
- Tile code is read from `block+0 + row_in_group*8 + cell*2`.

## Selector-1/2 Semantic Contract

The native helper retains these arcade semantic/source inputs:

- `a5@(0x10A8)` selector/direction.
- `a5@(0x10CA)` strip index.
- `a5@(0x10CC)` strip group.
- Descriptor pointer table at `Genesis-WRAM 0x00FF1040`.
- Descriptor word table at `Genesis-WRAM 0x00FF1080`.
- Tile source blocks referenced by the rebuilt descriptor pointer table.
- Current `staged_scroll_y_fg`, used only to derive the Genesis resident-window row.

The native helper replaces these PC080SN-specific tail effects:

- C-window FG destination writes.
- C-window-derived destination indexing as final output authority.
- PC080SN name-RAM projection as gameplay Plane A owner.

## Native Formulas

Selector-0 correction:

- `logical_column = (((a5+0x10CC) & 0x000F) << 2) + ((a5+0x10CA) & 3)`.
- `logical_row = segment * 4 + cell`.
- `visible_top = (((-staged_scroll_y_fg + 8) & 0x01FF) >> 3) & 0x003F`.
- `delta = (logical_row - visible_top) & 0x003F`.
- Resident if `delta < 32`.
- **Build 0245 correction:** `physical_row = delta & 0x001F`, not `logical_row & 0x001F`.

Selector-1/2 implementation:

- `row_in_group = (a5+0x10CA) & 3` when `a5+0x10A8 == 2`.
- `row_in_group = (~(a5+0x10CA)) & 3` when `a5+0x10A8 != 2`.
- `logical_row = ((((a5+0x10CC) & 0x000F) << 2) + row_in_group) & 0x003F`.
- `logical_column = segment * 4 + cell`.
- `source_offset = row_in_group * 8 + cell * 2`.
- Collision destination: `Genesis-WRAM 0x00FF1E00 + ((logical_row * 64 + logical_column) * 2)`.
- Resident Plane A destination: `staged_fg_buffer[((logical_row - visible_top) & 0x001F) * 64 + logical_column]` when `(logical_row - visible_top) & 0x003F < 32`.
- Dirty row: `fg_row_dirty` bit `physical_row`.

## Runtime Probe Note

A focused original-arcade MAME Lua probe was attempted under:

`states/traces/build0244_native_selector12_implementation_20260729_131809/arcade_selector12_proof/`

The first attempt failed because this arcade driver Lua environment does not expose `install_execute_tap`. The fallback C-window write taps reached gameplay state `2/3/0`, but the noninteractive run did not naturally exercise the `0x055990/0x055A14` selector-1/2 write PCs before exit. This is recorded as a runtime-capture limitation, not as negative evidence against the selector-1/2 path.

Implementation proof for this build therefore rests on:

- Original arcade disassembly of the selector-1/2 tail.
- Exact JSON address mapping of the selector-1/2 patched site.
- Build 0245 manifest/disassembly proof that the site routes to the native helper.
- Release gate and standard 30-second Genesis smoke trace.

## Implementation

Changed production source:

- `apps/rastan-direct/src/tilemap_hooks.s`
  - Added `.global genesistan_hook_tilemap_plane_a_selector12_native`.
  - Added `ARCADE_PC080SN_SELECTOR_OFFSET = 0x10A8` for selector-1/2 direction.
  - Corrected selector-0 resident row write from logical-row low bits to delta-row low bits.
  - Added `genesistan_hook_tilemap_plane_a_selector12_native`.
  - Preserved `a5+0x1330 = 1` selector-1/2 side effect.
  - Writes final Genesis Plane A staging words and collision-map values without C-window final authority.
- `apps/rastan-direct/src/vdp_comm.s`
  - Prevented `vdp_project_fg_tall_if_dirty` from projecting over gameplay Plane A. The tall-FG path remains transitional compatibility code only and no longer owns gameplay output.
- `specs/rastan_direct_remap.json`
  - Added the new helper to required symbols.
  - Changed `arcade_pc 0x055990` from the transitional `genesistan_hook_tilemap_fg` route to `genesistan_hook_tilemap_plane_a_selector12_native`.
  - Kept the replacement byte-neutral: same opcode site count, no copied-program insertion/removal.
- `tools/translation/postpatch_startup_rom.py` and `tools/translation/verify_canonical_rom.py`
  - Updated strict canonical covered-byte invariant from `0x183CFC` to `0x183E70` for the new helper body size. Opcode replacement site count remains `216`.

## Generated Verification Facts

Build 0245 manifest excerpts:

- `arcade_pc 0x055968`, `runtime_genesis_pc 0x055B68`: `4EF9000704A4...` routes to `genesistan_hook_tilemap_plane_a_selector0_native`.
- `arcade_pc 0x055990`, `runtime_genesis_pc 0x055B90`: `4EB90007060A...` routes to `genesistan_hook_tilemap_plane_a_selector12_native`.

Build 0245 symbol facts:

- `genesistan_hook_tilemap_plane_a_selector0_native = runtime_genesis_pc 0x000704A4`.
- `genesistan_hook_tilemap_plane_a_selector12_native = runtime_genesis_pc 0x0007060A`.
- `vdp_project_fg_tall_if_dirty = runtime_genesis_pc 0x000701B6` and now begins with the gameplay-scene skip.

Generated ROM byte facts:

- `ROM[0x055B68] = 4ef9000704a4...`.
- `ROM[0x055B90] = 4eb90007060a...`.

## Build Result

- Build produced: YES.
- Build number: `0245`.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0245.bin`.
- SHA-256: `3a6c9bb9731a83ed9c68aa872d36ddb550c6f9175d946232cd9bd28e2d2c057d`.
- Size: `1588848` bytes.
- Counter: `245`.
- Gate: `GATE_PASS`.
- Opcode replacement patched-site count: `216`.
- Canonical covered bytes: `0x183E70`.
- Tile scene budget: largest scene `1067 / 1164`; all scenes fit.
- Standard smoke trace: `states/traces/rastan_direct_video_test_build_0245_mame_30s_20260729_132349/`, `1798` frames, `fg_cwindow_live count=0`.

## Architecture Compliance

- Semantic cut retained: arcade selector, strip index, strip group, descriptor tables, source blocks, and scroll-derived visible window.
- Complete chip-specific tail removed for selector-1/2: no final C-window/PC080SN destination writes remain at `arcade_pc 0x055990`.
- Transitional compatibility still present: legacy tall-FG buffer/helper code remains in source, but VBlank no longer projects it over gameplay Plane A. Removal is deferred until remaining non-gameplay/legacy callers are audited.
- No Plane B, PC090OJ, palette, HUD, collision redesign, audio, input, rope, or gameplay progression changes were intentionally made.

## Open/Closed Issues Impact

- Open issues touched: OPEN-001.
- New issues opened: none.
- Issues closed: none.
- Intentionally deferred: Plane B native replacement, PC090OJ, rope/post-rope, collision/player-state, palette/HUD, and broader gameplay visual correctness.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This is an implementation continuation of known native Plane A migration and the established KF-072 resident-window coordinate model.

## User Verification Scope

- Start Build 0245 and reach Stage 1.
- Verify Plane A foreground/terrain behavior while moving horizontally and jumping/falling enough to exercise selector-1/2 row publications.
- Treat visual imperfections outside Plane A selector-0/1/2 ownership as separate follow-up evidence.
