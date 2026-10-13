# Historical Full-64 Background Update Audit (Andy)

**Date:** 2026-10-11 · **Type:** RESEARCH / STATIC FORENSIC ONLY. No production source, no ROM, no
build number, no repair, Cody's working tree untouched. Git/log/doc archaeology.

**Question:** Why did the earlier native background path process **full 64-cell strips** rather than
the nominal visible span? Was it accidental, or a deliberate correctness fix for exactly the
stale/displaced Layer A/B corruption seen in Build 0415/0416?

**Bottom line:** It was **deliberate and correctness-driven**, proven across Builds 0169–0172
(64-row "tall" buffer), 0246 (full 64×64 initial fill), and 0373 (64-column trailing retention), and
governed by **KF-072**, which records that a prior narrow **ring / col-dirty** rewrite (**Build
0226**) FAILED and was reverted. Build 0415/0416's 41×29 narrowing reintroduces exactly the model
KF-072 forbids, which is why 0416 still corrupts on real hardware despite fixing the fine-scroll +1.

---

## 1. Earliest full-64 implementation

- **Vertical (64 rows):** Builds **0169–0172**. KNOWN_FINDINGS (KF around line 598–616) proves Stage-1
  terrain uses a **long/tall PC080SN column of 64 rows that the 32-row Genesis ring cannot preserve**:
  trace evidence shows "source row 39 (`row+32`) overwrites the same Genesis staging cell" — row N and
  row N+32 **alias** in a 32-row ring. Fix: `staged_fg_tall_buffer` (64×64 words) +
  `vdp_project_fg_tall_if_dirty` (Build 0172), with a rolling 32-row projection from the 64-row tall
  buffer and VSRAM carrying only the `&7` sub-tile residual (Build 0171 BG, 0172 FG).
- **Horizontal (64 columns) + full initial fill:** Build **0246**
  (`Andy_build0246_plane_a_arbitrary_row_source_proof.md`): "The initial fill publishes **64 logical
  columns × 64 logical rows** via selector-0, exposing the complete Stage-1 logical Plane A map
  (**including the rows 33–54 that the 32-row Genesis ring is missing**) before the camera pan." Every
  cell is a pure function of `(row, col, segment_index)` over ROM tables.
- **Sonic-style edge-streaming refinement (kept full-span):** Builds **0349–0352**, deliberately
  within the proven full-span coordinate model per KF-072.
- Routines: `.Lplane_a_publish_logical_row_native`, `genesistan_hook_tilemap_plane_a_selector0/12_native`,
  `genesistan_plane_a_pan_publish_entering_rows_up/down`, `.Lplane_b_publish_logical_row_native`
  (`tilemap_hooks.s`). Source file throughout: `apps/rastan-direct/src/tilemap_hooks.s` (+ the retired
  tall projector `vdp_project_*_tall_if_dirty`).

Commit granularity is coarse (Build 247/249/251/256/282…), so exact per-build hashes aren't 1:1; the
rationale lives in the contemporaneous KNOWN_FINDINGS/design docs cited.

---

## 2. Was full-64 a correctness fix? — **YES**

Contemporary evidence (not inferred from current code):
- KF (598–616): *"This proves Stage 1 terrain is using a long/tall PC080SN BG column that the current
  32-row staging model cannot preserve."* → the 64-row maintenance exists because the arcade logical
  map is 64 rows tall and a 32-row ring aliases.
- Build 0246: *"PROVEN (derivable) … exposing the complete Stage-1 logical Plane A map including the
  rows 33–54 that the 32-row Genesis ring is missing."*
- **KF-072** (the governing finding): the Build 0226 ring / full-VSRAM / **col-dirty** rewrite
  produced a **cyan band + half-screen FG displacement** and was reverted; the proven-correct model is
  0223's full-span coordinate space. HAZARD verbatim: *"do NOT reintroduce a ring / full-VSRAM /
  col-dirty layer without ALSO converting every producer … to the same coordinate space — piecemeal
  is what broke 0226."*

So full-64 is a **deliberate correctness fix** for (a) the 64-row-map vs 32-row-plane aliasing and
(b) retention of still-visible trailing terrain.

