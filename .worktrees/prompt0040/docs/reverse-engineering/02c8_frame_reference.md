# Rastan `0x02c8` Frame Logic Reference

This note focuses on the live frame-selection side of the `0x02c8` actor
system.

Use it when the question is:

- how a live `0x02c8` actor chooses frame codes
- which branches are active after record loading
- where facing, timers, and state-driven frame changes are applied

## Why This Note Matters

The constructor and bridge notes tell us who might own a `0x02c8` actor.

This note covers the next step:

- what happens after a `0x02c8` actor is live
- how it becomes a concrete frame code for the sprite builder

The highest-value routines are:

- `0x4684e`
- `0x47140`
- `0x473b8`

## `0x4684e`

This is a concrete `0x02c8` update branch and one of the strongest body-facing
leads currently documented.

### `a4 + 0x3e == 2 or 8`

If:

- `a4 + 0x3e == 2`
- or `a4 + 0x3e == 8`

then on first entry:

- if `a4 + 0x07 == 0`
  - it reloads records through `0x41cfa`
  - then derives facing through `0x468d0`

After that it calls:

- `0x3ceb0`

For `a4 + 0x3e == 2`, it selects `a4 + 0x01` from a short range around:

- base `0x93`

using `a4 + 0x0e`.

For `a4 + 0x3e == 8`, it:

- writes `a4 + 0x22`
- uses `a4 + 0x0e`
- chooses a frame in the range around:
  - base `0x4d`

### Other `a4 + 0x3e` values

If `a4 + 0x3e` is not `2` or `8`:

- it loads record set `16` through `0x41cfa`
- derives facing through `0x468d0`
- runs `0x4691e`
- masks `a4 + 0x0e` with `7`
- selects frame from the table at `0x46916`
- adds base `0x6e`

Interpretation:

- `0x4684e` is not a simple one-frame branch
- it owns a real small state machine for frame and motion behavior

## `0x468d0`

This is the facing helper used by `0x4684e`.

It:

- reads actor X from `a4 + 0x16`
- masks to `0x1ff`
- compares against live player X at `a5 + 0x10be`

Then writes:

- `a4 + 0x02 = 1` if actor X is left of player X
- `a4 + 0x02 = 0` otherwise

Interpretation:

- this is explicit facing derivation from player-relative position
- that makes `0x4684e` more body-facing than helper-only paths

## `0x4691e`

This is a small motion/timer helper.

Behavior:

- copies `a4 + 0x08 -> a4 + 0x09`
- sets `a4 + 0x07 = 1`
- then advances a countdown / stepper sequence

When the timer runs:

- decrements `a4 + 0x09`
- may decrement `a4 + 0x0e`
- may clear `a4 + 0x07`
- updates `a4 + 0x0d` using `a4 + 0x0f`

It then calls:

- `0x46976`

and adds resulting deltas into:

- `a4 + 0x16`
- `a4 + 0x1a`

Interpretation:

- this is real movement/frame stepping inside the `0x02c8` branch
- not just a static frame assignment

## `0x46976`

This is the delta-table helper used by `0x4691e`.

It indexes a word-pair table at:

- `0x4699e`

and writes signed deltas to:

- `a4 + 0x14`
- `a4 + 0x18`

Important detail:

- X delta is negated when `a4 + 0x02 != 0`

Interpretation:

- this is another facing-sensitive body-motion clue

## `0x47140`

This is the dominant live frame builder for `0x02c8` states `3..12` and `18`.

On first entry:

- if `a4 + 0x07 == 0`
  - reloads records through `0x41cfa` using state `a4 + 0x05`

Then it calls:

- `0x3ceb0`

and branches on:

- `a4 + 0x3e`

### Key `a4 + 0x3e` cases

- `0`: frame range based on `a4 + 0x0e`, around base `0x17`
- `1`: frame range based on `a4 + 0x0d` and `a4 + 0x0e`, around base `0x23`
- `2`: frame range around base `0x93`
- `3`: chooses between ranges around base `0x5f`
- `4`: range around base `0xc9`
- `5`: range around base `0xd0`
- `6`: range around base `0xdd`
- `7`: range around base `0x5f`
- `8`: range around base `0x4d`
- `9`: range around base `0x6e`
- `10`: special-case logic depending on runtime state `a4 + 0x05`
- fallback: range around base `0xb5`

Interpretation:

- `0x47140` is a multi-family frame selector inside one actor family path
- seeing a familiar frame base alone still does not prove body ownership

## `0x4734a`

This is a small timing helper used by `0x473b8`.

Behavior:

- if `a4 + 0x741` and `a4 + 0x2b` are both zero, it exits quickly
- otherwise it halves `a4 + 0x08`
- ensures it does not become zero

Interpretation:

- local animation-timer shaping

## `0x4736a`

This is a collision/proximity-trigger helper used before `0x473b8`.

If:

- `a4 + 0x07 == 0`
- state `a4 + 0x05 < 13`

then it:

- checks the map/collision system through `0x53a2e`
- updates `a4 + 0x074f`
- after 3 hits:
  - writes `a4 + 0x39 = 1`
  - calls `0x447f0`

Interpretation:

- another place where `0x02c8` can be forced into the fallback/bridge logic

## `0x473b8`

This is the dominant live frame builder for `0x02c8` states `1`, `2`, `13`,
and `14`.

On first entry:

- reloads records through `0x41cfa`

Then it branches on:

- `a4 + 0x3e`

Key cases:

- if `a4 + 0x3e == 1`
  - sets `a4 + 0x08 = 4`
  - runs `0x4734a`
  - sets `a4 + 0x0a = 8`
- if `a4 + 0x3e == 10`
  - sets `a4 + 0x08` to `2` or `7` depending on `a4 + 0x2e`
  - runs `0x4734a`
- otherwise:
  - runs `0x4734a`

After that it:

- calls `0x3ceb0`
- clears bit `0` in `a4 + 0x20`
- checks state `a4 + 0x05`
- for most states runs `0x4205c`

Then it uses globals:

- `a5 + 0x0234`
- `a5 + 0x0236`

to compare actor facing and may set bit `0` in:

- `a4 + 0x20`

Interpretation:

- `0x473b8` is live, stateful, and context-sensitive
- it is not just a one-shot frame lookup

## `0x40c62`

This is a useful side branch inside the `0x02c8` system.

When:

- `a5 + 0x1410 == 1`

it scans the `0x02c8` list for another live entry matching:

- the same `a4 + 0x3e`
- the same `a4 + 0x752`
- not inactive
- not state `15`

If it finds one, it calls:

- `0x44852`

Interpretation:

- this is a cross-entry bridge inside `0x02c8`
- useful for understanding when fallback/bridge logic gets triggered between
  related body-facing entries

## Practical Conclusion

The `0x02c8` live frame side is now clearly understood well enough to say:

- `0x4684e`
- `0x47140`
- `0x473b8`

are real, rich frame-selection paths and not just shallow dispatch stubs.

The remaining unknown is still constructor ownership, not frame logic.

## Best Next Step

Keep tracing backward from these live branches until the constructor that seeds
their class/state tuple is proven.

The most useful next proof target is:

- the constructor path that creates the live `0x02c8` class `10`, `11`, or
  `18` owner seen by `0x447ce`
