# Cody — Startup Test Pattern Removal (Build 0038)

## Scope
Remove synthetic startup pattern sources from normal runtime while preserving required startup/boot logic for `apps/rastan-direct`.

## Required Reading Status
- `AGENTS_LOG.md`: read (latest sections, including Build 0036 and early-phase analysis)
- `docs/design/Andy_test_pattern_execution_verification.md`: read
- `apps/rastan-direct/src/main_68k.s`: read
- `apps/rastan-direct/src/boot.s`: **missing at this path**
- `apps/rastan-direct/src/boot/boot.s`: read (actual boot source)
- `specs/rastan_direct_remap.json`: read (exists)
- `tools/translation/postpatch_startup_rom.py`: read

## Phase 1 — Synthetic Startup Element Isolation and Classification

Startup element:
  name: checkerboard fill of `staged_bg_buffer`
  file: `apps/rastan-direct/src/main_68k.s`
  line(s): prior loop at `init_staging_state` block around old `.Lbg_row/.Lbg_col` (replaced at current lines 2066-2070)
  classification: Synthetic scaffolding — safe to remove
  reason: generated non-runtime checkerboard indices (`0x0001`/`0x0002`) for startup visualization only.

Startup element:
  name: synthetic tile seed path (`tile_init_words` -> `staged_tile_words`)
  file: `apps/rastan-direct/src/main_68k.s`
  line(s): old copy path in `init_staging_state`; data label remains at lines 2180-2190
  classification: Synthetic scaffolding — safe to remove from normal boot path
  reason: seeds synthetic tile patterns (`0x1111`, `0x2222`, `0x3030/0x0303`) not required by runtime intent translation.

Startup element:
  name: synthetic palette seed path (`palette_init_words` -> `staged_palette_words`)
  file: `apps/rastan-direct/src/main_68k.s`
  line(s): old copy path in `init_staging_state`; data label remains at lines 2170-2178
  classification: Synthetic scaffolding — safe to remove from normal boot path
  reason: seeds diagnostic CRAM values for synthetic bring-up visibility.

Startup element:
  name: dirty-flag activation for synthetic startup commits (`palette_dirty=1`, `tiles_dirty=1`)
  file: `apps/rastan-direct/src/main_68k.s`
  line(s): `init_staging_state` lines 2049-2050
  classification: Mixed / needs care
  reason: these flags drive real VBlank commit machinery; must be set to safe values that prevent synthetic commit while preserving later runtime updates.

Startup element:
  name: VDP boot/setup (`vdp_boot_setup`) and scene preload (`load_scene_tiles`)
  file: `apps/rastan-direct/src/main_68k.s`
  line(s): `main_68k` lines 75-78; setup body starts line 121
  classification: Required startup — must be preserved
  reason: required VDP register initialization and preload pipeline for runtime tile availability.

Startup element:
  name: direct Plane A clear in init (`VRAM_PLANE_A_BASE` write)
  file: `apps/rastan-direct/src/main_68k.s`
  line(s): 2078-2083
  classification: Required startup — preserved
  reason: valid startup clear state; not synthetic pattern generation.

Startup element:
  name: RAM/workram init + DIP/input defaults
  file: `apps/rastan-direct/src/main_68k.s`
  line(s): 2090-2165
  classification: Required startup — must be preserved
  reason: required state causality for boot progression and runtime logic.

## Phase 2 — Safe Removal Plan

Removal target:
  action: Replace checkerboard fill with zero-clear of full `staged_bg_buffer`.
  preserved dependencies: `staged_bg_buffer` still initialized deterministically; VBlank strip logic unchanged.
  risk: accidental non-zero garbage if init skipped.
  mitigation: explicit full 2048-word clear loop.

Removal target:
  action: Remove synthetic tile seed copy path and clear `staged_tile_words` instead.
  preserved dependencies: tile staging buffer still valid memory; later runtime tile updates still use existing dirty/commit path.
  risk: stale data committed if `tiles_dirty` remains set.
  mitigation: clear `tiles_dirty` during init.

Removal target:
  action: Remove synthetic palette seed copy path and clear `staged_palette_words` instead.
  preserved dependencies: palette staging buffer remains valid; runtime palette writes can still mark dirty and commit.
  risk: synthetic palette upload at first VBlank if `palette_dirty` set.
  mitigation: clear `palette_dirty` during init.

Removal target:
  action: dirty flag post-init state
  preserved dependencies: all VBlank commit functions remain unchanged and runtime-usable.
  risk: breaking later real commits.
  mitigation: initialize to idle-safe values only in init:
    - `tiles_dirty = 0`
    - `palette_dirty = 0`
    - `bg_row_dirty = 0`
    - `fg_row_dirty = 0`
    Runtime hooks continue to set these when real content arrives.

## Phase 3 — Implementation Applied

Files edited:
- `apps/rastan-direct/src/main_68k.s`
- `tools/translation/postpatch_startup_rom.py`

Code changes in `init_staging_state`:
- `palette_dirty` initialization: `#1` -> `clr.b`
- `tiles_dirty` initialization: `#1` -> `clr.b`
- Replaced `palette_init_words` copy loop with full clear of `staged_palette_words` (64 words).
- Replaced `tile_init_words` copy loop with full clear of `staged_tile_words` (48 words).
- Replaced checkerboard loop with full clear of `staged_bg_buffer` (2048 words).

No changes made to:
- `vdp_boot_setup`
- `load_scene_tiles`
- `_VINT_handler` commit sequencing
- workram factory defaults / DIP / input initialization
- boot vector/startup code in `boot/boot.s`

Invariant update in patcher:
- `tools/translation/postpatch_startup_rom.py`
- Updated expected `total_genesis_bytes_covered` from `0xFC1E8` to `0xFC1C4` to match the reduced wrapper footprint.
- `opcode_replace` patched site count expectation remains `56`.

## Phase 4 — Build and Verification

Build command:
```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Build result:
- PASS
- Numbered ROM artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0038.bin`
- Automatic 30s trace produced by build target.

Verification:
- Exact intentional source changes:
  - `apps/rastan-direct/src/main_68k.s`
  - `tools/translation/postpatch_startup_rom.py`
- `tile_init_words` still exists in binary symbols: YES (data label retained)
- `tile_init_words` reachable in normal boot path: NO (no remaining reference in `init_staging_state`; symbol only definition)
- `palette_init_words` still exists in binary symbols: YES (data label retained)
- `palette_init_words` reachable in normal boot path: NO (no remaining reference in `init_staging_state`; symbol only definition)
- Checkerboard BG fill reachable in normal boot path: NO (loop removed; replaced with buffer clear)

Unrelated change handling:
- Build-generated tracked artifacts were reverted after verification so only intentional task edits remain.

## Phase 5 — User Verification Target

User must verify after running Build 0038:
1. IMG_02 no longer shows startup synthetic pattern.
2. Early output is blank/cleared or real runtime-driven content only.
3. Boot still proceeds (no obvious hang/regression; input/DIP startup behavior still intact if observable).

## STOP Conditions
- No STOP condition triggered.