---

## 3. Historical bug most similar to 0415/0416

- **Build 0226** (visual-similarity **HIGH**): cyan band + **half-screen FG displacement** —
  large coherent *placement* corruption (identical bytes rendered at the wrong coordinate), caused by
  a **piecemeal** ring/col-dirty narrowing where producers were not all converted to the ring
  coordinate space. Fix: revert the ring; keep the 0223 full-span coordinates (KF-072).
- **Build 0399** (visual-similarity **MEDIUM**, `Andy_build0399_plane_a_combined_xy_misplaced_cell.md`):
  "Horizontal-only: clean. Vertical-only: generally clean. **Combined H+V**: intermittently one valid
  terrain cell where sky belongs; scrolling out and back self-repairs it." Root cause: a vertical
  source-ROW error; the stray is the **phase-correct terrain tile for its own column** at the wrong
  row. Same *character* as 0415/0416 (coherent terrain displaced, self-repairs on rescroll) but only
  2 cells — the 0415/0416 version is the *systematic* form.
- **Build 0373** (rope view): "the visible cell is **trailing segment-2 terrain retained in the
  64-column ring** while the stream front has advanced into progression 3." Directly shows the
  64-column ring deliberately retaining still-visible trailing terrain.

The strongest match is **0226** (large coherent displacement from a narrow ring/col-dirty model) —
the same failure class Build 0415/0416 reintroduced.

---

## 4. Rope connection — PARTLY related (shared ring invariant), temporally adjacent

- **Directly related:** the rope *block* fix (Build 0373) is about the **64-column ring retaining
  still-visible trailing-segment terrain** — the same horizontal-retention invariant the full-span
  provides. Shared invariant: **off-front / off-visible map cells must stay resident and
  source-correct while the stream front advances.**
- **Timing-only** for the rest: the rope-grab/geometry fixes (0362–0365, `Cody_build0365_rope_grab_contact_geometry_regression.md`)
  are collision-geometry, not plane-span. The full-span correctness lineage is 0169–0172 / 0227
  (KF-072) / 0246 / 0349–0352, which is temporally adjacent to the rope period but governed by the
  ring/tall-buffer invariant, not the rope logic. Tighe's memory of "around the rope period" maps to
  the 0349–0352 Sonic-streaming work that deliberately kept the full span (and 0373's ring-retention
  fix at the rope view).

---

## 5. Why 64, specifically — the exact invariant

Full-64 satisfies candidates **A + B + D + G** combined:
- **(A/G) The arcade logical map is 64 rows tall and the source is a function of
  `(row, col, segment_index)` over ROM tables; the Genesis plane is 32 physical rows, so rows N and
  N+32 alias.** You must maintain the full 64-row logical column (tall buffer) and project the visible
  32-row window, or vertical scroll exposes aliased/stale rows. (KF 598–616; Builds 0170–0172.)
- **(B/D) The source context moves:** `map_advance_source_ptrs` (arcade `0x0558C6`) advances the
  per-row source pointer +4 (one 4-column block) per scrolled block, and the segment counter
  `a5@0x013E` changes at segment boundaries (Build 0352). Already-staged **off-window** cells remain
  correct only because the full ring retains their *resolved* words; a narrow window that stops
  re-resolving them lets a segment rebase leave large coherent stale regions.
- **Trailing retention (0373):** the 64-column ring retains still-visible trailing-segment terrain
  after the stream front advances.

Could a smaller span have worked then? **NO**, not under the runtime PC080SN-derived representation —
because the source context moves and the arcade map is 64 rows tall, a narrow resident window cannot
be kept coherent without (i) full ring-height maintenance, (ii) trailing retention, and (iii) a bulk
reseed on segment rebase — i.e., effectively the full span. KF-072 proves the one prior attempt
(0226) failed.

---

## 6. Old full-64 vs current 41×29 — what the narrow model drops

