# Cody — Build 0029 FG C-Window Live Write Trace Report

## Summary
Added a new live write watch (`fg_cwindow_live`) to the Genesis trace arming config and ran a fresh 30-second MAME trace against Build 0029.

## Trace Arming Config Change
File updated:
- `tools/mame/scripts/genesistrace.lua`

Added live write watch:
- `name`: `fg_cwindow_live`
- `start_addr`: `0xC08000`
- `end_addr`: `0xC0BFFF` (inclusive)

Captured fields (already emitted by the trace system for live writes):
- `pc`
- `addr`
- `data`
- `mask`

## Trace Command
```bash
timeout 120s tools/mame/run_genesis_trace_wsl.sh \
  dist/rastan-direct/rastan_direct_video_test_build_0029.bin \
  -video none -sound none -nothrottle -seconds_to_run 30
```

## Saved Trace Artifacts
- `states/traces/rastan_direct_video_test_build_0029_mame_30s_20260413_212116/genesis_exec_summary.txt`
- `states/traces/rastan_direct_video_test_build_0029_mame_30s_20260413_212116/genesis_exec_trace.log`

## fg_cwindow_live Results
Source: `genesis_exec_summary.txt`

- `count`: `8`
- `first_pc`: `03C52A`
- `first_addr`: `C09EA0`
- `first_frame`: `170`
- `last_pc`: `03C518`
- `last_addr`: `C09EA6`
- `last_frame`: `384`

## addr=C09EA0 Scan
Source: `genesis_exec_trace.log`

Match found:
- `[frame 000170] live_write fg_cwindow_live pc=03c52a addr=c09ea0 data=0000 mask=ffff count=1`

PC that wrote `addr=C09EA0`:
- `03C52A`

## Notes
- Regression watch from the same summary still reports `reg_c50000_live count=0`.
- This report is data collection only; no game code or patch spec changes were made.
