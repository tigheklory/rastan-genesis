# Build 0421 collision/visual semantic audit

Build 0419 remains the accepted baseline. Builds 0420 and 0421 are rejected.
This audit concerns semantic ownership, not the historical optimization-phase
label “Background Phase C.” Genesis Plane A and Plane B are visual planes;
neither is the gameplay collision map.

## Arcade provenance

Gameplay collision is a separate 64×64 word ring at arcade WRAM `0x0010DE00`
(mapped Genesis WRAM `0x00FF1E00`). Arcade
`collision_map_lookup_53a2e` (`0x053A2E`) converts the requested world point and
the foreground scroll at A5+`0x10AE/0x10B0` into an address in that ring and
returns it in A0. Player and actor collision routines read the word at A0,
usually masking its low seven bits; they do not read PC080SN name RAM or a
rendered tile code.

The retained arcade producers `0x0559B2` and `0x055A14` select collision words
from the collision field beginning at metatile offset `+0x20` (including the
`0x00FF` uniform-value form) and write them to `0x10DE00`. Their adjacent
PC080SN writes are a separate visual product. Genesis preserves this division:
selector 0/1/2 and `genesistan_stage_bg_collision_column` write the mapped WRAM
collision ring independently of Plane-A/Plane-B staging.

Collision can also change after base map production. Arcade
`collision_map_surface_postprocess_5a29c` (`0x05A29C`) calls
`collision_map_surface_mark_5a2ee` (`0x05A2EE`), which writes four collision
words at A0, independently modifies four earlier collision words, and only
then performs a distinct four-cell PC080SN visual tail. Build 0376 replaced
only that visual tail with `genesistan_collision_surface_mark_visual_native`;
the gameplay collision writes remain arcade-owned.

Static corpus evidence disproves visual identity as collision authority:

- pointers `0x3100` and `0x3200` have the same sixteen visual tile identities,
  but collision cells 13–14 are `0x3700` versus `0x3C00`;
- pointers `0x106C` and `0x21B0` have different visual tile identities, but the
  same sixteen collision values (`0x0001`).

Therefore visually identical records may differ in collision, different
visual records may share collision, and the live collision map may be mutated
without deriving a value from either Genesis visual plane.

## Build 0421 generated-record audit

The generated 64-byte record co-stores `visual[16]` followed by
`collision[16]`, keyed by the arcade descriptor's metatile pointer. This is
convenient storage, not shared semantic ownership:

- `resolve_plane_a_cell` reads only `visual[]` and never reads `+0x20`;
- `resolve_plane_a_collision_cell` reads `collision[]` directly and does not
  create or inspect a Genesis name word;
- the fused selector accessor deliberately returns both independent fields for
  one shared coordinate/descriptor lookup;
- Plane-B row resolution neither uses the generated record nor accesses
  collision;
- collision publication targets `0x00FF1E00`, never Plane-A/Plane-B staging;
- later gameplay collision mutations still target the separate WRAM ring.

`verify_collision_visual_semantics.py` gates these API boundaries and proves
both many-to-many directions in the authoritative corpus.

## Classification

**B — VISUAL AND COLLISION SHARE AN ARCADE DESCRIPTOR BUT REMAIN INDEPENDENT
FIELDS/PRODUCTS.** The produced collision ring then has an independent dynamic
lifetime. Collision is not derived from Genesis Plane-A or Plane-B tile
identity, and Plane B has no gameplay-collision ownership.

