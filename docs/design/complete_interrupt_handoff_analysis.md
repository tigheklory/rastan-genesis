# Complete Interrupt Handoff from Launcher to Arcade — Forensic Analysis

## 1. Executive Summary

The SGDK VBlank interrupt handler (`_VINT` in `sega.s`) is the **permanent hardware VBlank owner** after launch. The 68000 vector table is in ROM at address 0x00000078, pointing to `_VINT`. This cannot be changed without relocating the vector table to RAM. The user callback `genesistan_frontend_live_vint_handoff` is called from within `_VINT` via the `vintCB` function pointer every frame.

The arcade's VBlank handler at 0x03A008 never executes as a true interrupt handler. It is called **synchronously** from the SGDK callback via `genesistan_run_original_frontend_tick`, which builds a fake exception frame and JMPs into the arcade code. The arcade "VBlank" is a subroutine call disguised as an interrupt, not a real interrupt-driven frame owner.

The primary bug is: **the handoff from launcher to arcade never installs the arcade as the true VBlank owner because the 68000 vector table is in ROM and permanently points to SGDK's `_VINT`**. The SGDK interrupt dispatcher — including its task scheduler, `vtimer` increment, XGM sound process check, and BMP process check — runs every frame between the hardware VBlank and the arcade tick, adding latency and maintaining SGDK as the active frame mediator.

## 2. Current Interrupt Ownership Before Launch

**Before `request_start_rastan()` is called:**

| Resource | Owner | Mechanism |
|----------|-------|-----------|
| 68000 VBlank vector (0x78) | SGDK `_VINT` | ROM vector table (`sega.s:73`) |
| VBlank callback (`vintCB`) | NULL (no user callback) | `reset_launcher_runtime_state()` sets `SYS_setVIntCallback(NULL)` (`main.c:2049`) |
| Frame progression | SGDK main loop | `SYS_doVBlankProcess()` called each iteration (`main.c:2278`) |
| HInt | Disabled | Not configured in launcher |
| Z80 | Running (SGDK default) | SGDK init starts Z80 with default sound driver |
| Task scheduler | Active | SGDK `_VINT` checks `task_lock` every frame (`sega.s:143`) |

**Launcher frame model:** The `main()` while-loop polls joypad input, updates display, and calls `SYS_doVBlankProcess()` to synchronize with VBlank. The VBlank interrupt fires `_VINT`, which runs the task scheduler and calls `vintCB` (NULL = no-op). The launcher is driven by the main loop, not the interrupt.

## 3. Current Interrupt Ownership After Launch

**After `request_start_rastan()` completes:**

| Resource | Owner | Mechanism |
|----------|-------|-----------|
| 68000 VBlank vector (0x78) | SGDK `_VINT` | **UNCHANGED** — ROM vector table, cannot be modified |
| VBlank callback (`vintCB`) | `genesistan_frontend_live_vint_handoff` | `SYS_setVIntCallback()` at `main.c:1996` |
| Frame progression | SGDK `_VINT` → user callback → arcade tick | Callback calls `genesistan_run_original_frontend_tick()` synchronously |
| HInt | Disabled | `VDP_setHInterrupt(0)` at `main.c:1985` |
| Z80 | Held in reset | `Z80_startReset()` at `startup_bridge.c:284` |
| Task scheduler | **Still active** | `_VINT` still checks `task_lock` before calling user callback |
| XGM process check | **Still active** | `_VINT` checks `PROCESS_XGM_TASK` flag at `sega.s:175` |
| BMP process check | **Still active** | `_VINT` checks `PROCESS_BITMAP_TASK` flag at `sega.s:181` |
| Main loop | **Still running** | `while(TRUE)` at `main.c:2141` — enters empty `SCREEN_FRONTEND_LIVE` branch |
| `SYS_doVBlankProcess()` | **Skipped** | `main.c:2276-2278` — not called when `current_screen == SCREEN_FRONTEND_LIVE` |

**Post-launch frame execution sequence:**

