# Rastan VBlank and VDP Buffer Architecture

## 1. Purpose

Design the correct Genesis graphics publish architecture for Rastan based on
a verified audit of what arcade Rastan does during VBlank.

This document provides:
- assembly-level audit of the arcade VBlank interrupt handler
- classified responsibilities (keep / adapt / replace)
- opcode identification strategy for PC080SN / PC090OJ / scroll intent
- Genesis WRAM buffer architecture
- ordered Genesis VBlank publish sequence
- scroll conversion design
- DMA routine design
- semantic relocation strategy
- application to the title screen
- recommended first implementation slice

Reference implementations explicitly used throughout:
- Rainbow Islands (Taito PC080SN + PC090OJ → Genesis VDP, producer→consumer ownership validation)
- Cadash (Taito TC0100SCN + PC090OJ → Genesis VDP, intent-class primitive mapping)

---

## 2. Arcade Rastan VBlank Audit

### Interrupt Structure

- **Level 5 hardware interrupt** fires at VBlank.
  - Vector at ROM offset 0x74 = `0x0003A008` (level 5 autovector).
- **Level 4** (0x70 → 0x3A004 → `braw 0x3A080`) routes to a crash/infinite-loop handler.
  Level 4 is deliberately treated as an error — not the VBlank path.
- **Only one `rte`** exists in the entire ROM, at `0x3A07E`.
  All interrupt returns go through this single exit.

### VBlank Handler Entry at `0x3A008`

```
0x3A008  oriw  #0x0F00, sr          ; mask all interrupts (level 7)
0x3A00C  clrw  0x350008             ; watchdog refresh
0x3A012  movew d0, 0x3C0000         ; hardware sync latch (coin/control hardware)
0x3A018  movew a5@(2), d0           ; load major game state
0x3A01C  cmpiw #2, d0
0x3A020  bcss  0x3A03E              ; if state < 2, skip next
0x3A022  cmpiw #4, d0
0x3A026  bccs  0x3A03E              ; if state > 4, skip next
0x3A028  bsrw  0x3A126              ; conditional scroll/DMA sync (states 2-4 only)
0x3A02C  tstw  a5@(0)
0x3A032  cmpiw #1, a5@(5012)
0x3A03A  bsrw  0x41F30              ; conditional scroll sync
0x3A03E  bsrw  0x3AB7C              ; frame counter / watchdog check
0x3A042  bsrw  0x3ABE2              ; per-frame bookkeeping (coin detect, counters)
0x3A046  bsrw  0x3A0A8              ; input polling
0x3A04A  bsrw  0x3EEFA              ; sound/game timing sync A
0x3A04E  bsrw  0x3EF5C              ; sound/game timing sync B
0x3A052  pea   pc@(0x3A074)         ; push return address for dispatch
0x3A056  movew a5@(0), d0           ; major state → dispatch index
0x3A05A  addw  d0, d0               ; ×2 for word table
0x3A05C  lea   pc@(0x3A06C), a0     ; table base
0x3A060  addaw d0, a0               ; a0 = &table[state]
0x3A062  movew a0@, d0              ; word displacement
0x3A064  lea   pc@(0x3A06C), a0     ; table base again
0x3A068  addaw d0, a0               ; a0 = table_base + displacement
0x3A06A  jmp   a0@                  ; dispatch to per-state handler
         ; --- per-state handler executes, returns to 0x3A074 ---
0x3A074  jsr   0x55CA2              ; post-dispatch cleanup
0x3A07A  andiw #-3841, sr          ; restore interrupt mask (re-enable level 1-6)
0x3A07E  rte                        ; return from exception
```

### Per-State Dispatch Table at `0x3A06C`

Word displacements from table base `0x3A06C`:

| State | Offset | Handler |
|-------|--------|---------|
| 0 | 0x0992 | `0x3A9FE` |
| 1 (title) | 0x0840 | `0x3A8AC` |
| 2 | 0x0B02 | `0x3AB6E` |
| ... | ... | ... |

### Title State VBlank Handler at `0x3A8AC` (state=1)

```
0x3A8AC  tstw  a5@(44)              ; test timer gate A5+0x2C
0x3A8B0  beqs  0x3A8B8              ; if zero, proceed
0x3A8B2  subqw #1, a5@(44)         ; decrement and return early
0x3A8B6  rts
0x3A8B8  movew a5@(2), d0          ; sub-state
0x3A8BC  addw  d0, d0              ; ×2 for word table
0x3A8BE  lea   pc@(0x3A8CE), a0    ; sub-state table base
0x3A8C2  addaw d0, a0
0x3A8C4  movew a0@, d0
0x3A8C6  lea   pc@(0x3A8CE), a0
0x3A8CA  addaw d0, a0
0x3A8CC  jmp   a0@                 ; dispatch to sub-state handler
```

Sub-state 0 handler at `0x3A8D2`:
```
0x3A8D2  bsrw  0x3ADD8             ; display orientation → write 0xC50000 (PC080SN ctrl)
0x3A8D6  bsrw  0x3AD4C             ; sprite RAM clear (fill D00000 with 0x00000100)
0x3A8DA  bsrw  0x3AE5A             ; tile plane clear (fill C00100/C08100 with 0x20)
                                   ; + scroll/control init via 0x3B098
0x3A8DE  moveq #1, d1
0x3A8E0  bsrw  0x3B902             ; timing counter update
0x3A8E4  jsr   0x59F5E             ; additional producer
0x3A8EA  moveq #9, d0
0x3A8EC  bsrw  0x3BB48             ; text dispatch selector 9 (title text line)
0x3A8F0  moveq #10, d0
0x3A8F2  cmpiw #1, a5@(18)
0x3A8F8  beqs  0x3A8FC
0x3A8FA  moveq #11, d0
0x3A8FC  bsrw  0x3BB48             ; text dispatch selector 10/11
0x3A900  jsr   0x5A410             ; additional title producer
```

