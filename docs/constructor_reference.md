# Rastan Constructor Reference

This note collects the constructor and seed paths that have already been
identified clearly enough to classify.

Use it when the question is:

- where actor class/state bytes are actually written
- which constructors are helper-only
- which constructors are still missing for the real `0x02c8` body owner

## Why This Note Exists

The current bottleneck is not animation decode or tile decode.

The bottleneck is constructor ownership.

We already know that `0x447ce` only gives direct player-coordinate ownership to
`0x02c8` classes:

- `10`
- `11`
- `18`

So the next proof step is to find who writes those classes into a live
body-facing `0x02c8` actor.

## Known Direct Class Writers

These writes are now confirmed in the disassembly:

- `0x41b3a -> a4 + 0x06 = 1`
- `0x423d6 -> a4 + 0x06 = 17`
- `0x42406 -> a4 + 0x06 = 23 + slot index`
- `0x444c0 -> a4 + 0x06 = stage-seeded class from 0x444e0`
- `0x45356 -> a4 + 0x06 = 8`
- `0x45364 -> a4 + 0x06 = 9`
- `0x4565a -> a4 + 0x06 = 11`
- `0x457dc -> a4 + 0x06 = 15`
- `0x45aa6 -> a4 + 0x06 = 13`
- `0x45b4a -> a4 + 0x06 = 10 or 18`
- `0x45b72 -> a4 + 0x06 = 11`
- `0x45b9e -> a4 + 0x06 = 11`
- `0x45bca -> a4 + 0x06 = 11`

This is enough to classify the obvious false leads.

## Helper-Only Or Helper-Heavy Constructors

### `0x45642`

This builds the `0x07c8` strip:

- sets a countdown in `a5 + 0x0212`
- walks `a5 + 0x07c8`
- writes:
  - `a4 + 0x21`
  - `a4 + 0x06 = 11`
- calls:
  - `0x4543e`
  - `0x45cfc`
  - `0x45c0c`

Important detail:

- `0x45c0c` positions from live player coordinates

Interpretation:

- strongly player-linked helper strip
- not proof of the visible body

### `0x457b2`

This builds the `0x0748` strip:

- walks 5 entries at `a5 + 0x0748`
- each entry gets:
  - `a4 + 0x38 = 1`
  - `a4 + 0x21 = 0`
  - `a4 + 0x06 = 15`
- calls:
  - `0x4543e`
  - `0x45cfc`

Then it hardcodes positions:

- X from `152 + slot * 4`
- display X fixed at `160`
- Y fixed at `16`
- display Y fixed at `24`

Interpretation:

- definitely helper/subpart/effect-like
- explicitly not the visible player body

### `0x45b2e`

This is the multipart helper constructor.

It seeds:

- `0x06c8`
- `0x09c8`
- `0x0988`
- `0x0948`

Class writes:

- primary slot gets:
  - class `10`
  - or class `18` when stage `2`
- secondary slots get:
  - class `11`

It also writes:

- `a4 + 0x38` from the high byte of the same `d0` used for class

Then it calls:

- `0x4543e`
- `0x45cfc`
- `0x45be8`

Important detail:

- `0x45be8` positions from `a5 + 0x071e / 0x0722`, not live player world
  coords

Interpretation:

- this explains why classes `10`, `11`, and `18` kept showing up in the notes
- but this constructor still looks helper-only, not body-owned

## Stage-Family Seeders

### `0x4449e`

This seeds fixed actor slots:

- usually `a5 + 0x0708`
- stage `5` uses `a5 + 0x0648`

Class comes from the stage table at `0x444e0`:

- `1 -> 0x0e`
- `2 -> 0x13`
- `3 -> 0x14`
- `4 -> 0x15`
- `5 -> 0x10`
- `6 -> 0x17`

Interpretation:

- real constructor
- useful for stage-linked actors
- already disproven as the player body when used by itself

## Direct `0x02c8` Seeds

### `0x4677c`

This is the clearest currently documented direct seeder for `0x02c8`.

It starts at:

- `lea a5 + 0x02c8, a4`

and branches on:

- `a5 + 0x013e`

It uses:

- `0x45248`

to seed the first `0x02c8` slot and, for some ranges, also:

- `0x0308`
- `0x0348`
- `0x0388`

Interpretation:

- not helper-strip construction
- real direct `0x02c8` seeding
- stage/event driven, not yet proven player-body ownership

### `0x46790`

This is the shared direct-entry helper inside `0x4677c`.

It normalizes `d0/d1` and then calls:

- `0x45248`

Because later event code calls `0x46790` directly, it should be treated as a
real `0x02c8` seed entry point, not just an internal branch label.

### `0x4c706` And `0x4ca34`

These are event-side direct `0x02c8` seeds.

`0x4c706`:

- seeds `0x02c8` through `0x46790` with:
  - `d2 = 72`
  - `d3 = 0x0179`

`0x4ca34`:

- seeds `0x02c8` through `0x46790` with:
  - `d2 = 116`
  - `d3 = 0x0d06`
- also writes:
  - `a4 + 0x38 = 2`

Interpretation:

- these are the first concrete direct `0x02c8` seeds that survive outside the
  earlier helper-only constructor families
- still not proof of the player body, but no longer dismissible as just helper
  false leads
- the wider `0x46300..0x46776` trace now shows that `0x46790` is a generic
  fixed-slot seed path reused across many stage/event-owned slots, so direct
  `0x02c8` seeding alone is not body ownership

## `0x0508`-Facing Constructors

### `0x45342`

Known player-linked seed for the first `0x0508` entries.

Class writes:

- `8`
- `9`

Interpretation:

- clearly player-linked
- still not the final visible body proof

### `0x423bc..0x423f2`

Known helper seed path:

- writes:
  - active flag
  - family `1`
  - state `17`
  - class `17`
- calls `0x4543e`

Interpretation:

- helper or stage/event cluster
- not the body

## Negative Result That Matters

At this point, the obvious direct class writers for:

- `10`
- `11`
- `18`

all belong to helper-heavy paths, especially:

- `0x45642`
- `0x45b2e`
- `0x457b2`

That is why the harness kept landing on wrong family-1 actors.

The newer `0x4677c` / `0x46790` direct `0x02c8` seeds change the constructor
picture, but they still do not solve the missing bridge-owned class proof.

## What Is Still Missing

Still missing:

- the constructor that seeds a live body-facing `0x02c8` entry with class
  `10`, `11`, or `18`

- or proof that a direct `0x4677c` / `0x46790` seeded entry later becomes one
  of those bridge-owned classes

That missing constructor is now the main reverse-engineering target.

## Best Next Step

Trace backward from the `0x02c8` owner side instead of forward from known
helper constructors:

1. start at `0x447ce`
2. follow the concrete `0x02c8` branch at `0x4684e`
3. identify which earlier code path can produce its live class/state tuple
