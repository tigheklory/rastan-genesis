# Andy — Build 0384 → 0398 Catch-Up Review (ANALYSIS ONLY — no code, no build)

**Current baseline:** Build 0398 (user-tested). **Counter:** 398 → 398 (no build this task). No production
source changed. Legend used below: **[FACT]** documented/static, **[USER]** Tighe-confirmed result,
**[HYP]** current unproven hypothesis, **[CONCERN]** my architectural note.

## Markdown reviewed
Root: PROMPT_TEMPLATE, RULES, ARCHITECTURE, CLAUDE, BUILD_INSTRUCTIONS, KNOWN_FINDINGS (KF-078), OPEN_ISSUES
(028/029 + reconciliation), CLOSED_ISSUES (020). AGENTS_LOG 0384→0398. docs/design (new since 0384):
Cody_build0387_record17_selector1_transpose, Cody_build0387_rejection_third_chain_reanalysis,
Cody_record17_selector1_identity_and_manual_trace, Cody_phase2_initial_plane_a_population,
Cody_build0390_phase1_waterfall_regression, Cody_round_start_ready_video_comparison,
Cody_build0392_round_ready_teardown_fix, Cody_build0393_round_ready_last_writer_fix,
Cody_build0394_scene_load_display_ownership, Cody_build0396_segment10_segment11_plane_a_transition,
Cody_build0398_segment11_segment12_plane_a_transition, Cody_rope_exit_surface_ownership_step1; plus my
Andy_build0386_flying_demon_decompilation_ownership_palette.

## 1. Build timeline (0384 → 0398)
| Build | Attempt | Status |
|---|---|---|
| 0384 | Test burst+cave authoring (incomplete family: _c failed delta) | [FACT] preserved canonical=PASS, _c missing |
| 0385 | Burst+cave complete family (fixed cheat delta) | [USER] accepted baseline at the time |
| 0386 | Flying Demon whole-death fix (my opcode_replace @0x44898, KF-044 rebase) | [FACT] canonical=PASS |
| 0387 | record-17 selector-1 transpose correction | [USER] **REJECTED** (third-chain / Plane-A); **but** Tighe confirmed Flying-Demon wing-kill → whole demon dies → **CLOSED-020** |
| 0388, 0389 | unsupported map-data relocation experiments | [USER] **REJECTED** |
| 0390 | improved Phase-2 initial Plane-A population | [USER] **PARTIAL** — regressed first waterfall |
| 0391 | fixed waterfall, kept Phase-2 population | [USER] **ACCEPTED** graphics milestone (first waterfall correct; Phase-2 layout substantially correct; palette still separate) |
| 0392 | restored native semantic clear (arcade teardown) | [FACT] valid semantic work; did **not** fix the visible ROUND/READY defect |
| 0393 | dirty Plane-B publish before display-on | [USER] **REJECTED**; stale-live-Plane-B root cause **withdrawn as unsupported** (do not resurrect) |
| 0394 | scene-load display-ownership analysis (+_s failure consumed) | [FACT] analysis; established load_scene_tiles is a loader, not the presentation owner |
| 0395 | display-ownership correction (load_scene_tiles returns display-OFF; caller completes maps; fg_boundary_install_post_reseed enables display) | [USER] **ACCEPTED** — ROUND/READY defect FIXED |
| 0396 | Seg10→11 overlap package 8 (+_s coverage issue, consumed incomplete) | [FACT] incomplete family preserved |
| 0397 | Seg10→11 overlap package 8 complete | [USER] **ACCEPTED** — transition visually fixed |
| 0398 | Seg (record 12→13) overlap package 9 | [USER] **ACCEPTED** — current baseline |

## 2. Current architecture (ownership)
- **Arcade gameplay** [FACT]: original 68000 owns gameplay, timing, state progression, collision semantics,
  actors, frame progression. Genesis provides bounded native hardware realization only.
- **Plane A** [FACT]: native Genesis names produced from retained arcade record/source/descriptor/scene-fill
  decisions (semantic cut above the PC080SN C-window tail, which stays retired). Horizontal = dirty-column
  publication, vertical = dirty-row publication, both via `staged_fg_buffer`, published in VBlank (KF-072
  coordinate/publication prior; KF-078 initial-fill residency prior).
- **Plane B** [FACT]: same native model; initial Plane-B name DMA moved to the post-fill boundary (0395).
- **Pattern residency / packages** [FACT]: record-selected residency installed before first publication
  (KF-078); scene packages owned by `load_scene_tiles` (residency/identity/palette/cache) with display OFF.
