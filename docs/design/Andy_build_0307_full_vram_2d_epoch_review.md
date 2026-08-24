# Andy — Build 0307 Full-VRAM / 2D-Epoch Independent Review

**Type:** independent architecture review. No production change, no ROM, Build 0307 not consumed.
Baseline: Build 0306 (`7d3ab8da…c2c08`). Reviews the held Cody Build-0307 prompt (full-VRAM +
2D-handoff-union).

## Verdict: **B — SEND AFTER SPECIFIC REVISIONS.**
The capacity reclaim is real but must be **sprite-peak-bounded**, and the rope fix must be **driven by
a proven owner/mechanism**, not a blanket source-handoff union. Two of Tighe's problems have **two
different root causes** and the held prompt conflates them.

---

## The decisive split: drops vs the rope are different bugs
`boundary_report.json` `packages_detail`: **`droppedA == 0` in every one of the 170 packages**;
only Plane B ever drops (22 packages, max 315 @ rec11 var0). Therefore:
- **Problem 1 (drops despite idle VRAM) is Plane-B-only** — a capacity-policy issue.
- **Problem 2 (rope vanishes on approach/climb) cannot be a drop** — nothing Plane-A is ever dropped,
  and Plane B drops resolve to blank, not to the "still-there-then-gone" the rope shows. The rope is a
  **2D-handoff/envelope** failure, not a VRAM-capacity failure. More VRAM alone will not fix it.

---

## Q1 / Q13 — Is 64..1023 a hardware limit? **NO — project policy.**
Runtime VRAM layout (`vdp_comm.s`): `VRAM_PLANE_B_BASE=0xC000`, `VRAM_PLANE_A_BASE=0xE000`,
`VRAM_HSCROLL_BASE=0xFC00`, SAT via reg 5. Pattern data lives below the Plane-B name table, i.e.
**slots 0..1535 (0x0000..0xBFFF) are physically pattern-capable** (1536 slots).
- Name-word pattern index = **`0x07FF` (11 bits → slots 0..2047 addressable)**; attribute mask
  `0xF800`. Report confirms `pattern_index_mask=0x07FF`, `attribute_preservation_mask=0xF800`.
- **No hidden 10-bit truncation:** every `andi.w #0x3FFF,%d3` in `tilemap_hooks.s`/`fg_tile_cache.s`
  masks the **arcade code before LUT lookup**, never the resolved slot; resolved slots keep attr bits.
  So slots **1024..1535 are fully representable by plane name words.**
- The `slot_last = 1023` / 960-slot cap is purely the **allocator policy**, not hardware.

**Answer: 64..1023 is POLICY. Physical pattern ceiling = slot 1535 (0xC000).** Reclaimable region =
1024..1535 (currently sprite-reserved), *conditional on sprite need*.

## Q2 / Q11 — What does PC090OJ actually use? **Reservation is a 512-slot cache, actual peak unproven.**
`pc090oj_hooks.s`: `SPRITE_TILE_BASE=1024`; comment "VRAM cells (tiles 1024..1535)";
`sprite_tile_resident_code: .space (128*2)` = **128 resident codes → up to 512 Genesis patterns**
(16×16 = 4 patterns each). So 512 is the **cache capacity**, not a proven simultaneous Stage-1 peak.
The actual max simultaneous Stage-1 sprite-pattern count depends on the enemy/spawn model, which is
**deferred/unresolved** in this project and **cannot be established statically here**. **Do not assume
all 512 are needed, and do not assume all 512 are reclaimable.** This must be measured before the plane
ceiling is raised into the sprite band.

## Q3 — Can zero drops fit physically? **Plane A: already yes. Plane B: only if sprite peak ≤ ~197.**
- Peak zero-drop **plane** requirement = current cap 960 + max Plane-B drop 315 = **~1275 slots**
  (rec11; deduped combined A∪B). (Whole-Stage-1 identity vocabulary = 2708, not simultaneously live.)
- Available below 0xC000 after the reserved low 64 = slots 64..1535 = **1472**.
- Zero-drop needs `1275 + sprite_peak ≤ 1472` → **`sprite_peak ≤ 197`**. Notably `1472 − 1275 = 197`,
  and the current deficit `1275 + 512 − 1472 = 315` **equals the max drop exactly** — i.e. today's
  drops are precisely the sprite reservation squeezing Plane B. **Zero-drop is achievable iff the true
  Stage-1 sprite peak is ≤197; if sprites genuinely need ~512, zero-drop does NOT fit** and either
  interval-splitting or reclaim-after-measurement is required. This is the pivotal unmeasured number.

## Q7 — Is the Y-variant model valid for a 2D game? **NO — proven gap.**
Compiler: ordinary records compile **8 Y-variants** (`base_row ∈ {0,8,…,56}`), each a **40-row band**
(36-row core + 2 margin/side), out of the 64-row Plane-B map; vertical records 17/21 use the **full 64
rows**. Runtime: `fg_boundary_install` is invoked **only at the record-boundary hook** (`0x013E`
increment) and post-reseed — **there is no within-record, Y-triggered re-selection.** Therefore the
selected 40-row band is **frozen between X record boundaries**. A player who moves vertically far
enough inside one ordinary record (climbing a rope) **escapes the compiled band** — the newly visible
Plane-B rows fall outside `base_row..base_row+40` and render blank/wrong. The 36-row core tolerates
only ~one 64px Y-class + 16px margin; a rope climb is hundreds of px. **This is a real architectural
gap and the most likely rope mechanism**, and it exactly matches Tighe's "especially when X and Y are
crossed at ~the same time" (the Y class only ever re-selects at an X boundary).

