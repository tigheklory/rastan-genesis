# Layer A / Layer B Future Optimization Backlog (Andy, as of Build 0425)

**Date:** 2026-10-14 · **Type:** DOCUMENTATION ONLY. No production source, no ROM, no Build 0426, no
Phase D/E. Files changed by this task: this file, `OPTIMIZATIONS.md` (pointer), `AGENTS_LOG.md`.

> **STATUS: Layer A / Layer B performance optimization is CLOSED for the current performance phase
> (Build 0425).** Builds 0423/0424/0425 removed the known material background translation costs, and
> real-Genesis evidence shows Build 0425_do horizontally scrolls with **no enemies** present without
> the previous `_do` black overrun bars. This document preserves deferred ideas so they are not lost;
> it is **not** permission to keep optimizing. Reopen only under the criteria in the last section.

This is the one authoritative place to learn, months from now: what was already optimized, what
remains, what was deliberately deferred, which old approaches are forbidden, and what evidence would
justify reopening backgrounds.

---

## 1. What is already done (do not redo)

| Build | Change | Status |
|---|---|---|
| 0418 | **128-KiB VDP-DMA source-boundary fix** — 32-byte-align the PC080SN tile corpus so no `code*32` tile straddles a 0x20000 source bank (KF-090). | accepted |
| 0419 | Fused `resolve_plane_a_name_collision_cell` (shared address/descriptor traversal; visual + collision still independent fields). | accepted |
| 0420 | Generated native metatile records (`tile[16]`+`collision[16]`) introduced; crashed (`tst.l %a0` 68020+-only). | rejected (crash) |
| 0421 | Crash fixed (`cmpa.l #0,%a0`) but Segment-0 visual regression. | rejected |
| 0422 | **Accepted Segment-0 correction** (the native-record keying/ring-front seam fix). | accepted |
| 0423 | Plane-B native 6-byte visual records (`genesistan_pc080sn_plane_b_visual_records`) + 16-column group descriptor cache. | accepted |
| 0424 | Plane-A **selector-0 four-ROW** segment hoist. | accepted |
| 0425 | Plane-A **selector-1/2 four-COLUMN** segment hoist (block4). | accepted |

**Net result:** the arcade descriptor *payload interpreter* is replaced by O(1) native record lookups
on both planes; per-strip descriptor traversals collapsed to per-4-cell-group; visual + collision are
independently sourced fields co-located in one record (shared allocation, not shared semantics).

## 2. Boundaries that MUST be preserved (proven constraints)

- **64-cell logical maintenance domain** vs the **physical Genesis 64×32 plane** — these are distinct;
  the logical ring is 64 wide, the physical plane is 64×32. (Historical full-64 audit; KF on the
  64-row aliasing.)
- **Independent visual and collision semantics**; the **separate 64×64 WRAM collision map**
  (`collision_map_64x64_words_base` @ `0xFF1E00`) read by camera+probe coords, never from VRAM.
  Collision is **Classification B** (shared descriptor source, independent field), not derived from
  visual tile identity.
- **Live arcade camera/ring/descriptor selection stays arcade-owned** (gameplay-semantic, like Sonic's
  level layout — RULES.md: arcade owns execution; no Genesis gameplay scheduler).
- **Dynamic residency where genuinely dynamic** (`fg_cache_resolve` per cell).
- **The ring-front seam requirement** that invalidated Build 0421 and the **accepted Build-0422
  correction** — a 4-cell/16-col group that straddles the live ring front must fall back to the seam
  path; group hoists are valid only within a group that does not cross the front.
- **Selector-0 four-ROW sharing boundaries (0424)** and **selector-1/2 four-COLUMN sharing boundaries
  (0425)** — each hoist shares one descriptor/record across exactly its 4-aligned group; never across
  a segment/ring-front boundary.
- **The 0418 128-KiB VDP-DMA source-boundary fix** — any future change to the tile corpus or ROM-source
  DMA must preserve 32-byte alignment / boundary-safe splitting.

