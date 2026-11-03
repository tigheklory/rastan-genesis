# Cody - Build 0115 Gameplay/Demo Crash + PC080SN Layout Evidence

**Date:** 2026-06-29  
**Type:** Runtime evidence / analysis only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0115.bin`  
**ROM SHA256:** `5af34e440a79f2d9d447a767592ea903d026edea3f174a97d446b03ed23026e3`  
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build/invariant changes. No bookmark cycle. No implementation or fix design.

## Phase 0

Classification: **EXTENDING**. Architecture guardrails loaded from `RULES.md` and `ARCHITECTURE.md`: arcade code is the program; Genesis-side code is helper/opcode-replacement only. Relevant priors loaded from `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, and latest-first `AGENTS_LOG.md` context.

Relevant priors/context:

- `KF-010`: BG/FG staging and full-plane VDP commit model.
- `KF-032`: raw PC080SN writes must route through staging.
- `KF-036`: mapped work-RAM base lesson.
- `KF-038`: Build 0115 item-description row aliasing in the current 32-row Genesis BG staging model.
- `OPEN-001`: rendering remains active.
- `OPEN-015`: crash-handler screen values are unreliable; WRAM crash record is the trusted crash source.
- `OPEN-022` / `OPEN-023` / `OPEN-024`: context for item-description/high-score/rendering follow-up.

No contradiction was detected. The task remained evidence-only.

## Evidence Artifacts

Trace directory:

`states/traces/build_0115_gameplay_demo_crash_pc080sn_20260629_111638/`

Artifacts:

- `build0115_gameplay_demo_crash_pc080sn.cmd`
- `native_debug_trace.log`
- `native_events.log`
- `crash_record_ff6800.bin`
- `stack_region_feff00.bin`
- `wram_ff0000_at_crash.bin`
- `staged_bg_at_crash.bin`
- `staged_fg_at_crash.bin`
- `mame_stdout_2.txt`
- `mame_stderr_2.txt`

Run note: the usable MAME run completed the debugger capture and emitted crash artifacts, but the outer `timeout` wrapper returned `124`; `mame_stderr_2.txt` says `Exited via the debugger`. The captured debugger events and dumps are used as evidence.

## Result Summary

The requested gameplay/demo crash was **not reproduced** in this no-input MAME trace.

The run crashed while still in the item-description cleanup/state path:

- `%a5@(0) = 0x0002`
- `%a5@(2) = 0x0002`
- `%a5@(4) = 0x0004`
- `%a5@(44) = 0x0000`

This is the item-page state family the prompt explicitly asked to distinguish from gameplay/demo. The captured crash is the same copied-arcade pointer/table crash site as the prior item-description evidence, not new gameplay/demo evidence.

## Part A - Crash Identity

### Exception

Reliable crash source: WRAM crash record / debugger-side events, not the on-screen crash fields (`OPEN-015`).

Captured reliable fields:

- Exception type: `0x03` = ADDRESS ERROR
- Stacked SR: `0x2700`
- Stacked PC: `runtime_genesis_pc 0x00055B1C`
- Faulting instruction address: `runtime_genesis_pc 0x00055B1A`
- Instruction word: `0x34D4`
- Fault address: `0x0000000F`
- Access/frame word: `0x34D5`

The disassembly at `runtime_genesis_pc 0x00055B1A` is:

```asm
55b1a: 34d4    movew %a4@,%a2@+
```

Interpretation: the fault is an odd-address word access through `%a4 = 0x0000000F`. The instruction is in copied arcade code, not in a Genesis helper.

### Address Mapping Discipline

Mapping was checked through `build/rastan-direct/address_map.json`.

`runtime_genesis_pc 0x00055B1A` is inside this exact JSON segment:

```json
{
  "genesis_start": "0x054A64",
  "genesis_end_exclusive": "0x055B68",
  "kind": "arcade_copy",
  "arcade_start": "0x054864",
  "arcade_end_exclusive": "0x055968",
  "identity_offset": 512
}
```

By the JSON segment-relative mapping, `runtime_genesis_pc 0x00055B1A` corresponds to `arcade_pc 0x0005591A`. `runtime_genesis_pc 0x00055B1C` corresponds to `arcade_pc 0x0005591C`.

No arithmetic offset was used as standalone authority.

### State At Crash

From `CRASH_HALT` and `wram_ff0000_at_crash.bin`:

```text
EVENT CRASH_HALT ... crash_sr=2700 crash_pc=00055B1C fault=0000000F access=34D5 s0=0002 s2=0002 s4=0004 cnt=0000 ...
```

Work RAM state at crash:

