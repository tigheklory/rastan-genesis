# Arcade VBlank → Genesis VDP Commit Architecture Plan

## 1. Purpose

This document defines the authoritative graphics architecture for Rastan Genesis, establishing
the arcade vblank interrupt as the single owner of frame timing and display commit. It documents
the complete pipeline from arcade vblank entry through Genesis VDP commit, identifies every
hardware-dependent behavior requiring replacement, and defines the ordered implementation phases.

This plan is grounded in verified research: the arcade vblank structure from
`rastan_vblank_and_vdp_buffer_architecture.md`, the title screen call inventory from
`title_screen_graphics_call_inventory.md`, the current codebase state in `main.c` and
`startup_bridge.c`, and confirmed runtime results from builds 271–278.

---

## 2. Core Direction (Arcade VBlank as Authoritative Frame Controller)

**The arcade vblank interrupt handler at 0x3A008 owns the frame.**

- It fires on Level 5 hardware interrupt (vector at ROM 0x74 = 0x0003A008).
- It masks all lower interrupts on entry, runs all per-frame logic, and returns via the single
  `rte` at 0x3A07E.
- All state-specific work, including graphics production, text dispatch, sprite production, and
  the post-dispatch cleanup, runs inside this handler via the dispatch table at 0x3A06C.
- There is no separate frame controller. The main thread initializes state; VBlank drives frames.

On Genesis:
- The arcade vblank handler is patched into the Genesis ROM and runs natively on the Genesis 68000.
- SGDK's VBlank callback (`SYS_doVBlankProcess`) is used only during the launcher/config phase.
- Once the arcade code launches (SCREEN_FRONTEND_LIVE), the arcade vblank owns display.
- No separate SGDK/C renderer path should own display after launch.

---

## 3. Arcade VBlank Structure: Entry Points, Phases, What It Controls

### Entry Point

| Address | Role |
|---------|------|
| 0x3A008 | Level 5 VBlank handler entry — all interrupt returns pass through 0x3A07E |

### Top-Level VBlank Flow (0x3A008)

| Address | Instruction | Phase | Controls |
|---------|-------------|-------|----------|
| 0x3A008 | `oriw #0x0F00, sr` | Interrupt mask | Prevents re-entrant VBlank |
| 0x3A00C | `clrw 0x350008` | Watchdog | Hardware watchdog clear (arcade only) |
| 0x3A012 | `movew d0, 0x3C0000` | Hardware sync | Coin/control hardware latch (arcade only) |
| 0x3A028 | `bsrw 0x3A126` | Scroll sync | States 2–4: scroll/DMA sync |
| 0x3A03E | `bsrw 0x3AB7C` | Frame counter | Frame counter / overflow watchdog |
| 0x3A042 | `bsrw 0x3ABE2` | Bookkeeping | Coin detect, BCD counter |
| 0x3A046 | `bsrw 0x3A0A8` | Input polling | Reads 0x390000 shadow |
| 0x3A04A | `bsrw 0x3EEFA` | Sound timing A | Writes to 0x380000 shadow |
| 0x3A04E | `bsrw 0x3EF5C` | Sound timing B | Same |
| 0x3A06A | `jmp a0@` | Per-state dispatch | All state-specific work via table at 0x3A06C |
| 0x3A074 | `jsr 0x55CA2` | Post-dispatch cleanup | Runs after all state-specific work |
| 0x3A07A | `andiw #-3841, sr` | Interrupt restore | Re-enables Level 1–6 |
| 0x3A07E | `rte` | Return | Only rte in ROM |

### Per-State Dispatch Table (at 0x3A06C)

| State | Handler | Role |
|-------|---------|------|
| 0 | 0x3A9FE | Attract/init state |
| 1 (title) | 0x3A8AC | Title screen VBlank handler |
| 2–4 | various | Gameplay states |

### Title State VBlank Handler (0x3A8AC, state=1)

Dispatches per substate via inner table at 0x3A8CE.

