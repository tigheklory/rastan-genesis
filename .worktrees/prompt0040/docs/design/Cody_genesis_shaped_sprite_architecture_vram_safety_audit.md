# Cody — Genesis-Shaped Sprite Architecture / VRAM Safety Audit

## Scope and baseline

This is a read-only architecture audit. It does not modify production source, build a ROM, run
MAME, create a trace, consume a build number, change the counter, or begin Phase D/E or HUD work.

- Accepted baseline: **Build 0439**
- Exact accepted ROM-producing source commit:
  `033795e327a70b2cb79b94ed2632cb2630ed628b`
- Accepted rope benchmark: `798 / 798 / 798`, `13,317.147 ms`
- Active HEAD contains later documentation only. `git diff 033795e3..HEAD --
  apps/rastan-direct/src specs tools` is empty.
- Tighe-established fact accepted without re-investigation: free tile space remains throughout
  Round 1.

The governing semantic cut remains:

```text
arcade actor lifecycle / frame / position / orientation / presentation state
    -> generated native frame selection
    -> Genesis presentation geometry and tile residency
    -> final Genesis SAT
```

The retired chip tail is PC090OJ mapping-program/object-record production, object-RAM traversal,
and PC090OJ hardware interpretation. None of those should be rebuilt as a virtual device.

## Evidence and existing-tool reuse

