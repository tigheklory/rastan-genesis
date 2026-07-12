# Andy — Build 0163: Sprite Prepare / Activation Gate (micro-target) — STOP (D), NO BUILD

## 1. Baseline
HEAD 9b1c22c, working candidate Build 0162 (`7bcb3179…`, counter 162, opcode_replace 137, coverage 0x1820AC).
Accepted build remains 0160. No source/spec/tool/ROM edit, no build.

## 2. Who calls vdp_prepare_sprites + gate
`vdp_prepare_sprites` is called **unconditionally** from `_vblank_service` (vdp_comm.s:167), the Genesis VINT
handler, which also does the BG/FG/palette/scroll/sprite commits and chains to the arcade VINT (`jmp 0x3A208`).
So "prepare runs" == "_vblank_service runs". There is NO per-call gate on prepare itself.

## 3. State-causality (measured, Build 0162, F535-560)
- **_vblank_service / vdp_prepare_sprites runs only ~40% of gameplay frames** (prepare_calls per frame:
  F535=1,536=0,537=0,538=0,539=1,540=0,541=0,542=1,544=1,547=1,550=1,552=1,555=1,557=1,560=1 — irregular, ~10
  of 26 frames). So the VINT handler is not invoked every gameplay VBlank. (BG/palette look stable only because
  they are committed once and VRAM/CRAM retain; sprites need per-frame SAT commit -> flicker.)
- **The represent engine froze at 6**: represented_count writes happen only F536-538 (1,3,1 = the title->gameplay
  transition), then **0 from F539 onward** while represented stays 6. So even when prepare runs (F539+), the
  resweep produces NO activate/deactivate for the churning 24 gameplay object records.
- mirror_dirty is set each frame (producers), so the resweep is not gated off; the represent freeze is in the
  sync/decode/activate path, not a single dirty flag.

## 4. Classification: **D** (more than one subsystem; no single proven gate) — STOP
Two distinct root causes, neither a single bounded gate:
(1) **VBlank/VINT scheduling** — `_vblank_service` (hence prepare + all commits) runs only ~40% of gameplay
    VBlanks. Fixing this touches the interrupt/VBlank scheduling (the arcade VINT chain `jmp 0x3A208` /
    VINT enable), out of the sprite-prepare micro-scope and NOT a sprite dirty/candidate flag.
(2) **Represent maintenance freeze** — with prepare running, the resweep does not re-represent the changing
    gameplay object records (rep_writes=0 after F538); the represented set stays at a stale 6. Whether this is a
    decode-filter (blank/clip), a candidate-timing, or an already-represented mis-key is not a single proven
    gate — it needs the deeper process_candidates/sync analysis flagged in Andy_gameplay_sat_link_management.md.
Not A (no single missing dirty flag proven), not B (prepare isn't scene-gated; it runs, just not every VBlank),
not C (no single scene-transition clear proven — the transition ops DO run F536-538). **STOP, no build.**

## 5. Exact change if built
NONE (STOP). counter stays 162, opcode_replace 137.

## 6. Validation if built
N/A.

## 7. Open/Closed + KF + Architecture
OPEN-017: micro-fix not found. Gameplay sprite failure is two-fold: (1) `_vblank_service`/`vdp_prepare_sprites`
runs only ~40% of gameplay VBlanks (VINT scheduling), and (2) the represent engine froze at 6 after the
title->gameplay transition and does not re-represent the 24 changing gameplay object records. Neither is a
single bounded gate; both need a dedicated (non-LOW-budget) analysis — the VINT/VBlank invocation path and the
process_candidates/sync represent maintenance. Not closed. KNOWN_FINDINGS: Option A (no new indexed finding).
Architecture compliance CONFIRMED: analysis only; no source/spec/tool/ROM/build; no collision/selector/FG_SRC/
palette/geometry changes; arcade is the reference.
