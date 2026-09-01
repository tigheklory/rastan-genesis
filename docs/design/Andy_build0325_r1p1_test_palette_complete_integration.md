# Andy — Build 0325: Complete R1/P1 Test-Palette Architecture

**Type:** Implementation / Verification. ROM produced. Classification: **EXTENDING**. Baseline Build 0324.

## 1. Phase 0
Priors/hazards honored: **KF-043** (Line 3 was sprite bank 0x33 — now vacated to Layer-A; sprites moved to L0/L1); **KF-0174** (FG carrier overwritten by frontend → re-assert each gameplay VBlank). Deferred: vertical-scroll (untouched). Issues touched: none reopened. Contradiction status: none.

## 2. Test authority
Frozen `build/rastan-direct/build0314/Test.snapshot.json` SHA `deb696452d7456b3…` is the sole palette authority. Line values come from `target_palette_lines`; sprite maps from `usage_palette_mappings`. No manual second palette definition; the assembly `test_sprite_line0/1` + `editor_layera_palette` are byte-equal to the profile (and the sprite reindex records the profile SHA).

## 3. Semantic inventory (from Andy_r1p1_test_sprite_semantic_resolution.md)
8 distinct production mappings / 7 source banks, all RESOLVED, key `(code,bank)`, 0 cross-bank collisions, bat 0x3E disjoint. 124 sprite codes.

## 4. Offline sprite reindex (`tools/graphics_editor/gen_reindexed_pc090oj.py`)
Reads frozen Test maps + corpus code sets; reindexes each of the 124 resolved sprite codes' pixels into its authored line's entries (index 0 stays transparent); emits `build/regions/pc090oj_editor.bin` + `pc090oj_editor_manifest.json` (per code: bank, usage, line, index_map, pattern SHA). Bat variants preserved distinct (code 616 = small_bat map; 1014–1017 = large_bat map). No runtime transform, no ΔE, no dominant collapse.

## 5. Runtime O(1) lookup
Because there are **0 cross-bank code collisions** and the bat variants use disjoint codes, the reindex is **code-indexed**: `pc090oj_editor.bin` is the code→pattern region the existing native SAT path already indexes by code. No runtime search/hash/LRU/variant selector needed — the "(code,bank)" identity is resolved offline into the region bytes. The sprite **palette line** comes from `palette_route_lookup(PC090OJ, effective_bank)` via the route table (7 explicit source-bank rows → L0/L1).

## 6. Line 0/1 staging + survival
`vdp_reassert_test_lines` (vdp_comm.s) asserts `test_sprite_line0`→L0, `test_sprite_line1`→L1, `editor_layera_palette`→L3 each **gameplay** VBlank (scene 1 only), marks `palette_dirty`; Line 2 never touched. This survives arcade palette conversions and frontend writes (KF-0174). Frontend scenes keep their own lines (gate on scene_id==1). **Runtime-verified**: with the cave scene loaded, staged L0==Test L0, L1==Test L1, L3==Test L3 (exact).

## 7. Rastan off Line 3
Route table: PC090OJ bank 0x33 → Line 0 (was Line 3). Rastan renders his offline-reindexed pixels against Test L0. No raw-palette relocation. No R1/P1 sprite selects Line 3.

## 8. Layer-A → Line 3
`.Lplane_a_native_attr_from_word` (tilemap_hooks.s) replaced route-lookup+`bank&3` fallback with a single `moveq #3` → **all** authored Layer-A source banks resolve to Line 3 (one generalized rule, no per-bank exception). Verified in ROM at offset `0x703FA` (`7003 e148 eb48`), on the gameplay path (`selector0_native`/`selector12_native` both call it). Test L3 CRAM `0000 028C 044C 0026 0004 0002 0424 0624 0402 0202 0200 0422 0440 0660 0AA6 0884` staged + re-asserted.

## 9. LA-0458 proof
`pc080sn_editor_layera.bin[0x70]` SHA = `888a34a5fc2e5272` (unchanged). Layer-A name words now select Line 3 (forced-line-3 code confirmed in ROM; fresh gameplay emits line 3 — the stale 0324 save state still holds 0324's name words, so its histogram is not evidence). Bank 0x4 no longer falls through to Line 0 (fallback removed).

## 10. Normal-build / provenance
`PC090OJ_EDITOR` is an ordinary Make dependency of `pc090oj_assets.o`, generated from the frozen Test profile + corpus + preconverted region. Provenance: profile SHA `deb696452d7456b3…`, sprite asset SHA `9a022a0a…`, manifest SHA `1f245ae6…`. No `/tmp`, no one-off command, no hardcoded mapping.

## 11. Verification / builds
Build 0325 → `dist/rastan-direct/rastan_direct_video_test_build_0325.bin` SHA `3691f6d9…`. Static/build gates: seven-epoch gate PASS (records 0,3,4,10,11,12,15), plane-A/B full-LUT PASS, plane drops 0, exceptions 0, sp_valid YES, MAME 30s boot clean. Runtime: staged L0/L1/L3 == Test (exact). Reuse policy unchanged (no diff). Layer B / Line 2 untouched.

## 12. USER MUST VERIFY (visual, gameplay)
1. Rastan appearance. 2. Lizardman appearance. 3. Other encountered R1/P1 enemies. 4. Segment-1 cave stone = purple/mauve Test palette. 5. Exterior Layer-A. 6. Layer B. 7. Ignore deferred vertical-fill / Segment-11 reuse until this palette build is accepted.
