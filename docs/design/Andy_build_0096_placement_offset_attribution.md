# Andy — Build 0096 Placement-Offset Attribution (+16 px X / +8 px Y), per-axis

**Author:** Andy
**Date:** 2026-06-24
**Build:** 0096 (rastan-direct; H40 / 320×224 confirmed; raw scroll words zero; Layer B raw staging faithful and BG block-copy helper exonerated — none reopened)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No build. No runtime probing. Addresses via `build/rastan-direct/address_map.json` (JSON only). Hardware constants from the in-repo MAME reference (`docs/reference/mame/rastan/`). Labels: [STATIC] proven from source/disasm/reference; [ARCADE-INTENT] arcade display behavior; [GENESIS-BEHAVIOR]; [INFERENCE]; [USER-VISUAL] from the user's addition-blend overlay measurement.

---

## Phase 0 — Baseline

**Relevant priors:** KF-015 (scroll model: full-plane, documented "+8 vertical bias"; `staged_scroll_*` unwired = 0 — STRONG, central), KF-010 (FG→Plane A `0xE000`, BG→Plane B `0xC000`), KF-014 (tile preload), KF-024 (region/DIP, upright non-flipped), KF-028. **Classification:** EXTENDING (OPEN-001). **Issues:** OPEN-001 active, OPEN-016 context, OPEN-015 do-not-touch. **Contradiction:** NONE. **Architecture compliance:** CONFIRMED (eventual fix is a shared display-origin/viewport policy; no Genesis control-flow ownership). **Established facts honored, not reopened:** display H40/320×224; raw scroll words zero both sides; Layer B raw staging faithful; block-copy helper exonerated.

**Symptom under attribution** [USER-VISUAL]: the Genesis title composition sits **+16 px X (+2 cols)** and **+8 px Y (+1 row)** versus the same-ROM arcade reference (addition-blend overlay). This supersedes the earlier rough "+1/+1". The asymmetry (16 ≠ 8) is the key clue: it points at **two different constants → two different mechanisms**, not one origin.

---

## 1. X (+16 px) — CONFIRMED: un-replicated PC080SN `scrolldx = −16` [STATIC, ARCADE-INTENT]

The PC080SN tilemap chip applies a **fixed horizontal display offset** to every tilemap it draws, independent of the per-frame scroll registers. From the in-repo MAME reference:

`docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp:93–96`:
```
m_tilemap[0]->set_scrolldx(-16 + m_x_offset, -16 - m_x_offset);   // BG tilemap
m_tilemap[0]->set_scrolldy(m_y_offset, -m_y_offset);
m_tilemap[1]->set_scrolldx(-16 + m_x_offset, -16 - m_x_offset);   // FG tilemap
m_tilemap[1]->set_scrolldy(m_y_offset, -m_y_offset);
```

`m_x_offset`/`m_y_offset` default to 0 (`pc080sn.cpp:63–64`) and **Rastan never overrides them** — `rastan.cpp` references the `pc080sn` device (lines 163/184/211/251/255/256/318–321) but contains **no `set_offsets` call**. Therefore for the upright/non-flipped config (KF-024):

> **`scrolldx = −16` for BOTH tilemap[0] (BG) and tilemap[1] (FG).** [STATIC]

Meaning: the arcade draws each tilemap shifted **16 px left** of its raw nametable position. Genesis stages the raw nametable faithfully (proven) and applies **no** equivalent fixed −16 horizontal display offset (`staged_scroll_x_* = 0`, and the Genesis VDP has no scrolldx-equivalent baked in). So Genesis content lands **16 px right** of where the arcade puts it.

> **+16 px X = the un-replicated PC080SN `scrolldx = −16`. CONFIRMED.** [STATIC]
> The "−16 ≈ +16" coincidence the task flagged is **real and causal**, not a red herring. Magnitude matches exactly (−16 not applied → +16 displacement).

This is **[ARCADE-INTENT] arcade hardware display behavior**, not a Genesis staging bug. The port should **REPLICATE** the −16 horizontal display origin.

---

## 2. Y (+8 px) — CONFIRMED: un-replicated screen `visarea` Y-start = 8; REJECT PC080SN `scrolldy` [STATIC, ARCADE-INTENT]

