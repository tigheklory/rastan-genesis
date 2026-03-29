# Phase 1 Sprite Pipeline: Block-A → SAT → VDP Inside Arcade VBlank

## 1. Purpose

Define the minimal, complete implementation for Phase 1: converting Block-A sprite descriptors
to Genesis SAT entries and writing them to VDP VRAM, executing entirely inside the arcade
level-5 vblank handler. This document is the authoritative implementation specification for
Cody. No guessing is permitted; every value, address, and ordering constraint is explicit.

---

## 2. Insert Point (exact address, function, surrounding structure)

### Arcade VBlank Handler Chain

The arcade level-5 vblank handler enters at genesis ROM address `0x3A208` (relocated from
arcade `0x3A008`). The single `rte` is at genesis `0x3A27E` (relocated from arcade `0x3A07E`).

The C entry point that drives the arcade handler from the SGDK VInt callback is:

```
genesistan_frontend_live_vint_handoff()   [main.c line 1881]
  └─ genesistan_run_original_frontend_tick()   [startup_trampoline.s line 68]
       └─ jmp (0x03A008 + 0x200)   = jmp 0x03A208 [trampoline line 74]
            └─ arcade level-5 handler executes natively
            └─ returns to genesistan_frontend_tick_return [trampoline line 76]
       └─ rts back to genesistan_frontend_live_vint_handoff
```

The arcade handler runs natively on the Genesis 68000. Control returns to C code at
`genesistan_frontend_tick_return` (trampoline line 76) after the arcade `rte`.

### Current Sequence Inside the Arcade Handler (title state=1, substate=0)

From the vblank architecture plan, the sequence that matters for Phase 1:

| Address (genesis ROM) | Action |
|-----------------------|--------|
| 0x03A208 | Interrupt mask `oriw #0x0F00, sr` |
| ~0x03A40C | `movew d0, 0x3C0000` hardware sync latch (harmless on Genesis — no chip present) |
| 0x03A228 | `bsrw` → scroll sync |
| 0x03A23E | `bsrw` → frame counter |
| 0x03A242 | `bsrw` → bookkeeping |
| 0x03A246 | `bsrw` → input polling |
| 0x03A24A | `bsrw` → sound timing A |
| 0x03A24E | `bsrw` → sound timing B |
| 0x03A26A | `jmp a0@` → per-state dispatch → state=1 → title handler → substate=0 handler |
| **0x03AAEC** | **JSR 0x05A174 — block-A builder (producer) fires here** |
| **0x03AAF2** | **JSR 0x202B80 — genesistan_render_sprites_vdp_bridge (renderer) fires here** |
| (returns from dispatch) | |
| 0x03A274 | `jsr 0x55CA2` post-dispatch cleanup |
| 0x03A27A | `andiw #-3841, sr` interrupt restore |
| 0x03A27E | `rte` |

### INSERT POINT

The SAT pipeline executes AFTER `0x03AAEC` (producer) AND AFTER `0x03AAF2` (renderer call),
and BEFORE `0x03A274` (post-dispatch cleanup `jsr 0x55CA2`).

**The renderer call at `0x03AAF2` IS the insert point.** The renderer bridge
(`genesistan_render_sprites_vdp_bridge` at `0x202B80`) calls `genesistan_render_sprites_vdp()`
which contains the entire Block-A → SAT → VDP pipeline. No new hook insertion is needed.

**There is no new hook to add for Phase 1.** The pipeline already runs inside the arcade
vblank via this chain:

```
0x03AAEC: JSR 0x05A174    ← producer: block-A builder fills 0xE0FF11FE
0x03AAF2: JSR 0x202B80    ← renderer bridge
    movem.l d0-d7/a0-a6, -(sp)
    JSR genesistan_render_sprites_vdp    ← reads Block-A, builds SAT, DMA to VDP
    movem.l (sp)+, d0-d7/a0-a6
    RTS
(dispatch returns)
0x03A274: jsr 0x55CA2    post-dispatch cleanup
0x03A27E: rte
```

