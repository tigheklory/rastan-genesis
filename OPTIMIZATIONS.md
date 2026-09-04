# OPTIMIZATIONS.md — Rastan Genesis Performance Optimization Registry

Living registry of **performance optimizations** for the Rastan Genesis port. Add an entry when an
optimization is discovered (even if not yet implemented); update its Status + Build when implemented.
This is the single place we track *what could be faster*, *how much it might save*, and *when we did it*.

The port's central performance fact: the arcade offloaded tilemap + sprite rendering to dedicated
chips (PC080SN, PC090OJ) that the arcade 68000 fed with **cheap register/RAM writes**. The Genesis
has no such chips, so **our 68000 does that work in software** (build nametables, expand sprites,
convert palettes, drive DMA). The arcade **game logic** is translated byte-for-byte and costs the
same on both machines; therefore **the entire per-frame cost delta is our native production code +
DMA**, and that is what this registry targets.

## Strategy: accumulation, not a single hero fix ("life by a thousand cuts")
Performance here is won by **headroom**, and headroom is **additive**. No single optimization has to be
huge; many recurring per-frame savings **compound** into the budget needed to hold 60 fps. Priorities:
1. **Per-frame *recurring* cuts first** — a cycle saved in the sprite/plane/DMA path is saved dozens of
   times per frame, 60×/sec. These compound; one-time/event-driven cuts (e.g. palette conversion) don't,
   though they're still worth banking.
2. **Bank the zero-risk *subtractive* cuts freely** — prebaking (OPT-001, OPT-003) moves work to the
   Python build step: runtime gets faster **and** the ROM gets smaller/cleaner. Low risk, do steadily.
3. **Measure to count the cuts and find the fattest** (OPT-007) — measurement aims the program; it does
   not replace it. Track each optimization's saving and keep a running total below.

### The three levers (Tighe)
Every optimization here is one of three moves, and they reinforce each other:
- **Schedule** — move *essential* code so it runs **inside vblank**. Only VDP access is timing-sensitive;
  arcade logic may spill into active display. This is OPT-005 (essential-first split) and OPT-004(b).
- **Optimize** — spend fewer cycles per frame in the native production paths so the essential work
  actually *fits* in the vblank window (OPT-003/004/006).
- **Bake** — precompute at build time in the Python scripts so the runtime does an **indexed load**, not
  a calculation (OPT-001/003/006). "As little runtime calculation/operation as possible."

**Invariant this program must restore (CRAM):** every CRAM word must be committed while `VCounter ≥ $E0`
(vblank). A CRAM write once the beam re-enters active display is drawn by the VDP as a stray coloured dot
at the beam position — this *is* the "noise band" and the lower-screen coloured pixels (see OPT-004
evidence). VRAM DMA is display-safe and is **not** subject to this; CRAM is. Schedule + Optimize shrink the
frame until CRAM naturally completes in blanking; the V-counter gate is only the belt-and-suspenders guard.

## Cumulative savings tracker
As each optimization is implemented, record its **measured cycles/frame saved** (or a labeled estimate)
and add it to the running total, so the accumulated headroom is always visible.

| Running total cycles/frame saved (implemented) | Frame budget (~) | % recovered |
|---|---|---|
| OPT-008 (Build 0342): not a per-frame cut but a **transition-DMA reduction** — R1/P1 residency 7→5 epochs / 6→4 transitions (two boundary DMAs eliminated); the DMA-halt saving is per-boundary, not per-frame. Exact cycles pending measurement. | ~127,840 cyc/frame @ 7.67 MHz / 60 Hz | — |

## How to use
- **Discover:** add an entry with Status `PROPOSED`, a concrete code reference, and an impact estimate.
- **Implement:** change Status to `IMPLEMENTED`, record the **Build number** and ROM SHA, and note the measured effect.
- Also valid: `DEFERRED` (real but not now), `REJECTED` (investigated, not worth it — say why), `MEASURING` (blocked on data).
- **Measure before ranking.** Instruction count alone is misleading — **68k→VRAM/CRAM DMA halts the CPU**, so the true metric is *cycles* (native-production instructions **+ DMA-halt stalls**). See OPT-004.