```
Hardware VBlank fires
  → 68000 vectors to _VINT (sega.s:139)
    → SGDK task scheduler logic (sega.s:140-165)
    → save d0-d1/a0-a1 (sega.s:172)
    → intTrace |= 1 (sega.s:173)
    → vtimer++ (sega.s:174)
    → check XGM flag → XGM_doVBlankProcess if set (sega.s:175-178)
    → check BMP flag → BMP_doVBlankProcess if set (sega.s:181-184)
    → load vintCB → call genesistan_frontend_live_vint_handoff (sega.s:187-188)
      → genesistan_refresh_arcade_inputs() (main.c:2119)
      → genesistan_run_original_frontend_tick() (main.c:2120)
        → build fake exception frame (startup_trampoline.s:880-881)
        → JMP 0x03A008+ARCADE_ROM_BASE (startup_trampoline.s:882)
          → arcade VBlank state machine executes
          → opcode hooks fire (scroll, sprites, tilemap, text)
          → arcade code executes RTE
        → returns to genesistan_frontend_tick_return (startup_trampoline.s:884)
      → sanitize_arcade_workram() (main.c:2121)
      → genesistan_palette_commit_asm() (main.c:2122)
    → intTrace &= ~1 (sega.s:189)
    → restore d0-d1/a0-a1 (sega.s:190)
    → RTE (sega.s:191)
```

**Who owns VBlank after launch?** SGDK's `_VINT` is the hardware VBlank owner. The arcade VBlank handler at 0x03A008 runs only as a synchronous subroutine call **inside** the SGDK callback, not as a true interrupt handler.

**Does the arcade VBlank code run directly?** No. It runs only through SGDK callback mediation. The call chain is: `_VINT` → SGDK dispatch → `vintCB` → C callback → ASM trampoline → fake exception frame → arcade JMP. The arcade code believes it is running from a VBlank interrupt (because of the fake SR/PC frame), but it is actually nested inside the SGDK interrupt handler.

## 4. Why SGDK VBlank Was Left Active

The SGDK VBlank was left active because **it cannot be removed without relocating the 68000 vector table to RAM**.

The Genesis 68000 vector table is in ROM:
- `sega.s:48`: `.org 0x00000000`
- `sega.s:73`: `dc.l _VINT` at the level-6 autovector position (offset 0x78)

This is a **ROM address**. The 68000 reads the VBlank vector from 0x00000078 on every VBlank. Since the ROM cannot be modified at runtime, `_VINT` is permanently the VBlank handler.

The implementation chose to work within this constraint by:
1. Installing a user callback via `SYS_setVIntCallback()` (`main.c:1996`)
2. Having that callback invoke the arcade tick synchronously (`main.c:2120`)
3. Leaving the SGDK dispatch infrastructure in place

This was not an oversight — it was the path of least resistance. But it means:
- The SGDK task scheduler runs every frame (even though no SGDK tasks are active post-launch)
- The XGM and BMP process flags are checked every frame (even though neither is used)
- The `vtimer` counter increments every frame (unused post-launch)
- The `intTrace` flag is set/cleared every frame (unused post-launch)
- The main loop continues running with an empty `SCREEN_FRONTEND_LIVE` branch, consuming CPU between VBlanks

**No sound dependency holds SGDK open.** The Z80 is held in reset (`Z80_startReset()` at `startup_bridge.c:284`). Sound commands go to shadow registers only (`genesistan_sound_send_command` in `startup_trampoline.s:38-47`). XGM is not initialized for the arcade game. The `PROCESS_XGM_TASK` flag check is overhead, not a dependency.

## 5. Correct Complete Handoff Model

The correct model after launch:

### What Must Be Disabled
1. **SGDK task scheduler**: The `_VINT` task_lock/unlock logic (lines 140-165) should not run post-launch. No SGDK tasks are active.
2. **XGM process check**: No XGM sound is in use. The Z80 is held in reset.
3. **BMP process check**: No bitmap mode is in use.
4. **SGDK `vtimer`/`intTrace` bookkeeping**: Not needed by arcade code.
5. **Main loop polling**: The `while(TRUE)` loop with `JOY_readJoypad` runs between VBlanks but does nothing for `SCREEN_FRONTEND_LIVE`. It wastes CPU that could be used for inter-frame work or power savings (STOP instruction).

