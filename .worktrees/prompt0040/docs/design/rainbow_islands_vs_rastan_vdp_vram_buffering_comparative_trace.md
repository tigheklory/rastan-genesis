# Rainbow Islands vs Rastan — VDP / VRAM / Buffering Comparative Trace

## 1. Executive Summary

Rainbow Islands Genesis uses a **staged two-phase commit model**: game logic runs in the main loop (during active display) and populates WRAM staging buffers, then the VBlank handler commits those buffers to VDP hardware via DMA. Build 311 uses a **monolithic VBlank execution model**: the entire arcade state machine plus all VDP writes execute inside the VBlank interrupt handler, with no WRAM staging layer and no display-disable window.

The three most critical divergences from the proven Rainbow Islands Genesis approach are:

1. **No display-disable window** — Rainbow Islands Genesis disables display output (VDP register 1 bit 6) at the start of VBlank, performs all DMA/VRAM writes, then re-enables display. Build 311 writes to VDP with the display active, causing writes that overrun VBlank to corrupt active display.

2. **No WRAM staging layer** — Rainbow Islands Genesis stages sprite SAT, tilemap rows, palette data, and scroll values in dedicated WRAM buffers before VBlank. Build 311's opcode hooks write directly to VDP hardware during arcade tick execution. There is no intermediate staging that allows commit-time validation or batched transfer.

3. **Game logic inside VBlank** — Rainbow Islands Genesis runs game logic outside VBlank (main loop), spending VBlank time only on hardware commits (~3-5ms). Build 311 runs the entire Rastan arcade tick inside VBlank, consuming both game-logic time and VDP-write time within the same interrupt window.

**Single best next focus area**: Implement display-disable/re-enable bracketing around VDP writes in `_VINT_arcade_mode`.

---

## 2. Methodology and Sources Used

### Ghidra Analysis Targets
- **Rainbow Islands Arcade**: Interleaved program ROMs `b22-10-1.19` + `b22-11-1.20` (131,072 bytes), disassembled with `m68k-elf-objdump`. Key addresses: entry 0x0F80, main loop 0x0664, VBlank dispatched via TRAP-based task scheduler.
- **Rainbow Islands Genesis**: `Rainbow Islands - The Story of Bubble Bobble 2 (JU) [p1].bin` (524,288 bytes), disassembled with `m68k-elf-objdump`. Key addresses: VBlank handler 0x0380, main loop 0x11D2, frame sync 0x173C.
- **Rastan Arcade**: `build/regions/maincpu.bin` (393,216 bytes). Key addresses: VBlank handler 0x3A008, entry 0x3A000, mode dispatch via jump table at A5+0.
- **Build 311 Genesis**: `dist/Rastan_311.bin` (3,932,160 bytes), source at `apps/rastan/src/`. Key: `_VINT_arcade_mode` at `sega.s:202`, arcade tick trampoline at `startup_trampoline.s`.

### Project Documents Used
- `docs/research/rainbow_islands_arcade_vs_genesis_graphics_comparison.md`
- `docs/research/cadash_arcade_vs_genesis_graphics_comparison.md`
- `docs/design/pc080sn_tilemap_architecture.md`
- `docs/design/build310_vdp_and_input_timing_audit.md`
- `docs/design/build310_complete_arcade_execution_model.md`
- `docs/design/arcade_owned_graphics_replacement_design.md`
- `apps/rastan/src/boot/sega.s`, `apps/rastan/src/main.c`, `apps/rastan/src/startup_trampoline.s`, `apps/rastan/src/startup_bridge.c`

---

## 3. Rainbow Islands Arcade Graphics Update Model

Rainbow Islands arcade uses a cooperative multitasking kernel based on TRAP #1 dispatch. The 68000 runs at 0x0664 in an idle loop, with a priority-based task scheduler dispatching tasks from a queue at A5+0x0804. The VBlank interrupt drives task wakeup.

### Graphics-Related Addresses (Arcade)

| Subsystem | Arcade Address Range | Hardware Device |
|-----------|---------------------|-----------------|
| Tilemap RAM | 0xC00000–0xC0FFFF | PC080SN |
| BG scroll | 0xC20000, 0xC40000 | PC080SN control |
| FG scroll | 0xC20002, 0xC40002 | PC080SN control |
| Control | 0xC50000 | PC080SN control |
| Sprite RAM | 0xD00000–0xD03FFF | PC090OJ |
| Palette RAM | 0x200000–0x200FFF | Palette device |

