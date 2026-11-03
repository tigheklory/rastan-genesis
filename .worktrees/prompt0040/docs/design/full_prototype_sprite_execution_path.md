# Full Prototype Sprite Execution Path

## 1. Purpose

This document defines the first full prototype for the Rastan Genesis sprite execution path.
The prototype produces visible sprite output with real arcade tile data — not a test pattern,
not tile 1, not a solid block. After this prototype, SAT entries reference real decoded arcade
tiles from `rastan_pc090oj`, VRAM contains real pixel patterns for those tiles, and the entire
pipeline runs under arcade-vblank-owned control.

This plan is grounded in:
- Confirmed Block-A data: entry 0 = `0000 00E8 03CA 0010` (tile code 0x03CA)
- Confirmed assembly commit path: `genesistan_sprite_commit_asm` fires every vblank (793 hits)
- Confirmed SAT at 0xF800 is nonzero from assembly writes
- Confirmed visual FAIL: all SAT entries currently point to VRAM tile 1 (test pattern, `0x8001`)
- Confirmed root cause: no real sprite tile data is decoded or uploaded in the live vblank path
- Known tile format: `rastan_pc090oj` ROM embedded in Genesis binary; 4096 cells × 128 bytes;
  each cell decodes to 4 Genesis 8×8 tiles (32 bytes each); total 4 tiles per arcade sprite cell
- Confirmed decoder exists in C: `frontend_decode_pc090oj_cell(u16 code, u32 *dst_tiles)`
- Confirmed VRAM slot logic exists in C: `frontend_runtime_tile_for_code(code, &unique_count)`
  fills `VRAM tile index = FRONTEND_RUNTIME_SPRITE_TILE_BASE + (slot * 4)`, base = 1024

---

## 2. Chosen Prototype Path (one choice, justified)

**Option A: Pre-decoded tile upload of the active Block-A set, called from vblank handoff
before the assembly SAT commit.**

### Definition

Before `genesistan_sprite_commit_asm()` fires each vblank, a new C call
(`genesistan_sprite_tile_prepare()`) scans Block-A at `0xE0FF11FE` (18 entries), extracts
each unique tile code, calls `frontend_decode_pc090oj_cell(code, dst)` to decode each cell
into 4 Genesis tiles, and uploads the decoded tiles to a fixed VRAM region reserved for
sprite tiles. The assembly commit then reads Block-A again and builds SAT entries using the
real VRAM tile indices from that fixed region.

### Why Option A over B and C

**Why not Option B (per-frame demand cache with LRU eviction)?**
The existing `tile_cache_get()` in main.c is built for the text tile system and is hardwired
to `rastan_pc080sn` (the text ROM). Adapting it to `rastan_pc090oj` in-place would risk
regression to the text path. More importantly, LRU cache management inside or adjacent to
the assembly commit loop adds lookup latency and state complexity that is not justified for a
prototype covering 18 entries. The current Block-A stream has a small, bounded unique tile
set (probe data: entry0=0x03CA, other entries likely in a compact range). A flat per-frame
scan of 18 entries and upload of all unique tiles is bounded, simple, and requires no eviction
policy.

**Why not Option C (startup pre-decode of all tiles)?**
`rastan_pc090oj` is 524288 bytes = 4096 cells × 128 bytes = 16384 Genesis tiles × 32 bytes =
524288 bytes of VRAM just for tiles. Genesis VRAM is 65536 bytes total. Uploading all sprite
tiles at startup is not feasible. Even a partial pre-decode of the first N cells would require
bounding knowledge of which cells are needed — which is exactly what Block-A provides at
runtime.

**Option A is the correct prototype path.** It is:
- Bounded: at most 18 unique tile codes per frame, each code decodes to 4 tiles (128 bytes VRAM)
- Simple: no cache, no eviction, fixed VRAM region, direct index formula
- Correct: real arcade pixel data from `rastan_pc090oj` in VRAM before SAT references it
- Achievable: `frontend_decode_pc090oj_cell()` already exists and is proven correct
- Ordered: tile decode runs before SAT commit (arcade vblank constraint satisfied)

