# Build 0400 IRQ6 Decomposition + Genesis Frame-Reorder Plan

Status: DESIGN / DECOMPOSITION. No production source change. No ROM. Counter 400.
Author: Andy. Continues `Andy_build0400_frame_ownership_audit.md` (frame-ownership proof not repeated).

Evidence classes: **[STATIC]** source/disasm proof · **[EXACT]** tap/beam measurement ·
**[STAT]** PC-sampling · **[HYP]** hypothesis. Not promoted across classes.

### Corrections folded in from the frame-ownership review (now authoritative)
1. "Active-display CPU is wasted" is **too broad**. [STAT] 98.8% of frame-done samples are inside the
   IRQ6 lifetime; the worker runs *past* VBlank into active display. The CPU is **already using**
   active-display time — it is trapped in one long IPL7 interrupt; only the post-RTE remainder spins.
2. Missed/coalesced VINT is **NOT yet proven**. Proven: **handler overrun** and **next-VINT
   preemption impossible** (IPL7). Not distinguished: VINT *lost* vs *serviced late* vs startup
   contamination. Needs the steady-gameplay counts (Phase 20).
3. The sprite producer is **not SAT-only**: it also writes the **single-buffered** tile-DMA worklist
   that publication consumes (confirmed §8). SAT double-buffering alone does NOT make it preemptible.

---

## CURRENT EXECUTION TREE  [STATIC]

```
L6 vector 0x00070 -> _vblank_service 0x700C2            (vdp_comm.s:175; movem, no SR op)
  BSR rastan_direct_update_inputs 0x7238E              (tilemap_hooks.s:3659) RTS   [input latch]
  BSR vdp_prepare_sprites        0x745DC               (pc090oj_hooks.s:2380) RTS   [SAT guard; no-op in gameplay]
  BSR dma_publish_frame          0x70250               (dma.s:70) RTS   [PUBLISH frame N-1]
       BSR vdp_commit_palette            CRAM DMA   (palette_pending + staged_palette_words)
       BSR vdp_commit_tiles_if_dirty     VRAM PIO   (tiles_dirty + staged_tile_words)
       BSR vdp_commit_bg_strips_if_dirty Plane B DMA(bg_row_dirty + staged_bg_buffer)
       BSR vdp_commit_fg_narrow_strips   Plane A    (fg dirty + staged_fg_buffer)
       BSR vdp_commit_sprites_vram       patternDMA+SATDMA (sat_frame_ready, sat bank, tile worklist)
       BSR vdp_commit_scroll             HScroll + VSRAM
  JMP (0x3A208).l   -- TAIL JUMP into arcade VBlank worker (no return; RTE ends it)
       0x3A208  oriw #0x0F00,%sr          [IRQ glue: raise IPL7 -> worker is atomic]
       0x3A20C  6x NOP                     [patched-out original hook site]
       0x3A218  movew %a5@(2),%d0; cmpi; bcc/bcs   [game-mode gate]
       0x3A228  BSR 0x42130 (cond)        [gameplay subsystem]
       0x3A23E  BSR 0x3AD7C               [gameplay subsystem]
       0x3A242  BSR 0x3ADE2               [gameplay subsystem]
       0x3A246  BSR 0x3A2A8               [reads 0xFF61F8 input bits; control]
       0x3A24A  BSR 0x3F0FA               [gameplay subsystem]
       0x3A24E  BSR 0x3F15C               [gameplay subsystem]
       0x3A252  PEA 0x3A274 ; jump-table dispatch on %a5@(0) game-state -> JSR 0x55D32
                 [state worker; sprite dispatcher + native hooks run under here:
                  genesistan_pc090oj_hook_target_41dae/_45dfa -> native_stage_dispatch_*
                  -> pc090oj_native_emit_pass (sets pc090oj_sat_frame_ready, writes SAT+worklist)]
       0x3A27A  oriw #0x0600,%sr          [IRQ glue: set return IPL]
       0x3A27E  rte                        [IRQ exit -> mainline]
  mainline (post-RTE): busy-wait/delay spin loops 0x3B0B6 / 0x3B0FE  [STAT 1.2% of samples]
```

Ages [STATIC]: publication (stage 3) commits buffers staged by the **previous** IRQ6's worker; the
worker (stage 4) then stages the **next** frame. EXACT: SAT DMA and scroll each occur once per tick.

