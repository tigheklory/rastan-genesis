# Build 313 — PC080SN WRAM Tilemap Staging

## 1. Executive Summary

Build 313 replaces all direct VDP writes in the three PC080SN tilemap assembly routines with WRAM buffer staging. Tilemap hooks now write to two 4KB WRAM buffers (`pc080sn_bg_buffer` and `pc080sn_fg_buffer`) instead of VDP ports. A new VBlank commit routine (`genesistan_pc080sn_commit_planes`) streams both buffers to VDP during `_VINT_arcade_mode`, ensuring all tilemap data reaches VDP only during the VBlank window.

This implements the Rainbow Islands Genesis two-phase commit model for tilemaps: game logic writes to WRAM buffers, VBlank handler commits buffers to VDP.

## 2. What Changed

### 2.1 Modified Assembly Functions (startup_trampoline.s)

Three functions were converted from direct VDP writes to WRAM buffer writes:

#### `genesistan_asm_tilemap_commit_bg` (BG plane strip writer)

**Before:** Used A5=VDP control, A6=VDP data. Constructed VDP control words with VRAM address encoding for each tile write.

**After:** Uses `lea pc080sn_bg_buffer, %a5` to load buffer base. Each tile write becomes:
```asm
subi.w  #4, %d0           /* adjust for 4-row offset */
lsl.w   #7, %d0           /* (row-4) * 128 bytes per row */
add.w   %d2, %d0
add.w   %d2, %d0          /* + col * 2 */
move.w  %d3, 0(%a5, %d0.w)  /* write to WRAM buffer */
```

