# Andy — Rastan-Direct Runtime Decomposition Design

**Agent:** Andy
**Type:** Analysis + Design (no implementation)
**Build context:** current `rastan-direct`
**Target files:** [apps/rastan-direct/src/main_68k.s](apps/rastan-direct/src/main_68k.s), [apps/rastan-direct/src/boot/boot.s](apps/rastan-direct/src/boot/boot.s), [apps/rastan-direct/src/crash_handler.s](apps/rastan-direct/src/crash_handler.s)

**Supersedes:** [Andy_init_staging_state_split_design.md](docs/design/Andy_init_staging_state_split_design.md) — the lifecycle-split latch design is obsolete under the tighter RULES.md reading. That design's `boot_initialized` byte is a Genesis-side "safe re-entry" mechanism forbidden by RULES §7.

**Architecture compliance:** CONFIRMED against [RULES.md](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md). No proposed change preserves Genesis-owned control flow.

---

## Summary

Current `rastan-direct` violates RULES.md §1, §2, §3, §6, §7 by giving
Genesis code a runtime loop, a separate VBlank owner, and a
boot/init re-entry path on arcade warm restart. The fix is to:

1. Hand execution to arcade code *permanently* after cold boot.
   Genesis code never owns a loop.
2. Route the level-5 (VBlank) auto-vector through a thin
   VDP-commit servicing stub that tail-JMPs into arcade's own L5
   handler at arcade_pc `0x0003A008`.
3. Opcode-replace arcade's warm-restart trampoline at arcade_pc
   `0x00039F9E` so it no longer reads `ROM[0x0004]` (which on
   Genesis is the cold-boot vector) but instead directly re-enters
   arcade startup_common at arcade_pc `0x0003A000`.
4. Split `main_68k.s` into three production modules: `vdp_comm.s`,
   `tilemap_hooks.s`, `scene_load.s`. Delete the Genesis-owned loop,
   delete `_VINT_handler` as a top-level handler, delete
   `arcade_tick_logic`, delete `frame_counter`, delete
   `init_staging_state` in its current form.
5. Boot.s grows a single boot-only helper, `_bootstrap`, that sets up
   VDP, clears staging buffers *once*, loads the initial title
   scene, and JMPs (never BSRs/JSRs) into arcade startup_common.

After this, no Genesis symbol owns a loop. No Genesis symbol owns a
VBlank identity. Arcade code has continuous control.

---

## Exact files modified

- [apps/rastan-direct/src/boot/boot.s](apps/rastan-direct/src/boot/boot.s) — vector table level-5 target change; cold-boot handoff; new `_bootstrap` helper body.
- [apps/rastan-direct/src/main_68k.s](apps/rastan-direct/src/main_68k.s) — deleted entirely; contents split into the three files below.
- [apps/rastan-direct/src/vdp_comm.s](apps/rastan-direct/src/vdp_comm.s) **(new)** — VDP register services + staging commit helpers + vblank service stub.
- [apps/rastan-direct/src/tilemap_hooks.s](apps/rastan-direct/src/tilemap_hooks.s) **(new)** — opcode-replacement hooks for PC080SN / PC090OJ / text writers / number renderer / C-window clear.
- [apps/rastan-direct/src/scene_load.s](apps/rastan-direct/src/scene_load.s) **(new)** — `load_scene_tiles`, scene preload tables, scene range tables.
- [apps/rastan-direct/src/crash_handler.s](apps/rastan-direct/src/crash_handler.s) — **unchanged body**; one source-level adjustment: drop its reference to `frame_counter`, replace with a zero or a preserved raw IRQ counter (see Phase 6).
- `specs/rastan_direct_remap.json` — **one** new `opcode_replace` entry at arcade_pc `0x00039F9E` (warm-restart retarget). Not a design-scope code edit but required for the architecture to be valid; flagged for Cody.
- `apps/rastan-direct/Makefile` — source list updated to include new files.

No other files change.

---

## Exact Symbols / Functions / Labels Added or Changed

| Kind             | Symbol                                  | Action                     |
| ---------------- | --------------------------------------- | -------------------------- |
| Function         | `main_68k`                              | **REMOVED**                |
| Function         | `_VINT_handler`                         | **REMOVED** (top-level identity gone; body moves into `_vblank_service` in `vdp_comm.s`) |
| Function         | `arcade_tick_logic`                     | **REMOVED**                |
| Function         | `init_staging_state`                    | **REMOVED**                |
| Function         | `rastan_direct_update_inputs`           | **REMOVED** from call ownership — body kept as helper called from opcode-replace site (see Phase 2) |
| BSS              | `frame_counter`                         | **REMOVED**                |
| BSS              | `tick_counter`                          | **REMOVED**                |
| Constant         | `rastan_direct_arcade_tick_entry`       | **REMOVED** (dead: no Genesis caller after `arcade_tick_logic` removal) |
| Function         | `_bootstrap` (new, in `boot.s`)         | ADDED — cold-boot helper; non-looping |
| Function         | `_vblank_service` (new, in `vdp_comm.s`) | ADDED — level-5 vector target; VDP commit + tail JMP to arcade L5 |
| Function         | `vdp_boot_setup`                        | MOVED to `vdp_comm.s`; called once from `_bootstrap` |
| Function         | `vdp_set_reg`                           | MOVED to `vdp_comm.s` |
| Function         | `vdp_set_vram_write_addr`               | MOVED to `vdp_comm.s` |
| Function         | `vdp_commit_tiles_if_dirty`             | MOVED to `vdp_comm.s` |
| Function         | `vdp_commit_bg_strips_if_dirty`         | MOVED to `vdp_comm.s` |
| Function         | `vdp_commit_fg_strips_if_dirty`         | MOVED to `vdp_comm.s` |
| Function         | `vdp_commit_palette`                    | MOVED to `vdp_comm.s`; gated by `palette_dirty` test inside `_vblank_service` |
| Function         | `vdp_commit_scroll`                     | MOVED to `vdp_comm.s` |
| Function         | `sprite_dma_addr_high_bits_fix`         | MOVED to `vdp_comm.s` |
| Function         | `load_scene_tiles`                      | MOVED to `scene_load.s` |
| Function         | All `genesistan_hook_tilemap_*`         | MOVED to `tilemap_hooks.s` |
| Function         | All `genesistan_hook_text_writer_*`     | MOVED to `tilemap_hooks.s` |
| Function         | `genesistan_hook_number_renderer_3c2e2` | MOVED to `tilemap_hooks.s` |
| Function         | `genesistan_hook_cwindow_clear`         | MOVED to `tilemap_hooks.s` |
| Rodata tables    | `genesistan_pc080sn_tile_vram_lut`, `_attr_lut`, `_tile_rom`, scene preloads, scene_a0_ranges | MOVED to `scene_load.s` |
| BSS              | `genesistan_scene_a0_lo`, `_hi`, `genesistan_current_scene_id` | MOVED to `scene_load.s` |
| BSS              | `staged_*` (bg/fg buffer, palette, tile words, scroll, dest ptrs) | MOVED to `vdp_comm.s` |
| BSS              | `palette_dirty`, `tiles_dirty`, `bg_row_dirty`, `fg_row_dirty` | MOVED to `vdp_comm.s` |
| BSS              | `genesistan_shadow_input_*`, `genesistan_shadow_dip*`, `prev_coin_p1_a_pressed` | MOVED to `tilemap_hooks.s` (or a future `input.s`; lives with the opcode-replace hook that consumes them) |
| Opcode-replace   | arcade_pc `0x00039F9E` warm-restart trampoline | **ADDED** (direct `JMP arcade_pc 0x3A000`) |
| Vector           | boot.s vector 29 (level-5 auto-vector)  | CHANGED `_VINT_handler` → `_vblank_service` |
| Vector           | boot.s reset PC (`.long _start`)        | UNCHANGED |
| Vector           | arcade `ROM[0x0004]` (file offset 4) — unused after opcode-replace of `0x39F9E` | N/A — Genesis `_start` address remains at that offset; arcade no longer reads it |