## Impact scale (rough, until measured)
`HIGH` = plausibly a large share of per-frame budget · `MED` = worth doing · `LOW` = small/occasional but free/clean.

---

## Summary

| ID | Title | Subsystem | Impact | Status | Build |
|---|---|---|---|---|---|
| OPT-001 | Prebake static palette conversions (offline xBGR-555 → CRAM) | palette | LOW–MED | PROPOSED | — |
| OPT-002 | Collapse runtime 2-step color conversion to 1 step | palette | LOW | PROPOSED | — |
| OPT-003 | Prebake per-piece palette line (kill per-piece route-table scan) | sprites | MED–HIGH | STOPPED (gate-blocked) | — (no numbered ROM) |
| OPT-004 | Reduce DMA-halt cost (volume + land DMA in vblank) | vblank/DMA | HIGH (suspected) | MEASURING | — |
| OPT-005 | Split VBlank: essential VDP transfers vs deferred arcade logic | vblank | HIGH (if VINT-deferred) | MEASURING | — |
| OPT-006 | Prebake fixed per-descriptor piece coordinate offsets | sprites | LOW | PROPOSED | — |
| OPT-007 | Per-frame cycle-cost profiler/visualization (tool) | tooling | (enables all) | PARTIAL | 0337 bar, 0339 metric |
| OPT-008 | Reclaim 0xD000 gap + unused Window VRAM -> Layer-A 484->676 contiguous (7->5 epochs) | vram/vblank | HIGH | IMPLEMENTED | 0342 |

---

## OPT-001 — Prebake static palette conversions (offline xBGR-555 → CRAM)
- **Subsystem:** palette (`palette_hooks.s`)
- **Status:** PROPOSED · **Impact:** LOW–MED
- **Problem:** `.Lxbgr555_to_cram` (`palette_hooks.s:108`, **20 instructions/color**) plus the inline arcade `0RGB444 → xBGR555` step (~11 instrs) means **~31 instructions across two conversions per color**, at **7 call sites** (`:207, :270, :282, :316, :426`, and the water/`03ab00` paths). xBGR-555 should not exist in the ROM at runtime at all.
- **Fix:** any palette whose source is a **ROM table** — the water animation frames (`0x59B7A`), the per-segment stage palettes loaded via the pointer tables — is a deterministic function of ROM bytes. Convert them to **final CRAM words at build time (Python)** and have the runtime **copy** them. The Genesis then works in CRAM, never xBGR-555, for all static palette data.
- **Estimated saving:** small per-frame in steady gameplay (palette staging is event-driven since Build 0329), but real at scene loads / palette events, and removes conversion code + xBGR-555 from the ROM.
- **Notes:** must distinguish ROM-sourced (prebakeable) from arcade-runtime-computed palettes (see OPT-002).

## OPT-002 — Collapse runtime 2-step color conversion to 1 step
- **Subsystem:** palette (`palette_hooks.s`)
- **Status:** PROPOSED · **Impact:** LOW
- **Problem:** for genuinely runtime-computed colors (not prebakeable), the hooks still do `0RGB444 → xBGR555 → CRAM` (two conversions). Both are simple bit rearrangements.
- **Fix:** a single `0RGB444 → CRAM` bit-rearrangement (~halves per-color conversion cost). Keep only where OPT-001 can't prebake.
- **Notes:** Build 55 "locked" the 2-step path for MAME-parity reasons; verify the 1-step is algebraically identical before adopting.