### Update Sequence (Arcade)

The arcade 68000 writes directly to chip-mapped hardware windows:
1. Game logic tasks run between VBlanks, writing tile cells to PC080SN RAM incrementally
2. Sprite entries written to PC090OJ RAM at 0xD00000
3. Palette entries written to palette RAM at 0x200000
4. Scroll/control registers written to 0xC20000/0xC40000/0xC50000
5. Hardware chips render directly from their internal RAM — no staging, no commit

### Key Characteristic
Graphics hardware renders continuously from chip-internal RAM. The CPU writes incrementally. There is **no VBlank commit phase** in the arcade — the hardware reads its RAM asynchronously.

---

## 4. Rainbow Islands Genesis VDP / VRAM / Buffering Model

### VBlank Handler (0x0380–0x041A) — Disassembly Evidence

```
0x0380: movem.l %d0-%fp, -(%sp)        ; Save all registers
0x0384: move.w 0xC00004, %d0            ; Acknowledge VBlank (read VDP status)
0x038A: move.w #0x0100, 0xA11100        ; Request Z80 bus
        [wait for Z80 bus grant]
0x039C: tst.w 0xFFFFF69A                ; Check display-disable flag
0x03A4: move.w (0xFFFFF624), %d0        ; Load VDP reg 1 shadow
0x03AC: move.w %d0, 0xC00004            ; DISABLE DISPLAY (bit 6 cleared)
0x03B2: bsr 0x085A                      ; *** DMA tiles from WRAM to VRAM ***
0x03B6: bsr 0x06B0                      ; *** DMA SAT from WRAM to VDP ***
0x03BA: bsr 0x073C                      ; *** Copy tilemap rows to VRAM ***
0x03BE: bsr 0x07BE                      ; *** Upload palette to CRAM ***
0x03CA: move.w (0xFFFFF624), %d0        ; Load VDP reg 1 shadow
0x03D2: move.w %d0, 0xC00004            ; RE-ENABLE DISPLAY (bit 6 set)
0x03D8: move.l #0x40000010, 0xC00004    ; VDP: write VSRAM offset 0
0x03E2: move.l (0xFFFFF630), 0xC00000   ; Write scroll values from WRAM
0x03EA: bsr 0x04B4                      ; Read joypad inputs
0x03EE: jsr 0x1CC8                      ; RNG / timer
0x0408: jsr 0x1190A                     ; Z80 sound communication
0x040E: move.w #0, 0xA11100             ; Release Z80 bus
0x0416: movem.l (%sp)+, %d0-%fp        ; Restore registers
0x041A: rte
```

### VBlank Commit Order (Exact)

| Step | Address | Operation | Source | Destination | Method |
|------|---------|-----------|--------|-------------|--------|
| 1 | 0x03AC | Display disable | VDP reg 1 shadow at 0xFFFFF624 | VDP reg 1 | Direct write, bit 6 cleared |
| 2 | 0x085A | Tile DMA | WRAM staging → VRAM | VRAM at 0xC000 | DMA (regs 0x93–0x97), flag at 0xFFFFF690 |
| 3 | 0x06B0 | SAT DMA | WRAM 0xFFFFF800 (80×8 bytes) | VDP SAT | DMA (regs 0x93–0x97), every frame |
| 4 | 0x073C | Tilemap copy | WRAM at pointer 0xFFFFF644 | VRAM planes A/B | Direct VDP writes (row loop), flag at 0xFFFFF63C |
| 5 | 0x07BE | Palette upload | ROM/WRAM staging | CRAM at 0x0000 | Direct VDP writes (word stream), flag at 0xFFFFF680 |
| 6 | 0x03D2 | Display re-enable | VDP reg 1 shadow | VDP reg 1 | Direct write, bit 6 set |
| 7 | 0x03D8 | Scroll write | WRAM 0xFFFFF630 | VSRAM offset 0 | Direct VDP write (1 long) |
| 8 | 0x04B4 | Input read | I/O port 0xA10003 | WRAM 0xFFFFF610 | Direct port read |

### WRAM Staging Buffers (Evidence from Disassembly)

