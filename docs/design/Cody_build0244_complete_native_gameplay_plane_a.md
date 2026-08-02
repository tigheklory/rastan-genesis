# Cody - Build 0244 Complete Native Gameplay Plane A Gate

**Agent:** Cody  
**Date:** 2026-07-29  
**Mode:** Analysis / gate check; no production source edits; no ROM build  
**Baseline:** Build 0244 source, continuing Build 0242-0244 selector-0 work  
**Build 0244 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0244.bin`  
**Build 0244 SHA-256:** `939c303b37b21352f693311cd1df19bbbd87810d2a4419c97ac356366fd99a62`  
**Build counter before task:** `244`

## Scope

The task asked for completion of the native gameplay Plane A migration from Build 0244, including selector-0, selector-1, selector-2, initial fill, horizontal streaming, vertical streaming, direction reversal, native VDP output, and removal of gameplay dependence on `staged_fg_tall_buffer` / `vdp_project_fg_tall_if_dirty`.

The task also explicitly forbids producing a ROM after only one selector. The build gate requires all selector classes and vertical/reversal behavior to be proven and implemented before consuming the next build number.

## Phase 0 Baseline

Relevant priors read before task-specific inspection:

- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- `PROMPT_TEMPLATE.md`
- `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- Latest relevant `AGENTS_LOG.md` entries

Relevant known findings touched:

- `KF-010`: BG/FG staging and VBlank commit are the rendering lifecycle boundary.
- `KF-011`: Arcade VBlank owns frame lifecycle; Genesis helper code must return to arcade flow.
- `KF-014`: Address-map discipline is mandatory; copied-code PCs must not be inferred by arithmetic.
- `KF-015` / `KF-072`: C-window / PC080SN-derived transitional paths are not final native architecture.
- `KF-030`: Plane ownership and VDP commit sequencing remain critical.
- `KF-032`: Raw PC080SN writes must route through staging/native publication, not hardware writes.
- `KF-036`: Work-RAM mapped-base discipline applies to copied arcade state.
- `KF-037` / `KF-038`: Gameplay PC080SN behavior is tied to scene/scroll/collision source state; do not overfit a title/front-end model.
- `KF-041`: Scroll and visible-window interpretation must be proven from runtime behavior.
- `KF-068` / `KF-071` / `KF-072`: Native PC080SN replacement policy supersedes transitional projection and chip-shaped emulation as final architecture.
- `KF-073`: Native replacement must preserve arcade semantic decisions while replacing the chip-specific tail.

Rediscovery hazards touched:

- Plane A gameplay producer ownership.
- Old tall-map projection versus native VDP-backed output.
- Scroll/visible-window coordinate model.
- Copied-code PC mapping versus data-pointer conversion.

Task classification: `EXTENDING` existing OPEN-001 / native PC080SN migration work.

Contradiction of CONFIRMED or STRONG finding detected: `NONE`.

## Build 0244 Preservation

Build 0244 source and baseline metadata were preserved before analysis at:

`states/traces/build0244_complete_native_gameplay_plane_a_20260729_120657/`

Preserved contents include:

- `source_snapshot_0244/src/`
- `source_snapshot_0244/Makefile`
- `source_snapshot_0244/specs/`
- `source_snapshot_0244/translation_tools/`
- `baseline/build0244_rom_sha256.txt`
- `baseline/build0244_rom_ls.txt`
- `baseline/build_counter_before.txt`
- `baseline/git_status_before.txt`
- `baseline/production_diff_before.patch`

No numbered ROM artifact was deleted or overwritten.

## Files And Evidence Inspected

- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `specs/rastan_direct_remap.json`
- `build/rastan-direct/address_map.json`
- `build/maincpu.disasm.txt`
- `build/genesis_postpatch.disasm.txt`
- `apps/rastan-direct/out/symbol.txt`
- `docs/design/Andy_plane_a_semantic_cut_contract.md`
- `docs/design/Andy_plane_a_selector0_logical_coordinate_proof.md`
- `docs/design/Cody_plane_a_selector0_chip_tail_retirement_audit.md`
- `docs/design/Cody_plane_a_selector0_native_tail_implementation.md`
- `docs/design/Cody_build0242_selector0_route_fix.md`
- `docs/design/Cody_build0243_plane_a_visibility_fix.md`
- `states/traces/rastan_direct_video_test_build_0244_mame_30s_20260729_105440/`

## Address Mapping Discipline

Mapped PC evidence was checked through `build/rastan-direct/address_map.json`; arithmetic relocation was not used as authority.

Exact relevant mappings:

- `runtime_genesis_pc 0x055B48` -> `arcade_pc 0x055948`
- `runtime_genesis_pc 0x055B50` -> `arcade_pc 0x055950`
- `runtime_genesis_pc 0x055B68` -> `arcade_pc 0x055968`
- `runtime_genesis_pc 0x055B90` -> `arcade_pc 0x055990`
- `runtime_genesis_pc 0x055BB2` -> `arcade_pc 0x0559B2`
- `runtime_genesis_pc 0x055C14` -> `arcade_pc 0x055A14`