Substate 0 handler (0x3A8D2):
| Address | Call | Controls |
|---------|------|----------|
| 0x3A8D2 | `bsrw 0x3ADD8` | Display orientation → writes 0xC50000 (PC080SN control) |
| 0x3A8D6 | `bsrw 0x3AD4C` | Sprite RAM clear — fills 0xD00000 with off-screen sentinel 0x00000100 |
| 0x3A8DA | `bsrw 0x3AE5A` | Tile plane clear — fills 0xC00100/0xC08100 with 0x20 (space) + scroll/ctrl via 0x3B098 |
| 0x3A8DE | `bsrw 0x3B902` | Timing counter update |
| 0x3A8E4 | `jsr 0x59F5E` | Additional producer (title init) |
| 0x3A8EC | `bsrw 0x3BB48` | Text dispatch selector 9 (title text line) |
| 0x3A8FC | `bsrw 0x3BB48` | Text dispatch selector 10/11 |
| 0x3A900 | `jsr 0x5A410` | Additional title producer |

**Key finding**: Text producers (0x3BB48 dispatches) run INSIDE the VBlank handler. This is the
arcade's single-phase design: clear hardware RAM, then repopulate it in the same VBlank.

---

## 4. Hardware-Dependent Behavior Audit

### Keep / Replace Classification

| Behavior | Arcade Code | Arcade Hardware | Classification | Genesis Action |
|----------|-------------|-----------------|----------------|----------------|
| Interrupt mask | `oriw #0x0F00, sr` at 0x3A008 | 68000 SR | KEEP | Genesis 68000 uses same SR mask |
| Watchdog clear | `clrw 0x350008` | Taito watchdog chip | REMOVE | No Genesis watchdog |
| Hardware sync latch | `movew d0, 0x3C0000` | Coin/control chip | REMOVE | No Genesis equivalent |
| Conditional scroll sync (states 2–4) | `bsrw 0x3A126` | PC080SN scroll regs | ADAPT | Redirect to VDP VSRAM |
| Frame counter | `bsrw 0x3AB7C` | WRAM only | KEEP | Pure logic, no hardware dep |
| Per-frame bookkeeping | `bsrw 0x3ABE2` | WRAM + coin hardware | KEEP | Coin path already shadowed |
| Input polling | `bsrw 0x3A0A8` | 0x390000 I/O | KEEP | Already mapped to shadow |
| Sound timing A | `bsrw 0x3EEFA` | 0x380000 shadow | KEEP | Already mapped to shadow |
| Sound timing B | `bsrw 0x3EF5C` | 0x380000 shadow | KEEP | Already mapped to shadow |
| Per-state dispatch | `jmp a0@` at 0x3A06A | None (WRAM state) | KEEP EXACTLY | Core of arcade VBlank |
| Post-dispatch cleanup | `jsr 0x55CA2` | None | KEEP | Pure logic |
| Interrupt restore + rte | 0x3A07A/0x3A07E | 68000 SR | KEEP | Same on Genesis |
| Display orientation → 0xC50000 | `bsrw 0x3ADD8` | PC080SN ctrl reg | REPLACE | VDP register write (layer control) |
| Sprite RAM clear (0xD00000) | `bsrw 0x3AD4C` | PC090OJ D-Window | REPLACE | Fill `genesistan_shadow_d00000_words` with zero sentinel |
| Tile plane clear (0xC00100/0xC08100) | `bsrw 0x3AE5A` inner | PC080SN C-Window | REPLACE | Fill text shadow at 0xE0FFC84C with 0x0020 |
| Text producers (0x3BB48) | `bsrw 0x3BB48` in VBlank | PC080SN C-Window | ADAPT | Write to text shadow; existing `genesistan_hook_text_writer_3bb48_impl` |
| Scroll/control writes (0xC20000/C40000/C50000) | `jsr 0x200DC2` callsites | PC080SN chip | ADAPT | Already via `genesistan_scroll_from_workram_vdp`; VDP VSRAM/H-scroll |
| Sprite descriptor writes (0xD00000+) | producer paths | PC090OJ D-Window | ADAPT | Write to WRAM descriptor blocks; renderer reads these |
| SAT DMA to VDP | not present in arcade | N/A (arcade writes direct) | NEW (Genesis only) | DMA `genesistan_shadow_d00000_words` → VRAM 0xF800 every VBlank |
| Plane DMA to VDP | not present in arcade | N/A (arcade writes direct) | NEW (Genesis only) | DMA text shadow → VRAM plane A/B nametables every VBlank |

