# Title Screen Composition Ownership Audit

## 1. Executive Summary

- The RASTAN sword logo is **PC080SN BG tilemap tiles** — a 28×20 tile block written from ROM data at `0x5B0B2` to the BG C-window at `0xC00328` via routine `0x5A38E`→`0x5A4DE`. On Genesis, this C-window write is **redirected to `genesistan_cwindow_null`** (a 2-word null sink) by the spec patcher. The tilemap data is silently discarded. Since the nametable entries never reach the VDP plane, tile indices are never referenced, `tile_cache_get()` is never called, and **tile graphics are never DMA'd to VRAM**.
- The TAITO text, copyright lines, and credit display are **FG text writer output** via `0x3BB48` with text IDs 12/30, 32, 18, 19. After Build 300's text writer fix, this path produces correctly positioned text.
- **PC090OJ sprites ARE used** — 42 sprite descriptors initialized by `0x3B8B0` (from `startup_common`) to `0xD00020`–`0xD00128`. These are for animated overlay elements (sword glint, metallic shine). On Genesis, these writes go to `genesistan_shadow_d00000_words` but are **never read** by the sprite rendering pipeline, which only reads Block-A at workram offset `0x11B2` (mapped to `0xD003C0` on arcade).
- The **palette conversion** at `0x59AD4` writes to `0x200000` which IS correctly redirected to `genesistan_palette_clcs` by the spec patcher. Palette data is captured.
- The fundamental failure: the Genesis translation intercepts PC080SN tilemap writes only via **strip builder call hooks** at `0x55968`/`0x55990`. The title screen bypasses the strip builder entirely, using **direct block writes** to the C-window. These direct writes are null-sunk by design (stability measure), making the entire title screen background invisible.

---

## 2. Element Ownership Table

| Element | Source System | Data Origin | Arcade Routine | Genesis Hook | Status |
|---------|-------------|-------------|----------------|--------------|--------|
| RASTAN sword logo (base) | PC080SN BG tilemap | ROM `0x5B0B2` (28×20 tile indices) | `0x5A38E` → `0x5A4DE` block copy to C-window `0xC00328` | **NONE** — C-window write null-sunk | **MISSING** |
| Sword animated overlays | PC090OJ sprites | ROM tables at `0x3B950`/`0x3B9B0`/`0x3B9D4` | `0x3B8B0` writes 42 entries to `0xD00020`–`0xD00128` | Shadow captured but **not read** by sprite pipeline | **MISSING** |
| Background fill/sky | PC080SN BG tilemap | Same 28×20 block (tile `0x00AD` = background fill) | Same `0x5A38E` path | **NONE** | **MISSING** |
| "1UP", "HIGH SCORE", "2UP" | FG text writer | ROM text table entry (text IDs from `0x3BB7C` jump table) | `0x3BB48` with ID in D0 | `genesistan_hook_text_writer_3bb48_impl` | **WORKING** (Build 300+) |
| "TAITO" styled text | FG text writer | ROM text table entry (one of IDs 18/19) | `0x3BB48` | Same text writer hook | **WORKING** (Build 300+) |
| "© 1987 TAITO CORPORATION JAPAN" | FG text writer | ROM text table entry | `0x3BB48` | Same text writer hook | **WORKING** (Build 300+) |
| "ALL RIGHTS RESERVED" | FG text writer | ROM text table entry | `0x3BB48` | Same text writer hook | **WORKING** (Build 300+) |
| "CREDIT 0" | FG text writer | ROM text table entry (ID 32) | `0x3BB48` | Same text writer hook | **WORKING** (Build 300+) |
| Per-frame animated sprites | PC090OJ sprites | Workram offset `0x11B2` (Block-A, 18 entries) | `0x41F5E` copies workram → `0xD003C0` | `genesistan_sprite_tile_prepare()` + `genesistan_sprite_commit_asm()` | **PARTIAL** — only populated entries render |

---

## 3. VRAM Population Analysis

### How Assets Reach VRAM on Arcade Hardware

