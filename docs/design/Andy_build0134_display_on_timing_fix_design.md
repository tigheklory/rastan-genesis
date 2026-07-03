# Andy — Build 0134 DISPLAY_ON Timing Fix Design (Design Only)

**Author:** Andy
**Date:** 2026-07-02
**Baseline:** Build 0134 (byte-identical to Build 0132), SHA256 `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`.
**Priors:** `Cody_build0133_hv_vcounter_display_on_diagnostic.md`; `Andy_build0132_residency_cache_static_review.md`; `Cody_pc090oj_persistent_sprite_tile_dma_cache_build0132.md`; `Andy_build0130_graphics_timing_budget_analysis.md`.
**Scope:** DESIGN ONLY. No implementation/edit/build/diagnostic-ROM. All addresses Genesis-native (`runtime_genesis_pc`); no arcade↔genesis arithmetic. Labels **[OBS]** verified from Build 0134 source; **[INT]** interpretation.

> **BOTTOM LINE:** The commit chain (`0x03`→`0x0A`) completes **inside** VBlank; only the DISPLAY_ON write (`0x0B`) lands late, and the diagnostic exaggerates that lateness (ring overhead between `0x0A` and `0x0B`) but does not invent it. The narrowest safe fix is a **pure reorder** of `_vblank_service`: issue **DISPLAY_ON immediately after `vdp_commit_sprites`** (the last stage that mandatorily needs display disabled — bulk VRAM tile/SAT DMA), and run the small **palette (CRAM)** and **scroll (VSRAM + a 2-word HScroll)** commits *after* DISPLAY_ON, still within VBlank. This reclaims the palette+scroll wall-clock from the display-off window so DISPLAY_ON lands inside VBlank on more frames. Zero net code-size change; no VRAM/plane/sprite/ownership/cache risk. **Recommend Option D (reorder).**

---

## == PHASE 0 ==

- **Relevant priors:** Build 0130 timing analysis (late-DISPLAY_ON SUPPORTED; commit body runs inside VBlank, only 0x0B late); residency cache verified correct (churn removed); PC080SN VRAM ownership (1024..1343 sprite-exclusive); Exodus Build 132 layer-separated view (planes/sprites complete → defect is display-output timing, not content).
- **High-rediscovery hazards:** (1) the diagnostic ring overhead between checkpoints over-estimates 0x0A→0x0B lateness — do not treat measured scanline lateness as production truth; (2) VRAM name-table / SAT / tile-pattern writes MUST stay display-off (they corrupt the scanned frame), so only CRAM/VSRAM/tiny-VRAM stages may move after DISPLAY_ON; (3) KF-021 (staged SAT ≠ truth) — unaffected.
- **Task classification:** Narrow display-timing fix DESIGN for OPEN-001 (built on the completed OPEN-024 cache).
- **Contradiction detected:** NO. (The "0x0A inside VBlank but 0x0B late" pair is explained by the ring-overhead caveat + DISPLAY_ON being structurally at the tail.)
- **Open/Closed pre-check:** OPEN-001 primary (title display band), OPEN-024 context (cache done); not closing.
- **Build 0134 baseline:** verified `989b17e8…b611832`, byte-identical to 0132; Build 0133 was temporary diagnostic, reverted.
- **Build 0133 diagnostic summary:** checkpoint 0x0A (after scroll) inside VBlank for all anchors; 0x0B (after DISPLAY_ON) usually after VBlank — no-input 8/8 late, coin/start 7/9 late, total 15/17; VCounter at DISPLAY_ON varied.
- **diagnostic caveat:** the ring records between 0x0A and 0x0B, adding overhead that pushes the measured DISPLAY_ON later than production; exact 0x0A→0x0B scanline lateness is not production-accurate, but the production visual band + 15/17 aggregate still support live late-DISPLAY_ON.
- **address_map.json loaded:** YES. **arithmetic offset used as proof:** NO.

---

## == Q1 REMAINING LATENESS ==

