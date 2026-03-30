# Next Major Graphics Phase — Python-First Architecture

**Agent:** Andy (Architecture)
**Build baseline:** 291
**Date:** 2026-03-30
**Mandate:** Define the next major graphics implementation phase that steers the architecture toward Python preprocessing and eventual assembly hot-path ownership.

---

## 1. Purpose

Define a real, significant, non-scaffolding implementation phase that:

1. Moves static graphics work from runtime C into Python build-time preprocessing
2. Eliminates WRAM staging buffers where ROM-direct DMA can replace them
3. Reduces the sprite tile-prepare hot path to a minimal DMA-per-code loop
4. Lays the foundation for full assembly ownership of the tile-prepare inner loop
5. Aligns with the project's confirmed rendering strategy: opcode-replacement with shift-table reflow, Python as the static translation layer, C as transitional glue

This is an architecture plan. No code, spec, or build files are modified by this document.

---

## 2. Required Reading Incorporated

**Core project docs:**
- `AGENTS.md` — confirms: "direct opcode replacement with shift-table reflow" as the rendering strategy; holistic remap over trampoline hacks; specs as inputs, manifests as outputs
- `AGENT_GUIDE.md` — confirms: build real systems, not scaffolding; Andy plans, Cody implements, validate with evidence
- `ARCHITECTURE.md` — confirms: arcade produces intent, Genesis executes it; frame ownership is single-owner arcade vblank; pipeline = arcade logic → WRAM buffers → VBlank commit → VDP
- `CURRENT_STATE.md` — stale (references C-helper replacement which is complete since Build 281)
- `PROJECT_STORY.md` — confirms: key realization is "arcade expresses intent, not hardware commands"; original strategy was opcode-level translation; graphics is a pipeline; build real systems not scaffolding

**Current graphics architecture and results:**
- `full_graphics_system_completion_plan.md` — full phase map; confirmed Phase 3 (CRAM line 3 load) as remaining sprite blocker
- `opcode_vblank_sprite_migration_plan.md` — documents migration from C helper to opcode/ROM-side paths; now complete
- `vblank_graphics_architecture_plan.md` — authoritative architecture; defines five WRAM graphics buffers; confirms sprite pipeline is the hot path
- `full_prototype_sprite_execution_path.md` — justifies Option A (per-frame decode+upload from vblank handoff); confirms `rastan_pc090oj` as source
- `full_prototype_sprite_execution_results.md` — Build 283 baseline; confirms VDP tile region populated; one sprite visible; CRAM confirmed issue
- `sprite_interpretation_failure_diagnosis.md` — link chain and column-major order fixes defined; both confirmed fixed Build 284
- `sprite_interpretation_fix_results.md` — confirms both fixes applied; sequential link chain working
- `live_decode_buffer_wiring_fix_results.md` — Build 285: confirms `VDP_loadTileData` fires every vblank; VRAM 0x8000 = `1199 8111...`
- `canonical_blocka_attr_decode_results.md` — Build 286: `attr_lut=0x6000` → pal_line=3; sprites use CRAM line 3
- `zero_code_filter_results.md` — Build 287: `active_count=1`, `chain_ok=true`
- `next_sprite_content_selection_object_composition.md` — defines zero-code filter reasoning; confirmed implemented

**Reference implementations:**
- `rainbow_islands_arcade_vs_genesis_graphics_comparison.md` — see Section 11
- `cadash_arcade_vs_genesis_graphics_comparison.md` — see Section 11

**Code sources read:**
- `apps/rastan/src/main.c` — `frontend_decode_pc090oj_cell()`, `genesistan_sprite_tile_prepare()`, `tile_cache_get()`, WRAM overlay declarations
- `specs/startup_title_remap.json` — whole_maincpu_copy, declared arcade windows, required symbols

**MAME / hardware references:**
- PC090OJ: Taito 4bpp sprite hardware. Tiles are 16×16 pixels. MAME decodes sprite tile ROMs during machine init (gfxdecode) — a static one-time operation equivalent to Python build-time preprocessing.
- PC080SN: Taito dual-plane tilemap hardware. Same gfxdecode pattern. `rastan_pc080sn` is already in Genesis-compatible 32-bytes-per-8×8-tile format (confirmed by `tile_cache_get()` using `arcade_tile * 32U` for direct DMA).

---

## 3. Python vs C vs Assembly Ownership Map

### 3.1 Sprites / PC090OJ

