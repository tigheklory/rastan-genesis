# Joint Build 0356 Frame-Timing / VBlank-IRQ / Performance Investigation — PLAN

Roles: **Cody = measurement lead**, **Andy = architecture/review lead**. Tighe = final authority.
Handoff order: Cody measures → Andy reviews/challenges → Cody re-measures → joint synthesis. No fake
consensus; disagreements preserved. Production/ROM/counter: **unchanged (356)** for this investigation.

## Agreed baseline (Phase 0)
- Build 0356 removed the normal-gameplay sprite palette post-pass (`.Lnative_pal_fixup` / route scan).
- Typical publication is now ~6–22 physical scanlines; exceptional (transition) ~63 lines
  (Cody physical-beam; the retired 8-bit V-counter `%262` numbers are void).
- Cody's prior harness reported publisher **entry** in active display ~86% of gameplay publications.
- **This does NOT by itself prove VBlank IRQ6 was serviced late.** IRQ assertion, IRQ6 service entry,
  and publisher entry are distinct events and must be timestamped separately.

## Andy's Phase-0 static control-flow finding (the frame model)
On the Genesis, `_vblank_service` is **vector 30 (the level-6 VBlank autovector)** and it ends with
`jmp (0x00003A208)` — the arcade tick — **with no RTE**. So each frame:

```
VBlank -> IRQ6 taken (CPU raises SR mask to level 6, pushes SR/PC)
       -> _vblank_service (native): update inputs -> vdp_prepare_sprites (guard) -> dma_publish_frame
       -> jmp 0x3A208 (ARCADE TICK: game logic + native producers stage NEXT frame)  [still mask 6]
       -> ... (RTE is somewhere in the copied arcade program) -> pre-interrupt wait/main loop
```

Consequence to test: the arcade tick + native producers run as a **masked continuation of the VBlank
ISR (mask level 6)**, so VBlank IRQ6 **cannot preempt** them. If total per-frame work
(pre-publisher + publisher + arcade tick + producers) exceeds one 262-line frame, the next VBlank
fires while masked, stays **pending**, and is serviced only after the arcade tick's RTE — which can
land in active display. That would make "publisher enters active display 86%" a **symptom of
total-frame overrun**, not a masking bug, and would explain why 0356 still feels slow (the publisher
is now cheap, but the arcade tick + producers are the bulk and still overrun the frame). **HYPOTHESIS —
requires Cody's dynamic proof (see OPEN_QUESTIONS Q2/Q3/Q5/Q6).**

## Deliverables in this directory
- `CODY_MEASUREMENTS.md` — Cody's evidence (physical-beam + MAME debugger IRQ/SR/VINT + tick counts +
  hierarchical non-publication profiling). Raw traces alongside or under `states/traces/`.
- `ANDY_REVIEW.md` — Andy's Phase-0 static groundwork (done) + review of Cody's measurements (after).
- `OPEN_QUESTIONS.md` — the measurement requests / uncertainties, tracked to RESOLVED/UNRESOLVED/
  NOT MEASURABLE.
- `FINAL_CONSENSUS.md` — joint synthesis, only after the review loop.

## Method discipline (both agents)
Prefer MAME debugger / external tracing. No production edit to ease collaboration. If a measurement
truly needs ROM instrumentation not doable externally: justify, propose the minimum, STOP for Tighe
before any numbered ROM. Separate STEADY / CONDITIONAL / TRANSITION costs. Rank by whole-frame gain,
not local percentage. D00462 stays a separate issue (record if hit, don't fix here).
