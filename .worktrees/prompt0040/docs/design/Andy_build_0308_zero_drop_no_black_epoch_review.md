# Andy — Build 0308 Zero-Drop / No-Black Epoch Review

**Type:** analysis-only architecture review. No production change, no ROM, Build 0308 not consumed.
Baseline 0307 (`c46ed6b8…b96ac9`). Prepares the Cody Build-0308 implementation.

## Scope: residency completeness + black-frame removal. Scrolling/map placement DEFERRED.

## Black frame — CONFIRMED cause (not inferred)
`fg_boundary_advance_segment` (replaces arcade `0x558FE`, the record increment) calls
`fg_boundary_install` **synchronously, mid-gameplay-frame — not in VBlank** (reseed records defer to
`fg_boundary_install_post_reseed`, still not VBlank). `fg_boundary_install`:
1. `move.w %sr,-(%sp); ori.w #0x0700,%sr` (mask ints),
2. **VDP MODE2 DISPLAY OFF** (`0x34`, `vdp_set_reg`, fg_tile_cache.s:207),
3. clear the **10240-word active LUT** (20,480 B of writes),
4. populate LUT from up to ~960 `(code,slot)` pairs,
5. **remap both name tables** (`fg_boundary_name_remap_a/b` → `.Linstall_remap_plane`, up to 2×4096
   cells old-slot→identity→new-slot),
6. **DMA up to 960 patterns** (`vdp_dma_words_to_vram`, worst rec2var0 = 960×32 = **30,720 B**),
7. **DISPLAY ON** (`0x74`, fg_tile_cache.s:364).

All of steps 2–7 run with **display disabled, synchronously, starting mid-frame**. The work
(≈20.5 KB LUT clear + ≈30.7 KB pattern DMA + ≈16 KB name-table scan) far exceeds one frame, so the
disabled display spans **at least one full displayed frame → the user sees a black frame**. This is
the exact "black frame on every package load" Tighe reports, present since the boundary method began.
It is caused directly by the mid-frame `DISPLAY OFF`, not by mixed ownership (the remap prevents that).

## Worst transition payload (post-0307)
- LUT clear: **10,240 words (20,480 B)** fixed.
- Pattern DMA: worst **960 patterns × 32 = 30,720 B** (rec2 var0 = 237 A + 854 B).
- Name-table remap: 2 planes × up to 4096 cells scanned/translated (~16 KB touched).
- **Total ≈ 67 KB of VDP work with display off.** Genesis NTSC VBlank moves only ~7.6 KB to VRAM per
  frame (≈3,584 bytes safe budget in a 38-line blank at ~205 B/line active-off). ⇒ **the worst
  transition cannot fit in one enabled-display VBlank (Strategy A infeasible).** Deficit ≈ 60 KB.

## Compiler over-inclusion — CONFIRMED
`ordered_plane_b_codes(descriptors, rows)` iterates **every row × every descriptor × all 16 columns**
of the descriptor window — the **whole-block union**, including columns/tiles that can never be
visible in the epoch. Plane A (`seg_fg_tiles` = `collect_runtime_gameplay_fg_tiles(seg)`) is the
**whole-segment** FG set. So both planes over-union relative to the epoch's actual reachable column
window. For the widened rope records this reaches the full-stage BG (854) even though only a horizontal
sub-window scrolls past during the interval. **A column-aware model (below) would materially reduce the
required Plane-B set and is likely the difference between over-cap drops and zero-drop.**

## Root architecture: the two problems are coupled through free VRAM
- **Zero-drop** needs the plane pool grown from 960 to the real free set (64..1535 = 1472) minus the
  **proven** sprite-live set — and/or the column-aware reduction above.
- **No-black** needs a **prepare/commit** transition: preload next-only patterns into *free* slots while
  the current epoch still displays, then commit atomically in VBlank. That preload space **is** the same
  reclaimed VRAM. So the reclaim (zero-drop) is a prerequisite for no-black preload.

