# Andy — PC080SN Genesis-Native Gameplay Streaming Design

> ## ⚠️ ARCADE-DERIVED CORRECTION (2026-07-25) — authority reset
> The occupancy/blank/density facts below §"Executive result"/§Phase-1 were derived from **Genesis staged buffers and are INVALID.** They are superseded by the arcade-sourced findings in this box (Ghidra + MAME arcade `rastan` driver, authority order arcade-first). Build 0235 is demoted to a final pixel-parity witness only.
>
> ### INVALIDATED (were Genesis-derived)
> - ~~"Plane A transparent blank = 0x2000"~~ — WRONG. `0x2000` is a **Genesis-VDP-converted** word (post tile-LUT). It is not an arcade value.
> - ~~"Plane B dense / Plane A sparse @ ~50%"~~, ~~"most-common = blank"~~ — measured off the translation layer; retracted.
>
> ### CONFIRMED from the arcade (Ghidra + MAME name-RAM reads)
> - **Two active PC080SN tilemap layers** (each a 64×64 ring, 0x4000 bytes): **Layer @ arcade 0xC00000** (dense, tiles ≈0x0665–0x06B8, no dominant base) and **Layer @ arcade 0xC08000** (base tile **0x0020** ≈59% + varied 0x00CD/0x00CC/0x00D8…). `0xC04000` layer = all `0x0000` (unused).
> - **Arcade name-RAM cell = 2 words:** **word0 (even) = `0x0003` constant attribute** (palette/priority), **word1 (odd) = the tile code.** (Measured: even words 0x0003 ×4096; odd words are the real tiles.) So the "blank" is a **tile value in word1** (e.g. `0x0020` for the 0xC08000 layer), never 0x0003 and never the Genesis 0x2000.
> - **Two independent scroll layers (parallax):** `a5@0x10EE→0xC20000(X)`, `a5@0x10B0→0xC20002(Y)`; `a5@0x10EC→0xC40000(X)`, `a5@0x10AE→0xC40002(Y)` (0x055AB4). Measured X≈0x149 vs 0x1B3, Y≈0x149 vs 0x166 — different rates ⇒ genuine parallax; the two layers scroll independently.
> - **Producers (Ghidra, address-faithful):** publisher `0x055948`; BG-path column `0x055968`→cell `0x0559B2` (writes word1 tile from streaming source `*(a1)`, word0 from descriptor, **collision → 0x10DE00 + (a0−0xC08000)/2**); FG-path column `0x055990`→cell `0x055A14`; descriptor rebuild `0x055904`; scroll `0x055AB4`; H trigger `0x055822`, V trigger `0x05572E→0x055788`.
> - **Collision is tied to the 0xC08000 layer** (index `(a0−0xC08000)/2`) — so the **0xC08000 layer is the playfield/foreground** whose surfaces align with collision; the **0xC00000 layer is the dense background scenery**. (Assignment inferred from the collision base + density; the a5@0x10A8 selector→layer capture is still pending as a cross-check.)
> - Each arcade layer is a **full 64×64 ring** (streams new columns/rows, wraps), NOT a 32-row band (my earlier "band" reading was an artifact). The Genesis 64×**32** plane therefore genuinely needs a **resident 32-row window** of the arcade's 64 rows — the 0238 blanket `row&31` fold is wrong because it aliases; the sliding-window contract (Phase 3 of this doc) is the correct structure but must key on arcade rows.
>
> ### CHANGED
> - Blank handling: the Genesis cache must clear reused cells to the **Genesis conversion of the arcade layer's base tile** (`tile_vram_lut[0x0020]` for the playfield layer), not a hardcoded 0x2000. The word0=0x0003 attribute collapses into the Genesis VDP word via the attr LUT.
> - Layer roles: **Plane B (BG, 0xC000) ← arcade 0xC00000 dense scenery; Plane A (FG, 0xE000) ← arcade 0xC08000 playfield.** (Density is opposite to what the Genesis-buffer reading implied for one of them — re-derive occupancy from the arcade layers, using `word1 != base_tile`, never `word != 0`.)
>
> ### REMAINING UNKNOWNS (need proof before implementation)
> 1. Definitive a5@0x10A8 selector→layer(0xC00000 vs 0xC08000) mapping and the 0xC00000 layer's base/blank tile (MAME selector-tagged write capture — the earlier attempts had the capture window/selector-read miss).
> 2. Arcade scene-init cadence and the exact 64→32 resident-window origin per layer (derive from arcade scroll + name-RAM occupancy over vertical movement / rope).
> 3. Arcade tile-word→Genesis-VDP-word conversion table for word1 tiles + the 0x0003 attribute mapping (from the existing `genesistan_pc080sn_tile_vram_lut`/`_attr_lut` build data, validated against arcade values).
>
> **The Phase-1/Executive figures below are retained only as a record of the discredited Genesis-buffer method; do not use them.**


