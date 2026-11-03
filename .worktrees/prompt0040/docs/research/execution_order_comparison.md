# Arcade vs Genesis Execution Order Comparison (`A5+0x0104` / selector seeding)

## Purpose
Compare intended arcade order vs current launcher order and identify the first divergence that causes selector seed skip.

## Source Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md`
- `README.md`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_trampoline.s`
- `build/maincpu.disasm.txt`
- `specs/startup_title_remap.json`
- `build/rastan/startup_common_rom_manifest.json`
- `build/rastan/startup_common_relocations.json`
- `dist/Rastan_5.bin`
- Ghidra (arcade): `tools/ghidra/rastan_project/rastan_arcade:maincpu.bin`
- Ghidra (Genesis): `tools/ghidra/rastan_project/rastan_genesis:Rastan_5.bin`
- MAME reference source: `src/mame/taito/rastan.cpp`, `src/mame/taito/taitoipt.h`

## Address Mapping Note
- Arcade frontend entry: `arcade_addr: 0x03A008` -> `genesis_rom_addr: 0x03A208` before shift, callable in Build 5 through relocated slice.
- Seed routine: `0x04527E -> 0x04549A`.
- Crash-index routines: `0x0561D6 -> 0x0563EC`, `0x0561FE -> 0x056414`.

## Findings

## Timeline A: Intended Arcade Order
1. `0x03A000 -> 0x03AE86` startup/common init path runs.
2. WRAM clear/config setup is applied with A5 as canonical workram base (`0x03AF04`).
3. Frontend flow progresses through `0x03A008` state machine.
4. Selector seed routine is reached at `0x03A736 -> jsr 0x04527E` while gate condition still allows seed (`A5+0x0104 == 0`).
5. `A5+0x0118` and `A5+0x0117` get valid domain value (`1..8` source formula, default seen as `1`).
6. Later routines `0x0561D6/0x0561FE` consume selector safely (`d0--` no underflow into invalid table index).

## Timeline B: Current Genesis/Launcher Order (Build 5)
1. `request_start_rastan()` calls `genesistan_init_workram_direct()` directly (startup_common not replayed as full arcade sequence).
2. `genesistan_init_workram_direct()` writes `A5+0x0104 = 1` early (`startup_bridge.c`, direct seed).
3. Frontend runs via `genesistan_run_original_frontend_tick -> 0x03A008`.
4. `0x03A736 -> jsr 0x04527E` executes, but `tst.b (0x0104,A5)` is non-zero.
5. Selector writes to `A5+0x0118/0x0117` are skipped.
6. `0x055DDC` progression reaches `0x0561D6/0x0561FE`; `d0--` underflows from selector `0`.
7. Invalid table slot is used; bogus pointer pair reaches `0x0563A6`; Address Error follows.

## First Divergence Point
- First proven divergence: launcher-side write to `A5+0x0104` in `genesistan_init_workram_direct()` before selector seed call at `0x04527E`.

## What Happened Too Early
- `A5+0x0104 = 1` was asserted before the selector seed gate was intended to run open.

## What Was Skipped Because of That
- Selector writes:
  - `move.b D1,(0x0118,A5)` at `arcade_addr: 0x045292`
  - `move.b D1,(0x0117,A5)` at `arcade_addr: 0x045296`

## What Later Code Wrongly Assumed
- `0x0561D6` / `0x0561FE` assume selector domain is valid before executing `subq #1` and table indexing.

## Additional Relevant Patch-State Observation
- `specs/startup_title_remap.json` still contains opcode replacements:
  - `0x03A294 -> RTS+NOP`
  - `0x03A2B2 -> RTS+NOP`
- These are independent transition-cluster modifications and can affect broader flow integrity, but they are not required to prove the `A5+0x0104` gate skip causality chain.

## Uncertainties
- Exact cycle/tick at which selector seed would have first occurred under all runtime branches is state dependent.
- Some transition behaviors are additionally altered by existing opcode replacements, which may influence secondary symptoms.

## Conclusion
### Root Cause Judgment
- `PROVEN: early write to A5+0x0104 is the direct cause of skipped selector seeding`

Why:
- write site identified (`startup_bridge.c`),
- gate instruction identified (`0x04528C`),
- skipped seed writes identified (`0x045292`, `0x045296`),
- downstream underflow/index failure identified (`0x0561D6/0x0561FE`),
- consumer failure path identified (`0x0563A6`),
- chain verified in both arcade and Build 5 Genesis address spaces.
