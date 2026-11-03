# Cody - Lizard b5 Activation Writer Provenance

**Date:** 2026-07-18
**Type:** Runtime evidence / writer provenance only
**Build context:** Build 0205/256, SHA `4238d2ffcd226c45f1251ccbe4e7e64fa9b642acb18c4957ab85e1fd888b4aee`
**Scope:** Evidence-only extension of KF-064/KF-065. No source/spec/tool/Makefile/ROM/invariant changes. No build. Build 0206 was not produced.

Address labels: `arcade_pc` and `runtime_genesis_pc` are code addresses mapped through `build/rastan-direct/address_map.json`; `arcade_WRAM` is original arcade work RAM; `Genesis-WRAM` is Genesis work RAM; `HW_ADDRESS` is hardware.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-064 (the first visible Stage-1 lizards are block `A5+0x02C8` -> composite records ~140..229, not record 46), KF-065 (Build 0205 whole-block scratch staging route for block `A5+0x02C8`), KF-063 (engine safety / shared `0x3C950` non-C-window tuple writes), KF-060..KF-062 (PC090OJ provenance context), and the active issue context in OPEN-017/OPEN-024.

Rediscovery-hazard HIGH findings touched: KF-064 and related PC090OJ ownership findings. No contradiction of CONFIRMED/STRONG findings detected.

Architecture compliance: **CONFIRMED**. This task observes the original arcade program and the translated Genesis helper path. It does not force actors, seed state, add a renderer, add SAT entries, or modify the ROM.

## Baseline

