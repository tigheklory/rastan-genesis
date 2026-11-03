# Cody FU1 Playtrace Harness

## Purpose

This document describes the reusable arcade-MAME FU1 logging harness that captures full active PC090OJ descriptor-region writes during a human-played Rastan session.

Scope: tooling only (no game-code/spec/MAME-source changes).

## Files

- `[run_rastan_fu1_playtrace.sh](/home/tighe/projects/rastan-genesis/tools/mame/scripts/run_rastan_fu1_playtrace.sh)`
- `[rastan_fu1_playtrace_debug.cmd](/home/tighe/projects/rastan-genesis/tools/mame/scripts/rastan_fu1_playtrace_debug.cmd)`

## Run Command

From repo root:

```bash
tools/mame/scripts/run_rastan_fu1_playtrace.sh
```

Optional output location:

```bash
tools/mame/scripts/run_rastan_fu1_playtrace.sh --output-dir /absolute/or/relative/path
```

Optional smoke-test environment knobs:

- `FU1_SECONDS_TO_RUN` (passes `-seconds_to_run`)
- `FU1_QT_PLATFORM` (exports `QT_QPA_PLATFORM` for debugger UI environment handling)
- `FU1_MAME_EXTRA_ARGS` (appends additional MAME args)

Example smoke test used in this implementation pass:

```bash
FU1_QT_PLATFORM=offscreen FU1_SECONDS_TO_RUN=4 FU1_MAME_EXTRA_ARGS='-video none -sound none -nothrottle' \
  tools/mame/scripts/run_rastan_fu1_playtrace.sh
```

## MAME Requirements

- MAME target: `rastan` arcade driver
- ROM location: `./roms/rastan.zip`
- MAME version validated: `0.276`
- Native debugger used (`-debug`, no Lua)
- Video capture enabled (`-aviwrite`)

## Debugger Syntax Used

Command file contents are loaded via `-debugscript` and are log-and-continue.

```text
wp d00000,800,w,,{ printf "WP_D00 ..." ; go }
bp 3AD44,,{ printf "BP_03AD44_FILL_PRIMITIVE ..." ; go }
bp 3C9C2,,{ printf "BP_03C9C2_WORD_LOOP ..." ; go }
bp 510EA,,{ printf "BP_510EA_FU1_TARGET ..." ; go }
bp 510F4,,{ printf "BP_510F4_FU1_TARGET ..." ; go }
go
```

Notes:

- Watchpoint region is full active descriptor RAM: `HW_ADDRESS 0x00D00000..0x00D007FF` (size `0x800`).
- Breakpoints are at actual write instructions `arcade_pc 0x03AD44` and `0x03C9C2` plus FU1 targets `0x0510EA` and `0x0510F4`.
- All actions end with `go`, so MAME does not halt on hit.

## Output Directory Pattern

Default pattern:

```text
states/traces/fu1_rastan_playtrace_YYYYMMDD_HHMMSS/
```

Per-run artifacts:

- `fu1_debugger.log` — raw debugger events
- `rastan_fu1_playtrace.avi` — video capture
- `fu1_summary.txt` — post-run summary
- `mame_stdout.log` / `mame_stderr.log` — emulator output
- `rastan_fu1_playtrace_debug.cmd` — copied command file for reproducibility

## Operator Workflow (Tighe)

1. Verify ROM exists: `./roms/rastan.zip`.
2. Launch harness from repo root.
3. During run:
   - Insert coin (`5` by default)
   - Start (`1` by default)
   - Play 2-5 minutes
   - Vary actions/state (movement, combat, transitions) to broaden writer coverage
4. Exit MAME normally (Esc or window/menu close).
5. Share the generated output directory path for downstream analysis.

## Summary Generation Method

After MAME exits, launcher parses `fu1_debugger.log` with `grep`/`awk` to produce `fu1_summary.txt` containing:

- Total writes in `0x00D00000..0x00D007FF`
- Unique writer PCs and per-writer hit counts
- Per-descriptor index write counts (`(addr - 0xD00000) / 8`)
- Writes targeting `0x00D00698`
- Breakpoint hit counts (`0x03AD44`, `0x03C9C2`, `0x510EA`, `0x510F4`)
- Unique post-write values at `0x00D00698`
- Paths to output/video/log artifacts

If a metric cannot be parsed, summary reports `parsing failed for <metric>` without fabricating values.

## Important Limitation / Compatibility Note

On MAME 0.276, `-debuglog` is a boolean flag and does **not** accept a custom path argument. The launcher handles this by:

- running MAME with CWD set to the output directory
- allowing MAME to emit `debug.log` there
- renaming it to `fu1_debugger.log` after exit

This keeps runs reproducible and output-contained.

## Verification Results (This Implementation Pass)

Smoke-run verification completed:

- Launch script executable: YES
- Command file accepted by MAME: YES
- Full-region watchpoint installed: YES (`d00000,800,w`)
- Log-and-continue behavior: YES (session runs without debugger halt on hit)
- Breakpoints installed: YES (`0x03AD44`, `0x03C9C2`, `0x510EA`, `0x510F4`)
- Video capture enabled: YES (`rastan_fu1_playtrace.avi` produced)
- Output directory creation: YES
- Summary generation: YES
- Short test watchpoint events: YES (2007 in 3-second headless smoke run)

## Out-of-Scope

This harness captures evidence only. FU1 classification/port-scope decisions are downstream analysis tasks.