**Date:** 2026-07-25 · **Design-only** (no source/spec/tool/ROM/build changes). Baseline: accepted Build 0235 source (`9aff0b11…`). Rejected 0236 (64×64) / 0238 (row-fold) preserved. Target: replace the gameplay PC080SN tall-buffer projection with native dual **64×32** Plane B (BG) / Plane A (FG) resident caches, VRAM layout unchanged (planesize 0x01, Plane B 0xC000, Plane A 0xE000, SAT 0xF800, HSCROLL 0xFC00).

## Executive result
- **Plane A transparent blank word = `0x2000`** (measured: 1020/2048 ≈ 50% of the FG plane). 0238's "FG nz=2016" was NOT correctness proof — ~1020 of those are the nonzero blank `0x2000`; real meaningful FG ≈ **~1028 cells** (word ≠ 0x2000).
- **Plane B is dense** — no dominant blank (most-common word only 38/2048; 522 distinct tiles). Every resident cell is an intentional background tile.
- **The dense BG is a SCENE-INIT full population, not per-frame streaming.** Measured: BG tall buffer written ~49k× only at scene entry (F2700–2900), then **0 writes** during steady horizontal gameplay. Horizontal BG updates come from the plane_a column streamer; the projection only re-windows on vertical base change.
- **GO/STOP: CONDITIONAL GO** — the whole architecture is recovered EXCEPT the exact arcade caller of the scene-init dense-BG fill (`genesistan_hook_tilemap_bg_fill_tall` has only an item-page source-caller, yet fills densely at gameplay scene entry). One more trace (below) pins it; everything else is implementation-ready.

---

## Phase 1 — Visual oracle (Build 0235, read-only)
Matched-frame captures (staged buffers, scroll, projection base, scene state). Key occupancy (F3000, gameplay, using blank-aware tests):
| Plane | Buffer | Most-common word | Meaningful cells | Semantics |
|---|---|---|---|---|
| **B (BG)** | staged_bg_buffer | 0x422B ×38 (no blank) | ~2048 (dense) | 522 distinct tiles — dense scenery |
| **A (FG)** | staged_fg_buffer | **0x2000 ×1020 (= transparent blank)** | ~1028 (word≠0x2000) | 45 distinct meaningful tiles — sparse playfield |

BG tall-write cadence: **scene-init burst only** (F2700=1535, F2800=27136, F2900=20480, F3000+=0). ⇒ presentation-change classification for steady horizontal travel is **entering-column** (plane_a), not full projection.

**Occupancy rule for all future verification:** count Plane B meaningful = initialized cells; Plane A meaningful = `word != 0x2000`. Never use `word != 0`.

---

## Phase 2 — Real arcade producers
| Semantic event | Genesis boundary | Arcade boundary | Status |
|---|---|---|---|
| Dense BG scene-init | `genesistan_hook_tilemap_bg_fill_tall` (fills staged_bg_tall_buffer, 64 rows) at scene entry | **UNPROVEN caller** (source-caller is only item-page 0x055C5E; gameplay scene-init caller not identified) | **MISSING PROOF** |
| BG entering-column (horizontal) | `genesistan_hook_tilemap_plane_a` → staged_bg_buffer (row&31, ~212 cells/frame = the entering column) | arcade BG column producer 0x055968 / cell 0x0559B2 | recovered |
| FG scene-init + streaming | `genesistan_stage_fg_src_column` → `fg_fill_tall` (64-row) today; **`fg_fill` (32-row, row=(cell>>6)&0x1F, staged direct) reproduces identical content** (0238 proof: 2016/45 == 0235) | arcade FG column producer 0x055990 / cell 0x055A14 | **recovered + proven** |
| Publisher (col or row, orientation) | (translated via the above) | **0x055948** (BG if a5@0x10A8==0 else FG; adv a5@0x10CA; post 0x558A2 rebuild every 4) | recovered |
| Entering-row trigger (vertical) | projection re-window today | **0x05572E→0x055788** (vscroll bit-3 tile cross) | recovered |
| Entering-column trigger (horizontal) | plane_a | **0x055822** | recovered |
| Descriptor rebuild | `genesistan_hook_pc080sn_descriptor_rebuild` | **0x055904** (16-entry table 0x10D1C0) | recovered, RETAIN |
| Scroll commit | staged_scroll_* | **0x055AB4** (4 regs → C2/C40000/0002) | recovered, RETAIN |
| Collision (BG cell) | `genesistan_stage_bg_collision_column` | **0x0559B2** side-channel → 0x10DE00+(dest−0xC08000)/2 | recovered, RETAIN |

