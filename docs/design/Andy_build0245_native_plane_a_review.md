# Build 0245 Native Plane A Review (analysis; no source/build)

**Type:** architecture review. **Production / build / counter:** unchanged (245).
**Authority:** original arcade opcodes + `docs/arcade_reference/pc080sn/` + `Andy_plane_a_selector0_logical_coordinate_proof.md` + Build 0245 source + `address_map.json`.
**Evidence:** `states/traces/build0245_plane_a_review_*/`. Baseline note: Build 0235 is *not* a
correctness baseline; 0242–0245 are forward development.

---

## 1. Orientation / decompilation-to-address map

| Arcade PC | Role (semantic) | Genesis disposition in 0245 |
|---|---|---|
| 0x0503DC/0x050434 | scene fill (64 publications, seeds C08000 cursors, `−0x3FFC`/`−0x100` back-step) | drives dispatch; C08000 cursor bookkeeping still arcade-owned |
| 0x0558A2/0x0558C6 | ring/source progression (10CA/10CC, base +4, rebuild) | **retained arcade-owned** |
| 0x055904 | descriptor rebuild → 0x10D040 (ptrs) / 0x10D080 (words) | **retained arcade-owned** (native helpers read these) |
| 0x055948 | selector dispatch (10A8), 10CA++ | **retained**; routes to native helpers |
| 0x055968 | selector-0 column driver (16 seg over 0x10D040/80; a0=C08000 cursor) | byte-neutral route → `..._selector0_native` |
| 0x055990 | selector-1/2 row driver | byte-neutral route → `..._selector12_native` |
| 0x0559B2 | selector-0 cell producer (C08000 writes, collision, +0x100 stride) | **replaced natively** |
| 0x055A14 | selector-1/2 cell producer (dir-aware, strip complement) | **replaced natively** |
| 0x055AB4 | scroll publication | `vdp_commit_scroll` (VSRAM) |

## 2. Selector-0 semantic review (native helper `..._selector0_native`)

- **logical_column = (a5@0x10CC · 4 + a5@0x10CA) & 63** — matches the proven contract
  (`Andy_plane_a_selector0_logical_coordinate_proof.md`). ✓
- **logical_row = segment·4 + cell** (seg 0..15, cell 0..3). ✓
- **collision** = `0xFF1E00 + (logical_row·64 + logical_column)·2` for every cell (uses an
  explicit collision base to dodge the 8-bit displacement wrap). ✓ Matches proven contract.
- **tile source** = `*(block + cell·8 + strip·2)` (block = 0x10D040[seg]); LUT via
  `pc080sn_tile_vram_lut`. ✓
- **attribute source** = per-segment word0 = 0x10D080[seg]; extracted (see §7) — **defective**.
- **register discipline** = `movem.l d0-d7/a0-a6` save/restore. ✓ (the Build 0240 clobber root is fixed.)
- **placement** = resident-window `physical_row = (logical_row − visible_top)&31`, resident iff
  `(logical_row − visible_top)&63 < 32`; `visible_top = (−staged_scroll_y_fg + 8) >> 3 & 63`.
  **This is the core defect (§6).**

## 3. Selector-1/2 semantic review (native helper `..._selector12_native`)

- **shape:** one entering ROW across 64 columns (16 seg × 4 cells = 64 columns). ✓
- **strip/direction:** `strip = 10CA&3`; **if selector ≠ 2: `strip = (~strip)&3`** (reversal) —
  matches arcade 0x055A14 (`notw/andi #3` when 10A8≠2). Structurally correct; **not runtime-proven**
  (probe never reached selector-1/2).
- **logical_row = (10CC·4 + strip) & 63**; **logical_column = segment·4 + cell**. Symmetric to
  selector-0 on the Y axis; **strong hypothesis, unproven at runtime.**
- **source indexing** = `block + 20 + cell·2 + strip·8` (collision) / `block + cell·2 + strip·8`
  (tile) — matches 0x055A14's row-major `stripT·8 + row·2`. ✓
- **collision** = same logical formula as selector-0. ✓
- **placement:** same resident-window model as selector-0 → **same core defect (§6).**

## 4. Cody source audit (classification)

