# Final Architecture: Block-Write Hook + Scene-Scoped Tile Loading

## 1. Executive Summary

This document defines the final implementation architecture for Rastan's missing PC080SN block-write graphics subsystem and the scene-scoped VRAM tile loading model that makes it feasible on Genesis hardware.

**Two problems, one integrated solution:**

1. **Block-write translation** — The arcade's `0x5A4DE` bulk tilemap copy routine is currently null-sunk. A single assembly hook replaces it, translating each tile cell directly to VDP nametable writes using the same LUT pipeline as the existing strip builder. No buffer. No C-window shadow.

2. **Scene-scoped tile loading** — 2272 unique PC080SN tiles across all scenes cannot fit in 1164 VRAM slots simultaneously. The Python precompute assigns VRAM slots with cross-scene reuse (same slot number for tiles that never coexist). Per-scene preload manifests DMA the correct tile graphics from ROM into VRAM at scene transitions. The `tile_cache_get()` LRU cache is eliminated entirely — text glyphs join the static LUT with permanent VRAM slots.

**Key decisions:**
- Global static VRAM assignment is **rejected** (overflows by 1108 tiles)
- One global LUT with cross-scene slot reuse
- Three scene categories: Title/Attract, Gameplay, End-Round
- Text glyph tiles get permanent VRAM slots (loaded once, never evicted)
- `tile_cache_get()` eliminated from all paths — text writer uses the static LUT
- Scene transition detected inside the block-write hook via source-address lookup
- Preload fires inline before the first block-write VDP commit of a new scene
- Strip builder keeps its existing ownership; its tiles are included in Gameplay and End-Round scene preloads

---

## 2. Final System Overview

```
ARCADE CODE calls 0x5A4DE with D0/D1/D2/A0/A1
    ↓
spec patch: JMP genesistan_bulk_tilemap_commit (assembly)
    ↓
assembly entry: save registers, JSR genesistan_bulk_preload_check(A0)
    ↓
C preload check:
    look up scene_id from A0 (source ROM address) via ROM table
    if scene_id != genesistan_current_scene_id:
        call genesistan_preload_scene_tiles(scene_id)
        update genesistan_current_scene_id
    return
    ↓
assembly: decode A1 → plane (BG/FG) + starting (row, col)
    ↓
assembly: load attr_partial from pc080sn_attr_lut[key_from_D2]
    ↓
assembly: column-major nested loop:
    read tile_index from (A0)+
    vram_slot = pc080sn_tile_vram_lut[tile_index & 0x3FFF]
    tile_attr = attr_partial | vram_slot
    vdp_addr = plane_base + (row - 4) * 128 + col * 2
    write VDP control port (0xC00004) ← address command
    write VDP data port (0xC00000) ← tile_attr
    advance row (inner loop), advance col (outer loop)
    ↓
assembly: restore registers, RTS
    ↓
VDP nametable updated. Tile graphics already in VRAM from preload.
Screen shows correct scene.
```

**Coexistence with existing systems:**

| System | Relationship |
|--------|-------------|
| Strip builder (`0x55968`/`0x55990`) | Unchanged. Fires during gameplay scrolling. Its tiles are preloaded as part of Gameplay and End-Round scenes. |
| Text writer (`0x3BB48`/`0x3C3FE`) | Modified: replaces `tile_cache_get()` with static LUT lookup. Text glyph tiles have permanent VRAM slots. |
| Scroll sync (`genesistan_scroll_from_workram_vdp`) | Unchanged. Reads arcade workram scroll offsets. Now scrolls over real content placed by block writer. |
| Palette (`load_arcade_palette`) | Unchanged. Block writer does not touch palette. |
| Sprites (`genesistan_sprite_tile_prepare`) | Unchanged. Uses separate VRAM range (1024–1279). |

---

## 3. Final Block-Write Hook Strategy

### Hook Point

Replace the first 6 bytes of `0x5A4DE` with `JMP genesistan_bulk_tilemap_commit`.

