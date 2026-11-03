# Build 310 — VDP + Input Timing Audit

## 1. Executive Summary

The arcade-mode VBlank path (`_VINT_arcade_mode`) runs the complete arcade tick synchronously inside the VBlank interrupt. All per-frame VDP writes occur inside this interrupt handler, meaning they execute during VBlank — not during active display. Genesis button A correctly maps to arcade coin input (bit 0 of shadow register 0x390007). Input is sampled and written during VBlank before the arcade tick consumes it.

The single primary finding is: **three C opcode-hook functions called from within the VBlank interrupt handler use `SYS_disableInts()` / `SYS_enableInts()`, which can re-enable interrupts while still inside the interrupt handler, risking re-entrant VBlank and corrupted frame state.** These are `genesistan_hook_text_writer_3bb48_impl`, `genesistan_hook_text_writer_3c3fe`, and `genesistan_preload_scene_tiles` (via `genesistan_bulk_preload_check`).

## 2. Launcher VBlank Behavior vs Arcade VBlank Behavior

### Launcher Mode (`arcade_vblank_active == 0`)

| Aspect | Launcher |
|--------|----------|
| Interrupt owner | SGDK `_VINT` full dispatch |
| Task scheduler | Active (task_lock/unlock) |
| vtimer/intTrace | Updated every frame |
| XGM check | Runs (even if unused) |
| VDP writes in VBlank | Only via `vintCB` (currently NULL after reset) |
| Frame progression | Main loop: `SYS_doVBlankProcess()` |
| Input sampling | `JOY_readJoypad()` in main loop (outside VBlank) |
| VDP writes outside VBlank | SGDK wrapper calls in main loop (text, planes, tiles, sprites) |
| Game logic advanced in VBlank | No |

### Arcade Mode (`arcade_vblank_active == 1`)

| Aspect | Arcade |
|--------|--------|
| Interrupt owner | `_VINT_arcade_mode` fast path |
| Task scheduler | Bypassed |
| vtimer/intTrace | Bypassed |
| XGM check | Bypassed |
| VDP writes in VBlank | ALL per-frame writes: palette, sprites, tilemaps, scroll, text |
| Frame progression | `_VINT_arcade_mode` runs full arcade tick |
| Input sampling | `genesistan_refresh_arcade_inputs()` at start of VBlank handler |
| VDP writes outside VBlank | None (CPU STOPped between frames) |
| Game logic advanced in VBlank | YES — full arcade state machine runs inside VBlank |

### Key Difference

In launcher mode, VDP writes happen in the main loop (active display period) and the VBlank interrupt does minimal work. In arcade mode, the VBlank interrupt does ALL work — game logic, VDP writes, input — and the CPU halts between frames.

## 3. Current Active VDP Write Sites

### Per-Frame Arcade VDP Write Sites (During VBlank)

| # | Function | File | VDP Resource | Called By |
|---|----------|------|-------------|-----------|
| 1 | `genesistan_palette_commit_asm` | startup_trampoline.s:84-133 | CRAM (64 colors) | `_VINT_arcade_mode` directly |
| 2 | `genesistan_render_sprites_vdp_asm` | startup_trampoline.s:146-197 | VRAM sprite tiles (DMA) + SAT at 0xF800 | Opcode hook 0x03A8E4 → bridge |
| 3 | `genesistan_asm_tilemap_commit_bg` | startup_trampoline.s:458-576 | VRAM nametable plane A (0xC000) | C hook `genesistan_hook_tilemap_plane_a` |
| 4 | `genesistan_asm_tilemap_commit_fg` | startup_trampoline.s:582-712 | VRAM nametable plane B (0xE000) | C hook `genesistan_hook_tilemap_plane_b` |
| 5 | `genesistan_bulk_tilemap_commit` | startup_trampoline.s:729-870 | VRAM nametables (bulk, either plane) | Opcode hook 0x05A4DE |
| 6 | `genesistan_scroll_from_workram_vdp` | main.c:1702-1718 | VSRAM (H/V scroll, both planes) | 10 opcode hooks in startup_common/frontend_core |
| 7 | `genesistan_hook_text_writer_3bb48_impl` | main.c:1643-1696 | VRAM nametable plane A (via VDP_setTileMapXY) | Opcode hook 0x03BB48 |
| 8 | `genesistan_hook_text_writer_3c3fe` | main.c:1721-1765 | VRAM nametable plane A (via VDP_setTileMapXY) | Opcode hook 0x03C3FE |

### Conditional Per-Frame Arcade VDP Write Sites (During VBlank)

| # | Function | File | VDP Resource | Trigger |
|---|----------|------|-------------|---------|
| 9 | `genesistan_preload_scene_tiles` | main.c:1579-1620 | VRAM tile data (DMA bulk load) | Called from `genesistan_bulk_preload_check` when scene changes |

