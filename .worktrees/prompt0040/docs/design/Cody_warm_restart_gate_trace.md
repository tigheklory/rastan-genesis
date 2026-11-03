# Cody — Warm-Restart Gate Runtime Trace + Supporting Decompilation (Build 0051)

Agent: Cody  
Type: Runtime Trace + Reference Decompilation  
ROM under test: `dist/rastan-direct/rastan_direct_video_test_build_0051.bin`

Architecture compliance: CONFIRMED (trace/decomp only; no source/spec/tool edits)

## Phase 1 — Ghidra Coverage Verification

### Gate region (arcade_pc 0x039F80..0x039FC0)
- Existing export verified: `docs/design/ghidra_exports/039F9E_warm_restart_trampoline.txt`
- Coverage present in file:
  - `arcade_pc 0x039F80`: `tst.w (0x2c,A5)`
  - `arcade_pc 0x039F84`: `beq.b 0x39F8C`
  - `arcade_pc 0x039F86`: `subq.w #1,(0x2c,A5)`
  - `arcade_pc 0x039F9E`: trampoline entry
  - `arcade_pc 0x039FA8`: `bcs.b 0x39FAC`
  - `arcade_pc 0x039FAA`: `bra.b 0x39F8C`
  - `arcade_pc 0x039FAC`: `rts`
- Result: **Gate coverage complete for the runtime gate-entry decision path**.

### Caller A region (arcade_pc 0x03AB80..0x03AB90)
- Existing exports verified:
  - `docs/design/ghidra_exports/03AB84_reset_gate_cmp_site.txt`
  - `docs/design/ghidra_exports/03AB8A_reset_gate_bsr_site.txt`
- Includes:
  - `arcade_pc 0x03AB84`: `cmpi.w #0x100,(0x12,A5)`
  - `arcade_pc 0x03AB8A`: `bsr.w 0x39FA8`
- Result: **Caller A coverage complete**.

### Caller B region (arcade_pc 0x03B080..0x03B098)
- Existing export verified: `docs/design/ghidra_exports/03B092_reset_gate_bsr_site_b.txt`
- Includes:
  - `arcade_pc 0x03B08C`: `cmpi.w #0x100,(0x12,A5)`
  - `arcade_pc 0x03B092`: `bsr.w 0x39FA8`
- Result: **Caller B coverage complete**.

### Supplementary exports
- New supplementary export files created: **NONE**.

## Phase 2 — Runtime Trace Setup (MAME Native Debugger)

- Emulator: `mame` (reported as `0.276 (unknown)`)
- Native debugger: **YES** (`-debug -debugger qt`)
- Lua harness used: **NO**
- Trace method: native debugger `trace` + `tracelog`, plus native breakpoints and native write watchpoints.

### Breakpoints configured
- `CP_GATE`: `runtime_genesis_pc 0x0003A1A8` (`arcade_pc 0x039FA8`)
- `CP_CALLER_A`: `runtime_genesis_pc 0x0003AD8A` (`arcade_pc 0x03AB8A`)
- `CP_CALLER_B`: `runtime_genesis_pc 0x0003B292` (`arcade_pc 0x03B092`)
- `CP_RESTART_HANDOFF`: `runtime_genesis_pc 0x0003A19E` (`arcade_pc 0x039F9E`)
- `CP_BOOTSTRAP_REENTRY` requested at `runtime_genesis_pc 0x00000284` (configured exactly as requested)

### Write-watch configuration
- Watchpoint on `HW_ADDRESS 0x00FF0012` (word write): **configured and active**
- Watchpoint on `HW_ADDRESS 0x00FF002C` (word write): **configured and active**

Artifacts:
- Debugger script: `/tmp/build0051_warm_gate_trace.cmd`
- Debugger log: `/tmp/build0051_warm_gate.debug.log`
- Instruction trace: `/tmp/build0051_warm_gate.trace`

## Phase 3 — First Gate Entry Capture

### First gate entry hit
- Breakpoint target: `runtime_genesis_pc 0x0003A1A8` (`arcade_pc 0x039FA8`)
- Debugger event line captured:
  - `EVENT CP_GATE pc=03A1AA sr=2709 sp=00FEFFEE a5=00FF0000 usp=00000000 m12w=0000 m2cw=0000 m12d=00000000 m2cd=00000000`
