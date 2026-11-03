# Build 0246 — Stage 1 Plane A Pan-Y Trigger Boundary (research; no source/build)

**Agent:** Andy. **Type:** focused trigger-boundary proof.
**Production source / remap spec / ROM / build / counter:** UNCHANGED (Build 0246 / counter 246).
**Authority:** `build/rastan-direct/address_map.json` (arcade→genesis, segment-membership; **no fixed-offset
inference**), `specs/rastan_direct_remap.json`, `build/rastan-direct/rastan_direct_patch_manifest.json`,
Build 0246 ROM disassembly, arcade opcodes (`analysis/ghidra/rastan_arcade/exports/`).
**Evidence:** `states/traces/build0246_pan_y_trigger_20260801/` (`pany.lua`/`pany.txt` — Genesis Build 0246
write-tap; `segchk.lua`/`segchk.txt` — arcade column-source oracle). C08000 used **only as oracle**.
**Builds on (not repeated):** `Andy_build0246_plane_a_arbitrary_row_source_proof.md` (source proven).

## Native-hardware-replacement acknowledgement (policy §10/§12)

- **Semantic cut retained:** the arcade owns the camera/scroll decision — it writes the FG Y accumulator
  `a5@0x10B0` every frame during the settle. The native tail only reacts to that arcade-owned scroll by
  publishing the entering Plane A row from semantic ROM map source.
- **Chip tail removed:** no `0xC08000`, no name-RAM walk, no tall projector; the publisher writes final
  Genesis Plane A words to `staged_fg_buffer`.
- **No compatibility layer, no Genesis frame watcher, no scheduler.** The hook is an arcade-invoked call
  inside the arcade's own per-frame scroll arm.

---

## 1. Result summary

- **Pan-Y producer PINNED:** genesis PC **`0x0559A4`** = arcade **`0x0557A4`** (`movew d1,a5@0x10B0`),
  the **up-arm no-publish Y-scroll writer**. It is the **sole** `a5@0x10B0` writer during the pan
  (62 of 62 pan writes; the other 3 writers are one-time inits). Reached via the **selector-independent**
  no-publish path `0x055790` (branch `0x055736 bges 0x55790` on `10BA≥8`, taken *before* the `sel==2`
  check) — which is why `sel=0` yet the selector-2 arm's scroll runs. This **revises** the prior audit's
  "scripted selector-0 camera move" guess.
- **Entering-row formula proven:** increasing `visible_top` → `entering_row = (new_visible_top + 31) & 63`
  (verified: `vtop 1→2 ⇒ row 33 … vtop 22→23 ⇒ row 54` — exactly the missing band). Decreasing (down arm,
  derived) → `entering_row = new_visible_top & 63`.