## Recommended transition architecture — **Strategy C** (compiler-scheduled preload + atomic VBlank commit)
Strategy A (one-VBlank) is infeasible (60 KB deficit). Strategy B (preload all next patterns in one
prior frame) can exceed the VBlank budget for heavy transitions. **Strategy C:**
- **PREPARE** (across the current epoch's many frames, display ON): a compiler-generated per-transition
  **next-only pattern DMA schedule** streams next-only identities into currently-free slots (never
  overwriting a live current identity), a few KB per VBlank. Shared identities stay in stable slots
  (already the design). Precompute the **next LUT** (double-buffered pointer) and a **name-table patch**
  (only the cells whose slot changes — not a full 4096-cell recommit).
- **COMMIT** (at the boundary, in the next VBlank, display ON): pointer-swap the active LUT + apply the
  small precomputed name-table patch + retire now-dead old-only slots. No `DISPLAY OFF`. Coherence is
  preserved because patterns are already resident and the name patch + LUT swap are one atomic VBlank.
- This is **not** per-frame residency: the schedule is deterministic, compiler-known, keyed to the same
  semantic boundary; no mark-live / allocator / LRU / eviction / miss-load / polling.

## Capacity for preload (current-live ∪ next-preload)
Worst current plane residency ≈ 1275 (rec11) or 1091 (rec2/3 full-64 A∪B). Preload needs the
**next-only** delta held simultaneously with current. With the pool at 1472 and shared-slot retention,
the feasible margin depends on the **sprite-live set**, which is **still unmeasured (FACT 1)**. If
sprite-live ≤ ~197 at the heavy intervals, current∪next-only fits; if sprites truly need ~512, heavy
transitions must lean on the column-aware reduction and/or multi-VBlank preload to stay within budget.

## Sprite reservation — **PARTIALLY justified; real peak still unmeasured**
512 = cache capacity (128 codes × 4), not proven need. Static family bases exist (fam0..4). The real
per-section coexisting sprite-pattern peak requires the driven-input gameplay observation (attract never
enters gameplay). **Recommend Build-0308 prep build that harness first** (I will build it, deriving
inputs from existing traces/arcade FU1 — not asking Tighe), measure the Stage-1 sprite peak, and bound
the reclaim by it. Until then, a conservative static per-section family bound may be used, fail-closed.

## Recommended Build sequence (builds are cheap)
- **Build 0308 = residency-complete, zero-drop.** Add the **column-aware** Plane-A/Plane-B requirement
  model (below); grow the allocator to the real free set (64..1535 minus sprite-live-per-interval,
  non-contiguous); **fail the build on any required residency miss** (no slot-0 blanking). Add the
  residency-complete assertion. Keep everything else from 0307. Sprite bound from the harness (or
  conservative static). Drops → 0.
- **Build 0309 = no-black prepare/commit.** Using the free VRAM the reclaim exposes, implement the
  Strategy-C preload schedule + atomic VBlank commit + name-table patch (replace full recommit). Remove
  the mid-frame `DISPLAY OFF`.
(If the harness proves ample free VRAM, 0308 may fold in the commit-in-VBlank change; keep them
splittable so a residency-complete build ships even if no-black needs another iteration.)

## Column-aware static model (the key compiler change for 0308)
BG block geometry is proven: 16 cols × 64 rows, row-major `src + row*0x20 + col*2`, code `& 0x3FFF`;
FG segment = 512 px = 64 cols (4 cols/group × 16 groups). For each record/epoch derive statically:
`(record, column, row-range) → Plane-A identities, Plane-B identities`, then union only the columns in
the epoch's **reachable scroll window** (entry columns + columns that can scroll in before the next
boundary), not the whole descriptor block. Report per-record: current-compiler A/B counts vs
column-aware A/B counts; this quantifies the over-inclusion and whether zero-drop fits without any
sprite reclaim. **Column knowledge is used ONLY to decide residency, not placement** (scrolling stays
deferred).

## Residency-complete assertion (Build-0308 gate)
For every legal publication `(record, x-col, y-row, plane, arcade_code)`, its canonical 32-byte identity
must exist in the active package's residency set — else **BUILD FAILS**. Applies to **both** planes
(droppedA==0 today does not prove Plane A included every legally-publishable identity; audit it under
the same column model).

## Deferred (recorded, not designed): vertical scrolling / map placement remains messy; that is the next
task after residency is complete. Do not fix here.

---

## Amendment (2026-08-22) — Level-1 Plane-B Global Residency Evidence

Tighe's new evidence (Plane B was correct before the package compiler; Level-1 B looks unchanged
outdoor↔inside) is confirmed by direct static computation. **The per-record/per-Y Plane-B packaging is
a compiler-invented regression, not a real tileset change.** This supersedes the column-aware Plane-B
recommendation above (kept only for later map/scroll work, not for residency).