---

## CLASSIFICATION SUMMARY

| class | items | VDP? | writes WRAM? | writes pub-visible RAM? | buffering | needs exc frame? | needs IPL7? | active-display? |
|---|---|---|---|---|---|---|---|---|
| **I IRQ/timing** | L6 entry, `movem`, tail transfer | no | no | no | — | the entry only | no | n/a (tiny) |
| **II VDP commit** | the 6 `vdp_commit_*` in dma_publish_frame | **YES** | no | reads only | — | no | no | **NO (keep IRQ)** |
| **III gameplay CPU** | 0x42130,0x3AD7C,0x3ADE2,0x3A2A8,0x3F0FA,0x3F15C, state JSR 0x55D32 tree | no* | **yes** (a5 WRAM) | no | — | no | for atomicity only | YES (logic) |
| **IV CPU graphics producers** | native_stage_dispatch_*, pc090oj_native_emit_pass, plane/scroll/palette producers | no* | reads a5 | **yes** | — | no | for atomicity only | YES after §10 isolation |
| **V publication staging** | staged_palette/tile/bg/fg buffers, dirty masks, SAT banks, **tile worklist**, pending flags | no | — | — | SAT=DOUBLE; rest=SINGLE | no | no | n/a (data) |
| **VI IRQ/exc glue** | 0x3A208 `ori #0x0F00,sr`; 0x3A27A `ori #0x0600,sr`; 0x3A27E `rte` | no | %sr | no | — | **YES** | defines it | must CONVERT |
| **VII scene/transition** | package/residency install, Plane-B C-window clear bulk | some via staging | yes | yes | single | no | no | AFTER-PREREQ (prepare/commit split) |
| **VIII delay/idle** | mainline spins 0x3B0B6/0x3B0FE; init-only 0x3Bxxx VDP setup | init only | — | — | — | no | no | DELETE/obsolete for the new model |

\* "no*" = no **direct** VDP access found for the core gameplay-worker subroutines in static scan, but
see the VDP gate below — some retained frontend/status arcade routines reference 0xC0xxxx and their
gameplay-reachability is unproven.

---

## DIRECT VDP ACCESS AFTER dma_publish_frame  — **GATE: NOT FULLY CLOSED**  [STATIC + needs EXACT]

Method: enumerated every VDP-port operand and every `lea/movea #0xC0xxxx` pointer setup in the final
ROM disasm.

- Genesis publisher (0x70000+): expected (CRAM/VRAM/SAT/scroll + HV reads). KEEP.
- Crash handler 0x1ACxxx and reset/init 0x3B064–0x3B7Bx: one-time, **not per-frame**. (0x3B12C
  `lea 0xc00000,a0` etc. is power-on VRAM clear / VDP reg setup; `andiw #0xF0FF,%sr` at 0x3B27A enables
  interrupts after init.)
- The **core gameplay-worker BSR targets** (0x3AD7C, 0x3ADE2, 0x3A2A8, 0x3F0FA, 0x3F15C, 0x55D32) show
  **no** VDP-port operand and **no** 0xC0xxxx pointer setup → **no direct VDP access proven for the
  core worker.**
- BUT retained arcade **frontend/HUD/status producers** reference 0xC0xxxx: 0x52A0A/0x52B26
  (`#0xC08000`), 0x560C2/0x560EC, 0x5765E, 0x57970, **0x5A3D0–0x5A4B6** (the 0x5A098 status-lane
  family). Their **gameplay-reachability is UNPROVEN** here.

**Result: POST-PUBLICATION CORE WORKER HAS NO PROVEN DIRECT VDP ACCESS; the 0xC0xxxx-referencing
frontend/status routines must be proven gameplay-unreachable (or redirected) before the worker moves.**
Close this with the gameplay trace: add a VDP-write detector that flags any VDP write occurring in the
worker window (after publication burst, before the next tick). If gameplay shows zero worker-phase VDP
writes, the gate closes empirically. **Do not proceed to the worker move under assumption.**

---

## TRUE ARCADE TICK BODY  [STATIC]

