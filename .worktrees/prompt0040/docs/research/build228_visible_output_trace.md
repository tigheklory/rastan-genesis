1) Purpose
- Trace the exact started-path visible-output pipeline in Build 228 and determine why frontend/title output is mostly black with sparse dots.

2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest Build 228 started-path and direct-title-prep sections)
- `README.md`
- `docs/research/build228_direct_title_prep_replacement_no_shims.md`
- `docs/research/build228_started_path_visible_trace.md`
- `apps/rastan/src/main.c`
- `apps/rastan/out/symbol.txt`
- `apps/rastan/out/rom.out` disassembly (`m68k-elf-objdump`)
- Runtime probes (started-path with injected START):
  - `/tmp/build228_vdp_write_probe.txt`
  - `/tmp/build228_vdp_write_probe_pcs.txt`
  - `/tmp/build228_vdp_value_hist.txt`
  - `/tmp/build228_hook_exec_probe.txt`
  - `/tmp/build228_buffer_probe.txt`
  - `/tmp/build228_buffer_dump.txt`

3) Active Frontend Execution Path
- Started-path validity is proven (`current_screen` transitions to `0x00000004`, `SCREEN_FRONTEND_LIVE`).
- Per-frame live branch in `main.c` (`current_screen == SCREEN_FRONTEND_LIVE`) executes:
  - `genesistan_refresh_arcade_inputs()`
  - hook cursor reset (`genesistan_hook_col_a/row_a`, `genesistan_hook_col_b/row_b`)
  - `genesistan_run_original_frontend_tick()`
  - `sanitize_arcade_workram()`
  - `load_arcade_palette()`
  - `sync_arcade_scroll_to_vdp()`
  - `render_frontend_sprite_layer()` -> `genesistan_render_sprites_vdp()`
- Runtime state fields during this started run:
  - `A5+0x0000 = 0x0002`
  - `A5+0x0002 = 0x0000`
  - `A5+0x0004 = 0x0000`
  - `A5+0x002C` decrements over frames (`0x0097 -> 0x0010` in sampled window)

4) Final VDP Write Owners
A) Tilemap / Name Table
- Expected writers:
  - `genesistan_hook_tilemap_plane_a` (`0x200000`)
  - `genesistan_hook_tilemap_plane_b` (`0x2001A6`)
  - `genesistan_hook_text_writer_3bb48_impl` (`0x20034C`)
  - `genesistan_hook_text_writer_3c3fe` (`0x200DE2`)
- Runtime execution probe (`/tmp/build228_hook_exec_probe.txt`): all four = `count=0` in started run.
- VDP write classification for tilemap/text ownership: `NO_VDP_WRITES` (from these producers).
- Confidence: High.

B) Sprite / SAT
- Active writer:
  - `genesistan_render_sprites_vdp` (`0x20060C`, execution count `143`, started frames 28..596).
- Downstream VDP port writers observed from this path:
  - `0x200B92/0x200B98` and `0x200AAE/0x200AB4` (`movew ... , 0xC00004/0xC00000`)
  - `0x202D58/0x202E66` + `0x202D80..0x202DDE` (`DMA_doCPUCopyDirect` control/data writes)
- Source data (runtime sampled):
  - sprite descriptor block A (`0xFF11B2`, 18*8 bytes): nonzero count `0`
  - sprite descriptor block B (`0xFF0170`, 4*8 bytes): mostly zero, only a few nonzero bytes
  - VDP data stream at `0x202D80..0x202DDE`: overwhelmingly `0x0000`
- Classification: `ZERO_DATA` (active write path, mostly empty payload).
- Confidence: High.

C) Palette / CRAM
- Active writers:
  - `load_arcade_palette()` path (`PAL_setColors`, `DMA_doDmaFast` PCs `0x202C74..0x202D08`)
  - sprite-palette refresh in `genesistan_render_sprites_vdp` (PCs `0x200AAE/0x200AB4`, `0x200B92/0x200B98`)
- Proven VDP writes:
  - control port `0xC00004`: nonzero command words (`C000..C07E`, `8F02`, `9340`, ...)
  - data port `0xC00000`: nonzero color words (`0222`, `0444`, `0666`, `0888`, `0AAA`, `0CCC`, `0EEE`)
- Classification: `VALID`.
- Confidence: High.