This audit reused current source and generated artifacts as authority:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/dma.s`
- `apps/rastan-direct/Makefile`
- `build/pc090oj_frame_table.report.txt`
- `build/pc090oj_frame_table.coverage.json`
- the generated frame/index/piece-table binaries
- `specs/palette_decisions.json`
- `tools/translation/precompute_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_direct_dispatch.py`
- `tools/graphics_editor/gen_reindexed_pc090oj.py`
- the accepted native-sprite, residency, VRAM-capacity, and performance reports cited by those
  artifacts

New tooling created: **none**. New tooling was not necessary.

## Current path and ownership

| Step | Current implementation | Classification |
|---|---|---|
| actor lifecycle, state, position, animation selector, orientation, collision, AI, timing | retained arcade work-RAM/gameplay logic | **ARCADE GAMEPLAY SEMANTIC** |
| family/frame dispatch | exact generated Level-B route first, compact death route, then generated universal route | **ALREADY NATIVE**, with residual universal record interpretation |
| frame geometry/order | Python-generated normal/mirrored records | **OFFLINE-GENERATABLE; already offline for all reachable keys** |
| player BODY/weapon/secondary | 1,200 primary and 416 secondary generated keys; compact six-byte pieces except 28 genuinely mixed-attribute primary keys | **ALREADY NATIVE / GENESIS-SHAPED** |
| common Lizardman/Large Bat/Small Bat/cave/burst route | 38 exact Level-B records, eight-byte indexes and six-byte `{dx,dy,finalized_key}` pieces | **ALREADY NATIVE / GENESIS-SHAPED** |
| other legal gameplay frames | 1,898 universal general and 24 specialized records | **NATIVE**, but the ten-byte piece interpreter is **RESIDUAL TRANSLATION OVERHEAD** |
| position realization | add live actor X/Y; preserve wrapped PC090OJ coordinate semantics; convert to Genesis SAT bias in finalizer | **NECESSARY GENESIS PRESENTATION** |
| orientation | normal/mirrored layout is generated offline; live finalizer maps the retained H/V presentation bits to Genesis hardware flip bits | layout is **ALREADY OFFLINE**; hardware flip is **NECESSARY PRESENTATION** |
| pattern identity | Level-B/player keys are offline-finalized; universal records may still add actor base and perform dynamic variant selection | compact paths are **ALREADY NATIVE**; universal work is **RESIDUAL** where static |
| palette | retained effective arcade bank selects the existing generated palette route; SAT palette bits are composed at finalization | **NECESSARY GENESIS PRESENTATION** |
| tile residency | exact O(1) reverse lookup; first free cell not used by this frame; bounded miss worklist | **NECESSARY GENESIS PRESENTATION** |
| clipping | source opaque bounding box plus viewport tests | **NECESSARY PRESENTATION**; not safely removable globally |
| sprite size | every current visual piece is one 16x16 cell and emits Genesis size word `0x0500 | link` | **ALREADY GENESIS SAT**, but not rectangle-packed across pieces |
| ordering | six bounded semantic lanes are finalized in arcade paint order | **NECESSARY SEMANTIC/PRESENTATION BRIDGE** |
| SAT staging | finalizer writes one eight-byte Genesis SAT entry per accepted piece into one of two `staged_sprite_sat` banks | **ALREADY NATIVE** |
| VBlank publication | pattern worklist DMA first, then complete 80-entry/640-byte SAT DMA to VRAM `0xF800` | **ALREADY NATIVE / NECESSARY PUBLICATION** |

Normal gameplay does not parse an arcade descriptor or piece stream on a generated actor hit. The
old native fallback parser is retired. The generic actor miss path owns no output, and generated
coverage proves zero reachable unresolved generic/special keys. A dormant player unresolved-key
return into the retained compositor is still present behind validity checks, although all 1,200
primary and 416 secondary reachable keys are generated. The contact-coordinate helper also retains
a separate legacy reconstruction miss path; that is gameplay contact compatibility, not the visual
SAT pipeline.

Classification of remaining content:

- **NATIVE:** player, secondary/legs, Lizardman, Large Bat, Small Bat, cave block, burst, death
  effects, Chimera, Flying Demon, Four-Armed enemy, Valkyrie, and every statically reachable
  universal general/special gameplay key.
- **PARTIALLY NATIVE:** only dormant invalid/unproven-key compatibility boundaries, not a proven
  normal-gameplay visual route.
- **GENERIC FALLBACK:** no reachable normal-gameplay PC090OJ descriptor/piece interpreter.
- **ATTRACT/FRONTEND ONLY:** separate native frontend/status producers; they are not justification
  for changing the gameplay semantic cut.
- **UNKNOWN:** the 638 universal dense-index holes, all of which the generator classifies
  `PROVEN_UNREACHABLE`; they are not known gameplay frames.

Therefore “normal gameplay generic fallback still present” is best stated as **PARTIAL**: there is
dormant compatibility at invalid-key boundaries, but no proven reachable normal-gameplay generic
interpreter dependency.

## Current ROM frame representations

### Compact Level-B/common-enemy format

```text
frame: { u32 piece_offset, u8 count, u8 status, u16 frame_attribute } = 8 bytes
piece: { s16 dx, s16 dy, u16 finalized_pattern_key }                 = 6 bytes
```

The 38 records contain 237 pieces (`1,422` bytes) and cover cave block, burst, selectors
`0x17..0x1F` Lizardman, `0xB6..0xB8` Large Bat, and `0xB9..0xBB` Small Bat, both orientations.
The loop adds actor X/Y, performs the retained hidden-Y/capacity checks, and directly appends the
four-word semantic tuple. It does not call the generic per-piece emitter.

### Player format

The 12-byte primary/secondary indexes carry offset, count, format, frame attribute, and player
weapon-anchor geometry. The dedicated piece table is `19,428` bytes. Of 1,200 primary keys, 1,172
use compact six-byte pieces and only 28 use eight-byte pieces because their attributes genuinely
vary by piece. All 416 secondary keys are compact. Primary frames contain 2–8 pieces; secondary
frames contain 0–4 pieces.

### Universal format

The universal index has 2,560 six-byte records: 1,898 general native records, 24 specialized
dispatch records, and 638 statically unreachable holes. Its generated ten-byte pieces still carry
flags for a special condition, optional actor-Y adjustment, base-plus-delta identity, stage-based
code override, and per-piece attribute. The runtime interprets those flags and calls
`native_sprite_emit_fast` for each emitted piece. This is the largest clearly translation-shaped
producer that remains.

## VRAM ownership and safety

### Fixed and allocatable regions

The existing authoritative R1/P1 capacity proof gives:

| Owner | Pattern slots | VRAM bytes | Reusable for sprites? |
|---|---:|---:|---|
| transparent | 0 | `0x0000..0x001F` | no |
| fixed Plane B part 1 | 1..662 | `0x0020..0x52DF` | no |
| Plane-A selected package arena | 663..1301 | `0x52E0..0xA2BF` | no |
| proven R1/P1 sprite envelope | 1302..1535 | `0xA2C0..0xBFFF` | yes, sprites only |
| Plane-B nametable | 1536..1663 | `0xC000..0xCFFF` | no |
| fixed Plane B part 2 | 1664..1791 | `0xD000..0xDFFF` | no |
| Plane-A nametable | 1792..1919 | `0xE000..0xEFFF` | no |
| fixed Plane B part 3 | 1920..1983 | `0xF000..0xF7FF` | no |
| SAT | 1984..2015 | `0xF800..0xFBFF` | no |
| HScroll | 2016..2047 | `0xFC00..0xFFFF` | no |

Visually empty name-table/SAT/HScroll space is not pattern capacity. The nominal Window area is
also occupied by fixed Plane-B vocabulary in this gameplay layout.

### Current residency ceiling

Current source uses:

```text
SPRITE_TILE_BASE = 1339
NATIVE_CELLS     = 49
```

One resident cell is one 16x16 PC090OJ cell: four consecutive Genesis 8x8 patterns, 128 bytes.
The current region is patterns `1339..1534`, 196 patterns, **6,272 bytes**. Pattern 1535 is outside
the pool.

The allocator is:

- **tile/cell based**, not family-, frame-, or block-based;
- fully associative over 49 resident 16x16 identities;
- persistent between frames but reusable;
- replacing/evicting a resident identity only in a slot not marked used by the current frame;
- protected against same-frame overwrite by `pc090oj_cell_used`;
- backed by an exact two-level O(1) reverse index;
- serviced by a bounded 12-cell pattern-DMA worklist per update.

It is therefore a reusable cell cache, not a scene high-water allocator and not a fixed family
partition. If all 49 cells are needed by the current frame, or more than 12 new cells need upload,
the excess piece is dropped rather than reusing a live cell.

### Proven additional headroom and its limit

The R1/P1 proof permits at most 58 complete cells at base pattern 1302, using patterns
`1302..1533`; patterns `1534..1535` are a two-pattern fragment. Relative to the current 49-cell
pool, that is **nine additional complete cells / 36 patterns / 1,152 bytes** of proven R1/P1
capacity.

The same evidence measured 10,781 R1 frames: median 9 cells, P95 29, maximum 63; 47 frames exceeded
49 cells and eight exceeded 58. Thus 58 is a safe physical R1/P1 ceiling under the existing
background layout, but it does not prove zero-drop fidelity at the observed 63-cell peak. It also
does not prove that the same tail is safe in later rounds. A whole-game permanent expansion or
family partition therefore remains unproven.

## Options

### A. More native frame descriptors in ROM — YES

The Build-0426 and Build-0428 formats already prove this design. Moving statically decidable
universal frames to compact, orientation-specific ROM descriptors can remove:

- per-piece flag loads/tests;
- static condition branches;
- static Y-adjust decisions;
- base-plus-delta code construction when effective identity is fixed;
- repeated per-piece attribute loads when the frame attribute is invariant;
- per-piece calls through `native_sprite_emit_fast`;
- repeated queue-cursor reconstruction.

This costs ROM, not VRAM. Live actor X/Y, genuinely dynamic attributes/palette state, clipping,
residency, SAT order/linking, and publication must remain.

### B. Orientation-specific descriptors — YES

Normal/mirrored records are already generated for player, Level-B, and universal paths. Expanding
that practice duplicates small descriptor/piece data in ROM. It does **not** duplicate pixel data
or consume VRAM. Hardware H/V flip should still be used where it is the genuine final presentation
operation; descriptor orientation is for piece geometry/order, not a mandate to duplicate art.

### C. Packing into larger Genesis hardware sprites without a VRAM change — NO generally

The pipeline already performs the universally safe packing: each 16x16 source cell is one Genesis
2x2-pattern SAT entry rather than four 8x8 entries. Combining neighboring 16x16 cells into a
larger 1x1-through-4x4-cell Genesis sprite requires every 8x8 pattern for the rectangle to be
contiguous in Genesis size-order. The fully associative cache guarantees four-pattern contiguity
only *inside* one current cell; neighboring logical pieces may occupy unrelated resident slots.

Some exact frames may form legal rectangles, but they cannot use fewer SAT entries under the
current arbitrary inter-cell placement. They require offline-repacked contiguous art plus block
residency. Partial visibility also changes from per-16x16 clipping to one larger rectangle, so an
offline visual-equivalence proof is required for each candidate.

### D. Direct SAT emission — already close, but not producer-direct

The finalizer already writes native Genesis SAT words directly; no PC090OJ record exists between
the queues and SAT. Completely bypassing the queues at each actor producer is not presently safe:
the queues preserve six-lane paint order across independently traversed actor groups, and the
shared finalizer owns current-frame residency protection, clipping, SAT links, palette selection,
and the 80-entry ceiling.

The safe near-term interpretation of “native frame -> SAT” is therefore:

```text
arcade selects actor/frame
  -> compact native descriptor appends bounded native pieces
  -> one shared ordered finalizer resolves residency and writes SAT