- **Overlap packages** [FACT]: deterministic **offline** overlap packages bridge residency boundaries where
  outgoing-visible + incoming identities exceed what a direct stable-package switch retains. Accepted
  sequence: stable 2 → **overlap 8** → stable 3 → **overlap 9** → stable 4. Atomic name remap; generated
  metadata controls handoff; **no runtime segment special-case**; stable packages unchanged.
- **Initial scene presentation** [FACT, 0395]: `load_scene_tiles` (display OFF, residency/identity/palette/
  cache/package) → caller's 64-iteration fill completes initial Plane A/B → `fg_boundary_install_post_reseed`
  (display-enable @0x0728DE) owns final initial publication + enables display.
- **Sprites** [FACT]: native semantic priority lanes + final SAT merge for gameplay (KF-074); frontend
  compatibility object store retained. Offline (code,bank) sprite reindex + O(1) variant selector (Builds
  0381–0386) owns pixel-variant selection; palsel LUT owns (scene,bank)→CRAM line.
- **Palette (runtime)** [FACT]: Line 0 = shared sprite palette, Line 1 = shared sprite palette, **Line 2 =
  Layer B (PROTECTED)**, Line 3 = shared Layer-A master palette. (Note the Composer earlier modelled Line 3
  as the sprite line; the current runtime doc model is the above — see §5.)
- **Collision** [FACT]: arcade-owned; the only native replacement is the PC080SN visual tail of the bit-7
  surface marker (`genesistan_collision_surface_mark_visual_native`, Build 0376 @0x5A334); the arcade
  collision mutations (0x5A29C → 0x5A2EE) are retained.
- **VBlank** [FACT]: arcade Level-5 VBlank owns frame progression; Genesis VBlank is servicing-only (staged
  publish → DMA). Sprite tile DMA historically dominated VBlank cost (verify current numbers before relying).
- **Audio** [FACT]: Z80 + sound-comm infrastructure exists; arcade-sound-intent → Genesis realization is
  incomplete (stub/bring-up; no game audio).

## 3. Accepted / CLOSED — do NOT reopen (absent new evidence)
- Flying Demon whole-death (wing kill → whole demon dies) — **CLOSED-020** [USER].
- Build 0391 first-waterfall repair + Phase-2 initial Plane-A population [USER].
- Build 0395 scene-presentation display-ownership (load_scene_tiles → fill → fg_boundary_install_post_reseed)
  — ROUND/READY defect fixed [USER].
- Build 0397 overlap package 8 (Seg10→11) and Build 0398 overlap package 9 (record 12→13) [USER].
- Native PC080SN / PC090OJ replacement direction (policy doc authoritative).
- **Do NOT resurrect** the Build-0393 "stale-live-Plane-B before display-on" root cause (explicitly withdrawn).

## 4. Open items
**Confirmed user-visible bugs:**
- **Plane-A combined X/Y scroll cell error** [USER, intermittent]: during simultaneous H+V scroll, ~one 8×8
  tile missing + one appearing in blank space; self-corrects after scrolling away and back.
- **Rope-adjacent missing platform** [USER]: record-2 (X48/Y40) and record-14 (X44/Y36), both shared
  descriptor 0x2120 (tile 0x0438 / A-0868 / LA-0372, bank 0x003). Genesis shows wrong/missing platform;
  Rastan lands one metatile low; lizard men traverse where the platform should be.
- Round-1/P1 gameplay gaps [USER]: no health meter/HUD; Rastan takes no damage and plays no hit reaction;
  sound stubbed; runs slower than arcade target.
- Palette-tool coverage gaps [USER]: Flying Demon palette not fully represented in the Composer; enemy
  drop-item palettes unmapped; generic enemy explosion/burst unauthored (acceptable default); weapon
  **pickups** unmapped (held weapons ARE mapped); Composer incomplete; Tighe wants dynamic-vs-stable CRAM
  entry identification and Line 2 editable-protected-but-allocation-visible.
- **OPEN-028** [FACT]: first-arrival Plane-A sky cells can retain isolated stale names.
- **OPEN-029** [FACT]: R1 Phase-2 third-chain upper-route traversal blocked.