### What Must Remain Enabled
1. **68000 level-6 interrupt**: VBlank must still fire — this is the frame clock.
2. **VDP VBlank interrupt enable**: VDP register 1 bit 5 must remain set.
3. **Arcade tick execution**: The arcade VBlank handler at 0x03A008 must execute once per frame.
4. **`genesistan_palette_commit_asm`**: Must execute once per frame after arcade tick (CLCS→CRAM transfer).
5. **Input refresh**: `genesistan_refresh_arcade_inputs()` must execute once per frame before arcade tick.
6. **Workram sanitize**: `sanitize_arcade_workram()` must execute once per frame after arcade tick.

### What Becomes the New VBlank Owner
A **minimal VBlank handler** that replaces SGDK's `_VINT` as the effective frame owner. Two approaches:

**Approach A — Minimal SGDK callback (least invasive):**
Keep `_VINT` as the hardware handler but accept the SGDK dispatch overhead (~50 cycles of task scheduler + flag checks). The user callback is already lean (4 calls). This approach acknowledges that the SGDK overhead is small and the vector table constraint is real. The main loop should be modified to execute a `STOP #0x2000` instruction instead of busy-polling, yielding CPU to the interrupt.

**Approach B — RAM vector table (complete handoff):**
Write a new VBlank handler in assembly. At launch time, copy the 68000 vector table to RAM (0xFF0000 area), modify the VBlank vector to point to the new handler, and set VDP register 0 bit 0 to enable RAM vector table mode (if the Genesis/SGDK supports this — note: the Mega Drive does not have a hardware RAM vector table bit like some 68000 systems; the vector table is always read from 0x000000 in the ROM). This approach is **not possible on stock Genesis hardware** without a mapper or bank-switching scheme.

**Approach C — Patched `_VINT` with mode switch (correct practical approach):**
Modify the project's copy of `sega.s` (which is already customized — it has the RASTAN_EXCEPTION_DUMPER_MODE changes). Add a mode flag checked at the very top of `_VINT`. When the flag is set (post-launch), skip the task scheduler, XGM check, BMP check, vtimer, and intTrace — jump directly to a minimal handler that calls the arcade frame sequence and RTEs. When the flag is clear (launcher mode), run the full SGDK dispatch as before.

This is the correct approach because:
- `sega.s` is already a project-local copy with custom modifications
- No hardware constraints prevent modifying the handler code
- The mode flag adds one `tst.w` + `bne` (~8 cycles) to normal launcher operation
- Post-launch, the entire SGDK dispatch is bypassed
- The main loop can be halted with STOP or an infinite-wait loop

### How the Arcade Gets Control Each Frame (Approach C)

```
Hardware VBlank fires
  → 68000 vectors to _VINT (sega.s)
    → tst.w arcade_vblank_active
    → bne _VINT_arcade_mode
      (launcher path: full SGDK dispatch as before)

_VINT_arcade_mode:
    → save d0-d7/a0-a6
    → genesistan_refresh_arcade_inputs
    → build fake exception frame, JMP 0x03A008+ARCADE_ROM_BASE
    → (arcade tick + all opcode hooks)
    → genesistan_frontend_tick_return
    → sanitize_arcade_workram
    → genesistan_palette_commit_asm
    → restore d0-d7/a0-a6
    → RTE
```

Total overhead between hardware VBlank and arcade code: ~20 cycles (flag test + branch + register save). Current overhead: ~100+ cycles (task scheduler logic + flag checks + vtimer + intTrace + callback indirection).

## 6. Single Primary Interrupt Ownership Bug

**The SGDK interrupt dispatcher (`_VINT` in `sega.s`) remains the unconditional frame mediator after launch, with no mode switch to bypass its task scheduler, process flags, and bookkeeping.**

Justification from code:

1. `_VINT` at `sega.s:139-191` runs the full SGDK dispatch on every VBlank, regardless of whether the launcher or the arcade game is active.

2. Lines 140-165: The task scheduler checks `task_lock` and potentially performs a context switch — this is launcher/SGDK infrastructure that has no purpose when the arcade is running.

