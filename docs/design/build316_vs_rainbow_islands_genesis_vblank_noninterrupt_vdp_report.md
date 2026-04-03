# Build 316 vs Rainbow Islands Genesis — VBlank & Non-Interrupt VDP Execution Report

## 1. Executive Summary

This report compares the complete VDP execution model of **Rastan Build 316** against **Rainbow Islands Genesis**, covering both the VBlank interrupt path and all non-interrupt VDP access. Build 316 has evolved significantly from Build 311 — it now includes display-disable bracketing, WRAM tilemap staging buffers, and a forced clean VRAM init at handoff — but still diverges from the Rainbow Islands model in game-logic placement, SAT commit strategy, and scroll commit timing.

---

## 2. VBlank Interrupt Path Comparison

### 2.1 Rainbow Islands Genesis VBlank Handler (0x0380–0x041A)

```
Entry:
  movem.l %d0-%fp, -(%sp)             Save all registers
  move.w  0xC00004, %d0               Acknowledge VBlank (read VDP status)
  move.w  #0x0100, 0xA11100           Request Z80 bus
  [wait for Z80 bus grant]

Commit Phase (display disabled):
  1. move.w (0xFFFFF624), %d0          Load VDP reg 1 shadow
     move.w %d0, 0xC00004             DISPLAY OFF (bit 6 cleared)
  2. bsr 0x085A                        DMA tiles from WRAM staging → VRAM
  3. bsr 0x06B0                        DMA SAT from WRAM 0xFFFFF800 → VDP SAT
  4. bsr 0x073C                        Copy tilemap rows from WRAM → VRAM planes
  5. bsr 0x07BE                        Upload palette from WRAM staging → CRAM
  6. move.w (0xFFFFF624), %d0          Load VDP reg 1 shadow
     move.w %d0, 0xC00004             DISPLAY ON (bit 6 set)
  7. move.l #0x40000010, 0xC00004      Write scroll to VSRAM (single long)

Post-commit:
  8. bsr 0x04B4                        Read joypad inputs
  9. jsr 0x1CC8                        RNG / timer update
  10. jsr 0x1190A                       Z80 sound communication
  11. move.w #0, 0xA11100              Release Z80 bus
  movem.l (%sp)+, %d0-%fp             Restore registers
  rte
```

**Key characteristics:**
- VBlank is **commit-only** — zero game logic
- Display-disable uses a **shadow register** (0xFFFFF624) rather than hardcoded values
- All commits are **flag-triggered** (tile DMA at 0xFFFFF690, tilemap at 0xFFFFF63C, palette at 0xFFFFF680)
- SAT DMA runs **unconditionally** every frame
- Scroll write happens **after** display re-enable (safe because VSRAM write is fast)
- Z80 bus held throughout commit phase

### 2.2 Rastan Build 316 VBlank Handler (_VINT_arcade_mode, sega.s:202–214)

```
Entry:
  movem.l %d0-%d7/%a0-%a6, -(%sp)     Save all registers

Phase 1 — Input:
  1. jsr genesistan_refresh_arcade_inputs    Read joypads → shadow regs

Phase 2 — Display-disable bracket open:
  2. move.w #0x8134, 0x00C00004        DISPLAY OFF (hardcoded 0x34)

Phase 3 — Arcade tick (game logic + hooks):
  3. jsr genesistan_run_arcade_tick_lean
     └─ Enters Rastan arcade code at 0x03A008
     └─ Runs ENTIRE game state machine
     └─ Opcode hooks fire during execution:
        ├─ genesistan_scroll_from_workram_vdp    → VDP VSRAM writes (4 calls)
        ├─ genesistan_asm_tilemap_commit_bg       → WRAM buffer writes (not VDP)
        ├─ genesistan_asm_tilemap_commit_fg       → WRAM buffer writes (not VDP)
        ├─ genesistan_bulk_tilemap_commit          → WRAM buffer writes (not VDP)
        ├─ genesistan_render_sprites_vdp_asm      → VDP DMA + SAT writes
        ├─ genesistan_hook_text_writer_3bb48_impl → WRAM buffer writes (not VDP)
        ├─ genesistan_hook_text_writer_3c3fe      → WRAM buffer writes (not VDP)
        └─ genesistan_bulk_preload_check          → VDP DMA (scene transitions)

Phase 4 — Post-tick sanitize:
  4. jsr sanitize_arcade_workram        Zero C-window pointers

Phase 5 — Buffered commits:
  5. jsr genesistan_pc080sn_commit_planes
     ├─ BG: VRAM write 0xC000, 2048 words from pc080sn_bg_buffer
     └─ FG: VRAM write 0xE000, 2048 words from pc080sn_fg_buffer
  6. jsr genesistan_palette_commit_asm
     └─ CRAM write: 64 colors from genesistan_palette_clcs[]

Phase 6 — Display-disable bracket close:
  7. move.w #0x8174, 0x00C00004        DISPLAY ON (hardcoded 0x74)

Exit:
  movem.l (%sp)+, %d0-%d7/%a0-%a6     Restore registers
  rte
```

