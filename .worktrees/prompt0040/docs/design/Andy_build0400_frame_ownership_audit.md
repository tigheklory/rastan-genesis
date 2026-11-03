# Build 0400 Frame-Ownership + Active-Display Optimization Audit

Status: PROOF + DESIGN pass. No production ROM change. Build counter unchanged (400).
Author: Andy. Accepted baseline: Build 0400 (canonical SHA 36e0806…c02fe5).

Evidence classes used below: **[STATIC]** source/disasm proof · **[EXACT]** memory-tap /
beam runtime measurement · **[STAT]** PC-sampling statistics · **[OBS]** user observation ·
**[HYP]** hypothesis. Nothing is promoted across classes.

Supersedes the "pre-publication producer" framing in the VBlank Budget report (corrected in §2).
This is the "bounded runtime timing evidence" that `Cody_gameplay_vint_invocation_ownership.md`
§18 said was the required next step.

---

## 1. Build 0400 static execution order  [STATIC]

From `apps/rastan-direct/src/vdp_comm.s:175` (`_vblank_service`) and the final ROM disassembly
(`build/genesis_postpatch.disasm.txt`). Runtime addresses from `apps/rastan-direct/out/symbol.txt`.

| # | Stage | symbol / addr | caller | returns by |
|---|---|---|---|---|
| 0 | L6 vector → | `_vblank_service` 0x700C2 | 68000 autovector | (falls through) |
| 1 | input latch | `rastan_direct_update_inputs` 0x7238E | bsr | rts |
| 2 | SAT producer GUARD | `vdp_prepare_sprites` 0x745DC | bsr | rts |
| 3 | **publication** | `dma_publish_frame` 0x70250 | bsr | rts |
| 4 | **arcade VBlank worker** | 0x3A208 | **tail `jmp (0x3A208).l`** | — |
| 4a | gameplay/object subroutines | bsr 0x3AD7C, 0x3ADE2, 0x3A2A8, 0x3F0FA, 0x3F15C | bsr | rts |
| 4b | game-state jsr | 0x55D32 (via a5@0 jump table) | jsr | rts |
| 5 | **RTE** | 0x3A27E | — | rte → mainline |

Stage 2 is a guard: `vdp_prepare_sprites` does `tst.w pc090oj_sat_frame_ready; bne .done; bsr
pc090oj_native_emit_pass` (pc090oj_hooks.s:2380). In gameplay the SAT is already staged by stage 4,
so stage 2 is a **no-op**.

The heavy sprite producer actually runs in **stage 4**: the arcade sprite dispatcher calls the hooks
`genesistan_pc090oj_hook_target_41dae` / `_45dfa` (pc090oj_hooks.s:229/253), which run
`native_stage_dispatch_*` (expand arcade objects → 6 native lanes) then `pc090oj_native_emit_pass`
(concatenate lanes → SAT) and set `pc090oj_sat_frame_ready=1`.

**The entire gameplay worker + sprite producer + plane producers execute inside the IRQ6 lifetime**
(entered by the L6 vector, ended by the RTE at 0x3A27E). The arcade worker raises IPL to 7
(`oriw #0x0F00,%sr` at 0x3A208), so VINT is masked for the whole worker.

### Does gameplay run before or after publication?  **AFTER.**  [STATIC]
Publication (stage 3) runs before the tail jmp to the arcade worker (stage 4).

### Does `vdp_prepare_sprites` run before or after publication?  **BEFORE** (stage 2), but it is a
no-op guard in gameplay; the real emit work is stage 4 (after publication).  [STATIC]

### What publication commits  [STATIC + EXACT]
Publication (stage 3) DMAs the buffers staged by the **previous** IRQ6's stage-4 worker: it commits
frame N−1 while stage 4 then produces frame N. EXACT confirmation: the SAT DMA and the scroll (VSRAM)
write each occur exactly once per gameplay tick (537 each vs 538 ticks in the attract validation run).

---

## 2. Correction to the VBlank Budget report  [STATIC]

The report's "pre-publication producer" framing is **wrong** and must be corrected after the new
measurements land:

- The sprite **producer** (`pc090oj_native_emit_pass`/`native_sprite_emit`) and the arcade gameplay
  tick both run **AFTER** publication, in stage 4, inside IRQ6 — not "pre-publication".
- The only pre-publication producer step is the `vdp_prepare_sprites` guard, which is a no-op in
  gameplay.
- Correct mental model: `publish(frame N−1) → arcade tick + producers(stage frame N) → RTE`, all
  inside one IRQ6.

