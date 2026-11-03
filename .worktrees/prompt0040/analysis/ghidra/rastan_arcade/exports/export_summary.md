# Rastan Arcade Ghidra Export Summary
- Source image: `analysis/ghidra/rastan_arcade/input/rastan_world_rev1_maincpu_68000.bin`
- Ghidra project: `analysis/ghidra/rastan_arcade/ghidra_project/rastan_arcade_world_rev1.gpr`
- Repro runner: `analysis/ghidra/rastan_arcade/run_headless_export.sh`
- Export directory: `analysis/ghidra/rastan_arcade/exports/`
- Linear disassembly: `linear_disassembly.tsv` covers every decoded line from `build/maincpu.disasm.txt` for `0x000000..0x05FFFF`.
- Hardware/scalar/reference rows: `453`
  - `PC080SN_tilemap`: `124`
  - `arcade_WRAM`: `101`
  - `PC090OJ_sprite_RAM`: `52`
  - `arcade_inputs`: `46`
  - `arcade_sound_comm`: `34`
  - `arcade_palette_RAM`: `34`
  - `arcade_watchdog`: `16`
  - `arcade_sprite_ctrl`: `14`
  - `PC080SN_yscroll`: `11`
  - `PC080SN_xscroll`: `11`
  - `PC080SN_ctrl`: `6`
  - `arcade_unknown_350008`: `4`

## Coverage

# Ghidra Coverage Report

- ROM bytes: `0x60000` (393216)
- Instruction count: `4094`
- Code bytes classified by Ghidra: `0x3974` (14708)
- Code coverage by byte: `3.74%`
- Function count: `181`
- Unresolved/data gap count: `139`
- Largest unresolved/data gap: `0x398C6` bytes
- Note: unresolved gaps include intentional data tables, graphics/text descriptors, jump tables, constants, and any code Ghidra did not discover statically.
