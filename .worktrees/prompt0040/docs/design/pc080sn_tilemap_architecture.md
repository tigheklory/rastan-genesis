# PC080SN Tilemap Translation Architecture

## Mandatory Reference Baseline

**MAME PC080SN** (`src/mame/taito/pc080sn.cpp`):
- Two tilemap planes. Each plane: 64×64 tile RAM. Each entry: 2 words (attr word + tile index word).
- Arcade CPU writes into chip-mapped C-window: plane 0 (BG) at `0xC00000`, plane 1 (FG) at `0xC08000`.
- Entry layout: `word0 = attr` (prio=bit13, vflip=bit15, hflip=bit14, palette=bits1:0), `word1 = tile index` (14-bit, `& 0x3FFF`).
- PC080SN hardware renders continuously from its tile RAM. The 68000 writes incrementally, not in full-plane bursts.
- Rastan MAME instance: scroll registers at `0xC20000/0xC40000`. `screen_update` calls `m_pc080sn->tilemap_update()` then `tilemap_draw()` for each layer in Z-order.

**Rainbow Islands** (primary Genesis translation analog):
- Arcade intent: direct writes to PC080SN C-window cells → Genesis: compute VDP destination, stream converted words.
- Pattern confirmed: arcade scroll/control writes → VDP register writes via helper (not staged in WRAM).
- Producer→consumer validation rule applies: every arcade tile write must reach an active VDP plane owner.

**Cadash** (secondary analog):
- Tile/plane intent → VDP plane stream write. Scroll/control intent → VDP register write.
- Intent-to-owner mapping is the architecture. Not per-screen callsite patches.

---

## 1. Full Pipeline (End-to-End)

```
Arcade 68000 executes PC080SN C-window strip builder
  at 0x055968 (BG strips) / 0x055990 (FG strips)
    ↓
spec patch: JSR genesistan_hook_tilemap_plane_bg / genesistan_hook_tilemap_plane_fg
    ↓
C thin dispatcher:
  reads strip_index  from genesistan_arcade_workram_words[0x10CA/2]
  reads dest_ptr     from genesistan_arcade_workram_words[0x10A0/2] (BG) or [0x10A4/2] (FG)
  derives dest_row, dest_col from dest_ptr via addr formula
  calls assembly entry: genesistan_asm_tilemap_commit_bg / _fg(desc_list, strip_index, dest_row, dest_col)
    ↓
Assembly: genesistan_asm_tilemap_commit_bg / _fg
  outer loop (16 descriptors from A5+0x1000..0x103C):
    load desc_addr (u32 BE) from workram
    load attr_word (u16) from rastan_maincpu[desc_addr]
    load table_base (u16) from rastan_maincpu[desc_addr+2]
    extract attr_key (5 bits: prio, vflip, hflip, pal)
    attr_partial = pc080sn_attr_lut[attr_key]          ← ROM, Python-generated, 32-entry u16 table
    inner loop (4 strip cells):
      tile_addr = table_base + strip_offset(strip_index, cell)  ← plane-specific formula
      tile_word = rastan_maincpu[tile_addr]
      arcade_tile = tile_word & 0x3FFF
      vram_slot = pc080sn_tile_vram_lut[arcade_tile]    ← ROM, Python-generated, 16384-entry u16 table
      tile_attr = attr_partial | vram_slot
      vdp_vram_addr = plane_vram_base + dest_row*128 + dest_col*2
      write 0xC00004 ← VDP control word (VRAM write command)
      write 0xC00000 ← tile_attr
      advance dest_row (BG) or dest_col (FG) by strip stride
  write updated dest_ptr back to genesistan_arcade_workram_words[0x10A0/2] or [0x10A4/2]
    ↓
VDP plane written: BG_B (VRAM 0xC000) for BG / BG_A (VRAM 0xE000) for FG
```

Scroll path (separate, already implemented, architecture freezes it as final form):

