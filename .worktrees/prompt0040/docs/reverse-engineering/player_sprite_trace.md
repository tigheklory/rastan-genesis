# Rastan Player Sprite Trace

This note captures the first confirmed path from actor state to rendered sprite data in the arcade ROMs.

## Confirmed facts

- The player graphics are not stored in the 68000 program ROM.
- Raw sprite graphics live in the `pc090oj` region built from:
  - `b04-05.15`
  - `b04-06.28`
  - `b04-07.14`
  - `b04-08.27`
- The 68000 code selects:
  - which sprite family to use
  - which animation/state to use
  - which frame within that animation to use
  - which color/palette bits to apply

## RAM blocks involved

The game clears and initializes sprite/object RAM at startup:

- `0x3ad4c`: clears `0xd00000`
- `0x3ad62`: clears `0xd00170`
- `0x3ad72`: clears most of `0xd00000`

The main object-to-sprite pass later writes several object groups into PC090OJ work RAM:

- `0x41dd2` -> writes a group to `0xd001c8`
- `0x41e0c` -> writes a group to `0xd00300`
- `0x41e60` -> writes a group to `0xd00460`
- `0x41e9e` -> writes a group to `0xd00170`

The pass at `0x41e76` is the most important one so far for the player-like actor set:

- actor source base: `a5 + 0x748`
- sprite destination: `0xd00170`
- count: `11`
- per-entry size: `0x40`
- dispatch call: `0x3d054`

## Important actor fields

Within one `0x40`-byte actor entry, these fields are now clearly significant:

- `+0x16`: X position
- `+0x1a`: Y position
- `+0x20`: sprite priority/order input used during sprite build
- `+0x21`: animation/frame counter or frame selector
- `+0x26`: flag byte used by some helper logic
- `+0x27`: sprite attribute bits, including flip/palette-related bits
- `+0x38`: sprite type / sprite family selector
- `+0x3e`: actor kind/state selector
- `+0x752`: alternate form/state byte used by animation setup

## Sprite build path

### 1. Actor initialization

`0x4092e` clears and initializes a `0x40`-byte actor structure.

This routine is called repeatedly before helper code fills in the actor's type, state, position, and animation fields.

### 2. Animation/state setup

`0x4543e` is a key routine.

It uses:

- `a4 + 0x06`
- `a4 + 0x38`
- `a4 + 0x3e`
- `a4 + 0x752`

and loads a small record into:

- `a4 + 0x1e`
- `a4 + 0x3a`
- `a4 + 0x01`
- `a4 + 0x28`
- `a4 + 0x2c`

This is a strong sign that `0x4543e` resolves animation metadata for the current actor state.

### 3. Common "make visible" helper

`0x45cfc` marks an actor active for rendering:

- `a4 + 0x00 = 1`
- `a4 + 0x05 = 3`
- `a4 + 0x1c = 1`

This helper appears in many player-related setup paths.

### 4. Final sprite dispatch

`0x3d054` is the generic sprite builder dispatch.

It first checks `a4 + 0x38` and jumps to a sprite-family-specific handler:

- if `a4 + 0x38 == 1` -> `0x4770e`
- if `a4 + 0x38 == 2` -> `0x3f0bc`
- if `a4 + 0x38 == 3` -> `0x3ffdc`
- if `a4 + 0x38 == 4` -> `0x3fff0`
- otherwise it uses a jump table starting at `0x3d09e`

This is the key proof that the correct Rastan standing pose cannot be recovered by graphics-ROM matching alone. The program chooses a sprite family first, then the family handler chooses tile codes and attributes.

## Player-related construction sites

Several player/boss/event setup paths build actors and then call the animation helper:

- `0x457d0`
- `0x4588c`
- `0x458d8`
- `0x4597a`
- `0x459c6`
- `0x45a08`
- `0x45a26`
- `0x45a60`
- `0x45a8a`
- `0x45b02`
- `0x45b2e`
- `0x45b64`
- `0x45b90`
- `0x45bb8`

One especially important path is:

- `0x45b2e`

It builds extra actors, assigns:

- `a4 + 0x21` from `a5 + 0x200`
- `a4 + 0x06 = 0x0112` or `0x000a`
- `a4 + 0x38 = high byte of that value`

and then calls `0x4543e` and `0x45cfc`.

This suggests some multipart player-related display objects are encoded by packing sprite-family and animation-state information into the value written to `a4 + 0x06` / `a4 + 0x38`.

## Current conclusion

The previous ROM-derived neutral sprite was wrong because it guessed a tile arrangement from graphics data alone.

The correct method is:

1. identify the player actor in the `a5 + 0x748` object set
2. trace the specific sprite-family handler selected by `a4 + 0x38`
3. recover the tile code list and attribute words that handler writes into the `0xd00170` sprite entries
4. recover the palette bits from the same path or related attribute tables
5. rebuild the standing pose from those exact tile codes in `pc090oj`

## Next target

Disassemble the sprite-family handlers reached from `0x3d054`, starting with the family actually used by the player object, and log the tile code / color values they emit to the `0xd00170` entries.