| Buffer | Address | Size | Purpose |
|--------|---------|------|---------|
| Sprite SAT | 0xFFFFF800 | 640 bytes (80 sprites × 8) | Sprite descriptor staging |
| Sprite write ptr | 0xFFFFFA80 | 4 bytes | Current SAT append position |
| Tile DMA staging | 0xFFFFFB00 | variable | Tile graphics to DMA |
| Tilemap source ptr | 0xFFFFF644 | 4 bytes | Source for tilemap row copy |
| Tilemap dest cmd | 0xFFFFF648 | 4 bytes | VDP command for plane dest |
| Tilemap request flag | 0xFFFFF63C | 2 bytes | 1=plane A, 2=plane B |
| Palette request flag | 0xFFFFF680 | 2 bytes | Nonzero = commit palette |
| Tile DMA flag | 0xFFFFF690 | 2 bytes | Nonzero = DMA tiles |
| Scroll BG | 0xFFFFF630 | 4 bytes | X/Y scroll for BG plane |
| Scroll FG | 0xFFFFF634 | 4 bytes | X/Y scroll for FG plane |
| VDP reg 1 shadow | 0xFFFFF624 | 2 bytes | Register 1 value (display on/off) |
| Frame counter | 0xFFFFF620 | 2 bytes | Incremented each VBlank |
| Odd/even frame | 0xFFFFF628 | 1 byte | Bit 0 alternates per frame |

### Main Loop (0x11D2) — Frame Sync Model

```
0x11D2: move.w #0, 0xFFFFF600           ; Clear game mode
0x11D8: move.w #0, 0xFFFFF602           ; Clear sub-mode
0x11DE: bsr 0x173C                       ; *** WAIT FOR VBLANK ***
0x11E2: move.w (0xFFFFF600), %d0        ; Read game mode
0x11E6: jsr (PC, %d0)                   ; Dispatch to mode handler
0x11EA: bra.s 0x11DE                     ; Loop back to VBlank wait
```

Frame sync at 0x173C:
```
0x1746: move.w (0xFFFFF620), %d0        ; Read frame counter
0x174A: move.w #0x2500, %sr             ; Enable interrupts (IPL=5)
0x174E: cmp.w (0xFFFFF620), %d0         ; Has counter changed?
0x1752: beq.s 0x174E                     ; No → poll again
0x1758: move.w #0x2700, %sr             ; Disable interrupts
```

### Sprite Staging Routine (0x19A2) — Evidence

```
0x19A2: movem.l %d0-%d2/%a1, -(%sp)
0x19A6: sub.w (0xFFFFF630), %d0         ; Y - scroll offset
0x19AA: add.w #128, %d0                 ; + screen offset
0x19AE: move.w %d0, (%a5)+             ; Write Y to SAT staging
0x19B0: move.w (%a1), (%a5)+           ; Write size/link
0x19B4: move.w (%a1, %d2*2 + 2), (%a5)+ ; Write tile
0x19B8: add.w #128, %d1                ; X + screen offset
0x19BC: move.w %d1, (%a5)+             ; Write X to SAT staging
0x19BE: move.l %a5, (0xFFFFFA80)       ; Update write pointer
```

This conclusively shows: sprites are built in WRAM at the current append pointer (starting 0xFFFFFA80), then DMA'd to VDP SAT during VBlank by the handler at 0x06B0.

### Palette Commit (0x07BE) — Evidence

```
0x07BE: cmp.w #1, (0xFFFFF680)          ; Palette update requested?
        [if set, load palette data from ROM table]
0x0802: move.l #0xFF0000, %fp           ; Set WRAM staging destination
        bsr 0x18B2                       ; Decompress/copy palette to WRAM
0x083E: move.l #0x40000002, 0xC00004    ; VDP: write CRAM at offset 0
0x084E: move.w (%a2)+, (%a3)            ; Stream palette words to VDP data
        dbf %d7, 0x84E                   ; Loop all entries
0x0854: clr.w (0xFFFFF680)              ; Clear request flag
```

Two-phase: palette first decompressed to WRAM staging at 0xFF0000, then streamed to CRAM via VDP data port.

---

## 5. Rainbow Islands Arcade → Genesis Translation Model

### Translation Strategy: Intent-to-VDP-Primitive Rewrite

Rainbow Islands Genesis does NOT emulate the arcade hardware. It **rewrites** the arcade game logic to use Genesis VDP primitives directly. This is a complete native port.