```
Arcade writes to 0xC20000 / 0xC40000 (PC080SN scroll)
  → spec patches at 0x055AB4/BC/C4/CC and 0x03ABBA/C0 and boot callsites 0x00016A/0x000170
  → JSR genesistan_scroll_from_workram_vdp
      reads A5+0x10EC → BG X  → VDP_setHorizontalScroll(BG_B, -x)
      reads A5+0x10EE → BG Y  → VDP_setVerticalScroll(BG_B, -y + 8)
      reads A5+0x10AE → FG X  → VDP_setHorizontalScroll(BG_A, -x)
      reads A5+0x10B0 → FG Y  → VDP_setVerticalScroll(BG_A, -y + 8)
```

---

## 2. Python Responsibilities

### 2a. PC080SN Tile VRAM LUT

**Script**: `tools/translation/precompute_pc080sn_tile_lut.py`

**Input**:
- `build/regions/pc080sn.bin` — 524288 bytes (16384 tiles × 32 bytes each, already in Genesis format)
- `rastan_maincpu` (embedded ROM): all tile strip tables reachable from descriptor chains

**Algorithm**:
1. Walk all tile strip tables accessible from the descriptor list at A5+0x1000 across all arcade game states encoded in the ROM (this is a static ROM scan, not a runtime trace).
2. Collect the set of unique 14-bit tile codes that ever appear in any strip table entry.
3. Assign each unique tile code a VRAM slot sequentially, starting at TILE_USER_INDEX (20). Tile code 0x0000 (transparent/empty) is assigned slot 0 (Genesis blank tile).
4. Build a flat 16384-entry u16 array: `lut[arcade_tile] = assigned_vram_slot` (0 for never-used tile codes).
5. Build a VRAM preload list: sorted list of (arcade_tile, vram_slot) pairs for tiles with nonzero assignments.

**Output**:
- `build/pc080sn_tile_vram_lut.bin` — 16384 × 2 = 32768 bytes, ROM-resident as `.rodata_bin`
- `build/pc080sn_vram_preload.bin` — N × 4 bytes (u16 arcade_tile, u16 vram_slot) pairs, followed by sentinel 0xFFFF. N ≤ unique tile count.
- `build/pc080sn_unique_tile_count.txt` — scalar, for VRAM region sizing validation

**Guarantee**: Every arcade tile code that appears at runtime in a strip table entry has a nonzero assigned VRAM slot. Tile lookup in the assembly hot path is always O(1), no DMA at hit time.

---

### 2b. PC080SN Attribute LUT

**Script**: `tools/translation/precompute_pc080sn_attr_lut.py`

**Input**: None (pure bit logic from MAME PC080SN attr format and SGDK TILE_ATTR_FULL definition).

**Algorithm**:
For each 5-bit key `k` in `0..31`:
```
pal      = k & 0x03
hflip    = (k >> 2) & 0x01
vflip    = (k >> 3) & 0x01
prio     = (k >> 4) & 0x01
lut[k]   = (prio << 15) | (pal << 13) | (vflip << 12) | (hflip << 11)
```

Key extraction from arcade attr_word:
```
pal   = attr_word & 0x03
hflip = (attr_word >> 14) & 0x01
vflip = (attr_word >> 15) & 0x01
prio  = (attr_word >> 13) & 0x01
k     = (prio << 4) | (vflip << 3) | (hflip << 2) | pal
```

**Output**: `build/pc080sn_attr_lut.bin` — 32 × 2 = 64 bytes, ROM-resident. Contains the upper 5 bits of the Genesis `TILE_ATTR_FULL` word, ready to OR with the VRAM tile index.

---

## 3. Runtime Responsibilities

### C Layer (thin only)

`genesistan_hook_tilemap_plane_bg()`:
- Reads `strip_index` from `genesistan_arcade_workram_words[0x10CA/2]`.
- Reads `dest_ptr` from `genesistan_arcade_workram_words[0x10A0/2]`.
- Converts `dest_ptr` to `(dest_row, dest_col)` using the C-window address formula.
- Invokes `genesistan_asm_tilemap_commit_bg(desc_list, strip_index, dest_row, dest_col)`.
- Writes updated `dest_ptr` back to `genesistan_arcade_workram_words[0x10A0/2]` (assembly returns updated value).