3. Lines 173-174: `intTrace` and `vtimer` are SGDK bookkeeping — unused by the arcade.

4. Lines 175-178: `XGM_doVBlankProcess` is checked every frame even though the Z80 is held in reset and XGM is not in use.

5. Lines 181-184: `BMP_doVBlankProcess` is checked every frame even though bitmap mode is not in use.

6. Lines 187-188: The arcade tick only reaches execution after all of the above has run. The arcade is the **last** thing called in the VBlank, after SGDK has consumed the most timing-critical portion of the VBlank window.

7. `main.c:2183-2189`: The main loop's `SCREEN_FRONTEND_LIVE` branch is empty but still polls `JOY_readJoypad` every iteration, wasting CPU between frames.

This is not a theoretical problem. The VBlank window on Genesis is approximately 4,500 68000 cycles (NTSC). Every cycle consumed by SGDK dispatch before the arcade tick starts is a cycle unavailable for DMA transfers and VDP writes that must complete within VBlank. The SGDK overhead (task scheduler + flag checks + bookkeeping + callback indirection) consumes cycles that should be available to the arcade's VDP operations.

## 7. Exact Next Implementation Target

**Modify `apps/rastan/src/boot/sega.s` to add a post-launch fast path in `_VINT`.**

Specifically:

1. Add a global flag: `arcade_vblank_active` (word-sized, in `.bss`)

2. At the top of `_VINT` (immediately after `sega.s:139`), before the task scheduler logic at line 140:
   ```asm
   _VINT:
       tst.w   arcade_vblank_active
       bne     _VINT_arcade_mode
       /* ... existing SGDK dispatch ... */
   ```

3. Add `_VINT_arcade_mode` label (at end of `_VINT` or in `startup_trampoline.s`):
   - Save registers
   - Call `genesistan_refresh_arcade_inputs`
   - Call `genesistan_run_original_frontend_tick` (or inline its trampoline logic)
   - Call `sanitize_arcade_workram`
   - Call `genesistan_palette_commit_asm`
   - Restore registers
   - RTE

4. In `request_start_rastan()` (`main.c`):
   - Remove `SYS_setVIntCallback(genesistan_frontend_live_vint_handoff)` and `SYS_enableInts()`
   - Instead: set `arcade_vblank_active = 1` and ensure SR interrupt mask allows level 6

5. Retire `genesistan_frontend_live_vint_handoff` — it is replaced by the `_VINT_arcade_mode` fast path.

6. In the main loop's `SCREEN_FRONTEND_LIVE` branch: replace the empty body with `stop #0x2000` (halt CPU until next interrupt) or an equivalent low-power wait.

**Files to modify:**
- `apps/rastan/src/boot/sega.s` — add mode flag check at top of `_VINT`, add `_VINT_arcade_mode` handler
- `apps/rastan/src/startup_trampoline.s` — may host `_VINT_arcade_mode` implementation
- `apps/rastan/src/main.c` — set flag in `request_start_rastan()`, retire callback, modify main loop

**What this achieves:**
- SGDK dispatch is completely bypassed after launch
- No task scheduler, no XGM check, no BMP check, no vtimer, no intTrace
- Arcade tick executes within ~20 cycles of hardware VBlank (vs ~100+ currently)
- Main loop stops busy-polling
- The VBlank callback indirection is eliminated — the arcade handler IS the VBlank handler

## 8. Final Verdict

The current architecture has SGDK's `_VINT` as the permanent, unconditional VBlank handler. After launch, the arcade game runs as a nested subroutine call inside the SGDK interrupt dispatcher, behind the task scheduler, XGM process check, BMP process check, and bookkeeping logic. The launcher's main loop continues running with an empty branch, wasting CPU.

The fix is a mode-switched `_VINT`: one `tst.w` + `bne` at the top of the handler routes post-launch VBlanks directly to a minimal arcade frame handler, completely bypassing SGDK dispatch. This is practical because `sega.s` is already a project-local customized copy. No hardware constraints prevent this change. The arcade becomes the true VBlank owner with minimal interrupt-to-execution latency.
