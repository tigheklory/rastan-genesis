# Current C-Owned VBlank Graphics Responsibilities — Forensic Analysis

## 1. Executive Summary

The live VBlank callback `genesistan_frontend_live_vint_handoff()` calls 8 functions per frame. Of these, **5 are C-owned graphics/display responsibilities** that directly touch VDP, CRAM, or VSRAM hardware. An additional **2 C functions** are called indirectly via arcade ROM opcode_replace hooks during the arcade tick: the text writers (`3bb48_impl`, `3c3fe`) and the sprite renderer (`genesistan_render_sprites_vdp`).

The single leading culprit is **`load_arcade_palette()`** — it overwrites ALL 64 CRAM entries every frame, including the palette lines used by the text/tilemap system, using a scanning heuristic that may select the wrong 64-color block from the 2048-entry `genesistan_palette_clcs` buffer.

## 2. Live VBlank Call Graph (Graphics-Relevant Only)

```
genesistan_frontend_live_vint_handoff()  [C, per-frame, main.c:2103]
  ├── genesistan_refresh_arcade_inputs()     [C, LOGIC - no hardware]
  ├── genesistan_run_original_frontend_tick() [ASM, per-frame]
  │     └── JMP 0x03A208 (arcade V-Int handler)
  │           ├── (arcade code) → genesistan_scroll_from_workram_vdp()  [C, opcode_replace]
  │           │     └── VDP_setHorizontalScroll, VDP_setVerticalScroll (BG_A, BG_B)
  │           ├── (arcade code) → genesistan_hook_text_writer_3bb48_impl()  [C, opcode_replace]
  │           │     └── VDP_setTileMapXY (BG_A nametable)
  │           ├── (arcade code) → genesistan_hook_text_writer_3c3fe()  [C, opcode_replace]
  │           │     └── VDP_setTileMapXY (BG_A nametable)
  │           ├── (arcade code) → genesistan_render_sprites_vdp()  [C, opcode_replace]
  │           │     └── VDP_loadTileData (VRAM DMA), VDP_setSpriteAttribute (SAT)
  │           ├── (arcade code) → genesistan_bulk_tilemap_commit  [ASM, opcode_replace at 0x5A4DE]
  │           │     └── Direct VDP data port writes (nametable BG_A/BG_B)
  │           ├── (arcade code) → genesistan_asm_tilemap_commit_bg  [ASM, opcode_replace]
  │           │     └── Direct VDP data port writes (nametable BG_B)
  │           └── (arcade code) → genesistan_asm_tilemap_commit_fg  [ASM, opcode_replace]
  │                 └── Direct VDP data port writes (nametable BG_A)
  ├── sanitize_arcade_workram()              [C, LOGIC - no hardware]
  ├── load_arcade_palette()                  [C, GRAPHICS → CRAM DMA]
  ├── sync_arcade_scroll_to_vdp()            [C, GRAPHICS → VDP scroll regs]
  │     └── genesistan_scroll_from_workram_vdp() [C]
  ├── genesistan_sprite_tile_prepare()       [C, GRAPHICS → VRAM DMA]
  ├── refresh_frontend_sprite_palettes()     [C, GRAPHICS → CRAM]
  └── genesistan_sprite_commit_asm()         [ASM, GRAPHICS → VRAM SAT 0xF800]
```

## 3. Inventory of C-Owned Graphics/Display Responsibilities

### Per-Frame (VBlank Callback Path)

| # | Function | File:Line | Hardware | Frequency | Category |
|---|----------|-----------|----------|-----------|----------|
| 1 | `load_arcade_palette()` | main.c:626 | CRAM (DMA, 64 colors) | Per-Frame | Palette |
| 2 | `sync_arcade_scroll_to_vdp()` → `genesistan_scroll_from_workram_vdp()` | main.c:2098, 1701 | VDP scroll regs (BG_A H/V, BG_B H/V) | Per-Frame | Scroll |
| 3 | `genesistan_sprite_tile_prepare()` | main.c:1080 | VRAM (DMA, up to 18×128 bytes tile data) | Per-Frame | Sprite tiles |
| 4 | `refresh_frontend_sprite_palettes()` | main.c:1186 | CRAM (4×16 colors via PAL_setColor) | Per-Frame | Sprite palette |
| 5 | `genesistan_render_sprites_vdp()` | main.c:1773 | VRAM (DMA tiles) + SAT (sprite attributes) | Per-Frame (via opcode_replace) | Sprite render |