`genesistan_hook_tilemap_plane_fg()`:
- Same as above, using `dest_ptr` from `[0x10A4/2]`, invoking `_fg` assembly entry.
- Reads `mode` from `[0x10A8/2]` and `strip_raw` from `[0x10CA/2]` to compute the FG strip_index formula:
  - `strip_index = (mode == 2) ? (strip_raw & 0x3) : (~strip_raw & 0x3)`.
  - Passes computed `strip_index` (not strip_raw) to assembly.
- Sets `genesistan_arcade_workram_words[0x1330/2] = 1` (flag required by arcade state machine).

C MUST NOT:
- Iterate the descriptor list.
- Compute attr bits or tile attributes.
- Call `tile_cache_get()` or any VDP function.
- Read from `rastan_maincpu` for tile or attr data.

`genesistan_hook_tilemap_plane_bg/fg()` plus the C-layer VRAM preload init are the only C tilemap functions.

`genesistan_scroll_from_workram_vdp()`: Final form as-is. Reads four scroll words from arcade WRAM, writes four VDP scroll registers. No changes.

C VRAM preload init (scene-start only):
- Iterates `pc080sn_vram_preload.bin` pair list.
- For each (arcade_tile, vram_slot): `VDP_loadTileData(rastan_pc080sn + arcade_tile*32, vram_slot, 1, DMA)`.
- Runs once at game start and at each scene transition detected via arcade state machine.
- Does NOT run at vblank.

---

### Assembly Layer

**`genesistan_asm_tilemap_commit_bg`** and **`genesistan_asm_tilemap_commit_fg`** in `startup_trampoline.s`.

Inputs (via registers from C dispatcher):
- A0: pointer to descriptor list in arcade WRAM (16 × 4-byte BE u32 addresses)
- A1: pointer to `rastan_maincpu` ROM base
- A2: pointer to `pc080sn_tile_vram_lut` (ROM, 16384 × u16)
- A3: pointer to `pc080sn_attr_lut` (ROM, 32 × u16)
- D0: strip_index
- D1: dest_row (BG) or dest_col (FG)
- D2: desc_count = 16

Outputs:
- D7: updated dest value (C dispatcher writes to workram)

Plane VRAM bases:
- `genesistan_asm_tilemap_commit_bg`: plane_vram_base = 0xC000 (BG_B)
- `genesistan_asm_tilemap_commit_fg`: plane_vram_base = 0xE000 (BG_A)

Loops:
1. **Outer loop** (16 iterations, desc_count in D2):
   - Load desc_addr (4 bytes, big-endian) from (A0)+.
   - Bounds-check desc_addr against ROM size; skip if invalid.
   - Load attr_word from `rastan_maincpu[desc_addr]` (word).
   - Load table_base from `rastan_maincpu[desc_addr+2]` (word).
   - Extract 5-bit attr_key from attr_word (inline bit ops, no branch table).
   - Load attr_partial from `pc080sn_attr_lut[attr_key*2]` (word).
2. **Inner loop** (4 iterations, cell = 0..3):
   - BG strip tile address: `rastan_maincpu + table_base + (strip_index << 1) + (cell << 3)`
   - FG strip tile address: `rastan_maincpu + table_base + (strip_index << 3) + (cell << 1)`
   - Load tile_word (word). Mask `& 0x3FFF` → arcade_tile.
   - Load vram_slot from `pc080sn_tile_vram_lut[arcade_tile*2]` (word).
   - `tile_attr = attr_partial | vram_slot`
   - BG VRAM addr = 0xC000 + dest_row*128 + dest_col*2; dest_col fixed per desc, dest_row advances.
   - FG VRAM addr = 0xE000 + dest_row*128 + dest_col*2; dest_row fixed per desc, dest_col advances.
   - VDP control word: `0x40000003 | ((vdp_addr & 0x3FFF) << 16) | (vdp_addr >> 14)`
   - Write control word to `0xC00004`.
   - Write tile_attr to `0xC00000`.
