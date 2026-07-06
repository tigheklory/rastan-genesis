# Cody - FG Vertical Strip Narrow Commit Build 0140

**Date:** 2026-07-05  
**Type:** Production implementation + numbered build + static verification + MAME runtime evidence  
**Design authority:** `docs/design/Andy_fg_vertical_strip_narrow_commit_design.md`  
**Final build:** Build 0140  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0140.bin`  
**SHA256:** `f6e63eb3e3a6d5e82caf9e151ef2eb1c23418633ee7118adad51f1c2081a135c`  
**Evidence:** `states/traces/fg_vertical_strip_narrow_commit_build_0140_20260705_145903/`

## Executive Result

Implemented Andy's corrected producer-local FG narrow commit for the selected PC080SN FG vertical-strip producer only:

- Selected producer: `arcade_pc 0x055990` / `runtime_genesis_pc 0x055B90`.
- Selected helper remains at `runtime_genesis_pc 0x0703EA`.
- Selected wrapper bytes are byte-identical to Build 0138: `4eb9000703ea` + NOP padding.
- `opcode_replace` count remains `133`.
- Address-map coverage remains gap/overlap clean: total covered bytes `0x17D680`.
- No spec changes were made.
- No one-frame-lag pipeline, frame queue, buffer swap, active-display VDP write, BG/sprite/palette generalization, or unrelated producer conversion was introduced.

One intermediate artifact, Build 0139, was rejected during verification because the first implementation layout moved `genesistan_hook_tilemap_fg` from `0x0703EA` to `0x070462`, changing the selected wrapper operand. The implementation was restructured before final acceptance. Build 0140 is the artifact to test.

## Andy Design Followed

The implemented transaction follows the corrected design:

- Fixed-capacity descriptor list, selected producer only.
- Descriptor size: 2 bytes.
- Descriptor byte 0: `base_row`.
- Descriptor byte 1: `col_offset_x2`.
- Capacity: 64 descriptors.
- Strict narrow eligibility: `col_offset_x2 + 120 < 128`.
- Wrapping/unsupported shapes, invalid descriptors, and capacity overflow fall back to the broad dirty-row path.

Implementation detail: the required `fg_narrow_pending_rows` 2-byte symbol is allocated and cleared as specified. The selected producer uses a 32-bit stack-local pending-row mask internally so rows 16-31 cannot be lost when broad fallback ORs into the existing 32-bit `fg_row_dirty` mask.

## Execution-State Limitation

Build 0138/0140 frontend/attract automation does not reach playable Genesis gameplay. The Build 0140 MAME runtime capture used only the reachable frontend coin/start sequence and must not be described as gameplay validation.

The Build 0140 automated frontend capture completed to frame `3600` and final state `2/3/0`, but did not execute `runtime_genesis_pc 0x055B90`. Therefore selected-runtime word reduction is not measured in this task. The implementation is accepted on static/build invariants plus frontend stability; a future state/input replay that reaches `0x055B90` is needed to measure the expected 256-to-64 selected transfer reduction in the new build.

## Files Changed

- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/boot/boot.s`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- Generated build outputs under `apps/rastan-direct/out/`, `apps/rastan-direct/dist/`, `dist/rastan-direct/`, `build/`, and `states/traces/`.
- This report.
- `AGENTS_LOG.md` appended after the final verification pass.

Pre-existing handoff edits preserved:

- `docs/design/Andy_fg_vertical_strip_narrow_commit_design.md`
- existing top-of-log content in `AGENTS_LOG.md`

## Build Number / ROM

