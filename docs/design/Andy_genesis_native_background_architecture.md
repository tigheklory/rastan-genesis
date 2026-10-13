# Genesis-Native Background Architecture (PC080SN-derived Layer A/B + collision + scroll)

**Author:** Andy · **Date:** 2026-10-10 · **Type:** DESIGN / REVIEW ONLY. No production source,
no ROM, no build number, Cody's working tree untouched. Builds on
`docs/design/Andy_build0414_scroll_enemy_performance_review.md`.

**Goal:** the background equivalent of the native sprite system — *arcade map/scroll semantics
preserved*, data and runtime expressed natively for the Genesis VDP. Not a faster PC080SN emulation.

Principle (same as sprites): **Python preprocesses invariant map/graphics knowledge; the Genesis
68000 handles only dynamic camera/scroll/gameplay state and the final incremental plane placement.**

---

## 1. Current background data model (traced, not inferred)

| State | Where | Class |
|---|---|---|
| arcade strip descriptor tables | `PC080SN_DESC_REBUILD_SRC/PTR/WORD` (`A5+0x1000/0x1040/0x1080`) | ORIGINAL ARCADE FORMAT (live, scroll-advanced by `map_advance_source_ptrs` arcade `0x0558C6`) |
| selector / strip index / group | `A5+0x10A8 / 0x10CA / 0x10CC / 0x10F4` | ARCADE RUNTIME STATE |
| tile → VRAM slot | `genesistan_pc080sn_tile_vram_lut` (`pc080sn_tile_vram_lut.bin`) | TRANSLATION TABLE (Genesis-native, already offline) |
| per-scene resident tile set | `pc080sn_scene_preload_{title,gameplay,gameplay_cave,endround}.bin` | GENESIS-NATIVE DATA (context-resident) |
| name word (pattern+pal+pri+flip) | built per cell at runtime by `resolve_plane_a_cell` (`tilemap_hooks.s:606`) via descriptor walk + tile LUT + `.Lplane_a_native_attr_from_word` | RUNTIME-RESOLVED (the cost) |
| collision word | built per cell at runtime by `resolve_plane_a_collision_cell` (`:729`) | RUNTIME-RESOLVED (the cost) |
| collision map | `collision_map_64x64_words_base` @ `0x00FF1E00` (64×64 words = 8 KB) | GENESIS RUNTIME STATE (arcade physics reads it) |
| Plane A/B staged image | `staged_fg_buffer` / `staged_bg_buffer` (2048 words each = full 64×32 plane) | GENESIS RUNTIME STATE |
| dirty | `fg_row_dirty` / `bg_row_dirty` (32-bit per-row masks) | GENESIS RUNTIME STATE |
| scroll position | `A5+0x10B0` (FG Y), strip index/group, scroll-Y FG offset | SCROLL-DYNAMIC |

**Already native:** tile→VRAM translation (LUT), per-scene resident tile sets, the staged full-plane
image, the central publisher. **Still runtime arcade/PC080SN-derived:** per-cell name-word
resolution (`resolve_plane_a_cell`) and per-cell collision resolution
(`resolve_plane_a_collision_cell`) — each walks the live descriptor pointer table, does
strip-group/index arithmetic, range-checks, a second-word dereference, uniform/non-uniform
classification, and attr packing.

**Primary structural inefficiency:** `genesistan_hook_tilemap_plane_a_selector12_native` rebuilds
all 16 segments × 4 cells = **64 columns per horizontal strip event** (only ~4 newly exposed), and
**each cell is resolved twice** (collision + name), each a full descriptor walk. ~153,890 cyc.

---

## 2. Proposed native map record

The arcade map is a grid of logical cells `(row, col)`; each resolves today to a finalized Genesis
name word (VRAM slot | palette line | priority | Hflip | Vflip) and a collision word. **All of those
are build-time/context invariant** except a small set of gameplay-dynamic cells (§4), because the
tile→VRAM slot is fixed once a context's tile set is scene-resident.

