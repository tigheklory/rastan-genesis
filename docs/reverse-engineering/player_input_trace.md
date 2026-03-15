# Rastan Player Input And Render Trace

This note records the confirmed control path from live input toward the player
world position and candidate sprite render hooks.

## Confirmed control path

### 1. Raw controls are read from the input ports

At `0x3a778` the program reads:

- `0x390001`
- `0x390003`

It swaps them for cocktail mode when needed and stores the selected byte at:

- `a5 + 0x16`

This is an early global input byte, not yet actor-specific.

### 2. Gameplay uses a latched control word

The main gameplay update at `0x41f0e` calls into a state machine that branches
on a latched control word at:

- `0x10d37a`

Key examples:

- `0x51e24`
- `0x51ed2`
- `0x51f10`
- `0x5206e`

Observed bit usage:

- bit `0`: one directional/action branch
- bit `1`: opposite directional/action branch
- bit `2`: another directional branch
- bit `3`: another directional branch

The exact button mapping still needs to be named, but these are live gameplay
control bits, not menu-only inputs.

### 3. Input drives movement accumulators

The control state machine updates these globals:

- `a5 + 0x1262`
- `a5 + 0x1264`
- `a5 + 0x1266`
- `a5 + 0x1268`

These are consumed at `0x517fa` and converted into step amounts for four motion
paths:

- `0x53850`
- `0x538ea`
- `0x53956`
- `0x539c2`

### 4. Those motion paths update the player world coordinates

The player world position is now confirmed:

- `a5 + 0x10be`: player X
- `a5 + 0x10c0`: player Y

These routines clamp and update those coordinates while consulting collision
state:

- `0x53850`
- `0x538ea`
- `0x53956`
- `0x539c2`

The collision/ground flags they consult are in:

- `a5 + 0x10ce`
- `a5 + 0x10d0`
- `a5 + 0x10d8`
- `a5 + 0x10da`

This is the strongest confirmed player-specific path so far.

## Candidate render hooks

### Direct copy from player world position into actor coordinates

At `0x447b6`:

- `a5 + 0x10be -> a4 + 0x32`
- `a5 + 0x10c0 -> a4 + 0x30`
- then it clears `a4 + 0x07`

This is the first direct, confirmed copy from player world coordinates into an
actor render position.

### Actor handler that uses that copy

At `0x447ce`, actor states:

- `10`
- `11`
- `18`

jump straight to `0x447b6`.

For other states the same handler sets timeout/visibility behavior and may call
`0x448b2`.

This makes the `0x447ce` family a strong candidate for the player body actor or
an immediately player-linked visual actor.

### Where that actor family is processed

`0x449b4` iterates the actor list at:

- `a5 + 0x02c8`

and, for nearby active actors, calls:

- `0x447ce`

So the `a5 + 0x02c8` list is one current candidate list containing a
player-linked render actor.

## Palette findings

The generic sprite builder at `0x3c9e8` checks actor byte:

- `a4 + 0x27`

If bit `6` is set there, it uses that byte when composing sprite attributes.

Confirmed writers affecting that attribute byte include:

- `0x45c04`: `bset #7, a4 + 0x27`
- `0x45376`: `bset #7, a4 + 0x27`
- `0x45388`: `bset #7, a4 + 0x27`

Important limitation:

- I have not yet found the player's final palette bank value.
- I have only confirmed that actor byte `+0x27` participates in final sprite
  attributes, and that several routines set bit `7`.

So the grayscale placeholder in `hello-rastan` is still wrong, but the path to
the real palette is now narrowed to the actor attribute side rather than raw
graphics.

## Current conclusion

What is now proven:

- live gameplay input reaches a latched control word at `0x10d37a`
- that drives movement state
- movement updates the confirmed player world coordinates at
  `a5 + 0x10be / a5 + 0x10c0`
- at least one actor render path copies those exact coordinates into an actor
  at `0x447b6`

What still needs to be pinned down:

1. which concrete actor entry is the main player body
2. which `a4 + 0x06` state corresponds to neutral standing
3. the exact palette bank / attribute bits for that actor

## Start-of-level spawn findings

The level-start player position is also directly written by scripted setup
code, not only by the movement paths.

### Title / start handoff

The game-start flow is now clearly separate from the stage-entry drop logic.

At `0x3a79c`, the program dispatches on `a5 + 0x04` as a high-level mode
state.

- mode `0` at `0x3a7ae` keeps running updates and waits for the start/commit
  transition
- mode `1` at `0x3a832` waits for a later gameplay-ready condition
- mode `2` falls onward into another controller path at `0x55ddc`

The key transition out of the pre-game/title-credit phase happens at
`0x3a7fa`:

- it clears the `0x02c8` actor list
- calls `0x45dfa`
- calls `0x3b902`
- sets `a5 + 0x13ac = 8`
- sets `a5 + 0x04 = 1`

That is a strong stage-initialization handoff point.

### Stage initialization chain

Once gameplay/stage setup is active, `0x501ea` runs a structured init chain:

- `0x50248`: selects the stage id into `a5 + 0x013e`
- `0x502cc`: installs stage-specific pointer tables
- `0x503dc`: stage background/system setup
- `0x504fa`: per-stage player/world spawn table load
- `0x5053a`: clears and seeds player/drop/script state globals