---

## Permanent vs Temporary Classification

Every added item is **PERMANENT** production code:

- `_bootstrap` — permanent cold-boot helper
- `_vblank_service` — permanent level-5 vector target
- New source files — permanent module layout

No scaffolding, no diagnostic, no bring-up, no test-mode code introduced.

---

## Scaffolding Inventory

None. The only thing this design removes is existing infrastructure
that was already architecturally invalid. Nothing new is scaffolding.

---

## Removal / Revert Plan

Not applicable — all items are permanent. If the decomposition is ever
rolled back, the `main_68k.s`-as-single-file layout can be
reconstituted by merging the three new files, but that would
re-introduce the RULES violations and should not be done.

---

## Build Artifact Path

N/A — design only. No build produced.

---

## Verification Status

N/A — design only. Cody will implement, build, and run MAME / BlastEm
verification in a follow-up task.

---

## Risks / Known Limitations

See Phase 7 for per-decision risks. Three implementation-time
prerequisites Cody must resolve before the design is executable:

**P1.** Confirm arcade-side startup_common at arcade_pc `0x0003A000`
executes correctly post-translation under the current
`specs/rastan_direct_remap.json`. This was not a concern under the
previous Genesis-owned-loop architecture because Genesis code substituted
for it ([main_68k.s:2094-2167](apps/rastan-direct/src/main_68k.s#L2094-L2167)
arcade-workram factory-defaults block). Under the new architecture
arcade's own startup_common is the authoritative source of that state,
and must run to completion each warm restart.

**P2.** Confirm arcade L5 handler at arcade_pc `0x0003A008` writes to
hardware addresses that are all covered by existing opcode_replace
hooks, so arcade's intent translates correctly when it runs as the
actual interrupt handler. Spot-check the first ~40 instructions of
arcade_pc `0x0003A008` for writes to unhooked hardware.

**P3.** Decide how the `rastan_direct_update_inputs` body is invoked
under the new architecture. Currently it is called from the deleted
`arcade_tick_logic`. The correct pattern is a Genesis shadow-write
helper invoked via opcode_replace at the arcade input-read site — or
inline-replacement of arcade's input-read logic. Detail in Phase 2
under `rastan_direct_update_inputs`.

---

# Design Phases

## Phase 1 — Architectural violations in current code

Every violation identified. Format: **Symbol / Lines / Current
behavior / Why it violates / Replacement direction**.

### 1.1 `main_68k` entry + `.Lmain_loop` spin

- **Symbol/lines:** `main_68k` at [main_68k.s:75-92](apps/rastan-direct/src/main_68k.s#L75-L92)
- **Current behavior:** Genesis entry point. Disables IRQ, calls `vdp_boot_setup`, `load_scene_tiles`, `init_staging_state`, re-enables IRQ, then enters `.Lmain_loop` which spins on `frame_counter` change and calls `arcade_tick_logic` each VBlank.
- **Violates:** §1 (arcade owns execution — Genesis cannot own a loop), §2 (no separate Genesis runtime — `.Lmain_loop` is one), §4 (helper functions only — loops forbidden), §9 (would not exist in final production ROM).
- **Replacement direction:** REMOVE. Cold-boot body moves into `_bootstrap` helper that runs once and JMPs to arcade startup_common. `.Lmain_loop` deleted entirely — arcade's own loop (gameplay code between IRQs + warm-restart cycle) is the only loop.

### 1.2 `_VINT_handler` as top-level level-5 vector

- **Symbol/lines:** `_VINT_handler` at [main_68k.s:94-122](apps/rastan-direct/src/main_68k.s#L94-L122); vector table entry 29 in [boot.s:67](apps/rastan-direct/src/boot/boot.s#L67).
- **Current behavior:** directly wired as the level-5 auto-vector. Owns the VBlank frame: saves regs, disables display, commits tiles/BG/FG/palette, re-enables display, commits scroll, increments `frame_counter`, RTEs.
- **Violates:** §3 (arcade VBlank is the only frame authority; Genesis VBlank can only service hardware), §1 (frame_counter increment is frame-progression ownership).
- **Replacement direction:** Body kept as a VDP-servicing helper, renamed `_vblank_service`, which at its tail JMPs to arcade_pc `0x0003A008` (arcade's own L5 handler). Level-5 vector points to `_vblank_service`. The `frame_counter` increment is DELETED (no Genesis consumer remains).

### 1.3 `arcade_tick_logic` (Genesis-side caller of arcade)

- **Symbol/lines:** `arcade_tick_logic` at [main_68k.s:1964-1971](apps/rastan-direct/src/main_68k.s#L1964-L1971).
- **Current behavior:** Called from `.Lmain_loop`. Calls `rastan_direct_update_inputs`, PEAs a return label, pushes SR, JMPs to `rastan_direct_arcade_tick_entry = 0x0003A208` (Genesis ROM) = arcade_pc `0x0003A008`. On arcade RTE, lands at `.Ltick_return`.
- **Violates:** §1 (Genesis schedules arcade tick), §3 (Genesis simulating an arcade VBlank handler invocation), §4 (not a service routine — it owns scheduling), §7 (manufactured arcade-call state machine).
- **Replacement direction:** REMOVE entirely. Arcade's L5 handler at arcade_pc `0x0003A008` runs because level-5 IRQ vector routes through `_vblank_service` → JMP arcade_pc `0x3A008` naturally. No Genesis caller needed.

### 1.4 `frame_counter` BSS word + `.Lwait_vblank` spin

- **Symbol/lines:** [main_68k.s:85-89, 119, 2233-2234](apps/rastan-direct/src/main_68k.s#L85-L89)
- **Current behavior:** VBlank handshake pacer; `.Lmain_loop` reads it, spins until it changes (VBlank increments it), then calls `arcade_tick_logic`.
- **Violates:** §1 (Genesis-side frame pacing), §2 (separate Genesis runtime mechanism), §7 (hidden Genesis-side lifecycle).
- **Replacement direction:** REMOVE both the BSS word and the increment site. No consumer in the new architecture. Crash handler's `frame_counter` read at [crash_handler.s:209-210](apps/rastan-direct/src/crash_handler.s#L209-L210) must be updated — see Phase 6.

### 1.5 Warm-restart re-entry into `main_68k`

- **Symbol/lines:** Arcade-side at arcade_pc `0x00039F9E` (MOVEA.L (0x0004).W, A0; JMP (A0)); Genesis side at the top of `main_68k`.
- **Current behavior:** Arcade's trampoline reads `ROM[0x0004]` = `_start` (Genesis cold-boot entry!) and JMPs there every warm restart. That makes arcade code re-enter Genesis boot code every frame.
- **Violates:** §6 (no re-entry into boot/init during gameplay) — direct, literal violation.
- **Replacement direction:** Opcode-replace arcade_pc `0x00039F9E` with `JMP arcade_pc 0x0003A000` (direct hardcoded branch to arcade's own cold-init entry). Bypasses `ROM[0x0004]` indirection entirely. Genesis `_start` stays at ROM `0x0004` for 68000 reset semantics, but arcade code never reads the vector again.

### 1.6 `init_staging_state` running on warm restart

- **Symbol/lines:** [main_68k.s:2041-2169](apps/rastan-direct/src/main_68k.s#L2041-L2169)
- **Current behavior:** Called from `main_68k` line 81. Because `main_68k` is re-entered every warm restart, this runs every frame and clears staging buffers between arcade tick and next VBlank.
- **Violates:** §1, §6, §7. Plus the functional root cause of the current stripe pattern bug (confirmed in [Andy_stripe_root_cause_build0046.md](docs/design/Andy_stripe_root_cause_build0046.md)).
- **Replacement direction:** REMOVE. Its body splits:
  - **Genesis-side staging/VDP init** (staged_bg_buffer/fg_buffer/palette/tile word clears, Plane A clear, dirty flag clears, scroll clears, dest ptr init): moved into `_bootstrap` and runs exactly once at cold boot.
  - **Arcade workram factory defaults** (lines 2094-2167: coinage, DIP mirrors, init/delay/mode/bonus/diff/sprite marker/block A+B/title/config): DELETED. Arcade's own startup_common at arcade_pc `0x0003A000` is the authoritative source and runs on every warm restart (prerequisite P1 — verify).

### 1.7 Required explicit answers

**Why `main_68k` as currently written is invalid:** it is a Genesis-owned runtime loop (`.Lmain_loop`) that calls into arcade code (`arcade_tick_logic` JMP) as if arcade were a subroutine of Genesis. RULES §1 and §2 require the inverse — arcade runs continuously, Genesis code services arcade's hardware requests. There is no legitimate shape of `main_68k` that preserves its current loop ownership.

**Why `_VINT_handler` as currently written is invalid:** it declares itself as the VBlank frame owner (commits staging, increments `frame_counter`, is wired as the direct level-5 vector with no chain to arcade's own L5 handler). RULES §3 requires the arcade VBlank to be the only frame authority. Genesis's VBlank vector may only service hardware (VDP commit / DMA) and must pass control to arcade's VBlank handler.

**Labels in `main_68k.s` that are architecturally valid and must survive intact** (moved to the new modules, content unchanged):

- `vdp_boot_setup`, `vdp_set_reg`, `vdp_set_vram_write_addr`, `sprite_dma_addr_high_bits_fix`
- `vdp_commit_tiles_if_dirty`, `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty`, `vdp_commit_palette`, `vdp_commit_scroll`
- `load_scene_tiles`
- All `genesistan_hook_tilemap_*`, `genesistan_hook_text_writer_*`, `genesistan_hook_number_renderer_3c2e2`, `genesistan_hook_cwindow_clear`
- All `.Ltw_*` and `.L3c*_*` local text-writer helpers (live inside `tilemap_hooks.s` with their parent hook)
- All `staged_*` BSS buffers and all `*_dirty` flags
- All rodata: `genesistan_pc080sn_tile_vram_lut`, `_attr_lut`, `_tile_rom`, scene-preload blobs, `genesistan_scene_a0_ranges`
- All hook-consumed shadows: `genesistan_shadow_input_*`, `genesistan_shadow_dip*`, `prev_coin_p1_a_pressed`

---

## Phase 2 — Routine classification

Every major routine in `main_68k.s` and `boot.s`. Categories:
**BOOT-ONLY HELPER**, **RUNTIME HELPER (called by arcade, RTS)**,
**VBLANK COMMIT HELPER (called from _vblank_service, RTS)**,
**HOOK / OPCODE REPLACEMENT HELPER**, **CRASH-ONLY HELPER**,
**ARCHITECTURAL VIOLATION (remove or replace)**.

| Symbol                              | Current file   | Category                         | Keep/move/remove | Destination module | Justification |
| ----------------------------------- | -------------- | -------------------------------- | ---------------- | ------------------ | ------------- |
| `_start`                            | boot.s         | BOOT-ONLY HELPER                 | KEEP (body mostly)| boot.s            | 68000 reset vector target; SR/SP/TMSS; JSR `_bootstrap`; hang. Rewrite terminal `jsr main_68k` → `jsr _bootstrap` → not reached again. |
| `_bootstrap` (new)                  | —              | BOOT-ONLY HELPER                 | ADD              | boot.s             | Single cold-boot helper: calls `vdp_boot_setup`, initializes Genesis staging once, calls `load_scene_tiles` once (title scene), then `jmp` arcade_pc `0x0003A000`. No loop, no RTS back to `_start`. |
| `_boot_guard_legacy_rte`            | boot.s         | BOOT-ONLY HELPER (guard tag)     | KEEP             | boot.s             | Preserves invariant expected by `verify_rastan_direct_boot_guard.py`. |
| `main_68k`                          | main_68k.s     | ARCHITECTURAL VIOLATION          | REMOVE           | —                  | Genesis-owned loop. Replaced by `_bootstrap`. |
| `_VINT_handler`                     | main_68k.s     | ARCHITECTURAL VIOLATION (body reusable) | REMOVE as symbol; body re-forms inside `_vblank_service` | vdp_comm.s | Top-level VBlank owner. Replaced by `_vblank_service` which tail-JMPs to arcade's L5 handler. |
| `_vblank_service` (new)             | —              | VBLANK COMMIT HELPER             | ADD              | vdp_comm.s         | Level-5 vector target. Saves regs, commits staged tiles/BG/FG/palette/scroll to VRAM, restores regs, `jmp arcade_l5_handler` (arcade_pc `0x3A008` → Genesis ROM `0x3A208`). Arcade's handler RTEs. |
| `arcade_tick_logic`                 | main_68k.s     | ARCHITECTURAL VIOLATION          | REMOVE           | —                  | Genesis-called arcade dispatcher. No caller after loop deletion; L5 vector reaches arcade naturally. |
| `rastan_direct_update_inputs`       | main_68k.s     | RUNTIME HELPER (arcade-driven)   | MOVE + retarget call | tilemap_hooks.s (or future input.s) | Reads MD pads, writes to `genesistan_shadow_input_*`. Today invoked from `arcade_tick_logic`; must become a hook called via opcode_replace at arcade's input-read site. **Prerequisite P3** — Cody must identify arcade_pc that currently reads `0x390001/3/5/7` and add opcode_replace entry. Until then, `_vblank_service` MAY call it prior to the tail JMP to arcade L5 handler (this is still a Genesis VBlank servicing action, not frame ownership). Recommend the opcode_replace route for architectural cleanness. |
| `init_staging_state`                | main_68k.s     | ARCHITECTURAL VIOLATION (body split) | REMOVE; split body | Genesis-side staging portion → `_bootstrap`; arcade-workram factory defaults → DELETED (arcade's startup_common owns it) | See §1.6 / P1. |
| `vdp_boot_setup`                    | main_68k.s     | BOOT-ONLY HELPER                 | MOVE             | vdp_comm.s         | VDP register init. Called once from `_bootstrap`. Never called again. |
| `vdp_set_reg`                       | main_68k.s     | RUNTIME HELPER (shared)          | MOVE             | vdp_comm.s         | VDP register write primitive. Used by `vdp_boot_setup`, `load_scene_tiles`, and the crash renderer — service primitive, always RTSes. |
| `vdp_set_vram_write_addr`           | main_68k.s     | RUNTIME HELPER (shared)          | MOVE             | vdp_comm.s         | Same rationale. |
| `sprite_dma_addr_high_bits_fix`     | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | vdp_comm.s         | Sprite DMA address fix-up used by an opcode_replace. Service routine, RTS. |
| `vdp_commit_tiles_if_dirty`         | main_68k.s     | VBLANK COMMIT HELPER             | MOVE             | vdp_comm.s         | Called from `_vblank_service`. RTS. |
| `vdp_commit_bg_strips_if_dirty`     | main_68k.s     | VBLANK COMMIT HELPER             | MOVE             | vdp_comm.s         | Same. |
| `vdp_commit_fg_strips_if_dirty`     | main_68k.s     | VBLANK COMMIT HELPER             | MOVE             | vdp_comm.s         | Same. |
| `vdp_commit_palette`                | main_68k.s     | VBLANK COMMIT HELPER             | MOVE             | vdp_comm.s         | Same (gated by `palette_dirty` test inside `_vblank_service`). |
| `vdp_commit_scroll`                 | main_68k.s     | VBLANK COMMIT HELPER             | MOVE             | vdp_comm.s         | Same. |
| `load_scene_tiles`                  | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER (also BOOT-ONLY caller in `_bootstrap`) | MOVE | scene_load.s | DMA-loads scene tile set into VRAM. Called from `_bootstrap` (cold boot, title scene) and from `genesistan_hook_tilemap_plane_a` / `_tilemap_fg` scene-transition preambles (arcade-driven). |
| `genesistan_hook_tilemap_plane_a`   | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | BG C-window write opcode replacement. |
| `genesistan_hook_tilemap_fg`        | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | FG C-window write opcode replacement. |
| `genesistan_hook_tilemap_bg_fill`   | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | C-window fill opcode replacement. |
| `genesistan_hook_text_writer_3c4d2` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Text-writer opcode replacement. |
| `genesistan_hook_text_writer_3c550` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_text_writer_3c586` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_text_writer_3c636` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_text_writer_3c6dc` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_text_writer_3c75c` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_text_writer_3c7a4` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_text_writer_3c830` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_text_writer_3c950` | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_number_renderer_3c2e2` | main_68k.s | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| `genesistan_hook_cwindow_clear`     | main_68k.s     | HOOK / OPCODE REPLACEMENT HELPER | MOVE             | tilemap_hooks.s    | Same. |
| All `_crash_stub_*`                 | crash_handler.s | CRASH-ONLY HELPER               | KEEP             | crash_handler.s    | Fault-only. Not runtime. |
| `_crash_common`, `crash_*` helpers  | crash_handler.s | CRASH-ONLY HELPER               | KEEP             | crash_handler.s    | Fault-only. Write to `frame_counter` reference (see Phase 6) is the only coupling to runtime state; must be adjusted. |

---

## Phase 3 — Module split

| File                                   | Purpose                                  | Symbols it should contain                                                      | Symbols that must NOT be placed here                                    | File type |
| -------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------- | --------- |
| `boot.s`                               | CPU reset + cold boot handoff to arcade. | Vector table; `_start`; `_boot_guard_legacy_rte`; `_bootstrap`.                | Any runtime helper. Any VBlank helper. Any hook. No `main_68k`, no `_VINT_handler`, no loop of any shape. | BOOT-ONLY |
| `vdp_comm.s`                           | VDP register/DMA services + staged-output commit helpers + VBlank service stub. | `vdp_boot_setup`, `vdp_set_reg`, `vdp_set_vram_write_addr`, `sprite_dma_addr_high_bits_fix`, `vdp_commit_tiles_if_dirty`, `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty`, `vdp_commit_palette`, `vdp_commit_scroll`, `_vblank_service`. BSS: all `staged_*` buffers, `palette_dirty`, `tiles_dirty`, `bg_row_dirty`, `fg_row_dirty`, `staged_dest_ptr_bg`, `staged_dest_ptr_fg`. | Any hook function. Any loop owner. `load_scene_tiles` (depends on scene tables; lives with data). No input logic. | MIXED (boot-called + vblank-called) |
| `tilemap_hooks.s`                      | All opcode-replace helpers that translate arcade hardware writes to Genesis staging. | All `genesistan_hook_tilemap_*`, `genesistan_hook_text_writer_*`, `genesistan_hook_number_renderer_3c2e2`, `genesistan_hook_cwindow_clear`, `rastan_direct_update_inputs` (pending P3 resolution). BSS: `genesistan_shadow_input_*`, `genesistan_shadow_dip1`, `genesistan_shadow_dip2`, `prev_coin_p1_a_pressed`. | VDP commit helpers. Scene-load logic. Vector targets. No entry point. | RUNTIME HELPER |
| `scene_load.s`                         | Scene tile DMA + scene range tables.     | `load_scene_tiles`. Rodata: `genesistan_pc080sn_tile_vram_lut`, `genesistan_pc080sn_attr_lut`, `genesistan_pc080sn_tile_rom`, `genesistan_scene_preload_title`, `_gameplay`, `_endround`, `genesistan_scene_a0_ranges`. BSS: `genesistan_current_scene_id`, `genesistan_scene_a0_lo`, `_hi`. | Hooks. VDP commit helpers (shared primitives are imported from `vdp_comm.s`). No loop. | RUNTIME HELPER (called from `_bootstrap` at cold boot; from hook preambles during arcade scene transitions) |
| `crash_handler.s`                      | Fault-only crash screen.                 | All `_crash_stub_*`, `_crash_common`, `crash_vdp_reinit`, `crash_init_cram`, `crash_upload_font`, `crash_render_screen`, `crash_*` primitives, `crash_font_1bpp`, string tables, `genesistan_crash_handler_end`. | Any runtime/VBlank helper. Any arcade hook. Must not share BSS with runtime state (has its own crash-record block at `0xFF6800`). | CRASH-ONLY |

### Mandatory constraints confirmed

- `vdp_comm.s` contains only VDP service routines + the level-5
  service stub. No loop, no state machine.
- `crash_handler.s` remains separate and fault-only. Its sole
  reference to runtime BSS is `frame_counter` — adjusted in Phase 6.
- No new file hides a Genesis runtime owner. `_vblank_service` is the
  only vector-reachable Genesis entry after cold boot, and it is a
  pure VDP servicing stub that tail-JMPs to arcade code.

---

## Phase 4 — Correct control-flow ownership

Production call graph under RULES.md.

### Cold boot

```
step 1: CPU reset
        → reads ROM[0x0000] → SP = 0xFF0000
        → reads ROM[0x0004] → PC = _start (in boot.s at 0x00000202)

step 2: _start (boot.s)
        → move.w #0x2700, %sr       ; IRQ mask
        → lea 0x00FF0000, %sp       ; SP safety
        → TMSS unlock (if needed)
        → jsr _bootstrap

step 3: _bootstrap (boot.s)
        → bsr vdp_boot_setup        ; one-time VDP register init
        → bsr _init_genesis_staging ; one-time staging-buffer clear
                                    ; (staged_bg_buffer, staged_fg_buffer,
                                    ;  staged_palette_words, staged_tile_words,
                                    ;  all *_dirty flags, Plane A VRAM clear,
                                    ;  staged_scroll_*, staged_dest_ptr_bg/fg)
                                    ; NOTE: this function is local to
                                    ; _bootstrap; not a separate export.
        → moveq #0, %d0             ; scene id 0 = title
        → bsr load_scene_tiles      ; one-time title-tile DMA load
        → move.w #0x2000, %sr       ; enable IRQ
        → jmp arcade_pc_0x0003A000  ; = Genesis ROM 0x00003A200
                                    ; HANDOFF — never returns.

final step: arcade startup_common runs. Arcade initializes its own
            workram, sets up its gameplay state, falls through into the
            main arcade gameplay loop. Genesis no longer has control
            flow. Level-5 IRQ will fire periodically; crash stubs fire
            on fault; nothing else is a Genesis entry.
```

### Runtime

```
arcade-owned progression path:
  arcade_pc 0x3A000 (startup_common)
    → full arcade init + branches to post-init main loop body
    → arcade main loop executes arcade logic indefinitely
    → eventually reaches warm-restart trampoline at arcade_pc 0x39F9E:
        original:  MOVEA.L (0x0004).W, A0 ; JMP (A0)
        opcode-replaced: JMP arcade_pc 0x3A000
      and the cycle repeats — arcade's own loop.

helper calls made by arcade code (via opcode-replace in remap.json):
  - PC080SN C-window writes → genesistan_hook_tilemap_plane_a / _tilemap_fg / _tilemap_bg_fill
  - text producer routines → genesistan_hook_text_writer_*
  - number renderer → genesistan_hook_number_renderer_3c2e2
  - C-window clear → genesistan_hook_cwindow_clear
  - sprite DMA address fix-up → sprite_dma_addr_high_bits_fix
  - scene preload trigger (inside hook preambles) → load_scene_tiles
  - input-shadow read (prerequisite P3) → rastan_direct_update_inputs

Every helper is called (JSR or opcode_replace-synthesized JSR),
performs one hardware translation, and RTSes back to arcade code.
No helper contains a loop over arcade state. No helper schedules
arcade work.
```

### VBlank (morphed arcade VBlank)

```
step 1: Level-5 IRQ fires
        → 68000 auto-vector 29 → PC = _vblank_service
          (boot.s vector table entry changed from _VINT_handler)

step 2: _vblank_service (vdp_comm.s)
        → movem.l %d0-%d7/%a0-%a6, -(%sp)
        → moveq #VDP_REG_MODE2, %d0; moveq #VDP_MODE2_DISPLAY_OFF, %d1; bsr vdp_set_reg
        → bsr vdp_commit_tiles_if_dirty
        → bsr vdp_commit_bg_strips_if_dirty
        → bsr vdp_commit_fg_strips_if_dirty
        → tst.b palette_dirty; beq.s .Lskip_pal
        → bsr vdp_commit_palette; clr.b palette_dirty
        .Lskip_pal:
        → moveq #VDP_REG_MODE2, %d0; moveq #VDP_MODE2_DISPLAY_ON, %d1; bsr vdp_set_reg
        → bsr vdp_commit_scroll
        → movem.l (%sp)+, %d0-%d7/%a0-%a6
        → jmp arcade_l5_handler_entry
          (= Genesis ROM 0x0003A208 = arcade_pc 0x0003A008)
        NOTE: jmp, NOT jsr. Arcade's handler owns the RTE and returns
        to whichever arcade PC was interrupted.

what it must NOT do:
  - increment any frame counter
  - dispatch arcade work
  - maintain any Genesis state machine
  - call init functions or load_scene_tiles
  - touch staging BSS other than the commit helpers do
```

### Crash

```
fault-only path, isolated from runtime:
  Any CPU exception except level-5 → vector table entry →
  _crash_stub_* → _crash_common → VDP reinit → render screen → STOP.

Crash handler never participates in runtime. It does not share BSS
with runtime state (its record is at 0xFF6800, above BSS). Its sole
runtime coupling is the display of a few live-state values; that
coupling adjusts to remove the `frame_counter` reference (Phase 6).
```

### Required explicit answers

- **No Genesis-owned loop exists.** Arcade's own main loop
  (post-`0x3A000`) and arcade's warm-restart cycle are the only loops
  in the system.
- **No separate Genesis-owned VBlank identity exists.** `_vblank_service`
  is a pure VDP servicing stub with a mandatory tail JMP to arcade's
  own L5 handler. RULES §3 compliance is by construction.
- **No re-entry into boot/init during gameplay.** Arcade's warm-restart
  at arcade_pc `0x39F9E` is opcode-replaced to JMP directly to
  arcade's own startup_common, never into Genesis code. `_bootstrap`
  runs once at CPU reset and is never reached again.

---

## Phase 5 — Fate of current `main_68k`

**Outcome: REMOVED entirely.**

Every responsibility currently carried by `main_68k` is either
redistributed (cold-boot one-shot work → new `_bootstrap`;
Genesis-staging init → `_bootstrap`-local helper) or **deleted**
(Genesis-owned loop, Genesis-owned VBlank pacing, arcade-tick
dispatching, arcade-workram factory defaults).

| Aspect                                 | Value |
| -------------------------------------- | ----- |
| Outcome                                | REMOVED |
| New symbol name (if any)               | none (responsibilities split between `_bootstrap` in boot.s and `_vblank_service` in vdp_comm.s) |
| New purpose                            | N/A |
| Whether boot.s still calls it          | NO. `_start` calls `_bootstrap` instead. |
| What code remains in it                | none — file `main_68k.s` is deleted |
| What code moves out                    | all helpers (VDP services, commit helpers, hooks, `load_scene_tiles`, rodata tables, staged BSS) per Phase 3 table |
| What code is deleted entirely          | `.Lmain_loop`, `.Lwait_vblank`, `arcade_tick_logic`, `_VINT_handler` symbol and identity, `frame_counter`, `tick_counter`, `init_staging_state` as a single function (body split per §1.6), the arcade-workram factory-defaults block at main_68k.s:2094-2167 |

Rationale for deletion (not renaming): keeping a label named
`main_68k` as a thin alias for `_bootstrap` would be misleading —
nothing about the new function is a "main." The `main_68k` name
implies ownership. The removal is total to reinforce that Genesis
code does not own a main.

`rastan_direct_arcade_tick_entry` (`.equ` at main_68k.s:67) is also
deleted. It was the JMP target used by `arcade_tick_logic`; with the
latter gone and arcade's L5 handler now reachable via the vector
table, the constant has no caller.

---

## Phase 6 — VBlank commit helper design

Per-action classification of the current `_VINT_handler` body
([main_68k.s:94-122](apps/rastan-direct/src/main_68k.s#L94-L122)).

| Action                                                      | Keep / move / remove | Called from                   | Justification |
| ----------------------------------------------------------- | -------------------- | ----------------------------- | ------------- |
| `movem.l %d0-%d7/%a0-%a6, -(%sp)` (register save)           | KEEP                 | top of `_vblank_service`      | Required for IRQ-safe execution; arcade's L5 handler expects entry with the interrupted register state intact (we save our own scratch and restore before the tail JMP). |
| `move.w VDP_CTRL, %d0` (status read / discard)              | REMOVE               | —                             | Reads VDP status but discards. No architectural value; dead code even today. |
| `moveq #VDP_REG_MODE2, %d0; moveq #VDP_MODE2_DISPLAY_OFF, %d1; bsr vdp_set_reg` (display off) | KEEP | `_vblank_service` | Avoids tearing during DMA commits. |
| `bsr vdp_commit_tiles_if_dirty`                             | KEEP                 | `_vblank_service`             | Flushes staged tile updates to VRAM via DMA; bounded work, RTS. |
| `bsr vdp_commit_bg_strips_if_dirty`                         | KEEP                 | `_vblank_service`             | Flushes dirty BG rows to Plane B. |
| `bsr vdp_commit_fg_strips_if_dirty`                         | KEEP                 | `_vblank_service`             | Flushes dirty FG rows to Plane A. |
| `tst.b palette_dirty; beq.s .Lskip; bsr vdp_commit_palette; clr.b palette_dirty` | KEEP | `_vblank_service` | Conditional palette flush. |
| `moveq #VDP_REG_MODE2, %d0; moveq #VDP_MODE2_DISPLAY_ON, %d1; bsr vdp_set_reg` (display on) | KEEP | `_vblank_service` | Symmetric with display-off. |
| `bsr vdp_commit_scroll`                                     | KEEP                 | `_vblank_service`             | Commits staged scroll words to VSRAM / HSCROLL. |
| `addq.w #1, frame_counter`                                  | REMOVE               | —                             | Only consumer was `.Lmain_loop` (deleted) and `crash_handler.s` (CRASH_FRAME_COUNTER capture — retargetable). No runtime consumer remains. |
| `movem.l (%sp)+, %d0-%d7/%a0-%a6` (register restore)        | KEEP                 | `_vblank_service`             | Paired with the save. |
| `rte`                                                       | REMOVE               | —                             | Replaced by `jmp arcade_l5_handler_entry`. Arcade's handler owns the RTE so arcade-interrupted PC is correctly resumed. |

### Additional action: input-shadow refresh

Currently `rastan_direct_update_inputs` is called from the deleted
`arcade_tick_logic`. Its output (`genesistan_shadow_input_*`) is
consumed by arcade code reading work-RAM mirrors of the arcade input
ports. Two placement choices, in order of architectural preference:

- **Preferred (P3 resolved):** arcade-side opcode_replace at the
  arcade PC that reads the input port. The replacement calls
  `rastan_direct_update_inputs` to refresh the shadow, then lets the
  original arcade read (now reading from the shadow at `0x00390001`
  etc., which is Genesis-side mirrored memory) fall through.
- **Fallback (P3 unresolved):** call `rastan_direct_update_inputs`
  from `_vblank_service` prior to the tail JMP. This keeps it a
  VDP-adjacent servicing action (reading hardware pads at VBlank time
  is conventionally valid servicing work), still RTS-return, not a
  loop. Worse architectural signaling — a VDP-commit stub doing input
  work — but does not violate any numbered rule.

### `frame_counter` removal impact on crash handler

[crash_handler.s:209-211](apps/rastan-direct/src/crash_handler.s#L209-L211):

```
move.w  frame_counter, %d6
move.w  %d6, CRASH_FRAME_COUNTER
```

With `frame_counter` removed this must be adjusted. Two choices,
design-neutral for RULES:

- **Preferred:** replace with `clr.w CRASH_FRAME_COUNTER`. Crash
  screen shows `FRAME: 0000`. Accurate — arcade owns frame timing;
  Genesis side has no frame concept. The field is kept for future
  arcade-side frame-counter probe if one becomes available.
- **Alternative:** capture arcade work-RAM frame byte if arcade
  exposes one at a known A5 offset. Requires arcade_pc analysis not
  currently in scope.

Cody to implement the preferred option unless P1/P2 analysis
surfaces an arcade-side frame counter.

---

## Phase 7 — Risk assessment

| Decision                                         | Risk                                                                                       | Why acceptable / not acceptable                                                                         | Mitigation                                                                                                             | Requires impl-time verification |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| Remove Genesis-owned runtime loop                | Arcade's own main loop may reference hardware or state not fully translated, and without a Genesis safety net, execution may stall or diverge early. | Acceptable — the alternative is a permanent RULES violation. If arcade's main loop has unhooked writes, those are opcode_replace gaps that must be identified and fixed, not wrapped. | Prerequisite P1: verify arcade_pc `0x3A000` cold init runs cleanly under current remap. If it stalls, identify the missing hook; do not reintroduce a Genesis loop. | YES (P1) |
| Move VDP helpers into `vdp_comm.s`               | Helper call sites across files introduce linking-order or section-placement surprises.     | Acceptable — straightforward mechanical split; no semantic change.                                      | Cody verifies `.globl` declarations match consumers; linker script adjusted only if `.text.boot` vs `.text` placement requires it. | NO |
| Separate tilemap hooks into `tilemap_hooks.s`    | Hooks reference `staged_*` BSS (now in `vdp_comm.s`) and LUT tables (now in `scene_load.s`). | Acceptable — cross-module references are normal `.globl` imports.                                        | Cody adds `.extern` declarations where needed. No behavior change. | NO |
| Cold-boot handoff target = arcade_pc `0x3A000`   | If the translated arcade_pc `0x3A000` has a residual dependency on Genesis code that used to be in `init_staging_state` (workram factory defaults), arcade may initialize its own workram incorrectly and behave differently from Build 0046. | Needs verification — may be acceptable or may require a targeted fix. | Prerequisite P1. If arcade startup_common misses something, the fix is either a new opcode_replace or a trivial pre-JMP workram patch in `_bootstrap` (one-time, cold-boot only, does not violate §6). | YES (P1) |
| VBlank commit ownership transfer (to `_vblank_service` + tail JMP to arcade L5 handler) | Arcade L5 handler at arcade_pc `0x3A008` may write to unhooked hardware; or may expect Genesis to have already performed a specific action. | Verification-bounded. | Prerequisite P2: spot-check first ~40 instructions of arcade_pc `0x3A008` for unhooked hardware writes. If found, extend `specs/rastan_direct_remap.json`. | YES (P2) |
| Warm-restart opcode_replace at arcade_pc `0x39F9E` | 3-instruction replacement (MOVEA.L, MOVEA.L, JMP) must fit within original 10 bytes, or use shift-table. | Fits exactly: new code is `JMP arcade_pc 0x3A000` (6 bytes `4EF9 0003 A000`) + 4 NOP-pad bytes — but NOPs are banned per project rule. Use a 6-byte `JMP (xxx).L` + 4-byte... actually: preferred form is `4EF9 0003 A000` (`JMP $0003A000`) = exactly 6 bytes, leaving 4 bytes of the original instruction sequence. Shift-table reflow handles the 4-byte gap by shifting subsequent code. Or the opcode_replace covers the full 10-byte range and the replacement is `JMP $0003A000` + `BRA.S $4` padding that jumps over the next 2 bytes — still banned. **Architecturally cleanest:** opcode_replace covers all 10 bytes; replacement is `4EF9 0003 A000 60FC` — `JMP $0003A000` + `BRA.S .` where `.` refers to itself (infinite loop, unreachable after the JMP). The JMP is taken; the BRA never executes. This is structural padding, not a behavioral NOP, and is permitted per the padding-NOP exemption in [feedback_no_nops_rts](memory). Cody must confirm the padding is flagged as structural, not behavioral, and gets explicit approval per memory guidance. | Replacement bytes above; shift-table reflow alternative if approved. | YES (opcode_replace approval; byte verification) |
| Crash handler separation                         | `frame_counter` reference breaks at link time after BSS symbol deletion.                  | Acceptable — trivial adjustment per Phase 6.                                                            | Cody applies the Phase 6 preferred crash-handler adjustment. | NO |
| `rastan_direct_update_inputs` placement          | If fallback path is taken (called from `_vblank_service`), arcade-input freshness is tied to VBlank rate — matches existing behavior. If preferred path is taken, an opcode_replace must be identified and validated. | Both acceptable. Preferred is architecturally cleaner but requires P3 work.                               | P3 analysis when time allows. Fallback is safe in the interim. | YES (P3 for preferred) |

No decision is architecturally blocked. All three prerequisites are
bounded analysis tasks (no open-ended spelunking).

---

## Phase 8 — Final implementation-ready spec

### New file layout (exact)

#### `apps/rastan-direct/src/boot/boot.s`

- Vector table at `.org 0x000000`:
  - `.long 0x00FF0000` (initial SP)
  - `.long _start` (initial PC — unchanged)
  - `.long _crash_stub_*` for vectors 2-11 (unchanged)
  - `.long _crash_stub_other` for vectors 12-29, 31, 48-63 (unchanged)
  - `.long _vblank_service`  **← replaces `_VINT_handler` at vector 30**
  - `.long _crash_stub_trap_00` … `_crash_stub_trap_15` at vectors 32-47 (unchanged)
- ROM header block at `.org 0x000100` (unchanged, except optionally update date/version strings).
- `.org 0x000200`: `_boot_guard_legacy_rte` (unchanged).
- `_start`: unchanged body except terminal `jsr main_68k` → `jsr _bootstrap`.
- **New function** `_bootstrap` (boot-only helper):
  ```
  _bootstrap:
      bsr     vdp_boot_setup
      bsr     _bootstrap_clear_staging    ; local helper, body below
      moveq   #0, %d0
      bsr     load_scene_tiles
      move.w  #0x2000, %sr                ; enable IRQ
      jmp     (0x00003A200).l              ; JMP arcade_pc 0x0003A000
                                           ; Genesis ROM = arcade_pc + 0x200
      ; not reached
  ```
- **New local function** `_bootstrap_clear_staging` (boot-only helper, called once):
  - Clear `staged_bg_buffer` (2048 words = 0)
  - Clear `staged_fg_buffer` (2048 words = 0)
  - Clear `staged_palette_words` (64 words = 0)
  - Clear `staged_tile_words` (48 words = 0)
  - Clear Plane A VRAM via direct `move.w #0, VDP_DATA` loop (2048 words)
  - `clr.w staged_scroll_x_bg`, `staged_scroll_x_fg`, `staged_scroll_y_bg`, `staged_scroll_y_fg`
  - `clr.b palette_dirty`, `tiles_dirty`; `clr.l bg_row_dirty`, `fg_row_dirty`
  - `move.l #0x00C00000, staged_dest_ptr_bg`; `move.l #0x00C08000, staged_dest_ptr_fg`
  - rts

#### `apps/rastan-direct/src/vdp_comm.s`

- `.section .text,"ax"` with `.globl`s for `vdp_boot_setup`, `vdp_set_reg`, `vdp_set_vram_write_addr`, `sprite_dma_addr_high_bits_fix`, `vdp_commit_tiles_if_dirty`, `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty`, `vdp_commit_palette`, `vdp_commit_scroll`, `_vblank_service`.
- `.equ` constants for VDP registers / VRAM bases (moved from main_68k.s).
- All function bodies moved verbatim from [main_68k.s](apps/rastan-direct/src/main_68k.s) except:
  - `_VINT_handler` replaced by `_vblank_service` as specified in Phase 4.
  - `frame_counter` increment removed.
  - `move.w VDP_CTRL, %d0` status-read removed.
- `.section .bss` with: `palette_dirty`, `tiles_dirty`, `bg_row_dirty`, `fg_row_dirty`, `staged_dest_ptr_bg`, `staged_dest_ptr_fg`, `staged_scroll_x_bg/fg`, `staged_scroll_y_bg/fg`, `staged_bg_buffer`, `staged_fg_buffer`, `staged_palette_words`, `staged_tile_words`. Plus `.extern` of arcade L5 handler target for use inside `_vblank_service`.

```
_vblank_service:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_OFF, %d1
    bsr     vdp_set_reg

    bsr     vdp_commit_tiles_if_dirty
    bsr     vdp_commit_bg_strips_if_dirty
    bsr     vdp_commit_fg_strips_if_dirty

    tst.b   palette_dirty
    beq.s   .Lvs_skip_pal
    bsr     vdp_commit_palette
    clr.b   palette_dirty
.Lvs_skip_pal:

    moveq   #VDP_REG_MODE2, %d0
    moveq   #VDP_MODE2_DISPLAY_ON, %d1
    bsr     vdp_set_reg

    bsr     vdp_commit_scroll

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    jmp     (0x00003A208).l              ; arcade_pc 0x0003A008 = arcade L5 handler
```

#### `apps/rastan-direct/src/tilemap_hooks.s`

- `.section .text,"ax"` with `.globl`s for every `genesistan_hook_*`
  and (pending P3) `rastan_direct_update_inputs`.
- Bodies moved verbatim from main_68k.s including all `.L*` local
  labels (text-writer helpers, etc.).
- `.externs` for `staged_bg_buffer`, `staged_fg_buffer`,
  `bg_row_dirty`, `fg_row_dirty`, `genesistan_pc080sn_tile_vram_lut`,
  `_attr_lut`, `genesistan_scene_a0_lo`, `_hi`, `genesistan_scene_a0_ranges`,
  `load_scene_tiles`.
- `.section .bss` with: `genesistan_shadow_input_390001/3/5/7`,
  `genesistan_shadow_dip1/2`, `prev_coin_p1_a_pressed`.

#### `apps/rastan-direct/src/scene_load.s`

- `.section .text,"ax"` with `.globl load_scene_tiles`.
- Body moved verbatim.
- `.externs` for `vdp_set_reg`, `vdp_set_vram_write_addr` (from `vdp_comm.s`).
- `.section .rodata,"a"` with `.globl`s for the LUTs and scene preload blobs:
  - `genesistan_pc080sn_tile_vram_lut` (`.incbin`)
  - `genesistan_pc080sn_attr_lut` (`.incbin`)
  - `genesistan_pc080sn_tile_rom` (`.incbin`)
  - `genesistan_scene_preload_title` / `_gameplay` / `_endround` and their end labels (`.incbin`)
  - `genesistan_scene_a0_ranges` (`.long` table)
- `.section .bss` with `genesistan_current_scene_id`, `genesistan_scene_a0_lo`, `genesistan_scene_a0_hi`.

#### `apps/rastan-direct/src/crash_handler.s`

- Unchanged except: replace the two `frame_counter` references in
  `_crash_common` with `clr.w CRASH_FRAME_COUNTER`.

### Removed symbols / behaviors (exact)

| Symbol / behavior                         | Why removed |
| ----------------------------------------- | ----------- |
| `main_68k`                                | RULES §1 violation (Genesis-owned loop) |
| `.Lmain_loop`, `.Lwait_vblank`            | Same. |
| `arcade_tick_logic`, `.Ltick_return`      | RULES §1, §3 violation |
| `_VINT_handler` identity                  | RULES §3 violation |
| `init_staging_state`                      | RULES §6 violation (re-entry into init) and functional root cause of BG stripe bug |
| `frame_counter`, `tick_counter` BSS       | No consumer after loop deletion |
| `rastan_direct_arcade_tick_entry`         | Dead after `arcade_tick_logic` deletion |
| Arcade-workram factory-defaults block ([main_68k.s:2094-2167](apps/rastan-direct/src/main_68k.s#L2094-L2167)) | Duplicates arcade startup_common; arcade owns it |
| `arcade_tick_logic`'s `pea/move/jmp/Ltick_return` pattern | N/A after removal |

### Retained helpers (exact labels; destination file)

See Phase 3 file-contents table. Full list:

- `boot.s`: `_start`, `_boot_guard_legacy_rte`, `_bootstrap`, `_bootstrap_clear_staging`
- `vdp_comm.s`: `vdp_boot_setup`, `vdp_set_reg`, `vdp_set_vram_write_addr`, `sprite_dma_addr_high_bits_fix`, `vdp_commit_tiles_if_dirty`, `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty`, `vdp_commit_palette`, `vdp_commit_scroll`, `_vblank_service`
- `tilemap_hooks.s`: all 11 `genesistan_hook_*` symbols; `rastan_direct_update_inputs` (P3-pending)
- `scene_load.s`: `load_scene_tiles`; all rodata tables; scene BSS
- `crash_handler.s`: all 28+ crash stubs; `_crash_common`; all `crash_*` renderer helpers; crash font; crash string tables; `genesistan_crash_handler_end`

### Cold boot flow (exact call sequence)

```
CPU reset
  → PC = _start (from ROM[0x0004])
_start:
  → move.w #0x2700, %sr
  → lea 0x00FF0000, %sp
  → TMSS write if required
  → jsr _bootstrap
_bootstrap:
  → bsr vdp_boot_setup            ; vdp_comm.s
  → bsr _bootstrap_clear_staging  ; local
  → moveq #0, %d0
  → bsr load_scene_tiles          ; scene_load.s (title set)
  → move.w #0x2000, %sr
  → jmp (0x00003A200).l           ; arcade_pc 0x0003A000; no return
```

### Runtime flow (exact owner and helper-call pattern)

Owner: arcade code in arcade ROM, post-translation.

Helper-call pattern (examples):

- Arcade performs `move.w %d3, (a0)` at a PC080SN port → opcode_replace dispatches to `genesistan_hook_tilemap_plane_a` (JSR) → hook writes `staged_bg_buffer` + sets `bg_row_dirty` → RTS to arcade.
- Arcade performs a C-window clear → opcode_replace → `genesistan_hook_cwindow_clear` → buffer fill + dirty all rows → RTS.
- Arcade text writer runs → opcode_replace → `genesistan_hook_text_writer_3c4d2` → FG staging writes → RTS.
- Arcade detects scene transition (inside hook preamble) → hook's scene-range logic calls `load_scene_tiles` → DMA load → RTS back into hook body.
- Arcade issues warm-restart at arcade_pc `0x39F9E` → opcode_replace → `JMP arcade_pc 0x3A000` → arcade startup_common → arcade main loop continues.

### VBlank flow (exact owner and helper-call pattern)

Owner: arcade VBlank. Genesis services VDP commits as a pure stub.

Vector 29 (level-5 auto-vector) → `_vblank_service` → VDP commits → `jmp` arcade_pc `0x3A008` → arcade's own L5 handler → RTE to interrupted arcade PC.

### Crash flow (exact role and isolation from runtime)

Vectors 2-11, 31, 48-63 → `_crash_stub_*` → `_crash_common` →
VDP reinit → render screen → `stop #0x2700` → halt.

Isolated because: crash stubs are separate section (`.text.boot`);
crash record uses its own WRAM block at `0xFF6800+`; crash renderer
uses its own embedded font (no dependency on staging VRAM); crash
handler's only runtime-BSS coupling (`frame_counter`) is removed.

### Call-site changes (exact)

| Current call site                                                                       | Current target                   | New target                       | Why |
| --------------------------------------------------------------------------------------- | -------------------------------- | -------------------------------- | --- |
| `boot.s:132` `jsr main_68k`                                                              | `main_68k` (deleted)             | `jsr _bootstrap`                 | `main_68k` is deleted; `_bootstrap` is the cold-boot helper. |
| `boot.s:67` vector 29 `_VINT_handler`                                                    | `_VINT_handler` (deleted identity) | `_vblank_service`              | `_VINT_handler` as a top-level identity is removed. |
| `main_68k.s:75-92` `main_68k` loop body                                                  | loop body                        | DELETED (no replacement)         | RULES §1 violation; no substitute. |
| `main_68k.s:94-122` `_VINT_handler` body                                                 | top-level IRQ handler            | body moved to `_vblank_service`; `rte` → `jmp (0x00003A208).l` | Hook becomes a chained service routine. |
| `main_68k.s:282` `bsr load_scene_tiles` (BG hook scene-transition preamble)              | unchanged                        | unchanged (now cross-module: scene_load.s) | Scene transitions legitimately load tiles; no rule violated. |
| `main_68k.s:454` `bsr load_scene_tiles` (FG hook scene-transition preamble)              | unchanged                        | unchanged (now cross-module)     | Same. |
| Arcade warm-restart at arcade_pc `0x00039F9E` (`MOVEA.L (0x0004).W, A0; JMP (A0)`)       | `ROM[0x0004]` = `_start`         | `JMP arcade_pc 0x0003A000` (hard-coded; opcode_replace in remap.json) | RULES §6 — no re-entry into boot/init during gameplay. |
| `crash_handler.s:209-210` `move.w frame_counter, %d6; move.w %d6, CRASH_FRAME_COUNTER`   | reads `frame_counter`            | `clr.w CRASH_FRAME_COUNTER`      | `frame_counter` BSS deleted. |

---

## STOP conditions — not triggered

- All architectural violations identified.
- All routines classified from existing source evidence.
- Every proposed module split preserves arcade-owned control flow.
- No proposed design violates RULES.md or ARCHITECTURE.md.
- The three open items (P1, P2, P3) are **prerequisite verifications**
  for the implementation phase, not design uncertainties. The design
  is self-consistent; prerequisite work is bounded and specified.

---

## Ready-for-Cody checklist

- Architectural violations identified: 6 (see Phase 1)
- Routines classified: 39 (see Phase 2)
- New modules defined: 3 new (`vdp_comm.s`, `tilemap_hooks.s`, `scene_load.s`) + 2 modified (`boot.s`, `crash_handler.s`)
- Genesis-owned loop preserved: NO
- Genesis-owned VBlank preserved: NO (top-level identity removed; servicing stub chains to arcade L5)
- Cold-boot handoff target resolved: YES (arcade_pc `0x0003A000`, Genesis ROM `0x00003A200`)
- Runtime owner resolved: YES (arcade code post-cold-boot)
- VBlank helper graph resolved: YES (`_vblank_service` → VDP commits → JMP arcade_pc `0x0003A008`)
- Prerequisites called out for Cody: P1, P2, P3
- Ready for Cody implementation: YES, **conditional** on prerequisite resolution (P1 and P2 before implementation; P3 acceptable to defer with fallback in place)