**Record (two parallel packed tables per context, not inline):**
- `pc080sn_native_name[context][row][col]` : **u16** finalized Genesis name word (fully offline).
- `pc080sn_native_collision[context][row][col]` : **u16** collision word (fully offline).
- `pc080sn_native_override[context]` : sparse `{cell → override_class}` for dynamic cells (§4).

**Parallel, not `{name, collision, class}` inline, because** the two consumers have different spans
and destinations: name words feed the visual plane ring (~40 visible columns of the 64-wide Genesis
name table); collision words feed the 64-wide collision ring the arcade physics reads. Parallel
tables let each path touch only its own data with its own span and keep each entering column's words
**contiguous** for a single strided DMA (§15). Inline would force reading collision bytes on a
visual-only update.

**Bytes/record:** 2 (name) + 2 (collision) = 4 B/cell, static; override is sparse.

**Static fields:** pattern index, palette line, priority, H/V flip, collision class — all folded into
the two u16s offline. **Dynamic fields (left to runtime):** camera position, plane ring index,
collision ring index, and per-cell gameplay override selection (§4). **Canonical tile identity
reused: YES** — the name word is built from the existing `genesistan_pc080sn_tile_vram_lut`; no second
tile-identity namespace is created.

---

## 3. Static vs dynamic classification