| Arcade Behavior | Genesis Translation |
|----------------|-------------------|
| CPU writes PC080SN tile RAM directly | Game logic writes WRAM staging buffer, VBlank copies rows to VDP plane |
| PC080SN renders from internal RAM continuously | VDP renders from VRAM; commit happens once per VBlank |
| CPU writes PC090OJ sprite RAM directly | Game logic builds SAT in WRAM 0xFFFFF800; VBlank DMAs to VDP SAT |
| CPU writes palette RAM at 0x200000 | Game logic sets palette request flag; VBlank uploads to CRAM |
| CPU writes scroll regs at 0xC20000/0xC40000 | Game logic writes WRAM 0xFFFFF630/0xFFFFF634; VBlank writes VSRAM |
| Hardware renders asynchronously | VDP renders from committed VRAM/CRAM/VSRAM |

### Key Translation Principles

1. **WRAM staging is mandatory** — No direct-to-VDP writes during game logic. Everything is buffered.
2. **VBlank is commit-only** — VBlank handler does hardware commits, input reads, and frame counting. No game logic.
3. **Display-disable bracketing** — Display output is disabled during DMA/VRAM writes, then re-enabled after all commits. This extends the safe write window.
4. **Flag-triggered commits** — Palette, tile DMA, and tilemap updates are conditional (flag-triggered). SAT DMA and scroll writes happen every frame.
5. **DMA for bulk transfers** — SAT and tile data use DMA. Tilemap rows use direct VDP writes but in a tight loop.

---

## 6. Rastan Arcade Graphics Update Model

### VBlank Handler (0x3A008) — Disassembly Evidence

```
0x3A008: ori.w #0x0F00, %sr             ; Mask interrupts (IPL=7)
0x3A00C: clr.w 0x350008                 ; Hardware register clear
0x3A012: move.w %d0, 0x3C0000           ; Watchdog/acknowledge
0x3A018: move.w A5+2, %d0               ; Read game mode
0x3A01C: cmp.w #2, %d0                  ; If in gameplay modes 2-3:
0x3A028:   bsr 0x3A126                   ;   Process input queue
0x3A02C:   tst.w A5+0                    ;   If game active:
0x3A03A:     bsr 0x41F30                 ;     Run gameplay tick
0x3A03E: bsr 0x3AB7C                    ; Subsystem update 1 (scroll/tilemap)
0x3A042: bsr 0x3ABE2                    ; Subsystem update 2 (sprite/palette)
0x3A046: bsr 0x3A0A8                    ; DIP/service input reading
0x3A04A: bsr 0x3EEFA                    ; Subsystem 3 (palette convert)
0x3A04E: bsr 0x3EF5C                    ; Subsystem 4 (scroll write)
0x3A052: push return address 0x3A074
0x3A05A: dispatch to mode handler via jump table
0x3A074: jsr 0x55CA2                     ; Timer/dispatch helper
0x3A07A: andi.w #0xF0FF, %sr            ; Unmask interrupts
0x3A07E: rte
```

### Key Characteristic

Rastan arcade, like many Taito arcade games, runs its **entire game tick inside the VBlank interrupt handler**. This includes:
- Input processing
- Gameplay logic (0x41F30)
- Scroll/tilemap updates (0x3AB7C)
- Sprite/palette updates (0x3ABE2)
- Palette conversion (0x3EEFA)
- Mode-specific dispatch

The CPU writes directly to PC080SN/PC090OJ/palette hardware windows within this VBlank tick. The hardware renders asynchronously from its internal state.

---

## 7. Build 311 Genesis Actual Update Model

### VBlank Handler (`_VINT_arcade_mode`, sega.s:202–209)

```asm
_VINT_arcade_mode:
    movem.l %d0-%d7/%a0-%a6, -(%sp)     ; Save registers
    jsr genesistan_refresh_arcade_inputs  ; Read joypads → shadow regs
    jsr genesistan_run_arcade_tick_lean   ; Run ENTIRE arcade state machine
    jsr sanitize_arcade_workram           ; Zero C-window pointers
    jsr genesistan_palette_commit_asm     ; CLCS → CRAM (64 colors)
    movem.l (%sp)+, %d0-%d7/%a0-%a6     ; Restore registers
    rte
```

