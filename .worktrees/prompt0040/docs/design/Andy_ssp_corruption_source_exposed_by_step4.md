# Andy — SSP Corruption Source Exposed by Step 4

## 1. Executive Summary

The working theory is CORRECT but needs one clarification. Step 4 did NOT create the SSP
corruption. A pre-existing call-convention mismatch between `arcade_tick_logic` and the arcade
tick handler is the root cause. The arcade tick routine at Genesis address 0x0003A208
(arcade ROM offset 0x3A008) is an interrupt service routine that terminates with `RTE`, not
`RTS`. It is called via `jsr rastan_direct_arcade_tick_entry`, which pushes 4 bytes (return
PC) to the stack. The `RTE` at the end of the arcade handler pops 6 bytes (SR + PC). Every
call net-shifts SP upward by +2 bytes and returns execution to a garbled PC constructed from
wrong stack bytes. This corrupts execution on the very first frame. Step 4's additional nested
`bsr` inside `_VINT_handler` exposed this existing corruption because a deeper call chain
within a VBlank occurring after the initial stack corruption produces a more visibly broken
failure mode, but the crash was always present.

## 2. Inputs Audited

- `apps/rastan-direct/src/main_68k.s` — complete source, all functions traced
- `apps/rastan-direct/src/boot/boot.s` — vector table and exception layout verified
- `docs/design/Cody_bg_row_dirty_strip_commit.md` — Step 4 design doc, full review
- `AGENTS_LOG.md` — last 100 lines reviewed (build 0012, strip commit implementation confirmed)
- `build/maincpu.disasm.txt` — arcade ROM disassembly, all A7/SP-modifying instructions searched
- `build/regions/maincpu.bin` — arcade ROM binary, byte-level opcode verification
- `apps/rastan-direct/dist/rastan_direct_video_test.bin` — Genesis ROM, vector table verified

## 3. Step 4 Call-Nesting Analysis

### Previous whole-plane implementation (pre-Step 4)

