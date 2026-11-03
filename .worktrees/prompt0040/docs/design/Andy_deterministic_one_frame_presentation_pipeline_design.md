# Andy — Deterministic One-Frame-Lag Presentation Pipeline Design (Architecture / Design Only)

**Author:** Andy
**Date:** 2026-07-03
**Baseline:** Build 0138, `dist/rastan-direct/rastan_direct_video_test_build_0138.bin`, SHA256 `719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615`.
**Priors:** Cody Build 0138 DISPLAY_OFF split; Cody 0137 active-count SAT; Andy 0136 active-count design; Cody/Andy 0136 candidate bitset; Cody 0135 budget/scan-depth.
**Scope:** ARCHITECTURE + implementation DESIGN only. No implementation/edit/build/diagnostic-ROM; no Cody delegation until the ownership model is proven (this doc). Genesis-native addresses; no arcade↔genesis arithmetic. Labels **[OBS]** verified from Build 0138 source; **[INT]** interpretation.

> **BOTTOM LINE:** The band exists because **all** VDP work runs inside the VBlank interrupt (`_vblank_service`), and on some frames DISPLAY_OFF→commit→DISPLAY_ON **overruns VBlank into active scanout** — top rows show the old committed state, the overrun window is blanked, bottom rows show the new state. The deterministic one-frame pipeline fixes this with three coupled requirements: (1) **double-buffer the producer-written staging** (BG/FG/tile/palette/scroll) so the VBlank commit consumes a **complete, stable FRONT** snapshot while producers write BACK; (2) **bound the VBlank commit to fit VBlank** — the real blocker is the **BG/FG strip commits (CPU `move.w` loops, up to 2048 words each)**, which must become bounded VRAM DMA; (3) keep sprite prep cheap (candidate mask already does) so it fits. Then DISPLAY_OFF spans only true VBlank and never enters scanout. **WRAM easily fits** full double-buffering (~10KB added into ~34KB free). Recommended first build: **Option A / Build 0139 — establish the frame-ownership + swap framework, piloted on the sprite snapshot** (lowest-risk), as **Phase 1** of a five-phase plan whose **final** state removes all temporal mixing. This is explicitly not the final solution — the visible band closes at Phase 2 (BG/FG) and DISPLAY_OFF is removed at Phase 5.

---

## == PHASE 0 ==

- **Relevant priors:** Build 0132 residency cache (tile DMA 0 steady); 0136 candidate mask (scan 256→~42); 0137 active-count SAT (≤320w, ~92 steady); 0138 sprite prep moved before DISPLAY_OFF (still in VBlank). KF-036 (arcade WRAM 0xFF0000–0xFF3FFF, Genesis BSS 0xFF4000+); KF-021 (staged SAT ≠ truth); VRAM layout (patterns 0..1503, Plane B 0xC000, Plane A 0xE000, Window 0xF000, SAT 0xF800, HScroll 0xFC00).
- **High-rediscovery hazards:** (1) VDP DMA length 0 = 0x10000-word transfer; (2) VRAM name-table/pattern/SAT writes during active scanout corrupt the visible frame; (3) producer-written staging (BG/FG) can be mid-write when VBlank preempts → partial frame; (4) VRAM is nearly full — **no room for alternate plane pages** without relocating patterns; (5) one-frame vs two-frame lag depends on where prep runs relative to commit.
- **Task classification:** Presentation-architecture DESIGN for OPEN-001 (temporal frame mixing / band).
- **Contradiction detected:** NO.
- **Build 0138 baseline:** verified SHA `719a9af2…044615`.
- **Owner fixed-latency decision:** implement a deterministic **fixed one-frame-lag** pipeline; not conditional; no ready-flag stall, no repeat-until-ready, no variable-latency queue, no same-frame producer→VRAM.
- **Conditional wait forbidden:** YES — no readiness wait, no unbounded retry, no DISPLAY_OFF-into-scanout to hide overload.
- **Current visual interpretation:** temporal frame mixing within one physical frame — `_vblank_service` (VBlank interrupt) overruns VBlank; the DISPLAY_OFF/commit window straddles active scanout (top=old committed state, middle=blanked overrun, bottom=new state). A full title frame appears just before a transition because that frame's commit happened to fit VBlank.
- **address_map.json loaded:** YES. **arithmetic offset used as proof:** NO.

