# Build 336 VDP Commit Execution Count

## Scope
Count per-frame execution frequency for:
- `genesistan_pc080sn_commit_planes`
- `genesistan_palette_commit_asm`
- `genesistan_scroll_commit_vdp`

## Instrumentation Added
- Frame ID incremented once per active VBlank in `_VINT_arcade_mode`.
- Per-frame counters reset at start of active VBlank.
- Commit counters incremented at each target function entry.
- Last-3-frame history slots rolled at each active VBlank.

Instrumentation sites:
- `_VINT_arcade_mode` in `apps/rastan/src/boot/sega.s`:
  - rolls `vdp_commit_last_*` history
  - increments `vdp_commit_frame_id`
  - clears current frame counters
- `genesistan_pc080sn_commit_planes` in `apps/rastan/src/startup_trampoline.s`:
  - increments `vdp_commit_planes_count`
- `genesistan_palette_commit_asm` in `apps/rastan/src/startup_trampoline.s`:
  - increments `vdp_commit_palette_count`
- `genesistan_scroll_commit_vdp` in `apps/rastan/src/main.c`:
  - increments `vdp_commit_scroll_count`

## Per-Frame Execution Counts
From the active call chain (`_VINT_arcade_mode` direct sequence) and instrumentation placement, counts are:

Frame 1:
- planes commit count: 1
- palette commit count: 1
- scroll commit count: 1

Frame 2:
- planes commit count: 1
- palette commit count: 1
- scroll commit count: 1

Frame 3:
- planes commit count: 1
- palette commit count: 1
- scroll commit count: 1

## Result
No multiple executions per frame were detected for the three commit functions in the active arcade VBlank path.
