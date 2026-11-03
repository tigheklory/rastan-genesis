# ANDY_REVIEW — Build 0356 Frame-Timing Investigation

**Status of this document:** Phase-0 **architecture groundwork** (Andy-owned, static, done now) +
the **review framework** for Cody's measurements. **Cody's `CODY_MEASUREMENTS.md` does not exist
yet**, so the per-conclusion AGREE / DISAGREE / UNKNOWN classifications below are **empty templates
awaiting Cody's evidence** — I have not reviewed measurements that have not been produced, and I have
not invented any. Everything numeric attributed to runtime remains Cody's to measure.

## A. Static control-flow (proven from source, Andy's domain)

1. **`_vblank_service` is the level-6 VBlank autovector** (`boot.s` vector table slot 30 →
   `.long _vblank_service`).
2. **It never RTEs; it tail-jumps to the arcade tick:** `vdp_comm.s:250 jmp (0x00003A208).l`, after
   `rastan_direct_update_inputs`, `vdp_prepare_sprites` (documented as a cheap guard/no-op in
   gameplay), and `dma_publish_frame`.
3. Therefore the **arcade tick (0x3A208) and all native producers it drives run at interrupt mask
   level 6** (the level the CPU raised when IRQ6 was taken), i.e. **VBlank cannot interrupt the game
   logic** — it runs to completion, then some RTE in the copied arcade program lowers the mask.
4. **Native SR masking** (grep of `apps/rastan-direct/src`): only `scene_load.s:97` and
   `fg_tile_cache.s:266` raise to level 7 (`ori.w #0x0700,%sr`) — both display-off scene-reload paths
   (transitional); plus `boot.s` and the crash handlers (`#0x2700`). **No native gameplay hot path
   raises the mask.** The arcade tick's own mask/RTE discipline is in the copied arcade program and is
   **Cody's to locate in the disassembly/Ghidra.**
5. **VDP VINT-enable / display-off** (grep): display-off + VINT-off appear only in the crash handlers
   (`0x8104`) and the display-off scene-load path (`VDP_MODE2_DISPLAY_OFF=0x34`) and the `_do` variant.
   Normal gameplay keeps display + VINT on. **Cody to confirm VINT stays enabled continuously through
   ordinary gameplay and is not toggled off around the late-publication frames.**

## B. Q1 interpretation (Andy-owned): what "86%" actually is

Cody's prior beam harness timestamped **`dma_publish_frame` entry** (the first `VC_MARK`/section
boundary), which occurs **after** `_vblank_service` entry + `rastan_direct_update_inputs` +
`vdp_prepare_sprites`. So "86% of publisher entries occur in active display" is a statement about
**publisher entry**, *not* about the VBlank boundary or IRQ6 service entry. It is therefore
**consistent with either**:
- IRQ6/`_vblank_service` itself being entered late (Case C — masked overrun), **or**
- `_vblank_service` entering promptly but pre-publisher work pushing `dma_publish_frame` into active
  display (Case B).
The harness as used **cannot distinguish these**. Resolving it requires separately timestamping the
VBlank boundary, IRQ6 vector entry, `_vblank_service` entry, and `dma_publish_frame` entry (OPEN Q2).
Given `vdp_prepare_sprites` is documented as a cheap gameplay guard, my prior expectation is Case C,
**but that is a hypothesis, not a measurement.**

## C. Andy's leading hypothesis (to be confirmed/refuted by Cody)

**H-CONT ("masked continuation overrun"):** because the game logic runs as a mask-6 continuation of
the VBlank ISR (A.2/A.3), VBlank does not preempt it; the effective frame rate is
`1 / ceil(total_frame_work / frame_period)` in whole frames. The publisher (now 6–63 ln) is a small
part of `total_frame_work`; the **arcade tick + native producers** are the bulk and still overrun one
frame, so (a) the next VBlank IRQ6 is serviced late (in active display) → the 86%, and (b) the game
advances at < 60 Hz → "still feels slow." Build 0356 helped only to the extent it shaved the publisher.

**This predicts specific measurements** (which is how it can be falsified):
- IRQ6 service entry (not just publisher entry) is itself frequently in active display **and** the
  previous frame's arcade-tick RTE occurs *after* the VBlank boundary → mask-blocked service.
- `total_frame_work` (pre-publisher + publisher + arcade tick + producers) median exceeds one frame
  period (~127,856 dots) in the cases where service is late.
- Arcade gameplay advances : Genesis external frames ≈ the observed publication ratio (~0.6–0.7), i.e.
  the game is running at roughly 36–42 "gameplay Hz," not 60.

If Cody's evidence shows IRQ6 is taken promptly at every VBlank and the arcade tick fits a frame,
**H-CONT is refuted** and the slowness is elsewhere (e.g. the emulator/measurement, or a wait state).