The earlier PC-sampling "producer 51% / 62%" remains valid **[STAT]** but is a sample share, not a
measured cycle percentage, and must keep that label.

---

## 3. What does mainline do after RTE?  **It spins/waits. No useful work.**  [STAT + STATIC]

EXACT/STAT: of 900 external frames sampled at frame-done, only **11 (1.2%)** caught a PC outside all
handler ranges; the other 98.8% were inside the IRQ6 handler. The non-handler (mainline) samples land
in **busy-wait delay loops**: 0x3B0B6 (`move.w #8191,%d0; … subq.w #1,%d0; bne`) and 0x3B0FE
(`subq.w #1,%d0; bne`). [STATIC] disasm confirms these are spin/delay loops, not gameplay.

**Answer to Tighe's question — corrected (not "all active-display CPU is wasted").** [STAT] 98.8% of
frame-done samples are inside the IRQ6 lifetime: the CPU is **already using** active-display time, but
it is trapped running the IPL7 non-preemptible worker that spilled past VBlank. Only the remainder
**after** RTE is wasted in the 0x3B0B6/0x3B0FE spin loops. The problem is scheduling (long
non-preemptible IRQ + mis-scheduled commit), not idle silicon. The benefit of the new model is a short
preemptible IRQ + mainline worker, **not** recovering ~224 idle scanlines that were never idle.

---

## 4. EXACT frame-timing instrument  [EXACT]

`tools/mame/scripts/frame_timing_trace.lua` + `tools/mame/run_frame_timing_trace_wsl.sh` (READ-ONLY).
Exec hooks (`cpu:add_exec`) are unavailable in this MAME; timing is taken from **memory-access taps**
+ the VDP HV counter (0xC00008, side-effect-free). Markers (symbol.txt): input-shadow write 0xFF61F6,
emit-count write 0xFFBED4 (one per gameplay tick = the reliable frame delimiter), VDP-port writes
0xC00000–7 (publication window + sub-phase by decoded CD/target). Validated headless (attract).

Headline metric: **gameplay ticks / display frame** (emit writes ÷ external VBlanks). <1.0 = dropped
gameplay frames = the crawl. Also per emitted-bucket: publication span (beam scanlines), producer-done
beam V (compV<224 ⇒ IRQ6 overran vblank), and publication sub-phase counts.

Attract validation (NOT representative — needs gameplay): ticks/frame ≈ 0.90, producer-done V ≈ 19
(100% overran vblank), SAT/VSRAM 1 per tick, tiles ≈ 49% of publication writes.

**Phase 3/4 (LIGHT/MEDIUM/HEAVY) and Phase 11 (publication re-measurement) require Tighe to play.**

---

## 5. Sprite producer decomposition  [STATIC]

Per-piece builder `.Lnq_emit_entry` (pc090oj_hooks.s:1988–2330), called once per lane piece from the
6 lanes (HUD, front_effect, player_front, middle, player_body, back_enemy):

| subphase | lines | cost | rejects here? |
|---|---|---|---|
| code validity + blank-bitset | 1992–2004 | ~6 insns + 1 byte read | yes (invalid/blank) |
| HUD tag + Y/X wrap normalize | 2005–2025 | ~13 insns | no |
| flip handling | 2026–2037 | ~10 insns (if flipped) | no |
| **opaque-bbox viewport clip** | 2041–2068 | ~28 insns + 4 byte reads | **yes (off-screen)** |
| variant residency remap | 2070–2102 | 1 u16 read + 1 byte read (O(1)) | no |
| reverse residency lookup | 2104–2133 | directory byte + leaf byte (O(1)) | miss→alloc/drop |
| palette + SAT attribute build + SAT write | .Lnq_hit | SAT entry construct + writes | — |

Key facts: pieces are **pre-expanded** (lanes built by `native_stage_dispatch_*` before emit); the
builder is **O(active pieces)** capped at `NATIVE_SAT_MAX=80`; **viewport culling happens before** the
residency/SAT work; the residency resolve is already **O(1)** (2-level directory+leaf, 2 byte reads),
not a search. candidate pieces = Σ lane counts; emitted = pieces passing clip under 80; rejected =
clipped/blank + over-cap (over-cap counted in `pc090oj_dropped_count`).

Cycles/subphase need an exec-hook build or hand cycle-count; the above static instruction counts are
the available [STATIC] evidence. Runtime piece/candidate/rejected counts are addable to the trace.

---

## 6. Repeated-work audit  [STATIC]

Residency reverse-lookup, variant remap, bbox clip, palette line, and SAT attribute build are redone
**every frame for every piece**, including unchanged pieces. BUT each is already **O(1) and cheap**
(a few table reads + arithmetic); there is **no per-frame search or redundant shared recompute**.