This separates the investigation into two useful linked phases:

1. title / credit / start transition into stage init
2. stage init into staged player entry/drop

### `0x5052e`

This routine loads per-stage setup data from a table at `0x050850` and writes:

- `a5 + 0x10ae`
- `a5 + 0x10b0`
- `a5 + 0x10b8`
- `a5 + 0x10ba`
- `a5 + 0x10be` (player X)
- `a5 + 0x10c0` (player Y)

### Main gameplay / entry update loop

The active gameplay loop at `0x51024` is now a useful anchor for the early
stage-entry investigation.

Per frame it:

- latches current controls into `a5 + 0x137a`
- updates side-entry thresholds through `0x5126e`
- runs `0x52bb6`, `0x52b38`, and `0x52b4a`
- runs the stage-entry/event controller at `0x54a2c`

That matters because it shows the `0x1376 / 0x13c6` logic is part of the
normal gameplay update, not a disconnected setup stub.

### `0x52b4a` is a small scripted byte-stream feeder

This routine only runs while:

- `a5 + 0x1376 == 1`

It chooses one pointer from the table at `0x052c1c` based on:

- `a5 + 0x1384`
- or, when that is zero, a byte at `0x10c118`

It then reads pairs of bytes:

- duration -> `a5 + 0x1372`
- command  -> `a5 + 0x1373`

and exposes the live command each frame as:

- `a5 + 0x137a`

When it reaches a zero terminator, it clears the script-active flag:

- `a5 + 0x1376 = 0xff`

So this path is best understood as a tiny timed command stream for the entry
sequence, not a sprite-frame decoder.

### `0x54a2c / 0x54a32` is a stage-entry event dispatcher

`0x54a2c` clears:

- `a5 + 0x13c4 = 0xff`

then `0x54a32` checks whether:

- `a5 + 0x13c6 == 1`

If not, it calls `0x54dd2`, then walks two RAM-resident 4-entry tables at:

- `0x10d2a8`
- `0x10d2c8`

Each entry contains:

- enable flag
- command id
- Y value
- X value

The command id selects handlers from the jump tables at:

- `0x550a8`
- `0x550c0`

The important correction is what those handlers do. The ones checked so far
mostly:

- change global stage/camera values such as `a5 + 0x013a`
- trigger subsystems like `a5 + 0x12f0`, `a5 + 0x130e`, `a5 + 0x1296`
- set motion/effect globals like `a5 + 0x1266 / 0x1268`
- gate event state through `a5 + 0x1388`, `a5 + 0x13c4`, `a5 + 0x1418`

This makes `0x54a32` useful for understanding the scripted stage-entry scene,
but it is not a strong lead for the player body sprite itself.

### `0x59f92` is tied to the same event state

`0x59f92` watches:

- `a5 + 0x1388`

and writes a small 4-word record to:

- `0x10c170`

using ids `0x0a6a .. 0x0a6d` when `a5 + 0x1388` is `0..3`.

This reinforces that `a5 + 0x1388` belongs to the stage-entry/event system
rather than a player sprite family/state selector.

## Refined conclusion

The start-of-level drop path is still useful, but the latest trace changes its
role in the investigation:

1. `0x5126e` proves when the player reaches the scripted side-entry threshold.
2. `0x52b4a` feeds a timed command stream for that sequence.
3. `0x54a32` dispatches stage-entry events and subsystem triggers from RAM
   tables.

So the drop path is a reliable player-only timing anchor, but not the direct
path to the player body sprite. The next likely useful target is the actor
group that reacts to these entry flags while also carrying real sprite-family
and palette fields.
- `a5 + 0x10c0` (player Y)

So the initial player spawn point is stage-table driven.

### `0x505fc`

This seeds temporary staging coordinates:

- `a5 + 0x1354 = 0x00a0` (`160`)
- `a5 + 0x1356 = 0x0080` (`128`)

These look like the pre-drop scripted position values.

### `0x52816`

This routine copies those staged coordinates into the live player world
position:

- `a5 + 0x1354 -> a5 + 0x10be`
- `a5 + 0x1356 -> a5 + 0x10c0`

and then computes a map pointer from the current world origin. This is one of
the strongest current hooks for the deterministic start-of-level drop sequence.

### `0x528ca`

This updates the staged coordinates in small steps from input/state bits:

- `0x5291e`: `a5 + 0x1354 -= 2`
- `0x52918`: `a5 + 0x1354 += 2`
- `0x5290c`: `a5 + 0x1356 -= 2`
- `0x52912`: `a5 + 0x1356 += 2`

So the staged spawn/drop position is a live scripted coordinate pair, not a
single one-shot constant.

### `0x5126e`

This watches the live player X position and promotes the spawn/drop sequence
into mode flags:

- for one case, when `a5 + 0x10be >= 216`, it sets:
  - `a5 + 0x1376 = 1`
  - `a5 + 0x1384 = 1`
  - `a5 + 0x13c6 = 1`
- for the mirrored case, when `a5 + 0x10be <= 80`, it sets:
  - `a5 + 0x1376 = 1`
  - `a5 + 0x1384 = 2`
  - `a5 + 0x13c6 = 1`

That strongly suggests a left/right stage-entry gate tied to the player's live
world X position, which matches the observed start-of-level drop behavior.
