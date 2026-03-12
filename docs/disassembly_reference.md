# Rastan 68000 Disassembly Reference

This is the working reference for the arcade `68000` code.

It sits above the raw disassembly and below the narrower investigation notes.
Use it when you need to answer:

- where a routine lives
- what subsystem an address belongs to
- which actor list or RAM block a path touches
- whether a path is body-facing logic or only helper/effect logic

For dedicated subsystem notes, also see:

- [docs/02c8_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_reference.md)
- [docs/02c8_constructor_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_constructor_reference.md)
- [docs/02c8_frame_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_frame_reference.md)
- [docs/02c8_state_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_state_reference.md)
- [docs/02c8_transition_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_transition_reference.md)
- [docs/02c8_filter_reference.md](/home/tighe/projects/rastan-genesis/docs/02c8_filter_reference.md)
- [docs/0508_reference.md](/home/tighe/projects/rastan-genesis/docs/0508_reference.md)
- [docs/bridge_visibility_reference.md](/home/tighe/projects/rastan-genesis/docs/bridge_visibility_reference.md)
- [docs/startup_mode_reference.md](/home/tighe/projects/rastan-genesis/docs/startup_mode_reference.md)
- [docs/sprite_animation_reference.md](/home/tighe/projects/rastan-genesis/docs/sprite_animation_reference.md)
- [docs/constructor_reference.md](/home/tighe/projects/rastan-genesis/docs/constructor_reference.md)

## Ground Truth

Generated artifacts:

- [build/maincpu.disasm.txt](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt)
- [build/regions/maincpu.bin](/home/tighe/projects/rastan-genesis/build/regions/maincpu.bin)

Generation tools:

- [tools/disasm_maincpu.sh](/home/tighe/projects/rastan-genesis/tools/disasm_maincpu.sh)
- [tools/show_disasm_range.py](/home/tighe/projects/rastan-genesis/tools/show_disasm_range.py)

Regenerate with:

```bash
tools/disasm_maincpu.sh
```

The raw disassembly is a linear `objdump` of a raw binary. That means:

- vector/data regions appear as instructions
- jump tables and lookup tables need manual interpretation
- the file is useful as ground truth, not as a finished decompilation

## Core Method

The productive workflow for this codebase is:

1. start from a confirmed gameplay fact
2. find the RAM fields that change
3. identify the actor list or system that consumes those fields
4. trace the constructor/setup code for that actor
5. only then decode sprite family/frame/tile/palette data

This avoids the false-positive loop we hit when matching graphics in isolation.

## High-Value RAM Fields

Global player and stage state:

- `a5 + 0x10be`: player X
- `a5 + 0x10c0`: player Y
- `a5 + 0x1376`: stage-entry script active
- `a5 + 0x137a`: latched stage-entry command / control byte
- `a5 + 0x1384`: entry side selector
- `a5 + 0x1388`: stage-entry mode
- `a5 + 0x13c6`: stage-entry dispatcher enable
- `0x10d37a`: latched gameplay control word

Per-actor fields that matter repeatedly:

- `+0x00`: active flag
- `+0x05`: runtime state
- `+0x06`: class / constructor-selected subtype
- `+0x16`: X
- `+0x1a`: Y
- `+0x1e`: tile base
- `+0x20`: draw priority/order input
- `+0x21`: frame/slot counter source in several helper paths
- `+0x27`: sprite attribute bits, strongest palette lead
- `+0x28`: animation X offset
- `+0x2c`: animation Y offset
- `+0x30`: display Y in some player-linked paths
- `+0x32`: display X in some player-linked paths
- `+0x38`: sprite family
- `+0x3a`: animation length / aux field from `0x4543e`
- `+0x3e`: animation/state selector for `0x4543e`
- `+0x528`: back-pointer used by some helper/subpart groups
- `+0x752`: alternate form selector

## Major Program Regions

### `0x3a772..0x3a85e`

Pre-game input and top-level startup mode dispatch.

Important routines:

- `0x3a772`: raw input-port read/latch
- `0x3a79c`: high-level mode dispatch on `a5 + 0x04`
- `0x3a7fa`: title/start to stage-init handoff
- `0x3a832`: wait-for-play path before mode `2`

Use this region when tracing:

- title to gameplay transition
- credit/start behavior
- early mode changes

### `0x3d054`

Sprite builder dispatcher.

This is one of the most important addresses in the entire program.

It selects a family-specific sprite builder from `a4 + 0x38`:

- family `1 -> 0x4770e`
- family `2 -> 0x3f0bc`
- family `3 -> 0x3ffdc`
- family `4 -> 0x3fff0`
- other families via the jump table beginning at `0x3d09e`

Practical implication:

- raw graphics in `pc090oj` are not enough
- the code chooses family, frame, tile base, and attribute behavior first

### `0x40b66..0x41e22`

`0x02c8` actor update and render system.

Important addresses:

- `0x4092e`: reset helper
- `0x4096c`: replacement / reseed gate
- `0x40b66`: `0x02c8` group update pass
- `0x40b80`: per-entry dispatcher
- `0x40bc2`: state jump table
- `0x41cfa`: state/class record loader
- `0x41e22`: render pass into `0xd00460`
- `0x45248`: small generic seed helper used by direct `0x02c8` seeds
- `0x4677c`: direct fixed-slot `0x02c8` seeder
- `0x46790`: shared direct `0x02c8` seed entry point

State-dispatch map:

- `0 -> 0x41180`
- `1, 2 -> 0x473b8`
- `3..12 -> 0x47140`
- `13, 14 -> 0x473b8`
- `15 -> 0x40ccc`

Why this region matters:

- it is a normal visible-body candidate path
- it contains the strongest direct player-coordinate hook at `0x447b6`

New concrete trace points:

- `0x41cfa` copies an 8-byte state/class record into:
  - `+0x02`
  - `+0x08`
  - `+0x0d`
  - `+0x0e`
  - `+0x0f`
  - `+0x10`
  - `+0x11`
  - `+0x13`
- `0x4684e` is one concrete `0x02c8` update branch that:
  - reloads state records through `0x41cfa`
  - derives facing at `0x468d0`
  - chooses frame bytes for several `a4 + 0x3e` cases
- `0x4677c` seeds `0x02c8` directly from stage/event id `a5 + 0x013e`, and
  for some ranges also seeds nearby slots `0x0308`, `0x0348`, and `0x0388`
- `0x46790` is reused later by event code such as:
  - `0x4c706`
  - `0x4ca34`
  so it should be treated as a real constructor-side entry point
- `0x40c62` matches `0x02c8` entries on `+0x3e` and `+0x752` and then forces
  `0x44852`, so it is better understood as a repack/fallback bridge than as
  class ownership
- `0x47140` and `0x473b8` are the dominant live frame builders after those
  record loads

Important caution:

- the wider `0x46300..0x46776` trace shows `0x46790` is a generic fixed-slot
  seed path reused across many stage/event-owned slots
- `0x461b4` no longer counts as proof of the direct `0x46790 -> 0x02c8`
  downstream path
- the currently traced callers act on neighboring fixed slots, not the seeded
  `0x02c8` slot itself
- the remaining proof gap is still where the seeded `0x02c8` slot gets class
  ownership and a body-facing runtime state

### `0x420e6..0x42e38`

`0x0508` actor state machine.

Important addresses:

- `0x420e6`: update pass
- `0x42102`: per-entry dispatcher
- `0x4213a`: state jump table
- `0x42838`: shared update handler for states `4..9`
- `0x428b2`: direct copy from player coords into display coords
- `0x42d26`, `0x42dfa`: animation descriptor loaders
- `0x42e38`: descriptor-driven animation advance

Why this region matters:

- it clearly follows the live player position
- but it has already produced false positives when treated as the visible body
  without proving the downstream owner

### `0x443e0..0x449b4`

Bridge and visibility logic between actor systems.

Important addresses:

- `0x443e0`: `0x0508` to `0x02c8` gating-related pass
- `0x4449e`: stage/class seeder
- `0x447b6`: copy `player X/Y` into a `0x02c8` actor
- `0x447ce`: gate keyed on actor class
- `0x449b4`: `0x02c8` proximity/visibility pass

This is currently the strongest ownership path for the real player body.

Confirmed `0x447ce` classes that receive direct player coordinates:

- class `10`
- class `11`
- class `18`

Important caution:

- class `11` appears heavily in helper construction paths elsewhere
- class identity alone is not enough to prove "main body"
- the newer direct `0x02c8` seeds at `0x4677c` / `0x46790` are better
  constructor-side leads than the earlier helper-only family-1 paths

Additional concrete behavior:

- `0x447b6` writes:
  - `player X -> a4 + 0x32`
  - `player Y -> a4 + 0x30`
  - `a4 + 0x0c = 0xff`
  - `a4 + 0x07 = 0`
- `0x447ce` falls through to `0x448b2` for non-`10/11/18` classes in several
  cases, so not every visible result from this region is the direct body path
- `0x448b2` forces:
  - `a4 + 0x05 = 15`
  - `a4 + 0x09 = 1`
  - `a4 + 0x08 = 0xff`
  - `a4 + 0x3c = 0`

### `0x450d8..0x45dfa`

Stage/event helper actor systems and helper constructors.

Important addresses:

- `0x45248`: generic helper actor initializer
- `0x453a8`: simple actor constructor, then `0x4543e`
- `0x4543e`: animation record resolver
- `0x45684`: palette/attribute table applicator
- `0x45b2e`: multipart helper constructor
- `0x45be8`: helper-positioner using `0x071e/0x0722`
- `0x45c0c`: helper-positioner using live player coords
- `0x45cfc`: generic "make active / visible"
- `0x45dfa`: startup-side sprite-list builder

This region is essential, but also dangerous:

- many routines here are real
- many are player-linked
- several are still only helper or subpart logic, not the visible body

Known helper-only or helper-heavy paths:

- `0x45b2e`
- `0x45642`
- much of the `0x0748` family

Additional useful constructor:

- `0x453a8`
  - `a4 + 0x00 = 1`
  - `a4 + 0x05 = 3`
  - `a4 + 0x1a = 0x0180`
  - then calls `0x4543e`

This is small enough to port, but on its own it does not prove a body actor.

### `0x4543e`, `0x45502`, `0x45562`, `0x45684`

Animation and palette-table logic.

`0x4543e` loads 8-byte records into:

- `a4 + 0x1e`
- `a4 + 0x3a`
- `a4 + 0x01`
- `a4 + 0x28`
- `a4 + 0x2c`

Key table blocks:

- `0x45502`: default animation records
- `0x45562`: alternate animation records
- `0x45722`, `0x4576a`: palette/attribute tables used by `0x45684`

This area answers:

- frame code
- tile base
- offset set
- palette/attribute modifier bits

### `0x4770e` and family-1 records at `0x4771c`

Family-1 sprite build path.

This is important because it is the path we already proved is rendering the
wrong candidate sprites in the Genesis harness.

What we know:

- the frame record table begins at `0x4771c`
- frame records are short 4-byte-per-part lists ending in `0xFF`
- each part encodes control, Y offset, tile delta, X offset

This region is not the current mystery. The mystery is which actor should feed
it.

### `0x501ea..0x505a4`

Stage initialization.

Important addresses:

- `0x501ea`: stage-init master
- `0x50248`: choose stage id
- `0x502cc`: install stage pointer tables
- `0x503dc`: stage/background setup
- `0x504fa`: load stage spawn record
- `0x5052e`: load per-stage setup data, including player X/Y
- `0x5053a`: seed runtime defaults

This is the main startup-side entry point for gameplay data.

### `0x51024..0x54a32`

Active stage/gameplay-side entry and event logic.

Important addresses:

- `0x51024`: core active frame update
- `0x5126e`: side-entry threshold detector
- `0x52b4a`: small command-stream feeder
- `0x54a2c -> 0x54a32`: stage-entry event dispatcher

This region matters for:

- when gameplay is really "live"
- how entry scripts interact with the player globals
- separating stage-entry control from body rendering

## Actor Group Summary

### `a5 + 0x02c8`

Status:

- still the strongest visible-body candidate
- not currently seeded in the harness in a way that exposes a real player-body
  actor yet

Why it matters:

- receives live player coords at `0x447b6`
- is part of the normal render path
- has dominant live frame builders at `0x47140` and `0x473b8`

New practical note:

- the Genesis harness still does not seed this list in a body-facing way
- that is why helper-family candidates keep dominating on-screen output
- the next useful porting work is to seed or mirror one proven `0x02c8` owner,
  not to add more family-1 helper rendering

### `a5 + 0x0508`

Status:

- strong player-linked control/state cluster
- likely upstream of visible-body logic, but not enough on its own

Why it matters:

- receives live player coords at `0x428b2`
- may own animation/logic that later feeds another visible system

### `a5 + 0x05c8`

Status:

- helper/event-heavy
- useful for harness validation
- weak candidate for the actual body

### `a5 + 0x0748`

Status:

- helper/subpart/effect-heavy
- already proven to produce wrong visible candidates in the harness

Do not treat this as the main player body path without stronger proof.

## Tables Already Dumped

Useful generated tables:

- [build/02c8_tables.txt](/home/tighe/projects/rastan-genesis/build/02c8_tables.txt)
- [build/4543e_tables.txt](/home/tighe/projects/rastan-genesis/build/4543e_tables.txt)
- [build/0508_state_handlers.txt](/home/tighe/projects/rastan-genesis/build/0508_state_handlers.txt)
- [build/0508_anim_tables.txt](/home/tighe/projects/rastan-genesis/build/0508_anim_tables.txt)
- [build/4a0d8_table.txt](/home/tighe/projects/rastan-genesis/build/4a0d8_table.txt)
- [build/family1_frames.txt](/home/tighe/projects/rastan-genesis/build/family1_frames.txt)

## Known False Leads

These have already consumed time and should be treated skeptically:

- blind tile matching in `pc090oj`
- treating the `0x0748 state 15` family-1 helper as the player body
- treating the `0x0708` stage-family family-1 actor as the player body
- assuming a player-linked helper path is automatically the visible body

## Best Next Targets

The next reverse-engineering should focus on proof, not candidate rendering.

Recommended order:

1. trace the `0x02c8` constructor path that yields class `10`, `11`, or `18`
2. follow that entry through `0x47140` or `0x473b8`
3. identify the final family/frame/tile-base tuple for that exact actor
4. then reintroduce harness rendering for only that proven path

Current strongest concrete addresses for that work:

- `0x41cfa`
- `0x447b6`
- `0x447ce`
- `0x4684e`
- `0x47140`
- `0x473b8`

If that fails, the next fallback is:

1. correlate the `0x0508` path at `0x428b2`
2. identify which `0x02c8` owner it gates or mirrors
