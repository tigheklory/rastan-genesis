# Cody - Build 0170 BlastEm Video Observations

**Date:** 2026-07-14  
**Type:** Runtime video evidence capture / visual observation only  
**Build:** 0170  
**Source video:** `states/screenshots/Blastem_build_170.mp4`  
**Video metadata:** 83.67s, 30 fps, 1252x1180, 2510 extracted frames  
**Scope:** Documentation/evidence only. No source, spec, tool, Makefile, ROM, invariant, or build changes.

## Evidence Captured

Full 30fps screenshot sequence:

- `states/screenshots/build_170_blastem_30fps/frames/frame_00001.jpg` through `frame_02510.jpg`
- Frame index: `states/screenshots/build_170_blastem_30fps/frame_index.tsv`
- Labeled contact sheet: `states/screenshots/build_170_blastem_30fps/contact_sheet_1sec_labeled.jpg`
- Secondary contact sheets: `states/screenshots/build_170_blastem_30fps/contact_sheet_1sec.jpg`, `states/screenshots/build_170_blastem_30fps/contact_sheet_2sec.jpg`

Representative annotated PNGs:

| Frame | Time | Path | Observation |
|---:|---:|---|---|
| 1 | 0.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_00001_title_full_art.png` | Title/logo screen renders with title art, sword, score text, and TAITO text. |
| 301 | 10.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_00301_push_button_prompt.png` | Coin/start prompt path is visible; statue/title prompt screen renders. |
| 451 | 15.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_00451_round_ready.png` | `ROUND 1` / `READY !` appears before gameplay. |
| 571 | 19.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_00571_gameplay_entry_sky_fixed_no_ground.png` | Gameplay begins; sky/cloud field is now visibly populated, but expected ground is absent. |
| 751 | 25.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_00751_gameplay_sky_fixed_missing_ground.png` | Sky remains populated; player is not on a proper visible floor/platform. |
| 1081 | 36.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_01081_gameplay_mountain_vertical_column_wrong.png` | Mountain/vertical-column composition is wrong; visible terrain still lacks correct ground. |
| 1561 | 52.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_01561_gameplay_mountain_fill_no_ground.png` | Screen becomes dominated by mountain texture; this does not match expected Stage 1 ground/terrain composition. |
| 1801 | 60.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_01801_gameplay_mountain_wall_no_ground.png` | Mountain/wall region remains wrong; no correct floor is visible. |
| 2251 | 75.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_02251_later_sky_loop_no_ground.png` | Later gameplay/loop view returns to sky-heavy projection with no correct ground. |
| 2491 | 83.000s | `states/screenshots/build_170_blastem_30fps/samples/frame_02491_late_capture_sky_no_ground.png` | Late capture still shows sky-heavy output and missing ground. |

## Observed Runtime Sequence

- **Observed:** Build 0170 reaches the title screen with the title logo and text visibly intact.
- **Observed:** The coin/start prompt and story/start transition are visible.
- **Observed:** `ROUND 1` / `READY !` appears before gameplay.
- **Observed:** Stage 1 gameplay starts around frame 571 / 19.0s.
- **Observed:** The sky/cloud layer is materially improved versus the pre-tall-BG symptom. The sky is now populated rather than blank/yellow/magenta.
- **Observed:** Mountains and vertical rock/wall columns are not composed correctly. They appear in wrong positions/large repeated spans.
- **Observed:** The expected ground/floor is not visible where Rastan should stand or walk.
- **Observed:** The player and scene continue moving/scrolling during gameplay after the start transition.
- **User-reported:** After starting the game, there was zero further player input.
- **User-reported:** Player input does nothing. The video itself does not include an input overlay, so this should be treated as a runtime/user observation rather than video-instrumented proof.

## Debug Window Observations

- **Observed:** The BlastEm VDP CRAM window remains populated through the run. There is no obvious full palette wipe in this recording.
- **Observed:** The BlastEm VDP VRAM/pattern window contains terrain/mountain-like pattern data while the main game window still lacks correct ground composition.
- **Interpretation:** The missing ground is unlikely to be explained solely as all terrain pattern data missing from VRAM. The stronger visual suspicion is still BG map/window/projection/row-origin selection, or which rows are being projected into the visible Genesis plane.
- **Caution:** This video is not a tile-code trace. The pattern-window view suggests residency, but does not by itself prove the exact arcade tile codes or Genesis slots used for a given visible cell.

## Build 0170 Assessment

Build 0170 appears to have fixed the most obvious sky/row-alias symptom from the Stage 1 tall-BG work. That is real progress: the sky is visibly present and stable across gameplay frames.

However, Build 0170 is not visually correct for Stage 1 gameplay:

- The mountain layer is wrong.
- The ground/floor is missing where expected.
- The player is not interacting with a proper visible terrain surface.
- The player/scene continues moving despite the user's report of no input after game start.
- User reports active input does not affect the player.

## Recommended Next-Build Focus

1. **Primary next target: Stage 1 BG visible-window / ground projection.**  
   The tall BG backing buffer appears to help sky rows, but the visible projection still does not select/compose the correct lower terrain rows. The next trace should compare the projected `staged_bg_buffer` cells for the actual visible bottom rows against the tall BG source rows and expected arcade Stage 1 cells at the same scroll position.

2. **Separate mountain/wall row-origin from tile residency.**  
   Since mountain-like pattern data is visible in the VRAM/pattern window, first test whether the wrong mountain/wall visuals are a projection/window-origin problem before chasing conversion or DMA residency.

3. **Treat input/control as a separate observed symptom unless proven shared.**  
   The user reports zero input after start and ineffective controls. The video shows autonomous movement/scrolling, but it does not prove where input state is lost. A focused gameplay input-read/state trace should be separate from the BG projection fix unless a shared state transition is proven.

4. **Do not broaden into PC090OJ or D00298 from this video.**  
   This recording's clearest failure is Stage 1 BG/terrain composition and visible ground absence. Sprite work and D00298 remain out of scope for this observation pass.

## Suggested Prompt Seed For Chad III / Next Cody Task

Use Build 0170 video evidence as a visual gate: sky is improved, but Stage 1 lower terrain is still wrong. Run a bounded Stage 1 BG visible-window trace at frames matching the BlastEm video around frame 571, 751, and 1081. For each frame, dump BG scroll Y, projection base, the 32 projected Plane-B rows, and the corresponding 64-row `staged_bg_tall_buffer` source rows. Compare visible bottom-row cells against original arcade Stage 1 expected ground/mountain cells. Do not touch input, collision, PC090OJ, D00298, or broad VBlank unless the trace proves a shared root.

## STOP Status

STOP triggered: NO. Evidence/documentation completed. No implementation was attempted.