**Key characteristics:**
- VBlank runs **game logic + commits** in same interrupt
- Display-disable uses **hardcoded** register values (not shadow register)
- Tilemap hooks now write to **WRAM buffers** (Build 313+), committed in Phase 5
- Text writer hooks also write to **WRAM buffers** (Build 315+)
- Scroll and sprite hooks still write **directly to VDP** during arcade tick
- No flag-triggered commit system — buffers committed unconditionally every frame
- No Z80 bus coordination
- No VBlank acknowledgement read

### 2.3 Side-by-Side VBlank Execution Order

| Step | Rainbow Islands Genesis | Rastan Build 316 |
|------|------------------------|-------------------|
| 1 | Acknowledge VBlank (read status) | — (not done) |
| 2 | Request Z80 bus | — (not done) |
| 3 | Display OFF (shadow reg) | Read joypad inputs |
| 4 | DMA tiles WRAM→VRAM (flagged) | Display OFF (hardcoded) |
| 5 | DMA SAT WRAM→VDP (every frame) | **Run entire arcade tick** (game logic + VDP hooks) |
| 6 | Copy tilemap rows WRAM→VRAM (flagged) | Sanitize arcade workram |
| 7 | Upload palette to CRAM (flagged) | Commit tilemap buffers → VRAM (unconditional) |
| 8 | Display ON (shadow reg) | Commit palette CLCS → CRAM |
| 9 | Write scroll to VSRAM | Display ON (hardcoded) |
| 10 | Read joypad inputs | — |
| 11 | RNG/timer update | — |
| 12 | Z80 sound communication | — |
| 13 | Release Z80 bus | — |

---

## 3. Non-Interrupt VDP Access Comparison

### 3.1 Rainbow Islands Genesis Non-Interrupt VDP Access

Rainbow Islands Genesis performs **no VDP writes outside VBlank** during gameplay. All VDP access from the main loop is mediated through WRAM staging:

| Operation | Main Loop Action | VDP Touch? |
|-----------|-----------------|------------|
| Sprite positioning | Write to WRAM SAT at 0xFFFFF800 | No |
| Tilemap updates | Write to WRAM staging at 0xFFFFF644 ptr | No |
| Palette changes | Set flag at 0xFFFFF680 | No |
| Scroll changes | Write to WRAM 0xFFFFF630/0xFFFFF634 | No |
| Tile DMA requests | Set flag at 0xFFFFF690 | No |
| Display enable/disable | Write shadow reg at 0xFFFFF624 | No |

The main loop (0x11D2) frame-syncs by polling the frame counter at 0xFFFFF620, then dispatches game mode handlers. All VDP writes are deferred to the next VBlank.

**Exception**: Initial setup at game boot performs direct VDP register writes and DMA for loading the initial tileset, palette, and screen layout. This happens with display disabled and interrupts masked.

### 3.2 Rastan Build 316 Non-Interrupt VDP Access

Build 316 has a significant non-interrupt VDP access path in `request_start_rastan()` (main.c:2026–2064):