| Component | Current owner | Target owner | Rationale |
|-----------|---------------|--------------|-----------|
| Tile graphics decode (arcade→Genesis format) | Runtime C (`frontend_decode_pc090oj_cell`) | **SHOULD MOVE TO PYTHON** | Decode is pure byte-rearrangement (memcpy only, no arithmetic). 4096 cells × 128 bytes is fully static. Python processes once at build time. |
| Tile lookup / VRAM slot assignment | Runtime C (unique-code loop in prepare) | SHOULD STAY TEMPORARILY IN C → EVENTUALLY ASSEMBLY | Per-frame scan of up to 18 active codes; bounded, deterministic. Assembly hot path once stable. |
| WRAM tile staging buffer | Runtime (8KB WRAM) | **ELIMINATE** | Replaced by direct DMA from pre-decoded ROM blob to VRAM. WRAM staging not needed when source is pre-baked ROM. |
| Attribute decode (word0 → pal_line/flip) | Runtime C (prepare loop) | SHOULD STAY TEMPORARILY IN C | Per-frame, per-entry live arcade data. Cannot be pre-baked. |
| SAT construction (word0/1/2/3 → SAT) | Runtime Assembly (`genesistan_sprite_commit_asm`) | SHOULD ULTIMATELY STAY ASSEMBLY | Already in assembly. Correct. Continues. |
| VRAM DMA upload | Runtime C (`VDP_loadTileData`) | SHOULD ULTIMATELY MOVE TO ASSEMBLY | After Python pre-decode lands, DMA call is trivial per code. Assembly inner loop can do 4-instruction DMA-per-code. |

### 3.2 Tilemaps / PC080SN

| Component | Current owner | Target owner | Rationale |
|-----------|---------------|--------------|-----------|
| Tile graphics conversion | Already done (`rastan_pc080sn` in Genesis format at 32 bytes/tile) | **ALREADY IN PYTHON / BUILD** | `tile_cache_get()` DMA-copies `rastan_pc080sn + arcade_tile * 32` directly. No conversion at runtime. |
| Tile index remap (LRU cache) | Runtime C (`tile_cache_get()`, O(N) linear scan) | SHOULD STAY TEMPORARILY IN C → deferred optimization | Cache miss path, not per-frame hot. LRU eviction is bounded. A hash map could reduce miss lookup to O(1) but this is a later optimization pass. |
| Tile attribute decode | Runtime C | SHOULD STAY TEMPORARILY IN C | Per descriptor write; arcade-live. |
| Address → x/y mapping | Runtime C (`pc080sn_attr_addr_to_xy`) | SHOULD STAY TEMPORARILY IN C | Descriptor-to-plane coordinate derived from C-window address; formula is stable. Could become a Python lookup table later if address space is fully mapped. |
| Strip / descriptor translation | Runtime C (Build 291 — real translation live) | SHOULD STAY TEMPORARILY IN C → EVENTUALLY ASSEMBLY | Real arcade descriptor path now active. Stable for now. Assembly ownership when hot-path cost proven. |
| Tilemap cell writes (`VDP_setTileMapXY`) | Runtime C (SGDK call) | SHOULD ULTIMATELY MOVE TO ASSEMBLY | SGDK overhead per cell write; in heavy-scroll gameplay this is a bottleneck. Direct VDP data-port write in assembly is faster. |
| Plane commit | Runtime C | SHOULD ULTIMATELY MOVE TO ASSEMBLY | Per-plane write path; after tilemap descriptor path stabilizes. |

### 3.3 Palette / CRAM

| Component | Current owner | Target owner | Rationale |
|-----------|---------------|--------------|-----------|
| Palette conversion (arcade 444→Genesis) | Python (already: `genesistan_palette_rom_table` pre-converted) | **ALREADY IN PYTHON** | Done. ROM table is pre-converted at build time. |
| CLCS runtime capture → CRAM | Runtime C (`genesistan_palette_clcs[]` capture) | SHOULD STAY IN C | Live arcade palette writes cannot be pre-baked. Capture mechanism must stay runtime. |
| CRAM load (all active banks) | Runtime C (`refresh_frontend_sprite_palettes`) | SHOULD STAY TEMPORARILY IN C → EVENTUALLY ASSEMBLY | Per-frame; one SGDK call per palette bank. Assembly equivalent is 16 word-writes to VDP data port — fast. |

### 3.4 Scrolling