### Key facts from research

- `rastan_pc090oj`: embedded in Genesis ROM as `const u8 rastan_pc090oj[]`; 524288 bytes;
  4096 cells; each cell is 128 bytes = 16 rows × 8 bytes per row; each byte = 2 nibbles = 2 pixels
- Decode: `frontend_decode_pc090oj_cell(code, dst)` splits one 128-byte cell into 4 Genesis
  tiles of 32 bytes each (top-left, top-right, bottom-left, bottom-right of a 16×16 cell)
- Block-A word2 carries the arcade cell index (masked to `& 0x3FFF`)
- Confirmed tile code in stream: `code = 0x03CA` (from probe data `blockA_entry0=0000 00E8 03CA 0010`)
- SAT tile index formula: Genesis SAT word2 tile field uses the VRAM tile index directly

---

## 3. Responsibility Classification

| Responsibility | Classification | Notes |
|---|---|---|
| Block-A scan (18 entries at 0xE0FF11FE) | MOVE NOW | Already in assembly commit; also needed in new tile prepare step |
| Validity filtering (zero-tuple, 0x0180 sentinel) | KEEP TEMPORARILY | Assembly commit already has 0x0180 check; full zero-tuple check deferred |
| Coordinate conversion (y+0x80, x+0x80) | MOVE NOW | Already in assembly commit; stays |
| **Tile decode (PC090OJ → Genesis 4bpp)** | **MOVE NOW** | Heart of the prototype; call `frontend_decode_pc090oj_cell()` per unique code |
| **VRAM tile residency (upload decoded tiles)** | **MOVE NOW** | Heart of the prototype; upload decoded tiles before SAT commit |
| Palette line handling | KEEP TEMPORARILY | Hardcoded PAL0, priority 1 in assembly; acceptable for prototype |
| SAT entry formation | MOVE NOW | Already in assembly commit; update to use real tile index |
| **SAT commit** | **MOVE NOW** | Already in assembly commit; update to use real VRAM tile index |
| Flipscreen | DEFER | Not implemented; acceptable prototype simplification |
| Animation/link/size fidelity | KEEP TEMPORARILY | Size stays 0x0500 (2×2); link stays sequential |
| Full palette correctness | DEFER | Not needed for prototype; PAL0 already loaded with visible colors |

---

## 4. Tile Decode / VRAM Ownership Model

### 4.1 Source of Tile Data

Arcade sprite tile patterns come from `rastan_pc090oj`, a `const u8[]` array embedded in the
Genesis ROM binary at link time. Size: 524288 bytes. Declared in `startup_bridge.c` and
referenced via `extern const u8 rastan_pc090oj[]`.

The Block-A producer at genesis 0x05A2B4 writes tile cell indices into word2 of each
descriptor at `0xE0FF11FE`. The index is used as `cell = word2 & 0x3FFF`.

The physical ROM bytes for cell N start at `rastan_pc090oj + (N * 128)`.

### 4.2 Decode Format

Each PC090OJ cell is 128 bytes representing a 16×16 pixel sprite cell:
- 16 rows, each row is 8 bytes
- Each byte holds 2 pixels (high nibble = left pixel, low nibble = right pixel)
- One cell = 16×16 pixels = 4 Genesis 8×8 tiles arranged in a 2×2 grid

`frontend_decode_pc090oj_cell(u16 code, u32 *dst_tiles)` performs this split:
- Rows 0–7 → tile-left (top-left 8×8) and tile-right (top-right 8×8)
- Rows 8–15 → tile-bottom-left and tile-bottom-right

Each output Genesis tile: 32 bytes, 4bpp packed (already in Genesis VDP 4bpp format).
No bit-reversal or byte-swap needed; the source nibble order matches Genesis VDP layout.