## 3. Forbidden / rejected theories (do NOT revive)

- **The 0421 "+0x200" value is NOT the established Segment-0 regression cause** — that was the
  independent-audit hypothesis; the accepted correction is Build 0422. Do not reopen on the +0x200
  theory.
- **The old A-0154 "active-display timing" theory is NOT the cause of the persistent A-0154 holes** —
  that was corrected: the A-0154 holes were the **128-KiB DMA source-boundary wrap** (KF-090, fixed in
  0418). Do not re-attribute A-0154 to active-display DMA.
- **No PC080SN emulation / shadow / mirror architecture** (RULES.md + the native-replacement policy).
  No reintroduction of a ring/full-VSRAM/col-dirty layer piecemeal (KF-072) — if ever changed, all
  producers convert together.

## 4. Remaining opportunity table (DEFERRED — do not implement now)

| # | Name | Source / addr | What 0425 does | Remains dynamic | Already native/offline | Possible future opt | Why it might save | Scale | Evidence class | Correctness risk | Measure before reopening | Constraining build/report |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Per-cell FG cache / residency resolve** | `fg_cache_resolve` (`tilemap_hooks.s:391,637,903,1001,1291,…`); boundary LUT in `fg_tile_cache.s` | calls `fg_cache_resolve` per output cell to turn a code into a residency-resolved VRAM slot word | the resident VRAM slot of a code (depends on current residency state) | the tile→VRAM LUT itself; boundary packages | hoist the per-actor/per-group resident base out of the per-cell loop where a group's cells share a code range; cache last-resolved code→slot within a block | removes a `bsr` + lookup per cell (×up to 64 cells/row, ×2 planes) | **MEDIUM** | STATIC-HYPOTHESIS | LOW (pure lookup; must preserve dynamic residency correctness) | per-cell `fg_cache_resolve` cycle cost × cells/frame, and hit-rate of a block-local cache | 0423 (boundary gate retained), fg_tile_cache boundary packages |
| 2 | **Plane-A residual per-cell work (post-0424/0425)** | `.Lplane_a_publish_name_block4_native` (`:1167+`); `resolve_plane_a_cell` (`:~700`) | per 4-cell block: source descriptor select + range validate + `native_metatile_record_from_d2` + `attr_from_word` ONCE; per cell: record tile fetch + `fg_cache_resolve` + attr OR + staged write | per-cell residency (see #1); per-block ring-front seam decision | descriptor payload (native record); 4-row/4-col group sharing | widen group sharing where proven safe (e.g. skip re-validating range within a confirmed in-front group); fuse the per-cell attr OR into the record where attr is group-uniform | fewer per-cell branches/ORs | **LOW–MEDIUM** | STATIC-HYPOTHESIS | MEDIUM (group/seam boundary correctness — see 0421/0422) | per-cell residual op count vs inherent (adds+write) | 0424, 0425, 0422 seam |
| 3 | **Plane-B residual per-cell work** | `.Lplane_b_*` (`:1377,1611` record base `genesistan_pc080sn_plane_b_visual_records`); 16-col group cache | 6-byte native visual records replace descriptor interpretation; 16-col group descriptor cached; per cell `fg_cache_resolve` + staged write | per-cell residency (#1); parallax fine-X phase; 16-col group validity across ring front | the Plane-B visual record payload; the group cache | same per-cell residency hoist (#1); validate the 16-col cache cannot smear across a ring-front/segment boundary (currently per-row self-consistent) | fewer per-cell resolves | **LOW–MEDIUM** | STATIC-HYPOTHESIS | MEDIUM (parallax-independent alignment; 16-col boundary) | per-cell Plane-B op count; parallax boundary correctness | 0423 |
| 4 | **Staging / dirty publication** | `staged_fg/bg_buffer`; `fg/bg_row_dirty`, `fg/bg_col_dirty`; `dma_publish_frame` (dma.s) + column/row DMA | writes final name words to staged buffers; per-row + per-column dirty masks; column gather + 32-word DMA / row DMA | which rows/cols are dirty each frame; gather at publish | the gather + strided column DMA (autoinc 128) | coalesce adjacent dirty columns into one multi-column DMA run; skip gather for unchanged columns; reduce row/column commit setup | fewer DMA commands / less gather | **UNKNOWN** | DEFERRED IDEA | LOW–MEDIUM (must not change publication timing/ownership — NOT Phase D here) | DMA command count + gather cycles per scroll frame; is publication a material share post-Phase-D? | KF-072 (no piecemeal ring), dma.s publish-first model |
| 5 | **Package / residency transitions** | scene/segment/package installs (`scene_load.s`, `fg_tile_cache` boundary install) | installs resident tile sets + boundary packages at scene/segment/package transitions | which package is active (camera/progression) | per-scene preloads, boundary packages | reduce transition-time install cost (batch/precompute); keep **separate from steady-frame cost** | lowers one-time transition spikes | **UNKNOWN** | DEFERRED IDEA | LOW | transition-frame cost vs steady-frame cost (measure separately) | 0423 boundary packages |
| 6 | **Frontend / textwriter / number-renderer paths** | `genesistan_hook_textwriter_dispatch` (still `jsr 0x565CE` for glyphs); number/glyph renderers | arcade glyph fetch + C-window token decode → native plane fill | arcade glyph source re-entry; C-window token keying | the native plane fill | native glyph LUT (remove `jsr 0x565CE`); use a cwindow→{plane,dest} LUT | removes arcade re-entry (but NOT gameplay hot path) | **LOW** (not gameplay hot path) | STATIC-PROVEN (coupling), UNKNOWN (cost) | LOW (keep text layout identical) | is it ever on a gameplay-frame hot path? (currently frontend/HUD) | KF-089 (textwriter most arcade-coupled) |
| 7 | **Collision republish risk** | native record collision written to the 64×64 map on republish | writes static record collision to the map each republish | gameplay-mutated collision (cave-block destroy) | the collision record field | ensure a republish does NOT overwrite gameplay-mutated collision (dirty/skip on mutated cells) | prevents restoring destroyed-block collision | n/a (**CORRECTNESS / ARCHITECTURAL DEBT**, not a perf item) | STATIC-HYPOTHESIS | **MEDIUM (correctness)** | destroy-then-scroll test: does collision restore? (if yes, fix regardless of perf) | Andy_build0421 audit; exists in 0419 too |

Notes: no cycle savings are invented. Every row whose savings were never measured is marked UNKNOWN /
STATIC-HYPOTHESIS / DEFERRED IDEA. Item 7 is **correctness debt**, tracked here only so it is not lost;
it is not a performance opportunity and may need attention independent of this closure.

## 5. Reopening criteria

Layer A/B performance **SHALL NOT be reopened merely because another optimization is conceivable.**
Reopen only when one of the following is **measured/forced**:

1. A later measurement shows **background cost is again a material portion of frame time** (e.g. a new
   trace shows Plane A/B > ~15–20% of the worker in a representative gameplay frame).
2. **Phase D/E** measurements expose publication/setup cost (item 4/5) as now-dominant after the
   gameplay worker moves out of IRQ6.
3. A **later level/context** exposes a background path not covered by current R1/P1 work (new selector,
   package, or descriptor shape).
4. A **correctness requirement** forces the path to be revisited (e.g. item 7, collision republish, or
   a new boundary/seam case).
5. Sprite/audio/other work leaves a **small, specifically-measured background budget gap** where one
   named optimization above would close it.

Otherwise: **LEAVE BACKGROUNDS CLOSED.** Before reopening any item, first take the measurement named in
its "Measure before reopening" column — do not reopen on hypothesis alone.

---

**Production modified: NO. ROM built: NO. Build number consumed: NO. Phase D started: NO. Phase E
started: NO.**
