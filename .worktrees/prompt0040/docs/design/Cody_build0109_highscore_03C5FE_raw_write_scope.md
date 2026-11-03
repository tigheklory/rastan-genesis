# Cody - Build 0109 High-Score Producer 0x03C5FE Raw-Write Scope

**Date:** 2026-06-27
**Type:** Runtime evidence + static correlation only
**Build:** 0109
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0109.bin`
**ROM SHA256:** `a9905cd73837099f6ed548dda5b4ff66a1bb6be0911730e1bf9204472e934bc9`
**Scope:** Evidence only. No source, spec, tool, Makefile, ROM, build, bookmark, diagnostic insertion, fix design, or implementation.

## Phase 0

Read for this task:

- `RULES.md`
- `ARCHITECTURE.md`
- `OPEN_ISSUES.md` / OPEN-018 context
- `KNOWN_FINDINGS.md` / KF-032 context
- latest `AGENTS_LOG.md`
- `docs/design/Cody_build0109_blastem_C09374_raw_write_evidence.md`

Classification: **EXTENDING** OPEN-018 / KF-032 raw PC080SN-write evidence.

The validated Build 0109 `runtime_genesis_pc 0x0003AD06` fall-through restore is not reopened here. This task scopes the raw-write surface of the high-score producer helper reached after high-score init.

## Evidence Artifacts

Trace directory:

`states/traces/build_0109_highscore_03c5fe_scope_20260627_210734/`

Files:

- `highscore_03c5fe_scope.cmd`
- `native_debug_trace.log`
- `events.log`
- `scope_analysis.json`
- `scope_analysis.md`
- `mame_stdout.log`
- `mame_stderr.log`

The MAME run was no-input and exited via debugger at the high-score tail completion breakpoint. No ROM diagnostics were inserted.

## Address Mapping Discipline

All code correlations below were checked through `build/rastan-direct/address_map.json`; no arithmetic offset was used as authority.

| Runtime Genesis PC | Address-map kind | Arcade PC | Role |
|---|---|---|---|
| `0x0003AD0C` | `arcade_copy` | `0x0003AB0C` | high-score init after restored fall-through |
| `0x0003B8BE` | `arcade_copy` | `0x0003B6BE` | high-score init helper |
| `0x0003B8F8` | `arcade_copy` | `0x0003B6F8` | loop setting up repeated `0x03C5FE` calls |
| `0x0003B900` | `arcade_copy` | `0x0003B700` | `bsr 0x03C5FE` call site |
| `0x0003C5FE` | `arcade_copy` | `0x0003C3FE` | high-score producer helper entry |
| `0x0003C62A` | `arcade_copy` | `0x0003C42A` | raw attr-word write |
| `0x0003C646` | `arcade_copy` | `0x0003C446` | raw code-word write |
| `0x0003C64A` | `arcade_copy` | `0x0003C44A` | static raw space-word write path, not hit in this run |
| `0x0003C654` | `arcade_copy` | `0x0003C454` | local 6-byte descriptor table |
| `0x0003C4E2` | `arcade_copy` | `0x0003C2E2` | nearby text writer, already routed by opcode replacement |

## Static Loop Structure

The active raw producer helper is `runtime_genesis_pc 0x0003C5FE`:

```asm
3c5fe: 3e3c 0000       move.w #0,%d7
3c602: 3400            move.w %d0,%d2
3c604: 0240 007f       andi.w #0x007f,%d0
3c608: c0fc 0006       mulu.w #6,%d0
3c60c: 41fa 0046       lea %pc@(0x3c654),%a0
3c610: d0c0            adda.w %d0,%a0
3c612: 3010            move.w (%a0),%d0          ; loop count
3c614: 3268 0002       movea.w 2(%a0),%a1       ; destination offset
3c618: d3fc 00c0 8000  adda.l #0x00c08000,%a1  ; PC080SN FG base
3c61e: 3468 0004       movea.w 4(%a0),%a2       ; source offset
3c622: d5fc 0010 c000  adda.l #0x0010c000,%a2  ; arcade work-RAM source
3c628: 4241            clr.w %d1
3c62a: 32c7            move.w %d7,(%a1)+        ; raw attr word
3c62c: 121a            move.b (%a2)+,%d1        ; source byte
3c62e: 0c01 003f       cmpi.b #0x3f,%d1
3c632: 6604            bne.s 0x3c638
3c634: 323c 274b       move.w #0x274b,%d1       ; '?' substitute
3c638: 0c01 0021       cmpi.b #0x21,%d1
3c63c: 6604            bne.s 0x3c642
3c63e: 323c 2744       move.w #0x2744,%d1       ; '!' substitute
3c642: 4a02            tst.b %d2
3c644: 6b04            bmi.s 0x3c64a
3c646: 32c1            move.w %d1,(%a1)+        ; raw code word
3c648: 6004            bra.s 0x3c64e
3c64a: 32fc 0020       move.w #0x0020,(%a1)+    ; raw space mode, not hit
3c64e: 5340            subq.w #1,%d0
3c650: 66d6            bne.s 0x3c628
3c652: 4e75            rts
```

Loop body: `0x03C628..0x03C650`.

Counter: `%d0`, loaded from the first word of a local 6-byte descriptor at `runtime_genesis_pc 0x03C654+index*6`.

Exit: `0x03C64E subq.w #1,%d0`; `0x03C650 bne.s 0x03C628`; exit to `0x03C652 rts`.