**Confirmation of correct call ordering (ORDER FIX PATCH B):**
Manifest entry `arcade_pc=0x03A8E4` / `rom_pc=0x03AAF2` confirms:
- `0x03AAEC`: JSR `0x05A174` = producer (block-A builder) — runs FIRST
- `0x03AAF2`: JSR `0x202B80` = renderer bridge — runs SECOND

This is the correct order. Producer populates Block-A, then renderer reads it.

---

## 3. Block-A Processing (iteration, termination, validity check)

### Source Buffers

The renderer iterates two WRAM descriptor blocks, defined in `sprite_blocks[]` at
`main.c` line 1549:

| Block | WRAM Byte Offset | Base WRAM Address | Entry Count |
|-------|-----------------|-------------------|-------------|
| A | `0x11B2` | `0xE0FF11FE` | 18 entries |
| B | `0x0170` | `0xE0FF01BC` | 4 entries |

Total entries scanned per frame: **22** (18 + 4). Genesis SAT limit is 80; 22 entries is
always within budget.

### Entry Format (8 bytes = 4 words per entry, big-endian)

| Byte offset | Word | Field | Content |
|-------------|------|-------|---------|
| +0, +1 | word0 | attr/flags | Palette bits [3:0], flipy [15], flipx [14], other attr |
| +2, +3 | word1 | y_raw | Raw Y coordinate; `0x0180` = off-screen sentinel |
| +4, +5 | word2 | tile code | `& 0x3FFF` = arcade tile index (15-bit mask applied) |
| +6, +7 | word3 | x_raw | Raw X coordinate |

### Iteration

Sequential scan from entry index 0 to count-1 for each block. Entries are packed contiguously
at 8 bytes each. No stride, no skip index, no linked-list walk needed.

**Termination**: Fixed count per block. Always scan all entries; use per-entry validity checks
to determine which entries emit SAT output.

### Validity Check Rules (per entry, evaluated in this order)

**Rule 1 — All-zero tuple skip:**
```
if ((word0 == 0) && (word1 == 0) && (word2 == 0) && (word3 == 0)) → SKIP
```
An all-zero entry is an unfilled slot. `word0==0` alone is NOT sufficient to skip — the block-A
builder writes `word0=0x0000` as the authentic arcade attr value for all logo sprites.

**Rule 2 — Off-screen Y sentinel:**
```
if (word1 == 0x0180) → SKIP (force y_raw = 0x0180 sets this explicitly as hidden)
```
Actually implemented as: `if all-zero → y_raw = 0x0180`, then later out-of-bounds check
catches it. The effect is the same.

**Rule 3 — Tile unavailable:**
```
if (tile_base < 0) → SKIP (tile_cache lookup failed; tile not loaded in VRAM)
```
`tile_base = frontend_runtime_tile_for_code(code, &unique_count)` returns -1 if tile loading
fails. Continue to next entry.

**Rule 4 — Final screen position out of bounds:**
```
if ((x <= -16) || (x >= 320) || (y <= -16) || (y >= 256)) → SKIP
```
Applied after sign extension and flipscreen transform.

---

## 4. SAT Mapping (exact field-by-field mapping table)

### Input → Output Mapping

| Genesis SAT Word | Field | Source field | Formula |
|-----------------|-------|--------------|---------|
| SAT.word0 | Y position (9-bit signed, +128 bias) | `block_a.word1` (`y_raw`) | `y = (s16)(y_raw & 0x01FF)`; if `y > 0x0140`, `y -= 0x0200`; pass raw `y` to `VDP_setSpriteFull` (SGDK adds +128) |
| SAT.word1 | size[1:0] width, size[1:0] height, link[6:0] | computed | size = `SPRITE_SIZE(2, 2)` (Phase 1 fixed); link = next sprite_count, or 0 for last |
| SAT.word2 | tile_attr: priority[15], palette[14:13], flipV[12], flipH[11], tile_index[10:0] | `block_a.word2` + computed | `TILE_ATTR_FULL(palette_line, TRUE, flipy, flipx, tile_base)` |
| SAT.word3 | X position (9-bit signed, +128 bias) | `block_a.word3` (`x_raw`) | `x = (s16)(x_raw & 0x01FF)`; if `x > 0x0140`, `x -= 0x0200`; pass raw `x` to `VDP_setSpriteFull` |