## Arcade Contract Recovered So Far

From `build/maincpu.disasm.txt`:

- `arcade_pc 0x055948` checks selector/control state at `%a5@(0x10A8)`.
- If the selector state is zero, it calls selector-0 driver `arcade_pc 0x055968`, then increments `%a5@(0x10CA)`.
- If selector state is nonzero, it calls selector-1/2 driver `arcade_pc 0x055990`, then increments `%a5@(0x10CA)`.
- After either path, it calls `arcade_pc 0x0558A2` and returns.

Selector-0 driver at `arcade_pc 0x055968`:

- Loads `%a0` from `%a5@(0x10A0)`.
- Uses 16 descriptor segments from rebuilt tables at `0x10D080` and `0x10D040`.
- Calls cell producer `arcade_pc 0x0559B2`.
- Saves updated `%a0` back to `%a5@(0x10A0)`.

Selector-1/2 driver at `arcade_pc 0x055990`:

- Loads `%a0` from `%a5@(0x10A4)`.
- Uses the same 16 descriptor-segment tables.
- Calls direction-aware cell producer `arcade_pc 0x055A14`.
- Does not save `%a0` back to `%a5@(0x10A4)` in the same way selector-0 saves `%a5@(0x10A0)`.

Selector-0 cell producer at `arcade_pc 0x0559B2`:

- Produces four logical cells per descriptor segment.
- Writes collision and C-window tile output.
- Its logical coordinate model has already been proven by Andy.

Selector-1/2 cell producer at `arcade_pc 0x055A14`:

- Produces direction-sensitive vertical/update behavior.
- Uses `%a5@(0x10A8)` to choose direction treatment.
- Contains different C-window/collision address movement than selector-0.
- Its logical coordinate model is not yet proven with the same rigor as selector-0.

## Selector-0 Status

Selector-0 native route exists in Build 0244:

- `specs/rastan_direct_remap.json` routes `arcade_pc 0x055968` to `genesistan_hook_tilemap_plane_a_selector0_native`.
- The hook preserves registers and returns to the original arcade caller after the replaced selector-0 tail.
- The hook writes final Genesis Plane A words into `staged_fg_buffer` and marks dirty rows for VBlank commit.
- The hook also publishes collision into `ARCADE_COLLISION_MAP_BASE`, preserving the semantic collision side effect.

Previously proven selector-0 semantics from `docs/design/Andy_plane_a_selector0_logical_coordinate_proof.md`:

- `logical_column = ((%a5@(0x10CC) * 4) + %a5@(0x10CA)) & 0x3F`
- `logical_row = segment_index * 4 + cell_index`
- Collision destination: `0x10DE00 + ((logical_row * 64 + logical_column) * 2)`
- Scene-fill/gameplay samples matched with zero mismatches.

### Selector-0 Correction Still Needed

Build 0244 selector-0 computes a visible-top logical row from `staged_scroll_y_fg`, then tests residency with:

`(logical_row - visible_top_logical_row) & 0x3F < 32`

However, when it writes to `staged_fg_buffer`, it uses:

`physical_row = logical_row & 0x1F`

rather than the resident-window row:

`physical_row = (logical_row - visible_top_logical_row) & 0x1F`

Interpretation: this is the first exact source-level selector-0 output mismatch candidate. It can explain native Plane A visibility incoherence when the logical window top is nonzero. It is a bounded correction candidate, but it is not enough to satisfy the task's build gate by itself because selector-1/2 and reversal remain unproven.

## Selector-1/2 Status

Selector-1/2 remains transitional in Build 0244.

Current route:

- `arcade_pc 0x055990` is replaced with `jsr genesistan_hook_tilemap_fg`.
- Gameplay path in `genesistan_hook_tilemap_fg` calls `genesistan_stage_fg_src_column`.
- `genesistan_stage_fg_src_column` still stages through `genesistan_hook_tilemap_fg_fill_tall`.
- `genesistan_hook_tilemap_fg_fill_tall` writes `staged_fg_tall_buffer` and marks `fg_tall_dirty`.

This is not final native architecture because it is still a PC080SN/C-window-shaped transitional pipeline rather than a complete semantic-tail replacement that directly publishes final Genesis Plane A rows/columns/jobs.

## Tall-FG Projection Status

`vdp_project_fg_tall_if_dirty` still exists for compatibility, but Build 0244 added `fg_native_gameplay_owner` gating:

- In non-gameplay, the old tall projection may still run for frontend compatibility.
- In gameplay, once `fg_native_gameplay_owner != 0`, the tall projector is skipped to avoid overwriting native selector-0 output.

