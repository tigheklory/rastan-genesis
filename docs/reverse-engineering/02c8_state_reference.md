# Rastan `0x02c8` State Cluster Reference

This note focuses on the `0x02c8` state cluster around:

- `0x40b66..0x41cfa`

Use it when the question is:

- how `0x02c8` state dispatch really works
- which branches are stage-tile driven
- where state transitions and side spawns happen before the live frame builders

## Why This Region Matters

This region sits between constructor ownership and live frame logic.

It answers:

- how a live `0x02c8` actor enters different runtime states
- how map/tile probes influence those states
- which branches spawn or trigger side effects before `0x4684e`, `0x47140`,
  and `0x473b8`

## Top-Level Update Pass

Main entry:

- `0x40b66`

What it does:

- clears `a5 + 0x0214`
- iterates 9 entries in the `0x02c8` list
- calls `0x40b80` per entry
- calls `0x40b52` after each entry

Per-entry dispatcher:

- `0x40b80`

Per-entry preconditions:

- entry must be active
- then it calls `0x4096c`
- if `a4 + 0x03 == 0`, it clears bit `0` in `a4 + 0x20`
- then dispatches by `a4 + 0x05`

## State Dispatch Overview

Known dispatch highlights:

- `0 -> 0x41180`
- `1, 2 -> 0x473b8`
- `3..12 -> 0x47140`
- `13, 14 -> 0x473b8`
- `15 -> 0x40ccc`
- `16 -> 0x40c08`
- `17 -> 0x4684e`
- `18 -> 0x47140`
- `19..33` branch into the `0x41362` cluster and its callees

Interpretation:

- `0x02c8` is not just a simple actor list
- many states enter a large tile-/stage-driven transition cluster before they
  reach the steady-state frame builders

## `0x41180`

This is the state-0 controller.

Behavior:

- decrements `a4 + 0x1c`
- every two ticks calls `0x41064`
- if `d1 != 0`, jumps into the large transition cluster at `0x41362`

If not:

- checks stage-specific limits via `0x4114a`
- computes probe positions from:
  - `a5 + 0x0216`
  - `a5 + 0x0218`
  - stage scroll globals
- probes map/tile data through `0x53a2e`

Then it:

- compares the probed tile code against `a4 + 0x0d`
- chooses whether to keep scanning or transition

Interpretation:

- state `0` is strongly tile-driven
- it looks like environment/contact/placement logic, not a simple animation
  state

## `0x41064`

This helper scans nearby map/tile data.

It:

- requires `a4 + 0x03 != 0`
- requires `a4 + 0x30 != 0`
- initializes scan coords in:
  - `a5 + 0x0216`
  - `a5 + 0x0218`
  - `a5 + 0x021a`
- loops over tilemap data through `0x53a2e`
- searches for a tile matching:
  - `a4 + 0x0d`
  - and `a4 + 0x2f`

If found, it writes:

- `a5 + 0x0222`
- `a5 + 0x0226`

Interpretation:

- this is one of the main tile-probe helpers feeding state transitions

## `0x41362`

This is the big transition cluster entered from `0x41180`.

Common entry behavior:

- stores `%a0` into `a4 + 0x0e`
- sets:
  - `a4 + 0x07 = 1`
  - `a4 + 0x09 = 1`

Then it dispatches based on the current tile/value in `d0`.

Important practical point:

- this cluster is not a constructor in the normal sense
- it is a transition/state-rewrite cluster based on current environment/tile
  conditions

## Important Transition Cases

### `0x4145a`

On matching tile/state:

- calls `0x41492`
- offsets X based on `a4 + 0x30` and bit `0` of `a4 + 0x20`
- sets:
  - `a4 + 0x05 = 34`
  - `a4 + 0x01 = 41`
- calls `0x45418`

### `0x414d4`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 33`
  - `a4 + 0x01 = 39`
- positions from `a5 + 0x0216 / 0x0218`
- calls `0x45418`

Also contains side-spawn branches through:

- `0x43f52`

### `0x41596`

On matching tile/state:

- may trigger sound `0x13`
- sets:
  - `a4 + 0x05 = 26`
  - `a4 + 0x01 = 7`
- calls `0x45418`
- calls `0x4354e`

### `0x41614`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 19`
- positions from `a5 + 0x0216 / 0x0218`
- chooses frame `3` or `5`
- calls `0x45418`

### `0x4167e`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 20`
  - `a4 + 0x01 = 1`
- calls `0x45418`

### `0x416b2`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 21`
- positions vary by stage and current tile
- computes frame near `0xf5`
- may call `0x41752`

### `0x41792`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 22`
  - `a4 + 0x01 = 0xf1`
- calls `0x45418`

### `0x417d2`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 23`
  - `a4 + 0x01 = 0xef`

### `0x41834`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 24`
  - `a4 + 0x01 = 0x91`
- calls `0x41854`
- calls `0x45418`

### `0x418a2`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 25`
  - `a4 + 0x01 = 0x87`
- sets `a4 + 0x1c = 7`
- calls `0x45418`

### `0x418f4`

On matching tile/state:

- may trigger sound `0x13`
- sets:
  - `a4 + 0x05 = 26`
  - `a4 + 0x01 = 0x7b`
- calls `0x45418`

### `0x419e0`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 27`
  - `a4 + 0x01 = 0x79`

### `0x41a14`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 28`
  - `a4 + 0x01 = 0x77`

### `0x41a48`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 29`
  - `a4 + 0x01 = 0x75`
- calls `0x41ada`
- calls `0x45418`

### `0x41b32`

On matching tile/state:

- writes:
  - `a4 + 0x06 = 1`
- positions from `a5 + 0x0216 / 0x0218`
- copies `0x20` bytes from `a5 + 0x0588` into the actor
- calls `0x4092e`

Interpretation:

- concrete class writer
- but clearly not the player-body class we need

### `0x41b6c`

On matching tile/state:

- sets:
  - `a4 + 0x05 = 30`
  - `a4 + 0x01 = 0x70`
- uses helper `0x41b90`

### `0x41bca`

On matching tile/state:

- calls `0x41c1e`
- calls `0x41c60`
- sets:
  - `a4 + 0x08 = 0xff`
  - `a4 + 0x05 = 32`
- calls `0x41bee`

## Side-Spawn Pattern

A recurring pattern in this cluster is:

- save `%a4`
- write a small count to `a5 + 0x0286`
- switch `%a4` to another fixed slot
- call:
  - `0x43f52`
  - or `0x43f4e`
- restore `%a4`
- set small flags in the `0x02a4..0x02c6` range

Interpretation:

- many `0x02c8` transition states trigger side actors or helper slots
- that makes this cluster rich in side effects, but still not a clean body
  constructor region

## Practical Conclusion

The key new result is:

- much of the `0x02c8` middle state space is driven by map/tile transition
  logic
- not by the helper constructors we were already chasing

The side-effect-heavy subset of that logic is now documented in:

- [docs/02c8_transition_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/02c8_transition_reference.md)

That means the missing player-body proof may not be a simple constructor at
all. It may be:

- a state transition into a class/state tuple already present in `0x02c8`
- then later claimed by the bridge logic at `0x447ce`

## Best Next Step

Keep tracing where live `0x02c8` entries acquire or change:

- class `10`
- class `11`
- class `18`

inside or adjacent to this state cluster, instead of assuming those classes
must come from the obvious helper constructors.