3. After inner loop: advance dest_row (BG) or dest_col (FG) by strip stride to next descriptor position.
4. After outer loop: return updated dest value in D7. No SGDK function calls anywhere.

---

## 4. Tilemap Update Strategy

**Strip-tracking (mirror arcade cadence)**.

Rastan's 68000 updates PC080SN tile RAM incrementally. Each call to the builder at 0x055968/0x055990 writes exactly one strip (4 rows for BG or 4 columns for FG) for each of the 16 active descriptors. The strip_index cycles across calls, progressively refreshing the full visible plane. The hook intercepts each builder call and produces the equivalent VDP writes for exactly that strip — no more, no less.

This is chosen because:
- The arcade hardware renders from its tile RAM continuously. The CPU updates only what it needs to change. Mirroring that cadence produces the correct incremental plane state.
- Full redraw (all 64×28 cells per plane per vblank) requires 7168 VDP writes per frame. At ~2µs per write: 14ms, exceeding the 16.7ms vblank window when combined with sprite and palette work.
- Dirty tracking (shadow comparison) adds O(N) comparison overhead and an additional 8KB WRAM shadow per plane.
- Strip-tracking has zero additional overhead: the arcade code already computes exactly which cells to update.

No dirty cache. No full redraw. No shadow WRAM per plane. The strip-tracking approach eliminates all three.

---

## 5. Scroll System

**Source**: Arcade WRAM at A5 offsets, written by the arcade 68000 before the PC080SN scroll write callsites.

| Arcade WRAM offset | Plane | Axis | VDP target |
|--------------------|-------|------|------------|
| A5+0x10EC          | BG    | X    | `VDP_setHorizontalScroll(BG_B, -value)` |
| A5+0x10EE          | BG    | Y    | `VDP_setVerticalScroll(BG_B, -value + 8)` |
| A5+0x10AE          | FG    | X    | `VDP_setHorizontalScroll(BG_A, -value)` |
| A5+0x10B0          | FG    | Y    | `VDP_setVerticalScroll(BG_A, -value + 8)` |

**Vertical bias +8**: Arcade visible height = 240px; Genesis visible height = 224px. Bias of +8 centers the 224px Genesis window within the 240px arcade crop.

**Application timing**: Applied at every intercepted PC080SN scroll write callsite (0x055AB4, 0x055ABC, 0x055AC4, 0x055ACC) and at boot scroll setup callsites (0x00016A, 0x000170, 0x03ABBA, 0x03ABC0, 0x03B098, 0x03B09E). These are already spec-patched via `genesistan_scroll_from_workram_vdp`.

**Per-line scroll**: Not required. Rastan uses full-plane scroll only (both BG and FG scroll their entire plane uniformly). Per-scanline H-scroll mode is not used.

**Scroll is final form as of Build 291**. Architecture freezes `genesistan_scroll_from_workram_vdp()` as-is. No changes to the scroll system in this phase.

---

## 6. Data Structures

### ROM-resident (Python-generated, `.rodata_bin`)

**`pc080sn_tile_vram_lut[16384]` — u16, 32768 bytes**
- Index: 14-bit arcade tile code (0x0000–0x3FFF)
- Value: assigned Genesis VRAM tile slot number. 0 = unmapped (arcade tile code never appears in any tilemap).
- Tile code 0x0000 maps to slot 0 (Genesis default blank tile).
- All other tile codes that appear in any strip table entry have nonzero assigned slots.
- This replaces `genesistan_tile_cache_arcade[]` + `genesistan_tile_cache_lru[]` + `genesistan_tile_cache_clock` for tilemap tile lookup. Those three arrays are eliminated.

**`pc080sn_attr_lut[32]` — u16, 64 bytes**
- Index: 5-bit attr_key = (prio << 4) | (vflip << 3) | (hflip << 2) | pal
- Value: upper Genesis TILE_ATTR word = (prio << 15) | (pal << 13) | (vflip << 12) | (hflip << 11)
- Assembly ORs this with vram_slot to produce the full TILE_ATTR word.

