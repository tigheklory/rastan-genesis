1. Executive Summary
Implemented the Genesis WRAM structural split by relocating Genesis `.bss` to `0xFF4000`, preserving arcade workram ownership at `0xFF0000`, restoring arcade factory defaults during `init_staging_state`, and keeping existing hook logic unchanged. This removes direct BSS/workram overlap and re-establishes deterministic arcade-state initialization on warm restarts.

2. Root Cause
Before this change, both arcade workram (A5-relative, base `0xFF0000`) and Genesis `.bss` were mapped at `0xFF0000`. That caused hard collisions:
- `frame_counter` at `0xFF0000` collided with arcade state `A5@(0)`.
- `staged_bg_buffer` starting at `0xFF002C` collided with arcade countdown/state fields (for example `A5@(44)`).
Any Genesis-side writes to BSS could corrupt arcade state, and vice versa.

3. Memory Model Before / After
Before:
- Arcade workram: `0xFF0000-0xFF3FFF` (effective expectation)
- Genesis BSS: `.bss 0xFF0000 (NOLOAD)`
- Result: overlapping ownership

After:
- Arcade workram: `0xFF0000-0xFF3FFF` (A5 base unchanged)
- Genesis BSS: `.bss 0xFF4000 (NOLOAD)`
- Result: no overlap between arcade state and Genesis wrapper buffers

4. Implementation Details
Applied changes:
- `apps/rastan-direct/link.ld`
  - `.bss 0xFF0000 (NOLOAD)` -> `.bss 0xFF4000 (NOLOAD)`
- `apps/rastan-direct/src/main_68k.s`
  - `arcade_tick_logic`: inserted `lea 0x00FF0000, %a5` after `bsr rastan_direct_update_inputs` and before exception-frame setup.
  - `init_staging_state`: changed `move.l #0xFFFFFFFF, bg_row_dirty` to `clr.l bg_row_dirty`.
  - `init_staging_state`: added full arcade factory-default block from design spec, including:
    - zeroing `0xFF0000-0xFF00FF`
    - setting `A5@(44)=160`, `A5@(38)=1`, `A5@(256)=1`
    - DIP/config defaults and transition buffer seeds
    - copying 39-byte config table to `A5+0x0140`

Confirmed unchanged (as required):
- `genesistan_hook_tilemap_plane_a` still sets `lea 0x00FF0000, %a5`.
- `genesistan_hook_tilemap_bg_fill` unchanged and does not use A5.
- Dead `lea 0x00FF0000, %a5` in `init_staging_state` kept in place.

5. Verification Results
Build:
- Command: `source tools/setup_env.sh && make -C apps/rastan-direct`
- Result: PASS

BSS relocation / symbol checks:
- `frame_counter` address: `0xFF4000`
- Key symbols relocated:
  - `tick_counter`: `0xFF4002`
  - `bg_row_dirty`: `0xFF4006`
  - `staged_bg_buffer`: `0xFF402C`
- Check for BSS symbols below `0xFF4000`: none found

Trace validation (20s MAME, latest build):
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0025.bin`
- Trace artifacts: `states/traces/rastan_direct_bss_relocation_20s_20260412_180111`
- Frames: `1199`
- `title_init_block@000200`: `0`
- `title_init_block@000000`: `0`
- `title_init_block@200000`: `0`
- Rapid restart loop: not positively observed in this trace window from tracer counters (no explicit restart-helper range hits), but normal title-init progression was not observed because `title_init_block` remained zero.

6. What Was NOT Changed
- No changes to `genesistan_hook_tilemap_plane_a` logic.
- No changes to `genesistan_hook_tilemap_bg_fill` logic.
- No patch-spec or patcher architecture changes.
- No rendering logic redesign.
- No global `0xFF0000` search/replace.
