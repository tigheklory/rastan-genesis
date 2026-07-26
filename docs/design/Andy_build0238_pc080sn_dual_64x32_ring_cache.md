# Andy — PC080SN Dual 64×32 Native Ring Cache (Build 0238 attempt → STOP for BG)

**Date:** 2026-07-25 · Baseline accepted Build 0235 (`9aff0b11…`). Rejected Build 0236 (64×64) preserved (`f471be01…`). This task's candidate landed as **Build 0238** (see numbering note). **Outcome: FG ring proven correct; BG ring FAILED (severe under-population); source reverted to exact 0235; STOP for the BG mapping.**

## Numbering note
An accidental `make -p` during Phase-1 verification built `build_0237.bin` (byte-identical to 0235) and bumped the counter to 237. Per owner decision, that duplicate is **preserved** and the implementation candidate was produced as **Build 0238** (no delete, no counter decrement). Artifacts: 0235=9aff0b11, 0236=f471be01, 0237=9aff0b11(dup), 0238=54757864.

## Phase 1 — Build 0235 baseline restoration: PASS
Reverted the 0236-only edits by `git checkout bad1499` (commit "Build Pre Build 236" = the 0235 source) of tilemap_hooks.s, vdp_comm.s, and the paired coverage `.py`. Verified by an unnumbered prepatch+patch build: **SHA256 = 9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5 (EXACT match to accepted 0235)**. `git diff bad1499` for the source/spec/gate is empty → provably the exact 0235 baseline.

## Corrected model (dual 64×32, plane row = world row & 31)
Keep VRAM layout unchanged (planesize reg 0x01 = 64×32; Plane B BG 0xC000, Plane A FG 0xE000; SAT 0xF800; HSCROLL 0xFC00). Plane column = world col & 63; **plane row = world row & 31**; VSRAM windows the 32-row (256 px) ring mod 256.

## Implemented cell mapping
- **FG (WORKS):** `genesistan_stage_fg_src_column` routed from `genesistan_hook_tilemap_fg_fill_tall` → `genesistan_hook_tilemap_fg_fill` (non-tall). With the same dest a0, `fg_fill` computes `cell=(dest−0xC08000)/4`, `col=cell&0x3F`, **`row=(cell>>6)&0x1F`** → writes `staged_fg_buffer[row&31][col]` and sets `fg_row_dirty`. Verified: gameplay FG population identical to the 0235 baseline (nz=2016, distinct=45 both). Genesis addr `genesistan_stage_fg_src_column` (arcade FG producer 0x055A14 family); arcade base 0xC08000.
- **BG (FAILED):** disabling the BG projection and relying on `genesistan_hook_tilemap_plane_a`'s direct `staged_bg_buffer` writes left BG at **nz=212 vs the 0235 baseline nz=2048** (severe under-population = black holes). Root cause below.

## Scroll equation (derived, applied)
Gameplay VSRAM = `(−staged_scroll_y_bg + 8) & 0x00FF` (BG and FG) — the proven 0235 origin `(−scroll_y+8)` with the wrap **widened from the 0235 sub-tile `&7` to the 32-row 256 px `&0xFF`** (not the 0236 `&0x1FF`, not 0235's `&7`). HSCROLL unchanged (arcade-owned, 64-col wrap). This was applied but the BG failure was a content-population issue, not a scroll issue.

## Publication structure
FG: `fg_fill` sets per-row `fg_row_dirty`; VBlank scene-gated to `vdp_commit_fg_strips_if_dirty` (DMA changed rows to Plane A) for gameplay, `vdp_commit_fg_narrow_strips` for frontend. Bounded (≤32 dirty rows). BG intended analogous but see failure.

## ROOT CAUSE of the BG failure (evidence)
`genesistan_hook_tilemap_plane_a` is **not** the BG full-content source. Matched MAME trace of accepted 0235: the BG **tall buffer is written 47,104×/run in gameplay** (a tilemap-region routine), and the BG **projection** (`vdp_project_bg_tall_if_dirty`) windows it to fill `staged_bg_buffer` fully (2048 cells, 522 distinct tiles). `plane_a` contributes only ~212 sparse cells (likely streaming/collision-adjacent). So the BG's real gameplay path is **(gameplay tall-buffer filler) → projection → staged**, unlike FG whose `fg_fill_tall` content is exactly reproducible by `fg_fill`. Disabling the BG projection removed the full-fill.

**To finish BG (next session):** identify the gameplay BG tall-buffer filler (the ~47k-write routine; source-caller of `genesistan_hook_tilemap_bg_fill_tall` is only the item-page, so the gameplay filler is a different path — likely `genesistan_hook_pc080sn_bg_scroll_fill` or a plane_a preamble) and route it to the non-tall `genesistan_hook_tilemap_bg_fill` (which already folds `row=(cell>>6)&0x1F` into `staged_bg_buffer`), exactly mirroring the proven FG conversion. Only then disable the BG projection.

## Verification (Build 0238, headless)
- Boot (scene 0 title) → Stage 1 (scene 1); no crash through F4800.
- **Both tall projectors: 0 gameplay calls** (bg & fg) ✓ — but BG rendered from the now-removed fill → **BG nz=212 vs 2048 = FAIL**.
- FG nz=2016/distinct=45 = identical to 0235 ✓. HUD score+1UP = 0235 baseline ✓. planesize 0x01, SAT/HSCROLL unchanged ✓.

## Outcome
STOP for the BG mapping (task condition: "producer-to-64×32 mapping cannot be proven without guessing"). Build 0238 produced but **fails** the "no large black holes" criterion for BG. FG conversion validated and documented for reuse. **Source reverted to the exact 0235 baseline** (git-identical to bad1499). All numbered artifacts preserved; counter 238.

## Compliance
No SAT/HSCROLL move, no 64×64, no sprite-cache shrink, no feature flag, no display-off, no PC090OJ change. Arcade retained ownership. Source ends at clean 0235.
