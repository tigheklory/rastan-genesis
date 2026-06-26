# Cody - Build 0096 Visible-Window Origin Correlation

**Date:** 2026-06-24  
**Type:** Read-only visible-window/runtime evidence correlation  
**Build:** Build 0096, `dist/rastan-direct/rastan_direct_video_test_build_0096.bin`  
**Build SHA256:** `c054107bc6dfccb45b1703a0896be9905f729b89d1e0b16a4677d30badfde51c`  
**Scope:** Existing Build 0096 ROM and original arcade runtime/reference only. No source/spec/tool/Makefile/ROM/build/invariant changes. No implementation. No ROM instrumentation. No bookmark cycle. No OPEN-015 or Start-crash work.

## Phase 0

Classification: **EXTENDING** (OPEN-001). OPEN-016 is context; OPEN-015 is not touched.

Architecture compliance: **CONFIRMED.** Arcade runtime is treated as visual intent; Genesis Build 0096 is measured as current port behavior. This diagnostic does not change program ownership or introduce Genesis-side lifecycle logic.

Address mapping discipline: all arcade-to-Genesis code/data address correlations in this note were checked against `build/rastan-direct/address_map.json`. No `+0x200` arithmetic is used as proof.

Relevant priors loaded:

- `docs/design/Cody_build_0096_scroll_origin_trace.md`
- `docs/design/Andy_build_0096_title_coordinate_origin_audit.md`
- `docs/design/Cody_build_0096_title_bg_blockcopy_staging_impl.md`
- `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, recent `AGENTS_LOG.md`

Established facts preserved:

- Scroll-word hypothesis is refuted for this title state: arcade and Genesis raw scroll words are all zero.
- Layer B raw staging for the title BG block is faithful: arcade PC080SN destination `0x00C00328` is row 3 / col 10; Build 0096 stages the block rows 3..22 / cols 10..37.
- `ALL RIGHTS RESERVED` and `CREDIT` are below the 224-line Genesis visible window in the captured Build 0096 title state.
- The BG block-copy helper remains exonerated.

## Evidence Artifacts

Arcade-intent visual evidence:

- Original arcade reference frame: `/home/tighe/.mame/snap/rastan/RASTAN TITLE REFERENCE MAME.png`
- Dimensions: `320x240`
- Prior original-arcade runtime dump directory: `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/`
- Runtime PC080SN BG dump: `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/arcade_pc080sn_bg_after_title.bin`
- Runtime PC080SN FG dump: `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/arcade_pc080sn_fg_after_title.bin`
- Runtime PC090OJ dump: `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/arcade_pc090oj_after_title.bin`

Genesis-behavior visual evidence:

- Fresh native MAME capture from Build 0096 ROM: `states/screenshots/build_0096_visible_origin_probe/mame_native/build0096.avi`
- Native AVI dimensions: `256x224`, `481` frames, about `8.027s`
- Exact Genesis title frame used: `states/screenshots/build_0096_visible_origin_probe/mame_native/exact_frames/build0096_frame_000060_title.png`
- Dimensions: `256x224`
- Contact sheet: `states/screenshots/build_0096_visible_origin_probe/mame_native/build0096_contact.png`
- Measured bbox images:
  - `states/screenshots/build_0096_visible_origin_probe/arcade_frame060_measured_bboxes.png`
  - `states/screenshots/build_0096_visible_origin_probe/genesis_frame060_measured_bboxes.png`
- Measurement JSON: `states/screenshots/build_0096_visible_origin_probe/visible_coordinate_measurements_frame060.json`

Notes:

- The Genesis frame is the native MAME output from the Build 0096 ROM. It is intentionally not a scaled GUI screenshot.
- A separate clean Exodus capture was inspected earlier, but native MAME `256x224` output is the primary Genesis-behavior evidence here.
- A debugger-side VDP-control trace attempt did not produce a usable Build 0096 transcript, so runtime VDP register facts are not claimed from that attempted trace.

## JSON Address Mapping Checks

| Arcade address | Mapped Genesis address | JSON segment | Segment kind/source |
|---:|---:|---:|---|
| `0x03AA88` | `0x03AC88` | `27` | `arcade_copy`, `whole_maincpu_copy` |
| `0x03BB48` | `0x03BD48` | `106` | `patched_site` |
| `0x05A38E` | `0x05A58E` | `171` | `arcade_copy`, `whole_maincpu_copy` |
| `0x05A4DE` | `0x05A6DE` | `172` | `patched_site` |
| `0x05B0B2` | `0x05B2B2` | `173` | `arcade_copy`, `whole_maincpu_copy` |

These mappings are JSON-derived. They are not arithmetic proof.

## Arcade Display / Window Setup

From the original MAME Rastan driver (`docs/reference/mame/rastan/src/mame/taito/rastan.cpp`):

- Screen size: `40*8` by `32*8` = `320x256`
- Visible area: X `0..319`, Y `8..247` = `320x240`
- The reference screenshot is therefore a 320x240 visible frame with visible tile rows corresponding to arcade tilemap rows 1..30.
- `screen_update` runs `pc080sn.tilemap_update()`, draws PC080SN layer 0 opaque, draws PC080SN layer 1, then draws PC090OJ sprites.

From `pc080sn.cpp`:

- Standard PC080SN tilemaps are `64x64` cells of `8x8` pixels.
- Base tilemap scrolldx includes `-16`, but the bounded runtime scroll-origin trace already proved the title-state raw scroll words and PC080SN scroll writes are zero.
- The important final-visible origin fact for this diagnostic is the arcade visible rectangle's Y start at pixel 8, not a nonzero title scroll word.

## Genesis VDP / Display Setup

From Build 0096 source setup in `apps/rastan-direct/src/vdp_comm.s`:

| Setting | Value / behavior |
|---|---|
| Plane A register | `0x38` -> Plane A base `0xE000` |
| Window register | `0x3C` -> window base `0xF000` |
| Plane B register | `0x06` -> Plane B base `0xC000` |
| SAT register | `0x7C` |
| BG color register | `0x00` |
| Mode 3 | `0x00`, full-screen scroll mode |
| Mode 4 | `0x0081` as written by source |
| HScroll table | `0x3F` -> `0xFC00` |
| Plane size | `0x01` |
| Window X/Y | `0x00` / `0x00` |
| VBlank display toggle | Mode2 off `0x34`, commits, Mode2 on `0x74` |
| Scroll commits | `staged_scroll_x_fg/bg` and `staged_scroll_y_fg/bg`; prior trace observed all zero |

Measured Genesis-behavior from native MAME video:

- Final visible output captured as `256x224`.
- The visible grid is therefore `32x28` cells at `8x8` pixels.
- This differs from original arcade `320x240` (`40x30` visible cells).

This is the load-bearing final-display/window discrepancy in the current evidence.

## Four-Coordinate Table

Coordinates are given as cell bounding boxes `[x0,y0,x1,y1]` for visible elements. Pixel boxes are in the JSON artifact.

`#1 arcade raw` and `#3 Genesis staged` are only asserted where the raw producer/staging path is already proven or safely isolable. `#2 arcade visible` and `#4 Genesis visible` are measured from the visual frames.