| Aspect | Selector-0 | Selector-1/2 |
|---|---|---|
| semantic inputs preserved | correct (10CA/10CC/tables/strip) | correct |
| chip-specific inputs retained | none in the helper (a0/C08000 not used) | none |
| tile source | **correct** | **correct** (matches producer) |
| attribute source | **incorrect** (§7) | **incorrect** (§7, same code) |
| logical coordinate | **correct** | **strong-hyp / unproven** |
| physical staging coordinate | **incorrect** (resident-window §6) | **incorrect** (§6) |
| collision coordinate | **correct** | correct (unproven at runtime) |
| VBlank publication | correct mechanism (`fg_row_dirty` + narrow-strip commit) | same |
| scroll relationship | **incorrect** (VSRAM residual vs resident model §6) | **incorrect** |
| return/register behavior | **correct** (movem save/restore) | correct |

The native VDP/DMA commit routines (`vdp_commit_fg_narrow_strips` etc.) work; the producer
*coordinate/attribute data* is wrong. Do not replace the commit routines.

## 5. Matched cell trace / evidence

Runtime (`rev.txt`): on flat Stage-1 ground the FG camera Y is static (`staged_scroll_y_fg`
constant 0x430E, `visible_top`=31), so Plane A is coherent there — consistent with the user's
"Plane A improved." Vertical camera motion only occurs during the pit-fall (not reachable in a
bounded probe), so the fall divergence is established from the **authoritative user observations
+ the code-level proof** (§6), not a fresh runtime fall capture. The selector-0 coordinate
formulas were independently runtime-proven earlier (205 publications, 0 mismatches) in
`Andy_plane_a_selector0_logical_coordinate_proof.md`.

## 6. Coordinate / scroll conclusion (the #1 bug)

**Proven from code + arcade semantics + user observations:**

- 0245 stages Plane A as a **resident window**: `physical_row = (logical_row − visible_top)&31`,
  and `vdp_commit_scroll` sets gameplay FG VSRAM to `(−scroll_y+8) & 0x0007` — **residual only**.
- These pair *internally*, **but the resident-window model requires the whole 32-row window to be
  repainted whenever `visible_top` changes.** The arcade only publishes **entering edges** (one
  column per selector-0, one row per selector-1/2) — it never repaints the window. So when the
  camera moves vertically (a fall/reset changes `scroll_y` → `visible_top`), every previously
  published cell is left at a physical row offset by the accumulated `visible_top` delta, and the
  residual VSRAM (≤8px) cannot compensate. Result exactly matches the reported symptoms:
  - land on invisible collision during a fall (collision is logical-indexed and correct; the
    *visual* rows are stale/misplaced);
  - horizontal motion "propagates" the ground (selector-0 republishes columns at the *current*
    `visible_top`, fixing them one column at a time);
  - reset redraws ground too high (`visible_top` at reset differs from the published rows).

**The correct model is the arcade's own RING, adapted to 32 rows:**

- `physical_row = logical_row & 31` (fixed per logical row, never tracks the camera), and
- **VSRAM_fg = full `(−scroll_y+8) & 0x1FF`** (hardware wraps at the 256px / 32-row plane).

Justification: the arcade C-window is a **64-row ring** (chip row = logical row; VSRAM covers the
full range; entering edges written at `logical`; vertical motion handled by scroll, no repaint).
The Genesis FG plane is 64×**32**. Within any ≤32-row visible window (the screen is 28 rows),
`logical_row & 31` is a **bijection** → no aliasing → a valid 32-row ring. Full VSRAM then
positions the view and vertical motion needs **no repaint**. **Cody's 0245 change away from
`physical_row = logical_row & 31` was the regression;** the fix is to restore `logical & 31`
**and** change gameplay FG VSRAM from `&7` to the full value. (Sel-0 and sel-1/2 must use the same
ring basis — Phase-4 Q7 — which they will once both use `logical & 31`.) These two models are
**not** equally plausible: the resident model is proven to violate the arcade's edge-only
publication; the ring model is the arcade's actual model. No STOP on the coordinate question.

## 7. Palette conclusion (the #2 bug)