| Property | Class |
|---|---|
| tile identity, palette, priority, H/V flip | BUILD-TIME INVARIANT |
| collision class (non-destructible) | BUILD-TIME INVARIANT |
| resident VRAM slot (pattern bits of the name word) | LEVEL/CONTEXT INVARIANT (scene-resident) |
| map coordinates / entering strip | SCROLL-DYNAMIC |
| plane destination / ring index | SCROLL-DYNAMIC |
| destructible (cave block) state | GAMEPLAY-DYNAMIC |
| animated BG tile phase (if any) | GAMEPLAY-DYNAMIC (investigate — likely palette-cycle, not tile rewrite) |
| mid-round background bank change (R3/R5/R6) | LEVEL/CONTEXT INVARIANT (a context switch → load the other context's map, not per-cell) |

Only the two GAMEPLAY-DYNAMIC rows leave Python; everything else is finalized offline.

---

## 4. Dynamic tile inventory (full static coverage is the goal)

| Class | Writer | States | Finite variant set? | Runtime need |
|---|---|---|---|---|
| **Destroyable cave block** (`usage:cave_block:bank0x3C`) | arcade block-destroy code (collision-mark path `collision_map_surface_mark_5a2ee`) | present / destroyed (2) | **YES** (2-state) | override entry: swap name+collision word on destroy |
| **Animated BG tile** (water/flame, if present) | investigate — likely palette-cycle (CRAM) not tilemap rewrite | few phases | YES if real | if palette-cycle: **no map change** (handled by palette path) |
| **Context/bank mid-round change** (R3/R5/R6) | scene loader | per-context | N/A | load the other context map; not per-cell |

**Conclusion:** the only genuine per-cell map rewrite is the destroyable block, which is a finite
2-state override. **One dynamic exception must NOT force all cells through the old generic resolver**
— it is a sparse override list indexed by cell. Requires generic fallback: **NO** (see §12).

---

## 5. Storage design — recommended: **Option E (static context arrays + sparse override)**

Compared: A full expanded array (simple, O(1), moderate ROM), C shared cell dictionary + per-segment
indexes (smallest ROM via dedup, one extra indirection), E hybrid static arrays + dynamic override
(A for the common case + a tiny override table). **Choose E, with C's dictionary applied by Python
only if ROM pressure demands it.**

- Why: O(1) direct indexed lookup (fastest 68000 path, matches the sprite system's finalized-vi
  model), the dynamic case is a bounded side table, and the project is willing to spend ROM to save
  68000 cycles.
- Approx ROM: per context, `map_cols × map_rows × 4 B`. R1/P1 logical map (≈ a few hundred columns ×
  ~32 rows) → order ~tens of KB per context; Python content-dedups identical columns (many repeat)
  if the cartridge approaches its limit. Collision is shared across contexts where identical.
- Approx RAM: none new beyond the existing staged plane + the existing 64×64 collision ring; the
  native tables live in ROM.
- Lookup complexity: **O(1)** indexed load (`name[row][col]`, `collision[row][col]`).

---

## 6. Horizontal ring-buffer runtime

A one-tile horizontal crossing (the arcade already advances the source pointer via
`map_advance_source_ptrs`): compute the newly-entering logical column `col_new = camera_col (± 1)`;
index the native map column; write the entering Genesis plane column (ring-wrapped modulo 64 name
columns) and the entering collision-ring column (modulo 64). Mirror of the already-incremental
vertical pan, which loops *entering rows*.

- **Right scroll:** entering column at the right edge of the visible window; `plane_col = col_new &
  63`; collision_col = `col_new & 63`.
- **Left scroll:** entering column at the left edge; same ring math with `col_new = camera_col - 1`.
- **Cells processed:** 1 entering column = ~28 visible rows (visual) + 64 rows (collision). (Not 64
  columns.)
- **Layer A writes:** ~28 name words (visible rows) into `staged_fg_buffer` column. **Layer B
  writes:** the paired Plane-B column into `staged_bg_buffer`. **Collision writes:** 64 collision
  words into the collision ring column.
- **Wrap logic:** name/collision column index = `col & 63` (mask, no modulo/division — §E).
- **Multiple crossings per gameplay update:** loop entering columns (like the vertical pan loops
  rows), bounded by the max per-frame scroll delta (a few tiles); still O(delta), not O(width).

---

## 7. Vertical integration

The existing `genesistan_plane_a_pan_publish_entering_rows_up/down` is already incremental and is the
reference. **Existing incremental path reusable: YES. Native map accessor shared: YES** — define one
`native_map_cell(context, row, col) → {name_word, collision_word}` (two indexed loads) used by: the
horizontal entering-column path, the vertical entering-row path, initial population, and any rebuild.
Required changes: replace both pan publishers' per-cell `resolve_plane_a_cell` call with the native
accessor; no second tile-interpretation system.

---

## 8. Collision side-channel contract (critical)

`collision_map_64x64_words_base` (`0x00FF1E00`, **64×64 words**) is read by `collision_map_lookup_53a2e`
from many gameplay sites (decompiler: 3468/3480/3588/4773/5918/6210/7205…) at arbitrary actor world
positions, and written by `collision_map_surface_mark_5a2ee` / `_postprocess_5a29c`.

- **Required valid span:** the full resident **64-column** logical ring (vertical 64 too) — arcade
  physics queries actors that may be near/just off the visible ~40-column window.
- **Can collision update be incremental: YES** — the collision map is itself a 64-wide ring; a
  one-tile crossing adds exactly one new collision column (64 rows). It does **not** need a full
  rebuild, just a wider ring than the visual.
- **Wider than visual span → maintain independently:** the visual plane updates its ~40-visible
  entering column; the collision ring updates its 64-wide entering column. Both incremental, both fed
  by the native accessor, different spans. **Do not force the visual plane to full-width because
  collision is wider** — that is exactly today's mistake.

---

## 9. Fused name + collision

The native accessor yields both words from **two parallel O(1) loads** (name table + collision table)
— replacing today's two independent descriptor walks (`resolve_plane_a_cell` +
`resolve_plane_a_collision_cell`). Collision stays a **parallel packed table**, not inline (§2
rationale: different spans/destinations, DMA contiguity). This alone is the Class-G fusion from the
0414 review, now expressed as "one indexed lookup pair."

---

## 10. Python compiler

