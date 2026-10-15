# Build 0425 — Enemy-Load Cost Attribution (Andy)

**Date:** 2026-10-14 · **Type:** READ-ONLY diagnostic. No production source, no ROM, no Build 0426,
no Phase D/E. Does not overlap Cody's arcade Silver Standard.

**Evidence basis (stated honestly up front):** The **top-level enemy-induced delta is MEASURED** —
Cody's controlled Build-0414 trace (retained in 0425; the sprite/gameplay worker path is unchanged
between 0414 and 0425, which only touched Plane-A background) gives quiet/static IRQ median **72,593**
→ one-enemy/static **87,443** = **+14,850 cyc** for **~10 emitted pieces**. The **per-category split
within that delta is STATIC-ESTIMATED** from the actual executed routines, anchored to the measured
total and the measured worker slope `≈ 55,600 + 2,609×emitted` (0414 HEAVY). I did **not** run a fresh
per-category breakpoint trace in this task; every category cycle figure below is marked MEASURED,
EST (static estimate + range), or UNKNOWN. The exact confirming trace (ready-made `profile_*`
breakpoints) is specified for Cody at the end — those PC hooks already exist in `pc090oj_hooks.s`.

---

## Scene

- **Location:** early Round-1 / Phase-1 horizontal-scroll stretch (the controlled 0414 enemy-static
  comparison; reproducible, simple horizontal camera, stable background selector).
- **Enemy type(s):** common R1 ground/air enemies — **lizardman** (usage bank 0x36), **small/large
  bat** (0x3E). All three are in the **proven native direct-dispatch set**
  (`verify_pc090oj_direct_dispatch.py:17-19`), so they exercise the native frame path, not the
  fallback.
- **No-enemy control:** horizontal scroll, no active renderable enemy (static camera, background
  stable) — 72,593 cyc.
- **Enemy-active control:** same scrolling/background state, one active enemy (~10 pieces) — 87,443.
- **Matched background state:** YES (same selector/scroll; the 0414 comparison was constructed to
  isolate the actor delta; background is unchanged between controls).

## Total cost

- No-enemy worker cycles: **72,593** (MEASURED, median)
- Enemy-active worker cycles: **87,443** (MEASURED, median)
- **Enemy-induced delta: +14,850 cyc** (MEASURED) for ~10 emitted pieces → ~**1,485 cyc / emitted
  piece** incremental (includes fixed per-actor + per-appearance finalize/DMA, so later/more enemies
  cost somewhat less per piece).
- Percentage increase: **+20.5%** for one enemy. (One enemy stays well under the 128,009 budget;
  overrun requires dense multi-enemy frames and/or scroll combined.)

## Enemy delta breakdown (STATIC-ESTIMATED, anchored to +14,850)

| Category | Cycles (EST) | Share | Basis |
|---|---|---|---|
| Gameplay AI / state machine (arcade) | ~1,000–2,500 | 10–25% | one actor's retained state-machine tick + movement; modest |
| Gameplay collision / physics | ~300–1,000 | <10% | `collision_map_lookup_53a2e` is cheap arithmetic + one 64×64-map read per probe; few probes |
| Animation / frame selection | ~300–800 | <10% | reads `a4@0x01/0x0B`; folded into the generic-frame classify |
| **Native sprite dispatch (classify + per-piece emit)** | **~5,000–8,000** | **35–55%** | `.Lnative_generic_frame_try` base-LUT + usage-descriptor validate (once/actor) + per-piece `.Lngft_emit` loop (×~10) + `native_sprite_emit_fast` |
| Fallback interpreter (`.Lnative_emit_actor_common`) | **~0** | **0%** | NOT exercised for lizardman/bats (native proven set) |
| Residency (resolve + worklist) | ~1,000–2,500 | 10–25% | per-piece `fg_cache_resolve`/reverse-map; mostly cheap resident hits once patterns loaded; new-pattern enqueue only on first appearance |
| SAT construction | ~1,000–2,000 | 10–20% | per-piece lane append; scales with pieces, small per piece |
| Sprite DMA preparation (CPU) | ~500–1,500 | <15% | worklist build; actual transfer is in VBlank publication |
| Background | ~0 | 0% | matched/unchanged between controls |
| Publication (incremental) | UNKNOWN | — | SAT DMA is ~fixed; one-time pattern DMA on first appearance (VDP occupancy, not worker CPU) |
| Other | UNKNOWN | — | — |
| **TOTAL** | **14,850** | **100%** | MEASURED total |

**The delta is dominated by sprite PRESENTATION** (dispatch + per-piece emit + residency + SAT + DMA
prep ≈ 65–85%), not by enemy gameplay/AI/collision (≈ 15–35%). The presentation cost scales with
emitted pieces (~10/enemy).

## Fallback status

- **`.Lnative_emit_actor_common` exercised: NO** for common Round-1 enemies. Lizardman/bats are in the
  proven direct-dispatch set, so `.Lnative_generic_frame_try` returns a hit and the wrapper restores
  and returns before reaching the retired fallback. **The UNRESOLVED fallback is NOT the cause of the
  common enemy-load cost.** (Confirm with a zero-hit breakpoint at `profile_native_actor_return`
  vs `profile_native_levelb_success` during R1 gameplay.)
- Actors/frames: n/a (not hit). Cycle impact: ~0.

## AI question

