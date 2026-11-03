# System-Wide Tile Visibility Results

## 1. Purpose
Implement the approved temporary system-wide sprite visibility bring-up slice on the active non-C commit path:
- one known-visible tile loaded to VRAM tile slot 1
- system-wide SAT tile_attr override to `0x8001` for the current Block-A stream
- no per-entry or logo-specific logic.

## 2. Exact Code Changes
Files changed:
- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_trampoline.s`

### 2.1 `main.c` change
In `genesistan_sync_title_vdp_layout()`:
- added one-time tile upload for tile slot 1 via `VDP_loadTileData(..., 1, 1, CPU)`
- tile pattern: 32 bytes of `0x11` nibbles (as 16 words of `0x1111`), i.e. a solid visible tile.

### 2.2 `startup_trampoline.s` change
In `genesistan_sprite_commit_asm` Block-A loop:
- replaced per-entry tile computation with:
  - `move.w #0x8001, %d1`
- applies uniformly to every valid processed Block-A entry.

## 3. Tile Slot 1 Initialization
Implementation location:
- `apps/rastan/src/main.c`, inside `genesistan_sync_title_vdp_layout()`.

Behavior:
- during title/live setup, tile slot 1 (VRAM address `0x0020`) is loaded with a solid pattern.
- this is setup-time initialization, not per-vblank commit logic.

## 4. Assembly TileAttr Override
Implementation location:
- `apps/rastan/src/startup_trampoline.s`, `genesistan_sprite_commit_asm` loop.

Behavior:
- all valid Block-A entries now use identical tile_attr value `0x8001`.
- no entry index branch, no logo pattern check, no sprite-specific condition.

## 5. Build Performed
Build command:
```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Fresh artifact:
- `dist/Rastan_281.bin`
- build output line: `Release: ../../dist/Rastan_281.bin`

## 6. Runtime Call Frequency Verification
Probe command:
```bash
timeout 180s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_281.bin \
  -autoboot_script /tmp/system_wide_tile_visibility_probe.lua -sound none -video none
```

Probe output:
- `/tmp/system_wide_tile_visibility_probe.txt`

Hit counts:
- `HIT 03A208 791`
- `HIT 202DC8 793` (`genesistan_sprite_commit_asm`)
- `HIT 202E2C 791` (`genesistan_run_original_frontend_tick`)
- `HIT 2005C4 2`

Result:
- non-C assembly commit remains sustained per-vblank.

## 7. VRAM Tile Verification
From `/tmp/system_wide_tile_visibility_probe.txt` at frame 700:
- `tile1_words=1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111`
- `tile1_nonzero_words=16/16`

Result:
- VRAM tile slot 1 (`0x0020`) contains visible nonzero tile data.

## 8. SAT Verification
From `/tmp/system_wide_tile_visibility_probe.txt` at frame 700:
- `sat[00]=0168 0500 8001 0090`
- `sat[01]=0080 0500 8001 0080`
- `sat[02]=0080 0500 8001 0080`
- ...
- `sat[11]=0080 0500 8001 0080`
- `sat_nonzero_entries_0_11=12`
- `sat_attr_8001_entries_0_11=12`

Result:
- multiple SAT entries (not just one) use tile_attr `0x8001`.
- override is system-wide for the sampled active stream.

## 9. Visual Verification
Capture command:
```bash
timeout 220s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_281.bin \
  -autoboot_script /tmp/system_wide_tile_visibility_visual.lua \
  -aviwrite /tmp/build281_system_wide_visibility.avi -sound none
```

Frame extraction:
```bash
ffmpeg -y -i /tmp/build281_system_wide_visibility.avi \
  -vf "select=eq(n\\,699)" -frames:v 1 -update 1 \
  /tmp/build281_system_wide_visibility_frame700.png
```

Observed:
- `/tmp/build281_system_wide_visibility_frame700.png` shows no visible yellow-green sprite blocks.
- `CREDIT` text remains visible.

Classification:
- **FAIL** (no visible yellow-green sprite blocks).

Pre-launch regression check:
- capture: `timeout 180s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_281.bin -autoboot_script /tmp/non_c_sprite_prelaunch.lua -aviwrite /tmp/build281_prelaunch.avi -sound none`
- extracted frame: `/tmp/build281_prelaunch_frame120.png`
- launcher/startup screen still renders; no obvious pre-launch regression.

## 10. No-Special-Case Verification
Confirmed:
- no entry-0-only condition added
- no logo-specific condition added
- same tile rule (`0x8001`) applied in one unconditional instruction for all valid entries in loop
- same tile slot 1 initialization is generic and not sprite-instance-specific.

## 11. Final Result
Implemented temporary system-wide bring-up exactly as requested:
- tile slot 1 initialized with visible data
- non-C commit still runs every vblank
- sampled SAT entries are system-wide `0x8001`
- no special-case logic was introduced

Visual blocks are still not visible in frame 700, so visual classification is FAIL.

Architectural checks that DID pass despite visual FAIL:
- tile slot 1 loaded and nonzero
- assembly commit sustained per-vblank
- SAT entries sampled as `0x8001` across multiple entries
- override rule applied system-wide (no per-sprite exception logic)