| Component | Current owner | Target owner | Rationale |
|-----------|---------------|--------------|-----------|
| Scroll register mapping | Runtime C (static WRAM offset map) | COULD PARTIALLY MOVE TO PYTHON | If scroll offset constants are static (same WRAM offsets for all game states), Python can validate and embed them as a const table. Runtime reads the table instead of hardcoded offsets. Minor benefit. |
| Runtime scroll commit | Runtime C (`genesistan_scroll_from_workram_vdp`) | SHOULD ULTIMATELY MOVE TO ASSEMBLY | 3–4 VDP register writes per plane. Trivial in assembly. |

### 3.5 HUD / Text

| Component | Current owner | Target owner | Rationale |
|-----------|---------------|--------------|-----------|
| Glyph tile graphics | `rastan_pc080sn` (PC080SN ROM, already in Genesis format) | **ALREADY DONE** | Font tiles are PC080SN tiles; pre-converted at build. |
| Digit system (score/lives/timer) | Not implemented (Phase 7 work) | SHOULD STAY TEMPORARILY IN C when built | Dynamic per-frame value reads. Cannot pre-bake digit values. |
| Descriptor translation | Runtime C (`window_rewrite_rules`) | SHOULD STAY TEMPORARILY IN C | Per descriptor, live arcade data. |

---

## 4. Chosen Next Major Implementation Phase

**Pre-decode the PC090OJ tile ROM from arcade layout to Genesis 4bpp column-major format using Python at build time, and update the sprite tile-prepare path to DMA directly from the pre-decoded ROM blob to VRAM — eliminating the 8KB WRAM staging buffer and all runtime decode arithmetic.**

Also bundled in this phase:
**Add `refresh_frontend_sprite_palettes()` to the vblank handoff to load CRAM line 3 (active sprite palette) each frame.**

The palette call is one line; the Python pre-decode is the architectural driver. Both are non-scaffolding real implementation work.

---

## 5. Why This Is the Right Next Phase

### 5.1 The decode is a pure layout transformation — the clearest Python opportunity in the project

`frontend_decode_pc090oj_cell()` (main.c:1026–1053) does:
```c
for (y = 0; y < 16; y++) {
    src_row = src + (y * 8);          // row = 8 bytes = left 4 + right 4
    tile_left  = column-major slot;
    tile_right = column-major slot;
    memcpy(tile_left,  src_row, 4);   // left 4 bytes → TL or BL tile
    memcpy(tile_right, src_row + 4, 4); // right 4 bytes → TR or BR tile
}
```

This is **pure byte rearrangement**. No pixel arithmetic. No format conversion beyond spatial layout. The PC090OJ ROM is already in Genesis 4bpp packed-nibble format; the decode merely reorganizes 16 rows × 8 bytes into 4 tiles × 32 bytes in column-major order.

Python can replicate this in a 20-line script. 4096 cells × 128 bytes = 512KB processed once at build time, replacing per-frame runtime loops.

### 5.2 Eliminating the staging buffer removes 8KB WRAM and the DMA two-step

Current flow:
```
CPU: decode → frontend_runtime_sprite_tile_buffer (8KB WRAM staging)
DMA: staging buffer → VRAM tile 1024+
```

After Python pre-decode:
```
DMA: rastan_pc090oj_genesis[code * 128] → VRAM tile 1024+  (ROM → VRAM directly)
```

The WRAM staging buffer is an architectural artifact of doing decode in C. With a pre-decoded ROM blob, the DMA controller reads directly from ROM (Genesis DMA can DMA from 68000 ROM address space to VRAM) and writes directly to VRAM. The staging step disappears.

8KB WRAM is freed. This is significant on the Genesis (64KB total WRAM; current WRAM overlay is large).

### 5.3 This is the foundation for assembly ownership of the sprite tile-prepare inner loop

After Python pre-decode, the per-unique-code work in `genesistan_sprite_tile_prepare()` reduces to:
```
for each active unique code:
    VDP_loadTileData(rastan_pc090oj_genesis + code * 128, SPRITE_TILE_BASE + slot*4, 4, DMA);
```

This is a 4-instruction assembly loop:
```asm
; d0 = code, d1 = slot
mulu  #128, d0        ; byte offset = code * 128
lea   rastan_pc090oj_genesis, a0
add.l d0, a0          ; a0 = &genesis_rom[code * 128]
; set up DMA: source a0, dest VRAM[slot*4 + SPRITE_TILE_BASE], count 4
```

This loop has no C dependencies once the pre-decoded blob exists. It's a natural assembly target.

### 5.4 This unlocks sprite visibility: CRAM load + correct tile data together