**`pc080sn_vram_preload.bin` — (u16, u16) pairs + sentinel**
- Preload manifest: sorted list of (arcade_tile, vram_slot) for all unique tile codes.
- C init walker uses this to DMA-load all PC080SN tiles into VRAM at scene start.
- Size: N_unique × 4 bytes + 2-byte sentinel (0xFFFF). N_unique ≤ 16384 (in practice ≤ ~4000).

### WRAM (live arcade state, read-only by tilemap system)

**`genesistan_arcade_workram_words`** — existing, no new fields:
- `[0x1000/2..0x103C/2]`: 16 descriptor address pointers (u32 BE, packed as two u16 words)
- `[0x10A0/2]`: dest_ptr for BG strip (u32 BE)
- `[0x10A4/2]`: dest_ptr for FG strip (u32 BE)
- `[0x10A8/2]`: mode (affects FG strip_index computation)
- `[0x10CA/2]`: strip_index raw value
- `[0x1330/2]`: flag set by FG hook (arcade state machine dependency)

### No new WRAM buffers

No tilemap shadow WRAM. No dirty bitfield. No staging buffer. Strip-tracking requires none of these. The only WRAM writes by the tilemap system are the updated dest_ptr values written back after each commit.

### Eliminated

- `genesistan_tile_cache_arcade[1164]` — replaced by `pc080sn_tile_vram_lut` (O(1) vs O(N) scan).
- `genesistan_tile_cache_lru[1164]` — no LRU eviction needed; slots are statically assigned by Python.
- `genesistan_tile_cache_clock` — eliminated with the above.
- `tile_cache_get()` — eliminated from tilemap hot path. The function may be retained only if other systems (text writer, etc.) still use it; its use in the tilemap commit loop is removed.
- `genesistan_hook_col_a`, `genesistan_hook_row_a`, `genesistan_hook_col_b`, `genesistan_hook_row_b` — cursor tracking replaced by dest_ptr derived from arcade workram.

---

## 7. Assembly Hot Path Design

### Entry: `genesistan_asm_tilemap_commit_bg` and `genesistan_asm_tilemap_commit_fg`

**Location**: `apps/rastan/src/startup_trampoline.s`

**Register contract (from C dispatcher)**:

| Register | Content |
|----------|---------|
| A0 | Descriptor list base (in genesistan_arcade_workram_words, 16 × 4-byte BE entries) |
| A1 | rastan_maincpu ROM base |
| A2 | pc080sn_tile_vram_lut base (ROM) |
| A3 | pc080sn_attr_lut base (ROM) |
| D0.w | strip_index |
| D1.w | starting dest_col (BG: column per desc, FG: column advances) |
| D2.w | desc_count = 16 |

**Returns**: D7.l = updated dest accumulator for C to write back to workram.

**Instruction-level behavior**:

Outer loop (dbf D2, outer_loop):
1. Load desc_addr: `movem.l (A0)+, D3` (4-byte BE: needs byte-swap if 68K is big-endian — it is, so direct load). Actually word-pair load: `move.w (A0)+, D3; swap D3; move.w (A0)+, D3` (or `movem` with byte-swap). The arcade workram is stored BE so this is a direct 32-bit load: `move.l (A0)+, D3`.
2. Bounds check D3 against ROM size limit; `bhs skip_desc` if out of range.
3. Add ROM base: `lea 0(A1,D3.l), A4`.
4. Load attr_word: `move.w (A4), D4`.
5. Load table_base: `move.w 2(A4), D5`.
6. Compute attr_key from D4 (5 bit ops, inline): `move.w D4, D6; and.w #3, D6; btst #13, D4; beq.s no_prio; bset #4, D6; no_prio: ...` (similar for vflip bit15, hflip bit14).
7. Load attr_partial: `move.w 0(A3,D6.w*2), D6` (or `lsl.w #1, D6; move.w 0(A3,D6.w), D6`).
8. Compute tile table base address: `lea 0(A1,D5.l), A4`.

Inner loop (dbf D3_inner, inner_loop) — D3 reused as cell counter = 3 (dbf counts from 3 to -1):

