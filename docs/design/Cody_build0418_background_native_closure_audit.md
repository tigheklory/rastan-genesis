# Cody — Build 0418 Background Native Closure Audit

Date: 2026-10-13  
Accepted baseline: Build 0418 (Tighe, real Genesis)  
Scope: bounded Plane A / Plane B / collision runtime-cost audit

## Result

Background graphics are **not closed**. Build 0418 has native Genesis staging,
package residency, dirty row/column publication, and 32-word column DMA, but
the gameplay producers still interpret live arcade descriptor layouts for each
logical cell. The largest immediately safe duplication is the independent
Plane-A name and collision walk for the same cell in selector 0 and resident
selector 1/2 work. That duplication is the Build 0419 target.

## Current semantic cut

The retained cut is the arcade gameplay producer's logical map/camera decision.
The retired chip tail is PC080SN name/collision hardware realization. Native
code consumes the live producer state and emits final Genesis Plane-A/Plane-B
name words plus the non-visible 64x64 collision ring. No C-window image or
software PC080SN device is introduced.

## Per-cell work in Build 0418

Plane A `resolve_plane_a_cell` performs:

1. logical row/column subcell decode;
2. live `A5+0x1000` row-group source-pointer load;
3. camera/front/ring unwrap using `A5+0x10CC`, `A5+0x10CA`, and
   `plane_a_src_ref_block`;
4. arcade-to-Genesis descriptor relocation and validation;
5. metatile-pointer validation and cell selection;
6. palette-route/priority/flip attribute conversion;
7. scene-package tile-code-to-resident-slot lookup; and
8. final Genesis name-word assembly.

Collision `resolve_plane_a_collision_cell` independently repeats steps 2–5,
then selects either the uniform collision word or the per-cell collision word.
The collision ring remains a full logical 64x64 map.

Plane B row and directional-column paths separately interpret their live
walker/table index (`A5+0x10FC`, `A5+0x1386`), relocate descriptors, select the
metatile cell, convert attributes, and resolve the code through the active
Plane-B residency LUT. Plane B is not interchangeable with Plane A.

## Runtime versus invariant authority

Invariant source pixels, authored palette mappings, static tile identities,
package membership, and code-to-package-slot data already come from the
existing generators. Their authorities remain
`analysis/graphics_optimizer/editor_policy/Test.json`,
`specs/palette_decisions.json`, the existing PC080SN region generator, and the
boundary-package compiler. No competing palette or tile identity registry is
needed.

The current descriptor choice is genuinely runtime-dependent: the live
source-pointer table moves with map advancement; ring unwrap depends on the
camera front and scroll direction; current package/record state controls tile
residency; and palette routing depends on active scene/context. A future
offline native map representation must preserve those selectors rather than
bake one observed route. That larger conversion is not yet proven safe.

## Workload and dominant cost

- Selector 0 resolves 64 logical rows for one entering column. Build 0418 does
  64 name traversals plus 64 collision traversals: 128 resolver walks.
- Selector 1/2 updates one logical row across 64 columns. It always resolves
  64 collision cells and resolves 64 names when that row is resident.
- A vertical pan entering row resolves 64 Plane-A names plus 64 Plane-B names.
- Physical projection remains 64x32 and publication remains incremental.

The exact established full-span selector-0 measurement is 135,751.6 cycles per
event over 40 events (median 135,750; range 135,748–135,762), with 64 name and
64 collision resolver entries. Build 0418 changes only ROM-DMA safety and
corpus alignment, not this producer, so this is its mechanically equivalent
background-preparation baseline. The broader retained exact trace reported
worker median/p95/max 147,248/286,286/307,732 and IRQ
157,405/297,317/314,479 cycles.

## Decision

Fuse the two Plane-A products at one shared live descriptor/metatile traversal
where both are requested. This removes 64 duplicate descriptor walks from a
selector-0 event without narrowing the logical domain, freezing runtime state,
changing collision storage, altering Plane B, or changing publication/DMA.

The larger native-map preprocessing stage remains open. Background closure is
therefore **NOT CLOSED**, and scheduler Phase D is not ready to begin.

