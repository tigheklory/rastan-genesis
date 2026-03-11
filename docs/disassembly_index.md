# Rastan Disassembly Index

This is the high-signal index for the arcade `68000` disassembly.

The full listing is:

- [build/maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt)

That file is useful as ground truth, but too large to navigate by line number.
Use this index and the address-based helper instead:

```bash
python3 tools/show_disasm_range.py 0x42838 0x42988
```

## Current workflow

1. Start from a confirmed gameplay fact.
2. Trace the RAM fields affected by that fact.
3. Find the actor group that consumes those fields.
4. Trace constructor/setup code for that actor group.
5. Only then decode sprite family/frame/tile/palette data.

This avoids repeating the earlier mistake of matching sprite graphics in
isolation and landing on the wrong actor.

## Important files

- [docs/player_input_trace.md](/home/tighe/projects/rastan-genesis/docs/player_input_trace.md)
- [docs/player_sprite_trace.md](/home/tighe/projects/rastan-genesis/docs/player_sprite_trace.md)
- [docs/player_actor_groups.md](/home/tighe/projects/rastan-genesis/docs/player_actor_groups.md)
- [build/02c8_tables.txt](/home/tighe/projects/rastan-genesis/build/02c8_tables.txt)

## Important RAM fields

- `a5 + 0x10be`: player X
- `a5 + 0x10c0`: player Y
- `a5 + 0x1376`: entry-script active flag
- `a5 + 0x137a`: live entry-script command / current control-latched word
- `a5 + 0x1384`: entry side selector
- `a5 + 0x1388`: stage-entry event mode
- `a5 + 0x13c4`: stage-entry event activity latch
- `a5 + 0x13c6`: stage-entry dispatcher enable
- `a4 + 0x27`: sprite attribute byte, strongest palette lead
- `a4 + 0x38`: sprite family selector
- `a4 + 0x3e`: animation/state selector for `0x4543e`
- `a4 + 0x752`: alternate-form selector

## Actor groups

### `a5 + 0x02c8`

- update pass: `0x40b66`
- render pass: `0x41e22`
- proximity / visibility pass: `0x449b4`
- strong player-coordinate hook: `0x447b6`

This remains one of the strongest visible-body candidates because it is part of
the normal render path and directly receives live player coordinates for states
`10`, `11`, and `18`.

### `a5 + 0x0508`

- update pass: `0x420e6`
- per-entry dispatcher: `0x42102`
- state jump table: `0x4213a`
- strong player-coordinate hook: `0x428b2`
- constructor seed: `0x45342`

This looks like a player-linked control/state cluster. It is important, but it
has already produced false positives when decoded without proving which visible
body actor it feeds.

### `a5 + 0x0748`

- render pass: `0x41e76`
- small linked object/effect constructors: `0x433ac`, `0x434ba`, `0x434ea`,
  `0x4354e`, `0x435ac`, `0x435e2`

This group appears to hold body-linked helpers, effects, or subparts. Several
entries store a back-pointer in `a4 + 0x528`, which makes it useful for tracing
multipart relationships.

## Core sprite/animation routines

### `0x3d054`

Sprite builder dispatcher. Chooses a sprite-family-specific handler based on
`a4 + 0x38`.

### `0x4543e`

Animation record resolver.

For normal families it writes:

- `a4 + 0x1e`: tile base
- `a4 + 0x3a`: animation length / frame count field
- `a4 + 0x01`: frame code
- `a4 + 0x28`: x offset
- `a4 + 0x2c`: y offset

### `0x45684`

Palette / attribute table applicator.

This ORs table-selected bits into `a4 + 0x27`, which is why it is one of the
main palette leads.

### `0x40a1e -> 0x40a46 -> 0x4a0d8`

Generic object reset / replacement path.

What it does:

- preserves the current family in `a4 + 0x38`
- preserves the current alternate selector staging in `a4 + 0x0753`
- clears / reinitializes the actor through `0x4092e`
- repopulates `a4 + 0x3e`, `a4 + 0x38`, `a4 + 0x0752`, and related fields from
  a stage/family table at `0x4a104`
- then calls `0x4544e` and `0x45684`

Important caveat:

- this is useful for understanding palette application
- but it is not, by itself, proof of the player idle body
- the caller at `0x40a1e` is reached from generic off-screen / map-object
  replacement handling

The decoded table is dumped in:

- [build/4a0d8_table.txt](/home/tighe/projects/rastan-genesis/build/4a0d8_table.txt)

### `0x45cfc`

Generic actor activation helper:

- `a4 + 0x00 = 1`
- `a4 + 0x05 = 3`
- `a4 + 0x1c = 1`

### `0x45c0c`

Player-coordinate-linked helper placement. This is not the main body path, but
it does copy:

- `a5 + 0x10be -> a4 + 0x32`
- `a5 + 0x10c0 - 16 -> a4 + 0x30`

## Key `0x0508` routines

### `0x4213a`

Jump table for the `0x0508` state machine.

Useful entries:

- `state 8 -> 0x42838`
- `state 9 -> 0x42838`
- `state 10 -> 0x425ea`
- `state 11 -> 0x421d8`
- `state 12 -> 0x42162`
- `state 15 -> 0x42abc`

### `0x42838`

Shared live-update handler for states `4..9`.

It loads animation descriptors through:

- `0x42d26`
- `0x42dfa`

and advances them through:

- `0x42e38`

For `state 8`, it also runs a dedicated frame loop from:

- `0x42932`
- `0x4298e`
- `0x4299e`

### `0x45342`

Known setup seed for the first two `0x0508` entries. It initializes them to
state `8` or `9` and sets bit `7` in `a4 + 0x27`.

This is player-linked, but not sufficient by itself to prove "visible body".

## Key `0x02c8` routines

### `0x443e0`

Pass over the `0x0508` list to update the `a4 + 0x0c` gating field used later
by the `0x02c8` visibility/body logic.

### `0x447b6`

Direct player-coordinate copy into a `0x02c8` actor:

- `a5 + 0x10be -> a4 + 0x32`
- `a5 + 0x10c0 -> a4 + 0x30`

### `0x447ce`

This gate is keyed on `a4 + 0x06`, not `a4 + 0x05`.

Only calls the direct player-coordinate copy for actor classes:

- class `10`
- class `11`
- class `18`

This is one of the strongest reasons to keep the `0x02c8` group in focus for
the real player body.

### `0x40b80`

Per-entry update dispatcher for the `0x02c8` group.

The state jump table at `0x40bc2` now decodes to:

- state `0 -> 0x41180`
- states `1, 2 -> 0x473b8`
- states `3..12 -> 0x47140`
- states `13, 14 -> 0x473b8`
- state `15 -> 0x40ccc`

This is important because it shows `0x47140` and `0x473b8` are the dominant
live frame/state handlers for active `0x02c8` actors.

### `0x41cfa`

Primary `0x02c8` state/class record loader used by both `0x47140` and
`0x473b8`.

It copies an 8-byte table record into:

- `a4 + 0x08`
- `a4 + 0x0d`
- `a4 + 0x0e`
- `a4 + 0x0f`
- `a4 + 0x10`
- `a4 + 0x11`
- `a4 + 0x13`
- `a4 + 0x02`

The raw records are dumped in:

- [build/02c8_tables.txt](/home/tighe/projects/rastan-genesis/build/02c8_tables.txt)

### `0x46f1e`

Secondary class record loader for the same 8-byte record shape. This appears in
the `0x4684e` branch and several related actor paths.

The raw class table is also dumped in:

- [build/02c8_tables.txt](/home/tighe/projects/rastan-genesis/build/02c8_tables.txt)

### `0x4449e`

Stage-specific helper/class seeder.

It picks one byte from the table at `0x444e0` and writes it into `a4 + 0x06`
before calling `0x453a8`. The current table entries are:

- stage `1 -> class 0x0e`
- stage `2 -> class 0x13`
- stage `3 -> class 0x14`
- stage `4 -> class 0x15`
- stage `5 -> class 0x10`
- stage `6 -> class 0x17`

This is useful because it gives one confirmed source of `a4 + 0x06` class
assignment and reinforces that the player-coordinate-slaved classes `10/11/18`
are not being reached from every generic constructor.

### `0x448b2`

## Stage-entry / event routines

### `0x51024`

Main gameplay update loop during active stage play.

For the current investigation, the important calls are:

- `0x5126e`: side-entry threshold detector
- `0x52bb6`
- `0x52b38`
- `0x52b4a`: timed entry-script feeder
- `0x54a2c`: stage-entry event dispatcher wrapper

This is the loop that proves the entry/drop logic is part of the normal frame
update, not just one-time initialization.

### `0x5126e`

Checks the live player X coordinate at `a5 + 0x10be` against side thresholds
and, when crossed, enables the scripted side-entry sequence by setting:

- `a5 + 0x1376 = 1`
- `a5 + 0x1384 = 1` or `2`
- `a5 + 0x13c6 = 1`

### `0x52b4a`

Small timed command-stream reader used while `a5 + 0x1376 == 1`.

It selects one pointer from the table at `0x052c1c`, loads:

- duration into `a5 + 0x1372`
- command into `a5 + 0x1373`

and exposes the current command at:

- `a5 + 0x137a`

This now looks like an entry-sequence script feeder, not a sprite decoder.

### `0x54a2c -> 0x54a32`

Stage-entry event dispatcher.

`0x54a2c` clears `a5 + 0x13c4`, then `0x54a32`:

- checks `a5 + 0x13c6`
- updates event timing through `0x54dd2`
- iterates two RAM tables at `0x10d2a8` and `0x10d2c8`
- dispatches handlers from jump tables at `0x550a8` and `0x550c0`

The handlers checked so far mostly adjust stage/camera/effect globals and fire
subsystems such as:

- `a5 + 0x12f0`
- `a5 + 0x130e`
- `a5 + 0x1296`
- `a5 + 0x1266 / 0x1268`
- `a5 + 0x1388`

This makes the path useful for stage-entry sequencing, but not a strong direct
lead for the player body sprite.

Resets a `0x02c8` actor into:

- `a4 + 0x05 = 15`
- `a4 + 0x08 = 0xff`
- `a4 + 0x09 = 1`

This is a helper reset path, not the body constructor, but it is part of the
same runtime behavior.

## Current conclusion

What is safe to say now:

- The player-controlled object and the visible body are not necessarily the same
  actor entry.
- The `0x0508` cluster is player-linked, but decoding its records directly has
  repeatedly produced non-player actors when used without constructor/context.
- The `0x02c8` group remains the best visible-body candidate because it lives in
  the normal render path and only certain states are explicitly slaved to the
  player coordinates.

What is still unresolved:

- the exact visible player-body class constructor for `a4 + 0x06 = 10/11/18`
- the exact neutral pose tuple
- the real palette bank / color source