**Hypotheses (not proven):**
- X/Y scroll error: **[HYP]** one cell occasionally staged/published at the wrong Plane-A ring coordinate
  during a simultaneous X/Y boundary crossing (Build-0353 left residual uncertainty on arbitrary-scroll ring
  rotation / camera-relative resident-column resolution). Not proven.

**Unfinished subsystem work:** HUD/health/damage/hit-reaction; sound realization; Composer completion;
full C decompilation.

## 5. Stale / contradictory documentation (listed, NOT edited)
- **The prompt's navigation summary is now behind the latest doc on rope-exit ownership.** The prompt said
  the 0x5A29C→0x5A2EE ownership question "remains OPEN." `Cody_rope_exit_surface_ownership_step1.md`
  **completed Step 1** and proves **ownership = NO**: at both anchors `descriptor+0x20 = 0x00FF` (uniform
  form), collision value `0x0001`, **bit 7 clear**, so `0x5A29C` never calls `0x5A2EE` for them. The
  platforms are **normal descriptor-0x2120 publication**, not the bit-7 surface path. Treat the rope-platform
  special-surface hypothesis as **REFUTED**; the next bounded question is where descriptor 0x2120's ordinary
  visual/collision output first diverges on Genesis at these anchors.
- **File-name vs content mismatch:** `Cody_build0398_segment11_segment12_plane_a_transition.md` is named
  "segment11_segment12" but its content correctly identifies the real boundary as **record 12 → record 13**
  (stable package 3 → 4). The filename reads stale; the content is correct.
- **Palette-line model:** the Composer tool/UI historically treats the sprite palette as Line 3 / bank 0x33,
  while the current runtime palette doc model is Line 0/1 = shared sprite, Line 3 = Layer-A master. These are
  different lenses (authoring coverage vs runtime ownership) but a reader could read them as contradictory;
  worth a one-line reconciliation when the Composer is next touched. Not edited here.

## 6. Architecture risks ([CONCERN], within the documents' own evidence)
- **Offline overlap packages are a per-boundary manual artifact.** Each residency boundary that exceeds a
  direct-switch's retention needs its own generated overlap package (8 at Seg10→11, 9 at record 12→13). This
  is policy-compliant (offline, deterministic, no runtime special-case), but it scales per-boundary — if many
  boundaries need them, the sequence table grows. Not a violation; a maintenance-surface note.
- **The initial-transition identification was wrong twice** (record 11→12 was the wrong boundary). This is a
  recurring hazard: "full name table + zero resolver misses" does not prove the correct residency package is
  installed (stated in the 0390 doc). Future transition work should verify package identity, LUT mapping,
  staged names, and physical patterns together — not just resolver hit-rate.
- No native-replacement-policy violation observed in 0384→0398: arcade still owns lifecycle/collision; the
  only native collision touch is the proven visual tail; Plane-A/B are native from retained arcade decisions.

## 7. Recommended next-work order (recommendation only — nothing started)
1. **Finish the two remaining Plane-A defects before combat/HUD/palette/audio.** Rationale: both are
   user-visible graphics correctness in the already-accepted gameplay path, both are bounded, and the
   residency/publication architecture is fresh and well-documented — the context cost is lowest now.
   - **(a) Rope platform:** pick up from the completed Step-1 result — trace descriptor 0x2120's ordinary
     visual + collision output at the two exact anchors (record-2 X48/Y40, record-14 X44/Y36) through the
     Genesis publication to find where it first diverges/disappears. The gameplay "lands one metatile low" +
     "lizard men traverse" suggests a shared visual/collision-grounding issue worth confirming together.
   - **(b) X/Y combined-scroll cell error:** reproduce deterministically, then prove (not assume) whether a
     cell is published at the wrong ring coordinate during simultaneous X/Y boundary crossing (relate to the
     Build-0353 arbitrary-scroll ring-rotation uncertainty). Intermittency makes a targeted static proof +
     narrow trace preferable to guesswork.
2. Then address OPEN-028 (sky stale names) and OPEN-029 (third-chain traversal) if still present.
3. Then combat correctness (damage/hit-reaction/HUD-health) — a larger, separate subsystem.
4. Palette-tool completion (drop-items, pickups, generic burst, Flying Demon full coverage, dynamic-vs-stable
   CRAM identification) can proceed in parallel as tooling, since it does not gate the Plane-A fixes.
5. Audio and full C decompilation remain long-horizon.

---
Production source changed: **NO** · ROM built: **NO** · Counter after: **398**. STOP.
