# Andy — Build 0155: Stage 1 FG Plane Restored at the Live Producer Boundary

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `98240a4` (Build 0154 accepted, `5346934`). Build 0154 ROM `69bd306e…`,
counter 154. **Evidence dir:** `states/traces/build_0155_stage1_fg_plane/`.

## Outcome
**Implemented.** The Stage 1 FG (PC080SN Plane A) is now populated through the existing global LUT, gameplay
manifest, `genesistan_hook_tilemap_fg_fill`, `staged_fg_buffer`, `fg_row_dirty`, and the existing FG VBlank
commit. `staged_fg` went **76 → 2020 / 2048** cells; the visible rows 0-27 match the arcade FG plane **98%**;
the stale opaque Plane A is gone; Plane B, palette, and the frontend are unchanged.

## Live boundary found (the fix vs the prior wrong hook)
The prior attempt hooked `genesistan_hook_tilemap_plane_a` (`0x070248`, reimplementation of arcade FG producer
`0x055968`), which is **dynamically bypassed** on Genesis (KF-040 class). Runtime tracing of the Stage 1 setup
loop (`0x50634`, `gen_disp.txt`) proved the **live boundary is `genesistan_hook_tilemap_fg` (`0x0703EA`)**:
- The setup loop runs 64 iterations (one per FG column), each calling the dispatcher `0x055B48`. Because
  `a5@0x10A8 = 0x0080 (≠ 0)`, the dispatcher routes to `0x0703EA` (not `0x070248`).
- `0x0703EA`'s native input `a5@0x10A4` = `0xC0C000+` (out of the FG C-window) so it bails, but the **real FG
  column dest is `a5@0x10A0` = `0xC08000 + dcol*4` (mod plane)**.

## Implementation
A preamble in `genesistan_hook_tilemap_fg` (gated on `genesistan_current_scene_id == 1`) computes each FG cell
**directly from ROM** using the proven deterministic model, driven by the real column dest `a5@0x10A0`:
```
dcol   = (a5@0x10A0 & 0x3FFC) >> 2 ;  group = dcol>>2 ;  colidx = dcol & 3
SRC    = 0x00016B1C + seg*0x22C0 + group*4        ; 0x1691C + copy delta 0x200
block  = ROM_word(SRC+2) + 0x200                  ; relocate arcade block ptr
code   = ROM_word(block + colidx*2 + row*8)       ; plane row = seg*4 + row
attr   = 0x0003 ;  cell -> genesistan_hook_tilemap_fg_fill(A0=cell, D0=(attr<<16)|code, D1=1)
```
Stages the **visible top 32 rows (seg 0..7)** — `fg_fill`'s 32-row buffer wraps, so segments 8..15 would
overwrite the visible top (that off-by-half was the first cut, corrected to 8 segments). Non-gameplay scenes
fall through to the unchanged FG descriptor path. **Register/CCR:** `fg_fill` preserves `d0-d7/a0-a6`; the
preamble uses `d0-d6/a0/a2/a4` (all restored by `fg_fill`); the `0x10DE00` shadow is arcade read-back only (not
display) and is not needed for the Genesis staging path.

## Generator (structural, re-applied)
`precompute_pc080sn_tile_lut.py:collect_runtime_gameplay_fg_tiles` walks the same chain (no hardcoded codes) and
derives the **49-code** FG family; merged into the gameplay scene set. Global ROM-resident LUT + per-scene
manifests unchanged; **48/49 mapped** (only `0x020` = transparent, blank pattern, assigned slot 0 → renders
transparent). Gameplay manifest 914 → 962, peak scene **1067/1164**, byte-identical across two runs.

## Validation (Genesis MAME, state 2/3/0)
- **FG staging:** `staged_fg` 76 → **2020/2048**; visible rows 0-27 match arcade FG cells **98%** (1768/1792;
  the ~2% are single edge cells; rows 28-31 are below the Y-scroll-0 window). Determinism: two clean boots →
  byte-identical staged FG.
- **Transparent regions:** `0x020` → LUT slot 0 (blank pattern) → transparent (BG shows through).
- **Plane B unchanged:** `staged_bg` 2048/277-distinct, identical to Build 0154.
- **Frontend intact:** title (RASTAN/HIGH SCORE 273100), story + BEST 5 (273100…112000 / 3/3/3/2/2 / COB…);
  no stale Plane A content remains.
- **Gate/map:** GATE_PASS, boot guard PASS, 30-s trace clean; address-map `gaps=[]`, `overlaps=[]`, covered
  `0x182044`, `opcode_replace=134`. Canonical coverage paired-updated `0x181EE8 → 0x182044` (+0x15C) in both
  gate scripts.

## Build 0155
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0155.bin`
- **SHA256:** `f226278f6306d68e5eec84ffcc882f87eff0ed94e828bee28b98a4f23d2d3866`
- **Size:** 1,581,124 B. Counter 155. Builds 0142–0154 not overwritten. Reproducible (rebuild → identical SHA).

## First downstream boundary
The FG plane is faithful, but the overall Stage 1 image is not yet arcade-perfect: the sky area renders the
BG (rocky) rather than the arcade's blue cloud sky (a BG-content/palette question), and a horizontal seam +
static BG X-scroll remain (scroll was deferred per the task). These are separate boundaries; gameplay PC090OJ
sprites remain absent (not investigated).

## Architecture-compliance statement
CONFIRMED. Reused the existing global ROM-resident LUT, per-scene manifests, `fg_fill` conversion/staging,
`fg_row_dirty`, and the existing FG VBlank commit. No manual FG code list (extraction is structural), no
hand-edited LUT, no hardcoded Plane A cells, no arcade plane-dump copy, no `state==2/3/0` test (gated on the
producer-derived scene id), no forced scroll, no scene-specific/RAM LUT, no second renderer/commit path, no
sprite fix. Build 0154 BG model / Build 0152 `0xC08C62` routing untouched; the dead raw writer `0x055BB2` not
patched.

## Open issue impact
- **OPEN-017:** advanced — the Stage 1 FG plane is restored at the proven live boundary (`0x0703EA`), matching
  arcade cells 98% with transparency correct and no frontend regression. Remaining: BG sky palette/content,
  horizontal seam, BG X-scroll, gameplay sprites. Not closed; no duplicate.
