# Build 0438 horizontal versus vertical background-scroll symmetry audit

Date: 2026-10-17
Audit type: read-only static performance/architecture audit
Baseline: Build 0438, commit `29412437861ea5e7fb046fc6d0b1c1bb58d73b2a`

## Conclusion

**B — HORIZONTAL IS PARTIALLY SYMMETRIC.**

The material descriptor/native-record work is already hoisted on both axes:
Build 0423 optimized the horizontal Plane-B directional-column producer and
Build 0424 optimized the horizontal Plane-A selector-0 producer. Build 0425 was
not the horizontal analogue of Build 0434: selector 1/2 publishes one fixed row
across 64 columns and is therefore another vertical row-entry producer.

Build 0434 added a later optimization class only to the general vertical pan
row publishers: select the active residency LUT and staging-row context once,
then perform the residency lookup inline. The two horizontal column producers
still enter the general scene-aware residency helper once per emitted logical
cell: up to 64 calls for Plane A and 32 calls for Plane B. Fixed-column staging
address terms are also still rebuilt inside those loops. Thus horizontal is
not missing all prior optimization, but it does retain a direct analogue of
the repeated helper/setup work removed from the general vertical path.

No implementation is made by this audit.

## Exact vertical crossing paths

### General scene-1 vertical pan: Plane A and Plane B

`genesistan_plane_a_pan_publish_entering_rows_up` and
`genesistan_plane_a_pan_publish_entering_rows_down` in
`apps/rastan-direct/src/tilemap_hooks.s` derive the old and new visible tops
from arcade-owned scroll state. For each crossed logical row they call, in
order:

1. `.Lplane_a_publish_logical_row_native`;
2. `.Lplane_b_publish_logical_row_native`.

Plane A processes one fixed logical row across all 64 logical columns as 16
four-column blocks. It hoists the row source pointer, physical staging-row
base, active-LUT base, and live horizontal ring front once per row. Fifteen
ordinary blocks select one descriptor/native record per block and resolve four
tile codes through the already-selected active LUT inline. The one block that
can straddle the live ring front retains four authoritative per-cell calls to
`resolve_plane_a_cell`. It writes 64 final staging words and marks one physical
row in `fg_row_dirty`. This visual row publisher does not own collision-map
writes.

Plane B processes one fixed logical row across all 64 logical columns. It
hoists its descriptor-table base, row offset, physical staging-row base, and
active-LUT base. It caches the current 16-column descriptor group, uses the
generated six-byte Plane-B visual record, performs 64 inline residency
lookups, writes 64 staging words, and marks one physical row in `bg_row_dirty`.
Plane B has no collision product and no Plane-A live-ring seam.

The existing VBlank strip publishers turn those dirty-row bits into 64-word
row DMAs. All 64 logical cells remain produced; Build 0434 did not prune the
logical domain.

### Selector 1/2 vertical row path: Plane A

`genesistan_hook_tilemap_plane_a_selector12_native` is a separate retained
vertical row-entry path. Despite an obsolete source comment calling it a
"horizontal column producer," its executable data flow fixes one logical row
and iterates 64 logical columns in 16 four-column blocks. Fifteen blocks share
descriptor/native-record/attribute work. The single block that can straddle
the live ring front falls back to four per-cell authoritative resolutions.

For a resident row, all 64 cells retain visual/residency work, staging writes,
and collision writes; for a nonresident row, all 64 collision writes remain
and visual/residency/staging work is omitted. Unlike the general pan row
publisher, the normal 60-cell shared-block path still calls
`fg_cache_resolve` per resident cell, and the seam block retains its general
resolver. Build 0434 did not rewrite this selector hook.

## Exact horizontal crossing paths

### Plane A selector 0

`genesistan_hook_tilemap_plane_a_selector0_native` publishes one fixed entering
logical column across all 64 logical rows. It obtains the entering column from
`A5+0x10CC`/`A5+0x10CA`, advances the boundary transition state, computes the
visible top once, and traverses 16 four-row descriptor segments.

Build 0424 already hoists the live source selection, descriptor
relocation/validation, generated native-metatile record lookup, and final
attribute calculation once per four-row segment. The inner four-cell loop
still:

- reads an independent collision word and visual tile code;
- calls `fg_cache_resolve` once for each valid visual cell;
- writes all 64 collision cells;
- tests each logical row against the 32-row resident window;
- writes only the 32 resident Plane-A staging cells.