**Tool:** extend `tools/translation/precompute_pc080sn_tile_lut.py` (it already discovers descriptor
tables, collects strip tiles, builds the tile→VRAM LUT and per-scene preloads, and has a
source-scene map). Add a native-map pass.

- **Inputs:** `build/regions/maincpu.bin` (descriptor/strip/segment tables), `pc080sn_tile_vram_lut`,
  `specs/palette_decisions.json` (palette lines), the arcade collision surface tables, per-context
  scope (`gameplay.r01.p01`, …).
- **Outputs:** `pc080sn_native_name_{context}.bin`, `pc080sn_native_collision_{context}.bin`,
  `pc080sn_native_override_{context}.bin` (dynamic metadata), `pc080sn_native_map.report.txt`
  (coverage matrix + hashes: maincpu/descriptor sha, tile-LUT sha, palette-decisions sha).
- Reuses the finalized-identity discipline from the sprite system; no second tile namespace.

---

## 11. Generated verification

A map verifier analogous to `verify_pc090oj_frame_table.py`: for **every statically resolvable cell**,
compare the generated `{name word, collision word}` against the **current** runtime resolvers
(`resolve_plane_a_cell` + `resolve_plane_a_collision_cell`) re-implemented independently in Python —
bit-exact on tile index, palette, priority, H/V flip, and collision word. Unresolved cells classified
explicitly (UNRESOLVED); **no silent fallback**. Plus an incremental-vs-bulk consistency check: after
N simulated crossings the ring equals a full bulk rebuild.

---

## 12. Runtime fallback policy

**Preferred final:** ordinary static cells 100% native (direct lookup); finite dynamic (cave block)
via the 2-state override; genuinely exceptional via a bounded dedicated override. **No generic
descriptor interpreter in the live scroll path.** During migration (BG-A/BG-B) keep the current
resolver with a **dev-only counter** (`native_map_fallback_count`); removal criterion = coverage
report shows 100% static coverage + all dynamic classes represented, and the counter reads 0 across
the human regression suite.

---

## 13. Initial plane population

A **bulk init** path (scene entry, Layer A/B init, scene reset, large camera jump) populates the full
visible plane + full 64×64 collision ring from the native map — legitimately different from the
incremental path but using the **same native accessor** over a full span. Incremental optimization
must not break init; the verifier's bulk-vs-incremental check guards this.

---

## 14. Staging / dirty

Keep the current publication architecture (no VBlank-ownership change). Incremental updates write
**final Genesis name words directly** into `staged_fg_buffer`/`staged_bg_buffer` (already full-plane
images). Dirty: **per-column** (new) for horizontal + the existing **per-row** (`fg_row_dirty`/
`bg_row_dirty`) for vertical — a column/row mask is far cheaper than per-word. The current full
64×32-word staged buffers are larger than an incremental step needs but are kept for publisher
compatibility; the dirty masks bound what the publisher actually DMAs.

---

## 15. DMA interface

For an entering column: a Genesis plane column is 32 name words at stride 128 bytes (row-major name
table). Set VDP auto-increment (reg 0x0F) = 128 and DMA the column as **one contiguous 32-word run**
from a **contiguous source** — so arrange the native name table (or a small gather scratch) so the
entering column's words are contiguous. **DMA runs per horizontal step: 1 per plane** (Plane A, Plane
B), 32 words each (fewer for the visible ~28 rows). This keeps CPU preparation minimal (the ~153K was
CPU prep, not DMA) — the native lookup writes straight into the staged column, publisher DMAs it.

---

## 16. Cycle model

| Stage | Expected row/map cyc (one-tile crossing) |
|---|---|
| **Current** | ~153,890 |
| **BG-A** (incremental strip, keep double resolver): ~4 cols instead of 64 | ~15,000–25,000 |
| **BG-B** (fused collision/name resolver): one walk instead of two | ~10,000–15,000 |
| **BG-C** (generated native records, direct O(1) lookup, no descriptor walk): ~28 visual + 64 collision cells × (load+write) | ~2,000–5,000 |
| **Final** (BG-C + per-column dirty + contiguous column DMA) | **~2,000–5,000** |

