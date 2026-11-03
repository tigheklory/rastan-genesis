# Cody Build 0027 CLR.W NOP Patch Report

## Summary
Build 0027 suppresses four `CLR.W abs.l` writes to PC080SN scroll register addresses (`0xC20000` and `0xC40000`) by adding four 6-byte opcode replacements in `specs/rastan_direct_remap.json`. No source code files were modified.

## Preconditions verified
- `opcode_replace_count` before edits: `39`
- No existing patches at arcade PCs:
  - `0x03ABBA`
  - `0x03ABC0`
  - `0x03B098`
  - `0x03B09E`
- Pre-edit ROM bytes matched exactly:
  - `0x03ADBA` (`0x03ABBA + 0x200`): `42B900C20000`
  - `0x03ADC0` (`0x03ABC0 + 0x200`): `42B900C40000`
  - `0x03B298` (`0x03B098 + 0x200`): `42B900C20000`
  - `0x03B29E` (`0x03B09E + 0x200`): `42B900C40000`

## Four CLR.W writes identified (hardware identification)
- `0x03ABBA`: `CLR.W 0x00C20000` (PC080SN yscroll register write on arcade hardware)
- `0x03ABC0`: `CLR.W 0x00C40000` (PC080SN xscroll register write on arcade hardware)
- `0x03B098`: `CLR.W 0x00C20000` (PC080SN yscroll register write, title path)
- `0x03B09E`: `CLR.W 0x00C40000` (PC080SN xscroll register write, title path)

No PC080SN device exists on Genesis, so these scroll register accesses are invalid on target hardware.

## Four patches added (6-byte / 3-NOP format)
Added four `opcode_replace` entries with exact-size 6-byte replacements:
- `arcade_pc: 0x03ABBA`
  - `original_bytes: 42B900C20000`
  - `replacement_bytes: 4E714E714E71`
- `arcade_pc: 0x03ABC0`
  - `original_bytes: 42B900C40000`
  - `replacement_bytes: 4E714E714E71`
- `arcade_pc: 0x03B098`
  - `original_bytes: 42B900C20000`
  - `replacement_bytes: 4E714E714E71`
- `arcade_pc: 0x03B09E`
  - `original_bytes: 42B900C40000`
  - `replacement_bytes: 4E714E714E71`

## Patch count updated
- `opcode_replace_count`: `39 -> 43`

## Build result
- Command: `source tools/setup_env.sh && make -C apps/rastan-direct`
- Result: PASS
- Produced numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0027.bin`

## ROM verification (exact bytes at Genesis offsets)
- `0x03ADBA`: `4E714E714E71`
- `0x03ADC0`: `4E714E714E71`
- `0x03B298`: `4E714E714E71`
- `0x03B29E`: `4E714E714E71`

## MAME trace results
- Trace command:
  - `timeout 120s tools/mame/run_genesis_trace_wsl.sh apps/rastan-direct/dist/rastan_direct_video_test.bin -video none -sound none -nothrottle -seconds_to_run 30`
- Saved directory:
  - `states/traces/rastan_direct_video_test_build_0027_mame_30s_20260412_232548/`
- Saved files (both non-empty):
  - `states/traces/rastan_direct_video_test_build_0027_mame_30s_20260412_232548/genesis_exec_summary.txt`
  - `states/traces/rastan_direct_video_test_build_0027_mame_30s_20260412_232548/genesis_exec_trace.log`
- Reported values from summary:
  - `reg_c50000_live count=0`
  - `title_init_block@000200 count=0`

## Final outcome
Build 0027 applied exactly the four required 6-byte NOP patches for PC080SN scroll `CLR.W` writes, updated `opcode_replace_count` to `43`, built successfully, verified ROM bytes at all four target offsets, and saved a 30-second MAME trace under the required `states/traces/` naming convention.
