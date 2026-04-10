# Cody Plane A Init Clear

## 1. Summary
Added a one-time 2048-word zero write to Plane A VRAM (`0xE000`) during `init_staging_state` so Plane A starts in a deterministic transparent state.

## 2. Root cause reference (Andy report)
Reference: `docs/design/Andy_fg_regression_after_commit_removal.md`.

## 3. Exact file modified
- `apps/rastan-direct/src/main_68k.s`

## 4. Exact code added
In `init_staging_state`, immediately after `.Lfg_clear`, added:
- `move.l  #VRAM_PLANE_A_BASE, %d0`
- `bsr     vdp_set_vram_write_addr`
- `move.w  #(2048 - 1), %d7`
- `.Lplane_a_clear:`
- `move.w  #0x0000, VDP_DATA`
- `dbra    %d7, .Lplane_a_clear`

## 5. Classification
- `PERMANENT` initialization behavior

## 6. Why FG regression occurred
After `vdp_commit_fg` removal, no remaining path initialized Plane A VRAM contents. WRAM FG staging remained zeroed, but VRAM Plane A retained undefined power-on contents, which rendered as visible garbage.

## 7. Why init-time VRAM clear is the correct fix
It initializes the actual rendered Plane A VRAM region directly, once, at startup. This restores deterministic FG transparency without reintroducing any per-frame FG publish path.

## 8. Why efficiency is preserved
The write occurs once during initialization outside steady-state VBlank. No VBlank FG upload path was added or restored.

## 9. Verification expectations
- Blue/garbage FG artifacts disappear.
- Checkerboard baseline remains stable.
- Steady-state behavior remains unchanged.

## 10. Relationship to future FG strip-level support
`staged_fg_buffer` and Plane A infrastructure remain available for future arcade-driven strip-level FG updates. This change only establishes deterministic startup state for Plane A VRAM.

## Scaffolding Inventory
- No TEMPORARY/DIAGNOSTIC/BRINGUP_ONLY scaffolding was added.

## Removal / Revert Plan
- No revert planned. This is required initialization behavior for deterministic Plane A state.

## Build Artifact Path
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

## Verification Status
- Build completed successfully.
- Runtime visual verification pending user emulator check.

## Risks / Known Limitations
- This does not implement future strip-level FG publishing; it only fixes startup Plane A determinism.
