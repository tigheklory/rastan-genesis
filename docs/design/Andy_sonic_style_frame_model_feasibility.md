# Andy — Sonic-Style Frame Model Feasibility Study

**Architecture / semantic proof only. No source, no ROM, no Test Build. Counter 359.**
Question: can Rastan's arcade-frame continuation move from a non-preemptible IRQ6 continuation into a
preemptible **mainline frame worker**, with IRQ6 reduced to a short bounded commit? Evidence:
`apps/rastan-direct/src/vdp_comm.s` (`_vblank_service`), `dma.s` (`dma_publish_frame`),
`pc090oj_hooks.s` (SAT double-buffer), the joint 0356 timing investigation, and KF-068.

## 1. Current IRQ6 continuation contract (proven)

`_vblank_service` (vector-30 / IRQ6, `vdp_comm.s:175`):
1. `movem.l d0-d7/a0-a6,-(sp)` — save all regs;
2. `bsr rastan_direct_update_inputs` — **input latch, at IRQ6 entry**;
3. `bsr vdp_prepare_sprites` — SAT staging guard (no VDP);
4. `bsr dma_publish_frame` — **the single bounded publication phase** (commits the *previous* frame:
   palette→CRAM, tiles, Plane B rows, Plane A rows, sprite pattern+SAT DMA, scroll). **Publish-first.**
5. `movem.l (sp)+,d0-d7/a0-a6` — restore;
6. `jmp (0x00003A208).l` — **tail-jump into the arcade VBlank handler, NO RTE.**

The arcade handler (arcade_pc 0x03A008 → runtime 0x03A208) then runs the **entire arcade frame** —
gameplay tick, object updates, scroll, PC080SN/PC090OJ semantic producers → native finalizer — raises
**IPM to 7** early (arcade 0x03A052), and ends with `ori #$0600,SR` (KF-068) + **RTE** at arcade
0x03A07E / runtime 0x03A27E. That RTE pops the SR(IPM0)+PC the CPU pushed when IRQ6 was taken and
returns to the interrupted Genesis mainline (the copied arcade main loop, which idles/waits).

**So the entire arcade frame *is* the IRQ6 service.** The "mainline" today does no frame work.
Non-preemptibility comes from three coupled facts: (a) the tail-**jmp** (no RTE between publish and
worker), (b) the worker **raises IPM7**, and (c) the worker **ends in RTE** expecting an interrupt
frame. The whole chain is ~285 median lines vs a 262-line frame; the bounded publish alone is
**6.205 median lines** (timing investigation) — so the worker is ~279 of the 285.

## 2. Preemptibility audit

| Frame part | Safe for IRQ6 to interrupt? | Note |
|---|---|---|
| arcade gameplay tick / object updates / scroll | mutates arcade WRAM (actor tables, counters) | safe **only if IRQ6 never reads live arcade WRAM** and never re-enters the tick |
| PC080SN producers (Plane A/B staging) | writes `staged_fg_buffer`/`staged_bg_buffer` | **single-buffered** → unsafe to publish mid-write |
| PC090OJ producers → native finalizer | writes `staged_sprite_sat`/`_b` | **double-buffered** (`pc090oj_sat_bank`) → already isolated |
| scroll / palette / tile staging | `staged_scroll_*`, palette buffer, staged tiles | **single-buffered** → unsafe to publish mid-write |

**Key isolation finding:** only the **SAT** is double-buffered. Plane A, Plane B, scroll, palette, and
tiles are **single-staged** — safe today purely because publish (step 4) runs strictly *before* the
worker writes them. In the target model (worker in mainline, IRQ6 commits concurrently), a mid-write
plane/palette/scroll buffer could be published half-updated → tearing/corruption.

## 3. Completed-frame publication

Target: **WORK buffer** (mainline builds) → **READY buffer** (complete, immutable) → **COMMIT** (IRQ6
consumes). SAT already supports this (bank swap + `pc090oj_sat_frame_ready`). Everything else does
**not**. Minimum additional state required: give Plane A, Plane B, scroll, palette, and tile staging
the same **ready-bank + atomic swap** the SAT has, and make `dma_publish_frame` read **only the ready
bank**. Without that, IRQ6 can publish a half-built frame — the one thing that must never happen.

## 4. Arcade frame semantics

- **1 tick ↔ 1 physical VBlank?** Today yes, because 1 IRQ6 = 1 worker run = 1 publish. But the arcade
  itself ran its frame inside its VBlank ISR, so when the arcade frame overran, its next VBlank frame
  was likewise delayed — the arcade **slowed down under load**. So a tick is *not* semantically nailed
  to a physical refresh; it is "one completed gameplay update," and the arcade already let that rate
  drop.
- **Can a tick span multiple physical frames?** Yes — that is exactly arcade slowdown, and it is the
  intended behavior of the target model.
- **If mainline misses a deadline:** IRQ6 should **republish the last completed buffer** (display holds
  a stable, complete frame) and RTE. This is *more* visually arcade-faithful than today: the current
  Genesis model shows black bars / late commit during active display; the arcade held a stable picture
  and slowed the logic.
- **Input latch:** must be latched **once per tick** (or latched into a buffer per VBlank and consumed
  once per tick), not once per physical VBlank — otherwise a decoupled VBlank rate over-/under-samples
  inputs. This is a relocation, not new logic.
- **Frame counters advance:** with the **worker/tick**, never in the publish-only IRQ6. They already
  live inside the arcade handler, so this is preserved as long as IRQ6 stops calling that handler.
