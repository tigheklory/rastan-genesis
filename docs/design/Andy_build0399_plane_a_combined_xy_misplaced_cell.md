# Andy — Plane-A Combined X/Y Misplaced 8×8 Cell (STATIC NARROWING — STOP, NO BUILD)

**Baseline:** Build 0398. **Counter:** 398 → 398 (no ROM; no production source changed). Andy performed no
gameplay verification — authority: TIGHE. No H25.

**Outcome: STOP before build.** Static analysis narrows the defect to a specific combined-X/Y-sensitive
surface, but the prompt's required first-divergence discriminator (a captured bad cell's staged vs VRAM word
with its H-source and V-source) needs a runtime capture of an intermittent event, which I cannot
deterministically reproduce. A guessed patch to that surface would risk the explicitly-protected accepted
Plane-A work (Builds 0391/0397/0398) and horizontal-only scrolling (which is correct). Per the task's
"if and ONLY if one concrete cause is proven" build gate, no build is produced.

## 1. Reproduction condition (from Tighe)
Horizontal-only scroll: no defect. Vertical-only (e.g. climbable-rope straight up): generally none.
**Combined horizontal + vertical** camera motion (jump across ascending/descending stepped terrain; jump up
with a small horizontal component): intermittently one 8×8 Plane-A terrain cell appears where blank/other
terrain should be, sometimes with a corresponding missing cell (observed up to 3 stray cells at once). The
pattern graphics are valid; the **name-table cell content/placement** is wrong. Scrolling the region out of
the ring and back usually self-repairs it.

## 2. Current Plane-A producer architecture (as read in `tilemap_hooks.s`)
- **Shared resolver `resolve_plane_a_cell`** (line 593) maps (logical/physical-ring row, column) → final
  Genesis name word. Its source selection is controlled by the **shared global `plane_a_src_ref_block`**:
  - value `16` ⇒ **resident/vertical mode**: ring-unwrap (lines 641–663) computes the per-column source block
    delta from the **live arcade front** `strip_group` (a5@0x10CC) and `strip_index` (a5@0x10CA), with a
    wrap-correction at the front cell (`cmp front_phys_col; subi #16`).
  - any other value ⇒ **horizontal leading-edge mode** (line 666): `delta = col_block − plane_a_src_ref_block`.
- **Horizontal producer** (line ~240): reads the live front (`strip_group`@245, `strip_index`@252), sets
  `plane_a_src_ref_block = strip_group`, and stages the ONE leading entering column (col_block == front ⇒
  delta 0) for all resident rows; sets `fg_col_dirty`.
- **Vertical row producers** (line ~820 `.Lplane_a_row_col_loop`, and the pan hooks
  `genesistan_plane_a_pan_publish_entering_rows_up/down` @495/531): set `plane_a_src_ref_block = 16` and stage
  the entering row across all 64 physical columns via the resident-mode ring-unwrap; set `fg_row_dirty`.

Each producer sets `plane_a_src_ref_block` at the top of its own routine and runs its loop, so the mode
global is not itself stale **within** a single producer's loop (that part is coherent).

## 3. Narrowed first-divergence surface (HYPOTHESIS — not yet proven)
Two candidate mechanisms, both specific to combined X/Y:
1. **Incoherent front snapshot between the two hooks.** The horizontal producer and the vertical/resident
   ring-unwrap each read the **live** arcade front (`strip_group`/`strip_index`, a5@0x10CC/0x10CA)
   *independently*, at different points in the frame. If the arcade advances the front (horizontal
   `map_advance_source_ptrs`, 0x558C6) **between** the horizontal-edge hook and the vertical-row hook during a
   combined-motion frame, the two producers stage from **different fronts**. A column staged by H at front N and
   re-resolved by V at front N+1 (or vice versa) would select a source block one off ⇒ a valid neighbouring
   metatile placed where the correct one belongs, and the correct cell left missing/stale. This matches the
   "one extra + one missing, self-repairs on re-entry" symptom.
2. **Ring-unwrap front-cell boundary.** The resident-mode wrap-correction (641–663) uses *physical-column*
   granularity (`col <= front_phys_col`) to choose a *block*-granularity delta, flipping by a full ring
   revolution (`−16` blocks) right at the front cell. During simultaneous X/Y motion where `strip_index`
   advances as a row enters, a column at that front-cell boundary could flip source block in a frame where the
   other axis expected the prior block.

These are consistent with the Build-0353 residual uncertainty about arbitrary horizontal scroll / ring
rotation (catch-up review §4). **Neither is proven.** Static reasoning shows the steady-state ring-unwrap is
self-consistent with the horizontal leading-edge staging *when both use the same front*; the defect therefore
most likely requires the two producers to disagree on the front (mechanism 1) or hit the boundary flip
(mechanism 2) during a single combined-motion update.

## 4. What is required to PROVE it (the discriminator — NOT YET DONE)
Catch ONE bad occurrence (simplest repro: jump up/down ordinary stepped terrain) and, for one stray physical
Plane-A cell, record: physical row/column; expected name word; actual Plane-A VRAM word; and the same cell in
`staged_fg_buffer` at publication.
- **Case A (staged already wrong):** the error is pre-VBlank. Capture, for that intersection cell, the
  horizontal producer's (world row/col, descriptor, code, resolved word, physical ring row/col) and the
  vertical producer's (same), and the front (`strip_group`/`strip_index`) each producer read. Answer the three
  separate questions: do they agree on **world source**, on **physical destination**, on **final name word**?
  Disagreement on world source with equal destination ⇒ mechanism 1/2 (source/front incoherence).
- **Case B (staged correct, VRAM wrong):** inspect `vdp_commit_fg_narrow_strips` publication order
  (column vs row vs narrow) for a late overwrite/omission at that physical cell.
This needs a runtime trace (BlastEm/MAME) during a combined-X/Y event; the intermittency prevents a
deterministic static proof of the specific bad cell.

## 5. Relation to OPEN-028
**NOT PROVEN same.** OPEN-028 (isolated stale Plane-A **sky** names on first arrival) could share mechanism 1
(incoherent/stale cell during streaming), but this combined-X/Y terrain defect has a distinct trigger
(simultaneous H+V) and self-repairs on re-entry. Left separate until one captured first divergence explains
both.

## 6. Why no build
No concrete first divergence is proven (only a strong static hypothesis), and the candidate surfaces
(resident-mode ring-unwrap / H-V front coherence) are exactly the Build-0353 code whose over-eager change
previously regressed Plane-A. A guessed fix risks the protected accepted work (0391 waterfall/population, 0397
overlap 8, 0398 overlap 9) and horizontal-only scrolling. The task's rule is "if and ONLY if one concrete
cause is proven and the fix is bounded." It is not yet proven, so: **no patch, no ROM, counter 398.**

## 7. Recommended next step
Instrument a bounded read-only Genesis trace keyed on **frames where both `fg_col_dirty` and `fg_row_dirty`
are non-zero** (combined X/Y) that dumps, for each dirty cell, the staged word, the post-commit VRAM word, and
the front (`strip_group`/`strip_index`) at both the horizontal-edge hook and the vertical-row hook. The first
frame where the two fronts differ (or a dirty cell's staged≠expected) is the first divergence; then patch the
proven cause (a single coherent front snapshot shared by both producers, if mechanism 1; or the boundary
delta, if mechanism 2) and build 0399.

---
Production source changed: **NO** · ROM built: **NO** · Counter after: **398**.