### Y Coordinate Detail

- `y_raw` is the raw value from `block_a.word1`.
- Apply 9-bit sign extension: `y = (s16)(y_raw & 0x01FF); if (y > 0x0140) y -= 0x0200;`
- Pass this `y` to `VDP_setSpriteFull(idx, x, y, ...)`. SGDK internally stores `y + 128`.
- Confirmed example: `word1=0x00E8` → `y = 0x00E8 = 232` → SAT Y = `232 + 128 = 360 = 0x0168`.
- Flipscreen: `y = (s16)(256 - y - 16); flipy = !flipy;`

### X Coordinate Detail

- `x_raw` is the raw value from `block_a.word3`.
- Apply 9-bit sign extension: `x = (s16)(x_raw & 0x01FF); if (x > 0x0140) x -= 0x0200;`
- Pass this `x` to `VDP_setSpriteFull(idx, x, y, ...)`. SGDK internally stores `x + 128`.
- Confirmed example: `word3=0x0010` → `x = 0x0010 = 16` → SAT X = `16 + 128 = 144 = 0x0090`.
- Flipscreen: `x = (s16)(320 - x - 16); flipx = !flipx;`

### Flip Bits

- `flipy = (word0 & 0x8000) != 0` — bit 15 of attr word
- `flipx = (word0 & 0x4000) != 0` — bit 14 of attr word

### Palette Line

- `sprite_ctrl = genesistan_arcade_workram_words[10]` (A5@(0x14) = A5@20)
- `sprite_colbank = (u16)((sprite_ctrl & 0x00E0) >> 1)`
- `color = (u16)((word0 & 0x000F) | sprite_colbank)`
- `palette_line = frontend_palette_line_for_bank(color >> 4, palette_bank_map, &palette_bank_count)`
- **Phase 1 known limitation**: Palette correctness depends on Phase 3 CRAM calibration.

### Tile Index

- `code = word2 & 0x3FFF`
- `tile_base = frontend_runtime_tile_for_code(code, &unique_count)`
- This loads the tile from `rastan_pc090oj` ROM array into VRAM if not already cached.
- Returns VRAM tile slot index (≥ 0) on success, or -1 on failure → SKIP entry.

### Sprite Size (Phase 1 Fixed Assumption)

- **All entries: `SPRITE_SIZE(2, 2)` = 2 tiles wide × 2 tiles high = 16×16 pixels.**
- This is a Phase 1 temporary assumption. Actual arcade sprite sizes are not decoded yet.
- Correct size decoding from the sprite descriptor chain is Phase 2+ work.

### Link Field

- `link = (sprite_count >= (SAT_MAX_SIZE - 1)) ? 0 : (u16)(sprite_count + 1)`
- `SAT_MAX_SIZE = 80` (`FRONTEND_RUNTIME_MAX_SPRITES`, `main.c` line 37)
- Link = 0 terminates the chain; the last emitted sprite always has link = 0.

---

## 5. SAT Buffer (location, size, layout)

### Existing Buffer — SGDK vdpSpriteCache

**Do NOT declare a new SAT buffer.** The SAT staging buffer is SGDK's internal `vdpSpriteCache`.

| Property | Value |
|----------|-------|
| Symbol | `vdpSpriteCache` |
| WRAM address | `0xE0FF6DF0` (from `symbol.txt`) |
| Managed by | SGDK: `VDP_setSpriteFull()` writes entries; `VDP_updateSprites()` DMA-uploads to VDP |
| Max entries | 80 (`SAT_MAX_SIZE`) |
| Entry size | 8 bytes (4 words: Y, size+link, tile_attr, X) |
| Total active data | 80 × 8 = 640 bytes |
| VDP VRAM target | `0xF800` (`TITLE_SAT_VRAM_ADDR`, `main.c` line 1290) |

### VDP SAT VRAM Address Confirmation

`VDP_setSpriteListAddress(TITLE_SAT_VRAM_ADDR)` is called in `genesistan_sync_title_vdp_layout()`
at `main.c` line 1401. This configures the VDP sprite table base to `0xF800` before the
vblank pipeline ever fires.

---

## 6. VDP Write (method, address, sequence)