## D. Review of Cody's first pass (completed 2026-09-14)

I verified the load-bearing claims against the **raw evidence and source**, not Cody's summary:
- Case counts + IPM: `frame_timing_reduction.json` — gameplay A=256/B=3/C=749; `interrupted_ipm_histogram={0:1008}`.
- Raw SR/IPM: `frame_timing_events.csv` — `IRQ6_SERVICE_ENTRY` rows show live SR=`2600` (IPM 6),
  **stacked SR=`2000` (IPM 0)**, interrupted PC=`0x03B27E`; `ARCADE_DISPATCH_ENTRY` SR=`2714` (IPM 7).
- Distributions: publisher median 3,028 dots; continuation 157,457; service period 163,381 — from JSON.
- The 49-slot search: **source** `pc090oj_hooks.s:1770 .Lnq_lookup_loop` (`cmp.w 0(%a2,%d0.w),%d3` × up to
  NATIVE_CELLS=49, then a second 49-cell free scan on miss). The `cmp.w` memory-indexed compare
  (~36 cyc/iter × 49 ≈ 1,764 cyc) matches Cody's ~1,751 dots/entry — the search IS the per-entry cost.
- Native path attribution: Ghidra `0x041DAE = FUN_00041dae → actor_family0_render_3d054` (sprite/actor).
- Address discipline: deltas are non-constant (0x03A208−0x03A008=0x200 but 0x051210−0x05100A=0x206) —
  Cody correctly resolved via `address_map.json`, not a fixed offset.

| # | Cody conclusion | Verdict | Evidence / qualification |
|---|---|---|---|
| C1 | "86%" timestamped `dma_publish_frame` entry (0x070250), not IRQ6/VBlank | **AGREE** | JSON event set; raw CSV. |
| C2 | Gameplay A=256/B=3/C=749; IRQ6 **service** entry itself late on 749 | **AGREE** | JSON case_counts + raw SR/IPM. The "one VBlank opportunity inferred per frame (no VDP-assert-edge tap)" is disclosed and does not weaken it — the RTE-precedes-service + IPM=0/6 evidence is direct. |
| C3 | Copied handler IPM 7→6, RTE at arcade 0x03A07E; RTE precedes service 67–84 dots | **AGREE** | Raw SR=2714/2700, stacked 2000; JSON arcade_mask_to_rte. |
| C4 | VINT stays enabled (3 reg1 writes, all bit5) | **AGREE-WITH-QUALIFICATION** | Bounded to observed writes; harness can't tap the assert edge, so this shows VINT was never *disabled*, not that it asserted every frame — adequate for H-CONT. |
| C5 | 1,800 frames : 1,257 services : 1,008 gameplay advances | **AGREE-WITH-QUALIFICATION** | Proven via one `0x04210E` per dispatch + 383/383 supplement. The 1,008 spans mixed startup/gameplay, so there is **no single steady gameplay-Hz**; the 41.84/s is a service rate. Keep that caveat. |
| C6 | Continuation = native-sprite early-update (~82–91k dots) + copied state-dispatch (~53–56k) | **AGREE** | JSON arcade_prefix/state_dispatch; native attribution via 0x041DAE. |
| C7 | Executing real work; no poll loop; RTE→service tiny | **AGREE-WITH-QUALIFICATION** | Correct that timing alone finds no *wait*. But I add a source finding it did not: the 49-slot per-frame residency search **is avoidable recomputation** (a runtime allocator rebuilding a code→slot map every frame) — see §F. |
| C8 | Short mainline sync loop (0x03A1A8 / 0x03B27E), not the cost | **AGREE** | Interrupted-PC = 0x03B27E in raw CSV; only 67–84 dots post-RTE. It is a legitimate small idle/sync wait, not removable hardware-tail. |
| C9 | Finalizer 137.9 ln median; back/enemy lane 86.2; r=0.90; ~3.59 ln/entry; 49-slot search | **AGREE** (sprite finalizer) **/ AGREE-WITH-QUALIFICATION** (Plane A/B producer CPU = bounded UNKNOWN, not isolated). Not decisive for the #1 target. |
| C10 | VC_MARK overhead ~379 dots / 0.777 ln, scaffolding | **AGREE** | Matches prior 0356 audit. Remove in next meaningful production build only. |
| — | Old ~258-line publisher = **falsified** (invalid `%262` on 8-bit V-counter) | **AGREE** | I already retired my own number; Cody's physical-beam method is authoritative. **The theory that VBlank *publication* is the primary slowdown cause is retired.** |

## E. Frame-model assessment (Q3) — architecture-lead call

