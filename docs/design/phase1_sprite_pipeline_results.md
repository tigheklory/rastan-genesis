# Phase 1 Sprite Pipeline Results

## 1. Purpose
Implement and validate the locked Phase 1 path from `docs/design/vblank_phase1_sprite_pipeline.md`:
Block-A producer -> existing renderer bridge -> `genesistan_render_sprites_vdp()` -> SAT staging -> SAT publish, all under arcade vblank ownership.

## 2. Activation Patch Verification
Spec file checked: `specs/startup_title_remap.json`

Required entry:
- `arcade_pc`: `0x059F90`
- required `replacement_bytes`: `4eb90005a0b44e75`

Result:
- before (current repo state): `4eb90005a0b44e75`
- after: unchanged (no spec edit required)

Static ROM confirmation (`dist/Rastan_278.bin`):
- `0x05A1A6`: `4e b9 00 05 a2 b4 4e 75` (`JSR 0x05A2B4; RTS`)
- `0x05A2B4`: `30 2d 01 3a 08 00 00 0f` (full builder preamble)
- title dispatch block:
  - `0x03AAEC`: `4e b9 00 05 a1 74` (producer call)
  - `0x03AAF2`: `4e b9 00 20 2d b8` (renderer bridge call)

## 3. Runtime Path Verification
Tooling used:
- Build: `source tools/setup_env.sh && make -C apps/rastan release`
- Runtime probe: `tools/mame/run_genesis_trace_wsl.sh`
- Lua script: `/tmp/phase1_sprite_pipeline_probe_v2.lua`
- Probe output: `/tmp/phase1_sprite_pipeline_probe_v2.txt`

Runtime hit evidence:
- `HIT 03A208 791` (arcade vblank entry active)
- `HIT 03AAEC 1` (producer slot executes)
- `HIT 03AAF2 1` (renderer slot executes)
- `HIT 05A174 1` (producer target executes)
- `HIT 05A1A6 4` (restored callsite executes)
- `HIT 05A2B4 1` (full block-A builder entry executes)
- `HIT 202DB8 7` (`genesistan_render_sprites_vdp_bridge` symbol in this build)
- `HIT 2005C4 2` (`genesistan_render_sprites_vdp` executes)

## 4. Block-A Verification
At frame 700:
- `blockA_entry0=0000 00E8 03CA 0010`
- `blockA_nonzero_entries=1`

Result: PASS for Phase 1 input activation (Block-A is not all-zero and includes expected tuple form).

## 5. SAT Staging Verification
`vdpSpriteCache` base in this build (`symbol.txt`): `0xE0FF6DF2`.

At frame 700:
- `vdpSpriteCache_entry0=0168 0501 8400 0090`
- `sat_cache_nonzero_entries=19`

Result: PASS for SAT staging (nonzero SAT entries are built in WRAM; sprite_count is effectively > 0).

## 6. VDP SAT Verification
VDP VRAM SAT region sampled at frame 700:
- `vram_sat_words_nonzero=0`
- `vram_f800=0000 0000 0000 0000`

Additional transfer observation from data-port tap:
- `sat_port_writes_words=0`
- `sat_port_writes_nonzero=0`

Result: FAIL for Phase 1 publish proof in this run (SAT content present in WRAM staging but not observed as nonzero in VRAM `0xF800`).

## 7. Visual Verification
Capture artifact:
- `docs/design/artifacts/build278_phase1_pipeline_frame700.png`

Observed image: black screen with `CREDIT` text only; no confirmed sprite/logo pixels.

Classification: FAIL

## 8. Primary Failure Classification (if needed)
Selected primary cause: **E. VDP sprite table base/write issue**.

Evidence used:
- Producer path runs and Block-A tuple is valid (`0000/00E8/03CA/0010`).
- Renderer path runs and SAT staging is nonzero (`vdpSpriteCache_entry0=0168 0501 8400 0090`, 19 nonzero entries).
- VRAM SAT region remains zero at `0xF800` in the measured frame.

## 9. Final Result
Phase 1 activation is confirmed through producer execution, Block-A population, and nonzero SAT staging in WRAM inside the arcade vblank flow. The end-to-end visible sprite result is still not achieved in this build because SAT publish is not observed as nonzero at VRAM `0xF800` in the measured run.