- **last inside-VBlank checkpoint:** **0x0A** (after `vdp_commit_scroll`) — inside VBlank for every captured anchor. This means the *entire* commit chain (tiles→BG→FG→sprites→palette→scroll) finishes within VBlank even with diagnostic overhead.
- **late checkpoint:** **0x0B** (after DISPLAY_ON) — after VBlank bit cleared in 15/17 anchors.
- **production code between (0x0A→0x0B):** only the DISPLAY_ON register write — `moveq #MODE2,%d0; moveq #DISPLAY_ON,%d1; bsr vdp_set_reg` (one word to VDP_CTRL) [OBS vdp_comm.s:179-181].
- **diagnostic overhead caveat:** the ring's per-checkpoint recording sits *between* 0x0A and 0x0B in the diagnostic build, so it inflates the measured 0x0A→0x0B gap; production has no such code there, so production DISPLAY_ON is *less* late than the diagnostic shows — but the production band proves it is still somewhat late.
- **classification (Q1.5):** **"DISPLAY_ON placed too late in the service" + "too much remaining VBlank work before DISPLAY_ON," with diagnostic overhead exaggerating but not inventing it.** Ruled out: not another display-off owner (`load_scene_tiles` is transition-only, main-loop; not in `_vblank_service`); not a layer/priority issue (Exodus shows planes+sprites complete). The commit uses most of VBlank and DISPLAY_ON sits at the very tail (after palette+scroll), so it lands at/just past VBlank end.

---

## == Q2 OPTION ANALYSIS ==

VDP rule used throughout: the MODE2 display-enable bit gates raster *output*, not VRAM *write access*. During **VBlank**, VRAM/CRAM/VSRAM are freely writable whether display-enable is on or off. Bulk VRAM writes to *scanned* structures (name tables, SAT, tile patterns) must not slip into **active display**, which is why they run under display-off. CRAM/VSRAM/HScroll writes are small and, done in VBlank, are safe with display already enabled. 68k is bus-stalled during VRAM DMA, so DMA completes before the next instruction.

**Option A — move DISPLAY_ON earlier (before final low-risk commits):**
- exact placement: after `bsr vdp_commit_sprites` (vdp_comm.s:169), before the palette block.
- visual impact: DISPLAY_ON issued earlier → inside VBlank on more frames → band reduced/removed.
- VRAM risk: none — all bulk VRAM DMA (tiles/BG/FG/sprite/SAT) already completed before this point.
- CRAM/VSRAM/register risk: palette(CRAM)+scroll(VSRAM/HScroll) now after DISPLAY_ON but still in VBlank → safe.
- Plane A/B risk: none (name-table writes done under display-off).
- sprites/SAT risk: none (SAT DMA done before DISPLAY_ON).
- story/title transition risk: low (scene loads use their own display-off in main-loop, untouched).
- 60 Hz preserved: YES. architecture preserved: YES. narrow enough: YES (relocate one 3-instruction block).
- **This is the concrete instance of the recommended fix; = Option D's placement.**

**Option B — keep DISPLAY_ON at end, reduce remaining VBlank work:**
- targets: mirror-scan CPU (256 entries), SAT DMA (320 words fixed), BG/FG strips, palette/scroll.
- visual impact: indirect; shrinks the window but leaves DISPLAY_ON structurally last.
- risks: reducing SAT DMA (e.g., partial SAT) or mirror-scan touches sprite correctness — broader than a timing fix; higher regression risk to sprites/SAT.
- 60 Hz: YES. architecture: at risk if SAT/scan changed. narrow: NO (touches sprite pipeline). **Defer — not the narrowest.**

**Option C — conditional display-off (only when heavy VRAM/DMA pending):**
- placement: guard the DISPLAY_OFF/ON around a "heavy work pending" test (dirty tiles/BG/FG/sprite-DMA).
- problem: SAT DMA is **unconditional every frame** (`.Lvcs_sat_dma`), and mid-active-display SAT DMA risks sprite glitches → cannot skip display-off without first proving SAT DMA is display-on-safe or making it conditional (broader).
- risks: high (must prove every unconditional VRAM op is display-on-safe). architecture: OK. narrow: NO. **Reject as primary.**

**Option D — split display-off-required vs display-on-safe work:**
- placement: DISPLAY_ON right after the last display-off-required stage (`vdp_commit_sprites`); then palette + scroll with display enabled (still VBlank).
- visual impact: same as A, with an explicit safety rationale per stage (Q3).
- VRAM/CRAM/VSRAM/plane/sprite risks: none for the moved stages (CRAM safe; VSRAM safe; the one HScroll-table 2-word VRAM write is tiny and VBlank-timed — see Q4 fallback).
- 60 Hz: YES. architecture: YES. narrow: YES. **RECOMMENDED (subsumes A).**

**Option E — other narrow fix:** e.g., issue DISPLAY_ON before scroll but after palette, or duplicate DISPLAY_ON — no advantage over D and adds code. Not recommended.

---

## == Q3 DISPLAY-OFF REQUIREMENT BY STAGE ==

