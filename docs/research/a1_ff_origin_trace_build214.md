# A1=0x000000FF Origin Trace (Build 214)

## Purpose
Trace the exact value chain that leads to `A1=0x000000FF` at the `ADDRESS_ERROR` reported at `PC=0x055E94` in Build 214, without implementing fixes.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest relevant entries)
- `README.md`
- `docs/research/flag_gate_analysis.md`
- `docs/research/original_init_responsibility_map.md`
- `docs/research/launcher_init_inventory.md`
- `docs/research/minimal_correct_launcher_init_design.md`
- `build/maincpu.disasm.txt` (arcade reference disassembly)
- `dist/Rastan_214.bin` (current Genesis ROM under investigation)
- Ghidra (arcade project `rastan_arcade:maincpu.bin` and Genesis Build 214 import `Rastan_214.bin`)
- `specs/startup_title_remap.json` (for known patch intent/context)

## Address Mapping Note
- Build 214 addresses are not globally `arcade+0x200` in this zone; local shift insertions are present.
- For the crash-local routine body, instruction signature matching shows:
  - `genesis 0x055E92` matches `arcade 0x055C7C` (`move.w (A1),(A0)+`)
  - `genesis 0x055E94` matches `arcade 0x055C7E` (`move.w D2,D7`)
- For the interrupt dispatcher marker:
  - `genesis 0x03A274` matches relocated interrupt epilogue call site derived from `arcade 0x03A074` pattern (`jsr ...; andi #$F0FF,SR; rte`)

## 1) Instruction At 0x055E94
- `genesis_addr: 0x055E94`
- instruction at `0x055E94`: `move.w D2,D7`
- immediately preceding instruction (`0x055E92`): `move.w (A1),(A0)+`
- faulting memory access behavior:
  - The word read via `(A1)` at `0x055E92` requires `A1` to be a valid even address.
  - With dump value `A1=0x000000FF` (odd, low/unmapped), that read faults.
- why exception reports `PC=0x055E94`:
  - On this exception frame path, PC reporting is consistent with fault at prior memory-access instruction (`0x055E92`) and next-in-sequence display at `0x055E94`.

## 2) Last Writes To A1 (Backward Trace)
### Proven local producer chain (intended path)
1. `genesis_addr: 0x055E78` (matches arcade `0x055C62` by opcode sequence)
   - instruction: `movea.l #0x0010D104, A1`
   - source kind: immediate constant
   - expected A1 after this: `0x0010D104` (valid/even)
2. `genesis_addr: 0x055E86`
   - instruction: `bsr.w 0x055E90`
   - enters loop that reads `(A1)` at `0x055E92`
3. `genesis_addr: 0x055E92`
   - instruction: `move.w (A1),(A0)+`

### Proven inconsistency at crash
- Crash dump has `A1=0x000000FF`, which is incompatible with the immediate setup at `0x055E78`.
- Therefore the faulting execution did **not** have valid setup state for this loop body when `(A1)` was dereferenced.

### Immediate bad source status
- Exact final instruction that wrote `A1=0x000000FF`: **UNKNOWN (not directly proven from static-only backward slice)**.
- Last **proven expected** writer in correct path remains `0x055E78` (`#0x0010D104`).

## 3) Does 0x03A27A Path Cause This?
### What 0x03A27A is in Build 214
- `genesis_addr: 0x03A274`: `jsr 0x055EA2`
- `genesis_addr: 0x03A27A`: `andi #$F0FF,SR`
- `genesis_addr: 0x03A27E`: `rte`
- This is the interrupt dispatcher epilogue marker (not the old `0x03A274` swap-helper meaning from earlier unshifted discussions).

### Causality determination
- `0x03A27A` in BT is a **context/return marker**, not the direct `(A1)` dereference site.
- The direct faulting dereference is in the `0x055E92` loop body.
- However, `0x03A274` is still causally relevant because it currently calls `0x055EA2` (see next section), which is the wrong entry point for the intended helper state dispatcher.

## 4) Source Classification Of Bad 0x00FF
- Classification: `OTHER` (stale/invalid address-register state at loop entry)
- What `0x00FF` is here:
  - A bad A1 register value at the time of word dereference, not a valid pointer.
- Why it became full A1:
  - Loop body executed without valid A1 setup contract (`A1` should be `0x0010D104` before first `(A1)` read).
- Why invalid at crash site:
  - `move.w (A1),...` on `A1=0x000000FF` is an odd/invalid word address.

## 5) Exact Root Cause Statement
ROOT CAUSE:
- `A1` becomes `0x000000FF` at the crash because execution reaches the copy-loop body (`0x055E92`) with setup contract broken, so `(A1)` dereference uses stale/invalid A1 instead of initialized `0x0010D104`.
- the immediate bad source is: loop-body entry with uninitialized/stale `A1` for that routine contract.
- that source is wrong because: the call target at `0x03A274` is mis-targeted to `0x055EA2` (mid-copy body in this build) rather than the relocated start of the intended dispatcher logic.

Primary classification: **BAD COPY PATH**
- Secondary effect: wrong call-target relocation/control-flow timing.

## 6) Minimal Fix Target (Design Only)
=== MINIMAL_FIX_TARGET ===
- fix_area: front-end interrupt-dispatch absolute call target relocation at `genesis 0x03A274` (arcade source call site `0x03A074`).
- exact_state_or_path_to_change: ensure this call resolves to the relocated start of the intended dispatcher routine (the block beginning with `cmpi.w #0,(0x4A,A5)` in Build 214, observed at `0x055EB8`), not into the loop body at `0x055EA2`.
- why_this_is_the_minimum_change: it repairs the producer-path contract for `A1` without changing startup policy, selector policy, or gameplay logic.
- what_must_NOT_be_changed: no manual selector seeding, no NOP/RTS bypasses, no wholesale startup_common restore, no shadow-RAM workaround.

## Uncertainties
- The exact final writer of literal `A1=0x000000FF` immediately before the fault is not directly proven from static slice alone.
- Exception-frame PC formatting for address-error display is implementation-specific; evidence indicates faulting memory access is at `0x055E92` regardless.

## Conclusion
The crash is a control-flow entry-target error into a copy kernel: `0x03A274` calls `0x055EA2`, which executes/loops through `0x055E92` without guaranteed A1 setup. The resulting stale `A1` (`0x000000FF`) causes the word dereference fault.
