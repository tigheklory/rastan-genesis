# Rastan Player Bridge And Visibility Reference

This note focuses on the bridge region around:

- `0x443e0..0x449ff`

Use it when the question is:

- how player-linked state crosses between actor systems
- where `0x02c8` entries are gated, forced, or directly slaved to player coords
- which routines are body-facing versus fallback/helper-facing

## Why This Region Matters

This is currently the strongest ownership region in the whole reverse-
engineering pass.

Why:

- `0x447b6` directly copies live player coordinates into a `0x02c8` actor
- `0x447ce` decides which actor classes receive that direct copy
- `0x449b4` is the major `0x02c8` proximity/visibility pass

If the real visible player body is to be proven, it is very likely to pass
through this region.

## `0x443e0..0x443fc`

This pass iterates over the `0x0508` list:

- clears `a5 + 0x0214`
- starts at `a5 + 0x0508`
- loops 20 entries of size `0x40`
- calls `0x443fe` per entry

Interpretation:

- this is a pre-pass over `0x0508`
- it updates gating fields that later affect the `0x02c8` bridge/visibility
  behavior

## `0x443fe`

This helper:

- skips inactive entries
- ignores entries with `a4 + 0x0c == 0`, `0xff`, or inactive timing states
- sets bits in `a4 + 0x2e` when the display and world coords come within
  `12` pixels on each axis
- when both bits are set, clears:
  - `a4 + 0x2e`
  - `a4 + 0x0c`

Special case:

- if `a4 + 0x0c == 1` and `a4 + 0x0e == 1`, it rewrites `a4 + 0x0c = 2`

Interpretation:

- this looks like proximity / arrival / visibility gating for `0x0508`
- it is relevant because later bridge logic tests fields updated here

## `0x4449e`

This is the stage/class seeder for fixed actor slots:

- clears `a5 + 0x13ac`
- reads stage id from `a5 + 0x0118`
- uses the stage table at `0x444e0`

The decoded table is:

- stage `1 -> class 0x0e`
- stage `2 -> class 0x13`
- stage `3 -> class 0x14`
- stage `4 -> class 0x15`
- stage `5 -> class 0x10`
- stage `6 -> class 0x17`

For stages other than `5`, it seeds:

- `a5 + 0x0708`

For stage `5`, it seeds:

- `a5 + 0x0648`

Then it:

- writes `a4 + 0x38 = 1` or `2`
- writes class into `a4 + 0x06`
- writes `a4 + 0x1c = 0x80`
- calls `0x453a8`
- adjusts `a4 + 0x3a` through `0x444e6`

Important caution:

- this is a real seeded actor path
- but it has already produced wrong on-screen candidates when treated as the
  player body by itself

## `0x446bc`

This helper derives a selector value in `d3` from:

- actor class `a4 + 0x06`
- selected actor fields like:
  - `+0x30`
  - `+0x37`
  - `+0x3e`
- global counter `a5 + 0x0214`

It uses small byte tables at:

- `0x44778`
- `0x44796`

Interpretation:

- this is a visibility/proximity-side selector helper
- it feeds later logic in `0x449b4`
- it is not direct proof of body ownership by itself

## `0x447b6`

This is the strongest direct ownership hook currently known.

It writes:

- `player X -> a4 + 0x32`
- `player Y -> a4 + 0x30`
- `a4 + 0x0c = 0xff`
- `a4 + 0x07 = 0`

This is the cleanest currently known place where a `0x02c8` actor is directly
slaved to the confirmed player world coordinates.

## `0x447ce`

This is the class gate before the direct copy.

It keys on:

- `a4 + 0x06`

Direct player-coordinate copy through `0x447b6` is only taken for:

- class `10`
- class `11`
- class `18`

Otherwise:

- if `a5 + 0x0214 >= 18`, it can mark `a3 + 0x02 = 0`
- it writes `a4 + 0x3d = 1` through `0x447f0`
- and for most non-class-7 cases it falls into `0x448b2`

Interpretation:

- this is the key ownership discriminator
- the missing proof is still: which constructor creates the live `0x02c8`
  class `10`, `11`, or `18` entry we care about

Also important:

- there are now documented direct `0x02c8` seeds through `0x4677c` / `0x46790`
  that are not just helper-strip constructors
- the missing proof is whether one of those seeded entries reaches this class
  gate as `10`, `11`, or `18`

## `0x448b2`

This is the forced-state fallback.

It writes:

- `a4 + 0x07 = 0`
- `a4 + 0x08 = 0xff`
- `a4 + 0x3c = 0`
- `a4 + 0x05 = 15`
- `a4 + 0x09 = 1`

and plays sound effect `0x10` through `0x3a0ec`.

Interpretation:

- visible results from this branch are not automatically body-owned
- this is one reason helper/fallback actors were easy to misread on screen

## `0x44852..0x448b0`

This continuation:

- calls `0x448b2`
- may call `0x3b726` with `a4 + 0x2c`
- special-cases classes `8`, `9`, and `11`
- for classes `8` and `9`, temporarily switches to `a5 + 0x0508`, sets
  `a4 + 0x3d = 1`, then adjusts Y by `-16`

Interpretation:

- more evidence that this region bridges `0x02c8` and `0x0508`
- not every bridged result is the main body

## `0x449b4`

This is the major `0x02c8` proximity/visibility pass.

Setup:

- clears `a5 + 0x0242`
- clears five entries in:
  - `a5 + 0x12a8`
  - `a5 + 0x12c8`
- calls:
  - `0x448f2`
  - `0x44910`
- clears `a5 + 0x021e`
- starts iterating:
  - `a5 + 0x02c8`

Per-entry filters at `0x449e8`:

- active flag must be set
- state `a4 + 0x05` must be nonzero
- `a4 + 0x3d` must be zero

Then:

- if `a4 + 0x03 != 0`, it jumps into the large selector branch at `0x44548`
- otherwise it calls `0x446bc`
- then uses current actor coords plus player coords:
  - `d4 = a4 + 0x16`
- `d5 = a4 + 0x1a`
- `d1 = player X`
- `d2 = player Y`

Concrete bridge point:

- at `0x44a52`, this pass calls `0x447ce`

Immediately before that, it:

- writes a small per-entry record into `a5 + 0x12a8`
- copies:
  - `a4 + 0x16 -> a3 + 0x04`
  - `a4 + 0x1a -> a3 + 0x06`
  - `a4 + 0x29 -> a3 + 0x03`
- calls:
  - `0x4498c`
  - `0x448d8`

Interpretation:

- `0x447ce` is not a free-standing test
- it is part of the concrete `0x449b4` ownership/visibility loop over live
  `0x02c8` entries
- that makes `0x44a52` the best currently documented call site for proving
  which live `0x02c8` entries actually hit the player-coordinate bridge

### `0x4498c`

This helper is narrower than it first looked.

It checks:

- `a4 + 0x05`

and only reacts for states:

- `24`
- `29`
- `33`

Even then, it only sets:

- `a3 + 0x03 = 3`

when:

- `a4 + 0x08 == 2`

Interpretation:

- this is a small selector flag helper for a narrow state subset
- it does not explain ownership by itself

### `0x448d8`

This helper only triggers for:

- `a4 + 0x3e == 12`

When that matches, it:

- calls `0x3b726` with `a4 + 0x2c`
- then calls `0x40a1e`

Interpretation:

- this is a special replacement/reseed escape
- not a general ownership transform before `0x447ce`

### `0x44930`

This is a small dispatcher into the filter helpers at:

- `0x44c66`
- `0x44c6c`
- `0x44c72`

It branches on:

- `a5 + 0x13b4`
- `a5 + 0x0214`
- sometimes `a4 + 0x05`

Interpretation:

- pre-bridge filtering happens here
- but it still looks like visibility/overlap selection, not constructor-side
  ownership assignment

Interpretation:

- this is the best current bridge from actor ownership to player-relative
  visibility logic
- it should remain a primary tracing target

The rectangle/selector helpers it relies on are now documented in:

- [docs/02c8_filter_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/02c8_filter_reference.md)

## What This Region Proves

Good for proving:

- which `0x02c8` classes are directly slaved to player coords
- which paths are fallback/forced-state logic
- how `0x0508` and `0x02c8` interact in visibility/proximity logic

Not sufficient by itself for proving:

- which constructor originally seeds the correct live `0x02c8` body actor

## Best Next Step

Continue documentation around the constructor side that feeds the class gate:

1. compare the direct `0x02c8` seed path at `0x4677c` / `0x46790` against the
   helper-only class writers
2. find where a live seeded `0x02c8` entry becomes class `10`, `11`, or `18`
3. tie that constructor/reseed path to this bridge region
4. then follow the entry into `0x4684e`, `0x47140`, or `0x473b8`

Known constructor-side notes now live in:

- [docs/constructor_reference.md](/home/tighe/projects/rastan-genesis/docs/reverse-engineering/constructor_reference.md)