This prevents stale tall projection from clobbering selector-0 native output, but it also means selector-1/2 gameplay output that still depends on `staged_fg_tall_buffer` can be dropped or become incomplete once native ownership is active.

Therefore, gameplay Plane A is not yet fully migrated away from the tall transitional path.

## VBlank And Scroll Status

`_vblank_service` still performs:

- tile cache commit
- BG tall projection
- BG strip commit
- FG tall projection gate
- FG strip commit
- sprite commit
- palette commit
- scroll commit
- tail jump to arcade VBlank

Plane A commit is VBlank-backed through dirty rows in `staged_fg_buffer`, which is consistent with project architecture.

Gameplay vertical scroll is still residualized in `vdp_commit_scroll`:

- `staged_scroll_y_fg & 0x0007`
- `staged_scroll_y_bg & 0x0007`

This may be correct only if native Plane A/B producers maintain the visible resident window in the staging buffers. For selector-0, the intended resident-window calculation exists but the physical-row write appears inconsistent. For selector-1/2, the native resident-window contract has not been proven.

No Plane B changes were made or proposed in this task.

## Initial Fill / Horizontal / Vertical / Reversal Evidence

Current evidence status:

- Initial fill: selector-0 source/route exists and previous selector-0 coordinate proof includes scene-fill samples.
- Horizontal streaming: selector-0 column publication and 63->0 wrap are previously proven.
- Downward/upward vertical streaming: not fully proven for selector-1/2 under native semantics.
- Direction reversal: not fully proven for selector-1/2 under native semantics.
- Selector-1/2 producer cell mapping: not yet matched to a native logical row/column contract with arcade and Genesis runtime evidence.

The task's implementation gate therefore is not satisfied.

## First Exact Divergence

Proven source-level divergence from final architecture:

1. Selector-0 is only partially native: output row placement appears to use logical low five bits rather than resident-window row relative to the current visible top.
2. Selector-1/2 remains routed through the old tall transitional Plane A path.
3. Gameplay tall projection is suppressed after native owner activation, so selector-1/2 transitional output is not a reliable gameplay Plane A producer once selector-0 native ownership starts.

The earliest complete migration blocker is selector-1/2 logical-coordinate proof at `arcade_pc 0x055A14` / `runtime_genesis_pc 0x055C14`, including the direction/reversal branches.

## STOP Decision

STOP triggered: `YES`.

Reason: the required build gate is not met. Completing only selector-0 or patching the selector-0 physical-row mismatch would produce another partial Plane A ROM, which the prompt explicitly forbids.

No implementation was performed. No ROM was produced. Build counter remains `244`.

## Smallest Safe Next Boundary

The next safe task is a focused selector-1/2 logical-coordinate proof, not another implementation pass.

Minimum trace/proof needed:

- Original arcade and Build 0244 matched traces around:
  - `arcade_pc 0x055990` / `runtime_genesis_pc 0x055B90`
  - `arcade_pc 0x055A14` / `runtime_genesis_pc 0x055C14`
- Capture `%a5@(0x10A8)`, `%a5@(0x10CA)`, `%a5@(0x10CC)`, `%a5@(0x10A4)`, relevant scroll fields, `%a0`, `%a1`, `%a3`, segment index, cell index, collision destination/value, and tile/attribute source output.
- Include downward vertical, upward vertical, and direction reversal windows.
- Derive native `logical_row`, `logical_column`, `physical_row`, dirty-row/column jobs, and collision address formula.
- Compare against the arcade C-window/collision oracle before removing selector-1/2 chip-tail behavior.

Once selector-1/2 is proven, a Build 0245 implementation can safely include:

- selector-0 physical-row correction if confirmed by trace;
- selector-1/2 native tail replacement;
- gameplay tall-FG projection removal/disablement for all gameplay Plane A producers;
- proof that frontend compatibility still uses isolated non-gameplay paths only.

## Architecture Compliance

Compliant in this task:

- No software PC080SN device was added.
- No C-window/name-RAM shadow was introduced as final architecture.
- No direct active-display VDP writes were added.
- No Genesis-owned gameplay scheduling was introduced.
- Existing transitional compatibility paths were identified and isolated in this report.
- No partial ROM was produced in violation of the prompt's build gate.

## Open / Closed Issues Impact

Open issues touched:

- `OPEN-001`: ongoing graphics/runtime parity and native PC080SN migration.

New issues opened: none.

Issues closed: none.

Issues intentionally deferred:

- Selector-1/2 native Plane A tail implementation.
- Plane B/native BG migration.
- PC090OJ/native sprite policy work.
- Rope/collision/map progression work.

## KNOWN_FINDINGS Impact

Option A - No new finding to index.

Rationale: this task records a build-gate STOP and narrows the next required proof boundary. It does not establish a durable new architecture fact beyond the already-indexed native replacement and transitional-path findings.