### Decisive static numbers (arcade ROM + canonical 32-byte decode)
- **Level-1 Plane-B = two fully disjoint vocabularies:** outdoor `attr=0x0002` (blocks D11C/D91C/E11C/
  E91C/F11C) = **854** canonical patterns; deep-cave `attr=0x0003` (F91C/1011C) = **460**; **shared = 0**.
  Complete union = 1314, but the two sets are never live simultaneously.
- Tighe's "outdoor and inside use the same B graphics" = outdoor **+ the segment-driven cave descent**,
  which keeps tm0 outdoor → both use the **same 854 outdoor vocabulary**. The 460 set is a *later*,
  genuinely different deep-cave area = the one real B graphics transition in Level 1.
- **Level-1 Plane-A = 1315** canonical patterns total, **≤484 per record** (max at rec11) — Plane A
  genuinely changes per record.
- Per-record **A ∪ B_outdoor peak = 484 + 854 = 1338** (A∩B = 0). **Fits the 1472 pool (margin 134).**
  Deep-cave peak = A + 460 ≈ 549. With the old 960 partition, 1338 does **not** fit → global-B needs the
  expanded 64..1535 pool and a sprite peak ≤ ~134.

### Why the current compiler thinks B changes (classification)
The current per-package Plane-B differences are **not** new pattern identities. `ordered_plane_b_codes`
filters the *same* 854 outdoor vocabulary by the 40/64-row **Y band** and by descriptor window, then the
960-slot cap drops the excess. So the B "epochs" are: (B) Y-envelope spatial exclusion + (C) descriptor
filtering + (D) 960-slot drops + (E) allocator repack — essentially **zero** genuine (A) new-identity
change within the outdoor section. Build 0307's rope fix (40→64 rows on records 2/3) helped only by
un-filtering more of the one 854 vocabulary; the deeper fix is to **stop spatially filtering B residency
entirely** and keep all 854 resident.

### Revised architecture — GLOBAL Plane-B per vocabulary + per-record Plane-A
- **Plane B:** two fixed residency sets — **854 outdoor** (resident throughout outdoor+descent, fixed
  canonical→slot, no Y variant, no per-record swap, no drop) and **460 deep-cave**, with **one** genuine
  transition between them at the real outdoor→deep-cave boundary. Ordinary record boundaries do **zero**
  B pattern DMA / B remap / B drop / B display-off.
- **Plane A:** stays **per-record** (genuinely changes, ≤484), delta-loaded — a much smaller transition
  than today's full 960-slot rebuild.
- **Capacity:** peak 1338 (A484 + B854) in 1472 → needs the expanded pool + sprite peak ≤ ~134. If the
  measured sprite peak exceeds ~134 at an outdoor record, trim via A/B column-awareness (still no B
  vocabulary swap). Sprite peak remains the one unmeasured input (FACT 1); give Cody both cases.

### Black-frame impact of the revised model
Under global-B, **all** ordinary-record B residency work disappears (DMA=0, remap=0, drops=0). The only
remaining true graphics-residency transitions are: **per-record Plane-A deltas** (small) and the **single
outdoor→deep-cave B transition**. Most ordinary record boundaries then need **no `fg_boundary_install` at
all** (no pattern change → no display-off → no black frame). The Strategy-C prepare/commit engine is
needed only for the few genuine transitions (the one B vocabulary switch and the larger A deltas), not
for every record — do not build a preload engine to hide transitions that should not occur.

### Supersession
The above column-aware **Plane-B residency** recommendation is **withdrawn** (B is globally resident;
per-column is unnecessary for B residency). Per-column geometry remains useful only for the later
map/scroll publication task. Plane-A per-record residency stands.

---

## Correction (2026-08-22b) — the "854 outdoor / 460 deep-cave" two-B-vocabulary claim was WRONG

**SUPERSEDES the amendment's `854 → 460` two-Level-1-B-vocabularies statement.** Ownership was
re-proven through the actual Genesis publication path, not the source-table scene label.

### Plane ownership — PROVEN (publication path, not table label)
The `0x3951C` descriptor (`PLANE_B_DESC_TABLE_ARCADE_BASE = 0x0003951C`, tilemap_hooks.s) resolves via
`fg_boundary_resolve_b` and writes **`staged_bg_buffer`** (tilemap_hooks.s:705/828/1133/1563/1839),
which `vdp_commit_bg_strips_if_dirty` DMAs to **`VRAM_PLANE_B_BASE = 0xC000` = Genesis Plane B**
(vdp_comm.s:293–296). The FG strip-source `0x1691C` resolves via `fg_boundary_resolve_a` and writes
**`staged_fg_buffer` → `VRAM_PLANE_A_BASE = 0xE000` = Plane A**. So `0x3951C` **is** Plane B; I did not
mislabel Plane A as Plane B.

