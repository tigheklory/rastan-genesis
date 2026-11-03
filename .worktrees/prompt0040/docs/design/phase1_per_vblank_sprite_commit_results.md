# Phase 1 Per-VBlank Sprite Commit Results

## 1. Purpose
Implement the approved Phase 1 migration slice: add an unconditional `genesistan_render_sprites_vdp()` call inside `genesistan_frontend_live_vint_handoff()` after `genesistan_run_original_frontend_tick()` returns, then validate sustained per-vblank sprite commit behavior.

## 2. Exact Code Change
File changed:
- `apps/rastan/src/main.c`

Function changed:
- `genesistan_frontend_live_vint_handoff()`

Before:
```c
genesistan_refresh_arcade_inputs();
genesistan_run_original_frontend_tick();
```

After:
```c
genesistan_refresh_arcade_inputs();
genesistan_run_original_frontend_tick();
genesistan_render_sprites_vdp();
```

Patch location from diff:
- `main.c` around line 1889
- inserted exactly one unconditional call after arcade tick return.

## 3. Build Performed
Build command:
```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Fresh artifact:
- `dist/Rastan_279.bin`
- Build output line: `Release: ../../dist/Rastan_279.bin`

## 4. Runtime Call Frequency Verification
Probe script:
- `/tmp/phase1_per_vblank_commit_probe.lua`
- output: `/tmp/phase1_per_vblank_commit_probe.txt`

Key runtime hits:
- `HIT 202DD8 791` (`genesistan_run_original_frontend_tick`)
- `HIT 03A208 791` (arcade level-5 entry path)
- `HIT 2005C4 793` (`genesistan_render_sprites_vdp`)

Result:
- Arcade tick still runs continuously.
- Helper is now sustained/per-vblank (793 helper entries across a 791-vblank live run), not the prior 2-hit behavior.

## 5. SAT Staging Verification
From `/tmp/phase1_per_vblank_commit_probe.txt`:
- Frame 300: `vdpSpriteCache_entry0=0168 0501 8400 0090`, `sat_cache_nonzero_entries=19`
- Frame 700: `vdpSpriteCache_entry0=0168 0501 8400 0090`, `sat_cache_nonzero_entries=19`
- `max_sat_cache_nonzero_entries=19`

Result:
- SAT staging remains nonzero and stable after the per-vblank call insertion.

## 6. VDP SAT Publish Verification
### 6.1 DMA-backed publish frequency evidence
Probe script:
- `/tmp/phase1_dma_publish_probe.lua`
- output: `/tmp/phase1_dma_publish_probe.txt`

Evidence:
- `sat_dma_cmd_post_launch=632` decoded DMA VRAM commands targeting SAT base `0xF800` (code `0x21`, addr `0xF800`) after launch.
- DMA setup register writes observed repeatedly:
  - `reg93=1649 reg94=1649 reg95=1594 reg96=1594 reg97=1649`

Interpretation:
- SAT DMA publish is now firing repeatedly post-launch rather than only transiently.

### 6.2 Direct SAT VRAM content check (DMA-safe method)
Probe script:
- `/tmp/vdp_port_read_sat.lua`
- output: `/tmp/vdp_port_read_sat.txt`

Method:
- Use VDP control port read-address command and read SAT words through VDP data port (hardware path), not CPU data-port write taps.

Observed at frame 700:
- `frame700_vdp_port_read_f800=0168 0501 8400 0090`
- control check at old base: `frame700_vdp_port_read_f400=0000 0000 0000 0000`

Result:
- SAT region at `0xF800` is confirmed nonzero via direct VDP read-port method.

## 7. Visual Verification
Capture artifact:
- `docs/design/artifacts/build279_per_vblank_commit_frame700.png`

Observed:
- `CREDIT` text is visible.
- No confirmed sprite/logo pixels are visible in this frame.

Classification:
- **FAIL** (still no confirmed sprite output).

## 8. Pre-Launch Regression Check
Capture artifact (no Start injected):
- `docs/design/artifacts/build279_prelaunch_frame120.png`

Observed:
- Launcher/startup config screen renders normally before launch.

Result:
- No obvious pre-launch regression observed in this pass.

## 9. Final Result
The approved Phase 1 slice was implemented exactly (single unconditional helper call in `genesistan_frontend_live_vint_handoff`). Runtime evidence confirms arcade tick continuity, sustained helper call frequency, stable nonzero SAT staging, and repeated DMA-backed SAT publish activity targeting `0xF800` with direct nonzero SAT word readback at frame 700. Visual sprite output is still not confirmed in this build frame.
