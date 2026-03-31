# Direct PC080SN Bulk Tilemap Translation Design

## 1. Executive Summary

The Genesis Rastan translation has TWO distinct PC080SN write patterns:

1. **Strip builder** (scrolling updates): One column/row per call, handled by existing hooks at `0x55968`/`0x55990` → `genesistan_asm_tilemap_commit_bg/fg`. Working.

2. **Block writer** (scene setup): Rectangular tile grids written via `0x5A4DE`, used for title screen, attract mode screens, gameplay scene transitions. Currently null-sunk. **This is the missing subsystem.**

Both patterns share the same tile format (attr_word + tile_index), the same Python-generated LUTs (`pc080sn_tile_vram_lut`, `pc080sn_attr_lut`), and the same VDP plane targets (BG_B at `0xC000`, BG_A at `0xE000`). The block writer is not a new graphics system — it is a second entry point into the same translation pipeline.

**Design:** Replace the core block-copy routine `0x5A4DE` with a genesis handler that reads the same register parameters (D0=width, D1=height, D2=attr, A0=source, A1=dest) and translates each cell directly to VDP nametable writes. One hook covers all 12+ callers — title screen, attract screens, and gameplay block loads.

This is **intent translation at the copy-engine level**, not C-window emulation. No shadow buffer. No memory mirroring.

---

## 2. Proven Arcade Producer Paths

### 2a. Core Engine: `0x5A4DE` — 2D Block Copy

All bulk tilemap writes funnel through this single routine.

**Register contract:**
| Register | Content |
|----------|---------|
| D0.w | Width: tiles per column-segment (inner loop count) |
| D1.w | Height: number of columns (outer loop count) |
| D2.w | Attr word: written to every cell (palette in bits 0–1, priority/flip in bits 13–15) |
| A0 | Source: ROM pointer to tile index words |
| A1 | Destination: C-window base address (determines plane + starting position) |

**Algorithm (arcade):**
```
For each column (D1 iterations):
    For each row within column (D0 iterations):
        Write D2 (attr) to C-window
        Write next source word (tile index) to C-window
    Advance dest by 256 bytes (= 1 C-window column)
```

**Column pitch:** 256 bytes = 64 cells × 4 bytes/cell = one C-window column. This confirms column-major traversal matching the PC080SN memory layout.

### 2b. Complete Caller Catalog

| Caller | Dimensions | Dest C-window | Source ROM | Attr (D2) | Context | Frequency |
|--------|-----------|---------------|------------|-----------|---------|-----------|
| `0x5A38E` | 28×20 | `0xC00328` | `0x5B0B2` | 0x0001 | Title screen logo + background | One-shot |
| `0x5A370` | 28×21 | `0xC00320` | `0x5A7DA` | 0x0001 | Attract alternate scene | One-shot |
| `0x5A3AC` | 12×10 | `0xC01240` | `0x5AC72` | 0x0001 | Attract overlay panel | One-shot |
| `0x5A3DE` | 12×14 | `0xC00E18` | `0x5AF62` | 0x0001 | Character display / info panel | One-shot + recurring |
| `0x5A410` | 12×14 | `0xC00C3C` | `0x5AF62` | 0x0001 | Status display | One-shot |
| `0x5A442` | 16×16 | `0xC00C38` | `0x5AD62` | 0x0001 | Menu graphics | One-shot |
| `0x5A474` | Variable | Multiple | `0x5A77A+` | Variable | Master attract setup | One-shot |
| `0x56356` | Variable | Variable | Variable | 0x0005 | Gameplay tile animation | Recurring |
| `0x5746x–0x575xx` | Variable | Variable | Variable | 0x0004–0x0006 | Gameplay animation frames | Recurring |

**Key insight:** The title screen is NOT a special case. The same engine powers all scene-setup tilemap loads across attract mode AND gameplay. One hook at `0x5A4DE` covers everything.

### 2c. Palette Companion Path: `0x59AD4`

