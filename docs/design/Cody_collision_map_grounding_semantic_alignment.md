# Collision-Map Grounding / 8-Pixel Semantic Alignment Closure

**Agent:** Cody  
**Task type:** Original arcade semantic model and Build 0281 comparison  
**Baseline:** Build 0281  
**Accepted ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0281.bin`  
**SHA-256:** `8f4997566386f30c0c3dd37f922762d7f6b0677f8bbd9c4a8995046dfb9ab790`  
**Counter:** 281  
**Build produced:** NO  
**Production implementation changed:** NO

## Evidence and address discipline

This analysis used the current Ghidra project/exports, current production source, the two
Build 0281 hitbox reports, KF-067 and its preserved evidence, and the native Plane A source
proofs. Executable addresses below are labeled by address space. Every arcade-to-Genesis PC
correlation was resolved by exact segment membership in
`build/rastan-direct/address_map.json`; no arithmetic offset is used as authority.

The Ghidra seed/export was extended for this task to define and durably export the original
arcade grounding functions and collision-map structures. The relevant recovered functions
are:

| Function | `arcade_pc` | `runtime_genesis_pc` | map classification |
|---|---:|---:|---|
| actor surface-marker finder | `0x041064` | `0x041264` | `arcade_copy` |
| actor spawn X-bound selector | `0x04114A` | `0x04134A` | `arcade_copy` |
| actor spawn/ground/activate | `0x041180` | `0x041380` | `arcade_copy` |
| actor velocity and map collision | `0x042E38` | `0x043038` | `arcade_copy` |
| collision-map lookup | `0x053A2E` | `0x053C2E` | `arcade_copy` |
| collision-map base load | `0x053A64` | `0x053C64` | `patched_site` |
| player side/upper probe family | `0x053A6E` | `0x053C6E` | `arcade_copy` |
| player ground/contact probe family | `0x053B34` | `0x053D34` | `arcade_copy` |
| collision surface postprocessor | `0x05A29C` | `0x05A46C` | `arcade_copy` |
| collision surface marker | `0x05A2EE` | `0x05A4BE` | `arcade_copy` |

The original collision map is `arcade WRAM 0x0010DE00..0x0010FDFF`. Its mapped Genesis
location is `Genesis-WRAM 0x00FF1E00..0x00FF3DFF`; the base immediate is explicitly rebased
at `arcade_pc 0x053A64` / `runtime_genesis_pc 0x053C64`.

## ORIGINAL ARCADE COLLISION-MAP GROUNDING

### Coordinate contract

**PROVEN:** `collision_map_lookup_53a2e` treats the collision map as 64 rows by 64 words.
Each row is `0x80` bytes, so the vertical collision row height is exactly 8 pixels over a
512-pixel wrapping coordinate space.

With `scroll_x = A5+0x10AE`, `scroll_y = A5+0x10B0`, caller X in D1, and caller Y in D2,
the vertical identity recovered from `arcade_pc 0x053A4A..0x053A62` is:

```text
relative_y = (D2 - scroll_y) & 0x01FF
map_row    = (relative_y & 0x01F8) >> 3
row_bytes  = map_row * 0x80
```

The lookup's `+8` instruction is in the horizontal calculation at `arcade_pc 0x053A42`.
There is no fixed vertical `+8` in the lookup. Vertical rounding truncates toward the lower
multiple of eight after 512-pixel wrapping.

The corresponding horizontal word column is:

```text
relative_x = (D1 - scroll_x) & 0x01FF
map_col    = ((((relative_x >> 1) + 8) & 0x00FC) >> 2)
address    = collision_map_base + map_row * 0x80 + map_col * 2
```

### Actor scan and grounded-Y reconstruction

**PROVEN:** `actor_spawn_ground_and_activate_41180` supplies actor candidate X/Y through
`A5+0x0216` and `A5+0x0218`, calls the shared lookup at `arcade_pc 0x04128A`, and scans one
collision row at a time. A failed downward scan increments candidate Y by 8 and advances A0
by `0x80` bytes at `arcade_pc 0x0412C4..0x0412C8`; wrapping is over the full `0x2000`-byte
map. A reverse scan uses the corresponding `-8`/`-0x80` pair.

For ordinary actors (`A4+3 == 0`), an accepted ground marker has high byte `0x31..0x3C`
except `0x34`. Marker-controlled actor classes require the high byte selected by `A4+0x0D`.
At the acceptance path `arcade_pc 0x0412FC`, the original code reconstructs logical actor Y
as:

```text
if (scroll_y & 7) != 0:
    resolved_y = accepted_candidate_y - 8 + (scroll_y & 7)
