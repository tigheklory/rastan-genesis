# Andy — Round 1 Phase 2 / Phase 3 Plane-A Visual Audit

**Type:** analysis/visualization artifacts. No production change, no ROM, no build consumed. Plane A/B
runtime untouched. Grayscale diagnostic contact sheets + map reconstructions, matching the Phase-1 format.

## Phase bounds (verified from arcade map-stream 0x50EE0/0x50F6B/0x507C5)
- **Phase 2 = records 16–20** (castle/fortress). Selectors: rec16 sel0 (H), **rec17 sel1 (VERTICAL)**,
  rec18–20 sel0 (H). Enters via event-4 reseed at rec15 (tm0 15→18).
- **Phase 3 = records 21–22** (boss). **rec21 sel1 (VERTICAL, event 6)**, rec22 sel0 (H, event 7 = stage
  end). Mixed orientation → shown as traversal-order cards with per-record scroll direction, not a fake
  horizontal panorama.

## Exact physical-pattern vocabularies (hashed 32-byte decoded patterns, exact-byte dedup)
| Phase | records | exact patterns | flip-normalized | shared w/ P1 | shared w/ P2 | phase-only |
|---|---|---|---|---|---|---|
| Phase 1 | 0–15 | 1315 | 1246 | — | — | — |
| **Phase 2** | 16–20 | **282** | see json | **1** | — | **281** |
| **Phase 3** | 21–22 | **314** | see json | **0** | **55** | **259** |

**Key finding — Plane-A foreground is nearly disjoint per phase.** Phase 1 (outdoor) and Phase 2
(castle) share **only 1** pattern; Phase 3 (boss) shares **0** with Phase 1 and **55** with Phase 2. So
the *foreground* graphics change almost completely at each phase boundary (outdoor terrain → castle
interior → boss room), even though Plane **B** (sky/mountains, the 854 set) is constant across all of
Round 1.

**Capacity consequence (evidence for later compiler work, not designed here):** Phase-2 A (282) and
Phase-3 A (314) each **fit** the ~485-slot A budget entirely — so castle and boss Plane-A can each load
once per phase and stay resident. Only **Phase 1 (1315)** exceeds the budget and needs the future-aware
streaming/retention analyzed earlier. Round-1 Plane-A residency is therefore naturally **3 per-phase
vocabularies** with genuine transitions only at the two phase boundaries.

## Artifacts
- `analysis/round1_phase2_plane_a/andy_contact_sheet/index.html` (+ tiles/, metadata.json)
- `analysis/round1_phase2_plane_a/andy_layout/index.html` (record_16..20.png, 512×512 each)
- `analysis/round1_phase3_plane_a/andy_contact_sheet/index.html` (+ tiles/, metadata.json)
- `analysis/round1_phase3_plane_a/andy_layout/index.html` (record_21..22.png)
- `analysis/round1_plane_a_visualization/index.html` (nav to all three phases)
- `analysis/round1_phase2_plane_a/transitions.json` (cross-phase reuse numbers)

## Fidelity (validated mechanically)
Phase 2: 282 patterns = 282 PNGs (all 8×8, 0 pixel mismatches), 5 record maps (all 512×512).
Phase 3: 314 patterns = 314 PNGs (all 8×8, 0 pixel mismatches), 2 record maps (all 512×512).
No offscreen pruning: full legal 64×64 tile map reconstructed per record. Sky/transparent cells use the
non-zero transparent tile 0x20 (renders black), distinct from true-empty — reported as visual, not
"blank tile code".

---

## Selector-1 World Orientation and Phase-3 Semantic Correction (2026-08-23)

**Phase-3 semantic correction:** record 21 is **final fortress / vertical fortress continuation** (still
fortress gameplay), record 22 is the **boss room**. Record membership (21–22) unchanged; only the human
label was too broad ("boss phase"). Breakdown proves it: rec21 = 116 exact patterns, **55 shared with
the Phase-2 castle** (fortress continuation); rec22 = 219 exact, **198 boss-only** (the distinct boss
room). shared 21↔22 = 21.

**Vertical-record world orientation — proven, not eyeballed.** The arcade selector-1/2 Plane-A publisher
(`genesistan_hook_tilemap_plane_a_selector12_native`) computes a **logical ROW** = `group*4 +
(strip_index & 3)` (`0(%sp)`), driven by **`staged_scroll_y_fg`** (the Y scroll), with the within-metatile
row bits **inverted** (`not.w %d1`). For selector-0 (horizontal) the same group/strip cascade drives the
**column** (X) via the X scroll. Therefore:
- Source→world axis mapping is **swapped** between horizontal and vertical records: for selector-1 the
  **group axis is world-Y**, not world-X.
- **World transform for selector-1 records = TRANSPOSE** (swap source col↔row), plus the within-metatile
  vertical row inversion.
- My earlier Phase-2/Phase-3 maps rendered records 17 and 21 with the horizontal convention
  (`col=group*4+colidx` → X), so those two vertical records were shown transposed (shaft running
  sideways). **Corrected.**

**Records affected:** 17 (Phase-2 fortress shaft) and 21 (Phase-3 fortress continuation) — both
selector-1. Horizontal records (16, 18, 19, 20, 22) are correct as-is.

**Artifacts:** each vertical record now has `record_17_raw.png`/`record_17_world.png` and
`record_21_raw.png`/`record_21_world.png` (raw = exact source grid, preserved for audit; world =
transposed). The layout HTMLs default to the WORLD view for vertical records with a RAW/WORLD toggle and
the corrected fortress/boss labels. Contact-sheet bitmaps and exact pattern counts are unchanged
(8×8 patterns are orientation-independent).