- Counter before/after: `205`.
- Rolling Build 0205 ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- Preserved Build 0205 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0205.bin`.
- SHA256: `4238d2ffcd226c45f1251ccbe4e7e64fa9b642acb18c4957ab85e1fd888b4aee`.
- `opcode_replace`: `214`.
- `total_genesis_bytes_covered`: `0x182950`.
- Build 0206 artifact: **absent** / not produced.

## Evidence Artifacts

Trace directory: `states/traces/lizard_b5_activation_writer_provenance_20260718_221518/`

Key files:

- `arcade_full_b5_events.log` - debugger-side write-watch events for original arcade `rastan`.
- `genesis_full_b5_events.log` - debugger-side write-watch events for Genesis Build 0205.
- `arcade_full_frame_state.csv` - per-frame arcade state sampler over the same window.
- `genesis_full_frame_state.csv` - per-frame Genesis state sampler over the same window.
- `arcade_full_debug_trace.log` / `genesis_full_debug_trace.log` - retained full debugger traces.
- `b5_event_summary.md` / `b5_event_summary.json` - reduced summaries generated from the watchpoint logs.

Method note: the successful evidence source is MAME debugger-side write watchpoints with trace logging. A Lua write-tap attempt was preserved in the trace directory but did not capture the actual b5 byte transitions reliably and is not used as proof. In the debugger watchpoint logs, `data=` is the write value; the script's `post=` field is a byte read at trigger time and behaves as the pre-write value for these hits, so it is not used as an authoritative post-write value.

## Watched Actor Bytes

The watched bytes are actor-block fields, not PCs.

| Entry | Actor window | arcade_WRAM b5 | Genesis-WRAM b5 |
|---:|---|---|---|
| 4 | `A5+0x03C8` | `0x0010C3CD` | `0x00FF03CD` |
| 5 | `A5+0x0408` | `0x0010C40D` | `0x00FF040D` |
| 6 | `A5+0x0448` | `0x0010C44D` | `0x00FF044D` |
| 7 | `A5+0x0488` | `0x0010C48D` | `0x00FF048D` |
| 8 | `A5+0x04C8` | `0x0010C4CD` | `0x00FF04CD` |

The watchpoint scripts also captured adjacent word clears at `entry_base+4` when a 16-bit clear covers `b4/b5` together; those clear hits are included separately from nonzero byte activations.

## Address Mapping Discipline

All arcade-to-Genesis code correlations below were checked through `build/rastan-direct/address_map.json`, not by treating `+0x200` arithmetic as proof.

| arcade_pc | runtime_genesis_pc | Segment kind | Role |
|---|---|---|---|
| `0x00041320` | `0x00041520` | `arcade_copy` | Actual b5 activation writer, `move.b %d1,5(%a4)` |
| `0x00041324` | `0x00041524` | `arcade_copy` | Watchpoint post-PC after the activation writer |
| `0x00040B66` | `0x00040D66` | `arcade_copy` | 9-entry block `A5+0x02C8` loop |
| `0x00040B80` | `0x00040D80` | `arcade_copy` | Per-entry `a4` selection and active-entry dispatch |
| `0x00041F0E` | `0x0004210E` | `arcade_copy` | Gameplay object/update caller |
| `0x0003A7B4` | `0x0003A9B4` | `arcade_copy` | Gameplay dispatcher caller into `0x41F0E` / `0x4210E` |
| `0x00040A1C` | `0x00040C1C` | `arcade_copy` | Later b5 state updater, observed after activation |
| `0x0003A2D4` | `0x0003A4D4` | `arcade_copy` | Actor-window clear/copy post-PC |
| `0x0003AF02` | `0x0003B102` | `arcade_copy` | Startup clear post-PC |

## Arcade Writer and Control Path

The exact arcade activation writer is:

```asm
arcade_pc 0x0004131A: move.b 4(%a4),%d1
arcade_pc 0x0004131E: addq.b #1,%d1
arcade_pc 0x00041320: move.b %d1,5(%a4)      ; actual b5 activation writer
arcade_pc 0x00041324: bsr.w 0x41336          ; watchpoint post-PC
```

The source value for the activation is `a4@(4)` plus one. The first activation events show `d1=0x02` for entries 8, 7, 6, and 5, implying source byte `a4@(4)=0x01`; entry 4 first activates with `d1=0x01`, implying source byte `a4@(4)=0x00`.

The observed caller/control path for first activations is:

```text
arcade_pc 0x0003A7B4  bsr.w 0x41F0E
arcade_pc 0x00041F0E  jsr 0x5100A
arcade_pc 0x00041F14  bsr.w 0x40B66
arcade_pc 0x00040B66  loop A5+0x02C8 entries 0..8
arcade_pc 0x00040B80  select A4 = A5+0x02C8 + index*0x40
arcade_pc 0x00040B96  require a4@(0) != 0
arcade_pc 0x00040B9C  bsr.w 0x4096C
arcade_pc 0x00041320  move.b d1,5(a4)
```

Stack breadcrumbs in the first activation events confirm the path: `stack0=00040B6E`, `stack4=00041F18`, `stack8=0003A7B8`.

Arcade first nonzero b5 write-watch events:

| Entry | Cycle | post-PC | arcade_WRAM | Write value | A4 | State | Mode | `A5+0x0214` |
|---:|---:|---|---|---|---|---|---|---|
| 8 | `48316101` | `0x041324` | `0x0010C4CD` | `0x02` | `0x0010C4C8` | `2/3/0` | `3` | `8` |
| 7 | `54839459` | `0x041324` | `0x0010C48D` | `0x02` | `0x0010C488` | `2/3/0` | `0` | `7` |
| 6 | `65649479` | `0x041324` | `0x0010C44D` | `0x02` | `0x0010C448` | `2/3/0` | `0` | `6` |
| 5 | `74311763` | `0x041324` | `0x0010C40D` | `0x02` | `0x0010C408` | `2/3/0` | `0` | `5` |
| 4 | `127529231` | `0x041324` | `0x0010C3CD` | `0x01` | `0x0010C3C8` | `2/3/0` | `1` | `4` |

Arcade per-frame sampler corroboration:

| Entry | First nonzero frame | b5 progression at first nonzero |
|---:|---:|---|
| 8 | `372` | `00 00 00 00 02` |
| 7 | `421` | `00 00 00 02 02` |
| 6 | `502` | `00 00 02 02 02` |
| 5 | `567` | `00 02 02 02 02` |
| 4 | `966` | `01 1F 01 01 01` |

## Genesis Positive Control and Divergence

The exact mapped Genesis activation writer is present and byte-equivalent in the translated runtime:

```asm
runtime_genesis_pc 0x0004151A: move.b 4(%a4),%d1
runtime_genesis_pc 0x0004151E: addq.b #1,%d1
runtime_genesis_pc 0x00041520: move.b %d1,5(%a4)      ; mapped b5 activation writer
runtime_genesis_pc 0x00041524: bsr.w 0x41536          ; watchpoint post-PC
```

Entry 8 is the positive control: Genesis Build 0205 reaches the mapped writer through the mapped path and writes `0x02` to `Genesis-WRAM 0x00FF04CD`.

```text
EVENT B5_WRITE entry=8 cyc=70839103 pc=041524 addr=00FF04CD size=8 data=00000002 ...
  a4=00FF04C8 a5=00FF0000 state=0002/0003/0000 mode=0003 t214=0008
  stack0=00040D6E stack4=00042118 stack8=0003A9B8