---

## == Q1 CURRENT OWNERSHIP ==

Every stage below runs **inside** `_vblank_service` (VBlank interrupt) [OBS vdp_comm.s:159-186].

- **tiles:** canonical=arcade tile producers; staging=`staged_tile_words` (96B, 0xFF609A); writer=tilemap producer hooks (main loop); consumer=`vdp_commit_tiles_if_dirty` (VBlank, CPU `move.w` 48w); overlap=YES (producer main-loop vs VBlank commit); **single-buffered**; cleared=no (overwritten); dirty-list (`tiles_dirty` byte).
- **BG (Plane B):** canonical=arcade PC080SN BG producer; staging=`staged_bg_buffer` (4096B, 0xFF401A); writer=`genesistan_hook_tilemap_bg_fill` (main loop); consumer=`vdp_commit_bg_strips_if_dirty` (VBlank, **CPU `move.w`, up to 32 rows × 64w = 2048w**); overlap=YES; **single-buffered**; dirty=`bg_row_dirty` (32-bit row mask); snapshot=row-staged + dirty mask.
- **FG (Plane A):** as BG — `staged_fg_buffer` (4096B, 0xFF501A); `genesistan_hook_tilemap_fg_fill`; `vdp_commit_fg_strips_if_dirty` (CPU, up to 2048w); `fg_row_dirty`; **single-buffered**; overlap=YES.
- **sprites (descriptor):** canonical=`pc090oj_object_ram` mirror (arcade producers); staging=`staged_sprite_descriptor_table` (960B); writer=`.Lvcs_mirror_scan`/emit (**prep**, in VBlank, not producers); consumer=`.Lvcs_link_chain_build`+`.Lvcs_tile_dma` (VBlank); overlap=NO (prep and consume both in the handler, sequential); **single-buffered**; cleared each frame (`.Lvcs_clear_generated_sprite_state`); snapshot.
- **sprites (SAT):** staging=`staged_sprite_sat` (640B, 0xFF6104); writer=prep (scan/link, VBlank); consumer=`.Lvcs_sat_dma` (VBlank DMA, active_count×4); **single-buffered**; overlap=NO; snapshot; count=`staged_sprite_active_count`.
- **sprite tile residency/DMA:** `sprite_tile_resident_code` (160B, 0xFF674A) + `pc090oj_candidate_bitset` (32B, 0xFF6FEA); writer=tile DMA (resident) / mirror-write hooks (candidate); persistent derived helper (NOT per-frame); **single-buffered** (correctly — persistent across frames).
- **palette (CRAM):** staging=`staged_palette_words` (128B, 0xFF601A); writer=palette producer hooks (main loop); consumer=`vdp_commit_palette` (VBlank, CPU 64w, **runs after DISPLAY_ON**); `palette_dirty`; **single-buffered**; overlap=YES.
- **scroll (VSRAM/HScroll):** `staged_scroll_x/y_bg/fg` (8B); writer=scroll hooks (main loop); consumer=`vdp_commit_scroll` (VBlank, 4w+regs, after DISPLAY_ON); **single-buffered**; overlap=YES.
- **scene/global VDP register state:** `genesistan_current_scene_id`, scene A0 range; `load_scene_tiles` (main-loop, its own DISPLAY_OFF/ON + IRQ mask) — a separate transition path.
- **other visible VDP state:** VDP mode/plane/SAT/HScroll base registers (set at boot, static).

