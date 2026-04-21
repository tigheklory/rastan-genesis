# Cody — Coverage Invariant Update

Agent: Cody  
Type: Implementation (bookkeeping only)  
Build Context: current `rastan-direct`

## Objective

Update stale hardcoded ROM-size literal values in the Build 0029 invariant
check to match the post-Phase-B ROM size.

## Phase 1 — Two-line literal update

File: `tools/translation/postpatch_startup_rom.py`

Targeted lines before/after:

- Line 1742 before:
  `int(segment_coverage["total_genesis_bytes_covered"]) != 0xFC1C4`
- Line 1742 after:
  `int(segment_coverage["total_genesis_bytes_covered"]) != 0xFBF20`

- Line 1747 before:
  `"total_genesis_bytes_covered=0xFC1C4 and "`
- Line 1747 after:
  `"total_genesis_bytes_covered=0xFBF20 and "`

Constraints preserved:
- Build 0029 marker preserved
- `len(opcode_replace_sites) != 73` unchanged
- error string `opcode_replace patched_site count=73; got` unchanged

## Phase 2 — Build

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct -B release
```

Result: PASS

Confirmed:
- no coverage invariant error
- no `resolve_symbol_address` errors
- postpatch completed without `RuntimeError`
- ROM emitted:
  - `apps/rastan-direct/dist/rastan_direct_video_test.bin`
  - numbered artifact `dist/rastan-direct/rastan_direct_video_test_build_0049.bin`

## Phase 3 — Manifest verification

From `build/rastan-direct/rastan_direct_patch_manifest.json`:

- `direct_execution.entry_arcade_pc`: `0x03A000`
- `direct_execution.entry_symbol`: `_bootstrap`
- `direct_execution.entry_symbol_address`: `0x00000226`

## Phase 4 — Integrity checks

Phase B structure:
- vector 29 -> `_vblank_service`: YES (`boot.s` vector entry)
- `_bootstrap` tail handoff `jmp (0x00003A200).l`: YES
- `_vblank_service` tail handoff `jmp (0x00003A208).l`: YES
- `_vblank_service` contains `RTE`: NO
- `main_68k` absent from source/symbol scans: YES
- no Genesis-owned loop symbols (`main_68k`, `arcade_tick_logic`, `frame_counter`, `tick_counter`, `rastan_direct_arcade_tick_entry`) in current source/symbol scans: YES

Phase A remap ledger:
- all 17 required Phase A sites present in spec: YES
- all 17 required Phase A sites verified in built ROM (`replacement present` and `original absent` at `rom_pc`): YES

## STOP condition

STOP triggered: NO