else:
    resolved_y = accepted_candidate_y
```

For an ordinary grounded actor, `arcade_pc 0x041328` stores the result to `A4+0x1A`.
This is the actor logical/render/hurtbox anchor. It is not the sprite bottom and is not a
render-derived coordinate.

### Stage-1 concrete result

**PROVEN:** At the matched Stage-1 state, `scroll_y = 0x0149`, so `scroll_y & 7 = 1`.
The arcade ground marker is selected in collision row 38. Candidate Y 128 maps to that row,
and reconstruction gives `128 - 8 + 1 = 121 (0x79)`. The original logical actor anchor is
therefore 121; its composed visible bottom is 129.

Concise semantic flow:

```text
actor candidate/world Y
-> ((candidate Y - scroll Y) & 0x1F8) >> 3
-> 8-pixel collision-map row
-> scan for class-accepted ground marker
-> accepted candidate - 8 + scroll subrow (when nonzero)
-> A4+0x1A logical grounded Y
```

**DISPROVEN:** Actor grounding compares a final SAT/sprite foot against terrain. It samples
the logical map from a candidate anchor and reconstructs `A4+0x1A`; composition offsets are
applied later.

## BUILD0281 GROUNDING PATH

**PROVEN:** Build 0281 retains the original actor grounding and map lookup semantics. The
actor function is copied at `runtime_genesis_pc 0x041380`; its accepted-Y reconstruction is
copied at `runtime_genesis_pc 0x0414FC`; and the ordinary actor anchor store is copied at
`runtime_genesis_pc 0x041528`. The lookup is copied at `runtime_genesis_pc 0x053C2E`, with
only its map-base load redirected to `Genesis-WRAM 0x00FF1E00` at
`runtime_genesis_pc 0x053C64`.

**PROVEN:** Current gameplay collision-map production is in the native Plane A selector
tails, not in the historical KF-067 helper:

| Arcade semantic site | Build 0281 route | Collision destination identity |
|---|---|---|
| `arcade_pc 0x055968` | `runtime_genesis_pc 0x055B1E` patched JMP to `genesistan_hook_tilemap_plane_a_selector0_native` | row=`segment*4+cell`; col=`group*4+strip` |
| `arcade_pc 0x055990` | `runtime_genesis_pc 0x055B46` patched JSR to `genesistan_hook_tilemap_plane_a_selector12_native` | row=`group*4+directed_strip`; col=`segment*4+cell` |

Both helpers write `Genesis-WRAM 0x00FF1E00 + (row*64+col)*2`. Selector 0 reads collision
from `block+20+cell*8+strip*2`, except the `block+32 == 0x00FF` form uses `block+34`.
Selector 1/2 uses the transposed cell/strip form. The current source uses the descriptor
rebuild pointer/word tables and the retained arcade selector, segment, group, and strip state.

**PROVEN:** The pre-native arcade oracle established selector-0 logical destination identity
over 205 publications with `colMismatch=0` and `rowMismatch=0`. The source proof reproduced
all 4096 Stage-1 cells from the retained ROM source tuple with zero mismatches. Current native
source implements those proven formulas.

**PROVEN:** `genesistan_hook_tilemap_plane_a` and its private
`genesistan_stage_bg_collision_column` body still exist as symbols/source, but Build 0281 has
no executable caller or remap route to that old hook. Current remap sites route directly to
the selector-0 and selector-1/2 native helpers. KF-067's historical assignment of the row
shift to `genesistan_stage_bg_collision_column` cannot be carried forward as the current
Build 0281 writer provenance.

**PROVEN:** The original collision surface postprocessor remains relevant. At
`arcade_pc 0x05A29C` / `runtime_genesis_pc 0x05A46C`, selector/state gates can scan a
scroll-selected map row. `collision_map_surface_mark_5a2ee` writes trigger words and marks
four cells five rows earlier with collision high byte `0x34`. Therefore final live map
content depends on native publication plus retained postprocessing and their ordering, not
only on the static destination formula.

## FIRST +8 DIVERGENCE

**PROVEN:** The first observed semantic divergence is before actor anchor assignment. With
matched world/camera inputs, the arcade actor accepts the Stage-1 ground surface in row 38 and
stores logical Y 121; Genesis accepts the corresponding surface one row later, at row 39, and
stores logical Y 129. With `scroll_y=0x149`, the Genesis arithmetic is:

```text
candidate 136 -> relative_y 319 -> row 39
resolved_y = 136 - 8 + 1 = 129
```

The lookup and accepted-Y reconstruction themselves are byte-equivalent retained arcade
semantics, so categories B, C, D, E, and H as arithmetic changes are **DISPROVEN** for this
path. There is no extra vertical `+8`, off-by-one lookup row, altered reconstruction, or
actor-specific replacement at those PCs.

**PROVEN semantic boundary:** At the instant the actor scan consumes the map, the first
accepted Stage-1 ground marker is available in logical collision row 39 instead of original
row 38. This is a collision-map content/availability divergence, not a hurtbox or renderer
divergence.

**HYPOTHESIS, not implementation proof:** The current cause is within category F/G at the
live producer boundary: source/descriptor selection, publication timing/order, retained
surface postprocessing, or a later overwrite. Current native selector formulas statically
match the original logical source/destination contracts, while Build 0281 still exhibits
logical Y 129. No Build 0281 map dump or last-writer/source-tuple trace exists at actor
activation, so choosing among those current writer causes would be speculation.

The exact missing fact is one automated Build 0281 capture at the actor activation instant:
collision rows 38/39 plus the last writer and source tuple
`(selector, segment_index, group, strip, descriptor pointer, block pointer, collision source
word, destination row, event order)` for the accepted actor column, including postprocessor
writes. No additional user-controlled gameplay is required.

## KF-067 RECONSTRUCTION

**PROVEN:** KF-067 measured the following matched Stage-1 state in Builds 0210/0213:

| Measurement | Arcade | Genesis before KF-067 | Genesis after render compensation |
|---|---:|---:|---:|
| actor world Y (`A4+0x1E`) | `0x4B` | `0x4B` | unchanged |
| camera `A5+0x10B0` | `0x149` | `0x149` | unchanged |
| actor logical/screen anchor (`A4+0x1A`) | 121 | 129 | 129 |
| visible foot/bottom | 129 | 137 | 129 |
| ground band row | 38 | 39 | 39 |

KF-067 shifted only the expanded block-`A5+0x02C8` composition records upward by 8. Its
modern equivalent is the uniform subtraction in `native_sprite_emit` for every
`NATIVE_LANE_BACK_ENEMY` piece. Neither form changes collision-map words, actor logical Y,
or hurtbox state.

**Classification:** visually correct temporary compensation at the wrong semantic layer.
It corrected the measured representation and was appropriate to its bounded historical task,
but it is semantically incomplete because collision consumers retain the one-row error.

**PROVEN:** The rejected Build 0211/0212 attempts additionally established that the old
expansion engine clobbered D0-D7 and required a stack-latched record count. That register
hazard is historical implementation evidence; it does not explain the +8 semantic defect.

## PLAYER GROUNDING / CONTACT COUPLING

**PROVEN:** Player contact uses the same `collision_map_lookup_53a2e` map origin, scroll
fields, 8-pixel row conversion, and collision map as actor grounding, through related but
separate consumers:

| Consumer | Inputs before lookup | Purpose |
|---|---|---|
| `player_collision_probe_family_53a6e` | player X/Y anchor with horizontal/vertical extents and D6 | side/upper collision flags |
| `player_ground_contact_probe_family_53b34` | D1 from player X/left-right extent; D2=`player Y + vertical extent + D6` | foot/ground, special surface, hazard/death probes |

The ground/contact family recognizes collision codes 1, 3, 4, 7, 6, 8, and `0x7E`; code 8
branches to the player mode-8 path. Player grounding therefore samples feet/extent-derived
coordinates rather than using the actor spawn scanner's candidate-Y reconstruction.

**PROVEN:** Build 0281 retains these consumers at `runtime_genesis_pc 0x053C6E` and
`0x053D34`. The Build 0279 continuation correction restored the shared scroll-origin state
(`A5+0x10B0=0x149` in the Stage-1 evidence); no separate current player logical `-8`
correction was found in these lookup consumers.

**PROVEN coupling:** A map-content/origin correction at rows 38/39 can change player foot,
landing, platform, and hazard results because those routines read the same map. The player's
accepted Build 0281 movement/landing behavior is therefore a mandatory regression gate.

**DISPROVEN:** Globally subtracting one row inside `collision_map_lookup_53a2e` is a safe
actor-only repair. It would move every player probe and every other lookup consumer as well.

Static scope does not prove every slope, rope, or moving-platform outcome. It does prove the
shared lookup and hazard coupling that a future correction must preserve and test.

## AFFECTED ACTOR FAMILIES

**PROVEN affected:** Ordinary map-grounded actors (`A4+3 == 0`) initialized by
`actor_spawn_ground_and_activate_41180`, including the captured Stage-1 Lizardman. Their
logical anchor comes directly from the accepted collision row.

**PROVEN map consumers, class-dependent effect:** Marker-controlled actors (`A4+3 != 0`)
use the same row scan but require class marker `A4+0x0D` and may apply specialized placement
offsets. Actor classes with `A4+6 < 5` also invoke the shared map lookup after velocity
updates. They are map-sensitive, but an exact universal `+8` outcome is not established for
every class.

**Not proven affected:** Airborne enemies, bats, projectiles, bosses, and items cannot be
classified from BACK_ENEMY lane membership. Some may encounter shared map consumers, but
classes that bypass grounding or use specialized placement are not proven to share the
Lizardman's row-to-anchor result.

**DISPROVEN:** Every BACK_ENEMY rendering consumer is necessarily a logical-grounding
consumer. BACK_ENEMY is a composition/priority lane and is broader than the original actor
grounding class.

## CORRECT SEMANTIC FIX BOUNDARY

**PROVEN:** The earliest correct semantic boundary is collision-map ground-surface
production/availability before `actor_spawn_ground_and_activate_41180` scans the map. The
original lookup and accepted-Y reconstruction already express the arcade contract and should
not be modified to compensate for wrong map content.

The target state is:

```text
original semantic source/descriptor event
-> ground marker in logical collision row 38 at the matched Stage-1 state
-> original actor scan resolves A4+0x1A = 121
-> original hurtbox uses anchor 121
-> native composition uses ordinary shared viewport conversion
```

**Not yet proven:** The exact Build 0281 instruction/data edit. The current native publisher
implements the statically proven logical formula, and the historical helper blamed by KF-067
is dead. Until the live row-38/39 source tuple and last writer are captured, changing a
descriptor index, map row, postprocessor, or event order would violate the state-causality
rule.

## BACK_ENEMY -8 RETIREMENT IMPACT

**PROVEN current representation:** Logical actor Y is 129. Every BACK_ENEMY piece receives
`piece_y - 8` at `native_sprite_emit`, so the composed visible bottom is 129 rather than the
uncorrected 137. Hurtbox state remains anchored at 129.

**PROVEN double-correction result:** If logical grounding is corrected from 129 to 121 while
the lane subtraction remains, all grounded actor pieces move upward once from the corrected
anchor and again from the lane compensation. The Lizardman visible bottom would become 121,
8 pixels above the original arcade bottom of 129.

**PROVEN intended result:** Correct logical Y to 121 and retire the BACK_ENEMY-only `-8` for
the affected native composition. The two representation movements cancel relative to the
current screen position: actor correction moves pieces up 8; compensation retirement moves
them down 8. Visible bottom remains 129 while logical collision becomes arcade-correct.

Concrete Stage-1 Lizardman result:

| Quantity | Build 0281 | Correct semantic result | Original arcade relationship |
|---|---:|---:|---:|
| logical/hurtbox anchor | 129 | 121 | 121 |
| normal hurtbox Y extent | 109..145 | 101..137 | anchor-relative `-20..+16` |
| visible bottom | 129 | 129 | 129 |

The corrected hurtbox Y=101..137 overlaps the already-proven standing offensive Y=102..104,
without widening or moving the sword box.

**Scope caution:** Because BACK_ENEMY includes actors not proven to use this grounding path,
retirement must be paired with a producer/family audit or a proof that all lane consumers now
arrive in the shared native viewport coordinate convention. It must not be removed in
isolation before the map correction.

## PROPOSED BOUNDED CORRECTION

**Exact bounded correction available: NO.** The semantic boundary and required end state are
proven, but the current Build 0281 producer event that first places/preserves the Stage-1
surface in row 39 rather than row 38 is not yet identified.

The next evidence step is bounded and automated, not a general gameplay capture:

1. At the first Stage-1 Lizardman activation, dump collision rows 38 and 39 for its column.
2. Log native selector-0/selector-1/2 collision writes and retained postprocessor writes with
   monotonically ordered events and the complete semantic source tuple.
3. Identify the last writer of the accepted row-39 marker and the missing/overwritten row-38
   marker.
4. Compare that tuple to the original arcade producer event using arcade addresses first and
   `address_map.json` for executable correlation.

Only after that proof is the bounded implementation set authorized:

```text
correct the proven current map producer/source/timing divergence
validate player movement, landing, platforms, and hazards against Build 0281
retire the now-redundant BACK_ENEMY render-only -8 in the same semantic correction
validate grounded actor families and non-ground BACK_ENEMY consumers
```

No user-controlled gameplay is required to obtain the missing producer fact. This task ran
no MAME session, produced no ROM, changed no production implementation, and left counter 281
unchanged.