---

## 5. WRAM Graphics Buffer Definitions

All buffers reside in Genesis WRAM (0xE00000–0xFFFFFF range). Declared in `startup_bridge.c`.

### Buffer A — Sprite Descriptor Staging (`genesistan_shadow_d00000_words`)

- **Memory**: `volatile uint16_t genesistan_shadow_d00000_words[0x0400]` (section `.bss.patcher`)
- **Size**: 0x0400 words = 2KB; covers 80 Genesis SAT entries × 8 bytes = 640 bytes active
- **Entry format** (Genesis SAT, 8 bytes per entry):
  - word 0: Y position (9-bit, 1-based)
  - word 1: size (2-bit h×w) | link (7-bit next-entry index)
  - word 2: tile index (11-bit) + priority + palette + H/V flip
  - word 3: X position (9-bit, 1-based)
- **Producer**: `genesistan_render_sprites_vdp` (renderer at genesis 0x2005C4) builds SAT tuples
  from arcade descriptor blocks at WRAM offsets 0x11B2 (18 entries) and 0x0170 (4 entries).
  The block-A builder at genesis 0x05A2B4 (arcade 0x05A098) fills source blocks from animation state.
- **Consumer (VBlank)**: DMA B — `genesistan_shadow_d00000_words` → VDP VRAM 0xF800 every VBlank
- **Clear protocol**: Fill with zero sentinel at start of VBlank before producers run (replaces
  arcade `0x3AD4C` which cleared 0xD00000 with 0x00000100 off-screen sentinel)

### Buffer B — Text / Tilemap Shadow (`0xE0FFC84C` inside `genesistan_arcade_workram_words`)

- **Memory**: Offset within `genesistan_arcade_workram_words` at compile-time offset
  `TEXT_WRITER_SHADOW_PAGE2_OFFSET`; base `0xE0FFC84C` at runtime; 0x0800 words = 2KB
- **Entry format**: One word per cell = Genesis nametable cell:
  - bits 15:13 = priority (1) + palette line (2)
  - bits 12:11 = V flip, H flip
  - bits 10:0 = tile pattern index in VRAM
- **Producer**: `genesistan_hook_text_writer_3bb48_impl` dispatches selectors 9/10/11 etc.,
  resolving glyph codes to VRAM tile indices via `tile_cache_get` and writing cell words.
  Secondary producer `genesistan_hook_text_writer_3c3fe` handles 0x3C3FE path.
- **Consumer (VBlank)**: DMA C — text shadow → VDP plane A (VRAM 0xE000) and plane B (VRAM 0xC000)
- **Clear protocol**: Fill entire shadow with 0x0020 (space tile) before text producers run
  (replaces arcade `0x3AE64` clearing C-Window pages with 0x20)

### Buffer C — Palette / CRAM Source

- **Memory**: `const uint16_t genesistan_palette_rom_table[2048]` (section `.rodata_bin`)
- **Size**: 2048 entries × 2 bytes = 4096 bytes; pre-converted Genesis VDP color format
- **Entry format**: `0000 BBB0 GGG0 RRR0` (Genesis xBGR-444 with low bit zero)
- **Runtime capture**: `uint16_t genesistan_palette_clcs[2048]` (section `.bss.patcher`) holds
  runtime CLCS palette captures for live color correction