- **Entry:** first instruction after the IPL7 raise — 0x3A20C (effectively 0x3A218, after the NOP pad).
- **Exit:** 0x3A27A (just before the IRQ return-IPL set), i.e. the tick body is **0x3A20C–0x3A279**.
- **IRQ-only wrapper:** 0x3A208 (`ori #0x0F00,sr`), 0x3A27A (`ori #0x0600,sr`), 0x3A27E (`rte`).
- **Normal-callable conversion:** the body is already a linear BSR/JSR sequence returning to 0x3A27A;
  it can become `arcade_frame_worker: … rts` by (a) deleting the IPL7 raise, (b) deleting the return-IPL
  set, (c) converting `rte`→`rts`. The body itself makes no exception-frame assumption (verified: no
  stack-frame PC/SR reads inside 0x3A20C–0x3A279; the only SR ops are the two wrapper `ori`s).

---

## IRQ-CONTEXT CONVERSION  [STATIC]

| PC | op | role | class | target treatment |
|---|---|---|---|---|
| 0x3A208 | `oriw #0x0F00,%sr` | raise IPL7 (atomicity) | VI-C reentry protection | **REMOVE** from worker; replace with a *narrow* IPL mask around only the WORK→READY swap |
| 0x3A27A | `oriw #0x0600,%sr` | set return IPL | VI-B ISR-only | **REMOVE** (meaningless for an RTS worker) |
| 0x3A27E | `rte` | IRQ exit | VI-B ISR-only | **CONVERT to `rts`** |
| _vblank_service | (none) | — | — | already IPL-neutral; nothing to convert |

No exception-frame/stacked-PC reads exist in the worker body → conversion is mechanical **once
atomicity is re-provided by §9/§10 isolation**. The IPL7 was doing double duty: (a) ISR convention and
(b) implicit whole-worker atomicity. Only (b) must be re-created, and only around the swap.

---

## PUBLICATION DEPENDENCY GRAPH  [STATIC]

```
palette producer      -> staged_palette_words (+ palette_pending)         -> vdp_commit_palette   [SINGLE]
tile producer         -> staged_tile_words    (+ tiles_dirty)             -> vdp_commit_tiles     [SINGLE]
Plane B producer      -> staged_bg_buffer     (+ bg_row_dirty)            -> vdp_commit_bg_strips [SINGLE]
Plane A producer      -> staged_fg_buffer     (+ fg dirty/narrow state)   -> vdp_commit_fg_strips [SINGLE]
sprite dispatcher -> native lanes -> pc090oj_native_emit_pass
     -> staged_sprite_sat[bank]  (+ sat_frame_ready, pc090oj_sat_bank)    -> vdp_commit_sprites SAT [DOUBLE]
     -> pc090oj_tile_dma_worklist (+ pc090oj_tile_dma_count)              -> vdp_commit_sprites TILE[SINGLE]  <-- the hidden single-buffered edge
     -> sprite_tile_resident_code / reverse directory (residency alloc)   -> read by emit next frame [MUTABLE]
scroll producer       -> staged scroll words                             -> vdp_commit_scroll    [SINGLE]
```

Every edge except the SAT bank is single-buffered or mutable. The residency allocator state
(`sprite_tile_resident_code`, reverse directory/pages) is **mutated during emit and read by the next
emit** — it is live cross-frame state, not just a publication buffer; isolating it needs care (it is
not simply a frame buffer to swap).

---

## MINIMAL IMMUTABLE READY FRAME  [design]

Smallest isolation per subsystem (avoid blind full double-buffering):

| subsystem | WORK | READY | transition | cost |
|---|---|---|---|---|
| **SAT** | back bank (`pc090oj_sat_bank`) | front bank | bank flip (exists) | 0 (already paid) |
| **sprite tile worklist** | WORK worklist + count | READY worklist + count | copy/swap ≤12 entries | trivial |
| **residency alloc** | live `sprite_tile_resident_code`/dirs | — | keep cross-frame; publisher reads only the **worklist**, not the allocator, so isolate the worklist, NOT the allocator | verify publisher never reads mutable alloc mid-build |
| **Plane A** | staged_fg_buffer + dirty desc | READY dirty-row/col descriptor queue + its source words | double-buffer the **small dirty queue**, not the plane | small |
| **Plane B** | staged_bg_buffer + bg_row_dirty | READY dirty-row queue | double-buffer the queue | small |
| **scroll** | staged scroll | READY few words | snapshot | trivial |
| **palette** | staged_palette_words | READY 64 words or gen snapshot | snapshot | 128 B |
| **tiles** | staged_tile_words + tiles_dirty | READY bounded job | snapshot | small |