### Method: DMA via SGDK VDP_updateSprites

The existing renderer uses DMA for the SAT upload:

```c
VDP_updateSprites(sprite_count, DMA);   // main.c line 1653
VDP_waitDMACompletion();                // main.c line 1654
```

**Phase 1 uses this exact method. Do not change it.**

The DMA transfers `sprite_count × 8 bytes` from `vdpSpriteCache` to VDP VRAM at `0xF800`.
Maximum transfer for Phase 1 is 22 entries × 8 bytes = 176 bytes (well within vblank budget).

### Full Sequence Inside `genesistan_render_sprites_vdp()`

1. `memset(frontend_runtime_sprite_tile_buffer, 0, sizeof(...))` — clear tile staging
2. For each block in `sprite_blocks[]` (block A: 18 entries, block B: 4 entries):
   a. Read 8-byte entry from WRAM base + offset
   b. Extract word0 (attr), word1 (y_raw), word2 (code), word3 (x_raw)
   c. Apply Rule 1: all-zero → set `y_raw = 0x0180` (effectively forces skip via bounds check)
   d. Sign-extend y: `if (y_raw & 0x01FF) > 0x0140, y -= 0x0200`
   e. Look up tile VRAM slot: `tile_base = frontend_runtime_tile_for_code(code, &unique_count)`
   f. Apply Rule 3: `if (tile_base < 0) continue`
   g. Sign-extend x: `if (x_raw & 0x01FF) > 0x0140, x -= 0x0200`
   h. Apply flipscreen transform (if `workram_words[15] != 0`)
   i. Apply Rule 4: bounds check, `continue` if out of range
   j. Compute `tile_attr = TILE_ATTR_FULL(palette_line, TRUE, flipy, flipx, tile_base)`
   k. `SYS_disableInts()` → `VDP_setSpriteFull(sprite_count, x, y, SPRITE_SIZE(2,2), tile_attr, link)` → `SYS_enableInts()`
   l. Increment `sprite_count`; break if `>= SAT_MAX_SIZE`
3. If `unique_count > 0`:
   - `VDP_loadTileData(frontend_runtime_sprite_tile_buffer, FRONTEND_RUNTIME_SPRITE_TILE_BASE, unique_count * 4, DMA)`
   - `VDP_waitDMACompletion()`
4. `refresh_frontend_sprite_palettes(palette_bank_map, palette_bank_count)`
5. `VDP_updateSprites(sprite_count, DMA)` — **SAT DMA to VDP VRAM 0xF800**
6. `VDP_waitDMACompletion()`

---

## 7. Execution Flow (ordered steps inside vblank)

```
STEP 1  SGDK V-Int fires
        → genesistan_frontend_live_vint_handoff() [main.c:1881]
          Guard: frontend_live_handoff_active == TRUE
                 AND current_screen == SCREEN_FRONTEND_LIVE

STEP 2  → genesistan_refresh_arcade_inputs()
          Updates input shadow so arcade input polling reads current joypad state

STEP 3  → genesistan_run_original_frontend_tick() [startup_trampoline.s:68]
          lea genesistan_arcade_workram_words, a5   (A5 = 0xE0FF004C)
          push fake SR + genesistan_frontend_tick_return as return address
          jmp 0x03A208   (arcade level-5 handler entry)

STEP 4    ARCADE HANDLER (runs natively):
          oriw #0x0F00, sr          interrupt mask
          (hardware latch — harmless)
          bsrw → frame counter
          bsrw → bookkeeping
          bsrw → input polling
          bsrw → sound timing A/B
          jmp a0@ → per-state dispatch → state=1 → title handler → substate=0

STEP 5    0x03AAEC: JSR 0x05A174   PRODUCER — block-A builder runs
          Entry: arcade 0x05A098, genesis 0x05A2B4 (post-Phase-2 shift)
          Preamble: A0 = 0xE0FF11FE, D2 = 0x0010, D3 = 0x00E8
          Writes 18 × 4-word entries to block-A at 0xE0FF11FE..0xE0FF123E
          Confirmed output: word0=0x0000, word1=0x00E8, word2=0x03CA, word3=0x0010
          RTS → returns to dispatch path

STEP 6    0x03AAF2: JSR 0x202B80   RENDERER BRIDGE
          genesistan_render_sprites_vdp_bridge:
            movem.l d0-d7/a0-a6, -(sp)   saves full register state
            JSR genesistan_render_sprites_vdp

STEP 7      genesistan_render_sprites_vdp() [main.c:1538]:
            Reads block-A (18 entries at 0xE0FF11FE)
            Reads block-B (4 entries at 0xE0FF01BC)
            Per-entry: validity checks → flip decode → tile lookup → VDP_setSpriteFull
            DMA tile data → VRAM (if unique_count > 0)
            refresh_frontend_sprite_palettes()
            VDP_updateSprites(sprite_count, DMA) → SAT DMA → VRAM 0xF800
            VDP_waitDMACompletion()
            returns

STEP 8    bridge restores d0-d7/a0-a6, RTS → dispatch path returns

STEP 9    ARCADE HANDLER continues:
          0x03A274: jsr 0x55CA2   post-dispatch cleanup
          0x03A27A: andiw #-3841, sr   interrupt restore
          0x03A27E: rte

STEP 10   genesistan_frontend_tick_return [trampoline:76]
          move.l a0, genesistan_arcade_last_a0   (capture)
          movem.l (sp)+, d0-d7/a0-a6
          RTS → back to genesistan_run_original_frontend_tick → RTS

STEP 11   genesistan_frontend_live_vint_handoff returns to SGDK VInt dispatch
```