- **Producer**: Fixed at build time (post-build patcher). No per-frame updates unless scene changes.
  Runtime: `load_arcade_palette()` or `PAL_setColors()` with 64-entry slice on scene transition.
- **Consumer (VBlank)**: DMA D — scene-change triggered only; 64 words → VDP CRAM
- **Dirty flag**: palette-dirty flag gates CRAM upload; not re-uploaded every frame

### Buffer D — Tile Pattern Cache

- **Memory**:
  - `uint16_t genesistan_tile_cache_arcade[TILE_CACHE_SLOTS]` — arcade tile in each VRAM slot
  - `uint16_t genesistan_tile_cache_lru[TILE_CACHE_SLOTS]` — LRU counter per slot
  - `uint16_t genesistan_tile_cache_clock` — global LRU clock
  - Both in section `.bss.patcher`; 1164 slots total (slots 20–1023 + 1280–1439)
- **Source data**: `rastan_pc080sn` ROM array; 32 bytes per tile
- **Producer**: `tile_cache_get(arcade_code)` on every glyph/sprite lookup. On miss: evict LRU,
  DMA 32 bytes from ROM → VRAM slot (`VDP_loadTileData` + `VDP_waitDMACompletion`)
- **Consumer**: Referenced tile indices used in text shadow cell words and SAT entries
- **Ordering constraint**: All tile cache misses must resolve BEFORE SAT DMA and plane DMA

### Buffer E — Scroll / Control State

- **Memory**: Words within `genesistan_arcade_workram_words`:
  - 0xE0FF10AE (byte offset 0x10AE) = Plane A (FG) X scroll
  - 0xE0FF10B0 (byte offset 0x10B0) = Plane A (FG) Y scroll
  - 0xE0FF10EC (byte offset 0x10EC) = Plane B (BG) X scroll
  - 0xE0FF10EE (byte offset 0x10EE) = Plane B (BG) Y scroll
  - Shadow registers: `genesistan_shadow_c20000_words[2]`, `genesistan_shadow_c40000_words[2]`
- **Producer**: Arcade scroll writes to 0xC20000/0xC40000/0xC50000 are redirected to WRAM.
  The `jsr 0x200DC2` callsites in the title init path are already Genesis-native scroll publishers.
- **Consumer (VBlank)**: `genesistan_scroll_from_workram_vdp` reads WRAM scroll words and calls
  `VDP_setHorizontalScroll` / `VDP_setVerticalScroll` for both planes

---

## 6. Genesis VBlank Commit Phase: Ordered Sequence

The following ordered steps define the complete Genesis VBlank frame commit. Steps 1–3 and 13–14
are arcade code running natively. Steps 4–12 are Genesis-specific replacements inserted into
the arcade vblank's execution flow.

**Step 1 — Interrupt mask (KEEP)**
- `oriw #0x0F00, sr` at 0x3A008
- Prevents re-entrant VBlank; same behavior required on Genesis 68000

**Step 2 — Non-graphics housekeeping (KEEP, with hardware removals)**
- Remove: watchdog `clrw 0x350008` (no Genesis watchdog chip)
- Remove: hardware sync `movew d0, 0x3C0000` (no Genesis equivalent)
- Keep: frame counter `bsrw 0x3AB7C` — game logic depends on counter
- Keep: per-frame bookkeeping `bsrw 0x3ABE2` — coin detect, BCD counter
- Keep: input polling `bsrw 0x3A0A8` — reads 0x390000 shadow (already mapped)
- Keep: sound timing `bsrw 0x3EEFA` / `bsrw 0x3EF5C` — reads 0x380000 shadow (mapped)

**Step 3 — Per-state dispatch (KEEP EXACTLY)**
- `jmp a0@` via table at 0x3A06C
- Routes to state-specific handler; for title state=1 → 0x3A8AC → substate dispatch

