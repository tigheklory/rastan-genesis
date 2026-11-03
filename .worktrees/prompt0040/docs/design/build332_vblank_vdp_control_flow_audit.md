# Build 332 VBlank + VDP Control Flow Audit

## 1. Executive Summary
The active arcade VBlank path is `_VINT_arcade_mode` in `apps/rastan/src/boot/sega.s`. In that path, tilemap data is generated during `genesistan_run_arcade_tick_lean`, committed to VRAM every frame by `genesistan_pc080sn_commit_planes`, palette is committed every frame by `genesistan_palette_commit_asm`, and scroll registers/table are committed every frame by `genesistan_scroll_commit_vdp`.

The single presentation-state failure is that scroll commit currently discards runtime staged scroll state and writes hardcoded zero H/V scroll every frame. At the same time, the arcade tilemap update path (`genesistan_bulk_tilemap_commit` and plane hooks) continues running as a strip-update presentation path. This creates a persistent mismatch between tilemap presentation updates and scroll presentation state.

## 2. Active VBlank Entry and Call Chain
Active VBlank chain identified: YES.

Entry gate:
- `_VINT` in `apps/rastan/src/boot/sega.s`.
- Gate: `tst.w arcade_vblank_active` then `bne _VINT_arcade_mode`.

Active chain (`arcade_vblank_active != 0`):
1. `_VINT_arcade_mode`
2. `JOY_update`
3. `genesistan_refresh_arcade_inputs`
4. `move.w #0x8134, 0x00C00004` (display off)
5. sentinel/debug captures (`pc080sn_fg_buffer` probes)
6. `genesistan_run_arcade_tick_lean`
   - enters patched arcade tick (`jmp 0x03A008 + ARCADE_ROM_BASE`)
   - opcode-replaced hooks are active in this tick path:
     - tilemap hooks (`genesistan_hook_tilemap_plane_a`, `genesistan_hook_tilemap_plane_b`)
     - block commit hook (`genesistan_bulk_tilemap_commit`)
     - text hooks (`genesistan_hook_text_writer_3bb48`, `genesistan_hook_text_writer_3c3fe`)
     - scroll staging hook (`genesistan_scroll_from_workram_vdp`)
     - sprite bridge (`genesistan_render_sprites_vdp_bridge` -> suppressed by `rts` in `genesistan_render_sprites_vdp_asm`)
7. `sanitize_arcade_workram`
8. `genesistan_debug_fg_proof`
9. `genesistan_pc080sn_commit_planes`
10. `genesistan_palette_commit_asm`
11. `genesistan_scroll_commit_vdp`
12. `move.w #0x8174, 0x00C00004` (display on)
13. `rte`

Conditionals/gates in active path:
- `_VINT` mode gate on `arcade_vblank_active`.
- `genesistan_bulk_tilemap_commit` has destination-range gates and early exits (`.Lbulk_exit`).
- `genesistan_bulk_tilemap_commit` has scene-range miss gate to `genesistan_bulk_preload_check`.
- `genesistan_palette_commit_asm` has populated-block scan branch and black fallback branch.
- `genesistan_render_sprites_vdp_asm` has unconditional early `rts` (Build 329 proof suppression).

Early exits present: YES.

## 3. All Active VDP Write Paths
All active VDP write paths identified: YES.

### Every frame in active VBlank
1. `_VINT_arcade_mode` (`apps/rastan/src/boot/sega.s`)
- `0xC00004` register write: `0x8134` (display off)
- `0xC00004` register write: `0x8174` (display on)
- Affects register state (VDP reg 1)

2. `genesistan_pc080sn_commit_planes` (`apps/rastan/src/startup_trampoline.s`)
- `0xC00004` write: `0x8F02` (auto-increment=2)
- `0xC00004` command: VRAM write `0xC000` (BG)
- `0xC00000` data writes: 2048 words from `pc080sn_bg_buffer`
- `0xC00004` command: VRAM write `0xE000` (FG)
- `0xC00000` data writes: 2048 words from `pc080sn_fg_buffer`
- Affects tilemap data presentation for Plane B and Plane A nametables

3. `genesistan_palette_commit_asm` (`apps/rastan/src/startup_trampoline.s`)
- `0xC00004` command: CRAM write base
- `0xC00000` data writes: 64 words each frame (mirrored 16-entry block across 4 lines)
- Affects CRAM

4. `genesistan_scroll_commit_vdp` (`apps/rastan/src/main.c`)
- `0xC00004` write: `0x8F02` (auto-increment=2)
- `0xC00004` command: VRAM write `0xF000` (HScroll table)
- `0xC00000` writes: 2 words (BG_A/BG_B hscroll)
- `0xC00004` command: VSRAM write base
- `0xC00000` writes: 2 words (BG_A/BG_B vscroll)
- Affects HScroll table region and VSRAM scroll state