### One-Shot Init Arcade VDP Write Sites (During `request_start_rastan`, before interrupt handoff)

| # | Function | File | VDP Resource |
|---|----------|------|-------------|
| 10 | `restore_launcher_vdp_state` | main.c:609-625 | Full VDP reset, palette, font tiles, DIP tiles |
| 11 | `genesistan_sync_title_vdp_layout` | main.c:1428-1437 | Plane addresses (0xC000/0xE000), SAT address (0xF800) |
| 12 | `genesistan_preload_scene_tiles(TITLE)` | main.c:1579-1620 | VRAM tile data (DMA) for title scene |
| 13 | `VDP_clearPlane(BG_A/BG_B)` | main.c:1987-1988 | VRAM nametable clear |
| 14 | `clear_frontend_sprite_layer` | main.c:1192-1194 | SAT clear |
| 15 | `VDP_setHInterrupt(0)` + `VDP_setHIntCounter(0xFF)` | main.c:1985-1986 | VDP register 0/10 |

### Launcher-Only VDP Write Sites

| # | Category | File | VDP Resource |
|---|----------|------|-------------|
| 16 | SGDK text/tile/plane/sprite wrappers | main.c (various) | VRAM text, planes, tiles, sprites |

## 4. One-Shot Init Writes vs Per-Frame Writes

### One-Shot Init (runs once at launch, before `arcade_vblank_active = 1`)

Sites 10-15 above. These run in `request_start_rastan()` while interrupts are still under SGDK control. They complete before the handoff. No timing concern — they run with full VDP access.

### Per-Frame Arcade (runs every VBlank after handoff)

Sites 1-8 above, plus site 9 conditionally. ALL execute inside `_VINT_arcade_mode`, during VBlank.

### Launcher Per-Frame (runs in main loop, active display)

Site 16. These are SGDK wrapper calls in the main loop. They execute during active display but only in launcher mode.

## 5. VBlank vs Active-Display Classification

| Site | Timing Window | Justification |
|------|-------------|---------------|
| `genesistan_palette_commit_asm` | VBlank only | Called directly from `_VINT_arcade_mode` |
| `genesistan_render_sprites_vdp_asm` | VBlank only | Called from opcode hook during `genesistan_run_arcade_tick_lean` inside `_VINT_arcade_mode` |
| `genesistan_asm_tilemap_commit_bg` | VBlank only | Called from opcode hook during arcade tick inside VBlank |
| `genesistan_asm_tilemap_commit_fg` | VBlank only | Called from opcode hook during arcade tick inside VBlank |
| `genesistan_bulk_tilemap_commit` | VBlank only | Called from opcode hook during arcade tick inside VBlank |
| `genesistan_scroll_from_workram_vdp` | VBlank only | Called from 10 opcode hooks during arcade tick inside VBlank |
| `genesistan_hook_text_writer_3bb48_impl` | VBlank only | Called from opcode hook during arcade tick inside VBlank |
| `genesistan_hook_text_writer_3c3fe` | VBlank only | Called from opcode hook during arcade tick inside VBlank |
| `genesistan_preload_scene_tiles` (runtime) | VBlank only | Called from `genesistan_bulk_preload_check` during arcade tick |
| Launcher SGDK wrappers | Active display | Called from main loop (launcher mode only) |

**Conclusion: In arcade mode, all per-frame VDP writes occur during VBlank. No VDP writes occur during active display in arcade mode.**

## 6. Text Path vs PC080SN Path Timing Comparison

### Text Path (relatively stable in earlier builds)

- **Functions**: `genesistan_hook_text_writer_3bb48_impl`, `genesistan_hook_text_writer_3c3fe`
- **VDP write method**: `VDP_setTileMapXY(BG_A, ...)` — SGDK wrapper, individual tile-at-a-time
- **Execution context**: Opcode hooks during arcade tick, inside VBlank
- **Writes to**: VRAM nametable plane A at calculated (x,y) positions
- **Volume**: Typically small — a few dozen tiles per text update
- **Hazard**: Calls `SYS_disableInts()` / `SYS_enableInts()` inside VBlank handler

### PC080SN/Background Path (unstable/flickering)

- **Functions**: `genesistan_hook_tilemap_plane_a`, `genesistan_hook_tilemap_plane_b`, `genesistan_asm_tilemap_commit_bg`, `genesistan_asm_tilemap_commit_fg`, `genesistan_bulk_tilemap_commit`
- **VDP write method**: Direct VDP control/data port writes in assembly (0xC00004, 0xC00000)
- **Execution context**: Same — opcode hooks during arcade tick, inside VBlank
- **Writes to**: VRAM nametables plane A (0xC000) and plane B (0xE000)
- **Volume**: Potentially large — full tilemap strips per frame
- **Hazard**: `genesistan_bulk_tilemap_commit` can trigger `genesistan_bulk_preload_check` → `genesistan_preload_scene_tiles` which calls `SYS_disableInts()` / `SYS_enableInts()` and does DMA with `VDP_waitDMACompletion()` inside VBlank