- Observed debugger `PC=0x0003A1AA` at break event is consistent with 68000 prefetch representation while breaking on instruction at `0x0003A1A8`.

### Captured state at first gate entry
- `runtime_genesis_pc` target: `0x0003A1A8`
- `arcade_pc`: `0x039FA8`
- `SR`: `0x2709`
  - Carry flag (bit0): **1**
  - Zero flag (bit2): **0**
  - Interrupt mask (bits 8..10): **7**
- `A5`: `0x00FF0000`
  - A5 sanity check (`0x00FF0000` expected): **YES**
- `(A5+0x12)` = `HW_ADDRESS 0x00FF0012`:
  - word: `0x0000`
  - longword at address: `0x00000000`
- `(A5+0x2C)` = `HW_ADDRESS 0x00FF002C`:
  - word: `0x0000`
  - longword at address: `0x00000000`

### Full register file
- `D0=00000000 D1=60000003 D2=00000003 D3=00000000 D4=00000000 D5=00000000 D6=00000000 D7=0000FFFF`
- `A0=00FF601A A1=00000000 A2=00000000 A3=00000000 A4=00000000 A5=00FF0000 A6=00000000 A7(SP)=00FEFFEE`
- `USP=00000000`

### Stack top at gate entry (SSP..SSP+0xC)
- `d@SP     = 0x0003AD8E`
- `d@(SP+4) = 0x0003A242`
- `d@(SP+8) = 0x20000000`
- `d@(SP+C) = 0x00000000`

### Caller identification
- Event order in debugger log before first gate hit:
  1. `EVENT CP_CALLER_A pc=03AD8C ...`
  2. `EVENT CP_GATE pc=03A1AA ...`
- `CP_CALLER_B` did not hit before first gate entry.
- Caller determination: **Caller A** (`arcade_pc 0x03AB8A`) immediately preceded first gate entry.

### Compare-site confirmation (caller A)
Trace window around first gate call:
- `03AD84: cmpi.w #$100, ($12,A5)`
- `03AD8A: bsr $3a1a8`
- `03A1A8: bcs $3a1ac`

State evidence from trace around compare:
- Before compare (`PRE` line before `03AD84`): `SR=0x2704`
- After compare / at BSR prefetch state: `SR=0x2709`
- `(A5+0x12)` at compare: `0x0000`
- Carry set by compare: **1**

## Phase 4 — Writes to (A5+0x12) and (A5+0x2C) Before First Gate Entry

Trace interval: cold boot start -> first `arcade_pc 0x039FA8` entry.

### Watchpoint results
- `HW_ADDRESS 0x00FF0012` write watch hits before first gate: **0**
- `HW_ADDRESS 0x00FF002C` write watch hits before first gate: **0**

### Trace-diff results
Using instruction trace (`m12w/m2cw` per instruction) up to first gate:
- Changes in `m12w`: **0**
- Changes in `m2cw`: **0**

### Conclusion for initialization window
- No initialization writes to `0x00FF0012` or `0x00FF002C` were observed before first gate entry.
- Value at gate entry is reset-state WRAM value in this run (`0x0000` for both words).

## Phase 5 — Observational Only: 0xD00778 Before First Gate

- Search window: cold boot start -> first `arcade_pc 0x039FA8` entry.
- `HW_ADDRESS 0x00D00778` write observed in this window: **NO**.

No further analysis or fix attempted (out of scope by prompt).

## Required Summary

- Gate decomp coverage confirmed: **YES**
- Caller A decomp coverage confirmed: **YES**
- Caller B decomp coverage confirmed: **YES**
- `CP_GATE` first hit captured: **YES**
- Carry flag at first gate entry: **1**
- `(A5+0x12)` at first gate entry: **0x0000**
- `(A5+0x2C)` at first gate entry: **0x0000**
- Caller identified: **A**
- Writes to `0x00FF0012` before first gate: **0**
- Writes to `0x00FF002C` before first gate: **0**
- `0xD00778` write before first gate: **NO**
- Lua used: **NO**
- STOP triggered: **NO**