With CRAM line 3 loaded (palette fix) and VRAM tiles sourced directly from the pre-decoded ROM, the first recognizable Rastan logo sprite pixels will appear. This is not a visual criterion — it is the functional consequence of two pipeline stages being simultaneously correct for the first time.

### 5.5 The PC080SN side confirms the pattern works

`tile_cache_get()` at main.c:1247 already does:
```c
VDP_loadTileData((const u32 *)(rastan_pc080sn + (u32)arcade_tile * 32U), vram_slot, 1, DMA);
```

PC080SN tiles are already in Genesis format (32 bytes/tile). The cache miss path is already a direct DMA from ROM. This confirms the architecture: Python-pre-decoded blobs + ROM-direct DMA is the correct pattern for this project. PC090OJ should match this pattern.

### 5.6 No scaffolding

The pre-decoded blob contains real arcade PC090OJ tile pixel data, correctly arranged for Genesis VDP rendering. No test patterns, no demo content. Every pixel in the blob is a real arcade sprite pixel.

### 5.7 Alignment with project constraints

- **Python should do everything static**: tile layout rearrangement is 100% static
- **C should be thin**: prepare loop shrinks from decode+stage+bulk-DMA to lookup+per-code-DMA
- **SGDK helpers minimized**: fewer DMA calls (one per unique code vs one bulk + decode loop)
- **Assembly path prepared**: inner loop is trivially converted to assembly after landing

---

## 6. Exact Implementation Boundary

### 6.1 Python preprocessing — new script

**File:** `tools/translation/preconvert_pc090oj_tiles.py`

**Input:** `build/regions/pc090oj.bin` (4096 cells × 128 bytes, arcade spatial layout)

**Logic:**
```python
# For each cell 0..4095:
# src[cell * 128 : (cell+1) * 128] = 16 rows × 8 bytes
# dst[cell * 128 : (cell+1) * 128] = 4 tiles × 32 bytes, column-major
# Row y (0..15):
#   src_row = src[y*8 : y*8+8]
#   if y < 8:
#     dst[0*32 + y*4 : 0*32 + y*4+4] = src_row[0:4]   # TL tile, row y
#     dst[2*32 + y*4 : 2*32 + y*4+4] = src_row[4:8]   # TR tile, row y
#   else:
#     dst[1*32 + (y-8)*4 : 1*32 + (y-8)*4+4] = src_row[0:4]  # BL tile
#     dst[3*32 + (y-8)*4 : 3*32 + (y-8)*4+4] = src_row[4:8]  # BR tile
```

**Output:** `build/pc090oj_genesis.bin` (4096 cells × 128 bytes, Genesis column-major layout)

**Makefile integration:** Add a build rule before the SGDK compile step:
```makefile
build/pc090oj_genesis.bin: build/regions/pc090oj.bin
    python3 tools/translation/preconvert_pc090oj_tiles.py \
        build/regions/pc090oj.bin build/pc090oj_genesis.bin
```

### 6.2 ROM resource replacement

Replace the `rastan_pc090oj` resource declaration (currently embedding `build/regions/pc090oj.bin`) with `rastan_pc090oj_genesis` embedding `build/pc090oj_genesis.bin`.

The external symbol name in main.c changes from `rastan_pc090oj` to `rastan_pc090oj_genesis`. All references to `rastan_pc090oj` in main.c for the sprite path must be updated.

ROM size does not change: both blobs are 4096 × 128 = 512KB.

### 6.3 Runtime changes — `apps/rastan/src/main.c`