The Y offset is attributed **independently of X** (it is NOT the X mechanism, and the X attribution above never invokes anything vertical). Two candidates were tested:

**Candidate A — PC080SN `scrolldy` (the vertical analogue of the X cause): REJECTED.** [STATIC]
`pc080sn.cpp:94,96` set `scrolldy(m_y_offset, …)` = `scrolldy(0, …)` (m_y_offset=0, not overridden). **The PC080SN applies ZERO vertical fixed offset.** So the Y offset is **not** the vertical twin of the X mechanism — they are genuinely different.

**Candidate B — screen visible-area crop at Y=8: CONFIRMED.** [STATIC]
`docs/reference/mame/rastan/src/mame/taito/rastan.cpp:450–451`:
```
screen.set_size(40*8, 32*8);                  // 320 x 256 raster
screen.set_visarea(0*8, 40*8-1, 1*8, 31*8-1); // visible = (x 0..319, y 8..247)
```
The arcade's **visible window starts at Y = 8** (one tile row down) and ends at 247 → 240 visible lines. The top 8 px (tilemap rows that render at raster Y 0..7) are **cropped off the top** by the CRT visible area. So a given piece of title art at tilemap pixel Y appears on the **arcade** screen at `Y − 8`.

Genesis (H40/320×224) displays its plane from raster Y=0 with **no** equivalent top crop. So the same art appears on **Genesis** at `Y` (8 px lower than arcade).

> **+8 px Y = the un-replicated arcade `visarea` Y-start of 8. CONFIRMED.** [STATIC]
> X is horizontal (scrolldx); Y is the vertical visible-window crop. **Never conflated.**

This is **[ARCADE-INTENT] arcade display/viewport behavior** (the CRT visible rectangle), not a Genesis staging bug. The port should **REPLICATE** the −8 vertical display origin (show content 8 px higher / crop the top tile row).

> Note on KF-015: the documented Genesis "+8 vertical bias" in the scroll model is the **same magnitude** and the **correct latent home** for this correction — but it is currently `staged_scroll_y_* = 0` (unwired). The arcade source of that +8 is precisely this `visarea` Y=8, now attributed. [INFERENCE→STATIC link]

---

## 3. One mechanism or two? — **TWO** [STATIC]

| Axis | Magnitude | Mechanism | Hardware | Reference |
|---|---|---|---|---|
| X | −16 px (+16 on Genesis) | PC080SN tilemap **scrolldx** | PC080SN tilemap chip | `pc080sn.cpp:93,95` |
| Y | −8 px (+8 on Genesis) | Screen **visarea** top crop | CRT / screen device | `rastan.cpp:451` |

The +16/+8 **asymmetry is fully explained**: the two offsets come from **two unrelated hardware facilities** that happen to both be tile-fraction-aligned (16 = 2 tiles, 8 = 1 tile). This is **NOT** one display origin with per-axis constants, and **NOT** a single off-by-N. PC080SN `scrolldy = 0` proves the X chip-offset mechanism does **not** extend to Y. [STATIC]

Consequence for the fix: **two independent per-axis corrections** (a horizontal −16 and a vertical −8), even if both are ultimately expressed through one Genesis display-origin facility.

---

## 4. Do Layer A and Layer B share the offset? — **YES, both axes** [STATIC]

- **X:** `set_scrolldx(-16, …)` is applied to **both** `m_tilemap[0]` (BG = Layer B, Plane B `0xC000`) **and** `m_tilemap[1]` (FG = Layer A, Plane A `0xE000`) — `pc080sn.cpp:93` and `:95`. Same −16 on both planes.
- **Y:** the `visarea` Y=8 crop is a **screen-wide** property — it crops the composited output of every layer identically (`rastan.cpp:451`).

