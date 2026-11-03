# Build 228 State Machine Trace

## Purpose
Identify exactly why Build 228 started-path frontend execution does not enter the title-producing state path, despite running `genesistan_run_original_frontend_tick()` each frame.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest sections, especially Build 228 started/visible traces)
- `docs/research/build228_visible_output_trace.md`
- `apps/rastan/src/startup_bridge.c`
- `dist/Rastan_228.bin` disassembly (`m68k-elf-objdump`)

## 1) State Machine Identification
Inside `genesistan_run_original_frontend_tick()` (relocated frontend tick body at `0x03A208`):

- Major state variable: `A5+0x0000`
- Substate variable: `A5+0x0002`
- Step variable: `A5+0x0004`

Major dispatch:
- `0x03A256: move.w (0x0000,A5),D0`
- `0x03A25A..0x03A26A`: jump-table dispatch via table at `0x03A26C`

Table decode (`base=0x03A26C`):
- state 0 -> `0x03AC10`
- state 1 -> `0x03AAB8` (title cluster)
- state 2 -> `0x03A35A`
- state 3 -> `0x03AD80`

Title-producing state is therefore major state `A5+0x0000 == 1`.

Current started-path values (already proven in prior run):
- `A5+0x0000 = 0x0002`
- `A5+0x0002 = 0x0000`
- `A5+0x0004 = 0x0000`

`A5+0x0000 = 2` corresponds to the post-title/post-coin progression cluster (evidence: title idle body sets `A5+0x0000=2` at `0x03ABF0` after coin transition).

## 2) Branch Trace
### Branch that should lead to title producers
To run title producers, dispatch must go:
- `A5+0x0000 == 1` -> `0x03AAB8`
- then substate dispatch at `0x03AAC4..0x03AAD8`
- substate 0 target `0x03AADE` executes title init calls:
  - `0x03AADE -> 0x03AFEA`
  - `0x03AAE2 -> 0x03AF5E`
  - `0x03AAE6 -> 0x03B06C`
  - `0x03AAF2 -> 0x05A174`
  - `0x03AAFA/0x03AB0A/0x03AB16/0x03AB1C -> 0x03BD5E`

Those calls are the path that eventually feeds text/tile/sprite output producers.

### Branch actually taken in Build 228 started-path
With `A5+0x0000=2`, major dispatch goes to `0x03A35A`.

State-2 substate dispatch:
- `0x03A366: move.w (0x0002,A5),D0`
- `0x03A36A..0x03A37A`: jump-table via base `0x03A37C`

For `A5+0x0002=0`, first entry is used:
- table[0] displacement `+0x03EA`
- target `0x03A766`
- `0x03A766: nop`
- `0x03A768: rts`

So active state-2/substate-0 returns immediately without running title init/output calls.

## 3) Blocking Condition (Exact)
Why `0x200000 / 0x2001A6 / 0x20034C / 0x200DE2` are not reached:

1. Major-state gate:
- `0x03A256` loads `A5+0x0000`.
- Current value `0x0002` selects `0x03A35A` instead of title cluster `0x03AAB8`.

2. Immediate no-op substate within state 2:
- `0x03A366` loads `A5+0x0002`.
- Current value `0x0000` selects `0x03A766` (NOP/RTS).

This combination prevents execution of title init bodies that call the text/tile producer path (`0x03BD5E` chain) and related title-population helpers.

## 4) First Broken Input (Upstream Cause)
First upstream cause is launcher direct init seeding frontend state to state-2/substate-0/step-0:
- `apps/rastan/src/startup_bridge.c`
  - `genesistan_arcade_workram_words[0] = 2;` (`A5+0x0000`)
  - `genesistan_arcade_workram_words[1] = 0;` (`A5+0x0002`)
  - `genesistan_arcade_workram_words[2] = 0;` (`A5+0x0004`)

That seed drives dispatch into the non-title state branch and then into an immediate NOP/RTS substate target.

## 5) Minimal Fix Target
=== BUILD228_STATE_MACHINE_FIX_TARGET ===
- fix_area: frontend state seed / earliest state transition ownership for `A5+0x0000/+0x0002/+0x0004` before first live frontend tick.
- exact_branch_or_condition: major dispatch at `0x03A256..0x03A26A` currently sees `A5+0x0000=2` and routes to `0x03A35A`; then `0x03A366..0x03A37A` with `A5+0x0002=0` routes to `0x03A766` (NOP/RTS).
- current_wrong_value: `A5+0x0000=0x0002`, `A5+0x0002=0x0000`, `A5+0x0004=0x0000` at started-path frontend entry.
- correct_expected_value: value set/order that routes first live title entry through major-state target `0x03AAB8` (title cluster), not state-2/substate-0 NOP return.
- why_this_blocks_title_execution: title-producing calls are only in the major-state-1 title cluster; current state seed never enters that cluster.
- minimal_change_required: restore correct initial state/transition ownership so state machine naturally reaches major-state-1 title init path before any post-coin/state-2 branch.
- what_must_NOT_be_done: do not manually call producers, do not inject fake tile/sprite data, do not force runtime state mid-frame, do not add shims/trampolines/NOP bypasses.

## Conclusion
Title code never runs in the observed Build 228 started-path because frontend tick is seeded into major-state 2 and substate 0, and that path dispatches to `0x03A766` (`NOP; RTS`) instead of entering major-state 1 (`0x03AAB8`) where title producers execute.