After the traversal, it marks exactly one logical column in `fg_col_dirty`.
`vdp_commit_fg_columns_if_dirty` gathers the 32 strided staging words and emits
one 32-word Plane-A column DMA using VDP autoincrement `0x80`.

There is no within-column live-ring-front seam: the source column is fixed for
the event. The all-64-row traversal is nevertheless required because collision
and logical/cache coherence are 64-row contracts.

### Plane B directional column

`genesistan_pc080sn_directional_dispatch_native` follows the arcade direction
gates. Its forward crossing arm calls `.Ldirectional_publish_column_native`
when the subcolumn accumulator crosses the eight-pixel boundary. The reverse
arm in this current dispatcher adjusts scroll state but has no corresponding
column-publication call.

The publishing arm validates the selected descriptor once and converts it to
the generated six-byte Plane-B visual record once. Build 0423 restricts the
loop to the 32 resident logical rows, reads one tile code per row, and calls
`fg_boundary_resolve_b` once per row. It writes 32 staging cells and marks one
column in `bg_col_dirty`. `vdp_commit_bg_columns_if_dirty` gathers and DMAs the
32-word strided Plane-B column. There is no collision product.

## Build-by-build history

### Build 0423

Build 0423 was specifically a **horizontal Plane-B directional-column**
optimization. It moved invariant descriptor attribute conversion and copied
tile-block recovery into generated visual records, selected that record once,
and changed a 64-row probe/reject traversal into exactly 32 resident-row
outputs. Per column it changed 64 raw tile reads and 64 generic producer calls
to 32 tile reads and no generic producer calls; runtime attribute conversion
was removed. It deliberately retained 32 dynamic residency lookups. The
targeted measured operation fell from 64,578 to 12,486 median cycles.

### Build 0424

Build 0424 was specifically a **horizontal Plane-A selector-0 column**
optimization. Its "four-row" organization describes the traversal within a
fixed entering column; it does not mean vertical camera motion. Descriptor and
native-record selection changed from 64 to 16, attribute conversion from 80
to 16, while all 64 residency lookups and collision writes remained. The
targeted selector-0 event fell from 112,090 to 49,918 median cycles.

### Build 0425

Build 0425 was a **vertical Plane-A selector-1/2 row** optimization. Its fixed
logical row traverses 64 columns as 16 four-column blocks. It reduced
descriptor/native-record discovery from 64 to 19: 15 shared blocks plus four
per-cell seam fallbacks. It retained all 64 collision writes and, for a
resident row, all 64 residency lookups and staging writes. It is not the
horizontal analogue of Build 0434. The natural rope route did not execute this
hook; the controlled median fell from 122,672 to 33,984 cycles.

### Build 0434

Build 0434 optimized the separate general vertical pan path that pairs one
Plane-A row publication with one Plane-B row publication. Relative to Build
0433, it:

- hoisted Plane-A row source, staging-row base, active-LUT base, and ring front
  from 16 block setups to one row setup;
- reduced each ordinary Plane-A block helper to two-register preservation;
- inlined active-LUT/miss semantics for the 60 non-seam Plane-A cells;
- hoisted Plane-B staging-row and active-LUT bases;
- inlined the Plane-B lookup for all 64 cells;
- removed 124–128 general resolver entries per paired A/B row;
- preserved the four-cell Plane-A seam fallback, all 64 logical cells, miss
  counters, dirty rows, and existing two-row publication order.

It did not change selector 0, selector 1/2, or the directional Plane-B column
producer.

## Technique-by-technique symmetry