**Spec patch entry** (in `startup_title_remap.json`):
```json
{
  "address": "0x05A4DE",
  "original": "3800 2449 32c2 32d8 5340",
  "replacement": "jmp genesistan_bulk_tilemap_commit",
  "why": "replace PC080SN block-copy engine with direct VDP translation"
}
```

### Register Contract at Entry

| Register | Content | Source |
|----------|---------|-------|
| D0.w | Rows per column (inner loop count) | Set by caller |
| D1.w | Number of columns (outer loop count) | Set by caller |
| D2.w | Attr word (palette bits 0–1, priority bit 13, flip bits 14–15) | Set by caller |
| A0 | Source ROM pointer (tile index words) | Set by caller |
| A1 | C-window destination address (determines plane + position) | Set by caller |

### Ownership

| Responsibility | Owner |
|---------------|-------|
| Scene preload check | **C** — `genesistan_bulk_preload_check()`, called via JSR from assembly entry |
| A1 → plane + (row, col) decode | **Assembly** — inline at entry, before loop |
| D2 → attr_partial via `pc080sn_attr_lut` | **Assembly** — inline, one lookup per call |
| Inner/outer loop + VDP writes | **Assembly** — hot path, direct port writes |
| Return to caller | **Assembly** — RTS after loop completion |

### The Hook is a Single Assembly Routine

`genesistan_bulk_tilemap_commit` in `startup_trampoline.s`. It JSRs to one C function (`genesistan_bulk_preload_check`) at the top for scene management, then performs all VDP work in assembly. No other C involvement.

---

## 4. Scene Model

### Scene Categories

| Scene ID | Name | Block-Write Sources | Strip Builder Active? | Text Glyphs Active? |
|----------|------|--------------------|-----------------------|---------------------|
| 0 | **Title/Attract** | `0x5B0B2`, `0x5A7DA`, `0x5AC72`, `0x5AF62`, `0x5AD62` | No (no scrolling) | Yes |
| 1 | **Gameplay** | `0x56A22`–`0x570C2` (6 stage HUDs) | Yes (active scrolling) | Yes |
| 2 | **End-Round** | `0x5822A`, `0x5862A`, `0x58A2A`, `0x5919C`, + animation frames from `0x581A6`/`0x581CA`/`0x581FA` | Yes (may scroll during transition) | Yes |

### Per-Scene VRAM Budget (Validated)

| Scene | Block Tiles | Strip Tiles | Text Glyphs | Total | vs 1164 | Headroom |
|-------|------------|------------|-------------|-------|---------|----------|
| Title/Attract | 781 | 0 | 42 | 823 | OK | 341 |
| Gameplay | 492 | 289 | 42 | 817 | OK | 347 |
| End-Round | 727 | 289 | 42 | 1055 | OK | 109 |

**Note:** Title/Attract does not need strip builder tiles (no scrolling during title). Previous budgets conservatively included strip tiles for all scenes. Without strip tiles, Title/Attract has 341 slots headroom — much more comfortable.

### Tile Set Reconciliation

| Tile Category | Slot Type | Present In |
|--------------|-----------|-----------|
| Text glyphs (~42) | **Permanent** — loaded once at boot, never evicted | All scenes |
| Strip builder (289) | **Scene-specific** — loaded for Gameplay + End-Round | Gameplay, End-Round |
| Title block-write (781) | **Scene-specific** — loaded for Title/Attract | Title/Attract |
| Gameplay block-write (492) | **Scene-specific** — loaded for Gameplay | Gameplay |
| End-Round block-write (727) | **Scene-specific** — loaded for End-Round | End-Round |

---

## 5. Scene-Scoped LUT / Slot Assignment Model

### The LUT Is Global. The Preload Is Per-Scene.

**`pc080sn_tile_vram_lut[16384]`** — one global ROM table. Maps every arcade tile index to exactly one VRAM slot number. This table is used by the strip builder assembly, the block-write assembly, AND the text writer. No per-scene LUT switching at runtime.