### Frame Update Sequence (Actual, Ordered)

| Step | When | Function | VDP Resource | Method |
|------|------|----------|-------------|--------|
| 1 | VBlank start | `genesistan_refresh_arcade_inputs` | None | Read I/O → WRAM shadow |
| 2 | During arcade tick | `genesistan_scroll_from_workram_vdp` | VSRAM (H/V scroll) | Direct VDP register writes via SGDK wrappers |
| 3 | During arcade tick | `genesistan_asm_tilemap_commit_bg` | VRAM nametable 0xC000 | Direct VDP control+data per cell |
| 4 | During arcade tick | `genesistan_asm_tilemap_commit_fg` | VRAM nametable 0xE000 | Direct VDP control+data per cell |
| 5 | During arcade tick | `genesistan_bulk_tilemap_commit` | VRAM nametables | Direct VDP control+data (block) |
| 6 | During arcade tick | `genesistan_render_sprites_vdp_asm` | VRAM tiles (DMA) + SAT 0xF800 | DMA for tiles, direct for SAT |
| 7 | During arcade tick | `genesistan_hook_text_writer_3bb48_impl` | VRAM nametable plane A | Via `VDP_setTileMapXY` (SGDK wrapper) |
| 8 | During arcade tick | `genesistan_hook_text_writer_3c3fe` | VRAM nametable plane A | Via `VDP_setTileMapXY` (SGDK wrapper) |
| 9 | During arcade tick | `genesistan_preload_scene_tiles` | VRAM tile data | DMA via `VDP_loadTileData` |
| 10 | Post-tick | `sanitize_arcade_workram` | None | Zero C-window pointers |
| 11 | Post-tick | `genesistan_palette_commit_asm` | CRAM (64 colors) | Direct VDP control+data stream |

### What Is Staged vs Direct

| Subsystem | Staging? | Details |
|-----------|----------|---------|
| Sprite tiles | Partial | DMA from ROM to VRAM during arcade tick |
| Sprite SAT | No staging | Written directly to VDP SAT (0xF800) during arcade tick |
| Tilemap cells | No staging | Written directly to VDP planes during arcade tick, one cell at a time |
| Palette | Partial | Arcade writes to `genesistan_palette_clcs` (WRAM), then `palette_commit_asm` converts and writes to CRAM post-tick |
| Scroll | No staging | Written directly to VDP registers during arcade tick via SGDK wrappers |
| Text | No staging | Written directly to VDP plane A during arcade tick via `VDP_setTileMapXY` |

### What Is NOT Present in Build 311

- No display-disable/re-enable bracketing
- No WRAM SAT staging buffer (sprites go directly to VDP)
- No WRAM tilemap staging buffer (cells go directly to VDP)
- No flag-triggered commit system
- No separation of game logic from VDP writes
- No DMA for SAT commit (SAT is written entry-by-entry)

---

## 8. Rainbow Islands Genesis vs Build 311 Comparison

### A. Tile Data / Graphics Upload

| Aspect | Rainbow Islands Genesis | Build 311 |
|--------|----------------------|-----------|
| Source | ROM → WRAM staging at 0xFFFFFB00 | ROM → VRAM directly via `VDP_loadTileData` DMA |
| Trigger | Flag at 0xFFFFF690, committed during VBlank | Called from `genesistan_preload_scene_tiles` during arcade tick or at scene start |
| Timing | VBlank only (display disabled) | During arcade tick inside VBlank (display NOT disabled) |
| Display state | Display OFF during DMA | Display ON during DMA |

**Assessment**: Build 311's tile DMA runs with display on. If DMA occurs during active display (overrun), it can corrupt the display output. Rainbow Islands avoids this by disabling display first.

### B. Tilemap / Background Writes

| Aspect | Rainbow Islands Genesis | Build 311 |
|--------|----------------------|-----------|
| Staging | Rows staged in WRAM at pointer 0xFFFFF644 | No staging — written directly to VDP |
| Commit | Flag-triggered row copy during VBlank (display off) | Per-cell VDP control+data writes during arcade tick |
| Granularity | Full rows (40 words per row) | Individual cells (1 control + 1 data per cell) |
| Ordering | After tile DMA, before palette | Whenever arcade code hits scroll/tilemap opcode hooks |
| Display state | Display OFF | Display ON |