Plane-A Sonic-style entering-edge streaming is preserved: isolate the **dirty descriptor queue**, never
rebuild the plane. Key insight: the publisher reads the **worklist**, not the residency allocator, so
only the worklist (not the whole allocator) needs READY isolation — to be confirmed in §8 verification.

---

## CURRENT VS TARGET ORDER

| CURRENT Build 0400 | | TARGET |
|---|---|---|
| L6 → _vblank_service | STAY | L6 → short IRQ6 |
| input latch | MOVE | ack/timing latch |
| sprite guard (no-op) | DELETE | if READY new: publish READY N-1; set DISPLAYED=gen |
| **publish N-1** | STAY (in IRQ) | set tick_pending = 1 (saturating) |
| tail JMP worker | CONVERT | `rte` (fast) |
| gameplay/objects/AI/collision | MOVE | — mainline: — |
| scroll/plane/sprite producers | MOVE (after isolation) | consume tick_pending; run one arcade tick |
| stage frame N | MOVE | run CPU producers → WORK frame N |
| `ori/ori/rte` glue | CONVERT | atomic WORK→READY (narrow IPL mask) |
| mainline spin 0x3B0B6/0x3B0FE | DELETE | if tick still pending: loop; else wait |

---

## MOVE UNITS

**UNIT 1 — IRQ glue (SPLIT/CONVERT).** 0x3A208/0x3A27A/0x3A27E. Convert to RTS worker + short IRQ6;
re-provide atomicity narrowly (§9).

**UNIT 2 — arcade gameplay body (MOVE).** 0x3A218–0x3A251 (BSR 0x42130/0x3AD7C/0x3ADE2/0x3A2A8/
0x3F0FA/0x3F15C) + state dispatch 0x3A252→JSR 0x55D32 tree. Internally ordered as written (preserve
exactly). Depends on: input latched; a5 WRAM. Target: mainline worker. Change: no ISR wrapper; normal
return. **Prerequisite: VDP gate closed (§ gate).**

**UNIT 3 — sprite producer (MOVE, AFTER-PREREQ).** native_stage_dispatch_* + pc090oj_native_emit_pass.
Writes SAT (double) **and tile worklist (single)**. Prerequisite: READY-isolate the tile worklist (+
confirm publisher doesn't read mutable residency alloc). Target: mainline, end of worker.

**UNIT 4 — plane/scroll/palette/tile producers (MOVE, AFTER-PREREQ).** Prerequisite: READY-isolate each
single-buffered staging (§10). Target: mainline.

**UNIT 5 — publication (STAY).** The 6 `vdp_commit_*`. Keep in IRQ6; make them read **only READY**.

**UNIT 6 — mainline spin (DELETE).** 0x3B0B6/0x3B0FE delay loops serve the old arrangement.

---

## TARGET MINIMAL IRQ6  [design]

```
irq6:
    (L6 auto-ack; acknowledge VDP VINT per hardware requirement)
    if ready_generation != displayed_generation:
        publish READY (the 6 vdp_commit_* reading READY only)
        displayed_generation = ready_generation
    ; else: hold — write ONLY genuinely-required per-VBlank hardware state (see §13)
    tick_pending = 1            ; saturating
    rte
```
Removed from IRQ6: gameplay, AI, collision, all CPU producers, sprite emit, the IPL7 atomic wrapper,
the spin loops.

## TARGET ARCADE MAINLINE  [design]

```
main_wait:
    tst.b tick_pending
    beq.s main_wait
    clr.b tick_pending          ; consume exactly one
    bsr   arcade_frame_worker   ; = converted 0x3A20C..0x3A279 body, now RTS
    ; arcade_frame_worker: gameplay -> producers -> build WORK -> (narrow IPL mask) WORK->READY
    bra.s main_wait
```
Instructions between RTE and tick start: `tst/beq/clr/bsr` (~4). Old arcade delay loops NOT preserved
(class VIII). tick_pending saturating (0/1): no backlog, no catch-up storm, no reentry.

**Overrun behavior (§12):** if VBlank fires mid-worker, IRQ6 preempts, finds no new READY → holds the
picture, sets tick_pending=1, RTE; the worker **resumes from the interrupted PC** and finishes; then,
because tick_pending==1, the next tick begins **immediately** — not after waiting for the next frame
boundary.

---

## DISPLAY LATENCY  [STATIC]

Current: `VBlank N: publish N-1; produce N`. Target: `VBlank N: publish N-1; RTE; mainline produce N;
VBlank N+1: publish N`. **Additional intentional frame latency: NO.** Proof: both publish the frame
produced by the previous worker invocation; moving "produce N" from the post-publication IRQ tail to
the post-RTE mainline keeps the identical N-1→N relationship. The only element to double-check on the
gameplay trace is input: input is latched in IRQ6 (stage 1) and consumed by the tick; in the target it
is latched in the short IRQ6 and consumed by that frame's tick — same age. [HYP until trace confirms no
subsystem bypasses the N-1→N pipeline.]