The Level-6 continuation is **intentional preservation of the original arcade frame model**, not a
translation artifact: original Rastan ran its frame inside the 68000 VBlank ISR (arcade `0x03A008`
= the tick), and the translation preserves it exactly (`jmp 0x03A208` → arcade tick → arcade RTE at
`0x03A07E`). On the original arcade hardware this ISR fit within one 60 Hz frame. It overruns on
Genesis because **native compatibility work was added inside the ISR** — chiefly the sprite finalizer
that reproduces, in software, the residency/SAT work the arcade's PC090OJ chip did in silicon.

Therefore:
- **Strategy A (shrink the chain to fit one frame) is strongly preferred** and preserves the arcade
  frame/timing contract untouched.
- **Strategy B (move game/producer work out of the non-preemptible ISR to allow nested VBlanks) is
  NOT justified now.** It would change the arcade's frame ownership/timing contract, and we have no
  proof the arcade gameplay semantics survive a re-entrant/deferred model. Do not recommend B until
  that semantic contract is proven. Determine A's sufficiency first (§G).

## F. The #1 target, classified (arcade semantics vs native tail)

The finalizer's per-emitted-entry **49-slot linear residency search** is **Genesis-native
compatibility work** (it manages Plane-pattern VRAM that the arcade did in hardware), **not** arcade
gameplay semantics. That is exactly the class we may optimize. It is a runtime allocator recomputing
a `code→slot` mapping every frame (O(emitted × 49)). The architecturally-correct fix is a **bounded
O(1) `code→slot` reverse index** (maintained on allocation), or — aligned with the offline-compiler
target — a **phase/epoch-precomputed residency table** so residency is not rebuilt per frame. This
must preserve: lane/priority ordering, SAT ordering, dynamic flips, bounded 12-entry worklist,
pattern-residency correctness, the Palette-Tool authority, and context reindex profiles. **Not** a
giant Cartesian LUT — a per-code slot index (≤4096 codes → 1 byte, or a small hash) is bounded.

## G. Frame-deficit math (Q8) — and the honest gap

Median chain = 334.652 ln vs a 262-line frame ⇒ must recover **≈73 lines** just to fit, plus headroom
and correct publisher-vs-VBlank positioning (realistically target ~90–110 ln of recovery). The
finalizer median is ~138 ln (900-frame supplement) / the native early-update is ~168 ln (full trace).
**Whether the #1 fix ALONE crosses the one-frame median threshold is currently UNKNOWN**, because the
finalizer's cost is `fixed (setup ~11.7 + HUD ~12.5 + bookkeeping) + per-entry`, and I cannot cleanly
separate, from existing data, how much of the ~3.59 ln/entry is the **search** (recoverable) vs the
**coordinate/flip/bbox-clip transform + SAT write** (not recoverable by an index). My cycle estimate
says the search is roughly half-to-most of per-entry, which puts the post-fix chain **near** 262 ±
tens of lines — i.e. it could just cross, or just miss, the median threshold. That ambiguity
**materially changes** whether #1 suffices or whether #1 + a copied-core target are both needed →
this is the one item I reopen for Cody (§ OPEN A-13). The P95/worst spikes (0x05100A → 172 ln; worst
chain 861 ln) will **not** be fixed by the finalizer alone regardless.

## H. Copied-core hotspots (Q6) — classification status
`0x05100A` (median 45 ln, **P95 172 ln** — a large data-dependent spike), `0x040B66` (23 ln),
`0x0420E6` (19 ln) are copied arcade code. I **cannot** classify their sub-purpose from current Ghidra
exports (the function inventory's ranges are tiny leaf stubs that do not contain these PCs; the
full-listing did not resolve them as code at these addresses). **Verdict: UNKNOWN**, agreeing with
Cody. The 0x05100A P95 spike is *consistent with* a variable-iteration loop scaling with active
object/enemy count (which would also drive the sprite count) — i.e. likely legitimate gameplay object
processing — but that is a **hypothesis**, not established, and resolving it is deeper Ghidra/semantic
work (mine, later), **not** a Cody trace pass, and **not** a blocker for the #1 decision. Per CLAUDE.md
we must not touch copied gameplay semantics without proof.

## E. Methodology cautions I will hold Cody to
- Do not report "VBlank is delayed" unless IRQ6 **service entry** (not publisher entry) is shown late.
- The mask-6 continuation means "publisher in active display" ≠ "IRQ6 late" — keep them separate.
- Attribute the arcade-tick cost to **arcade gameplay semantics vs hardware-tail vs native
  compatibility vs avoidable recomputation** (Q13); a big number that is genuine arcade gameplay is
  not an optimization target the same way a translated busy-wait is.
- Separate STEADY / CONDITIONAL / TRANSITION; rank by whole-frame budget share, not local %.
- If H-CONT is confirmed, the architectural implication is significant and is **mine to assess**: the
  fix is not "optimize the publisher" but either shrink the arcade-tick/producer work below one frame
  or change the frame model so long work does not block VBlank service — evaluated against arcade
  semantic safety before any recommendation.
