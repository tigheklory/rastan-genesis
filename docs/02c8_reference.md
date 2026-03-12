# Rastan `0x02c8` Actor System Reference

This note focuses only on the `a5 + 0x02c8` actor list.

Use it when the question is:

- which routines own the `0x02c8` list
- where `0x02c8` entries receive player coordinates
- which branches are strongest for the visible player body
- which fields are loaded before `0x02c8` frame builders run

## Why `0x02c8` Matters

`0x02c8` remains the strongest current candidate for the real visible player
body path.

Why:

- it is part of a normal render-facing actor system
- it has a direct player-coordinate copy at `0x447b6`
- it feeds the dominant frame builders at `0x47140` and `0x473b8`

For the bridge region that feeds and gates this list, also see:

- [docs/bridge_visibility_reference.md](/home/tighe/projects/rastan-genesis/docs/bridge_visibility_reference.md)

For direct constructor and reseed paths that touch this list, also see:

- [docs/02c8_constructor_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_constructor_reference.md)

For the live frame-selection side, also see:

- [docs/02c8_frame_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_frame_reference.md)

For the tile-/transition-driven state cluster, also see:

- [docs/02c8_state_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_state_reference.md)

## Main Structure

Important routines:

- `0x4092e`: reset helper
- `0x4096c`: replacement / reseed gate
- `0x40b66`: list update pass
- `0x40b80`: per-entry dispatcher
- `0x40bc2`: state jump table
- `0x40c62`: repack / fallback matcher on `+0x3e` and `+0x752`
- `0x41cfa`: state/class record loader
- `0x41e22`: render pass into `0xd00460`
- `0x45248`: small generic seed helper used by direct `0x02c8` seeds
- `0x4677c`: direct fixed-slot `0x02c8` seeder
- `0x449b4`: proximity / visibility pass

Common entry size:

- `0x40` bytes

Important fields:

- `+0x00`: active flag
- `+0x05`: runtime state
- `+0x06`: class / subtype
- `+0x0c`: gating / timer-like field used by bridge logic
- `+0x16`: X
- `+0x1a`: Y
- `+0x30`: display Y in player-linked copies
- `+0x32`: display X in player-linked copies
- `+0x3e`: animation selector

## State Dispatch

The `0x40bc2` jump table currently resolves as:

- `0 -> 0x41180`
- `1, 2 -> 0x473b8`
- `3..12 -> 0x47140`
- `13, 14 -> 0x473b8`
- `15 -> 0x40ccc`
- `16 -> 0x40c08`
- `17 -> 0x4684e`
- `18 -> 0x47140`
- `19..33`: further branches at `0x40e4c` and above

Practical implication:

- `0x47140`
- `0x473b8`
- `0x4684e`

are the highest-value `0x02c8` body-facing branches.

## Record Loader

The key setup helper is:

- `0x41cfa`

It copies an 8-byte state/class record into:

- `+0x02`
- `+0x08`
- `+0x0d`
- `+0x0e`
- `+0x0f`
- `+0x10`
- `+0x11`
- `+0x13`

The source record table begins at:

- `0x41d26`

Why this matters:

- `0x02c8` frame logic is not choosing fields from scratch
- it depends on state/class records preloaded by `0x41cfa`

## Player Ownership Hook

The strongest direct ownership proof remains:

- `0x447b6`

This writes:

- `player X -> a4 + 0x32`
- `player Y -> a4 + 0x30`
- `a4 + 0x0c = 0xff`
- `a4 + 0x07 = 0`

The gate before it is:

- `0x447ce`

That gate keys on:

- `a4 + 0x06`

Direct player-coordinate copy is only taken for classes:

- `10`
- `11`
- `18`

This is one of the most important facts in the whole reverse-engineering pass.

## Constructor-Side Seeds

The most important new positive constructor-side evidence is:

- `0x4677c`
- `0x46790`
- `0x4c706`
- `0x4ca34`

What is now proven:

- there are real direct `0x02c8` seeds that do not go through the earlier
  helper-heavy family-1 constructors
- `0x45248` is the common small initializer used by those seeds
- late event code reuses the same direct seed path

What is not yet proven:

- that one of those direct seeds is the real visible player-body owner
- that one of them becomes a bridge-owned class `10`, `11`, or `18` entry
- where the seeded `0x02c8` slot itself picks up a body-facing runtime state
- whether the direct `0x02c8` seed is anything more than one member of a wider
  generic fixed-slot event family

## Non-Direct Branch From The Same Gate

When `0x447ce` does not take the direct copy path, it can fall into:

- `0x448b2`

That branch forces:

- `a4 + 0x07 = 0`
- `a4 + 0x08 = 0xff`
- `a4 + 0x3c = 0`
- `a4 + 0x05 = 15`
- `a4 + 0x09 = 1`

Important caution:

- visible results downstream from this area are not automatically body-owned
- some are fallback / forced-state results

## `0x40c62`

This is a useful negative-ownership bridge inside `0x02c8`.

It only runs when:

- `a5 + 0x1410 == 1`

Then it:

- saves the caller's:
  - `a4 + 0x3e`
  - `a4 + 0x752`
- scans the first 9 `0x02c8` entries
- looks for another active, non-hidden, non-state-15 entry with matching:
  - `+0x3e`
  - `+0x752`
- if it finds one, it calls:
  - `0x44852`

Interpretation:

- this is a repack/fallback matcher
- it does not explain class ownership
- it is another reason visible `0x02c8` results can still be non-body fallback
  behavior even when they look player-adjacent

## Concrete `0x02c8` Lead: `0x4684e`

`0x4684e` is the clearest currently documented body-facing `0x02c8` branch.

What it does:

- reloads state/class records through `0x41cfa`
- handles several `a4 + 0x3e` cases
- derives facing at `0x468d0`
- writes frame-selection-related fields before later frame builders run

Useful adjacent routines:

- `0x469e8`: startup gate, not body ownership by itself
- `0x46a22..0x46a5c`: `0x05c8` list scan with `0x447f0` on `0x0708`
- `0x46ab4..0x46b2e`: `0x0748` strip updater, useful but helper-heavy

Why `0x4684e` matters:

- it is concrete
- it sits inside the real `0x02c8` lifecycle
- it is more body-facing than the helper-family candidate paths we kept hitting

## Live Frame Builders

The dominant visible frame builders are:

- `0x47140`
- `0x473b8`

These are the places where `0x02c8` actor state becomes final frame behavior.

Current interpretation:

- `0x41cfa` loads the state/class records
- `0x4684e` and nearby branches select / modify state-facing fields
- `0x47140` / `0x473b8` produce the live frame behavior

## What Is Still Missing

The unresolved bridge is still:

- which constructor seeds the live `0x02c8` actor with class `10`, `11`, or
  `18`

Until that is proven, we still cannot say which `0x02c8` entry is the real
player body with confidence.

Known constructor-side false leads now live in:

- [docs/constructor_reference.md](/home/tighe/projects/rastan-genesis/docs/constructor_reference.md)

Known direct but not-yet-proven `0x02c8` seeds now live in:

- [docs/02c8_constructor_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_constructor_reference.md)

## Best Next Step

Trace the constructor path that creates a live `0x02c8` entry with:

- class `10`
- class `11`
- or class `18`

Then follow that exact entry through:

- `0x447b6`
- `0x4684e`
- `0x47140` or `0x473b8`

That is the shortest proof-based route to the visible player body.