### The real error: the 460 set is STAGE 2, not Level-1
`attr` on the `0x3951C` entries is a **scene/tileset class** (`0x0002`=SCENE_GAMEPLAY outdoor,
`0x0003`=SCENE_GAMEPLAY_CAVE), **not** a plane selector — both attrs feed Plane B. The `attr=0x0003`
(460) run **begins at descriptor index 56**, which the accepted Plane-B decoder places at the
**Stage-1→Stage-2 boundary** (Stage-1 records 0–22 reach cursor ≈56; last seed/fill 52→56). Therefore
the 460 set is **Stage-2's cave-interior Plane-B vocabulary and is never referenced during Level-1
gameplay.** Including it as "Level-1 deep-cave B" was the mistake.

### Corrected Level-1 conclusion — matches Tighe
- **Level-1 Plane B = the `attr=0x0002` outdoor vocabulary = 854 canonical patterns, ONE set,
  UNCHANGING** through the entire level (outdoor + the segment-driven cave descent; tm0 stays outdoor).
  Sky / mountains / statues stay Plane B and constant. **CONFIRMED.**
- The graphics that visibly change entering the cave are **Plane A** (foreground terrain, the `0x1691C`
  strip-source → `staged_fg_buffer` → 0xE000), which genuinely changes per record (Level-1 A = 1315
  total, ≤484/record; cave-terrain A tiles are part of that per-record change). **CONFIRMED.**
- **True Level-1 Plane-B residency epochs = 1** (load once at level entry). **B pattern DMA at ordinary
  records = 0. B pattern DMA at cave entry = 0. B Y-variants = none. B drops = none. B repack = none.**
- Capacity: fixed B 854 + per-record A (≤484) = peak **1338** in the 1472 pool → ~134 for sprites (the
  one unmeasured input). The genuine `854→(Stage-2 460)` switch happens only at the **level boundary**,
  not inside Level 1.

The amendment's global-B architecture recommendation stands; only the count (854, not 854+460) and the
number of in-level B transitions (0, not 1) are corrected. Everything downstream (no per-record B work,
per-record A, load-B-once) is unchanged and now simpler.

---

## Level-1 composition note (Tighe, authoritative, 2026-08-22)
Level 1 = **3 phases**: (1) **outside** — multiple sections with small caves, **Layer A over Layer B**;
(2) **inside castle/fortress** — primarily **Layer A**, **Layer B = the same tiles as outside**, only
visible **through the windows**; (3) **boss room** — layer composition unknown. (Rough later stages,
unconfirmed: Stage 2 = jungle + fortress-through-windows; Stage 3 = possibly a large cave.)
This directly corroborates: **Level-1 Plane B is one unchanging vocabulary** (the 854 `attr=0x0002` set,
same outdoors and behind the castle windows); the changing cave/castle graphics are **Plane A**.

---

## Final Amendment (2026-08-22c) — Arcade Mapping, Level-1 Phase Scope, Gameplay VRAM

### Arcade PC080SN layers (proven independently, accepted prior RE) → Genesis mapping
Two arcade tile layers, distinguished by scroll ownership (not visual depth):
- **Arcade slow/parallax layer** — X `0xC40000` (`a5@0x10EC`, **half** step delta), Y `0xC20000`
  (`a5@0x10EE`); source = **`0x3951C` descriptor blocks**. → **Genesis Plane B** (resolve_b →
  `staged_bg_buffer` → VRAM `0xC000`).
- **Arcade fast layer** — X `0xC40002` (`a5@0x10AE`, **full** delta), Y `0xC20002` (`a5@0x10B0`);
  source = **`0x1691C` strip tables**. → **Genesis Plane A** (resolve_a → `staged_fg_buffer` → `0xE000`).
- **Mapping independently proven:** YES (arcade scroll semantics + the pre-0302 native Plane-B twin
  both map `0x3951C`→Plane B). **Current port matches:** YES — lock it for Build 0308.

### Stage-1 scope locked
`attr=0x0002` (854) = Stage-1 Plane-B source (descriptors 0–55). `attr=0x0003` (460) = **Stage-2**,
begins at descriptor 56; **0 overlap** with Level-1 B. Compiler rule: a level vocabulary must be bounded
by the arcade stage-progression descriptor range, never by table adjacency. The 460 set is excluded.