### 4.3 VRAM Destination

Reserved for the prototype sprite tile region: **VRAM tile indices 1024–1279** (256 tiles,
= 64 cells × 4 tiles each = covering 64 unique sprite cells per frame).

- VRAM tile 1024 = VRAM byte address `1024 × 32 = 0x8000`
- VRAM tile 1279 = VRAM byte address `1279 × 32 = 0x9FE0`
- Region size: 256 tiles × 32 bytes = 8192 bytes = 0x2000 bytes
- SAT at 0xF800, planes at 0xC000 and 0xE000 — 0x8000–0x9FFF is free for sprites
- `FRONTEND_RUNTIME_SPRITE_TILE_BASE = 1024` is already defined in main.c and used by
  `frontend_runtime_tile_for_code()`. This constant must be reused.

This region is dedicated to the prototype. No text tiles, no tilemap tiles, no other assets
share this range during the prototype phase.

### 4.4 Residency Policy

**Per-frame flat scan with no eviction cache.**

On each vblank, before `genesistan_sprite_commit_asm()`:
1. Scan all 18 Block-A entries at `0xE0FF11FE`
2. For each non-sentinel entry, extract `code = word2 & 0x3FFF`
3. Decode and upload unique codes only (dedup within this frame's scan)
4. Upload to VRAM starting at `FRONTEND_RUNTIME_SPRITE_TILE_BASE + (slot * 4)` where `slot`
   is the sequential index of this unique code in the current frame's scan (0, 1, 2, ...)
5. Record: `decode_result[slot] = { code, vram_tile_index }` in a local frame buffer

This is the simplest viable residency policy for a prototype. It is:
- Correct: VRAM has the tile data for every code present in Block-A before SAT commit
- Bounded: 18 entries, at most 18 unique codes, 18 × 4 = 72 tiles, well within the 256-tile region
- No inter-frame state: the table is rebuilt from Block-A every vblank (idempotent)
- No LRU, no eviction, no cache clock

The `frontend_runtime_sprite_tile_buffer` WRAM buffer already reserved in `wram_overlay.launcher`
(64 entries × 4 tiles × 8 words = 2048 words) is the decode destination before DMA upload.
`frontend_runtime_sprite_codes[64]` tracks which codes are loaded in which slots (already exists).

### 4.5 SAT Tile Index Formula

Block-A word2 carries arcade cell index `code = word2 & 0x3FFF`.

Mapping:
```
slot = index_of(code) within current frame's unique code list
vram_tile_index = FRONTEND_RUNTIME_SPRITE_TILE_BASE + (slot * 4)
```

For the assembly commit, the tile index must be communicated from the C prepare step to the
assembly commit. Mechanism: a small WRAM lookup table populated by the C prepare step before
`genesistan_sprite_commit_asm()` fires.

**Lookup table layout:**
- Array of 18 entries: `uint16_t genesistan_sprite_tile_lut[18]`
- Index N corresponds to Block-A entry N at `0xE0FF11FE + (N * 8)`
- Value: the VRAM tile index to use in SAT word2 for that entry
- Entries that are sentinels (zero-tuple or 0x0180) get value 0 (assembly will skip them anyway)
- Declared in `startup_bridge.c` in `.bss.patcher`; exported as `genesistan_sprite_tile_lut`

The assembly commit reads `genesistan_sprite_tile_lut[N]` as the tile index for Block-A entry N,
builds SAT word2 as `(vram_tile_index & 0x07FF) | 0x8000` (priority bit on, palette 0,
no flip — same as current hardcoded path but with real tile index instead of 1).

This keeps tile decode in C (where `frontend_decode_pc090oj_cell` already lives) and
index consumption in assembly (where the SAT commit loop already lives).

---

## 5. Arcade VBlank-Owned Flow

After the prototype is implemented, the ordered execution sequence every vblank:

```
genesistan_frontend_live_vint_handoff():
  Guard: frontend_live_handoff_active == TRUE AND current_screen == SCREEN_FRONTEND_LIVE

  1. genesistan_refresh_arcade_inputs()
     - updates input shadow for arcade input polling path

  2. genesistan_run_original_frontend_tick()
     - runs arcade level-5 handler natively at 0x03A208 (genesis offset 0x200)
     - Block-A producer at 0x03AAEC (JSR 0x05A174) fills 0xE0FF11FE with 18 fresh entries
     - Returns after arcade RTE

  3. genesistan_sprite_tile_prepare()        [NEW — C function]
     - Scans Block-A at 0xE0FF11FE (18 entries)
     - For each non-sentinel entry: decode `code = word2 & 0x3FFF`
     - Calls frontend_decode_pc090oj_cell(code, &decode_buf[slot*4*8]) for each unique code
     - After all unique codes decoded: DMA upload decode_buf → VRAM at FRONTEND_RUNTIME_SPRITE_TILE_BASE
     - Populates genesistan_sprite_tile_lut[18]: each entry N gets the VRAM tile index for
       the code found at Block-A entry N (sentinel entries → 0)
     - Called from vblank handoff; interrupts disabled during DMA upload

  4. genesistan_sprite_commit_asm()          [MODIFIED — assembly]
     - Sets VDP write address to VRAM 0xF800 via control port
     - Iterates Block-A at 0xE0FF11FE (18 entries)
     - Per entry: skip if word1 == 0x0180
     - Loads genesistan_sprite_tile_lut[N] for entry N → real VRAM tile index
     - Builds SAT word2: (tile_index & 0x07FF) | 0x8000
     - Writes 4 words (Y, size/link, tile_attr, X) to VDP data port at 0xC00000
     - No DMA; direct CPU writes to VDP port

  return
```

Step 3 runs in C because `frontend_decode_pc090oj_cell()` is a C function that reads from
`rastan_pc090oj` (ROM-resident) and writes to a decode buffer, then DMA-loads via `VDP_loadTileData`.
Putting decode logic in assembly would require rewriting the 4-tile decode and DMA in 68000
assembly, which adds risk with no prototype benefit. The C path is the correct call site.

Step 4 in assembly reads the LUT and builds SAT — assembly already owns this step.

---

## 6. Implementation Boundary

### Files that GAIN responsibility

**`apps/rastan/src/main.c`**:
- New function `genesistan_sprite_tile_prepare()` added (in `.text.patcher` section or nearby)
- This function: scans Block-A 18 entries, decodes unique PC090OJ cells via
  `frontend_decode_pc090oj_cell()`, DMA-uploads to `FRONTEND_RUNTIME_SPRITE_TILE_BASE`,
  writes `genesistan_sprite_tile_lut[18]`
- Called from `genesistan_frontend_live_vint_handoff()` BEFORE `genesistan_sprite_commit_asm()`
- Declaration: `void genesistan_sprite_tile_prepare(void);`

**`apps/rastan/src/startup_bridge.c`**:
- New exported variable: `uint16_t genesistan_sprite_tile_lut[18]` in `.bss.patcher`
- This is the per-frame tile index LUT populated by the C prepare step and read by assembly

**`apps/rastan/src/startup_trampoline.s`**:
- Modify `genesistan_sprite_commit_asm`: replace `move.w #0x8001, %d1` hardcode with:
  - Load `genesistan_sprite_tile_lut` base into a register before the loop
  - On each iteration N: load `lut[N]` as the tile index
  - Build SAT word2: `(tile_index & 0x07FF) | 0x8000` (mask to 11-bit index, set priority)
  - Write to VDP data port as `%d1` (same register, same write site — `move.w %d1, (%a2)`)

**`apps/rastan/inc/main.h`** (or equivalent header):
- Extern declaration: `extern uint16_t genesistan_sprite_tile_lut[18];`

### Files that LOSE responsibility

**`apps/rastan/src/main.c`**:
- `genesistan_render_sprites_vdp()` remains dead code in the file; still NOT called from the
  vblank handoff (it was removed from that path in the non-C sprite commit slice)
- No new callers of `genesistan_render_sprites_vdp()` are added

### Files left UNTOUCHED

- All `specs/` JSON patch files — no changes
- Block-A producer (0x05A2B4) — unchanged
- Block-A WRAM (0xE0FF11FE) — unchanged
- Exception handlers (`z_qr_exception.c`, `z_qr_exception_handlers.s`) — unchanged
- `startup_bridge.c` VDP layout, tile cache arrays for text tiles — unchanged
- SGDK initialization code — unchanged
- Tilemap/scroll/palette code — unchanged
- `genesistan_tile_cache_arcade[]`, `genesistan_tile_cache_lru[]` — unchanged (text tile cache)
- `genesistan_render_sprites_vdp()` function body — left in place, still dead code

---

## 7. Temporary Prototype Limitations

These simplifications are accepted for the prototype. Each is annotated with the eventual fix.

| Limitation | Status | Future fix |
|---|---|---|
| Fixed sprite size 2×2 (16×16 pixels) for all entries | ACCEPTED | Decode word0 size bits |
| Fixed palette PAL0 for all entries | ACCEPTED | Decode word0 palette field |
| No flipscreen correction | ACCEPTED | Read `genesistan_arcade_workram_words[15]` |
| Sequential link chain (N links to N+1, last=0) | ACCEPTED | True link chain from descriptor |
| No per-frame animation cycling beyond what Block-A provides | ACCEPTED | Tile code changes per Block-A update automatically |
| No zero-tuple all-zero skip in assembly (only 0x0180 skip) | ACCEPTED | Add all-zero check to commit loop |
| Tile LUT rebuilt every frame (no cross-frame caching) | ACCEPTED | LRU cache for steady-state |
| No Block-B entries (0xE0FF01BC, 4 entries) processed for tile prep | ACCEPTED | Add Block-B scan to prepare step |

---

## 8. Success Criteria

Numbered, testable, measurable:

1. `genesistan_sprite_tile_prepare()` is called every vblank in `genesistan_frontend_live_vint_handoff()`,
   immediately before `genesistan_sprite_commit_asm()`. Static code check in main.c.

2. VRAM tile region 1024–1027 (bytes 0x8000–0x807F) contains non-zero, non-uniform data at
   frame 700. `vdp.spaces['videoram']:read_u16(0x8000)` returns a value that is neither
   `0x0000` nor `0x1111`. This proves real decoded arcade pixels are in VRAM, not the test pattern.

3. VRAM tile 1 (bytes 0x0020–0x003F) is irrelevant — `read_u16(0x0020)` is no longer the
   source of sprite pixels. SAT entries do NOT reference tile index 1 anymore.

4. SAT entry 0 at 0xF800 has tile_attr word (third word, at 0xF804) NOT equal to `0x8001`.
   It must equal `(FRONTEND_RUNTIME_SPRITE_TILE_BASE & 0x07FF) | 0x8000` = `0x8400` for
   slot 0 (tile code 0x03CA maps to VRAM tile 1024 = 0x0400, with priority bit = 0x8400).

5. `genesistan_sprite_tile_lut[0]` at runtime equals `FRONTEND_RUNTIME_SPRITE_TILE_BASE`
   (= 1024 = 0x0400). Measurable via WRAM probe at the LUT address.

6. Visible sprite output appears with recognizable pixel content (not solid color blocks, not
   invisible). Frame 700 capture shows pixels consistent with the Rastan title logo or sprite
   shapes. Visual classification must be PASS (sprite pixels visible with non-uniform content).

7. `genesistan_render_sprites_vdp()` is NOT called from the live vblank path. Static code check.

8. Both `genesistan_sprite_tile_prepare()` and `genesistan_sprite_commit_asm()` run under
   arcade-vblank-owned control: `HIT genesistan_sprite_tile_prepare == HIT 03A208` (±2 for
   frame boundary effects) at the ~791-vblank mark.

---

## 9. Out-of-Scope Items

Cody MUST NOT touch any of the following:

- One-sprite or title-logo-specific handling — prototype applies to all 18 Block-A entries uniformly
- PC080SN background/tilemap conversion — planes, text shadow, DMA C
- Final palette correctness — palette line decoding, `frontend_palette_line_for_bank`, CRAM calibration
- Final animation fidelity — frame cycling, animation state beyond Block-A content
- Final flipscreen fidelity — no transform applied
- Final sprite size decoding — all entries treated as 2×2 (16×16); word0 size bits not decoded
- Text/background system redesign — `genesistan_hook_text_writer_3bb48_impl` and associated path unchanged
- Scroll system — `genesistan_scroll_from_workram_vdp`, VSRAM updates
- `genesistan_tile_cache_arcade[]` / `genesistan_tile_cache_lru[]` — text tile cache unchanged
- Block-B sprite descriptors (0xE0FF01BC, 4 entries) — tile prepare only handles Block-A in prototype
- `genesistan_render_sprites_vdp()` function body deletion — leave dead code in place
- ROM/spec JSON file changes — no `specs/` changes
- Exception handler code — `z_qr_exception.c`, `z_qr_exception_handlers.s` untouched
- `startup_bridge.c` structure beyond adding `genesistan_sprite_tile_lut[18]`
- SGDK initialization, VDP layout setup

---

## 10. Rainbow Islands / Cadash Sanity Check

Both Rainbow Islands and Cadash confirm that tiles must be in VRAM before SAT entries reference
them — this is a fundamental ordering constraint of the Genesis VDP, which consumes SAT and tile
data simultaneously at scan time. Rainbow Islands stages sprite descriptors in WRAM buffers
around `0xFFFB00` and pushes to VDP via DMA sequences driven from interrupt-owned timing; the
tile data upload necessarily precedes the SAT DMA in that flow. Cadash similarly drives
script/descriptor emission through VDP data port sequences that are called after tiles are
known resident. Both games handle tile residency as a pre-SAT-commit step, matching the
structure of the chosen prototype path (Option A: prepare tiles, then commit SAT). The chosen
approach — scan Block-A for unique codes, decode via `frontend_decode_pc090oj_cell()`, DMA
upload to a fixed VRAM region, then run SAT commit with real indices — directly parallels the
producer-then-commit ownership discipline confirmed in both Taito Genesis ports.

---

## 11. Final Recommendation

The prototype path is Option A: per-vblank flat scan of Block-A, decode unique PC090OJ cells
via the existing `frontend_decode_pc090oj_cell()` function, DMA upload to the reserved VRAM
region at tile 1024 (`FRONTEND_RUNTIME_SPRITE_TILE_BASE`), populate `genesistan_sprite_tile_lut[18]`,
then have `genesistan_sprite_commit_asm` read the LUT for real tile indices instead of the
current `#0x8001` hardcode. This is the minimal change set that replaces fake tile data with
real decoded arcade sprite pixels in VRAM and proves the full pipeline: Block-A → tile decode
→ VRAM upload → SAT commit → VDP scanline output.

The existing decode infrastructure (`frontend_decode_pc090oj_cell`, `frontend_runtime_sprite_tile_buffer`,
`FRONTEND_RUNTIME_SPRITE_TILE_BASE`, `VDP_loadTileData`) is already proven in the old C helper.
This prototype reuses all of it, removes the standalone C helper call from the vblank path, and
wires the decode output to the assembly commit through a new 18-entry LUT.

The next implementation step is a full prototype sprite execution path for the entire current Block-A stream, with real tile decode, VRAM ownership, SAT formation, and SAT commit under arcade-vblank-owned control.
