# Crash Path Reconstruction (`0x0561D6/0x0561FE` -> bad A1)

## Purpose
Reconstruct the failing chain from frontend/runtime entry to invalid table index and bad pointer consumption, including the `d0--` underflow.

## Source Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md`
- `README.md`
- `build/maincpu.disasm.txt`
- `specs/startup_title_remap.json`
- `build/rastan/startup_common_rom_manifest.json`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_trampoline.s`
- `dist/Rastan_5.bin`
- Ghidra (arcade): `tools/ghidra/rastan_project/rastan_arcade:maincpu.bin`
- Ghidra (Genesis): `tools/ghidra/rastan_project/rastan_genesis:Rastan_5.bin`

## Address Mapping Note
Relevant mapped sites:
- `arcade_addr: 0x055DDC` -> `genesis_rom_addr: 0x055FF2`
- `arcade_addr: 0x0561D6` -> `genesis_rom_addr: 0x0563EC`
- `arcade_addr: 0x0561FE` -> `genesis_rom_addr: 0x056414`
- `arcade_addr: 0x0563A6` -> `genesis_rom_addr: 0x0565BC`
- selector gate routine: `0x04527E` -> `0x04549A`

## Findings (Step-by-Step Chain)

### 1) Runtime enters frontend state machine
- `genesistan_run_original_frontend_tick` jumps to `0x03A008` with `A5` pointing to `genesistan_arcade_workram_words`.

### 2) Launcher preconditions diverge selector gate
- `genesistan_init_workram_direct()` writes `A5+0x0104 = 1` before live frontend tick.

### 3) Selector seed call executes but seed is skipped
- frontend path reaches `0x03A736: jsr 0x04527E`.
- at `0x04528C`, `tst.b (0x0104,A5)` is non-zero; branch skips writes to `A5+0x0118` and `A5+0x0117`.
- selector remains unseeded (`0x00`) unless later modified.

### 4) Transition/state logic enters table-indexed path
- in `0x055DDC` state progression, states call:
  - `0x055F8C: bsr.w 0x0561D6`
  - `0x055FCE: bsr.w 0x0561FE`

### 5) Underflow happens at the exact `d0--` site
At both `0x0561D6` and `0x0561FE`:
1. `clr.w D0`
2. `move.b 0x10C118, D0`
3. `subq.w #1, D0`  <- underflow when selector is `0`
4. `lsl.w #3, D0`

If selector is `0`:
- after `subq`: `D0 = 0xFFFF`
- after `lsl #3`: `D0 = 0xFFF8`

### 6) Table lookup uses negative offset
- `0x0561E2` loads base `A1 = 0x0562CA` (or `0x0562FA` in second routine)
- `lea (A1,D0.w),A1` with `D0=0xFFF8` indexes 8 bytes before intended table base
- `movea.l (A1),A0` and `movea.l 4(A1),A1` load pointer pair from invalid table slot

### 7) Bad pointer consumed by copy writer
- both routines call `0x0563A6`
- `0x0563A6` runs pointer-driven writes (`move.w D1,(A1)+`, converted glyph writes, control markers)
- invalid/odd/low pointer values from bad table slot yield Address Error family, including externally observed `A1=0x0000FF` case.

## Explicit `A1=0x0000FF` Interpretation
- `A1=0x0000FF` is not produced by immediate load in `0x0561D6/0x0561FE`; it is consumed after bad table-based pointer extraction.
- The immediate cause is malformed pointer table index (`selector-1`, then `*8`) when selector stayed zero.

## Uncertainties
- The exact bad table contents read at `base-8` can vary by run/state, so the precise invalid pointer value may vary (`0x0000FF` in this external crash, earlier families had different malformed pointers).
- Additional corruption from other patched transition paths can amplify failure behavior, but this chain is sufficient to explain the reported crash family.

## Conclusion
- The crash chain is fully reconstructable from selector gate skip -> `d0--` underflow -> pre-table pointer load -> `0x0563A6` write consumer.
- The chain is execution-order dependent: seeding must occur before `0x0561D6/0x0561FE` become reachable.
