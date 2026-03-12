# Rastan Sprite And Animation Reference

This note consolidates the sprite/animation side of the `68000` code.

Use it when the question is:

- where sprite graphics actually come from
- how actor fields become family/frame/tile-base data
- which routines apply palette/attribute bits
- which sprite-family paths are already proven wrong for the player body

## Raw Graphics vs Program Logic

Confirmed:

- raw sprite graphics do not live in the main `68000` program ROM
- raw sprite graphics live in the `pc090oj` ROM region
- the `68000` program chooses:
  - sprite family
  - state/class
  - frame code
  - tile base
  - palette/attribute bits

This is why raw graphics matching by itself keeps failing.

## Object To Sprite RAM Passes

The program clears sprite/object RAM at startup:

- `0x3ad4c`
- `0x3ad62`
- `0x3ad72`

Later object-to-sprite passes write groups into PC090OJ work RAM:

- `0x41dd2 -> 0xd001c8`
- `0x41e0c -> 0xd00300`
- `0x41e60 -> 0xd00460`
- `0x41e9e -> 0xd00170`

Important current observation:

- destination RAM alone does not tell us who the player body is
- ownership still depends on which actor list and family feed that destination

## Important Actor Fields

Sprite-facing fields used repeatedly:

- `+0x1e`: tile base
- `+0x27`: attribute byte, strongest palette lead
- `+0x28`: animation X offset
- `+0x2c`: animation Y offset
- `+0x38`: sprite family
- `+0x3a`: animation length / aux field
- `+0x3e`: animation selector
- `+0x752`: alternate form selector

## Key Animation Resolver

Main routine:

- `0x4543e`

Normal-family behavior:

- resolves an 8-byte record from `0x45502` or `0x45562`
- writes:
  - `a4 + 0x1e`
  - `a4 + 0x3a`
  - `a4 + 0x01`
  - `a4 + 0x28`
  - `a4 + 0x2c`

Special-family behavior:

- if `a4 + 0x3e == 2`, it uses smaller family-specific tables near:
  - `0x454ba`
  - `0x454d2`
  - `0x454ea`

Important implication:

- `0x4543e` is the first place where actor ownership becomes frame/tile-base
  data

## Palette / Attribute Logic

Main routine:

- `0x45684`

Why it matters:

- it ORs table-selected bits into `a4 + 0x27`
- this is a stronger palette lead than simple bit-set helpers

Other confirmed writers:

- `0x45c04`
- `0x45376`
- `0x45388`

These mostly set bit `7`, but do not explain the full palette choice alone.

## Generic Sprite Builder

Main dispatcher:

- `0x3d054`

Known family dispatch:

- family `1 -> 0x4770e`
- family `2 -> 0x3f0bc`
- family `3 -> 0x3ffdc`
- family `4 -> 0x3fff0`
- others via jump table at `0x3d09e`

This is the central reason the correct player sprite cannot be derived only
from graphics ROM layout.

## Family-1 Path

Main routine:

- `0x4770e`

Frame-record table:

- `0x4771c`

Record format:

- 4 bytes per part
  - control
  - Y offset
  - tile delta
  - X offset
- terminator `0xff`

Validated facts:

- the offline extractor and Genesis harness now agree on family-1 frame-record
  parsing
- the offline extractor and Genesis harness now agree on `pc090oj` 16x16 tile
  decode order

So for family `1`, current visible errors are now ownership errors, not decode
errors.

## Proven Wrong Visible Candidates

Already disproven as the player body:

- `0x0748 state 15`, family `1`, frame `0x5f`, tile base `0x043a`
- the stage-family candidate that rendered as:
  - family `1`
  - state `14`
  - frame `0xdd`
  - tile base `0x03b3`

These candidates are still useful because they prove the renderer works well
enough to distinguish wrong ownership from wrong decode.

## Family-1 Reference Values Already Known

Useful examples from `family1_frames.txt`:

- state `10 -> tile_base 0x033e, frame 0x93`
- state `11 -> tile_base 0x02e8, frame 0x5f`
- state `15 -> tile_base 0x043a, frame 0x5f`

Important lesson:

- seeing a valid family/frame/tile-base tuple on screen does not prove it is
  the visible player body

## What This Subsystem Can Prove

Good for proving:

- tile-base to tile-index relationships
- frame-record composition
- palette/attribute ownership entry points
- whether a candidate on-screen sprite is decoded correctly

Not good enough by itself for proving:

- whether the actor feeding the builder is really Rastan's body

## Best Next Target

Do not spend more time on family-1 candidate forcing until actor ownership is
proved upstream.

The next proof-based route is:

1. find the real `0x02c8` body-facing actor
2. identify its final `family / frame / tile-base / attr` tuple
3. then use this sprite/animation reference to decode that proven tuple

