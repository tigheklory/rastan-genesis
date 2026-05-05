# Cody FU1 Arcade Runtime Verification: 0x510EA / 0x510F4

## Scope and Result

- Task target: **arcade Rastan on MAME arcade driver** (`mame rastan`), not `rastan-direct`.
- Method: native MAME debugger breakpoints/watchpoint only, no source/spec/tool edits.
- Result: **PARTIAL CAPTURE + STOP**.
- STOP reason: required gameplay coverage (coin/start and >=30s active gameplay with visible sprite-correlation pass) could not be completed in this headless environment.

## Phase 1 - Trace Setup (Arcade MAME)

- MAME version: `0.276`
- Driver: `rastan (Rastan (World Rev 1))`
- ROM source: `./roms/rastan.zip` via `-rompath ./roms`
- Native debugger used: YES
- Lua used: NO

Installed successfully:

- `BP_510EA`: `arcade_pc 0x0510EA`
- `BP_510F4`: `arcade_pc 0x0510F4`
- `WP_D00698`: write-watch on `HW_ADDRESS 0x00D00698` (`arcade PC090OJ active descriptor RAM region`)

Debugger script artifact:

- `/tmp/rastan_fu1_arcade_trace.cmd`

Log artifact:

- `/tmp/rastan_fu1_arcade_trace.debug.log`

Observation window actually captured:

- Cold boot + attract/demo runtime.
- Interactive gameplay requirement could not be satisfied (no reliable non-Lua input injection available in this shell environment).

## Phase 2 - Breakpoint Hit Capture

Target-site disassembly (arcade ROM):

- `[build/maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:102307)`
  - `510ea: 33fc 0002 00d0 0698   movew #2,0xd00698`
- `[build/maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:102310)`
  - `510f4: 33fc 0000 00d0 0698   movew #0,0xd00698`

Captured hit counts:

- `BP_510EA` total hits: **0**
- `BP_510F4` total hits: **0**

First/last hit cycles:

- `BP_510EA`: first `N/A`, last `N/A`
- `BP_510F4`: first `N/A`, last `N/A`

No breakpoint-hit register/stack payload exists because neither breakpoint fired.

## Phase 3 - Watchpoint Capture (All Writers to 0x00D00698)

Watchpoint hit total:

- `WP_D00698` total writes: **105**

Unique writer PCs observed:

| arcade_pc | hit count | values written (`new`) | first cycle | last cycle |
|---|---:|---|---:|---:|
| 0x03AD48 | 4 | 0000 | 1072154 | 72858157 |
| 0x03C9C6 | 101 | 0000,4046 | 360143121 | 373479879 |

Interpretation notes from captured log fields:

- Watchpoint log fields are reported exactly as MAME emitted (`old=`, `new=`).
- First four writes were from `arcade_pc 0x03AD48` and reported `old=0000 new=0000`.
- Remaining writes were from `arcade_pc 0x03C9C6`, mostly `old=4046 new=4046`, with first hit in that burst reported `old=4046 new=0000`.

Writer-site disassembly context:

- Loop near `0x03AD48`:
  - `[build/maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73893)`
  - `3ad44: movel %d0,%a0@+`
  - `3ad48: bnes 0x3ad44`
- Loop near `0x03C9C6`:
  - `[build/maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:76329)`
  - `3c9c2: movew %d0,%a1@+`
  - `3c9c6: extw %d1`

Full watchpoint event table (raw evidence):

| seq | cycle | writer arcade_pc | old | new | SR | SP | A0 | A1 | A5 |
|---:|---:|---|---|---|---|---|---|---|---|
| 1 | 1072154 | 0x03AD48 | 0x0000 | 0x0000 | 0x2700 | 0x0010DDF8 | 0x00D00698 | 0x00110000 | 0x0010C000 |
| 2 | 1668627 | 0x03AD48 | 0x0000 | 0x0000 | 0x2700 | 0x0010DDEE | 0x00D00698 | 0x00C09EA8 | 0x0010C000 |
| 3 | 29610029 | 0x03AD48 | 0x0000 | 0x0000 | 0x2700 | 0x0010DDEE | 0x00D00698 | 0x00C0986C | 0x0010C000 |
| 4 | 72858157 | 0x03AD48 | 0x0000 | 0x0000 | 0x2700 | 0x0010DDE8 | 0x00D00698 | 0x00C09EA8 | 0x0010C000 |
| 5 | 360143121 | 0x03C9C6 | 0x4046 | 0x0000 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 6 | 360276461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 7 | 360409781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 8 | 360543121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 9 | 360676461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 10 | 360809781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 11 | 360943121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 12 | 361076461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 13 | 361209781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 14 | 361343121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 15 | 361476451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 16 | 361609781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 17 | 361743121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 18 | 361876461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 19 | 362009781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 20 | 362143131 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 21 | 362276461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 22 | 362409781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 23 | 362543121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 24 | 362676461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 25 | 362809781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 26 | 362943121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 27 | 363076461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 28 | 363209781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 29 | 363343121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 30 | 363476451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 31 | 363609781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 32 | 363743121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 33 | 363876461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 34 | 364009791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 35 | 364143121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 36 | 364276461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 37 | 364409791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 38 | 364543121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 39 | 364676451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 40 | 364809791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 41 | 364943121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 42 | 365076461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 43 | 365209781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 44 | 365343121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 45 | 365476461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 46 | 365609801 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 47 | 365743121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 48 | 365876461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 49 | 366009781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 50 | 366143121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 51 | 366276461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 52 | 366409781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 53 | 366543131 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 54 | 366676451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 55 | 366809791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 56 | 366943121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 57 | 367076451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 58 | 367209781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 59 | 367343131 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 60 | 367476451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 61 | 367609781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 62 | 367743131 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 63 | 367876451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 64 | 368009781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 65 | 368143131 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 66 | 368276451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 67 | 368409791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 68 | 368543121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 69 | 368676461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 70 | 368809791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 71 | 368943131 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 72 | 369076461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 73 | 369209791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 74 | 369343121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 75 | 369476461 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 76 | 369609781 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 77 | 369743121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 78 | 369876451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 79 | 370009791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 80 | 370143121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 81 | 370276451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 82 | 370409801 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 83 | 370543121 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 84 | 370676451 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 85 | 370809791 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 86 | 370946549 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 87 | 371079879 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 88 | 371213209 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 89 | 371346539 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 90 | 371479879 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D5F0 | 0x00D00698 | 0x0010C000 |
| 91 | 371613209 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 92 | 371746549 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 93 | 371879869 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 94 | 372013209 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 95 | 372146539 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 96 | 372279869 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 97 | 372413209 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 98 | 372546539 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D611 | 0x00D00698 | 0x0010C000 |
| 99 | 372679879 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 100 | 372813199 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 101 | 372946549 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 102 | 373079879 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 103 | 373213199 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEA | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 104 | 373346539 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x0010C000 |
| 105 | 373479879 | 0x03C9C6 | 0x4046 | 0x4046 | 0x2700 | 0x0010DDEE | 0x0003D632 | 0x00D00698 | 0x |

