# Cody - Build 0092 Title-Screen First Failing Layer Trace

**Date:** 2026-06-20  
**Type:** Snapshot-based runtime measurement only  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0092.bin`  
**ROM SHA256:** `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`  
**Scope:** Existing Build 0092 only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No script modification. No bookmark cycle. No Start/C/A crash work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-028, KF-013, KF-011, KF-010, KF-004, KF-006, and KF-001 as context only. Rediscovery-hazard HIGH findings touched: KF-028, KF-013, KF-011, KF-010. Open issues touched: OPEN-001, OPEN-016, OPEN-015 context. No contradiction detected.

## Snapshot Methodology

- MAME debugger workflow only; no source instrumentation and no script modifications.
- VBlank exit / handoff target: `runtime_genesis_pc 0x00070100` (end of `_vblank_service`, immediately before handoff to arcade VBlank at `0x0003A208`).
- Snapshot command: repeated `go 70100` to the 600th VBlank handoff, then debugger `dump` commands.
- Stable window basis: prior M1-M4 audit characterized frames ~590-610 as steady no-input (`83` VDP writes/frame, `2` MODE2 writes/frame, `1/1` VBlank entry/handoff).
- Snapshot run status: `0`; exited via debugger after dumps.

## Evidence Artifacts

Primary dump directory: `states/traces/build_0092_title_screen_first_failing_layer_20260620_205816/`

- `mame_snapshot_commands.cmd` - debugger command file used for the snapshot
- `layer0_wram_state_ff0000.txt` - title/arcade WRAM state sample
- `layer1_flags_ff4000.txt` - dirty flags and staging pointers
- `layer1_staged_bg_buffer_ff401a.txt` - full BG staging buffer (`2048` words)
- `layer1_staged_fg_buffer_ff501a.txt` - full FG staging buffer (`2048` words)
- `layer1_tile_vram_lut_0f1f2c.txt` - tile VRAM LUT dump
- `layer1_attr_lut_0f9f2c.txt` - attribute LUT dump
- `layer1_staging_analysis.json` / `layer1_staging_analysis.md` - reduced analysis
- `genesis_exec_summary.txt` / `genesis_exec_trace.log` - existing MAME Lua trace copies

## Layer 0 - Title-State Execution Reached

**Result: PASS.** Runtime reached the stable no-input window without crash/reset. The MAME Lua trace reaches frame `000600` and continues to frame `000630` before debugger exit. The WRAM state dump shows the title/master state cell at `WRAM 0x00FF0000 = 0x0000`, with later title sub-state words populated (for example first words `0000 0001 0002 ...`). This matches the prior stable no-input title-state window used by M1-M4.

## Layer 1 - Title-Producer Staging

**Result: FAIL. This is the first failing layer.**

At the VBlank handoff snapshot, both visible-plane staging buffers are empty:

| Buffer | Words | Non-zero words | Non-zero rows |
|---|---:|---:|---|
| `staged_fg_buffer` (`WRAM 0x00FF501A`) | `2048` | `0` | none |
| `staged_bg_buffer` (`WRAM 0x00FF401A`) | `2048` | `0` | none |

Direct dump evidence:

```text
FF501A:  0000 0000 0000 0000 0000 0000 0000 0000
...
FF600A:  0000 0000 0000 0000 0000 0000 0000 0000
```

```text
FF401A:  0000 0000 0000 0000 0000 0000 0000 0000
...
```

Dirty flags are also clear in `layer1_flags_ff4000.txt`:

```text
FF4000:  0000 0000 0000 0000 0000 00C0 0000 00C0
```

The LUT dumps are not empty: `layer1_tile_vram_lut_0f1f2c.txt` contains `16384` words with `2325` non-zero entries, and `layer1_attr_lut_0f9f2c.txt` contains the expected attribute-line values (`0000`, `2000`, `4000`, ...). This points to producer/staging output absence, not an absent LUT file.

Because Layer 1 fails, the gated procedure stops here. Layers 2-4 were not dumped.

## Gated Layers

- Layer 0 (title-state execution reached): **PASS**
- Layer 1 (title-producer staging): **FAIL**
- Layer 2 (VBlank commit to VRAM): **NOT REACHED**
- Layer 3 (pattern/palette availability): **NOT REACHED**
- Layer 4 (VDP display configuration): **NOT REACHED**

## First Failing Layer

**Layer 1 - Title-producer staging.** The stable title state is reached, but the title-screen producers do not leave any title/logo/text cells in `staged_fg_buffer` or `staged_bg_buffer` by VBlank exit.

## Interpretation Boundary

This task does not prove which producer/helper instruction is wrong. It proves the first failing layer: before VBlank commit, there is no staged title-screen content to commit. The next task should fix the title producer/staging path so arcade title producers write real title-screen cells into the existing WRAM staging buffers.

## Deferred

- Start/C/A crash: not investigated.
- OPEN-015 crash-handler defects: not investigated.
- `0x0003ACEA` one-shot writer: not investigated; not directly implicated by the Layer 1 failure.
- Broader unhooked-writer survey: not performed.

## OPEN / KNOWN_FINDINGS Impact

OPEN-001 and OPEN-016 remain open. No issues opened or closed. KNOWN_FINDINGS impact: **Option C proposed** - refine KF-028 to record that Build 0092 reaches stable title-state timing but first fails at Layer 1, with both BG/FG staging buffers empty at VBlank exit. `KNOWN_FINDINGS.md` was not modified.

## Recommended Next Task

Bounded implementation task: fix the title producer/staging path for the title screen. Start from the Build 0092 title glyph/text producer path and its staging hook behavior; prove which expected title producer call should populate `staged_fg_buffer`/`staged_bg_buffer`, why it currently leaves both buffers empty, and patch that cause without changing VBlank ownership or commit architecture.

## STOP

STOP triggered: **NO**. The first failing layer was identified, and the gated trace stopped at Layer 1.