```
request_start_rastan() — called from launcher main loop (non-interrupt context):
  1. scrub_launcher_runtime_buffers()         No VDP
  2. genesistan_reclaim_launcher_wram()        No VDP
  3. genesistan_init_workram_direct()           No VDP
  4. restore_launcher_vdp_state()              VDP: calls VDP_init() → VDP_resetScreen()
                                                    → DMA_doVRamFill(0, 0, 0, 1) [full VRAM clear]
                                                    Reloads font tiles, DIP tiles, palettes
  5. VDP_setHInterrupt(0)                      VDP: register 0 write
  6. VDP_setHIntCounter(0xFF)                  VDP: register 10 write
  7. VDP_clearPlane(BG_A, TRUE)                VDP: DMA fill plane A
  8. VDP_clearPlane(BG_B, TRUE)                VDP: DMA fill plane B
  9. genesistan_sync_title_vdp_layout()        VDP: register writes (plane addresses, SAT)
  10. force_clean_vram_init()                   VDP: COMPREHENSIVE RESET
      ├─ Display OFF (reg 1 = 0x8134)
      ├─ Auto-increment = 2 (reg 15 = 0x8F02)
      ├─ VRAM clear: 32768 words via CPU fill at 0x0000
      ├─ CRAM clear: 64 words via CPU fill at 0x0000
      ├─ VSRAM clear: 40 words via CPU fill at 0x0000
      └─ All 19 VDP registers set to baseline values
  11. genesistan_preload_scene_tiles(TITLE)     VDP: DMA per tile from ROM → VRAM
  12. clear_frontend_sprite_layer()             VDP: SAT clear
  13. VDP_waitDMACompletion()                   VDP: poll DMA status
  14. genesistan_run_title_init_sequence()       Runs arcade init code (may trigger hooks)
  15. arcade_vblank_active = 1                  Switches VBlank to arcade mode
  16. andi.w #0xF8FF, %sr                       Unmask interrupts
```

**Critical observation**: Steps 4–13 perform extensive VDP access in non-interrupt context with the SGDK VBlank handler still active. The display state during this sequence:
- Steps 4–9: Display state depends on SGDK's VDP_init/VDP_resetScreen behavior
- Step 10: Explicitly disables display, performs full clear, leaves display off
- Steps 11–13: VDP DMA with display off (safe)
- Step 14: Runs arcade code — any VDP hooks fire with display off
- Step 15–16: Enables arcade VBlank, unmasks interrupts → display on at next VBlank

### 3.3 Non-Interrupt VDP Access Summary

| Category | Rainbow Islands Genesis | Rastan Build 316 |
|----------|------------------------|-------------------|
| Gameplay VDP writes from main loop | None (all staged in WRAM) | N/A (no main loop in arcade mode) |
| Boot/init VDP writes | Yes (display off, interrupts masked) | Yes (extensive, 16-step sequence) |
| VRAM clear at mode transition | Not applicable (single-mode game) | Yes (force_clean_vram_init at handoff) |
| Display state during init | Off (masked) | Off (explicit reg write in step 10) |
| DMA during init | Yes (tile loads) | Yes (scene preload, plane clears) |
| Interrupt safety during init | Interrupts masked | SGDK VBlank still active until step 15 |

---

## 4. VDP Write Subsystem Comparison (Build 316 vs Rainbow Islands)

### 4.1 Tilemap / Background Planes

| Aspect | Rainbow Islands Genesis | Build 316 |
|--------|------------------------|-----------|
| Staging | WRAM buffer at pointer 0xFFFFF644 | WRAM buffers: pc080sn_bg_buffer (4096B), pc080sn_fg_buffer (4096B) |
| Commit timing | VBlank, flag-triggered | VBlank, unconditional every frame |
| Commit method | Row copy in tight dbf loop | Full-plane streaming: 2×2048 words via dbf loop |
| Granularity | Partial rows (only dirty rows) | Full plane (all 2048 words regardless of changes) |
| Display state | Display OFF | Display OFF |
| Cycle cost per frame | Variable (0 if no dirty rows) | Fixed: ~2×(2048×12) ≈ 49,152 cycles (~6.9ms at 7.67MHz) |

**Delta**: Build 316 streams both full planes unconditionally. Rainbow Islands only commits dirty rows. The full-plane approach is simpler but wastes cycles when few cells changed. At ~6.9ms for both planes, this consumes ~41% of the 16.7ms frame budget.

### 4.2 Sprites (SAT)

| Aspect | Rainbow Islands Genesis | Build 316 |
|--------|------------------------|-----------|
| Staging | Full SAT in WRAM at 0xFFFFF800 (640 bytes) | No WRAM staging |
| Commit method | Single DMA from WRAM → VDP SAT | Direct per-entry writes during arcade tick |
| When | VBlank, every frame | During arcade tick (inside VBlank, display off) |
| Atomicity | Atomic (DMA) | Non-atomic (per-entry, interleaved with game logic) |
| Tile upload | DMA from WRAM staging, display off | DMA from ROM, display off |

**Delta**: Build 316 still writes SAT entries directly to VDP during the arcade tick. The display-disable bracket (Build 312+) prevents visible tearing, but the VDP may read a partially-updated SAT between the last sprite hook and the next scanline after display re-enable. Rainbow Islands' atomic DMA approach is strictly safer.

### 4.3 Palette

