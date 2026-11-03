# Cody - Build 0162 VINT Timing Trace Classification

**Date:** 2026-07-12
**Type:** Runtime timing evidence / classification only
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0162.bin`
**Scope:** Run the existing VINT timing trace harness and classify the VINT failure mode. No source/spec/ROM behavior changes. No build. No PC080SN, PC090OJ represent, collision, palette, player, camera/scroll, or D00298 work.

## Baseline

Source of truth for the harness and hypotheses: `docs/design/Cody_gameplay_vint_invocation_ownership.md` and `docs/design/Cody_vint_timing_trace_harness.md`.

Known pre-run facts carried in:

- Genesis VINT vector 30 points at `_vblank_service` (`runtime_genesis_pc 0x000700C2`).
- `_vblank_service` unconditionally calls `vdp_prepare_sprites` and then tail-jumps to arcade VBlank at `runtime_genesis_pc 0x0003A208`.
- Arcade VBlank returns by `runtime_genesis_pc 0x0003A27E rte`.
- Expected VDP register-1 writes are `0x8134` and `0x8174`, both VINT-enabled.

## Compatibility Note

The Lua harness could install VDP control-port write taps, but this MAME build did not expose the Lua `install_execute_tap` API needed for PC execution taps. The final evidence therefore used a read-only MAME debugger script with breakpoints that print the same event set to `debug.log`, followed by an offline parser that emitted the requested CSV and summary.

No ROM/source/spec behavior was changed. The Lua trace script was updated only as tooling compatibility/input support for future runs.

## Command Used

```bash
QT_QPA_PLATFORM=offscreen timeout 120s mame genesis \
  -cart dist/rastan-direct/rastan_direct_video_test_build_0162.bin \
  -video none -sound none -nothrottle -skip_gameinfo -seconds_to_run 25 \
  -debug -debugger qt -debuglog \
  -debugscript states/traces/vint_timing/build0162_vint_timing_debug.cmd \
  > states/traces/vint_timing/build0162_mame_stdout.log \
  2> states/traces/vint_timing/build0162_mame_stderr.log
```

Exit status: `0`.

Parser:

```bash
python3 states/traces/vint_timing/parse_vint_debuglog.py
```

## Evidence Files

- `states/traces/vint_timing/build0162_vint_timing.csv`
- `states/traces/vint_timing/build0162_vint_timing_summary.txt`
- `states/traces/vint_timing/build0162_vint_timing_debug.log`
- `states/traces/vint_timing/build0162_vint_timing_debug.cmd`
- `states/traces/vint_timing/parse_vint_debuglog.py`
- `states/traces/vint_timing/build0162_mame_stdout.log`
- `states/traces/vint_timing/build0162_mame_stderr.log`
- `states/traces/vint_timing/build0162_mame_exit.txt`

## Full-Run Summary

From `build0162_vint_timing_summary.txt`:

| Metric | Value |
|---|---:|
| External frame range sampled | `0..1499` |
| Event frame range | `0..1498` |
| `_vblank_service` entries (`0x700C2`) | `1404` |
| `_vblank_service` tail jumps (`0x70108`) | `1404` |
| Arcade VBlank entries (`0x3A208`) | `1404` |
| Arcade VBlank RTEs (`0x3A27E`) | `1404` |
| Frames with no `_vblank_service` after first service | `65` |
| Frames with entry but no RTE in same external frame | `15` |
| VDP register-1 writes | `2811` |
| VDP register-1 writes with VINT disabled | `0` |
| Longest full-run service chain | `64576` cycles at frame `55` |
| IPM>=6 pattern paired with missing service | `8` transition-frame instances |

The full run includes startup/title/story/gameplay transition clusters. Those clusters show delayed/coalesced service-chain events and should not be treated as steady gameplay frequency.

## Stable Gameplay Window

The stable gameplay/flickering-dot state `state=0002/0002/0006` appears by event frame `623`. The post-transition steady window used for gameplay classification was frames `637..1498`.

| Metric | Value |
|---|---:|
| Stable gameplay external frames sampled | `862` (`637..1498`) |
| `_vblank_service` entries | `863` |
| `_vblank_service` tail jumps | `864` |
| Arcade VBlank entries | `864` |
| Arcade VBlank RTEs | `871` |
| Frames with no `_vblank_service` | `0` |
| Frames with entry but no RTE | `0` |
| VDP register-1 writes | `1727` |
| Longest steady-window service chain | `9666` cycles at frame `891` |

Counts slightly above the number of frames are explained by boundary carryover/coalesced events from the preceding transition. The decisive facts are that every steady gameplay frame has `_vblank_service`, and no steady gameplay frame has `_vblank_service` without an arcade VBlank RTE before the next external frame.

## Classification

Primary classification for the stable gameplay/flickering-dot window: **A - Measurement artifact**.

Evidence:

- `_vblank_service` fires once per external frame in the steady gameplay window.
- The `_vblank_service -> arcade VBlank -> rte` chain completes before the next external frame in the steady gameplay window.
- No VDP register-1 write clears VINT enable bit 5.
- SR/IPM>=6 paired missing-service evidence appears only in transition clusters, not in the steady gameplay window.

## Non-Primary Observations

Startup and state-transition clusters do show delayed/coalesced service-chain events. Examples are visible around frames `34..55`, `262..278`, and `605..636`. These may merit a separate transition-timing investigation if they become user-visible or crash-relevant, but they do not explain a steady gameplay VINT frequency failure.

## Build Decision

No Build 0163 was produced.

Reason: the evidence does not prove a bounded VINT/interrupt ownership fix. D (VDP reg-1 clobber) is ruled out in this run, and E (steady SR/IPM block) is not supported. B/C-like transition clusters are not a proven exact fix locus and are outside the requested bounded-build criteria.

## Recommended Next Andy Task

Return to the PC090OJ sprite candidate/representation/SAT path or another already-proven gameplay rendering divergence. Do not spend Build 0163 on VINT service frequency unless a separate transition-specific symptom is being targeted.

Suggested prompt seed:

```text
Use Cody's Build 0162 VINT timing classification as settled input: steady gameplay frames 637..1498 have zero missing _vblank_service frames, zero entry-without-RTE frames, no VDP reg-1 VINT clobber, and longest steady chain 9666 cycles. Treat the prior 40% gameplay VINT frequency as a measurement artifact for steady gameplay. Continue with the PC090OJ candidate/representation/SAT divergence; do not modify VINT ownership unless new evidence targets transition clusters specifically.
```

## Open / Closed Issues Impact

Open issues touched: OPEN-017, OPEN-024, OPEN-001. New issues opened: NONE. Issues closed: NONE. Intentionally deferred: PC090OJ represent/candidate fix, collision, palettes, PC080SN/FG_SRC, player state, camera/scroll, D00298, transition-chain timing.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This resolves one runtime-measurement hypothesis for steady gameplay but does not establish a new durable bug mechanism.

## STOP

STOP triggered: NO. No bounded fix was proven, so the task stops at trace evidence and classification with no build.