```

The universal ten-byte interpreter can shrink. The shared finalizer cannot simply disappear until
ordering and shared residency have another proven owner.

### E. Genesis-contiguous frame/block graphics — selected families only

This is technically viable for a small R1/P1 pilot. It requires:

1. an offline-generated rectangular Genesis tile block;
2. a reserved/owned contiguous VRAM block or a block-aware allocator;
3. a frame descriptor with Genesis size and block-base identity;
4. exact clipping, palette, priority, flip, and ordering proof;
5. coexistence proof against the remaining dynamic 16x16 pool.

Using part of the nine-cell R1/P1 headroom is safer than carving the current 49-cell pool. It is
not yet safe for player/all enemies, and it is not proven beyond Round 1. A block pilot needs a
small residency partition/extension, but not a wholesale replacement of the existing cell cache.

## Representative families

“SAT entries” below means fully visible output; viewport clipping can reduce the published count.
No unproven packing count is presented as fact.

| Family/path | Current route | Proven logical pieces / SAT entries | Possible packed result | Extra ROM | Extra VRAM | CPU opportunity | Risk |
|---|---|---:|---|---|---|---|---|
| Rastan/player | compact native primary + secondary | primary 2–8; secondary 0–4; one SAT entry per visible piece | unknown; irregular body/weapon overlay and 28 mixed-attribute keys prevent a general static claim | already pays 14,400-byte primary index, 4,992-byte secondary index, 19,428-byte pieces | none for descriptors | compact loops are already near-minimal; finalizer dominates | high for rectangle conversion; low value now |
| Lizardman | Level-B compact, selectors `17..1F`, both orientations | 8 or 10 | not proven rectangular | none needed | none | little producer work remains; shared finalizer only | low value for another descriptor conversion |
| Large Bat | Level-B compact, selectors `B6..B8` | 2 or 4 | a four-piece frame is a plausible one-entry 32x32 candidate, but exact geometry/order must be verified offline | small block descriptor/art metadata | one 4-cell/16-pattern/512-byte reserved block for one 32x32 frame if added beside the dynamic pool | up to three SAT constructions/residency lookups removed on a qualifying four-piece frame; no cycle claim yet | medium; best bounded VRAM pilot |
| Small Bat | Level-B compact, selectors `B9..BB` | 1 | already optimal: 1 | none | none | none from packing | very low, but no benefit |
| stationary climbable rope | Plane-B map/collision terrain, not a sprite | not applicable | not applicable | none | none | none in sprite pipeline | out of scope |
| Segment-5 swinging rope | generated universal native actor, base `0x00F4`, state `0x20` | proven nine-piece 16x16 chain for selector 0; one SAT entry per visible piece | no fixed rectangle: later frames bend the chain | compact descriptors could add ROM | no descriptor VRAM; block layout not recommended | universal-interpreter work could be removed, but dynamic curved layouts make it a poor first rectangle pilot | medium/high; preserve contact/visibility coupling |
| Four-Armed enemy | universal native Level-A route | selector `0x61` has 9 pieces / up to 9 SAT entries | representative 48x67 composite is not a complete legal rectangle; no safe packed count proven | bounded compact duplicate described below | none | removes the universal ten-byte flag/base/attribute/helper work for a known nine-piece hot frame | low/medium; best ROM-only pilot |

The Four-Armed right-clipped reference proves why packing must not be inferred from a bounding box:
its nine source pieces can produce six SAT entries when three right-side pieces are clipped, but all
nine when fully visible.

## Palette/editor compatibility

Any new compact descriptor or block must remain generated by the existing pipeline, not hand-coded:

- `specs/palette_decisions.json` remains the sole decision registry.
- The precompute step must consume the existing decision ID and effective-bank context.
- `gen_reindexed_pc090oj.py` remains the artwork/reindex producer.
- `verify_pc090oj_frame_table.py` and the direct-dispatch verifier must compare generated geometry,
  identities, attributes, orientation, and piece order against the authoritative decoded result.

Relevant current registry decisions include
`PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001`,
`PAL-PC090OJ-STAGE1-LIZARDMAN-001`,
`PAL-PC090OJ-GAMEPLAY-LARGE-BAT-001`,
`PAL-PC090OJ-GAMEPLAY-SMALL-BAT-001`, and
`PAL-PC090OJ-GAMEPLAY-FOUR-ARMED-ENEMY-001`. A format change must not silently promote or alter
their statuses. The recommended pilot preserves the Four-Armed entry's current provisional status
and existing runtime palette route; it is a representation change, not a palette decision.

## Performance ranking supported by current evidence

1. **Universal ten-byte per-piece producer.** It still tests flags, may calculate special
   conditions/Y/base-relative codes/stage overrides, loads per-piece attributes, and calls the
   generic fast emitter. Build 0426 proved that converting comparable static frames to compact
   Level-B records removed 13–18 executed instructions per piece and reduced its controlled
   one-common-enemy delta from 14,850 to 12,800 cycles (`-2,050`, `-13.8047%`). That result supports
   the direction, not an unmeasured Four-Armed savings claim.
2. **Shared finalizer per accepted piece.** It still performs coordinate normalization, opaque-bbox
   clipping, palette/variant work where not pre-finalized, O(1) residency, used-cell marking, and
   SAT construction. Prior optimizations measured this as the largest remaining sprite cost
   center; it remains necessary work unless descriptors or block packing prove parts static.
3. **Residency misses and 128-byte cell DMA.** Stable frames cost no upload, but miss bursts consume
   the bounded 12-entry worklist and affect tail latency. This is a dynamic presentation cost, not
   generic PC090OJ interpretation.
4. **One SAT entry per 16x16 piece.** A legal packed block can remove repeated finalizer/SAT work,
   but only after contiguous-layout and clipping proof.

Orientation reconstruction and generic fallback dispatch are not leading hot costs: orientation
geometry is already generated offline, and no reachable normal-gameplay descriptor fallback is
executed.

## Tradeoff summary

| Candidate | ROM cost | VRAM cost | CPU benefit | SAT benefit | Risk |
|---|---|---|---|---|---|
| compact selected universal family/frame | small increase; generated six-byte pieces | zero | removes proven residual producer work | none | low/medium |
| broaden compact universal conversion globally | moderate/large; possible duplicate payloads | zero | broader removal of ten-byte interpreter | none | medium/high; dynamic exceptions must remain |
| enlarge current cache 49 -> 58 | tiny code/WRAM metadata change | +1,152 bytes used within proven R1 tail | fewer capacity drops/replacements, not guaranteed due 63 peak | none | medium; later rounds unproven |
| one Large-Bat 32x32 block pilot | small descriptor plus repacked art | 512-byte/four-cell block if added from headroom | fewer residency/finalizer operations | 4 -> 1 on qualifying frame | medium |
| frame/block layout for player or all enemies | large | large/variable | potentially large | potentially large | unacceptable as first step; coexistence/later rounds unknown |

## One recommended next bounded implementation

### Convert Four-Armed selector `0x61`, both orientations, to the compact direct route

This is the safest next implementation because the exact base/selector/compositor and nine-piece
frame are already proven, it exercises the residual universal path, and it changes neither VRAM
ownership nor SAT semantics.

Introduce one generated exact-usage dispatch for base `0x02E8`, family/discriminator 3,
compositor 0, selector `0x61`, both orientations. Represent each orientation with the existing
eight-byte compact index and nine six-byte `{dx,dy,finalized-or-dynamic-safe-key}` pieces. Preserve
the current palette decision/status and any genuinely dynamic attribute through frame metadata;
do not bake a new palette policy.

- Current visible SAT entries: **up to 9** (6 in the established right-clipped case).
- Expected native SAT entries: **unchanged, up to 9** (same clipping and order).
- Expected additional ROM: at most `2 * (8 + 9*6) + 10 = 134` bytes plus alignment if both
  orientation payloads are duplicated and one usage descriptor is added; generator deduplication
  can reduce this. The existing universal record must remain for other semantic keys until its
  consumer set proves removable.
- Expected additional VRAM: **0 bytes**.
- Runtime work removed for this frame: universal ten-byte flag interpretation, static condition/Y
  decisions where the generator proves them absent, base-plus-delta construction where safe,
  repeated invariant attribute loads, and per-piece `native_sprite_emit_fast` calls/cursor rebuild.
- Runtime work retained: arcade selection/state/position/orientation, live X/Y addition, queue
  bounds, final clipping, exact palette route, O(1) residency, miss DMA, SAT order/link/format, and
  VBlank publication.
- Expected CPU impact: **positive but unquantified**. Measure the same exact Four-Armed scene before
  and after; do not extrapolate Build 0426's 2,050-cycle controlled result.
- Validation: generator/verifier equality for both orientations and clipped/unclipped positions;
  unchanged piece order, attributes, pattern keys, queue lane, SAT entries, residency requests, and
  palette-decision consumers; normal canonical gates; then matched Four-Armed runtime timing and
  Tighe visual/hardware acceptance.
- Rollback boundary: the new exact usage descriptor, its compact records, and its one dispatch
  selection. Reverting those restores the existing universal route without touching cache,
  palette, VRAM, SAT finalizer, or gameplay logic.

This is more Genesis-shaped because static mapping-program interpretation becomes an offline ROM
frame and runtime becomes frame selection plus bounded native-piece append. It is safer than the
Large-Bat block experiment because it has zero VRAM and zero SAT-shape impact.

### Best later use of some proven free VRAM

After the ROM-only pilot is accepted, the safest separate VRAM experiment is one exact four-piece
Large-Bat frame repacked as a single 32x32 Genesis sprite in a four-cell/16-pattern/512-byte
contiguous block taken from the nine-cell R1/P1 headroom. It must remain a separate task because it
changes residency ownership, clipping granularity, and SAT count. It is not yet authorized or
implemented, and it cannot be generalized to later rounds from current evidence.

## Decision

- Native ROM frame descriptors can safely expand: **YES**.
- Orientation-specific descriptors can safely expand: **YES; zero additional VRAM**.
- Current arbitrary-residency pieces can be generally packed without VRAM-layout change: **NO**.
- Genesis-contiguous frame/block graphics require extra or partitioned contiguous VRAM: **YES**.
- Existing headroom is enough for one bounded R1/P1 block pilot: **YES, selected family only**.
- Residency redesign required: **NO** for the recommended compact Four-Armed pilot; **PARTIAL** for
  a future block pilot.
- Recommended next step: **the VRAM-neutral Four-Armed `0x02E8/0x61` compact descriptor pilot**.

Production source modified: **NO**. ROM built: **NO**. MAME run: **NO**. New trace: **NO**. Build
number/counter changed: **NO**. Phase D/E: **NO**.