| Aspect | Rainbow Islands Genesis | Build 316 |
|--------|------------------------|-----------|
| Staging | ROM→WRAM 0xFF0000, then VDP | CLCS buffer→convert→CRAM |
| Commit method | Word stream from staging | xRGB-444 conversion + word stream |
| Flag-triggered? | Yes (0xFFFFF680) | No (committed every frame) |
| Display state | Display OFF | Display OFF |

**Delta**: Both approaches are structurally similar — WRAM intermediary, VDP word stream during display-off. Build 316's per-frame conversion of 64 colors adds ~1,500 cycles. Rainbow Islands only commits when flagged.

### 4.4 Scroll

| Aspect | Rainbow Islands Genesis | Build 316 |
|--------|------------------------|-----------|
| Staging | WRAM at 0xFFFFF630/0xFFFFF634 | None — direct VDP writes via SGDK wrappers |
| Commit method | Single long write to VSRAM after display re-enable | Multiple VDP writes during arcade tick |
| When | VBlank, after display ON | During arcade tick (inside VBlank, display off) |
| Frequency | Once per frame | Multiple times per frame (each scroll hook hit) |

**Delta**: Build 316 writes scroll registers via SGDK wrappers during the arcade tick. Since display is off, the writes themselves are safe, but the redundant writes waste cycles. Rainbow Islands writes once, after all commits.

---

## 5. Architectural Divergences

### 5.1 Game Logic Placement

| | Rainbow Islands Genesis | Build 316 |
|---|---|---|
| Game logic runs in | Main loop (non-interrupt) | VBlank interrupt handler |
| VBlank contains | Commits only (~3-5ms) | Game logic + commits (unknown total) |
| Frame sync | Poll frame counter 0xFFFFF620 | Implicit (arcade tick fires from VBlank) |

This is the most fundamental structural difference. Rainbow Islands separates game logic from VDP commits. Build 316 runs everything in VBlank, relying on display-disable to extend the safe write window to the full frame time (~16.7ms).

**Why this persists**: The original Rastan arcade also runs its entire game tick inside the VBlank interrupt (0x3A008). Build 316 preserves the arcade's execution model. Refactoring to main-loop game logic would require extracting the arcade tick from the interrupt context — a significant architectural change.

### 5.2 Flag-Triggered vs Unconditional Commits

Rainbow Islands uses request flags for conditional commits:
- Palette: only commit if 0xFFFFF680 ≠ 0
- Tilemap: only commit if 0xFFFFF63C ≠ 0
- Tile DMA: only commit if 0xFFFFF690 ≠ 0
- SAT DMA: unconditional (every frame)
- Scroll: unconditional (every frame)

Build 316 commits unconditionally:
- Tilemap buffers: always stream both full planes (4096 words)
- Palette: always convert and stream 64 colors
- Scroll: always write (multiple times during tick)
- SAT: always write (during tick, per-entry)

The unconditional approach simplifies the code but wastes VBlank time on frames where nothing changed.

### 5.3 Z80 Bus Coordination

Rainbow Islands requests the Z80 bus at VBlank entry and holds it through all VDP commits. Build 316 does not coordinate with the Z80 at all. If the Z80 (sound driver) is performing bus-request operations during VRAM DMA, this could cause bus contention.

### 5.4 VBlank Acknowledgement

Rainbow Islands reads VDP status (0xC00004) at VBlank entry to acknowledge the interrupt and clear the pending flag. Build 316 does not read VDP status. This may cause issues with VDP status register state if any code later checks the VBlank flag.

---

## 6. Cycle Budget Analysis

### NTSC frame timing:
- Total frame: 16.72ms (262 scanlines × 63.9µs)
- VBlank window: ~4.47ms (38 scanlines × 63.9µs × 1.84)
- CPU cycles per frame: ~128,000 at 7.67MHz
- CPU cycles in VBlank: ~34,300

### Build 316 estimated VBlank costs:

| Phase | Operation | Est. Cycles | Est. Time |
|-------|-----------|-------------|-----------|
| Input | refresh_arcade_inputs | ~500 | ~65µs |
| Display off | Register write | ~20 | ~3µs |
| Arcade tick | Full game state machine | ~40,000–80,000 | ~5.2–10.4ms |
| Sanitize | Zero C-window pointers | ~200 | ~26µs |
| BG commit | 2048 words via dbf | ~24,576 | ~3.2ms |
| FG commit | 2048 words via dbf | ~24,576 | ~3.2ms |
| Palette | 64 colors convert+write | ~1,500 | ~195µs |
| Display on | Register write | ~20 | ~3µs |
| **TOTAL** | | **~91,400–131,400** | **~11.9–17.1ms** |

