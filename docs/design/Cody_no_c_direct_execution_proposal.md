# Cody No-C Direct-Execution Proposal

## 1. Executive Summary
This proposal defines `apps/rastan-direct/` as a pure-assembly direct-execution branch: no C files, no C runtime, no SGDK runtime ownership, no launcher, and no DIP menu UI. The execution model follows Rainbow Islands Genesis conversion style: game logic runs outside VBlank, and VBlank performs commit-only hardware publication.

## 2. Proposed Parallel App Structure
Proposed branch root: `apps/rastan-direct/`

Proposed tree (assembly-only):
- `apps/rastan-direct/README.md`
- `apps/rastan-direct/Makefile`
- `apps/rastan-direct/linker_rastan_direct.ld`
- `apps/rastan-direct/src/vectors.s`
- `apps/rastan-direct/src/boot_entry.s`
- `apps/rastan-direct/src/main_loop.s`
- `apps/rastan-direct/src/vblank_commit.s`
- `apps/rastan-direct/src/vdp_commit_planes.s`
- `apps/rastan-direct/src/vdp_commit_sat.s`
- `apps/rastan-direct/src/vdp_commit_palette.s`
- `apps/rastan-direct/src/vdp_commit_scroll.s`
- `apps/rastan-direct/src/input_ports.s`
- `apps/rastan-direct/src/arcade_bridge.s`
- `apps/rastan-direct/src/z80_boot.s`
- `apps/rastan-direct/src/state_wram.s`

Constraints:
- No `.c` files.
- No CRT0 / C runtime.
- `apps/rastan/` remains untouched.

## 3. Rainbow Islands Model Mapping
Rainbow Islands-style elements mapped to Rastan-direct:
- Hand-owned vector table in ROM: mapped to `vectors.s`.
- Hand-owned reset/boot sequence: mapped to `boot_entry.s`.
- No SDK runtime dispatch: mapped to absence of SGDK ownership.
- Main-loop game execution outside interrupt context: mapped to `main_loop.s`.
- VBlank as commit-only phase: mapped to `vblank_commit.s` and per-domain commit modules.
- Direct hardware I/O handling: mapped to `input_ports.s`, VDP port writes, Z80 boot in assembly.

## 4. Execution Model
Boot/vector ownership:
- Reset vector owned by `apps/rastan-direct/src/vectors.s`.
- Entry point owned by `boot_entry.s`.
- TMSS handling performed in `boot_entry.s` before enabling display path.

Runtime execution:
- Arcade tick runs in `main_loop.s`, outside VBlank.
- VBlank handler in `vblank_commit.s` performs commit-only operations.

Explicit ownership answers:
- Any game logic executes in VBlank: NO.
- SGDK used at runtime: NO.
- C used at runtime: NO.
- Launcher exists: NO.

## 5. VDP Ownership Model
State preparation (outside VBlank):
- Tilemap state prepared by arcade bridge/tick path in WRAM staging buffers.
- Sprite state prepared by arcade bridge/tick path in WRAM SAT staging buffer.
- Palette state prepared by arcade bridge/tick path in WRAM palette staging buffer.
- Scroll state prepared by arcade bridge/tick path in WRAM scroll staging words.

Hardware publication (VBlank only):
- Tilemap publish: `vdp_commit_planes.s`.
- Sprite SAT publish: `vdp_commit_sat.s`.
- Palette publish: `vdp_commit_palette.s`.
- Scroll publish: `vdp_commit_scroll.s`.

Commit order inside VBlank:
1. optional display-off bracket
2. tilemap planes
3. SAT publish
4. palette publish
5. scroll publish
6. display-on restore

VDP write rule:
- Any VDP write allowed outside VBlank: NO.

## 6. Input Model
Pad read strategy:
- Direct Genesis port reads in `input_ports.s` with active-low normalization.

Translation location:
- Input translation occurs in `main_loop.s` before arcade tick execution.
- Translated bits are written into arcade-facing WRAM shadow contract at fixed addresses.

Explicit input ownership answers:
- `JOY_update` exists: NO.
- SGDK input layer exists: NO.

## 7. Patch / Bridge Model
Patch infrastructure reuse:
- `startup_title_remap.json` patch infrastructure reused: YES.

Mapping model:
- Existing opcode replacement pipeline remains the source of patched arcade execution targets.
- Arcade hardware writes are redirected to branch WRAM staging contracts.
- Arcade hardware reads are redirected to branch-owned mirrors/constants (input, palette state, scroll state, mailbox state as applicable).

Useful current bridge concepts retained:
- Shift-table opcode replacement discipline.
- Declarative spec-driven remap ownership.
- Staging-before-commit separation by hardware domain.

## 8. Phased Implementation Plan
Phase 1: First bootable ROM milestone
- Deliver `vectors.s`, `boot_entry.s`, linker script, and infinite main loop in assembly.
- Confirm clean reset entry, TMSS path, interrupt vectors valid.

Phase 2: First VBlank interrupt milestone
- Install direct VBlank handler that acknowledges VBlank and returns.
- Confirm stable interrupt cadence and no SGDK dependencies.

Phase 3: First visible tilemap milestone
- Add WRAM tilemap staging buffers and VBlank plane commit module.
- Confirm stable non-rolling tile output with single VDP writer.

Phase 4: First input milestone
- Add `input_ports.s` direct pad reads and arcade-facing shadow write.
- Confirm mode/state transitions react to live controls.

Phase 5: First sprite milestone
- Add SAT staging in tick path and SAT publish in VBlank.
- Confirm sprite visibility and stable frame publication.

Phase 6: First audio/Z80 milestone
- Add Z80 boot/upload and command mailbox bridge in assembly.
- Confirm audio path starts and command writes are accepted.

## 9. Risks and Assumptions
Supported by current project evidence:
- Mixed VDP ownership caused unstable display behavior.
- One-writer VBlank commit discipline is required for stable output.
- Tick/commit separation is already established conceptually in current work.

Inferred from Rainbow Islands-style architecture:
- Full runtime ownership can be migrated to assembly-only boot/vectors/main/VBlank.
- Commit-only VBlank model can remain deterministic across all presentation domains.

Assumption/high-risk items:
- Full assembly boot replacement without SGDK safety scaffolding.
- Correct early interrupt/vector sequencing across all hardware variants.
- SAT publish correctness under strict single-owner timing.
- Z80 bring-up correctness without SGDK helpers.

## 10. Single Final Recommendation
Create `apps/rastan-direct/` as a pure-assembly direct-boot branch with no SGDK runtime ownership, no C runtime, no launcher, and one VBlank-owned hardware commit phase.

## 11. Final Verdict
The assembly-only direct branch is the correct architecture to eliminate ownership drift and enforce deterministic arcade-style execution. Building this in `apps/rastan-direct/` preserves `apps/rastan/` while enabling a Rainbow Islands-modeled runtime with strict main-loop tick and VBlank commit separation.