| Technique / work | Vertical current | Horizontal current | Status |
|---|---|---|---|
| Invariant source/map pointer hoist | A row source once per row; B table base once per row and descriptor cached by 16-column group | A source/descriptor once per four-row segment; B selected record once per column | Already present, different grouping |
| Staging row/column base | A/B physical row base once per row | Buffer base once, but fixed column byte offset and row destination arithmetic repeat per cell | Partially present |
| Residency-LUT base | Active LUT once per general pan row | Re-selected inside every general resolver call | Missing |
| Ring-front location | Once per A row; seam block guarded | Selector 0 has one fixed entering column and no within-column seam; fixed source reference is selected once | Not applicable to the same traversal; protected where applicable |
| Generated/native visual record | A native metatile record once per safe four-cell block; B generated record cached by group | A native metatile record once per four-row segment; B generated record once per column | Already present |
| General resolver elimination | General pan B: 64 inline; pan A: 60 inline plus four seam calls | A: up to 64 `fg_cache_resolve` calls; B: 32 `fg_boundary_resolve_b` calls | Missing |
| Repeated selector decoding | Row/selector state established outside cell loops | Entering column/subcolumn and direction gates established outside cell loops | Already present |
| Tile/code translation | Inline LUT lookup per cell after row-level base hoist | Helper-mediated LUT lookup per cell | Partially present |
| Address calculation | Physical row/staging base hoisted; per-column word offset remains | Buffer base hoisted, but physical-row and fixed-column destination terms are rebuilt per cell | Partially present / direction-dependent |
| Physical ring position | One physical row selected once | Physical row changes down the column; current code recalculates it per cell | Present in different form; progression could be cheaper but is not invariant |
| Attribute calculation | A once per safe four-cell block; B once per descriptor group | A once per four-row segment; B once per selected record | Already present |
| Residency lookup setup | Once per row, then inline per-cell lookup | Full helper prologue, scene decision, LUT-address helper, and epilogue per cell | Missing |
| Multi-cell grouping | 16 four-column blocks; one seam block ungrouped | A: 16 four-row segments; B: one 32-row resident loop | Already present in different form |
| Paired-row / paired-column processing | Pan controller publishes A then B for each crossed row | A and B crossing triggers are separate arcade-owned paths | Not applicable |
| Block-of-four processing | A uses four-column blocks; B caches 16-column groups | A uses four-row blocks; B uses one selected 16-column descriptor record | Already present in different form |
| Loop/control overhead | A 16 block calls plus inner loops; B one 64-cell loop | A nested 16x4 loops; B one 32-cell loop | Present in different form; horizontal helper calls add avoidable control flow |
| Seam fallback | Exactly one possible A four-cell block resolves per cell | Fixed-column traversal does not group across columns; no crossing block exists | Not applicable, and must remain protected in any future cross-column work |
| Miss/fallback handling | Inline zero/range/unresident behavior and A/B miss counters; A seam uses authoritative resolver | General helpers preserve scene selection, static LUT behavior, zero/range/unresident behavior, and counters | Already present semantically, slower form |
| Dirty bookkeeping | One A and one B row bit per crossed row | One A or B column bit per published column | Already present |
| Plane-A visual traversal | 64 columns; 60 inline plus four seam resolver cells | 64 rows; helper lookup per valid cell, 32 physical writes | Partially symmetric |
| Plane-B visual traversal | 64 columns, descriptor group cache, inline lookup | 32 resident rows, one generated record, helper lookup per cell | Partially symmetric |
| Collision traversal | General pan visual row does not write collision; selector 1/2 writes all 64 cells | Selector 0 writes all 64 cells; Plane B none | Different semantic ownership; must be preserved |

## Direct Build-0434 analogue test

Before Build 0434, the general Plane-A row path recomputed source-row,
staging-row, active-LUT, and ring-front context in each of 16 four-cell blocks,
and the paired A/B row entered general residency helpers 128 times. Build 0434
moved the invariant context to the row entry and made the hot residency lookup
an inline load while retaining the exact miss behavior.

Horizontal already performs the **descriptor/native-record/attribute** half of
that transformation: once per four-row segment on Plane A and once per selected
column record on Plane B. It does not perform the **residency context/general
helper** half:

- `tilemap_hooks.s`, selector-0 inner loop: `bsr fg_cache_resolve` at the
  current source line 425, within the 16x4 traversal;
- `tilemap_hooks.s`, directional Plane-B row loop: `MAP_GET_NAME_B` at the
  current source line 1663, expanding to `bsr fg_boundary_resolve_b`, within
  the 32-row traversal;
- `fg_tile_cache.s`, lines 181–236: each call saves/restores registers, tests
  scene identity, range-checks the code, calls `.Lactive_lut_address` on the
  gameplay path, loads the LUT word, and applies miss accounting.

The exact result is partial symmetry. Builds 0423/0424 did substantial
horizontal work, but neither incorporated the later Build-0434 active-LUT and
general-resolver elimination.

## Static repetition and cost