Therefore a generation-tagged resolved-slot cache (candidate E) saves only ~2 table reads + a little
arithmetic per unchanged piece, against a per-piece cache-validity check — **marginal**. The dominant
per-piece cost is the unavoidable SAT attribute construction + the lane iteration. The real levers are
**reducing piece count** (earlier object cull / active-lane lists) or **moving the O(N) producer out of
IRQ6** so it runs in active-display time instead of compressing the vblank frame.

---

## 7. Moveability matrix  [STATIC for context/buffering; SAFE-column = HYP pending prototype]

Buffering: SAT is **double-buffered** (`pc090oj_sat_bank` flip in vdp_commit_sprites, pc090oj_hooks.s:2394)
— [STATIC] confirmed. Plane A/B, scroll, palette, tiles are **single-buffered** (`staged_*_buffer`, no
flip). Producer writes only RAM (staged SAT back bank + tile worklist) — **no VDP access** [STATIC].

| operation | ctx now | direct VDP? | writes live arcade state? | output buffering | safe in active display? | safe to preempt by IRQ6? | prerequisite |
|---|---|---|---|---|---|---|---|
| input latch | IRQ6 | no (I/O port) | yes (shadow) | — | AFTER-PREREQ (once/tick) | no | tick cadence |
| **sprite producer (emit_pass)** | IRQ6 st4 | **no** | no (reads a5+lanes; writes SAT back bank **AND the single-buffered tile-DMA worklist + mutable residency alloc**) | **SAT double; worklist SINGLE** | **AFTER-PREREQ** | no | READY-isolate the tile worklist (SAT double alone is NOT sufficient — see decomposition §8) |
| arcade object/collision/AI tick | IRQ6 st4 | no | yes | — | YES (it is CPU logic) | no | one-tick cadence |
| scroll calc | IRQ6 st4 | no | writes staged scroll | single | AFTER-PREREQ | no | isolate scroll regs |
| Plane A producer | IRQ6 st4 | no | writes staged_fg_buffer | single | AFTER-PREREQ | no | plane isolation |
| Plane B producer | IRQ6 st4 | no | writes staged_bg_buffer | single | AFTER-PREREQ | no | plane isolation |
| palette producer | IRQ6 st4 | no | writes staged_palette | single | AFTER-PREREQ | no | palette isolation |
| tile staging | IRQ6 st4 | no | writes staged tiles + worklist | single | AFTER-PREREQ | no | tile isolation |
| **CRAM commit** | IRQ6 st3 | **yes** | no | — | **NO** | n/a | VDP vblank window |
| **VRAM pattern DMA** | IRQ6 st3 | **yes** | no | — | **NO** | n/a | VDP vblank window |
| **Plane name-table DMA** | IRQ6 st3 | **yes** | no | — | **NO** | n/a | VDP vblank window |
| **SAT DMA** | IRQ6 st3 | **yes** | no | — | **NO** | n/a | VDP vblank window |
| **scroll (VSRAM) commit** | IRQ6 st3 | **yes** | no | — | **NO** | n/a | VDP vblank window |

Strongest first candidate: the **sprite producer** — it is CPU-only, writes the **double-buffered** SAT
back bank, and is the measured dominant cost. It can run in active display if its input lanes are staged
and the back bank isn't being DMA'd.

---

## 8. Target Genesis frame model (arcade-owned)  [design]

Arcade code stays execution owner; VBlank stays timing authority. Genesis helpers stay finite HW
translation helpers. No Genesis-owned gameplay loop.

```
IRQ6 (short, bounded):
    latch input timing; record ONE pending tick opportunity
    commit the previous READY frame (CRAM/VRAM/plane/SAT/scroll DMA) — stages 3 only
    RTE quickly  (NO gameplay, NO producers)

ARCADE MAINLINE (replaces the current spin):
    if a tick opportunity is pending and no WORK in flight:
        consume exactly one opportunity (no backlog > 1)
        run exactly ONE original arcade gameplay frame  (object/collision/AI tick — stage 4 logic)
        run the CPU-only producers into WORK buffers (sprite/plane/scroll/palette/tiles)
        mark WORK → READY atomically (pointer/bank/generation swap)
    else: wait for next opportunity
```

Rules honored: at most one pending tick; no worker reentry; no catch-up storm; if the worker misses
the next VINT, IRQ6 **holds the displayed frame** — it does NOT re-DMA the previous frame (the VDP is
already showing it); it publishes only when `ready_generation != displayed_generation` (never a
half-built one); frame counters advance with the gameplay tick (mainline), not with publish; input
consumed once per tick. See `Andy_build0400_irq6_decomposition_and_reorder_plan.md` for the full plan.

