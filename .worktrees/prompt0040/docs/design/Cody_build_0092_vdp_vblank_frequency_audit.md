# Cody - Build 0092 VDP/VBlank Write Frequency Audit

**Date:** 2026-06-20  
**Type:** Runtime measurement / evidence capture only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0092.bin`  
**ROM SHA256:** `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`  
**Scope:** Existing Build 0092 ROM only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No bookmark cycle. No Start/C/A crash work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-028, KF-013, KF-011, KF-010, KF-004, KF-006, and KF-001 as context only. Open issues touched: OPEN-016, OPEN-001, OPEN-015. No contradiction detected.

## Evidence Artifacts

- Trace directory: `states/traces/build_0092_vdp_vblank_frequency_audit_20260620_105746/`
- Native debugger command file: `mame_debug_watchpoints.cmd`
- Raw native trace: `native_debug_trace.log`
- Extracted events: `native_events.log`
- VDP write events: `vdp_write_events.log`
- VBlank/commit events: `vblank_commit_events.log`
- Reduced analysis: `vdp_vblank_frequency_analysis.json`, `vdp_vblank_frequency_analysis.md`
- Existing Lua summary copy: `genesis_exec_summary.txt`

The run completed with status `0` over `959` MAME frames. No crash occurred.

## M1-M4 Results

- Native events captured: `78,786`
- VDP/VDP-aliased write events: `76,699`
- VBlank entries: `926`
- VBlank handoffs: `925` (final frame truncated by run end)
- Raw scroll/sprite-window watchpoints (`0xC20000`, `0xC40000`, `0xD00000`) fired: `0`
- FG C-window watchpoint fired: `1`

Steady-state samples were stable:

| Window | VDP writes/frame | MODE2 reg1 writes/frame | VBlank entry/handoff |
|---|---:|---:|---:|
| Frames 590-610 (~10s) | `83` every frame | `2` (`0x34`, `0x74`) | `1 / 1` |
| Frames 890-910 (~15s) | `83` every frame | `2` (`0x34`, `0x74`) | `1 / 1` |

This does **not** support extra VBlank commit cycles or repeated display-enable churn. The canonical display-off/display-on pattern appears once per full frame in the sampled steady window.

## Non-Canonical Writer

One non-canonical PC080SN/FG C-window write was observed:

```text
EVENT C_WINDOW_FG_WRITE cyc=31531012 pc=03ACF2 addr=00C09172 size=16 data=00002749 sr=2700
```

The standard Lua summary corroborates it:

```text
fg_cwindow_live count=1 first_frame=246 last_frame=246 first_pc=03ACF2 first_addr=C09172 first_data=2749
```

Disassembly shows the write instruction at `runtime_genesis_pc 0x0003ACEA`; the watchpoint reports the post-instruction PC `0x0003ACF2`:

```asm
3acea: 33fc 2749 00c0 9172  movew #0x2749,0x00c09172
3acf2: 3b7c 00a0 002c       movew #0x00a0,%a5@(44)
```

This is a confirmed remaining direct PC080SN-style C-window write outside `_vblank_service`, but it occurs once in the captured run, not repeatedly per frame.

## M5 Status

The requested VRAM/CRAM/staged-buffer coherence dump at VBlank exit was **not collected**. The existing read-only trace/debugger workflow captured write events and counters, but not synchronized VRAM/CRAM/staged memory snapshots without adding dump scripting or instrumentation. Per the prompt, this is recorded as a STOP-limited measurement gap rather than guessed evidence.

## Assessment

- S2/S3 (extra commit cycles or repeated display-enable toggles): **not supported** by M1-M4.
- S1 (unhooked writer presence): **narrowly supported** by the single direct `0x00C09172` write at `0x0003ACEA`, but not as repeated refresh-frequency churn.
- Primary graphics-output focus should remain on stable no-input rendering: the evidence points away from refresh-frequency chaos and toward staged-data/content correctness, while also preserving the single direct C-window writer as a concrete follow-up item.

## Deferred

- Start/C/A crash: not investigated.
- OPEN-015 crash-handler defects: not investigated.
- No fixes or issue closures.

## OPEN / KNOWN_FINDINGS Impact

OPEN-016 remains open. OPEN-001 remains open. OPEN-015 context only. KNOWN_FINDINGS impact: Option A - no update from this measurement alone; a KF refinement should wait for the next mechanism-level graphics finding.

## STOP

STOP triggered: **YES (limited)** - M5 memory coherence dumps were not collected by the existing read-only trace workflow. M1-M4 were collected successfully and are documented above.
