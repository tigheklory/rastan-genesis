# Build 0415 — BG-A Visual Regression Forensic Review (Andy)

**Date:** 2026-10-11 · **Type:** STATIC / FORENSIC REVIEW ONLY. No production source, no ROM, no
build number, no repair implemented, Cody's working tree untouched.

**Scope note:** Cody's working tree is **not** identical to the shipped Build 0415. The shipped 0415
used a `40×28` resident span; the current uncommitted tree already has `BG_A_RESIDENT_ROWS = 29` /
`BG_A_RESIDENT_COLS = 41` (`tilemap_hooks.s:114-115`) and
`tools/translation/verify_bg_a_incremental_background.py` has been rewritten to state this diagnosis
and require the old `40×28` model to fail. **This review independently confirms that root cause and
validates 41×29 as the minimal safe span** — it does not need a new repair invented.

---

## 0. Hardware facts (accepted)

Real Genesis: ~4 enemies before the diagnostic bar on 0413/0414/0415 alike → **no 0415
static/sprite regression**. BlastEm's ~2-enemy bar is emulator-specific, ignore. The real 0415
regression is **Layer A + Layer B corruption during scrolling** (coherent but displaced/stale
terrain + mountains/sky; sprites coherent). Build 0415 CPU win is real (row/map 153,890→98,298;
scroll IRQ 233,829→179,471) and should be preserved.

---

## 1. The 28-row assumption — UNSAFE (minimum safe = 29)

The Genesis Plane A/B name table is 64×**32**. The display is 224 px = **28** full cells high. The
VDP, whenever fine VSCROLL ≠ 0, exposes **one additional partial row** (the 29th). Shipped 0415
resolved only the **28** full-cell visible rows for an entering column, so the partial **29th** row
the VDP actually samples was never refreshed → stale. During any vertical/diagonal scroll (fine Y
almost always ≠ 0) that stale partial row shows the previous world content.

- **Minimum safe Plane A physical/logical rows per entering column: 29** (28 full + 1 fine-Y
  partial). **Plane B: 29** (shares the vertical scroll; its parallax is horizontal, not vertical).
- **The physical 32 is NOT required to be resident:** the viewport (29 rows) is smaller than the
  plane (32), and the ring never makes the other 3 physical rows simultaneously visible, so they may
  remain stale. The column DMA publishing 32 words (3 off-window stale rows) is therefore **harmless**
  — those 3 rows are never in the aligned visible window. This is why the fix is "+1", not "+4".
- **Evidence:** `BG_A_RESIDENT_ROWS` (now 29) vs the 32-word column DMA (`move.w #32,%d1`,
  `tilemap_hooks.s:4312/4382`); the selector-0 comment chain on deriving `visible_top` from the live
  scroll; the VDP fine-scroll partial-tile exposure rule.

**Verdict: the shipped 28-row span is UNSAFE; 29 is the minimal safe value and is what the current
tree uses.**

---

## 2. The 40-column assumption — UNSAFE (minimum safe = 41; Plane B independent)

Same mechanism horizontally: 320 px = **40** full cells; fine HSCROLL ≠ 0 exposes **one additional
partial column** (the 41st). Shipped 0415 refreshed 40 → the partial 41st column the VDP samples was
stale → vertical stale strip during horizontal scroll.

