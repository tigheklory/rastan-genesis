# Phase 2 Block-A Builder Implementation Results

## 1. Purpose
Apply the single approved Phase 2 spec change at arcade `0x059F90` to restore execution of the real block-A builder entry path, then validate via fresh build, static ROM checks, runtime probes, and visual capture.

## 2. Single Spec Change Applied
File changed: `specs/startup_title_remap.json`

Changed entry only:
- `arcade_pc`: `0x059F90`
- `original_bytes`: `4E75` (unchanged)
- `replacement_bytes`:
  - before: `4E75`
  - after: `4eb90005a0b44e75`

No other spec entry was edited.

## 3. Build Performed
Command used:
```bash
source tools/setup_env.sh && make -C apps/rastan release
```

Fresh artifact produced:
- `dist/Rastan_277.bin`
- Build output line: `Release: ../../dist/Rastan_277.bin`

## 4. Static ROM Verification
ROM checked: `dist/Rastan_277.bin`

1. Callsite bytes at Genesis `0x05A1A6`:
- observed: `4eb90005a2b44e75`
- expected: `4eb90005a2b44e75`
- result: PASS

2. Builder target preamble at Genesis `0x05A2B4`:
- observed: `302d013a0800000f`
- expected: `302d013a0800000f`
- result: PASS

3. Wrong-target exclusions (decoded call operand from `0x05A1A6`):
- decoded operand: `0x05A2B4`
- equals `0x05A4B4`? NO
- equals `0x05A2CE`? NO
- result: PASS

## 5. Runtime Block-A Verification
Probe run (existing Genesis MAME harness + Lua probe):
```bash
timeout 150s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_277.bin \
  -autoboot_script /tmp/phase2_blocka_restore_probe.lua \
  -sound none -video none
```

Runtime evidence (`/tmp/phase2_blocka_restore_probe.txt`):
- Producer/restore path hits:
  - `HIT 03AAEC 1`
  - `HIT 05A1A6 4`
  - `HIT 05A174 1`
  - `HIT 05A2B4 1`
- Block-A samples:
  - early (`frame=300`): `A=0000 0000 0000 0000`
  - productive (`frame=700`): `A=0000 00E8 03CA 0010`
- interpretation: block-A transitions from all-zero to nonzero descriptor content after producer path executes.

Result: PASS (block-A becomes nonzero)

## 6. Renderer Verification
Runtime evidence (`/tmp/phase2_blocka_restore_probe.txt`):
- Renderer path hits:
  - `HIT 03AAF2 1`
  - `HIT 202B80 6`
  - `HIT 2005C4 198`
- Renderer-visible payload indicators:
  - `renderer_blocka_nonzero_hits=38`
  - `sample frame=700 ... code0=03CA tilebuf_nonzero=128`
  - `sample frame=700 ... A=0000 00E8 03CA 0010`

Result: PASS (renderer sees nonzero sprite payload; `sprite_code0 != 0`)

## 7. Visual Verification
Visual capture command:
```bash
timeout 180s tools/mame/run_genesis_trace_wsl.sh dist/Rastan_277.bin \
  -autoboot_script /tmp/phase2_blocka_restore_probe.lua \
  -aviwrite /tmp/build277_phase2_logo.avi -sound none
```

Frame extracted from MAME AVI:
- `/tmp/build277_phase2_frame_11_6.png`

Observed visual state in captured pre-coin run:
- `CREDIT` text is visible.
- No clearly visible title-logo sprite pixels were observed in this capture.

Visual result classification: NOT_CONFIRMED_FOR_LOGO_PIXELS

## 8. Final Result
- Single approved patch byte-sequence was implemented exactly.
- Static targeting checks passed exactly (`0x05A1A6 -> 0x05A2B4`, full preamble confirmed).
- Runtime path and data checks improved as expected (block-A and sprite payload become nonzero).
- Visible logo pixels are not yet confirmed in the captured pre-coin visual output.

Implemented bytes: 4eb90005a0b44e75
Block-A runtime result: nonzero block-A confirmed (A=0000 00E8 03CA 0010 at frame 700)
Renderer result: nonzero payload confirmed (code0=03CA, tilebuf_nonzero=128, renderer_blocka_nonzero_hits=38)
Visual result: logo pixels not yet visually confirmed in captured pre-coin frame sequence