**Cross-scene slot reuse:** Two tile indices from different scenes CAN map to the same VRAM slot number, because they are never referenced simultaneously. Example:
- `lut[0x21B6] = 50` (title screen tile)
- `lut[0x2800] = 50` (end-round tile)

During the title scene, slot 50 contains tile 0x21B6's graphics (loaded by title preload). During end-round, slot 50 contains tile 0x2800's graphics (loaded by end-round preload). The nametable only references 0x21B6 during title and 0x2800 during end-round, so the correct graphics are always displayed.

**Within a single scene, all tile indices map to DISTINCT slots.** The Python precompute guarantees this.

### Slot Assignment Algorithm (Python, Build-Time)

```
1. Collect all tile indices per category:
   - text_tiles: scan ROM text tables (permanent set)
   - strip_tiles: existing descriptor table scan
   - title_tiles: scan 5 title/attract block-write source tables
   - gameplay_tiles: scan 6 gameplay HUD source tables
   - endround_tiles: scan all end-round source + animation tables

2. Build scene tile sets (what must coexist within each scene):
   - scene_0 = text_tiles ∪ title_tiles
   - scene_1 = text_tiles ∪ strip_tiles ∪ gameplay_tiles
   - scene_2 = text_tiles ∪ strip_tiles ∪ endround_tiles

3. Assign permanent slots for text_tiles:
   - slots 20, 21, 22, ... (first N after TILE_USER_INDEX)
   - these are never reused by other tiles

4. Assign scene-specific slots using greedy coloring:
   - For each tile in scene_0: assign next available slot not used by any
     other tile in scene_0
   - For each tile in scene_1: if tile already has a slot (shared with
     scene_0), keep it. Otherwise assign next available slot not used by
     any other tile in scene_1. Slots used by scene_0-only tiles ARE
     available for reuse.
   - For each tile in scene_2: same logic.
   - The slot pool is: 20..1023, 1280..1439 (1164 total),
     minus permanent text slots.

5. Build global LUT: lut[tile_index] = assigned_slot for all tiles.
   lut[tile_index] = 0 for tiles not in any scene.

6. Build per-scene preload manifests:
   - For each scene, list all (tile_index, slot) pairs where the VRAM
     content must be correct for that scene.
   - This includes permanent tiles (text) + scene-specific tiles.
   - Sentinel-terminated.
```

### Build Artifacts

| Artifact | Contents | Format | Runtime Consumer |
|----------|---------|--------|-----------------|
| `pc080sn_tile_vram_lut.bin` | Global LUT, 16384 entries | u16 BE array, 32768 bytes | Assembly: strip builder + block writer; C: text writer |
| `pc080sn_scene_preload_title.bin` | Title preload manifest | (u16 tile, u16 slot) pairs + 0xFFFF sentinel | C: `genesistan_preload_scene_tiles(0)` |
| `pc080sn_scene_preload_gameplay.bin` | Gameplay preload manifest | Same format | C: `genesistan_preload_scene_tiles(1)` |
| `pc080sn_scene_preload_endround.bin` | End-Round preload manifest | Same format | C: `genesistan_preload_scene_tiles(2)` |
| `pc080sn_attr_lut.bin` | Attr conversion, 32 entries | u16 BE array, 64 bytes | Assembly: strip builder + block writer |
| `pc080sn_source_scene_map.bin` | Source ROM addr → scene ID | (u32 addr, u8 scene_id) entries + sentinel | C: `genesistan_bulk_preload_check()` |

**`pc080sn_vram_preload.bin` is REPLACED** by the three per-scene manifests. The single monolithic preload is eliminated.

---

## 6. Required Build-Time Outputs (Python)

### Extend `precompute_pc080sn_tile_lut.py`

The existing script is extended (not split). New responsibilities:

1. **Block-write source table scan** — new function. Reads known source tables from `maincpu.bin`, collects tile indices per scene. Table addresses and dimensions are hardcoded constants (they are ROM-fixed).