`pc080sn_attr_lut.bin` is 32 entries (5-bit index). The helper builds the index as
`(word0 & 3) | (bit14<<2) | (bit15<<3) | (bit13<<4)`; the LUT maps **word0 bits 0-1 → Genesis
palette line (0-3)**, bit14→Hflip, bit15→Vflip, bit13→priority. Per the arcade reference, word0
color is **bits 0-8** (9 bits). So the Genesis palette line is derived from **only 2 of the 9
color bits** — arcade color banks that differ in bits 2-8 but share bits 0-1 collapse to the same
(often wrong) Genesis line, and this **conflicts with the established gameplay FG palette route
(bank 3 → line 1, carried by `vdp_reassert_fg_bank3_line`)**: word0=0x0003 yields bits0-1=3 →
line 3 here, while the intended gameplay FG colors live on line 1. This is exactly "correct tile,
wrong palette." **Palette-path bug in the attribute extraction/LUT index**, cleanly separable from
the tile (tile proven correct). Flips (bit14→H, bit15→V) are correct; bit13→priority is an
unverified assumption. **Fix:** derive the Genesis palette line from the full arcade color bank
via the palette-route table (the same bank→line mapping the sprite/carrier system uses), not from
word0 bits 0-1.

## 8. Tile preload / residency conclusion

No evidence of a tile-index→wrong-pattern defect: the tile LUT (`pc080sn_tile_vram_lut`) and scene
preload are unchanged from the accepted split-residency model; the user explicitly reports
**correct tile patterns** with wrong palette. So valid tile IDs reference the correct patterns —
this is **not** a preload/residency bug. (Unresolved: the cave/after-rope residency remains the
separately-tracked progression issue, not a Plane A migration defect.)

## 9. Reset-state conclusion

Reset "ground too high" is a direct consequence of §6: the level-start fill publishes at the reset
`visible_top`, and any residual stale ownership/`visible_top`/dirty state from before the reset
places the coarse row wrong. It is **not** a separate producer bug — it disappears once the ring
model (§6) removes the `visible_top`-dependent placement. (Confirm `fg_native_gameplay_owner`,
`fg_row_dirty`, and scroll are cleared on the scene-fill/clear path — a small init audit for the
fix, not a distinct defect.)

## 10. Plane B bounded audit

Plane B is **unchanged**: `_vblank_service` still calls `vdp_project_bg_tall_if_dirty` →
`vdp_commit_bg_strips_if_dirty` (tall buffer → project visible window → dirty-row DMA), with BG
VSRAM also `&7` residual. So the **Build 0235 shearing during vertical motion is inherited**,
same root as the FG resident-window/residual mismatch (the projection re-maps the window but the
residual VSRAM + per-crossing timing tear the composed screen). The Plane Viewer showing coherent
Plane B map data while the composed screen shears is consistent with a VSRAM/projection-timing
issue, not corrupt map data. **Highest safe future native Plane B boundary:** the tilemap0 vertical
streamer at **0x055B8E** (gameplay trigger) / cell walk **0x055C4A→0x055C5E→0x055C7A** — a native
Plane B strip publisher on the vertical trigger, using the same ring model. **Not designed or
implemented here.**

## 11. Ranked defect list

1. **[PROVEN · coordinate/scroll] Plane A resident-window placement + residual VSRAM.** First
   divergence: any cell survives a `visible_top` change (vertical camera move) → stale physical
   row. Class: coordinate + scroll. Smallest correction: `physical_row = logical_row & 31` in both
   native helpers **and** gameplay FG VSRAM `&7 → & 0x1FF`. Fixes existing helpers only — **no new
   producer needed.**
2. **[PROVEN · palette] Attribute palette-line from word0 bits 0-1 only.** First divergence: two
   arcade color banks sharing bits 0-1 → same Genesis line; conflicts with bank-3→line-1. Class:
   palette. Smallest correction: index the palette line by the full arcade color bank via the
   palette-route table. Fixes the existing attr path — no new producer.
3. **[INHERITED · Plane B] tall-projection + residual VSRAM shearing** (0235). Class: coordinate/
   commit. Correction: future native Plane B strip publisher (§10) — separate task, **not now.**
