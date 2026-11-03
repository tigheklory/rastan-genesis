# [Cody — PC090OJ v3.2 Postpatch Byte Baseline Correction]

Status: **STOP TRIGGERED** (boot verification did not meet required proof gates after build-unblock success).

## Scope for this task

Narrow build-maintenance scope applied:
- `tools/translation/postpatch_startup_rom.py` only:
  - `total_genesis_bytes_covered` expected baseline updated from `0x17C914` to `0x17C96C`
  - `opcode_replace patched_site count` kept at `90`
  - hard RuntimeError invariant gate preserved
  - explanatory comment extended with `0x58` dispatch-delta rationale

No edits were made in this task to:
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `specs/rastan_direct_remap.json`
- `docs/design/Andy_pc090oj_implementation_spec.md`
- `required_symbols`

## Build verification

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -j1
```

Result:
- **PASS**
- Postpatch invariant accepted:
  - count = `90`
  - bytes = `0x17C96C`
- Output artifacts produced:
  - `apps/rastan-direct/dist/rastan_direct_video_test.bin`
  - `dist/rastan-direct/rastan_direct_video_test_build_0053.bin`
- Postpatch manifest/disassembly steps completed successfully.

## Boot verification attempt (required phase)

Boot verification was attempted with MAME-based runtime capture:

1. Build-generated trace run:
   - `states/traces/rastan_direct_video_test_build_0053_mame_30s_20260428_132338/`
2. Additional targeted Lua runtime probe:
   - `/tmp/build0053_bootcheck.lua`
   - `/tmp/build0053_bootcheck_trace.txt`

Observed probe output:
- `d00778_writes=0` across periodic checkpoints
- `trap_pc_0010_hits=0`
- no direct proof hit at `runtime_genesis_pc 0x00003ADAA`
- no trustworthy positive proof that `pc090oj_dma_test_fired_flag` remained clear from this probe path

Because the requested D00778 and VRAM self-test pass conditions were not conclusively proven from this run’s instrumentation, boot verification is **not validated**.

## STOP reason

Build-system maintenance succeeded, but required boot-proof gates remain unproven in this task run:
- D00778 pass: **NOT VERIFIED**
- VRAM roundtrip self-test pass: **NOT VERIFIED**

Per task stop policy, no further scope expansion (logic edits) was performed.
