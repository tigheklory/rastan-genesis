# Andy — Build 0096 Title Coordinate/Origin Audit (shared +1/+1 shift)

**Author:** Andy
**Date:** 2026-06-24
**Build:** 0096 (rastan-direct; BG block-copy staging baseline — not reopened)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No build. No implementation. Bounded Cody trace recommended where static cannot settle a pixel-level value. Addresses via `build/rastan-direct/address_map.json` (JSON only). Labels: [ARCADE-INTENT], [GENESIS-BEHAVIOR], [STATIC], [INFERENCE], [USER-VISUAL].

---

## Phase 0 — Baseline

**Relevant priors:** KF-015 (scroll model: full-plane, "+8 vertical bias", no per-line — STRONG; central), KF-010 (FG→Plane A `0xE000`, BG→Plane B `0xC000`), KF-014 (tile preload), KF-028, KF-004/006. **Classification:** EXTENDING (OPEN-001). **Issues:** OPEN-001 active, OPEN-016 context, OPEN-015 do-not-touch. **Contradiction:** NONE. **Architecture compliance:** CONFIRMED (eventual fix is a shared scroll/origin correction; no control-flow ownership). Build 0096 block-copy fix is **not** reopened.

---

## 1. Per-plane offset — SHARED, same on both planes

[USER-VISUAL] The ~+1 column / +1 row shift is present on **Layer A** (text/logo plane) **and** Layer B (BG block-copy art). [STATIC] The new `genesistan_hook_tilemap_bg_blockcopy` writes **only** `staged_bg_buffer` (Layer B); it never touches Layer A. **A shift present on a plane the helper never writes cannot originate in that helper** → the bias is shared/upstream. Quantified offset is equal on both planes per the user overlay (the static evidence below explains why it must be equal — both planes traverse the identical decode + commit + scroll(=0) display path).

---

## 2. Arcade `0xC00328` → row/col → Genesis (math) [STATIC]

PC080SN BG C-window: cell index = `(A0 − 0xC00000) >> 2` (each cell = one longword), `col = idx & 0x3F`, `row = (idx >> 6) & 0x1F`.
`0xC00328`: `idx = 0x328 >> 2 = 202 (0xCA)` → **col 10, row 3** → Genesis `staged_bg_buffer` offset `row*128 + col*2 = 0x194`.
**Genesis nametable cell = (row 3, col 10) — IDENTICAL to the arcade cell. No +1/+1 in the address decode.** [STATIC]

---

## 3. `bg_fill` vs `blockcopy` math — IDENTICAL → shared, not helper [STATIC]

`genesistan_hook_tilemap_bg_blockcopy` (`tilemap_hooks.s:564`) per-cell decode:
```
subi.l #ARCADE_PC080SN_CWINDOW_BASE_BG, %d6 ; lsr.l #2,%d6
... col = %d6 & 0x3F ; row = (%d6 >> 6) & 0x1F ; offset = row*128 + col*2
```
This is **byte-for-byte the same** destination-to-cell math as the proven-correct `genesistan_hook_tilemap_bg_fill` (`subi #BASE_BG; lsr #2; col=&0x3F; row=>>6&0x1F; offset=row*128+col*2`) and the FG store helper `0x70794` (`row<<7 + col*2`). **No per-helper coordinate offset exists.** Equal math + equal shift on both planes ⇒ the bias is **SHARED/upstream**, not a Layer-B helper contributor. [STATIC]

---

## 4. Layer A producer + origin rule [STATIC + JSON]