## Runtime Count and Range

The no-input trace captured one high-score init pass. `0x03B8F8` set up a five-call loop over `0x03C5FE`:

```text
CALL_3C5FE_3B900: 5
ENTRY_3C5FE: 5
TABLE_DECODE_3C614: 5
RAW_ATTR_WRITE_3C62A: 15
RAW_CODE_WRITE_3C646: 15
RAW_SPACE_WRITE_3C64A: 0
EXIT_3C5FE: 5
```

Each call had `count_word=0x0003`, so each call emitted three cells. Total raw PC080SN writes in the captured high-score producer pass: **30 words**.

Descriptor sequence:

| Call | Input `%d0` | Caller `%d7` | Count | Dest offset | HW dest base | Source offset | Source base |
|---:|---:|---:|---:|---:|---|---:|---|
| 0 | `0` | `5` | `3` | `0x1374` | `HW_ADDRESS 0x00C09374` | `0x0157` | `0x0010C157` |
| 1 | `1` | `4` | `3` | `0x1574` | `HW_ADDRESS 0x00C09574` | `0x015A` | `0x0010C15A` |
| 2 | `2` | `3` | `3` | `0x1774` | `HW_ADDRESS 0x00C09774` | `0x015D` | `0x0010C15D` |
| 3 | `3` | `2` | `3` | `0x1974` | `HW_ADDRESS 0x00C09974` | `0x0160` | `0x0010C160` |
| 4 | `4` | `1` | `3` | `0x1B74` | `HW_ADDRESS 0x00C09B74` | `0x0163` | `0x0010C163` |

Overall raw-write range:

- first raw write: `HW_ADDRESS 0x00C09374`
- last raw write: `HW_ADDRESS 0x00C09B7E`
- all writes are within PC080SN FG C-window `0x00C08000..0x00C0BFFF`
- no BG C-window writes were observed from this helper pass
- within each 3-cell row fragment, stride is 2 between attr/code words and 4 per cell pair
- between row fragments, address jumps by `0x1F6` from prior code word to next row attr word, equivalent to destination bases stepping `0x200` between calls

## Attr/Code Pairing

Runtime proves attr/code pairs:

- `runtime_genesis_pc 0x0003C62A` writes the attr word first.
- `runtime_genesis_pc 0x0003C646` writes the code word second.
- `runtime_genesis_pc 0x0003C64A` would write `0x0020` in negative/space mode, but it did not execute in this no-input high-score pass because `%d2` was nonnegative (`0..4`).

Attr writer:

```text
RAW_ATTR_WRITE_3C62A count=15 first=0x00C09374 last=0x00C09B7C data=0x0000 only
```

Code writer:

```text
RAW_CODE_WRITE_3C646 count=15 first=0x00C09376 last=0x00C09B7E
unique data: 0x0000, 0x0001, 0x0013, 0x0014, 0x0018, 0x0034, 0x0046, 0x0066, 0x0084
```

Important refinement to the prior C09374 note: `HW_ADDRESS 0x00C09374` is the attr word of the first pair, not the code word. The matching code word for that cell is `HW_ADDRESS 0x00C09376`.

## Other Raw Writers in the Immediate Chain

Inside the `0x03C5FE` helper body / family:

- `runtime_genesis_pc 0x0003C62A` / `arcade_pc 0x0003C42A`: raw attr word writer, runtime hit 15 times.
- `runtime_genesis_pc 0x0003C646` / `arcade_pc 0x0003C446`: raw code word writer, runtime hit 15 times.
- `runtime_genesis_pc 0x0003C64A` / `arcade_pc 0x0003C44A`: raw space-mode writer, statically present but not runtime-hit in this no-input high-score pass.

