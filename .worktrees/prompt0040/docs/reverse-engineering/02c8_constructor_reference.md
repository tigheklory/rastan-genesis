# Rastan `0x02c8` Constructor Reference

This note focuses only on constructor and reseed paths that write directly into
the `a5 + 0x02c8` actor list.

Use it when the question is:

- which routines seed live `0x02c8` entries
- which of those seeds are stage/event driven instead of helper-only
- whether there is enough proof to build another ROM from the `0x02c8` side

## Why This Note Matters

The major unresolved problem is still actor ownership.

What changed in the latest trace is that we now have concrete constructor-side
evidence for direct `0x02c8` seeding that is not just the known helper-heavy
`0x0748` / `0x06c8` / `0x09c8` family.

What changed again after that is that the broader fixed-slot seeding cluster is
now clearer too. The direct `0x46790` path is real, but it is also visibly used
for many stage/event-owned slots besides `0x02c8`.

The most important routines are:

- `0x45248`
- `0x46216`
- `0x463aa`
- `0x4644c`
- `0x4650e`
- `0x4677c`
- `0x46790`
- `0x4c706`
- `0x4ca34`

## `0x45248`

This is the small generic initializer used by several stage/event seeds.

It writes:

- `a4 + 0x00 = 1`
- `a4 + 0x03 = 1`
- `a4 + 0x2f = d0`
- `a4 + 0x04 = 1`
- `a4 + 0x1c = 1`
- `a4 + 0x20 = 1`
- `a4 + 0x21 = d1`
- `a4 + 0x0d = d2`
- `a4 + 0x1e = d3`
- `a4 + 0x1a = 0x0180`

Notably, it does not write:

- `a4 + 0x05`
- `a4 + 0x06`

Interpretation:

- this is a direct live-actor seed
- it does not resolve animation records by itself
- it also does not solve the bridge-owned class problem by itself
- it matters because `0x4677c` and later event code use it to seed `0x02c8`
  slots without going through the earlier helper constructors

## `0x4677c`

This is the clearest newly traced direct seeder for `0x02c8`.

It starts at:

- `lea a5 + 0x02c8, a4`

and then branches on stage/event id:

- `a5 + 0x013e`

### Early cases

For lower stage ids it seeds the first `0x02c8` slot directly:

- `< 2`: `d2 = 72`, `d3 = 0x0179`
- `< 6`: `d2 = 79`, `d3 = 0x00f4`
- `< 16`: also writes `a4 + 0x01 = 0x74`, then `d2 = 73`, `d3 = 0x0dab`

All of these end by branching to:

- `0x46790`

### Mid-range case: `16..19`

This is the first clearly structured multi-slot seed.

It seeds:

- `0x02c8` with `d0 = 0`, `d1 = 0`, `d2 = 70`, `d3 = 0x0266`
- `0x0308` with `d0 = 1`, `d1 = 17`, `d2 = 70`, `d3 = 0x0266`
- `0x0348` with `d0 = 0`, `d1 = 17`, `d2 = 71`, `d3 = 0x0236`
- `0x0388` with `d0 = 0`, `d1 = 17`, `d2 = 77`, `d3 = 0x0234`

It also sets:

- `a4 + 0x30 = 1`

for the three secondary slots.

### Later case: `>= 20`

It seeds:

- `0x02c8` with `d0 = 0`, `d1 = 0`, `d2 = 75`, `d3 = 0x01fc`
- `0x0308` with `d0 = 1`, `d1 = 17`, `d2 = 87`, `d3 = 0x01fc`
- `0x0348` with `d0 = 0`, `d1 = 2`, `d2 = 88`, `d3 = 0x01fc`

Interpretation:

- this is not a helper-strip constructor
- it is a real `0x02c8` slot seeder
- it is stage/event driven rather than obviously player-body owned
- it is the first credible non-helper constructor-side path for another ROM
  build from the `0x02c8` side, but only once the downstream class/state bridge
  is tied to it

## `0x46790`

This is the shared entry point inside `0x4677c`.

It normalizes:

- `d0 = 0`
- `d1 = 0`

and then calls:

- `0x45248`

Interpretation:

- references to `0x46790` in later event code are effectively direct seeds into
  `0x02c8`
- this is useful because several late event controllers call `0x46790`
  explicitly with concrete `d2/d3` values

Also important:

- downstream `0x02c8` code uses `a4 + 0x0d` heavily
- `0x46790` therefore looks more like a direct frame/tile seed than a full
  ownership seed
- that is one reason the missing class/state proof still matters

After the wider `0x46300..0x46776` trace, it is safer to describe `0x46790` as
a generic fixed-slot seed entry used by several event and stage controllers,
not as a body-facing constructor by default.

## `0x461b4`

This was initially treated as the first strong downstream link from a direct
`0x46790` seed into a live `0x02c8` runtime state.

That interpretation is no longer reliable.

The currently traced callers:

- `0x4b106`
- `0x4b14e`
- `0x4cab0`
- `0x4caf2`

act on neighboring fixed slots such as:

- `0x0448`
- `0x0348`
- `0x0488`
- `0x0388`

not the seeded `0x02c8` slot itself.

Interpretation:

- this is still a real fixed-slot state-assignment helper
- it is not currently valid proof of the direct `0x46790 -> 0x02c8` body path
- it should not be used as the main downstream bridge for another ROM build

## `0x4096c`

This is not a constructor, but it is an important `0x02c8` reseed gate.

It exits early if:

- `a4 + 0x03 != 0`
- `a4 + 0x05 == 0`
- `a4 + 0x05 == 15`

Otherwise it:

- checks X in `[344, 488)`
- checks Y in `[304, 480)`
- probes map tiles through `0x53a2e`
- may remap state through:
  - `0x40a60`
  - `0x40ae6`
  - `0x40b16`

If the actor falls into the off-screen / replacement case, it takes:

- `0x40a1e`

That path:

- preserves family from `a4 + 0x26`
- preserves `a4 + 0x38`
- preserves `a4 + 0x0753`
- resets the object through `0x4092e`
- restores those saved fields
- calls `0x4a0d8`
- writes `a4 + 0x21`
- copies `a4 + 0x34 -> a4 + 0x1c`

Interpretation:

- this is a live replacement/reseed path for `0x02c8`
- it is relevant because not every `0x02c8` actor is born only through one
  constructor; some are recycled through this gate

## `0x43f4e` And `0x43f52`

These routines looked promising because many event controllers call them around
the same time they seed direct fixed slots.

They are not class writers.

What they actually do:

- `0x43f4e` selects the base at `a5 + 0x03c8`
- `0x43f52` walks `a5 + 0x03c8` for `a5 + 0x0286` entries
- if an entry is active and state `+0x05` is nonzero, it writes:
  - `a4 + 0x39 = 1`
  - then calls `0x447f0`
- if an entry is active but state `+0x05 == 0`, it resets that entry through
  `0x4092e`

Interpretation:

- these are fixed-slot sweep/reset helpers
- they do not explain `a4 + 0x06`
- they do not repair the missing ownership proof for the direct `0x02c8` seed
  path

## `0x46300..0x46776`

This block is now best understood as a generic fixed-slot event seeding
cluster.

What it visibly seeds:

- `0x03c8`
- `0x0408`
- `0x0448`
- `0x0488`
- `0x0308`
- `0x0348`
- `0x0388`
- and, through `0x4677c`, sometimes `0x02c8`

Important examples:

- `0x46300` seeds `0x03c8` through `0x46790`
- `0x46342` seeds `0x0408` through `0x46790`
- `0x46384` seeds `0x0308` and `0x0348`
- `0x4650e` dispatches on stage id and reaches:
  - `0x4677c`
  - `0x466e0`
  - `0x465b2`
  - `0x46538`
- these branches repeatedly reseed non-`0x02c8` fixed slots with different
  `d2/d3` tile-base pairs and occasional family/flag writes

Interpretation:

- this makes the direct `0x46790` path more important structurally
- but less special from an ownership standpoint
- it now looks like a shared fixed-slot seeding mechanism, not a narrow player
  body constructor

### Event Controllers Inside This Cluster

The newer trace makes the controller structure clearer too:

- `0x46216` drives a staged event sequence on `a5 + 0x028a`
- `0x463aa` drives a two-slot event sequence on `a5 + 0x0288`
- `0x4644c` drives a three-slot event sequence on `a5 + 0x021c`
- `0x4650e` dispatches on `a5 + 0x0118` and fans into the same generic
  fixed-slot seeding machinery

What they have in common:

- they repeatedly seed neighboring fixed slots through `0x45248`
- they gate progression on emptiness checks or X-position windows
- they sometimes include `0x02c8`, but they do not make `0x02c8` special enough
  to imply player-body ownership