> **Layer A (FG text/glyph: red TAITO logo, copyright, ALL RIGHTS, CREDIT) and Layer B (BG block-copy art: RASTAN/sword/throne) carry the IDENTICAL +16/+8 offset.** [STATIC]
> A single shared display-origin correction (−16 X, −8 Y) fixes both planes uniformly. This is consistent with the prior Build-0096 audit's "shift present on a plane the helper never writes ⇒ shared/upstream" finding — now given its exact arcade source.
> (Sprites/PC090OJ have their own separate `m_x_offset`/`m_y_offset` — out of scope here; if sprites later show a different offset, that is the PC090OJ pair, not this.)

---

## 5. Genuine Genesis bug vs arcade behavior to REPLICATE — **both are REPLICATE (viewport policy)** [INFERENCE, strong]

Neither +16 X nor +8 Y is a Genesis *staging* bug. The raw staging, cell decode (`(A0−CWINDOW_BASE)>>2 → row*128+col*2`), and VRAM commit are all **proven faithful** (prior audits). What is missing is the **arcade's fixed display origin** — the PC080SN scrolldx and the CRT visible-window crop, which the arcade applies at **display** time, downstream of the nametable.

> Both offsets are **[ARCADE-INTENT] display behavior the port should REPLICATE**, not bugs to eliminate by moving content arbitrarily. The "bug" is only that the port currently **fails to reproduce** the arcade's display origin (displays the raw nametable at Genesis origin with scroll 0). [INFERENCE]

This makes the correction a **viewport/display-origin policy decision** (a user call), not a blind nudge:
- The **−16 X** and **−8 Y** are the arcade-faithful values to bake in (well-attributed, exact).
- **Separately and still a user decision:** the **240→224 vertical extent** difference. Arcade visible height is **240** lines (Y 8..247); Genesis H40 is **224**. Even after replicating the Y=8 top crop, Genesis has **16 fewer** lines than the arcade visible window → the arcade's bottom 16 px (≈ rows 28–29, where ALL RIGHTS / CREDIT were measured staged-but-offscreen) have no Genesis scanline. The Y=8 origin replication and the 240→224 height clip are **distinct**; replicating the top crop does not create bottom room. Park the 240→224 policy for Tighe (squash, drop rows, or accept bottom clip).

---

## 6. Per-axis fix locus [STATIC-justified, mechanism-level]

The correction is a **fixed display-origin bias of −16 px X / −8 px Y, applied once to both planes**, at the display layer — **not** in the producers and **not** in the cell-decode/staging (those are faithful; touching them would un-faithful the proven staging and desync planes).

- **Natural Genesis facility:** a **fixed** horizontal and vertical scroll bias written at commit time — i.e. set `staged_scroll_x_* = +16` (content left 16 px) and `staged_scroll_y_* = +8` (content up 8 px) feeding `vdp_commit_scroll` (`vdp_comm.s:285`), which currently writes 0. KF-015's documented "+8 vertical bias" is the latent home for the Y term.
- **Critical distinction vs ESTABLISHED FACT "scroll words are zero":** the proven-zero values are the **dynamic per-frame scroll** (the arcade title scroll, genuinely 0 at the sampled state — keep wiring that to the arcade scroll source). The −16/−8 here are the PC080SN/visarea **fixed display offsets**, a **separate additive term** the arcade applies on top of the dynamic scroll. Baking in a fixed −16/−8 display bias is **NOT** "wiring a nonzero dynamic scroll word" — it is replicating the chip/screen fixed origin. The fix must add the fixed bias **without** disturbing the (correctly-zero) dynamic-scroll wiring: `applied_scroll = dynamic_scroll(=0) + fixed_bias(−16 X / −8 Y)`.
- **Per-axis independence:** X bias (−16) and Y bias (−8) are set independently (different sources), but can land in the same `staged_scroll_x_*` / `staged_scroll_y_*` commit. Both planes get the same pair.

Sign/direction check [STATIC]: Genesis content is currently +16 right / +8 down vs arcade. To align, content must move **left 16 / up 8**. On Genesis VDP, a **positive** H-scroll moves the plane content left, and a **positive** V-scroll moves it up → **H-scroll +16, V-scroll +8** (equivalently a −16/−8 display origin). Consistent with replicating arcade scrolldx −16 and visarea +8 crop.

---

## 7. Recommended next step — attribution COMPLETE; correction is a viewport-policy decision + named one-site change