```

Mapped Genesis caller/control path for the positive control:

```text
runtime_genesis_pc 0x0003A9B4  bsr.w 0x4210E
runtime_genesis_pc 0x0004210E  jsr 0x5120A
runtime_genesis_pc 0x00042114  bsr.w 0x40D66
runtime_genesis_pc 0x00040D66  loop A5+0x02C8 entries 0..8
runtime_genesis_pc 0x00040D80  select A4 = A5+0x02C8 + index*0x40
runtime_genesis_pc 0x00040D96  require a4@(0) != 0
runtime_genesis_pc 0x00040D9C  bsr.w 0x40B6C
runtime_genesis_pc 0x00041520  move.b d1,5(a4)
```

Genesis Build 0205 does **not** produce any nonzero b5 activation writes for entries 4, 5, 6, or 7 in the captured 1250-frame window. The only b5 nonzero writes are entry 8 state transitions.

| Entry | Genesis nonzero b5 write-watch result |
|---:|---|
| 4 | none |
| 5 | none |
| 6 | none |
| 7 | none |
| 8 | `0x041524 -> Genesis-WRAM 0x00FF04CD = 0x02`, then later `0x040C1C` state updates |

Genesis per-frame sampler corroboration: entry 8 first becomes nonzero at frame `563`; entries 4..7 remain `0x00` throughout the sampled window.

## Clears and Overwrites

Both environments perform startup/state clears covering these fields:

- Arcade startup clear post-PC `arcade_pc 0x0003AF02`, mapped Genesis post-PC `runtime_genesis_pc 0x0003B102`.
- Gameplay/state clear post-PC `arcade_pc 0x0003A2D4`, mapped Genesis post-PC `runtime_genesis_pc 0x0003A4D4`.

Those clears are not the first divergence. Arcade entries 4..7 are later re-activated by `arcade_pc 0x00041320`; Genesis entries 4..7 are not re-activated by `runtime_genesis_pc 0x00041520` in the captured run. Therefore the Genesis failure is not “writes correctly and is later overwritten” for entries 4..7; it is “nonzero activation write never occurs” for those entries during this runtime window.

## Classification

**First exact proven divergence:** writer-path reachability for entries 4..7.

- Arcade reaches `arcade_pc 0x00041320` with `a4` equal to each actor window for entries 8, 7, 6, 5, and 4, and writes nonzero b5 values.
- Genesis Build 0205 reaches the mapped writer `runtime_genesis_pc 0x00041520` for entry 8 only.
- Genesis Build 0205 never reaches that writer with `a4=0x00FF03C8`, `0x00FF0408`, `0x00FF0448`, or `0x00FF0488` in the captured run.

This rules out the Build 0205 whole-block scratch staging helper as the first cause of the one-lizard limit. The helper stages what the current Genesis actor state makes valid. The missing entries 4..7 fail earlier: their actor `b5` activation/progression path does not execute equivalently before the PC090OJ staging helper consumes the block.

Confidence:

- Exact activation writer PC/path: **CONFIRMED**.
- Exact Genesis mapped writer/path for positive-control entry 8: **CONFIRMED**.
- Entries 4..7 first divergence at activation-writer reachability: **CONFIRMED**.
- Exact upstream branch/table/gate inside the earlier actor update path that prevents entries 4..7 from reaching `runtime_genesis_pc 0x00041520`: **NOT fully pinned in this task**. The next implementation should not patch b5 directly from this evidence alone.

## Smallest Safe Fix Boundary

The smallest safe boundary is **upstream actor activation/progression for block `A5+0x02C8` entries 4..7**, specifically the control/data path that should drive the mapped per-entry update loop:

```text
runtime_genesis_pc 0x0003A9B4 -> 0x0004210E -> 0x00040D66 -> 0x00040D80/0x00040D9C -> ... -> 0x00041520
```

Do not patch `pc090oj_stage_block2c8` to force entries valid. Do not seed `b5`. Do not force records/SAT. The current evidence says the staging helper is downstream of the loss; the safe next implementation/design target must restore why entries 4..7 reach the original actor activation state path in arcade but not in Genesis.

Before an implementation patch, the remaining narrow proof should pin the exact earlier gate/table/source difference that stops entries 4..7 from entering the `0x41520` writer path. Entry 8 is the positive control for any such trace.

## OPEN / KNOWN_FINDINGS Impact

Open issues touched: OPEN-017 and OPEN-024. No issue closed. No new issue opened.

KNOWN_FINDINGS impact: **Option C** - KF-065 refined with Build 0205 writer-provenance evidence. KF-064 remains correct and is not weakened.

## STOP

STOP triggered: **NO** for the evidence task. The requested writer/provenance divergence is proven. Implementation remains deferred because the exact upstream activation gate/table defect is not yet patch-safe.
