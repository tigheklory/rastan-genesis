# Build 312 — Display-Disable Bracketing Experiment

## 1. Executive Summary

Build 312 adds Rainbow Islands-style display-disable bracketing around the arcade VDP commit window in `_VINT_arcade_mode`. Before the arcade tick and all VDP writes, VDP register 1 bit 6 is cleared (display off). After all VDP writes complete (palette commit is last), register 1 bit 6 is restored (display on). This prevents VDP writes from corrupting active display output if the arcade tick overruns the VBlank window.

## 2. Exact Display-Disable / Re-Enable Change

### Before (Build 311)

```asm
_VINT_arcade_mode:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    jsr     genesistan_refresh_arcade_inputs
    jsr     genesistan_run_arcade_tick_lean
    jsr     sanitize_arcade_workram
    jsr     genesistan_palette_commit_asm
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rte
```

### After (Build 312)

```asm
_VINT_arcade_mode:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    jsr     genesistan_refresh_arcade_inputs
    /* --- display-disable bracket: turn off display before VDP writes --- */
    move.w  #0x8134, 0x00C00004     /* VDP reg 1 = 0x34: display OFF, VInt ON, DMA ON, V28 */
    jsr     genesistan_run_arcade_tick_lean
    jsr     sanitize_arcade_workram
    jsr     genesistan_palette_commit_asm
    /* --- display-disable bracket: restore display after VDP writes --- */
    move.w  #0x8174, 0x00C00004     /* VDP reg 1 = 0x74: display ON, VInt ON, DMA ON, V28 */
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rte
```

### Instruction Details

- **Display disable**: `move.w #0x8134, 0x00C00004`
  - VDP register command: `0x81` = register 1
  - Value: `0x34` = bits: 0 0 1 1 0 1 0 0
    - Bit 6 = 0: display OUTPUT disabled
    - Bit 5 = 1: VBlank interrupt enabled
    - Bit 4 = 1: DMA enabled
    - Bit 2 = 1: V28 cell mode (224 lines)

- **Display re-enable**: `move.w #0x8174, 0x00C00004`
  - Value: `0x74` = bits: 0 1 1 1 0 1 0 0
    - Bit 6 = 1: display OUTPUT enabled
    - All other bits unchanged

## 3. Where the Register 1 Value Came From

SGDK initializes VDP register 1 to `0x74` in `tools/sgdk/src/vdp.c:92`:
```c
regValues[0x01] = 0x74;  /* reg. 1 - Enable display, V-Int, DMA + VCell size */
```

No code in the Rastan build modifies VDP register 1 after SGDK init. The value `0x74` is the steady-state register 1 value throughout arcade mode.

The display-disable value `0x34` is derived by clearing bit 6 (0x40) from `0x74`: `0x74 & ~0x40 = 0x34`.

Rainbow Islands Genesis uses the same technique at addresses 0x03A4–0x03AC (disable) and 0x03CA–0x03D2 (re-enable), reading from a WRAM shadow at 0xFFFFF624. Since our register 1 value is constant, a hardcoded constant is safe and avoids the need for a shadow variable.

## 4. Why the Bracket Was Placed Where It Was

### Display-disable placement: After input refresh, before arcade tick

Input sampling (`genesistan_refresh_arcade_inputs`) does NOT write to VDP — it reads joypad ports and writes to WRAM shadow registers. Therefore it runs with display still on, preserving the maximum visible display time from the previous frame.

The display-disable is placed immediately before `genesistan_run_arcade_tick_lean`, which is the first function that triggers VDP writes (via opcode hooks for scroll, tilemap, sprites, text).

### Display-re-enable placement: After palette commit, before register restore

`genesistan_palette_commit_asm` is the last VDP-writing function in the sequence. After it completes, all VDP writes for the frame are done. Display is re-enabled immediately after, before register restore and RTE.

### Launcher mode is unaffected

The `tst.w arcade_vblank_active / bne _VINT_arcade_mode` check at the top of `_VINT` ensures this code path is only reached in arcade mode. Launcher mode follows the SGDK dispatch path, which has its own display management.

## 5. Build 312 Verification

| Check | Result |
|-------|--------|
| Build succeeded | YES |
| ROM produced | `dist/Rastan_312.bin` (3,932,160 bytes) |
| Postpatch warnings | 28 (pre-existing, applied anyway) |
| Compiler warnings | 5 unused-function (pre-existing) |

## 6. Runtime Verification (MAME Trace, 1027 frames)

| Metric | Result |
|--------|--------|
| `startup_result_code` 0→1 | Frame 504 |
| VDP writes begin | Frame 150 (pre-launch init) |
| VDP write frequency | Every frame (sampled every 30 frames) |
| `arcade_mode4` reaches 2 | Frame 890 |
| `arcade_page2` set | Frame 888 |
| Hang detected | NO |
| Total frames | 1027 |
| Total VDP port writes | 28,411 |
| Display-disable write confirmed | YES (`last_data=8134` in vdp_ports_live) |

### Comparison with Build 311

| Metric | Build 311 | Build 312 |
|--------|-----------|-----------|
| Total frames | 622 | 1027 |
| VDP port writes | 24,036 | 28,411 |
| arcade_mode4 reaches 2 | Frame 600 | Frame 890 |
| Hang | NO | NO |

Build 312 ran 65% more frames in the same trace window, suggesting the display-disable bracket allows the arcade tick to complete more reliably without timing conflicts.

### Visual Verification

| Check | Result |
|-------|--------|
| Display-disable bracketing added | YES |
| Build succeeded | YES |
| ROM produced | `dist/Rastan_312.bin` |
| Input responds after launch | CANNOT CONFIRM (headless trace) |
| Black screen remains | CANNOT CONFIRM (headless) |
| Vertical dots/noise remain | CANNOT CONFIRM (headless) |
| Title/runtime display improved | CANNOT CONFIRM (headless) |
| Visible corruption reduced | CANNOT CONFIRM (headless) |

Visual verification requires BlastEm or visual MAME run.

## 7. Remaining Issues

- Visual verification pending (requires emulator with display output)
- The display-disable constant `0x34` is hardcoded. If any future code changes VDP register 1 (e.g., to enable H-Int, change V-cell mode), the constant must be updated. A WRAM shadow (like Rainbow Islands uses) would be more robust but was out of scope for this experiment.
- SGDK's internal `regValues[1]` shadow is not updated by our direct VDP register writes, so `VDP_getReg(1)` in launcher mode will still return `0x74` (correct, since we only write the modified value in arcade mode and always restore it).
- This experiment addresses VBlank overrun protection only. The deeper architectural divergences (no WRAM staging, no SAT DMA, game logic in VBlank) identified in the comparative report remain.
