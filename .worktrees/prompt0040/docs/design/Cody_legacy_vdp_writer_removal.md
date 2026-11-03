# Cody — Legacy VDP Writer Identification and Removal (Build 0044)

## Scope
Identify the legacy pre-pipeline VDP writer producing low-VRAM stripe/checkerboard content and remove only that path, while preserving translation pipeline and crash handler behavior.

## Required Reading Status
- `AGENTS_LOG.md`: read (latest entries including Build 0044 + Andy D-register trace)
- `apps/rastan-direct/src/main_68k.s`: read (full file; target functions audited)
- `apps/rastan-direct/src/boot/boot.s`: read
- `apps/rastan-direct/src/crash_handler.s`: read
- `docs/design/Andy_d_register_base_pointer_trace.md`: read
- `docs/design/Cody_startup_test_pattern_removal.md`: read

## Phase 1 — VDP Writes Before Frame 386

Direct VDP writes and early commit paths in `main_68k.s`:

1. Function: `vdp_set_reg`
- File/line: `apps/rastan-direct/src/main_68k.s:185-191`
- Instruction: `move.w %d2, VDP_CTRL`
- Target: `VDP_CTRL`
- Purpose: VDP register programming helper
- Still needed: YES (core VDP init/runtime control)

2. Function: `vdp_set_vram_write_addr`
- File/line: `apps/rastan-direct/src/main_68k.s:193-207`
- Instruction: `move.l %d1, VDP_CTRL`
- Target: `VDP_CTRL`
- Purpose: set VRAM write command
- Still needed: YES (all VRAM writes)

3. Function: `load_scene_tiles` (direct tile upload path)
- File/line: `apps/rastan-direct/src/main_68k.s:1971-2017`
- Instructions: `move.w (%a2)+, VDP_DATA` in `.Lload_scene_tile_words`
- Target: `VDP_DATA` (VRAM tile region)
- Purpose: preload scene tiles directly into VRAM
- Still needed: YES for runtime scene transitions; NO for unconditional pre-pipeline startup call

4. Function: `init_staging_state`
- File/line: `apps/rastan-direct/src/main_68k.s:2081-2085`
- Instruction: `move.w #0x0000, VDP_DATA` in `.Lplane_a_clear`
- Target: `VDP_DATA`
- Purpose: clear Plane A nametable
- Still needed: YES (startup deterministic nametable clear)

5. Function: `_VINT_handler` + commit calls
- File/line: `apps/rastan-direct/src/main_68k.s:95-115`
- Targets: `vdp_commit_tiles_if_dirty`, `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty`, optional `vdp_commit_palette`, `vdp_commit_scroll`
- Purpose: staging-buffer to VDP commit pipeline
- Still needed: YES (translation architecture)

6. Function: `vdp_commit_tiles_if_dirty`
- File/line: `apps/rastan-direct/src/main_68k.s:1770-1783`
- Instruction: `move.w (%a0)+, VDP_DATA`
- Target: `VDP_DATA`
- Purpose: commit staged tile words
- Still needed: YES (pipeline mechanism), but currently inactive in boot path because `tiles_dirty` is never set in normal startup.

7. Function: `vdp_commit_bg_strips_if_dirty`
- File/line: `apps/rastan-direct/src/main_68k.s:1787-1810`
- Instruction: `move.w (%a0)+, VDP_DATA`
- Target: `VDP_DATA`
- Purpose: commit staged BG rows
- Still needed: YES

8. Function: `vdp_commit_fg_strips_if_dirty`
- File/line: `apps/rastan-direct/src/main_68k.s:1824-1847`
- Instruction: `move.w (%a0)+, VDP_DATA`
- Target: `VDP_DATA`
- Purpose: commit staged FG rows
- Still needed: YES

9. Function: `vdp_commit_palette`
- File/line: `apps/rastan-direct/src/main_68k.s:1861-1869`
- Instructions: `move.l #0xC0000000, VDP_CTRL`, `move.w (%a0)+, VDP_DATA`
- Target: `VDP_CTRL` + `VDP_DATA`
- Purpose: commit staged CRAM palette
- Still needed: YES

10. Function: `vdp_commit_scroll`
- File/line: `apps/rastan-direct/src/main_68k.s:1871-1880`
- Instructions: `move.w staged_scroll_*, VDP_DATA` and `move.l #0x40000010, VDP_CTRL`
- Target: `VDP_CTRL` + `VDP_DATA`
- Purpose: scroll table updates
- Still needed: YES

