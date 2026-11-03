# Cody - VINT Timing Trace Harness

**Date:** 2026-07-12
**Type:** Analysis/tooling only
**Build target for next run:** Build 0162
**Prior source of truth:** `docs/design/Cody_gameplay_vint_invocation_ownership.md`
**Scope:** Create a reusable MAME Lua trace harness only. No ROM build, no source/spec/Makefile/ROM/invariant changes, no collision/palette/PC080SN/PC090OJ-represent/gameplay-state work.

## Baseline

The prior VINT ownership audit established:

- Genesis Level-6 vector 30 at ROM `0x000078` points to `_vblank_service` at `runtime_genesis_pc 0x000700C2`.
- `vdp_prepare_sprites` is unconditional inside `_vblank_service`.
- Known VDP Mode-2 register writes are `0x8134` and `0x8174`; both keep VINT enabled.
- `_vblank_service` tail-jumps at `runtime_genesis_pc 0x00070108` to arcade VBlank entry `runtime_genesis_pc 0x0003A208`.
- The arcade VBlank body returns by `runtime_genesis_pc 0x0003A27E rte`.
- The current leading hypothesis is combined handler duration, masking, reentrancy, VDP reg-1 clobber, or measurement artifact, not a missing vector or prepare dirty flag.

## Files Created

- `tools/traces/vint_timing_trace.lua`
- `docs/design/Cody_vint_timing_trace_harness.md`

`tools/traces/` did not previously exist; it was created because this harness is reusable tooling rather than one run's generated trace artifact. Output still goes under `states/traces/vint_timing/`.

## Trace Output

Default output:

- CSV: `states/traces/vint_timing/build0162_vint_timing.csv`
- Summary: `states/traces/vint_timing/build0162_vint_timing_summary.txt`

CSV columns:

```text
external_frame,event,pc,cycles,vcounter,hcounter,sr,ipm,write_addr,write_value,vdp_reg,vdp_value,vint_enabled,display_enabled,notes
```

The frame number is MAME's external frame callback count (`emu.register_frame_done`), not a counter maintained by `_vblank_service`.

## Events Logged

Execute taps are attempted for:

| Event | runtime_genesis_pc |
|---|---:|
| `VBLANK_SERVICE_ENTRY` | `0x000700C2` |
| `VBLANK_SERVICE_TAIL_JMP` | `0x00070108` |
| `ARCADE_VBLANK_ENTRY` | `0x0003A208` |
| `ARCADE_VBLANK_CLEAR_MASK` | `0x0003A27A` |
| `ARCADE_VBLANK_RTE` | `0x0003A27E` |
| `PC090OJ_SR_MASK_SAVE` | `0x00071BDC` |
| `PC090OJ_SR_RESTORE` | `0x00071C14` |

The script records install status in the summary. If this MAME build does not expose Lua execute taps, the summary reports those failures explicitly rather than treating missing PC events as evidence.

A write tap is installed on VDP control-port range `HW_ADDRESS 0x00C00004..0x00C00007`.

## VDP Register-1 Decode

For each VDP control-port word write, the script decodes VDP register writes. If the decoded register is 1, it reports:

- raw word, e.g. `0x8134` or `0x8174`
- register number `1`
- value byte
- VINT enable bit state (`value & 0x20`)
- display enable bit state (`value & 0x40`)

Any register-1 write with VINT disabled is counted in the summary.

## SR / IPM Support

The harness reads `cpu.state['SR']` when available and derives IPM as `(SR >> 8) & 7`. SR/IPM is sampled at each logged PC event and VDP write event.

The summary also counts frames where IPM was `>= 6` at one external frame boundary and the following frame had no `_vblank_service` entry. This is a conservative indicator only; it supports mask-blocking suspicion but is not, alone, proof of the exact missed-VINT mechanism.

## Cycle / VCounter Support

Cycle count and screen position are opportunistic because MAME Lua API availability varies by build:

- cycles: attempted through CPU cycle fields/methods if exposed
- VCounter/HCounter: attempted through screen `vpos`/`hpos` if exposed

If unavailable, the CSV fields are blank and the summary says service-chain duration is unavailable.

## Exact Command Line

Manual/gameplay capture, run until Andy stops MAME:

```bash
TRACE_DIR=states/traces/vint_timing VINT_TRACE_FRAMES=0 mame genesis -cart dist/rastan-direct/rastan_direct_video_test_build_0162.bin -window -nothrottle -sound none -skip_gameinfo -autoboot_script tools/traces/vint_timing_trace.lua
```

Bounded no-input smoke run, auto-exits after 1200 external frames:

```bash
TRACE_DIR=states/traces/vint_timing VINT_TRACE_FRAMES=1200 mame genesis -cart dist/rastan-direct/rastan_direct_video_test_build_0162.bin -window -nothrottle -sound none -skip_gameinfo -autoboot_script tools/traces/vint_timing_trace.lua
```

If local MAME needs an explicit ROM path setup, prepend the usual project `-rompath roms` argument.

## Expected-Good Interpretation

Expected good result:

- `VBLANK_SERVICE_ENTRY` fires once per external frame in the sampled gameplay window.
- Each frame has the chain `0x700C2 -> 0x70108 -> 0x3A208 -> 0x3A27E` before the next external frame.
- VDP register-1 writes are only VINT-enabled values such as `0x8134` and `0x8174`.
- No frame-boundary pattern shows IPM `>= 6` followed by a frame with no `_vblank_service` entry.

If this happens, Andy's prior 40% service measurement was likely a measurement artifact or used a bad frame source.

## Failure Interpretation

Use the distinctions from the prior audit:

- External frame advances but `0x700C2` does not fire: supports missed or masked VINT service.
- `0x700C2` fires but `0x3A27E` does not fire before the next external frame: supports overlong handler or stuck chain.
- Any VDP register-1 write with bit 5 clear: supports VINT-enable clobber.
- SR/IPM `>= 6` across an expected VBlank boundary: supports interrupt-mask blocking Level-6.
- One complete chain per external frame: prior 40% result is likely a measurement artifact.

Do not conclude from one counter alone; correlate chain events, VDP reg-1 writes, SR/IPM, and external frame count.

## Recommended Next Andy Prompt

```text
Run Build 0162 with `tools/traces/vint_timing_trace.lua` over the gameplay window where sprite prepare appeared to run on ~40% of frames.
Use external MAME frames from `build0162_vint_timing.csv`.
Report per-frame presence of `0x700C2`, `0x70108`, `0x3A208`, and `0x3A27E`.
Report any VDP reg-1 write where VINT enable bit 5 is clear.
Report SR/IPM at `0x700C2`, `0x70108`, `0x3A208`, `0x3A27A`, `0x3A27E`, `0x71BDC`, and `0x71C14`.
If cycle/VCounter fields are present, compute longest `0x700C2 -> 0x3A27E` duration.
Classify: missed VINT, overlong chain, VDP reg-1 clobber, SR mask block, or measurement artifact.
Do not change source, specs, ROM, PC080SN, PC090OJ represent logic, collision, or palettes.
```

## STOP Status

STOP triggered: **NO**. The task stayed tooling/documentation-only. No ROM/build/source behavior/spec changes were made.
