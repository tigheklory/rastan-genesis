# Build 0329 — Event-Driven R1/P1 Palette Ownership + Vertical-Noise Investigation

**Type:** Hybrid Analysis / Implementation. ROM produced (palette portion). Classification: **EXTENDING**. Baseline Build 0328.
**Result:** Part A (palette scaffolding removal) IMPLEMENTED + verified. Part B (visual noise) root cause **PARTIAL** — precise STOP, no speculative fix.

## 1. Phase 0
- **Relevant findings:** KF-010 (BG→Plane B, FG→Plane A); KF-015 (full-plane scroll, VSRAM `-raw+8`, gameplay uses full 9-bit `&0x1FF`); KF-011 (arcade Level-5 VBlank owns progression; Genesis VBlank servicing-only). HIGH-hazard: KF-011, KF-015 (canonical priors, honored — no VBlank ownership added, scroll untouched).
- **Deferred (untouched):** `(code,bank)` sprite color, HUD score/`1UP` (bank 0x30), Axe palette, waterfall palette animation, vertical-fill missing rows, epoch tile loss, cave wrong tile, Segment-7 tile, late partial lizardman.
- **Classification:** EXTENDING.
- **OPEN/CLOSED impact:** touches OPEN-006 palette architecture (improves ownership discipline); no issue closed/opened. OPEN-017 slowdown: partial contribution measured/argued, not closed.
- **Contradiction status:** none.

## 2. Previous-session checkpoint (reused, not rediscovered)
Established before the session limit and reused verbatim:
1. `vdp_reassert_test_lines` (vdp_comm.s) ran every VBlank; in scene 1 it unconditionally did `move.b #1, palette_dirty` → `vdp_commit_palette` (64-word PIO CRAM write) every gameplay frame. Line 2 not touched.
2. The arcade palette hooks `genesistan_palette_hook_3ba64/_59ad4/_45dae` (palette_hooks.s) remain live producers that route arcade banks into staged Lines 0/1/2/3 and set `palette_dirty`. Test sprite Lines 0/1 were installed **only** by the reassert.
3. `.Lplane_a_native_attr_from_word` (tilemap_hooks.s) forces all R1/P1 Layer-A name words to palette Line 3 (production execution logic, Build 0325).

## 3. Build 0328 closure
Shared PC090OJ piece-terminator fix: **CLOSED / accepted** for its scope. Not modified here. Late R1/P1 lizardman missing right-side pieces: **DEFERRED, cause unproven** (not investigated here).

## 4. Current every-VBlank behavior (Part A, proven)
`_vblank_service` (vdp_comm.s:204 pre-0329) → `bsr vdp_reassert_test_lines` → scene 1 → copies `test_sprite_line0`→staged L0, `test_sprite_line1`→L1, `editor_layera_palette`→L3, then unconditional `move.b #1, palette_dirty`. `vdp_commit_palette` re-DMAs all 64 staged CRAM words by PIO. So stable R1/P1 committed the whole CRAM image **every frame merely because a VBlank occurred**. Sole live caller was `_vblank_service:204` (verified by grep); the other two reasserts (`vdp_reassert_fg_bank3_line`, `vdp_reassert_bank36_line0`) were already dead (no `bsr`).

## 5. Why the reassert existed
The live arcade palette hooks still route arcade banks to staged Lines 0/1/3 during gameplay and would overwrite the frozen-Test values with raw arcade-converted colors. The Test sprite Lines 0/1 have no other installer. Build 0325 therefore chose the defensive shape *legacy producer may drift → every VBlank force Test back → mark whole palette dirty → recommit*. This is the prohibited maintenance-loop architecture: it makes static state depend on continuous per-frame maintenance.

## 6. True R1/P1 palette ownership (final)
| Line | Owner | Installed at | Changes again at |
|---|---|---|---|
| 0 | Test shared sprite palette (`test_sprite_line0`) | R1/P1 scene activation | Phase 2 / next scene-load event |
| 1 | Test shared sprite palette (`test_sprite_line1`) | R1/P1 scene activation | Phase 2 / next scene-load event |
| 2 | Layer B (arcade BG bank 48) — **independent, untouched** | arcade producer | arcade Layer-B semantics (unchanged) |
| 3 | Test Layer-A master (`editor_layera_palette`) | R1/P1 scene activation | Phase 2 / future explicit Line-3 waterfall animation |