### Rainbow Islands Genesis estimated VBlank costs:

| Phase | Operation | Est. Cycles | Est. Time |
|-------|-----------|-------------|-----------|
| VBlank ack | Read status | ~16 | ~2µs |
| Z80 bus | Request + wait | ~200 | ~26µs |
| Display off | Shadow reg write | ~24 | ~3µs |
| Tile DMA | Conditional, via DMA | ~500–2,000 | ~65–260µs |
| SAT DMA | 640 bytes via DMA | ~500 | ~65µs |
| Tilemap rows | Conditional, dirty rows only | 0–4,000 | 0–520µs |
| Palette | Conditional, word stream | 0–800 | 0–104µs |
| Display on | Shadow reg write | ~24 | ~3µs |
| Scroll | VSRAM write (1 long) | ~24 | ~3µs |
| Input | Joypad read | ~200 | ~26µs |
| RNG/timer | Update | ~100 | ~13µs |
| Z80 sound | Communication | ~500 | ~65µs |
| Z80 bus release | Release | ~16 | ~2µs |
| **TOTAL** | | **~2,100–8,400** | **~0.3–1.1ms** |

### Budget comparison:

| Metric | Rainbow Islands | Build 316 |
|--------|----------------|-----------|
| VBlank time used | 0.3–1.1ms | 11.9–17.1ms |
| Active display time available for game logic | ~15.6ms | 0ms |
| Display-disabled extended window needed | No | Yes (critical) |
| Frame overrun risk | None | Moderate (if tick exceeds ~10ms) |

---

## 7. What Build 316 Has Adopted from Rainbow Islands

| Pattern | Status | Build Introduced |
|---------|--------|------------------|
| Display-disable bracketing | Implemented | Build 312 |
| WRAM tilemap staging (BG/FG) | Implemented | Build 313 |
| WRAM text writer staging | Implemented | Build 315 |
| Palette WRAM intermediary | Implemented | Build 311 (original) |
| Forced clean VRAM at handoff | Implemented | Build 316 |

## 8. What Build 316 Has NOT Adopted

| Pattern | Status | Impact |
|---------|--------|--------|
| Game logic outside VBlank | Not implemented | Entire tick in VBlank; cycle budget tight |
| WRAM SAT staging + DMA | Not implemented | SAT written per-entry during tick |
| Flag-triggered conditional commits | Not implemented | Full planes streamed every frame |
| Dirty-row tilemap commit | Not implemented | 4096 words/frame regardless of changes |
| Shadow register for display enable | Not implemented | Hardcoded 0x8134/0x8174 |
| Z80 bus coordination | Not implemented | Potential bus contention |
| VBlank acknowledgement | Not implemented | VDP status not cleared |
| Scroll WRAM staging | Not implemented | Direct VDP writes during tick |

---

## 9. Risk Assessment

### Low Risk (display-disable covers it):
- **Scroll writes during tick**: Display is off, VSRAM writes are safe
- **Palette committed every frame**: Wastes ~200µs but no correctness issue
- **No VBlank acknowledgement**: Unlikely to cause issues unless code checks status

### Medium Risk:
- **Non-atomic SAT**: Sprite entries written during tick interleaved with game logic. Display-disable prevents tearing during commit, but if the sprite renderer is re-entered or partially complete when VBlank ends (frame overrun), the SAT state is undefined
- **Frame overrun**: If arcade tick + commits exceed ~16.7ms, the next VBlank fires before the current one completes. The 68000 does not re-enter the same interrupt, but the frame is lost — display will show the previous frame's state plus any partial updates
- **No Z80 coordination**: If the Z80 sound driver holds the bus during DMA, the DMA completes slower. Not a correctness issue but increases commit time

### High Risk:
- **Full-plane streaming cost**: ~6.4ms for both planes is a significant fraction of the frame budget. Combined with an arcade tick that may exceed 5ms, this leaves very little margin before frame overrun

---

## 10. Conclusion

Build 316 has closed the most critical gap from Build 311 — **display-disable bracketing** — and added **WRAM tilemap staging** that matches the Rainbow Islands model in concept. The remaining divergences (game logic in VBlank, non-atomic SAT, unconditional full-plane streaming) are structural choices driven by the Rastan arcade's monolithic VBlank execution model.

The most impactful remaining optimization would be **dirty-row tracking** for tilemap commits, reducing the ~6.4ms full-plane streaming cost to a variable cost proportional to actual changes. This would directly increase the cycle budget available for the arcade tick and reduce frame overrun risk.