**Step 4 — GENESIS: Palette publish (NEW — per scene change)**
- Triggered by palette-dirty flag set on scene transition
- Action: 64-word DMA from `genesistan_palette_rom_table` → VDP CRAM
- Must precede tile/sprite visibility to avoid miscolored first frame
- Implementation: `PAL_setColors(0, genesistan_palette_rom_table, 64, DMA)` + `VDP_waitDMACompletion()`

**Step 5 — Clear SAT staging buffer (REPLACE `0x3AD4C`)**
- Arcade: fills 0xD00000 with off-screen sentinel 0x00000100
- Genesis: fills `genesistan_shadow_d00000_words` with zero (Y=0 = off-screen sentinel, link chain clean)
- Must precede Step 7 (producer populates staging)

**Step 6 — Clear text/plane staging buffer (REPLACE `0x3AE64`)**
- Arcade: fills C-Window pages 0xC00100 and 0xC08100 with 0x20 (space character)
- Genesis: fills text shadow at 0xE0FFC84C with 0x0020 (space-cell, no attributes)
- Must precede Step 7 (text producers write active cells)

**Step 7 — Text producers execute (ADAPT `0x3BB48`)**
- Arcade: text producers (dispatched via 0x3BB48 with selectors 9, 10/11, 30, 32) write to PC080SN C-Window
- Genesis: `genesistan_hook_text_writer_3bb48_impl` intercepts these dispatches and writes to text shadow
- Tile cache resolves glyph indices; DMA A (cache miss tile upload) fires as needed
- Already implemented; no new work

**Step 8 — Logo/sprite descriptor producer (ADAPT `0x05A174`)**
- Arcade: producer fills PC090OJ descriptor RAM at 0xD00000
- Genesis: block-A builder at 0x05A2B4 fills WRAM descriptor blocks at 0xE0FF11B2 and 0xE0FF0170
- ORDERING: this producer must complete before Step 9 (renderer reads the descriptor blocks)
- Current bug (builds 271–278): in the 0x03AAB8 title init cluster, Step 9 (renderer 0x03AAEC)
  fires BEFORE Step 8 (producer 0x03AAF2). The producer/renderer call order must be swapped.

**Step 9 — GENESIS: Tile cache resolve for sprite tiles (NEW)**
- For each tile code in SAT staging entries: check tile cache; on miss, DMA tile from `rastan_pc080sn`
- Must complete before DMA B (SAT upload) so VRAM has sprite tile data before SAT entries reference it

**Step 10 — Sprite renderer: descriptor blocks → SAT staging (ADAPT `0x2005C4`)**
- Arcade: renderer writes descriptors to PC090OJ RAM
- Genesis: `genesistan_render_sprites_vdp` reads WRAM descriptor blocks, builds Genesis SAT tuples
  in `genesistan_shadow_d00000_words`, loads tile data to VRAM, updates palette if needed
- Currently implemented in main.c; already uses correct 4-word-null guard (Build 278)

**Step 11 — GENESIS: DMA B — SAT staging → VRAM (NEW)**
- DMA `genesistan_shadow_d00000_words` → VDP VRAM 0xF800 (SAT base, `TITLE_SAT_VRAM_ADDR`)
- Size: 80 entries × 8 bytes = 640 bytes = 320 words
- Implementation: `VDP_updateSprites(sprite_count, DMA)` + `VDP_waitDMACompletion()`
- Must follow Step 10 (SAT staging populated); must complete before active scan

**Step 12 — GENESIS: DMA C — text shadow → VDP planes (NEW)**
- Stream non-space cell rows from text shadow to VDP plane nametables:
  - Plane B (VRAM 0xC000 = `TITLE_PLANE_B_VRAM_ADDR`) for BG layer (PC080SN page 0)
  - Plane A (VRAM 0xE000 = `TITLE_PLANE_A_VRAM_ADDR`) for FG/text layer (PC080SN page 2)
- Optimization: dirty-row scan — only DMA rows containing non-space cells
- Must follow Step 7 (text producers complete); must complete before scan