State the old model maintained that 41×29 does NOT:
- **The full 64-row logical column** → so vertical scroll never projects an aliased/stale row.
  41×29 maintains 29; rows 29–31 (and the ring's N+32 aliases) go stale.
- **Still-visible trailing columns** (0373 ring retention) → 41×29 drops columns scrolled just past
  the window that the ring still displays.
- **Re-resolution of off-window cells after a source-pointer/segment rebase** → 41×29 never
  re-stages them, so a segment advance leaves them matching the *old* source context (large coherent
  displaced blocks).
- **A single coherent coordinate space across all producers** (KF-072) → 41×29 narrowed the visual
  producers while collision stays full-64 and the projection/ring assumptions differ → piecemeal.

---

## 7. Producer trigger coverage — can 41×29 expose an unrefreshed cell? **YES (CONDITIONAL)**

Sequence: scroll vertically until the projection `projection_row_base` (or VSRAM wrap) brings a
physical row that maps to a **logical row outside the 29 the producer refreshed** into view, WITHOUT a
tile-crossing entering-row producer call for that logical row (because the entering-row producer only
covers the newly-entering edge, assuming the rest of the column is already resident from the full
fill). Under the old full-64 fill + full-row maintenance, that row was resident; under 41×29 it was
never maintained → stale. A symmetric horizontal case occurs on segment rebase (trailing columns).
**Therefore 41×29 is fundamentally too narrow under the current (moving-source, 64-row-map) trigger
architecture, regardless of nominal viewport size.**

---

## 8. Segment / source-pointer rebase — the large-corruption mechanism

**Global rebase occurs: YES.** `map_advance_source_ptrs` (`0x0558C6`) advances `a5@0x1000[row_group]`
per scrolled block, and `a5@0x013E` (segment counter) changes at boundaries. Build 0352 fixed "cave
on Segment 0" precisely because the **global leading-edge segment term** was applied uniformly to
every column; the per-cell source is `a5@0x1000[row_group] + (col_block − strip_group)*4`.
**Requires bulk visual reseed: YES** — when the source front advances into a new segment, off-window
cells staged under the old context are stale; the full-span model re-resolves them continuously, a
narrow window does not. **This is the prime candidate for the large coherent rectangular corruption
Tighe sees** (whole trailing segments displaced), not a 1-cell seam.

---

## 9. Plane B history

- Plane B had its own full-span maintenance: `.Lplane_b_publish_logical_row_native` + the FG-boundary
  package system (`fg_tile_cache.s`, AB/BC transition packages) + `fg_boundary_resolve_b`, and the
  retired `vdp_project_bg_tall_if_dirty` 64-row BG tall buffer (Build 0171). Plane B parallax means its
  source front advances at a **different horizontal cadence**, so its boundary/package transitions
  invalidate strips independently of Plane A.
- Full-span rebuilding prevented stale **package** data across AB/BC parallax boundary transitions.
  Old bugs specifically affected mountain/sky bands (KF 614: "mountain bands materially more coherent"
  after the rolling 64-row projection).
- **Relevance to current corruption: HIGH.** Both planes corrupt because both had their full-span
  maintenance narrowed; Plane B additionally needs its independent parallax-cadence boundary
  re-resolution, which a shared 41-column Plane-A-aligned window cannot provide.

---

## 10. Bulk reseed events (and whether 0415/0416 removed one)

Historical bulk/full refreshes: **scene entry** (the 64×64 initial fill, Build 0246), **segment/source
rebase** (continuous full-span re-resolution), **large camera jump** (full reproject, KF-072 "peak
reproject on jump 4,736 B"), round/subround transition, rope-area transition (0373 ring context).
**Any removed/broken by 0415/0416: POSSIBLE/LIKELY** — the narrow incremental model refreshes only the
entering edge and assumes the rest is resident; if 0415/0416 did not preserve a **full reseed on
segment rebase / camera jump**, segment transitions leave whole trailing regions stale. This matches
"large blocks wrong" rather than "one stale edge tile."

---

## 11. Visual shape — favors the systematic mechanisms

0416 corruption is **extensive coherent regions on both planes**, not a 1-cell edge seam. A pure
fine-scroll +1 omission manifests first as a 1-cell edge strip; the observed large coherent
displacement points to the **64-row aliasing (§5A)**, **segment-rebase stale retention (§8)**, and
**trailing-column drop (§6)** mechanisms — ranked above the fine-scroll seam (which 0416 already
addressed). The remaining 0416 corruption is therefore NOT the off-by-one; it is the
narrow-resident-span dropping full-ring/trailing/segment-rebase state.

---

## 12. Classification — **B (conservative/required-with-missing-invariant)**

**FULL-64 WAS A DELIBERATE CORRECTNESS FIX; a smaller span is possible only with specific invariants
maintained.** Not C (incidental) — KF-072 + Builds 0170–0172/0246 prove intent. Not pure A — the
native-map architecture (§13) can make a narrow span safe. The **missing invariants** a narrow
window must add:
1. **Full ring-height per column** (all 32 physical rows, covering the 64-row-map aliasing), OR an
   explicit tall/projection model as in 0171–0172.
2. **Trailing-column retention** while the source front advances (0373).
3. **Bulk reseed on segment rebase / camera jump** (§8, §10).
4. **All producers (BG, FG, frontend, horizontal, vertical, VBlank) in one coordinate space**
   (KF-072) — no piecemeal narrowing.
Without all four, the narrow window corrupts — which is what 0415/0416 demonstrates.

---

## 13. Implication for the Genesis-native map architecture — **the key distinction**

**Full-64 was required by the OLD PC080SN-derived RUNTIME representation, NOT by VDP visibility.** The
reason a narrow window fails today is that cells are re-derived from a **moving source context**
(`map_advance_source_ptrs`, segment counter) and a 64-row logical map projected into a 32-row ring, so
cached off-window cells go stale when the context moves. With **Python-generated O(1) native map
tables keyed on absolute `(context, row, col)`**, there is **no moving source context** — every cell is
a pure function of its absolute logical position, resolvable on demand. So:

- **Does the final native-map architecture still need full-64 rebuilds? NO (SOMETIMES for collision
  span).** For the visual plane, a narrow entering-strip refresh is safe **because the native table
  makes any cell O(1)-correct regardless of camera/segment state** — the entering strip (plus the
  fine-scroll +1) is sufficient, and off-window cells need no maintenance because they're re-derived
  correctly whenever they enter. Collision still needs its full 64-ring span (physics reads
  off-visible), but that is a fixed ring, not a moving-context rebuild.
- **Minimum safe future architecture:** native O(1) map (Plane A + Plane B + collision, per context) +
  entering-strip incremental refresh (visible + fine-scroll +1) + a **bulk reseed on scene/segment/
  camera-jump** + per-plane independent resident-window tracking. This removes the full-64 requirement
  that the runtime representation imposed.

---

## RECOMMENDATION TO CODY

**Do not pursue a narrow (41×29) BG-A as a standalone fix.** It reintroduces the KF-072-forbidden
piecemeal narrowing and will keep corrupting on real hardware (as 0416 shows) because the current
runtime representation re-derives cells from a moving source context and a 64-row-map/32-row-ring.
Two safe paths:
1. **Restore the full-span (full ring-height + trailing retention + segment reseed) for BG-A** —
   accept the smaller CPU win — until BG-C lands; this is the KF-072-proven-correct model. The 0415
   transfer win (32-word column DMA vs 2048-word whole-row) is a **transfer-granularity** change that
   KF-072 explicitly permits and can be KEPT, as long as the *resident coordinate space* stays
   full-span. Keep the gather/column-DMA; widen the producer's maintained span back to the full ring.
2. **Go straight to BG-C** (Python native O(1) map tables): this is the only model under which a
   narrow entering-strip refresh is provably correct, because it removes the moving-source-context
   reason for full-64 entirely (§13).
Either way, convert **all producers together** (KF-072) and keep a **bulk reseed on segment/scene/jump**.
Do not declare BG-A correct from the verifier alone — real Genesis is the authority, and the large
coherent corruption is the segment-rebase / 64-row-alias / trailing-retention class, not the
fine-scroll seam already fixed.

---

**CODY TREE MODIFIED: NO. PRODUCTION MODIFIED: NO. ROM BUILT: NO. BUILD NUMBER CONSUMED: NO.**
