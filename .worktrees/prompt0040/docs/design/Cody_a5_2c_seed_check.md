# Cody — (A5+0x2C) Seed Site Execution Check (Build 0051)

Agent: Cody  
Type: Runtime Trace / Verification (surgical)  
ROM under test: `dist/rastan-direct/rastan_direct_video_test_build_0051.bin`

Architecture compliance: CONFIRMED (trace-only; no source/spec/tool modifications).

## Phase 1 — Setup
- MAME version: `0.276 (unknown)`
- Native debugger used: **YES** (`-debug -debugger qt`, no Lua)
- Lua used: **NO**
- Breakpoints installed (4): **YES**
  - `BP_SEED_A` runtime_genesis_pc `0x0003AD22` = arcade_pc `0x03AB22`
  - `BP_SEED_B` runtime_genesis_pc `0x0003AD5E` = arcade_pc `0x03AB5E`
  - `BP_SEED_C` runtime_genesis_pc `0x0003ADD0` = arcade_pc `0x03ABD0`
  - `BP_FIRST_RESTART` runtime_genesis_pc `0x0003A19E` = arcade_pc `0x039F9E`
- Write-watch on `HW_ADDRESS 0x00FF002C` (word): **YES**
- Window: cold boot through `-seconds_to_run 2` (first restart did not occur in-window).

## Phase 2 — Run to First Restart (or 2-second Window)
- `BP_FIRST_RESTART` hit: **NO** (within 2-second emulated window).

### Seed-site hit captures (with before/after 0x00FF002C)
| Breakpoint | Cycle | target runtime_genesis_pc | target arcade_pc | observed runtime_genesis_pc | observed arcade_pc | A5 | 0x00FF002C BEFORE | 0x00FF002C AFTER |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BP_SEED_A | N/A | 0x0003AD22 | 0x03AB22 | N/A | N/A | N/A | N/A | N/A |
| BP_SEED_B | N/A | 0x0003AD5E | 0x03AB5E | N/A | N/A | N/A | N/A | N/A |
| BP_SEED_C | 1261703 | 0x0003ADD0 | 0x03ABD0 | 0x0003ADD2 | 0x03ABD2 | 0x00FF0000 | 0x0000 | 0x0010 |
| BP_SEED_C | 2104403 | 0x0003ADD0 | 0x03ABD0 | 0x0003ADD2 | 0x03ABD2 | 0x00FF0000 | 0x0000 | 0x0010 |

## Phase 3 — Write History for HW_ADDRESS 0x00FF002C
| seq | cycle | writer runtime_genesis_pc (observed) | writer arcade_pc | instruction | old value | new value |
|---:|---:|---:|---:|---|---:|---:|
| 1 | 1261703 | 0x0003ADD6 | 0x03ABD6 | movew #16,%a5@(44) at arcade_pc 0x03ABD0 (prefetch-shifted observation) | 0x0000 | 0x0010 |
| 2 | 1262353 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x0010 | 0x000F |
| 3 | 1332137 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000F | 0x000E |
| 4 | 1391447 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000E | 0x000D |
| 5 | 1519437 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000D | 0x000C |
| 6 | 1638511 | 0x0003B102 | 0x03AF02 | startup zero-propagate loop store (movew %d0,%a1@+ at arcade_pc 0x03AEFC; observed at loop tail 0x03AF02) | 0x000C | 0x0000 |
| 7 | 2104403 | 0x0003ADD6 | 0x03ABD6 | movew #16,%a5@(44) at arcade_pc 0x03ABD0 (prefetch-shifted observation) | 0x0000 | 0x0010 |
| 8 | 2105053 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x0010 | 0x000F |
| 9 | 2174837 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000F | 0x000E |
| 10 | 2176857 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000E | 0x000D |
| 11 | 2287487 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000D | 0x000C |
| 12 | 2426709 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000C | 0x000B |
| 13 | 2561605 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000B | 0x000A |
| 14 | 2689887 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x000A | 0x0009 |
| 15 | 2818173 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x0009 | 0x0008 |
| 16 | 2946409 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x0008 | 0x0007 |
| 17 | 3096499 | 0x0003A18C | 0x039F8C | subqw #1,%a5@(44) at arcade_pc 0x039F86 (prefetch-shifted observation) | 0x0007 | 0x0006 |

- First nonzero write: cycle 1261703, writer observed arcade_pc 0x03ABD6, value 0x0010.
- First zero-after-nonzero write: cycle 1638511, writer observed arcade_pc 0x03AF02, 0x000C -> 0x0000.

## Phase 4 — Outcome Classification
- Outcome identified: **2**
- Supporting evidence:
  - `BP_SEED_A` hits: 0
  - `BP_SEED_B` hits: 0
  - `BP_SEED_C` hits: 2
  - `BP_FIRST_RESTART` hits: 0
  - Nonzero seed write observed (`0x0010`), then later write to zero before any restart (cycle 1638511).

## Integrity
- ROM under test: `dist/rastan-direct/rastan_direct_video_test_build_0051.bin`
- ROM SHA-256: `f9e1232fc98113a5f2aa106ff07727559d5d096dd7e73cff541c6219aa32ae52`
- Source/spec/tool modifications by this task: **none**