Indirect staging-buffer writes audited:
- `init_staging_state` currently clears (`clr.w`) `staged_bg_buffer`, `staged_fg_buffer`, `staged_tile_words`, `staged_palette_words` only (`apps/rastan-direct/src/main_68k.s:2057-2078`) — no non-zero synthetic fill.
- `tiles_dirty` writes in file are only clear paths (`apps/rastan-direct/src/main_68k.s:2051`, `1783`), no boot-time set path remains.

## Phase 2 — Stripe Source Confirmed

Confirmed stripe source:
- function: `main_68k` unconditional startup call into `load_scene_tiles`
- line(s): pre-fix `apps/rastan-direct/src/main_68k.s` around old line 79-80 (`moveq #0,%d0; bsr load_scene_tiles`) + loader body at `1971-2017`
- VRAM destination: tile slot destinations from scene manifest (minimum destination slot `0x0014`)
  - VRAM byte destination start = `0x0014 * 32 = 0x000280`
  - Title manifest range: `dst 0x0014..0x035C` (841 pairs)
  - Gameplay manifest range: `dst 0x0014..0x0350` (829 pairs)
  - Endround manifest range: `dst 0x0014..0x053E` (1067 pairs)
- data written:
  - Title preload includes sources such as `0x0023`, `0x0024`, `0x0025`, `0x0026` whose tile words contain repeated nibble patterns (`2222`, `0222`, etc.), producing striped/checkerboard structure.
  - Gameplay/endround preload includes early entries like `src 0x0001..0x0011` -> `dst 0x0052..0x005B`; sampled source tiles are all `0xFFFF` words (solid fill tiles).
- write type: direct VDP writes (`VDP_DATA`) from `load_scene_tiles`, not staging commit
- always executes: YES (before fix), because `main_68k` called `load_scene_tiles` unconditionally before entering main loop
- was it supposed to be removed: NO
  - `docs/design/Cody_startup_test_pattern_removal.md` explicitly preserved `load_scene_tiles` as required startup logic in Build 0038.

## Phase 3 — Removal Plan

Removal plan:
- target: unconditional startup preload call in `main_68k`
- action: remove pre-loop startup call to `load_scene_tiles` (`moveq #0,%d0` + `bsr load_scene_tiles`)
- preserved:
  - `load_scene_tiles` function itself preserved (runtime scene transition path)
  - VDP boot setup (`vdp_boot_setup`) preserved
  - init and VBlank translation commit pipeline preserved
  - crash handler unchanged
- post-removal VRAM state (low tile addresses): no unconditional boot-time direct writer populates low tile slots; low tile region remains untouched by this legacy startup path until legitimate runtime-triggered scene load or staging-commit writes occur
- risk: first visible content may appear later (no eager preload)
- mitigation: keep runtime `load_scene_tiles` entry points in hook scene preambles unchanged

Stop-condition check:
- "source was supposed to be removed previously": NO (not triggered)

## Phase 4 — Implementation

Changes made:
- `apps/rastan-direct/src/main_68k.s`
  - removed unconditional startup preload call in `main_68k`:
    - removed `moveq #0, %d0`
    - removed `bsr load_scene_tiles`
- `tools/translation/postpatch_startup_rom.py`
  - updated invariant expected total covered bytes to match resulting wrapper size change:
    - `0xFC1C4` -> `0xFC1BC` at Build 0029 invariant check and message text.

No changes made to:
- translation hook logic
- crash handler
- boot vector table behavior

## Phase 5 — Build and Verification

Build command:
```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Build result: PASS
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0045.bin`

Verification notes:
- Startup `main_68k` no longer directly calls `load_scene_tiles` before main loop.
- `load_scene_tiles` remains reachable only through runtime hook scene-transition preambles.
- Expected low-VRAM state after fix: no unconditional boot preload stripes/checkerboard from this path.

## Phase 6 — User Verification Targets

1. Low VRAM (tile indices `0x0000..~0x0020`) no longer receives immediate startup preload stripe/checkerboard content from the removed unconditional path.
2. Early frames are black/blank or real runtime-driven output only (not synthetic eager preload output).
3. Crash handler still triggers and renders on fault.
4. No boot regression (main loop progression remains intact).
