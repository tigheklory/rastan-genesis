# Rastan Mode Flow Reference

This note consolidates the major program modes and the best current entry and
exit points for each one.

Use it when the question is:

- where boot ends and title begins
- where full test mode branches off
- which routines drive title, attract, credits, and start
- where gameplay is entered
- which controller handles round transitions or game-over style sequences

This is deliberately split into:

- proven entry and exit points
- best current interpretation of each mode

That keeps the factual anchors separate from the parts that still need more
tracing.

## Core state words

These are the mode words that matter most in the current flow mapping:

- `a5 + 0x00`: high-level front-end / page controller state
- `a5 + 0x02`: substate inside the current page or startup controller
- `a5 + 0x04`: top-level runtime mode dispatch at `0x3a79c`
- `a5 + 0x12`: credits
- `a5 + 0x28`: player-count selection latch
- `a5 + 0x2a`: second player-count / prompt latch
- `a5 + 0x2c`: generic timer used by title/attract/test controllers
- `a5 + 0x34`: gameplay-active / in-stage flag used by several transitions
- `a5 + 0x46`: startup / stage-start branch selector
- `a5 + 0x1394`: meta-controller enable flag
- `a5 + 0x1392`: timer/counter for the `0x55ddc` controller
- `a5 + 0x13aa`: meta-controller substate for `0x55ddc`

## Proven top-level entry points

### Reset and common startup

- reset vector target: `0x03a000`
- first real branch target: `0x03ae86`

`0x03ae86..0x03b05c` is the common startup and basic hardware-test block that
runs on every boot.

Key split:

- `0x03b04e`: test the service/test DIP
- if set: jump to `0x0100`
- if clear: continue through normal startup at `0x03b05c`

### Full test mode

- entry: `0x0100`

This is the detailed test/service program, not the common boot test.

Key anchors:

- `0x052a..0x057c`: memory test over work RAM, `0x200000`, `0xC00000`,
  `0xC08000`, and `0xD00000`
- `0x03a4..0x04a0`: input and DIP display writer into startup text RAM
- `0x0156..0x0162`: steady-state test-mode loop

Current limit:

- the clean exit back to normal gameplay/title is not yet fully proven
- the traced path currently behaves like a self-contained test program

## Runtime mode map from `0x3a79c`

The dispatcher at `0x3a79c` branches on `a5 + 0x04`.

Known top-level meanings:

| `a5 + 0x04` | Entry routine | Best current meaning |
| --- | --- | --- |
| `0` | `0x3a7ae` | pre-game / title-credit-start controller |
| `1` | `0x3a832` | wait-for-play gate after start commit |
| `2` and above | `0x3a860` | later controller path, including round/death transition handling via `0x55ddc` |

This is the cleanest top-level split for the program after startup.

## Title, credits, and attract

### Title/start controller

- top-level entry: `0x3a7ae`
- caller: `0x3a79c` when `a5 + 0x04 == 0`

What it does:

- `0x3a772`: input latch from `0x390001` and `0x390003`
- `0x41f0e`: gameplay-style update still runs during title/start
- checks the start/commit condition

Important exits:

- if start/commit succeeds: `0x3a7fa`
- if an intermediate title/front-end subpage wants control:
  - `0x3a8ac`
  - `0x3a566`
  - `0x3a5bc`

### Credit and player-count pages

Important front-end page anchors:

- `0x3a31c`: credit/instruction page setup
- `0x3a39a`: player-count prompt branch for one of the front-end variants
- `0x3a420`: alternate player-count prompt path
- `0x3a478`: credit/start consumption path
- `0x3a91a`: direct start-button handling that decrements credits and commits a
  start

What is proven here:

- credits are stored in `a5 + 0x12`
- `0x3c2e2` updates the visible credit display
- the code distinguishes one-player and two-player start costs
- the title/front-end pages can branch back to title, deeper selection pages,
  or start commit

### Attract/story pages

Strongest attract-page controller:

- `0x3aa90..0x3ab58`

Important entries:

- `0x3aa54`: insert-coin / button-prompt page
- `0x3aaae`: story page
- `0x3ab00`: chronology / second attract page
- `0x3ab58`: timed cleanup/return path

Proven message-page anchors:

- `0x3aa54` emits message ids `30`, `32`, `18`, `19`
- `0x3aaae` emits message ids `17`, `63..70`
- `0x3ab00` emits message ids `60..62`

Best current interpretation:

- `0x3aa54` is the visible title/insert-coin page
- `0x3aaae` is the first story page
- `0x3ab00` is the second attract page

Exit behavior:

- these pages use `a5 + 0x2c` as their timer
- they fall back into the front-end state machine after timed display

## Start commit and gameplay bring-up

### Start commit

- entry: `0x3a7fa`

This is the cleanest proven handoff out of title/start.

What it does:

- calls `0x469e8`
- clears the `0x02c8` actor list
- calls `0x45dfa`
- calls `0x3b902`
- writes `a5 + 0x13ac = 8`
- writes `a5 + 0x04 = 1`

Exit:

- returns to the top-level dispatcher with mode `1`

### Wait-for-play gate

- entry: `0x3a832`

What it does:

- keeps running `0x3a772` and `0x41f0e`
- waits for `a5 + 0x10e8 == 16`

When the gate opens, it writes:

- `a5 + 0x46 = 2`
- `a5 + 0x1394 = 1`
- `a5 + 0x13aa = 9`
- `a5 + 0x04 = 2`
- then calls `0x41f5e`

Interpretation:

- this is the last proven startup gate before the round-transition controller
  takes over

### Stage initialization

- master entry: `0x501ea`

Important stage-start anchors:

- `0x50248`: choose stage id and write `a5 + 0x013e`
- `0x502cc`: install stage pointer tables
- `0x503dc`: background/map/camera setup
- `0x5049a`: stage-entry default/event globals
- `0x504fa`: load player/stage spawn record
- `0x5053a`: seed runtime defaults

First live player position:

- `0x5052e`: `a5 + 0x10be` player X
- `0x50534`: `a5 + 0x10c0` player Y

### First active gameplay loop

Best gameplay anchor:

- `0x41f0e`
- especially `0x51024`

That loop fans out into:

- `0x40b66` `0x02c8` actor updates
- `0x420e6` `0x0508` actor updates
- `0x443e0` bridge/gating path
- `0x449b4` player-linked `0x02c8` pass
- `0x54a32` stage-entry/event controller

## Transition controllers after gameplay begins

### Front-end/post-page controller around `0x3a566`

Entry:

- `0x3a566`

Dispatch key:

- `a5 + 0x04`

Known cases:

- `0x3a586`: clear `0x0200` page/object block, then `0x3ae5a`, `0x3add8`
- `0x3a5a4`: `0x3ad4c`
- `0x3a5aa`: reset input/front-end words and return to substate `2`

This appears to be a front-end / page-transition helper rather than the main
title/start controller.

### Death/game-over/continue controller

Strongest entry:

- `0x3a614`

What it writes:

- `a5 + 0x1394 = 1`
- `a5 + 0x13aa = 1`
- clears `a5 + 0x1242`
- calls `0x3b902`
- sets `a5 + 0x04 = 6`

Steady-state controller:

- `0x3a6b2 -> 0x55ddc`

Proven substate cluster:

- `0x55e10..0x55f2a` for `a5 + 0x13aa = 1..8`

Best current interpretation:

- this cluster is the death / game-over / continue sequence
- it reuses startup/title display writers and timed waits
- it eventually restores or clears round state and returns control through the
  later mode path

Strong evidence:

- `0x3bb7c` table contains:
  - `PLAYER 1 GAME OVER`
  - `PLAYER 2 GAME OVER`
  - `GAME OVER`
- `0x3a6e8..0x3a742` emits message ids `56`, `55`, and a blanking form of id
  `2`

Current limit:

- the exact moment where "game over" versus "continue" diverges still needs a
  tighter trace

### Round-transition / stage-presentation controller

Strongest entry:

- `0x3a832` writes `a5 + 0x1394 = 1` and `a5 + 0x13aa = 9`

Steady-state controller:

- `0x3a860 -> 0x55ddc`

Proven substate cluster:

- `0x55f58..0x56018` for `a5 + 0x13aa = 9..13`

Best current interpretation:

- this is the round-transition / stage-presentation controller
- it is entered on first game start
- it is probably reused for between-stage presentation later

Strong evidence:

- it is entered immediately after the wait-for-play gate at game start
- it calls stage-number-indexed loaders:
  - `0x56128`
  - `0x561d6`
  - `0x561fe`
  - `0x5632a`
- it clears `0xC08000` and `0xC00000` through `0x561a0`

Known exit:

- `0x55ffe..0x56018`
- clears `a5 + 0x13aa`
- clears `a5 + 0x1394`
- restores `a5 + 0x013e` from `a5 + 0x13b8 - 1`

Current limit:

- the exact user-facing interpretation of every `9..13` substate still needs
  more tracing against real board footage

## Best current mode map

This is the highest-confidence summary we have right now.

| Flow | Proven entry | Main controller | Proven exit / next step |
| --- | --- | --- | --- |
| common startup / boot test | `0x03ae86` | startup hardware init and basic RAM/window test | normal path through `0x03b05c`, test path to `0x0100` |
| full test / service mode | `0x0100` | `0x0156..0x0162` loop | not fully proven |
| title / credits / start | `0x3a79c -> 0x3a7ae` | `0x3a8ac`, `0x3a31c`, `0x3a39a`, `0x3a420`, `0x3a91a` | `0x3a7fa` start commit |
| attract / story pages | `0x3aa54`, `0x3aaae`, `0x3ab00` | `0x3aa90..0x3ab58` | timed fallthrough back into front-end flow |
| gameplay bring-up | `0x3a7fa`, `0x3a832`, `0x501ea` | wait-for-play then stage init | `0x41f0e / 0x51024` live gameplay |
| death / game-over / continue | `0x3a614` | `0x3a6b2 -> 0x55ddc` states `1..8` | later-mode cleanup path around `0x3a6c2..0x3a74e` |
| round / stage presentation | `0x3a832` with `13aa = 9` | `0x3a860 -> 0x55ddc` states `9..13` | clear `1394/13aa`, resume mode `2` |

## Most useful next trace points

- tighten the exact exit path of full test mode from `0x0100`
- separate "game over" from "continue" inside `0x55e10..0x55f2a`
- verify whether `0x55f58..0x56018` is reused for later round transitions or is
  only the first stage-intro path
- trace who calls `0x3a566` and `0x3a5bc` so those front-end transition
  controllers can be named more precisely