2. **Text glyph tile scan** — new function. Reads ROM text tables used by `0x3BB48` text writer to identify all glyph tile indices. These get permanent VRAM slots.

3. **Scene-aware slot assignment** — replaces the current simple sequential assignment. Implements the greedy coloring algorithm from Section 5.

4. **Per-scene preload manifest generation** — new. Outputs three manifest files.

5. **Source-to-scene map generation** — new. Outputs a small ROM table mapping known A0 source addresses to scene IDs.

### Script Inputs (Unchanged)

- `build/regions/maincpu.bin`
- `build/regions/pc080sn.bin`

### Script Outputs (Extended)

| Output | Status |
|--------|--------|
| `build/pc080sn_tile_vram_lut.bin` + `.inc` | **Updated** — now includes block-write + text glyph tiles with cross-scene reuse |
| `build/pc080sn_attr_lut.bin` + `.inc` | **Unchanged** |
| `build/pc080sn_vram_preload.bin` + `.inc` | **Removed** — replaced by per-scene manifests |
| `build/pc080sn_scene_preload_title.bin` + `.inc` | **New** |
| `build/pc080sn_scene_preload_gameplay.bin` + `.inc` | **New** |
| `build/pc080sn_scene_preload_endround.bin` + `.inc` | **New** |
| `build/pc080sn_source_scene_map.bin` + `.inc` | **New** |
| `build/pc080sn_unique_tile_count.txt` | **Updated** — reports per-scene and global counts |

---

## 7. Runtime Ownership (Python / Assembly / C)

| Responsibility | Owner | Location | When |
|---------------|-------|----------|------|
| Tile/slot/scene data generation | **Python** | `precompute_pc080sn_tile_lut.py` | Build time |
| `0x5A4DE` replacement (block-write VDP commit) | **Assembly** | `genesistan_bulk_tilemap_commit` in `startup_trampoline.s` | Every `0x5A4DE` call |
| Scene change detection | **C** | `genesistan_bulk_preload_check()` in `main.c` | Called from assembly at each `0x5A4DE` entry |
| Scene tile DMA preload | **C** | `genesistan_preload_scene_tiles(scene_id)` in `main.c` | On scene change (rare — once per state transition) |
| Strip builder VDP commit | **Assembly** | `genesistan_asm_tilemap_commit_bg/fg` (existing) | Per-frame during gameplay scrolling |
| Strip builder C dispatch | **C** | `genesistan_hook_tilemap_plane_a/b` (existing) | Per-frame during gameplay scrolling |
| Text writer tile lookup | **C** | `text_writer_build_tile_attr()` — **modified** to use `pc080sn_tile_vram_lut[]` instead of `tile_cache_get()` | Per text character rendered |
| Scroll sync | **C** | `genesistan_scroll_from_workram_vdp()` (existing, unchanged) | Per V-Int |
| Initial boot preload | **C** | `genesistan_preload_scene_tiles(SCENE_TITLE)` — replaces `genesistan_preload_pc080sn_title_frontend()` | Once at game launch |

### Functions Eliminated

| Function | Reason |
|----------|--------|
| `tile_cache_get()` | Replaced by static LUT lookup. All tile slots are pre-assigned. No runtime eviction needed. |
| `genesistan_preload_pc080sn_title_frontend()` | Replaced by `genesistan_preload_scene_tiles(SCENE_TITLE)` |
| `genesistan_tile_cache_arcade[]` | No LRU cache — slots are statically assigned |
| `genesistan_tile_cache_lru[]` | Same |
| `genesistan_tile_cache_clock` | Same |

### Functions Added

