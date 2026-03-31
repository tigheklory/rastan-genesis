# Build 309 — _VINT Arcade Handoff Completion Report

## 1. Recovery Status

Prior edit session was interrupted. Tree verification confirmed all edits landed cleanly:

| File | Edits Present | Status |
|------|--------------|--------|
| `sega.s` | Mode switch at top of `_VINT` (line 140-141), `_VINT_arcade_mode` handler (lines 202-209) | Complete |
| `main.c` | `arcade_vblank_active` extern, launch flag set, SR unmask, `sanitize_arcade_workram` non-static, callback retired, STOP in main loop, reset clears flag | Complete |
| `startup_trampoline.s` | `.globl arcade_vblank_active`, BSS allocation | Complete |

No broken half-edits found. Recovery = clean verification pass only.

## 2. _VINT Mode-Switch Implementation

### Before (Build 308)
```asm
_VINT:
    btst    #5, (%sp)           /* task scheduler */
    ...                          /* SGDK dispatch: task_lock, vtimer, XGM, BMP */
    move.l  vintCB, %a0         /* callback indirection */
    jsr     (%a0)               /* call genesistan_frontend_live_vint_handoff */
    ...
    rte
```

### After (Build 309)
```asm
_VINT:
    tst.w   arcade_vblank_active    /* Arcade mode? Skip ALL SGDK dispatch */
    bne     _VINT_arcade_mode

    btst    #5, (%sp)               /* Launcher: full SGDK path unchanged */
    ... (unchanged SGDK dispatch) ...
    rte

_VINT_arcade_mode:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    jsr     genesistan_refresh_arcade_inputs
    jsr     genesistan_run_original_frontend_tick
    jsr     sanitize_arcade_workram
    jsr     genesistan_palette_commit_asm
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rte
```

**Bypassed in arcade mode:**
- Task scheduler (task_lock/unlock)
- vtimer increment
- intTrace set/clear
- XGM_doVBlankProcess check
- BMP_doVBlankProcess check
- vintCB callback indirection

**Symbol addresses:**
- `_VINT_arcade_mode`: 0x000302
- `arcade_vblank_active`: 0xE0FF404C (BSS)
- `sanitize_arcade_workram`: 0x213868

## 3. Launch-Path Handoff Changes

### request_start_rastan() (main.c)

**Removed:**
```c
SYS_setVIntCallback(genesistan_frontend_live_vint_handoff);
SYS_enableInts();
```

**Added:**
```c
arcade_vblank_active = 1;
__asm__ volatile("andi.w #0xF8FF, %sr");  /* unmask all interrupts */
```

### reset_launcher_runtime_state() (main.c)
```c
arcade_vblank_active = 0;  /* Clear flag on reset */
```

### genesistan_frontend_live_vint_handoff
Retired. Function body replaced with comment. No longer participates in frame execution.

## 4. Main-Loop Wait Change

**Before:**
```c
else if (current_screen == SCREEN_FRONTEND_LIVE)
{
    /* empty — busy-spin */
}
```

**After:**
```c
else if (current_screen == SCREEN_FRONTEND_LIVE)
{
    __asm__ volatile("stop #0x2000");
}
```

CPU halts between VBlanks. SR 0x2000 = supervisor mode, all interrupts unmasked. Wakes on next VBlank.

## 5. sanitize_arcade_workram Visibility

Changed from `static void` to `void` in main.c to make it callable from `_VINT_arcade_mode` in sega.s via `jsr sanitize_arcade_workram`.

## 6. Build 309 Verification

| Check | Result |
|-------|--------|
| Build succeeded | YES |
| ROM produced | `dist/Rastan_309.bin` (3,932,160 bytes) |
| Postpatch warnings | 28 (all pre-existing shift-related, applied anyway) |
| Compiler warnings | 5 unused-function (expected: retired C functions still defined) |
| Linker errors | None |

## 7. Runtime Verification (MAME Trace, 840 frames)

| Metric | Result |
|--------|--------|
| `startup_result_code` 0→1 | Frame 408 |
| VDP writes begin | Frame 420 |
| VDP write frequency | Every frame (every 30-frame sample shows vdp_ports activity) |
| `helper_frontend_timers` entered | Frame 677 |
| `arcade_mode4` → 2 | Frame 790 |
| `arcade_page2` set | Frame 788 |
| Hang detected | NO |
| Total frames | 840 |

### Structural Verification

| Check | Result |
|-------|--------|
| `_VINT` fast path active in arcade mode | YES — mode check at 0x000139, fast path at 0x000302 |
| `genesistan_frontend_live_vint_handoff` still active owner | NO — retired, not called |
| SGDK scheduler bypassed in arcade mode | YES — `bne _VINT_arcade_mode` skips all SGDK dispatch |
| Main loop STOP active | YES — PC at 0x21215x between frames confirms STOP wait |
| CPU halts between VBlanks | YES — trace shows consistent wake-at-VBlank pattern |

### Visual Verification

| Check | Result |
|-------|--------|
| Flicker improved | CANNOT CONFIRM (headless trace) |
| Vertical dots improved | CANNOT CONFIRM (headless trace) |
| Black screen still present | CANNOT CONFIRM (headless trace) |
| Title/content improved | CANNOT CONFIRM (headless trace) |

Visual verification requires BlastEm or visual MAME run.

## 8. Remaining Issues

- Visual verification pending (requires emulator with display output)
- 28 postpatch warnings are pre-existing operand mismatches — not related to this change
- 5 retired C functions still defined but unused — can be cleaned up in a future pass
- `frontend_live_handoff_active` flag still exists but is now redundant with `arcade_vblank_active` — can be unified later
