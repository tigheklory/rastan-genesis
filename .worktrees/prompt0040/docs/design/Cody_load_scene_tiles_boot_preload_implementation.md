# Cody — load_scene_tiles and Boot-Time Title Preload Implementation

## Executive Summary
Implemented Step 1 foundation in `apps/rastan-direct/src/main_68k.s` only: embedded PC080SN tile ROM and scene manifests in `.rodata`, added ROM scene A0 range table, added WRAM scene state variables in `.bss`, added `load_scene_tiles`, and added boot-time `load_scene_tiles(0)` call in `main_68k` before `init_staging_state`.

## Preconditions Verified
Verified before edit:
- `main_68k`, `vdp_boot_setup`, and `init_staging_state` existed.
- `load_scene_tiles` did not exist.
- `genesistan_pc080sn_tile_rom` and all three `genesistan_scene_preload_*` blocks did not exist.
- `genesistan_current_scene_id`, `genesistan_scene_a0_lo`, and `genesistan_scene_a0_hi` did not exist.

## ROM Tile and Manifest Embedding
Added `.rodata` blocks in required order:
1. `genesistan_pc080sn_tile_rom` -> `.incbin "../../build/regions/pc080sn.bin"`
2. `genesistan_scene_preload_title` / `genesistan_scene_preload_title_end`
3. `genesistan_scene_preload_gameplay` / `genesistan_scene_preload_gameplay_end`
4. `genesistan_scene_preload_endround` / `genesistan_scene_preload_endround_end`

All are ROM-resident and placed in `.rodata`.

## ROM Scene Range Table Added
Added canonical ROM-resident range table:
- `genesistan_scene_a0_ranges`
- six `.long` values in required scene order:
  - scene 0: `0x0005A7DA`, `0x0005B0B2`
  - scene 1: `0x00056A22`, `0x000570C2`
  - scene 2: `0x0005822A`, `0x00059614`

## WRAM Scene-State Variables Added
Added to `.bss`:
- `genesistan_current_scene_id: .byte 0`
- `genesistan_scene_a0_lo: .long 0`
- `genesistan_scene_a0_hi: .long 0`

No extra scene-state variables were added.

## load_scene_tiles Implementation
Implemented `load_scene_tiles` in `.text` between `arcade_tick_logic` and `init_staging_state`.

Behavior implemented:
- input `scene_id` in `%d0` (0/1/2; defaults to title if out of range)
- selects matching manifest symbol
- masks interrupts (`move.w #0x2700, %sr`)
- disables display (`VDP_REG_MODE2`, `VDP_MODE2_DISPLAY_OFF`)
- iterates `(u16 arcade_tile, u16 vram_slot)` pairs
- sentinel stop on `arcade_tile == 0xFFFF`
- per pair:
  - VRAM address = `vram_slot << 5`
  - source = `genesistan_pc080sn_tile_rom + (arcade_tile << 5)`
  - writes exactly 16 words to `VDP_DATA`
- updates scene state after upload:
  - stores `genesistan_current_scene_id`
  - stores `genesistan_scene_a0_lo/hi` from `genesistan_scene_a0_ranges`
- re-enables display (`VDP_MODE2_DISPLAY_ON`)
- restores runtime interrupt state (`move.w #0x2000, %sr`)
- restores registers and returns with `rts`

No DMA and no trigger wiring were added.

## Boot-Time Title Preload Call
Updated `main_68k` boot sequence to:
- `bsr vdp_boot_setup`
- `moveq #0, %d0`
- `bsr load_scene_tiles`
- `bsr init_staging_state`

This preloads scene 0 (Title) at boot as required.

## Hook Left Unchanged in This Step
`genesistan_hook_tilemap_plane_a` logic was not modified for scene-trigger behavior in this step.

## Build Verification
Executed:
- `make -C apps/rastan-direct`

Results:
- assembler/linker succeeded
- no unresolved symbols
- no duplicate labels
- ROM produced at `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0015.bin`

## Runtime Expectations
Expected behavior change from this step:
- title-scene PC080SN tiles are loaded at boot by `load_scene_tiles(0)`.

Not included in this step:
- no hook scene-change trigger wiring
- no sprite changes
- no VBlank redesign

## Final Result
Step 1 foundation implemented exactly in `main_68k.s`, built successfully, and scoped to boot-time title preload plus loader/state/ROM asset embedding only.
