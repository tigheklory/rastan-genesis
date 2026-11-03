# Cody - Build 0117 Post-Descriptor-Relocation Crash Evidence

**Date:** 2026-06-29
**Type:** Runtime evidence / crash classification only
**Build:** 0117
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0117.bin`
**SHA256:** `17cb39c7da59406e4fba569862cdb04f44dc96258d162470c54c7edf9f9cd621`
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build changes. No fix design. No bookmark cycle. No KF-038 / sprites / HUD / Window work.

## Phase 0

Read `RULES.md`, `ARCHITECTURE.md`, latest `AGENTS_LOG.md`, and the task prompt. Architecture compliance: PASS. This task used MAME debugger tracing and WRAM dumps only; no ROM diagnostics or code changes were introduced.

OPEN-015 crash-screen caveat is active: formatted crash-screen numeric fields are not authoritative. The crash record in `Genesis-WRAM 0x00FF6800` and the debugger-side exception frame are authoritative.

## Evidence Artifacts

Primary crash evidence:

- `states/traces/build_0117_post_descriptor_crash_evidence_20260629_175100/build0117_post_descriptor_crash.cmd`
- `states/traces/build_0117_post_descriptor_crash_evidence_20260629_175100/wram_ff1000_after_hook.bin`
- `states/traces/build_0117_post_descriptor_crash_evidence_20260629_175100/stack_at_crash_common.bin`
- `states/traces/build_0117_post_descriptor_crash_evidence_20260629_175100/crash_record_ff6800.bin`
- `states/traces/build_0117_post_descriptor_crash_evidence_20260629_175100/wram_ff0000_state_at_crash.bin`

Additional state-window dump:

- `states/traces/build_0117_post_descriptor_crash_state_window_20260629_175319/crash_record_ff6800.bin`
- `states/traces/build_0117_post_descriptor_crash_state_window_20260629_175319/wram_ff1380_item_counters.bin`
- `states/traces/build_0117_post_descriptor_crash_state_window_20260629_175319/wram_ff10d0_descriptor_slots.bin`

Both runs reproduce the same authoritative crash record.

## Part A - Descriptor Relocation Fix Held

The descriptor relocation hook completed before the crash. The same debugger run that later captured the crash also dumped `Genesis-WRAM 0x00FF1000..0x00FF10BF` at hook completion.

Hook output after completion:

```text
FF1000:  0001 691C 0001 8BDC 0001 AE9C 0001 D15C
FF1010:  0001 F41C 0002 16DC 0002 399C 0002 5C5C
FF1020:  0002 7F1C 0002 A1DC 0002 C49C 0002 E75C
FF1030:  0003 0A1C 0003 2CDC 0003 4F9C 0003 725C
FF1040:  0000 22FC 0000 22FC 0000 22FC 0000 22FC
FF1050:  0000 22FC 0000 22FC 0000 22FC 0000 22FC
FF1060:  0000 22FC 0000 22FC 0000 2248 0000 2248
FF1070:  0000 2248 0000 2248 0000 2248 0000 2248
FF1080:  0003 0003 0003 0003 0003 0003 0003 0003
FF1090:  0003 0003 0003 0003 0003 0003 0003 0003
```

Conclusion: Build 0117's descriptor source-pointer relocation held. The prior Build 0116 wrong rebuild values are not present.

## Dead-Body Check

The original rebuild body at `runtime_genesis_pc 0x00055B0A..0x00055B46` should be dead after the entry jump at `0x00055B04`.

Scan result:

- External direct branch/call targets into `0x55B0A..0x55B46`: **0**.
- The only textual branch target in that range is internal to the dead body: `0x55B36 -> 0x55B18`.
- Existing external callers target `0x55B48`, not the dead rebuild body.

Conclusion: no direct external branch/caller enters the now-dead original rebuild body.

## Part B - Authoritative Crash Record

Crash reproduced: **YES**.

Authoritative record from `Genesis-WRAM 0x00FF6800`:

| Field | Value | Source |
|---|---:|---|
| Exception type | `0x03` (ADDRESS ERROR) | `0x00FF6802` |
| Stacked SR | `0x2704` | `0x00FF6804` |
| Authoritative stacked PC | `runtime_genesis_pc 0x00055E90` | `0x00FF6806` |
| Handler marker | `0x00000442` | `0x00FF680A` |
| SP at entry / A7 at exception frame | `0x00FEFFC8` | `0x00FF680E` |
| Fault address | `0x22113111` | `0x00FF6854` |
| Access/frame word | `0x3015` | `0x00FF6858` |
| IR from raw group-0 frame | `0x3016` | stack frame word at `SP+6` / saved D3 |

Raw exception frame at `_crash_common` entry (`runtime_genesis_pc 0x000003D0`):

```text
FEFFC8: 3015 2211 3111 3016 2704 0005 5E90 ...
```

Group-0 frame decode:

- access/frame word: `0x3015`
- fault address: `0x22113111`
- IR: `0x3016`
- SR: `0x2704`
- stacked PC: `0x00055E90`

Access classification: **word read**. Evidence: IR `0x3016` decodes as `move.w (%a6),%d0`; `A6=0x22113111`, an odd address, produces the ADDRESS ERROR on a word read. The stacked PC is the next instruction, consistent with the m68k group-0 frame behavior already seen in prior crash triage.

## Register Record Caveat

Per OPEN-015, `_crash_common` decodes the frame into D1-D5 and sets A0/A1 before saving registers. Therefore these saved values are not all true at-fault registers.

Crash record values:

| Register | Saved value | Reliability note |
|---|---:|---|
| D0 | `0x00000003` | exception type, handler value |
| D1 | `0x00002704` | decoded stacked SR |
| D2 | `0x00055E90` | decoded stacked PC |
| D3 | `0x00003016` | decoded IR |
| D4 | `0x22113111` | decoded fault address |
| D5 | `0x00003015` | decoded access/frame word |
| D6 | `0x00000000` | genuine at-fault register |
| D7 | `0x00000000` | genuine at-fault register |
| A0 | `0x00FEFFC8` | handler SP value |
| A1 | `0x00000442` | handler marker |
| A2 | `0x22113111` | genuine at-fault register |
| A3 | `0x0010D100` | genuine at-fault register |
| A4 | `0x0003951C` | genuine at-fault register |
| A5 | `0x00FF0000` | genuine at-fault register / Genesis-WRAM base |
| A6 | `0x22113111` | genuine at-fault register; faulting source pointer |
| A7 | `0x00FEFFC8` | SP at exception-frame entry |

## State Values

Main state at crash:

- `Genesis-WRAM 0x00FF0000` / `%a5@(0)`: `0x0002`
- `Genesis-WRAM 0x00FF0002` / `%a5@(2)`: `0x0002`
- `Genesis-WRAM 0x00FF0004` / `%a5@(4)`: `0x0004`
- `Genesis-WRAM 0x00FF002C` / `%a5@(44)`: `0x0000`

Item/internal counters from follow-up state window:

- `%a5@(0x1392)` / `Genesis-WRAM 0x00FF1392`: `0x0000`
- `%a5@(0x1394)` / `Genesis-WRAM 0x00FF1394`: `0x00FF`
- `%a5@(0x13AA)` / `Genesis-WRAM 0x00FF13AA`: `0x00FF`
- `%a5@(0x13B0)` / `Genesis-WRAM 0x00FF13B0`: `0x0001`

The crash is still in item-page state `2/2/4`; execution has not left the item-description state for gameplay/demo.

## Part C - Faulting Instruction

Authoritative stacked PC:

- `runtime_genesis_pc 0x00055E90`
- JSON map: copied arcade segment
- `arcade_pc 0x00055C90`

IR-identifed faulting instruction:

- `runtime_genesis_pc 0x00055E8E`
- JSON map: copied arcade segment
- `arcade_pc 0x00055C8E`

Disassembly:

```asm
55e88: de40            addw %d0,%d7
55e8a: 4df2 7000       lea %a2@(0,%d7:w),%a6
55e8e: 3016            movew %a6@,%d0       ; IR=0x3016, faulting word read
55e90: 3080            movew %d0,%a0@       ; stacked PC / next instruction
55e92: d1fc 0000 00fe  addal #254,%a0
```

Code classification: **copied arcade code**. It is not a patched site, not a Genesis-only helper, and not the crash-handler path.

The immediate local provenance visible in copied code:

```asm
55e5e: 206d 10f8       moveal %a5@(4344),%a0
55e62: 227c 0010 d104  moveal #0x0010D104,%a1
55e68: 267c 0010 d100  moveal #0x0010D100,%a3
55e6e: 2453            moveal %a3@,%a2
55e70: 6100 0008       bsrw 0x55e7a
...
55e8a: 4df2 7000       lea %a2@(0,%d7:w),%a6
55e8e: 3016            movew %a6@,%d0
```

Interpretation boundary: This evidence identifies the next raw/mapped descriptor-table class crash locus, but this task does not design or implement a fix.

## Claim Verification / Refutation

### Claim: faulting PC `runtime_genesis_pc 0x00045DC0`

**Refuted by authoritative evidence.** The crash record says stacked PC is `runtime_genesis_pc 0x00055E90`, with IR `0x3016` pointing to the faulting instruction at `runtime_genesis_pc 0x00055E8E`. `0x00045DC0` is not the faulting PC in this run.

For reference, `runtime_genesis_pc 0x00045DC0` maps via JSON to `arcade_pc 0x00045BC0`, but no crash-frame evidence points there. CLOSED-002 / `0x045DAE` is therefore not implicated by this Build 0117 evidence.

### Claim: screenshot fault PC around `runtime_genesis_pc 0x00006116`

**Refuted by authoritative evidence.** The crash record says stacked PC is `runtime_genesis_pc 0x00055E90`. The screenshot-style `0x6116` value is not authoritative and does not match the WRAM/debugger crash record.

For reference, `runtime_genesis_pc 0x00006116` maps via JSON to `arcade_pc 0x00005F16`, but no crash-frame evidence points there.

## Part D - Flow Classification

- Item-page descriptor rebuild completed: **YES**.
- Execution left item-description state: **NO**.
- State at crash: `2/2/4`, counter `0`.
- Flow classification: **item-page / item-description cleanup or continuation**, not attract transition and not gameplay/demo start.
- Gameplay/demo layer activity: not reached in this evidence. No gameplay/demo PC080SN or PC090OJ conclusions are made.

Context-only crash record graphics state:

- `CRASH_ARCADE_DEST_BG`: `0x00C08000`
- `CRASH_ARCADE_DEST_FG`: `0x00C0C000`
- `CRASH_BG_ROW_DIRTY`: `0x00000000`
- `CRASH_FG_ROW_DIRTY`: `0x0000000F`
- `CRASH_PALETTE_DIRTY`: `0x00`
- `CRASH_TILES_DIRTY`: `0x00`

## Label Correction

The Build 0117 descriptor-source relocation report/log previously said "OPEN-023 progressed." That was corrected in:

- `docs/design/Cody_build0117_pc080sn_descriptor_source_pointer_relocation.md`
- `AGENTS_LOG.md`

Correct label: **OPEN-016 / KF-028 runtime-pointer-relocation class**, with KF-036 as predecessor/context. OPEN-023 is Window/HUD and is not the owner for this descriptor source-pointer relocation.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-016 / KF-028: descriptor relocation held; next blocker captured.
- KF-036: predecessor remains valid.
- KF-038: not touched; no conclusion changed.
- OPEN-001 / OPEN-022 / OPEN-024: context only.
- OPEN-015: active caveat; authoritative WRAM/debugger record used over formatted crash screen.
- Issues opened/closed: none.
- `KNOWN_FINDINGS.md`: not edited by this task.

## STOP

STOP triggered: **NO** for evidence capture/classification.

Implementation remains unauthorized. The next fault is proven at `runtime_genesis_pc 0x00055E8E` / mapped `arcade_pc 0x00055C8E`, but this report intentionally does not propose or apply a fix.
