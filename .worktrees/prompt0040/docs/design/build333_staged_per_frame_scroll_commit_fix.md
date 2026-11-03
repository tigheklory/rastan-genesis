# Build 333 Staged Per-Frame Scroll Commit Fix

## 1. Executive Summary
Build 333 removes the hardcoded zero scroll commit behavior from `genesistan_scroll_commit_vdp` and commits the already-staged per-frame scroll values for both planes and both axes. The active frame order remains unchanged.

## 2. Exact Function Modified
- File: `apps/rastan/src/main.c`
- Function: `genesistan_scroll_commit_vdp`

## 3. Previous Hardcoded-Zero Behavior
Before this change, `genesistan_scroll_commit_vdp` wrote:
- HScroll table entries at VRAM `0xF000`: `0`, `0`
- VSRAM entries at offset `0`: `0`, `0`

This occurred every active arcade VBlank regardless of staged runtime scroll values.

## 4. New Staged-Scroll Commit Behavior
`genesistan_scroll_commit_vdp` now commits:
- HScroll:
  - BG_A from `staged_scroll_x_fg`
  - BG_B from `staged_scroll_x_bg`
- VScroll:
  - BG_A from `staged_scroll_y_fg`
  - BG_B from `staged_scroll_y_bg`

The same VDP write destinations and phase are used:
- VRAM HScroll table at `0xF000`
- VSRAM at offset `0`

## 5. What Was Intentionally Left Unchanged
- `genesistan_scroll_from_workram_vdp` unchanged.
- Tilemap generation hooks unchanged.
- `genesistan_bulk_tilemap_commit` unchanged.
- Palette logic unchanged.
- Input logic unchanged.
- VBlank ownership unchanged.
- Sprite suppression unchanged.
- Debug overlay unchanged.
- Frame order unchanged (`plane -> palette -> scroll`).

## 6. Build Verification
- Build command: `source tools/setup_env.sh && make -C apps/rastan release`
- Build result: success
- ROM artifact: `dist/Rastan_333.bin`
- Errors: none
- Warnings: no new warnings (same 5 pre-existing warnings)

## 7. Expected Runtime Result
- Rolling display should materially change.
- Visible frame presentation should now track staged per-frame scroll state.
- Existing Plane A debug overlay remains available for verification.

## 8. Final Verdict
Build 333 applies the single scoped presentation-state fix by replacing hardcoded zero scroll commits with staged per-frame scroll commits in the active arcade VBlank path.
