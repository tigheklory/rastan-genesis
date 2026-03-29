# Minimal Post-Launch Crash Handling Plan

## 1. Purpose

Define the smallest safe crash/exception strategy for post-launch runtime after SGDK vblank ownership is removed. The goal is crash visibility during active graphics bring-up without restoring SGDK frame ownership or building a large debug framework.

---

## 2. Current Crash/Exception State

### 2.1 What the project already has

The project ships a fully custom exception subsystem controlled by the compile-time flag `RASTAN_EXCEPTION_DUMPER_MODE`, defaulting to **mode 1** (text dump) as set in the Makefile (`apps/rastan/Makefile:9`).

The three modes are:

| Mode | Behavior |
|------|----------|
| 0 | SGDK default handlers (`_Bus_Error`, `_Address_Error`, etc.) — SGDK's own exception display |
| 1 | Custom project handlers: capture all registers + stack frame words, then call `rastan_exception_render()` which draws exception type, PC, SR, A-registers, SSP, and a 6-entry backtrace to VDP BG_A in text mode; loops forever |
| 2 | Same capture, but renders a QR code on-screen encoding the full crash payload; loops forever |

### 2.2 How vectors are wired

`apps/rastan/src/boot/sega.s` sets the M68K vector table at ROM offset 0 at link time. When `RASTAN_EXCEPTION_DUMPER_MODE != 0`, all eleven exception vectors (bus error, address error, illegal instruction, zero divide, CHK, TRAPV, privilege violation, trace, LINE 1010, LINE 1111, error exception) point to the project's own handlers in `z_qr_exception_handlers.s`. These vectors are in the Genesis ROM header and are active for the entire session — they cannot be overridden by the arcade ROM because the arcade ROM's code runs as translated C, not as a new ROM image with its own vector table.

### 2.3 What the custom handler does at runtime

`z_qr_exception_handlers.s` — `_Rastan_EX_Exception_Common`:
1. Immediately masks all interrupts (`move #0x2700, %sr`) — disables the arcade vblank ISR
2. Saves all D0–D7, A0–A7, SSP, USP to static variables
3. Copies 16 stack frame words to `rastan_qr_exc_frame_words`
4. Calls `rastan_exception_render()` (C function in `z_qr_exception.c`)
5. Loops forever after return

`rastan_exception_render()` calls `SYS_disableInts()` then draws to VDP directly using SGDK VDP helpers. It does NOT re-enter SGDK's frame/vblank ownership loop.

### 2.4 Current behavior on crash (mode 1, active default)

- Crash causes immediate interrupt mask
- All registers captured
- VDP reconfigured (320px, 64x32 plane, palette set)
- Text crash dump written to BG_A: exception type, PC, SR, key A-registers, backtrace candidates, raw stack frame words
- System halts — no reset, no watchdog
- Does NOT attempt to return to normal frame processing
- Does NOT re-enable SGDK vblank ownership

### 2.5 What SGDK's default handler would do (mode 0)

SGDK installs `_Bus_Error`, `_Address_Error`, etc. in `sys.c`. These call SGDK's `_errorexception_callback`, which displays a "genesis exception" screen using SGDK's own VDP/text routines and loops forever. That display does NOT require SGDK frame ownership — it is also a terminal handler. However it is less informative than mode 1 (no backtrace, no raw frame words).

---

## 3. Preferred Minimal Strategy

**Choice: D — Retain the project's existing custom exception display (`RASTAN_EXCEPTION_DUMPER_MODE=1`), which is already independent of SGDK frame ownership.**

This is not "retain SGDK's handler" — it is "retain the project's already-built superior replacement," which satisfies the spirit of option D.

---

## 4. Justification

The project already solved this problem. `RASTAN_EXCEPTION_DUMPER_MODE=1` is active by default. The handler:

- Is fully independent of SGDK frame timing — it masks the vblank ISR immediately on entry, so the arcade vblank owner is silenced by the exception itself before any display code runs
- Costs zero additional implementation — it exists and is compiled into every current build
- Provides PC, SR, A0/A1/A5/SP, exception type name, and a 6-entry backtrace scan — exactly what is needed during graphics bring-up to locate bad pointers
- Loops forever (visible halt), satisfying the requirement that crashes are not silent
- Does not require a power cycle — though it does not auto-reset, the build infrastructure can add watchdog behavior later without touching this design
- Causes no scope explosion — the files are already present and frozen

The only open question is whether to add auto-reset after the display (a loop-then-reset pattern). This is deferred: during active bring-up, a permanent halt is preferable because it keeps the crash dump on screen for inspection.

---

## 5. Implementation Boundary

### What Cody should do

1. Verify that the current production build is compiled with `RASTAN_EXCEPTION_DUMPER_MODE=1` (the Makefile default). No code changes are needed if confirmed.
2. If for any reason the current build was compiled with mode 0 or mode 2, set the Makefile default back to 1.
3. Optionally: verify in a BlastEm test that a deliberate bad-pointer write triggers the text crash dump and not a silent freeze.

### What Cody must NOT do

- Change any vblank handler, vblank ownership logic, or arcade vblank dispatch
- Modify the arcade ROM patch spec or any `.json` spec files
- Add SGDK frame ownership back to the exception path
- Expand `rastan_exception_render()` into a larger debug UI
- Modify the SAT/sprite pipeline work in progress
- Change the vector table wiring in `boot/sega.s` — it is already correct for mode 1
- Add watchdog/auto-reset behavior (out of scope for this plan; can be addressed post-bring-up)

### Files that may be touched (only if mode is wrong)

- `apps/rastan/Makefile` — confirm or correct `RASTAN_EXCEPTION_DUMPER_MODE ?= 1`

### Files that must remain untouched

- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/z_qr_exception.c`
- `apps/rastan/src/z_qr_exception_handlers.s`
- `apps/rastan/src/boot/sega.s`
- All `.json` spec files
- All sprite/SAT pipeline work

---

## 6. Success Criteria

1. A deliberate crash (e.g., write to address 0x000000 or a null pointer dereference) does NOT produce a silent freeze — the screen visibly changes within 1-2 frames.
2. The crash screen shows at minimum: exception type name, PC, and one or more register values.
3. The system halts on the crash screen (not a power-cycle-required freeze — the display itself is evidence the handler ran).
4. The exception handler does NOT re-enter SGDK frame ownership or the arcade vblank dispatch loop.
5. No changes to vblank architecture, sprite pipeline, or spec files are required to satisfy criteria 1–4.

---

## 7. Final Recommendation

The project's existing `RASTAN_EXCEPTION_DUMPER_MODE=1` path in `z_qr_exception_handlers.s` and `z_qr_exception.c` already implements the correct minimal post-launch crash strategy. It captures registers, disables interrupts (including the arcade vblank owner), renders a text dump to VDP without frame ownership, and halts. No new code is required. The only action needed is confirming the Makefile default is set to mode 1, which it currently is.

The preferred near-term crash strategy is intentionally minimal and does not restore SGDK frame ownership.