2B) Mandatory VDP Port Proof (`0xC00000` / `0xC00004`)
- Started run (600 frames) totals:
  - `0xC00000` writes: `14872`
  - `0xC00004` writes: `11583`
- Exact instruction examples:
  - `0x200AAE: movew %a3@(0,%d1:l),0xC00000`
  - `0x200AB4: addal #0x00020000,%a0` (in same CRAM write loop)
  - `0x200B92: movew %a2@(0,%d1:l),0xC00000`
  - `0x200B8C: movel %d3,0xC00004`
  - `0x202D52: movel %sp@(12),0xC00004`
  - `0x202D7C..0x202DA0: movel ... ,0xC00000`
  - `0x2159AA/0x2159B8/0x2159E0/0x2159E8: movel ... ,0xC00004`
  - `0x2159B2/0x2159BA/0x2159E2/0x2159EA: movew ... ,0xC00000`
- Frequency:
  - per-frame (started run): persistent writes across frames 28..596.

5) Actual Data Being Written
Tilemap / Name Table
- No execution of tilemap/text writer hook entries (`0x200000`, `0x2001A6`, `0x20034C`, `0x200DE2`) in this started run.
- Therefore no proven tilemap/text producer writes from intended title/frontend hooks.
- Classification: `NO_VDP_WRITES` for intended tile/text producer set.

Sprites / SAT
- Sprite path executes, but source descriptor data is mostly empty:
  - block A fully zero
  - block B nearly all zero
- DMA data stream tied to active copy path (`0x202D80..0x202DDE`) is entirely zero-valued in sampled histogram.
- Classification: `ZERO_DATA`.

Palette / CRAM
- CRAM writes are frequent and nonzero with stable color values.
- Classification: `VALID`.

6) Sparse Dot Root Cause
- The display is mostly black with sparse dots because:
  - title/text/tilemap producers are not executing in this started run (zero hits at tilemap/text hook entries), and
  - the active sprite/SAT path writes mostly zero payload (empty descriptor/tile data), while
  - palette writes are valid.
- Net effect: colors update, but geometry/text backing data is largely absent/zero, yielding sparse visible specks instead of full title composition.

7) Data Flow Breakpoint
- Expected producer chain:
  - frontend tick -> tilemap/text hook producers (`0x200000`, `0x2001A6`, `0x20034C`, `0x200DE2`) + sprite descriptor population.
- Actual producer chain in this run:
  - frontend tick -> sprite renderer (`0x20060C`) + palette/scroll writes.
- Exact breakpoint (proven by execution/write evidence):
  - tilemap/text producer entry points are not reached (`count=0`), and active sprite-source buffers are near-empty.
- Failure type:
  - `missing producer execution` (tile/text) + `zeroed payload` (sprite path).

8) Minimal Fix Target
=== BUILD228_VISIBLE_OUTPUT_MINIMAL_FIX_TARGET ===
- fix_area: started frontend state output-producer activation and payload production (tile/text + sprite descriptors)
- exact_output_path: `genesistan_run_original_frontend_tick()` downstream paths that should reach `0x200000/0x2001A6/0x20034C/0x200DE2` and populate sprite descriptor blocks before `genesistan_render_sprites_vdp`
- current_wrong_data: tile/text producers are not executing; active sprite copy stream is mostly `0x0000`; descriptor block A is fully zero
- correct_data_needed: nonzero tile attribute/text cell writes for plane A/B plus valid (non-hidden) sprite descriptor payload for title/logo elements
- why_this_is_the_next_step: VDP hardware writes are already live and palette is valid; missing/empty content producers are the direct blocker to visible title composition
- what_must_NOT_be_done: no shims/bridges/trampolines, no fake injected tile/sprite data, no forced state changes, no launcher-path reanalysis

9) Uncertainties
- This pass proves missing/empty producer outputs in the started path but does not yet isolate the single earliest branch condition inside `genesistan_run_original_frontend_tick()` that suppresses tile/text producer execution.
- Visual capture was not produced inside this pass; classification is based on direct VDP port/data evidence plus started-path state and producer execution evidence.

10) Conclusion
- Build 228 started-path rendering is not blocked by lack of VDP activity; it is blocked by missing tile/text producer execution and near-empty sprite payload, while palette/scroll writes remain active and valid.
