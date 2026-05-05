# Cody — D00778 vs Delay Loop Ordering Trace (Build 0052)

Date: 2026-04-22
ROM under test: `dist/rastan-direct/rastan_direct_video_test_build_0052.bin`
Trace type: native MAME internal debugger (no Lua)

## Required Reading Confirmation
- `RULES.md`: read
- `ARCHITECTURE.md`: read
- `AGENTS_LOG.md` (latest entries): read
- `docs/design/Cody_boot_s_160_deletion_implementation.md`: read
- `docs/design/Andy_interrupt_enable_timing.md`: read
- `docs/design/Cody_seed_clear_ordering_trace.md`: read
- `docs/design/Cody_a5_2c_seed_check.md`: read
- `docs/design/Andy_3BB60_to_3ABD0_control_flow.md`: read

## Phase 1 — Trace Setup

ROM verification:
- Path: `dist/rastan-direct/rastan_direct_video_test_build_0052.bin`
- SHA-256 expected: `935afce5ba3a1ef68e96d3472531d8c00593f478974dd24adbf1e0d397dc6030`
- SHA-256 actual: `935afce5ba3a1ef68e96d3472531d8c00593f478974dd24adbf1e0d397dc6030`
- Match: YES

Debugger environment:
- MAME version: `0.276 (unknown)`
- Native debugger: YES (`-debug -debugger qt`)
- Lua used: NO
- Observation window: 5 seconds emulated time

Monitored events configured:
1. `WP_D00778`
   - Type: write-watchpoint
   - Address: `HW_ADDRESS 0x00D00778`
   - Address-space label: `HW_ADDRESS / Genesis VDP mirror region`
   - Width: 4 bytes
   - Installed: YES

2. `BP_DELAY_LOOP`
   - Type: PC breakpoint
   - Target runtime_genesis_pc: `0x0003A192`
   - Target arcade_pc: `0x039F92`
   - Target instruction: `move.l $0.w, D0` (equivalent to `MOVE.L (0x00).W, D0`)
   - Installed: YES

Artifacts:
- Debug log: `/tmp/build0052_d00778_vs_delay.debug.log`
- Instruction trace: `/tmp/build0052_d00778_vs_delay.trace`
- Debugger script: `/tmp/build0052_d00778_vs_delay.cmd`

## Phase 2 — First-Event Ordering

Monitored event hits:

| Event | Hit | Cycle | Event type | Address space label |
|---|---|---:|---|---|
| `WP_D00778` (`HW_ADDRESS 0x00D00778`) | YES | `1798914` | watchpoint | `HW_ADDRESS / Genesis VDP mirror region` |
| `BP_DELAY_LOOP` (`runtime_genesis_pc 0x0003A192` / `arcade_pc 0x039F92`) | YES | `5487753` | breakpoint | `runtime_genesis_pc` + `arcade_pc` |

First event classification:
- `D00778_FIRST`

## Phase 3 — Capture at First D00778 Write

First `WP_D00778` hit:
- Cycle: `1798914`
- Current runtime_genesis_pc (observed): `0x0003AFAE`
- Corresponding arcade_pc (observed-0x200): `0x03ADAE`
- Instruction at hit context (from trace): `0x03AFAA: move.l D0, (A0)` with `A0=0x00D00778`
- Event line uses prefetch-shifted observed PC (`0x03AFAE`)

Registers at first hit:
- `D0=00000008 D1=0000000E D2=00000000 D3=00000000 D4=00000000 D5=00000000 D6=00000000 D7=00000160`
- `A0=00D00778 A1=00FF4000 A2=00000000 A3=00050082 A4=00000000 A5=00FF0000 A6=00000000`
- `SP=00FEFFF4` (`SSP` not separately exposed in this capture; CPU in supervisor mode so stack pointer is supervisor stack)

Stack top (5 longwords):
- `[SP+0x00]=0003AFA2`
- `[SP+0x04]=0003B12C`
- `[SP+0x08]=00000226`
- `[SP+0x0C]=00000000`
- `[SP+0x10]=00000000`

Watchpoint memory snapshot:
- `wp_old=00000000`
- `memW@0x00D00778=0000`
- `memL@0x00D00778=00000000`

Last 5 instruction PCs preceding first D00778 hit:

| relative seq | cycle | observed runtime_genesis_pc | arcade_pc equivalent |
|---|---:|---:|---:|
| -5 | 1798836 | 0x0003AF8E | 0x03AD8E |
| -4 | 1798848 | 0x0003AF94 | 0x03AD94 |
| -3 | 1798860 | 0x0003AF9A | 0x03AD9A |
| -2 | 1798880 | 0x0005B714 | 0x05B514 |
| -1 | 1798896 | 0x0003AFA0 | 0x03ADA0 |

## Phase 4 — Capture at First Delay-Loop Entry

First `BP_DELAY_LOOP` hit:
- Cycle: `5487753`
- Current runtime_genesis_pc (observed): `0x0003A194`
- Corresponding arcade_pc (observed-0x200): `0x039F94`
- Breakpoint target address: runtime `0x0003A192` = arcade `0x039F92`
- Instruction at hit: `0x03A192: move.l $0.w, D0` (prefetch-shifted observed PC `0x03A194`)

Registers at first hit:
- `D0=00000B02 D1=000A0000 D2=00000003 D3=00000000 D4=00000000 D5=00000001 D6=00000010 D7=00000160`
- `A0=0003AD6E A1=0003BE4E A2=0010C13F A3=00050082 A4=00000000 A5=00FF0000 A6=00000000`
- `SP=00FEFFF2` (`SSP` not separately exposed in this capture; CPU in supervisor mode so stack pointer is supervisor stack)

Stack top (5 longwords):
- `[SP+0x00]=0003A274`
- `[SP+0x04]=20090003`
- `[SP+0x08]=B2920000`
- `[SP+0x0C]=00000000`
- `[SP+0x10]=00010001`

Requested memory words at first delay-loop hit:
- `HW_ADDRESS 0x00FF0012` (`A5+0x12`): `0x0000`
- `HW_ADDRESS 0x00FF002C` (`A5+0x2C`): `0x0000`

Last 5 instruction PCs preceding first delay-loop hit:

| relative seq | cycle | observed runtime_genesis_pc | arcade_pc equivalent |
|---|---:|---:|---:|
| -5 | 5487701 | 0x0003A26C | 0x03A06C |
| -4 | 5487709 | 0x0003AD70 | 0x03AB70 |
| -3 | 5487719 | 0x0003A182 | 0x039F82 |
| -2 | 5487731 | 0x0003A186 | 0x039F86 |
| -1 | 5487741 | 0x0003A18E | 0x039F8E |

## Phase 5 — Ordering Summary

- `HW_ADDRESS 0x00D00778` write occurred within 5 seconds: YES
- `arcade_pc 0x039F92` delay-loop entry occurred within 5 seconds: YES
- Which occurred first: `D00778`
- Cycle delta (delay-loop minus D00778): `5487753 - 1798914 = 3688839`
- Whether the other event also occurred later in same run: YES

Ordering classification:
- `D00778_FIRST`

## Phase 6 — Integrity

- Build 0052 verified (SHA-256 match): YES
- No source/spec/tool modifications: YES
- MAME native debugger used: YES
- WP_D00778 result captured: YES
- BP_DELAY_LOOP result captured: YES
- First-event ordering classified: YES
- Required design document produced: YES

## Raw First-Hit Event Lines

```text
EVENT WP_D00778_FIRST cyc=1798914 hw_address=00D00778 region=GENESIS_VDP_MIRROR obs_pc=03AFAE obs_arcade=03ADAE sr=2700 sp=00FEFFF4 a5=00FF0000 d0=00000008 d1=0000000E d2=00000000 d3=00000000 d4=00000000 d5=00000000 d6=00000000 d7=00000160 a0=00D00778 a1=00FF4000 a2=00000000 a3=00050082 a4=00000000 a5=00FF0000 a6=00000000 s0=0003AFA2 s4=0003B12C s8=00000226 sC=00000000 s10=00000000 wp_old=00000000 memW=0000 memL=00000000
EVENT BP_DELAY_LOOP_FIRST cyc=5487753 target_runtime=0003A192 target_arcade=039F92 obs_pc=03A194 sr=2700 sp=00FEFFF2 a5=00FF0000 d0=00000B02 d1=000A0000 d2=00000003 d3=00000000 d4=00000000 d5=00000001 d6=00000010 d7=00000160 a0=0003AD6E a1=0003BE4E a2=0010C13F a3=00050082 a4=00000000 a5=00FF0000 a6=00000000 s0=0003A274 s4=20090003 s8=B2920000 sC=00000000 s10=00010001 m0012=0000 m002c=0000
```
