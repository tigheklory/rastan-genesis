# Rastan Startup And Mode Reference

This note consolidates the title/start/stage-init path.

Use it when the question is:

- how the game leaves the title/credit loop
- where stage init actually begins
- which globals mark the transition into active gameplay
- which parts of the early flow are setup versus scripted entry behavior

## High-Level Mode State

The top-level dispatcher at `0x3a79c` branches on:

- `a5 + 0x04`

Known meanings:

- mode `0`: pre-game / title-credit-start phase
- mode `1`: wait-for-play phase
- mode `2`: later gameplay controller path

Important addresses:

- `0x3a772`: read and latch raw input ports
- `0x3a79c`: top-level mode dispatch
- `0x3a7fa`: commit start / hand off to stage init
- `0x3a832`: wait for gameplay-ready condition

## Title / Credit / Start Phase

In mode `0`, the program keeps running:

- input handling
- early gameplay-style update logic
- start/commit tests

This is why some gameplay-side globals change before active play is fully live.

Important fact:

- this phase is not yet the "real stage" even though some update code is
  already active

## Start Commit Handoff

The important handoff is `0x3a7fa`.

This path:

- clears the `0x02c8` actor list
- calls `0x45dfa`
- calls `0x3b902`
- writes `a5 + 0x13ac = 8`
- writes `a5 + 0x04 = 1`

This is the cleanest known transition out of the title/start phase.

## Wait-For-Play Phase

Mode `1` centers on `0x3a832`.

Known behavior:

- waits for `a5 + 0x10e8 == 16`
- then calls `0x41f5e`
- writes:
  - `a5 + 0x46 = 2`
  - `a5 + 0x1394 = 1`
  - `a5 + 0x13aa = 9`
  - `a5 + 0x04 = 2`

This is the last startup gate before normal active gameplay mode.

## Stage Initialization

Main entry:

- `0x501ea`

Important callees:

- `0x50248`: choose stage id and write `a5 + 0x013e`
- `0x502cc`: install stage-specific pointer tables
- `0x503dc`: stage/background/camera setup
- `0x504fa`: load stage/player spawn record
- `0x5053a`: seed runtime defaults and entry-script globals

## Player Spawn Data

`0x5052e` loads stage-table data from `0x050850` and writes:

- `a5 + 0x10ae`
- `a5 + 0x10b0`
- `a5 + 0x10b8`
- `a5 + 0x10ba`
- `a5 + 0x10be` (`player X`)
- `a5 + 0x10c0` (`player Y`)

This proves the first live player position is stage-table driven.

## Scripted Entry / Drop

Important staging coords:

- `a5 + 0x1354`
- `a5 + 0x1356`

Important routines:

- `0x505fc`: seed staging coords to `160,128`
- `0x52816`: copy staging coords into live player coords
- `0x528ca`: update staged coords in small scripted steps
- `0x5126e`: detect left/right threshold and arm entry flags

Threshold behavior:

- if `player X >= 216`:
  - `a5 + 0x1376 = 1`
  - `a5 + 0x1384 = 1`
  - `a5 + 0x13c6 = 1`
- if `player X <= 80`:
  - `a5 + 0x1376 = 1`
  - `a5 + 0x1384 = 2`
  - `a5 + 0x13c6 = 1`

## Entry Script Controller

`0x52b4a` is a timed command-stream feeder, not a sprite decoder.

It runs only while:

- `a5 + 0x1376 == 1`

It reads small command streams from:

- `0x052c1c`

and updates:

- `a5 + 0x1372`
- `a5 + 0x1373`
- `a5 + 0x137a`

This is useful for player-only timing anchors, but not direct body ownership.

## Stage-Entry Event Dispatcher

`0x54a2c -> 0x54a32` is an event dispatcher for stage-entry logic.

It works from RAM tables at:

- `0x10d2a8`
- `0x10d2c8`

and mostly manipulates:

- stage/camera globals
- event latches
- subsystem triggers

This is scene control, not body-sprite ownership.

## First Active Gameplay Loop

Best anchor:

- `0x41f0e`
- especially `0x51024`

Important calls from that loop:

- `0x5126e`
- `0x52b4a`
- `0x54a32`
- `0x40b66`
- `0x420e6`
- `0x443e0`
- `0x449b4`
- `0x450d8`

This is the best "gameplay is now live" region.

## What This Region Can And Cannot Prove

Good for proving:

- when gameplay starts
- when player coordinates become live
- when scripted entry takes over
- which globals mark the transition into active play

Not good enough by itself for proving:

- the visible player body actor
- the correct sprite family/frame owner
- final palette bits