### Do they write in different timing windows?

**NO.** Both text and PC080SN paths execute in the same VBlank context, during the arcade tick. They are called from different opcode hooks but within the same interrupt handler execution.

### Do they run from different frame contexts?

**NO.** Both are called from opcode hooks that fire during `genesistan_run_arcade_tick_lean`, which runs inside `_VINT_arcade_mode`.

### Why might PC080SN appear less stable than text?

1. **Volume**: PC080SN writes more data per frame (full tilemap strips vs individual text tiles)
2. **DMA**: PC080SN scene preload does DMA inside VBlank; text does not
3. **SYS_enableInts hazard**: Both have the `SYS_enableInts()` re-entrancy risk, but the bulk tilemap path triggers DMA-heavy scene preloads that are more likely to overrun VBlank if re-entrancy occurs
4. **Scroll writes**: PC080SN layer scroll is written 10 times per frame via opcode hooks; text has no scroll component

## 7. Launcher Input Path vs Arcade Input Path

### Launcher Mode

```
Genesis controller hardware
  → JOY_readJoypad(JOY_1) in main() while loop (main.c:2133)
    → Returns u16 button state (SGDK format)
  → pressed = state & ~previous_state (main.c:2134)
    → Used for menu navigation, screen transitions
  → Timing: Between VBlanks, in main loop (active display period)
```

### Arcade Mode

```
Genesis controller hardware
  → JOY_readJoypad(JOY_1) + JOY_readJoypad(JOY_2)
    Called inside genesistan_refresh_arcade_inputs() (startup_bridge.c:192-193)
    Called from _VINT_arcade_mode (sega.s:204) — first call in VBlank handler
  → build_player_input_byte(p1_state) → genesistan_shadow_input_390001 (P1 directions+attack)
  → build_player_input_byte(p2_state) → genesistan_shadow_input_390003 (P2 directions+attack)
  → build_aux_input_byte(p1_state) → genesistan_shadow_input_390005 (auxiliary buttons)
  → build_system_input_byte(p1_state, p2_state) → genesistan_shadow_input_390007 (coin/start/service)
  → Shadow registers read by arcade code during same VBlank tick
    (memory-mapped via opcode replacements: arcade reads 0x390001-0x390007 → remapped to shadow vars)
  → Timing: During VBlank, before arcade tick executes
```

### Shadow Register Addresses

| Shadow Variable | Arcade Address | Content | Section |
|----------------|---------------|---------|---------|
| `genesistan_shadow_input_390001` | 0x390001 | P1: UP/DOWN/LEFT/RIGHT/B/C | `.bss.patcher` |
| `genesistan_shadow_input_390003` | 0x390003 | P2: UP/DOWN/LEFT/RIGHT/B/C | `.bss.patcher` |
| `genesistan_shadow_input_390005` | 0x390005 | Aux: B/C/A on bits 4/5/6 | `.bss.patcher` |
| `genesistan_shadow_input_390007` | 0x390007 | System: COIN1(b0)/SERVICE(b2)/START1(b3)/START2(b4) | `.bss.patcher` |

All values are **active-low** (0xFF = no buttons pressed, bit cleared = pressed).

## 8. Genesis Button → Arcade Input Mapping Verification

### Full Mapping Table

| Genesis Button | Arcade Function | Shadow Register | Bit | Polarity |
|---------------|----------------|----------------|-----|----------|
| D-pad UP | P1 Up | 0x390001 | 0 (0x01) | Active-low |
| D-pad DOWN | P1 Down | 0x390001 | 1 (0x02) | Active-low |
| D-pad LEFT | P1 Left | 0x390001 | 2 (0x04) | Active-low |
| D-pad RIGHT | P1 Right | 0x390001 | 3 (0x08) | Active-low |
| Button B | P1 Attack 1 (punch/sword) | 0x390001 | 4 (0x10) | Active-low |
| Button C | P1 Attack 2 (jump) | 0x390001 | 5 (0x20) | Active-low |
| **Button A** | **COIN1** | **0x390007** | **0 (0x01)** | **Active-low** |
| Button START | START1 | 0x390007 | 3 (0x08) | Active-low |
| A+B+C combo | SERVICE | 0x390007 | 2 (0x04) | Active-low |

### Does Genesis A map to arcade coin input?

