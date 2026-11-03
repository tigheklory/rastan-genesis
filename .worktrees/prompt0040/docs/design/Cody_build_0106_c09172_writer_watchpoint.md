# Cody - Build 0106 C09172 Writer Watchpoint Evidence

**Date:** 2026-06-26  
**Type:** Runtime evidence capture only  
**Target:** Build 0106 Genesis ROM in MAME Genesis driver  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`  
**ROM SHA256:** `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`  
**Scope:** Locate the writer to HW `0x00C09172` only. No source/spec/tool/ROM/build changes. No bookmark cycle. No inserted diagnostics. No fix design.

## Phase 0

Classification: **EXTENDING**. The task follows the Build 0106 / OPEN-017 diagnostic thread. `RULES.md`, `ARCHITECTURE.md`, and the latest `AGENTS_LOG.md` context were read before running the capture.

Architecture compliance: **PASS**. The run used the Build 0106 Genesis ROM under MAME's Genesis driver, not the original arcade Rastan driver. This is a read-only watchpoint capture of the translated runtime.

## Evidence Artifacts

Trace directory:

`states/traces/build_0106_c09172_writer_watchpoint_20260626_092815/`

Files:

- `c09172_watch_exact.cmd` - MAME debugger script with exact write watchpoint `wp 00c09172,2,w`.
- `mame_exact_stderr.log` / `mame_exact_stdout.log` - first attempted run; aborted because Qt debugger could not connect to display.
- `mame_exact_offscreen_stderr.log` / `mame_exact_offscreen_stdout.log` - successful offscreen debugger run.
- `debug.log` - MAME debugger transcript with the watchpoint hit.

Command form used for the successful run:

```bash
QT_QPA_PLATFORM=offscreen timeout 120s /usr/games/mame genesis \
  -cart /home/tighe/projects/rastan-genesis/dist/rastan-direct/rastan_direct_video_test_build_0106.bin \
  -window -video none -sound none -skip_gameinfo \
  -homepath /home/tighe/projects/rastan-genesis/build/mame/home \
  -debug -debuglog \
  -debugscript /home/tighe/projects/rastan-genesis/states/traces/build_0106_c09172_writer_watchpoint_20260626_092815/c09172_watch_exact.cmd
```

The first run without `QT_QPA_PLATFORM=offscreen` failed before runtime execution due to Qt display setup. The successful run exited via the debugger after the exact watchpoint fired.

## Watchpoint Result

Exact watchpoint:

```text
wp 00c09172,2,w
```

Debugger transcript:

```text
WP_C09172 cyc=33672816 pc=3ACF2 addr=C09172 data=2749 mem=0 \
  d0=0 d1=46 d2=0 d3=2E d4=C d5=0 d6=0 d7=FFFF \
  a0=3C4E2 a1=C09BA8 a2=C01C18 a3=50082 a4=0 a5=FF0000 a6=0 \
  sp=FEFFEC sr=2700 stack0=3A274 stack4=20040003 stack8=A27E2000

