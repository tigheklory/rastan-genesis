# Cody - Post-Item-Scroll Runaway RAM Fill / HV Counter Write Evidence

**Date:** 2026-06-29  
**Type:** Runtime evidence / debugger-watchpoint capture only  
**Build:** 0119  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0119.bin`  
**SHA256:** `e1d74a2514a2142a1ad56b54bedc49c6d39570ee5d5ca9da1bb7c9f9ce8d46c4`  
**Trace directory:** `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/`  
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No diagnostic ROM. No bookmark cycle. No fix design or implementation.

## Phase 0

Read and applied:

- `RULES.md`
- `ARCHITECTURE.md`
- latest relevant `AGENTS_LOG.md`
- `docs/design/Andy_build0118_20480013_itempage_pointer_field_correctness_design.md`
- `docs/design/Cody_build0119_itempage_strip_populator_pointer_relocation.md`

Classification: **EXTENDING** KF-028 / OPEN-016 runtime-pointer-relocation evidence. OPEN-001 context. OPEN-015 caveat applied: no formatted exception screen values are used.

No contradiction detected. Architecture compliance maintained: the arcade code remains the program; the Genesis side is not modified.

## Evidence Artifacts

Primary artifacts:

- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/runaway_pattern_eventonly_120s.cmd`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/runaway_pattern_eventonly_120s.out`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/hv_precise_bp.cmd`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/hv_precise_bp_trace.log`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/prior2_wram_ff10f0_after_strip_hook_3951c.bin`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/prior2_wram_ff10f0_after_old_read_d31c.bin`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/wram_ff0000_at_hv_prewrite.bin`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/wram_ff10f0_at_hv_prewrite.bin`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/wram_ff6100_at_hv_prewrite.bin`
- `states/traces/build_0119_post_itemscroll_runaway_hv_evidence_20260629_215725/wram_ff6800_at_hv_prewrite.bin`

Note: two large interrupted native trace files also exist in the trace directory from attempted whole-run instruction tracing. They are not used as primary evidence because a targeted breakpoint trace produced the same HV boundary more cleanly.

## Task A - Prior Build 0119 Fix Held

The Build 0119 item-page strip populator hook still performs the intended pointer relocation for the former Build 0118 crash case.

At hook completion for `Genesis-WRAM 0x00FF10FC == 0x0003951C`:

```text
FF10F0:  0000 0000 0000 0000 0000 0000 0003 951C
FF1100:  0000 D31C 0002 0000 0000 0000 0000 0000
```

Proven facts:

- raw descriptor pointer `0x0003951C` is still the walker value in `Genesis-WRAM 0x00FF10FC`.
- JSON-derived mapped descriptor is `genesis_rom_offset 0x0003971C` (from prior Build 0119 validation and address-map discipline).
- raw strip pointer `0x0000D11C` is relocated to mapped strip pointer `0x0000D31C`.
- `Genesis-WRAM 0x00FF1104 = 0x0002`.
- `Genesis-WRAM 0x00FF1100 = 0x0000D31C`.

At the old fault boundary after `runtime_genesis_pc 0x00055E8E`:

```text
FF10F0:  0000 0000 0000 000F 00C0 003C 0003 951C
FF1100:  0000 D31C 0002 0000 0000 0000 0000 0000
```

`runtime_genesis_pc 0x00055E90` was reached repeatedly with `Genesis-WRAM 0x00FF1100 = 0x0000D31C`, so the old `0x55E8E` ADDRESS ERROR is gone in this run.

## Task B - Runaway RAM Fill Pattern

The user-observed Exodus RAM fill pattern was:

```text
2004 0003 A27E 2004 0003 A27E ...
```

A bounded 120-second MAME no-input run watched representative Genesis-WRAM regions for writes of `0x2004`, `0x0003`, or `0xA27E`:

- `Genesis-WRAM 0x00FFF900..0x00FFF91F`
- `Genesis-WRAM 0x00FF6800..0x00FF687F`
- `Genesis-WRAM 0x00FF6100..0x00FF621F`