**Remove:**
- `frontend_decode_pc090oj_cell()` function body — dead code once Python handles it; leave declaration as a tombstone comment
- `frontend_runtime_sprite_tile_buffer[FRONTEND_RUNTIME_MAX_UNIQUE_CODES * 4 * 8]` from `wram_overlay.launcher` struct — frees 8KB WRAM
- `frontend_runtime_sprite_codes[FRONTEND_RUNTIME_MAX_UNIQUE_CODES]` — can be removed if unique-code tracking is simplified (the slot index IS the unique-code index now; codes don't need caching separately)
- `live_decode_upload_buffer` local in `genesistan_sprite_tile_prepare()`
- `memset(live_decode_upload_buffer, 0, ...)` at prepare start
- Bulk `VDP_loadTileData(live_decode_upload_buffer, ..., unique_count * 4U, DMA)` at prepare end

**Modify `genesistan_sprite_tile_prepare()`:**

The unique-code discovery loop must change. Instead of decoding into staging buffer on new code:

```c
// BEFORE:
slot = unique_count;
wram_overlay.launcher.frontend_runtime_sprite_codes[slot] = code;
frontend_decode_pc090oj_cell(code, live_decode_upload_buffer + (slot * 4 * 8));
unique_count++;

// AFTER:
slot = unique_count;
SYS_disableInts();
VDP_loadTileData(
    (const u32 *)(rastan_pc090oj_genesis + (u32)code * 128U),
    FRONTEND_RUNTIME_SPRITE_TILE_BASE + (u16)(slot * 4),
    4,
    DMA
);
VDP_waitDMACompletion();
SYS_enableInts();
unique_count++;
```

This DMA-uploads the pre-decoded cell directly from ROM to VRAM on first encounter. No staging buffer. No decode loop.

Note: interrupt disable around DMA is required for Genesis hardware correctness. This was already in the bulk upload path; it moves to per-code upload inline.

**Also add in `genesistan_frontend_live_vint_handoff()` (Phase 3 palette fix):**

```c
refresh_frontend_sprite_palettes();
```

Called after `genesistan_sprite_tile_prepare()`, before `genesistan_sprite_commit_asm()`. This loads CRAM line 3 (active sprite palette) from `genesistan_palette_rom_table`. This completes the sprite pipeline's CRAM break identified in full_graphics_system_completion_plan.md.

### 6.4 `apps/rastan/src/startup_bridge.c` (WRAM overlay)

Remove:
- `frontend_runtime_sprite_tile_buffer[FRONTEND_RUNTIME_MAX_UNIQUE_CODES * 4 * 8]` (8KB)
- `frontend_runtime_sprite_codes[FRONTEND_RUNTIME_MAX_UNIQUE_CODES]` (128 bytes)

Keep:
- `genesistan_sprite_tile_lut[18]` — still needed; maps entry idx → VRAM tile base
- `genesistan_sprite_attr_lut[18]` — still needed
- `genesistan_sprite_active_count` — still needed

### 6.5 What must remain temporary (runtime C)

- Unique-code LUT management (tracks which code is at which VRAM slot) — small loop, bounded
- `attr_lut` computation (per-frame arcade word0 decode) — live arcade data
- `refresh_frontend_sprite_palettes()` call — until CLCS capture is validated
- `tile_cache_get()` for PC080SN — LRU management stays C for now

### 6.6 What must NOT be touched

- `genesistan_sprite_commit_asm()` in startup_trampoline.s — already assembly, correct, no change
- `tile_cache_get()` PC080SN path — separate concern, not this phase
- Any spec/startup_title_remap.json entries — no spec changes needed
- Tilemap descriptor translation (Build 291 just landed) — let it stabilize

---

## 7. Required Python Preprocessing Deliverables

### 7.1 Script: `tools/translation/preconvert_pc090oj_tiles.py`

**Inputs:**
- `build/regions/pc090oj.bin` — Rastan PC090OJ sprite tile ROM, arcade spatial layout, 512KB

**Outputs:**
- `build/pc090oj_genesis.bin` — all 4096 cells pre-decoded to Genesis column-major format, 512KB

**Algorithm spec (exact, derived from `frontend_decode_pc090oj_cell()`):**

For each cell index `c` in range 0..4095:
1. `src = input[c * 128 : c * 128 + 128]` (16 rows × 8 bytes)
2. Allocate `dst = bytearray(128)` (4 tiles × 32 bytes)
3. For each row `y` in 0..15:
   - `src_row = src[y * 8 : y * 8 + 8]`
   - If `y < 8`:
     - `dst[0*32 + y*4 : 0*32 + y*4 + 4] = src_row[0:4]`  ← TL tile, row y
     - `dst[2*32 + y*4 : 2*32 + y*4 + 4] = src_row[4:8]`  ← TR tile, row y
   - Else:
     - `dst[1*32 + (y-8)*4 : 1*32 + (y-8)*4 + 4] = src_row[0:4]`  ← BL tile
     - `dst[3*32 + (y-8)*4 : 3*32 + (y-8)*4 + 4] = src_row[4:8]`  ← BR tile
4. Append `dst` to output file

**Verification step (required in script):**

After generating output, verify one known cell:
- Cell 0x03CA (tile code from Build 287 probe: `idx=0 code=03CA`): decode cell 0x03CA from input, decode cell 0x03CA from output using a reference C-equivalent pass, assert they match
- Print: `OK: cell 0x03CA matches reference decode`

This ensures the Python algorithm matches `frontend_decode_pc090oj_cell()` exactly.

**Where outputs are stored:**
- `build/pc090oj_genesis.bin` — intermediate build artifact, gitignored
- Embedded in Genesis ROM via Makefile resource declaration

**How runtime consumes:**
- SGDK `__bin` resource declared as `const u8 rastan_pc090oj_genesis[];`
- Referenced in main.c as `rastan_pc090oj_genesis + (u32)code * 128U` for DMA source
- No runtime decode; pointer arithmetic only

### 7.2 Makefile target

```makefile
PREREQ_PC090OJ_GENESIS = build/pc090oj_genesis.bin

$(PREREQ_PC090OJ_GENESIS): build/regions/pc090oj.bin tools/translation/preconvert_pc090oj_tiles.py
	python3 tools/translation/preconvert_pc090oj_tiles.py $< $@

# Add to deps before SGDK compile:
release: $(PREREQ_PC090OJ_GENESIS) ...
```

---

## 8. New Runtime Hot Path After This Phase

### 8.1 Per-vblank sprite path (after phase)

```
[1] genesistan_run_original_frontend_tick()
    → arcade tick runs; Block-A at 0xE0FF11FE populated with descriptor data

[2] genesistan_sprite_tile_prepare()   [C — significantly leaner after phase]
    for idx in 0..17:
        read entry from 0xE0FF11FE
        if sentinel (y == 0x0180) or code == 0: continue
        compute attr_lut[idx] from word0                  ← live; stays C
        if code not in unique_codes:
            DMA: rastan_pc090oj_genesis[code * 128] → VRAM[SPRITE_BASE + slot*4]  ← ROM→VRAM direct
            assign tile_lut[idx] = SPRITE_TILE_BASE + slot*4
            slot++
        else:
            tile_lut[idx] = cached slot                   ← O(1) after Python landing

[3] refresh_frontend_sprite_palettes()   [C — one call]
    → loads CRAM line 3 from genesistan_palette_rom_table
    → sprites now have live palette colors

[4] genesistan_sprite_commit_asm()   [Assembly — unchanged]
    → reads Block-A + tile_lut + attr_lut
    → builds SAT entries with sequential link chain
    → writes to VDP VRAM 0xF800
```

### 8.2 What runtime work disappears because Python did it

| Was runtime work | Goes away | How |
|-----------------|-----------|-----|
| `frontend_decode_pc090oj_cell()` call (16-iteration loop, 32 memcpy calls per unique code) | YES | Python pre-decoded all 4096 cells |
| `memset(live_decode_upload_buffer, 0, 8KB)` per frame | YES | No staging buffer |
| Bulk `VDP_loadTileData(staging_buffer, ...)` per frame | YES | Per-code DMA replaces bulk-after-decode |
| 8KB WRAM staging buffer | YES | ROM-direct DMA; no intermediate |

### 8.3 What runtime work remains

| Runtime work | Why it stays |
|-------------|-------------|
| Unique-code scan loop (O(active_count ≤ 18)) | Live Block-A per frame |
| Per-code DMA from `rastan_pc090oj_genesis` | One DMA per new unique code; negligible |
| `attr_lut` computation from word0 | Live arcade per-entry attribute |
| `refresh_frontend_sprite_palettes()` | Live palette from CLCS or ROM table |
| `genesistan_sprite_commit_asm()` (already assembly) | SAT formation from live Block-A |

### 8.4 Future assembly target unlocked

After Python pre-decode, the prepare hot loop becomes:

```
for each new unique code (typically 1–13 per frame):
    1. Code → ROM byte offset = code << 7
    2. Set up DMA: source = rastan_pc090oj_genesis + offset, dest = VRAM[SPRITE_BASE + slot*4], count = 4
    3. Trigger DMA
    4. slot++
```

This is 8–10 instructions per unique code in 68000 assembly. The entire per-code path can be a tight assembly loop with no C function calls. This is the natural next step after this phase.

---

## 9. Out-of-Scope For This Phase

The following MUST NOT be touched in this implementation pass:

- **PC080SN tile decode** — already in Genesis format; no decode step needed; `tile_cache_get()` is not the target of this phase
- **LRU cache optimization** — O(N) cache scan is not addressed; deferred
- **Tilemap descriptor translation** — Build 291 just landed; let it stabilize; no changes
- **SAT assembly** (`genesistan_sprite_commit_asm`) — already correct assembly; no changes
- **Scroll system** — not this phase; `genesistan_scroll_from_workram_vdp()` is separate work
- **In-game HUD** — Phase 7 work; not this phase
- **CLCS capture validation** — separate concern; ROM table fallback sufficient for this phase
- **Synthetic tile data, test patterns, demo content** — none; every pixel in the pre-decoded blob is real arcade sprite data
- **Visual debugging passes** — not this phase; the phase succeeds when code and data are correct, not when it "looks right"
- **Block-B sprite descriptors** — deferred; same pipeline applies but not in this pass
- **Any spec/startup_title_remap.json changes** — no ROM patch changes needed for this phase

---

## 10. Success Criteria

Success criteria are implementation-centric. Visual output is a consequence, not the primary measure.

### 10.1 Python preprocessing delivered

- `tools/translation/preconvert_pc090oj_tiles.py` exists and runs without error
- `build/pc090oj_genesis.bin` generated: 512KB, 4096 × 128 bytes
- Script verification: `OK: cell 0x03CA matches reference decode` printed
- Makefile dependency: `build/pc090oj_genesis.bin` declared as a prerequisite before SGDK compile step

### 10.2 Runtime code correctness

- `frontend_decode_pc090oj_cell()` not called at runtime (confirmed by disassembly: no reference to the decode function in the tile-prepare call graph)
- `frontend_runtime_sprite_tile_buffer` absent from WRAM overlay (confirmed by map file: the 8KB region no longer appears)
- `memset` of staging buffer absent from `genesistan_sprite_tile_prepare()` disassembly
- Bulk `VDP_loadTileData` from staging buffer absent from prepare disassembly
- Per-code `VDP_loadTileData(rastan_pc090oj_genesis + code * 128, ...)` present in prepare disassembly for new-code path

### 10.3 Data flow correctness

- ROM address of `rastan_pc090oj_genesis` is in the 68000 ROM address space (0x000000–0x3FFFFF): DMA source is accessible
- DMA transfer size per code: exactly 4 tiles × 32 bytes = 128 bytes = 1 call with count=4
- VRAM tile 1024 (byte offset 0x8000) contains same pixel data as before (regression check: same `1199 8111...` pattern for code 0x03CA)

### 10.4 WRAM savings confirmed

- WRAM map shows `frontend_runtime_sprite_tile_buffer` region eliminated: 8192 bytes freed
- Total WRAM overlay size decreases by at least 8KB

### 10.5 Palette (bundled Phase 3 fix)

- `refresh_frontend_sprite_palettes()` present in `genesistan_frontend_live_vint_handoff()` source
- Function loads CRAM line 3 with non-zero colors from `genesistan_palette_rom_table`
- CRAM entries 48–63 are non-zero after handoff (confirmed by reading `genesistan_palette_rom_table[48..63]` statically)

### 10.6 Future assembly path is clear

- Per-code DMA call in prepare has exactly one DMA setup + trigger per unique code: the assembly equivalent is a trivial 8–10 instruction loop with no function calls to external C

---

## 11. Rainbow Islands / Cadash / MAME Alignment

### 11.1 What MAME implies must stay runtime

MAME's `screen_update()` callback (per-frame) does:
- `m_pc090oj->draw_sprites(...)` — reads sprite RAM (live, per-frame), positions and renders sprites
- `m_pc080sn->tilemap_draw(...)` — reads tilemap RAM (live, per-frame), renders planes

These are inherently runtime because sprite RAM and tilemap RAM change every frame with live game data. The equivalent Genesis operations (Block-A read, PC080SN descriptor read) must also stay runtime.

MAME's `machine_start()` / gfxdecode does:
- Convert sprite tile ROM from planar to rendered format — **one time, static**
- Convert tilemap tile ROM from planar to rendered format — **one time, static**

These one-time operations are the Python equivalent. MAME does them at emulator load time. Python does them at build time. Python is earlier and therefore eliminates even the load-time overhead.

**Implication**: anything in MAME's gfxdecode phase (static ROM conversion) belongs in Python for this project. Anything in MAME's screen_update() (live state reads) must stay runtime.

### 11.2 What Rainbow Islands teaches for preprocessing vs runtime

Rainbow Islands Genesis (reference doc section 4):
- "Sprite/SAT-style path appears **staged** then uploaded" — WRAM staging at `0xFFFB00`, then VDP upload
- This is the WRAM-staging pattern that Rastan currently uses (and this phase eliminates)

The Rainbow Islands pattern of "stage in WRAM then DMA" is appropriate when the source data must be assembled from multiple live sources (e.g., per-sprite attribute + position + tile combined at runtime). For Rastan sprite tiles, the source is static ROM data that can be pre-decoded, making the staging buffer unnecessary.

**Rainbow Islands lesson**: staging is correct when data is dynamically assembled; it is overhead when data is purely static ROM that can be pre-baked.

### 11.3 What Cadash teaches for preprocessing vs runtime

Cadash Genesis (reference doc section 4):
- "Palette-like staged words in WRAM (`0xFF05F0`, `0xFF0640`, etc.) are pushed to VDP" — pre-staged palette data
- "Tile/plane writes: loops convert source words and stream to `0xC00000`" — runtime stream with conversion

The Cadash tile-write path does source conversion at runtime (loop that converts and streams). This is the pattern Rastan's current PC090OJ decode follows. This phase eliminates the conversion by pre-baking it, reducing the runtime loop to a pure DMA copy. Cadash's approach was appropriate for a different code base; Rastan's Python-first architecture can go further.

**Cadash lesson**: runtime tile-write conversion is valid as a translation pattern, but Python pre-decode is strictly better when the source is static — it reduces runtime to DMA-only and enables assembly ownership of the hot loop.

### 11.4 Where Rastan can be more preprocessing-heavy than the reference implementations

Both Rainbow Islands and Cadash Genesis were written as console games in the first place (or translated by teams without Python build tools). Their "preprocessing" was done at game development time, hardcoded into compiled data. Rastan's Python-first build system allows post-hoc preprocessing of arcade ROM data — something not possible in the original console development context.

**Rastan advantage**: Python can introspect and pre-convert the arcade ROM data offline, then embed the result. The reference implementations (Rainbow Islands, Cadash) cannot be meaningfully compared on preprocessing degree because they were built differently. Rastan should use its Python build pipeline to go further: all static ROM conversions done at build time, all runtime paths reduced to DMA + attribute lookups.

### 11.5 MAME PC090OJ gfxdecode → Python preconvert_pc090oj_tiles.py equivalence

MAME's PC090OJ GFX decode (from MAME source conventions for Taito 4bpp sprites):
```
GFXDECODE_ENTRY("gfx_oa91", 0, sprites_layout_16x16, 0, 16)
```
This tells MAME to decode the sprite ROM using the 16×16 layout, which converts the planar ROM data into MAME's internal "packed" format during machine init.

For Rastan, the `frontend_decode_pc090oj_cell()` confirms the PC090OJ ROM is already in packed (Genesis-compatible) 4bpp format — only the spatial rearrangement (rows → tiles) is needed. `preconvert_pc090oj_tiles.py` does the equivalent of MAME's gfxdecode spatial rearrangement, but at Python build time instead of emulator init time.

MAME gfxdecode = Python preconvert_pc090oj_tiles.py. Same logical operation, different execution time (emulator load vs build time).

---

## 12. Final Recommendation

The next implementation phase for Cody is:

1. **Write `tools/translation/preconvert_pc090oj_tiles.py`**: reads `build/regions/pc090oj.bin`, implements the same row→tile rearrangement as `frontend_decode_pc090oj_cell()`, outputs `build/pc090oj_genesis.bin`. Includes verification against known cell 0x03CA.

2. **Update Makefile**: add `build/pc090oj_genesis.bin` as a build prerequisite generated before SGDK compile.

3. **Replace `rastan_pc090oj` ROM resource** with `rastan_pc090oj_genesis` embedding `build/pc090oj_genesis.bin`.

4. **Modify `genesistan_sprite_tile_prepare()` in main.c**: remove staging buffer, remove decode call, replace with per-code `VDP_loadTileData(rastan_pc090oj_genesis + code * 128, slot, 4, DMA)` inline.

5. **Remove `frontend_runtime_sprite_tile_buffer` and `frontend_runtime_sprite_codes`** from WRAM overlay (startup_bridge.c and wram_overlay.launcher struct).

6. **Add `refresh_frontend_sprite_palettes()` call** to `genesistan_frontend_live_vint_handoff()` (Phase 3 palette fix — one line, bundled here since it completes the sprite pipeline).

This phase eliminates the only remaining non-trivial runtime work in the sprite tile path, frees 8KB WRAM, produces real arcade tile pixels from pre-decoded ROM, and establishes the clean DMA-from-ROM pattern that assembly will own in the following pass.

The next implementation direction is a significant, real graphics-system phase that moves static translation work into Python where possible, keeps runtime C thin, and prepares the true hot path for eventual assembly ownership.
