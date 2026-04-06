# Cody No-SGDK Direct-Execution Proposal

## 1. Executive Summary
This proposal defines a parallel direct-execution branch under `apps/rastan-direct/` that boots straight into arcade execution with no launcher and no SGDK runtime ownership. The architecture uses one frame model: arcade logic/tick runs outside VBlank, and only a single assembly VBlank handler publishes staged hardware state (tilemaps, SAT, palette, scroll) to VDP. `apps/rastan/` remains unchanged.

## 2. Proposed Parallel App Structure
Proposed branch path: `apps/rastan-direct/`

Proposed module layout:
- `apps/rastan-direct/Makefile` — independent build target and ROM artifact naming.
- `apps/rastan-direct/linker_rastan_direct.ld` — direct branch linker script with its own vector/boot layout.
- `apps/rastan-direct/src/vectors.s` — vector table and interrupt vector ownership.
- `apps/rastan-direct/src/boot_entry.s` — TMSS, Z80 gate, VDP register baseline, memory init, direct jump to arcade startup.
- `apps/rastan-direct/src/main_loop.c` — non-VBlank frame loop: input read, arcade tick, stage flags.
- `apps/rastan-direct/src/vblank_commit.s` — single VBlank-owned commit phase.
- `apps/rastan-direct/src/vdp_commit_planes.s` — staged BG/FG nametable publish.
- `apps/rastan-direct/src/vdp_commit_sat.s` — SAT publish (DMA-owned in VBlank only).
- `apps/rastan-direct/src/vdp_commit_palette.s` — CRAM publish from staged palette.
- `apps/rastan-direct/src/vdp_commit_scroll.s` — H/V scroll publish.
- `apps/rastan-direct/src/input_io.s` — direct pad port reads and active-low normalization.
- `apps/rastan-direct/src/arcade_bridge.s` — handoff helpers and bridge symbols used by patched arcade code.
- `apps/rastan-direct/src/arcade_state.c` — shared staging/state structs and frame flags.

`apps/rastan/` remains untouched.

## 3. Execution Model
Boot entry model:
- Reset vector enters `boot_entry.s` in `apps/rastan-direct`.
- Boot initializes hardware and transfers directly to arcade startup sequence.

Runtime model:
- Arcade tick runs in main loop outside VBlank.
- VBlank handler runs commit-only code and returns quickly.

Runtime ownership answers:
- SGDK used at runtime: NO.
- Launcher exists: NO.

Frame contract:
- Main loop: read input, run arcade execution slice, stage output buffers/flags.
- VBlank: consume staged buffers once, publish to hardware, clear frame flags.

## 4. VDP Ownership Model
State preparation owner:
- Arcade tick path outside VBlank prepares/stages frame state only.

Hardware publish owner:
- `_VINT_direct` in `vblank_commit.s` is the single hardware commit owner.

Publish placement:
- Tilemap commit: VBlank only (`vdp_commit_planes.s`).
- Sprite SAT publish: VBlank only (`vdp_commit_sat.s`).
- Palette commit: VBlank only (`vdp_commit_palette.s`).
- Scroll commit: VBlank only (`vdp_commit_scroll.s`).

Publish sequence for each VBlank:
1. optional display-off bracket
2. planes
3. SAT
4. palette
5. scroll
6. display-on restore

No VDP writes are permitted in tick path.

## 5. Input Model
Input read source:
- Direct 3-button pad reads from I/O ports in `input_io.s` (active-low bit handling in branch-local code).

`JOY_update` in this branch:
- NO.

Translation point:
- Input is translated to arcade-facing shadow registers in the main loop before arcade tick.
- Arcade logic reads the branch’s shadowed input contract, not SGDK cache state.

## 6. Migration Phases
Phase 1: Bootable direct branch milestone
- Deliver `vectors.s + boot_entry.s + main_loop.c` with no launcher.
- ROM boots to a stable direct loop with VBlank interrupt active.

Phase 2: First visible-output milestone
- Stage fixed test tilemap buffer outside VBlank.
- Publish planes in VBlank only.
- Confirm stable non-rolling display with single writer ownership.

Phase 3: First input milestone
- Add direct pad read in `input_io.s`.
- Map to arcade-facing input shadows.
- Confirm gameplay state transitions react to live controls.

Phase 4: First sprite milestone
- Add SAT staging in tick path and SAT publish in VBlank path.
- Confirm sprite visibility with no out-of-VBlank DMA.

Phase 5: Arcade parity milestone
- Route patched arcade producers to staging buffers used by the direct branch.
- Maintain one-writer VBlank commit discipline.

## 7. Risks and Assumptions
Proven by current project evidence:
- Split model (tick vs commit) already exists in current architecture and is observable.
- VDP ownership conflicts caused instability when non-VBlank writers existed.
- Commit functions can execute once per frame under controlled VBlank ownership.

Assumptions in this proposal:
- Direct branch can fully replace SGDK startup/vector ownership without introducing boot regressions.
- Existing patched producer outputs can be reused with minimal bridge-layer changes.
- Sound boot/handoff can be retained with branch-local init sequence.

Highest-risk areas:
- Correct hardware startup sequence without SGDK safety scaffolding.
- Interrupt/vector correctness during early boot and first VBlank.
- SAT publish timing and link-table correctness when moved to strict VBlank-only ownership.
- Maintaining binary compatibility of patched arcade expectations across a new app branch.

## 8. Single Final Recommendation
Create `apps/rastan-direct/` as a minimal C+assembly direct-boot branch with no SGDK runtime ownership, no launcher, and one VBlank-owned hardware commit phase.

## 9. Final Verdict
The direct branch is the clean path to remove mixed runtime ownership and isolate arcade execution from SGDK-side state machinery. Building this in `apps/rastan-direct/` preserves `apps/rastan/` while enabling deterministic single-owner VDP publishing and direct arcade boot.