### Sporadic in active tick path
5. `genesistan_preload_scene_tiles` via `genesistan_bulk_preload_check` (`apps/rastan/src/main.c`)
- Trigger path: `genesistan_bulk_tilemap_commit` scene-range miss
- Uses `VDP_loadTileData(..., DMA)` + `VDP_waitDMACompletion()`
- Affects VRAM tile graphics data (not nametable entries)

### One-shot at handoff (pre-active loop setup)
6. `force_clean_vram_init` and `apply_post_reset_test_palette` (`apps/rastan/src/main.c`)
- VRAM/CRAM/VSRAM clear and baseline register programming once at launch handoff
- Post-reset test palette writes CRAM once

## 4. Scroll Presentation State Audit
- Horizontal scroll active: YES.
- Vertical scroll active: YES.
- Scroll updated per frame: YES.

Current source of committed scroll values:
- `genesistan_scroll_commit_vdp` writes hardcoded `0` for both planes and both axes every frame.
- `genesistan_scroll_from_workram_vdp` stages live converted values in WRAM, but commit does not read those staged values.

Phase order in active frame:
- tick -> plane commit -> palette commit -> scroll commit.
- Scroll writes occur in VBlank, after plane and palette writes.

## 5. Tilemap Presentation Path Audit
Tilemap presentation path identified: YES.

Generation path during tick:
- `genesistan_hook_tilemap_plane_a` -> `genesistan_asm_tilemap_commit_bg`
- `genesistan_hook_tilemap_plane_b` -> `genesistan_asm_tilemap_commit_fg`
- `genesistan_bulk_tilemap_commit`
- text hooks also write translated tile attrs into FG buffer

Data written by these paths:
- Tile index plus palette/priority/flip attributes (`genesistan_pc080sn_tile_vram_lut` + `genesistan_pc080sn_attr_lut`)
- Writes land in WRAM staging buffers (`pc080sn_bg_buffer`, `pc080sn_fg_buffer`)

Presentation commit:
- `genesistan_pc080sn_commit_planes` streams both buffers to VRAM each frame inside VBlank.

Synchronization status:
- Tilemap and palette are committed in VBlank each frame.
- Scroll commit is also in VBlank, but currently commits fixed zero values instead of staged runtime values.

## 6. Palette / CRAM Timing Audit
- Post-reset test palette: `apply_post_reset_test_palette()` in `request_start_rastan()` after `force_clean_vram_init()`.
- Runtime palette updates: `genesistan_palette_commit_asm` each active VBlank.
- Palette writes are in the same VBlank ownership path as tilemap commit.

CRAM timing fully explains rolling output: NO.

Reason:
- CRAM timing explains visibility transitions and color availability.
- Rolling persists with active per-frame tilemap commit and active scroll commit path; the core mismatch is presentation-state coupling between tilemap updates and committed scroll state.

## 7. DMA Usage Audit
Active DMA rendering path present: YES.

Details:
- Per-frame sprite DMA path is inactive because `genesistan_render_sprites_vdp_asm` returns immediately.
- Active sporadic DMA path exists through `genesistan_bulk_preload_check` -> `genesistan_preload_scene_tiles` (`VDP_loadTileData(..., DMA)`), triggered on scene-range misses during tick.
- This DMA path transfers tile graphics to VRAM slots, not per-frame nametable streaming.

## 8. Single Presentation-State Failure
`TILEMAP_WRITES_NOT_SYNCHRONIZED_WITH_PRESENTATION_STATE`

## 9. Single Root Cause
The active frame path stages live arcade scroll values (`genesistan_scroll_from_workram_vdp`) and runs strip-based tilemap updates (`genesistan_bulk_tilemap_commit`), but `genesistan_scroll_commit_vdp` commits hardcoded zero H/V scroll every frame. This disconnect between tilemap presentation updates and committed scroll presentation state causes rolling/unstable visible output.

## 10. Single Next Implementation Target
Replace the hardcoded zero writes in `genesistan_scroll_commit_vdp` with commits of the staged per-frame values (`staged_scroll_x_fg`, `staged_scroll_x_bg`, `staged_scroll_y_fg`, `staged_scroll_y_bg`) in the same active VBlank phase.

## 11. Final Verdict
The active VBlank control flow is coherent and deterministic. The remaining rolling symptom comes from one presentation-state mismatch: per-frame tilemap updates are committed while scroll commit discards staged runtime scroll and forces zero each frame.
