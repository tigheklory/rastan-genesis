# Cody — Implementation: Genesis BSS Relocation

See `docs/design/Andy_genesis_bss_relocation_and_wram_map_design.md`, Task 6.

That document contains the complete implementation prompt, all code changes, and the
required AGENTS_LOG entry and report-back format. Follow Task 6 exactly.

Summary of changes:
1. `apps/rastan-direct/link.ld` line 21: `.bss 0xFF0000` → `.bss 0xFF4000`
2. `apps/rastan-direct/src/main_68k.s` arcade_tick_logic: add `lea 0x00FF0000, %a5`
3. `apps/rastan-direct/src/main_68k.s` init_staging_state line 700: `clr.l bg_row_dirty`
4. `apps/rastan-direct/src/main_68k.s` init_staging_state before final rts: arcade workram factory defaults
5. `docs/design/WRAM_memory_map.md`: create new

Reference for factory defaults: `apps/rastan/src/startup_bridge.c:246–396`