Each block-write caller is typically preceded by a palette load via `0x59AD4`, which writes converted colors to `0x200000`. This is already correctly redirected to `genesistan_palette_clcs` by the spec patcher. No additional palette work is needed.

---

## 3. Translation Ownership Model

Following the Rainbow Islands and Cadash producer→consumer principle:

### What the Arcade Producer Owns

The arcade code at each caller site owns:
- Which source ROM data table to use
- Which C-window destination (plane + position)
- What attribute to apply
- What dimensions to fill
- When to fire (state machine driven)

The arcade code calls `0x5A4DE` with these parameters in registers. This is the **intent boundary** — the caller expresses "fill this rectangle with these tiles on this plane."

### What the Genesis Translation Layer Owns

The replacement handler at `0x5A4DE` owns:
- Decoding the C-window destination address to VDP plane + (row, col)
- Converting each arcade tile index to a Genesis VRAM tile slot via `pc080sn_tile_vram_lut`
- Converting the attr word to Genesis tile attribute bits via `pc080sn_attr_lut`
- Computing VDP nametable VRAM addresses
- Writing tile+attr pairs to VDP

### What the Final VDP Commit Owner Is

The assembly hot path writes directly to VDP ports (`0xC00004` control, `0xC00000` data). No intermediate buffer. Same pattern as the existing strip builder assembly.

### The Translation Is Symmetric with the Strip Builder

| Property | Strip Builder | Block Writer |
|----------|--------------|-------------|
| Hook point | `0x55968` / `0x55990` (strip entry) | `0x5A4DE` (block copy entry) |
| Data source | Descriptor list in workram | ROM tile index table |
| Attr source | Per-descriptor attr_word | Single attr_word (D2) for entire block |
| Iteration | 16 descriptors × 4 cells = 64 cells per strip | D0 × D1 cells per block |
| Destination decode | dest_ptr → (row, col) via `pc080sn_dest_ptr_to_row_col()` | C-window address → (row, col) via same formula |
| Tile lookup | `pc080sn_tile_vram_lut[arcade_tile]` | Same LUT |
| Attr lookup | `pc080sn_attr_lut[attr_key]` | Same LUT |
| VDP write | Direct port writes in assembly | Same |

---

## 4. Buffer / Output Model

### No Intermediate Buffer

The block writer translates source data directly to VDP nametable writes. There is no staging buffer, no shadow C-window, no command queue.

**Why no buffer:** The block writer fires once per scene transition. It writes a bounded rectangle (max observed: 28×21 = 588 cells = 1176 VDP writes). This completes in well under 1ms at 68000 speeds. There is no need to defer, batch, or stage — direct VDP writes during the scene setup call are sufficient.

**Comparison with Rainbow Islands:** Rainbow Islands' tilemap streaming routines (`0x28D6`, `0x28FA`, `0x291E`, `0x2942`) compute VDP plane destinations and stream directly to VDP data port `0xC00000`. No intermediate buffer. The Rastan block writer follows the same pattern.

### Data Flow

```
ROM tile table (A0)
    ↓ read tile_index word
pc080sn_tile_vram_lut[tile_index & 0x3FFF]
    ↓ VRAM slot
    + pc080sn_attr_lut[attr_key_from_D2]
    ↓ combined tile_attr
VDP control port (set VRAM write address)
VDP data port (write tile_attr)
```

### Format at Each Stage

| Stage | Format |
|-------|--------|
| Source (ROM) | 16-bit arcade tile index per cell |
| Attr (D2 register) | 16-bit arcade attr word (palette bits 0–1, priority bit 13, flip bits 14–15) |
| After LUT lookup | 16-bit Genesis TILE_ATTR: (priority\|palette\|vflip\|hflip\|vram_slot) |
| VDP write | 32-bit control word + 16-bit data word |

---

## 5. Opcode / Hook Strategy

### Recommended: Replace `0x5A4DE` at Routine Entry

**Hook point:** Replace the first 6 bytes of `0x5A4DE` with `JMP genesistan_bulk_tilemap_commit`.

