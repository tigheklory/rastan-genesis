# Cody — Seed vs Clear Ordering Trace (Build 0051)

Date: 2026-04-22
ROM under test: `dist/rastan-direct/rastan_direct_video_test_build_0051.bin`
Trace mode: MAME native internal debugger (`-debug -debugger qt`), no Lua

## Required Reading Confirmation
- `RULES.md`: read
- `ARCHITECTURE.md`: read
- `AGENTS_LOG.md` (latest entries): read
- `docs/design/Cody_a5_2c_seed_check.md`: read
- `docs/design/Andy_reset_path_root_cause.md`: read

## Phase 1 — Setup
- MAME version: `0.276`
- Native debugger: `YES`
- Lua used: `NO`
- Breakpoints installed: `2` (`YES`)

Configured breakpoints:
- `BP_SEED`: runtime_genesis_pc `0x0003ADD0` (arcade_pc `0x03ABD0`)
- `BP_CLEAR`: runtime_genesis_pc `0x0003B0FC` (arcade_pc `0x03AEFC`)

Capture artifacts:
- Debug log: `/tmp/build0051_seed_clear_ordering.debug.log`
- Instruction trace: `/tmp/build0051_seed_clear_ordering.trace`
- Debugger script: `/tmp/build0051_seed_clear_ordering.cmd`

## Phase 2 — First-Hit Capture

### Breakpoint: SEED (`BP_SEED`)
- Cycle at hit: `1261703`
- Target runtime_genesis_pc: `0x0003ADD0`
- Target arcade_pc: `0x03ABD0`
- Observed runtime_genesis_pc at event: `0x0003ADD2` (prefetch offset)
- A5: `0x00FF0000`

Stack capture (from breakpoint event):
- SP: `0x00FEFFF2`
- [SP+0x00]: `0x0003A242`
- [SP+0x04]: `0x20000000`
- [SP+0x08]: `0x02420000`
- [SP+0x0C]: `0x00000000`
- [SP+0x10]: `0x00000000`

Last 5 instruction PCs before first SEED hit (from trace):

| relative seq | cycle | observed runtime_genesis_pc | arcade_pc equivalent |
|---|---:|---:|---:|
| -5 | 1261651 | 0x0003BD6A | 0x03BB6A |
| -4 | 1261659 | 0x0003BD6C | 0x03BB6C |
| -3 | 1261669 | 0x0003BD62 | 0x03BB62 |
| -2 | 1261677 | 0x0003BD64 | 0x03BB64 |
| -1 | 1261687 | 0x0003BD7C | 0x03BB7C |

### Breakpoint: CLEAR (`BP_CLEAR`)
- Cycle at hit: `N/A (no breakpoint event in 2-second window)`
- Target runtime_genesis_pc: `0x0003B0FC`
- Target arcade_pc: `0x03AEFC`
- Observed runtime_genesis_pc at event: `N/A (breakpoint did not fire)`
- A5: `N/A (no breakpoint event)`

Stack capture:
- SP: `N/A (no breakpoint event)`
- [SP+0x00]: `N/A`
- [SP+0x04]: `N/A`
- [SP+0x08]: `N/A`
- [SP+0x0C]: `N/A`
- [SP+0x10]: `N/A`

Last 5 instruction PCs before first trace pass at target runtime_genesis_pc `0x0003B0FC` (fallback from trace):

| relative seq | cycle | observed runtime_genesis_pc | arcade_pc equivalent |
|---|---:|---:|---:|
| -5 | 1637909 | 0x0003B0E8 | 0x03AEE8 |
| -4 | 1637913 | 0x0003B0EA | 0x03AEEA |
| -3 | 1637921 | 0x0003B0EC | 0x03AEEC |
| -2 | 1637933 | 0x0003B0F2 | 0x03AEF2 |
| -1 | 1637945 | 0x0003B0F8 | 0x03AEF8 |

Trace line for first target pass:
- Cycle `1637957`: observed runtime_genesis_pc `0x0003B0FC` (arcade_pc `0x03AEFC`) in `/tmp/build0051_seed_clear_ordering.trace`

## Phase 3 — Ordering Observation
- First to fire by breakpoint event cycle: `SEED`
- `BP_SEED` first-hit cycle: `1261703`
- `BP_CLEAR` first-hit cycle: `N/A (not hit in window)`
- Cycle delta between first SEED and first CLEAR breakpoint hits: `N/A`

## Phase 4 — Integrity
- ROM SHA-256 (computed): `f9e1232fc98113a5f2aa106ff07727559d5d096dd7e73cff541c6219aa32ae52`
- No source/spec/tool modifications by this task: `YES`

## Raw Event Snippets
From debugger log:

```text
EVENT BP_SEED cyc=1261703 target_runtime=0003ADD0 target_arcade=03ABD0 obs_pc=03ADD2 sr=2704 sp=00FEFFF2 a5=00FF0000 s0=0003A242 s4=20000000 s8=02420000 sC=00000000 s10=00000000
```

No `EVENT BP_CLEAR ...` line was emitted in the 2-second run window.