### Key Finding: Text Producers Run Inside VBlank

`0x3BB48` is the primary text dispatch entry (`genesistan_hook_text_writer_3bb48_impl`).
It is called from INSIDE the VBlank interrupt handler with specific selectors.

This means:
- In arcade Rastan, text cell writes to PC080SN C-Window happen **during VBlank**.
- Main thread runs the broader init sequence (0x03AAB8 cluster) before the first VBlank.
- Per-frame text updates (selector 9, 10/11) are VBlank-driven, not main-thread-driven.

Consequence for Genesis design: the VBlank publish window must include text producer
execution or must read from WRAM staging buffers populated just before VBlank fires.

### Sprite RAM Clear at `0x3AD4C`

```
0x3AD4C  movew #8, d1
0x3AD50  lea   0xD00000, a0
0x3AD56  movel #0x00000100, d0      ; off-screen Y=256 for PC090OJ
0x3AD5C  bsrs  0x3AD44             ; fill loop (write d0 to a0@+, d1 times)
0x3AD5E  movew #386, d1
0x3AD62  lea   0xD00170, a0
0x3AD68  movel #0x00000100, d0
0x3AD6E  bsrs  0x3AD44             ; fill rest of sprite RAM
```

This clears the PC090OJ descriptor RAM each VBlank with an "off-screen" sentinel.
Main thread then repopulates active sprite entries after VBlank returns.
This is the standard Taito per-frame sprite commit pattern.

### Tile Plane Clear at `0x3AE64`

```
0x3AE64  lea   0xC00100, a0         ; PC080SN page 0 FG start
0x3AE6A  movew #1900, d1
0x3AE6E  moveq #32, d0              ; 0x20 = space character
0x3AE70  bsrw  0x3AD44             ; fill BG layer with spaces
0x3AE74  lea   0xC08100, a0         ; PC080SN page 2 BG start
0x3AE7A  movew #1900, d1
0x3AE7E  moveq #32, d0
0x3AE80  bsrw  0x3AD44             ; fill FG/text layer with spaces
```

Both tile planes are cleared to space (0x20) every VBlank.
Then text producers refill active cells in the same VBlank.
This is a full-refresh per-frame pattern — no dirty-region tracking in arcade.

---

## 3. Classified VBlank Responsibilities

| Responsibility | Code | Classification |
|---|---|---|
| Mask interrupts | `oriw #0x0F00, sr` at `0x3A008` | MUST KEEP (Genesis also uses SR mask) |
| Watchdog clear | `clrw 0x350008` | HARDWARE-SPECIFIC — no Genesis watchdog; remove |
| Hardware sync latch | `movew d0, 0x3C0000` | HARDWARE-SPECIFIC — no Genesis equivalent; remove |
| Conditional state-2/4 scroll sync | `bsrw 0x3A126` | MUST KEEP SEMANTICALLY — adapt scroll to VDP |
| Frame counter / overflow watchdog | `bsrw 0x3AB7C` | MUST KEEP — game logic depends on counter |
| Per-frame bookkeeping (coin detect) | `bsrw 0x3ABE2` | MUST KEEP — game logic / coin count |
| Input polling | `bsrw 0x3A0A8` | MUST KEEP — reads 0x390000 shadow already mapped |
| Sound/timing sync A | `bsrw 0x3EEFA` | MUST KEEP — writes to 0x380000 shadow |
| Sound/timing sync B | `bsrw 0x3EF5C` | MUST KEEP — same |
| Per-state dispatch table | `jmp a0@` at `0x3A06A` | MUST KEEP EXACTLY — drives all state-specific work |
| Post-dispatch cleanup | `jsr 0x55CA2` | MUST KEEP |
| Restore interrupt mask | `andiw #-3841, sr` | MUST KEEP |
| RTE | `0x3A07E` | MUST KEEP |
| Display orientation → `0xC50000` | `bsrw 0x3ADD8` | GRAPHICS-HARDWARE-SPECIFIC — replace with VDP scroll/control |
| Sprite RAM clear (D00000) | `bsrw 0x3AD4C` | GRAPHICS-HARDWARE-SPECIFIC — replace with SAT buffer clear |
| Tile plane clear (C00100/C08100) | `0x3AE64` | GRAPHICS-HARDWARE-SPECIFIC — replace with WRAM text shadow clear |
| Text producers in VBlank (0x3BB48) | `bsrw 0x3BB48` | MUST KEEP SEMANTICALLY — adapt to write WRAM staging + VDP publish |
| Scroll/control init (0x3B098) | via `0x3AE5A` | GRAPHICS-HARDWARE-SPECIFIC — replace with VDP register writes |

---

## 4. Opcode Identification Strategy for PC080SN / PC090OJ / Scroll

### A) PC080SN-Related Operations

Recognition rules in disassembly:

1. **Direct C-Window writes**:
   - Pattern: `movew Dn, 0xCXXXXX` or `movel Dn, 0xCXXXXX` where target is in `0xC00000–0xC0FFFF`.
   - Sub-addresses identify the layer:
     - `0xC00000–0xC03FFF` = page 0 (BG layer 0 / Plane B)
     - `0xC08000–0xC0BFFF` = page 2 (FG/text layer / Plane A)
     - `0xC04000–0xC07FFF` and `0xC0C000–0xC0FFFF` = additional pages
   - Both planes start at row offset 0x400 into their page.

2. **Address setup into C-Window**:
   - Pattern: `lea 0xC0XXXX, An` followed by write loop using `An@+`.
   - Fill loops (clear): `movel #0xXXXX, d0; subqw #1, d1; bnes loop` targeting C-Window.

3. **Helper/wrapper routines**:
   - The fill helper at `0x3AD44`: `movel d0, a0@+; subqw #1, d1; bnes loop`
     Called with `a0 = C-Window address`, `d0 = fill word`, `d1 = count`.
   - Identified as PC080SN intent when `a0` setup is in C-Window range.

4. **Text/tile descriptor producer paths**:
   - Entry via `bsrw 0x3BB48` or `bsrw 0x3BD5E` with selector in D0.
   - Selector dispatch → per-text table → cell writes to active C-Window page.
   - Already translated: `0x20034C` producer writes translated cell data.

Evidence categories:
- **Direct memory-window write**: moves directly to `0xC00000+` range.
- **Descriptor producer**: selector-dispatched routines (via 0x3BD5E, 0x3BB48) that resolve
  text layout tables and emit per-cell words.
- **Helper fill**: 0x3AD44-family fill loops with C-Window destination.
- **Control path**: writes to `0xC20000`, `0xC40000`, `0xC50000` (scroll/control registers).

### B) PC090OJ-Related Operations

Recognition rules:

1. **Direct D-Window writes**:
   - Pattern: `movew Dn, 0xD0XXXX` or `movel Dn, 0xD0XXXX` in `0xD00000–0xD03FFF`.

2. **Descriptor/object fill**:
   - Clear fill of `0xD00000` with `0x00000100` (off-screen sentinel) = sprite RAM clear.
   - Structured longword writes to `0xD00000+offset` = sprite descriptor update.
   - PC090OJ descriptor format: consecutive words for Y, size+link, tile, X.

3. **Descriptor producer paths**:
   - `0x05A174` cluster: produces logo/title sprite descriptors into WRAM windows
     (`0xE0FF11B2`, `0xE0FF0170`) that are consumed by the renderer path.
   - Renderer at `0x2005C4`: reads from WRAM descriptor windows and emits to VDP/SAT.
   - Key identification: descriptor write patterns to `0xE0FF11FE`, `0xE0FF01BC` (renderer-owned),
     vs legacy windows `0xE0FF11B2`, `0xE0FF0170` (producer-owned).
   - A write to `0xE0FF791C / 0xE0FF6DF0` families is renderer-side staging.

4. **Producer/consumer boundary**:
   - Producer writes: `0x05A174` → fills `0xE0FF0170+` / `0xE0FF11B2+`
   - Consumer reads: `0x2005C4` → reads `0xE0FF11FE+` / `0xE0FF01BC+`
   - The producer and consumer windows are distinct; the renderer uses its own staging.

Evidence categories:
- **Direct D-Window write**: moves directly to `0xD00000+`.
- **Descriptor producer**: routines filling structured word/longword blocks in WRAM
  (four-word tuples: y, attr, tile, x) destined for SAT.
- **Control register path**: any write to PC090OJ control area (not present separately in Rastan;
  the chip is fully controlled via descriptor content).

### C) Scroll / Control Operations

Recognition rules:

1. **Direct scroll register writes**:
   - `movew Dn, 0xC20000` = PC080SN Y-scroll register
   - `movew Dn, 0xC40000` = PC080SN X-scroll register
   - `movew Dn, 0xC50000` = PC080SN control (flip, layer enable)

2. **Scroll source reads**:
   - Pattern: `movew a5@(N), d0; movew d0, 0xC20000` (read WRAM, write chip).
   - Scroll source words already identified: `0xE0FF113A`, `0xE0FF1138`, `0xE0FF10FC`, `0xE0FF10FA`.

3. **The `0x200DC2` wrapper**:
   - Called via `jsr 0x200DC2` with scroll state in WRAM.
   - This is the translated scroll/control publisher (already in the project).
   - Recognition: any `jsr 0x200DC2` callsite = scroll/control intent.

4. **VDP control register programming (Genesis-side, NOT scroll)**:
   - `0x93xx / 0x94xx / 0x95xx / 0x96xx / 0x97xx` values written to `0xC00004`
     are DMA setup registers, **not scroll registers**.
   - Scroll registers are VDP registers 0x8B, 0x8D (H/V scroll mode),
     plus VSRAM writes (access through VDP address setup 0x40000010 for VSRAM).

---

## 5. Genesis WRAM Buffer Architecture

All confirmed from AGENTS.md (Build 112 session) and existing project state,
cross-validated against Rainbow Islands WRAM staging model.

### A) SAT Staging (`genesistan_shadow_d00000_words`)

- **Purpose**: Hold the current frame's sprite descriptor set between producer writes
  and VBlank DMA to VDP SAT.
