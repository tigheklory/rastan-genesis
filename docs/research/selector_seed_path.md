# Selector Seed Path (`A5+0x0118` / `A5+0x0117`)

## Purpose
Map the exact selector-seeding path, including gate behavior on `A5+0x0104`, produced values, and call responsibility.

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
- MAME reference source: `src/mame/taito/rastan.cpp` and `src/mame/taito/taitoipt.h` (factory-default DIP context)

## Address Mapping Note
For this path:
- seed routine `arcade_addr: 0x04527E`
- `patched_maincpu_addr: 0x04529A` (shift delta `+28`)
- `genesis_rom_addr: 0x04549A`

Gate instruction:
- `arcade_addr: 0x04528C`
- `genesis_rom_addr: 0x0454A8`

Write targets:
- `arcade_addr: 0x045292` (`A5+0x0118`)
- `arcade_addr: 0x045296` (`A5+0x0117`)

## Findings

### Seed Routine
- arcade_addr: `0x04527E`
- genesis_rom_addr: `0x04549A`
- routine behavior:
  1. `move.w (0x0005FF9E).l, D1`
  2. `not.w D1`
  3. `andi.w #0x0007, D1`
  4. `addq.w #1, D1`
  5. `tst.b (0x0104,A5)`
  6. if zero: `move.b D1, (0x0118,A5)` and `move.b D1, (0x0117,A5)`
  7. `rts`

### Gate on `A5+0x0104`
- gate instruction: `tst.b (0x0104,A5)` at `0x04528C`
- branch: `bne 0x04529A`
- gate meaning:
  - `A5+0x0104 == 0`: seed selector bytes
  - `A5+0x0104 != 0`: skip selector seeding entirely

### Produced Values
- source constant in ROM: `0x05FF9E`
- Build 5 observed bytes at `0x05FF9E`: `0xFFFF`
- formula output under that value:
  - `(~0xFFFF & 0x0007) + 1 = 1`
- expected seed result when gate open:
  - `A5+0x0118 = 0x01`
  - `A5+0x0117 = 0x01`

### Responsible Caller and Reach Timing
- callsite to seed routine:
  - `arcade_addr: 0x03A736`
  - instruction: `jsr 0x04527E`
- upstream call path (frontend):
  - `request_start_rastan()`
  - `genesistan_init_workram_direct()`
  - `current_screen = SCREEN_FRONTEND_LIVE`
  - `genesistan_run_original_frontend_tick()` (jumps to `0x03A008`)
  - state handler reaches `0x03A736` and calls `0x04527E`

### Current Launcher Path Impact
- launcher writes `A5+0x0104 = 1` before frontend tick (`startup_bridge.c`, direct seed)
- when `0x04527E` runs, gate sees non-zero and skips writing `0x0118/0x0117`
- result: selector remains at clear/default value unless modified elsewhere

## Uncertainties
- The exact number of ticks between `SCREEN_FRONTEND_LIVE` entry and first `0x03A736` execution is state-dependent and not statically fixed from disassembly alone.
- No alternate seed routine writing both `0x0118` and `0x0117` before `0x0561D6/0x0561FE` was proven in this pass.

## Conclusion
- The selector seed path is explicit and gated by `A5+0x0104`.
- Under Build 5 execution order, launcher-side early write to `A5+0x0104=1` causes the seed routine to skip.
- This leaves `A5+0x0118/0x0117` unseeded at the point where later table-index code expects seeded values.