**Mixed-frame paths (expose old-above / black / new-below):** (a) BG/FG CPU strip commits overrunning VBlank into scanout (largest); (b) tile commit; (c) sprite tile DMA / SAT DMA if they push the window past VBlank end; (d) palette/scroll after DISPLAY_ON if the whole service overran; (e) a **producer mid-write** to `staged_bg/fg_buffer`/`staged_palette_words`/`staged_scroll_*` when VBlank preempts → partial staging committed. The DISPLAY_OFF/ON toggle converts overrun into a **black** band (current masking).

---

## == Q2 FRAME CONTRACT ==

- **producer frame:** arcade state being translated during a visible period (producers write mirror + `staged_*`).
- **prepare snapshot:** the BACK set of buffers being filled for the next visible frame (producers + sprite prep).
- **commit snapshot:** the FRONT set of buffers, read-only, consumed by the VBlank commit.
- **displayed snapshot:** the VDP state visible for the whole physical frame (product of the last commit).
- **advance point:** exactly at **VBlank entry**, once per frame — swap FRONT↔BACK, then commit the new FRONT. (Not VBlank exit, not arcade handoff.)
- **one-frame latency proof (Q2.9):** producers fill BACK during visible frame N; at VBlank(N→N+1) the swap makes that BACK the FRONT and the commit DMAs it; visible frame N+1 displays it. There is **no readiness test** — the swap and commit are unconditional every VBlank; the buffer that was BACK is always taken as complete because the arcade has finished its frame's producers before it yields to VBlank (the mirror/staging is stable at VBlank entry). Latency is therefore always exactly one frame, never variable.
- **producer buffer (Q2.4):** BACK is writable by producers (main loop). **VBlank-read-only (Q2.5):** FRONT.
- **cleared/recycled (Q2.6):** the new BACK (old FRONT) is recycled after the swap; sprite prep clears+rebuilds its snapshot each frame; BG/FG use dirty masks (only changed rows restaged) carried per buffer.
- **boot behavior (Q2.7):** both buffers cleared to a blank/offscreen snapshot; frame 0 commits a blank FRONT (blank first frame — the fixed one-frame startup cost), prep fills BACK; frame 1 displays it. No wait.
- **transition behavior (Q2.8):** scene transitions use a **predetermined** contract (Q8) — bulk plane/tile changes are spread over a fixed number of frames or use the existing fixed `load_scene_tiles` blank sequence; the per-frame pipeline never waits on readiness.

---

## == Q3 BUFFERING ==

Principle: **double-buffer state that PRODUCERS write** (BG/FG/tile/palette/scroll) — those race the VBlank commit. State written **only by prep in the handler** (sprite descriptor/SAT) is sequentially safe but is **also** double-buffered to establish one uniform swap framework and to enable moving prep out of the pre-commit window. The **mirror** stays single canonical (scanned at VBlank when stable). Candidate mask + residency cache stay **single** (persistent derived helper, correct as-is).

