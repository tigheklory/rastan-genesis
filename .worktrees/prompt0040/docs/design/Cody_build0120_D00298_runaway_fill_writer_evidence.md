# Cody - Build 0120 D00298 / Runaway Fill Writer Evidence

**Date:** 2026-06-30
**Type:** Runtime evidence / debugger-watchpoint capture only
**Build:** 0120
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`
**SHA256:** `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No bookmark cycle. No state forcing, memory seeding, or diagnostic ROM.

## Phase 0

Read and applied `RULES.md`, `ARCHITECTURE.md`, current `AGENTS_LOG.md`, `docs/design/Cody_build0120_itempage_bg_strip_producer_route.md`, `docs/design/Andy_build0119_itempage_strip_destination_hv_write_design.md`, and `docs/design/Cody_post_itemscroll_runaway_fill_hv_counter_evidence.md`.

Classification: **EXTENDING** prior Build 0120 / OPEN-022 item-page strip-route evidence. OPEN-001 context. OPEN-015 context for crash-record reliability. No contradiction of current known findings was identified.

Address mapping was checked through `build/rastan-direct/address_map.json`:

- `runtime_genesis_pc 0x00055E5E` is a patched site mapped to `arcade_pc 0x00055C5E`.
- `runtime_genesis_pc 0x00055E7C` is `arcade_copy`, mapped to `arcade_pc 0x00055C7C`.
- `runtime_genesis_pc 0x00055E8E` is `arcade_copy`, mapped to `arcade_pc 0x00055C8E`.
- `runtime_genesis_pc 0x0007163C`, `0x00071672`, `0x00071818`, and `0x00071EEE` are `genesis_only` helper code, with no arcade PC mapping.
- `runtime_genesis_pc 0x000003D0` is in the preserved vector/crash-handler area, with no arcade PC mapping.

## Evidence Artifacts

Trace directory:

`states/traces/build_0120_D00298_runaway_fill_writer_20260630_120438/`

Primary files:

- `input_coin_start_manual_timing.lua`
- `input_run7.log`
- `build0120_d00298_runaway_target_pattern_after_hook.cmd`
- `debug.log` (trace-local debugger log for final targeted run)
- `native_trace.log` (large first-pass trace containing hook and routed `bg_fill` events)
- `run7_crash_record_ff6800_before_armed.bin`
- `run7_crash_record_ff6800_at_crash_common.bin`
- `run7_wram_fff700_before_armed.bin`
- `run7_wram_fff700_at_crash_common.bin`

The `.bin` dump files are MAME debugger ASCII hexdumps in this workflow.

## Input Path

The run used emulator input only, through the MAME Genesis driver input harness. No memory/state forcing was used.

Observed input path from `input_run7.log`:

- P1 A/coin pulse: frames `740..761`
- P1 Start hold: frames `960..1041`
- Post-start A/B/C pulses: frames `1120`, `1160`, `1200`, `1240`, `1280`, `1320`

The harness found controller fields for P1 Start/A/B/C and used those fields directly.

## Task A - Build 0120 Strip Route Status

**Hook reached: YES.**

The Build 0120 hook `genesistan_hook_itempage_strip_blit` was reached at `runtime_genesis_pc 0x0007163C` (`genesis_only`). Final targeted run:

```text
EVENT ARM_TARGET_PATTERN_AFTER_COL2_HOOK cyc=139525270 pc=07163E sr=2700 s0=0002 s2=0002 s4=0004 cnt=0000 ff10f6=0002 ff10f8=00C00008 ff1100=0000D31C ff1104=0002 sp=00FEFFDA
```

This proves the requested col-2 item-page strip state was reached with:

- `%a5@(0)/(2)/(4)/(44) = 0x0002 / 0x0002 / 0x0004 / 0x0000`
- `Genesis-WRAM 0x00FF10F6 = 0x0002`
- `Genesis-WRAM 0x00FF10F8 = 0x00C00008`
- `Genesis-WRAM 0x00FF1100 = 0x0000D31C`
- `Genesis-WRAM 0x00FF1104 = 0x0002`

**Old raw `HW_ADDRESS 0x00C00008` writer status: NOT HIT in this run.**

