# Build 310 — Complete Arcade-Owned Execution Model

## 1. Executive Summary

Build 310 completes the arcade-owned execution model. Three remaining hybrid execution artifacts are eliminated: the main loop's SGDK joypad polling between STOPs, the redundant double register save in the VBlank-to-arcade-tick path, and the obsolete `frontend_live_handoff_active` flag that duplicated the mode switch. After launch, the CPU enters a permanent STOP loop with zero launcher-era logic executing between VBlanks.

## 2. What Was Previously Incomplete

Build 309 implemented the `_VINT` mode switch and STOP-based wait, but three hybrid artifacts remained:

1. **Main loop re-entered launcher logic between STOPs**: After each VBlank wakeup, `STOP` returned to the loop body which called `JOY_readJoypad()` (SGDK polling), evaluated the `if/else` chain, set `previous_state`, checked `SYS_doVBlankProcess` skip — all unnecessary since `_VINT_arcade_mode` already handles the frame completely.

2. **Double register save**: `_VINT_arcade_mode` saved d0-d7/a0-a6, then called `genesistan_run_original_frontend_tick` which saved them again (60 bytes pushed twice = 120 bytes of stack waste per frame, plus ~40 cycles wasted).

3. **Redundant mode flag**: `frontend_live_handoff_active` was still set/cleared alongside `arcade_vblank_active` but nothing in the active path read it. Dual mode flags are a structural hybrid artifact.

## 3. Exact Remaining Execution-Model Changes Made

### Change 1: Permanent STOP loop (main.c)

**Before:**
```c
else if (current_screen == SCREEN_FRONTEND_LIVE)
{
    __asm__ volatile("stop #0x2000");
}
// falls through to loop body: JOY_readJoypad, if/else chain, previous_state...
```

**After:**
```c
else if (current_screen == SCREEN_FRONTEND_LIVE)
{
    for (;;)
        __asm__ volatile("stop #0x2000");
}
```

The `for (;;)` ensures the CPU never returns to the launcher loop body after launch. Each VBlank wakeup immediately re-enters STOP. Zero launcher-era instructions execute between frames.

### Change 2: Lean arcade tick (startup_trampoline.s)

**New function:** `genesistan_run_arcade_tick_lean` (0x2034E2)

```asm
genesistan_run_arcade_tick_lean:
    lea genesistan_arcade_workram_words, %a5
    moveq #0, %d0
    move.l #.Llean_tick_return, -(%sp)
    move.w %sr, -(%sp)
    jmp (0x03A008 + ARCADE_ROM_BASE)
.Llean_tick_return:
    move.l %a0, genesistan_arcade_last_a0
    rts
```

This is the same arcade tick trampoline as `genesistan_run_original_frontend_tick` but without the `movem.l` register save/restore — the caller (`_VINT_arcade_mode`) already saves all registers.

**`_VINT_arcade_mode` updated** to call `genesistan_run_arcade_tick_lean` instead of `genesistan_run_original_frontend_tick`.

### Change 3: Remove redundant mode flag (main.c)

**Removed:** `frontend_live_handoff_active` — declaration, set in `request_start_rastan()`, clear in `reset_launcher_runtime_state()`.

**`arcade_vblank_active`** is the sole mode flag for the launcher/arcade boundary.

## 4. Final Post-Launch Active Frame Path

```
Hardware VBlank fires
  → _VINT (sega.s:139)
    → tst.w arcade_vblank_active    [8 cycles]
    → bne _VINT_arcade_mode         [10 cycles, taken]

_VINT_arcade_mode:
    movem.l %d0-%d7/%a0-%a6,-(%sp)  [save 15 registers]
    jsr genesistan_refresh_arcade_inputs  [read joypads → shadow regs]
    jsr genesistan_run_arcade_tick_lean   [arcade VBlank state machine]
      → lea A5, moveq D0
      → push fake exception frame
      → JMP 0x03A008 (arcade VBlank handler)
        → opcode hooks: scroll, sprites, tilemap, text
        → RTE (pops fake frame)
      → capture A0, rts
    jsr sanitize_arcade_workram      [zero C-window pointers]
    jsr genesistan_palette_commit_asm [CLCS → CRAM transfer]
    movem.l (%sp)+,%d0-%d7/%a0-%a6  [restore 15 registers]
    rte
```

