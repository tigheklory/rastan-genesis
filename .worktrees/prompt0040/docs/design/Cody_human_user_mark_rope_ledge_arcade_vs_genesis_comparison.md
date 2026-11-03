# Cody — Human USER_MARK rope-ledge arcade versus Genesis comparison

> **RETRACTED / SUPERSEDED (2026-09-24):** The conclusion below that the two human markers
> identify different intended locations is wrong. Genesis Rastan is four logical rows lower
> because the ledge is missing. See
> `docs/design/Cody_rope_ledge_same_world_block_comparison.md` for the corrected same-world-block
> comparison. The original text is retained only as historical evidence of the superseded
> interpretation.

**Date:** 2026-09-24  
**Task type:** Focused runtime-evidence comparison; no implementation  
**Genesis baseline:** Build 0373  
**Build produced:** None  
**Production source/spec changes:** None

## Scope

This report compares only the manually placed `USER_MARK` records from the same visually intended
Round-1 rope-side ledge location in:

- ORIGINAL ARCADE MAME:
  `states/traces/build0374_rope_ledge_human_user_mark/`
- GENESIS NTSC MAME, Build 0373:
  `states/traces/build0374_rope_ledge_human_user_mark_genesis0373/`

The human markers are authoritative for this comparison. The previous automated-route assumption
(`0x02C550 / 0x2024`) is not used to assert that the two captures reached the same logical cell.

## Tooling discipline

Existing project tools reused:

- `tools/mame/scripts/rastan_arcade_rope_ledge_human_trace.lua`
- `tools/mame/scripts/rastan_genesis_rope_ledge_human_trace.lua`
- Existing ORIGINAL ARCADE and GENESIS NTSC MAME launch conventions

New tooling created for this comparison: **None**.

Why new tooling was necessary: **Not applicable**. This task read the two completed captures only.

No automated gameplay, new route, new trace script, neighboring-map investigation, ROM build, or
production patch was performed.

## Authoritative USER_MARK records

| Field | ORIGINAL ARCADE | GENESIS NTSC Build 0373 | Difference |
|---|---:|---:|---:|
| USER_MARK frame | 1845 | 1948 | capture-local frame numbers |
| `A5+0x013E` | `0x0003` | `0x0003` | equal |
| `A5+0x10A8` | `0x0000` | `0x0000` | equal |
| `A5+0x10CA` | `0x0000` | `0x0000` | equal |
| `A5+0x10CC` | `0x0003` | `0x0003` | equal |
| foreground scroll X | `0x0107` | `0x0107` | equal |
| foreground scroll Y | `0x0149` | `0x0129` | Genesis `-0x20` pixels |
| player screen X | `0x008A` | `0x0088` | Genesis `-2` pixels |
| player screen Y | `0x0070` | `0x0070` | equal |
| world-ring X | `0x183` | `0x181` | Genesis `-2` pixels |
| world-ring Y | `0x127` | `0x147` | Genesis `+0x20` pixels |
| player logical cell | row 36, col 48 | row 40, col 48 | Genesis four rows lower |
| exact collision probe | row 36, col 50 | row 40, col 50 | Genesis four rows lower |
| collision word | `0x0000` | `0x0496` | different cells; not a valid cell-to-cell comparison |

The Genesis retained foreground scroll and native staged foreground scroll both equal
`X=0x0107, Y=0x0129`; the discrepancy is not between those two Genesis representations.

## Source records at each marked cell

These values document what each marker selected. They must not be treated as an arcade-versus-
Genesis content divergence because the logical rows differ.

| Boundary | ORIGINAL ARCADE row 36/col 48 | GENESIS row 40/col 48 |
|---|---:|---:|
| live row-source pointer | `0x02A2A8` | `0x02C568` |
| retained source entry | `0x02A28C` | `0x02C54C` |
| Genesis runtime source entry | n/a | `0x02C74C` |
| descriptor attribute | `0x0003` | `0x0003` |
| metatile | `0x3408` | `0x2320` |
| player-cell source word | `0x01F6` | `0x043E` |
| collision-probe source word | `0x01F8` | `0x044A` |
| live arcade Layer-A word | `0x0003` | n/a |
| Genesis staged Plane-A word | n/a | `0x62DC` |
| Genesis final Plane-A VRAM read | n/a | `0x0000` |

At the exact Genesis collision-probe cell row 40/column 50, the staged word is `0x62E3`, the
final VRAM read is `0x0000`, and the collision word is `0x0496`. At the exact arcade collision
probe row 36/column 50, the live Layer-A word is `0x0003` and collision word is `0x0000`.

## First divergence and stop result

**Same logical world/map cell: NO.**

The first upstream divergence is coordinate state, before source selection:

```text
foreground scroll Y: arcade 0x0149, Genesis 0x0129
world-ring Y:         arcade 0x127,  Genesis 0x147
logical row:          arcade 36,     Genesis 40
```

There is also a two-pixel X difference (`screen X 0x008A` versus `0x0088`; world-ring X
`0x183` versus `0x181`), but it does not change the logical column or collision-probe column.

Because the marked captures resolve to different logical rows, their source pointers,
descriptors, metatiles, collision words, staged names, and final VRAM words are downstream values
for different cells. They cannot establish a terrain-publication defect at one shared cell.

## Likely subsystem classification

The evidence stops at **camera/foreground-scroll or manual-location alignment**. It does not prove
a defect in map-source resolution, descriptor decoding, collision publication, Plane-A staging,
VBlank publication, or VRAM. Per the task stop rule, no attempt was made to choose a neighboring
cell, reinterpret the marker, or fix anything.

## Relationship to prior Build-0374 route evidence

`docs/design/Cody_build0374_missing_rope_block_visual_collision.md` records the earlier automated
route evidence. This human-marker result supersedes that route as the authority for whether the
two manually intended locations match. It does not invalidate individual values measured in the
old route; it establishes that those values cannot yet be compared to these two unequal marked
cells as though they represented one shared location.

## Result

- Same logical world cell: **NO**
- First divergence: **foreground/world coordinate state**
- Build: **NOT BUILT**
- Patch: **NONE**
- STOP: **YES**, as explicitly required when the marked cells differ