[OBS vdp_comm.s + VDP layout: Plane B nametable 0xC000, Plane A 0xE000, sprite tiles 0x8000, SAT 0xF800, HScroll 0xFC00, tile patterns 0x20.]

- **input update** (`rastan_direct_update_inputs`): no VDP writes → display-agnostic (runs before DISPLAY_OFF).
- **DISPLAY_OFF register write:** the control itself.
- **tile commit** (patterns → VRAM 0x20): **must happen while display disabled** (pattern VRAM write; conservative — could corrupt scanned tiles).
- **BG commit** (Plane B nametable 0xC000): **must happen while display disabled** (writing the visible tilemap mid-scan corrupts Plane B).
- **FG commit** (Plane A nametable 0xE000): **must happen while display disabled.**
- **sprite/SAT commit** (sprite tile DMA → 0x8000; SAT DMA → 0xF800): **must happen while display disabled** (bulk VRAM DMA + mid-scan SAT corruption). **← last display-off-required stage.**
- **palette commit** (CRAM, `vdp_commit_palette`): **should happen in VBlank but display can already be enabled** (CRAM writes are VBlank-safe regardless of display bit; conditional on `palette_dirty`).
- **scroll commit** (VSRAM + 2-word HScroll VRAM at 0xFC00, `vdp_commit_scroll`): **should happen in VBlank, display can already be enabled** — VSRAM safe; the tiny HScroll-table VRAM write is the single item to verify on hardware (Q4 fallback covers it).
- **DISPLAY_ON register write:** the fix point (moves to right after sprite/SAT commit).
- **arcade VBlank handoff** (`jmp 0x3A208`): no VDP → display-on fine.

**classification:** MUST-be-display-off = {tiles, BG, FG, sprites/SAT}; display-on-safe-in-VBlank = {palette, scroll}. DISPLAY_ON belongs immediately after sprites/SAT.

---

## == Q4 RECOMMENDED FIX ==

- **chosen option:** **Option D** (reorder; concrete placement = Option A).
- **exact placement:** in `apps/rastan-direct/src/vdp_comm.s`, `_vblank_service`. Move the DISPLAY_ON block (currently lines 179-181) to **immediately after `bsr vdp_commit_sprites`** (line 169). Resulting order:
  ```
      bsr  vdp_commit_tiles_if_dirty
      bsr  vdp_commit_bg_strips_if_dirty
      bsr  vdp_commit_fg_strips_if_dirty
      bsr  vdp_commit_sprites          ; last display-off-required stage
      moveq #VDP_REG_MODE2,%d0         ; --- DISPLAY_ON moved here ---
      moveq #VDP_MODE2_DISPLAY_ON,%d1
      bsr  vdp_set_reg
      tst.b palette_dirty              ; palette now runs with display enabled (VBlank)
      beq.s .Lvs_skip_palette
      bsr  vdp_commit_palette
      clr.b palette_dirty
  .Lvs_skip_palette:
      bsr  vdp_commit_scroll           ; scroll now runs with display enabled (VBlank)
      movem.l (%sp)+,%d0-%d7/%a0-%a6
      jmp  (0x00003A208).l
  ```
- **old DISPLAY_ON handling:** the single existing DISPLAY_ON write is **moved, not duplicated**; no guard added; the old tail position is removed.
- **later work after DISPLAY_ON:** palette commit (conditional) + scroll commit (unconditional) + handoff.
- **why safe:** all bulk VRAM DMA (tiles/BG/FG/sprite/SAT) completes before DISPLAY_ON (Q3); the only post-DISPLAY_ON VDP writes are CRAM (palette) and VSRAM+2-word HScroll (scroll), which are VBlank-safe with display enabled; the whole service already completes inside VBlank (0x0A inside), so these finish before active scan; 68k is bus-stalled through the SAT DMA so DISPLAY_ON executes after DMA completion; `vdp_set_reg` writes a complete 1-word register command (no half-latched address hazard before the palette/scroll address setups).
- **why narrow:** pure reorder of existing instructions in one function; no new logic, no new symbols, no cache/ownership/plane/SAT change.
- **expected impact:** DISPLAY_ON issued earlier by the palette+scroll wall-clock → lands inside VBlank on more frames → the residual band reduces or disappears; **zero net code-size** (`opcode_replace` 133 and `total_genesis_bytes_covered` unchanged — pure reorder).
- **risks:** (1) if the 2-word HScroll VRAM write slips into active display on real hardware, a 1-frame scroll seam could appear — low (tiny, VBlank-timed, now issued earlier than before). (2) if the residual band is actually driven by display-off work exceeding VBlank in worst frames (not just DISPLAY_ON placement), this reorder only partially helps → follow-up Option B / diagnostic. Neither risk corrupts VRAM or sprites.
- **STOP conditions:** a scroll seam appears with display-on scroll → **fallback**: place DISPLAY_ON *after* `vdp_commit_scroll`'s VRAM writes but keep palette after DISPLAY_ON (reclaims palette only), or keep scroll before DISPLAY_ON entirely; any post-DISPLAY_ON write proves unsafe → revert; the band is unchanged by the reorder → re-diagnose (do not add masking); moving DISPLAY_ON would require touching plane/SAT/HScroll bases, the cache, PC080SN ownership, SAT-canonical, broad rewrite, or 30 FPS → STOP (none are required by this design).