- **Minimum safe Plane A columns per entering row: 41** (40 + 1 fine-X partial).
- **Plane B: 41, independently aligned.** Plane B scrolls at a different (parallax) horizontal rate,
  so its fine-X phase and entering-column cadence differ from Plane A (Cody's own note: "Plane-B
  horizontal work follows its retained parallax crossing cadence"). B's 41-column window must be
  computed from **B's** scroll, not A's.
- The other 23 physical columns (64−41) need not be resident (never simultaneously visible), so the
  savings are preserved.

**Verdict: the shipped 40-column span is UNSAFE; 41 is minimal safe; Plane B needs its own aligned
41-column window.**

---

## 3. Gather / dirty audit — SAFE (not the bug)

Traced `vdp_commit_fg_columns_if_dirty` / `vdp_commit_bg_columns_if_dirty` (`tilemap_hooks.s:4273-4396`):

- **Gather filled by:** the **publisher**, at publication time (`.Lfgcol_gather_word` / `.Lbgcol_gather_word`).
- **Filled by producer:** NO.
- **Multiple pending dirty columns possible:** YES (64-bit `fg/bg_col_dirty`, multiple bits).
- **Data source for each dirty bit:** the publisher scans columns 0..63 and, for each set bit,
  **re-gathers 32 words fresh from `staged_fg_buffer[(row&31)*64+col]`** (strided 128 B) into the
  single gather, then DMAs, then advances to the next bit. So each column is gathered immediately
  before its own DMA.
- **Gather regenerated per dirty column:** YES.
- **Scratch overwrite possible:** NO — the single 32-word gather is a sequential publish-time
  transient; column N is fully DMA'd before column N+1 is gathered.

**Multiple pending columns are handled correctly. The single gather buffer is safe. Not the bug.**

---

## 4. Row/column overlap — SAFE (not the bug)

The gather reads `staged_fg_buffer` at **publication time (VBlank)**, after every producer (row and
column) has written the staged buffer during the frame. The staged buffer is the single source of
truth; the gather always reflects the final staged state. Diagonal motion (column C dirty, then row R
writes `staged[C,R]`) is safe because the gather for column C runs at publish, strictly after the
row write. **Stale gather possible: NO.** Ordering: all producers → staged buffer → (VBlank) dirty
scan → per-column gather → DMA.

---

## 5. VDP column DMA — mathematically correct

- Plane A destination: `VRAM_PLANE_A_BASE + col*2`; Plane B: `VRAM_PLANE_B_BASE + col*2` (`col*2`
  from `add.w %d4,%d0` with `%d4 = col*2`).
- 32-word sequence: autoincrement set to **0x80 = 128 bytes = 64 words = one name-table row**, so
  word k lands at `base + col*2 + k*128` = physical row k, column col. Correct for a 64×32 plane.
- **Autoincrement 128 correct: YES.** **32-word sequence correct: YES.** **Wrap correct: YES** (one
  column, physical rows 0..31, no intra-column wrap; `col` is already `&63`).
- The DMA publishes all 32 physical rows including the 3 off-window unrefreshed rows — **harmless**
  (§1): never in the aligned visible window.

**The DMA path is not the bug.**

---

## 6. Why the old verifier passed broken 0415

The pre-fix verifier modeled the **logical `40×28` viewport** and checked that the producer resolved
and staged those cells correctly. It did **not** model: (a) the VDP's fine-scroll **+1 partial
row/column** exposure (the actual physical visible set is 41×29 when fine scroll ≠ 0); (b) the
physical 64×32 ring aliasing and which physical cells the VDP samples at a given scroll; (c)
independent Plane-B parallax alignment. Because its "visible set" was exactly the `40×28` the
producer refreshed, the stale 41st column / 29th row were **outside the verifier's model**, so broken
0415 passed.

(The **current** tree's verifier already closes this: its header models physical ring aliasing, fine
offsets 0..7, independent Plane-B scroll, and requires the `40×28` contract to FAIL and `41×29` to
hold. This review corroborates that design.)

---

## 7. Minimal failing sequence (fails broken 0415, passes the fix)

**Sequence:** from a steady horizontal scroll, advance the camera by **1 pixel** (fine HSCROLL = 1,
**no** tile crossing → no entering-column producer runs this frame). Model the VDP sampling the
full exposed set.

- **Expected (golden full-plane):** the viewport now covers 41 columns; column 41 (the partial)
  holds the correct current-world tiles.
- **Broken 0415 (40×28 model):** column 41 was never resolved/staged → the VDP samples the stale ring
  cell (previous world column) → coherent displaced terrain strip at the right edge, both planes.
- **Fixed (41×29):** column 41 is resident and correct → match.

A symmetric vertical variant (fine VSCROLL = 1, no row crossing) fails on the 29th row.

---

## 8. Root-cause ranking

**#1 — Resident span omitted the fine-scroll +1 partial row/column (40×28 instead of 41×29).**
Confidence: **HIGH.** Evidence: shipped span = full-cell viewport; VDP fine-scroll partial-tile rule;
Cody's own in-progress 29/41 correction + rewritten verifier. Symptom: coherent displaced/stale
1-cell edge strip, revealed whenever fine scroll ≠ 0 (i.e. almost always while scrolling); **both
planes** (both reduced); rectangular/coherent (stale ring cells = real old-world tiles); sprites
unaffected. Discriminating test: §7 (1-pixel fine scroll, no tile crossing). Repair: 40×28 → 41×29
(already in tree).

**#2 — Plane-B window not independently aligned to its parallax scroll.** Confidence: **MEDIUM.**
Evidence: B scrolls at a different horizontal rate (parallax); if B reuses A's window origin/cadence,
B's entering edge drifts. Symptom: B-only stale strip whose offset tracks the parallax ratio (A
clean). Discriminating test: scroll horizontally and compare A vs B edge correctness. Repair: compute
B's resident window + entering strip from B's own scroll register.