**Step 12b — Scroll/control publish (ADAPT 0xC20000/C40000/C50000)**
- Arcade: per-frame scroll words written to PC080SN chip registers
- Genesis: `genesistan_scroll_from_workram_vdp` reads WRAM words → `VDP_setHorizontalScroll`
  / `VDP_setVerticalScroll` for both planes
- Already implemented; callsites via `jsr 0x200DC2` are Genesis-native
- Applied last: scroll repositions the view of data already committed to VRAM

**Step 13 — Post-dispatch cleanup (KEEP)**
- `jsr 0x55CA2` at 0x3A074

**Step 14 — Restore interrupt mask and RTE (KEEP)**
- `andiw #-3841, sr` at 0x3A07A
- `rte` at 0x3A07E

### Justification of Order

- Palette before tiles: avoids miscolored first frame
- Clear before produce: prevents prior-frame stale data from persisting (mirrors arcade discipline)
- Tiles before SAT/plane DMA: VRAM must have pattern data before SAT/nametable entries reference indices
- SAT DMA and plane DMA before scan: both must complete within VBlank window
- Scroll last: new scroll values take effect against already-resident VRAM data

---

## 7. Hardware Replacement Strategy

### Sprites

| Layer | Arcade | Genesis |
|-------|--------|---------|
| Producer writes | PC090OJ D-Window (0xD00000+) | WRAM blocks 0xE0FF11B2 / 0xE0FF0170 |
| Renderer reads | Same D-Window via descriptor indices | WRAM blocks → `genesistan_shadow_d00000_words` |
| Hardware output | PC090OJ drives scanline sprite circuit | VDP SAT at VRAM 0xF800 via DMA B |
| Clear pattern | Fill 0xD00000 with 0x00000100 per frame | Fill `genesistan_shadow_d00000_words` with 0 per frame |
| Tile source | PC090OJ sprite ROM (external chip) | `rastan_pc090oj` ROM array in Genesis ROM |

### Tilemaps

| Layer | Arcade | Genesis |
|-------|--------|---------|
| Cell writes | PC080SN C-Window (0xC00100/0xC08100) | Text shadow at 0xE0FFC84C |
| Clear pattern | Fill C-Window with 0x20 per frame | Fill shadow with 0x0020 per frame |
| Hardware output | PC080SN drives tile circuit | VDP plane nametables via DMA C |
| BG layer | Page 0 (0xC00000–0xC03FFF) | Plane B (VRAM 0xC000 = `TITLE_PLANE_B_VRAM_ADDR`) |
| FG/text layer | Page 2 (0xC08000–0xC0BFFF) | Plane A (VRAM 0xE000 = `TITLE_PLANE_A_VRAM_ADDR`) |
| Tile source | PC080SN tile ROM (external chip) | `rastan_pc080sn` ROM array in Genesis ROM |

### Scroll

| Layer | Arcade | Genesis |
|-------|--------|---------|
| Y scroll | `movew Dn, 0xC20000` | `VDP_setVerticalScroll(plane, value)` |
| X scroll | `movew Dn, 0xC40000` | `VDP_setHorizontalScroll(plane, value)` |
| Layer control | `movew Dn, 0xC50000` | VDP register writes (layer enable, flip mode) |
| Staging | WRAM words 0xE0FF10AE/10B0/10EC/10EE | Same WRAM words (no change needed) |
| Publisher | Direct chip write | `genesistan_scroll_from_workram_vdp` (already implemented) |

### Palette

| Layer | Arcade | Genesis |
|-------|--------|---------|
| Source | External palette RAM (Taito CLCS hardware) | `genesistan_palette_rom_table` (pre-converted, ROM) |
| Runtime capture | Hardware palette RAM reads | `genesistan_palette_clcs[2048]` WRAM capture |
| Commit | Always-live RAM writes (immediate) | DMA D: ROM/capture → VDP CRAM on scene change |
| Format | Taito xRGB-444 | Genesis `0000 BBB0 GGG0 RRR0` (pre-converted) |
| Trigger | Continuous (hardware) | palette-dirty flag on scene transition |