## Phase 4 - Behavior Correlation (Visible Sprite Effects)

Status: **NOT COMPLETED (STOP CONDITION)**.

Reason:

- Prompt requires boot + attract + at least 30s active gameplay with visual before/after correlation for each relevant write.
- In this headless environment, reliable non-Lua coin/start input injection could not be established.
- Therefore visible-sprite change correlation is unproven in this run.

Captured only:

- Watchpoint writer/cycle/value evidence.
- No verified gameplay state with controlled input and visual frame-step evidence.

## Phase 5 - MAME Device Semantic Cross-Reference

Source references:

- Descriptor sizing and count:
  - `[pc090oj.cpp](/home/tighe/projects/rastan-genesis/docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:12)`
  - `[pc090oj.cpp](/home/tighe/projects/rastan-genesis/docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:13)`
- Byte-field map for 8-byte descriptor:
  - `[pc090oj.cpp](/home/tighe/projects/rastan-genesis/docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:17)` through line 27
- Runtime draw field decode (`data` = word0 attr/flip/palette):
  - `[pc090oj.cpp](/home/tighe/projects/rastan-genesis/docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:186)` through line 193

Address meaning check:

- `HW_ADDRESS 0x00D00698` is in active sprite descriptor window (`0x00D00000..0x00D007FF`).
- Byte offset within active area: `0x698`.
- Descriptor index: `0x698 / 8 = 0xD3` (decimal 211).
- In-descriptor byte offset: `0x698 % 8 = 0`.
- Therefore this is descriptor 211, byte 0 / word0 field region (attr/flip/palette word as used in MAME draw path).

## Phase 6 - Classification

Because Phase 4 could not be completed (no validated gameplay + visual correlation), final A/B/C classification is **deferred** for strict compliance.

Target sites:

- `arcade_pc 0x510EA`: **UNCAPTURED (STOP before full required window)**
- `arcade_pc 0x510F4`: **UNCAPTURED (STOP before full required window)**

Additional writers observed to `HW_ADDRESS 0x00D00698`:

- YES: `arcade_pc 0x03AD48` (4 hits), `arcade_pc 0x03C9C6` (101 hits)

## Phase 7 - Translation Implication (Supplement Spec Input)

Phase 3 observed additional writers beyond 0x510EA/0x510F4, so supplemental spec input is required for downstream port scoping.

Minimal supplement specification (no implementation):

1. Site: `arcade_pc 0x03AD48` (prefetch-adjacent loop writer around `0x03AD44`).
   - Write type seen at target address: looped store sequence reaching `HW_ADDRESS 0x00D00698`.
   - Affected descriptor: index 211 (`0x698` offset), descriptor word0 region.
   - Required behavior: any Genesis translation plan must preserve writes reaching descriptor-211 word0 through this path, not only direct-immediate sites.

2. Site: `arcade_pc 0x03C9C6` (prefetch-adjacent loop writer around `0x03C9C2`).
   - Write type seen at target address: repeated looped writes reaching `HW_ADDRESS 0x00D00698`.
   - Affected descriptor: index 211 (`0x698` offset), descriptor word0 region.
   - Required behavior: translation must preserve recurrent runtime updates to descriptor-211 word0 from this path.

3. Existing FU1 targets:
   - `arcade_pc 0x510EA` and `0x510F4` remain unresolved in this run due no hits in captured window.
   - Must be rechecked in a completed gameplay-capable arcade trace session.

## Phase 8 - Integrity

- MAME arcade driver accessed successfully: YES
- No source/spec/tool/ROM/MAME modifications: YES
- MAME native debugger used: YES
- Observation window complete per prompt requirement (boot + attract + >=30s gameplay): **NO**
- `BP_510EA` result captured: YES (hit count 0)
- `BP_510F4` result captured: YES (hit count 0)
- `WP_D00698` all-writers capture complete: YES (105 writes)
- Classification produced for both target sites: **NO (deferred due STOP)**
- Additional writers enumerated: YES
- Phase 7 supplement produced: YES
- Required design document produced: YES

## STOP Statement

- STOP triggered: **YES**
- Reason: unable to satisfy mandatory gameplay-and-visual-correlation window in this environment (no reliable non-Lua input path for coin/start + controlled gameplay capture).
