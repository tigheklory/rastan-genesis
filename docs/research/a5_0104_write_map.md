# A5+0x0104 Write Map

## Purpose
Map every discovered write to `A5+0x0104` (arcade work RAM selector gate byte), including launcher-side writes and ROM-side writes, with execution-order context.

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

## Address Mapping Note
This report uses three address spaces:
- `arcade_addr`: original arcade maincpu address (from arcade disassembly/Ghidra).
- `patched_maincpu_addr`: `arcade_addr + cumulative_shift_delta` from `specs/startup_title_remap.json` `shift_replacements` entries with `arcade_pc < arcade_addr`.
- `genesis_rom_addr`: `patched_maincpu_addr + 0x200` (relocation delta from `startup_common_rom_manifest.json`).

For Build 5, `genesis_rom_addr` bytes were validated from `dist/Rastan_5.bin`.

## Findings

### W1
- item_id: `W1_launcher_direct_init`
- arcade_addr: `N/A (C-side launcher seed, not arcade ROM instruction)`
- genesis_rom_addr: `N/A (compiled C code path)`
- function/routine: `genesistan_init_workram_direct()` (`apps/rastan/src/startup_bridge.c:304`)
- exact instruction: `genesistan_arcade_workram_words[130] = 1; /* A5@(260) */`
- value written: `0x01`
- conditional or unconditional: `Unconditional` within routine
- predecessor call chain: `request_start_rastan() -> genesistan_init_workram_direct()`
- phase classification: `early launcher/init`
- confidence: `High`

### W2
- item_id: `W2_frontend_state_write_03A1F2`
- arcade_addr: `0x03A1F2`
- patched_maincpu_addr: `0x03A1F2` (shift delta `+0`)
- genesis_rom_addr: `0x03A3F2`
- function/routine: frontend state handler block in `0x03A196` dispatch region
- exact instruction: `move.b #0x1,(0x104,A5)`
- value written: `0x01`
- conditional or unconditional: `Unconditional` in that handler
- predecessor call chain: `genesistan_run_original_frontend_tick -> 0x03A008 state machine -> 0x03A196 sub-dispatch -> handler containing 0x03A1F2`
- phase classification: `startup phase`
- confidence: `High`

### W3
- item_id: `W3_frontend_transition_write_03A7EC`
- arcade_addr: `0x03A7EC`
- patched_maincpu_addr: `0x03A7F4` (shift delta `+8`)
- genesis_rom_addr: `0x03A9F4`
- function/routine: transition handler near `0x03A772..0x03A8A8`
- exact instruction: `move.b #0x1,(0x104,A5)`
- value written: `0x01`
- conditional or unconditional: `Conditionally reached handler; write itself unconditional`
- predecessor call chain: `genesistan_run_original_frontend_tick -> 0x03A008 -> frontend sub-dispatch -> transition branch -> handler at 0x03A7EC`
- phase classification: `late init`
- confidence: `High`

### W4 (non-executable decode artifact)
- item_id: `W4_artifact_00001264`
- arcade_addr: `0x0001264`
- patched_maincpu_addr: `0x0001264`
- genesis_rom_addr: `0x0001464`
- function/routine: `UNKNOWN (disassembly stream in data-like region)`
- exact instruction: `oril #11337987,%a5@(260)`
- value written: immediate OR value in decoded stream
- conditional or unconditional: `Unknown`
- predecessor call chain: `Unknown (no proven executable call path)`
- phase classification: `unknown`
- confidence: `Low`

### W5 (non-executable decode artifact)
- item_id: `W5_artifact_00001790`
- arcade_addr: `0x0001790`
- patched_maincpu_addr: `0x0001790`
- genesis_rom_addr: `0x0001990`
- function/routine: `UNKNOWN (disassembly stream in data-like region)`
- exact instruction: `oril #34865493,%a5@(260)`
- value written: immediate OR value in decoded stream
- conditional or unconditional: `Unknown`
- predecessor call chain: `Unknown`
- phase classification: `unknown`
- confidence: `Low`

### W6 (non-executable decode artifact)
- item_id: `W6_artifact_00002F58`
- arcade_addr: `0x0002F58`
- patched_maincpu_addr: `0x0002F58`
- genesis_rom_addr: `0x0003158`
- function/routine: `UNKNOWN (disassembly stream in data-like region)`
- exact instruction: `oril #11337987,%a5@(260)`
- value written: immediate OR value in decoded stream
- conditional or unconditional: `Unknown`
- predecessor call chain: `Unknown`
- phase classification: `unknown`
- confidence: `Low`

### W7 (non-executable decode artifact)
- item_id: `W7_artifact_00003798`
- arcade_addr: `0x0003798`
- patched_maincpu_addr: `0x0003798`
- genesis_rom_addr: `0x0003998`
- function/routine: `UNKNOWN (disassembly stream in data-like region)`
- exact instruction: `oril #35914069,%a5@(260)`
- value written: immediate OR value in decoded stream
- conditional or unconditional: `Unknown`
- predecessor call chain: `Unknown`
- phase classification: `unknown`
- confidence: `Low`

## Uncertainties
- The artifact rows (`W4`..`W7`) are included because they decode as writes, but they sit in non-executable-looking table/data regions and have no proven call path.
- Sub-dispatch table decoding around `0x03A17C` and `0x03A1AC` is partially opaque in flat disassembly; handler reachability is inferred from surrounding executable flow and validated instructions.

## Conclusion
- The dominant early write that diverges startup order is `W1` (`startup_bridge.c`), which sets `A5+0x0104=1` before frontend state progression reaches selector seeding at `0x04527E`.
- Two arcade runtime writes (`W2`, `W3`) also set `A5+0x0104=1`, but they occur later in frontend progression.
- No startup_common write to `A5+0x0104` was found in executable startup_common range (`0x03AE86..0x03B05B`).
