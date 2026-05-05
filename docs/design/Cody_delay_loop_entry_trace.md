# Cody — Delay-Loop Entry Trace (Build 0051)

Agent: Cody  
Type: Runtime Trace / Verification (trace-only)  
ROM under test: `dist/rastan-direct/rastan_direct_video_test_build_0051.bin`

Architecture compliance: CONFIRMED (no source/spec/tool modifications)

## Scope Result

STOP triggered: **YES**.

Reason: `BP_DELAY_LOOP` (`runtime_genesis_pc 0x0003A18C`, `arcade_pc 0x039F8C`) did not trigger within the required window; first delay-loop entry could not be captured in this run.

Partial capture below is complete and exact up to stop time.

## Phase 1 — Trace Setup

- Emulator: MAME `0.276 (unknown)`
- Debugger mode: native internal debugger (`-debug -debugger qt`, `QT_QPA_PLATFORM=offscreen`)
- Lua used: **NO**
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0051.bin`
- Artifacts:
  - debugger log: `/tmp/build0051_delay_loop_final.debug.log`
  - instruction trace: `/tmp/build0051_delay_loop_final.trace`
  - run stderr/stdout: `/tmp/build0051_delay_loop_final.run.out`

Configured breakpoints (targets in `runtime_genesis_pc`):
- `BP_DELAY_LOOP` 0x0003A18C (`arcade_pc 0x039F8C`)
- `BP_GATE_ENTRY` 0x0003A1A8 (`arcade_pc 0x039FA8`)
- `BP_GATE_BRA_DELAY` 0x0003A1AA (`arcade_pc 0x039FAA`)
- `BP_WATCHDOG_ENTRY` 0x0003A180 (`arcade_pc 0x039F80`)
- `BP_WATCHDOG_BEQ_DELAY` 0x0003A184 (`arcade_pc 0x039F84`)
- `BP_CALLER_A_BSR` 0x0003AD8A (`arcade_pc 0x03AB8A`)
- `BP_CALLER_A_COMPARE` 0x0003AD84 (`arcade_pc 0x03AB84`)
- `BP_CALLER_B_BSR` 0x0003B292 (`arcade_pc 0x03B092`)
- `BP_CALLER_B_COMPARE` 0x0003B28C (`arcade_pc 0x03B08C`)
- `BP_AB6E_DEAD` 0x0003AD6E (`arcade_pc 0x03AB6E`)
- `BP_BTST_HW` 0x0003AD96 (`arcade_pc 0x03AB96`)

Configured watchpoints:
- `WP_A5_12`: `HW_ADDRESS/chip/region 0x00FF0012` (word write)
- `WP_A5_2C`: `HW_ADDRESS/chip/region 0x00FF002C` (word write)

## Phase 2 — BP_DELAY_LOOP Capture

- `BP_DELAY_LOOP` first hit captured: **NO**
- `runtime_genesis_pc 0x0003A18C` breakpoint event: **none recorded**
- Stop window exceeded without delay-loop entry hit.

## Phase 3 — Captured Hit Chain Before STOP

### Breakpoint hit counts (event lines only)

| Breakpoint | target runtime_genesis_pc | target arcade_pc | hit count |
|---|---:|---:|---:|
| BP_DELAY_LOOP | 0x0003A18C | 0x039F8C | 0 |
| BP_GATE_ENTRY | 0x0003A1A8 | 0x039FA8 | 14 |
| BP_GATE_BRA_DELAY | 0x0003A1AA | 0x039FAA | 0 |
| BP_WATCHDOG_ENTRY | 0x0003A180 | 0x039F80 | 14 |
| BP_WATCHDOG_BEQ_DELAY | 0x0003A184 | 0x039F84 | 14 |
| BP_CALLER_A_BSR | 0x0003AD8A | 0x03AB8A | 14 |
| BP_CALLER_A_COMPARE | 0x0003AD84 | 0x03AB84 | 14 |
| BP_CALLER_B_BSR | 0x0003B292 | 0x03B092 | 0 |
| BP_CALLER_B_COMPARE | 0x0003B28C | 0x03B08C | 0 |
| BP_AB6E_DEAD | 0x0003AD6E | 0x03AB6E | 14 |
| BP_BTST_HW | 0x0003AD96 | 0x03AB96 | 2 |

Observed recurring chain prior to STOP:
1. `BP_CALLER_A_COMPARE` (`obs_pc 0x03AD86`, compare at `arcade_pc 0x03AB84`)
2. `BP_CALLER_A_BSR` (`obs_pc 0x03AD8C`, call at `arcade_pc 0x03AB8A`)
3. `BP_GATE_ENTRY` (`obs_pc 0x03A1AA`, gate at `arcade_pc 0x039FA8`)
4. `BP_AB6E_DEAD` (`obs_pc 0x03AD70`, branch site at `arcade_pc 0x03AB6E`)
5. `BP_WATCHDOG_ENTRY` (`obs_pc 0x03A182`, at `arcade_pc 0x039F80`)
6. `BP_WATCHDOG_BEQ_DELAY` (`obs_pc 0x03A186`, at `arcade_pc 0x039F84`)
7. `WP_A5_2C` write (`obs_pc 0x03A18C`) decrementing `(A5+0x2C)`

No hit recorded for gate tail branch breakpoint (`BP_GATE_BRA_DELAY`) and no Caller-B breakpoint hits.

## Phase 4 — Write History (boot -> STOP)

### Writes to `HW_ADDRESS/chip/region 0x00FF0012` (A5+0x12)

| Seq | writer runtime_genesis_pc (observed) | writer arcade_pc | value (word) |
|---:|---:|---:|---:|
| 1 | 0x0003B102 | 0x03AF02 | 0x0000 |

Count: **1**.

### Writes to `HW_ADDRESS/chip/region 0x00FF002C` (A5+0x2C)

| Seq | writer runtime_genesis_pc (observed) | writer arcade_pc | new value (word) |
|---:|---:|---:|---:|
| 1 | 0x0003ADD6 | 0x03ABD6 | 0x0000 |
| 2 | 0x0003A18C | 0x039F8C | 0x0010 |
| 3 | 0x0003A18C | 0x039F8C | 0x000F |
| 4 | 0x0003A18C | 0x039F8C | 0x000E |
| 5 | 0x0003A18C | 0x039F8C | 0x000D |
| 6 | 0x0003B102 | 0x03AF02 | 0x000C |
| 7 | 0x0003ADD6 | 0x03ABD6 | 0x0000 |
| 8 | 0x0003A18C | 0x039F8C | 0x0010 |
| 9 | 0x0003A18C | 0x039F8C | 0x000F |
| 10 | 0x0003A18C | 0x039F8C | 0x000E |
| 11 | 0x0003A18C | 0x039F8C | 0x000D |
| 12 | 0x0003A18C | 0x039F8C | 0x000C |
| 13 | 0x0003A18C | 0x039F8C | 0x000B |
| 14 | 0x0003A18C | 0x039F8C | 0x000A |
| 15 | 0x0003A18C | 0x039F8C | 0x0009 |
| 16 | 0x0003A18C | 0x039F8C | 0x0008 |
| 17 | 0x0003A18C | 0x039F8C | 0x0007 |

Count: **17**.

## Phase 5 — Observational Points

- `BP_AB6E_DEAD` hit count: **14** (so `arcade_pc 0x03AB6E` executed in this capture window)
- `BP_BTST_HW` hit count: **2**
- `HW_ADDRESS/chip/region 0x00390007` values observed at `BP_BTST_HW`: `0x8A`, `0x8A`

## Phase 6 — Integrity Snapshot

- ROM under test exists: `dist/rastan-direct/rastan_direct_video_test_build_0051.bin`
- ROM SHA-256: `f9e1232fc98113a5f2aa106ff07727559d5d096dd7e73cff541c6219aa32ae52`
- `apps/rastan-direct/src/boot/boot.s`: `lea 0x00FF0000, %a5` present at line 159 (intact)
- `apps/rastan-direct/src/scene_load.s`: save/raise/restore SR pattern present; no `move.w #0x2700, %sr` or `move.w #0x2000, %sr`
- `specs/rastan_direct_remap.json`: `direct_execution.entry_symbol = "_bootstrap"`, `entry_arcade_pc = "0x03A000"`, and opcode_replace entry at `arcade_pc 0x03AF04` present
- Source/spec/tool modifications by this task: **none**

## STOP Summary

- Required event missing: first `BP_DELAY_LOOP` hit
- STOP condition met: delay-loop entry not captured within required trace window
- Additional required capture to complete objective: continue runtime trace until first `BP_DELAY_LOOP` event (`runtime_genesis_pc 0x0003A18C`, with observed `pc` potentially prefetch-shifted), then capture full register+stack state and immediate pre-entry instruction window.