No old raw C-window write event fired before the later crash-common breakpoint. The old copied arcade writer at `runtime_genesis_pc 0x00055E7C` / `arcade_pc 0x00055C7C` remained dead-bodied by the Build 0120 entry hook for this path.

**Old `0x55E8E` ADDRESS ERROR status: NOT REPRODUCED.**

The Build 0120 hook route reached/passed the former item-page writer boundary. No old `runtime_genesis_pc 0x00055E8E` address-error boundary was observed.

**Routed `bg_fill` evidence: PRESENT.**

The large `native_trace.log` captured the hook entering and issuing routed `bg_fill` calls rather than raw PC080SN writes. First column sample:

```text
EVENT HOOK_ITEMPAGE_STRIP_BLIT_ENTRY cyc=138235654 pc=07163E ... s0=0002 s2=0002 s4=0004 cnt=0000 ff10f6=0000 ff10f8=00C00000 ff1100=0000D31C ff1104=0002
EVENT FIRST_ROUTED_BG_FILL_CALLPOINT cyc=138235822 pc=071674 ... a0=00C00000 d0=000204A6 ... a2=0000D31C ff10f6=0000 ff10f8=00C00000 ff1100=0000D31C ff1104=0002
```

For the final col-2 target run, the hook entry state proved the intended first routed destination would be `HW_ADDRESS 0x00C00008` with strip source `0x0000D31C` and attr `0x0002`. Static disassembly confirms `runtime_genesis_pc 0x00071672` is `moveq #1,%d1`, immediately before the `bg_fill` call, so the hook-side intended call shape is the one-cell routed fill path.

## Task B - D00298 Reproduction

**`HW_ADDRESS 0x00D00298` write reproduced in MAME: NO.**

The final targeted run installed an exact write-watchpoint on `HW_ADDRESS 0x00D00298`:

```text
wp 00D00298,2,w,,{ printf "EVENT D00298_WRITE_FIRST ..." ... }
```

No `EVENT D00298_WRITE_FIRST` occurred before the crash-common breakpoint. No D00298 dump files were produced.

Interpretation: the user-observed BlastEm/Nomad `D00298` strict-target failure remains valid out-of-band evidence, but this MAME scripted input path did **not** reproduce it before the later crash-common stop. Therefore this report does not identify a `D00298` writer PC.

## Task C - Runaway Fill / Pattern Evidence

**Runaway-like pattern present by crash-common: YES.**

At the post-hook col-2 arm point, the crash-record target region was mostly clean and the high-WRAM target window was zero-filled.

`run7_crash_record_ff6800_before_armed.bin`:

```text
FF6800:  0000 0000 0000 0000 0000 0000 0000 0000
FF6810:  0000 0000 0000 0000 0000 0000 0000 0005
FF6820:  A7DA 0005 B0B2 0000 0000 0000 0000 0000
```

`run7_wram_fff700_before_armed.bin`:

```text
FFF700:  0000 0000 0000 0000 0000 0000 0000 0000
FFF710:  0000 0000 0000 0000 0000 0000 0000 0000
```

At crash-common entry, both regions contained the repeating `2004 0003 A27E` pattern.

`run7_crash_record_ff6800_at_crash_common.bin`:

```text
FF6800:  2004 0003 A27E 2004 0003 A27E 2004 0003
FF6810:  A27E 2004 0003 A27E 2004 0003 A27E 2004
```

`run7_wram_fff700_at_crash_common.bin`:

```text
FFF700:  0003 A27E 2004 0003 A27E 2004 0003 A27E
FFF710:  2004 0003 A27E 2004 0003 A27E 2004 0003
```

**Exact first writer of the pattern: NOT CAPTURED.**

The final run armed target write-watchpoints after the col-2 hook on:

- `Genesis-WRAM 0x00FF6800..0x00FF699F`
- `Genesis-WRAM 0x00FFF700..0x00FFFEFF`

with filters for `0x2004`, `0x0003`, or `0xA27E`. Those target watchpoints did **not** fire before the crash-common breakpoint, even though the crash-common dumps show the target regions were patterned by then.

Earlier broader probes did catch writes near the lower helper/dirty area, but they do not prove the requested runaway writer:

```text
EVENT FIRST_WRITE_FF6600_6AFF_AFTER_HOOK cyc=143939205 pc=071EEE addr=00FF6748 size=16 data=00000000 ... s0=0002 s2=0002 s4=0005
EVENT PATTERN_WRITE_FF6600_6AFF_AFTER_HOOK cyc=143969166 pc=07181E addr=00FF6746 size=16 data=00000003 ... s0=0002 s2=0002 s4=0005
```

`runtime_genesis_pc 0x00071818` is a normal Genesis-only helper write to `Genesis-WRAM 0x00FF6744`; the debug event reports post-instruction PC `0x0007181E`. This is not a proven writer for the `0xFF6800` crash record or the `0xFFF700` high-WRAM pattern.

## Task D - Crash Record Reliability

**Crash record reliability: NOT RELIABLE in this run.**

Crash-common breakpoint event:

```text
EVENT CRASH_COMMON_ENTRY cyc=1447474386 pc=0003D2 sr=2610 sp=00FE6742 s0=0002 s2=0003 s4=0000 cnt=0000 ex=00 stacked_sr=A27E stacked_pc=20040003 fault=20040003 access=A27E
```

Because `Genesis-WRAM 0x00FF6800..` already contains the repeating `2004 0003 A27E` pattern by the time crash-common is reached, the on-record values reported from `0xFF6804`, `0xFF6806`, `0xFF6854`, and nearby fields are pattern-corrupted. This event is reliable only for the fact that the crash handler was entered and for the live state values sampled directly in the debugger expression. It is **not** reliable evidence for the real exception type, stacked PC, fault address, or access word.

## Task E - Flow Position

At the col-2 hook target, flow was still the item-page strip-copy path:

- `%a5@(0)/(2)/(4)/(44) = 0x0002 / 0x0002 / 0x0004 / 0x0000`
- `Genesis-WRAM 0x00FF10F8 = 0x00C00008`
- `Genesis-WRAM 0x00FF1100 = 0x0000D31C`
- `Genesis-WRAM 0x00FF1104 = 0x0002`

At crash-common entry, flow had advanced to:

- `%a5@(0)/(2)/(4)/(44) = 0x0002 / 0x0003 / 0x0000 / 0x0000`

This establishes that the observed corruption/crash was downstream of the Build 0120 item-page strip route, after the `2/2/4` strip-copy state and before or within the later `2/3/0` path. It does not by itself identify the transition writer or the runaway writer.

## Classification

- Build 0120 hook reached: **YES**.
- Old raw `0x00C00008` writer: **not hit** in this path.
- Old `0x55E8E` address-error boundary: **not reproduced**.
- `HW_ADDRESS 0x00D00298` write: **not reproduced** in this MAME scripted run.
- Runaway pattern in crash/high WRAM: **observed by crash-common**.
- First writer PC for the `2004 0003 A27E` pattern: **UNKNOWN / not captured**.
- Same writer as `D00298`: **UNKNOWN** because neither the D00298 write nor the first pattern writer was captured in this run.

## STOP Status

**STOP: YES - evidence-limited.**

The task successfully proves that the Build 0120 item-page strip hook is reached via legitimate input and that the old `0x00C00008` raw-writer / old `0x55E8E` failure is gone on that path. It also proves the crash-record/high-WRAM target regions are clean after the hook and contain the repeating pattern by crash-common.

However, the exact `D00298` write did not reproduce in MAME, and the exact first writer of the `2004 0003 A27E` pattern was not captured despite target watchpoints. No fix should be designed from this report alone.

## Non-Actions

No source, spec, tool, Makefile, ROM, build, invariant, bookmark, or issue-status changes were made. No `KNOWN_FINDINGS.md` update was made.

## Open / Closed Issues Impact

- OPEN-022 / KF-032: Build 0120 route evidence progressed; runtime hook reachability confirmed for the legitimate input path; downstream corruption remains unresolved.
- OPEN-001: context only.
- OPEN-015: context only; crash record is specifically unreliable here because the record is pattern-corrupted by handler entry.
- Issues opened: NONE.
- Issues closed: NONE.
- KNOWN_FINDINGS impact: Option A - no update from this evidence-limited trace.