- **WRAM size**: 80 entries × 8 bytes = 640 bytes.
  (Genesis SAT supports 80 sprites; Rastan's visible sprite count fits within this.)
- **Entry format** (per Rainbow Islands and Genesis SAT spec):
  ```
  word 0: Y position (9-bit, 1-based)
  word 1: size (2-bit height×width) | link (7-bit next entry index)
  word 2: tile index (11-bit) + priority + palette + H/V flip bits
  word 3: X position (9-bit, 1-based)
  ```
- **Producer**: PC090OJ-translated sprite descriptor writes (already mapped in project)
  via the renderer path `0x2005C4`, staging into WRAM blocks at `0xE0FF791C / 0xE0FF6DF0` families.
- **VBlank consumer**: DMA to VDP SAT at VRAM `0xF800`.
- **Clear protocol**: Fill with sentinel (Y=0, link=0, tile=0, X=0) each VBlank before
  producer populates — directly analogous to arcade `0x3AD4C` clearing D00000.

### B) Tilemap / Plane Staging (text shadow at `0xE0FFC84C`)

- **Purpose**: Hold the current frame's text/tile cell updates for Plane A and Plane B
  between producer writes and VBlank DMA to VRAM plane nametables.
- **WRAM size**: 0x0800 words = 2KB (already allocated in project).
- **Entry format**: Each word is a Genesis nametable cell:
  ```
  bits 15:13  = priority (1) + palette line (2)
  bits 12:11  = V flip, H flip
  bits 10:0   = tile pattern index in VRAM
  ```
- **Clear protocol**: Fill entire shadow with 0x0020 (space tile, no attributes) each VBlank
  before producers run — directly analogous to arcade `0x3AE64` clearing C-Window.
- **Producer**: `0x20034C` text producer path + `0x200E56` secondary producer.
  These write decoded glyph cells into the shadow region.
- **VBlank consumer**: DMA or stream-write from shadow to:
  - Plane B (`0xC000` VRAM base) for BG layer (page 0 mappings)
  - Plane A (`0xE000` VRAM base) for FG/text layer (page 2 mappings)
- **Column/row mapping**: Text shadow base is at page offset 0x400 per AGENTS.md
  (both planes start at row 8 col 0).

### C) Palette / CRAM (pre-converted ROM table)

- **Purpose**: Provide per-frame CRAM state without runtime conversion.
- **WRAM size**: No WRAM staging needed — source is ROM.
- **Format**: `genesistan_palette_rom_table` — pre-converted 2048-entry table in ROM
  using Genesis VDP color format (per AGENTS.md Build 112 palette architecture).
- **Producer**: None per-frame. Table is fixed at build time.
- **VBlank consumer**: One-shot DMA on scene change: ROM table → VDP CRAM.
  `load_arcade_palette()` performs this transfer.
- **Dirty tracking**: Scene-change flag or palette-dirty flag gates the DMA.
  Not re-uploaded every frame unless color state changes.

### D) Tile / Pattern Cache (per AGENTS.md Build 112)

- **Purpose**: Track which arcade tile indices are resident in VRAM tile slots,
  and drive DMA uploads of missing tiles.
- **WRAM size**: ~4.6KB total:
  ```
  uint16_t cache_slot_to_arcade[1164]   // 2.3KB — arcade tile in each slot
  uint16_t cache_slot_lru[1164]         // 2.3KB — LRU counter per slot
  uint16_t cache_lru_clock              // 2 bytes — global LRU counter
  ```
- **VRAM slots**: Slots 20–1023 and 1280–1439 (from AGENTS.md).
- **Producer**: Every text/sprite producer that resolves a tile index checks the cache.
  On miss: evict oldest LRU slot, DMA 32 bytes from `rastan_pc080sn` ROM to VRAM slot.
- **VBlank consumer**: Cache misses are resolved before SAT/plane DMA so tile data
  is resident before visible references publish.

### E) Scroll / Control Staging

- **Purpose**: Accumulate per-frame scroll state for publish in VBlank.
- **WRAM size**: 4 words = 8 bytes (already present in project).
  ```
  0xE0FF113A  = Plane A (FG) Y scroll
  0xE0FF1138  = Plane B (BG) Y scroll
  0xE0FF10FC  = Plane A (FG) X scroll
  0xE0FF10FA  = Plane B (BG) X scroll
  ```
- **Producer**: Arcade scroll writes (0xC20000, 0xC40000, 0xC50000) are intercepted
  and redirected to these WRAM words. Already handled by `genesistan_scroll_from_workram_vdp`.
- **VBlank consumer**: Reads these words and writes to VDP scroll registers/VSRAM
  during the Genesis VBlank publish sequence.
- **What is staged vs direct**: All scroll values are staged; control register writes
  (layer enable, flip) can be direct VDP writes since they are infrequent.

---

## 6. Genesis VBlank Publish Sequence

The design principle from Rainbow Islands and Cadash:
- **Preserve** required arcade semantic responsibilities.
- **Add** Genesis VDP publish work in the correct order.
- Do NOT replace the arcade VBlank wholesale.

### Ordered Sequence

**Step 1 — Interrupt mask setup (KEEP)**
- `oriw #0x0F00, sr`
- Why: Genesis 68000 still uses the SR interrupt mask; this prevents re-entrant VBlank.

**Step 2 — Non-graphics housekeeping (KEEP)**
- Watchdog: remove (no Genesis watchdog); hardware sync latch (0x3C0000): remove.
- Frame counter / overflow watchdog (`0x3AB7C`): keep — game logic depends on this counter.
- Per-frame bookkeeping (`0x3ABE2`, coin detect, BCD counter): keep — no graphics impact.
- Input polling (`0x3A0A8`, reads 0x390000 shadow): keep — already mapped to Genesis shadow.
- Sound/timing sync (`0x3EEFA`, `0x3EF5C`, writes to 0x380000 shadow): keep.

**Step 3 — Per-state dispatch entry (KEEP EXACTLY)**
- `jmp a0@` dispatch via `0x3A06A` table.
- Why: this is the core of the arcade VBlank; all state-specific work is routed here.

**Step 4 — GENESIS: Palette publish (NEW)**
- Triggered once per scene change by palette-dirty flag.
- Action: DMA from `genesistan_palette_rom_table` in ROM → CRAM via VDP DMA.
- Must happen before tile/sprite visibility to avoid miscolored frames.
- Size: 64 words (4 palette lines × 16 colors × 2 bytes).

**Step 5 — Clear SAT staging buffer (REPLACE `0x3AD4C`)**
- Arcade: fills `0xD00000` with off-screen sentinel `0x00000100`.
- Genesis: fills `genesistan_shadow_d00000_words` with zero/sentinel (Y=0, link=self, tile=0, X=0).
- Why step 5: must happen before producer populates SAT in step 7.

**Step 6 — Clear text/plane staging buffer (REPLACE `0x3AE64`)**
- Arcade: fills `0xC00100` and `0xC08100` with 0x20 (space char).
- Genesis: fills text shadow `0xE0FFC84C` with space-tile cells (0x0020).
- Why step 6: must happen before text producers write active cells.

**Step 7 — Text producers execute (ADAPT `0x3BB48`)**
- Arcade: text producers write to PC080SN C-Window (0xC00100/0xC08100).
- Genesis: text producers write to text shadow (`0xE0FFC84C`).
- The existing `genesistan_hook_text_writer_3bb48_impl` already routes here.
- Selectors 9, 10/11 fire with correct tile-cache-resolved VRAM indices.

**Step 8 — Logo/sprite descriptor producer (ADAPT `0x05A174`)**
- Arcade: producer fills PC090OJ descriptor RAM (`0xD00000`).
- Genesis: producer fills WRAM descriptor windows (`0xE0FF11FE`, `0xE0FF01BC`).
- **CRITICAL ORDERING**: producer (Step 8) must complete before renderer (Step 9).
- Current bug in Build 271: sprite renderer (`0x03AAEC`) is called BEFORE logo producer
  (`0x03AAF2`) in the title init path (Steps 9 and 10 of title_screen_graphics_call_inventory.md).
  The fix is to swap these calls in the 0x03AAB8 title init cluster.

**Step 9 — GENESIS: Tile cache resolve (NEW)**
- For each non-zero tile index referenced in text shadow and SAT staging:
  check the tile cache; on miss, DMA 32 bytes from `rastan_pc080sn` ROM to the evicted VRAM slot.
- Must happen before plane/SAT DMA so VRAM has the actual tile data.

**Step 10 — Sprite renderer: SAT staging → SAT DMA (ADAPT `0x2005C4`)**
- Arcade: renderer writes descriptors to PC090OJ RAM.
- Genesis: renderer builds Genesis SAT tuples in `genesistan_shadow_d00000_words`.
  Then DMA: `genesistan_shadow_d00000_words` → VDP SAT at VRAM `0xF800`.
  Size: 80 entries × 8 bytes = 640 bytes.

**Step 11 — GENESIS: Plane write publish (NEW)**
- Stream non-space cells from text shadow (`0xE0FFC84C`) to Plane A and Plane B VRAM.
- Plane B (`0xC000` VRAM) for BG layer cells (page 0 source).
- Plane A (`0xE000` VRAM) for FG/text cells (page 2 source).
- Can be done via VDP address setup + word stream write, or DMA.

**Step 12 — Scroll/control publish (ADAPT `0xC50000/C20000/C40000` writes)**
- Arcade: write scroll words directly to PC080SN chip registers.
- Genesis: read WRAM scroll words (`0xE0FF113A/1138/10FC/10FA`) and write to:
  - VDP VSRAM via `40000010` address command for per-plane scroll (H-scroll mode 00 = full-screen),
    or per-tile VSRAM for V-scroll.
  - Or VDP registers 0x8D (H-scroll table addr), 0x8B (scroll mode).
  - Already handled by `genesistan_scroll_from_workram_vdp` / `0x200DC2` path.

**Step 13 — Post-dispatch cleanup (KEEP)**
- `jsr 0x55CA2`

**Step 14 — Restore interrupt mask and RTE (KEEP)**
- `andiw #-3841, sr`
- `rte`

### Justification of Order

- Palette before tiles: avoids miscolored first frame.
- Clear before produce: ensures stale producer content from prior frame does not persist.
  (Same discipline as arcade: 0x3AD4C clear before sprite producers, 0x3AE64 clear before text producers.)
- Tiles before SAT/plane DMA: VRAM must have pattern data before SAT entries reference tile indices.
- SAT DMA before plane DMA: sprite rendering takes priority over tilemap updates
  (following Cadash/Rainbow Islands rendering order: tilemap draw then sprites).
  Actually for Genesis VDP, SAT and plane data are both consumed at scan time, so order of DMA upload
  doesn't affect visibility — what matters is that all DMAs complete before active display.
- Scroll last: scroll writes affect the view of data that is already in VRAM; applied last to
  minimize the frame of incorrect scroll before new data is visible.

---

## 7. Scroll Conversion Design

### Arcade Side

Scroll registers in Rastan:
- `0xC20000` = PC080SN Y scroll (two words: layer 0 Y, layer 1 Y)
- `0xC40000` = PC080SN X scroll (two words: layer 0 X, layer 1 X)
- `0xC50000` = PC080SN control (layer enable, flip, priority)

These are written:
- During VBlank (via `0x3ADD8` orientation write and `0x3B098` scroll init).
- Accumulated in WRAM: `0xE0FF113A/1138/10FC/10FA`.
- Published by `jsr 0x200DC2` callsites in the title init path.

The `0xC20000/C40000/C50000` writes are HARDWARE-CHIP writes to the PC080SN.
The VDP DMA registers `0x93..0x97` are NOT scroll — they are DMA setup registers and must never
be confused with scroll state.

### Genesis Side

Genesis scroll equivalents:
- **H-scroll** (X): full-screen mode → write X value to VSRAM word 0 (plane A) and word 2 (plane B).
  Or use per-tile H-scroll table in VRAM (mode 3).
- **V-scroll** (Y): full-screen mode → write Y value to VSRAM word 0 (plane A) and word 2 (plane B).

VSRAM access: set VDP address to VSRAM destination using control word `0x40000010`
(or `0x40000000 | (vsram_offset << 16) | 0x10`), then write scroll words to data port.

### What Gets Staged vs Written Directly

- **Staged**: X and Y scroll values in WRAM (`0xE0FF113A/1138/10FC/10FA`).
  These are updated throughout the frame by game logic.
  Published in VBlank Step 12 to VSRAM.

- **Written directly**: Layer control state (layer enable, flip mode).
  These change rarely (scene transitions only), so direct VDP register writes are acceptable.
  VDP register 0x8B (scroll mode) and register 0x81 (display enable / DMA enable) are examples.

- **Must happen before tile/sprite visibility**: scroll publish in Step 12 is intentionally after
  tile uploads (Step 9) and SAT DMA (Step 10) to ensure new tile data is already resident when
  scroll repositions the view.

---

## 8. DMA Routine Design

Based on Cadash and Rainbow Islands DMA patterns (`0x93/0x94/0x95/0x96/0x97` register programming).

### DMA A — Tile Pattern Upload (on cache miss, per-frame conditional)

- **When**: Any VBlank in which a tile cache miss occurred.
- **What**: 32 bytes per missing tile (one tile = 8×8 pixels × 4 bits/pixel = 32 bytes).
- **Source**: ROM at `rastan_pc080sn` base + (arcade_tile_index × 32).
- **Destination**: VRAM at (evicted_slot_index × 32).
- **Size**: 32 bytes per miss; typically 5–50 misses per scene transition, 0 in steady state.
- **Ordering constraint**: Must complete before any plane or SAT DMA that references this tile index.
- **DMA setup**: VDP DMA mode (source = ROM, auto-increment = 2, length = 32/2 = 16 words).

### DMA B — SAT Upload (every frame)

- **When**: Every VBlank, after SAT staging buffer is populated.
- **What**: Full SAT block — 80 entries × 8 bytes = 640 bytes = 320 words.
- **Source**: `genesistan_shadow_d00000_words` in WRAM.
- **Destination**: VRAM at `0xF800` (SAT base).
- **Ordering constraint**: After tile DMA A completes; before active display scan.
- **DMA setup**: VDP DMA mode (source = WRAM, destination = VRAM 0xF800, length = 320 words).

### DMA C — Text / Plane Publish (every frame, dirty cells only)

- **When**: Every VBlank, after text producers have written to text shadow.
- **What**: Active text cell rows from `0xE0FFC84C` shadow to Plane A or Plane B VRAM.
- **Source**: `0xE0FFC84C` (text shadow, WRAM).
- **Destination**: Plane A (`0xE000`) for FG/text cells; Plane B (`0xC000`) for BG cells.
- **Size**: Up to 64 columns × 28 rows × 2 bytes = 3584 bytes per plane;
  in practice, title screen text uses a fraction of this.
  Optimization: scan for non-space rows and only DMA those rows (dirty-row approach).
- **Ordering constraint**: After tile DMA A (tile data resident); before scan.

### DMA D — Palette / CRAM Upload (per scene change, not every frame)

- **When**: On scene transition (palette-dirty flag set by state machine).
- **What**: 64 Genesis palette words (4 lines × 16 colors × 2 bytes = 128 bytes).
- **Source**: `genesistan_palette_rom_table` in ROM.
- **Destination**: VDP CRAM via CRAM write command (`0xC0000003` for CRAM address 0).
- **Ordering constraint**: Before tile/plane/SAT DMA to avoid miscolored first frame.

### DMA Register Programming Pattern (from Cadash / Rainbow Islands)

```
movel #0x93XX0000, VDP_CTRL   ; DMA length high (0x9300 | length_high)
movel #0x94XX0000, VDP_CTRL   ; DMA length low  (0x9400 | length_low)
movel #0x95XX0000, VDP_CTRL   ; DMA source low  (0x9500 | src_low)
movel #0x96XX0000, VDP_CTRL   ; DMA source mid  (0x9600 | src_mid)
movel #0x97XX0000, VDP_CTRL   ; DMA source high (0x9700 | src_high>>1 | 0x80 for VRAM DMA)
movel #dest_cmd,   VDP_CTRL   ; destination command (VRAM/VSRAM/CRAM write + DMA bit)
; VDP executes DMA transfer
```

Note: `0x93..0x97` are VDP register write commands (high byte = register number, low byte = value).
They are NOT scroll registers. Confusion between DMA setup registers and scroll registers is
a documented project error vector.

---

## 9. Semantic Relocation Strategy

### The Problem

Every opcode replacement that changes instruction size causes all subsequent absolute and relative
references to shift. As more patches are applied, earlier-computed addresses become stale.
The project has already experienced this: wrong call targets after insertions (Builds 214, 218).

### The Strategy

**Rule 1 — `original_bytes` validation on every spec entry**
Every `opcode_replace` entry in `specs/startup_title_remap.json` must specify `original_bytes`.
The patcher validates this match before applying the replacement.
A mismatch means the address has shifted — stop and diagnose before proceeding.

**Rule 2 — Semantic anchoring for all callsite targets**
When recording a callsite target (e.g., `jsr 0x202B74`), also record the first 4–6 bytes
of the target function as a semantic signature. Store this in the spec entry:
```json
{
  "type": "opcode_replace",
  "address": "0x03B2B8",
  "original_bytes": "6100...",
  "replacement_bytes": "...",
  "target_signature": "48E7....",
  "comment": "text producer dispatch"
}
```
Before applying a relocation fix, the patcher verifies `target_signature` matches the
bytes at the (shifted) target address. Mismatch = stop, not silently mis-relocate.

**Rule 3 — Jump table entries as (base, index) pairs, not absolute words**
Jump table displacements must be computed at patch time from the current (shifted) table base,
not stored as pre-computed absolute values. The patcher must re-derive table offsets from
the current state of the binary after each insertion batch.

**Rule 4 — Batch insertions, then full relocation pass**
After a set of related opcode insertions (e.g., all title-init text patches in one batch):
1. Apply all insertions.
2. Run full shift-table relocation pass (all absolute and relative references).
3. Validate the binary before proceeding to the next patch batch.
Never apply a second batch before the first batch's relocation is fully resolved.

**Rule 5 — WRAM buffer addresses as named symbols, not hardcoded literals**
Buffer addresses (`0xE0FFC84C`, `0xE0FF11FE`, etc.) appear as immediate operands in arcade code
replacements. These should be derived from named linker symbols in the Genesis binary, not from
hardcoded hex literals in the spec. If the Genesis link map shifts a buffer, only the linker symbol
needs updating, not every spec entry that references it.

**Rule 6 — Semantic entry validation before every patch**
Already implemented (Build 214): the validator checks that callsite targets land at function
entry points (first instruction of a routine), not mid-body. This prevents the silent mid-body
entry bug that caused A1=0x00FF crashes. Keep this as a required pre-patch gate.

**Rule 7 — Post-patch manifest**
After every patch batch, emit a manifest listing:
- Source producer identity (arcade PC / function name)
- Transformed consumer target (Genesis symbol / address)
- Relocation adjustments applied
- Semantic signature match result

This manifest enables reproducible verification: re-apply from scratch and diff against the
reference manifest to detect any shift divergence.

---

## 10. Title Screen Application

### Title State Flow Through the New Architecture

**Main thread (before first VBlank)**:

1. `0x03AAB8`: title state machine entry, timer gate check.
2. `0x03AADE`: `bsrw 0x03AFEA` — sets frontend control mode flag (`A5+0x1E`, `0xE0FF629E`).
3. `0x03AAE2`: `bsrw 0x03AF5E` — clears WRAM descriptor staging blocks
   (`0xE0FF11FE` / `0xE0FF01BC`).
4. `0x03AAE6`: `bsrw 0x03B06C` — title prep cluster:
   - `0x03B076`: clears text shadow `0xE0FFC84C`.
   - `0x03B2AA/B0`: `jsr 0x200DC2` (scroll/control publish × 2 — already Genesis-native).
   - `0x03B2B8 → 0x03BD5E → 0x202B74 → 0x20034C`: text producer with D0=2.
   - `0x03B2BE → 0x03C4F8 → 0x03C614 → 0x200E56`: secondary text producer.

5. **ORDERING FIX REQUIRED**: Per `title_screen_graphics_call_inventory.md`:
   - Step 9: `0x03AAEC → 0x202B80 → 0x2005C4` (sprite bridge / renderer) — currently BEFORE
   - Step 10: `0x03AAF2 → 0x05A174` (logo descriptor producer) — currently AFTER
   - The renderer at `0x2005C4` reads descriptor windows at call time.
     If the producer hasn't run yet, those windows are zero → renderer outputs zero.
   - **Fix**: swap the call order: logo producer (`0x03AAF2`) must precede
     sprite bridge (`0x03AAEC`) in the `0x03AAB8` title init sequence.
   - Implementation: opcode replacement of the two `jsr`/`bsrw` instructions at
     `0x03AAEC` and `0x03AAF2` to reorder them, or replacement of the call at `0x03AAEC`
     to add a pre-call producer invocation inline.

6. `0x03AB0E → 0x05A62E`: text source setup.
7. `0x03AB20`: `movew #1, a5@(2)` — transition to substate 1.

**VBlank fires (state=1, substate=0)**:

8. Timer gate check at `0x3A8AC` — passes on first VBlank after init.
9. **GENESIS REPLACE** `0x3ADD8`: display orientation → VDP register write (layer control).
10. **GENESIS REPLACE** `0x3AD4C`: SAT staging buffer cleared (sentinel fill).
11. **GENESIS REPLACE** `0x3AE64`: text shadow cleared to space cells.
12. Text producers fire (`0x3BB48` with selectors 9, 10/11, 30, 32):
    - Already write to text shadow `0xE0FFC84C` via `genesistan_hook_text_writer_3bb48_impl`.
    - Tile cache resolves glyph tile indices; DMA A fires on misses.
13. **GENESIS NEW**: DMA C — text shadow → Plane A VRAM (`0xE000`).
14. Logo producer (`0x05A174`) already fired in Step 5 (main thread, before VBlank).
    Descriptor windows (`0xE0FF11FE`, `0xE0FF01BC`) are now non-zero.
15. Sprite renderer (`0x2005C4`) reads live descriptor tuples:
    - Resolves sprite tile indices.
    - DMA A fires on tile cache misses.
    - Builds Genesis SAT tuples in `genesistan_shadow_d00000_words`.
16. **GENESIS NEW**: DMA B — SAT staging → VRAM `0xF800`.
17. **GENESIS ADAPT** `0x200DC2`: scroll words → VDP VSRAM.

**Why this solves "consumer runs too early / nothing visible"**:

- Current failure (Builds 229/271): renderer calls `0x2005C4` when producer windows are zero
  because renderer fires BEFORE producer in the `0x03AAB8` init cluster.
- Fix: swap init call order (Step 5 above). After swap:
  - Producer fills windows → renderer reads live tuples → SAT staging has drawable entries.
- Secondary fix (SAT DMA timing): even with live descriptor tuples, SAT must be DMA'd to
  VRAM `0xF800` during VBlank, not before. The DMA B step ensures this.
- Text plane visibility (already working in Build 259/271): maintained by existing
  `0x20034C` producer path + text shadow mechanism.

---

## 11. Risks / Open Questions

1. **Title init call order swap** (producer before renderer):
   - Risk: other callers of `0x03AAEC`/`0x03AAF2` may have intentional ordering.
   - Mitigation: audit all call sites of both routines before patching.

2. **Text shadow dirty-region vs full-plane DMA**:
   - Full plane DMA (3.5KB per plane) during VBlank may consume too much time.
   - Mitigation: dirty-row scanning — scan shadow, count non-space rows, DMA only those rows.
   - Worst case (full title screen text) is manageable within Genesis VBlank budget (~4ms).

3. **Tile cache miss storms at scene transitions**:
   - First frame of a new scene may need 200–400 tile uploads = 6.4–12.8KB DMA.
   - This exceeds a single VBlank budget.
   - Mitigation: preload strategy — during the scene's producer setup phase (main thread),
     pre-resolve tile cache for the expected working set before the first VBlank.

4. **Substate 1 and ongoing title loop handlers** (beyond substate 0):
   - `0x3BA14` digit producer, `0x03ABD4/E4` per-frame sprite bridge, `0x03C614 → 0x200E56`
     secondary text producer — these all need the same buffer/VBlank treatment.
   - Not addressed in this slice; full per-frame loop design follows after first slice proves.

5. **Semantic relocation for reorder patches**:
   - Swapping `0x03AAEC` and `0x03AAF2` call order requires two opcode replacements
     at adjacent addresses. The shift from one may affect the other's recorded address.
   - Mitigation: apply both in one batch with a single relocation pass after.

6. **SAT entry count and link chain**:
   - Genesis SAT requires a valid link chain (last entry links to itself or entry 0).
   - If SAT staging buffer is only partially filled, remaining entries must be zeroed
     and the link chain must terminate correctly.
   - The renderer at `0x2005C4` must emit the link-terminator entry.

---

## 12. Recommended First Implementation Slice

Based on all the above, the smallest change that will prove the full architecture is:

**Target**: Logo sprite (RASTAN title) visible in SAT output before exception handler.

**Required changes** (opcode patches, no shims/trampolines):

1. **Swap producer/renderer call order** in `0x03AAB8` title init cluster:
   - Move `0x03AAF2 → 0x05A174` (logo producer) to execute before `0x03AAEC → 0x202B80`
     (sprite bridge / renderer) in the same init sequence.
   - Implement as opcode replacement of the call at `0x03AAEC` (or the surrounding dispatch)
     so the producer fires first, then the renderer.

2. **Verify SAT DMA executes after renderer populates staging**:
   - Confirm `genesistan_shadow_d00000_words` is DMA'd to VRAM `0xF800` in VBlank AFTER
     the renderer has built tuples.
   - If the DMA currently fires before renderer output, add the DMA call to the correct
     position in the VBlank publish sequence.

3. **Validate tile cache resolve fires for logo tile indices**:
   - Ensure that when `0x05A174` builds logo tuples, the referenced tile codes trigger
     cache lookup/miss resolution before the renderer tries to reference them in SAT.

**Validation criteria for this slice**:
- `sprite_code0 != 0x0000` in probe output (logo tile index is non-zero).
- `tilebuf_nonzero > 0` in probe (tile buffer has data).
- `sat_writes > 0` in probe (SAT staging received tuples).
- Visual: logo sprite pixel or partial row appears on screen before exception handler.

**Why this is the right first slice**:
- Title text is already visible (Build 271 baseline: "CREDI" proven).
- The remaining gap is logo sprite → SAT path.
- Fixing the producer/renderer order is a pure opcode reorder, no new translation work needed.
- Once SAT is proven visible, the full per-frame loop can build on this foundation.

**What NOT to do**:
- Do not patch individual descriptor word values to force a "test" logo — that is fake data injection.
- Do not add a C wrapper to call the producer from the renderer — that is a trampoline.
- Do not NOP the renderer call and replace it with a hardcoded SAT entry — that is a per-screen hack.
- Do not move the DMA call to a new C function detached from the VBlank path — that is a shim.
- Only reorder existing calls in the existing code paths using opcode replacement.