| Element | Layer / source | #1 arcade raw PC080SN coordinate | #2 arcade final visible | #3 Genesis staged / nametable | #4 Genesis final visible | Visible delta (#4 - #2) |
|---|---|---|---|---|---|---|
| SCORE / 1UP / HIGH SCORE / 2UP | Separate/top HUD path, not isolated in Build 0096 staging | Not isolated in this task | `[6,0,37,3]` visible top HUD region | Not present in captured staging rows 0..2 per prior scroll trace | Absent semantically in Build 0096 title frame | Missing, not a measured shifted element |
| RASTAN wordmark + sword/title art | Layer B title BG block | Block destination `0x00C00328` = raw row 3 col 10; block size `28x20` | Nonblack title-art bbox `[8,2,32,21]` | Rows `3..22`, cols `10..37` in `staged_bg_buffer` | Nonblack title-art bbox `[10,3,31,21]`, right-clipped at x=255 | Top-left +2 cols, +1 row by bbox; raw block origin itself is same col and +1 visible row because arcade visible Y starts at tile row 1 |
| Large red TAITO logo | Layer A / FG glyph-symbol path, semantic raw logo not fully isolated | Not safely isolated; prior trace only identified symbol descriptor rows 23/24 | `[15,22,24,23]` | Candidate symbol rows 23/24 exist, but not enough to prove whole logo raw bbox | `[18,23,26,24]` | +3 cols, +1 row by bbox; X not treated as raw-math proof |
| Copyright line | Layer A text | Build 0096 descriptor row 26 col 9 for `@ TAITO AMERICA CORP. 1987`; arcade reference text differs by region/content | `[4,25,33,25]` | Row 26, cols 9..34 in `staged_fg_buffer` | `[9,26,31,26]`, right-clipped at x=255 | +5 cols, +1 row by bbox; X affected by different string/content and 32-column clipping |
| ALL RIGHTS RESERVED | Layer A text | Descriptor row 28 col 12 | `[10,27,28,27]` | Row 28, cols 12..30 | Absent | Clipped by Genesis 28-row / 224-line visible window |
| CREDIT | Layer A text | Descriptor row 30 col 33 | `[31,29,39,29]` | Row 30, cols 33..41 | Absent | Clipped by Genesis 28-row / 224-line visible window and horizontally outside 32-column width |