### Per-Frame (Opcode-Replace Hooks, Called from Arcade Tick)

| # | Function | File:Line | Hardware | Category |
|---|----------|-----------|----------|----------|
| 6 | `genesistan_scroll_from_workram_vdp()` | main.c:1701 | VDP scroll regs | Scroll (duplicate call) |
| 7 | `genesistan_hook_text_writer_3bb48_impl()` | main.c:1642 | VDP nametable (BG_A) via VDP_setTileMapXY | Tilemap/Text |
| 8 | `genesistan_hook_text_writer_3c3fe()` | main.c:1720 | VDP nametable (BG_A) via VDP_setTileMapXY | Tilemap/Text |

### One-Shot Init (request_start_rastan)

| # | Function | File:Line | Hardware | Category |
|---|----------|-----------|----------|----------|
| 9 | `restore_launcher_vdp_state()` | main.c:608 | VDP init, CRAM (4 palettes), VRAM (font), SAT | Display init |
| 10 | `genesistan_sync_title_vdp_layout()` | main.c:1427 | VDP plane/SAT address regs | Display layout |
| 11 | `genesistan_preload_scene_tiles()` | main.c:1578 | VRAM (DMA, scene tile manifest) | Tile preload |
| 12 | `clear_frontend_sprite_layer()` | main.c:1191 | SAT (clear) | Sprite init |

**Total C-owned graphics responsibilities: 12**

## 4. Logic vs Graphics Classification

| Function | Classification | Justification |
|----------|---------------|---------------|
| `genesistan_refresh_arcade_inputs()` | **A. Logic/State/Input** | Reads joypads, writes shadow registers. No hardware. |
| `genesistan_run_original_frontend_tick()` | **A. Logic/State** (trampoline) | ASM trampoline into arcade ROM. Hardware effects are through opcode_replace hooks, not this function itself. |
| `sanitize_arcade_workram()` | **A. Logic/State** | Zeroes C-window pointers in workram. No hardware. |
| `load_arcade_palette()` | **B. Graphics/Display** | Writes 64 colors to CRAM via DMA. |
| `sync_arcade_scroll_to_vdp()` | **B. Graphics/Display** | Writes scroll X/Y to VDP registers for BG_A and BG_B. |
| `genesistan_sprite_tile_prepare()` | **B. Graphics/Display** | Loads sprite tile data to VRAM via DMA. |
| `refresh_frontend_sprite_palettes()` | **B. Graphics/Display** | Writes sprite palette colors to CRAM. |
| `genesistan_render_sprites_vdp()` | **B. Graphics/Display** | Loads sprite tiles to VRAM, writes SAT attributes. |
| `genesistan_hook_text_writer_3bb48_impl()` | **B. Graphics/Display** | Writes text glyphs to BG_A nametable. |
| `genesistan_hook_text_writer_3c3fe()` | **B. Graphics/Display** | Writes text/tile entries to BG_A nametable. |
| `restore_launcher_vdp_state()` | **B. Graphics/Display** | Full VDP reinit, palette load, font load. |
| `genesistan_sync_title_vdp_layout()` | **B. Graphics/Display** | Sets plane addresses and sizes. |
| `genesistan_preload_scene_tiles()` | **B. Graphics/Display** | Bulk tile DMA to VRAM. |
| `clear_frontend_sprite_layer()` | **B. Graphics/Display** | Clears SAT. |

**Summary: 3 logic/state, 11 graphics/display** (but only the 8 per-frame ones matter for ongoing rendering).

## 5. Intent of Each Graphics Helper

