# Cody Build 55 MAME Genesis Palette Runtime Trace

## §1.1 ROM identity
- Path: `dist/rastan-direct/rastan_direct_video_test_build_0055.bin`
- Size (bytes): `1559136` = `0x17CA60` (matches expected invariant)
- SHA256: `d4235aa984f8eedf217f19a3d3e321adc3b55a722e0f8cab49d353852a0b64e2`
- Verification: PASS

## §1.2 Trace target verification against symbol map
From `apps/rastan-direct/out/symbol.txt`:
- `genesistan_palette_hook_59ad4` = `0x000711E2` (line 176) PASS
- `genesistan_palette_hook_03ab00` = `0x00071248` (line 177) PASS
- `genesistan_palette_hook_45dae` = `0x0007126C` (line 178) PASS
- `vdp_commit_palette` = `0x000701CC` (line 159) PASS
- `_vblank_service` = `0x000700C2` (line 155) PASS
- `palette_dirty` = `0x00FF4000` (line 244) PASS
- `staged_palette_words` = `0x00FF601A` (line 256) PASS
- `staged_palette_words + 0x80` = `0x00FF609A` (computed end-exclusive)

## §1.3 MAME harness invocation
- Driver: `genesis`
- Command:
  - `GENESISTAN_ROOT=/home/tighe/projects/rastan-genesis QT_QPA_PLATFORM=offscreen /usr/games/mame genesis -cart /home/tighe/projects/rastan-genesis/dist/rastan-direct/rastan_direct_video_test_build_0055.bin -debug -debugger qt -debugscript /home/tighe/projects/rastan-genesis/states/traces/build55_palette_runtime_trace_20260504_134411/build55_palette_trace.cmd -debuglog -video none -sound none -nothrottle -skip_gameinfo -seconds_to_run 65`
- Output artifacts:
  - `states/traces/build55_palette_runtime_trace_20260504_134411/build55_palette_trace.cmd`
  - `states/traces/build55_palette_runtime_trace_20260504_134411/debug.log`
  - `states/traces/build55_palette_runtime_trace_20260504_134411/mame_stdout_qt.log`
  - `states/traces/build55_palette_runtime_trace_20260504_134411/mame_stderr_qt.log`
- Duration:
  - Emulated: `64 seconds` (`mame_stdout_qt.log`)
  - Wall: `18 seconds`

## §1.4 Trace executed
- Status: YES
- Trace log size: `652311` lines (`debug.log`)

## §2.1 Hit count summary (PC targets)
From `debug.log` event counts:
- `genesistan_palette_hook_59ad4` (`0x000711E2`): `hit_count = 0`
- `genesistan_palette_hook_03ab00` (`0x00071248`): `hit_count = 0`
- `genesistan_palette_hook_45dae` (`0x0007126C`): `hit_count = 0`
- `vdp_commit_palette` (`0x000701CC`): `hit_count = 0`

Additional observed control target:
- `_vblank_service` breakpoint (`0x000700C2`): `hit_count = 255`
  - first sample line: `debug.log:34580`
  - last sample line: `debug.log:652276`

## §2.2 `staged_palette_words` write summary (`0x00FF601A..0x00FF6099`)
- Total writes: `960` (`WP_STAGED_PALETTE`)
- Distinct addresses written: `64`
  - full range observed: `FF601A` through `FF6098` (all 64 word slots)
- First 5 writes (trace-cited):
  - `debug.log:54` `addr=FF601A pre=0 post=0 pc=298`
  - `debug.log:56` `addr=FF601C pre=0 post=0 pc=298`
  - `debug.log:58` `addr=FF601E pre=0 post=0 pc=298`
  - `debug.log:60` `addr=FF6020 pre=0 post=0 pc=298`
  - `debug.log:62` `addr=FF6022 pre=0 post=0 pc=298`
- Last write sample:
  - `debug.log:608984` `addr=FF6098 pre=0 post=0 pc=298`
- Writer PC context:
  - all `960/960` writes from `pc=298`
  - `build/genesis_postpatch.disasm.txt` shows bootstrap clear loop at `0x294..0x298` (`clrw %a0@+`, `dbf`)
- Non-zero writes:
  - `0` non-zero (`post` always `0`)
- Helper-range correlation:
  - no write from helper PCs (`0x711E2/0x71248/0x7126C`)

## §2.3 `palette_dirty` write summary (`0x00FF4000`)
- Total writes: `15` (`WP_PALETTE_DIRTY`)
- Value sequence:
  - all observed writes are `pre=0 post=0`
  - first: `debug.log:52` (`pc=27A`)
  - subsequent periodic examples: `debug.log:43538`, `87024`, `130510`, ..., `608856`
- Ever became `1`: NO
- Writer PC context:
  - `pc=27A` (bootstrap clear path; `build/genesis_postpatch.disasm.txt` contains `clrb 0xff4000` at `0x272`)

## §2.4 `vdp_commit_palette` execution evidence
- `hit_count = 0` (no `BP_VDP_COMMIT_PALETTE` events)
- Because commit entry never hit:
  - `palette_dirty` at entry: N/A
  - staged sample at entry: N/A
  - commit-scoped CRAM writes: N/A

## §2.5 CRAM-target write capture
- Capture configured: YES (`WP_VDP_CTRL`, `WP_VDP_DATA`)
- Total captured:
  - `WP_VDP_CTRL`: `30855`
  - `WP_VDP_DATA`: `294060`
- Control writes at/near `vdp_commit_palette` PCs:
  - none observed (`pc=701CC..701EA` not present in `WP_VDP_CTRL` lines)
- Data writes at/near `vdp_commit_palette` PCs:
  - none observed (`pc=701CC..701EA` not present in `WP_VDP_DATA` lines)
- CRAM-target control pattern (`0xC000xxxx`) in this trace:
  - NOT OBSERVED in captured control write `pre=` values

## §2.6 First broken link classification
- Classification: **A. helpers not reached**

Evidence:
- All three helper entry breakpoints had zero hits:
  - `genesistan_palette_hook_59ad4`: `0`
  - `genesistan_palette_hook_03ab00`: `0`
  - `genesistan_palette_hook_45dae`: `0`
- Staging/dirty writes observed were bootstrap clears only:
  - `staged_palette_words` writes from `pc=298`, all zero (`debug.log:54..608984`)
  - `palette_dirty` writes from `pc=27A`, all zero (`debug.log:52..608856`)
- `_vblank_service` is active (`255` hits), but `vdp_commit_palette` entry is never hit (`0`).

## §3 Integrity
- §1.1 ROM identity verified: YES
- §1.2 trace targets match symbol map: YES
- §1.3 harness invoked: YES
- §1.4 trace executed: YES
- §2.1 hit counts for all 4 PC targets: YES
- §2.2 staged write summary: YES
- §2.3 dirty write summary: YES
- §2.4 commit evidence: YES (`hit_count: 0`)
- §2.5 CRAM-target capture: YES (capture configured; commit-scoped CRAM pattern not observed)
- §2.6 classification: A
- Findings cited from local trace artifacts: YES
- No hypotheses beyond evidence: YES
- No fixes recommended: YES
- No external sources: YES
- Trace duration sufficient: YES (64s emulated)