**Why routine entry, not callers:**
- One hook covers 12+ callers (all attract screens + gameplay)
- Callers prepare registers and BSR/JSR to `0x5A4DE` — the register contract is the clean intent boundary
- No caller-specific logic is needed in the handler
- Avoids modifying 12+ call sites with potential shift-budget issues

**Why not inner-loop interception:**
- The inner loop is only 8 instructions. Intercepting within the loop adds overhead per cell with no benefit.
- The entire routine is being replaced, not augmented.

**Why not caller-site interception:**
- Would require 12+ opcode_replace entries instead of one
- Each BSR.W is 4 bytes; replacing with JSR needs 6 bytes — shift budget mismatch at every site
- Callers contain parameter setup logic that must still execute

### Spec Patch Entry

In `startup_title_remap.json`, add to `opcode_replace`:

```json
{
  "address": "0x05A4DE",
  "original": "3800 2449 32c2 32d8 5340",
  "replacement": "jmp genesistan_bulk_tilemap_commit",
  "why": "replace PC080SN block-copy engine with direct VDP translation"
}
```

The replacement JMP (6 bytes) overwrites the first 3 instructions. The remaining bytes of the original routine (through 0x5A500) become dead code — the genesis handler returns via its own RTS.

### Handler Register Contract

The handler receives exactly what the arcade routine would:

```
Entry:  D0.w = tile count per column (width)
        D1.w = column count (height)
        D2.w = attr word
        A0   = ROM source pointer (tile indices)
        A1   = C-window destination address
Exit:   RTS (no return value needed — callers don't use one)
```

---

## 6. Tile / Attr / VRAM Flow

### Tile Graphics Availability

**Problem:** The existing Python precompute (`precompute_pc080sn_tile_lut.py`) scans strip builder descriptor tables to discover which tile indices need VRAM slots. The block writer uses DIFFERENT tile indices from ROM data tables (e.g., `0x5B0B2` for the title screen). These tiles may not have VRAM slots assigned.

**Solution — extend Python precompute:**

Add a new scan pass to `precompute_pc080sn_tile_lut.py` that:
1. Reads the block-write source data tables from the arcade ROM
2. Collects all unique tile indices from these tables
3. Merges them into the VRAM slot assignment with the strip builder tiles
4. Outputs updated `pc080sn_tile_vram_lut.bin` and `pc080sn_vram_preload.bin`

**Known block-write source tables to scan:**

| ROM Address | Used By | Approx Tile Count |
|-------------|---------|-------------------|
| `0x5B0B2` | Title screen (28×20) | ~560 |
| `0x5A7DA` | Attract grid (28×21) | ~588 |
| `0x5AC72` | Attract overlay (12×10) | ~120 |
| `0x5AF62` | Info panel (12×14) | ~168 |
| `0x5AD62` | Menu graphics (16×16) | ~256 |

Many tiles will be duplicates (e.g., background fill tile `0x00AD`). Unique count across all tables is likely modest (estimated 200–400 additional unique tiles).

**VRAM slot budget:** The current LUT assigns slots starting at TILE_USER_INDEX (20). With 1004 slots in range A (20–1023) and 160 in range B (1280–1439), there is ample room for 200–400 additional tiles.

### Preload Strategy

The existing `genesistan_preload_pc080sn_title_frontend()` iterates `pc080sn_vram_preload` pairs and DMA-loads tile graphics at scene start. With the Python tool extended to include block-write tiles, this preload automatically covers the new tiles. No new preload code is needed.

### Attr Conversion

The attr word (D2) uses the same format as strip builder descriptors:
- Bits 0–1: palette
- Bit 13: priority
- Bit 14: hflip
- Bit 15: vflip

Extract the 5-bit attr_key: `(prio << 4) | (vflip << 3) | (hflip << 2) | pal`. Look up `pc080sn_attr_lut[attr_key]`. OR with VRAM tile slot. This is identical to the strip builder's attr handling.

### BG vs FG Plane Determination

