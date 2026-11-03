# Cody - Build 0172 PC080SN FG 64-Row Parity Candidate

**Date:** 2026-07-15
**Type:** Implementation + build + bounded runtime/visual validation
**Baseline:** Build 0171 candidate `dist/rastan-direct/rastan_direct_video_test_build_0171.bin`
**Baseline SHA256:** `819a2131a7643135b46c6faaaf00153ac95c37fae2ed357659fed74075d45ab9`
**Build produced:** Build 0172
**Build 0172 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0172.bin`
**Build 0172 SHA256:** `c2ed780af704737ed813704a414a7609ed2e7f4629b243108c8934273da15ac9`
**Build 0172 size / counter:** `1,582,224` bytes / `172`

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010 (PC080SN BG -> Plane B, FG -> Plane A), KF-011 (arcade VBlank owns frame progression), KF-015 (vertical scroll convention `-raw + 8`), KF-038 (long PC080SN rows require tall preservation before visible-window projection), KF-042 (Stage 1 selector repair moved gameplay path back through BG branch, requiring FG_SRC fold), OPEN-017 (Stage 1 gameplay bring-up), OPEN-001 (rendering context), and OPEN-003 (VDP readback caution). No contradiction of a CONFIRMED/STRONG finding detected.

Architecture compliance: **CONFIRMED**. Arcade code remains the program. The change is limited to Genesis helper/staging/VBlank commit behavior for arcade-produced PC080SN FG intent; no collision, input, player state, hardcoded tiles, alternate renderer, or Genesis-owned lifecycle was added.

## User Correction Recorded

This task treats the remaining Build 0171 symptom as **PC080SN FG / visible foreground row-depth and projection parity**, not as collision ground and not as another BG-only sampling exercise.

Preserved assumptions:

- Build 0171 BG tall backing and rolling projection remain intact.
- Build 0171 sky/mountains/left wall improvement should not be undone.
- The visible foreground/floor/terrain under and around Rastan remained wrong/missing in Build 0171.
- Tighe believes that missing visible terrain is FG/foreground behavior.

## Current FG Source Path Before Build 0172

The gameplay FG source path is `genesistan_hook_tilemap_plane_a -> genesistan_stage_fg_src_column`, gated by `genesistan_current_scene_id == 1`. This was introduced by the Build 0160 FG_SRC fold after Build 0159 fixed the PC080SN pass selector back to the BG branch.

Before this task, the path used:

- `FG_SRC_BASE_GEN = 0x00016B1C`
- `FG_SRC_STRIDE = 0x000022C0`
- `FG_PRODUCER_ROW_COUNT = 4`
- `FG_PRODUCER_SEG_COUNT = 8`
- `genesistan_hook_tilemap_fg_fill`

That means only `8 * 4 = 32` rows were staged. The source comment explicitly documented the hidden limitation: segments `8..15` would wrap/overwrite because `genesistan_hook_tilemap_fg_fill` stages into the 32-row `staged_fg_buffer` model.

## Bounded Mechanism

The bounded parity mechanism is real:

1. The gameplay FG model is structurally a 16-segment / 64-row source family, matching the same row-depth class as the Stage 1 long BG column producer.
2. Build 0171's gameplay FG_SRC path preserved only segments `0..7` / rows `0..31`.
3. Rows `32..63` were not preserved in any gameplay FG backing representation.
4. Non-gameplay FG paths are separate and still use the original 32-row FG behavior.

This made the implementation safe to bound to gameplay scene 1.

## Implementation

### `apps/rastan-direct/src/tilemap_hooks.s`

- Added `genesistan_hook_tilemap_fg_fill_tall`.
- Changed `FG_PRODUCER_SEG_COUNT` from `8` to `16`.
- Changed `genesistan_stage_fg_src_column` to route gameplay FG cells through `genesistan_hook_tilemap_fg_fill_tall` instead of the legacy 32-row `genesistan_hook_tilemap_fg_fill`.
- Added `staged_fg_tall_buffer` clear in `genesistan_hook_cwindow_clear` and sets `fg_tall_dirty` when cleared.

The new tall FG fill helper mirrors the Build 0170 tall BG helper but uses:

- C-window base `0x00C08000`.
- `staged_fg_tall_buffer` as the 64-row backing.
- `fg_tall_dirty` as the projection dirty flag.

### `apps/rastan-direct/src/vdp_comm.s`

- Added `vdp_project_fg_tall_if_dirty`.
- Called it during `_vblank_service` after BG projection/commit and before `vdp_commit_fg_narrow_strips` / `vdp_commit_fg_strips_if_dirty`.
- Projection uses the same row-base convention as BG:
  `(((-staged_scroll_y_fg + 8) & 0x01FF) >> 3) & 0x3F`.
- Copies 32 visible rows from `staged_fg_tall_buffer` into `staged_fg_buffer`.
- Sets `fg_row_dirty = 0xFFFFFFFF` after projection.
- Gameplay Plane A vertical scroll now commits only the residual pixel offset `& 0x0007`, matching the Build 0171 BG model.
- Added BSS symbols: `fg_tall_dirty`, `fg_tall_project_base`, `staged_fg_tall_buffer`.

### `apps/rastan-direct/src/boot/boot.s`

- Added externs for the new FG tall symbols.
- Clears `fg_tall_dirty`, `fg_tall_project_base`, and `staged_fg_tall_buffer` during boot staging clear.

### Canonical Invariants

First release invocation stopped at the expected coverage gate:

- expected coverage: `0x182318`
- observed coverage: `0x182490`
- opcode_replace count: `151` unchanged

Updated only the canonical coverage constants in:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

## Build Verification

Release result: **PASS**.

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0172.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256 for both: `c2ed780af704737ed813704a414a7609ed2e7f4629b243108c8934273da15ac9`
- Size: `1,582,224` bytes
- `cmp`: byte-identical (`0`)
- Boot guard: PASS
- Canonical gate: `GATE_PASS`
- `opcode_replace` patched-site count: `151`
- `total_genesis_bytes_covered`: `0x182490`

Important symbols:

- `vdp_project_fg_tall_if_dirty = 0x000701BE`
- `genesistan_hook_tilemap_fg_fill_tall = 0x00070A52`
- `fg_tall_dirty = 0x00FF400E`
- `fg_tall_project_base = 0x00FF4010`
- `staged_fg_buffer = 0x00FF70A6`
- `staged_fg_tall_buffer = 0x00FF80A6`
- `staged_palette_words = 0x00FFA0A6`
- `pc090oj_object_ram = 0x00FFA9B8`

## Runtime Validation

Trace directory:

`states/traces/build0172_fg64_validation_20260715_181940/`

Files:

- `fg64_trace.lua`
- `build0172_fg64_samples.csv`
- `build0172_fg64_summary.log`
- `capture_build0172_snapshots.lua`
- `build0172_0000.png` .. `build0172_0004.png`
- `build0172_contact_sheet.png`

MAME exited cleanly (`0`) for both data trace and screenshot capture.

### Data Results

By frame `571` in gameplay scene 1:

- `bg_tall_nz = 4096`
- `fg_tall_nz = 4032`
- `bg_nz = 2048`
- `fg_nz = 2016`
- `bg_base = 0x0001`
- `fg_base = 0x0001`
- `fg_tall_dirty = 0` after projection/commit
- `fg_row_dirty = 0` at steady sample after commit

At steady frames `820`, `900`, `1081`, and `1400`:

- `fg_tall_nz = 4032`
- `fg_nz = 2016`
- `fg_base` follows the same row-base class as BG (`0x0016` at frame `820`, `0x0017` at frames `900+`).
- Sampled projected FG words match their corresponding tall backing rows.

Representative samples:

| Frame | Screen col,row | FG projected | FG tall source | Tall source row | BG projected | BG tall source |
|---:|---:|---:|---:|---:|---:|---:|
| `820` | `4,15` | `0x6062` | `0x6062` | `37` | `0x4273` | `0x4273` |
| `820` | `28,18` | `0x603F` | `0x603F` | `40` | `0x426C` | `0x426C` |
| `1081` | `4,15` | `0x6065` | `0x6065` | `38` | `0x427B` | `0x427B` |
| `1081` | `16,17` | `0x603F` | `0x603F` | `40` | `0x426B` | `0x426B` |
| `1400` | `28,18` | `0x6044` | `0x6044` | `41` | `0x42D3` | `0x42D3` |

This confirms the tall FG path is live and projected. It is not dead code and not merely diagnostic scaffolding.

## Visual Validation

Screenshot contact sheet:

`states/traces/build0172_fg64_validation_20260715_181940/build0172_contact_sheet.png`

Observed from the captured frames:

- Sky remains visible and materially coherent.
- Mountains remain visible and materially improved compared with pre-Build-0171 behavior.
- Left wall remains visible.
- Foreground/floor/terrain under and around Rastan changes substantially: the lower region is now filled by visible repeated green/foreground-looking tiles in many frames instead of the same Build 0171 empty/missing presentation.
- The new foreground is not arcade-correct yet. It appears as repeated green/leaf-like tiles and still has blank/black bands in some frames.
- The Build 0171 `frame_1081` black band at `y=112..146` is not reproduced in the same way in the Build 0172 `frame_1081` capture; instead the lower half contains projected foreground/terrain patterning.
- Black/blank band behavior is not eliminated globally: examples include Build 0172 screenshot black runs at `138..223`, `2..49`, and `0..122` depending on frame.

This is a **real candidate parity step**, not a final visual fix.

## Required Answers

1. **What is the current gameplay FG source path?**
   `genesistan_hook_tilemap_plane_a -> genesistan_stage_fg_src_column`, gated by scene 1, using `FG_SRC_BASE_GEN` / `FG_SRC_STRIDE` and the real column dest from `a5@0x10A0`.

2. **Does the gameplay FG path stage only 32 rows?**
   Build 0171 did: `FG_PRODUCER_SEG_COUNT=8` and row count `4` = 32 rows.

3. **Does the current FG path discard/fail to preserve rows 32..63?**
   Build 0171 did not preserve them. Build 0172 now preserves them in `staged_fg_tall_buffer`.

4. **Does arcade PC080SN FG/page-2 data for Stage 1 use rows beyond the current 32-row FG model?**
   The Stage 1 FG_SRC source has 16 four-row segments. Build 0172 samples show nonzero tall FG rows beyond the former 32-row window, with `fg_tall_nz=4032`.

5. **Does FG use the same scroll/display-origin convention as BG?**
   Build 0172 uses the same `-raw + 8` row-base convention for gameplay FG projection, because FG and BG staged Y scroll values matched in the captured gameplay window. No contrary evidence was found.

6. **Are FG dirty flags compatible with projecting 32 rows from a tall buffer?**
   Yes. `fg_tall_dirty` gates projection, projection sets `fg_row_dirty=0xFFFFFFFF`, and steady samples show dirty flags clear after commit.

7. **Would gameplay-only tall FG affect title/story/high-score screens?**
   The new source routing is gated to scene 1 gameplay. Non-gameplay FG writers still use existing 32-row behavior. The VBlank projection is also scene-1 gated.

8. **Would Plane A VDP scroll need residual-only handling like gameplay BG after projection?**
   Yes. Build 0172 applies `& 0x0007` to gameplay FG vertical scroll after projection owns tile-row selection.

9. **Does the candidate preserve Build 0171 BG behavior unchanged?**
   The BG tall path and BG residual scroll logic were not changed. Validation samples still show BG projected words matching BG tall backing words.

10. **Is this a real candidate fix or diagnostic-only?**
   Real candidate parity fix. Visual correctness is not final, but the mechanism is production-intent and active.

## Non-Goals / Deferred

- Collision not touched.
- Input not touched.
- Player state/landing not touched.
- PC090OJ not touched.
- D00298, Exodus loop, READY/header, continue/game-over not touched.
- Real Genesis verification remains Tighe-side.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017; OPEN-001 context; OPEN-003 context for readback/visual correlation caution.
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: remaining black/blank band timing, exact arcade-correct foreground tile selection, crouch/down-held, automatic movement/input, collision byte-equivalence, real Genesis behavior, PC090OJ/READY/header, continue/game-over, D00298, Exodus loop, records `132..134`.

## KNOWN_FINDINGS Impact

Option C - KF-038 updated with the Build 0172 gameplay FG 64-row parity extension.

## STOP

STOP triggered: **NO**.
