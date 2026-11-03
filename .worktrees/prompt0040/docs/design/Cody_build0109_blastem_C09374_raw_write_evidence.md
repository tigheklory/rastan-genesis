# Cody - Build 0109 BlastEm C09374 Raw-Write Evidence

**Date:** 2026-06-27
**Type:** Runtime evidence / static correlation only
**Build:** 0109
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0109.bin`
**ROM SHA256:** `a9905cd73837099f6ed548dda5b4ff66a1bb6be0911730e1bf9204472e934bc9`
**Scope:** Evidence only. No source, spec, tool, Makefile, ROM, build, bookmark, or invariant changes. No fix design or implementation.

## Phase 0

Read for this task:

- `RULES.md`
- `ARCHITECTURE.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- latest `AGENTS_LOG.md`
- relevant OPEN-018 / KF-032 / Build 0109 high-score fall-through context

Classification: **EXTENDING** OPEN-018 / KF-032 raw PC080SN-write evidence.

The validated Build 0109 `0x03AD06 rts -> nop` fall-through restore is not reopened here. The task only investigates the user-reported BlastEm/Nomad strict-target failure at `HW_ADDRESS 0x00C09374`.

## Evidence Artifacts

Trace directory:

`states/traces/build_0109_c09374_raw_write_evidence_20260627_205242/`

Files:

- `c09374_watch_exact.cmd`
- `mame_stdout.log`
- `mame_stderr.log`
- `native_debug_trace.log`

Runtime command used MAME Genesis driver with a write-watchpoint on `HW_ADDRESS 0x00C09374`. MAME is tolerant of the raw VDP-mirror write, so this capture identifies the writer that BlastEm/Nomad reject.

The run exited through the debugger after the watchpoint fired. No ROM diagnostics were inserted.

## Watchpoint Result

The exact C09374 write fired once:

```text
EVENT WP_C09374 cyc=55220228 pc=03C62E addr=00C09374 data=0000 mem=0000
 d0=00000003 d1=00000000 d2=00000000 d3=00000030 d4=0000000C
 d5=00000000 d6=00000000 d7=00000000
 a0=0003C654 a1=00C09374 a2=0010C157 a3=00050082 a4=00000000
 a5=00FF0000 a6=00000000 sp=00FEFFE2 sr=2704
 s0=0000 s2=0001 s4=0002 cnt=0000
 stack0=0003B904 stack4=00000000 stack8=00000005
```

MAME reports the watchpoint action after the faulting instruction. The actual writer is the preceding instruction at `runtime_genesis_pc 0x0003C62A`.

Generated disassembly:

```asm
3c5fe: 3e3c 0000       movew #0,%d7
3c602: 3400            movew %d0,%d2
3c614: 3268 0002       moveaw %a0@(2),%a1
3c618: d3fc 00c0 8000  addal #0x00c08000,%a1
3c62a: 32c7            movew %d7,%a1@+
3c62e: 0c01 003f       cmpib #63,%d1
```

Writer bytes at `genesis_rom_offset 0x0003C62A`: `32 C7`.

Observable fact: `runtime_genesis_pc 0x0003C62A` writes word `0x0000` to `HW_ADDRESS 0x00C09374` through `%a1@+`.

## Address Mapping Discipline

All code correlations below were checked through `build/rastan-direct/address_map.json`.

| Runtime Genesis PC | Address-map kind | Arcade PC |
|---|---|---|
| `0x0003C62A` | `arcade_copy` | `0x0003C42A` |
| `0x0003C62E` | `arcade_copy` | `0x0003C42E` |
| `0x0003AD08` | `arcade_copy` | `0x0003AB08` |
| `0x0003B05A` | `arcade_copy` | `0x0003AE5A` |
| `0x0003B064` | `arcade_copy` | `0x0003AE64` |
| `0x0003B070` | `arcade_copy` | `0x0003AE70` |
| `0x0003B080` | `arcade_copy` | `0x0003AE80` |
| `0x0003AF44` | `patched_site` | `0x0003AD44` |
| `0x0003AD0C` | `arcade_copy` | `0x0003AB0C` |
| `0x0003B8BE` | `arcade_copy` | `0x0003B6BE` |
| `0x0003B8F8` | `arcade_copy` | `0x0003B6F8` |
| `0x0003C5FE` | `arcade_copy` | `0x0003C3FE` |

No arithmetic offset was used as authority.

## Call Chain Context

The high-score transition and clear/fill path did execute before the C09374 write:

```text
STORY_EXPIRY_HANDLER_03AD00: 1
HIGH_INIT_CLEAR_CALL_03AD08: 1
HIGH_CLEAR_WRAPPER_03B05A: 3
CLEAR_ENTRY_03B064: 3
CLEAR_BG_CALL_03B070: 3
CLEAR_FG_CALL_03B080: 3
DISPATCH_03AF44: 15
HIGH_SCORE_INIT_03AD0C: 1
WP_C09374: 1
```

