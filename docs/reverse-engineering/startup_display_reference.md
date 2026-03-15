# Rastan Startup Display Reference

This note documents the early boot / test / title display writers that target
the arcade text RAM region around `0xC08000`.

It is the right place to work from for real startup/title rendering, because
these routines already describe:

- where text is written
- how numeric/status fields are formatted
- which startup-side object blocks are seeded before display

## Primary addresses

- `0x3b8b0`: startup display/object seed block
- `0x3b902`: small display-state fill helper
- `0x3b930`: structured record writer into `0xD000xx`
- `0x3bb48`: string emitter into `0xC08000` text RAM
- `0x3c2e2`: decimal / nibble formatter into `0xC08000`
- `0x3c3fe`: fixed startup string writer into `0xC08000`
- `0x3c482`: tile pattern/table build helper

## `0x3b8b0`

This is the strongest startup-display seed routine.

What it does:

- seeds records at:
  - `0xD00020`
  - `0xD000E0`
  - `0xD00128`
- then calls `0x3b902` to fill/update `0xD00088`
- also calls `0x3b802` with small mode ids

That means the boot/test/title presentation is not just text RAM writes. It has
an object/record side in `0xD000xx` as well.

### `0x3b930`

This helper writes one structured 8-byte record per entry:

- clears a leading word
- copies two source bytes as words
- loads a word into `d7`
- calls `0x5b512`
- stores the transformed result back into the record

This is probably coordinate/attribute preparation for startup-side display
objects rather than plain text.

## `0x3bb48`

This is the clearest startup/title string emitter.

Inputs:

- `d0`: message id, low `7` bits used as table index
- sign of `d0`: normal emit vs blanking emit

Behavior:

- indexes a pointer table at `0x3bb7c`
- each entry resolves to:
  - destination text RAM address in `0xC08000`
  - attribute word
  - message bytes
- emits alternating words:
  - attribute word
  - character code word

Normal path:

- writes the source byte directly as the glyph code

Negative / blanking path:

- writes `0x0020` (space) instead of the source byte

So the hardware text RAM format here is effectively:

1. attribute word
2. tile/glyph code word
3. repeated

### proven message data

The table/data around `0x3bc98` clearly contains startup/test/title strings
such as:

- `BEST 5`
- `SCORE ROUND NAME`
- `CREDIT`
- `1ST`
- `PLAYER 1 READY`
- `PLAYER 2 READY`

That is the strongest current proof that real startup/title text should be
mapped from this writer, not from placeholder HUD strings.

## `0x3c2e2`

This routine formats numeric/status values into the same `0xC08000` text RAM.

Behavior:

- indexes a small table at `0x3c37c`
- each entry supplies:
  - width/count
  - destination text RAM address
  - source RAM pointer
- converts nibbles into ASCII digits by adding `0x30`
- writes alternating:
  - attribute word `0`
  - glyph code word

Special cases:

- if the low nibble is `7` in the sentinel case, it emits:
  - `A`
  - `L`
  - `L`
- `0x3c42a..0x3c44e` remaps:
  - `?` (`0x3f`) -> `0x274b`
  - `!` (`0x21`) -> `0x2744`

This is important because it shows the startup display path is not pure ASCII.
There are already special tile ids mixed into the text stream.

## `0x3c3fe`

This is another startup text/status writer.

What it does:

- indexes a table at `0x3c454`
- resolves:
  - a width/count
  - a text RAM offset, then adds `0xC08000`
  - a source pointer in work RAM, then adds `0x10C000`
- emits alternating attribute/glyph words into text RAM

Like `0x3c2e2`, it remaps:

- `?` -> `0x274b`
- `!` -> `0x2744`

So both formatters agree on the same special non-ASCII tile ids.

## Current implementation guidance

To make real progress on startup/title rendering:

1. keep the `0xC08000..0xC0BFFF` text RAM shadow
2. stop substituting SGDK text/font behavior for final presentation
3. model text RAM as alternating attribute/glyph words
4. honor special tile ids like `0x2744` and `0x274b`
5. map the `0x3bb48`, `0x3c2e2`, and `0x3c3fe` writers directly
6. only after that, map the supporting `0xD000xx` startup object records from
   `0x3b8b0`

## Why this matters

This is the cleanest route toward real startup/title graphics because it uses:

- real arcade write destinations
- real arcade message tables
- real arcade glyph codes

instead of placeholder strings or font substitution tricks.
