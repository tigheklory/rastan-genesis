# Cody - Build 0097 BlastEm HV Counter Write Diagnostic

**Date:** 2026-06-24  
**Type:** Runtime diagnostic + conditional-fix decision  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0097.bin`  
**ROM SHA256:** `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`  
**Scope:** Diagnostic only. No source/spec/tool/Makefile/ROM/invariant edits. No build. No bookmark cycle. No OPEN-015 work. Build 0097 display-origin fix intentionally untouched.

## Phase 0

Classification: **EXTENDING** (OPEN-017 / OPEN-005 context). Relevant priors loaded: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, `AGENTS_LOG.md` latest entries, `docs/design/Cody_build_0097_display_origin_bias_impl.md`, and `docs/design/Andy_build_0096_placement_offset_attribution.md`.

Architecture compliance: **PASS**. This task treats arcade code as the program and Genesis code as helper/hardware service only. No diagnostic ROM or scaffold patch was added.

Contradiction detected: **NO**.

## Local BlastEm Availability

A local BlastEm executable was not found in this environment via `command -v blastem`, `command -v blastem.exe`, or a bounded filesystem search. Therefore the reported BlastEm fatal could not be reproduced directly here.

## Static Scan for Literal `0x00C00008`

Build 0097 contains two literal `0x00C00008` references in executable code. Disassembly resolves both as **reads** from the HV counter into WRAM audit state, not writes to the HV counter:

```asm
7186c: 33f9 00c0 0008 00ff 678c  movew 0x00c00008,0x00ff678c
71bc6: 33f9 00c0 0008 00ff 678c  movew 0x00c00008,0x00ff678c
```

`0x00FF678C` is `audit_guard_vcount`. The source-level sites are `apps/rastan-direct/src/pc090oj_hooks.s` lines 420 and 804. These are audit-guard readbacks of the VDP HV counter.

Result: **no direct/literal HV-counter write was found statically.**

## Address Mapping Discipline

Mapping was checked through `build/rastan-direct/address_map.json`, not arithmetic. The relevant JSON segment maps arcade `0x03AD44..0x03AD4C` to Genesis patched site `0x03AF44..0x03AF4C` and records replacement bytes:

```text
4EB9{symbol:genesistan_hook_3ad44_dispatch}4E75
```

The generated symbol table resolves `genesistan_hook_3ad44_dispatch = 0x000717D8`.

This matters because original arcade runtime evidence shows the `0x03AD44` fill primitive can write PC080SN tilemap addresses `0x00C00008` and `0x00C0000A`. In Build 0097, that exact arcade primitive is JSON-mapped to the Genesis dispatch helper rather than left as a raw VDP write.

## Runtime Watchpoint Evidence

### Clean event-only MAME run

Trace directory:

`states/traces/build_0097_blastem_hv_counter_write_20260624_212731/`

Command script:

`states/traces/build_0097_blastem_hv_counter_write_20260624_212731/mame_hv_counter_write_eventonly.cmd`

Watchpoint:

```text
wp c00008,8,w,,{ printf "EVENT HV_COUNTER_WRITE ..." ; quit }
```

Result:

- MAME ran Build 0097 for 9 seconds.
- No `EVENT HV_COUNTER_WRITE` line was produced.
- No crash-handler halt event was produced in that window.

This does **not** prove BlastEm cannot hit the fatal path. It does prove that the local no-input MAME Genesis-driver path did not reproduce a write to `0x00C00008..0x00C0000F`.

### Oversized first attempt

Trace directory:

`states/traces/build_0097_blastem_hv_counter_write_20260624_212521/`

This first attempt accidentally enabled full instruction tracing with MAME's `trace` command, producing a large `native_debug_trace.log`. Grep over that trace found no `HV_COUNTER_WRITE` or `CRASH_HALT` event. The artifact is retained as generated diagnostic evidence but should not be treated as the clean primary trace; the clean event-only run above is the primary result.

### Read/write split attempt

Trace directory:

`states/traces/build_0097_blastem_hv_counter_readwrite_20260624_212842/`

A read/write split probe was attempted, but the debugger wrapper did not exit cleanly and was manually interrupted. It is not used as decisive evidence.

## Known Arcade Runtime Context

Existing original-arcade runtime evidence contains these events:

```text
states/traces/original_arcade_attract_page_replacement_20260623_171701/native_events.log
EVENT BG_PC080SN_WRITE ... pc=03AD48 addr=00C00008 ... data=00000000 ... a0=00C00008
EVENT BG_PC080SN_WRITE ... pc=03AD48 addr=00C0000A ... data=00000020 ... a0=00C00008
```

Per the existing MAME watchpoint callback convention, the reported `pc=0x03AD48` is the post-instruction callback PC for the `0x03AD44` fill primitive. In original arcade runtime, these are valid PC080SN tilemap writes. In Genesis Build 0097, the JSON-mapped `0x03AF44` patched site dispatches to `genesistan_hook_3ad44_dispatch`, whose tilemap branch covers `A0 in [0x00C00000,0x00C10000)` and routes tilemap work into staging rather than raw VDP/HV space.

## Classification

Resolved classification: **E - unknown / exact BlastEm write site not captured**.

Why not A-D yet:

- **A native helper/startup offset bug:** not proven. The two literal HV references are native helper audit reads, not writes.
- **B translated arcade write hitting HV:** plausible historically for original arcade `0x03AD44` writes, but Build 0097's JSON-mapped patched site should intercept that path, and the MAME write watchpoint did not fire.
- **C bad pointer/corrupted address register:** not proven; no runtime write event captured.
- **D DMA/control-port setup bug:** not proven; no control/DMA write sequence was tied to the BlastEm fatal.
- **E unknown:** selected because the exact first BlastEm-side write PC/instruction/register state remains unavailable.

## Conditional Fix Decision

No fix was applied.

Reason: the prompt allowed a fix only if the exact site and correct behavior were unambiguous, local, and not a catch-all sanitizer. That bar is not met:

- BlastEm is not available locally to capture the actual fatal PC.
- MAME did not reproduce a write to `0x00C00008..0x00C0000F` in the no-input window.
- Static scan found no direct HV writes.
- The known original arcade `0x03AD44 -> 0x00C00008` PC080SN write path is already mapped to the Build 0097 dispatch helper.

A patch here would be speculative and would risk masking the real failure.

## Recommended Next Evidence Step

Capture the BlastEm-side halt PC/register state directly. The required minimum evidence is:

- exact fatal address reported by BlastEm,
- Genesis PC at halt,
- current instruction bytes/disassembly,
- effective address source registers if register-indirect,
- whether the access is a true write or a strict-emulator failure on read/mirror access.

If BlastEm cannot expose watchpoints, use a short instruction trace ending at the fatal dialog or a debugger screenshot with PC/registers. Once the exact PC is known, re-run the A-E classification and only then decide whether a local helper correction is safe.

## Non-Actions

- Source changes: NO
- Spec changes: NO
- Tool changes: NO
- Makefile changes: NO
- ROM/invariant changes: NO
- Build run: NO
- Bookmark cycle: NO
- OPEN-015 work: NO
- Build 0097 display-origin code touched: NO
- Issues opened/closed: NO

## OPEN / KNOWN_FINDINGS Impact

- OPEN-017: touched as context; not closed.
- OPEN-005: touched as historical HV-counter context; not closed.
- OPEN-001: context only.
- OPEN-015: not touched.
- KNOWN_FINDINGS impact: Option A - no update. No durable root cause was proven.

## STOP

STOP triggered: **YES**.

Reason: the exact BlastEm first-write PC/instruction was not captured, and MAME did not reproduce the HV-counter write. Implementation is not safely placeable from current evidence.