Unlike the prior +1/+1 audit (which deferred the exact value to a runtime trace), the **values are now proven static** from the hardware reference (`scrolldx −16`, `visarea` Y=8, `scrolldy 0`, offsets not overridden). **No runtime trace is required to fix the X/Y origin.** What remains is a **user viewport-policy decision**, then a localized Cody implementation:

1. **Decision for Tighe (viewport policy):** REPLICATE the arcade display origin = apply fixed **−16 px X / −8 px Y** display bias to both PC080SN planes (Layer A + B). This is the arcade-faithful answer; confirm the port should reproduce the arcade visible window rather than show the raw nametable at Genesis origin.
2. **Separate decision for Tighe (parked):** the **240→224** vertical-extent policy (independent of #1; governs ALL RIGHTS/CREDIT bottom rows and any 30th-row content).
3. **Implementation (Cody, on approval):** set a fixed −16/−8 bias into the `staged_scroll_x/y_*` path feeding `vdp_commit_scroll` (`vdp_comm.s:285`), as an additive term layered on the (zero) dynamic scroll — both planes, X and Y independent. No producer/staging/cell-decode changes. No NOP/RTS scaffolding.

**Safe to implement now:** the **X/Y origin values are settled and safe** [STATIC]; what gates implementation is the **policy confirmation** (#1, and the parked #2), not missing analysis. Once Tighe confirms "replicate arcade display origin," the −16/−8 bias is a precise, single-site, both-planes change — no nudge-to-taste, no plane desync.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active — +16 X / +8 Y placement now **attributed per-axis to two arcade display mechanisms** (PC080SN scrolldx −16; visarea Y=8 crop), Layer A/B shared, fix locus named; **not closed** pending viewport-policy decision + implementation), OPEN-016 (context — fixed-bias change is small/localized, minor relocation class), OPEN-015 (not touched).
- New issues opened: NONE. Issues closed: NONE.
- Intentionally deferred: the 240→224 vertical-extent viewport policy (parked, user decision), the four missing red-TAITO Layer-A tiles (separate KF-014 preload defect), SCORE/1UP/2UP HUD producer thread (separate, not-staged), Start crash / OPEN-015 / OPEN-017, implementation (gated on policy confirmation), PC090OJ sprite offsets (separate facility, out of scope).

## KNOWN_FINDINGS impact

**Option C — proposed refinement to KF-015** (assess-only; not edited; Tighe/Chad Sr. approve). Proposed addition:

> Build 0096 placement +16 X / +8 Y attributed per-axis to **two distinct arcade display mechanisms**, both currently un-replicated on Genesis: **(X) PC080SN fixed `scrolldx = −16`** applied to BOTH tilemaps (BG `m_tilemap[0]` and FG `m_tilemap[1]`) — `pc080sn.cpp:93,95`, `m_x_offset=0` (Rastan never calls `set_offsets`); **(Y) screen `visarea` top crop at Y=8** (`set_visarea(0,319,8,247)`, `rastan.cpp:451`) — PC080SN `scrolldy = 0`, so Y is NOT the vertical twin of X. Two mechanisms, not one origin; the +16/+8 asymmetry is fully explained. Layer A (FG) and Layer B (BG) carry the **identical** offset (scrolldx on both tilemaps; visarea crops the whole screen) → one shared display-origin correction fixes both. The correct fix is a **fixed display-origin bias** of −16 px X / −8 px Y, applied as an additive term in the `staged_scroll_x/y_*` → `vdp_commit_scroll` path, **distinct from** the (correctly-zero) dynamic per-frame scroll word — replicating the arcade chip/screen fixed origin, not wiring a nonzero dynamic scroll. The documented KF-015 "+8 vertical bias" is the Y term; its arcade source is the visarea Y=8. Separately, arcade visible height 240 vs Genesis 224 clips the bottom 16 px regardless of origin (a distinct viewport-extent policy).

Confidence: **STRONG/STATIC** for both per-axis attributions (proven from the hardware reference: scrolldx −16 both tilemaps, scrolldy 0, visarea Y=8, offsets not overridden). The remaining gate is a viewport-policy decision, not analysis.

## STOP triggered

NO.
