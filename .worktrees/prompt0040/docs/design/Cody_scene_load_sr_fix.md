# Cody — load_scene_tiles SR Fix (Option C)

Agent: Cody  
Type: Implementation (targeted source edit + verification)  
Build context: Build 0050 -> Build 0051  
Architecture compliance: CONFIRMED

## 1) Source edit (exact Option C)

File edited:
- `apps/rastan-direct/src/scene_load.s`

### Edit 1 (manifest-ready entry)
Before:
```asm
    move.w  #0x2700, %sr
```
After:
```asm
    move.w  %sr, -(%sp)
    ori.w   #0x0700, %sr
```

### Edit 2 (function exit)
Before:
```asm
    move.w  #0x2000, %sr
```
After:
```asm
    move.w  (%sp)+, %sr
```

No other logic changes were made in `load_scene_tiles`.

## 2) Build result

Command:
```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: PASS

- postpatch completed without error: YES
- numbered ROM emitted: `dist/rastan-direct/rastan_direct_video_test_build_0051.bin`
- SHA-256: `f9e1232fc98113a5f2aa106ff07727559d5d096dd7e73cff541c6219aa32ae52`

## 3) Static integrity checks

- `_start` at runtime_genesis_pc `0x00000202` and SP setup (`lea 0x00ff0000,%sp`) present: YES
- `_bootstrap` ends with `jmp (0x00003A200).l`: YES
- `boot.s` still has `lea 0x00FF0000, %a5` at line 159 before `move.w #0x2000, %sr` at line 160: YES
- `_vblank_service` ends with `jmp (0x00003A208).l`: YES
- `_vblank_service` has no `RTE`: YES
- `load_scene_tiles` has consecutive save/raise pair after manifest selection: YES
- `load_scene_tiles` restores SR immediately before register restore: YES
- `load_scene_tiles` contains zero `move.w #0x2700,%sr`: YES
- `load_scene_tiles` contains zero `move.w #0x2000,%sr`: YES

Phase A remap ledger integrity:
- 17 Phase A entries present in spec: YES
- all 17 entries in Build 0051 ROM: replacement present + original absent: YES
- opcode_replace at arcade_pc `0x03AF04` present and applied in Build 0051 ROM: YES

## 4) Runtime verification (native MAME, no Lua)

Method:
- MAME internal debugger script (`/tmp/build0051_a5_lifecycle.cmd`)
- native `bp` checkpoints CP1..CP8
- native `trace/tracelog` to `/tmp/build0051_a5_lifecycle.trace`
- deterministic post-process to extract A5 writes between CP1 and first CP8
- Lua harness used: NO

Resolved checkpoint targets (Build 0051):
- CP1 `_bootstrap` entry: runtime_genesis_pc `0x00000226`
- CP2 `jsr load_scene_tiles`: runtime_genesis_pc `0x00000232`
- CP3 `lea 0x00FF0000,%a5`: runtime_genesis_pc `0x00000238`
- CP4 `move.w #0x2000,%sr`: runtime_genesis_pc `0x0000023E`
- CP5 `jmp (0x3A200).l`: runtime_genesis_pc `0x00000242`
- CP6/CP7 arcade handoff target: runtime_genesis_pc `0x0003A200` (arcade_pc `0x0003A000`)
- CP8 `_vblank_service` entry: runtime_genesis_pc `0x000700C2`

Address deltas vs Build 0050: none.

### Table A — Checkpoint capture

| CP | runtime_genesis_pc (target) | hit? | observed debugger PC | A5 at hit | SP at hit | SR at hit |
|---|---|---|---|---|---|---|
| CP1 | 0x00000226 | YES | 0x00000228 | 0x00000000 | 0x00FEFFFC | 0x2700 |
| CP2 | 0x00000232 | YES | 0x00000234 | 0x00000000 | 0x00FEFFFC | 0x2714 |
| CP3 | 0x00000238 | YES | 0x0000023A | 0x00000000 | 0x00FEFFFC | 0x2714 |
| CP4 | 0x0000023E | YES | 0x00000240 | 0x00FF0000 | 0x00FEFFFC | 0x2714 |
| CP5 | 0x00000242 | NO | N/A | N/A | N/A | N/A |
| CP6 | 0x0003A200 | NO | N/A | N/A | N/A | N/A |
| CP7 | 0x0003A200 | NO | N/A | N/A | N/A | N/A |
| CP8 | 0x000700C2 | YES | 0x000700C4 | 0x00FF0000 | 0x00FEFFF6 | 0x2600 |

### Table B — A5 writes from CP1 to first CP8 hit

| Seq | runtime_genesis_pc of writer | arcade_pc (if applicable) | Instruction disasm | A5 before | A5 after |
|---|---|---|---|---|---|
| 1 | 0x00000238 | N/A | `lea $ff0000.l, A5` | 0x00000000 | 0x00FF0000 |

Post-process result: exactly one A5 write in the CP1->first CP8 window.

Primary pass criterion:
- A5 on first `_vblank_service` entry = `0x00FF0000`: YES

Fix verification outcome:
- FIX VERIFIED: YES

## 5) Emulator behavior note

- Exodus executable availability in this environment: not found in PATH
- BlastEm executable availability in this environment: not found in PATH
- Because neither emulator binary is available here, a local 5-second interactive run in those emulators could not be executed in this task environment.

No remediation attempts were made for any additional runtime behavior in this pass.
