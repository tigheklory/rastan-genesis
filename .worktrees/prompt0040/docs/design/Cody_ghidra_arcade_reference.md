# Cody Ghidra Arcade Reference

## 1. Import Setup
- Source binary: `build/regions/maincpu.bin`
- Binary size: `0x60000` bytes
- Ghidra project: `tools/ghidra/rastan_project/rastan_arcade_ref.gpr` (`.rep` alongside)
- Processor/language: `68000:BE:32:default:default`
- Image base: `0x00000000`
- Headless export method: Ghidra `analyzeHeadless` using custom Java script export passes (`/tmp/ExportArcadeReference*.java`) that emitted per-site plain-text reports into `docs/design/ghidra_exports/`

Address alignment verification (from `docs/design/ghidra_exports/00_alignment_verification.txt`):
- `arcade_pc 0x03A000`: `bra.w 0x0003ae86` (aligned)
- `arcade_pc 0x03A008`: `ori #0xf00,SR` (aligned)
- `arcade_pc 0x039F9E`: `movea.l (0x00000000).w,SP` (aligned)
- `arcade_pc 0x03AE86`: `move.w #0x0,(0x00c50000).l` (aligned)
- `arcade_pc 0x03AF04`: bytes match A5 init opcode sequence (`4B F9 00 10 C0 00`) (aligned)

Known addresses aligned correctly: YES.

## 2. Startup Flow
Entry point:
- `arcade_pc 0x03A000` (`startup_common`): `bra.w 0x03AE86`

Startup body region:
- `arcade_pc 0x03AE86` (`FUN_0003ae86`): clears key hardware/state locations and enters long initialization/probe loops
- Decompiler and disassembly both show repeated delay/probe loops and bulk memory propagation before broader game-state looping

A5 initialization site:
- First explicit A5 base load site in exported startup region is at `arcade_pc 0x03AF04`: `lea (0x10c000).l,A5`

Observed long-loop/probe style behavior in startup:
- Repeated `0x1fff` countdown loops around startup hardware setup
- Bulk propagation from `0x10c000` source region during initialization path

## 3. Interrupt / VBlank Flow
L5 handler entry:
- `arcade_pc 0x03A008` (`level5_vblank_handler`)
- Early instructions include:
  - `ori #0xf00,SR`
  - `clr.w (0x00350008).l`
  - `move.w D0w,(0x003c0000).l`

Key A5-relative assumptions inside handler:
- `arcade_pc 0x03A018`: `move.w (0x2,A5),D0w`
- `arcade_pc 0x03A02C`: `tst.w (0x0,A5)`
- `arcade_pc 0x03A032`: `cmpi.w #0x1,(0x1394,A5)`
- `arcade_pc 0x03A056`: `move.w (0x0,A5),D0w`

The decompiler warns on an indirect jump dispatch near `arcade_pc 0x03A06A`; handler flow uses a jump-table-like branch target derived from A5-relative state.

## 4. Reset / Warm-Restart Flow
Countdown gate and trampoline region:
- Function renamed `warm_restart_watchdog_gate` at `arcade_pc 0x039F80`
- Key path:
  - `arcade_pc 0x039F80`: `tst.w (0x2c,A5)`
  - `arcade_pc 0x039F84`: `beq.b 0x00039f8c`
  - `arcade_pc 0x039F86`: `subq.w #0x1,(0x2c,A5)`
  - `arcade_pc 0x039F9E`: `movea.l (0x00000000).w,SP`
  - `arcade_pc 0x039FA2`: `movea.l (0x00000004).w,A0`
  - `arcade_pc 0x039FA6`: `jmp (A0)`

Caller-chain evidence:
- `arcade_pc 0x03AB84` and `arcade_pc 0x03B092` both route through `bsr.w 0x00039fa8` in their respective control paths.

## 5. Key RAM/State Observations
A5 role summary:
- A5 is used as the core work RAM base pointer in startup/interrupt/reset paths.
- Numerous state checks and writes are performed at A5-relative offsets before indirect dispatch and reset-gate decisions.

Observed offsets (from exported disassembly):

| Offset | Observed instruction(s) | Suspected role | Confidence |
|---|---|---|---|
| `A5+0x00` | `tst.w (0x0,A5)` at `0x03A02C`; `move.w (0x0,A5),D0w` at `0x03A056`; `cmpi.w #0x3,(0x0,A5)` at `0x03AB8E` | primary state/mode selector used by L5 dispatch and reset gating | HIGH |
| `A5+0x02` | `move.w (0x2,A5),D0w` at `0x03A018`; `clr.w (0x2,A5)` at `0x03ABDC` | secondary state/substate counter used in L5 range checks | HIGH |
| `A5+0x12` | `cmpi.w #0x100,(0x12,A5)` at `0x03AB84`/`0x03B08C`; `cmpi.w #0x9,(0x12,A5)` near `0x03A0D0`/`0x03A0DE` | credit/input/watchdog threshold gate field (exact semantic varies by caller) | MEDIUM |
| `A5+0x2C` | `tst.w (0x2c,A5)` / `subq.w #0x1,(0x2c,A5)` at `0x039F80`/`0x039F86`; `move.w #0xa0,(0x2c,A5)` at `0x03AB22`; `move.w #0x10,(0x2c,A5)` at `0x03ABD0` | restart/watchdog countdown timer field | HIGH |
| `A5+0x14` | `move.w D0w,(0x14,A5)` at `0x03AF24` | initialized runtime value after A5 base setup | MEDIUM |
| `A5+0x34` | `tst.w (0x34,A5)` at `0x03A0EC` and near `0x03A126` | gate controlling coin/credit input queue updates | MEDIUM |

## 6. Practical Value to the Genesis Project (Reference Only)
This artifact provides a concrete arcade-code reference for:
- startup sequencing from `arcade_pc 0x03A000`
- VBlank/L5 assumptions at `arcade_pc 0x03A008`
- reset countdown and trampoline behavior around `arcade_pc 0x039F80..0x039FA6`
- A5-relative state usage and likely ownership of key control variables

This document is intentionally reference-only and does not prescribe implementation changes.

## Safe Rename Record (Applied in Ghidra Project)
From `docs/design/ghidra_exports/00_safe_rename_log.txt`:
- `thunk_FUN_0003ae86` -> `startup_common` at `arcade_pc 0x03A000`
- `FUN_0003a008` -> `level5_vblank_handler` at `arcade_pc 0x03A008`
- `FUN_00039f80` -> `warm_restart_watchdog_gate` at `arcade_pc 0x039F80`
- `FUN_0003ab7c` -> `warm_restart_gate_caller_a` at `arcade_pc 0x03AB7C`
- `FUN_0003b084` -> `warm_restart_gate_caller_b` at `arcade_pc 0x03B084`