**Assessment**: Build 311 writes individual tilemap cells with VDP control+data pairs (2 writes per cell). For a 16-descriptor strip with 4 cells each = 64 cells = 128 VDP writes per hook call. Rainbow Islands writes full rows in tight loops. Build 311's per-cell approach is slower and unprotected by display-disable.

### C. Sprites

| Aspect | Rainbow Islands Genesis | Build 311 |
|--------|----------------------|-----------|
| Tile upload | DMA from WRAM staging, display off | DMA from ROM during arcade tick, display on |
| SAT staging | Full SAT built in WRAM 0xFFFFF800 | No staging — written directly to VDP SAT |
| SAT commit | Single DMA from WRAM to VDP SAT (0x9401/0x9340 setup) | Individual VDP writes during arcade tick |
| Link assignment | VBlank handler assigns link chain (0x06B0 loop) | Assembly sprite renderer writes entries directly |
| Display state | Display OFF during DMA | Display ON |

**Assessment**: Rainbow Islands DMAs the entire SAT in one operation (~640 bytes, takes ~160µs via DMA). Build 311 writes individual SAT entries with per-entry VDP control+data setup. The DMA approach is faster and atomic — the VDP sees a complete, consistent SAT. Build 311's per-entry approach means the VDP may read a partially-updated SAT.

### D. Palette

| Aspect | Rainbow Islands Genesis | Build 311 |
|--------|----------------------|-----------|
| Source | ROM/decompressed data → WRAM 0xFF0000 | Arcade CLCS buffer `genesistan_palette_clcs[64]` |
| Staging | Two-phase: decompress to WRAM, then stream to CRAM | One intermediate: arcade writes CLCS, then asm converts+streams |
| Commit | Flag-triggered during VBlank, display off | Post-tick, after arcade tick completes |
| Conversion | None needed (data pre-converted for Genesis) | xRGB-444 → Genesis 0BBB0GGG0RRR0 in assembly |
| Display state | Display OFF | Display ON |

**Assessment**: Build 311's palette path is structurally sound — it's the closest to Rainbow Islands' model because it uses a WRAM intermediary (CLCS buffer) and commits in a post-tick phase. The main weakness is lack of display-disable bracketing.

### E. Scroll

| Aspect | Rainbow Islands Genesis | Build 311 |
|--------|----------------------|-----------|
| Staging | WRAM 0xFFFFF630/0xFFFFF634 | Arcade WRAM at A5+0x10EC/0x10EE/0x10AE/0x10B0 |
| Commit | Single long write to VSRAM during VBlank, after all other commits | Multiple writes during arcade tick via SGDK wrappers |
| Frequency | Once per frame (VBlank handler) | Multiple times per frame (every opcode hook hit, up to 10 sites) |
| Display state | Display ON (after re-enable, safe since VSRAM write is fast) | Display ON |

**Assessment**: Build 311 writes scroll registers multiple times per frame as arcade code hits scroll opcode hooks. Rainbow Islands writes once. Multiple scroll writes are not harmful (VDP latches the last value), but they waste cycles. The real issue is timing: Build 311's scroll writes happen at unpredictable points during the arcade tick.

---

## 9. Rastan Arcade vs Rainbow Islands Arcade Comparison

### Structural Similarities

| Aspect | Rastan Arcade | Rainbow Islands Arcade |
|--------|--------------|----------------------|
| PC080SN tilemap chip | Yes (0xC00000) | Yes (0xC00000) |
| PC090OJ sprite chip | Yes (0xD00000) | Yes (0xD00000) |
| Palette RAM | 0x200000 | 0x200000 |
| Scroll registers | 0xC20000/0xC40000 | 0xC20000/0xC40000 |
| CPU writes directly to chip RAM | Yes | Yes |
| Hardware renders asynchronously | Yes | Yes |

### Structural Differences

| Aspect | Rastan Arcade | Rainbow Islands Arcade |
|--------|--------------|----------------------|
| VBlank model | Monolithic — entire game tick in VBlank | Task scheduler — game logic dispatched as tasks between VBlanks |
| Game logic timing | Inside VBlank handler | Outside VBlank (cooperative multitasking) |
| C-Chip | None | Yes (protection/gameplay) |
| Workram base | 0x10C000 (A5 register) | 0x10C000 (A5 register) — same convention |

### Key Difference: Execution Model