## Q5 / Q6 — Rope owner / mechanism: **owner NOT definitively provable statically; mechanism most
likely Plane-B Y-envelope escape.**
Design history groups "**Plane A, collision, rope**" and notes "BG has no collision channel"
(`Andy_build0247_*`), so the rope's **collision** is Plane A. Its **visual** owner (Plane A tiles,
Plane B backdrop tiles, PC090OJ sprite, or composite) is **not proven from static data** and the
symptom (vanish on Y crossing, which only Plane B has variants for) points at **Plane B** or a
**composite**. I did **not** infer it visually and I could not close it statically. **This must be
proven by a bounded Genesis-MAME observation of the exact transition** (last-good vs first-missing:
record, Y-variant, world Y, physical slot, whether an install fired, whether X record and/or Y class
changed) **before** committing to a fix — precisely as the prompt itself demands.

## Q8 — Is the 2D transition graph complete? **Complete for X boundaries; the gap is the absence of any
within-record Y transition, not a missing edge.**
`legal_edges` = self-loops ∪ {adjacent record R→R+1 for **every** `old_variant × new_variant`}. So
diagonal **X+Y** boundary transitions (V→V±1 on a record change) **are** modeled (1354 edges). What is
missing is a **within-record Y re-selection mechanism at all** — so the failure is not an absent graph
edge, it is that pure vertical movement produces **no transition**.

## Q9 / Q10 — Do we need a handoff set? **Not the held source-handoff union. HYBRID, mostly Y-envelope.**
- The held design (destination ∪ still-visible source identities ∪ immediate 2D envelope) fixes
  **X-retention / destination-absent** cases. That is the right tool **only** for a proven
  destination-absent Plane-A/B identity.
- The dominant proven gap (Y-envelope escape) is **not** fixed by a source union — the escaped rows
  were never in *either* the source or destination band. It needs one of: **(a)** re-select the
  Y-variant at an **existing arcade Y-progression event** (not per-frame polling), or **(b)** a
  **wider / true-2D Y envelope** for ordinary records that legally permit vertical travel (as vertical
  records 17/21 already do with full 64 rows), applied **selectively** where climbable geometry exists.
- **Recommended model: HYBRID** — keep stable-slot boundary remap; add **within-record Y handling**
  (event-driven re-select or selective wider Y envelope) as the primary rope fix; reserve source-handoff
  overlap only for any *proven* destination-absent identities.

## Q12 — Canonical identity / stable slot: **keep.** Exact 32-byte dedup, deterministic code→identity,
plane sharing (shared PC080SN character ROM makes code identity plane-independent), and stable-slot
retention remain correct. Widening the slot range does not affect index width (0x07FF already covers it).

## Q14 / Q15 — Sprite coexistence & Exodus. Prefer **reclaiming holes while leaving live sprite slot
numbers unchanged** (raise the plane ceiling only up to `sprite_live_base`, keeping SAT/pattern indices
coherent). The Exodus "unused" pattern area is plausibly the **under-filled 1024..1535 sprite band**
plus slack in lighter packages — but whether it is *reclaimable* depends entirely on the unmeasured
sprite peak (Q2); it must not be treated as free until that peak is bounded from sprite ownership, not
screenshots.

---

## Required revisions to the held Cody Build-0307 prompt (verdict B)
1. **Capacity:** Raise the allocator ceiling from 1023 toward 1535 **bounded by the proven Stage-1
   sprite-pattern peak**, not a blanket 512 reclaim. First establish that peak from sprite ownership;
   add a compile assertion `plane_top < sprite_live_base ≤ 1536`. Name words already permit it (0x07FF).
2. **Rope:** **Do not implement a source-handoff union first.** Require a bounded Genesis observation
   proving the rope owner and failure class. If (as evidence indicates) it is **Plane-B Y-envelope
   escape**, fix with **event-driven within-record Y re-selection** or **selective wider/2D Y envelope**
   for climb-legal ordinary records — never per-frame polling. Use handoff-overlap only for proven
   destination-absent identities.
3. **Capacity-after-2D:** Compute the hardest transition as **full Plane A + wide-Y Plane B + sprite
   peak − dedup** and compare to 1472; accept **selective** Y widening if the global case does not fit.
4. **Keep unchanged:** no-per-frame residency, canonical 32-byte identity, stable-slot allocation,
   boundary-only remap/recommit, 0x07FF name words.

## What I could not prove statically (must precede implementation)
- The exact **rope visual owner** (Plane A vs B vs sprite vs composite).
- The true **Stage-1 simultaneous sprite-pattern peak** (gates how much VRAM is really reclaimable and
  whether zero-drop fits).
Both are bounded, single-observation questions — resolve them, then compile statically (0 trace deps).
