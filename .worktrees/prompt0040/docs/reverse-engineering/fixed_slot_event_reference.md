# Rastan Fixed-Slot Event Reference

This note documents the event-controller cluster that repeatedly seeds fixed
actor slots through the shared helper at `0x45248`.

It matters because this cluster originally looked like a promising constructor
side path for the visible player body, but the wider trace shows it is better
understood as generic stage/event slot management.

The most important addresses are:

- `0x46216`
- `0x463aa`
- `0x4644c`
- `0x4650e`
- `0x4677c`
- `0x46790`

## Why This Note Matters

The direct `0x02c8` seeder at `0x4677c` is real.

The problem is that it sits inside a much larger family of fixed-slot event
controllers that also seed:

- `0x03c8`
- `0x0408`
- `0x0448`
- `0x0488`
- `0x0308`
- `0x0348`
- `0x0388`

That means:

- direct `0x02c8` seeding is now proven
- but it is not special enough by itself to imply visible-body ownership

## Shared Seed Helper: `0x45248`

All of the controllers below eventually funnel into:

- `0x45248`

That helper writes:

- `+0x00 = 1`
- `+0x03 = 1`
- `+0x04 = 1`
- `+0x0d = d2`
- `+0x1c = 1`
- `+0x1e = d3`
- `+0x1a = 0x0180`
- `+0x20 = 1`
- `+0x21 = d1`
- `+0x2f = d0`

And it does not write:

- `+0x05`
- `+0x06`

That omission is why these controllers still do not solve the player-body
ownership problem by themselves.

## `0x46216`: Event State Machine On `a5 + 0x028a`

This is a staged controller driven by:

- `a5 + 0x028a`

States currently mapped:

- `1 -> 0x46240`
- `2 -> 0x4629e`
- `3 -> 0x462d4`
- `4 -> 0x46342`
- `5 -> 0x46384`

### State `1`: `0x46240`

Seeds:

- `0x0448` through `0x4676e`
- `0x0488` through `0x4676e`

Then calls:

- `0x461ce`

with explicit offsets and pointer literals.

Interpretation:

- fixed-slot scripted setup
- not a clean `0x02c8` constructor

### State `2`: `0x4629e`

Counts emptiness across:

- `0x0308`
- `0x0348`
- `0x0388`
- `0x03c8`
- `0x0408`

If all five are empty, it advances `a5 + 0x028a`.

Interpretation:

- progression gate waiting for a helper cluster to clear
- not ownership logic

### State `3`: `0x462d4`

Seeds:

- `0x0388` through `0x4676e`

Then calls:

- `0x461ce`

and immediately seeds:

- `0x03c8` through `0x46790`

with:

- `d2 = 100`
- `d3 = 0x09f6`

It also writes:

- `a4 + 0x38 = 2`
- `a4 + 0x34 = 32`

Interpretation:

- explicit mixed fixed-slot event setup
- useful because it proves family writes and `0x46790` seeds can coexist in the
  same controller

### State `4`: `0x46342`

Seeds:

- `0x0408` through `0x46790`

Then calls:

- `0x461ce`

and writes:

- `a4 + 0x38 = 2`
- `a4 + 0x34 = 32`

Interpretation:

- same generic fixed-slot event pattern
- not a body-facing proof

### State `5`: `0x46384`

Seeds:

- `0x0308`
- `0x0348`

through `0x46790`, then clears:

- `a5 + 0x02a4`

and advances `a5 + 0x028a`.

Interpretation:

- multi-slot event fan-out
- still generic

## `0x463aa`: Event State Machine On `a5 + 0x0288`

This is another small progression controller.

It operates on:

- `0x0408`
- `0x0448`

### State `1`: `0x463ca`

Counts emptiness across two slots:

- `0x0408`
- `0x0448`

If both are empty, it advances `a5 + 0x0288`.

### State `2`: `0x46400`

Checks:

- `a5 + 0x049e` in `[256, 264)`

Then seeds:

- `0x0408`

through `0x45248` with:

- `d2 = 89`
- `d3 = 0x0546`

### State `3`: `0x4642c`

Checks:

- `a5 + 0x049e` in `[208, 216)`

Then clears:

- `a5 + 0x02a4`

and seeds:

- `0x0448`

through `0x45248` with:

- `d2 = 90`
- `d3 = 0x0546`

Interpretation:

- spatially gated event spawner
- tightly tied to fixed-slot choreography, not direct player-body ownership

## `0x4644c`: Event State Machine On `a5 + 0x021c`

This controller stages three-slot activity across:

- `0x03c8`
- `0x0408`
- `0x0448`

### State `1`: `0x46470`

Counts emptiness across the three slots above and advances when all are clear.

### State `2`: `0x464a6`

Checks:

- `a5 + 0x049e` in `[200, 208)`

Then seeds:

- `0x03c8`

through `0x45248` with:

- `d2 = 90`
- `d3 = 0x0546`

### State `3`: `0x464d2`

Checks:

- `a5 + 0x03de` in `[200, 208)`

Then seeds:

- `0x0408`

through `0x45248` with:

- `d2 = 91`
- `d3 = 0x0546`

### State `4`: `0x464ee`

Checks:

- `a5 + 0x041e` in `[200, 208)`

Then clears:

- `a5 + 0x02a4`

and seeds:

- `0x0448`

through `0x45248` with:

- `d2 = 92`
- `d3 = 0x0546`

Interpretation:

- another fixed-slot choreography controller
- structured like a local scripted sequence, not a dedicated ownership bridge

## `0x4650e`: Stage-Id Dispatcher On `a5 + 0x0118`

This is the strongest bridge from stage id into the generic fixed-slot seeding
cluster.

It dispatches on:

- `a5 + 0x0118`

and reaches:

- `0x4677c`
- `0x466e0`
- `0x465b2`
- `0x46538`
- plus later far branches at `0x4c312` and `0x4cb9e`

### What It Does

Across those branches it repeatedly seeds combinations of:

- `0x02c8`
- `0x03c8`
- `0x0408`
- `0x0448`
- `0x0488`
- `0x0308`
- `0x0348`
- `0x0388`

using concrete `d2/d3` pairs and occasional writes such as:

- `a4 + 0x30 = 1`
- `a4 + 0x38 = 2`
- `a4 + 0x2f = 1`

Examples:

- `0x46538`: branches by `a5 + 0x013e`, reseeding `0x0488`, `0x0448`,
  and sometimes `0x03c8`
- `0x465b2`: reseeds `0x0488` / `0x0448` pairs for several stage-id windows
- `0x46666`: reseeds a larger cluster including `0x02c8`, `0x0448`, `0x0408`,
  `0x03c8`, and `0x0388`
- `0x466e0`: earlier stage-id branch family that sometimes reaches `0x4677c`

Interpretation:

- `0x4650e` is not a body constructor
- it is a stage-id-controlled dispatcher over the generic fixed-slot seeding
  machinery
- this is the clearest reason the direct `0x4677c` / `0x46790` seeds must not
  be treated as player-body ownership by default

## What This Changes

This trace sharpens the constructor-side picture:

- direct `0x02c8` seeding is real
- but the broader fixed-slot event cluster is now clearly generic
- the `0x02c8` slot participates in stage/event choreography alongside many
  neighboring fixed slots

That means the remaining ownership problem is still downstream:

- where the seeded `0x02c8` slot gets `+0x06`
- which runtime state it receives
- whether that combination reaches `0x447ce` as a class `10`, `11`, or `18`
  owner

## Best Next Step

The next proof target is still:

1. find where a live `0x02c8` seed picks up `+0x06`
2. show whether that seed reaches `0x447ce`
3. separate that path from the generic fixed-slot event controllers above
