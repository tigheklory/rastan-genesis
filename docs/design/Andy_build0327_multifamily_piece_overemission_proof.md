# Build 0327 — Multi-Family Sprite Piece Over-Emission: Root-Cause PROOF

**Type:** Analysis / static proof. No ROM, no implementation. Classification: **EXTENDING**. Baseline Build 0327.
**Result: ROOT CAUSE PROVEN, shared across families, via static descriptor decode + arcade reference.** No Tighe trace required.

## 1. Phase 0
Priors/hazards: corrects/extends the Build-0328 STOP. Deferred (untouched): `(code,bank)` color, vertical-fill/noise, HUD/axe, waterfall anim. Contradiction status: none.

## 2. Corrected user evidence (all reconciled below)
Two lizardmen ~42px apart = **two legitimate actors** (correct). The defect is **per-actor over-emission of extra pieces**: one lizardman shows much of a *second animation pose* overlaid; others show a duplicated lower-left cell. Exodus outline offset = stacked-sprite diagnostic, not a real coordinate shift.

## 3. Arcade end-of-representation rule — PROVEN: `0xFF` terminator
The lizardman (family 0, class 0x17) descriptor @ genesis `0x3D7EB` decodes as a **sequence of poses, each terminated by control byte `0xFF`**:
- pose 0: ords 0–7 (8 pieces, codes +0x1B/0x19/0x03/0x01/0x1A/0x18/0x02/0x00, two columns X=0 and X=−16), **`0xFF`** at ord 8.
- pose 1: ords 9–16 (8 pieces, codes 0x1E/0x1C/…), **`0xFF`** at ord 17.
- pose 2: ords 18+…
The arcade expander (`actor_four_record_expand_3c902` / helper `FUN_0003c606`) compares the control byte to `0xFF` (`0x03C60A: cmpi.b #0xFF`) and **returns** (`0x03C634: rts`) — i.e. **`0xFF` ends the current representation.** So the arcade emits exactly the current pose (8 pieces for the lizardman) and stops.

## 4. Genesis piece-budget semantics — PROVEN: destination capacity used as source count, `0xFF` mis-handled
`.Lnea_dloop` (`emit_actor_common`) reads a control byte; on `0xFF` it branches to `.Lnea_dnext` (**skip — emit nothing, but continue**) and loops **exactly `d2` (budget) iterations**, with **no terminator**. The budget is assigned per lane by the callers and is the **arcade PC090OJ destination-slot capacity** — proven because the "advance-only" path does `adda #(budget*8), a1` on the `0x00D00460` destination pointer. `.Lns41_enemy` budget = **10**, special-cased to **19 for slot 8** (`cmpi #8,%d5; moveq #19`). Middle lane = 4, effect = 1, players = 13.
**Semantic mismatch (proven):** the arcade stops at the `0xFF` pose terminator; Genesis treats `0xFF` as a skip and runs to the fixed destination-capacity budget, **over-reading into the next pose(s)** whenever `pose_len < budget`.

## 5. Lizardman proof (exact)
Legitimate pose = **8 pieces**. Genesis emits `budget` iterations:
- **Slot 8 (budget 19):** ords 0–7 (pose 0, 8) + `0xFF` skip + ords 9–16 (**pose 1, 8 pieces = a different animation frame**) + `0xFF` skip + ord 18 (1 piece of pose 2) = **17 emitted, 9 excess (+112%)** → "first lizardman rendered twice in a different animation position." **§8 = YES, PROVEN.**
- **Budget 10 (other slots):** ords 0–7 (pose 0) + `0xFF` skip + ords 9–10 (**pose 1 pieces 0,1**, codes 0x1E/0x1C at X=0 left column) = **10 emitted, 2 excess** → the duplicated **lower-left** cell(s). **§9 = SAME MECHANISM, PROVEN.**

## 6–10. Results
- **Adjacent animation pose:** YES — the excess pieces are literally the next `0xFF`-delimited pose in the descriptor.
- **Lower-left duplicated cell:** SAME MECHANISM (the first 1–2 pieces of the next pose, left column).
- **Exodus outline displacement:** stacked sprites at effectively the same Genesis coordinates (the excess pieces use the actor's base X/Y + the next pose's local offsets); not a genuine 1px shift.
- **Paired-actor exclusion:** the two 42px-separated records are legitimate separate actors; the over-emission is intra-record (descriptor over-read), not the paired-actor mechanism. Distinct.

## 11–12. Cross-family generalization — SHARED DEFECT (PROVEN)
`.Lnea_dloop` is the **single shared emit loop** for every family (via `emit_actor_common`), and the `0xFF`-terminated pose format is **shared** (verified: family 0 classes 0x17/0x18=8-piece, 0x1C=10-piece, 0x70=4-piece; family 2 classes 0x0B=4-piece, 0x13=1-piece — all `0xFF`-terminated). So **all families pass through the same broken loop**; visible severity = `budget − pose_len`:

| Family (R1/P1) | Same shared path? | Arcade end preserved? | Over-read structurally possible? | Predicted symptom |
|---|---|---|---|---|
| Lizardman | YES | NO | YES (pose 8 < budget 10/19) | 2 stray cells; **full 2nd pose on slot 8** |
| Valkyrie / Chimera / Flying Demon / Four-Armed Insect | YES (shared loop) | NO | YES where pose_len < its lane budget | varies: from 1 stray cell to a partial second pose |
| Small/Large Bat | YES | NO | YES if pose_len < budget | small over-read (few-piece poses) |

Severity rule: `pose_len == budget` → no duplication; `pose_len` slightly `< budget` → 1 stray cell; `pose_len << budget` (e.g. 8 vs 19) → large second-pose overlay. This is the Build-0328 validation checklist.

## 15. Performance
Excess pieces are **real unnecessary** SAT + pattern-DMA + emit work: lizardman +2 (budget 10) to +9 (budget 19) pieces per actor. With several enemies active, tens of excess pieces/frame. **Unnecessary sprite work: PROVEN.** But **overall gameplay slowdown: NOT PROVEN** (needs a corrected `pc090oj_emitted_count` gameplay measurement, per prior correction) — this is a *contributing factor*, not established as the whole cause.

## 16. Generalized Build-0328 boundary (no implementation here)
The fix is a **single, general repair of the shared expansion loop**: `.Lnea_dloop` (and `.Lnea_dmirror`) must **treat `0xFF` as the end-of-representation terminator (stop the loop)** rather than a skip-and-continue, matching the arcade — leaving the remaining destination-capacity slots empty. **No per-enemy magic numbers, no coordinate/SAT filtering, no hand-deleting cells.** One change fixes all families.

## 17. Deferred `(code,bank)` color task — unchanged and separate.
## 18. Follow-ups — HUD `1UP`/score (bank 0x30) + Axe → first-class Palette Composer representations (no hardcoding).

## KNOWN_FINDINGS
- Carry forward **C**: rendered count = `pc090oj_emitted_count` / terminated chain; full-buffer `Y!=0` invalid.
- **New (proposed B):** *`0xFF` is the PC090OJ actor piece-descriptor end-of-representation terminator; the native `.Lnea_dloop` must stop on it. Using the arcade destination-slot capacity as a fixed source piece count causes cross-family over-read into the next animation pose.*
