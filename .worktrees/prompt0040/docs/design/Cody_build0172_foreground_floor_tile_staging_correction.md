# Cody - Build 0172 Foreground Floor-Tile Staging Correction

**Date:** 2026-07-15
**Type:** Implementation-first analysis / no-build STOP
**Baseline artifact:** Build 0171 candidate `dist/rastan-direct/rastan_direct_video_test_build_0171.bin`
**Baseline SHA256:** `819a2131a7643135b46c6faaaf00153ac95c37fae2ed357659fed74075d45ab9`
**Baseline size / counter:** `1,581,848` bytes / `171`
**Scope:** Re-open the visible foreground/floor-tile boundary from Tighe's Build 0171 screenshots. No source/spec/tool/Makefile/ROM/invariant changes. No build. No collision/input/PC090OJ/D00298/Exodus chase.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010 (PC080SN BG -> Plane B, FG -> Plane A), KF-011 (arcade VBlank owns lifecycle; Genesis VBlank is service/helper and tail-jumps), KF-015 (vertical scroll convention `-raw + 8`), KF-038 (long PC080SN BG row aliasing and Build 0170/0171 tall-BG projection), OPEN-017 (Stage 1 gameplay bring-up), OPEN-001 (rendering context), OPEN-003 (MAME VDP readback can be inconclusive), and OPEN-023 (window-layer context only). Rediscovery-hazard HIGH findings touched: KF-010, KF-011, KF-038. No contradiction of a CONFIRMED/STRONG finding detected.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. This task inspects Genesis helper/staging/VBlank evidence only and does not introduce a second renderer, state forcing, collision patch, input patch, or diagnostic ROM.

## User Correction Recorded

Tighe's Build 0171 screenshots are controlling visual evidence:

- The sky/mountain background is much improved after Build 0171.
- The visible foreground/floor/terrain region is still wrong or missing.
- This is visible terrain, not collision ground.
- Tighe believes the missing visible floor/terrain is FG/foreground.
- The prior `BG sampled cells matched` result does not, by itself, resolve the visual problem.
- Sparse FG overlays cannot be dismissed until the exact screenshot region is mapped against arcade.
- Rastan crouching/down-held is a secondary symptom unless tied directly to this foreground/floor state.

## Evidence Inspected