**No new C hook, wrapper, or callback is required for Phase 1.**

---

## 8. Success Criteria (measurable checks)

### Check 1 — Block-A is populated (producer ran)

Tap at renderer entry `genesistan_render_sprites_vdp` (genesis `0x002005C4`).
Read WRAM at `0xE0FF11FE` through `0xE0FF124D` (18 entries = 144 bytes).

**Pass**: At least one of the 22 entries contains nonzero data.
**Expected specific value**: `word2` at `0xE0FF1202` = `0x03CA` (logo tile code).
**Fail**: All 144 bytes at `0xE0FF11FE..0xE0FF124D` are zero (builder did not run).

MAME Lua probe:
```lua
cpu:space(AS_PROGRAM):read_u16(0xE0FF1202)  -- expect 0x03CA
```

### Check 2 — SAT staging buffer has nonzero entries (renderer ran)

After `VDP_setSpriteFull` calls complete (tap at `VDP_updateSprites` callsite,
`main.c` line 1653), read `vdpSpriteCache` at WRAM `0xE0FF6DF0`.

**Pass**: `sprite_count > 0`; first 8 bytes at `0xE0FF6DF0` are nonzero.
**Fail**: All bytes at `0xE0FF6DF0..0xE0FF6DF7` are zero (`sprite_count` stayed 0).

### Check 3 — VDP VRAM 0xF800 contains SAT data (DMA ran)

In emulator VDP memory viewer, inspect VRAM at `0xF800` (SAT region) after one rendered frame.

**Pass**: VRAM `0xF800` word 0 (Y field) is nonzero.
**Expected value**: With `y=0x00E8=232`, SGDK stores `y+128=360=0x0168`. VRAM `0xF800` should
contain `0x0168` (high byte `0x01`, low byte `0x68`).
**Fail**: VRAM `0xF800..0xF807` all zero (DMA did not fire or DMA target is wrong).

### Check 4 — Visible sprite pixels on screen (visual)

Run in BlastEm or Exodus; observe title screen after launch.

**Pass**: Any nonzero pixel row appears in the sprite plane.
**Expected position**: logo sprite at approximately x=16, y=232 (screen coordinates).
**Acceptable partial pass**: Any sprite pixel visible anywhere on screen — confirms full
pipeline (Block-A → renderer → SAT → VDP) is operational end-to-end.
**Fail with known cause**: Checks 1–3 pass but no visible pixels. Indicates VRAM tile data
absent (Phase 2 limitation) or palette all-black (Phase 3 limitation). This is NOT a Phase 1
pipeline failure — it confirms the SAT path is correct.

---

## 9. Known Limitations (explicit list)

