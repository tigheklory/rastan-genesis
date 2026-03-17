# Rastan Palette Table Reference

This note separates real palette-color tables from the smaller startup/title
text attribute words.

That distinction matters because earlier startup/title message records contain
small values like `0x0000`, `0x0001`, `0x0002`, `0x002e`, and `0x002f`. Those
are **not** palette RAM addresses and they are **not** the full game's palette
state.

They are attribute words carried by startup/title text records in the current
`world_rev1` `maincpu.bin`.

## Ground Truth

- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt)
- [build/regions/maincpu.bin](/home/tighe/projects/rastan-genesis/build/regions/maincpu.bin)
- [palette_application_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/palette_application_reference.md)
- [palette_fit_audit.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/palette_fit_audit.md)

## What The Small Startup Values Actually Are

The startup/title text emitter:

- `0x3bb48`

reads message records from:

- `0x3bb7c`

Each record contains:

- destination pointer in the `0xC08000` text layer
- one attribute word
- message bytes

So values like:

- `0x0000`
- `0x0001`
- `0x0002`
- `0x002e`
- `0x002f`

are simply the attribute words used by that message table in the current
`world_rev1` startup/title front-end path.

They are:

- specific to those decoded startup/title message records
- not palette RAM addresses
- not the full game's palette inventory

## Real Palette Block Loader

The clearest proven color-table upload helper is:

- `0x59ad4`

What it does:

1. takes `a0` as the source palette-table base
2. uses `d1 * 32` to choose one `16`-color row from that table
3. uses `d0 * 32` to choose one destination block inside `0x200000`
4. converts `16` source words
5. stores the converted `16` words into the `0x200000` region

Important conversion detail:

- source word format is `0x0RGB`
  - top nibble = red
  - middle nibble = green
  - low nibble = blue
- converted destination format is `0BBBBBGGGGGRRRRR`
  - `4-bit` source channels are expanded to `5-bit` steps
  - `0x0fff` becomes `0x7bde`

So `0x59ad4` is handling real `16`-color palette blocks, not symbolic
attribute selectors.

## Proven Front-End Palette Tables

These are the first static front-end palette tables now grounded through
`0x59ad4`.

### `0x5a6fa`

Loaded by:

- `0x5a356`

Destination:

- block `d0 = 1`
- row `d1 = 0`

Source words:

```text
0000 0ff8 0ec0 0c90 0a70 0850 0740 0530
0fed 0ba9 0876 0654 0530 0432 0f00 0800
```

Converted words:

```text
0000 43de 031c 0258 01d4 0150 010e 00ca
6b9e 4a96 31d0 214c 00ca 10c8 001e 0010
```

### `0x5a73a`

Loaded by:

- `0x5a3ac`

Destination:

- block `d0 = 1`
- row `d1 = 0`

Source words:

```text
0000 0000 0fb9 0f97 0b65 0740 0420 0890
0560 0cba 0876 0f20 0a40 0fff 0fc0 0a80
```

Converted words:

```text
0000 0000 4ade 3a5e 2996 010e 0088 0250
018a 52d8 31d0 009e 0114 7bde 031e 0214
```

### `0x5a75a`

Loaded by:

- `0x5a3de`
- `0x5a410`

Destination:

- block `d0 = 1`
- row `d1 = 0`

Source words:

```text
0000 0000 0fb9 0f97 0b65 0740 0420 006a
0027 0cba 0876 0f20 0a40 0fff 0fc0 0a80
```

Converted words:

```text
0000 0000 4ade 3a5e 2996 010e 0088 5180
3880 52d8 31d0 009e 0114 7bde 031e 0214
```

### `0x5a77a`

Loaded by:

- `0x5a474`

Destinations:

- block `3`, row `0`
- block `4`, row `1`
- block `5`, row `2`

Source words:

```text
0000 0fff 0fb9 0f97 0b65 0740 0420 006a
0027 0cba 0876 0f20 0a40 0fff 0fc0 0a80
```

Converted words:

```text
0000 7bde 4ade 3a5e 2996 010e 0088 5180
3880 52d8 31d0 009e 0114 7bde 031e 0214
```

## Other Proven Static Palette Rows

These are also clearly palette-like tables used through the same loader.

### `0x511da`

Loaded by:

- `0x511bc`
- `0x511d0`

Rows used:

- row `0`
- row `1`

Row `0` converted:

```text
7bde 7bd2 7bd2 7bd2 7bca 7bce 5a4c 7bd2
2908 0000 2108 4210 6318 5294 2940 18c6
```

Row `1` converted:

```text
7bde 7bde 7bde 7bde 7bde 7bde 7bde 7bde
7bde 0000 2108 4210 6318 5294 2940 18c6
```

### `0x5649e`

Loaded by:

- `0x56136`
- `0x56184`

Known rows used:

- row `0`
- row `4`

### `0x564fe`

Loaded by:

- `0x5614a`
- `0x5615c`
- `0x5616e`

Known row used:

- row `0`

Its converted row matches the front-end block at `0x5a73a`.

### `0x5651e`

Loaded by:

- `0x56198`

Known row used:

- row `0`

## Mid-Game / Dynamic Palette Drivers

These are real palette flows too, but they are not just one static table each.

### `0x5988c`

Uses:

- palette table base `0x59910`
- destination-block index table `0x59950`
- selector from `a5 + 0x2a2`

This looks like a mode- or scene-selectable front-end/gameplay palette driver
that chooses between multiple destination blocks.

### `0x59962`

Uses:

- palette table base `0x59b1a`
- destination-block index table `0x59a98`
- selector from:
  - `a5 + 0x118`
  - `a5 + 0x12e8`

### `0x599b2`

Uses:

- palette table base `0x59b7a`
- destination-block index table `0x59aa4`
- selector from:
  - `a5 + 0x118`
  - `a5 + 0x12ea`

### `0x59de0`

Uses:

- table chooser at `0x59e8c`
- table-count table at `0x59ebc`
- table pointer table at `0x59ec8`
- source pointer from `0x59e6c`
- destination block from `a5 + 0x13ae`

This looks like a stronger general-purpose palette sequencer / animation
driver, not just a one-shot front-end setup.

## What This Means For The Port

The graphics ROMs are not enough by themselves.

The port needs to preserve:

- source graphics from `pc080sn` / `pc090oj`
- palette bank selection from actor/video attributes
- palette block upload behavior from `0x59ad4` and its higher-level drivers

That is encouraging for Genesis because:

- color source words are already table-driven
- front-end/title loads are clearly `16`-color block based
- several tables repeat or share rows

So the likely port shape is:

- keep palette source words in ROM-derived tables
- map logical arcade palette blocks into Genesis `PAL0..PAL3`
- consolidate where the audit proves rows are identical or near-identical

## Variant Scope

This audit is currently grounded in the extracted:

- `world_rev1`

main program region:

- [build/regions/maincpu.bin](/home/tighe/projects/rastan-genesis/build/regions/maincpu.bin)

Given the very small `world_rev1` / `us_rev1` delta, much of this is likely to
carry across, but the addresses and decoded tables above should be treated as
proven for the current `world_rev1` baseline unless rechecked for another
variant.
