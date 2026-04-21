# Cody — A5 Lifecycle Trace (_bootstrap -> First VBlank)

Agent: Cody  
Type: Runtime Trace / Verification (no source/spec/tool modifications)  
Build Context: Build 0050 `rastan-direct`  
ROM: `dist/rastan-direct/rastan_direct_video_test_build_0050.bin`

## Phase 1 — Checkpoint Resolution

Resolved from `apps/rastan-direct/out/symbol.txt` + ROM disassembly (`m68k-elf-objdump`).

| CP | Label | runtime_genesis_pc | arcade_pc | genesis_rom_offset | Instruction |
|---|---|---:|---:|---:|---|
| CP1 | `_bootstrap` entry | `0x00000226` | N/A | `0x00000226` | `jsr 0x70000` |
| CP2 | `jsr load_scene_tiles` | `0x00000232` | N/A | `0x00000232` | `jsr 0x711b0` |
| CP3 | `lea 0x00FF0000,%a5` | `0x00000238` | N/A | `0x00000238` | `lea 0xff0000,%a5` |
| CP4 | post-`lea` (`move.w #0x2000,%sr`) | `0x0000023E` | N/A | `0x0000023E` | `movew #8192,%sr` |
| CP5 | post-SR write (`jmp 0x3A200`) | `0x00000242` | N/A | `0x00000242` | `jmp 0x3a200` |
| CP6 | byte after JMP / handoff target | `0x0003A200` | `0x0003A000` | `0x0003A200` | `braw 0x3b086` |
| CP7 | first instruction at arcade handoff | `0x0003A200` | `0x0003A000` | `0x0003A200` | `braw 0x3b086` |
| CP8 | `_vblank_service` entry | `0x000700C2` | N/A | `0x000700C2` | `moveml %d0-%fp,%sp@-` |

## Phase 2 — Capture Setup

- MAME native debugger: **YES**
- Lua harness used: **NO**
- Emulator invocation: `mame genesis -cart dist/rastan-direct/rastan_direct_video_test_build_0050.bin -debug -debugger qt -debugscript /tmp/build0050_a5_lifecycle.cmd -debuglog -video none -sound none -nothrottle -skip_gameinfo -seconds_to_run 30` with `QT_QPA_PLATFORM=offscreen`
- Breakpoints installed: CP1..CP8: **YES**
- Register watchpoint on A5: **NO (not supported directly by MAME register watchpoint commands in this build)**
- Fallback used: **YES** — native `trace` + `tracelog` (register snapshot per instruction), deterministic post-process across CP1..CP8 window.

## Phase 3 — Tables

### Table A — Checkpoint capture

| CP | runtime_genesis_pc (target) | hit? | observed debugger PC | A5 at hit | SP at hit | SR at hit |
|---|---:|---|---:|---:|---:|---:|
| CP1 | `0x00000226` | YES | `0x00000228` | `0x00000000` | `0x00FEFFFC` | `0x2700` |
| CP2 | `0x00000232` | YES | `0x00000234` | `0x00000000` | `0x00FEFFFC` | `0x2714` |
| CP3 | `0x00000238` | NO | N/A | N/A | N/A | N/A |
| CP4 | `0x0000023E` | NO | N/A | N/A | N/A | N/A |
| CP5 | `0x00000242` | NO | N/A | N/A | N/A | N/A |
| CP6 | `0x0003A200` | NO | N/A | N/A | N/A | N/A |
| CP7 | `0x0003A200` | NO | N/A | N/A | N/A | N/A |
| CP8 | `0x000700C2` | YES | `0x000700C4` | `0x00000000` | `0x00FEFFC2` | `0x2600` |

Observed hit order from debugger log: **CP1 -> CP2 -> CP8**.

Trace evidence at IRQ entry point immediately before CP8:
- `runtime_genesis_pc 0x071246: move #$2000, SR`
- then interrupt: `(interrupted at 07124A, IRQ 6)`
- then `runtime_genesis_pc 0x0700C2: movem.l ...` (`_vblank_service`)

### Table B — A5 writes in CP1..CP8 window

Deterministic post-process (`awk`) over `/tmp/build0050_a5_lifecycle.trace` from first `PRE pc=000228` through first `PRE pc=0700C4`:
- Result: `TOTAL_CHANGES=0`

| Seq | runtime_genesis_pc of writer | arcade_pc | Instruction disasm | A5 before | A5 after |
|---|---:|---:|---|---:|---:|
| *(none)* |  |  |  |  |  |

## Phase 4 — Classification

A5 LIFECYCLE CLASSIFICATION: **CASE 1**

Supporting evidence:
- Table A: CP3 (`runtime_genesis_pc 0x00000238`, `lea 0x00FF0000,%a5`) was **not hit** before first CP8.
- Table A: CP8 hit with `A5=0x00000000`.
- Table B: zero A5-write events in CP1..CP8 window; no write producing `0x00FF0000`.
- IRQ sequence in trace confirms first VBlank arrived while execution was still inside `load_scene_tiles` path, before CP3/CP4/CP5/CP6/CP7.

## Phase 5 — Integrity

- ROM under test Build 0050: **YES**  
  Path: `dist/rastan-direct/rastan_direct_video_test_build_0050.bin`  
  SHA-256: `de90634339cff7b00ed7167899b8cf9399f579d923943cdc743d1d85cab47ee1`
- `boot.s` line 159 still `lea 0x00FF0000, %a5`: **YES**
- `vdp_comm.s` first `_vblank_service` instruction still `movem.l %d0-%d7/%a0-%a6, -(%sp)`: **YES**
- 17 Phase A entries in spec: **YES**
- opcode_replace at `arcade_pc 0x03AF04` in spec: **YES**
- 17 Phase A entries verified present in Build 0050 ROM (replacement present + original absent): **YES**
- No source/spec/tool modifications made by this task: **YES**

## STOP

STOP triggered: **YES**

Reason:
- Mandatory stop condition hit: checkpoint order violated (`CP8` reached before `CP6/CP7`, and before `CP3/CP4/CP5`).
- This is itself a runtime finding: first VBlank preempts `_bootstrap`/startup sequence before the `_bootstrap` A5 `lea` executes.

Architecture compliance: **CONFIRMED** (trace-only task; no source/spec/tool edits).