| Function | Actual Intent |
|----------|--------------|
| `load_arcade_palette()` | Scan 2048-entry palette CLCS buffer for the first non-zero 64-color block, convert from arcade xRGB-444 to Genesis BGR format, and overwrite ALL 64 CRAM entries via DMA. Falls back to ROM table if no live palette captured. |
| `sync_arcade_scroll_to_vdp()` | Read arcade workram scroll offsets (BG X/Y, FG X/Y at 0x10AE/0x10B0/0x10EC/0x10EE), negate, apply vertical crop bias, write to VDP scroll registers for BG_A and BG_B planes. |
| `genesistan_sprite_tile_prepare()` | Deduplicate up to 18 sprite entries from Block-A (0xE0FF11FE). For each unique code, DMA 4 tiles (128 bytes) from pc090oj ROM to VRAM. Build per-entry VRAM tile index and attribute (palette/flip) LUTs for the commit pass. |
| `refresh_frontend_sprite_palettes()` | Refresh all 4 palette lines (64 colors) for sprite use. For each entry, prefer runtime CLCS capture, fall back to ROM table. Writes via PAL_setColor (CRAM). |
| `genesistan_render_sprites_vdp()` | Full sprite pipeline: scan 2 workram sprite blocks (22 entries total), deduplicate tiles, DMA tile data to VRAM, build palette bank map, write SAT attributes via SGDK VDP_setSpriteAttribute. Called from arcade tick via opcode_replace. |
| `genesistan_hook_text_writer_3bb48_impl()` | Replace arcade 0x03BB48 text writer. Read text descriptor table, decode text string, convert each glyph to arcade tile → LUT → VRAM slot, write nametable entry to BG_A via VDP_setTileMapXY. Also stages shadow copy in workram. |
| `genesistan_hook_text_writer_3c3fe()` | Replace arcade 0x03C3FE secondary text writer. Read 6-byte descriptors, map tile codes through LUT, write to BG_A nametable. |
| `restore_launcher_vdp_state()` | Full VDP reinit for title screen transition: VDP_init(), 320px mode, load 4 launcher palettes (not arcade palettes), load font tiles and DIP indicator tiles, clear SAT. |
| `genesistan_sync_title_vdp_layout()` | Configure VDP plane layout: 64×32 plane size, BG_A at 0xE000, BG_B at 0xC000, SAT at 0xF800, window off. |
| `genesistan_preload_scene_tiles()` | Bulk load all tiles for the target scene from ROM manifest to VRAM. Each manifest entry maps (arcade_tile_index → vram_slot). |
| `clear_frontend_sprite_layer()` | Clear SAT so no stale sprites render during transition. |

## 6. Responsibilities Incorrectly Owned by C

| Function | Should remain in C? | Future ownership | Reason |
|----------|---------------------|------------------|--------|
| `load_arcade_palette()` | **NO** | Assembly or opcode hook | Overwrites all CRAM every frame using a scanning heuristic. The arcade palette system writes to known addresses; an opcode hook at the write site would capture exactly the right values without scanning. The scan-and-overwrite approach clobbers palette state set by other systems (text, tilemap). |
| `sync_arcade_scroll_to_vdp()` | **NO** | Already has opcode hook (`genesistan_scroll_from_workram_vdp` at 0x03B098/0x03B09E); the C wrapper in VBlank is a **redundant duplicate call**. The opcode hook already runs during the arcade tick. The VBlank wrapper should be removed. |
| `genesistan_sprite_tile_prepare()` | **NO** | Assembly (consolidated with sprite_commit_asm) | Per-frame DMA of up to 18×128 bytes inside VBlank is a heavy C path with interrupt disable/enable pairs per tile. Should be assembly with batched DMA. |
| `refresh_frontend_sprite_palettes()` | **NO** | Should be subsumed by correct palette ownership | Currently re-applies palette because `load_arcade_palette()` clobbers it. If palette ownership is fixed, this becomes unnecessary. |
| `genesistan_render_sprites_vdp()` | **NO** | Assembly (consolidate with sprite_commit_asm + sprite_tile_prepare) | Heavy C sprite pipeline called from opcode_replace during arcade tick. Contains DMA, SAT writes, palette bank mapping — all display-level work that conflicts with the other sprite C paths. |
| `genesistan_hook_text_writer_3bb48_impl()` | **Partially OK** | Text LUT lookup can stay in C; the VDP_setTileMapXY call is acceptable since it's glyph-at-a-time. The shadow staging in workram is correct arcade emulation. |
| `genesistan_hook_text_writer_3c3fe()` | **Partially OK** | Same as above — acceptable in C for now. |
| `restore_launcher_vdp_state()` | **YES** (one-shot init) | Stays in C. One-shot setup is appropriate for C. |
| `genesistan_sync_title_vdp_layout()` | **YES** (one-shot init) | Stays in C. |
| `genesistan_preload_scene_tiles()` | **YES** (one-shot init) | Stays in C. Bulk preload is init-time only. |
| `clear_frontend_sprite_layer()` | **YES** (one-shot init) | Stays in C. |