Compliance: the arcade program still decides all gameplay/state/traversal and still runs its own tick
exactly once per VBlank opportunity; Genesis code only (a) commits finished buffers in VBlank and
(b) schedules "run the arcade tick once" — it does not author gameplay. This is the Rainbow-Islands /
Sonic split (short VBlank commit + mainline frame worker) applied to the arcade-owned tick.

Risk: the current arcade worker runs at IPL7 as one atomic interrupt; moving it to mainline means it
can be preempted by IRQ6. The WORK/READY swap must be the only IRQ6-visible transition, and IRQ6 must
read only READY (never WORK). This is the central correctness obligation.

---

## 9. Completed-frame isolation (WORK → READY → COMMIT)  [design]

Cheapest correct isolation per stager (avoid blind full double-buffering):

| stager | current | proposed isolation | cost |
|---|---|---|---|
| SAT | already double-buffered (bank flip) | keep as-is | 0 (already paid) |
| Plane A (entering-edge) | single `staged_fg_buffer` + dirty mask | **double-buffer the small dirty-row/col queue**, not the whole plane | small (queue only) |
| Plane B | single `staged_bg_buffer` + `bg_row_dirty` | double-buffer the dirty-row queue | small |
| scroll | single words | double-buffer (few words) | trivial |
| palette | single 64 words | double-buffer or generation snapshot | trivial (128 B) |
| tiles | single staged + worklist | double-buffer worklist (≤12 entries) | trivial |

Plane A Sonic-style entering-edge streaming stays intact: isolate the **dirty queue** (the small list
of changed rows/cols), not the plane, so no full-plane rebuild is introduced.

---

## 10. What stays in VBlank  [STATIC]

Keep in IRQ6 (genuine VDP timing window): CRAM commit, VRAM pattern DMA, plane name-table DMA, SAT DMA,
VSRAM scroll commit — all are direct VDP access (dma.s). Everything CPU-only (producers, arcade tick)
has **no** hardware/timing dependency on vblank and should move to the mainline worker.

---

## 12. Optimization ranking  [evidence-tagged; cycle deltas pending the HEAVY trace]

| rank | change | evidence | expected saving | prerequisite | risk |
|---|---|---|---|---|---|
| 1 | **B. Move arcade frame worker + producers out of IRQ6** (the §8 model) | [STAT] producer ~51–62% sample share; [EXACT] producer-done V in active display, ticks/frame<1; [STATIC] worker fully in IRQ6, mainline spins | reclaim the ~whole active-display window (≈200+ lines) for the frame worker; raises the load ceiling before frames drop | §9 isolation; IPL7→preemptible | high (atomicity) |
| 2 | **A. Move just `vdp_prepare_sprites`/SAT producer to active display** | [STATIC] CPU-only, SAT double-buffered | partial of #1; smaller blast radius; good first step | back-bank idle guard | medium |
| 3 | **F. Earlier piece culling / G. active-lane traversal** | [STATIC] O(pieces); clip already before resolve | fewer pieces → linear producer saving; only if off-cull is cheap and pieces are often off-screen | lane active-flag | low |
| 4 | **C. WORK/READY isolation for non-SAT stagers** | [STATIC] single-buffered | enables #1/#2 correctness; not a saving by itself | — | low |
| 5 | **H. package transition prepare-vs-commit split** | [STATIC] Plane B transition bulk 37.8 ln (0356 beam) | removes the rare transition spike from vblank | prepare buffer | medium |
| 6 | **D. native_sprite_emit hot-loop micro-opt** | [STATIC] already O(1)/piece | small | — | low |
| 7 | **E. generation-tagged resolve cache** | [STATIC §6] resolve already O(1) | marginal (≈2 reads/piece) vs check cost | per-piece gen tag | low |

Intuition explicitly rejected: caching the resolve (E) ranks LAST because the resolve is already O(1);
the measured win is architectural (move O(N) work off the vblank-compressed frame), not micro-opt.

---

## Pending (require Tighe to play; then update the VBlank Budget)

- Phase 3/4: LIGHT/MEDIUM/HEAVY exact timing via `run_frame_timing_trace_wsl.sh`.
- Phase 11: Build-0400 publication sub-phase span (movement / vertical / sprite-heavy).
- Phase 5 runtime: add candidate/visible/rejected piece counters to the trace if the cycle split is wanted.
- Then: correct the report per §2, replace Build-0356 publication labels with Build-0400 where re-measured.
