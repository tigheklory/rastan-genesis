# A5+0x0104 Read/Test Map

## Purpose
Map every discovered read/test/compare gate on `A5+0x0104`, including branch outcomes and downstream effects.

## Source Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md`
- `README.md`
- `build/maincpu.disasm.txt`
- `specs/startup_title_remap.json`
- `build/rastan/startup_common_rom_manifest.json`
- `dist/Rastan_5.bin`
- Ghidra (arcade): `tools/ghidra/rastan_project/rastan_arcade:maincpu.bin`
- Ghidra (Genesis): `tools/ghidra/rastan_project/rastan_genesis:Rastan_5.bin`

## Address Mapping Note
Address handling is the same as `a5_0104_write_map.md`:
- `patched_maincpu_addr = arcade_addr + cumulative_shift_delta`
- `genesis_rom_addr = patched_maincpu_addr + 0x200`

Validated Build 5 mappings (for active gates):
- `0x03A624 -> 0x03A828`
- `0x03A714 -> 0x03A91C`
- `0x04528C -> 0x0454A8`
- `0x0452BA -> 0x0454D6`
- `0x0452CE -> 0x0454EA`

## Findings

### R1
- item_id: `R1_test_03A624`
- arcade_addr: `0x03A624`
- genesis_rom_addr: `0x03A828`
- exact instruction(s):
  - `tst.b (0x104,A5)`
  - `beq 0x03A63E`
- condition checked: `A5+0x0104 == 0 ?`
- zero path: skip special branch, continue to common setup and sprite/text progression
- non-zero path: set `A5@(0x1394)=0x00FF`, then derive/update `A5@(0x1242)` from `A5@(0x013E)-1`
- downstream consequence: modifies transition behavior and countdown/state values
- call chain: `genesistan_run_original_frontend_tick -> 0x03A008 -> state dispatch -> handler at 0x03A614`
- confidence: `High`

### R2
- item_id: `R2_test_03A714`
- arcade_addr: `0x03A714`
- genesis_rom_addr: `0x03A91C`
- exact instruction(s):
  - `tst.b (0x104,A5)`
  - `bne 0x03A730`
- condition checked: `A5+0x0104 != 0 ?`
- zero path: emits text id `0x37` and displays digit from `A5+0x0117` (`ori #0x30` path)
- non-zero path: skips the selector-digit display branch
- downstream consequence: hides/shows selector-related text path and state presentation
- call chain: `genesistan_run_original_frontend_tick -> 0x03A008 -> transition handler at 0x03A6E8`
- confidence: `High`

### R3
- item_id: `R3_gate_04528C`
- arcade_addr: `0x04528C`
- genesis_rom_addr: `0x0454A8`
- exact instruction(s):
  - `tst.b (0x104,A5)`
  - `bne 0x04529A`
- condition checked: seed gate for selector init
- zero path: executes writes at `0x045292` and `0x045296` (`A5+0x0118` and `A5+0x0117`)
- non-zero path: returns without seeding selector bytes
- downstream consequence: determines whether selector seed occurs before table-indexed routines (`0x0561D6/0x0561FE`)
- call chain: `genesistan_run_original_frontend_tick -> 0x03A736 jsr 0x04527E`
- confidence: `High`

### R4
- item_id: `R4_gate_0452BA`
- arcade_addr: `0x0452BA`
- genesis_rom_addr: `0x0454D6`
- exact instruction(s):
  - `tst.b (0x104,A5)`
  - `bne 0x0452C4`
- condition checked: gate for initial write to `A5@(0x1242)`
- zero path: writes computed `D0` to `A5@(0x1242)`
- non-zero path: skips write
- downstream consequence: alters later UI/transition numeric baseline
- call chain: `genesistan_run_original_frontend_tick -> 0x03A656 jsr 0x04529C`
- confidence: `High`

### R5
- item_id: `R5_gate_0452CE`
- arcade_addr: `0x0452CE`
- genesis_rom_addr: `0x0454EA`
- exact instruction(s):
  - `tst.b (0x104,A5)`
  - `bne 0x0452DA`
- condition checked: gate for `addiw #0x10, A5@(0x1242)` adjustment
- zero path: applies +16 adjustment to `A5@(0x1242)`
- non-zero path: skips adjustment
- downstream consequence: further diverges selector/transition-dependent numeric path
- call chain: `genesistan_run_original_frontend_tick -> 0x03A656 jsr 0x04529C`
- confidence: `High`

### R6 (non-executable decode artifact)
- item_id: `R6_artifact_000013D0`
- arcade_addr: `0x00013D0`
- genesis_rom_addr: `0x00015D0`
- exact instruction(s): `movepl %a5@(260),%d0`
- condition checked: none (read-like decode)
- zero path: `N/A`
- non-zero path: `N/A`
- downstream consequence: `Unknown`
- call chain: `Unknown (data-like decode stream)`
- confidence: `Low`

## Uncertainties
- `R6` appears in data-like regions and has no proven executable path.
- The frontend jump-table decode (`0x03A17C`, `0x03A1AC`) is partially opaque in flat disassembly text; call-chain framing for `R1/R2` is reconstructed from surrounding executable instructions and direct Ghidra probes.

## Conclusion
- There are five high-confidence, active `A5+0x0104` gates in gameplay/frontend code paths (`R1`..`R5`).
- The most critical gate is `R3` at `0x04528C`, which controls selector seeding into `A5+0x0118/0x0117`.
- With `A5+0x0104` already set non-zero by launcher init, `R3` takes the non-seed path, enabling the later selector underflow chain.
