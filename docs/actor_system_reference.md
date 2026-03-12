# Rastan Actor System Reference

This note collects the actor-list structure in one place.

It is meant to answer:

- which list a routine operates on
- which lists are plausible player-body owners
- which lists are mostly helpers/effects
- which code paths bridge between lists

## Common Actor Facts

Most active object lists in the current investigation use `0x40`-byte entries.

Frequently used fields:

- `+0x00`: active
- `+0x05`: runtime state
- `+0x06`: class / subtype
- `+0x16`: X
- `+0x1a`: Y
- `+0x1e`: tile base
- `+0x20`: draw priority source
- `+0x21`: slot/frame helper field in several constructors
- `+0x27`: sprite attribute bits
- `+0x30`: display Y in player-linked copies
- `+0x32`: display X in player-linked copies
- `+0x38`: sprite family
- `+0x3e`: animation selector

## `a5 + 0x02c8`

Role:

- strongest current candidate for the real visible player body

Main routines:

- `0x40b66`: list update pass
- `0x40b80`: per-entry dispatcher
- `0x41cfa`: state/class record loader
- `0x41e22`: render pass to `0xd00460`
- `0x449b4`: proximity / player-linked pass

Key body-facing hook:

- `0x447b6`
  - `player X -> a4 + 0x32`
  - `player Y -> a4 + 0x30`

Key class gate:

- `0x447ce`
  - direct player-coordinate copy only for classes `10`, `11`, `18`

Main live frame builders:

- `0x47140`
- `0x473b8`

Important branch now identified:

- `0x4684e`
  - reloads records through `0x41cfa`
  - derives facing through `0x468d0`
  - chooses frame bytes from `a4 + 0x3e` and related fields

Current status:

- structure is good enough to target next
- harness does not yet seed this list in a body-facing way
- dedicated note:
  [docs/02c8_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_reference.md)

## `a5 + 0x0508`

Role:

- player-linked control/state cluster
- possible upstream owner or mirror of visible-body logic

Main routines:

- `0x420e6`: update pass
- `0x42102`: per-entry dispatcher
- `0x4213a`: state jump table
- `0x42838`: shared update path for states `4..9`
- `0x428b2`: player-coordinate display copy

Important hook:

- `0x428b2`
  - `player X -> a4 + 0x32`
  - `player Y - 16 -> a4 + 0x30`

Current status:

- clearly player-linked
- not sufficient on its own to prove visible-body ownership
- dedicated note:
  [docs/0508_reference.md](/home/tighe/projects/rastan-genesis/docs/0508_reference.md)

## `a5 + 0x05c8`

Role:

- stage/event helper actor cluster

Main routines:

- `0x450d8`: manager/dispatch entry
- `0x45248`: generic constructor helper
- `0x423b2` path used in the harness for a helper-group seed

Current status:

- useful for harness validation
- weak body candidate

## `a5 + 0x0648`, `a5 + 0x0688`, `a5 + 0x0708`

Role:

- stage/class seeded fixed actors

Important routines:

- `0x4449e`: stage-specific class seeder
- `0x453a8`: small constructor that feeds `0x4543e`

Known behavior:

- stage table at `0x444e0` seeds classes:
  - stage `1 -> 0x0e`
  - stage `2 -> 0x13`
  - stage `3 -> 0x14`
  - stage `4 -> 0x15`
  - stage `5 -> 0x10`
  - stage `6 -> 0x17`

Current status:

- real and useful
- already shown to produce wrong visible family-1 candidates when treated as
  the player body by itself

## `a5 + 0x0748`

Role:

- helper/subpart/effect-like strip

Main routines:

- `0x41e76`: render pass to `0xd00170`
- `0x457b2..0x4580a`: constructor path for `state 15` family-1 actors

Known behavior:

- rendered through `0x3d054`
- proved capable of showing family-1 multipart graphics
- repeatedly produced wrong non-player visible output in the Genesis harness

Current status:

- do not use as proof of body ownership

## Multipart Helper Lists

Important fixed helper slots:

- `a5 + 0x06c8`
- `a5 + 0x09c8`
- `a5 + 0x0988`
- `a5 + 0x0948`

Main constructor:

- `0x45b2e`

Why these are not the body:

- positioned from `a5 + 0x071e / 0x0722` through `0x45be8`
- they are player-linked helpers, not direct users of the confirmed player
  world coordinates

## Practical Ownership Rules

Treat as high-value body candidates:

- `0x02c8`
- `0x0508`

Treat as helper-only until proven otherwise:

- `0x0748`
- `0x05c8`
- `0x45b2e` multipart helper lists
- stage-seeded fixed family actors at `0x0648 / 0x0688 / 0x0708`

## Next Reverse-Engineering Step

Find the constructor that seeds a live `0x02c8` actor with class `10`, `11`,
or `18`, then follow it through:

- `0x447b6`
- `0x4684e`
- `0x47140` or `0x473b8`

That is the shortest proof-based route to the real player body.
