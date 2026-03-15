# Rastan `0x02c8` Filter And Selector Reference

This note focuses on the filter helpers around:

- `0x44c5a..0x44fa8`

Use it when the question is:

- how `0x02c8` entries survive the proximity/visibility passes
- what the tables at `0x44ce0` and `0x44fa8` do
- whether this region is ownership logic or only filtering logic

## Why This Note Matters

The `0x449b4` visibility pass relies on small selector/filter helpers.

Those helpers are now clear enough to classify:

- they are rectangle/overlap filters
- not constructor logic
- not sprite decode logic

So they are important for narrowing survivors, but they do not tell us who the
player body actor is.

## Entry Helpers

The main entry points are:

- `0x44c5a`
- `0x44c60`
- `0x44c66`
- `0x44c6c`
- `0x44c72`

These choose one of several global anchor blocks:

- `a5 + 0x1254`
- `a5 + 0x028c`
- `a5 + 0x02b0`
- `a5 + 0x1248`
- `a5 + 0x022c`

Interpretation:

- the caller selects which global reference rectangle to test against

## Table Selection

The core selector is:

- `0x44c76`

It:

- uses `d3` as a table index
- defaults to table:
  - `0x44ce0`
- but if `a4 + 0x38 == 2`, it switches to:
  - `0x44fa8`

Then it normalizes:

- `d1`
- `d2`
- `d4`
- `d5`

into wrapped `0..511` coordinate space by adding `128` and masking with
`0x01ff`.

Interpretation:

- this is a family-aware spatial filter

## `0x44cba`

This helper performs the actual rectangle test.

It:

- reads 2 signed bytes from `%a0`
- reads 2 signed bytes from `%a1`
- adds them to the normalized actor/global coords
- compares the resulting extents

If the two ranges overlap, it returns:

- `d0 = 1`

Otherwise:

- `d0 = 0`

Interpretation:

- this is just a compact overlap test
- not actor ownership logic

## Tables

The tables at:

- `0x44ce0`
- `0x44fa8`

are signed offset pairs used by the overlap test.

Practical meaning:

- they define family- or selector-specific bounding rectangles
- they are not frame tables and not class tables

## Practical Conclusion

This region answers one useful question cleanly:

- why some `0x02c8` entries survive the proximity/visibility passes while
  others do not

It does not answer:

- who created the body-facing actor
- which constructor owns the player body

So this region is now considered understood well enough and should not be
treated as a primary unknown anymore.
