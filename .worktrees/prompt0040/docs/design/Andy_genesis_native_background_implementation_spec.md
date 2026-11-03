# Genesis-Native Background — Implementation Specification (for Cody)

**Author:** Andy · **Date:** 2026-10-10 · **Type:** DESIGN / STATIC ANALYSIS ONLY. No production
source, no ROM, no build number, Cody's tree untouched. Supersedes the ambiguous unit/column wording
in `docs/design/Andy_genesis_native_background_architecture.md` (that doc stays; this one is
authoritative on units, loops, DMA, dynamic coverage, and the BG-A/BG-C contract).

---

## 0. Unit model (RESOLVED from source — no ambiguity left)

| Unit | Width (px) | Genesis name cells | Notes |
|---|---|---|---|
| Arcade tile / Genesis 8×8 name cell / **logical cell** | 8 | 1 | one name-table word; these three coincide |
| **Segment** | 32 | **4** cells | `logical index = segment*4 + cell`, `cell = 0..3`, `segment = 0..15` |
| Full map dimension | 512 | **64** cells | 16 segments × 4; the Genesis plane is 64×32 |
| Visible window | 320×224 | ~**40** cols × ~**28** rows | staging residency gate `(row−visible_top)&0x3F < 32` |
| Camera tile step | 8 | 1 cell | strip_index (`A5+0x10CA`, &3) + strip_group (`A5+0x10CC`/`0x10F4`, &0xF): `pos = group*4 + index` |

**The 1-vs-4-vs-64 ambiguity — RESOLVED.** The two current horizontal/vertical producers are
*transposed*, proven from the index math:

- **`selector0_native`** (arcade `0x055968`, selector 0 = **horizontal**): fixes the **entering
  column** `0(%sp) = (group&0xF)*4 + (index&3)` and loops `d1 = segment*4 + cell = 0..63 = the ROW`.
  → publishes **ONE entering column × 64 rows** (comment: "publishes only the LEADING entering
  column"). This is already a single-column producer.
- **`selector12_native`** (arcade `0x055990`, selector 1/2 = **vertical-style row**): fixes the
  **row** `0(%sp)` and loops `d1 = 0..63 = the COLUMN`. → publishes **ONE row × 64 columns**.
- **`genesistan_plane_a_pan_publish_entering_rows_up/down`** (arcade `0x055704/0x055790`): the pure
  vertical pan, already incremental over entering rows.

So **the entering unit per crossing is 1 cell-wide strip spanning the full 64 map dimension**
(1 column×64 rows for horizontal; 1 row×64 cols for vertical). The earlier "~4 newly exposed
columns" was the **segment** granularity (4 cells); the earlier "64 columns rebuilt" was the **loop
span** (the full 64 map dimension of the orthogonal axis). **Both prior terminologies were describing
different axes of the same strip. Use only this model going forward.**

**Two inefficiencies, both proven:** (1) each producer resolves the **full 64** map dimension though
only the **visible** span (~28 rows / ~40 cols) needs the *visual* write (collision does need 64 —
§Collision); (2) **each cell is resolved twice** (`resolve_plane_a_collision_cell` + `resolve_plane_a_cell`).

**One residual quantity to MEASURE in Step 1 (do not guess):** how many 64-cell producer invocations
occur per representative heavy scroll event (which, combined with the ~153,890 figure, sets the real
per-cell cost and the BG-A/BG-C multipliers). Also confirm whether `selector12_native` and the
vertical pan path are redundant for pure vertical motion.

### Exact horizontal event
- **Right crossing:** camera moves +8 px (+1 tile); entering source = 1 column at
  `col = (group*4+index) & 63`; entering Plane A columns = **1**; entering Plane B columns = **1**;
  entering collision-ring columns = **1** (× 64 rows).
- **Left crossing:** camera −8 px; entering column `col = (group*4+index) & 63` (group/index already
  decremented by the arcade); Plane A/B/collision entering columns = **1** each.

---

## 1. BG-A exact loop contract

BG-A keeps the current resolvers but produces **only the entering strip** and resolves the **visible
span** for the visual plane (collision keeps the full ring). Pseudocode (horizontal, selector 0):

```
; RIGHT or LEFT scroll, one entering column
col      = (group*4 + index) & 63            ; entering logical column (arcade already advanced group/index)
vis_top  = ((-scroll_y_fg + 8) >> 3) & 63    ; existing formula (A5+0x10B0 / 0x10BExx)
; --- visual (Plane A + Plane B): visible rows only ---
row = vis_top
for n = 0 .. VISIBLE_ROWS-1 (=28):           ; NOT 0..63
    name_a = map_get_name_a(col, row)        ; accessor (§BG-A/BG-C)
    name_b = map_get_name_b(col, row)
    stage_fg[(row & 31)*64 + col] = name_a
    stage_bg[(row & 31)*64 + col] = name_b
    row = (row + 1) & 63
set fg_col_dirty bit `col&63`; set bg_col_dirty bit `col&63`
; --- collision: full ring height (physics reads off-visible) ---
for r = 0 .. 63:
    collision[r*64 + col] = map_get_collision(col, r)
```

- Initial index: `col` from arcade strip pos; `row = vis_top`.
- Termination: visual loop `n == VISIBLE_ROWS`; collision loop `r == 64`.
- Wrap mask: `& 63` (name ring), `& 31` for the staged-buffer row (64×32 image), `& 63` collision.
- Direction: right vs left differ only in which arcade strip pos is used (group/index already
  reflect direction); the loop body is identical.
- Source/dest stride: dest Plane column stride = 64 words (row-major staged image); collision stride
  = 64 words; source stride defined by the accessor.
- **Multi-crossing:** if the per-frame scroll delta crosses k tiles, loop the k entering columns
  (bounded; like the vertical pan loops entering rows). k is small (a few).

Vertical (selector 1/2 / pan): symmetric — fix the entering **row**, loop visible **columns** (~40)
for visual, full **64** for collision; dest row stride 1 word; set `fg_row_dirty`/`bg_row_dirty`.

---

## 2. Collision ring contract

`collision_map_64x64_words_base` @ `0x00FF1E00` (64×64 words). **Writers:** the strip producers
(via `resolve_plane_a_collision_cell`) and arcade `collision_map_surface_mark_5a2ee`. **Readers:**
`collision_map_lookup_53a2e` from many gameplay sites at arbitrary world positions.

- World→ring: `ring_col = (world_x >> 3) & 63`, `ring_row = (world_y >> 3) & 63`; word index
  `= ring_row*64 + ring_col` (×2 bytes). (Matches the producer's `row*64 + col` index.)
- **Entering collision span per horizontal crossing = exactly ONE column × 64 rows** (not 4, not 64
  columns). A 4-cell *segment* step still enters cell-by-cell; the camera tile step is 1 cell.
- Collision requires the **full 64-row height** of the entering column (physics queries any row),
  but only the **entering column(s)** horizontally — so collision is incremental over the 64-ring,
  maintained **independently** of the ~40-visible visual span. Do **not** widen the visual plane to
  64 because collision needs 64 rows; they are different axes/tables.

---

## 3. DMA source-layout contract — **Option A: per-plane gather buffer (chosen)**

A Genesis plane **column** is 32 words at **128-byte stride** in the row-major staged image — **not
contiguous**. A plane **row** is 64 contiguous words. So:

| Option | CPU setup | RAM | DMA cmds | Interaction | Verdict |
|---|---|---|---|---|---|
| A gather entering column into a contiguous scratch, DMA with dest-autoinc=128 | low (write-through during resolve) | 2×64 words scratch | 1/plane | clean; staged image still authoritative for rows | **CHOSEN (columns)** |
| B column-major second staging buffer | med | +4 KB/plane | 1/plane | duplicates state, sync risk | rejected |
| C CPU/publisher word-by-word column write | high | 0 | 0 DMA (PIO) | slow for 32 words | fallback only |
| D row DMA (already contiguous) | low | 0 | 1/plane | **use as-is for ROW (vertical) updates** | **CHOSEN (rows)** |

**Chosen:** **columns → Option A gather** (the resolve loop writes each entering column's words into
a small contiguous per-plane scratch *as well as* the staged image; the column DMA sources the
scratch with VDP **destination** autoincrement = 128). **Rows → Option D** (the staged row is already
contiguous; DMA it directly, dest-autoinc = 2).

**SOURCE increment vs DESTINATION autoincrement:** the gather scratch is written **contiguously**
(source autoinc = 2 words); the VDP **destination** autoincrement is set to **128** so consecutive
source words land in consecutive plane *rows* (a vertical column). A row-major staged column is NOT a
contiguous source — never DMA it as one run; that is why the gather exists.

Gather buffer: `bg_col_gather` / `fg_col_gather`, **64 words each** (full ring height; collision uses
the ring directly, no gather), session-lifetime BSS, owned by the background producer, written during
the column resolve loop; only the visible rows carry live name words, the rest are the existing
resident ring words (partial visible-height columns: gather the full 64 so the DMA always writes a
complete column; non-visible rows re-emit their current resident name, a no-op visually).

---

## 4. Dirty-state contract

- **Columns (new):** `fg_col_dirty` / `bg_col_dirty` = **64-bit** masks (two longs each, or a
  `.long`×2). MC68000-practical: `bset col&31` into the low/high long selected by `col>>5`.
- **Rows (existing):** `fg_row_dirty` / `bg_row_dirty` 32-bit (32 plane rows).
- Set by: the producer (per entering column/row). Cleared by: the publisher after DMA (as today for
  rows). Publisher enumerates set bits → one column/row DMA each.
- Multiple entering columns in one tick: each sets its bit; publisher coalesces adjacent set bits
  into one multi-column DMA run where contiguous (optional optimization).
- **Row + column dirty coexisting in one staged frame:** allowed (combined H+V motion). Overlap: a
  cell covered by both a dirty row and a dirty column is written identically by both (idempotent —
  same native word); publisher may DMA the row then the column (or union) without double-visual.
- Does **not** change IRQ/mainline ownership.

---

## 5. Plane A vs Plane B data model

**They are NOT the same table.** Plane B (`.Lplane_b_publish_logical_row_native`,
`.Lplane_b_stage_gameplay_producer_cell_native`) resolves via `fg_boundary_resolve_b` + the gameplay
producer-cell path and the FG boundary packages (`fg_tile_cache.s` AB/BC transition packages) — a
distinct background source from Plane A's strip descriptors. **Specify separate native tables:**
`pc080sn_native_plane_a_name[context]` and `pc080sn_native_plane_b_name[context]`. Collision is a
Plane-A-side channel only → one `pc080sn_native_collision[context]`.

---

## 6. Dynamic-tile coverage

Static sweep of retained writers to map descriptors / tilemap source / collision cells / scene bank:

| Class | Writer | Classification |
|---|---|---|
| Destroyable cave block | `collision_map_surface_mark_5a2ee` (+ its visual tail) | **CONFIRMED FINITE DYNAMIC** (2-state) |
| Background animated tile | none found by name in the decompiler | likely **PALETTE-ONLY** (CRAM cycle, no map write) — must be **confirmed by the BG-C coverage report** |
| Mid-round bank change (R3/R5/R6) | scene loader | **CONTEXT SWITCH** (load other context map; not per-cell) |
| Other tilemap writers | — | **UNKNOWN until the generator's per-cell equivalence pass runs** |

**Generic fallback required:** **NO — conditional.** The final no-fallback claim is valid only once
the BG-C coverage report proves `UNKNOWN = 0` for reachable gameplay (every cell either matches the
generated static word or is an enumerated dynamic override). Until then, keep the dev-only
`native_map_fallback_count` (§11). Do not claim no-fallback before the coverage report is green.

---

## 7. Cave-block override contract

- **Static default record:** the generated `name_a` / `collision` word for the intact block cell.
- **Destroyed record:** a second generated `{name_a, collision}` for the destroyed appearance
  (likely blank/background) — a finite 2-entry variant per block cell.
- **State source:** the arcade block-state (the same flag `collision_map_surface_mark_5a2ee`
  consumes). **Cell key:** `(context, ring_row, ring_col)` of each block cell.
- **Bounded lookup (no per-cell linear search):** a per-context **override bitset** over logical
  cells (1 bit/cell = 64×map_rows/8 bytes); only when the bit is set does the producer consult the
  small override table (hashed or directly indexed by cell) for the live state → pick default vs
  destroyed word. Ordinary cells test one bit and skip. Visual word changes and collision word
  change **together** on destroy. Works identically for incremental scroll and bulk init (both call
  the accessor, which applies the override).

---

## 8. Native map index formula

Layout each context's tables **column-major** (so an entering column is contiguous for the gather)
or row-major (so an entering row is contiguous) — **pick column-major for Plane A/B name tables**
(horizontal is the costly axis) and keep collision row-major (matches the arcade ring index).

```
plane_a_name:  off = ctx_base_a + ((col * MAP_ROWS) + row) * 2      ; column-major
plane_b_name:  off = ctx_base_b + ((col * MAP_ROWS) + row) * 2
collision:     off = ctx_base_c + ((row * 64)       + col) * 2      ; row-major (arcade ring)
```

Runtime avoids multiply: precompute per-context **base pointers** (`ctx_base_*` loaded once per
scene) and, for the column loop, a single `adda.l #MAP_ROWS*2, %aN` step per row (no multiply in the
inner loop; the column base `col*MAP_ROWS*2` computed once per entering column via one `mulu` or a
per-column pointer table). Collision inner step: `adda.w #128, %aN` per row.

**Cycles for one ordinary static lookup:** `move.w (ptr)+, %dN` ≈ **~8–12 cyc** (vs the current
~200–300 cyc descriptor-walk resolve). The override-bitset test adds ~1 `btst` (~8 cyc) per cell.

---

## 9. Generated files (Python)

| File | Element | Dims | Order | Align | Link |
|---|---|---|---|---|---|
| `pc080sn_native_plane_a_<ctx>.bin` | u16 name word | MAP_COLS×MAP_ROWS | big-endian, **column-major** | 2 | incbin in a new `background_assets.s` |
| `pc080sn_native_plane_b_<ctx>.bin` | u16 name word | MAP_COLS×MAP_ROWS | big-endian, column-major | 2 | incbin |
| `pc080sn_native_collision_<ctx>.bin` | u16 collision word | 64×MAP_ROWS | big-endian, **row-major** | 2 | incbin |
| `pc080sn_native_override_<ctx>.bin` | bitset + {cell→{default,destroyed}} | sparse | — | 2 | incbin |
| `pc080sn_native_map.report.txt` | coverage matrix + hashes | — | — | — | build log |

Metadata: per-context `MAP_COLS`, `MAP_ROWS`, `ctx_base_*`, and the input hashes (maincpu/descriptor
sha, `pc080sn_tile_vram_lut` sha, `specs/palette_decisions.json` sha). Context ordering = the project
context registry order (`gameplay.r01.p01` first). Generator = extend
`tools/translation/precompute_pc080sn_tile_lut.py`.

---

## 10. Verifier golden reference (survives resolver retirement)

During migration: compare generated output vs a **Python reimplementation** of the current
descriptor semantics (`resolve_plane_a_cell` / `_collision_cell`), bit-exact. **After retirement:**
the Python reference implementation is **kept in the repo as the golden model** (not the ROM), so
verification never becomes generated-code-verifying-itself. Specify: reference inputs = `maincpu.bin`
descriptor/strip tables + tile LUT + palette decisions; expected outputs = the two name words +
collision word per cell; coverage matrix = per-context {static-resolved, dynamic-override, UNKNOWN};
hash deps = all input shas recorded; failure = build abort on any mismatch or any UNKNOWN in
reachable gameplay.

---

## 11. BG-A/BG-C accessor stability

Define a cheap accessor used by BG-A and re-pointed by BG-C **without touching scroll/ring/dirty/DMA
code**. Form: an **assembly macro or private leaf routine** returning the word in a register (NOT a
general C-style call):

```
; BG-A/B: macro expands to the current resolver
;   map_get_name_a(col,row) -> bsr resolve_plane_a_cell        (keep today's semantics)
; BG-C: macro expands to the O(1) ROM lookup
;   map_get_name_a(col,row) -> move.w (a_ptr + col*MAP_ROWS*2 + row*2), %d0  (+ override btst)
```

Keep it a leaf (no save/restore beyond the resolver's own) so the 68000 cost in BG-C is ~8–12 cyc.
A dev-only `native_map_fallback_count` increments whenever BG-C's accessor cannot resolve and must
defer to the legacy resolver; removal of the legacy path is gated on this reading 0.

---

## 12. Expected work counts (one normal horizontal crossing, resolved units)

Per entering column (×64 ring rows, visible ~28). "Invocations/event" = the Step-1 measured
multiplier M (unknown until instrumented; the ~153,890 figure implies M×(per-invocation cost)).

| | Plane A cells resolved | Plane B cells resolved | collision cells | descriptor walks | name writes | collision writes |
|---|---|---|---|---|---|---|
| **CURRENT** (per invocation) | 64 | 64 | 64 | **128** (2×/cell) | ~40 staged of 64 | 64 |
| **BG-A** | **28** (visible) | 28 | 64 | 2×/cell still | 28 | 64 |
| **BG-B** (fused) | 28 | 28 | 64 | **1×/cell** | 28 | 64 |
| **BG-C** (native O(1)) | 28 (lookup) | 28 | 64 | **0** | 28 | 64 |

BG-A cuts resolved visual cells 64→28 and drops the non-entering strips; BG-B halves descriptor
walks; BG-C removes the descriptor walk entirely (lookup replaces resolve).

---

## 13. Updated cycle model (best / conservative; Step-1 instrumentation confirms M)

Per-cell: current resolve ≈ 200–300 cyc; BG-C lookup ≈ 10–20 cyc (incl. override btst + write).
Per entering column: visual 28×2 planes + collision 64.

| | Best | Conservative |
|---|---|---|
| **CURRENT** row/map | — | ~153,890 (measured) |
| **BG-A** | resolve 28+28+64 cells × ~250 × M vs 64+64+64: ~**0.55× current** → ~**70–85K** | ~95K |
| **BG-B** | fuse → ~**0.4× current** → ~**45–60K** | ~75K |
| **BG-C** | lookups: (56 visual×~15 + 64 collision×~250 for collision which still resolves unless also generated) → **collision MUST be generated too**: 56×15 + 64×15 ≈ ~2K/column × M | ~8–15K |

**Key:** BG-C must generate the **collision** table too (not just visual), else the 64 collision
resolves per column dominate. With both generated: BG-C row/map ≈ **~8–15K** (comfortable).
Expected complete scroll IRQ: ~230K − (153.89K − ~12K) ≈ **~88K**. **One-frame margin: ~40K below
128,009 — comfortable (not borderline).** BG-A alone (~70–95K row/map → scroll IRQ ~145–170K) may NOT
yet clear 128,009 under worst M; **BG-B is likely required for the hardware pass, BG-C for margin.**
Confirm with Step-1 M measurement before promising BG-A alone clears hardware.

---

## 14. Cody implementation order

| Step | Work | Files/routines | Invariant preserved | Mechanical test | Perf test | Human test |
|---|---|---|---|---|---|---|
| **1** | Instrumentation: count producer invocations + cells resolved + collision cells per scroll event; confirm selector12-vs-pan redundancy | `frame_timing_trace.lua` (Cody-owned; coordinate) | none (read-only) | counts stable run-to-run | establishes M + per-cell cost | — |
| **2** | Introduce `map_get_name_a/b` + `map_get_collision` accessor macros wrapping current resolvers (no behavior change) | `tilemap_hooks.s` | byte-identical output | diff staged plane vs pre-change = 0 | neutral | scroll identical |
| **3** | BG-A: visible-span visual loop + entering-strip-only (both selectors + pan), collision full-ring entering column | `tilemap_hooks.s` producers | plane+collision bit-identical to bulk | incremental==bulk verifier | scroll IRQ drop | real-Genesis L/R + U/D scroll identical |
| **4** | Column dirty mask + gather buffer + column DMA; publisher enumerates col dirty | `tilemap_hooks.s`, `dma.s`, `vdp_comm.s` publisher | publication identical | dirty→DMA coverage test | DMA cost neutral/down | no missing/stale columns |
| **5** | Measure (real Genesis + trace) | — | — | — | scroll IRQ vs 128,009 | Tighe scroll pass? |
| **6** | BG-B: fuse collision+name into one descriptor walk behind the accessor | `tilemap_hooks.s` | collision+name bit-identical | fused==unfused verifier | further drop | collision-while-scrolling correct |
| **7** | BG-C: Python native tables (Plane A/B/collision/override) + generator + golden verifier; accessor → O(1) lookup; dev fallback counter | `precompute_pc080sn_tile_lut.py`, new `background_assets.s`, `tilemap_hooks.s`, new verifier | generated==golden bit-exact; UNKNOWN=0 | map/collision equivalence + coverage report | row/map ~8–15K | cave block + dynamic + long scroll |
| **8** | BG-D/BG-E: retire the live descriptor walk (counter=0), unify vertical/horizontal/init on the accessor | `tilemap_hooks.s` | fallback counter 0 across suite | no descriptor walk in scroll path | margin confirmed | full regression suite |

Human regression suite (Step 7–8, real Genesis = authority): horizontal L/R, vertical U/D, segment
wrap, map boundary, cave-block destroy-while-scrolling, dynamic/animated tiles, collision while
scrolling, enemy+scroll, rope/scroll, Layer A/B identity, palette, priority, flips, initial
population (entry + large jump), long continuous scroll.

---

**PRODUCTION MODIFIED: NO. ROM BUILT: NO. BUILD NUMBER CONSUMED: NO. CODY TREE MODIFIED: NO.**
