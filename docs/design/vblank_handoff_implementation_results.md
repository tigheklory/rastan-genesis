# VBlank Handoff Implementation Results

## 1. Purpose
Implement post-launch frame-ownership handoff so launcher/SGDK no longer owns live frame progression or post-launch display update flow, and arcade level-5 (`0x3A008` -> Genesis `0x03A208`) remains the sole authoritative frame controller.

## 2. Launcher/SGDK Ownership Path Identified
Identified in `apps/rastan/src/main.c` (previous `SCREEN_FRONTEND_LIVE` branch):

- `genesistan_refresh_arcade_inputs()`
- `genesistan_run_original_frontend_tick()`
- `genesistan_sync_title_vdp_layout()`
- `sanitize_arcade_workram()`
- `load_arcade_palette()`
- `sync_arcade_scroll_to_vdp()`
- `render_frontend_sprite_layer()`
- plus unconditional `SYS_doVBlankProcess()` at loop tail

This was a launcher/main-loop post-launch owner path. It continued to drive live progression and post-launch updates from C loop context after launch.

## 3. Exact Code Change
File changed: `apps/rastan/src/main.c`

### A) Added explicit post-launch V-Int handoff callback
- Added `frontend_live_handoff_active` flag
- Added `genesistan_frontend_live_vint_handoff()`:
  - gate: active only when `frontend_live_handoff_active == true` and `current_screen == SCREEN_FRONTEND_LIVE`
  - action: `genesistan_refresh_arcade_inputs(); genesistan_run_original_frontend_tick();`

### B) Activated handoff at launch
In `request_start_rastan()`:
- `genesistan_reclaim_launcher_wram();`
- `frontend_live_handoff_active = TRUE;`
- `SYS_setVIntCallback(genesistan_frontend_live_vint_handoff);`
- `SYS_enableInts();`

### C) Preserved pre-launch behavior and disabled post-launch launcher ownership
- In `reset_launcher_runtime_state()`:
  - `frontend_live_handoff_active = FALSE;`
  - `SYS_setVIntCallback(NULL);`
- In main loop `SCREEN_FRONTEND_LIVE` branch:
  - removed prior post-launch owner calls (branch is now handoff comment/no-op)
- Loop tail changed to:
  - call `SYS_doVBlankProcess()` only when `current_screen != SCREEN_FRONTEND_LIVE`

## 4. Build Performed
Command:
```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Fresh artifact:
- `dist/Rastan_278.bin`
- Build output line: `Release: ../../dist/Rastan_278.bin`

## 5. Runtime Handoff Verification
Probe script:
- `/tmp/vblank_handoff_probe.lua`

Run command:
```bash
timeout 180s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_278.bin \
  -autoboot_script /tmp/vblank_handoff_probe.lua -sound none -video none
```

Probe output:
- `/tmp/vblank_handoff_probe.txt`

Key runtime stats:
- `launch_detected frame=241`
- `STAT frontend_live_vint_handoff total=371 pre=0 post=371 last=619`
- `STAT run_original_frontend_tick total=371 pre=0 post=371 last=619`
- `STAT arcade_level5_entry total=371 pre=0 post=371 last=619`
- `STAT sys_dovblankprocess_ex total=227 pre=227 post=0 last=240`

Interpretation:
- after launch, V-Int handoff callback runs continuously
- after launch, arcade level-5 entry runs continuously
- after launch, launcher loop vblank-process owner path (`SYS_doVBlankProcessEx`) no longer runs

## 6. Pre-Launch Regression Check
Visual capture with delayed launch start:
```bash
timeout 220s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_278.bin \
  -autoboot_script /tmp/vblank_handoff_probe.lua \
  -aviwrite /tmp/build278_vblank_handoff.avi -sound none
```

Extracted frame (pre-launch):
- `/tmp/build278_vblank_handoff_frame_001.png` (frame 100)

Observed:
- launcher/config screen is visible before launch (no pre-launch regression).

## 7. Post-Launch Ownership Verification
Post-launch evidence in same capture/probe:
- frame samples after launch (`frame=260/420/560`) show live state progression
- `SYS_doVBlankProcessEx` stops exactly at pre-launch boundary (`last=240`)
- `frontend_live_vint_handoff`, `run_original_frontend_tick`, and `arcade_level5_entry` continue through post-launch frames

No dual ownership after launch:
- launcher/SGDK post-launch owner path count: `post=0`
- arcade level-5 path count: `post=371`

## 8. Final Result
Handoff was implemented as a minimal ownership-only change:
- pre-launch launcher behavior preserved
- post-launch launcher/SGDK frame-owner path disabled
- arcade level-5 frame ownership preserved and active
- dual ownership removed post-launch

Launcher post-launch ownership: stopped (post-launch `SYS_doVBlankProcessEx` hits = 0)
Arcade level-5 ownership: active (post-launch `0x03A208` hits = 371)
Dual ownership removed: yes (launcher post=0 while arcade post>0)