- **Column source is X-scroll, NOT `a5@0x13E`:** during the pan `X-scroll(0x10AE)=0` while the stream
  counter `a5@0x13E=1` (the fill's ring cycle advanced it). The C08000 entering rows equal `E(seg=0)`,
  **not** `E(seg=1)` (discriminating samples proven). The publisher must key columns on the X-scroll base
  (=0 during pan), not the stream counter.
- **Frame ordering proven:** `0x0559A4` (scroll update) runs **before** `0x055CC4` (staged_scroll_y_fg
  staging) every frame → a row published at the hook is staged before the matching VBlank commit.
- **Highest safe hook:** the **no-publish path** genesis `0x055990` (up, arcade `0x055790`) /
  `0x055904` (down, arcade `0x055704`) — fires **only on scroll-without-publish frames**, so it fills the
  exact crossings the arcade leaves (the pan) with **no double-publish**. Byte-neutral in-place JMP.
- **STOP: not triggered.**

## 2. Address-map / remap route table

| Item | Arcade PC | Genesis PC | JSON kind | Note |
|---|---:|---:|---|---|
| Pending-direction scroll dispatcher | `0x055658` | `0x055858` | arcade_copy | reads `a5@0x10D0`, `bsr`s arms |
| Down arm entry | `0x055696` | `0x055896` | arcade_copy | bit0 of `0x10D0`; loads `10BA` @`0x05569C` |
| Up arm entry | `0x05572E` | `0x05592E` | arcade_copy | bit1 of `0x10D0`; loads `10BA` |
| **Down no-publish path (hook)** | `0x055704` | **`0x055904`** | arcade_copy | `10BA += 10DA`, → scroll |
| **Up no-publish path (hook)** | `0x055790` | **`0x055990`** | arcade_copy | `10BA -= 10DA`, → scroll |
| Down scroll store | `0x055718` | `0x055918` | arcade_copy | `10B0 = (10B0+10DA)&511` |
| **Up scroll store (pan-Y writer)** | `0x0557A4` | **`0x0559A4`** | arcade_copy | `10B0 = (10B0-10DA)&511` — 62/62 pan writes |
| Up scroll-apply call | `0x0557B2` | `0x0559B2` | arcade_copy | `jsr 0x406a4` |
| FG scroll → staged_scroll_y_fg | `≈0x055AC4` | `0x055CC4` | **patched_site** | 254 writes; runs *after* `0x0559A4` |
| Existing selector-1/2 helper site | `0x055990` | `0x055B90` | patched_site | **no collision** (distinct genesis addr) |
| Existing descriptor rebuild site | `0x055904` | `0x055B04` | patched_site | **no collision** (distinct genesis addr) |

The recommended hook genesis addresses `0x055990` / `0x055904` are `arcade_copy` and do **not** collide with
the existing patched sites at genesis `0x055B90` / `0x055B04`.

## 3. Exact pan-Y producer (Phase 1)

The per-frame **pending-direction scroll dispatcher** `0x055658`–`0x055694` reads the pending-direction
bitmask `a5@0x10D0` and `bsr`s the down arm (`0x055696`, bit0) or up arm (`0x05572E`, bit1). During the
Stage-1 settle, **bit1 (up) is set**, so the up arm runs every frame:

```
0x05572E  d1 = a5@0x10BA
0x055732  cmpiw #8,d1
0x055736  bges 0x55790          ; 10BA>=8 -> NO-PUBLISH path (selector NOT yet checked)
   0x055790  d1 = a5@0x10DA ; a5@0x10BA -= d1     ; no-publish bookkeeping   [HOOK SITE, genesis 0x055990]
   0x055798  d1 = a5@0x10B0
   0x05579C  d1 -= a5@0x10DA
   0x0557A0  d1 &= 511
   0x0557A4  a5@0x10B0 = d1      ; ★ PAN-Y WRITER (genesis 0x0559A4)
   0x0557A8  a5@0x13D0 = 1       ; direction code (1=up)
   0x0557AE  d2 = 1
   0x0557B2  jsr 0x406a4         ; apply scroll (feeds staged_scroll_y_fg downstream)
   0x0557B8  rts
```

**Writer evidence (`pany.txt`, Genesis Build 0246):** histogram of `a5@0x10B0` (0xFF10B0) writers:
`0x0559A4 count=62` (the pan), plus one-time inits `0x03A4D0/0x03B0FE/0x050718` (count=1, value 0). During
F396–F466 the sole writer is `0x0559A4`, stepping `10B0 −= 10DA(=3)`/frame from `0x1FF` to `0x149`
(`10BA` tracks it, `10CA=10CC=0` ring static, `sel=0`). **One write per frame; no bounded loop in the
writer.** The down arm is symmetric (`0x0556A4 blts 0x55704` when `10BA<256`; `0x055718` writes
`10B0 += 10DA`).

## 4. Per-crossing evidence + entering-row formula (Phase 2)

`visible_top(scy) = ((-scy + 8) & 0x1FF) >> 3 & 0x3F`. During the pan `staged_scroll_y_fg` (0xFF40EA)
decreases `0x1FF → 0x149`, so `visible_top` increases **1 → 23** monotonically (22 transitions):

| F | vtop | staged | 10B0 | sel | seg | entering_row = (new_vt+31)&63 | phys = row&31 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 400 | 1→2 | 0x1F6 | 0x1F6 | 0 | 1 | 33 | 1 |
| 418 | 7→8 | 0x1C6 | 0x1C6 | 0 | 1 | 39 | 7 |
| 442 | 15→16 | 0x187 | 0x187 | 0 | 1 | 47 | 15 |
| 458 | 20→21 | 0x160 | 0x160 | 0 | 1 | 52 | 20 |
| 466 | 22→23 | 0x14E | 0x14E | 0 | 1 | 54 | 22 |

The entering rows are **33..54** landing at physical rows **1..22** — precisely the wrong-tenant rows the
fill audit identified. **Formulas (direction-complete):**

- **Increasing `visible_top`** (camera reveals lower map, up arm): `entering_row = (new_visible_top + 31) & 63`;
  the row enters at the ring **bottom**.
- **Decreasing `visible_top`** (down arm, derived from the symmetric `0x055718` writer):
  `entering_row = new_visible_top & 63`; the row enters at the ring **top**.
- **Physical row** = `entering_row & 31` (both directions).

**Boundaries per invocation:** the pan moves `10DA=3` px/frame → at most **one** 8-px boundary per frame
(transitions every 2–3 frames; often zero). A general fall can move more per frame, so the helper needs a
**bounded loop**: `crossings = |new_visible_top − old_visible_top|`, upper-bounded by `ceil(|Δ10B0|/8)`. For
the pan the maximum is **1**; the helper should still iterate to be fall-safe.

**Column source (proven, `segchk.txt`, arcade oracle):** during the pan `X-scroll(0x10AE)=0x0000` (static)
and `a5@0x13E=1`, yet the C08000 entering-row tiles equal `E(seg_index=0)`:

```
r=40 c= 0  C08000=00CC  E(seg=0)=00CC  E(seg=1)=00BD   <- discriminates: seg=0 correct
r=54 c=63  C08000=0123  E(seg=0)=0123  E(seg=1)=007B   <- discriminates: seg=0 correct
```

So the publisher's column source is the **X-scroll-derived column base** (`=0` during the pan), **not**
`a5@0x13E`. This is the dual-axis wrapped-map convention: **columns from X-scroll (`0x10AE`), rows from
Y-scroll/`visible_top`**. Using `a5@0x13E` would read the wrong map column.

## 5. Frame-order proof (Phase 3)

Required order (all within one arcade-owned frame, before VBlank):

1. **arcade camera/scroll update** — up arm writes `a5@0x10B0` at `0x0559A4`.
2. **native entering-row staging** — hook (upstream of `0x0559A4`) → `staged_fg_buffer[row&31]`.
3. **`fg_row_dirty`** — mark the published physical row.
4. **`staged_scroll_y_fg` staging** — `0x055CC4`.
5. **arcade VBlank**; 6. **row DMA/commit**.

**Proven (`pany.txt`):** within every pan frame `W10B0 @0x0559A4` precedes `W40EA @0x055CC4`
(e.g. `F=430: 0x0559A4` then `0x055CC4`). The hook fires upstream of `0x0559A4`, so steps 2–3 complete
before step 4 (scroll staging) and step 5 (VBlank). Therefore the entering row appears with its matching
scroll position and is committed by the existing arcade-owned VBlank path.

**No legacy overwrite:** gameplay tall-FG projection is gated off for scene 1
(`vdp_project_fg_tall_if_dirty` returns when `genesis_current_scene_id==1`, per
`Cody_build0246_native_plane_a_vertical_source_proof.md`); `fg_native_gameplay_owner=1` gates the legacy FG
writers (fill audit §2). No C-window/compatibility helper becomes the row authority. **No independent
Genesis frame watcher is needed** — the arcade `bsr`s the arm each frame.

## 6. Highest safe hook boundary + byte-neutrality

**Recommended: the no-publish path** genesis `0x055990` (up, arcade `0x055790`) and `0x055904`
(down, arcade `0x055704`). Rationale:

- It fires **only on scroll-without-publish frames** (the `10BA≥8`/`<256` gate). On publish frames the
  arcade already publishes the entering row via `0x55948` → the existing selector-1/2 helper, and this
  hook does **not** run → **no double-publish**. During the pan every crossing is a no-publish crossing
  (62/62), so the hook covers them all.
- It is arcade-owned (the arm is `bsr`'d by the dispatcher each frame), upstream of the scroll store
  (so old `10B0` is still in memory and new is computable) and upstream of staging → correct ordering.
- Higher boundaries (arm entry `0x05572E`, dispatcher `0x055658`) do not cleanly expose the per-crossing
  scroll delta; lower boundaries (`0x0557A4` writer, `0x0557B2` jsr) lose the old value.

**Byte-neutrality: YES (in-place, ROM-size neutral).** The no-publish body is
`322d 10da` + (`936d 10ba` up / `d36d 10ba` down) = **8 bytes**. Overwrite the first **6** bytes at
genesis `0x055990`/`0x055904` with `jmp genesistan_plane_a_pan_publish_entering_rows_{up,down}`
(`4ef9 xxxxxxxx`, 6 bytes); the 2 trailing stale bytes are jumped over. The whole-maincpu-copy model
overwrites in place — **no bytes inserted or removed** (same discipline as the existing
`0x055968`/`0x055990` opcode_replace entries). Original bytes to record for the remap:
`0x055790: 322d 10da 936d 10ba` (up), `0x055704: 322d 10da d36d 10ba` (down).

## 7. Register / argument / return contract

Helper `genesistan_plane_a_pan_publish_entering_rows_{up,down}` (genesis_only), invoked by the in-place JMP:

- **Register preservation:** `movem.l` save/restore **every** non-owned register (`d0–d7/a0–a4/a6`);
  preserve `a5` (arcade WRAM base) and `d2` (the arm sets `d2` at `0x0557AE`/`0x055722` after the return
  point, but nothing before it depends on the helper — still save all per the Build 0240 clobber lesson).
- **Displaced work reimplemented:** `a5@0x10BA -= a5@0x10DA` (up) / `+=` (down) — the no-publish
  bookkeeping the JMP replaced.
- **Old/new scroll (both exposed, no retained state):** `old = a5@0x10B0` (memory, not yet stored);
  `new = (old ∓ a5@0x10DA) & 0x1FF`. `old_vt = vtop(old)`, `new_vt = vtop(new)`.
- **Publish:** for each crossed boundary (bounded loop), `entering_row = up ? (vt+31)&63 : vt&63`; call the
  proven `publish_plane_a_logical_row(entering_row)` (arbitrary-row proof §4) with the **X-scroll column
  base** (from `a5@0x10AE`; =0 during the pan) — **not** `a5@0x13E`. Emit final Plane A words to
  `staged_fg_buffer[entering_row & 31]`, mark `fg_row_dirty`. No collision write (arcade already owns it).
- **Logical-row argument:** `entering_row` 0..63; helper derives `seg=row>>2`, `cell=row&3` internally.
- **Direction convention:** two entry labels (up/down) fix the sign and the top/bottom insertion; or read
  `a5@0x13D0` (1=up/0=down) — but the up/down hook sites already disambiguate.
- **Return / fallthrough:** `jmp` back to the arcade scroll store — genesis `0x055998` (up, arcade
  `0x055798`) / `0x05590C` (down, arcade `0x05570C`) — which performs the real `a5@0x10B0` store and the
  normal tail (`a5@0x13D0`, `d2`, `jsr 0x406a4`, `rts`) → returns to the dispatcher. The helper does **not**
  store `10B0` itself (the arcade tail does), keeping it minimal.
- **Retained state:** none required (old/new both exposed at the hook). A helper-local `prev_visible_top`
  is **not** needed at this boundary.

**Worst-case work:** one 64-cell row = 64 × (compute `E`, deref `dp`, read tile, convert, store) ≈ the
same cost as one existing selector publication; runs in active display before VBlank, within frame budget.
Pan invocations publish ≤1 row each.

## 8. Exact Cody implementation task

1. Add `opcode_replace` entries (byte-neutral, in-place) at genesis `0x055990` (up) and `0x055904` (down)
   → `jmp genesistan_plane_a_pan_publish_entering_rows_{up,down}`, each returning by `jmp` to genesis
   `0x055998` / `0x05590C`. Record original bytes (§6).
2. Implement the helper per §7: reimplement the displaced `10BA` bookkeeping; compute old/new
   `visible_top`; loop the crossed boundaries; call `publish_plane_a_logical_row(entering_row)` with the
   **X-scroll column base** (`a5@0x10AE`), reusing the proven selector-0 `convert(tile,attr)`; write
   `staged_fg_buffer` + `fg_row_dirty`; full `movem` discipline; no collision, no `0xC08000`.
3. Gate: none needed at this site (no-publish path only fires when the arcade did not publish), but assert
   `fg_native_gameplay_owner==1` and skip if a crossing was already published this frame (defensive).
4. Validate: re-run `pany.lua` (expect the 22 pan crossings to now stage rows 33..54 into
   `staged_fg_buffer[1..22]` with `fg_row_dirty` set) and confirm the initial-fill symptom is gone; keep
   `0xC08000` oracle-only. Unifying general selector-1/2 gameplay falls is a **separate** later task.

## 9. STOP status

**STOP not triggered.** A single writer is proven (`0x0559A4`, 62/62; others one-time init); old/new scroll
are observable at the chosen boundary; no autonomous Genesis watcher is required (arcade `bsr`s the arm);
row publication completes before the matching VBlank (frame order proven); and the route needs no
compatibility state or full-window projection. The one non-trivial contract detail — the column source is
X-scroll-derived, not `a5@0x13E` — is proven, not left open.