**YES.** `build_system_input_byte()` at startup_bridge.c:177: `if ((p1_state & BUTTON_A) != 0) value &= (uint8_t)~0x01;`

This writes to `genesistan_shadow_input_390007`, bit 0 = COIN1.

### Does the arcade game read that exact address/bit?

**YES.** The arcade code reads 0x390007 which is remapped to `genesistan_shadow_input_390007` via memory window mapping in `startup_title_remap.json`. The arcade's coin processing reads bit 0 of this address.

### Is that read happening in the right frame phase?

**YES.** The shadow register is written BEFORE the arcade tick (`genesistan_refresh_arcade_inputs` is the first call in `_VINT_arcade_mode`). The arcade tick then reads the shadow register in the same VBlank.

## 9. Whether Coin-Up Is Sampled/Written/Consumed During Arcade VBlank

| Step | Happens During VBlank? | Details |
|------|----------------------|---------|
| Genesis A button sampled | YES | `JOY_readJoypad(JOY_1)` in `genesistan_refresh_arcade_inputs` |
| Coin-up state written to shadow | YES | `genesistan_shadow_input_390007` bit 0 cleared |
| Game code reads/consumes coin state | YES | Arcade tick reads 0x390007 during same VBlank |

**The coin-up chain is complete and correct.** Button A → shadow 0x390007 bit 0 → arcade reads during same frame tick → coin registered.

## 10. Whether Active-Display Writes Are a Real Current Problem

**NO.** In arcade mode, no VDP writes occur during active display.

All per-frame VDP writes execute inside `_VINT_arcade_mode`, which runs during the VBlank period. Between frames, the CPU executes `STOP #0x2000` and does nothing until the next VBlank.

The potential problem is not active-display writes, but:

1. **VBlank overrun**: The entire arcade tick (game logic + all VDP writes + DMA) must complete within one VBlank period (~4500 68000 cycles on NTSC). If it overruns, VDP writes spill into active display.

2. **Re-entrant VBlank via SYS_enableInts**: Three C functions called from within the VBlank handler call `SYS_enableInts()`, which unmasks interrupts. If the next VBlank fires before the current one completes, the handler re-enters, causing double writes and state corruption.

## 11. Single Primary Timing/Input-Related Finding

**Three C opcode-hook functions called from inside the VBlank interrupt handler use `SYS_disableInts()` / `SYS_enableInts()`, which re-enables interrupts while still inside `_VINT_arcade_mode`. This creates a re-entrant VBlank hazard that can corrupt frame state.**

The affected functions:

1. `genesistan_hook_text_writer_3bb48_impl` (main.c:1664/1695)
2. `genesistan_hook_text_writer_3c3fe` (main.c:1734/1764)
3. `genesistan_preload_scene_tiles` (main.c:1595/1615) — called from `genesistan_bulk_preload_check` during arcade tick

In the old SGDK-mediated model, these functions ran from a VBlank callback where `SYS_disableInts/enableInts` toggled the interrupt mask safely (the callback was at a lower priority). In the new model, these run directly inside the level-6 VBlank interrupt handler. `SYS_enableInts()` at the end of each function unmasks interrupts, allowing a new VBlank to fire before `_VINT_arcade_mode` completes its `movem.l restore + rte` sequence.

This is the most likely cause of visual instability: if the frame overruns even slightly, `SYS_enableInts` allows re-entry, causing partial double-writes to VDP state.

## 12. Exact Next Target

**Remove `SYS_disableInts()` / `SYS_enableInts()` from the three C functions that are called inside the VBlank interrupt handler.**

Specifically:

1. `genesistan_hook_text_writer_3bb48_impl` (main.c:1664 and 1695) — remove both calls
2. `genesistan_hook_text_writer_3c3fe` (main.c:1734 and 1764) — remove both calls
3. `genesistan_preload_scene_tiles` (main.c:1595 and 1615) — remove both calls

These `SYS_disableInts/enableInts` pairs were safety wrappers for when these functions ran outside VBlank (in the old SGDK callback model). Now that they run inside the VBlank handler, interrupts are already disabled by the 68000's interrupt priority mechanism. The disable/enable calls are not only unnecessary but actively harmful — the `enableInts` call re-enables interrupts inside the handler, creating the re-entrancy hazard.

## 13. Final Verdict

The VDP write timing is structurally correct — all arcade-mode writes occur during VBlank. Input mapping is correct — Genesis A is coin, directions and buttons map correctly, timing is correct (sampled before tick, consumed during tick).

The real hazard is `SYS_enableInts()` re-enabling interrupts inside the VBlank handler. This was harmless in the old model where these C hooks ran from a software callback, but in the new direct-interrupt model it creates a re-entrant VBlank risk. Removing these calls is the next required fix.