| Path | Current repeated work per crossing | Count | Locality / constraints |
|---|---|---:|---|
| Plane A selector 0 | `fg_cache_resolve` scene/LUT setup and call frame | up to 64 | Local to the visual residency step, but collision writes for all 64 rows and 32-row visual projection must remain |
| Plane B directional column | `fg_boundary_resolve_b` scene/LUT setup and call frame | 32 | Local visual-only loop; preserve scene/static-LUT behavior and B miss counter |
| Plane A selector 0 | physical-row test/address plus fixed-column contribution | 64 tests, 32 writes | Row varies; only fixed-column/base terms can safely be hoisted |
| Plane B directional column | physical-row address plus fixed-column contribution | 32 writes | Row varies and wraps; a strided pointer form must prove identical wrap destinations |

For each nonzero gameplay-resident code, the nested outer resolver call and
its `.Lactive_lut_address` call alone account for approximately 68 standard
68000 control-transfer cycles (`BSR`/`RTS` pairs), before register `MOVEM`,
scene/range branches, memory loads, or loop work. That control-transfer floor
is about 4,352 cycles for 64 Plane-A calls and 2,176 cycles for 32 Plane-B
calls. These are static floors, not predicted net savings and not a conversion
to rope frames. Zero-code and non-gameplay/static paths take different
branches.

Risk is bounded but not zero. The Build-0434 inline macro is valid because its
general pan entry is a proven scene-1 semantic boundary. A horizontal change
must either prove the same scene contract for each column entry or select the
active versus static LUT once per column. It must preserve exact zero,
out-of-range, unresident, and miss-counter behavior. Plane A must additionally
preserve all 64 collision writes, the 32-row physical projection, N/N+32
coherence, and transition-step ordering.

## Rope-route relevance

**YES.** Existing evidence shows the deterministic rope route executed both
horizontal parent paths materially:

- Build 0423 measured 66 matching Plane-B directional-column samples on the
  rope route and reduced the route by 21 frames versus Build 0422.
- Build 0424 measured 196 matching Plane-A selector-0 samples on the rope route
  and reduced the route by 41 frames versus Build 0423.

That does not prove a future helper-inline change will save a whole rope frame,
but it does prove the route executes the candidate loops. By contrast, the
selector-1/2 vertical hook optimized in Build 0425 was not naturally executed
by that route, and the Build-0434 general vertical change left the global rope
result unchanged at 803 frames.

## Smallest safe future implementation boundary

The highest-value bounded candidate is the residency-resolution step inside
`genesistan_hook_tilemap_plane_a_selector0_native`, followed independently by
the same step in `.Ldirectional_publish_column_native`.

For each function, a future implementation should:

1. select the correct active or static residency-LUT context once at column
   entry;
2. replace only the per-cell general helper call with an inline lookup that is
   semantically identical to `fg_boundary_resolve_a` or
   `fg_boundary_resolve_b`;
3. preserve exact miss counters and blank results;
4. retain all existing descriptor/native-record grouping;
5. retain Plane-A's 64 collision writes, 64 logical resolutions, and 32
   resident staging writes;
6. retain Plane-B's 32 resident-row traversal;
7. retain the existing column dirty bits and 32-word gathered DMA publishers.

No future proposal may group across the live 64-column ring front. This
particular fixed-column candidate does not require such grouping, but static
equivalence must still cover every scene/LUT mode, all tile codes, all 64
logical rows, all visible-top placements and wraps, Plane-A collision words,
staging destinations, miss deltas, and dirty-column publication. Targeted
entry/return timing and the existing deterministic rope regression check would
be appropriate only in that later implementation task.

## Recommendation

Keep Build 0438 unchanged. Record the horizontal residency-context/helper
elimination as a later bounded background optimization, beginning with Plane A
selector 0 because it repeats the general helper up to 64 times on a
rope-exercised path. Treat Plane B as a separate, simpler 32-call follow-up.
Do not reopen descriptor grouping, reduce the 64-cell logical domain, merge
visual and collision ownership, or weaken the ring-front seam rule.

Production source modified: **NO**
ROM built: **NO**
MAME run: **NO**
New trace created: **NO**
Rope benchmark run: **NO**
Build number consumed: **NO**
Build counter changed: **NO**
HUD/framing work resumed: **NO**
Phase D: **NO**
Phase E: **NO**