Rainbow Islands arcade uses a **cooperative task scheduler** (TRAP #1 based) where game logic runs as scheduled tasks between VBlanks. The VBlank interrupt merely wakes up the scheduler. Rastan arcade runs its **entire game tick inside the VBlank interrupt handler**.

This is important because it means:
- Rainbow Islands arcade already had a "game logic outside interrupt, hardware commits inside interrupt" separation
- Rastan arcade does NOT have this separation — everything is in the interrupt
- The Rainbow Islands Genesis port preserved this separation naturally
- Porting Rastan to Genesis requires **introducing** this separation, not preserving it

### Applicability of Rainbow Islands as Template

Rainbow Islands Genesis is valid as a reference for:
- ✅ WRAM staging buffer patterns and layout
- ✅ VBlank commit ordering
- ✅ Display-disable bracketing technique
- ✅ DMA usage for SAT and tile transfers
- ✅ Flag-triggered conditional commits
- ✅ Frame sync model (poll frame counter)

Rainbow Islands Genesis is NOT directly copyable for:
- ❌ Game logic structure (Rainbow Islands already had task-based separation)
- ❌ Exact WRAM buffer addresses/layouts (game-specific)
- ❌ Tile data formats (different tile counts, sizes)
- ❌ C-Chip handling (not applicable to Rastan)

---

## 10. Where Build 311 Appears Off Track

### Issue 1: No Display-Disable Bracketing (CRITICAL)

**Rainbow Islands Genesis**: Disables VDP display (register 1, bit 6) at the start of VBlank commit, performs all DMA/VRAM writes, then re-enables display. This:
- Prevents visible corruption from writes during active display
- Extends the safe VRAM write window beyond VBlank
- Makes DMA transfers invisible to the viewer

**Build 311**: Never disables display. All VDP writes happen with the display active. If the arcade tick + VDP writes exceed the VBlank window (which is likely given the Rastan arcade tick's complexity), writes spill into active display and cause visual corruption.

**Evidence**: Rainbow Islands Genesis at 0x03A4–0x03AC disables display; at 0x03CA–0x03D2 re-enables it. Build 311's `_VINT_arcade_mode` (sega.s:202–209) has no equivalent.

### Issue 2: No WRAM Staging Layer (MAJOR)

**Rainbow Islands Genesis**: All graphics subsystems stage data in WRAM before VBlank commits it. This provides:
- Atomic updates (VDP sees complete, consistent data)
- Decoupled timing (game logic writes at any time, commit at VBlank)
- Opportunity for validation or transformation before commit

**Build 311**: Opcode hooks write directly to VDP during the arcade tick. The VDP sees partially-updated state between hook calls. A tilemap strip may be half-written when the next VBlank fires (if overrun).

**Most impactful**: Sprite SAT has no staging buffer. In Rainbow Islands Genesis, the full 80-sprite SAT is DMA'd atomically. In Build 311, individual sprite entries are written to VDP during the arcade tick, meaning the VDP may display a mix of old and new sprite positions.

### Issue 3: Game Logic Inside VBlank (STRUCTURAL)

**Rainbow Islands Genesis**: Main loop runs game logic (~60% of frame time available), VBlank does hardware commits only (~3-5ms).

**Build 311**: The entire Rastan arcade tick runs inside VBlank. The arcade tick includes game logic, AI, collision detection, scroll calculations, and all graphics hook dispatch. This must all complete within the VBlank + display-disabled window.

**Time budget**: Genesis VBlank is ~4.5ms (NTSC). Display-disabled mode adds additional safe time. Rastan's arcade tick may require 5-10ms of game logic alone, plus VDP write time. Without display-disable, the time budget is extremely tight.

### Issue 4: Multiple Redundant VDP Writes Per Frame (MINOR)

Scroll registers are written up to 10 times per frame (once per opcode hook hit). This is wasteful but not directly harmful since the VDP latches the last value. However, it consumes precious VBlank cycles.

---

## 11. Ranked Top 3 Off-Track Areas

### 1. Display-Disable Bracketing (MOST LIKELY OFF-TRACK)

**Subsystem**: VDP register 1, bit 6 (display output enable)

**Reason**: Rainbow Islands Genesis disables display output before ANY DMA or VRAM writes, then re-enables after all commits complete. Build 311 writes to VDP with display fully active. When writes extend past the VBlank window into active display (which is extremely likely given the Rastan arcade tick runs entirely inside VBlank), the VDP reads partially-updated VRAM, CRAM, or SAT during active scanline rendering, producing corrupted or torn output.

**Evidence**:
- Rainbow Islands Genesis: 0x03AC writes VDP reg 1 with bit 6 cleared (display off); 0x03D2 writes with bit 6 set (display on)
- Build 311 sega.s:202–209: No display-disable instruction. VDP writes occur with display active.
- Build 310 VDP audit confirms all VDP writes happen during VBlank but with no guarantee they complete before active display begins

**This is the single most likely cause of visible rendering issues.** It is also the simplest fix: add `move.w` to VDP control port to disable display at the start of `_VINT_arcade_mode`, re-enable at the end (before `rte`).

### 2. No WRAM SAT Staging (SECOND MOST LIKELY)

**Subsystem**: Sprite Attribute Table commit path

**Reason**: Rainbow Islands Genesis builds the complete SAT in WRAM at 0xFFFFF800, assigns link chain values, then DMAs the entire buffer to VDP SAT in one atomic transfer. Build 311's sprite renderer (`genesistan_render_sprites_vdp_asm`) writes individual SAT entries to VDP during the arcade tick. The VDP may read a partially-updated SAT during scanline rendering if the sprite hook fires late in the arcade tick and writes overlap with active display.

**Evidence**:
- Rainbow Islands Genesis: SAT staging at 0xFFFFF800, link assignment loop at 0x06B0–0x0738, DMA setup at 0x0710–0x072A
- Build 311: `genesistan_render_sprites_vdp_asm` (startup_trampoline.s:146–197) writes directly to VDP SAT via VDP data port with no WRAM staging
- The atomic DMA approach ensures the VDP always sees a complete, consistent SAT

### 3. Tilemap Commit Granularity (THIRD MOST LIKELY)

**Subsystem**: Background/foreground tilemap nametable writes

**Reason**: Rainbow Islands Genesis copies tilemap data in row-sized blocks during VBlank (40 words per row in a tight `dbf` loop). Build 311 writes individual tilemap cells with separate VDP control+data pairs (2 VDP writes per cell), which is ~2× slower per cell due to the per-cell address setup overhead. For a 16-descriptor × 4-cell strip = 128 VDP writes, this consumes significant VBlank time.

**Evidence**:
- Rainbow Islands Genesis: 0x1A70–0x1AAE writes rows in `dbf` loops with pre-set VDP destination, advancing destination by 0x800000 (next row) between rows
- Build 311: `genesistan_asm_tilemap_commit_bg/fg` (startup_trampoline.s:458–712) computes VDP control word per cell, then writes control+data

---

## 12. Single Best Next Focus Area

**Display-disable/re-enable bracketing in `_VINT_arcade_mode`.**

This is:
1. The most likely cause of visible rendering issues
2. The simplest fix (add 2-4 assembly instructions)
3. Directly validated by the Rainbow Islands Genesis reference implementation
4. Required regardless of whether other staging improvements are made later

**Implementation target**: Add VDP register 1 write with bit 6 cleared at the start of `_VINT_arcade_mode` (after register save, before any JSR calls), and VDP register 1 write with bit 6 set at the end (after `genesistan_palette_commit_asm`, before register restore).

This extends the safe VRAM write window from ~4.5ms (VBlank only) to the full frame time (~16.7ms for NTSC), allowing the entire arcade tick to run with unlimited VDP access.

---

## 13. Final Verdict

Build 311's execution model (running the full arcade tick inside VBlank) is structurally valid — Rastan arcade itself does the same thing. But the Genesis VDP is NOT the same as arcade hardware. The arcade's PC080SN/PC090OJ chips read their RAM asynchronously and tolerate writes at any time. The Genesis VDP cannot safely accept VRAM/CRAM/VSRAM writes during active display without display-disable protection.

Rainbow Islands Genesis solves this by:
1. Disabling display before writing
2. Staging all data in WRAM before committing
3. Using DMA for bulk transfers
4. Separating game logic from VDP commits

Build 311 does none of these. The display-disable bracketing is the minimum required fix and the clear next step. WRAM staging and DMA improvements are subsequent optimizations that would further align with the proven Rainbow Islands approach.