That is why this whole cluster is now better described as generic fixed-slot
event choreography instead of a clean constructor family for the visible body.

## `0x4c706`

This is an event-side direct `0x02c8` seed.

When:

- `a5 + 0x013e == 129`

it does:

- `lea a5 + 0x02c8, a4`
- `d2 = 72`
- `d3 = 0x0179`
- `jsr 0x46790`

Then:

- clears `a5 + 0x02a4`
- increments `a5 + 0x0206`

Interpretation:

- this is direct proof that event code can reseed `0x02c8` through the same
  fixed-slot path used by `0x4677c`

## `0x4ca1a` And `0x4ca34`

This is the strongest late event-side `0x02c8` seed currently documented.

After a two-slot emptiness check, it seeds:

- `0x0308` with `d2 = 121`, `d3 = 0x0d06`
- writes `a4 + 0x38 = 2`
- clears `a4 + 0x20`

Then it seeds:

- `0x02c8` with `d2 = 116`, `d3 = 0x0d06`
- writes `a4 + 0x38 = 2`

Interpretation:

- this is a concrete non-helper event path that writes directly into the first
  `0x02c8` slot
- because it also changes family to `2`, it is a strong reminder that not all
  live `0x02c8` owners are family `1`
- it still does not prove the seeded `0x02c8` slot reaches a body-facing class
  or runtime state

## `0x4ca50..0x4cb04`

This continuation seeds additional slots through the same shared path:

- `0x0348` with `d2 = 115`, `d3 = 0x0d06`
- `0x0488` with `d2 = 76`, `d3 = 0x0224`
- `0x0388` with `d2 = 82`, `d3 = 0x0224`

and ties them to helper/effect setup through:

- `0x461b4`
- `0x4354e`

Interpretation:

- this is event-driven mixed seeding, not clean player-body ownership
- but it proves the `0x46790` path is real and active in larger event systems

## Common Event Wrappers

Several small wrappers call `0x46790` with concrete `d2/d3` pairs.

Examples:

- `0x4bd54..0x4bd6c`
  - `d2 = 85, 76, 82, 83, 84`
  - `d3 = 0x0224`
- `0x4b988..0x4b9bc`
  - `d2 = 114, 113, 120, 123`
  - `d3 = 0x09ea`
  - or `d2 = 105, 104, 103, 118`
  - `d3 = 0x0224`

Interpretation:

- the `0x46790` seed path is widely reused
- but these wrappers still look event/stage driven, not uniquely player owned

## What This Changes

Before this trace, the constructor-side picture was dominated by helper-only or
helper-heavy paths:

- `0x45642`
- `0x457b2`
- `0x45b2e`

Now we also know:

- `0x4677c` seeds `0x02c8` directly
- `0x46790` is a live shared `0x02c8` seeding entry point
- `0x4c706` and `0x4ca34` reuse that same path in event logic
- `0x43f4e` / `0x43f52` do not solve class ownership
- the wider `0x46300..0x46776` region shows `0x46790` is a generic fixed-slot
  seed path, not a uniquely body-facing constructor

That is enough to stop saying "all constructor-side paths are helper false
leads."

## What Is Still Missing

Still missing:

- proof that one of these direct `0x02c8` seeds is the actual visible
  player-body owner
- the concrete path that yields a bridge-owned class `10`, `11`, or `18`
  entry through `0x447ce`
- proof of where `a4 + 0x06` is assigned for a live `0x46790`-seeded
  `0x02c8` actor before the bridge sees it
- proof that the seeded `0x02c8` slot becomes more than one member of a generic
  fixed-slot event family

Updated clarification:

- `0x461b4` no longer counts as proof of the direct `0x02c8` downstream path
- the remaining missing proof is both `a4 + 0x06` and the seeded slot's real
  body-facing runtime state

## Best Next Step

The next best proof target is now narrower:

1. trace which `0x4677c` / `0x46790` seeded entries survive into the
   `0x447ce -> 0x447b6` bridge
2. compare those against the known helper-only class writers
3. prove where that seeded entry receives `a4 + 0x06`
4. identify the real downstream state-assignment bridge for the seeded slot
5. if one direct `0x02c8` seeded entry reaches the bridge as class `10`, `11`,
   or `18`, that is enough to justify a new ROM build from the proven
   `0x02c8` owner side