---

## 8. Implementation Order (Phases 1–5)

### Phase 1 — Sprite Pipeline: Block-A → SAT → VDP

**Input**: Block-A builder at 0x05A2B4 writing 8-byte descriptor tuples to WRAM blocks
          (confirmed: word0=0x0000, word1=0x00E8, word2=0x03CA, word3=0x0010 at build 278)

**Output**: Genesis SAT entries visible in VDP VRAM 0xF800; logo sprite pixels on screen

**Work**:
1. Fix producer/renderer call order in 0x03AAB8 title init cluster:
   - Swap 0x03AAEC (renderer `jsr 0x202B80`) and 0x03AAF2 (producer `jsr 0x05A174`)
   - Producer must fire before renderer in the init sequence
2. Confirm DMA B (SAT staging → VRAM 0xF800) fires inside arcade VBlank after renderer populates staging
3. Confirm tile cache resolve fires for logo tile codes before SAT DMA

**Verification**:
- `sprite_code0 != 0` in probe (logo tile index non-zero)
- `sat_writes > 0` in probe (SAT staging received tuples)
- Visual: logo sprite pixel row appears on screen

### Phase 2 — Tile Upload System: Tile Queue → DMA

**Input**: `tile_cache_get(arcade_code)` cache miss returns — arcade tile codes from text shadow
          and SAT descriptor entries

**Output**: VRAM tile slots populated with correct 8×8 pixel patterns from `rastan_pc080sn`

**Work**:
1. Verify tile cache DMA (`VDP_loadTileData` + `VDP_waitDMACompletion`) is ordered before
   SAT DMA and plane DMA in every frame path
2. Audit scene-transition tile preload: for first VBlank after scene change, cache miss volume
   may require main-thread preload rather than single-VBlank resolution

**Verification**:
- `tilebuf_nonzero > 0` in probe (tile data present)
- Tile patterns visible in graphics test viewer for logo tile codes
- No corrupted tile appearances due to timing race

### Phase 3 — Tilemap Updates: Text Shadow → VDP Planes

**Input**: Text shadow buffer at 0xE0FFC84C populated by `genesistan_hook_text_writer_3bb48_impl`
          with cell words (glyph + palette + priority)

**Output**: Plane A and Plane B nametables updated in VDP VRAM; text rows visible on screen

**Work**:
1. Implement DMA C: text shadow → Plane A (VRAM 0xE000) and Plane B (VRAM 0xC000) in VBlank
2. Adopt dirty-row scan optimization: only DMA non-space rows to stay within VBlank budget
3. Handle column/row mapping: PC080SN page offset 0x400 maps to row 8 col 0 in Genesis planes

**Verification**:
- All title text strings visible (not only CREDIT as in build 271)
- Text clearing/refilling works correctly across state transitions (no stale text)

### Phase 4 — Scroll Handling: WRAM State → VDP Registers

**Input**: Scroll words in `genesistan_arcade_workram_words` at offsets 0x10AE/10B0/10EC/10EE,
          updated by arcade scroll producers intercepted via `jsr 0x200DC2` callsites

**Output**: VDP VSRAM holding correct X/Y scroll values for Plane A and Plane B

**Work**:
1. Confirm `genesistan_scroll_from_workram_vdp` is called in VBlank (Step 12b) and reads
   the canonical WRAM words consistently
2. Validate scroll values are sign-correct (negated with vertical crop bias as in current impl)
3. Test with gameplay state scroll changes to confirm no tearing or incorrect plane repositioning

**Verification**:
- Title screen background tiles align with expected position
- Scroll transitions do not produce torn or offset frames

### Phase 5 — Palette Handling: Palette Buffer → CRAM

**Input**: `genesistan_palette_rom_table` (build-time pre-converted) and
          `genesistan_palette_clcs` (runtime CLCS capture)

**Output**: VDP CRAM updated with correct arcade palette on scene transitions