### Delta Interpretation

Measured final-visible rows share a consistent `+1` row component for the visible title elements:

- Layer B title art: arcade visible row 2 -> Genesis visible row 3.
- Layer A red TAITO: arcade visible row 22 -> Genesis visible row 23.
- Layer A copyright: arcade visible row 25 -> Genesis visible row 26.

This row delta is explained by the final-visible-window difference:

- Arcade final visible area starts at source pixel Y=8, so raw tilemap row 3 appears at visible row 2.
- Genesis native output starts at visible row 0 and is 224 lines tall, so staged row 3 appears at visible row 3.

The measured X deltas are **not** a clean shared +1 cell in native Build 0096 evidence:

- Layer B bbox top-left: +2 cols, with the right edge clipped at Genesis cell 31.
- Large red TAITO bbox: +3 cols, with raw semantic logo coordinate not safely isolated.
- Copyright bbox: +5 cols, affected by region/text-content difference and right clipping.

The stronger X finding is not a scroll-origin cell nudge; it is that native Genesis Build 0096 is displayed as 32 cells wide (`256px`) while arcade intent is 40 cells wide (`320px`). The Layer B raw block is staged cols 10..37; in a 32-column visible window, cols 32..37 are offscreen.

## Questions Answered

### 1-2. Final visible coordinates

Arcade-intent and Genesis-behavior coordinates are listed in the four-coordinate table above. The arcade frame is `320x240`; the Genesis native frame is `256x224`.

### 3. Per-element visible deltas

Layer A and Layer B share a **+1 visible row** component. They do **not** share a proven uniform +1 visible X-cell delta in the native MAME evidence. X behavior is dominated by a 32-column final window and right-side clipping.

### 4. Layer A raw coordinate confirmation

Layer A raw math was not globally re-proven here. Safely supported Layer A raw facts from the prior Build 0096 trace:

- `@ TAITO AMERICA CORP. 1987`: row 26, first col 9, last col 34.
- `ALL RIGHTS RESERVED`: row 28, cols 12..30.
- `CREDIT`: row 30, cols 33..41.
- Symbol rows 23/24 exist and likely contribute to the red TAITO logo, but the large red TAITO logo's full semantic raw bbox was not isolated in this task. Therefore no Layer-A-specific raw offset is proven.

### 5. Genesis VDP display setup

Build 0096 source writes Plane A/B bases, full-screen scroll mode, HScroll table, plane size, and window registers as listed above. Prior runtime trace observed all scroll commits writing zero. The fresh native MAME capture shows final Genesis output as `256x224` (`32x28` cells).

### 6. Arcade PC080SN display/window setup

Original arcade MAME driver sets visible area to `320x240`: X `0..319`, Y `8..247`. This is a 40-column by 30-row visible window, with the top source tile row cropped away by the arcade visible rectangle.

### 7. Verdict

**Verdict: (d) something more specific than the earlier scroll-word hypothesis: final visible-window/display policy mismatch.**

Proven:

- Raw scroll-word delta is `0/0` for both arcade and Genesis in this title state.
- Layer B raw staging is faithful.
- Native Genesis Build 0096 final output is `256x224`, while arcade intent is `320x240`.
- Visible rows differ by one because arcade clips source row 0 (`visible Y starts at 8`) while Genesis displays staged row 0 at the top of a 224-line frame.
- X mismatch is not proven as a uniform +1 cell. It is primarily a 40-column arcade window vs 32-column Genesis native visible window/clipping problem in this evidence.

Not supported:

- A fix that adjusts the BG block-copy helper.
- A fix that wires a nonzero scroll word for this title state.
- A claim that Layer A has a separate raw-coordinate bug from this evidence.

Owning layer: **final display/window setup / viewport policy**, not producer coordinate decode or staging.

### 8. ALL RIGHTS / CREDIT

Confirmed clipped by Build 0096's native `224px` / 28-row visible output:

- `ALL RIGHTS RESERVED` is staged at row 28, just below visible rows 0..27.
- `CREDIT` is staged at row 30 and horizontally begins at col 33, outside both the 28-row height and 32-column native width.

Their absence is not evidence of a producer failure in this title frame.

### 9. SCORE / 1UP / 2UP

The arcade reference visibly contains SCORE/1UP/2UP in the top HUD region. Build 0096's native title frame does not semantically contain that top HUD line. Prior staging evidence did not find it in rows 0..2. It is therefore classified as **missing/not staged or separate HUD path**, not merely clipped by the +1 row display-window effect.

## Recommended Fix Class

Recommended class: **VDP display-register / visible-window setup investigation**, specifically reconciling the Genesis final visible mode/window with the arcade `320x240` intent.

Do **not** implement from this diagnostic alone. The evidence is sufficient to stop chasing raw staging and scroll-word wiring, but it is not yet a complete patch recipe because:

- Native Build 0096/MAME output is `256x224` despite the source register setup including Mode4 `0x0081`; a runtime-confirmed VDP register/mode decode should be captured before changing display setup.
- Vertical policy must be chosen deliberately: arcade shows 30 rows (Y source 8..247), while Genesis currently shows 28 rows. Whether to target 224-line clipping, 240-line mode, or content re-windowing is a user/architecture decision.
- SCORE/1UP/2UP remains a separate HUD-production question.

Safe to implement now: **NO**. Safe to narrow next: **YES** - capture runtime VDP register state/output mode and decide the 320x240-to-Genesis viewport policy before any display-register change.

## OPEN / CLOSED Issues Impact

- OPEN-001: active; visible title-window failure narrowed to final display/window policy plus separate missing HUD path.
- OPEN-016: context only; no closure.
- OPEN-015: not touched.
- New issues opened: NONE.
- Issues closed: NONE.

## KNOWN_FINDINGS Impact

Option A: no `KNOWN_FINDINGS.md` update from this diagnostic alone. The durable finding should wait until a runtime-confirmed display setup fix or policy decision exists.

## STOP

STOP triggered: **NO** for diagnostic completion.  
Implementation safety: **NO**; exact display-mode/viewport correction is not safely placeable yet.

---

## CORRECTION - User-Provided H40 Evidence Supersedes 256x224 Capture Interpretation

**Date:** 2026-06-24  
**Correction type:** Documentation correction only. No new diagnostic, no source/spec/tool/ROM/build changes, no implementation.

### Authoritative User-Provided Evidence

Tighe provided live Build 0096 VDP evidence from Exodus and a same-ROM MAME screenshot after this report was written. This evidence is **user-provided**, not Cody-generated.

User-provided Build 0096 live Exodus VDP register evidence:

- VDP register 12 / Mode Set 4 = `0x81`.
- RS1 / H40 enable is set.
- Build 0096 is therefore confirmed as **H40 / 320x224**, the intended horizontal display mode.
- Corroborating user-provided register state:
  - Plane A base: `0xE000`
  - Plane B base: `0xC000`
  - Window base: `0xF000`
  - HScroll table: `0xFC00`
  - H-scroll size: `64`
  - V-scroll size: `32`
- User-provided MAME screenshot from the same Build 0096 ROM, run with `mame genesis -cart ... -window -nounevenstretch -nofilter -nomaximize -resolution 640x480`, shows `320x224` output.