`genesistan_hook_pc080sn_bg_scroll_fill`/`_fg_scroll_fill` are **no-ops** (movem/rts) — not producers.

**The single missing proof:** which routine calls `genesistan_hook_tilemap_bg_fill_tall` at gameplay scene entry (the ~49k-write dense fill). Exact trace to resolve: on 0235, tap writes to staged_bg_tall_buffer (0xFF60EE) during F2700–2900, capture the **caller return address** via a reliable method (PC breakpoint / execution log, NOT an in-tap SP read — that errors in this MAME), map through address_map.json to the arcade scene-init caller. Likely the scene-load / item-page-to-gameplay transition path (`scene_load.s` / arcade 0x055C5E family), reused for Stage 1's initial 64-row BG.

---

## Phase 3 — Resident-cache contract (32-row window, NOT fold)
Arcade BG/FG source is a 64-row ring; the Genesis resident cache is 32 rows. **Do not fold all 64 rows with `row&31` (0238's error — aliases two source rows onto one physical row simultaneously).** Instead a sliding 32-row resident window:

```
arcade_ring_height = 64      (BG/FG source rows)
cache_rows         = 32      (Genesis plane height)
cache_top_row      = derived per plane from that plane's vertical scroll
                     (BG: staged_scroll_y_bg; FG: staged_scroll_y_fg)

relative_row = (authoritative_row - cache_top_row) mod 64
RESIDENT  ⇔  relative_row < (cache_rows + guard)     [guard rows derived below]
physical_plane_row = authoritative_row mod 32        (only meaningful when resident)
physical_plane_col = authoritative_col mod 64
```

- **Guard rows:** the accepted origin is `(-scroll_y + 8)`; the +8 (one tile) is the top-margin bias → **1 guard row** at top; derive the exact resident span from the accepted output (28 visible tiles + top/bottom guard). A source row is published only while resident; when the camera moves and a row leaves the window, its physical row is reused by the entering row (32 apart) — no simultaneous aliasing because only ≤32 distinct source rows are ever resident.
- **Independent per plane:** Plane B and Plane A derive `cache_top_row` from their own scroll (parallax may differ) and have different density.

### Scroll equations
```
HSCROLL_bg = staged_scroll_x_bg - 16   (unchanged from 0235; 64-col wrap = 512px, native)
HSCROLL_fg = staged_scroll_x_fg - 16
VSRAM_bg   = (-staged_scroll_y_bg + 8) & 0xFF     (32-row = 256px ring)
VSRAM_fg   = (-staged_scroll_y_fg + 8) & 0xFF
```
`&0xFF` (256px) is the 32-row window wrap (NOT 0235 `&7`, NOT 0236 `&0x1FF`). Sign/bias inherited from the proven 0235 origin; confirm the exact guard offset against the oracle when implementing.

---

## Phase 4 — Genesis-native publication helpers (contracts)
All are `movem`-guarded, RTS, arcade-called (translate the arcade's already-decided cells). Address space noted.

1. **`initialize_bg_cache`** — at the arcade scene-init boundary (the MISSING-PROOF caller). In: arcade BG source map + a5 camera. Out: all 32 resident Plane B rows × 64 cols in staged_bg_buffer (dense), full `bg_row_dirty`. Supersedes: bg_fill_tall + first projection.
2. **`initialize_playfield_cache`** — same boundary. Out: **clear all 32×64 to `0x2000`**, then write only meaningful FG cells (word≠0x2000). Full `fg_row_dirty`. Supersedes: fg_fill_tall + first FG projection.
3. **`publish_bg_entering_column`** — arcade 0x055822/0x055968 boundary (translated in `genesistan_hook_tilemap_plane_a`). Out: all 32 rows of the entering physical column (`col = auth_col & 63`), set `bg_row_dirty` for those rows / a `bg_col_dirty` bit.
4. **`publish_playfield_entering_column`** — arcade FG column (translated in `genesistan_stage_fg_src_column`→`fg_fill`). Out: **clear the reused 32-cell column to 0x2000**, then write only meaningful FG cells for it. Never leave stale terrain.
5. **`publish_bg_entering_row`** — arcade 0x05572E→0x055948 (FG-selector) / BG vertical. Out: all 64 cols of the entering physical row (`row = auth_row & 31`), dirty that row.
6. **`publish_playfield_entering_row`** — clear reused 64-cell row to 0x2000, then meaningful FG spans.
7. **`publish_changed_cell_or_span`** — resident cells only (bounded); outside-cache changes stay in arcade state until they enter.
8. **`commit_scroll`** — arcade 0x055AB4 (existing staging) → HSCROLL/VSRAM per Phase 3.

Registers preserved d0-d7/a0-a6; collision (helper 0x0559B2 side-channel) unchanged; tile/attr conversion via existing `genesistan_pc080sn_tile_vram_lut`/`_attr_lut`.

---

## Phase 5 — Active-display staging + VBlank commit
Two final-format 64×32 shadows (staged_bg_buffer, staged_fg_buffer — **already the right size**, no growth). Per plane: 32-bit `*_row_dirty`; add a 64-bit `*_col_dirty` (2 longs) for entering-column publication. The semantic helper marks row vs column vs cell — no raw-write transcript.

- **Dirty row** = 64 contiguous words → one 64-word DMA, autoinc 2 (existing `vdp_commit_bg/fg_strips_if_dirty`).
- **Dirty column** = 32 separated words (stride 64 words). **Measure**: (a) 32-word PIO loop autoinc 128, vs (b) stage a contiguous 32-word packet during active display + one DMA autoinc 128. Choose the cheaper; (b) likely wins (DMA ~ (b) same as row DMA, PIO ~2× slower during active-display contention). Restore autoinc 2 after.
- **Plane A clears** are part of the same bounded column/row unit (clear-to-0x2000 then write meaningful), never separate full-plane clears.
- **Commit order:** tiles → BG row/col updates → FG clear+meaningful updates → sparse cells → sprites → scroll → palette; restore autoinc. No command processor.

---

## Phase 6 — Collision / playfield alignment
Collision stays arcade-owned WRAM at **0x10DE00**, produced by the 0x0559B2 side-channel: `0x10DE00 + (dest − 0xC08000)/2`, same wrapped cell index as the BG visual. Plane A's visible floors/walls/platforms are the **same authoritative world cell** as the collision entry (both from the arcade dest), so alignment is automatic IF the Genesis visual mapping preserves `(dest−0xC08000)` tile indexing. **Required correction:** finish the OPEN-0159 rebase (0x10DE00→0x00FF1E00) and the KF-067 row-origin so collision and the Plane A visual share one origin. Do NOT derive collision from VRAM; not every Plane A tile is collidable (non-colliding foreground artwork exists).

---

## Phase 7 — Retirement + performance
**Retain:** arcade map/camera/scroll/progression, descriptor rebuild (0x055904), scroll commit (0x055AB4), collision production, tile/attr LUT conversion, frontend/title/HUD/item-page paths (item-page bg_fill_tall stays for the item screen).
**Replace/bypass in gameplay:** staged_bg_tall_buffer, staged_fg_tall_buffer, `vdp_project_bg/fg_tall_if_dirty`, the 32×64 projection copies, the gameplay full-map tall fills that imitate PC080SN RAM. **Only after** the real scene-init + streaming producers are retargeted (0238's lesson: never disable a projector before replacing its real producer).
**Do NOT touch:** PC090OJ path, SAT/HSCROLL location, sprite-tile cache, palette routing, HUD/score, numbered artifacts, planesize.

**Cycle estimates (68000 @ 7.67 MHz, ~127,800 cyc/frame):**
| Event | Est. cost | vs 0235 |
|---|---|---|
| Scene init (dense BG 32×64 + FG clear+sparse) | one-time ~50–90k (at transition/blackout) | replaces the scene-load fill; not per-frame |
| Sub-tile move | scroll commit only ~200 cyc | ≈ same |
| BG entering column (32 words) | ~1,500–3,000 cyc (DMA) | replaces nothing extra |
| FG entering column (clear 32 + ~sparse) | ~2,000–3,500 cyc | new (was projection) |
| BG/FG entering row (64 words DMA) | ~1,800 cyc each | vs projection ~45,000/plane |
| Diagonal | row + column (sum of above) | vs ~90,000 both projections |
| Worst VBlank (both entering row + FG clear) | ~8–10k cyc bounded | **vs ~90,000** (2× projection) |

Net: eliminates the ~45k-cyc/plane projection copy; per-frame cost drops to a few bounded DMAs.

---

## STOP / GO
**CONDITIONAL GO.** All contracts (layer semantics, blank words, resident-cache window, scroll, helpers, staging/VBlank, collision, retirement, cycles) are implementation-ready EXCEPT **Proof #1: the exact arcade caller of the scene-init dense-BG fill.** Single trace to unblock (Phase 2 above). With that resolved, implementation can proceed in sequential candidate builds via the normal Makefile.

Explicitly avoided: 64×64 planes, SAT/HSCROLL move, sprite-cache shrink, `row&31` blanket fold, projector-disable-before-producer, nonzero-as-content, feature flag, display-off, Genesis-owned map logic.

## Compliance
No production source, spec, tool, ROM, build counter, or numbered artifact changed. Arcade retains full ownership. Design only.