The C-window destination address determines the plane:
- `0xC00000`–`0xC07FFF` → BG → VDP plane base `0xC000`
- `0xC08000`–`0xC0FFFF` → FG → VDP plane base `0xE000`

The starting (row, col) is derived from the C-window offset using the same column-major formula as `pc080sn_dest_ptr_to_row_col()`:
```
offset = (A1 & 0x00FFFFFF) - cwindow_base
cell = offset / 4
col_start = cell / 64       (column-major: cell >> 6)
row_start = cell % 64       (column-major: cell & 0x3F)
```

### VDP Address Computation

For each cell at position (row, col) in the VDP plane:
```
vdp_addr = plane_base + (row - visible_bias) * 128 + col * 2
```
Where `visible_bias = 4` (rows 0–3 are off-screen in the 64-row C-window).

Rows < 4 are skipped (invisible top margin). Row wraps at 32 (VDP plane height for 64×32 configuration).

---

## 7. Assembly vs C vs Python Ownership

### Python (Build-Time)

**Extend `precompute_pc080sn_tile_lut.py`:**
- Add scan pass for block-write ROM data tables
- Input: arcade ROM + table of known block-write source addresses and dimensions
- Output: merged `pc080sn_tile_vram_lut.bin` and `pc080sn_vram_preload.bin`
- This is static analysis — runs once at build time, produces ROM-resident LUTs

### Assembly (Runtime Hot Path)

**New function: `genesistan_bulk_tilemap_commit`** in `startup_trampoline.s`

This is the replacement for `0x5A4DE`. It must:
1. Decode A1 to determine plane (BG/FG) and starting (row, col)
2. Extract 5-bit attr_key from D2, load `pc080sn_attr_lut[attr_key]` once (constant for entire block)
3. Outer loop (D1 iterations = columns):
   - Inner loop (D0 iterations = rows per column):
     - Read tile index from (A0)+
     - Mask to 0x3FFF
     - Load VRAM slot from `pc080sn_tile_vram_lut[tile_index]`
     - OR with attr_partial
     - If row ≥ visible_bias: compute VDP address, write control+data to VDP ports
     - Advance row (wrap at 32)
   - Advance col by 1, reset row to starting row
4. RTS

**Register plan:**
| Register | Usage |
|----------|-------|
| A0 | Source ROM pointer (tile indices), auto-increment |
| A1 | Not used after initial decode (original dest discarded) |
| A2 | `pc080sn_tile_vram_lut` base |
| A3 | VDP data port (`0xC00000`) |
| A4 | Not used / scratch |
| A5 | VDP control port (`0xC00004`) |
| D0 | Inner loop counter (saved in D4) |
| D1 | Outer loop counter |
| D2 | attr_partial (pre-computed from original D2 via attr_lut) |
| D3 | Scratch: tile index, VDP addr |
| D4 | Saved inner count |
| D5 | Current row |
| D6 | Current col |
| D7 | VDP plane base (0xC000 or 0xE000) |

**Justification for assembly:** This is a direct VDP write path — same class as the existing strip commit assembly. The inner loop is 8–10 instructions per cell with VDP port writes. C function call overhead per cell would be unacceptable. SGDK helpers add unnecessary abstraction. Assembly is the correct owner.

### C (Thin Glue Only)

**No new C functions required.** The assembly handler is self-contained. It reads LUTs from ROM, registers from caller, and writes to VDP. If needed, a C wrapper could be added for the initial A1 decode (plane/row/col), but this is simple enough for inline assembly (subtract base, shift, mask).

---

## 8. Relationship to Scrolling

### How Bulk Write Enables Meaningful Scroll

Currently, scrolling is wired (`sync_arcade_scroll_to_vdp()` called per V-Int since Build 300) but meaningless because the VDP planes are empty — no tilemap data to scroll over.

With the bulk write path operational:
1. **Scene setup** (one-shot): `0x5A4DE` handler fills VDP plane with initial tilemap (title screen, level start, etc.)
2. **Scroll sync** (per-frame): `sync_arcade_scroll_to_vdp()` reads arcade workram scroll offsets and applies to VDP — now the camera moves over real content
3. **Strip updates** (per-frame): As scroll advances, the strip builder hooks fire to fill in new columns/rows at the edges — now there IS content at the center and new strips extend the visible area