## 7. Live palette writers — audit after Test install (A2/A5)
| Producer | Reaches L0/1/3 in scene 1? (after 0329) | Classification | 0329 handling |
|---|---|---|---|
| `vdp_install_test_lines` | Yes, **once** at scene activation | Legitimate R1/P1 install event | new one-shot installer; dirty once |
| `genesistan_palette_hook_3ba64` | No (gated); Line 2 still flows | Layer-B legitimate (L2) / obsolete legacy for L0/1/3 | scene-1 gate: only `d6==2` (Line 2) writes; L0/1/3 skipped |
| `genesistan_palette_hook_59ad4` | No (gated) | Obsolete legacy sprite-palette owner for Test lines | scene-1 gate: whole hook skipped (targets only Test lines/dead caches) |
| `genesistan_palette_hook_45dae` | No (gated) | Empty-source copy → Test lines | scene-1 gate: skipped (also removes a spurious `palette_dirty`) |
| Layer-B / bank-48 path | Yes (Line 2 only) | Legitimate Layer-B | unchanged |

During stable R1/P1, **nothing** re-owns Lines 0/1/3, so `palette_dirty` is asserted only by (a) the one-shot install event, or (b) a genuine Layer-B Line-2 change. Never by "a VBlank occurred."

## 8. Semantic activation boundary (A1)
`load_scene_tiles` (scene_load.s) is the scene-activation event (display off, interrupts masked). At line 133 it sets `genesistan_current_scene_id`; ids 3–8 collapse to logical scene 1 (gameplay family = all current R1/P1 segments). It already calls `fg_cache_reset` on the `d5==1` gameplay entry. Build 0329 installs the Test lines in that same `d5==1` block — a genuine one-shot per scene/segment load, **not** a per-frame detector. Phase 2 will load a different manifest and can install different ownership at the same boundary (structure preserved).

## 9. Scaffolding removal (A4) — implementation
1. **vdp_comm.s**: deleted the `_vblank_service` per-VBlank `bsr vdp_reassert_test_lines`; refactored/renamed the routine to `vdp_install_test_lines` (one-shot semantic installer — copies L0/L1/L3, sets `palette_dirty` once; internal scene gate removed because the caller provides the semantic context).
2. **scene_load.s**: `bsr vdp_install_test_lines` in the `d5==1` gameplay-scene-entry block (next to `fg_cache_reset`).
3. **palette_hooks.s**: added `.extern genesistan_current_scene_id`; scene-1 gates on `_59ad4` (skip whole hook), `_3ba64` (at `.L3ba64_line_ok`: keep only Line 2, skip L0/1/3), `_45dae` (skip copy). Two `.L3ba64_next` short branches widened to `.w` (displacement grew).

No per-frame reassert, no per-frame compare/poll, no watchdog, no periodic refresh. Line 2 untouched (A6 verified: no edit to any bank-48/Line-2 path). Non-scene-1 (frontend, endround, future phases) palette behavior unchanged (all gates are `scene_id==1` only).

## 10. CRAM workload before/after (A7, C1)
- **Build 0328 (stable R1/P1):** `palette_dirty` set every frame by the reassert → **1 CRAM commit/frame** = 64 words (128 bytes) PIO every frame.
- **Build 0329 (stable R1/P1):** Test Lines 0/1/3 contribute **0** recurring commits. Commits occur only on a scene/segment load (one-shot install) or a genuine Layer-B Line-2 change. Proven by construction: the sole unconditional per-frame `palette_dirty` writer was removed (symbol `vdp_reassert_test_lines` gone; no `bsr` remains), and the arcade hooks are gated off Lines 0/1/3 during scene 1.
- **Performance classification:** scaffolding removal = **CONTRIBUTING FACTOR** to the 0325+ slowdown (real per-frame CRAM PIO eliminated), **not** claimed as the whole cause (64 words/frame is modest). Overall slowdown: **NOT fully PROVEN** — needs a corrected gameplay measurement in Tighe's real playthrough.

## 11–15. Part B — READY / vertical-noise investigation
**Artifact history (corrected):** the horizontal corruption band is **pre-existing** — visible in Build 0324 on `ROUND 1 READY` (stationary, just above the ROUND 1 line, ~1 s), and historically on the title screen. Build 0325 did **not** invent it. What 0325 changed is that a similar band now **survives into gameplay** and appears to travel vertically as the viewport scrolls.