### Level-1 phases → records/descriptors (from the map-stream event structure)
- **Phase 1 (outside + small caves):** records 0–15 (to event 4), descriptors 0–~34.
- **Phase 2 (castle/fortress interior):** records 16–20 (event-4 reseed → event 6), descriptors ~36–46.
- **Phase 3 (boss room):** records 21–22 (event 6/7), descriptors ~46–55.
(Map phase ≠ pattern-residency phase — see below.)

### Plane-B vocabulary per phase — PROVEN (no assumption for the boss)
| Phase | B canonical | Added vs prior |
|---|---|---|
| Phase 1 | **854** (all 5 outdoor blocks) | — |
| Phase 2 | 663 | **0** (subset of Phase 1) |
| Phase 3 boss | 643 | **0** (subset of Phase 1∪2) |
| **Level-1 B (all)** | **854** | — |

**All three phases draw from the same 5 `attr=0x0002` blocks; no phase adds a single new B pattern.**
Boss records use descriptors 46–55 (all `attr=0x0002`) — statically proven to introduce no new B
vocabulary. ⇒ **Level-1 Plane B = ONE 854-pattern vocabulary, all 3 phases** (the "854 for all Level 1"
conclusion is now proven, including Phase 3). **In-level B residency epochs = 1; B DMA/remap/drop/Y-var
at every ordinary record AND at Phase 1→2 AND at boss entry = 0.**

### Plane-A per Level-1 — genuinely per-record
Level-1 A = **1315** canonical total; per-segment A = 49…483 (peak 483 ≈ rec11); cumulative reaches 1315.
**Global A does NOT fit** (1315 + 854 = 2169 > 1472). A **per-phase** union is also too large (Phase 1
alone approaches ~960). ⇒ **A stays per-record** (each ≤484). Coarser A grouping only where a group's A
union still fits with B854 — mostly not, so per-record is the working granularity. A transitions are the
**only** remaining genuine pattern-residency transitions in Level 1.

### Capacity (phase/interval specific)
Peak per-record **A(≤484) + B(854, fixed) = 1338** in the 1472 pool → **margin 134 for sprites** (and
any live frontend). With the old 512 sprite reservation it does **not** fit (1850) — so Build 0308 needs
the expanded 64..1535 pool **and** the reclaim below and/or a sprite peak ≤ ~134. Boss (Phase 3) B=643 +
its A is lighter; the hardest interval is a heavy Phase-1 record (A≈484).

### Gameplay VRAM ownership (color-tint correlation — partial, honest)
The color-tinted Build-0307 capture's **GREEN = free** and **RED = TAITO/frontend** labels are accepted.
Semantic-lifetime classification: **TAITO/title patterns are FRONTEND-live → DEAD/reclaimable at gameplay
entry → reload on return** (deterministic ownership, not per-frame cache). No gameplay tile should be
dropped while dead frontend graphics sit resident. **Exact green/red slot ranges must be read from the
actual capture correlated to Build-0307 VRAM state** — I will produce that with the driven-input harness
(which also closes the sprite peak); until then, treat the frontend band and any un-referenced holes in
64..1535 as reclaimable, fail-closed. Do not optimize around nominal partitions.

### Revised Build-0308 model (supersedes the column-aware-B recommendation entirely)
1. **Plane B: load the single 854-pattern Level-1 vocabulary ONCE at level entry into fixed
   canonical→slot assignments.** Zero B DMA / remap / drop / Y-variant / repack at any ordinary record,
   Phase 1→2, or boss entry. (One genuine B switch exists only at the **Stage-1→Stage-2** boundary.)
2. **Plane A: per-record residency** (≤484), delta-loaded; allocate A + fixed-B into the non-contiguous
   64..1535 pool minus the live sprite set; reclaim dead frontend slots.
3. **Zero required drops**, residency-complete assertion both planes → build fails on any legally-
   publishable identity missing (no slot-0 fallback).
4. **Black frame:** ordinary records and phase entries with no A *or* B change call **no** install; the
   only genuine transitions are per-record A deltas (small) → Strategy-C prepare/commit / VBlank commit
   for those, no mid-frame DISPLAY OFF. Expected ordinary-epoch black frames: **0**.
5. Sprite bound: static per-phase coexisting-family bound now, harness-validated later; do not block.
