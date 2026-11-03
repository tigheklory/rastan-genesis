# Cody — Phase A Count Guard Fix

Agent: Cody  
Type: Implementation (bookkeeping only)  
Build Context: current `rastan-direct`

## Scope

This change updates only stale opcode-replacement count guards so the already-added Phase A remap entries can build and verify.

No remap entry content was changed.

## Files changed

- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`

## Phase 1 — Count guard updates

### 1) remap spec metadata

- Field: `expectations.opcode_replace_count`
- Old value: `56`
- New value: `73`

### 2) postpatch invariant check

File: `tools/translation/postpatch_startup_rom.py`

Updated hard-coded invariant in Build 0029 check:
- `len(opcode_replace_sites) != 56` -> `len(opcode_replace_sites) != 73`
- Error message text:
  - `opcode_replace patched_site count=56; got ` -> `opcode_replace patched_site count=73; got `

## Phase 2 — Build

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: PASS

Build artifact:
- `dist/rastan-direct/rastan_direct_video_test_build_0047.bin`

Patched ROM used for byte checks:
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

## Phase 3 — Byte verification (replacement present / original absent)

Verification source:
- `build/rastan-direct/rastan_direct_patch_manifest.json` (`address_rewrites` entries, `kind=opcode_replace`)
- ROM bytes read directly from `apps/rastan-direct/dist/rastan_direct_video_test.bin` at each `rom_pc`.

P1 checks:
- `0x3AE86`: YES
- `0x3AE8E`: YES
- `0x3AE96`: YES
- `0x3AEA2`: YES
- `0x3AEAA`: YES
- `0x3AEBC`: YES
- `0x3AEC6`: YES
- `0x3AECE`: YES
- `0x3AEE0`: YES
- `0x3AEEA` (pointer fix): YES
- `0x3AEF0` (pointer fix): YES
- `0x3AF0A`: YES
- `0x3AF14`: YES
- `0x3AF4C`: YES
- `0x3AF72`: YES

P1 result: PASS

P2 checks:
- `0x3A00C`: YES
- `0x3A012`: YES

P2 result: PASS

## Notes

- Root cause confirmed: stale count guard (`56`) vs actual opcode replacements (`73`) after Phase A additions.
- This is metadata/invariant bookkeeping only; no behavioral opcode replacement content was modified.
