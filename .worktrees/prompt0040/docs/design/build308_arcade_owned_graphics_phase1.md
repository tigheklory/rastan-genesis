# Build 308 — Arcade-Owned Graphics Phase 1 Report

## 1. Build

- **Output:** `dist/Rastan_308.bin` (3,932,160 bytes)
- **Build tool:** `postpatch_lenient.py` (28 opcode_replace warnings, all pre-existing shift-related operand mismatches — applied anyway)
- **Compiler warnings:** 5 unused-function warnings (expected: removed functions still defined but no longer called)

## 2. What Changed

### VBlank Callback (main.c)

**Before (Build 306):** 8 per-frame calls — 5 were C-owned graphics:
```
genesistan_refresh_arcade_inputs()
genesistan_run_original_frontend_tick()
sanitize_arcade_workram()
load_arcade_palette()                    ← REMOVED
sync_arcade_scroll_to_vdp()              ← REMOVED
genesistan_sprite_tile_prepare()         ← REMOVED
refresh_frontend_sprite_palettes()       ← REMOVED
genesistan_sprite_commit_asm()           ← REMOVED (old ASM sprite commit)
```

**After (Build 308):** 4 calls — logic + single palette commit:
```
genesistan_refresh_arcade_inputs()       (logic: input shadow regs)
genesistan_run_original_frontend_tick()  (arcade tick: all graphics via opcode hooks)
sanitize_arcade_workram()                (logic: stability sanitize)
genesistan_palette_commit_asm()          (NEW: single CLCS→CRAM transfer)
```

### New Assembly Routines (startup_trampoline.s)

1. **`genesistan_palette_commit_asm`** (0x202DFA)
   - Reads `genesistan_palette_clcs[0..63]`
   - Converts CLCS xRGB-444 → Genesis 0BBB0GGG0RRR0 format
   - Streams 64 colors to CRAM via VDP data port
   - Falls back to `genesistan_palette_rom_table` if CLCS empty

2. **`genesistan_render_sprites_vdp_asm`** (0x202E5C)
   - Full assembly sprite pipeline replacing C `genesistan_render_sprites_vdp()`
   - Pass 1: DMA tile data from `rastan_pc090oj` ROM for each visible sprite
     - Block-A: 18 entries at A5+0x11B2
     - Block-B: 4 entries at A5+0x0170
     - Tile base: VRAM index 1024, 128 bytes per cell
   - Pass 2: Write SAT entries to VDP at VRAM 0xF800
     - Y/X with +0x80 SAT bias, code masking, colbank palette, flip bits
     - Priority on, size 2×2, link chain

3. **`genesistan_render_sprites_vdp_bridge`** updated to call `genesistan_render_sprites_vdp_asm` (was calling C function)

## 3. MAME Trace Results (750 frames)

| Metric | Result |
|--------|--------|
| Startup init (`startup_result_code` 0→1) | Frame 295 |
| First VDP writes | Frame 300 |
| Frontend core entered | Frame 564 |
| Startup common re-entered | Frame 675 |
| Arcade state progression (`arcade_mode4` 0→1→2) | Frames 674–677 |
| Hang detected | NO |
| VDP write frequency | Every 30 frames (consistent) |

## 4. Ownership Verification

| VDP Resource | Build 306 Writers | Build 308 Writer | Duplicate Removed? |
|-------------|-------------------|-------------------|-------------------|
| Scroll H/V BG_A/B | Opcode hooks + `sync_arcade_scroll_to_vdp()` | Opcode hooks only | YES |
| CRAM entries 0-63 | `load_arcade_palette()` + `refresh_frontend_sprite_palettes()` | `genesistan_palette_commit_asm()` only | YES |
| VRAM sprite tiles | `genesistan_render_sprites_vdp()` (C) + `genesistan_sprite_tile_prepare()` | `genesistan_render_sprites_vdp_asm` only | YES |
| SAT (0xF800) | `genesistan_render_sprites_vdp()` (C) + `genesistan_sprite_commit_asm()` | `genesistan_render_sprites_vdp_asm` only | YES |
| Nametable BG_A/B | Opcode hooks only | Opcode hooks only | N/A (was clean) |

## 5. Assessment

| Question | Answer |
|----------|--------|
| Flicker improved | CANNOT CONFIRM (MAME trace is headless — no visual output) |
| Vertical noise improved | CANNOT CONFIRM (headless) |
| Black screen | CANNOT CONFIRM (headless) |
| Title text visible | CANNOT CONFIRM (headless) |
| Duplicate scroll ownership removed | **YES** — `sync_arcade_scroll_to_vdp()` removed from callback |
| Duplicate palette ownership removed | **YES** — `load_arcade_palette()` and `refresh_frontend_sprite_palettes()` removed |
| Duplicate sprite ownership removed | **YES** — C sprite renderer no longer active; assembly owns tiles + SAT |
| Sprite owner is assembly | **YES** — `genesistan_render_sprites_vdp_asm` called via bridge |
| Arcade state machine running | **YES** — `arcade_mode4` reaches 2, frontend_core entered |
| No hang | **YES** — 750 frames completed |

## 6. Design Alignment

This build implements the approved design from `docs/design/arcade_owned_graphics_replacement_design.md`:

- **Rainbow Islands pattern achieved:** Single owner per VDP resource, intent-to-VDP-primitive mapping
- **Cadash anti-pattern eliminated:** No C-side scanning heuristic (`load_arcade_palette` removed)
- **Four properties satisfied:**
  1. Single owner per VDP resource — verified in §4
  2. No C-side polling/scanning of shared buffers — palette commit reads known offset
  3. Assembly for all hot-path graphics — palette and sprites both assembly
  4. WRAM staging → VDP transfer model — CLCS capture → assembly commit

## 7. Known Limitations

- Visual verification requires BlastEm or visual MAME run (not available in headless trace)
- The 28 `postpatch_lenient.py` warnings are pre-existing operand mismatches from the multi-pass shift table patcher — not related to this build's changes
- Unused C functions (`load_arcade_palette`, `sync_arcade_scroll_to_vdp`, etc.) are still defined but no longer called — can be removed in a cleanup pass