- **sprite buffers:** two copies of `staged_sprite_sat` (640B ea), `staged_sprite_descriptor_table` (960B ea), `staged_sprite_active_count` (2B ea). Candidate mask + residency cache single. `source_id`/order per buffer (the scan writes them into the BACK copy). active_count per buffer (commit reads FRONT's). — **immutable commit snapshot + writable prepare snapshot.**
- **BG buffers:** two copies of `staged_bg_buffer` (4096B ea) + `bg_row_dirty` (4B ea). Producers write BACK; commit DMAs FRONT dirty rows; dirty mask owned per buffer (accumulate on BACK, consumed+cleared on FRONT). — **full double buffer** (producer-written).
- **FG buffers:** two copies of `staged_fg_buffer` (4096B ea) + `fg_row_dirty` (4B ea). Same as BG.
- **tile buffers:** two copies of `staged_tile_words` (96B ea) + `tiles_dirty` (1B ea). — **full double buffer** (small).
- **palette buffers:** two copies of `staged_palette_words` (128B ea) + `palette_dirty` (1B ea). Commit CRAM **only during VBlank** (moved before DISPLAY_ON in the pipeline). — **full double buffer.**
- **scroll buffers:** two copies of `staged_scroll_x/y_bg/fg` (8B ea) latched per frame. — **front/back latch.**
- **pointer/index state:** one `present_bank` byte (0/1) selecting FRONT; each subsystem's two copies are indexed `base + present_bank*size` (or a front/back pointer pair per subsystem). Swap = `present_bank ^= 1`, **once** at VBlank entry, before the commit.
- **swap rule:** at VBlank entry: `present_bank ^= 1` (BACK completed last frame → FRONT); then commit FRONT; producers/prep then write the new BACK. Writer=producers/prep (BACK); reader=commit (FRONT); clear=per-subsystem on the new BACK (dirty masks / scan clear).

For each buffer (exact): sizes and current addresses as in Q1; **proposed second-buffer sizes equal the first** (BG +4096, FG +4096, sprite SAT +640, desc +960, active_count +2, tile +96, palette +128, scroll +8, dirty flags +~10); alignment 2 (word); boot value = cleared/blank; swap as above.

---

## == Q4 WRAM BUDGET ==

[OBS symbol.txt] Genesis BSS: `staged_bg_buffer` 0xFF401A … high-water `genesistan_scene_a0_hi` ≈ **0xFF7106** → **~12.5 KB used** (0xFF4000–0xFF7106). Arcade WRAM 0xFF0000–0xFF3FFF (16KB, KF-036). Stack near top of 0xFFFFFF.

- **current usage:** ~12.5 KB Genesis BSS; free Genesis WRAM ≈ 0xFF7106 → stack (~0xFFF800) ≈ **~34 KB**.
- **added buffers (full double-buffer):** BG 4096 + FG 4096 + sprite SAT 640 + desc 960 + active_count 2 + tile 96 + palette 128 + scroll 8 + dirty flags ~12 ≈ **~10 KB**.
- **remaining space:** ~34 − ~10 = **~24 KB free** after full double-buffering.
- **risks:** none material — align to word; keep new second-copies contiguous after 0xFF7106; verify stack low-water (Cody to confirm the exact stack base and that ~24KB margin holds).
- **classification:** **FITS with large margin.** Full deterministic double-buffering is affordable — **no** compact command-queue fallback is needed; no conditional readiness is introduced.

**Phase 1 (sprite-only) added:** SAT 640 + desc 960 + active_count 2 + flags ≈ **~1.6 KB** — trivial.

---

## == Q5 SCHEDULING ==

Two scheduling forms are viable; the design targets **Form B** (prep in the visible period) as the end state, with **Form A** (prep at VBlank tail) as a safe interim that already removes the band.

- **prepare call:** the sprite scan/link and the (future) BG/FG/tile snapshot builders — WRAM only, never VDP, never the FRONT (commit) buffer.
- **producer boundary (Q5.4):** the arcade finishes its frame's producers before it yields to VBlank; therefore the mirror + `staged_*` BACK are complete at VBlank entry. The exact arcade main-loop "producers-done" instruction (for Form B visible-period prep) is `jmp 0x3A208`-adjacent arcade code — locating it precisely is a **later** Cody arcade-audit item; it is **not** required for Form A.
- **Form A (interim, no arcade hook):** in `_vblank_service`: (1) `present_bank ^= 1` (swap); (2) **commit FRONT** (bounded DMA) — the only VDP work, at VBlank head, fits VBlank; (3) `update_inputs`; (4) **prep BACK** (WRAM only) — may run into active scanout harmlessly (no VDP writes). This yields a fixed **two-frame** lag but **zero band** (commit is bounded and at VBlank head). Deterministic, no wait.
- **Form B (end state, one-frame):** invoke prep in the **visible period** right after the arcade producer boundary (needs the arcade hook); VBlank then does only swap+commit. Fixed **one-frame** lag, zero band.
- **swap call (Q5.6):** `present_bank ^= 1` at VBlank entry, once.
- **VBlank consumer:** commits only the FRONT snapshot; bounded VDP work; finishes before scanout.
- **input timing (Q5.8):** `update_inputs` stays at VBlank (sampled once/frame); Form A/B do not change input cadence (arcade consumes inputs during its visible logic).
- **fixed-latency proof (Q5.9):** the swap+commit are unconditional every VBlank; the displayed snapshot is always the one prepared exactly one (Form B) or two (Form A) frames earlier — a fixed constant, never a variable queue, because nothing gates the advance.

**Recommendation:** ship the framework with **Form A first** (no arcade-hook dependency, already band-free once the commit is bounded), then migrate to **Form B** (one-frame) once the producer-boundary hook is located and proven. The owner requires *exactly one frame*; Form A is a deterministic stepping stone (fixed two-frame) that proves the machinery — flag this explicitly and treat Form B as the required end state.

---

## == Q6 COMMIT BUDGET ==

Per-frame VBlank commit (worst case), NTSC VBlank ≈ ~38 lines ≈ ~18–20k 68k cycles; VRAM DMA budget in VBlank ≈ ~3800 words:

| stage | max words | cond/fixed | CPU or DMA | approx cost | worst transition | steady |
|---|---:|---|---|---|---|---|
| tile commit | 48 | dirty | **CPU** move.w | ~1 line | small | ~0 |
| BG commit | **2048** | dirty rows | **CPU** move.w | **~40+ lines** | full plane redraw | few rows |
| FG commit | **2048** | dirty rows | **CPU** move.w | **~40+ lines** | full plane redraw | few rows |
| sprite tile DMA | ≤1472 | changed (residency) | DMA | ~1–3 lines | churn | ~0 |
| SAT DMA | ≤320 (~92) | active_count | DMA | ~0.4–1 line | ~1 line | ~0.4 line |
| palette | 64 | dirty | CPU | ~1 line | small | ~0 |
| scroll | 4 + regs | fixed | CPU | negligible | negligible | negligible |

1. **full deterministic commit fit in VBlank (steady):** YES — steady title/gameplay commit ≈ SAT DMA + few dirty rows + scroll ≪ VBlank.
2. **heavy title/story/scene transitions:** NO with the **current CPU BG/FG strip loops** — a full-plane redraw (2048+2048 words CPU ≈ 80+ lines) massively overruns VBlank. This is the band's root on transition/redraw-heavy frames.
3. **gameplay:** steady gameplay fits; scroll-driven row updates are a few rows/frame (fits) if BG/FG are DMA and bounded.
4. **proven upper bound:** unbounded today (CPU BG+FG can be 4096 words). Under the pipeline: bound per-frame name-table DMA to ≤ ~1500 words (BG+FG combined) so commit+SAT+tile ≤ VBlank DMA budget.
5. **largest blocker:** **BG/FG strip commit** (CPU `move.w`, up to 2048 words each) — must become **bounded VRAM DMA**.

**Required optimization (no readiness wait):** convert BG/FG strip commit to **VRAM DMA of dirty rows**; **bound** the per-frame dirty-row DMA (e.g., ≤ N rows/frame); spread bulk plane changes over a fixed number of frames or route them through the fixed `load_scene_tiles` transition sequence (Q8). **Do not** solve overload with DISPLAY_OFF into scanout.

---

## == Q7 VDP STRATEGY ==

VRAM is nearly full [OBS]: patterns 0..1503 (→0xBBC0), Plane B 0xC000, Plane A 0xE000, Window 0xF000, SAT 0xF800, HScroll 0xFC00 — only ~1KB free (0xBBC0–0xC000). **Alternate 4KB plane pages do not fit** without relocating patterns.

- **SAT (0xF800):** fully updatable in VBlank — active-count DMA (≤320w). Atomic-enough (whole SAT before scanout).
- **Plane A name table (0xE000):** in-place; update **dirty rows via bounded DMA** in VBlank (double-buffered WRAM source). Full-plane change = transition contract (Q8).
- **Plane B name table (0xC000):** same as Plane A.
- **tile-pattern VRAM:** residency-cached (sprites, Build 0132) + bounded DMA for BG/FG patterns; scene bulk via `load_scene_tiles`.
- **CRAM:** full 64-word DMA/CPU in VBlank, cheap.
- **VSRAM/scroll:** tiny, in VBlank.
- **VDP registers:** static; MODE2 display bit is the only per-frame toggle — confined to true VBlank.
- **selected option:** **Option C-variant** — residency-cached patterns + **bounded in-place DMA of name-table dirty rows** + full SAT/CRAM/VSRAM in VBlank; **NO alternate plane pages** (VRAM-infeasible). Bulk plane/tile changes use the deterministic transition contract (Q8), not paging. (Option B rejected: no VRAM room. Option A insufficient alone: full plane redraw won't fit one VBlank. Option D not needed.)

---

## == Q8 OVERLOAD POLICY ==

No conditional readiness wait. Deterministic rules:

- **normal gameplay frame contract:** prep is **bounded** (candidate mask keeps sprite scan cheap; BG/FG restage only actually-dirty rows) and always completes; the VBlank commit is **bounded** (DMA, ≤ per-frame row cap); it fits VBlank; DISPLAY_OFF spans only true VBlank (Phase 5 may remove it). The pipeline advances every frame unconditionally.
- **preparation overrun:** preparation is designed to be **bounded and always complete** within the frame's CPU interval (WRAM only). If a future producer path is unbounded, it must be **deterministically divided** before entering the pipeline — never a wait.
- **commit overrun:** the per-frame name-table DMA is **capped**; any change exceeding the cap is **deterministically spread over a fixed number of frames** (predetermined, not readiness-gated). The FRONT snapshot displayed during the spread is a **complete** (older) frame — no partial mixing.
- **scene transition:** uses the existing **fixed `load_scene_tiles` blank sequence** (its own bounded DISPLAY_OFF in main-loop context) — a predetermined transition, not an indefinite readiness condition. This is the **predetermined scene-transition contract**, distinct from the normal-frame contract.
- **producer changes state during preparation:** prevented by double-buffering — producers write BACK, prep/commit use FRONT; the swap is atomic (one byte toggle) at VBlank with producers halted (arcade in VBlank).
- **no-wait proof:** every rule above advances on a fixed schedule (per-frame cap, fixed spread count, fixed blank sequence); none tests "is it ready?"; none extends DISPLAY_OFF into scanout.

---

## == Q9 PHASES ==

- **Phase 1 (Build 0139):** frame-ownership variables (`present_bank` + swap) + **double-buffer the sprite snapshot** (SAT/descriptor/active_count) + commit-FRONT-at-head / prep-BACK-at-tail (Form A for sprites). Files: `pc090oj_hooks.s`, `vdp_comm.s`. New state: `present_bank`, second sprite-staging copies. Expected result: sprite commit consumes a stable FRONT; sprite prep leaves the pre-commit window; **plausible small band reduction** (VBlank freed of sprite prep before the commit). Invariants: sprite emitted/order/source_id/active-count/link identical; residency cache intact. Evidence: SAT DMA length/link parity vs 0138; sprite screenshots. Rollback: revert to single-buffer sprite commit. **Still permits mixing** (BG/FG unbuffered/CPU) — NOT the final solution.
- **Phase 2 (Build 0140):** **double-buffer BG/FG staging + convert strip commit to bounded VRAM DMA** (dirty rows, per-frame cap). Files: `vdp_comm.s`, `tilemap_hooks.s`. Expected: removes the dominant overrun → **band largely closes** for steady frames. Invariants: PC080SN producer semantics preserved; identical rendered tilemap. Evidence: BlastEm band contact sheet; row-DMA counts. Rollback: revert to CPU strip commit. Still permits transition-frame mixing until Q8 spread lands.
- **Phase 3 (Build 0141):** double-buffer tile-pattern commit state; bounded pattern DMA; preserve residency/cache. Removes tile-source mutation during DMA.
- **Phase 4 (Build 0142):** latch palette + scroll into the front/back snapshot; commit CRAM/VSRAM **only in VBlank** (move palette/scroll before DISPLAY_ON / into the bounded commit).
- **Phase 5 (Build 0143):** move **all** VDP writes into the bounded VBlank commit; **remove visible-period DISPLAY_OFF** (commit fits VBlank, so no display disable into scanout); enforce the transition contract (Q8) for bulk changes.
- **final invariant:** no VDP writes during active scanout; every physical frame displays exactly one complete committed snapshot; fixed one-frame lag; deterministic advance every frame; no readiness wait.

---

## == Q10 FIRST BUILD ==

- **selected option:** **Option A — Build 0139: frame-ownership variables + double-buffered sprite staging** (Phase 1).
- **why:** narrowest step that establishes the **reusable** `present_bank`/swap/commit-front/prep-back framework (reused verbatim by Phases 2–5, not discarded); lowest regression risk (sprite path already isolated, DMA-committed, semantics well-characterized); moves sprite prep out of the pre-commit VBlank window (plausible band reduction) without touching the higher-risk BG/FG producer path yet. Option B (all-state snapshot in one build) is large/risky; Option C (alternate plane pages) is VRAM-infeasible; Option D unnecessary (ownership model proven here).
- **expected result:** sprite commit consumes a stable FRONT snapshot; no sprite regression; VBlank slightly freed; framework in place.
- **limitations (explicit):** Build 0139 **does not close the band** — BG/FG single-buffered CPU commits (the dominant overrun) remain until Phase 2, and DISPLAY_OFF remains until Phase 5. Build 0139's success criterion is **architectural** (correct swap/ownership, sprite parity, framework reuse), not visual band removal. The band closes progressively across Phases 2–5.

---

## == Q11 CODY PROMPT ==

**copy-ready prompt:**

---
**Cody — Build 0139 Frame-Ownership Framework + Double-Buffered Sprite Snapshot (production, narrow, Phase 1)**

**Type:** One narrow production build. No temporary diagnostic in the production ROM. Phase 1 of the deterministic one-frame pipeline — **framework + sprites only**.
**Baseline:** Build 0138, SHA256 `719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615`.
**Design:** `docs/design/Andy_deterministic_one_frame_presentation_pipeline_design.md`.

**Owner rule:** deterministic fixed-lag presentation; **no conditional readiness wait**, no repeat-until-ready, no variable-latency queue, no DISPLAY_OFF into active scanout. This build establishes the swap framework; it does not yet remove the band.

**Files allowed:** `apps/rastan-direct/src/pc090oj_hooks.s`, `apps/rastan-direct/src/vdp_comm.s`, and `apps/rastan-direct/src/boot/boot.s` (cache/buffer boot clear only). No PC080SN, `tilemap_hooks.s`, `scene_load.s`, candidate-mask, residency-cache, or decode-predicate changes.

**Exact buffer ownership:** add `present_bank` (byte, 0/1). Duplicate the sprite snapshot into two copies: `staged_sprite_sat[2]`, `staged_sprite_descriptor_table[2]`, `staged_sprite_active_count[2]`. FRONT = copy `present_bank`; BACK = copy `present_bank ^ 1`. Candidate mask, residency cache, and `pc090oj_object_ram` mirror stay **single**.

**Exact swap point & calls (Form A, in `_vblank_service`):**
```
    ; --- swap once ---
    present_bank ^= 1
    ; --- commit FRONT (bounded, VDP) ---
    <DISPLAY_OFF>                          ; unchanged for now (Phase 5 removes)
    vdp_commit_tiles_if_dirty              ; legacy (Phase 2)
    vdp_commit_bg_strips_if_dirty          ; legacy
    vdp_commit_fg_strips_if_dirty          ; legacy
    vdp_commit_sprites_vram(FRONT)         ; tile DMA + SAT DMA + clear_dirty read FRONT copy
    <DISPLAY_ON>
    palette / scroll                       ; unchanged
    ; --- prep BACK (WRAM only, after commit) ---
    rastan_direct_update_inputs
    vdp_prepare_sprites(BACK)              ; .Lvcs_mirror_scan + .Lvcs_link_chain_build write BACK copy
    jmp 0x3A208
```
`vdp_prepare_sprites` writes the BACK copy; `vdp_commit_sprites_vram` reads the FRONT copy; both index by `present_bank`. Do not change scan/link/DMA logic beyond retargeting them to the FRONT/BACK copy base.

**Boot:** clear both sprite-snapshot copies (blank/offscreen, active_count 0); `present_bank = 0`. First frame commits a blank FRONT (expected one-frame startup blank).

**Build/gate:** `opcode_replace` 133 unchanged; `total_genesis_bytes_covered` grows by the framework (update the two canonical tools only if the gate stops on the new value); boot guard + canonical gate PASS; rolling==numbered. Confirm WRAM: new copies fit above 0xFF7106 with ≥ ~20KB stack margin.

**Semantic comparison (vs Build 0138):** across a full run, the SAT DMA length/low-high bytes, active-count set `[12,19,23,27,30,32]`, terminating link proof, emitted/drawable/dropped counters, and source_id order **identical** (allowing the fixed one/two-frame presentation phase shift). Residency-cache writes still 0 steady.

**Timing evidence:** confirm sprite prep no longer runs before the commit in `_vblank_service` (disassembly order); note whether the display-off window shrinks.

**User BlastEm handoff:** provide the numbered ROM for Tighe's BlastEm visual test. **Do not** require Cody BlastEm automation; MAME + native-debugger evidence for the semantic checks, Tighe for visual.

**STOP conditions:** any sprite emitted/order/source_id/active-count/link mismatch vs 0138; any producer/commit found writing the FRONT copy or reading the BACK mid-commit; WRAM margin < ~8KB; a zero-length SAT DMA; candidate mask/residency/decode perturbed; invariant gate fails unexpectedly.

**OPEN-001 / OPEN-024 impact:** OPEN-001 — establishes the pipeline framework toward band removal (not closed; band removal is Phase 2+); OPEN-024 — sprite semantics/mirror/cache preserved (not closed).

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-001 (temporal frame mixing / band — architecture + phased plan; not closed), OPEN-024 (sprite pipeline — framework piloted, semantics preserved; not closed).
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend, once Phase 2+ lands, a KNOWN_FINDINGS entry: presentation is a deterministic fixed-lag double-buffered snapshot; VBlank commit must stay bounded; DISPLAY_OFF must never enter active scanout).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** Form B one-frame (needs the arcade producer-boundary hook — a later arcade audit); BG/FG double-buffer + DMA conversion (Phase 2, the dominant band lever); tile/palette/scroll into the snapshot (Phases 3–4); DISPLAY_OFF removal (Phase 5); scene-transition spread contract; alternate plane pages (VRAM-infeasible without pattern relocation).

AGENTS_LOG updated: YES
STOP status: NO — ownership model proven; WRAM fits full double-buffering; deterministic no-wait pipeline specified with a five-phase plan; first build (Option A / Build 0139, Phase 1) delegated to Cody as the reusable framework pilot. (The required *exactly-one-frame* end state is Form B, gated on locating the arcade producer boundary — flagged as a later audit, not a wait.)