| Function | Owner | Purpose |
|----------|-------|---------|
| `genesistan_bulk_tilemap_commit` | Assembly | Replaces `0x5A4DE`. Decodes A1, loops D0×D1 cells, LUT lookup, VDP writes. |
| `genesistan_bulk_preload_check(u32 source_addr)` | C | Looks up scene from source address. If scene changed, calls preload. Fast no-op if scene unchanged. |
| `genesistan_preload_scene_tiles(u8 scene_id)` | C | Walks the per-scene preload manifest. DMA-loads each tile from `rastan_pc080sn` ROM to assigned VRAM slot. |

---

## 8. Preload Trigger / Scene Transition Strategy

### When Does Preload Happen?

Preload is triggered **inside the block-write hook**, before the first VDP write of a new scene. This is self-organizing — no separate state machine monitoring is needed.

### Mechanism

1. The assembly entry of `genesistan_bulk_tilemap_commit` saves registers and calls `genesistan_bulk_preload_check(A0)`.

2. `genesistan_bulk_preload_check()` reads `A0` (source ROM pointer) and scans `pc080sn_source_scene_map` — a small ROM table (~25 entries) mapping known source addresses to scene IDs.

3. If the looked-up scene_id differs from `genesistan_current_scene_id`, it calls `genesistan_preload_scene_tiles(new_scene_id)`.

4. `genesistan_preload_scene_tiles()` disables interrupts, walks the per-scene preload manifest, DMA-loads each tile, waits for DMA completion, re-enables interrupts, and updates `genesistan_current_scene_id`.

5. Assembly continues with VDP writes. The VRAM now contains the correct tile graphics for the current scene.

### Timing Properties

| Property | Value |
|----------|-------|
| Preload frequency | Once per scene transition (rare — typically seconds apart) |
| Preload cost | ~800 tiles × 32 bytes = ~25KB DMA. At 68000 speeds: <5ms. Acceptable for a scene transition. |
| Common-case overhead | One compare (`current_scene_id == looked_up_id`) — nearly zero. |
| Recurring animation callers (every 10/28/26 frames) | No preload — scene hasn't changed. Just the fast-path compare. |
| Unknown source address (not in map) | No preload triggered. Block write proceeds with current VRAM content. Tiles may display as wrong graphics but no crash. |

### Scene Transition Points (Concrete)

| Transition | First Block-Write Caller | Source ROM | Scene ID |
|-----------|------------------------|-----------|----------|
| Boot → Title | `0x5A38E` (title screen) | `0x5B0B2` | 0 (Title) |
| Attract → Insert Coin | `0x5A3AC` | `0x5AC72` | 0 (Title) — same scene |
| Attract → Game Over | `0x5A3DE` | `0x5AF62` | 0 (Title) — same scene |
| Attract → Stage Intro | `0x5A442` | `0x5AD62` | 0 (Title) — same scene |
| Start Game → Gameplay HUD | `0x56356` | stage-dependent from `0x5635E` table | 1 (Gameplay) |
| Stage Clear → End-Round | `0x5744E` init calls | `0x5822A` etc. | 2 (End-Round) |
| End-Round Complete → Next Stage | `0x56356` again | stage-dependent | 1 (Gameplay) |

### Boot Preload

At game launch, `genesistan_preload_scene_tiles(SCENE_TITLE)` is called from the existing init path (replacing `genesistan_preload_pc080sn_title_frontend()`). This loads text glyphs + title scene tiles. The block-write hook will not need to preload until the first gameplay transition.

---

## 9. Interaction with Strip-Builder Pipeline

### Strip Builder Keeps Its Existing Ownership

The strip builder assembly (`genesistan_asm_tilemap_commit_bg/fg`) is unchanged. It uses the same global `pc080sn_tile_vram_lut` for tile lookups. It fires during gameplay and end-round scrolling.

### Strip Builder Tiles Are Scene-Budgeted

Strip builder tiles (289) are included in the Gameplay and End-Round preload manifests. They are NOT included in the Title/Attract manifest (no scrolling during title). When transitioning from Title to Gameplay, the preload loads strip builder tiles into their assigned VRAM slots alongside gameplay block-write tiles.

### Shared Slot Pool