**#3 — Resident-window origin phase vs scroll source (the Build-0399 class).** Confidence: **LOW**
(0399 already switched the producer to the live `a5@0x10B0`). Symptom: 1-cell leading-edge stale
during *combined* H+V motion. Test: pure-axis vs diagonal. Repair: ensure window origin uses the same
live scroll the VDP publishes.

**#4 — Gather lifetime / multiple pending columns.** Confidence: **REJECTED** (§3): publish-time,
per-column, from staged.

**#5 — Column DMA destination / autoinc / wrap math.** Confidence: **REJECTED** (§5): correct.

---

## 9. Recommended repair (design only)

Adopt the span already in Cody's tree: **`BG_A_RESIDENT_ROWS = 29`, `BG_A_RESIDENT_COLS = 41`** (full
visible + 1 fine-scroll partial on each axis), applied to selector-0 (entering column: 29 rows),
selector-1/2 + pan (entering row: 41 cols), for **both** planes. Additionally (**#2**) give Plane B
an **independent** resident window + entering-strip derivation from B's own parallax scroll, rather
than sharing Plane A's origin/cadence. Keep the full-span (64-row) **collision** maintenance
unchanged (physics needs the full ring; §collision in the implementation spec). No change to the
gather, dirty, or DMA paths (all sound).

Guard it with the rewritten verifier (model the physical 64×32, fine offsets 0..7, independent B
scroll, require 40×28 to fail and 41×29 to pass) so the regression cannot recur.

---

## 10. Performance impact of repair

The fix adds **one row** per entering column and **one column** per entering row (and separates
Plane-B alignment) — roughly **+1 resolver call per entering strip**, negligible against the per-strip
work.

| | row/map median |
|---|---|
| 0414 | 153,890 |
| 0415 (broken, 40×28) | 98,298 |
| **Repaired BG-A (41×29)** — best | **~99,000–101,000** |
| Repaired BG-A (41×29) — conservative | **~103,000–106,000** |

**Essentially all of the 0415 gain survives** (the gain came from entering-strip-only production +
the 32-word column DMA, not from under-resolving the visible window). Scroll IRQ stays well under the
0414 figure; the remaining path to a comfortable one-frame margin is BG-B (fused resolver) + BG-C
(native tables), unchanged by this correctness fix.

---

## 11. Preserve the future architecture

The root cause is a **span-by-one** error, not an architectural flaw. Keep: the accessor seam
(`MAP_GET_NAME_A/B`, `MAP_GET_COLLISION`), the eventual native map tables (BG-C), and the
incremental visual / full-span collision separation. **BG-B/BG-C must not start until BG-A visual
correctness is restored and Tighe-confirmed on real Genesis.**

---

**CODY WORKING TREE MODIFIED: NO. PRODUCTION SOURCE MODIFIED: NO. ROM BUILT: NO. BUILD NUMBER
CONSUMED: NO.**
