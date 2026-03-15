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

## What We Can Use Right Now

For debugging:

- `GRAPHICS TEST` in `apps/rastan` now surfaces raw ROM offsets for the current
  page, so the graphics side is already grounded in the extracted ROM regions
- `PC080SN` and `PC090OJ` are both browsed directly from those extracted
  regions, so later remap work can tie original code back to canonical ROM
  offsets instead of guessed copies
- the next useful debug step is to surface `a4 + 0x27` and the selected table
  byte when proven actor paths run

## Best Next Step

The best next palette-focused trace is:

1. follow real callers of `0x45684`
2. log `a4 + 0x3e`, `a4 + 0x38`, `a4 + 0x752`, `a5 + 0x118`, and `a5 + 0x2a2`
3. confirm which table byte gets ORed into `a4 + 0x27`
4. then correlate that attribute byte with the final PC090OJ render path