Layer A content (large red TAITO logo, copyright, ALL RIGHTS, CREDIT) is rendered by the glyph/text-writer path: arcade `0x03BB48` → **Genesis `0x03BD48`** (SEG#106 patched_site) → FG store helper `0x70794`, staging into `staged_fg_buffer` with the **same** `row*128 + col*2` cell math and the same `(A0 − CWINDOW_BASE) >> 2` decode. (BG block-copy: arcade `0x05A4DE` → Genesis `0x05A6DE`, SEG#172 patched_site.) **Layer A shares the identical origin rule with Layer B** (decode → staged buffer → commit → display). So a shared display-origin offset hits both equally. [STATIC]

---

## 5. Where a shared +1/+1 can enter — ranked

- **(D/E) Shared scroll/display origin — STRONGEST [STATIC].** `staged_scroll_x_bg/fg` and `staged_scroll_y_bg/fg` are `.bss` and **never written by any producer** (no writers found in source) → `vdp_commit_scroll` writes **0** to HSCROLL and VSRAM for both planes. So the arcade's scroll/window origin (KF-015: arcade scroll from A5 `0x10EC/0x10EE/0x10AE/0x10B0`, "+8 vertical bias"; arcade scroll-register writes `0xC20000`/`0xC40000`) is **not applied on Genesis**. Both planes therefore display from nametable cell (0,0) instead of the arcade's scrolled visible-window origin → a uniform tile shift on both planes, presenting as a clean +1/+1. [STATIC for "scroll=0"; the resulting shift is INFERENCE pending the exact arcade scroll value.]
- **(A) Per-producer — RULED OUT [STATIC]:** identical math across helpers; shift present on Layer A which the new helper never writes.
- **(B) Shared PC080SN address decode — present but FAITHFUL [STATIC]:** `(A0−base)>>2 → (row,col)` is correct (§2); shared but not the +1/+1 source.
- **(C) Shared staging→VDP commit origin — FAITHFUL [STATIC]:** `vdp_commit_bg/fg_strips` write staged row R → `VRAM_PLANE_BASE + R*128` (= nametable row R), 64 cells/row. No +1.

---

## 6. Viewport clip vs origin bias (offscreen ALL RIGHTS / CREDIT)

[INFERENCE] Two independent effects can coexist:
- **Coordinate-origin bias (+1 row down):** the same shared display-origin offset that shifts everything down would push the lowest title rows below the visible area.
- **True 240→224 clipping:** arcade Rastan is 320×**240** (30 tile rows); Genesis H40 is 320×**224** (28 rows). The arcade's bottom 16 px (rows 28–29) have **no** Genesis scanlines regardless of origin.
ALL RIGHTS / CREDIT being staged-but-below-boundary is consistent with **either or both**. Distinguishing requires the staged row index of those cells vs the 28-row visible window — a bounded trace (§8). Do not assume one; they compound.

---

## 7. SCORE / 1UP / 2UP (top line) [STATIC-limited → trace]

Static analysis cannot confirm from the title state machine alone whether the top HUD line is (a) not staged at all (a separate HUD producer/lane) or (b) staged above the visible boundary. Note: a **downward** origin bias would move the top line *down* (more visible), so a *missing* top line is more consistent with **not staged** (separate HUD path) than with the +1/+1 bias. This is flagged for the trace, not concluded.

---

## 8. One-based vs zero-based [STATIC]

A clean +1/+1 is the classic one-based-vs-zero-based signature, **but** the cell decode (§2) and the commit (§5C) are 0-based and faithful — the +1/+1 is **not** in the cell indexing. It is in the **display origin** (the arcade's scrolled visible-window origin vs Genesis displaying the nametable from cell (0,0) with scroll=0). So the symptom presents as a clean +1/+1 while the root is a viewport/scroll-origin policy difference, not an index off-by-one.

---

## 9. Cause classification — **SHARED: display/scroll-origin**

[STATIC + INFERENCE] The +1/+1 is a **single shared upstream cause**: the arcade scroll/window origin is not translated (`staged_scroll_* = 0`), so both planes display from the nametable origin instead of the arcade's scrolled origin. It is **not** per-producer, **not** the cell decode, and **not** the commit origin (all proven faithful/identical).

---

## Recommended next step

**Do NOT touch `genesistan_hook_tilemap_bg_blockcopy`** — it is byte-identical to the proven `bg_fill` and faithfully decodes coordinates; "fixing" it would desync the planes and mask the shared cause (per Correction 1).

The shared fix lives at the **scroll/display-origin layer** (`staged_scroll_x/y_*` are unwired to 0; the arcade scroll/window origin is not applied). **Static analysis is sufficient to (a) confirm the cause is shared, (b) exonerate the helper, and (c) name the layer — but NOT to fix it blind**, because the exact origin value and mechanism (apply arcade scroll vs a fixed viewport-origin policy vs whether the arcade title scroll is even non-zero) depend on runtime values. **Recommended bounded Cody trace:**
1. At the steady title state, read `staged_scroll_x/y_bg/fg` (confirm all 0).
2. Read the arcade scroll source — A5 `0x10EC/0x10EE/0x10AE/0x10B0` (KF-015) and whether arcade writes to `0xC20000`/`0xC40000` are hooked to `staged_scroll_*` or dropped.
3. Measure the exact on-screen offset (is it exactly 8 px / 8 px = 1 tile, confirming the scroll-origin hypothesis, or another value?).
4. For ALL RIGHTS / CREDIT and the top SCORE line: capture their staged row indices vs the 28-row visible window to split origin-bias from 240→224 clipping and to classify the HUD line.

The fix that follows is **one upstream scroll/origin correction** (apply the arcade scroll origin into `staged_scroll_*`, or set the shared display origin) affecting both planes uniformly. **Safe to implement now: NO** — pending the trace to fix the exact origin value without nudging-to-taste or desyncing planes. The 240→224 viewport policy, if it contributes, is a separate user decision (park).

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active — +1/+1 shift attributed to a shared display/scroll-origin gap, helper exonerated; not closed), OPEN-016 (context), OPEN-015 (not touched).
- New issues opened: NONE. Issues closed: NONE.
- Intentionally deferred: the 4 missing red-TAITO Layer-A tiles (attribute-only, separate lane), high-score-table mechanism (note-only), Start crash/OPEN-015/OPEN-017, preload/LUT, the Build 0096 block-copy fix, exact origin value (→ trace), implementation.

## KNOWN_FINDINGS impact

**Option C — proposed refinement to KF-015** (assess only; not edited; Tighe/Chad Sr. approve). Proposed addition:

> Build 0096: `staged_scroll_x/y_bg/fg` are `.bss` and never written by any producer, so `vdp_commit_scroll` applies scroll 0 to both planes — the documented arcade scroll/window origin ("+8 vertical bias", A5 `0x10EC/0x10EE/0x10AE/0x10B0`) is **not translated**. Both Plane A and Plane B therefore display from nametable cell (0,0) rather than the arcade's scrolled origin, producing a shared ~+1 col / +1 row title shift. The per-cell decode (`(A0−CWINDOW_BASE)>>2 → row*128+col*2`) and the staged→VRAM commit are faithful and identical across `bg_fill`, `bg_blockcopy`, and the FG text store; the shift is a shared display-origin gap, not a per-helper offset. Separately, arcade 320×240 vs Genesis 320×224 (28 rows) clips the bottom 2 tile rows regardless of origin.

Confidence: STRONG that the cause is shared display-origin and the helper is exonerated; the exact origin value/mechanism is WORKING_HYPOTHESIS pending the §8 trace.

## STOP triggered

NO.