Block-write and strip builder tiles share the same 1164-slot VRAM pool. The Python precompute assigns slots to both tile sets within each scene's budget. No tile-type partitioning of the slot range.

### No Conflict in Write Timing

| System | Fires When | VDP Target |
|--------|-----------|-----------|
| Block writer | Scene transitions (one-shot) | VDP nametable (plane addresses) |
| Strip builder | Per-frame during scrolling | VDP nametable (plane addresses) |

Both write to VDP nametable planes. They do not write simultaneously — block writer fires once at scene entry, strip builder fires per-frame afterward. The block writer initializes the plane; the strip builder incrementally updates it. This is the intended producer relationship.

### Scenes Where Both Must Coexist

| Scene | Block-Write | Strip Builder | Coexistence |
|-------|------------|--------------|-------------|
| Title/Attract | Active | Inactive | No conflict |
| Gameplay | Active (HUD setup) | Active (scrolling) | Both tiles preloaded. Different VDP plane regions. |
| End-Round | Active (quadrant fill + animation) | Possibly active | Both tiles preloaded. |

---

## 10. Text Glyph / Font Interaction

### SGDK Font Does NOT Compete

SGDK font tiles occupy slots 1440–1535 (above the PC080SN cache range). Used only by the launcher/config screen. No interaction with the block-write or strip-builder systems.

### In-Game Text Glyphs: Permanent Static Slots

**Current behavior:** `tile_cache_get()` allocates glyphs into the LRU cache on demand, competing with tilemap tiles for eviction.

**New behavior:** Text glyph tiles are assigned **permanent VRAM slots** by the Python precompute. They are loaded once at boot and never evicted. The text writer looks up `pc080sn_tile_vram_lut[glyph_tile_index]` instead of calling `tile_cache_get()`.

### Implementation Change in Text Writer

`text_writer_build_tile_attr()` currently calls `tile_cache_get(arcade_tile)` to get a VRAM slot. This is replaced with:

```c
vram_tile = genesistan_pc080sn_tile_vram_lut[arcade_tile & 0x3FFF];
```

Same one-line lookup the strip builder assembly already uses. No DMA stall per glyph. No LRU overhead.

`text_writer_build_tile_attr_from_arcade_code()` — same change.

### Headroom Reservation

Text glyph tiles (~42) get the first ~42 VRAM slots after TILE_USER_INDEX (20). These slots are permanent — never reassigned to scene-specific tiles. The remaining ~1122 slots are available for scene-specific assignment.

The per-scene budgets in Section 4 already account for text glyph slots. No additional reservation logic is needed at runtime.

---

## 11. Implementation Order for Cody

### Step 1: Python — Extend `precompute_pc080sn_tile_lut.py`

**Dependencies:** None (build-time only).

1. Add block-write source table scanner (hardcoded table addresses + dimensions from validation gate)
2. Add text glyph tile scanner (scan ROM text tables used by `0x3BB48`)
3. Add scene-aware slot assignment (greedy coloring per Section 5)
4. Generate per-scene preload manifests (three `.bin` + `.inc` files)
5. Generate source-to-scene map (`.bin` + `.inc`)
6. Remove old single `pc080sn_vram_preload.bin` generation
7. Update `build/pc080sn_unique_tile_count.txt` with per-scene + global counts

**Verification:** Run script. Confirm per-scene tile counts match validation gate numbers. Confirm no scene exceeds 1164 slots.

### Step 2: C — Scene Preload Infrastructure

**Dependencies:** Step 1 outputs.

1. Add ROM declarations in `startup_bridge.c` for the three per-scene preload manifests and source-scene map
2. Implement `genesistan_preload_scene_tiles(u8 scene_id)` — walks manifest, DMA-loads tiles
3. Implement `genesistan_bulk_preload_check(u32 source_addr)` — scene lookup + conditional preload
4. Add `genesistan_current_scene_id` state variable
5. Replace `genesistan_preload_pc080sn_title_frontend()` call with `genesistan_preload_scene_tiles(SCENE_TITLE)` at boot
6. Modify `text_writer_build_tile_attr()` and `text_writer_build_tile_attr_from_arcade_code()` to use `pc080sn_tile_vram_lut[]` instead of `tile_cache_get()`
7. Remove `tile_cache_get()`, `genesistan_tile_cache_arcade[]`, `genesistan_tile_cache_lru[]`, `genesistan_tile_cache_clock` (dead code after text writer change)