## 7. Single Leading Culprit

### `load_arcade_palette()` (main.c:626)

**Evidence:**

1. **Screenshot evidence (Build 306)**: Main screen is black. CRAM debugger shows palette line 0 has rich colors (greys, warm tones) but they are the LAUNCHER palette colors, not arcade title screen colors. Palette lines 2-3 show cyan/white/red — these are the SGDK default or partially-overwritten entries. The arcade title screen requires specific palette entries in line 0 for text visibility and line 1+ for background tiles.

2. **How it works**: Scans the 2048-entry `genesistan_palette_clcs` buffer for the FIRST non-zero 64-entry block. If found, converts and overwrites ALL 64 CRAM entries. If not found, falls back to `genesistan_palette_rom_table`.

3. **Why it's wrong**:
   - The scan picks the first non-zero block, which may not be the correct palette for the current display state.
   - It writes ALL 64 entries every frame, clobbering palette lines used by text (which may need specific entries for visibility).
   - `refresh_frontend_sprite_palettes()` exists ONLY because `load_arcade_palette()` destroys sprite palette state — it's a compensating workaround, not an independent responsibility.
   - The arcade system writes palettes to specific CLCS offsets at specific times. The scan-and-overwrite-everything approach is fundamentally different from how the arcade handles palette.

4. **CRAM debugger confirmation**: The Build 306 CRAM shows palette line 0 with launcher-like greys and warm colors. The font/text palette (which would make text visible) would need a high-contrast palette in at least one line. The current palette is the fallback ROM table or a wrong CLCS block — either way, text rendered to the nametable would be invisible or wrong-colored against black.

5. **The vertical dots/noise in the main display** are consistent with tiles being written to the nametable (text writers ARE running) but the palette making them nearly invisible — only a few scattered pixels have enough contrast to show through.

## 8. Orphan Risk Analysis

### If `load_arcade_palette()` were removed right now:

**What breaks:**
- All 64 CRAM entries would retain whatever was last written by `restore_launcher_vdp_state()` (the 4 launcher palettes). The launcher palettes are designed for the config screen, not the arcade title screen.
- No runtime palette updates would occur. The arcade palette capture system (`genesistan_palette_clcs`) would still fill, but nothing would read and apply it to CRAM.
- Sprites and tilemap tiles would render with wrong colors (launcher colors instead of arcade colors).

**What must be preserved when moving to assembly/opcode ownership:**
- The CLCS → Genesis color format conversion (xRGB-444 → 0BBB0GGG0RRR0)
- The mapping from arcade palette bank to CRAM palette line
- The timing: palette must be committed during VBlank to avoid mid-frame tearing
- The palette routing: different palette banks serve different display layers (BG tiles, text, sprites). The replacement must write the CORRECT bank to the CORRECT CRAM lines, not blindly overwrite all 64 entries.
- `refresh_frontend_sprite_palettes()` can be removed once palette ownership is correctly established — it's purely compensatory.

## 9. Final Analysis Verdict

The live VBlank path has **8 per-frame C-owned graphics responsibilities** and **4 one-shot C init functions**. Of the per-frame responsibilities:

- **5 should NOT remain in C**: `load_arcade_palette`, `sync_arcade_scroll_to_vdp` (redundant), `genesistan_sprite_tile_prepare`, `refresh_frontend_sprite_palettes` (compensatory), `genesistan_render_sprites_vdp`
- **2 are acceptable in C**: text writer hooks (3bb48, 3c3fe)
- **1 is already assembly**: `genesistan_sprite_commit_asm`

The **leading culprit** is `load_arcade_palette()`. It overwrites all 64 CRAM entries every frame using a block-scanning heuristic that selects the wrong palette data, making correctly-placed nametable tiles invisible. The fix direction is to replace the scan-and-overwrite approach with targeted palette writes driven by the arcade's own palette write path (opcode hooks at the CLCS write sites), writing only the correct palette banks to the correct CRAM lines.