Result: **not reproduced in this MAME evidence pass.** No `EVENTONLY_PATTERN_HIT_*` dump files were produced, and no crash-handler breakpoint fired during that bounded run.

A heavier interrupted trace did prove the prior hook and old boundary were reached, but it did not reach any `RUNAWAY_PATTERN_*` event before being stopped:

- `PRIOR_FIX_HOOK_HELD`: 1 event
- `OLD_55E8E_BOUNDARY_PASSED`: 1024 events
- `RUNAWAY_PATTERN_*`: no pattern-hit event (only the trace-armed marker)
- `CRASH_COMMON_ENTRY`: 0 events

Therefore the runaway writer PC, write direction, and repeating pattern source are **not proven by this MAME run**. The Exodus-observed fill remains user-observed/out-of-band relative to this evidence bundle.

## Task C - HV Counter Write

The first confirmed write to the HV-counter/VDP-port alias window is from the item-page strip copy loop.

Precise targeted breakpoint evidence:

```text
EVENT HV_PREWRITE_55E7C cyc=337261218 pc=055E7E target_a0=00C00008 src_a1=00FF1104 src_word=0002 sr=2704 d0=0003951C d1=00002048 d2=00000000 d3=00000000 d4=0000000C d5=00000000 d6=00000000 d7=000007E2 a0=00C00008 a1=00FF1104 a2=0000D31C a3=00FF1100 a4=0003971C a5=00FF0000 a6=0000DAFE sp=00FEFFD6 s0=0002 s2=0002 s4=0004 cnt=0000 ff10fc=0003951C ff1100=0000D31C ff1104=0002
```

Disassembly around the writer:

```asm
55e5e: moveal %a5@(4344),%a0      ; destination pointer, from Genesis-WRAM 0x00FF10F8
55e62: moveal #0x00FF1104,%a1     ; header/source word slot
55e68: moveal #0x00FF1100,%a3     ; strip pointer slot
55e6e: moveal %a3@,%a2            ; a2 = 0x0000D31C
55e70: bsrw 0x55e7a
55e7a: clrw %d2
55e7c: movew %a1@,%a0@+           ; actual write: 0x0002 -> 0x00C00008
55e7e: movew %d2,%d7              ; MAME/live monitors report post-write PC here
55e80: lslw #5,%d7
55e82: movew %a5@(4342),%d0
55e86: lslw #1,%d0
55e88: addw %d0,%d7
55e8a: lea %a2@(0,%d7:w),%a6
55e8e: movew %a6@,%d0
55e90: movew %d0,%a0@
```

Address labels:

- **Actual writer instruction:** `runtime_genesis_pc 0x00055E7C: movew %a1@,%a0@+`.
- **MAME post-write PC:** `runtime_genesis_pc 0x00055E7E`.
- **Live monitor corroboration:** earlier run recorded `last_pc=055E80`, `last_addr=C00008`, `last_data=0002`; this is also a post-write/later-PC observation, not the faulting instruction address.
- **Target:** `HW_ADDRESS 0x00C00008`.
- **Value:** `0x0002` from `Genesis-WRAM 0x00FF1104`.
- **Segment mapping:** `runtime_genesis_pc 0x00055E7C -> arcade_pc 0x00055C7C`, `kind=arcade_copy`, `source=whole_maincpu_copy`, via `build/rastan-direct/address_map.json`.

Registers at the pre-write breakpoint:

```text
D0=0003951C D1=00002048 D2=00000000 D3=00000000
D4=0000000C D5=00000000 D6=00000000 D7=000007E2
A0=00C00008 A1=00FF1104 A2=0000D31C A3=00FF1100
A4=0003971C A5=00FF0000 A6=0000DAFE SP=00FEFFD6
SR=2704
```

State at the HV pre-write:

```text
%a5@(0)  / Genesis-WRAM 0x00FF0000 = 0x0002
%a5@(2)  / Genesis-WRAM 0x00FF0002 = 0x0002
%a5@(4)  / Genesis-WRAM 0x00FF0004 = 0x0004
%a5@(44) / Genesis-WRAM 0x00FF002C = 0x0000
```

Relevant item slots at the HV pre-write:

```text
FF10F0:  0000 0000 0000 0002 00C0 0008 0003 951C
FF1100:  0000 D31C 0002 0000 0000 0000 0000 0000
```

Interpretation from observable state:

- `Genesis-WRAM 0x00FF10F8 = 0x00C00008`, so the copied arcade strip writer's destination pointer has entered the Genesis VDP/HV alias region.
- The write is not from Genesis VBlank service code. It is copied arcade item-page code writing through `%a0`.
- The write is a word write, and this routine normally advances `%a0` with `a0@+` plus later row-stride adjustment.

## Task D - Flow Position

At the HV write, the game is still in item-page state:

```text
state = %a5@(0)/%a5@(2)/%a5@(4) = 0x0002 / 0x0002 / 0x0004
counter %a5@(44) = 0x0000
```

Evidence does **not** show that item scroll fully finished or that control left `2/2/4` before the HV write. The faulting write occurs inside the item-page strip consumer/copy path (`runtime_genesis_pc 0x00055E5E..0x00055EA0`), not after a confirmed transition to gameplay/demo/attract cleanup.

This narrows the BlastEm/Nomad HV-counter failure to an item-page strip destination-pointer problem: the consumer copies header/strip words to a destination pointer that has become `HW_ADDRESS 0x00C00008`.

## Task E - Crash Record Reliability

Crash-record region before runaway / at prior hook:

```text
FF6800:  0000 0000 0000 0000 0000 0000 0000 0000
FF6810:  0000 0000 0000 0000 0000 0000 0000 0005
FF6820:  A7DA 0005 B0B2 0000 0000 0000 0000 0000
```

Crash-record region at the HV pre-write:

```text
FF6800:  0000 0000 0000 0000 0000 0000 0000 0000
FF6810:  0000 0000 0000 0000 0000 0000 0000 0005
FF6820:  A7DA 0005 B0B2 0000 0000 0000 0000 0000
```

The `0x00FF6800..0x00FF6880` region is unchanged between the prior hook capture and HV pre-write capture in MAME. However, because the Exodus-observed runaway fill was not reproduced in this MAME pass, this task cannot prove the post-runaway crash-record state. If a later run reproduces the `2004 0003 A27E` fill reaching `0x00FF6800`, the crash record should be treated as unreliable unless captured before that overwrite.

## Classification

**Proven by this task:** Build 0119's prior pointer-relocation fix holds, and the old `0x55E8E` ADDRESS ERROR is gone. The first confirmed HV-counter write is produced by copied arcade item-page strip code at `runtime_genesis_pc 0x00055E7C` (`arcade_pc 0x00055C7C`) because `%a0`/`Genesis-WRAM 0x00FF10F8` equals `HW_ADDRESS 0x00C00008` while the code writes `0x0002` from `Genesis-WRAM 0x00FF1104`.

**Not proven / not reproduced here:** the Exodus-style descending RAM fill pattern `2004 0003 A27E` and its writer PC. The bounded MAME watchpoint pass did not catch that pattern in the representative regions.

## Non-Actions

No source, spec, tool, Makefile, ROM, invariant, build artifact, diagnostic ROM, or bookmark artifact was modified. No fix was designed or implemented. No issue was opened or closed.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-016 / KF-028: progressed with a new downstream item-page destination-pointer/HV-port boundary.
- OPEN-001: context only.
- OPEN-015: context; formatted exception output not used.
- KNOWN_FINDINGS impact: Option A for this evidence task; no canonical update applied.

## STOP

STOP triggered: **NO** for architecture/scope. Evidence limitation recorded: the user-observed runaway RAM-fill pattern was not reproduced in the bounded MAME runs, so its writer remains unresolved by this report.