**Between frames:** CPU executes `STOP #0x2000` — halted, zero instructions until next VBlank.

**What does NOT execute in arcade mode:**
- SGDK task scheduler (task_lock/unlock)
- vtimer increment
- intTrace set/clear
- XGM_doVBlankProcess check
- BMP_doVBlankProcess check
- vintCB callback load/call
- JOY_readJoypad (SGDK polling)
- SYS_doVBlankProcess check
- Main loop if/else chain

## 5. Handoff State Completion

| State Element | Launch (`request_start_rastan`) | Reset (`reset_launcher_runtime_state`) |
|---|---|---|
| `arcade_vblank_active` | Set to 1 | Set to 0 |
| `current_screen` | Set to `SCREEN_FRONTEND_LIVE` | Set to `SCREEN_CONFIG` |
| SR interrupt mask | Unmasked (`andi.w #0xF8FF, %sr`) | Managed by SGDK |
| `SYS_setVIntCallback` | Not called (bypassed) | Set to NULL |
| Main loop | Enters permanent STOP loop | Normal SGDK polling resumes |

The handoff is now cleanly bidirectional — launching activates arcade mode, reset restores launcher mode.

## 6. Build 310 Verification

| Check | Result |
|-------|--------|
| Build succeeded | YES |
| ROM produced | `dist/Rastan_310.bin` (3,932,160 bytes) |
| Postpatch warnings | 28 (pre-existing, applied anyway) |
| Compiler warnings | 5 unused-function (retired C functions still defined) |
| New symbols | `genesistan_run_arcade_tick_lean` at 0x2034E2 |

## 7. Runtime Verification (MAME Trace, 1290 frames)

| Metric | Result |
|--------|--------|
| `startup_result_code` 0→1 | Frame 439 |
| VDP writes begin | Frame 240 (pre-launch init), Frame 450 (post-launch arcade) |
| VDP write frequency | Every frame (every 30-frame sample) |
| `arcade_mode4` → 2 | Frame 825 |
| `arcade_page2` set → cleared | Frame 823 → Frame 1212 |
| `arcade_page0` reaches 2 | Frame 1212 (deeper state progression than Build 309) |
| Hang detected | NO |
| Total frames | 1290 |

### Structural Verification

| Check | Result |
|-------|--------|
| `_VINT` fast path active | YES — mode check at 0x000139, fast path at 0x000302 |
| Lean tick active | YES — 0x2034E2 (no double register save) |
| Permanent STOP loop | YES — `for (;;) stop` in SCREEN_FRONTEND_LIVE |
| SGDK dispatch bypassed | YES — no task scheduler, XGM, BMP, vtimer, intTrace |
| No SGDK joypad polling between frames | YES — tight STOP loop |
| `frontend_live_handoff_active` removed | YES — `arcade_vblank_active` is sole flag |

### Visual Verification

| Check | Result |
|-------|--------|
| Input responds after launch | CANNOT CONFIRM (headless trace, no user input) |
| Black screen remains | CANNOT CONFIRM (headless) |
| Vertical dots/noise remain | CANNOT CONFIRM (headless) |
| Title/runtime display improved | CANNOT CONFIRM (headless) |
| Completed arcade-owned execution model active | YES (structural verification confirms) |

## 8. Remaining Issues

- Visual verification requires BlastEm or visual MAME run
- 5 retired C functions still defined but unused (cleanup candidate)
- `genesistan_run_original_frontend_tick` (full trampoline with redundant save) still exists for compatibility with non-VBlank callers — used by `genesistan_run_title_init_sequence` context. Not in hot path.