Expected complete scroll IRQ: ~230,000 − ~150,000 ≈ **~80,000** < 128,009. **One-frame fit plausible:
YES.** The required ~102K recovery is met at BG-A alone (structural), with BG-B/BG-C providing
comfortable margin and removing the arcade interpreter.

---

## 17. Migration plan

| Phase | Work | Acceptance |
|---|---|---|
| **BG-A** | Incremental horizontal strip only (rebuild entering segment(s), keep current resolver); confirm collision span handled by the 64-ring entering column | mechanical: incremental-vs-bulk plane identical; perf: scroll IRQ < ~128K on a one-tile crossing; human: horizontal L/R scroll visually identical on real Genesis; rollback: revert to full-width producer |
| **BG-B** | Fuse collision+name into one descriptor walk | verifier: collision + name bit-identical to BG-A; perf: further drop; human: collision-while-scrolling correct |
| **BG-C** | Generate native map records (Python); runtime does direct O(1) lookup | map verifier 100% static coverage (bit-exact); perf: row/map ~2–5K; human: full scroll + cave block + dynamic tiles |
| **BG-D** | Retire the generic descriptor walk from the live scroll path (dev-only fallback counter must read 0) | counter 0 across regression suite; perf confirmed; human: long continuous scroll |
| **BG-E** | Unify vertical + horizontal (and init) on the single native accessor | one accessor only; vertical/horizontal/init all bit-identical; human: combined scroll + segment wrap + boundary |

Adjust order only if source evidence demands; each phase is independently verifiable and reversible.

---

## 18. Verifiers required

1. **Map-equivalence verifier** — generated name words vs current `resolve_plane_a_cell`, all static
   cells, bit-exact (tile/pal/pri/flip).
2. **Collision-equivalence verifier** — generated collision words vs `resolve_plane_a_collision_cell`,
   full 64×64, bit-exact.
3. **Incremental-vs-bulk consistency** — after N simulated crossings (both directions, with wrap and
   segment boundaries) the ring equals a bulk rebuild; plus a dev-only `native_map_fallback_count`.

## Human regression tests (real Genesis = authority)

Horizontal right/left scroll; vertical up/down; segment wrap; map boundary; cave block
destroy-while-scrolling; animated/dynamic tiles; collision while scrolling (land on surfaces,
walls); enemy + scrolling; rope/scroll interaction; Layer A + Layer B visual identity; palette;
priority; flips; initial map population (scene entry + large jump); long continuous scrolling.

---

## 19. Secondary — enemy scaling (short)

- **Owning-probe cache.** Key: `(family a4@0x38, anim a4@0x01)`. Lifetime: whole scene (invariant per
  key). Invalidation: none within a scene (clear on scene load). Generated data: a small table
  `path_owner[family][anim] ∈ {generic, universal, unresolved}` from the frame-table generator.
  Avoids the generic-probe miss then universal-probe retry. Expected: **~100–300 cyc/active actor**.
  Verifier: for every key, the cached owner matches which probe actually resolves it.
- **Per-actor variant-group-base hoist.** Key: the actor's base tile code range. Lifetime: one actor
  emit. Invalidation: per actor. Generated data: none new (reuse `pc090oj_variant_group_base`).
  Hoist the group-base lookup out of the per-piece loop where the actor's pieces share a code group.
  Expected: ~tens of cyc × pieces/actor. Verifier: emitted `vi` identical to per-piece resolution.

Expected value: each widens the static-camera enemy margin by roughly one enemy; secondary to scroll.

---

**Cody working tree modified: NO. Production source modified: NO. ROM built: NO. Build number
consumed: NO. Phase D: NO. Phase E: NO.**