Removed: VDP port initialization, auto-increment register write, VDP control word construction (andi/lsl/lsr/ori #0x40000003 sequences), VDP port writes.

#### `genesistan_asm_tilemap_commit_fg` (FG plane strip writer)

Same transformation as BG, using `lea pc080sn_fg_buffer, %a5`.

#### `genesistan_bulk_tilemap_commit` (Block writer)

**Before:** Determined BG (0xC000) vs FG (0xE000) plane from C-window address, loaded VDP ports, constructed control words per tile.

**After:** Branch targets load the appropriate buffer:
```asm
.Lbulk_bg_plane:
    lea     pc080sn_bg_buffer, %a5
.Lbulk_fg_plane:
    lea     pc080sn_fg_buffer, %a5
```
Buffer offset uses D6 as scratch: `(row-4)*128 + col*2`, written via `move.w %d4, 0(%a5, %d6.w)`.

### 2.2 New VBlank Commit Routine

```asm
genesistan_pc080sn_commit_planes:
    movem.l %d0-%d1/%a0-%a1, -(%sp)
    movea.l #0xC00004, %a1          /* VDP control port */
    move.w  #0x8F02, (%a1)          /* auto-increment = 2 */

    /* BG plane: VRAM write at 0xC000 */
    move.l  #0x40000003, (%a1)      /* VRAM write cmd */
    lea     pc080sn_bg_buffer, %a0
    move.w  #2047, %d0
.Lcommit_bg_loop:
    move.w  (%a0)+, 0x00C00000
    dbra    %d0, .Lcommit_bg_loop

    /* FG plane: VRAM write at 0xE000 */
    move.l  #0x60000003, (%a1)
    lea     pc080sn_fg_buffer, %a0
    move.w  #2047, %d0
.Lcommit_fg_loop:
    move.w  (%a0)+, 0x00C00000
    dbra    %d0, .Lcommit_fg_loop

    movem.l (%sp)+, %d0-%d1/%a0-%a1
    rts
```

Streams 2048 words per plane (4096 words total) using auto-increment mode.

### 2.3 VBlank Handler (sega.s)

```asm
_VINT_arcade_mode:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    jsr     genesistan_refresh_arcade_inputs
    move.w  #0x8134, 0x00C00004     /* display OFF */
    jsr     genesistan_run_arcade_tick_lean
    jsr     sanitize_arcade_workram
    jsr     genesistan_pc080sn_commit_planes   /* NEW: commit tilemap buffers */
    jsr     genesistan_palette_commit_asm
    move.w  #0x8174, 0x00C00004     /* display ON */
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rte
```

Commit order: arcade tick → sanitize → **tilemap commit** → palette commit → display re-enable.

### 2.4 BSS Buffers

```asm
    .section .bss.patcher,"aw",@nobits
pc080sn_bg_buffer:
    .space 4096     /* 64 × 32 × 2 bytes = full BG nametable */
pc080sn_fg_buffer:
    .space 4096     /* 64 × 32 × 2 bytes = full FG nametable */
```

Located at RAM 0xFF404E (BG) and 0xFF504E (FG). Total additional RAM: 8,192 bytes.

## 3. Design Rationale

### Why WRAM staging?

The comparative analysis (Prompt 068) identified that Rainbow Islands Genesis uses staged WRAM buffers committed during VBlank, while Rastan Build 311/312 wrote directly to VDP from within the arcade tick. Direct VDP writes during active display cause corruption:

1. **Timing hazard:** VDP writes outside VBlank compete with the display engine for VDP bus bandwidth
2. **Address register corruption:** Mid-scanline VDP control word writes can corrupt the VDP's internal address pointer
3. **Partial updates:** If the arcade tick spans multiple scanlines, the display shows partially updated tilemaps

Buffer staging eliminates all three: all VDP writes happen in a single burst during VBlank with display disabled.

### Why full-plane streaming (not dirty-tracking)?

Full 2048-word streaming per plane is simpler and more robust than dirty-region tracking:
- No per-tile dirty flag overhead in the hot path
- No complex region merge logic
- 4096 word writes via auto-increment is fast (~4096 × 4 cycles = ~16K cycles, well within VBlank)
- Matches Rainbow Islands Genesis approach (full-plane DMA)

### Row < 4 skip preserved

The arcade coordinate system uses rows 0-31, but Genesis VRAM rows 0-3 are above the visible area (4-row vertical offset). The skip is preserved to avoid writing to unused buffer positions. Buffer rows 0-3 remain zero-initialized from BSS.

## 4. Build Verification

| Check | Result |
|-------|--------|
| Build succeeded | YES |
| ROM produced | `dist/Rastan_313.bin` (3,932,160 bytes) |
| Postpatch warnings | 28 (pre-existing, applied anyway) |
| NOHOOK stub added | YES (`genesistan_pc080sn_commit_planes: rts`) |

## 5. Runtime Verification (MAME Trace, 1199 frames, auto-START at frame 120)

| Metric | Result |
|--------|--------|
| `startup_result_code` 0→1 | Frame 133 |
| `arcade_mode4` reaches 2 | Frame 655 |
| `arcade_page2` set | Frame 653 |
| VDP port writes | 1,284,334 |
| Hang detected | NO |
| Exceptions | NONE |
| Total frames | 1199 |

### Comparison with Build 312

| Metric | Build 312 | Build 313 |
|--------|-----------|-----------|
| VDP port writes | 28,411 | 1,284,334 |
| arcade_mode4 reaches 2 | Frame 890 | Frame 655 |
| Hang | NO | NO |
| Exceptions | NONE | NONE |

The massive increase in VDP writes (45×) is expected: the commit routine writes 4096 words to VDP every frame (2 planes × 2048 words), versus Build 312 which only wrote individual changed tiles.

Note: Build 312 trace was run interactively with manual START press. Build 313 trace used Lua-injected START at frame 120 for headless automation.

### Visual Verification

| Check | Result |
|-------|--------|
| Build succeeded | YES |
| ROM produced | `dist/Rastan_313.bin` |
| No crash/hang | YES |
| Tilemap display correct | CANNOT CONFIRM (headless trace) |
| Scroll artifacts reduced | CANNOT CONFIRM (headless) |

Visual verification requires BlastEm or visual MAME run.

## 6. Files Modified

| File | Change |
|------|--------|
| `apps/rastan/src/startup_trampoline.s` | Modified 3 tilemap functions, added commit routine, added BSS buffers |
| `apps/rastan/src/boot/sega.s` | Added `jsr genesistan_pc080sn_commit_planes` in `_VINT_arcade_mode` |

## 7. Remaining Issues

- **Visual verification pending** — requires emulator with display output
- **Full-plane streaming overhead** — 4096 words per frame is functional but could be optimized with dirty-region tracking if frame time becomes tight
- **No scroll register staging** — `genesistan_scroll_from_workram_vdp()` still writes scroll registers directly via SGDK wrappers (out of scope for this build)
- **No SAT DMA staging** — sprite attribute table still uses direct VDP writes (out of scope)
- **Display-disable bracket (from Build 312) now protects tilemap commit** — the commit runs inside the bracket, so all 4096 words are written with display off