**Verification:** Build succeeds. Boot preload loads title scene tiles. Text still renders correctly using static LUT.

### Step 3: Spec Patch — Add `0x5A4DE` Hook

**Dependencies:** Step 4 (assembly function must exist first).

Add to `startup_title_remap.json`:
```json
{
  "address": "0x05A4DE",
  "original": "3800 2449 32c2 32d8 5340",
  "replacement": "jmp genesistan_bulk_tilemap_commit",
  "why": "replace PC080SN block-copy engine with direct VDP translation"
}
```

### Step 4: Assembly — `genesistan_bulk_tilemap_commit`

**Dependencies:** Step 2 (C preload functions must exist).

New function in `startup_trampoline.s`:

1. Save all caller-used registers (`movem.l`)
2. Push A0 as argument, JSR `genesistan_bulk_preload_check`
3. Decode A1 → plane base (BG `0xC000` or FG `0xE000`) + starting (row, col):
   - `offset = (A1 & 0x00FFFFFF) - 0x00C00000`
   - If offset ≥ 0x8000: FG plane, subtract 0x8000
   - `cell = offset / 4`
   - `col_start = cell >> 6` (column-major)
   - `row_start = cell & 0x3F`
4. Extract attr_key from D2, load `pc080sn_attr_lut[attr_key]` once
5. Outer loop (D1 iterations = columns):
   - Inner loop (D0 iterations = rows per column):
     - Read tile index from (A0)+
     - Mask to 0x3FFF
     - Load VRAM slot from `pc080sn_tile_vram_lut[tile_index * 2]`
     - OR with attr_partial
     - Compute VDP addr: `plane_base + (row - 4) * 128 + col * 2`
     - Skip if row < 4 or row >= 36 (outside visible 32-row VDP plane)
     - Write VDP control word to `0xC00004`
     - Write tile_attr to `0xC00000`
     - Increment row
   - Increment col, reset row to row_start
6. Restore registers, RTS

**Register plan:**

| Register | Usage |
|----------|-------|
| A0 | Source ROM pointer (auto-increment) |
| A1 | Scratch (original dest discarded after decode) |
| A2 | `pc080sn_tile_vram_lut` base |
| A3 | VDP data port (`0xC00000`) |
| A4 | Scratch |
| A5 | VDP control port (`0xC00004`) |
| D0 | Inner loop counter (saved in D4) |
| D1 | Outer loop counter |
| D2 | attr_partial (pre-computed from original D2) |
| D3 | Scratch: tile index, VDP control word |
| D4 | Saved inner count |
| D5 | Current row |
| D6 | Current col |
| D7 | VDP plane base (0xC000 or 0xE000) |

**Verification:** Title screen renders RASTAN logo. Block-write VDP writes produce correct nametable entries.

### Step 5: Integration Verification

1. Title screen: RASTAN logo + background visible with correct colors
2. Attract mode: Insert coin panel, game over, stage intro screens render
3. Text: All text strings still render correctly (static LUT path)
4. Gameplay: HUD tiles render at stage start
5. Scrolling: Strip builder still works during gameplay
6. End-round: Quadrant fill + animation render
7. Scene transitions: No tile corruption when switching between scenes

---

## 12. Rejected Approaches

### Global Static VRAM Assignment
Rejected. 2272 unique tiles, 1164 slots. Overflows by 1108. Proven impossible in validation gate.

### Generic C-Window Shadow Emulation
Rejected. Would require 32KB+ shadow RAM, dirty-scan every frame, and intercept ALL C-window writes. This is emulation, not translation.