On the arcade, the PC080SN chip has its own internal tilemap RAM and its own tile ROM (character generator). The CPU writes nametable entries (attr+tile pairs) to the chip via two address aliases:

- **`0x200000`–`0x20FFFF`**: PC080SN device registers (MAME: `pc080sn_device::word_w`)
- **`0xC00000`–`0xC0FFFF`**: PC080SN device registers (same physical chip, second address decode)

The chip renders directly from its internal RAM + ROM. No separate "VRAM upload" step is needed — writing nametable entries is sufficient.

### Why Assets Are NOT in Genesis VRAM

**Three-stage failure chain:**

**Stage 1 — Nametable data null-sunk:**
The spec patcher (`startup_title_remap.json`) rewrites all C-window addresses in the `game_engine_059b1a` code range:
```json
{
  "range": "game_engine_059b1a",
  "arcade_base": "0x00C00000",
  "arcade_end": "0x00D00000",
  "symbol": "genesistan_cwindow_null"
}
```
The `moveal #0xC00328, %a1` instruction at `0x5A38E` gets its target address rewritten from `0xC00328` to `genesistan_cwindow_null`. The 28×20 tile block is written to a 2-word null buffer and silently discarded.

**Stage 2 — Tile indices never referenced:**
The Genesis tile cache (`tile_cache_get()`) loads PC080SN tiles into VDP VRAM on demand. It is called from the tilemap strip assembly (`genesistan_asm_tilemap_commit_bg/fg`) when processing nametable entries. Since the title screen's nametable entries never reach the strip pipeline (they were null-sunk), the tile indices from `0x5B0B2` are never looked up.

**Stage 3 — No tile DMA occurs:**
With no `tile_cache_get()` calls for title screen tiles, VDP VRAM never receives the tile graphics. The VRAM viewer shows no logo tiles because they were never uploaded.

### Answer: We Are Failing to Reference the Tiles

The tiles exist in cartridge ROM (`rastan_pc080sn[]`). The tile cache is capable of loading them. The failure is that the **nametable entries pointing to those tiles are discarded before they can trigger the cache**. The chain is:

```
ROM tile data ──exists──→ rastan_pc080sn[524288]     ✓ present
Nametable entries ──written to──→ C-window 0xC00328   ✓ arcade code executes
C-window ──redirected to──→ genesistan_cwindow_null    ✗ DATA LOST
Nametable → tile_cache_get() → VDP VRAM               ✗ NEVER CALLED
VDP plane → screen                                      ✗ EMPTY
```

---

## 4. Sprite System Involvement

### PC090OJ Sprites ARE Used on the Title Screen — CONFIRMED

**Evidence from disassembly:**

State 0 attract handler at `0x3AA40`:
```
3aa48:  6100 0410      bsrw 0x3ae5a    ; → 0x3ae64 → 0x3b098
```

And `startup_common_continue_normal` (trampoline.s:452):
```
jsr (0x03B8B0 + ARCADE_ROM_BASE)
```

**Routine `0x3B8B0` — Sprite Descriptor Initialization:**
```
0x3B8B0: Load 24 sprite descriptors from ROM 0x3B950 → D00020
         Load 9 sprite descriptors from ROM 0x3B9B0 → D000E0
         Load 9 sprite descriptors from ROM 0x3B9D4 → D00128
         Total: 42 sprite descriptors
```

Each descriptor is 8 bytes (4 words): `{zero, y_pos_byte, x_pos_byte, tile_code_word}`. The tile codes are transformed via `jsr 0x5B512` before writing.

**These sprites form the animated overlay elements**: sword blade metallic glint, animated shine effects. The static RASTAN text/background is PC080SN tilemap; the animated visual elements layered on top are sprites.

### Genesis Sprite Pipeline Status

The Genesis sprite pipeline reads from **workram offset `0x11B2`** (Block-A, 18 entries) and **offset `0x0170`** (Block-B, 4 entries). Both `genesistan_sprite_tile_prepare()` and `genesistan_sprite_commit_asm()` use hardcoded address `0xE0FF11FE` as the Block-A source.