The C09374 watchpoint occurred after `HIGH_SCORE_INIT_03AD0C`, not during the clear/fill helper chain. The stack at the watchpoint contains `stack0=0x0003B904`, which is the return address after the call at `runtime_genesis_pc 0x0003B900` into the helper at `runtime_genesis_pc 0x0003C5FE`.

Observed path:

```text
0x03AD00 story-expiry handler
  -> 0x03AD08 high-score clear call
  -> 0x03B05A / 0x03B064 / 0x03B070 / 0x03B080 clear helper path
  -> 0x03AF44 routed dispatch path
  -> 0x03AD0C high-score init
  -> 0x03B8BE
  -> 0x03B8F8
  -> 0x03B900 bsr 0x03C5FE
  -> 0x03C62A move.w %d7,(%a1)+ writes HW_ADDRESS 0x00C09374
```

## Target Decode

`HW_ADDRESS 0x00C09374` is in the PC080SN FG C-window range `0x00C08000..0x00C0BFFF` and aliases Genesis VDP port space on hardware.

For the actual writer, the meaningful base is the whole FG C-window base `HW_ADDRESS 0x00C08000`, because the routine explicitly does:

```asm
3c618: addal #0x00c08000,%a1
```

Derived target position relative to FG base:

- FG offset: `0x1374`
- word index: `0x09BA`
- this is the code-word lane of an attr/code pair whose attr word would be at `0x00C09372`
- cell index: `(0x1374 - 2) / 4 = 0x04DC`
- row: `19`
- column: `28`

Interpretation: this is a raw high-score/FG text producer write to a PC080SN FG cell, not a direct call to the translated clear/fill helper.

## Known-vs-New Comparison

This site does **not** match the already known OPEN-018 raw immediate Class A sites:

- `0x0003ACEA`
- `0x0003A550`
- `0x0003A8FE`
- `0x0003A908`

It does **not** match the OPEN-018 remaining register-absolute sites:

- `0x0003A92A`
- `0x0003D24C`

It does **not** match the OPEN-018 remaining producer-loop raw writes explicitly listed in prior evidence:

- `0x0003B3CC`
- `0x0003B7F6`
- `0x0003B7F8`

It also does **not** identify the clear/fill helper as the offending writer. The clear/fill chain fires earlier and routes through the existing dispatch path; the C09374 hit is after high-score init, inside the `0x03C5FE` helper body.

## Existing Routing Context

The repo already has staged-routing machinery for related classes:

- `genesistan_hook_3ad44_dispatch` routes selected tilemap clear/fill callers through staging.
- `genesistan_hook_tilemap_fg_fill` and `genesistan_hook_tilemap_bg_fill` stage fill output.
- `genesistan_hook_cwindow_clear` clears staged BG/FG buffers.
- Existing `genesistan_hook_text_writer_*` helpers route several text writers into FG staging.

Observable fact: `runtime_genesis_pc 0x0003C62A` is still copied arcade code and writes directly to `HW_ADDRESS 0x00C09374`; it is not currently routed through that staging machinery.

## Classification

**B - NEW raw PC080SN write exposed by Build 0109**, with an important refinement:

- It is new relative to the explicit OPEN-018 deferred/raw-site list checked above.
- It is a raw copied-arcade PC080SN FG C-window write and belongs to the same broad KF-032 / OPEN-018 class.
- It is **not** a clear/fill write. The prompt's clear/fill hypothesis is refuted by the trace timing and call chain: clear/fill ran earlier; the C09374 hit is in the high-score init/text producer helper after `0x03AD0C`.

So the narrow result is: **new raw high-score FG producer write, not clear/fill**.

## What This Does Not Prove

- It does not prove the correct fix shape.
- It does not prove the full extent of the `0x03C5FE` helper's raw write coverage.
- It does not reopen the Build 0109 `0x03AD06` fall-through fix.
- It does not analyze the visual high-score table contents, zero/blank high-score data, sprites, window layer, HUD, or unrelated glyph/punctuation paths.

## Recommended Follow-up Boundary

A follow-up design/implementation task should treat `runtime_genesis_pc 0x0003C62A` / `arcade_pc 0x0003C42A` as a newly confirmed raw high-score FG producer write and decide how to route the relevant producer path through the existing FG staging/text-writer machinery.

That is a recommendation for scoping only, not a fix design in this evidence task.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-018: touched and extended by evidence. The site is a new member of the raw PC080SN-write class, but no issue was closed and no issue file was edited in this task.
- OPEN-001: context only.
- OPEN-015: not touched.
- KNOWN_FINDINGS: no update recommended from this evidence-only task; KF-032 already captures the broad raw PC080SN-write hazard class.

## STOP Status

STOP triggered: **NO** for evidence capture.

Scope limitation recorded: this task identifies and classifies the offending raw write only; it does not design or implement routing.
