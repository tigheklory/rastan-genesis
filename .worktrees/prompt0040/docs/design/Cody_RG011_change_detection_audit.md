# RG-011 Change-Detection and Static-Reconstruction Audit

**Date:** 2026-10-21  
**Scope:** read-only Phase 2 audit of current Genesis-native presentation/service code  
**Production changes:** none

## Architecture boundary and method

The sprite semantic cut remains arcade actor/frame/position/flip/palette/visibility/order state ->
generated native frame record -> final Genesis SAT. The PC090OJ descriptor/piece interpreter,
object-RAM producer/mirror/scan/decoder tail is already retired. The audit inspected current native
sprite production/finalization, tile residency, palette presentation, Plane A/B publication,
frontend presentation, scene/package installation, generated tables, the current address map, the
canonical Ghidra exports, and established profiling reports/scripts. It did not create a new trace or
drive gameplay.

This audit distinguishes consumer polling from necessary per-frame evaluation. It does not classify
ordinary comparisons as polling. Palette publication (`palette_pending`), tile publication
(`tiles_dirty`), Plane A/B row/column dirty masks, and finished SAT publication
(`pc090oj_sat_frame_ready`) are already producer/event triggered. Scroll and moving-sprite SAT
publication are legitimately per-frame. The accepted gameplay HUD writer-triggered dirty design is
locked and was not reopened.

## Ranked inventory

Five concrete audit findings remain: one high-priority generated/static opportunity, two
medium-priority generated/static opportunities, and two do-not-touch legitimate/necessary polling
cases. There is no proven mutation-site A/B change in scope; consequently this audit proposes no new
dirty flag and claims no complete writer set for one.

| Priority | Finding | Class | Current repeated work | Recommended future model | Rope | Cave bats | Risk |
|---|---|---|---|---|---|---|---|
| HIGH | Frame/orientation aggregate opaque bounds with exact edge fallback | C + D | exact four-read/four-compare clip on every piece, including wholly offscreen actors | generated aggregate frame bounds; reject whole actor once, retain exact per-piece clip at viewport edges | high-frequency | potentially high for two airborne actors/three pieces | medium |
| MEDIUM | Stable actor-family classification | C + F | base LUT plus ten-byte discriminator/compositor/attribute/bank validation once per actor frame | generated family handle selected at a proven creation/state-transition boundary, or narrower exact dispatch | medium | medium: two bat actors versus one Lizardman | high until every identity-changing writer is proven |
| MEDIUM | Fixed-family palette-line resolution | C | effective bank/map lookup per emitted piece even for families with generated fixed R1/P1 policy | bake final line only for exhaustively fixed generated families; retain dynamic path elsewhere | medium | medium, multiplied by three pieces | medium |
| DO NOT TOUCH | Reverse residency lookup / physical tile slot | D | O(1) directory+leaf lookup per visible piece and miss handling | keep unless a later scene/package proof establishes non-evictable family residency | high-frequency | plausible miss/DMA sensitivity | high; slot is genuinely late-bound |
| DO NOT TOUCH | Frontend HUD scalar comparison cache | E, out of implementation scope | ten scalar-byte comparisons per stable frontend VBlank | polling remains until every P1/P2/high-score/credit/player-switch writer is proven | none in gameplay rope | none | high reflow/state risk; HUD explicitly excluded |

### 1. Aggregate frame bounds with exact edge fallback

**Authoritative state:** generated frame piece geometry/orientation plus live actor X/Y and global
flip. The generated frame index already owns the finite piece set and orientation. No retained-code
writer hook is required.

**Current work:** each piece independently selects its oriented source bounds, adds absolute X/Y,
and performs four viewport comparisons. This is correct but repeats rejection work when a complete
multi-piece actor is outside the viewport.

**Preferred model:** C, generated/static native data, combined with D at the edge. Generate one
aggregate bbox per frame/orientation. Test it once after live actor placement. If wholly outside,
reject the entire frame. If it intersects the viewport edge, preserve today's exact per-piece clip;
if wholly inside, the future design may mark its pieces clip-proven. This preserves partial-object
edge behavior and SAT order.

**Expected benefit:** proportional to pieces in rejected or wholly visible actors; it can remove
multiple bbox table reads/branches but not residency or SAT work. It is rope-relevant and could help
airborne actors crossing viewport edges. Risk is medium because every orientation, wrap case, global
flip, and partially visible frame requires exhaustive equivalence. Recommended future work: RG-012
profiling/proof before implementation, then a single isolated candidate if the rejected/inside
population is material.

### 2. Stable actor-family classification

**Authoritative state:** retained actor base code (`a4+0x1E`), raw discriminator, compositor
(`a4+0x38`), selector, attribute policy, effective bank, and orientation. Current
`.Lnative_generic_frame_try` uses the generated base LUT then revalidates these fields every actor
frame. Selector/orientation and many state transitions genuinely change; the family identity is
usually stable but is not yet proven immutable.

**Authoritative writers:** not bounded by this audit. They include actor creation and animation/state
transitions spread through retained logic. Therefore no A/B hook or dirty flag is recommended. A
future task must use Ghidra/address-map proof for all identity-changing writers and preserve
registers, CCR, stack, PC-relative references, declared tables, and shift reflow; the Build
0470/0471 failures make inference here unacceptable.