- Build counter after final release: `140`.
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0140.bin`.
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- SHA256 for both: `f6e63eb3e3a6d5e82caf9e151ef2eb1c23418633ee7118adad51f1c2081a135c`.
- `cmp` result: byte-identical.
- Canonical gate: `GATE_PASS`.

## WRAM Symbols

From `apps/rastan-direct/out/symbol.txt`:

| Symbol | Address | Size / role |
|---|---:|---|
| `fg_row_dirty` | `0x00FF4006` | existing 32-bit FG dirty mask |
| `fg_narrow_desc_table` | `0x00FF400A` | 128 bytes, 64 descriptors |
| `fg_narrow_desc_count` | `0x00FF408A` | 2 bytes |
| `fg_narrow_pending_rows` | `0x00FF408C` | 2 bytes |
| `staged_fg_buffer` | `0x00FF509E` | existing Plane-A staging buffer |

New WRAM range: `0x00FF400A..0x00FF408D`, exactly 132 bytes. All symbols are 2-byte aligned and do not overlap the adjacent `fg_row_dirty` or `staged_fg_buffer` regions.

## Descriptor Implementation

Descriptor table layout:

```text
fg_narrow_desc_table[count + 0] = base_row byte
fg_narrow_desc_table[count + 1] = col_offset_x2 byte
fg_narrow_desc_count            = visible descriptor count
```

The selected producer writes descriptor bytes before incrementing `fg_narrow_desc_count`:

- `0x705B6`: store base row byte.
- `0x705C0`: store `col_offset_x2` byte.
- `0x705C6`: increment/store descriptor count.

## Producer Transaction

Selected helper entry remains `0x0703EA`.

Key static points:

- Existing destination range/alignment rejection still exits through `0x705EE`; this path allocates no local transaction frame and cannot append descriptors, write staging cells, or change `fg_row_dirty`.
- Valid path captures `base_row` at stack local `sp+4` and `col_offset_x2 = 2 * (base_col + strip)` at `sp+6`.
- In-loop staging store remains at `0x7054E`, writing to `staged_fg_buffer` through `%a6 = 0x00FF509E`.
- In-loop dirty update is replaced with a local pending-row OR at `0x70552..0x70556`; selected valid staging no longer writes `fg_row_dirty` during the loop.
- Per-descriptor invalid path sets `any_invalid_desc` at `sp+8` and continues descriptor progression.
- Final decision starts at `0x7058A`.

## Corrected Wrap Eligibility

Strict check in generated disassembly:

```asm
70590: move.w  %sp@(6),%d0       ; col_offset_x2
70594: addi.w  #120,%d0
70598: cmpi.w  #128,%d0
7059c: bcc.s   0x705ce           ; broad fallback if col_offset_x2 + 120 >= 128
```

No 256-byte threshold, row-spill transfer, masked per-word wrap, wrapped-segment split, or descriptor enlargement was introduced.

## Fallbacks

Fallback path at `0x705CE`:

```asm
705ce: move.l  %sp@,%d0          ; pending rows
705d0: beq.s   0x705e0
705d2: move.l  0xff4006,%d3      ; existing fg_row_dirty
705d8: or.l    %d0,%d3
705da: move.l  %d3,0xff4006      ; OR only, no assignment/clear
```

Fallback conditions:

- any invalid descriptor flag set;
- `col_offset_x2 + 120 >= 128`;
- descriptor count already `64`.

## Remaining FG Dirty Writers

The implementation changed only the selected producer's valid-path dirty behavior. Other FG producers still write `fg_row_dirty` through their existing paths, including fill/text/helper/general FG commit paths. No global dirty policy was changed, and no dirty bit owned by another producer is cleared by this producer.

## Narrow VBlank Routine

Final VBlank topology:

```asm
700d6: bsr 0x7010e  ; tiles
700da: bsr 0x70138  ; BG row commit
700de: bsr 0x71708  ; narrow FG presenter wrapper
700e2: bsr 0x72124  ; sprite VRAM service
...
71776: movem restore
7177a: bra.w 0x70186 ; unchanged broad FG row commit
```

The broad FG row commit code remains at `0x70186..0x701D2` and is reached after the narrow presenter restores registers.

## VDP Autoincrement Handling

Generated presenter:

- `0x71716..0x7171A`: sets VDP autoincrement register `0x0F` to `0x08` only if descriptor count is nonzero.
- `0x71750`: writes one source word to `VDP_DATA`.
- `0x71756`: source advances by 8 bytes.
- `0x7175A`: exactly 16 writes per row via `dbf d2`.
- `0x71760`: exactly 4 rows per descriptor via `dbf d5`.
- `0x71768..0x7176C`: restores autoincrement to `0x02`.
- `0x71770`: clears `fg_narrow_desc_count` after processing.
- Zero-count fast path branches to `0x71776` without touching autoincrement.

## Static Verification

| Check | Result |
|---|---|
| Baseline Build 0138 SHA available | PASS: `719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615` |
| Selected wrapper byte-identical to Build 0138 | PASS |
| Selected arcade entry maps correctly | PASS: address-map segment `arcade_start 0x055990`, `genesis_start 0x055B90` |
| Opcode replacement count | PASS: `133` |
| Address-map gaps/overlaps | PASS: `gaps=[]`, `overlaps=[]` |
| Valid staging store preserved | PASS statically at `0x7054E` using same composed cell inputs and `staged_fg_buffer` base |
| Range reject writes no staging/descriptor/dirty | PASS statically; reject at `0x705EE` before transaction frame |
| Invalid descriptor fallback | PASS: flag at `0x70568`, fallback at `0x705CE` |
| Corrected wrap fallback | PASS: `col_offset_x2 + 120 >= 128` branches to fallback |
| Count-64 fallback | PASS: `cmpi.w #64` then `bcc` fallback |
| Descriptor before count | PASS |
| Narrow success dirty suppression | PASS statically; no `fg_row_dirty` write on append path |
| Fallback ORs pending rows | PASS |
| General FG commit unchanged | PASS: still row-copy path with 64 word writes per dirty row |
| No frame pipeline introduced | PASS |

## Address-Map And Byte Delta Verification

Address-map segment for selected patched site:

```json
{
  "genesis_start": "0x055B90",
  "genesis_end_exclusive": "0x055BB0",
  "size_bytes": 32,
  "kind": "patched_site",
  "arcade_start": "0x055990",
  "arcade_end_exclusive": "0x0559B0",
  "origin": "opcode_replace",
  "replacement_bytes": "4eb9000703ea4e714e714e714e714e714e714e714e714e714e714e714e714e71",
  "shift_delta": 0
}
```

Wrapper bytes comparison:

| Build | Bytes at `0x55B90..0x55BAF` |
|---|---|
| 0138 | `4eb9000703ea4e714e714e714e714e714e714e714e714e714e714e714e714e71` |
| 0139 rejected | `4eb900070462...` |
| 0140 final | `4eb9000703ea4e714e714e714e714e714e714e714e714e714e714e714e714e71` |

## MAME Frontend/Attract Runtime Evidence

Evidence path:

- `states/traces/fg_vertical_strip_narrow_commit_build_0140_20260705_145903/narrow_commit_runtime_summary.md`
- `states/traces/fg_vertical_strip_narrow_commit_build_0140_20260705_145903/narrow_commit_runtime_summary.json`
- `states/traces/fg_vertical_strip_narrow_commit_build_0140_20260705_145903/narrow_commit_lua_events.log`
- `states/traces/fg_vertical_strip_narrow_commit_build_0140_20260705_145903/frame_markers.log`
- Release smoke trace: `states/traces/rastan_direct_video_test_build_0140_mame_30s_20260705_145705/`

Runtime result:

- MAME Genesis driver completed the 3600-frame headless frontend capture cleanly.
- Final recorded state: `2/3/0`.
- Selected producer `0x055B90` did not execute in this capture.
- Selected staging stores: `0`.
- Descriptor table writes: `0`.
- Narrow VDP data writes: `0`.
- New exception observed: NO.

Counts from `narrow_commit_runtime_summary.md`:

| Event | Count |
|---|---:|
| `FG_STAGING_WRITE` | 134 boot-time zeroing events |
| `NARROW_DESC_TABLE_WRITE` | 0 |
| `NARROW_COUNT_WRITE` | 1 boot-time clear |
| `FG_DIRTY_WRITE` | 2 boot-time dirty clears |
| `VDP_DATA_NARROW_WRITE` | 0 |
| `VDP_DATA_BROAD_FG_WRITE` | 0 |

## Build 0138 Versus Build 0140 Word Comparison

Static selected-operation comparison:

| Path | Selected logical cells | Presentation model | Plane-A words |
|---|---:|---|---:|
| Build 0138 selected broad path | 64 | 4 full rows x 64 words | 256 |
| Build 0140 selected narrow path | 64 | 4 strided runs x 16 words | 64 |

Static reduction for one eligible selected invocation: `192` fewer Plane-A words, `75%` reduction.

Runtime-selected reduction was not measured because the Build 0140 automated frontend capture did not hit `0x055B90`.

## DISPLAY_OFF-To-DISPLAY_ON Comparison

Build 0140 static ordering keeps the presenter inside the existing DISPLAY_OFF window:

- DISPLAY_OFF set at `0x700CE..0x700D2`.
- Narrow presenter call at `0x700DE`.
- Broad FG row commit is tail-called at `0x7177A -> 0x70186`.
- Sprite VRAM service remains after FG presentation at `0x700E2`.
- DISPLAY_ON remains at `0x700E6..0x700EA`.

No reliable cycle-delta comparison was claimed because the automated capture did not exercise a nonzero descriptor count.

## Visual Observations

No Build 0140 visual screenshots were created in this task. The MAME release trace and headless frontend capture completed without a new exception. The user remains the final BlastEm visual tester.

## Limitations

- Build 0139 is an invalid intermediate artifact; do not use it for testing.
- Build 0140 did not measure an actually selected `0x055B90` narrow transfer at runtime because the automated frontend/attract sequence did not reach that producer.
- Valid narrow invocation count, range-rejected selected invocation count, invalid-descriptor fallback count, wrap fallback count, overflow fallback count, descriptor count before/after VBlank, and selected Plane-A words before/after are static-only for Build 0140.
- Runtime visual proof of reduced DISPLAY_OFF cost requires a future capture or save-state/input path that reaches `0x055B90`.

## User BlastEm Test Instructions

Test this ROM only:

```bash
/usr/games/blastem -m gen /home/tighe/projects/rastan-genesis/dist/rastan-direct/rastan_direct_video_test_build_0140.bin
```

Do not use Build 0139 for visual evaluation.

## Evidence Index

- Implementation report: `docs/implementation/Cody_fg_vertical_strip_narrow_commit_build_0140.md`
- Runtime evidence: `states/traces/fg_vertical_strip_narrow_commit_build_0140_20260705_145903/`
- Final ROM: `dist/rastan-direct/rastan_direct_video_test_build_0140.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Release smoke trace: `states/traces/rastan_direct_video_test_build_0140_mame_30s_20260705_145705/`
- Rejected intermediate evidence retained: `states/traces/fg_vertical_strip_narrow_commit_build_0139_20260705_184220/`

## Issue / Known Findings Impact

- OPEN-001 / PC080SN optimization context only; remains open.
- No issues opened or closed.
- `KNOWN_FINDINGS.md` not edited.

## STOP Status

STOP triggered for the intermediate Build 0139 layout because selected wrapper bytes changed. That implementation layout was rejected and reworked. Final Build 0140 does not trigger STOP on static/build invariants. Runtime selected-transfer evidence remains limited, as documented above.
