# Rastan Palette Application Reference

This note tracks where palette and attribute bits are applied in the arcade
`68000` program.

It matters because the graphics ROMs alone do not determine final color. In
Rastan, the graphics regions (`pc080sn`, `pc090oj`) hold tile data, while the
program chooses palette/attribute bits at runtime and writes them into actor
state and later sprite/object RAM.

## Ground Truth

- [maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt)
- [4543e_tables.txt](/home/tighe/projects/rastan-genesis/build/4543e_tables.txt)
- [sprite_animation_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/sprite_animation_reference.md)

## Important Palette-Carrying Fields

Main per-actor field:

- `a4 + 0x27`
  - sprite attribute byte
  - strongest current palette lead
  - receives table-selected bits from the main palette applicator

Supporting selector fields:

- `a4 + 0x38`
  - sprite family
- `a4 + 0x3e`
  - animation/state selector
- `a4 + 0x752`
  - alternate form selector
- `a5 + 0x118`
  - player-count / front-end selector used in palette table indexing
- `a5 + 0x2a2`
  - alternate palette table selector

## Main Palette Applicator

Main routine:

- `0x45684`

Core behavior:

1. checks `a4 + 0x3e`
2. if `a4 + 0x3e != 2`
   - uses table `0x45722` by default
   - uses table `0x4576a` if `a5 + 0x2a2 != 0`
3. indexes that table by:
   - `(a5 + 0x118 - 1) * 12`
   - plus `a4 + 0x3e`
4. loads one byte from the selected table
5. forces bit `6` on that byte
6. ORs the result into `a4 + 0x27`

Relevant disassembly:

- `0x4568c`: `lea 0x45722, a0`
- `0x45696`: `lea 0x4576a, a0`
- `0x4569c..0x456ae`: player-count and state indexing
- `0x456b0`: `moveb (a0), d1`
- `0x456b2`: `bset #6, d1`
- `0x456b6`: `orb d1, a4@(0x27)`

## Special Palette Path For `a4 + 0x3e == 2`

If `a4 + 0x3e == 2`, `0x45684` switches to a different table:

- `0x456bc`: `lea 0x456ec, a0`

That path indexes by:

- `a4 + 0x752`, with stride `18`
- `a5 + 0x118 - 1`, with stride `3`
- `a4 + 0x38`, normalized so values `>= 3` subtract `2`

Then it falls through to the same final byte load and OR path:

- `0x456e8`: add family-based offset
- `0x456ea`: branch back to `0x456b0`

Practical meaning:

- form selector, player-count selector, and family all influence the final
  attribute byte when this special state is active

## Concrete Constructor-Side Caller

One strong caller is:

- `0x4a0ce`

Path:

- `0x4a086` loads a record into:
  - `a4 + 0x04`
  - `a4 + 0x3e`
  - `a4 + 0x38`
  - `a4 + 0x752`
  - `a4 + 0x36`
  - `a4 + 0x1c`
  - `a4 + 0x34`
- then:
  - `0x4a0c8`: `jsr 0x4544e`
  - `0x4a0ce`: `jsr 0x45684`

This is useful because it proves the palette applicator is part of a real
spawn/setup path, not just a late render decoration.

## Related Attribute Writers

Other confirmed writers discussed elsewhere:

- `0x45376`
- `0x45388`
- `0x45c04`

These appear to set or force high attribute bits, especially bit `7`, but they
do not replace `0x45684` as the clearest table-driven palette source.

## Hardware Implication

Current extracted ROM regions:

- [build/regions/pc080sn.bin](/home/tighe/projects/rastan-genesis/build/regions/pc080sn.bin)
- [build/regions/pc090oj.bin](/home/tighe/projects/rastan-genesis/build/regions/pc090oj.bin)

These are graphics data regions, not standalone palette ROMs.

Current implication:

- final color selection appears to be program-driven through palette/attribute
  tables and runtime palette RAM writes
- not through a separate dedicated palette region in the current extracted set

That matches the custom-hardware reality better:

- `pc080sn` and `pc090oj` provide tile/object graphics
- the `68000` and video hardware path decide which palette bank or attribute
  bits those graphics use

Important boundary:

- we have a strong handle on palette-bank / attribute selection in actor code
- we do **not** yet have a proven final palette-RAM write routine or final
  palette-RAM address map for the custom video path
- so right now the clearest proven palette point is still the attribute byte
  path centered on `a4 + 0x27`, not the final hardware color load

## Startup / Title Attribute Words Are Not Palette Addresses

The small values previously discussed:

- `0x0000`
- `0x0001`
- `0x0002`
- `0x002e`
- `0x002f`

are **not** palette RAM addresses.

They come from the startup/title text message table at:

- `0x3bb7c`

and are simply the message-record attribute words consumed by:

- `0x3bb48`

That is a startup/title text-layer detail for the current `world_rev1`
`maincpu.bin`, not a general "all palettes in the game" statement.

See also:

- [palette_fit_audit.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/palette_fit_audit.md)
- [palette_table_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/palette_table_reference.md)

## Real Palette Block Loader

The clearest proven color-table upload helper is:

- `0x59ad4`

What it does:

- reads `16` source words from `a0`
- selects one source row using `d1 * 32`
- selects one destination block using `d0 * 32`
- writes the converted words into the `0x200000` region

Important conversion detail:

- source words are in `0x0RGB` form
- `0x59ad4` converts them to `0BBBBBGGGGGRRRRR`
- example:
  - source `0x0fff`
  - converted `0x7bde`

This is the first clear point where we can say "these are real color blocks"
instead of attribute selectors.

Strong front-end callers include:

- `0x5a356`
- `0x5a3ac`
- `0x5a3de`
- `0x5a474`

These use static palette tables at:

- `0x5a6fa`
- `0x5a73a`
- `0x5a75a`
- `0x5a77a`

See:

- [palette_table_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/palette_table_reference.md)

## Genesis VDP Palette Reality

For the Genesis target, the important constraints are:

- the VDP color space is `9-bit RGB`
  - `3 bits red`
  - `3 bits green`
  - `3 bits blue`
- that means the machine can represent `512` possible colors in total
- but it cannot display all `512` at once
- it has `64` CRAM entries resident at one time
  - `4` palettes
  - `16` colors per palette

So the short answer is:

- **no**, the Genesis does **not** display `512` colors simultaneously
- it supports a `512`-color master space and `64` palette slots at once

Important practical limit:

- each tile or sprite selects one of the `4` palette lines
- color index `0` in a palette line is usually treated as the transparent slot
  for tiles/sprites, with the backdrop using the background color path

That means the final port problem is not "can the Genesis show enough raw RGB
precision?" so much as:

- can we fit Rastan's active palette banks into `4 x 16` palette lines at the
  same time
- and can we translate the arcade palette-bank selection encoded in actor/video
  attributes into Genesis palette-line selection cleanly

## What This Means For Rastan

Good news:

- Rastan already looks palette-bank driven rather than truecolor driven
- `0x45684` and friends select table-based attribute bits instead of embedding
  color directly in the graphics ROMs
- that makes a bank-remap strategy plausible on Genesis

Pressure points:

- sprites, text, and background all compete for the same `64` CRAM entries on
  Genesis
- the arcade hardware may allow more simultaneous logical palette banks than a
  straightforward Genesis mapping does
- if the arcade scene uses too many distinct banks at once, we will need:
  - palette-line remapping
  - scene-specific packing
  - or a compatibility policy for overflow cases

Current best working assumption:

- the graphics ROMs (`pc080sn`, `pc090oj`) can carry over directly as graphics
  sources
- the hard part is translating arcade palette selection and palette RAM state
  into Genesis CRAM layout each frame

## Current Fit Assessment

What looks promising:

- actor-side palette selection is already narrow enough to reason about through
  `a4 + 0x27`
- we already know the graphics browser can ground pages back to canonical ROM
  offsets
- that means we can eventually debug:
  - graphics source
  - palette-bank selector
  - Genesis palette-line assignment
  as separate problems

What is still missing before we can judge the fit well:

- the final palette RAM write/init path on the arcade side
- the number of simultaneously active palette banks in:
  - title
  - attract/story
  - live gameplay
  - boss / effect-heavy scenes
- how `pc080sn` layer palettes and `pc090oj` sprite palettes are partitioned in
  the original hardware

## What We Can Use Right Now

For debugging:

- `GRAPHICS TEST` in `apps/rastan` now surfaces raw ROM offsets for the current
  page, so the graphics side is already grounded in the extracted ROM regions
- `PC080SN` and `PC090OJ` are both browsed directly from those extracted
  regions, so later remap work can tie original code back to canonical ROM
  offsets instead of guessed copies
- the next useful debug step is to surface `a4 + 0x27` and the selected table
  byte when proven actor paths run

For the first consolidation / fit pass, also see:

- [palette_fit_audit.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/palette_fit_audit.md)

## Best Next Step

The best next palette-focused trace is:

1. follow real callers of `0x45684`
2. log `a4 + 0x3e`, `a4 + 0x38`, `a4 + 0x752`, `a5 + 0x118`, and `a5 + 0x2a2`
3. confirm which table byte gets ORed into `a4 + 0x27`
4. correlate that attribute byte with the final PC090OJ render path
5. find the arcade-side palette RAM write/init routines
6. measure how many palette banks are truly live at once per scene so we can
   judge the Genesis `4 x 16` fit honestly
