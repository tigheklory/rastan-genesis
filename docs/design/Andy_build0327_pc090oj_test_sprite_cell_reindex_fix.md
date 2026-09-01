# Build 0327 — PC090OJ Test-Sprite 128-byte Cell Reindex Fix

**Type:** Implementation / Verification. ROM produced. Classification: **EXTENDING** (corrects the Build-0325 offline sprite reindex). Baseline Build 0326.

## 1. Phase 0
Priors/hazards: this corrects the defect documented in `Andy_build0326_r1p1_test_palette_playtest_analysis.md` #1. KF-043 (sprite line ownership) and the Build-0325 architecture preserved. Deferred: vertical-fill/noise/entity-dup/axe/HUD-text/waterfall-anim/cave-tiles — all OUT OF SCOPE. Issues touched: none reopened. Contradiction status: none.

## 2. Proven 32-vs-128 defect
The native runtime uploads a PC090OJ sprite pattern from `rastan_pc090oj + code*128` (`pc090oj_hooks.s:2038`, `mulu.w #128,%d0`). A PC090OJ **code = one 16×16 cell = four Genesis 8×8 tiles = 128 bytes**. The Build-0325 reindexer used `code*32` / 32 bytes, so it transformed the wrong offset and only one quadrant; the real runtime cells stayed **raw**, and every enemy with a non-identity map showed raw pixels (lizardman looked ~right only because its map is near-identity).

## 3. Corrected transformation
`tools/graphics_editor/gen_reindexed_pc090oj.py`: `CELL = 128`; read/transform/write `code*128 : +128`, applying the frozen-Test `index_map` to every pixel nibble across all four 8×8 subtiles; index 0 stays transparent; subtile ordering preserved (untouched). Only the offset/size changed — semantics, banks, lines, and Test maps are the already-resolved ones. Region: `build/regions/pc090oj_editor.bin` (asset SHA `9b346dda…`); provenance now records `source_offset=code*128`, `source_size=128`, `cell_sha256`, `cell_model`.

## 4. Independent verification (`tools/graphics_editor/verify_reindexed_pc090oj.py`)
Re-derives each expected 128-byte cell from the **raw** region + Test map independently and asserts `pc090oj_editor[code*128:+128] == expected` (semantic-cell assertion, not offset repetition). Result: **authored 124, transformed 120, mismatch 0, incomplete 0, stray-writes-outside-authored-cells 0**; 4 cells legitimately unchanged (identity map or used indices don't hit a non-identity entry — documented, not failure). Per-family independent proofs (editor==expected, cell changed): Rastan 138 `0673e06d…`, Lizardman 75 `efa65b44…`, Valkyrie 577 `45a0293d…`, Chimera 208 `e395dcb5…`, Flying Demon 297 `2476edee…`, Four-Armed Insect 744 `e85d1e89…`, Large Bat 1014 `9dd23292…`, Small Bat 616 `3732e664…`.

## 5. Coverage audit
authored codes 124 · expected transformed 120 · transformed 120 · missing 0 · unexpected 0 · incomplete 128B cells 0 · authored non-identity unexpectedly raw 0 · writes outside intended 128B cells 0.

## 6. Provenance
Manifest `pc090oj_editor_manifest.json` records per code: bank, usage, line, index_map, `source_offset=code*128`, `source_size=128`, `cell_sha256`, and profile SHA `deb696452d7456b3…`. The prior 32-byte `pattern_sha256` field is replaced by `cell_sha256` (128-byte cell).

## 7. Build-0326 palette preservation
Build 0327 touched only the offline sprite tool + the Makefile HUD default — no change to `palette_hooks.s` / `vdp_comm.s` / `tilemap_hooks.s`. Therefore Line 0 (Test sprite), Line 1 (Test sprite), Line 2 (protected Layer B), Line 3 (Test Layer-A) CRAM staging, the generalized Layer-A→Line 3 rule, and the gameplay re-assert are **byte-identical** to Build 0326. LA-0458 unchanged (`888a34a5fc2e5272`). Approved Segment-11 pattern-reuse policy unchanged (no diff).

## 8. Permanent HUD default — verified, not overridden
`apps/rastan-direct/Makefile` default is `RASTAN_GAMEPLAY_HUD_SPRITES ?= 2`. Build 0327 ran via the **normal** `make` (no command-line override); the regenerated `out/pc090oj_config.inc` contains `.equ RASTAN_GAMEPLAY_HUD_SPRITES, 2`. 1UP + P1 score remain enabled. Variable remains externally overridable for diagnostics; repo default stays 2.

## 9. Deferred HUD Palette Composer requirement
The 1UP/score text is red because the HUD text representation (source bank `0x30`) is **not** in the Test sprite reindex/palette set. **Not** fixed here (no hardcoded white, no CRAM-entry hack). Required follow-up: **add the gameplay HUD 1UP/score text representation to the Palette Composer as a first-class editable object/usage** (identify its complete code vocabulary), so Tighe can author its intended white line/index mapping, and then fold it into the offline reindex like the enemies. HUD appearance left unchanged in 0327 except as an incidental consequence of the stride fix (the HUD codes are not in the authored set, so it is unchanged).

## 10. Build / MAME
Build 0327 → `dist/rastan-direct/rastan_direct_video_test_build_0327.bin` SHA `2cb27f47…`. Gates: seven-epoch PASS (records 0,3,4,10,11,12,15), plane-A/B full-LUT PASS, plane drops 0, exceptions 0, sp_valid YES, MAME 30s boot clean (923% speed).

## 11. USER MUST VERIFY (visual)
Rastan, lizardman idle + swing, small/large bat, chimera (across poses), valkyrie, flying demon, four-armed insect all match the Palette Composer; Layer-A unchanged from 0325/0326; 1UP+score displayed (may still be red — deferred). Ignore vertical-fill/noise/entity-dup/axe/waterfall-anim for this test.
