# Cody — _bootstrap A5 Initialization Fix

Agent: Cody  
Type: Implementation (one instruction, one file)  
Build context: Build 0049 `rastan-direct` prompt executed on current head (numbered output advanced to build 0050)

## Change applied

File changed:

- `apps/rastan-direct/src/boot/boot.s`

Exact insertion in `_bootstrap`:

```asm
    jsr     load_scene_tiles
    lea     0x00FF0000, %a5
    move.w  #0x2000, %sr
```

Insertion point verification:

- `jsr load_scene_tiles` found: YES
- `lea 0x00FF0000, %a5` inserted immediately after: YES
- before `move.w #0x2000, %sr`: YES

## Build result

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: PASS

- postpatch completed without error: YES
- symbol errors: NONE
- numbered ROM emitted: `dist/rastan-direct/rastan_direct_video_test_build_0050.bin`

## Integrity verification

### Boot/decomposition structure

- `_start` present and sets SP to `0xFF0000`: YES
- `_bootstrap` present and ends with `jmp (0x3A200).l`: YES
- inserted `lea 0x00FF0000, %a5` present before IRQ enable: YES
- `_vblank_service` ends with `jmp (0x3A208).l`: YES
- `_vblank_service` issues `RTE`: NO

### Remap ledger

Verified against `specs/rastan_direct_remap.json` + `build/rastan-direct/rastan_direct_patch_manifest.json` + built ROM bytes:

- 17 Phase A entries present in spec: YES
- all 17 Phase A sites in ROM show replacement present and original absent: YES
- opcode_replace at `arcade_pc 0x03AF04` present and intact in spec/manifest/ROM: YES

## Required runtime check outcome

Required check: "A5 non-zero on first entry to `_vblank_service`"

Captured with MAME debugger breakpoint at `runtime_genesis_pc 0x000700C2` (first hit):

```text
FIRST_VBLANK_SERVICE pc=0700C4 sp=00FEFFC2 a5=00000000 sr=2600
```

Result: **A5 non-zero on first `_vblank_service` entry = NO**.

## STOP status

STOP triggered: YES

Reason:

- Prompt stop condition hit: A5 could not be confirmed non-zero on first `_vblank_service` entry.
- This pass implemented the requested one-instruction insertion exactly and completed build/integrity checks, but the required runtime condition did not pass.

## Architecture compliance

CONFIRMED.

- No loop ownership changes
- No VBlank ownership changes
- No boot re-entry logic added
- No scaffolding/test-path code added
