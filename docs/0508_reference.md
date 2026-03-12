# Rastan `0x0508` Actor System Reference

This note focuses only on the `a5 + 0x0508` actor list.

Use it when the question is:

- how the player-linked control/state cluster behaves
- which `0x0508` states mirror live player position
- which constructors feed the list
- why this system is important but still not proven as the visible body

## Why `0x0508` Matters

`0x0508` is one of the clearest player-linked systems in the game.

Why:

- it has a direct player-coordinate display copy at `0x428b2`
- it owns a large shared live-update cluster for states `4..9`
- it repeatedly spawns or bridges to helper/subpart groups

What it does not prove yet:

- that `0x0508` itself is the final visible player body

## Main Structure

Important routines:

- `0x420e6`: update pass over 20 entries
- `0x42102`: per-entry dispatcher
- `0x41fac`: pre-dispatch class-gated state shaper
- `0x4213a`: state jump table
- `0x42838`: shared update cluster for states `4..9`
- `0x428b2`: direct copy from player coordinates into display coordinates
- `0x42d26`, `0x42dfa`: animation descriptor loaders
- `0x42e38`: generic animation player

Common entry size:

- `0x40` bytes

Important fields:

- `+0x00`: active flag
- `+0x05`: runtime state
- `+0x06`: class / subtype
- `+0x16`: X
- `+0x1a`: Y
- `+0x30`: display Y
- `+0x32`: display X
- `+0x3e`: animation selector
- `+0x528`: back-pointer used by some helper relationships

## State Dispatch

The `0x4213a` jump table currently resolves as:

- `0 -> 0x42bc8`
- `1, 2 -> 0x42c4e`
- `3 -> 0x42220`
- `4..9 -> 0x42838`
- `10 -> 0x425ea`
- `11 -> 0x421d8`
- `12 -> 0x42162`
- `13 -> 0x424f6`
- `14 -> 0x424c8`
- `15 -> 0x42abc`
- `16 -> 0x4221a`
- `17 -> 0x421cc`
- `18 -> 0x421d2`
- `19 -> 0x42422`

Practical implication:

- `0x42838`
- `0x421d8`
- `0x42162`
- `0x425ea`

are the main `0x0508` branches worth following.

## Shared Live-Update Cluster

The most important routine is:

- `0x42838`

This is shared by states:

- `4`
- `5`
- `6`
- `7`
- `8`
- `9`

What it does:

- loads animation descriptors through `0x42d26` or `0x42dfa`
- advances them through `0x42e38`
- runs state-specific logic for selected cases

Special case:

- state `8` also uses the frame loop at `0x42932`

## Direct Player Coordinate Copy

The strongest `0x0508` ownership hook is:

- `0x428b2`

This writes:

- `player X -> a4 + 0x32`
- `player Y - 16 -> a4 + 0x30`

Important difference from `0x02c8`:

- `0x0508` uses `player Y - 16`
- `0x02c8` uses the direct player Y at `0x447b6`

That difference is one reason `0x0508` may be a control/body-adjacent mirror
or upstream owner rather than the final visible body.

## Constructor Seed

Known setup seed:

- `0x45342`

This initializes the first `0x0508` entries into:

- state `8`
- or state `9`

and sets bit `7` in:

- `a4 + 0x27`

Why this matters:

- it is clearly player-linked
- but seeding a player-linked state is not the same as proving visible-body
  ownership

## Important State-Specific Branches

### `0x41fac..0x42056`

This runs from the `0x42102` dispatcher before the main state jump table.

It waits until:

- `a4 + 0x07 == 0`
- `a4 + 0x05 != 3`
- `a4 + 0x05 < 15`

Then it only continues for classes:

- `8..12`
- `15`
- `18`

It rotates and masks:

- `a4 + 0x21`

then uses player-relative comparisons to rewrite:

- `a4 + 0x05`

into a small state set:

- `4`
- `5`
- `6`
- `7`
- `8`
- `9`

Interpretation:

- this is a real class-to-state bridge inside `0x0508`
- class `18` is especially interesting because it overlaps one of the
  bridge-owned `0x02c8` classes at `0x447ce`

### `0x42162`

This branch:

- copies coordinates from the back-pointer at `a4 + 0x528` into:
  - `a4 + 0x16`
  - `a4 + 0x1a`
- then advances animation through `0x42e38`

Interpretation:

- helper/subpart or mirrored-object behavior

### `0x421d8`

This branch can spawn:

- `0x0748 state 15`

through:

- `0x457d0`

after:

- `0x4092e`

when:

- `a4 + 0x06 == 15`

Interpretation:

- very important for proving multipart relationships
- not proof of main visible player body

### `0x4236a -> 0x423b2 -> 0x42380`

Known helper seed path used earlier in the harness for `0x05c8`.

Interpretation:

- useful bridge from `0x0508`
- not the body itself

## Why `0x0508` Produced False Positives

This system is close to the player and close to helper spawns, which makes it
easy to misread.

It can:

- follow the live player position
- advance animation-like state
- spawn helper/subpart actors

But that still does not prove that the list is the final visible player body.

## What This System Can Prove

Good for proving:

- player-linked state ownership
- animation descriptor behavior
- helper/subpart spawn relationships
- back-pointer relationships through `+0x528`

Not good enough by itself for proving:

- the final visible player body actor
- the final family/frame/tile-base tuple on screen

## Best Next Step

Use `0x0508` as an upstream ownership map, not as the final render owner.

The most productive route is:

1. trace which `0x0508` path feeds or gates a live `0x02c8` actor
2. prove the `0x02c8` class/state owner
3. only then decode final sprite output