### Broad Memory Mirroring
Rejected. Null-sinking C-window writes was a deliberate stability measure. Reversing it to capture block writes would reintroduce VDP corruption risk from non-block-write C-window accesses.

### Old C Tilemap Rendering Loops
Rejected. `VDP_setTileMapXY()` per cell is too slow. The architecture uses assembly-owned VDP port writes for all hot paths.

### Title-Screen-Only Hack
Rejected. 17 call sites across attract, gameplay, and end-round. A single hook at `0x5A4DE` covers all of them.

### Hand-Managed Ad Hoc Slot Picking in C
Rejected. VRAM slot assignment is a build-time constraint satisfaction problem. Python solves it once; ROM tables encode the result. No runtime slot allocation logic.

### Retaining `tile_cache_get()` Alongside Static LUT
Rejected. The LRU cache and static LUT both write to the same VRAM slot range. LRU eviction could overwrite a statically-assigned tile's graphics, causing visual corruption. Eliminating the LRU cache removes this conflict entirely. Text glyphs are small enough (~42 tiles) to include in the static assignment.

### Per-Scene LUT Switching
Rejected. Would require 3 × 32KB = 96KB of ROM for three LUTs, or runtime LUT patching. The single global LUT with cross-scene slot reuse uses 32KB total and requires no runtime LUT changes.

---

## 13. Final Recommended Architecture

```
BUILD TIME (Python):
  precompute_pc080sn_tile_lut.py
    ├── scan strip builder descriptor tables (existing)
    ├── scan block-write source tables (new)
    ├── scan text glyph tile tables (new)
    ├── scene-aware slot assignment with cross-scene reuse (new)
    ├── output: pc080sn_tile_vram_lut.bin (global, 32KB)
    ├── output: pc080sn_attr_lut.bin (unchanged, 64B)
    ├── output: pc080sn_scene_preload_title.bin (new)
    ├── output: pc080sn_scene_preload_gameplay.bin (new)
    ├── output: pc080sn_scene_preload_endround.bin (new)
    └── output: pc080sn_source_scene_map.bin (new)

RUNTIME:
  ┌─────────────────────────────────────────────────┐
  │  0x5A4DE → JMP genesistan_bulk_tilemap_commit   │
  │            (assembly, startup_trampoline.s)      │
  │                                                  │
  │  1. JSR genesistan_bulk_preload_check (C)        │
  │     → scene lookup from A0 source address        │
  │     → if scene changed: preload tiles from ROM   │
  │                                                  │
  │  2. Decode A1 → plane + (row, col)               │
  │  3. D2 → pc080sn_attr_lut[key] → attr_partial    │
  │  4. Column-major loop:                           │
  │       tile = (A0)+ & 0x3FFF                      │
  │       slot = pc080sn_tile_vram_lut[tile]          │
  │       tile_attr = attr_partial | slot             │
  │       → VDP control port (0xC00004)               │
  │       → VDP data port (0xC00000)                  │
  │  5. RTS                                          │
  └─────────────────────────────────────────────────┘

COEXISTENCE:
  Block writer:  0x5A4DE → genesistan_bulk_tilemap_commit (NEW)
  Strip builder: 0x55968 → genesistan_hook_tilemap_plane_a (EXISTING)
                 0x55990 → genesistan_hook_tilemap_plane_b (EXISTING)
  Text writer:   0x3BB48 → genesistan_hook_text_writer_3bb48 (EXISTING, modified to use static LUT)
  Palette:       0x59AD4 → genesistan_palette_clcs (EXISTING)
  Scroll:        genesistan_scroll_from_workram_vdp (EXISTING)
  Sprites:       genesistan_sprite_tile_prepare + commit_asm (EXISTING)

One new hook. One new assembly function. Two new C functions. Python extension.
Zero new buffers. Zero C-window emulation. Zero LRU cache.
Complete coverage of all bulk tilemap writes across attract, gameplay, and end-round.
```