1. **Tile data may be absent or incorrect in VRAM.** `frontend_runtime_tile_for_code` loads
   from `rastan_pc090oj` ROM array. If the ROM array does not contain correct sprite tile
   data, VRAM slots will have garbage patterns or empty tiles. Correct tile population is
   Phase 2 work.

2. **Sprite size is fixed at 2×2 tiles (16×16 px) for all entries.** The block-A entry format
   does not encode sprite size. Actual arcade logo sprite sizes may differ. Correct size
   decoding is Phase 2+ work.

3. **Palette will likely be wrong.** `genesistan_palette_rom_table` is a greyscale placeholder
   (build 113). Sprites may appear in wrong colors or all-black. Correct palette conversion and
   CRAM upload is Phase 3 work.

4. **Link chain is sequential only.** Link values are `sprite_count + 1`, last entry = 0.
   This does not replicate any arcade-specific sprite ordering. Phase 2+ may re-examine.

5. **Flipscreen unvalidated.** The flipscreen path fires when `workram_words[15] != 0`. Whether
   this register is set correctly for the title screen state is not validated in Phase 1.

6. **Phase 2 spec patch required to activate.** The block-A builder will NOT fire until the
   `shift_replacements` entry at `arcade_pc=0x059F90` is changed from `4e75` to
   `4eb90005a0b44e75`. Without this patch, Block-A remains all-zero and no sprites appear.
   Phase 1 pipeline is structurally complete; the Phase 2 patch provides the data.

---

## 10. Implementation Notes for Cody (specific warnings and constraints)

### CRITICAL: Do NOT change the all-zero tuple guard

Current guard at `main.c` lines 1593–1595:
```c
if ((data == 0) && (y_raw == 0) && (code == 0) && (x_raw == 0))
    y_raw = 0x0180;
```
This is correct. The block-A builder writes `word0=0x0000` as authentic arcade attr data for
all logo sprites. Reverting to `if (data == 0)` alone would suppress every sprite.

### Do NOT add a new C hook function for Phase 1

`genesistan_render_sprites_vdp()` already contains the full pipeline. No new hook, callback,
or wrapper is needed.

### Do NOT move VDP_updateSprites out of genesistan_render_sprites_vdp for Phase 1

The architecture plan notes this refactor is desirable long-term. For Phase 1, the DMA call
stays inside `genesistan_render_sprites_vdp()` at `main.c` line 1653. Do not move it.

### Do NOT enable SYS_doVBlankProcess post-launch

The main loop guard ensures `SYS_doVBlankProcess` only runs when
`current_screen != SCREEN_FRONTEND_LIVE`. This must not be changed.

### The only change needed to activate Phase 1 is the Phase 2 spec patch

Patch spec file: `startup_common_rom_manifest.json` (or equivalent), entry
`arcade_pc=0x059F90`:
- Before: `"replacement_bytes": "4e75"`
- After: `"replacement_bytes": "4eb90005a0b44e75"`

Breakdown of replacement bytes:
- `4eb9` = JSR abs.l opcode
- `0005a0b4` = pre-compensated embedded address (patcher adds +0x200 → genesis target `0x05A2B4`)
- `4e75` = RTS (producer returns to caller)

No `.c` files, Makefile, or other spec entries need modification for Phase 1.

### Confirm FRONTEND_RUNTIME_SPRITE_TILE_BASE does not overlap TITLE_SAT_VRAM_ADDR

Sprite tiles are loaded to VRAM starting at `FRONTEND_RUNTIME_SPRITE_TILE_BASE`. Verify this
constant does not overlap the SAT region at `0xF800`. This is an existing constraint; Phase 1
does not change it, but the value must be confirmed correct before testing.

### Confirm genesistan_sync_title_vdp_layout() is called before first vblank fires

`VDP_setSpriteListAddress(TITLE_SAT_VRAM_ADDR)` must execute before the renderer's
`VDP_updateSprites` DMA fires. It is called in `genesistan_sync_title_vdp_layout()`
(`main.c` line 1401). Verify this function is called during launch before
`frontend_live_handoff_active = TRUE` is set.

---

Phase 1 defines a minimal Block-A to SAT pipeline inside arcade vblank, ready for direct implementation.