**The bulk write is the FOUNDATION that makes scroll and strip updates visible.**

### Scroll Ownership After This Subsystem

No change to scroll ownership. `genesistan_scroll_from_workram_vdp()` remains the final-form scroll handler (architecture frozen per `pc080sn_tilemap_architecture.md`). The bulk write does not interact with scroll registers — it only populates the VDP nametable. Scroll reads from workram are independent.

### Timeline

| Phase | What Happens |
|-------|-------------|
| Before bulk write | VDP planes empty. Scroll applies to nothing. Strips write to empty plane edges. |
| After bulk write | VDP planes initialized with scene tilemap. Scroll pans over real content. Strips extend visible edges correctly. |
| During gameplay | Bulk write fires on scene transitions (level start, attract state changes). Strip builder fires continuously for scrolling. Both write to the same VDP planes at different times. |

---

## 9. Compatibility with Existing Systems

### Strip Builder Hooks (0x55968 / 0x55990)

**No conflict.** The strip builder and block writer operate at different times:
- Block writer: fires during scene setup (state machine transitions)
- Strip builder: fires during per-frame scroll updates

Both write to the same VDP planes (BG_B, BG_A). The block writer initializes the plane; the strip builder incrementally updates it. No overlap in write timing.

**Shared resources:** Both use `pc080sn_tile_vram_lut` and `pc080sn_attr_lut` (ROM, read-only). Both write to VDP ports (serialized by 68000 instruction order). No contention.

### Text Writer Hooks (0x3BB48 / 0x3C3FE)

**No conflict.** Text writes to BG_A (FG plane) via `rastan_draw_tile_xy()`. Block writes may also target BG_A when dest is in FG C-window range (`0xC08000+`). The arcade state machine ensures text writes occur AFTER scene setup, so text overwrites the correct cells on top of the tilemap base. This is the intended layering — same as on arcade.

### Palette Path

**No conflict.** Palette conversion (`0x59AD4` → `genesistan_palette_clcs`) is already working. The block writer does not touch palette data. `load_arcade_palette()` reads from CLCS and applies to VDP CRAM independently.

### Sprite Path

**No conflict.** Sprite rendering reads from workram Block-A/B, writes to VDP SAT. Block writer reads from ROM, writes to VDP nametable planes. Different data sources, different VDP targets.

---

## 10. Rejected Approaches

### Full C-Window Shadow Emulation

Rejected. Would require 32KB+ of shadow RAM (two 64×64 planes × 4 bytes/cell). Would require intercepting ALL C-window writes system-wide. Would require a per-frame dirty-scan to find changed cells and commit them. This is emulation, not translation. It adds O(N) overhead every frame for data that changes only on scene transitions.

### Broad Memory Mirroring

Rejected. The spec patcher already null-sinks C-window writes for stability. Reversing this to mirror into shadow RAM would reintroduce the VDP corruption risk that the null-sink was designed to prevent. It would also capture writes that are irrelevant (C-window clears, intermediate state) alongside the writes that matter.

### Reviving Old C Renderer

Rejected. The old C tilemap rendering loops (`VDP_setTileMapXY()` per cell from C) were explicitly removed. They are too slow for per-frame strip updates and add C function call overhead per tile. The architecture direction is assembly-owned hot paths with C as thin glue only.

### SGDK Tilemap Loops as Long-Term Owner

Rejected. SGDK's `VDP_setTileMapXY()` is a convenience function that sets up VDP control words per call. For 560 tiles, this means 560 C function calls, each computing a VDP address. The assembly hot path inlines the computation and streams directly to VDP ports — 5–10× faster for bulk operations.

### Title-Screen-Only One-Off Hack

Rejected. The audit identified 12+ callers of `0x5A4DE` across attract mode AND gameplay. A title-screen-only solution would leave gameplay block loads broken. The correct design hooks the core engine (`0x5A4DE`) and covers all callers automatically.