**Work**:
1. Confirm palette-dirty flag gate is set on all scene transitions
2. Ensure DMA D (palette → CRAM) fires in VBlank Step 4 before tile/sprite visibility
3. Validate color accuracy against arcade reference (correct `0000 BBB0 GGG0 RRR0` format)

**Verification**:
- Title screen colors match arcade reference palette
- No miscolored frames on scene transition
- Palette update does not fire every frame (performance guard)

---

## 9. Components to Remove

The following exist in the current codebase and should be removed or disabled once the arcade
vblank owns display after launch:

### SGDK/C Rendering Paths (to remove after Phase 1 proves)

| Component | Location | Reason to Remove |
|-----------|----------|------------------|
| `SYS_doVBlankProcess()` call in main loop | main.c line 2026 | Launcher-only; must not run during SCREEN_FRONTEND_LIVE |
| `VDP_clearPlane(BG_A/B, TRUE)` calls in `request_start_rastan` | main.c lines 1764–1765 | One-time init only; arcade vblank owns clear after launch |
| `genesistan_hook_tilemap_plane_a` / `genesistan_hook_tilemap_plane_b` | main.c lines 1185/1229 | Column/row cursor approach is superseded by full text shadow + DMA C |
| `col_a/row_a/col_b/row_b` cursor state | startup_bridge.c lines 93–100; main.c lines 1189/1216 etc. | Replaced by text shadow offset calculation |
| `render_frontend_sprite_layer()` wrapper | main.c line 1657 | Dead wrapper; arcade vblank drives sprite render |
| `VDP_setSpriteFull()` inside `genesistan_render_sprites_vdp` | main.c line 1620 | SGDK sprite API; replace with direct SAT staging write |
| `VDP_updateSprites(sprite_count, DMA)` inside renderer | main.c line 1651 | Move this DMA to VBlank Step 11; not inside C renderer function |

### Temporary Scaffolding (to remove)

| Component | Location | Reason to Remove |
|-----------|----------|------------------|
| `VDP_fillTileMapRect(BG_A, ...)` call | main.c line 528 | Launcher text fill; not in title/game path |
| `c_window_poison_wipe` function | main.c ~1840 | Debug tool for C-Window stale word scan; not needed in final |

### Architecture Violations (must not exist in final)

| Component | Why Invalid |
|-----------|-------------|
| Any C function calling `VDP_*` APIs from main loop during SCREEN_FRONTEND_LIVE | Violates: arcade vblank is sole display owner after launch |
| Any `SYS_doVBlankProcess()` call that runs after arcade starts | Violates: SGDK VBlank framework must not run after handoff |
| Any direct `PAL_setColors()` call outside scene-change path | Violates: palette DMA belongs in VBlank Step 4 behind dirty flag |
| Any per-frame C rendering wrapper that bypasses arcade dispatch table | Violates: all per-frame work routes through arcade state dispatch |

---

## 10. Final Recommendation

The immediate unblocking action is Phase 1: fix the producer/renderer call order in the
0x03AAB8 title init cluster so the block-A builder (0x05A2B4) fires before the renderer
(0x2005C4). This is a single opcode reorder (swap two adjacent JSR calls via patch spec entry),
with no new translation work. Once this is applied and the logo sprite appears in VDP output,
Phases 2–5 can proceed incrementally on a proven foundation.

The renderer guard bug (word0==0 forcing y=0x0180) was narrowed in Build 278 to detect only
fully-zero tuples. This is correct and should not be reverted.

DMA B (SAT staging → VRAM 0xF800) is currently invoked inside `genesistan_render_sprites_vdp`
via `VDP_updateSprites(sprite_count, DMA)`. This is structurally acceptable for the title
screen phase; in the steady-state architecture this DMA should be driven by the arcade VBlank
step sequence, not by the C renderer function. Plan for this refactor in Phase 1 validation.

The arcade vblank remains the authoritative frame controller; Genesis VDP/DMA commit replaces all hardware-facing behavior within that flow.
