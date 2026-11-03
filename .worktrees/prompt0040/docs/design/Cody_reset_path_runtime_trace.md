# Cody — Runtime Trace for Reset Path Disambiguation

**Agent:** Cody  
**Type:** Runtime Trace / Verification (no fixes, no implementation)  
**Build context:** current `rastan-direct`

## Architecture compliance

Read and followed:
- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS_LOG.md` (latest entries)
- `docs/design/Andy_reset_path_root_cause.md`
- `docs/design/Andy_rastan_direct_runtime_decomposition.md`

This report is runtime capture only. No code path was modified.

## Address-space legend

- `arcade_pc`: arcade ROM address space
- `runtime_genesis_pc`: executing PC in translated Genesis ROM
- `HW_ADDRESS`: runtime memory address on Genesis (`0x00FFxxxx` WRAM)

## Capture method

Source evidence: `debug.log` entries prefixed with `RPTRACE`.

Configured breakpoints (arcade targets requested):
- `arcade_pc 0x0003AB6E` (Path A caller)
- `arcade_pc 0x0003AB8A` (Path B caller site 1)
- `arcade_pc 0x0003B092` (Path B caller site 2)
- `arcade_pc 0x00039F9E` (reset trampoline entry)

Log confirms breakpoint setup and trace start:
- `debug.log:4-27` (`Breakpoint ... set`)
- `debug.log:28` (`RPTRACE setup_done`)

## Phase 1 — Breakpoint hits (first occurrence scope)

### `arcade_pc 0x0003AB6E`
- Hit: **NO**
- Evidence: no `RPTRACE ... arcade_pc=0x03AB6E` entries in `debug.log`

### `arcade_pc 0x0003AB8A`
- Hit: **YES**
- First hit: `debug.log:30`
  - `runtime_genesis_pc=0x03AD8C`
  - `HW_ADDRESS 0x00FF002C = 0x00A0`
  - `HW_ADDRESS 0x00FF0012 = 0x0000`
- Last observed hit: `debug.log:1514`
  - `HW_ADDRESS 0x00FF002C = 0x0000`
  - `HW_ADDRESS 0x00FF0012 = 0x0000`

### `arcade_pc 0x0003B092`
- Hit: **NO**
- Evidence: no `RPTRACE ... arcade_pc=0x03B092` entries in `debug.log`

### `arcade_pc 0x00039F9E`
- Hit: **NO**
- Evidence: no `RPTRACE reset` and no `arcade_pc=0x039F9E` entries in `debug.log`

### Branch site observed during run
- `arcade_pc 0x00039FA8` (`BCS`) hit repeatedly
- First branch log: `debug.log:32`
  - `taken=1`, `ff002c=0x00A0`, `ff0012=0x0000`, `condA=0`, `condB=0`
- Last branch log: `debug.log:1516`
  - `taken=1`, `ff002c=0x0000`, `ff0012=0x0000`, `condA=1`, `condB=0`

## Phase 2 — Values at deciding branch

No valid "deciding branch immediately before first `arcade_pc 0x39F9E`" exists in this capture because first `0x39F9E` was never reached.

Nearest observed candidate branch (`arcade_pc 0x039FA8`, `BCS`) values:
- `HW_ADDRESS 0x00FF002C = 0x0000` (last observed)
- `HW_ADDRESS 0x00FF0012 = 0x0000` (last observed)
- Branch condition instruction: `BCS`
- Branch taken: **YES** (`taken=1`)

Condition evaluation at observed branch sample:
- Path A condition (`0x00FF002C == 0`): **MET** (at last sample)
- Path B condition (`0x00FF0012 >= 256`): **NOT MET**

## Phase 3 — Disambiguation conclusion

**Conclusion: Insufficient runtime evidence (STOP).**

Reason:
- The current capture does not reach first `arcade_pc 0x39F9E`, so caller-immediately-before-first-reset-entry cannot be proven.

What additional capture is required to resolve:
1. Extend trace window until first `arcade_pc 0x39F9E` hit occurs, while keeping the same four caller/reset breakpoints active.
2. At that first `0x39F9E` hit, record the immediately preceding caller hit (`0x3AB6E` vs `0x3AB8A`/`0x3B092`) and the same two memory words.
3. Keep branch taken/not-taken logging for `BEQ`/`BCS` in the final pre-reset sequence.

## Required status summary

- Build produced: **NO**
- ROM path: **N/A**
- Root cause confirmed: **NO** (disambiguation blocked by missing first `0x39F9E` occurrence)
- Fix implemented: **NO**
- No unrelated changes: **YES** (runtime-trace reporting only)