Stopped at watchpoint 1 writing 2749 to C09172 (PC=0003ACEA)
```

Important PC note: the formatted `pc=3ACF2` field in the action is the post-instruction PC. MAME's stop line identifies the actual faulting/writing instruction PC as `0x0003ACEA`.

## Exact Writer

**Exact writer runtime_genesis_pc:** `0x0003ACEA`

**Instruction:**

```asm
3acea:  33fc 2749 00c0 9172   movew #0x2749,0x00c09172
```

**Effective write:** `HW 0x00C09172`, size word, data `0x2749`.

The write is an absolute raw C-window/VDP-aliased write. It is not routed through `staged_fg_buffer`, not routed through the `0x70794` staging store, and not a Genesis helper write.

## Disassembly Window

Genesis disassembly around the writer:

```asm
3acbc:  6100 108a       bsrw 0x3bd48
3acc0:  7040            moveq #64,%d0
3acc2:  6100 1084       bsrw 0x3bd48
3acc6:  7041            moveq #65,%d0
3acc8:  6100 107e       bsrw 0x3bd48
3accc:  7042            moveq #66,%d0
3acce:  6100 1078       bsrw 0x3bd48
3acd2:  7043            moveq #67,%d0
3acd4:  6100 1072       bsrw 0x3bd48
3acd8:  7044            moveq #68,%d0
3acda:  6100 106c       bsrw 0x3bd48
3acde:  7045            moveq #69,%d0
3ace0:  6100 1066       bsrw 0x3bd48
3ace4:  7046            moveq #70,%d0
3ace6:  6100 1060       bsrw 0x3bd48
3acea:  33fc 2749 00c0 9172  movew #10057,0xc09172
3acf2:  3b7c 00a0 002c movew #160,%a5@(44)
3acf8:  3b7c 0002 0004 movew #2,%a5@(4)
3acfe:  4e75            rts
3ad00:  4eb9 0007 1488 jsr 0x71488
3ad06:  4e75            rts
```

Arcade source comparison from the same mapped segment:

```asm
3aae4:  7046            moveq #70,%d0
3aae6:  6100 1060       bsrw 0x3bb48
3aaea:  33fc 2749 00c0 9172  movew #10057,0xc09172
3aaf2:  3b7c 00a0 002c movew #160,%a5@(44)
3aaf8:  3b7c 0002 0004 movew #2,%a5@(4)
3aafe:  4e75            rts
```

## Register Snapshot

From the watchpoint action:

| Register | Value |
|---|---:|
| D0 | `0x00000000` |
| D1 | `0x00000046` |
| D2 | `0x00000000` |
| D3 | `0x0000002E` |
| D4 | `0x0000000C` |
| D5 | `0x00000000` |
| D6 | `0x00000000` |
| D7 | `0x0000FFFF` |
| A0 | `0x0003C4E2` |
| A1 | `0x00C09BA8` |
| A2 | `0x00C01C18` |
| A3 | `0x00050082` |
| A4 | `0x00000000` |
| A5 | `0x00FF0000` |
| A6 | `0x00000000` |
| SP | `0x00FEFFEC` |
| SR | `0x2700` |

Stack samples at `SP`:

- `stack0 = 0x0003A274`
- `stack4 = 0x20040003`
- `stack8 = 0xA27E2000`

The top stack word `0x0003A274` is consistent with the arcade VBlank/master-dispatch return marker in this code path. This instruction is inline inside the title producer tail; no immediate BSR/JSR caller return address for the individual absolute write is present on the stack.

## JSON Address Mapping

Mapping source: `build/rastan-direct/address_map.json`.

Segment containing `runtime_genesis_pc 0x0003ACEA`:

```json
{
  "genesis_start": "0x03AB20",
  "genesis_end_exclusive": "0x03AD00",
  "size_bytes": 480,
  "kind": "arcade_copy",
  "arcade_start": "0x03A920",
  "arcade_end_exclusive": "0x03AB00",
  "source": "whole_maincpu_copy",
  "identity_offset": 512
}
```

Using this JSON segment mapping, `runtime_genesis_pc 0x0003ACEA` corresponds to `arcade_pc 0x0003AAEA`. This is a segment-relative JSON mapping, not an independent global offset assumption.

Classification from map: **`arcade_copy`**. The instruction is copied arcade code still performing an absolute write to `0x00C09172`.

## Routed vs Raw Determination

**Verdict:** raw C-window / PC080SN-style write.

Evidence:

- The watchpoint is hit by `0x3ACEA: movew #0x2749,0x00c09172`.
- The segment kind is `arcade_copy`, not `genesis_only` helper code and not an `opcode_replace` patched site.
- The effective address is the VDP-aliased hardware address `0x00C09172` directly.
- No staging-buffer address (`0xFF501A..0xFF601A`) participates in the write.

This is the concrete Build 0106 writer to the BlastEm-reported address. It is not the previously ruled-out staged FG helper path.

## STOP Status

STOP triggered: **NO**.

The exact watchpoint worked after forcing the MAME debugger UI offscreen. The writer PC was captured and mapped through `address_map.json`.

## Non-Actions

- No source changes.
- No spec changes.
- No tool changes.
- No ROM/build changes.
- No bookmark cycle.
- No diagnostic code inserted.
- No fix designed or implemented.
- No issue opened or closed.

## Open / Known Findings Impact

- OPEN-017: context extended with runtime proof that Build 0106 reaches a raw copied arcade absolute write at `runtime_genesis_pc 0x0003ACEA` to `HW 0x00C09172`.
- OPEN-001: context only; this is a rendering/VDP-aliased raw-write symptom.
- OPEN-015: not touched.
- `KNOWN_FINDINGS.md`: no update in this task.