4. **[STRONG HYP · selector-1/2] row formula + reversal unproven at runtime.** Structurally matches
   arcade 0x055A14 and selector-0 symmetry, but never executed in a probe. Needs a
   selector-1/2-reaching trace (vertical crossing) to confirm up/down/reversal before trusting.

## 12. Distinctions

- **Proven bugs:** #1 (coordinate/scroll), #2 (palette).
- **Strong hypotheses:** #4 (selector-1/2 row/reversal correctness); bit13→priority.
- **Unresolved questions:** exact VSRAM bias/sign for the full-VSRAM ring (small implementation
  proof); whether any reset path leaves stale `fg_native_gameplay_owner`/dirty (init audit).
- **Expected consequences of incomplete work:** selector-1/2 correctness pending a reaching trace;
  vertical coherence pending #1.
- **Inherited Build 0235 defects:** Plane B shearing (#3); the first-rope/progression defect
  (unchanged — NOT caused by the Plane A migration).

## 13. Recommended next implementation boundary

**Fix the existing selector-0 helper only, smallest step:** change its placement from
`physical_row = (logical_row − visible_top)&31` to `physical_row = logical_row & 31`, and change
gameplay FG VSRAM in `vdp_commit_scroll` from `& 0x0007` to `& 0x01FF` (paired — they must change
together). Validate on flat ground (unchanged) and, if a vertical scene is reachable, that ground
stays visible through a fall/reset with no repaint. Defer selector-1/2 runtime proof, the palette
fix (#2, independent), and Plane B (#3) to separate steps. Do **not** add any shadow/mirror/
projection; the ring model writes final Plane A words directly (policy-compliant).

## 14. Sonic 1 / Rainbow Islands dual-ring alignment (added)

The intended reference model — Rainbow Islands' native Mega Drive port + the Sonic 1 disasm
map-draw (`DrawBlocks_LR`/`_TB`, `Calc_VRAM_Pos` folding world X/Y into a wrapped plane cell via
`andi` masks, edge-only, no shadow) — is a **dual X/Y ring**. This is precisely the model §6
concludes, and it confirms (does not change) this review:

- **X ring = 64** (plane is 64 cols = 512px). Already correct in 0245: selector-0
  `logical_column = (10CC·4+10CA)&63`, HSCROLL already full (`staged_scroll_x_fg − bias`). **No
  change needed on X.**
- **Y ring = 32** (plane is 64×**32** = 256px). This is the axis Cody broke. Fix = make Y a ring
  like X: `physical_row = logical_row & 31` + **full VSRAM** (`&0x1FF`). Camera Y motion is then a
  pure VSRAM scroll with **no repaint** — the Sonic/RI property.

**Refinement (important):** because the arcade map is 64 logical rows but the Genesis Y ring is
only 32, the two must be reconciled by a **residency gate**, which 0245 already has and which
**stays**: only publish logical rows inside the current 32-row visible window
(`(logical_row − visible_top)&63 < 32`) — otherwise a column's rows 0-31 and 32-63 would alias
onto the same physical rows. The bug is **not** that gate; it is the **placement**: 0245 uses
`physical_row = (logical_row − visible_top)&31` (a visible_top-relative remap → every logical
row's physical cell moves when the camera moves → stale), whereas the ring places at
`physical_row = logical_row & 31` (fixed per logical row → the entering row overwrites the aliased
leaving row that has scrolled off, and VSRAM shows the window). So the corrected selector-0 inner
logic is: **keep the residency gate; change only the placement to `logical_row & 31`; and set
VSRAM to full.** (X needs neither change.) This is the dual X/Y ring, edge-only, no shadow, no
PC080SN compatibility layer — matching the policy and the RI/Sonic model.

**Plane B (§10)** should become the same dual-ring native publisher (X&63 / Y&31 / full VSRAM) at
0x055B8E — replacing the tall-projection — in its own later task.

## STOP

Not triggered. Decompilation confirms the selector meanings; the coordinate model is determined
(ring, not resident) by arcade semantics + user evidence — not equally plausible; the palette
mismatch is cleanly separated from tile-index (tile correct); the safe cut is resolved
(fix existing helpers). Selector-1/2 runtime proof is a follow-up, not a blocker for the review.