- **Next tick before previous commit?** Must not start until the previous WORK buffer is marked READY
  (single-worker discipline) — no arcade-frame reentrancy (see §5).

**Honest caveat:** the target model *changes the display/logic timing coupling*. It preserves gameplay
tick semantics and improves visual stability, but the relationship "logic overrun ⇒ next refresh
delayed" becomes "logic overrun ⇒ display holds + logic slows." That is a deliberate, arguably
more-faithful change, not a pure no-op — Tighe should accept it explicitly.

## 5. Reentrancy / KF-068

KF-068 crashed because the arcade's `andi #$F0FF,SR` lowered IPM one instruction *before* its RTE,
opening a window where the next VBlank IRQ6 **re-entered the arcade frame handler** (0x3A208) while
the previous frame was still on the stack → nested arcade frames → falling SP, repeated 0x3A27E stack
material, illegal PC. The fix (`ori #$0600,SR`) kept IPM≥6 until RTE so **no second frame could start**.

**The distinction the target model relies on is valid:** *nested execution of the arcade frame
handler* (BAD, what KF-068 hit) is categorically different from *IRQ6 interrupting the worker only to
DMA an already-completed, immutable buffer and RTE* (candidate GOOD). The latter never calls 0x3A208,
never touches the worker's live state, and leaves the suspended worker's registers/stack intact
(IRQ6 saves/restores them). **This is sufficient in principle to be safe** — but only under two hard
invariants: (a) IRQ6 is **strictly publish-only** and never reaches the arcade handler, and (b) the
worker must **lower its IPM to allow IRQ6** (otherwise the worker's IPM7 masks VBlank and the publish
is delayed again — the very overrun we're removing). Lowering the worker's IPM is safe *only* once (a)
holds and §3 isolation holds; it is the semantic heart to prove before any build.

## 6. Bounded IRQ6 responsibility (target)

Smallest reasonable IRQ6:
1. acknowledge VBlank / hardware housekeeping;
2. if a new READY buffer exists select it, else reselect the last completed one;
3. `dma_publish_frame` on the ready bank (bounded VDP/SAT/scroll/palette/plane commit);
4. latch inputs into the per-tick input buffer;
5. set a frame-opportunity flag for the worker;
6. RTE.

**Upper bound:** `dma_publish_frame` is already measured at **6.205 median lines**; adding ack + input
latch + flag keeps IRQ6 well under ~8–10 lines — comfortably inside the ~38-line VBlank, with margin
for the occasional larger commit. The bounded commit fitting VBlank is *already proven* today.

## 7. Feasibility verdict — **FEASIBLE WITH PREREQUISITES**

The publish phase is already bounded, publish-first, and (for SAT) double-buffered, and the KF-068
distinction makes the model sound in principle. It is **not** a drop-in: the worker is literally the
arcade's interrupt handler (IPM7 + terminal RTE), and most staging is single-buffered. Concrete
prerequisites before any prototype:

1. **Break the RTE/IPM coupling of the worker** — let the arcade frame handler (0x3A208, ends in RTE,
   raises IPM7) run as a mainline-invoked unit that (a) returns cleanly (trampoline / synthesized
   frame so its terminal RTE lands at a known worker-return point) and (b) runs at **IPM ≤ 5** so IRQ6
   can fire. *Largest, most delicate prerequisite.*
2. **Full completed-frame buffer isolation** — give Plane A, Plane B, scroll, palette, and tiles the
   ready-bank + atomic-swap the SAT already has; make `dma_publish_frame` read only the ready bank.
3. **IRQ6 strictly publish-only** — it must never reach 0x3A208 (the KF-068-safe invariant).
4. **Relocate the input latch** to per-tick (or latch-to-buffer, consume per tick).
5. **Keep tick-advance / frame counters in the worker**; verify no worker critical section depends on
   VBlank staying masked once §3 isolation holds.
6. **Explicit acceptance of the timing-semantics change** (display holds + logic slowdown vs today's
   overrun/black bars) — §4.

## 8. Prototype plan (smallest safe sequence — DO NOT IMPLEMENT here)

Each experiment is its own numbered build (do not conserve numbers); each has a rollback = the prior
build.

- **Experiment A — RTE decouple in place.** Introduce a trampoline so the arcade worker is entered as
  a callable unit returning cleanly, but keep invoking it from the IRQ6 tail (no scheduling change).
  *Acceptance:* behavior/timing identical to 0359 (proves the return mechanics only). *Rollback:*
  restore the `jmp (0x3A208)`.
- **Experiment B — completed-frame isolation.** Add ready-bank double-buffering for Plane A/B, scroll,
  palette, tiles; `dma_publish_frame` reads only the ready bank; still fused (publish-then-worker).
  *Acceptance:* read-only invariant capture shows publish never reads a buffer the worker is
  mid-writing; no visual regression on the cave route. *Rollback:* revert buffering.
- **Experiment C — schedule decouple.** IRQ6 becomes publish-only + RTE + input-latch-to-buffer +
  opportunity flag; the mainline loop runs the (trampolined) worker at IPM ≤ 5 and marks READY on
  completion; a late worker causes IRQ6 to republish the last READY buffer. *Acceptance* on the
  first-cave no-kill route: **stable display, no black bars**, graceful slowdown, no crash/desync,
  arcade frame counter advances per completed tick, inputs correct. *Rollback:* revert to the
  Experiment-B fused model.

Only after C passes is the "Sonic-style" model real; A and B are independently valuable and low-risk.
