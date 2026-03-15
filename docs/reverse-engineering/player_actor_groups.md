# Rastan Player Actor Group Notes

This note records the next layer of actor-system structure after the initial
player-input trace.

The goal is to separate:

- the real player body actor
- player-linked helper actors
- unrelated stage/event helper objects

before updating `hello-rastan` again.

## Confirmed actor group layout

### `a5 + 0x02c8` (`29` entries)

- updated by `0x40b66`
- rendered by `0x41e22` to `0xd00460`
- proximity-filtered again by `0x449b4`

This is the group that currently contains the strongest direct player-position
copy at `0x447b6`:

- `a5 + 0x10be -> a4 + 0x32`
- `a5 + 0x10c0 -> a4 + 0x30`

Important caveat:

- the same list is also used for many nearby-object and helper-object passes
- so a direct copy to player coordinates is not yet enough to prove "main body"
- the gate at `0x447ce` is driven by `a4 + 0x06` actor class, not `a4 + 0x05`
  state

### `a5 + 0x0508` (`20` entries)

- updated by `0x420e6`
- per-entry dispatcher at `0x42102`
- state jump table begins at `0x4213a`

This list is a serious candidate for player-body or player-adjacent animation
logic because it has a large dedicated update pass and several handlers that
operate on alternate display coordinates:

- `a4 + 0x30`
- `a4 + 0x32`

One especially important coordinate copy appears inside a handler at `0x428b2`:

- `a5 + 0x10be -> a4 + 0x32`
- `a5 + 0x10c0 - 16 -> a4 + 0x30`

So there are at least two separate systems that can slave actor display
coordinates to the live player world position:

- `0x447b6`
- `0x428b2`

### `a5 + 0x05c8` and nearby slots (`5` main entries plus adjacent fixed slots)

- stage/system manager dispatch starts at `0x450d8`
- many constructors here call the generic initializer at `0x45248`

This region is definitely used for stage- and event-driven helper actors.
Examples:

- `0x45248` sets generic actor startup fields:
  - `a4 + 0x00 = 1`
  - `a4 + 0x03 = 1`
  - `a4 + 0x04 = 1`
  - `a4 + 0x1c = 1`
  - `a4 + 0x20 = 1`
  - `a4 + 0x21 = d1`
  - `a4 + 0x0d = d2`
  - `a4 + 0x1e = d3`
  - `a4 + 0x1a = 0x0180`

This is useful structure, but it is not the player-body proof we need.

## Important de-risking result

Some of the earlier "state 10 / 11" paths are now clearly helper-object
construction and should not be treated as proof of the player body.

### `0x45b2e` multipart helper path

`0x45b2e` builds several actors at:

- `a5 + 0x06c8`
- `a5 + 0x09c8`
- `a5 + 0x0988`
- `a5 + 0x0948`

It assigns:

- `a4 + 0x21` from `a5 + 0x0200`
- `a4 + 0x06 = 0x0112` or `0x000a`
- high byte into `a4 + 0x38`
- then calls `0x4543e`, `0x45cfc`, and `0x45be8`

But `0x45be8` positions these actors from:

- `a5 + 0x071e`
- `a5 + 0x0722`

and not from the confirmed player world coordinates at:

- `a5 + 0x10be`
- `a5 + 0x10c0`

So this family should be treated as player-linked multipart helpers, not the
main body.

### `0x45642` helper strip

`0x45642` builds `9` actors starting at `a5 + 0x07c8`, sets:

- `a4 + 0x21` from the loop index
- `a4 + 0x06 = 11`
- then calls `0x4543e`, `0x45cfc`, and `0x45c0c`

`0x45c0c` does copy player coordinates into alternate display coordinates, but
it also lays these actors out using small position tables based on index and
player X range. That makes this strip look more like helper placement than the
core body sprite.

## Palette findings

The attribute byte at `a4 + 0x27` remains the best palette lead.

Confirmed writers:

- `0x45c04`: `bset #7, a4 + 0x27`
- `0x45376`: `bset #7, a4 + 0x27`
- `0x45388`: `bset #7, a4 + 0x27`
- `0x456b6`: `orb d1, a4 + 0x27`

The `0x45684..0x456ba` path is important because it is the first confirmed path
that ORs table-driven bits into `a4 + 0x27` instead of only forcing bit `7`.
That makes it a stronger palette-bank candidate than the simple `bset #7`
helpers.

## `0x4543e` record findings

I added a ROM table dumper at:

- [tools/dump_4543e_tables.py](/home/tighe/projects/rastan-genesis/tools/dump_4543e_tables.py)

and generated:

- [build/4543e_tables.txt](/home/tighe/projects/rastan-genesis/build/4543e_tables.txt)

Important concrete records:

- base state `8`: `tile_base=0x004b`, `frame=0x17`
- base state `9`: `tile_base=0x00d0`, `frame=0x23`
- alternate state `8`: same frame, different offsets
- alternate state `9`: same frame, different offsets

So `state 8/9` are real reusable animation records, but the table data alone
still does not prove they are the neutral standing body.

## `a4 + 0x0752` alternate-form finding

The first confirmed writer for `a4 + 0x0752` is:

- `0x4a09c`

That write happens inside a generic actor spawner at `0x4a086`, which is fed by
table data from `0x4a104` and then immediately calls:

- `0x4544e`
- `0x45684`

Important caveat:

- this spawner is reached from `0x4a0d8`
- `0x4a0d8` is itself called from `0x40a46`
- `0x40a46` is part of generic object teardown / replacement handling

So `a4 + 0x0752` is definitely live gameplay data, but this specific writer
looks like a general actor/effect spawn path, not direct proof of the main
player body.

## Current conclusion

What is now less likely:

- the earlier guessed family/state combinations from blind ROM probing
- the `0x45b2e` multipart helper path as the main player body
- the `0x45642` strip as the main player body

What is now more important:

- the `0x02c8` actor list path through `0x447b6`
- the `0x0508` actor list path through `0x428b2`
- any state handler that combines:
  - live player-coordinate copies
  - `0x4543e` animation setup
  - meaningful writes into `a4 + 0x27`

## `a4 + 0x06` class finding

The latest useful correction is that `0x447ce` checks `a4 + 0x06`, not the
runtime state in `a4 + 0x05`.

Confirmed direct-player-coordinate classes at `0x447ce`:

- class `10`
- class `11`
- class `18`

That makes the unresolved problem more precise:

- find the constructor that seeds a `0x02c8` entry with class `10`, `11`, or
  `18`
- then follow that class into `0x47140` / `0x473b8`

I added:

- [tools/dump_02c8_tables.py](/home/tighe/projects/rastan-genesis/tools/dump_02c8_tables.py)

which generates:

- [build/02c8_tables.txt](/home/tighe/projects/rastan-genesis/build/02c8_tables.txt)

That dump now contains:

- the `0x41cfa` 17-entry state/class record table
- the `0x46f1e` 16-entry class record table
- the stage-to-class seed table at `0x444e0`

One concrete result from the new dump:

- `0x4449e` seeds classes `0x0e, 0x13, 0x14, 0x15, 0x10, 0x17` by stage

So class `10` is confirmed to exist as a seeded actor class, while classes `11`
and `18` still need a tighter constructor trace.

## New `0x02c8` state-dispatch map

The `0x02c8` per-entry update pass at `0x40b80` dispatches on `a4 + 0x05`
through the jump table at `0x40bc2`.

That table now decodes to:

- state `0 -> 0x41180`
- states `1, 2 -> 0x473b8`
- states `3..12 -> 0x47140`
- states `13, 14 -> 0x473b8`
- state `15 -> 0x40ccc`

This matters because it proves `0x47140` and `0x473b8` are not rare special
cases. They are the main live frame builders for most active `0x02c8` states.

### Practical implication

If the visible player-body actor lives in `0x02c8`, then once we know its
state and class tuple we can place it into one of three buckets immediately:

- `0x47140` family of frame rules
- `0x473b8` family of frame rules
- `0x40ccc` special transition path

That is a much tighter target than searching sprite families in isolation.

## New class-constructor narrowing

The direct class writers checked this pass reinforce that class `11` is mostly
coming from helper paths we already distrusted:

- `0x4565a`
- `0x45b72`
- `0x45b9e`
- `0x45bca`

Those are all helper/multipart constructors, not good candidates for the main
player body.

So the remaining interesting unresolved direct-player-coordinate classes are:

- class `10`
- class `18`

with class `11` now looking even more like a helper-only branch.

## `0x4a0d8` spawn-table finding

I added:

- [tools/dump_4a0d8_table.py](/home/tighe/projects/rastan-genesis/tools/dump_4a0d8_table.py)

which generates:

- [build/4a0d8_table.txt](/home/tighe/projects/rastan-genesis/build/4a0d8_table.txt)

This path comes from:

- `0x40a1e -> 0x40a46 -> 0x4a0d8`

and does the following:

- preserves the current family in `a4 + 0x38`
- decodes stage/family-specific records from `0x4a104`
- writes:
  - `a4 + 0x04`
  - `a4 + 0x3e`
  - packed family / alt-form nibbles into `a4 + 0x38` and `a4 + 0x0752`
  - `a4 + 0x36`
  - `a4 + 0x1c`
  - `a4 + 0x34`
- then calls:
  - `0x4544e`
  - `0x45684`

This is the clearest current palette-bearing constructor path, but it is still
not the direct player-body proof we need. The caller at `0x40a1e` is generic
object reset / replacement handling, reached when an actor goes off-screen or
hits certain map/object conditions.

## Next target

Trace the `0x0508` state handlers around `0x428b2` and correlate them with the
`0x02c8` path at `0x447b6` to determine which system owns the visible neutral
Rastan body, then extract:

- state
- frame code
- tile base
- family
- attribute/palette byte

## `0x0508` shared handler findings

I added:

- [tools/dump_0508_jump_table.py](/home/tighe/projects/rastan-genesis/tools/dump_0508_jump_table.py)
- [tools/dump_0508_anim_tables.py](/home/tighe/projects/rastan-genesis/tools/dump_0508_anim_tables.py)

which generate:

- [build/0508_state_handlers.txt](/home/tighe/projects/rastan-genesis/build/0508_state_handlers.txt)
- [build/0508_anim_tables.txt](/home/tighe/projects/rastan-genesis/build/0508_anim_tables.txt)

The `0x0508` dispatcher at `0x4213a` maps:

- `states 4..9 -> 0x42838`
- `state 10 -> 0x425ea`
- `state 11 -> 0x421d8`
- `state 12 -> 0x42162`
- `state 15 -> 0x42abc`
- `state 19 -> 0x42422`

This matters because the earlier `state 8/9` records are part of one shared
player-linked handler, not isolated one-off actors.

### What `0x42838` actually does

`0x42838` is not a constructor. It is the live per-frame update for states
`4..9`.

Important behavior:

- if animation is not currently running (`a4 + 0x07 == 0`), it may call:
  - `0x42dfa` when bit `7` in `a4 + 0x27` is set and the gating checks pass
  - `0x42d26` otherwise, using `state - 1` as the descriptor index
- after that it always calls `0x42e38`, which advances the active animation
  descriptor copied into:
  - `a4 + 0x08`
  - `a4 + 0x09`
  - `a4 + 0x0d`
  - `a4 + 0x0e`
  - `a4 + 0x0f`
  - `a4 + 0x10`
  - `a4 + 0x11`
  - `a4 + 0x12`

So `0x42d20`, `0x42d26`, and `0x42dfa` are descriptor loaders, while
`0x42e38` is the generic "play that descriptor" routine.

### State `8` body-follow and frame cycle

Inside `0x42838`, state `8` is special-cased after the generic animation step.

- it uses frame base `0x30`
- it cycles through the 8-byte sequence at `0x42932`
- if `a4 + 0x3f == 0`, the frame loop is:
  - `0x30, 0x30, 0x33, 0x31, 0x32, 0x30, 0x30, 0x33`
- if `a4 + 0x3f != 0`, it switches to the alternate sequence at `0x4298e`
  with per-frame metadata from `0x4299e`
- `0x428b2` copies:
  - `a5 + 0x10be -> a4 + 0x32`
  - `a5 + 0x10c0 - 16 -> a4 + 0x30`

That makes state `8` a strong player-body or player-shadowed candidate, but it
still needs to be correlated with the correct tile base and palette tuple.

### Transition states around the shared handler

`0x425ea` (`state 10`) and `0x421d8` (`state 11`) do not set sprite families
directly. They also route through the same descriptor loader / animation
machinery:

- `0x425ea` uses `0x42d20(8)` when `a4 + 0x2a == 6`, otherwise `0x42d26`
- `0x421d8` runs `0x42e38`, then `0x41f96`, then visibility and teardown logic
- `0x42162` (`state 12`) also runs `0x42d20` and then slaves itself to another
  actor through `a4 + 0x528`

This makes `states 8..12` one coherent movement / transition cluster rather
than unrelated actor types.

### Current practical conclusion

The `0x0508` system now looks more like a real player-linked body/equipment
cluster than a helper-only system.

What is still missing:

- where this cluster gets its `a4 + 0x06` state transitions from during normal
  idle gameplay
- which exact constructor calls `0x4543e` for the visible neutral-body member
- the final `a4 + 0x27` palette bits for that member