BG variant (`genesistan_asm_tilemap_commit_bg`):
9. `tile_addr = A4 + (D0.w << 1) + (cell << 3)` where cell = 3−D3_inner.
   - Pre-compute `A4 + (D0 << 1)` once per desc (outside inner loop).
   - Inside loop: offset = cell × 8; advance pointer by 8 each iteration.
10. `move.w (tile_ptr), D3_tile; and.w #0x3FFF, D3_tile` → arcade_tile.
11. `lsl.w #1, D3_tile; move.w 0(A2,D3_tile.l), D3_tile` → vram_slot.
12. `or.w D6, D3_tile` → tile_attr (attr_partial | vram_slot).
13. Compute VDP VRAM address: `plane_vram_base + dest_row*128 + dest_col*2`.
    - Per desc: dest_col is fixed. dest_row cycles 0,1,2,3 within inner loop.
    - VDP addr = 0xC000 + dest_col*2 + dest_row*128.
14. Build VDP control word: `vdp_ctl = 0x40000003 | ((vdp_addr & 0x3FFF) << 16) | (vdp_addr >> 14)`.
    - Pre-compute once per cell; no dynamic dispatch.
15. `move.l D_ctl, 0xC00004` — VDP control write.
16. `move.w D3_tile, 0xC00000` — VDP data write.
17. `dest_row += 1`.

After inner loop: `dest_col += 4` (advance to next descriptor's column position for BG).

FG variant (`genesistan_asm_tilemap_commit_fg`):
- Inner loop iterates over columns (not rows).
- `tile_addr = A4 + (strip_index << 3) + (col << 1)`.
- VRAM addr = 0xE000 + dest_row*128 + dest_col*2. dest_row is fixed per desc, dest_col advances.
- After inner loop: `dest_row += 1`.

**No SGDK calls. No C function calls. No memory allocation. No conditional function dispatch.**

---

## 8. Out of Scope

The following are explicitly NOT addressed in this architecture:

- **HUD text plane** — text is a separate intent class (Class A, `genesistan_hook_text_writer_*`). Text tiles use a separate VRAM region and a separate path from the tilemap system. Text is not part of this phase.

- **Palette correctness** — palette loading is Class E (`refresh_frontend_sprite_palettes`, CLCS capture). The tilemap architecture uses whatever CRAM state is present. Palette loading is a separate phase.

- **Sprite/tilemap Z-order interaction** — Genesis hardware handles Z-order via the VDP priority bit (bit 15 of TILE_ATTR). The priority bit is correctly translated through `pc080sn_attr_lut`. No additional Z-order logic is required.

- **Tilemap LRU cache for non-tilemap systems** — `tile_cache_get()` may remain for the text writer path if it uses the same LRU. Text writer tile lookup is a separate concern. The architecture removes `tile_cache_get()` only from the tilemap commit hot path.

- **PC090OJ sprite tiles** — sprite tiles use a separate VRAM region (`FRONTEND_RUNTIME_SPRITE_TILE_BASE = 1024`) and the `rastan_pc090oj_genesis` DMA path (Build 292). Not part of this system.

- **Scrolling layer effects (raster effects, per-line scroll)** — Rastan does not use per-scanline H-scroll. Full-plane scroll is sufficient. Raster effects are not part of this phase.

- **Scene transition tile preload timing** — the C init preloader walks `pc080sn_vram_preload.bin` at scene start. The mechanism for detecting scene transitions is the arcade state machine already tracked by the launcher. Exact trigger points are Cody implementation detail, not this design.

- **Tile VRAM region overflow** — if Python's unique tile count exceeds available VRAM slots (TILE_USER_INDEX through TILE_CACHE_BASE_A+TILE_CACHE_SIZE_A-1), the precompute script fails at build time with an explicit error. No runtime handling needed; this is a build-time constraint.

- **TC0100SCN** (Cadash tilemap chip) — Cadash uses TC0100SCN, not PC080SN. Architecture patterns from Cadash are applied but TC0100SCN-specific details are not applicable to Rastan.

---

PC080SN tilemap system defined for direct translation into an assembly-owned runtime pipeline with Python-preprocessed data and no intermediate C scaffolding.
