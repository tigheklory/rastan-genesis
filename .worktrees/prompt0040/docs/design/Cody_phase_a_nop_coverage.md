# Cody Phase A NOP Coverage Analysis

## Scope
- Task type: static cross-reference only (no runtime re-run, no implementation).
- Ledger source: `specs/rastan_direct_remap.json` (Build 0051 context).
- Trace source: `/tmp/genesis_boot_1s.trace` (existing first-second Genesis run).
- Original arcade instruction source: `build/maincpu.disasm.txt` with `build/regions/maincpu.bin` backing ROM.
- Address spaces used in this document:
  - `arcade_pc`: ledger and disassembly addresses.
  - `runtime_genesis_pc`: trace addresses; mapped as `arcade_pc = runtime_genesis_pc - 0x200` for ROM code.

## Phase 1 - Phase A Entry Classification
- Total ledger entries in `specs/rastan_direct_remap.json`: **73**
- Phase A entries analyzed: **17**
- NOP/suppression entries: **15**
- Helper-redirect entries: **0**
- Other entries (non-NOP address remaps): **2**
- Count check: 15 + 0 + 2 = 17

### Non-NOP Phase A Entries (Out of Scope for HIT/NOT_HIT Table)
| ledger_index | arcade_pc | replacement_bytes | note |
|---:|---|---|---|
| 42 | `0x03AEEA` | `41F900FF0000` | Redirect arcade work-RAM base A0 from 0x10C000 (unmapped on Genesis) to Genesis WRAM 0xFF0000; matches A5 remap at 0x3AF04. Downstream zero-propagate loop at 0x3AEF6..0x3AF02 inherits. |
| 43 | `0x03AEF0` | `43F900FF0002` | Redirect arcade work-RAM propagate-destination A1 from 0x10C002 to Genesis WRAM 0xFF0002; matches A5 and A0 remaps. Loop ends at 0xFF3FFE, no BSS clobber. |

## Phase 2 - Executed arcade_pc Set From First-Second Trace
- Trace file used: `/tmp/genesis_boot_1s.trace`
- Trace file exists: **YES**
- Total instructions mapped to ROM-window `arcade_pc` values: **1139710**
- Total unique executed `arcade_pc` values: **822**

## Phase 3 - NOP/Suppression Cross-Reference
| ledger_index | arcade_pc | arcade_original_instruction | replacement | executed? | hit_count | first_hit_cycle |
|---:|---|---|---|---|---:|---:|
| 38 | `0x03AEBC` | `movew %d1,0x200000` | `4E714E714E71` | **HIT** | 4178 | 1332441 |
| 41 | `0x03AEE0` | `movew %d1,0x200000` | `4E714E714E71` | **HIT** | 2998 | 1509991 |
| 0 | `0x03A00C` | `clrw 0x350008` | `4E714E714E71` | **HIT** | 14 | 803975 |
| 1 | `0x03A012` | `movew %d0,0x3c0000` | `4E714E714E71` | **HIT** | 14 | 803987 |
| 32 | `0x03AE86` | `movew #0,0xc50000` | `4E714E714E714E71` | **HIT** | 1 | 1332329 |
| 33 | `0x03AE8E` | `movew #0,0xd01bfe` | `4E714E714E714E71` | **HIT** | 1 | 1332345 |
| 34 | `0x03AE96` | `clrw 0x350008` | `4E714E714E71` | **HIT** | 1 | 1332361 |
| 36 | `0x03AEA2` | `moveb #4,0x3e0001` | `4E714E714E714E71` | **HIT** | 1 | 1332385 |
| 37 | `0x03AEAA` | `moveb #1,0x3e0003` | `4E714E714E714E71` | **HIT** | 1 | 1332401 |
| 39 | `0x03AEC6` | `moveb #4,0x3e0001` | `4E714E714E714E71` | **HIT** | 1 | 1509935 |
| 40 | `0x03AECE` | `moveb #0,0x3e0003` | `4E714E714E714E71` | **HIT** | 1 | 1509951 |
| 45 | `0x03AF0A` | `movew %d0,0x3c0000` | `4E714E714E71` | **HIT** | 1 | 2250313 |
| 46 | `0x03AF14` | `movew %d0,0x3c0000` | `4E714E714E71` | **HIT** | 1 | 2346599 |
| 48 | `0x03AF4C` | `movew %d0,0x3c0000` | `4E714E714E71` | **NOT_HIT** | 0 | N/A |
| 49 | `0x03AF72` | `movew %d0,0x3c0000` | `4E714E714E71` | **NOT_HIT** | 0 | N/A |

## Phase 4 - Summary Statistics
- NOP entries HIT during first second: **13** of **15**
- NOP entries NOT_HIT during first second: **2** of **15**
- Total suppression executions during first second: **7213**
- `arcade_pc` with most executions: **0x03AEBC** (**4178** hits)
- NOP entries in startup region `arcade_pc 0x03A000..0x03AF04`: **11**
  - `0x03A00C`, `0x03A012`, `0x03AE86`, `0x03AE8E`, `0x03AE96`, `0x03AEA2`, `0x03AEAA`, `0x03AEBC`, `0x03AEC6`, `0x03AECE`, `0x03AEE0`
- NOP entries outside startup region: **4**

## Phase 5 - Integrity
- Ledger file read: **YES**
- Ledger entry count: expected 17 for Phase A subset, actual analyzed: **17**
- Trace file located: **YES** (`/tmp/genesis_boot_1s.trace`)
- Arcade ROM readable: **YES** (`build/regions/maincpu.bin`)
- `apps/rastan-direct/src/boot/boot.s` line 159 intact (`lea 0x00FF0000, %a5`): **YES**
- `apps/rastan-direct/src/scene_load.s` save-SR/restore-SR pattern intact and zero instances of `move.w #0x2700, %sr` / `move.w #0x2000, %sr`: **YES**
- No source/spec/tool modifications by this task: **YES**