### Retractions

The following conclusions in the original report are **RETRACTED**:

- The interpretation that Build 0096's ROM display mode was `256x224` / H32.
- The interpretation that the title-art X mismatch was dominated by a real 32-column / 256px Genesis visible window.
- The conclusion that right-side clipping from a 256-wide ROM display window explains the horizontal placement issue.

The earlier native MAME AVI measurement genuinely produced a `256x224` capture. The error was interpreting that capture size as the ROM's VDP display mode. Per user-provided live Exodus VDP registers, that AVI size is now classified as a **capture-path artifact**, not Build 0096 display intent or runtime VDP mode.

### Corrected Placement Measurement

Tighe measured the Build 0096 Genesis title screenshot against the original arcade title screenshot using addition-layer overlay blending.

Corrected user-measured visible displacement:

- X: Genesis is `+16 px` RIGHT relative to arcade = `+2 tile columns`.
- Y: Genesis is `+8 px` DOWN relative to arcade = `+1 tile row`.

This supersedes all earlier rough `+1/+1` wording. The placement bug is **asymmetric** (`+2 columns`, `+1 row`), so it is **not** a uniform one-based-vs-zero-based origin bug.

### Still-Valid Findings

These parts of the original report remain valid:

- Layer B raw staging for the known title-art block remains faithful: arcade PC080SN destination `0x00C00328` maps to row 3 / col 10, and Build 0096 stages rows `3..22`, cols `10..37`.
- The BG block-copy helper remains exonerated by raw staging evidence.
- Scroll-word hypothesis remains refuted for this title state: arcade and Genesis raw scroll words are zero in the bounded trace.
- `ALL RIGHTS RESERVED` at row 28 and `CREDIT` at row 30 remain below the Genesis 28-row / 224-line visible area. Their absence is still expected 240-to-224 vertical clipping / viewport policy, not a producer failure by itself.
- SCORE / 1UP / 2UP remains missing/not staged in the captured Build 0096 title evidence and is still a separate HUD thread.
- The large red TAITO logo must **not** be described as complete. It still has four internal missing tiles, tracked as a separate Layer A glyph/tile defect.

### Corrected Verdict

Corrected verdict: **Build 0096 is confirmed H40 / 320x224, and the title-composition placement bug remains OPEN.**

The valid placement problem is now:

- Genesis title composition is offset from arcade by `+16 px` X (`+2 cols`) and `+8 px` Y (`+1 row`).
- This offset is real user-measured evidence.
- Its mechanism is still unexplained by the current report.
- The previous 256-wide/right-clipping explanation is retracted.

Owning class remains display/coordinate/origin investigation under OPEN-001, but the exact mechanism is **not safely placeable** from the corrected evidence alone.

### KNOWN_FINDINGS Impact

Option C - assess-only proposal, not applied:

> Build 0096 title visible-window correction: user-provided live Exodus VDP registers confirm H40 / `320x224` (`VDP reg 12 = 0x81`, RS1 set). A prior Cody native-MAME AVI captured `256x224`, but that is now classified as a capture-path artifact, not ROM display mode. User addition-blend overlay against the arcade title screenshot measures the real title-composition offset as `+16 px` X (`+2 cols`) and `+8 px` Y (`+1 row`). The offset is asymmetric and remains OPEN; it is not explained by a uniform one-based origin bug, by the BG block-copy helper, or by nonzero scroll-word wiring in the measured title state.

### Corrected Implementation Safety

Safe to implement now: **NO**.

Recommended next diagnostic: a bounded coordinate/origin trace that starts from the corrected facts (`H40 / 320x224`, real offset `+16/+8`) and identifies why faithful raw staging still reaches final visible composition offset by `+2 cols / +1 row`. Do not chase H32/256px mode. Do not modify the BG block-copy helper. Do not treat the red TAITO logo as complete.

### Open / Closed Issues Impact

- OPEN-001: active; placement bug remains open and is now corrected to `+16 px / +8 px` user-measured offset.
- OPEN-016: context only.
- OPEN-015: not touched.
- New issues opened: NONE.
- Issues closed: NONE.

### STOP

STOP triggered: **NO** for documentation correction.  
Implementation safety: **NO**; placement remains unresolved.
