# Cody — Build 54 HV Counter Writer Runtime Trace

## Scope
Read-only runtime evidence collection for Build 0054 (`dist/rastan-direct/rastan_direct_video_test_build_0054.bin`) using MAME debugger watchpoints on:
- `0x00C00008`
- `0x00C0000A`
- `0x00C0000C`
- `0x00C0000E`

No source/spec/tool changes were made.

## Required Reading Status
- `RULES.md`: READ
- `ARCHITECTURE.md`: READ
- `AGENTS_LOG.md` (latest entries): READ
- `docs/design/Andy_build54_hvc_writer_root_cause.md` §1.7.2: READ
- `docs/design/Cody_build54_hvc_writer_search.md`: READ

## Rule 24 (MAME-first) Execution
### Driver availability
Command:
```bash
/usr/games/mame -listfull | rg "(^genesis\s|^megadriv\s|^megadrivj\s)"
```
Observed:
- `genesis` present
- `megadriv` present
- `megadrivj` not listed

### ROM path used
- `dist/rastan-direct/rastan_direct_video_test_build_0054.bin`

### Genesis watchpoint run (successful debugger command execution)
Command script used:
- `/tmp/build54_hvc_genesis_probe.cmd`

Script content (verbatim):
```text
printf "HVC_GENESIS_1777500779 START pc=%X cyc=%d\n",pc,totalcycles()
wp c00008,2,w,,{ printf "HVC_GENESIS_1777500779 WP_HVC08 cyc=%d pc=%X addr=%X pre=%X post=%X d0=%X d1=%X d2=%X d3=%X d4=%X d5=%X d6=%X d7=%X a0=%X a1=%X a2=%X a3=%X a4=%X a5=%X a6=%X sp=%X sr=%X\n",totalcycles(),pc,wpaddr,wpdata,w@wpaddr,d0,d1,d2,d3,d4,d5,d6,d7,a0,a1,a2,a3,a4,a5,a6,sp,sr ; quit }
wp c0000a,2,w,,{ printf "HVC_GENESIS_1777500779 WP_HVC0A cyc=%d pc=%X addr=%X pre=%X post=%X d0=%X d1=%X d2=%X d3=%X d4=%X d5=%X d6=%X d7=%X a0=%X a1=%X a2=%X a3=%X a4=%X a5=%X a6=%X sp=%X sr=%X\n",totalcycles(),pc,wpaddr,wpdata,w@wpaddr,d0,d1,d2,d3,d4,d5,d6,d7,a0,a1,a2,a3,a4,a5,a6,sp,sr ; quit }
wp c0000c,2,w,,{ printf "HVC_GENESIS_1777500779 WP_HVC0C cyc=%d pc=%X addr=%X pre=%X post=%X d0=%X d1=%X d2=%X d3=%X d4=%X d5=%X d6=%X d7=%X a0=%X a1=%X a2=%X a3=%X a4=%X a5=%X a6=%X sp=%X sr=%X\n",totalcycles(),pc,wpaddr,wpdata,w@wpaddr,d0,d1,d2,d3,d4,d5,d6,d7,a0,a1,a2,a3,a4,a5,a6,sp,sr ; quit }
wp c0000e,2,w,,{ printf "HVC_GENESIS_1777500779 WP_HVC0E cyc=%d pc=%X addr=%X pre=%X post=%X d0=%X d1=%X d2=%X d3=%X d4=%X d5=%X d6=%X d7=%X a0=%X a1=%X a2=%X a3=%X a4=%X a5=%X a6=%X sp=%X sr=%X\n",totalcycles(),pc,wpaddr,wpdata,w@wpaddr,d0,d1,d2,d3,d4,d5,d6,d7,a0,a1,a2,a3,a4,a5,a6,sp,sr ; quit }
gtime 2000
printf "HVC_GENESIS_1777500779 NO_WP_BEFORE_TIMEOUT pc=%X cyc=%d\n",pc,totalcycles()
quit
```

Observed debugger log lines (`/tmp/debug.log`):
```text
HVC_GENESIS_1777500779 START pc=204 cyc=34
HVC_GENESIS_1777500779 NO_WP_BEFORE_TIMEOUT pc=3A19E cyc=62836386
```

No `WP_HVC08/WP_HVC0A/WP_HVC0C/WP_HVC0E` hit line was produced before timeout.

### Megadriv watchpoint run (attempted)
Command script present and executed attempt:
- `/tmp/build54_hvc_megadriv_probe.cmd`
- stdout: `/tmp/build54_hvc_megadriv_probe.out`
- stderr: `/tmp/build54_hvc_megadriv_probe.err`

Result: run exited via debugger, but no watchpoint-hit evidence line was captured in debug console output files during this attempt.

## Phase 1 Evidence Items
### §1.1 Halt-instruction state
- NOT CAPTURED (watchpoint did not trigger before timeout).

### §1.2 Register state at halt
- NOT CAPTURED (watchpoint did not trigger before timeout).

### §1.3 Effective address computation
- NOT CAPTURED (watchpoint did not trigger before timeout).

### §1.4 Backward instruction trace
- NOT CAPTURED (watchpoint did not trigger before timeout).

### §1.5 Source-verified containing function for chain
- NOT CAPTURED (watchpoint did not trigger before timeout).

### §1.6 Frame timing context
- Available timing observation from timeout run:
  - start: `pc=0x00000204`, `cycles=34`
  - timeout: `pc=0x0003A19E`, `cycles=62836386`
  - watchpoint hit: none observed before timeout.

## Integrity
- Rule 24 MAME-first execution: YES
- MAME driver used for primary trace: `genesis`
- Write watchpoints set on `0xC00008/0x0A/0x0C/0x0E`: YES
- Watchpoint fired: NO
- Halt instruction captured (§1.1): NO
- Full register state captured (§1.2): NO
- Effective address computation captured (§1.3): NO
- Backward trace captured (§1.4): NO
- Source-verified chain mapping captured (§1.5): NO
- No analysis/diagnosis/hypotheses/recommendations: YES
- No source/spec/tool modifications: YES

## STOP Condition
STOP triggered: YES

Reason:
- Required runtime watchpoint did not fire before timeout in MAME Genesis-driver timed run (`gtime 2000`), so mandatory halt-state and address-computation-chain evidence could not be collected.
