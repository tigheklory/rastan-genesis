# Rastan `0x02c8` Transition And Side-Effect Reference

This note focuses on the secondary `0x02c8` transition branches around:

- `0x4375c..0x441a0`

Use it when the question is:

- what the less-documented `0x02c8` state exits do
- which branches are cleanup/timer logic
- which ones trigger side-slot resets rather than body ownership

## Why This Note Matters

The `0x02c8` state cluster does not only hand off to frame builders.

A large set of branches in the middle state space:

- probe tiles
- mutate frame/tile values
- reset or mark side slots
- force timers and small animation loops

These are important to understand, but they are mostly not clean player-body
ownership proof.

## Common Pattern

Many of these branches begin with:

- `0x40e74`

That helper compares the current tile value fetched from `a4 + 0x0e` against:

- `a4 + 0x0d`

and returns a mismatch flag in:

- `d1`

Interpretation:

- these branches are tile-/transition-sensitive
- not simple constructor code

## `0x43f4e..0x43f86`

This is a side-slot reset helper.

It walks fixed slots starting at:

- `a5 + 0x03c8`

for a count from:

- `a5 + 0x0286`

Per slot:

- if inactive, skips
- if active with state `0`, calls `0x4092e`
- otherwise sets `a4 + 0x39 = 1` and calls `0x447f0`

Interpretation:

- this is a cleanup / forced-transition helper for side actors
- useful for understanding side effects
- not a body constructor

## `0x4375c`

This branch:

- checks stage and tile conditions
- may rewrite:
  - `a4 + 0x0d`
  - `a4 + 0x1e`
  - `a4 + 0x01`
  - `a4 + 0x38`
- otherwise falls back to `0x4092e`

If no immediate tile transition is taken, it enters a small timer loop using:

- `a4 + 0x08`
- `a4 + 0x09`
- `a4 + 0x0b`

Interpretation:

- transition/timer behavior
- not a clean ownership source

## `0x43840`

This branch is another stage- and tile-sensitive transition.

It can:

- reset immediately through `0x4092e`
- or rewrite:
  - `a4 + 0x0d`
  - `a4 + 0x1e`
  - `a4 + 0x38`
  - `a4 + 0x01`

If no immediate transition occurs, it falls into another timer loop on:

- `a4 + 0x08`
- `a4 + 0x09`
- `a4 + 0x0b`

Interpretation:

- another mid-state transition path
- strong on tile behavior, weak on body ownership

## `0x4396a`

This branch:

- stores `a4 + 0x0d` in `a5 + 0x022b`
- calls `0x4103a`
- rewrites:
  - `a4 + 0x1e`
  - `a4 + 0x0d`
  - `a4 + 0x30`
  - `a4 + 0x2f`

Then it enters a longer timer/step loop using:

- `a4 + 0x08`
- `a4 + 0x0b`
- `a4 + 0x1c`
- `a4 + 0x01`

Interpretation:

- substantial transition logic
- still more like stage/tile response than body-owner proof

## `0x43ae6`

This is a simpler tile-reactive branch.

If a tile mismatch is detected:

- only special-case tile `0x60` survives
- otherwise resets through `0x4092e`

On the surviving path it:

- calls `0x4103a`
- writes:
  - `a4 + 0x1e = 0x00f4`
  - `a4 + 0x0d = 0x4f`

If no mismatch:

- frame comes from:
  - masked `a5 + 0x0200`
  - current actor index `a5 + 0x0214`

Interpretation:

- looks more like transitional/environment logic than ownership logic

## `0x43ecc`

This branch is especially important because it directly triggers side-slot
reset behavior.

If the tile mismatch path is taken:

- immediate reset through `0x4092e`

Otherwise:

- runs a timer/loop on:
  - `a4 + 0x08`
  - `a4 + 0x0b`
  - `a4 + 0x1c`

When the actor advances far enough:

- sets `a4 + 0x1c = 0x0100`
- sets `a4 + 0x08 = 2`
- calls:
  - `0x43f4e`
- then writes flags:
  - `a5 + 0x021c = 1`
  - `a5 + 0x02a4 = 1`

Interpretation:

- very important side-effect path
- but what it proves is side-slot reset behavior, not player-body ownership

## `0x43f88`

This branch:

- responds to tile mismatch with stage-sensitive rewrites of:
  - `a4 + 0x0d`
  - `a4 + 0x1e`
- otherwise runs another small timer loop over:
  - `a4 + 0x08`
  - `a4 + 0x09`
  - `a4 + 0x0b`

## `0x44082`

Another tile-reactive branch.

It:

- distinguishes state `24` specially
- rewrites:
  - `a4 + 0x0d`
  - `a4 + 0x1e`
- otherwise runs timer logic similar to neighboring branches

## `0x4415a`

This branch begins with:

- Y-range test around `472..488`
- otherwise falls back to `0x40e74`

It then:

- rewrites `a4 + 0x0d`
- rewrites `a4 + 0x1e`
- uses `a4 + 0x2f` in the selection

Interpretation:

- yet another transition/tile response path

## Practical Conclusion

The important result is not any one branch.

The important result is the pattern:

- the `0x4375c..0x441a0` cluster is dominated by transition, timer, and side-
  effect logic
- several branches call `0x4092e`
- several mutate `a4 + 0x0d`, `a4 + 0x1e`, and `a4 + 0x01`
- at least one branch (`0x43ecc`) clearly resets side slots through `0x43f4e`

So these branches are real and relevant, but they are mostly not the missing
constructor proof for the player body.

## Best Next Step

Treat this cluster as transition support around `0x02c8`, not as the primary
ownership source.

The main proof path remains:

1. identify who creates the live `0x02c8` class `10`, `11`, or `18` entry
2. tie that to the bridge at `0x447ce`
3. then follow it into the live frame logic