Nearby routed writer context:

- `runtime_genesis_pc 0x0003C4E2` / `arcade_pc 0x0003C2E2` is already opcode-replaced to `jsr 0x70C22` (`genesistan_hook_number_renderer_3c2e2`) and is not a raw PC080SN writer in Build 0109.
- The earlier high-score init calls to `0x03BD48` are already routed through `genesistan_hook_glyph_renderer_3bd48`.

So the newly scoped raw surface is not the entire high-score init helper family; it is specifically the still-copied `0x03C5FE` producer loop and its attr/code/space write sites.

## Data Source

The helper uses a local descriptor table at `runtime_genesis_pc 0x0003C654` with 6-byte entries:

```text
[count word][destination offset word][source offset word]
```

Runtime source pointers are `0x0010C157..0x0010C166`. These are arcade work-RAM addresses, not ROM descriptor text. The helper adds `0x0010C000` to the source offset at `0x03C622` and then reads source bytes via `move.b (%a2)+,%d1` at `0x03C62C`.

Observed source/code byte sequence emitted by `0x03C646`:

```text
18 01 34 66 84 00 13 18 46 00 01 34 14 00 00
```

Special substitutions are present but did not fire in this capture:

- source byte `0x3F` would become tile/code `0x274B`
- source byte `0x21` would become tile/code `0x2744`

The attr word `%d7` inside `0x03C5FE` is not sourced from the caller's `%d7`; the helper resets `%d7` to `0x0000` at entry (`0x03C5FE: move.w #0,%d7`). Therefore every attr write is deliberately `0x0000`.

## Zero-Data Classification

There are two different zero sources:

- Attr zeros are intentional: the helper explicitly sets `%d7=0` and writes it as the attr word for every cell.
- Code zeros come from the arcade work-RAM source bytes at `0x0010C15C`, `0x0010C160`, `0x0010C164`, and `0x0010C165` in this capture.

The helper is **not** intentionally blanking the code cells in this no-input high-score pass. The negative/space-mode path at `0x03C64A` did not execute. Code values are source-data-driven.

Assessment: the strict-target freeze and any zero/blank high-score content do **not** share the same immediate root. The freeze root is raw PC080SN writes to VDP-mirror space. Blank/zero code cells, where present, come from upstream high-score backing data or its initialization state. That upstream data question remains separate and was not fixed or pursued here.

## Resemblance to Existing Helpers

The helper resembles existing routed text-writer hooks in structure:

- It decodes a descriptor/table entry.
- It computes a PC080SN FG destination in the `0x00C08000` C-window.
- It walks a source byte stream.
- It emits per-cell attr/code words.

Differences from existing routed hooks:

- The attr and code words are emitted by two separate raw instructions (`0x03C62A` then `0x03C646`) rather than by an already wrapped store helper.
- It has a local 6-byte descriptor table at `0x03C654` and fixed `0x0010C000` work-RAM source addressing.
- It has a special substitute path for `!` and `?` and an unused-in-this-run negative space-mode branch.

Evidence-only feasibility assessment: routing the whole helper or its producer loop through existing FG staging is feasible in principle, because the helper already expresses a normal FG attr/code stream. It likely needs a wrapper for the raw `%a1@+` stream or a function-level replacement analogous to the existing `genesistan_hook_text_writer_*` family, rather than a one-cell patch at `0x00C09374`.

This is only a scoping assessment, not a design.

## Classification

**C - MULTIPLE raw writers.**

Reason: `0x03C62A` is indeed a producer loop, but the full helper surface includes multiple raw PC080SN writer PCs in that loop/family:

- active attr writer `0x03C62A`
- active code writer `0x03C646`
- static negative/space writer `0x03C64A`, not hit in this no-input pass

So classification B is true but incomplete; classification C is the safer scope for the next task.

## Recommended Follow-up Boundary

Scoping-only recommendation: Andy should design routing for the **whole `0x03C5FE` producer loop/helper family**, not for the single `HW_ADDRESS 0x00C09374` cell. A single-cell fix would almost certainly expose the next raw write in the same loop.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-018: touched and extended by evidence. This scopes a new high-score producer-loop raw-write family beyond the previously listed raw sites. No issue was closed and no issue file was edited.
- OPEN-001: context only.
- OPEN-015: not touched.
- KNOWN_FINDINGS: no update recommended in this evidence-only task; KF-032 already captures the broad raw PC080SN staging requirement.

## STOP Status

STOP triggered: **NO**.