- **READY artifact layer / row / name / pattern:** **NOT PROVEN.** Static analysis narrows it to a stale/uncleared plane row (Plane A/FG is the leading candidate, per KF-010 and the Layer-A→Line-3 exposure below), but the exact layer, logical row, physical/circular VRAM row, and whether it is a stale *name word* vs a stale *pattern slot* cannot be distinguished without a VRAM/plane capture.
- **Text→gameplay-pattern transformation:** consistent with **stale name entry / pattern-slot reuse** (name word constant, referenced VRAM pattern replaced by the R1/P1 load) — but not yet captured, so not asserted.
- **Fixed-row-scroll hypothesis (B4):** leading model — a single stale physical plane row is stationary in plane space; static on READY (scroll static), and carried vertically through screen space by normal gameplay vertical scroll (KF-015 gameplay `&0x1FF` full 9-bit scroll). **NOT PROVEN.**
- **0324→0325 persistence divergence (B5/B6):** leading hypothesis is a **visibility/exposure** change, not new corruption: Build 0325 forces all R1/P1 Layer-A to CRAM **Line 3** (`.Lplane_a_native_attr_from_word`, `moveq #3`) and installs a colorful Test Line 3. A stale FG row that rendered black/invisible under its 0324 line/palette can become visible once its name words resolve to the now-populated Test Line 3. This would make it a **Build-0325 exposure of a pre-existing stale-row bug**, not a 0325-created defect. **NOT PROVEN** — must compare the same row's name words + palette bits + referenced pattern across 0324/0325.
- **Relevant existing mechanism:** `genesistan_hook_cwindow_clear` (tilemap_hooks.s:3335) already blanks `staged_bg_buffer`/`staged_fg_buffer` and marks all 32 rows dirty. Whether it runs at the READY→gameplay transition, and whether its clear reaches the offending physical row, is the pivotal unproven runtime question.

**Visual root cause: PARTIAL / NOT PROVEN.** No visual fix is included (per rules: do not guess, do not conceal with black CRAM or masking).

## 16. Implementation summary
Part A only. Files: `vdp_comm.s`, `scene_load.s`, `palette_hooks.s`. Sprite terminator (Build 0328) untouched; `(code,bank)` architecture untouched; HUD default `RASTAN_GAMEPLAY_HUD_SPRITES ?= 2` unchanged; Line 2 / Layer B untouched.

## 17. Automated verification
Build 0329 → `dist/rastan-direct/rastan_direct_video_test_build_0329.bin`, SHA256 `237a2e88b85684047dc1599a8ad781694432c78dd98c4dea37532cee13d60f1e`, size 1,670,840, counter 329. Boot guard PASS (pre+post). GATE_PASS (canonical). Seven-epoch gate PASS (records 0,3,4,10,11,12,15). Plane-A full LUT PASS; Plane-B fixed LUT PASS; plane drops 0; exceptions 0; sp_valid YES. MAME Genesis-NTSC 30s boot clean (938%). Symbol check: `vdp_install_test_lines` present; `vdp_reassert_test_lines` removed; no per-frame reassert `bsr` in source.

## 18. USER MUST VERIFY
R1/P1 sprite palettes (Rastan + enemies) still correct; Layer-A palette correct; Layer-B unchanged; READY corruption band; READY text during transition; **the moving gameplay band** (does removing the per-frame reassert change it? — expected NO, since the noise is a plane/VRAM lifecycle defect, not palette scaffolding); gameplay speed (any felt improvement from dropping the per-frame CRAM commit); Build-0328 sprite fix still correct.

## 19. Deferred tasks
`(code,bank)` full sprite architecture; HUD `1UP`/score (bank 0x30) + Axe → first-class Palette Composer representations (no hardcoded colors); waterfall palette animation (future explicit event-driven Line-3 updates — architecture now supports this); vertical-noise visual fix (pending the capture in §11); late partial lizardman; vertical-fill/epoch/cave/Segment-7.

## 20. Visual STOP condition (Part B)
STOP without visual implementation: the READY band's **layer, logical/physical row, and stale-name-vs-stale-pattern classification cannot be proven from static analysis**, and the gameplay band cannot yet be tied to a specific native row-publication/clear lifecycle boundary. Required next evidence (autonomously capturable at READY, then a short gameplay confirmation): Plane-A/B name-table row dump at READY (identify the bad physical row, its name words, palette bits, tile indices, referenced pattern), the same row's pattern before/after the R1/P1 load, and `scroll_y_fg` vs screen-Y correlation across gameplay frames to confirm the fixed-row-scroll model — plus whether `genesistan_hook_cwindow_clear` executes at the transition and reaches that row.
