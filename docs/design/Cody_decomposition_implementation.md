# Cody — Runtime Decomposition Implementation (Phase B)

Agent: Cody
Type: Implementation
Build Context: current `rastan-direct`

## Scope executed

Implemented the Phase B decomposition split from `main_68k.s` into:

- `src/vdp_comm.s` (new)
- `src/tilemap_hooks.s` (new)
- `src/scene_load.s` (new)

and updated:

- `src/boot/boot.s`
- `src/crash_handler.s`
- `Makefile`

Then deleted:

- `src/main_68k.s`

No warm-restart opcode_replace was added in this pass.
No changes were made to `specs/rastan_direct_remap.json` in this phase.

## Implemented changes

### boot.s

- Replaced startup call:
  - `jsr main_68k` -> `jsr _bootstrap`
- Rewired vector entry from `_VINT_handler` to `_vblank_service` at the existing VINT slot in the table.
- Added `_bootstrap`:
  - `jsr vdp_boot_setup`
  - `bsr _bootstrap_clear_staging`
  - `moveq #0, %d0`
  - `jsr load_scene_tiles`
  - `move.w #0x2000, %sr`
  - `jmp (0x00003A200).l`
- Added local `_bootstrap_clear_staging` with one-time boot staging clears:
  - clears `staged_bg_buffer`, `staged_fg_buffer`, `staged_palette_words`, `staged_tile_words`
  - clears dirty flags
  - initializes staged/arcade dest pointers
  - clears plane A VRAM
  - zeros staged scroll words

### vdp_comm.s (new)

Contains moved VDP service/commit logic:

- `vdp_boot_setup`
- `vdp_set_reg`
- `vdp_set_vram_write_addr`
- `sprite_dma_addr_high_bits_fix`
- `vdp_commit_tiles_if_dirty`
- `vdp_commit_bg_strips_if_dirty`
- `vdp_commit_fg_strips_if_dirty`
- `vdp_commit_palette`
- `vdp_commit_scroll`

Added new vector target:

- `_vblank_service`
  - saves registers
  - display off
  - commits tiles/bg/fg
  - conditional palette commit
  - scroll commit
  - display on
  - restores registers
  - `jmp (0x00003A208).l`

No `rte` in `_vblank_service`.

BSS moved here:

- `palette_dirty`, `tiles_dirty`
- `bg_row_dirty`, `fg_row_dirty`
- `staged_dest_ptr_bg`, `staged_dest_ptr_fg`
- `staged_scroll_x_bg`, `staged_scroll_x_fg`, `staged_scroll_y_bg`, `staged_scroll_y_fg`
- `staged_bg_buffer`, `staged_fg_buffer`, `staged_palette_words`, `staged_tile_words`

`src/crash_handler.s` is included from this module (same include pattern previously used via `main_68k.s`).

### tilemap_hooks.s (new)

Contains moved hook + input helper bodies:

- all `genesistan_hook_tilemap_*`
- all `genesistan_hook_text_writer_*`
- `genesistan_hook_number_renderer_3c2e2`
- `genesistan_hook_cwindow_clear`
- `rastan_direct_update_inputs`

BSS moved here:

- `genesistan_shadow_input_390001`
- `genesistan_shadow_input_390003`
- `genesistan_shadow_input_390005`
- `genesistan_shadow_input_390007`
- `genesistan_shadow_dip1`
- `genesistan_shadow_dip2`
- `prev_coin_p1_a_pressed`

### scene_load.s (new)

Contains moved scene/tile load logic + tables:

- `load_scene_tiles`
- `genesistan_pc080sn_tile_vram_lut`
- `genesistan_pc080sn_attr_lut`
- `genesistan_pc080sn_tile_rom`
- `genesistan_scene_preload_title` and `_end`
- `genesistan_scene_preload_gameplay` and `_end`
- `genesistan_scene_preload_endround` and `_end`
- `genesistan_scene_a0_ranges`

BSS moved here:

- `genesistan_current_scene_id`
- `genesistan_scene_a0_lo`
- `genesistan_scene_a0_hi`

### crash_handler.s

Adjusted frame-counter capture per Phase B.6:

- removed `frame_counter` reads
- now uses:
  - `clr.w CRASH_FRAME_COUNTER`

### Makefile

- removed `main_68k.o`
- added objects/rules:
  - `vdp_comm.o`
  - `tilemap_hooks.o`
  - `scene_load.o`

### main_68k.s

- deleted

## Build result

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: **FAIL (STOP)**

Failure:

- `postpatch_startup_rom.py` failed symbol table check:
  - `RuntimeError: Required symbol not found in out/symbol.txt: rastan_direct_arcade_tick_entry`

Context:

- assembly + link succeeded
- failure occurs during postpatch symbol validation stage

## Verification snapshot before STOP

- `_bootstrap` exists and ends with `jmp (0x00003A200).l`: YES
- `_vblank_service` exists and ends with `jmp (0x00003A208).l`: YES
- `_vblank_service` contains `rte`: NO
- `main_68k.s` deleted: YES
- `main_68k` symbol present in `out/symbol.txt`: NO
- `_VINT_handler` symbol present in `out/symbol.txt`: NO
- `crash_handler.s` `frame_counter` reference removed: YES
- Phase A 17 entries present in remap spec: YES

## STOP condition triggered

YES

Reason:

- undefined required symbol in postpatch validation after decomposition deletion:
  - `rastan_direct_arcade_tick_entry`

Per prompt stop rules, execution stopped at first build-blocking symbol failure.