### Intercepting Individual Callers

Rejected. Would require 12+ separate opcode patches, each with potential shift-budget conflicts (BSR.W is 4 bytes, JSR is 6 bytes). Each caller would need its own parameter extraction logic. The single hook at `0x5A4DE` receives the parameters already prepared in registers — cleaner, safer, complete.

---

## 11. Final Recommended Architecture

### Implementation Steps (Ordered)

**Step 1 — Python: Extend tile LUT to cover block-write tiles**

Modify `precompute_pc080sn_tile_lut.py`:
- Add known block-write source table addresses and dimensions as a scan list
- Walk each table, collect unique tile indices
- Merge into existing VRAM slot assignment
- Regenerate `pc080sn_tile_vram_lut.bin` and `pc080sn_vram_preload.bin`

**Step 2 — Spec: Add opcode_replace for `0x5A4DE`**

Add entry to `startup_title_remap.json` replacing `0x5A4DE` with JMP to `genesistan_bulk_tilemap_commit`.

**Step 3 — Assembly: Implement `genesistan_bulk_tilemap_commit`**

New function in `startup_trampoline.s`:
- Decode A1 → plane base + starting (row, col)
- Pre-compute attr_partial from D2 via `pc080sn_attr_lut`
- Column-major nested loop: read tile index, LUT lookup, compute VDP addr, write
- RTS

**Step 4 — Verify: Title screen renders**

With steps 1–3 complete:
- Title screen background + RASTAN logo tiles appear in VDP nametable
- Tile graphics present in VRAM (preloaded by existing `genesistan_preload_pc080sn_title_frontend()`)
- Correct palette applied (already captured via `0x59AD4` → CLCS → `load_arcade_palette()`)
- Scroll at (0,0) shows centered title screen

### Architecture Diagram

```
ARCADE PRODUCERS (unchanged):
  0x5A38E ──┐
  0x5A370 ──┤
  0x5A3AC ──┤  all call 0x5A4DE with D0/D1/D2/A0/A1
  0x5A3DE ──┤
  0x5A442 ──┤
  0x5746x ──┤
  0x5752x ──┘
            │
            ▼
  ┌─────────────────────────────────────────┐
  │  0x5A4DE → JMP genesistan_bulk_tilemap  │  ← spec patch
  │           _commit (assembly)            │
  └─────────────────────────────────────────┘
            │
            ├── A1 decode → BG (0xC000) or FG (0xE000)
            ├── D2 → pc080sn_attr_lut[key] → attr_partial
            │
            ▼
  ┌─────────────────────────────────────────┐
  │  Column-major nested loop:              │
  │    tile = (A0)+ & 0x3FFF               │
  │    vram_slot = tile_vram_lut[tile]      │
  │    tile_attr = attr_partial | vram_slot │
  │    vdp_addr = base + row*128 + col*2   │
  │    → VDP control port (0xC00004)        │
  │    → VDP data port (0xC00000)           │
  └─────────────────────────────────────────┘
            │
            ▼
  VDP Nametable (BG_B or BG_A)
            │
            ▼
  Screen output (with scroll + palette already working)
```

### Coexistence Summary

```
SCENE SETUP:     0x5A4DE → genesistan_bulk_tilemap_commit (NEW)
SCROLLING:       0x55968 → genesistan_hook_tilemap_plane_a (EXISTING)
                 0x55990 → genesistan_hook_tilemap_plane_b (EXISTING)
TEXT:            0x3BB48 → genesistan_hook_text_writer_3bb48 (EXISTING)
PALETTE:         0x59AD4 → genesistan_palette_clcs (EXISTING)
SCROLL REGS:    genesistan_scroll_from_workram_vdp (EXISTING)
SPRITES:         genesistan_sprite_tile_prepare + commit_asm (EXISTING)
```

One new hook. One new assembly function. One Python extension. Zero new buffers. Zero new C rendering. Complete coverage of all bulk tilemap writes across attract mode and gameplay.