---

## == Q5 CODY PLAN ==

**next Cody prompt (copy-ready):**

---
**Cody — Build 0135 DISPLAY_ON Timing Reorder (production, narrow)**

**Type:** One narrow production build. No temporary diagnostic in the production ROM.
**Baseline:** Build 0134, SHA256 `989b17e8b065ae678764e5901c45cf156fd4c37bf2a128d8686f4f493b611832`.
**Design:** `docs/design/Andy_build0134_display_on_timing_fix_design.md`.

**Change (single file, `apps/rastan-direct/src/vdp_comm.s`, `_vblank_service` only):** move the DISPLAY_ON block (`moveq #VDP_REG_MODE2,%d0; moveq #VDP_MODE2_DISPLAY_ON,%d1; bsr vdp_set_reg`) from its current tail position (after `bsr vdp_commit_scroll`) to **immediately after `bsr vdp_commit_sprites`**. Leave the palette block and `bsr vdp_commit_scroll` in place so they now run after DISPLAY_ON. This is a **pure reorder** — do not add/remove instructions, do not duplicate DISPLAY_ON, do not touch any commit routine, `pc090oj_hooks.s`, `scene_load.s`, `tilemap_hooks.s`, PC080SN artifacts, or the residency cache.

**Invariants:** `opcode_replace` patched-site count `133` unchanged; `total_genesis_bytes_covered` unchanged (pure reorder → zero size delta). If either changes, STOP and report.

**Evidence (production, no ring):**
- Build number/SHA/size; confirm rolling==numbered (`cmp -s`).
- Exodus + emulator contact sheet: title (no-input), End-Round, coin/start — show the horizontal band reduced or gone vs Build 0134.
- Title score sprites still present (codes 0x2A–0x49; ~22/27) — screenshot.
- PC090OJ `emitted_count` sane (~0x17 title) and residency-cache writes still 0 in steady state (unchanged from 0132).
- No PC080SN plane regression (Plane A/B viewers intact).
- Layer-separated Exodus capture confirming composite now shows more/all of the frame.

**Optional tiny non-perturbing proof (only if the visual result is ambiguous, and as a SEPARATE temporary build, not in Build 0135):** a single VCounter read at the new DISPLAY_ON site, captured once, then reverted byte-identical — same discipline as Build 0133. Prefer visual proof; add this only if needed.

**Constraints:** no scene_load.s change; no 30 FPS; no broad rewrite; no cache/ownership/SAT-canonical change; no bookmark unless STOP requires diagnosis.

**STOP if:** invariants change unexpectedly; a scroll seam appears (fall back to DISPLAY_ON after scroll, palette-only reclaim); the band is unchanged (re-diagnose, do not mask); build/boot/canonical gate fails.

**Open/Closed Issues Impact:** OPEN-001 (title display band — direct fix attempt), OPEN-024 (context, cache intact); none closed until visual proof.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-001 (late-DISPLAY_ON band — narrow reorder fix designed; not closed), OPEN-024 (context: residency cache intact, unaffected).
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend, if Build 0135 confirms, a KNOWN_FINDINGS entry: `_vblank_service` display-off window need only span the VRAM-DMA-critical commits (tiles/BG/FG/sprite/SAT); DISPLAY_ON may precede CRAM/VSRAM/HScroll commits within VBlank).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** Option B work-reduction if the band persists; the diagnostic-overhead-free scanline quantification; `.Lpc090oj_emit_slot` producer/render split (OPEN-024 debt).

AGENTS_LOG updated: YES
STOP status: NO — a safe earlier DISPLAY_ON placement is identified and proven from code + Genesis VDP rules (Option D reorder); delegated to Cody as one narrow production build with a defined fallback.