The previous `vdp_commit_bg` function is not in the current source (it was removed per
Cody's implementation log entry). The design doc confirms it was replaced entirely.
Whether the old `vdp_commit_bg` called `bsr vdp_commit_tiles_if_dirty` or inlined the tile
check cannot be determined from static analysis of the current codebase alone — the old
code is absent. This is UNKNOWN.

### Step 4 call chain

```
_VINT_handler
  bsr vdp_set_reg              (depth +1)
  bsr vdp_commit_bg_strips_if_dirty   (depth +1)
    bsr vdp_commit_tiles_if_dirty      (depth +2)
      bsr vdp_set_vram_write_addr       (depth +3) — not present, vdp_set_vram_write_addr
                                                       is called directly inside tiles_if_dirty
      [no further nesting]
    bsr vdp_set_vram_write_addr         (depth +2, per dirty row)
  bsr vdp_commit_palette        (depth +1)
  bsr vdp_set_reg               (depth +1)
  bsr vdp_commit_scroll         (depth +1)
    bsr vdp_set_vram_write_addr  (depth +2)
```

`vdp_commit_tiles_if_dirty` contains one `bsr vdp_set_vram_write_addr` call.
`vdp_commit_bg_strips_if_dirty` contains one `bsr vdp_commit_tiles_if_dirty` and, for each
dirty row, one `bsr vdp_set_vram_write_addr`. Maximum nesting depth inside `_VINT_handler`
is **3 levels** (handler → strip_commit → set_vram_write_addr).

If the previous `vdp_commit_bg` did NOT call `vdp_commit_tiles_if_dirty` via `bsr` (i.e.,
it was inline), then Step 4 added one additional level of nesting. If it did call it via
`bsr`, the nesting depth is unchanged.

### Does the added nesting matter for the actual crash?

No. The crash occurs before any VBlank handler nesting matters. The system is already in a
corrupted state from frame 1 due to the JSR/RTE mismatch described in Section 5.

## 4. Direct Step 4 Stack-Bug Audit

### `vdp_commit_bg_strips_if_dirty`

- Register usage: D4, D5, D6 (loop counters/indices). D7 used implicitly via `move.w` in
  the row copy inner loop. A0 used via `lea`.
- No registers saved/restored explicitly. This is acceptable because `_VINT_handler` saves
  and restores D0–D7/A0–A6 around the whole handler body.
- The `bsr vdp_commit_tiles_if_dirty` is paired with the `rts` at the end of that function.
  Stack is balanced.
- No A7/SP modification.
- No mismatched push/pop.
- Early-exit path at `.Lbg_done` falls through to `rts`. No fallthrough bypass.
- The `.Lbg_next_row` branch and the inner `beq.s .Lbg_done` path all converge at `rts`.

**No direct stack bug found.**

### `vdp_commit_tiles_if_dirty`

- Uses A0 (via `lea staged_tile_words`) and D7 (loop counter).
- `bsr vdp_set_vram_write_addr` is paired with that function's `rts`.
- Early-exit at `.Ltiles_done` is clean.
- No A7/SP modification.

**No direct stack bug found.**

## 5. SSP/A7 Corruption Source Analysis

### The arcade tick entry point is an ISR, not a subroutine

Arcade ROM offset 0x3A008 (Genesis address 0x0003A208) is the `rastan_direct_arcade_tick_entry`
routine. Static disassembly of the byte sequence at that address confirms:

```
3a008: 007c 0f00    oriw  #0x0F00, %sr      ; disable interrupts (IPM = 7)
3a00c: 4279 ...     clrw  0x350008           ; watchdog kick
...                 (multiple BSR calls to sub-functions)
3a07a: 027c f0ff    andiw #0xF0FF, %sr      ; re-enable interrupts
3a07e: 4e73         rte                      ; ← terminates with RTE, not RTS
```

This routine is the arcade hardware's VBlank interrupt service routine. It begins by
disabling interrupts via `ORI #0x0F00, %sr` and ends with `RTE`.

### The mismatch

`arcade_tick_logic` in `main_68k.s` calls this with:

```asm
jsr  rastan_direct_arcade_tick_entry
```

`JSR` pushes 4 bytes (return address PC) to the supervisor stack and jumps. `RTE` pops 6
bytes (2-byte SR + 4-byte PC). The net stack effect per call:

```
JSR pushes: -4 bytes (SP decrements by 4)
RTE pops:   +6 bytes (SP increments by 6)
Net:        +2 bytes per call (SP drifts upward)
```

The SR that `RTE` reads is the **high 2 bytes of the return PC** that `JSR` pushed. The PC
that `RTE` jumps to is the **low 2 bytes of the return PC concatenated with 2 bytes that
were already on the stack before the `JSR`**. This is completely garbled execution.

### Execution trace — frame 0/1

Before the first `arcade_tick_logic` call, SP is approximately 0xFEFFF4 (after `_start` JSR
to `main_68k` and several `bsr` calls for init that return cleanly). On the first call:

1. `bsr arcade_tick_logic` pushes return addr: SP = 0xFEFFF0
2. `bsr rastan_direct_update_inputs` (balanced)
3. `jsr rastan_direct_arcade_tick_entry`: SP = 0xFEFFEC, pushes return-to-rts-in-tick_logic
4. Arcade handler runs its BSR sub-calls (all balanced)
5. `RTE` at 0x3A07E: reads SR from 0xFEFFEC (= high word of return addr), reads PC from
   0xFEFFEE (= low word of return addr | bytes from earlier stack frame), SP → 0xFEFFEC + 6 = 0xFEFFF2
6. CPU jumps to garbled PC

From this point, execution is at a random address. Subsequent instructions may push/pop
in arbitrary amounts, eventually moving SP away from the initial 0xFFxxxx range.

### Observed state reconciliation

- **Frames 1, 60, 240, 478: PC = 0x00000200, SSP = 0x00E0000A** — The garbled execution
  eventually triggers an exception (illegal instruction, bus error, or similar). The
  exception vector for nearly all exception types points to 0x00000200 (`_default_handler` =
  `RTE`). With SSP = 0x00E0000A, the `RTE` reads SR+PC from ROM address 0x00E0000A. The
  ROM bytes at that address happen to resolve to a PC value of 0x00000200 again, creating a
  stable loop: `PC=0x000200, SSP=0x00E0000A` repeats every frame.

- **Frame 120: PC = 0x00702D00, SSP = 0x00F6E264** — This is a transient state during
  garbled execution. PC 0x00702D00 is 7,351,040 bytes past the arcade ROM copy start
  (arcade ROM ends at Genesis address 0x060200). The game has left all valid code regions.
  SSP 0x00F6E264 is in the 0xF-range, consistent with SP having drifted from 0xFEFFxx
  downward (via net +2 drift plus arbitrary push/pop from garbled code). This is NOT valid
  game execution — it is garbled code running after the RTE mismatch corrupted the first
  frame.

### A7 corruption path — exact mechanism

`SSP = 0x00E0000A` results from garbled code executing after the JSR/RTE mismatch. The
exact sequence of instructions that moves SP from ~0xFEFFF2 to 0x00E0000A cannot be
determined by static analysis because they are executed at addresses outside the known
code region. A runtime trace would be required to map the exact path.

The value 0x00E0000A is in the cartridge ROM address space (Genesis ROM maps 0x000000–
0x3FFFFF). Address 0x00E0000A contains valid ROM bytes; the `_default_handler` RTE loop
reads those bytes as SR and PC, which happens to reconstruct PC = 0x000200, sustaining
the loop.

### Confirming this is pre-existing (not caused by Step 4)

The JSR/RTE mismatch exists in `arcade_tick_logic` which has not been modified by Step 4.
Step 4 only changed:
1. The BG commit function called from `_VINT_handler`
2. Added `bg_row_dirty` dirty bits and strip-based commit

None of these touch `arcade_tick_logic` or the JSR to `rastan_direct_arcade_tick_entry`.
The crash would occur with or without Step 4.

### Why Step 4 "exposes" it

Before Step 4, the VINT handler had fewer nested BSR calls. With a corrupted SSP in the
0x00E0000A range, each BSR inside `_VINT_handler` pushes a return address to an invalid
ROM address (ROM is read-only; the write is ignored by the emulator or causes a bus error).
The additional BSR nesting introduced by Step 4 makes it more likely that a VBlank fires
at a moment when the corruption is in a specific state that produces the observed lock
rather than a different failure mode. The fundamental behavior — crashing on frame 1 —
is unchanged.

## 6. Exception Path to 0x00000200

From `boot.s`:

```asm
.org 0x000000
.long 0x00FF0000      ; vec[0] = initial SSP
.long _start          ; vec[1] = initial PC
.rept 28
.long _default_handler ; vec[2]-vec[29] = 0x000200
.endr
.long _VINT_handler   ; vec[30] = Level 6 (VBlank)
.long _default_handler ; vec[31]
.rept 32
.long _default_handler ; vec[32]-vec[63]
.endr

.org 0x000200
_default_handler:
    rte
```

ALL exception vectors except `_VINT_handler` (vec[30]) point to 0x00000200.
This includes: bus error (vec[2]), address error (vec[3]), illegal instruction (vec[4]),
divide by zero (vec[5]), privilege violation (vec[8]), line-A emulator (vec[10]),
line-F emulator (vec[11]), and all user-defined traps and auto-vectors except VINT.

When garbled execution triggers any of these exceptions:
1. 68000 hardware saves SR + PC to SSP; PC loads from exception vector = 0x000200
2. `_default_handler` executes `RTE`
3. `RTE` pops SR + PC from SSP = 0x00E0000A
4. ROM at 0x00E0000A yields bytes that reconstruct PC = 0x000200
5. CPU loops: every exception returns to 0x000200, which immediately re-fires via RTE

This is the stable loop observed at frames 1, 60, 240, and 478.

**Why does this note also appear at frame 1, before 60+ frames of valid game output?**
Because the crash happens on frame 0 or 1 (the very first `arcade_tick_logic` call). The
VBlank interrupt fires after init but before the first game tick executes more than a few
instructions. There is no "60 frames of valid game output" — the system is locked in the
exception loop from frame 1 onward.

## 7. Keep-or-Revert Decision for Step 4

**KEEP Step 4.**

Step 4 is structurally correct. `vdp_commit_bg_strips_if_dirty` and
`vdp_commit_tiles_if_dirty` have no stack bugs. The call nesting is balanced. The register
usage is safe within the context of `_VINT_handler` (which saves/restores all working
registers). Reverting Step 4 would not fix the crash — the JSR/RTE mismatch would still
exist and the crash would persist.

## 8. Single Root Cause

`arcade_tick_logic` calls the arcade's VBlank ISR at 0x0003A208 via `jsr`, but that
routine terminates with `rte` instead of `rts`; each call pops 2 more bytes from the stack
than were pushed by the `jsr`, immediately corrupting the return PC and drifting the
supervisor stack pointer to an invalid address on the first game frame.

## 9. Single Next Correction

In `arcade_tick_logic`, replace the `jsr rastan_direct_arcade_tick_entry` with a call
wrapper that constructs a proper 68000 exception frame on the stack before transferring
control: push the desired return address and a safe SR value explicitly, then use `jmp`
(not `jsr`) to transfer to `rastan_direct_arcade_tick_entry`. The arcade's `rte` will then
pop this constructed frame and return to the correct address with the correct SR.

Concretely, the replacement for:
```asm
jsr  rastan_direct_arcade_tick_entry
```
is:
```asm
move.w  %sr, -(%sp)               ; push SR (2 bytes)
pea     .Ltick_return             ; push return address (4 bytes) -- total 6 bytes = RTE frame
jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
```
This constructs the 6-byte frame that `rte` expects: SR (2 bytes) + PC (4 bytes).

## 10. What Must Not Be Changed Yet

- All opcode_replace entries in `specs/rastan_direct_remap.json` (34 entries)
- The `c_window` declared arcade window declaration
- `rom_absolute_call_relocation` configuration
- A5 initialization in `main_68k.s` (`lea 0x00FF0000, %a5` in `init_staging_state`)
- `genesistan_hook_tilemap_plane_a` implementation (structurally correct)
- `vdp_commit_bg_strips_if_dirty` and `vdp_commit_tiles_if_dirty` (Step 4, correct)
- `bg_row_dirty` dirty-bit mechanism (Step 4, correct)
- All other VDP commit functions (`vdp_commit_palette`, `vdp_commit_scroll`,
  `vdp_set_reg`, `vdp_set_vram_write_addr`)
- The `_VINT_handler` structure (correct; the movem save/restore is correct)
- The boot.s vector table layout

## 11. Final Verdict

Step 4 is correct and should be kept. The SSP corruption is a pre-existing call-convention
bug: the arcade tick handler is an ISR (terminates with `rte`) being invoked via `jsr`. The
fix is a one-instruction change in `arcade_tick_logic` that constructs a proper exception
frame before jumping to the arcade tick handler, allowing its `rte` to return correctly.
Step 4 did not cause this and does not need to be reverted.