**The 42 sprites from `0x3B8B0`** are written to D00020–D00128 → redirected to `genesistan_shadow_d00000_words`. This shadow buffer is **NEVER READ** by the sprite pipeline. The pipeline only reads workram `0x11B2`/`0x0170` blocks.

**Result:** Static title screen sprites (sword, logo overlays) are **invisible on Genesis**. Only sprites that the arcade's per-frame tick logic (`0x41F5E`) stages into workram Block-A/B are rendered. The small dots visible in the Build 300 screenshot are likely a few per-frame sprite entries with valid tile codes.

### Sprite Rendering is Not the Primary Logo System

The 42 sprites from `0x3B8B0` are overlay/animation elements. The BASE logo (the "RASTAN" text and sword outline) is PC080SN tilemap tiles. Even if all 42 sprites rendered correctly, the logo would still be incomplete without the tilemap base layer.

---

## 5. PC080SN Responsibility — CONFIRMED as Primary Title Screen System

### PC080SN IS Responsible for the Title Screen Background + Logo

**Proof:**

1. **Routine `0x5A356`** (called from state 1 handler at `0x3AA54`):
   - Calls `0x59AD4` with source data at `0x5A6FA` → palette conversion to `0x200000` (redirected to `genesistan_palette_clcs`)
   - Calls `0x5A38E` → copies 28×20 tile grid from ROM `0x5B0B2` to BG C-window at `0xC00328`

2. **Data at `0x5B0B2`** contains tile indices:
   ```
   00ad 00ad 00ad 00ad 00ad 00ad 00ad 00ad    ← background fill (tile 0x00AD)
   00ad 00ad 00ad 00ad 00ad 21b6 21b7 00ad    ← logo tiles start (0x21B6, 0x21B7)
   00ad 00ad 00ad 00ad 00ad 00ad 21c2 21c3    ← more logo tiles
   ```
   The non-0xAD entries are specific PC080SN tile indices that compose the RASTAN logo and background scene.

3. **Copy routine `0x5A4DE`** writes attr+tile pairs to the C-window:
   ```
   Inner loop: *A1++ = D2 (attr=1), *A1++ = *A0++ (tile index from ROM)
   Outer loop: advance A1 by 256 bytes (= 1 C-window column) per row
   Dimensions: 28 columns × 20 rows = 560 cells
   ```
   At 8×8 pixels per tile: 224×160 pixels — covers the center screen area.

4. **Routine `0x3AE64`** (called during state 0 setup) CLEARS both C-windows:
   ```
   Fill 0xC00100 with 0x00000020 (1900 words) → clear BG C-window
   Fill 0xC08100 with 0x00000020 (1900 words) → clear FG C-window
   ```
   This prepares clean tilemap planes before the title screen data is loaded.

### Why Current Focus on PC080SN Strip Builder Is Insufficient

The strip builder hooks at `0x55968`/`0x55990` handle **scrolling tilemap updates during gameplay**. These are called by the arcade's column/row advance routines as the camera pans. The title screen does NOT use the strip builder — it writes the ENTIRE tilemap as a single block via `0x5A4DE`.

The Genesis translation has **no mechanism to intercept bulk C-window block writes**. The spec patcher redirects them to a null buffer for stability (preventing VDP corruption from raw C-window address writes). This is correct for preventing crashes but means the title screen tilemap is invisible.

---

## 6. Failure Classification

| # | Class | Affected Elements | Root Cause |
|---|-------|-------------------|------------|
| 1 | **Missing nametable consumption** | RASTAN logo, background fill, all BG tilemap content | C-window block writes at `0x5A38E` null-sunk by spec patcher (`genesistan_cwindow_null`). Strip builder hooks cannot intercept bulk writes. No alternative path exists to capture and replay these nametable entries to the VDP. |
| 2 | **Wrong pipeline assumption** | All static title sprites (sword, logo overlays) | Sprite rendering pipeline reads only workram blocks `0x11B2`/`0x0170`. Static sprites at `D00020`–`D00128` (from `0x3B8B0`) go to shadow memory that is never read. The pipeline assumes all visible sprites are staged through workram Block-A/B by the per-frame tick. |
| 3 | **Missing sprite upload** (secondary) | Animated sprite elements | Even for sprites that DO reach the rendering pipeline via workram, the attract mode may only populate a subset of entries. The VRAM viewer shows minimal sprite tile content. |