- `WRAM 0xFF0000 = 0x0002`
- `WRAM 0xFF0002 = 0x0002`
- `WRAM 0xFF0004 = 0x0004`
- `WRAM 0xFF002C = 0x0000`

Reliable register values relevant to the fault:

- `%a2 = 0x0010D080`
- `%a3 = 0x00059B50`
- `%a4 = 0x0000000F`
- `%a5 = 0x00FF0000`
- `%a6 = 0x00FF0298`

Per `OPEN-015`, saved `D0-D5/A0/A1` values are not treated as true at-fault registers.

### Stack Breadcrumbs

`stack_region_feff00.bin` begins with the exception frame and nearby return breadcrumbs:

```text
FEFFD0: 34D5 0000 000F 34D4 2700 0005 5B1C 0005
FEFFE0: 05E0 0005 040A 0004 551C 0003 A85C 0003
FEFFF0: A274 2009 0003 A1AC 0003 B296 0000 0226
```

Breadcrumbs include `0x55B1C`, `0x505E0`, `0x5040A`, `0x4551C`, `0x3A85C`, `0x3A274`, `0x3A1AC`, and `0x3B296`. These are recorded as stack evidence, not as a fully proven call chain.

### Classification

For the requested gameplay/demo crash: **G - Not enough evidence / not reproduced.**

Reason: the trace never reached a gameplay/demo state before crashing. It reproduced the known item-description cleanup crash state.

For the captured crash itself: **E - copied-arcade pointer/table logic**, same observed site/mechanism family as the prior item-page `0x55B1A` crash. The fault is in copied arcade code and is not evidence of Genesis helper rebasing, VDP commit failure, or the Build 0115 text-writer dispatcher.

## Part B - PC080SN Layout Evidence Before Crash

### Event Counts

Reduced event counts from `native_events.log`:

```text
A5_COUNTER_WRITE: 532
A5_STATE_WRITE: 21
BG_FILL_ENTRY_70588: 573
CWINDOW_CLEAR_ENTRY_7136C: 1
FG_FILL_ENTRY_7065E: 21
PC090OJ_HELPER_71CE2: 1
RAW_BG_CWINDOW_WRITE: 6288
STAGED_SCROLL_WRITE: 116
TEXTWRITER_DISPATCH_714C8: 1
VDP_SCROLL_COMMIT_701F0: 2563
CRASH_COMMON_ENTRY: 1
CRASH_HALT: 1
```

Important caveat: the `RAW_BG_CWINDOW_WRITE` watchpoint label caught writes to Genesis VDP port addresses `0xC00000..0xC00006` from low-ROM boot/crash/VDP-service paths. It did not capture non-port raw copied-arcade C-window addresses such as `0xC00828` before the crash. These raw events are not treated as gameplay PC080SN tilemap writes.

### PC080SN BG/FG Helper Activity

BG staging helper entries were observed before the crash. They include item-description activity, not gameplay/demo tilemap activity.

Representative item-description destination range observed through the BG helper:

- Starts around `HW_ADDRESS 0x00C00828`
- Extends through observed item-page destinations around `HW_ADDRESS 0x00C03E28`

This is consistent with the known long item-description BG C-window span recorded in `KF-038`.

FG helper activity was also observed, but it belongs to title/story/high-score era or clearing paths before the item crash. Representative destinations include:

- `HW_ADDRESS 0x00C09170`
- `HW_ADDRESS 0x00C09374`
- `HW_ADDRESS 0x00C09B7C`
- `HW_ADDRESS 0x00C08100`

No gameplay/demo FG layout evidence was reached.

### Scroll Evidence

`STAGED_SCROLL_WRITE` events occurred, and the VBlank scroll commit path was active. However, item-page scroll values stayed zero in the captured crash window:

- `staged_scroll_x_bg = 0`
- `staged_scroll_x_fg = 0`
- `staged_scroll_y_bg = 0`
- `staged_scroll_y_fg = 0`

At crash halt:

```text
x_bg=0000 x_fg=0000 y_bg=0000 y_fg=0000
```

No raw PC080SN X/Y scroll writes were observed in the event counts before this crash.

### Layout Conclusion

The trace does **not** establish gameplay/demo PC080SN layout behavior. It confirms that the run reached the known item-description long-BG-row behavior before crashing in the same item cleanup path.

Therefore Part B remains unresolved for gameplay/demo. The only proven layout evidence is item-page BG text staging and zero scroll in the captured item-page run.

## Part C - Sprite / Window / HUD Evidence

### PC090OJ

One PC090OJ helper event occurred before the crash:

```text
EVENT PC090OJ_HELPER_71CE2 cyc=78325476 pc=071CE4 sr=2704 a0=00056426 a1=00D00170 d0=000000E0 d1=00000000 stack0=0005631A s0=0002 s2=0002 s4=0006 cnt=0000
```

This event is in the item-page state path (`%a5@(0)=2/%a5@(2)=2/%a5@(4)=6`) and does not prove gameplay sprite layout.

No raw PC090OJ sprite RAM writes were observed before the crash.

### Window / HUD

No gameplay window/HUD evidence was reached. No raw FG scroll/window write class was observed before the crash. The crash occurs before a gameplay/demo state can be established.

### Part C Conclusion

Part C is not resolved for gameplay/demo. The trace only proves one item-page PC090OJ helper event and no raw PC090OJ writes before the repeated item-page crash.

## State Timeline

The trace stayed in attract/item-page states and crashed before gameplay/demo. Last relevant state writes include:

```text
EVENT A5_STATE_WRITE ... pc=03A7B6 addr=00FF0004 ... post_s0=0002 post_s2=0000 post_s4=0002
EVENT A5_STATE_WRITE ... pc=03A7BA addr=00FF0002 ... post_s0=0002 post_s2=0000 post_s4=0000
EVENT A5_STATE_WRITE ... pc=03A812 addr=00FF0004 ... post_s0=0002 post_s2=0002 post_s4=0000
EVENT A5_STATE_WRITE ... pc=03A84A addr=00FF0004 ... post_s0=0002 post_s2=0002 post_s4=0001
EVENT A5_STATE_WRITE ... pc=03A8E6 addr=00FF0004 ... post_s0=0002 post_s2=0002 post_s4=0006
EVENT A5_STATE_WRITE ... pc=03A970 addr=00FF0004 ... post_s0=0002 post_s2=0002 post_s4=0008
EVENT A5_STATE_WRITE ... pc=03A894 addr=00FF0004 ... post_s0=0002 post_s2=0002 post_s4=0002
EVENT A5_STATE_WRITE ... pc=03A8B0 addr=00FF0004 ... post_s0=0002 post_s2=0002 post_s4=0003
```

Crash halt then reports `%a5@(0)=2/%a5@(2)=2/%a5@(4)=4`.

## Answer To Prompt Questions

### Did Build 0115 reach gameplay/demo before crashing?

**No, not in this trace.** The run crashed in the item-description cleanup state family.

### Is this the same site/mechanism as the item-page `0x55B1A` crash?

**Yes.** The captured faulting instruction is `runtime_genesis_pc 0x00055B1A: movew %a4@,%a2@+`, with `%a4=0x0000000F`, fault address `0x0000000F`, and state `%a5@(0)=2/%a5@(2)=2/%a5@(4)=4`.

### Does this implicate Genesis helper rebasing or the Build 0115 dispatcher?

**No.** The faulting PC is inside an `arcade_copy` segment by `address_map.json`. The Build 0115 dispatcher had already routed item text into BG staging before this crash; the crash is not in the dispatcher, LUT, VDP commit path, or opcode rebasing.

### Does this establish gameplay/demo PC080SN layout?

**No.** It only records item-page layout behavior before the repeated crash.

## Recommended Next Evidence Target

Because this no-input trace did not reach gameplay/demo, the next evidence task should not claim gameplay layout from this run. Two safe options:

1. Resolve or further characterize the repeated item-page `0x55B1A` copied-arcade pointer/table crash before attempting no-input gameplay/demo layout evidence again.
2. If Tighe has a manual or scripted path that reaches gameplay/demo past the item page, capture a new video-anchored or input-scripted runtime trace and explicitly prove the state leaves `%a5@(0)=2/%a5@(2)=2` before classifying gameplay/demo PC080SN behavior.

These are recommendations only; no fix is proposed here.

## OPEN / KNOWN_FINDINGS Impact

- `OPEN-001`: still open; no gameplay rendering conclusion from this trace.
- `OPEN-015`: context only; WRAM crash record was used.
- `OPEN-022` / `OPEN-023` / `OPEN-024`: context only.
- `KF-038`: reinforced as the trace again hit item-page behavior, but no new finding is established.

`KNOWN_FINDINGS.md` was not modified by this task.

## Non-Actions

No source, spec, tool, Makefile, ROM, build, invariant, or bookmark artifacts were modified. No implementation or fix design was performed.

## STOP

STOP triggered: **YES (evidence limitation)**. The requested gameplay/demo crash was not reproduced; the run crashed earlier in the known item-page path. Evidence is documented without overclaiming gameplay/demo layout.
