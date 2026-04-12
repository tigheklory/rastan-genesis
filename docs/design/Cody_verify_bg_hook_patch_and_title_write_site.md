# Cody Verify BG Hook Patch And Title Write Site

## 1. Executive Summary

The hook patch at arcade PC `0x055968` is present in the built Genesis ROM, but title-scene execution evidence shows that site is not executed during the 3000-frame title/attract observation window. Title-scene PC080SN BG RAM writes were observed at `0x03AD48` with high repetition, making it the single next patch target under the required selection rules.

## 2. Task 1 — Patch Presence

- ROM file used: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Offset checked: `0x055B68` (`0x055968 + 0x000200`)
- Exact bytes found at `0x055B68` (first 16):
  - `4E B9 00 07 01 30 4E 71 4E 71 4E 71 4E 71 4E 71`
- First 6 bytes:
  - `4E B9 00 07 01 30`
- Interpretation:
  - `4E B9 xx xx xx xx` = `JSR abs.l`
- patch present: **YES**

## 3. Task 2 — Execution Check

- Exact MAME command used:
  - `mame rastan -rompath /home/tighe/projects/rastan-genesis/roms -debug -debugger none -debugscript /tmp/bp_055968.cmd -debuglog -video none -sound none -nothrottle -skip_gameinfo -seconds_to_run 60`
- Breakpoint command used:
  - `bp 0x055968`
  - `g`
- Runtime duration:
  - 60 seconds (`Average speed: 616.13%`, effectively well beyond 3000 arcade frames)
- Breakpoint hit count:
  - `0`
  - (`/tmp/debug.log` contains only debugger startup banner and no breakpoint-stop lines)
- Supporting frame-window check (`3000` frames) also reported zero sampled PC hits at `0x055968`.
- executes during Title: **NO**

## 4. Task 3 — BG Write PCs (with counts + classification)

- Exact MAME command used:
  - `GENESISTAN_ROOT=/home/tighe/projects/rastan-genesis mame rastan -rompath /home/tighe/projects/rastan-genesis/roms -debug -debugger none -autoboot_script /tmp/bg_write_probe_227.lua -video none -sound none -nothrottle -skip_gameinfo -seconds_to_run 60`
- Exact watchpoint/method used:
  - Lua write tap on `0xC00000-0xC03FFF`:
    - `prog:install_write_tap(0xC00000, 0xC03FFF, 'bgwrites227', ...)`
- Observation window:
  - `3000` frames (title/attract window)
- At least 4 write events:
  - collected (`756` total)
- ALL unique PCs observed and counts:
  - `0x03AD48`: `756`
- Classification by required rule (`LOOP` if `>50`, else `SETUP`):
  - `0x03AD48` → `LOOP`

## 5. Task 4 — Root Outcome

Selected outcome: **B. patch applied, but 0x055968 not used in Title**

Reasoning from Tasks 1–3:
- Task 1 confirms patch bytes are present at `0x055B68`.
- Task 2 shows no execution hits for `0x055968` during title/attract observation.
- Task 3 shows title-scene BG writes happening from `0x03AD48`.

## 6. Task 5 — Selected Patch Target

- selected PC: `0x03AD48`
- hit count: `756`
- justification using strict rules:
  1. Highest hit count among observed write PCs: `0x03AD48` (only unique PC observed).
  2. Tie-break rule not needed.
  3. Classified as `LOOP` because `756 > 50`.

## 7. Final Result

- Patch at `0x055968` exists in ROM.
- `0x055968` is not executed during title/attract in this test window.
- Actual title-scene BG write loop PC observed: `0x03AD48`.
- Single next patch target (per rules): `0x03AD48`.