### What Is NOT a Failure

| System | Status | Explanation |
|--------|--------|-------------|
| Palette capture | **WORKING** | `0x59AD4` writes to `0x200000` → correctly redirected to `genesistan_palette_clcs`. After Build 300 wired `load_arcade_palette()`, palette data reaches VDP CRAM. |
| Text rendering | **WORKING** (Build 300+) | Text writer `0x3BB48` hook correctly intercepts calls and writes to VDP plane A. Text IDs 12/30, 32, 18, 19 produce copyright text, credit display. |
| Scroll sync | **WORKING** (Build 300+) | `sync_arcade_scroll_to_vdp()` now called from V-Int handler. |
| Strip builder tilemap commits | **WORKING** | BG/FG strip hooks correctly convert C-window strip operations to VDP writes. Not relevant to title screen (title screen doesn't use strip builder). |

---

## 7. Evidence References

### Arcade Disassembly Addresses

| Address | Function | Writes To |
|---------|----------|-----------|
| `0x3AA40` | State 0 attract init | Calls 0x3ADD8, 0x3AD4C, 0x3AE5A |
| `0x3AA54` | State 1 title screen setup | Calls 0x5A356, then text writer 0x3BB48 ×4 |
| `0x5A356` | Title screen data loader | Calls 0x59AD4 (palette), 0x5A38E (tilemap) |
| `0x59AD4` | Palette converter | Writes transformed colors to `0x200000` |
| `0x5A38E` | Tilemap block writer | Writes 28×20 grid to `0xC00328` via 0x5A4DE |
| `0x5A4DE` | 2D copy routine | `*A1++ = attr; *A1++ = tile` in nested loop |
| `0x3AE64` | C-window clear | Fills `0xC00100` and `0xC08100` with space tiles |
| `0x3AD4C` | Sprite RAM clear | Fills `0xD00000`/`0xD00170` with sentinel 0x100 |
| `0x3B8B0` | Sprite descriptor init | Writes 42 entries to `D00020`/`D000E0`/`D00128` |
| `0x3BB48` | Text writer | Writes text to FG C-window (hooked on Genesis) |
| `0x41F5E` | Per-frame sprite copy | Copies workram `0x11B2` → `D003C0` |

### Genesis Implementation Files

| File | Key Code | Function |
|------|----------|----------|
| `main.c:1269–1285` | `pc080sn_dest_ptr_to_row_col()` | Strip dest_ptr decode (fixed Build 298) |
| `main.c:1287–1310` | `genesistan_hook_tilemap_plane_a()` | BG strip hook — only handles strip builder calls |
| `main.c:1312–1338` | `genesistan_hook_tilemap_plane_b()` | FG strip hook — only handles strip builder calls |
| `main.c:1371–1424` | `text_writer_ptr_to_xy()` | Text coordinate decode (fixed Build 300) |
| `main.c:1494–1547` | `genesistan_hook_text_writer_3bb48_impl()` | Text writer hook — CALL-level intercept |
| `main.c:1064–1147` | `genesistan_sprite_tile_prepare()` | Reads Block-A from `0xE0FF11FE` (workram) |
| `startup_trampoline.s:81–160` | `genesistan_sprite_commit_asm()` | SAT writer — reads same Block-A address |
| `startup_trampoline.s:172–290` | `genesistan_asm_tilemap_commit_bg()` | BG strip VDP writer |
| `startup_trampoline.s:296–426` | `genesistan_asm_tilemap_commit_fg()` | FG strip VDP writer |

### Spec Patcher Rules

| Rule | Effect |
|------|--------|
| `game_engine_059b1a` C-window → `genesistan_cwindow_null` | All C-window writes in `0x59B1A`–`0x60000` null-sunk |
| `palette_convert_59ad4` `0x200000` → `genesistan_palette_clcs` | Palette writes correctly captured |
| `game_engine_059b1a` D-window → `genesistan_shadow_d00000_words` | Sprite RAM writes captured in shadow |
| Opcode replace at `0x55968` | Strip builder BG → `genesistan_hook_tilemap_plane_a` |
| Opcode replace at `0x55990` | Strip builder FG → `genesistan_hook_tilemap_plane_b` |
| Opcode replace at `0x3BB48` | Text writer → `genesistan_hook_text_writer_3bb48` |

### ROM Data Sources

| Address | Content | Size |
|---------|---------|------|
| `0x5A6FA` | Title screen palette data (source for `0x59AD4`) | Variable (0xFFFF-terminated) |
| `0x5B0B2` | Title screen BG tilemap tile indices (28×20 grid) | ~1120 bytes (560 words) |
| `0x3B950` | Sprite descriptor table 1 (24 entries) | 48+ bytes |
| `0x3B9B0` | Sprite descriptor table 2 (9 entries) | 18+ bytes |
| `0x3B9D4` | Sprite descriptor table 3 (9 entries) | 18+ bytes |

---

## 8. Screenshot Reconciliation

### MAME Arcade Screenshot (Ground Truth)

| Visual Element | System | Rendering Path |
|---------------|--------|----------------|
| Gold/brown background gradient | PC080SN BG tiles (tile `0x00AD` + variants) | Nametable at `0xC00328` |
| "RASTAN" metallic gold text | PC080SN BG tiles (indices `0x21B6`, `0x21B7`, `0x21C2`, `0x21C3`, etc.) | Same nametable block |
| Sword blade behind text | PC090OJ sprites (24 entries at `D00020`) | `0x3B8B0` init |
| Metallic glint/shine animation | PC090OJ sprites (9+9 entries at `D000E0`/`D00128`) | `0x3B8B0` init |
| "1UP", "HIGH SCORE 275100", "2UP" | FG text writer | `0x3BB48` text IDs |
| "TAITO" | FG text writer | `0x3BB48` text ID 18 or 19 |
| "© 1987 TAITO CORPORATION JAPAN" | FG text writer | `0x3BB48` text ID 18 or 19 |
| "ALL RIGHTS RESERVED" | FG text writer | `0x3BB48` text ID 18 or 19 |
| "CREDIT 0" | FG text writer | `0x3BB48` text ID 32 |

### Build 300 Genesis Screenshot (Current State)

| What's Visible | Why |
|---------------|-----|
| Brown/orange solid fill | `load_arcade_palette()` now loads palette; brown is likely PAL line 0 or 1 background color from the captured arcade palette. No BG tiles to show the gradient/scene. |
| Small scattered dots | Per-frame sprite entries in workram Block-A. A few entries are populated → a few sprites render with DMA'd tiles. Not the full 42-sprite logo. |
| Partial text fragments | Text writer working (Build 300 fix), but many characters may overlap or be from attract-state text cycles. "CREDIT", alphabet visible in VRAM = font tiles loaded by text writer. |
| No RASTAN logo | BG tilemap block write null-sunk. Tile indices never reach VDP. No tile DMA. |
| No sword graphic | Static sprite descriptors at D00020–D00128 in shadow memory, never read by rendering pipeline. |
| "ABCDEFGHIJKLMNOPQRSTUVWXYZ" in VRAM | Font glyph tiles loaded by `tile_cache_get()` via text writer hook. Proves text writer and tile cache ARE functional. |

### VRAM Viewer Analysis

The VRAM viewer in the screenshot shows:
- **Row 1**: Small partial tiles + "CREDIT" text fragment — font tiles cached by text writer
- **Row 2**: "AOMP.1987" + garbled — more text writer cached tiles, partial strings
- **Bottom**: Full alphabet "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + digits + punctuation — complete font glyph set

**What's ABSENT from VRAM**: Any large graphical tiles (logo components, background art, sword pieces). These PC080SN tiles were never loaded because their nametable references were null-sunk before `tile_cache_get()` could be triggered.
