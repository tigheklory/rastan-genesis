# Cody — Scene Preload Restore (Build 0045)

## Scope
Restore the boot-time scene preload call removed in Build 0045, while keeping all synthetic startup test-pattern paths removed.

## Required Reading Status
- `AGENTS_LOG.md`: read (latest entries)
- `docs/design/Cody_legacy_vdp_writer_removal.md`: read
- `docs/design/Cody_startup_test_pattern_removal.md`: read
- `apps/rastan-direct/src/main_68k.s`: read

## Phase 1 — Restore

Restored exactly two lines in `main_68k` at the Build 0044 slot:

```asm
moveq   #0, %d0
bsr     load_scene_tiles
```

Location in source:
- `apps/rastan-direct/src/main_68k.s:79-80`
- Positioned between:
  - `bsr vdp_boot_setup`
  - `bsr init_staging_state`

This matches the previous Build 0044 ordering and remains pre-loop initialization.

## Phase 2 — Synthetic Startup Content Check

Checked `init_staging_state` and boot path for synthetic startup content:

- `tile_init_words` startup commit: **ABSENT**
  - Label exists in rodata only; no startup copy/commit path from it.
- `palette_init_words` startup commit: **ABSENT**
  - Label exists in rodata only; no startup copy/commit path from it.
- checkerboard staging fill: **ABSENT**
  - `staged_bg_buffer`/`staged_fg_buffer` are cleared with `clr.w` loops.
- synthetic dirty flags at boot: **ABSENT**
  - `palette_dirty` and `tiles_dirty` are `clr.b` at init.
- indirect synthetic init via helper calls: **ABSENT**
  - Boot calls are `vdp_boot_setup`, restored `load_scene_tiles`, `init_staging_state`.
  - No helper in this boot chain reintroduces synthetic tile/palette seed commits.

## Phase 3 — Build and Verification

Build command:
```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: **PASS**
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0046.bin`

Required postpatch adjustment:
- `tools/translation/postpatch_startup_rom.py`
- Build 0029 invariant expected total covered bytes restored to `0xFC1C4` (from temporary `0xFC1BC`) to match restored startup call size.

Crash handler status:
- crash handler source unchanged in this task.

## Phase 4 — User Verification Targets

1. Real title-scene tile assets visible in VRAM after boot.
2. Stripe/checkerboard behavior unchanged from Build 0045 (restore is not a stripe fix).
3. Crash screen still appears on fault.
4. No boot regression.
