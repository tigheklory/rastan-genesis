# Cody — direct_execution Spec Metadata Fix

Agent: Cody  
Type: Implementation (spec metadata correction only)  
Build Context: current `rastan-direct`

## Objective

Update `direct_execution.entry_symbol` and `direct_execution.entry_arcade_pc` in
`specs/rastan_direct_remap.json` to match Phase B decomposition metadata, then
rebuild and verify system integrity.

## Phase 1 — Spec field updates

File: `specs/rastan_direct_remap.json`  
Block: `direct_execution`

Applied in-place value changes only:

1. `entry_symbol`
   - Old: `"rastan_direct_arcade_tick_entry"`
   - New: `"_bootstrap"`
   - Confirmed in file: YES (line 15)

2. `entry_arcade_pc`
   - Old: `"0x03A008"`
   - New: `"0x03A000"`
   - Confirmed in file: YES (line 14)

Formatting/structure check:
- Existing `direct_execution` object preserved (same field order, indentation style).
- No new fields added.
- No JSON restructure performed.

## Phase 2 — Pre-build symbol check + build

Pre-build symbol check (`apps/rastan-direct/out/symbol.txt`):
- `_bootstrap` present: YES
- Address: `0x00000226`
- Symbol type: `t` (local text symbol)

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Build result: **FAIL (STOP)**

Postpatch failure:

```text
RuntimeError: Replacement references missing symbol: _bootstrap
```

Throw site:
- `tools/translation/postpatch_startup_rom.py:1689`
- call: `resolve_symbol_address(symbol_addresses, direct_entry_symbol)`

Interpretation:
- Spec metadata now points to `_bootstrap` as requested.
- Postpatch symbol resolver still cannot resolve `_bootstrap` from parsed symbol set.
- Build stopped before patched ROM emission.

## Phase 3 — Integrity snapshot at STOP

Static structure checks (source/symbol-level):
- vector 29 -> `_vblank_service`: YES (`boot.s` vector table line 87)
- `_bootstrap` ends with `jmp (0x00003A200).l`: YES (`boot.s` line 160)
- `_vblank_service` ends with `jmp (0x00003A208).l`: YES (`vdp_comm.s` line 179)
- `_vblank_service` contains `RTE`: NO
- `main_68k` absent from symbol/source scans: YES
- no Genesis-owned loop symbols (`main_68k`, `arcade_tick_logic`, `frame_counter`, `tick_counter`, `rastan_direct_arcade_tick_entry`) in current `apps/rastan-direct/src` + `out/symbol.txt`: YES
- Phase A 17 remap entries present in spec: YES (17/17)

Not verifiable due build stop:
- Phase A 17 entries in built ROM: NO (postpatch failed before final patched ROM output)

## STOP condition

STOP triggered: **YES**

Reason:
- Build failed with `resolve_symbol_address` missing-symbol error for `_bootstrap`.
- Prompt requires stopping on any build failure / symbol resolution error.
- No additional fixes applied in this pass.