- `states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/build0171_frame_1081.png`
- `states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/build0171_frame_0571.png`
- `states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/build0171_frame_0751.png`
- `states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/build0171_frame_1600.png`
- `states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/build0171_frame_2200.png`
- `states/traces/build0172_stage1_ground_fg_boundary_20260714_215247/arcade_zero_ground_samples.csv`
- `states/traces/build0172_stage1_ground_fg_boundary_20260714_215247/genesis_zero_ground_samples_v2.csv`
- `states/traces/build0172_stage1_ground_fg_boundary_20260714_215247/genesis_zero_ground_summary_v2.log`
- `states/traces/build0172_stage1_ground_fg_boundary_20260714_215247/arcade_zero_ground_summary.log`
- Build 0171 ROM LUT and tile-pattern bytes from `dist/rastan-direct/rastan_direct_video_test_build_0171.bin` using symbol addresses in `apps/rastan-direct/out/symbol.txt`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`

## Exact Screenshot Region

Primary rendered-frame anchor: `states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/build0171_frame_1081.png`.

The exact missing/black visual region in that screenshot is:

- Pixel rectangle: `x=0..319`, `y=112..146`
- Tile rows: row `14` through row `18` (8-pixel rows)
- Actual visible result: full-width black band across rows `112..146`, with row `18` partially transitioning back to mountain pixels below the band.

The full-width black band is not stationary across Build 0171 screenshots:

| Screenshot | Fully black row run |
|---|---:|
| `build0171_frame_0571.png` | none |
| `build0171_frame_0751.png` | `0..33` |
| `build0171_frame_1081.png` | `112..146` |
| `build0171_frame_1600.png` | `24..58` |
| `build0171_frame_2200.png` | none |

That moving rendered band is not consistent with a single fixed missing source row or a simple unstaged FG floor strip.

## Arcade vs Genesis Cell Samples For The Black Band

The following samples cover the same screen-row family as the `y=112..146` black band. The arcade and Genesis scripted timelines are not perfectly frame-locked, so these are used as ownership/source-row evidence, not as a perfect per-frame visual composite proof.

| Screen col,row | Arcade BG code | Arcade FG code | Genesis staged BG | Genesis tall BG | Genesis staged FG | Build 0171 BG slot source |
|---:|---:|---:|---:|---:|---:|---|
| `2,14` | `0x06AB` | `0x0420` | `0x4271` | `0x4271` | `0x0000` | slot `0x0271` maps to arcade tile `0x06AB` |
| `4,15` | `0x06B5` | `0x0426` | `0x427B` | `0x427B` | `0x6065` | slot `0x027B` maps to arcade tile `0x06B5` |
| `8,16` | `0x0696` | `0x0020` | `0x425C` | `0x425C` | `0x6000` | slot `0x025C` maps to arcade tile `0x0696` |
| `16,17` | `0x06A5` | `0x00BF` | `0x426B` | `0x426B` | `0x6000` | slot `0x026B` maps to arcade tile `0x06A5` |
| `28,18` | `0x0676` | `0x00C3` | `0x423C` | `0x423C` | `0x6000` | slot `0x023C` maps to arcade tile `0x0676` |

Build 0171 ROM tile-pattern residency check:

| Arcade tile | Build 0171 pattern status |
|---:|---|
| `0x06AB` | nonblank (`32/32` nonzero bytes) |
| `0x06B5` | nonblank (`32/32` nonzero bytes) |
| `0x0696` | nonblank (`32/32` nonzero bytes) |
| `0x06A5` | nonblank (`32/32` nonzero bytes) |
| `0x0676` | nonblank (`32/32` nonzero bytes) |
| `0x0426` | nonblank (`32/32` nonzero bytes) |

Interpretation: the exact black-band row family has BG terrain cells staged and projected, and their Build 0171 tile patterns are resident/nonblank. FG is sparse in arcade and sparse/blank in Genesis at these sample points. Missing sparse FG overlays remain real work, but they do not explain a full-width black band that erases nonblank BG terrain.

## FG-Specific Answers

1. **Is the arcade missing floor/foreground visual layer on FG/Plane A?**
   Partially. The sampled arcade region is primarily BG/PC080SN page 0 terrain with sparse FG/page 2 overlays (`0x0420`, `0x0426`, `0x00BF`, `0x00C3`, and blanks). It is not an FG-only floor.

2. **Does Genesis stage those FG cells at all?**
   Partially. Build 0171 steady summaries show `fg_nz=2016`, and the sampled row family contains one sparse overlay (`0x6065`) plus mostly blank/blank-slot cells (`0x0000` or `0x6000`).

3. **Are staged FG cells blank, wrong, or correct?**
   Mixed/incomplete. The sample at screen `4,15` stages a nonblank overlay slot (`0x6065`) corresponding to arcade tile `0x0426`. Other sampled cells are blank or blank-slot while arcade has sparse overlay codes at some points. This is an FG overlay gap, but not enough to explain the full-width black terrain band.

4. **Are expected FG tile graphics resident in the LUT/VDP tile set?**
   For sampled overlay tile `0x0426`, Build 0171 slot `0x0065` maps back to nonblank tile data. The evidence does not prove every sparse overlay tile is resident, but the key black-band terrain is already carried by nonblank BG slots.

5. **Are expected FG cell words committed to Plane A?**
   Not proven by reliable VDP readback. The source path exists (`vdp_commit_fg_narrow_strips` branches into `vdp_commit_fg_strips_if_dirty`), but MAME `:gen_vdp` readback in the previous harness returned all-zero and is treated as inconclusive under OPEN-003.

6. **Are priority/palette/transparent-code bits causing them to disappear?**
   Not proven. The sampled BG cells use nonblank slots with attr bits such as `0x4000`; sampled FG blanks use slot `0x0000` with `0x6000`. Priority/palette/transparency could affect sparse overlays, but cannot by itself explain why an entire nonblank BG row family renders as black without rendered-frame VDP/CRAM evidence.

7. **Is FG using a 32-row model where it needs a tall/rolling model?**
   Not proven for the black band. Gameplay FG_SRC staging currently emits the visible top 32 rows from `FG_SRC_BASE_GEN` using `genesistan_stage_fg_src_column`. The exact sampled black-band terrain is BG-owned and already handled by the tall-BG projection path.

8. **Did the Build 0160 FG_SRC fold only restore title/FG counts but miss gameplay floor-bearing rows?**
   The fold participates in gameplay FG staging and produces `fg_nz=2016`, but the sampled main terrain/floor cells are not primarily FG-owned. The missing sparse overlays remain a separate follow-up, not the first proven black-band cause.

9. **Are FG rows overwritten or not marked dirty?**
   Not proven. Steady samples show `fg_dirty=0` after commits, which is expected after a successful VBlank commit. No evidence here proves a later overwrite or missing dirty marking for the sampled full-width black band.

10. **Is Plane A hidden, masked, or scrolled differently than arcade?**
   Not proven. Plane A/window/SAT overlap remains a possible rendered-frame issue, but this task did not produce reliable VDP layer readback for the exact screenshot frame.

## BG Sanity Check

The exact black-band row family in Build 0171 is not empty in BG staging:

- `staged_bg_buffer` and `staged_bg_tall_buffer` match for the sampled cells.
- The mapped slots correspond to the expected arcade terrain tile family (`0x06AB`, `0x06B5`, `0x0696`, `0x06A5`, `0x0676`).
- The Build 0171 ROM contains nonblank tile patterns for those source tiles.
- `bg_nz=2048` and `tall_bg_nz=4096` in steady gameplay summaries.

Therefore the first proven divergence is not `BG/FG source failed to populate the exact row family`. The divergence is later: staged/intended nonblank terrain exists, but the rendered screenshot still has black pixels.

## Classification

Primary classification: **G - more evidence needed**.

Working interpretation: evidence points toward an **F-class VINT/VDP/render-presentation boundary** because the exact black band moves between screenshots and covers nonblank staged/projected BG terrain. However, the exact subtype is not proven: missed VINT, display-off duration/overrun, Plane B commit timing, scroll/projection phase, Window/SAT masking, CRAM/priority, or emulator readback artifact remain distinguishable possibilities.

Rejected as a build-safe classification:

- **A:** not proven. The sampled visible floor/terrain is not FG-only and Genesis has sparse FG overlay staging.
- **B:** not proven. Plane A commit failure is possible for overlays but does not explain full-width BG terrain disappearing.
- **C:** not proven. Some FG overlays may be blank/wrong, but sampled BG pattern data is nonblank.
- **D:** partially true as visual composition context, but not enough to identify a patch. The full black band covers BG-owned terrain too.
- **E:** not supported for this exact row family. The black-band samples now cover `y=112..146` / rows `14..18`, and BG is populated there.
- **F:** suspected, but not proven narrowly enough to build.

## Build Decision

Build 0172 was **not** produced. A source patch would be speculative because no bounded FG staging/commit/source/window defect is proven for the exact missing visual region.

The smallest safe next proof is rendered-frame VDP correlation for the exact black-band window:

- Plane B nametable cells for pixel rows `112..146`, columns across the screen.
- Plane B pattern bytes for slots `0x0271`, `0x027B`, `0x025C`, `0x026B`, `0x023C` and nearby cells.
- CRAM line for the BG attr bits used by `0x42xx` cells.
- Plane A/window/SAT coverage over the same rectangle.
- VDP reg 1 display-enable timing and `0x700C2..0x3A27E` VBlank-chain cadence around frames `751`, `1081`, and `1600`.

## Crouch / Down-Held Note

Rastan crouching/down-held remains recorded as a user-visible symptom, but this task did not prove it shares a cause with the visible terrain/floor failure. No input, collision, or player-state patch is justified here.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017; OPEN-001 and OPEN-003 context; OPEN-023 context only for possible window/layer masking.
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: exact rendered-frame VDP correlation, sparse FG overlay completeness, VINT/display-off timing, input/crouch/control-lock, collision byte-equivalence, real Genesis freeze/contact behavior, PC090OJ/READY/header sprites, continue/game-over, D00298, Exodus loop, records `132..134`.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed. This task corrects the Build 0172 visible-region analysis and narrows the black-band boundary, but does not prove a durable new mechanism beyond existing KF-038/open VDP timing concerns.

## STOP

STOP triggered: **YES for implementation/build**. The exact visual region is now sampled, but the first proven divergence is rendered output after nonblank staging, not a bounded FG floor-tile staging defect.