---

## CPU-WORK ACCOUNTING

- **Actually eliminated:** mainline delay/spin loops (class VIII); the IPL7 raise/restore pair;
  potentially redundant per-VBlank re-publication (frame-hold, §13). Small but real.
- **Rescheduled (not removed):** gameplay, AI, collision, all CPU producers, sprite emit — moved from
  IRQ6 tail to active-display mainline. This is the bulk; it is the **same work**, run preemptibly.
- **Still VBlank-bound:** the 6 `vdp_commit_*` (CRAM/VRAM/SAT/plane/scroll DMA).

Expected benefit: short bounded IRQ6; VBlank can preempt a long tick; over-budget ticks resume
immediately and don't wait for the next boundary; clean frame-hold on a missed deadline instead of a
progressive crawl. **Not a promise of 60 fps** — that depends on whether total per-frame work fits
16.67 ms (Phase 20 / HEAVY trace).

---

## SAFE IMPLEMENTATION ORDER  (disposable test builds; derive from the dependency map)

- **0401** — Instrument only: extend the gameplay trace to close the VDP gate (worker-phase VDP-write
  detector) and capture LIGHT/MEDIUM/HEAVY tick timing + external:IRQ6 ratio. No code move. (If the gate
  shows worker-phase VDP writes, stop and redirect those first.)
- **0402** — READY-isolate the sprite publication state (SAT already double; add WORK/READY tile
  worklist + count; confirm publisher reads no mutable residency alloc). No scheduling move. Verify
  identical output vs 0400.
- **0403** — Move the sprite producer (UNIT 3) to a mainline call; IRQ6 sprite path reads READY only.
  Keep the rest of the worker in IRQ6 for now. Measure.
- **0404** — READY-isolate plane/scroll/palette/tile staging (UNIT 4 small dirty-queue double-buffers).
- **0405** — Convert the arcade worker to an RTS mainline worker (UNIT 1+2): remove IPL7 wrapper, add
  the narrow WORK→READY mask, reduce IRQ6 to the §11 minimal commit + tick_pending + frame-hold.
- **0406** — Delete obsolete spin loops; finalize frame-hold + saturating tick_pending + overrun resume.

Each build: exact change, expected behavior, what Tighe tests, rollback = previous numbered ROM,
compare metric = frame_timing ticks/frame + producer-done V + pub span vs Build 0400.

## PERFORMANCE-BENEFIT ORDER (if everything were already safe)

1. 0405/0406 (full worker out of IRQ6 + short commit) — the whole scheduling win.
2. 0403 (sprite producer out) — largest single CPU chunk off the vblank tail.
3. 0404 (plane/scroll/palette isolation) — enables the rest.
(Prerequisites 0401/0402 are low direct benefit but are mandatory enablers — not low-value.)

---

## REMAINING EVIDENCE GAPS (need the gameplay trace)

- LIGHT/MEDIUM/HEAVY tick duration; whether heavy workload fits 16.67 ms (decides 60 fps vs graceful 30).
- External-VBlank : IRQ6-entry ratio over steady gameplay → promote VINT-loss from LIKELY to PROVEN or
  reclassify as "serviced late."
- Worker-RTE → next-IRQ6 delay (the real idle window size).
- VDP gate: zero worker-phase VDP writes in gameplay (closes the §gate empirically).
- Exact Build-0400 publication sub-phase spans (Phase 11 of the prior task).

None of these change the structural movability conclusions above except the VDP gate, which is a hard
prerequisite for UNIT 2/3 and is explicitly gated.
