# Non-C Sprite Commit Results

## 1. Purpose
Implement the approved ownership-migration slice: add `genesistan_sprite_commit_asm` and make it the live post-launch per-vblank sprite commit path from `genesistan_frontend_live_vint_handoff()`, replacing direct handoff ownership by `genesistan_render_sprites_vdp()`.

## 2. Exact Code Changes
Files changed:
- `apps/rastan/src/startup_trampoline.s`
- `apps/rastan/src/main.c`

### 2.1 `startup_trampoline.s`
- Added exported symbol: `genesistan_sprite_commit_asm`.
- Added new assembly routine that:
  - sets VDP auto-inc (`0x8F02`)
  - sets SAT write destination to VRAM `0xF800` (`0x78000003`)
  - iterates Block-A at `0xE0FF11FE` for 18 entries
  - skips only `word1 == 0x0180`
  - emits SAT words directly to `0xC00000`:
    - `Y = word1 + 0x80`
    - `size/link = 0x0500` (temporary)
    - `tile/attr = (word2 & 0x3FFF) + 0x0400`, OR `0x8000` (temporary hardcoded attr policy)
    - `X = word3 + 0x80`
- Added no-hook fallback stub in `#else`: `genesistan_sprite_commit_asm: rts`.

### 2.2 `main.c`
- Added declaration: `void genesistan_sprite_commit_asm(void);`
- In `genesistan_frontend_live_vint_handoff()` replaced:
  - `genesistan_render_sprites_vdp();`
  - with `genesistan_sprite_commit_asm();`

## 3. Assembly Routine Behavior
Implemented routine (`apps/rastan/src/startup_trampoline.s:75`) performs the approved minimal non-C commit:
- destination SAT base programmed to VRAM `0xF800`
- source descriptor block read from `0xE0FF11FE`
- hidden sentinel filter only (`word1 == 0x0180`)
- SAT words written directly through VDP data port
- no `VDP_setSpriteFull`, no `VDP_updateSprites`, no `vdpSpriteCache` publish dependency in this path.

## 4. Build Performed
Build command:
```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Fresh artifact:
- `dist/Rastan_280.bin`
- build output line: `Release: ../../dist/Rastan_280.bin`

## 5. Live Ownership Verification
Static proof from `genesistan_frontend_live_vint_handoff()` (`apps/rastan/src/main.c:1891-1893`):
- still runs arcade tick first: `genesistan_run_original_frontend_tick();`
- now calls assembly commit: `genesistan_sprite_commit_asm();`
- no `genesistan_render_sprites_vdp();` call remains in this handoff body.

Runtime probe used:
```bash
timeout 180s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_280.bin \
  -autoboot_script /tmp/non_c_sprite_commit_probe.lua -sound none -video none
```

Output: `/tmp/non_c_sprite_commit_probe.txt`

Key hits:
- `HIT 03A208 791` (arcade level-5 path)
- `HIT 202E38 791` (`genesistan_run_original_frontend_tick`)
- `HIT 202DC8 793` (`genesistan_sprite_commit_asm`)
- `HIT 2005C4 2` (`genesistan_render_sprites_vdp`)
- `HIT 202B80 0` (bridge)

Result:
- assembly commit is the sustained post-launch handoff path.
- helper is no longer handoff-owned (no per-vblank helper parity).

## 6. Assembly Call Frequency Verification
From `/tmp/non_c_sprite_commit_probe.txt`:
- `genesistan_sprite_commit_asm` hits: `793`
- arcade tick hits: `791`

Conclusion:
- assembly commit runs continuously/per-vblank in the live path (slight +2 due frame/tap boundary effects).

## 7. VRAM SAT Verification
Same probe (`/tmp/non_c_sprite_commit_probe.txt`) captured at frame 700:
- `sat_f800=0168 0500 87CA 0090` (nonzero SAT data at active SAT base)

Additional assembly-origin write evidence:
- `asm_vdp_ctrl_writes=1582`
- `asm_vdp_data_writes=37440`
- `asm_sat_word_writes=512`

This confirms SAT-region writes are being driven from the new assembly routine.

## 8. Helper Path Displacement Verification
At frame 700 sample (`/tmp/non_c_sprite_commit_probe.txt`):
- `vdpSpriteCache0=0168 0501 8400 0090`
- `sat_f800=0168 0500 87CA 0090`

Interpretation:
- live SAT content differs from cached SGDK tuple format/value, indicating direct assembly SAT publication is now authoritative.
- helper no longer owns the live handoff commit path.

## 9. Visual Verification
Capture run:
```bash
timeout 220s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_280.bin \
  -autoboot_script /tmp/non_c_sprite_commit_visual.lua \
  -aviwrite /tmp/build280_non_c_sprite_commit.avi -sound none
```

Frame extraction:
```bash
ffmpeg -y -i /tmp/build280_non_c_sprite_commit.avi \
  -vf "select=eq(n\\,699)" -frames:v 1 -update 1 \
  /tmp/build280_non_c_sprite_commit_frame700.png
```

Observed frame:
- `/tmp/build280_non_c_sprite_commit_frame700.png`
- visible `CREDIT` text only; no confirmed sprite/logo pixels.

Visual classification:
- **FAIL**

Pre-launch regression check:
- capture run: `timeout 180s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_280.bin -autoboot_script /tmp/non_c_sprite_prelaunch.lua -aviwrite /tmp/build280_non_c_prelaunch.avi -sound none`
- extracted frame: `/tmp/build280_non_c_prelaunch_frame120.png`
- observed: launcher/config screen still renders before launch (no obvious pre-launch regression).

## 10. Known Temporary Limitations
Intentionally retained for this slice:
- tile lookup remains stubbed/hardcoded (`+0x0400` base)
- palette handling remains hardcoded
- size/link remains fixed `0x0500`
- flipscreen handling deferred
- full link-chain correctness deferred
- animation/size decoding deferred

## 11. Final Result
Architectural migration outcome:
- `genesistan_render_sprites_vdp()` removed from live handoff ownership path.
- `genesistan_sprite_commit_asm` is now the per-vblank live commit owner in handoff.
- SAT VRAM at `0xF800` is nonzero and written from assembly path.

Visual outcome:
- sprite/logo pixels are still not confirmed in this build frame (visual FAIL), but ownership migration criteria for this slice are satisfied.

Live helper ownership removed: yes (from `genesistan_frontend_live_vint_handoff`)
Assembly commit frequency: sustained (793 hits vs 791 arcade ticks)
VRAM SAT at 0xF800: nonzero (`0168 0500 87CA 0090` at frame 700)
Visual result: FAIL (no confirmed sprite/logo pixels)