- **Enemy AI itself a major cost: NO / MODERATE.** One enemy's arcade state-machine + movement is a
  modest retained tick (EST 10–25% of the delta). **Reason:** the arcade enemy logic is inherently
  small per actor; collision is a cheap arithmetic lookup. **DO NOT NATIVIZE GAMEPLAY FOR
  PERFORMANCE** — the retained arcade AI/collision is not the lever (no evidence of expensive
  translated call overhead or memory-indirection hot path for a single common enemy). If a dense
  multi-enemy trace later shows AI scaling badly, revisit; current evidence says no.

## Sprite question

- **Sprite presentation larger than AI: YES** (presentation ≈ 65–85% of the delta vs AI/collision
  ≈ 15–35%).
- **Largest sprite cost:** the native per-piece path — `.Lnative_generic_frame_try` classify + the
  per-piece emit loop + `native_sprite_emit_fast`, scaling with ~10 pieces/enemy. Residency and SAT
  are secondary (cheap per piece but × pieces).

## DMA question

- **Enemy load primarily adds: CPU WORK.** The incremental 14,850 is 68000 computation (classify +
  per-piece expand + residency resolve + SAT build + worklist prep). Actual VDP DMA occupancy
  increases only by (a) the SAT DMA (≈ fixed, published in VBlank) and (b) a **one-time pattern DMA
  on an enemy's first appearance** (when its patterns are not yet resident) — not a steady-state
  per-frame transfer for a resident enemy. **Evidence:** residency is dominated by cheap resident
  hits once loaded; the worker slope is a CPU-cycle slope (`2,609×emitted` is worker cycles, not DMA
  words).

## Next nativization opportunity

- **#1 — Sprite presentation per-piece cost (dispatch + per-piece emit + residency hoist).** Payoff:
  **MEDIUM.** Classify as **ALGORITHMIC OPTIMIZATION POSSIBLE** (already native, but per-piece): hoist
  the per-actor-invariant residency/variant-group lookup out of the per-piece loop; consider batching
  the SAT lane append. Lowers the ~1,485/piece slope → raises the enemy-count headroom before
  overrun.
- **#2 — Residency per-piece resolve (`fg_cache_resolve` / reverse-map).** Payoff: **LOW–MEDIUM.**
  ALGORITHMIC (hoist per-actor; cache the resident base for an actor's code group). Mostly cheap hits
  already.
- **#3 — SAT construction.** Payoff: **LOW.** ALREADY NATIVE / INHERENT WORK — scales with sprite
  count; little to cut beyond batching.
- (Gameplay AI/collision: **ALREADY NATIVE / INHERENT**, cheap — not an opportunity.)

## Scheduler implication

- **Would further local optimization materially reduce the remaining overrun before Phase D/E?
  PARTLY.** Reason: the per-enemy delta is modest (one enemy fits budget comfortably: 87,443 <
  128,009). Local presentation optimization **raises the enemy-count threshold** before a dense frame
  exceeds budget — useful headroom — but it does **not** change the fact that an over-budget frame
  **tears / `_do`-blanks** instead of degrading to slowdown. That tearing behavior is the
  **worker-inside-IRQ6** architecture (per the post-0425 study), which only Phase D (WORK/READY/
  DISPLAYED) + Phase E (worker to mainline) fixes. No single local category, if optimized, removes the
  overrun; the biggest local category (presentation) is already substantially native.

## Recommendation

- **NEXT IMPLEMENTATION TARGET:** **Phase D/E scheduling (worker out of IRQ6)** is the strategic lever,
  because (a) one enemy fits budget, (b) the overrun under load manifests as *tearing*, which is a
  scheduler property not a computation property, and (c) the largest local cost (sprite presentation)
  is already native with only algorithmic trims left. An **optional short pre-Phase-D closure** is the
  **#1 sprite-presentation residency/variant hoist** (MEDIUM, raises headroom), but it is not required
  to make a single-enemy frame fit.
- **DO THIS BEFORE PHASE D: NO** (optional). The attribution shows no local category whose fix removes
  the overrun; proceed to Phase D/E, optionally preceded by the small presentation hoist.

---

## Confirming trace recipe for Cody (the measured per-category split this task estimated)

The exact PC breakpoints already exist as globals in `pc090oj_hooks.s` — bracket each with the
established debugger-cycle method (KF-088): `cpu.debug:bpset(pc,"1",'printf "...",totalcycles; g')`,
drained from the console log, zero added cycles. Per-enemy category = (exit − entry) summed over the
frame:
- **Dispatch+classify:** `profile_native_levelb_entry` → `profile_native_levelb_success` /
  `profile_native_levelb_miss`.
- **Per-piece emit:** count `profile_native_levelb_piece` hits × and bracket `native_sprite_emit_fast`
  / `native_sprite_fast_context`.
- **Fallback (expect 0):** `profile_native_actor_entry` reaching past `profile_native_levelb_*` into
  the fallback tail (`profile_native_actor_return` without a levelb success).
- **Gameplay AI/collision:** bracket the arcade enemy update + `collision_map_lookup_53a2e` (0x53A2E)
  entry/exit.
- **SAT/residency/DMA-prep:** bracket the finalizer (`pc090oj_native_emit_pass`) and the sprite
  worklist/DMA sites.
Run matched no-enemy (Control A) vs one-enemy (Control B) vs two-enemy (Control C) reproducible
states (save state or deterministic input; **do not** patch out enemy code). Subtract A from B/C per
category. This converts every EST row above into MEASURED and confirms the 0% fallback.

---

**PRODUCTION MODIFIED: NO. ROM BUILT: NO. BUILD NUMBER CONSUMED: NO. PHASE D STARTED: NO. PHASE E
STARTED: NO.**