**Preferred model:** C/F. Prefer a generated direct family dispatch or creation-time native family
handle only after complete writer proof. Keep selector/orientation and any transforming/death state
late-bound. Expected benefit is once per active actor frame, so two bats can cost more classification
than one Lizardman even before piece work. Risk and reflow risk are high. Recommended future work:
after RG-012 measurement, a dedicated provenance-only RG task before any build.

### 3. Fixed-family palette-line resolution

**Authoritative state:** generated piece/frame attribute plus `native_sprite_lane`,
`pc090oj_sprite_ctrl_shadow`, actor override, and `current_sprite_palette_map`. Scene installation
sets the map. Sprite-control writes are centralized at arcade PCs `0x03A1D8`, `0x03AE34`,
`0x03AF1E`, `0x03EF28`, `0x03EF48`, `0x03EF8A`, `0x03EFAA`, and `0x045306`; the current address map
maps them to patched sites `0x03A3D8`, `0x03B04C`, `0x03B136`, `0x03F124`, `0x03F144`, `0x03F186`,
`0x03F1A6`, and `0x045502`. Those sites prove controller capture, not that every actor's effective
palette is fixed.

**Preferred model:** C only for generated families whose scene/lane/low-nibble policy is exhaustive
and fixed. Bake the final Genesis palette line in frame metadata. Dynamic Level-A, actor override,
scene-map, and controller cases retain the current lookup. No writer insertion is needed for the
fixed subset. Expected benefit is a small table/addressing reduction per proven piece; rope and bats
are medium relevance. Risk is medium because wrong policy changes artwork colors. A future RG task
must enumerate fixed families and exhaustively compare all bank/map outcomes.

### 4. Reverse residency is legitimate late-bound work

The generated key identifies artwork, not its current physical VRAM cell. The 49-cell pool can be
allocated, evicted, and refilled; misses create a bounded DMA work item. The exact O(1)
directory+leaf lookup is therefore D, legitimate per-frame work. Baking a physical slot into a
record would be incorrect under current eviction semantics. A future scene/package resident binding
is only plausible after proving a family's complete working set and non-eviction lifetime. Until
then this path is do-not-touch. Bat animation/direction may expose residency misses or DMA churn, so
it should be measured, not presumed removable.

### 5. Frontend HUD comparison cache is polling but excluded

`genesistan_hud_prepare_frontend` compares P1, P2, high-score, and credit bytes against
`native_hud_cache` during each stable frontend VBlank. This is genuine consumer polling. The normal
gameplay HUD uses its accepted writer-triggered dirty contract and is untouched. The frontend writer
set is not proven here, `_full_hud` is known absent, and RG-011 forbids HUD implementation. This is E
and do-not-touch until a separate HUD prompt proves every writer and safe presentation boundary.

## Additional translation remnants

No PC090OJ object-RAM scanner, mirror, descriptor interpreter, or arcade piece-stream parser remains
in gameplay. The generated universal Level-A path still computes a small number of retained
conditions and applies generated records; it is native coverage compatibility, not a chip emulator.
It can shrink as exact Level-B family coverage grows, but must not be bypassed.

PC080SN still has transitional runtime interpretation outside the sprite finalizer: the shared
`0x03C950` C-range dispatcher/staging route, runtime descriptor rebuild/source relocation, and
item-page strip pointer relocation. The descriptor rebuild is event-bound to scene/reseed state, not
per-frame change polling. These should be retired only by moving the semantic cut above their
respective PC080SN producer tails and emitting final Plane A/B words directly. They are additional
architectural-removal candidates, not Phase 2 production changes.

## Bat / flying-enemy presentation conclusion

One Large Bat plus one Small Bat means two actor classifications and three piece finalizations. That
alone does not prove the reported slowdown. Rapid selector/direction changes may alter generated
frame choice; shared graphics may either improve hits or expose residency churn; offscreen crossings
may amplify per-piece clipping; animation can create tile-DMA misses. All are presentation-side and
none requires changing bat gameplay.

A dedicated bat-versus-Lizardman profile is warranted. Reuse the existing `profile_native_*`
symbols and native sprite cost-bucket tooling. On an owner-provided or already established route,
record per frame: actor probe/hit/miss counts, Level-B/universal classification cost, piece attempts,
bbox rejects, residency hits/misses, allocations/evictions, tile-DMA worklist count, emitted SAT
pieces, and finalizer cycles. Separate Large Bat and Small Bat by their proven generated families and
compare equal-duration windows with Lizardman. Do not manually navigate or create an unrelated
gameplay trace.

## Roadmap and closure

1. **RG-012 measurement:** bat-versus-Lizardman and rope cost buckets using existing instrumentation.
2. If measured material, isolate aggregate frame culling as one candidate build with exhaustive edge
   equivalence.
3. Only if classification is material, perform a writer-complete family-identity provenance task.
4. Consider fixed palette-line baking only for exhaustively fixed generated families.
5. Keep reverse residency, moving-sprite SAT, scroll, and exact edge clipping late-bound.

Places still discovering changes by polling: frontend HUD only in this audit. Places that should
become writer-triggered: none proven in current scope. Places suited to generated/static data:
aggregate frame bounds, a future proven stable family handle, and fixed-family palette lines.
Legitimate per-frame checks that remain: actor activity/state/selector/orientation/position/global
flip, viewport-edge clipping, residency/miss/DMA, SAT ordering/link/capacity, moving sprite SAT, and
scroll. Normal HUD, absent full HUD, bat gameplay, Plane A/B behavior, audio, Phase D, and Phase E
remain untouched.