## OPT-003 — Prebake per-piece palette line (eliminate per-piece route-table scan)
- **Subsystem:** sprites (`pc090oj_hooks.s`)
- **Status:** STOPPED — implemented + proven output-identical, blocked by the seven-epoch gate; **NOT in any numbered production ROM** · **Impact:** MED–HIGH (scales with emitted sprite pieces — the per-frame hot path)
- **Problem:** `.Lnative_palsel` (`pc090oj_hooks.s`) computes each emitted piece's Genesis palette line **at runtime**: bank special-cases + a call to `palette_route_lookup`, which **linearly scans the route table** every piece. With ~28 pieces/frame average (up to 72), that's a table scan per piece, every frame.
- **Fix (implemented):** baked the exact current `(scene_id, effective_bank) → line` result into a generated 4×128 direct LUT (`out/pc090oj_palsel_lut.inc`, generator `tools/translation/gen_pc090oj_palsel_lut.py`, source-of-truth = `palette_route_table` + the 0x30→2 special case + `(eb>>4)&3` fallback). Runtime does one indexed byte load; the per-piece linear scan is gone. DERIVED artifact, not a registry.
- **Offline equivalence:** 512 combinations, **0 mismatches**; spot checks 0x30/0x33/0x36/miss/frontend all correct.
- **BLOCKED BY (root cause OPEN, two prior hypotheses refuted):** OPT-003 deterministically fails the seven-epoch gate at epoch 1 (Plane-A code 0x034C, expected slot 0x04E0, actual 0x0000); reference passes. **Refuted:** (1) gate sampling-fragility (fails at a stable 8-frame boundary); (2) native-BSS/arcade-workram collision — a **matched-config** rebuild shows OPT-003 moves **zero** BSS symbols (`fg_boundary_active_lut`=0xFF6188 in both; the earlier "−8 shift" was a score-variant-vs-release symbol-map artifact). OPT-003 changes only **code/rodata layout** (`fg_boundary_packages` −16, `pc090oj_native_emit_pass` −14, +512B LUT). **Divergence isolated (Build 0342 investigation):** `active_lut[0x034C]` is correctly written at frame 327 then **clobbered to 0 at the frame-328 epoch-change install** in OPT-003 only — despite byte-identical package data (49732 bytes), a correctly-relocated package pointer (no stale address survives), identical BSS, and identical installer code. Exact clobbering instruction **not capturable** (DRC bypasses Lua write-taps; headless debugger watchpoint didn't fire). Pinned-LUT experiment inconclusive (broke the canonical coverage invariant). **Open stakes:** the gate reaches epoch 1 by *synthetic installer injection*; whether the clobber occurs in *natural gameplay* is untested. Next: validate OPT-003 in natural gameplay + capture the clobber PC via a non-DRC/interpreter trace. See `docs/design/Andy_opt003_code_rodata_layout_divergence_and_landing.md`.
- **Estimated saving (NOT measured):** removes a per-piece linear scan from the busiest per-frame loop → ~tens of cycles/piece, order ~10³ cycles/frame at ~28 pieces (more at 72). No production saving recorded until a numbered OPT-003 build passes the gate.
- **Build-number note:** a differential `make all` accidentally consumed **Build 0340** with the *non*-OPT-003 revert ROM; any OPT-003 candidate must be **0341+**. Decision pending (gate settle-window vs re-baseline; leave 0340 vs roll back).

## OPT-004 — Reduce DMA-halt cost (volume + land DMA in vblank)
- **Subsystem:** vblank / DMA (`vdp_comm.s` `_vblank_service` + the commit routines)
- **Status:** MEASURING · **Impact:** HIGH (suspected #1 per-frame cost)
- **Problem:** 68k→VRAM/CRAM **DMA halts the 68000** for the whole transfer. We DMA plane rows + the sprite SAT + the palette **every frame**, and with the display left ON (Build 0227) much of it runs **during active display, where DMA is far slower per word** — stalling the CPU longer. The arcade never paid this (chips read their own RAM). This is *cycles*, not instructions, so an instruction-count chart misses it.
- **Fix candidates:** (a) commit only rows/SAT/palette that actually changed (minimize word volume); (b) get the CRAM/plane DMA into the true vblank window (also fixes the noise band); (c) reconsider display-on vs a bounded blank for the heaviest transfer.
- **Blocked on:** OPT-007 measurement (per-frame DMA word count + display-on rate → halt cycles).
- **CONFIRMED evidence (2026-09-02, GENESIS NTSC via Exodus).** The lower-screen coloured pixels/dots
  ("individual pixels in the lower right", dots over gameplay dirt, welded to the top edge of the `_d`
  green backdrop band) are **CRAM writes executing while the beam is in active display** — not a plane,
  not a sprite. Ruled out by elimination + register read: Window is disabled (**reg $11 = $00, reg $12 =
  $00**), so nothing overlays Layer A via the window; the parked CREDIT text is **Layer B** (visible in the
  Plane-B viewer); and the dots carry **no SAT bounding-box outline** in Exodus, so they are not sprites.
  What remains is the Build-0336 unconditional **64-word 68k→CRAM palette DMA** (`vdp_comm.s:177-183`,
  multicolour) plus the `_d` bar's backdrop (CRAM entry 0) writes, crossing the active/blank boundary. The
  VDP FIFO/Port Monitor shows these as **code `03` (CRAM write)**; reading their **VCounter** shows writes
  at `V < $E0` = active display = the dots. This is the same root as the vertical noise band.
- **Direct fix (this optimization):** guarantee CRAM commit completes inside vblank — order it first and/or
  gate it on `VCounter ≥ $E0` — and, per the three levers above, shrink the frame (Optimize/Bake) so the
  essential VDP work fits in blanking rather than relying on the gate. Stage the V-counter guard
  build-flagged first (watch the dots vanish) before touching the release commit.

## OPT-005 — Split VBlank: essential VDP transfers vs deferred arcade logic
- **Subsystem:** vblank architecture (`vdp_comm.s`, arcade handler `0x3A208`)
- **Status:** MEASURING · **Impact:** HIGH *if* the game is VINT-deferred; SMOOTHNESS/noise-fix if CPU-bound
- **Problem/idea (Tighe):** everything (Genesis servicing + full arcade game logic) runs in one long VINT-triggered handler. If the arcade masks interrupts during logic (KF-012), the essential VDP transfers effectively run late (into active display → noise + serialization).
- **Fix:** a short "essential VBlank" (VDP CRAM/VRAM/SAT/scroll transfers) that runs first and returns; the arcade game logic ("low-priority") runs immediately after — it may finish in vblank or spill into active display (allowed; only VDP access is timing-sensitive). Accept **1 frame of output lag** (already implied by the staged double-buffer; **no new RAM**).
- **Honest caveat:** reordering does **not** create CPU cycles. If CPU-bound (per-frame work > 1 frame), it fixes the band and smooths degradation (e.g., ~46 Hz instead of hard 30 Hz) but does **not** restore full speed — that needs work reduction (OPT-003/004). Confirm CPU-bound vs deferred via OPT-007 first.

## OPT-006 — Prebake fixed per-descriptor piece coordinate offsets
- **Subsystem:** sprites (`pc090oj_hooks.s`)
- **Status:** PROPOSED · **Impact:** LOW
- **Problem:** per-piece coordinate math (`pc090oj_hooks.s:587–644`) adds base X/Y/tile (`a4@22/26/30`) + sign-extended descriptor offsets + `PC090OJ_TO_GENESIS_Y_OFFSET` + type-0x70 adjustments, per piece.
- **Fix:** the *descriptor-local* offsets (and the fixed Y/X origin bias, type-0x70 adjust) are constant and can be **pre-combined offline** into the descriptor data, leaving only the runtime `+ base X/Y` (actor position). Partial win.
- **Notes:** lower priority than OPT-003; do alongside the `(code,bank)` reindex work.

## OPT-007 — Per-frame cycle-cost profiler / visualization (enabling tool)
- **Subsystem:** tooling (non-production)
- **Status:** PROPOSED · **Impact:** enables correct targeting of all others
- **Goal:** a read-only measurement + HTML chart artifact showing per-frame cost by subsystem = **native-production instructions + DMA-halt cycles**, built from real static instruction counts × measured dynamic counts (sprite pieces/frame, dirty rows/frame, DMA words/frame) + computed DMA-halt cycles. Ranked, with each bar annotated by its OPT-### opportunity.
- **Why first:** confirms whether the game is CPU-bound or VINT-deferred, and whether the #1 cost is DMA-halt vs sprite expansion vs plane production — so we optimize the biggest lever instead of guessing. Exact full-instruction tracing is not feasible on the Genesis DRC core; this cost-model + DMA-cycle computation is the honest substitute.
- **PARTIAL — in-ROM CPU-load raster bar (Build 0337).** `RASTAN_DIAG_CPU_BAR` build flag: `_vblank_service` sets the VDP backdrop (CRAM 0) bright across the Genesis VBlank servicing window (sprite + plane + scroll VDP commits/DMA) and clears it when done, so the on-screen coloured band shows that servicing cost and whether it overruns vblank into active display — visible in any emulator or a screenshot, and it captures DMA-halt time. **Dual-build convention:** every `make` now emits both the numbered release ROM (`_NNNN.bin`, bar off) and a same-numbered diagnostic ROM (`_NNNN_d.bin`, bar on); the `_d` reuses the number and is never numbered/ledgered itself. Caveat: the bar currently marks the *Genesis servicing* window (post-palette-DMA → end of commits), not the full frame incl. arcade logic; and it's a relative/visual indicator (perturbs timing by a few instructions).
- **DONE — numeric score metric (Build 0338, `_s` build).** `RASTAN_DIAG_SCORE_METRIC` flag: _vblank_service measures the peak active-display scanlines the Genesis servicing overran (V-counter at servicing end; 0 = fits in vblank), self-initialising running max, written as 3-digit BCD to the P1 score (0xFF011E) so the 1UP HUD shows a stable NUMBER. **Triple-build convention:** every `make` now emits `_NNNN.bin` (release), `_NNNN_d.bin` (bar), `_NNNN_s.bin` (metric) sharing one number; `_d`/`_s` are postpatch-only copies, never numbered/ledgered.
- **STILL PENDING:** the full-frame bar/metric (currently measures only the Genesis servicing window, not the arcade logic — needs the arcade idle/rte hook), a game-logic-fps metric, and the scripted headless MAME meter feeding the cumulative-savings tracker.

---

## OPT-008 — Reclaim unused VRAM → contiguous 676-slot Layer-A (fewer residency transitions)
- **Subsystem:** VRAM layout / vblank DMA (`compile_pc080sn_genesis.py`, generated boundary data)
- **Status:** IMPLEMENTED · **Build 0342** · **Impact:** HIGH (transition DMA-halt reduction)
- **Problem:** Layer-A residency was capped at 484 slots (855–1338), forcing R1/P1 into 7 stable epochs with
  6 residency transitions; each transition DMAs the incoming epoch's non-retained patterns (68k halted).
- **Fix (offline, clean repack):** reclaim the permanently-unused 0xD000–0xDFFF gap (128 slots) and the
  unused Window region 0xF000–0xF7FF (64 slots) as **static Plane-B** pattern storage (Plane-B split into
  [1–662] ∪ [1664–1791] ∪ [1920–1983], source-code ordered), freeing a **contiguous 663–1338 = 676-slot**
  Layer-A window. Recompiled residency at 676 → **5 stable epochs, 4 transitions** (both proven streamed
  transitions retained; two simple boundaries eliminated). Sprites 1339–1535 unchanged; no runtime
  allocator/search/LRU; within-epoch DMA still 0. Generated boundary binary 49,732→47,268 B.
- **Result:** 7→5 epochs, 6→4 transitions. Per-boundary DMA-halt saving (exact cycles pending the scripted
  meter). Also shrinks the ROM. See `docs/design/Andy_clean_vram_repack_676_contiguous_layerA.md`.
- **Note:** implemented as the low-risk 5-epoch (kept both streamed transitions) rather than the 4-epoch
  minimum; eliminating the rope streamed transition (→4 epochs) is a further available cut. OPT-003 was
  reverted for this build (its 0x034C clobber fails the epoch gate); 0342 does not contain OPT-003.

---

## Implementation log (append on each implemented optimization)
- **OPT-008 — Build 0342** (sha256 `dea2711b749cae22…`; `_d` `33db4980…`, `_s` `30c57ab8…`): clean VRAM
  repack; Layer-A 484→676 contiguous; R1/P1 residency 7→5 epochs / 6→4 transitions. All gates PASS
  (transition-retention, canonical, gameplay-entry, seven-epoch). Effect: transition-DMA reduction
  (per-boundary); exact cycles/frame not yet measured. UNVERIFIED pending Tighe gameplay.