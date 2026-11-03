# Handoff → Cody: runtime per-subround palette (+ reindex/line) selection

**From:** Andy · **Date:** 2026-10-26 · **For:** Cody (native Genesis runtime)
**Why:** The Palette Composer now authors a distinct palette per subround (R1-S2 castle, R2-S2, …),
but the production ROM can only render R1-S1's. This handoff is the native runtime work to make each
subround load and render its own authored palette. No Composer/authoring change is requested here.

---

## The gap (verified in the current checkout)
The static build bakes exactly ONE global palette + ONE tile reindex, both hardcoded to R1-S1, and all
seven standard variant ROMs are post-patch copies that share it (stage-select `_S1-x` ROMs included):

- `tools/graphics_editor/gen_test_palette_cram.py` bakes **only** `Test.json.target_palette_lines`
  (the base = R1-S1 colors) → `build/rastan-direct/test_palette_line{0,1,3}.bin`, incbin'd into
  `apps/rastan-direct/src/palette_hooks.s` (Makefile line 369). Line 2 stays arcade Layer-B.
- `tools/graphics_editor/gen_reindexed_region.py` reindexes Plane-A tile pixels using **only**
  `context_policies["context:gameplay.r01.p01"].plane_usage_palette_mappings` (line 31) →
  `build/regions/pc080sn_editor_layera.bin`. It is **code-indexed** and emits the most-frequent variant
  per tile code (documented Build-0315 limitation), so shared tile codes across subrounds conflict.

Result: boot into R1-S2 (stage byte `0x5FF9F`) and the castle renders with R1-S1's palette and R1-S1's
reindex — the Composer's R1-S2 colors, bank→line moves, and flame→Line-2 reuse do not appear. A static
per-variant bake cannot fix this (one shared ROM can't carry two per-subround palettes, and shared tile
codes can't be reindexed two ways).

## The authored data is ready (Composer side — do not rebuild it)
Everything you need is already produced by the Composer pipeline:

- **Per-scene CRAM blobs** (the palette to install): `build/palette_export/cram/<scene_key>.bin`, e.g.
  `PAL-R1-S2-PLANEA-CASTLE.bin`. Format: authorable Lines **0, 1, 3** × 16 big-endian CRAM words
  (index 0 = 0x0000 transparent). Line 2 is excluded (arcade Layer-B, never authored). Regenerate with
  `tools/graphics_editor/export_subround_palette_manifest.py --profile Test`.
- **Scene manifest**: `build/palette_export/palette_scene_manifest.json` — per scene_key: round,
  subround, env, `record_band`, `stage_index`, `palette_status`, `cram_lines`, `cram_asset`.
- **Subround → records / stage map**: `specs/palette_subround_map.json` (18 subrounds × environments,
  scene keys, native status, records, stage_index with subround offsets outside=0/castle=16/boss=22).
- **Authoring source of truth** (if you need the raw per-scene overrides + mappings):
  `analysis/graphics_optimizer/editor_policy/Test.json` →
  `context_policies["PAL-R1-S2-PLANEA-CASTLE"]` holds `tpl` (per-line color overrides) and
  `plane_usage_palette_mappings` (`{usage_id: {line, index_map}}`). The CRAM blob already bakes the
  effective colors; the mappings are what a per-subround **reindex** needs (see below).

## What to implement (native runtime)
At the existing scene/subround boundary — the proven scene decode `0x13E → 0x507C5 → 0x3951C` 12-byte
descriptor, round counter `a5@0x118` (`0x10C118`), stage index `a5@0x1242` (`0x10D242`) — select the
scene_key for the current round+subround+environment and:

1. **Palette (colors):** load that scene's CRAM blob into palette RAM Lines 0, 1, 3 (`0x200000` banks
   for those lines). **Leave Line 2 to the arcade Layer-B path** (unchanged). When a scene's
   `palette_status` is `missing`/`provisional`, keep the existing arcade conversion — do NOT substitute
   another subround's palette (the manifest says which).
2. **Tile reindex + line selection (the harder half):** the Composer's `plane_usage_palette_mappings`
   reassign which palette entry (and line) each Plane-A usage draws from. Statically this is baked into
   `pc080sn_editor_layera.bin`, but code-indexed baking can't represent two subrounds' assignments for a
   shared tile code. Options to evaluate (your call on the native-replacement boundary):
   - per-subround reindexed Plane-A tile banks selected at the scene boundary, or
   - a runtime (code,bank)→palette-entry/line resolution using the per-usage mappings, or
   - reindex keyed by (code,bank) rather than code so shared codes don't collide.
   The right cut is the one that removes the R1-S1-only hardcode, not a per-scene special-case.
3. **Keep it data-driven:** consume the per-scene export + subround map; don't hardcode R1-S2. The same
   path must serve every subround that has an authored palette.

## Constraints (project rules)
- Line 2 / Plane B is arcade-controlled — never authored or overwritten.
- Only install palettes for scenes whose decisions are approved/proven; respect `palette_status`.
- Honor the USA/NTSC target; validate on the `genesis` machine, arcade ROM as ground truth.
- No NOP/RTS/stub/trampoline; follow the shift-table reflow pipeline for any maincpu replacement.
- This replaces the R1-S1-only static bake with one data-driven per-subround owner — a net reduction of
  the hardcode, consistent with the holistic native-replacement mandate.

## How to verify
Build, then boot each subround via the stage-select byte (`0x5FF9F`: R1-S1 outside = stage 0, R1-S2
castle = stage 16) on the USA/NTSC `genesis` machine, and confirm each subround's Plane-A renders its own
Composer palette. Cross-check colors against the scene's CRAM blob; Line 2 must match the arcade Layer-B
result. Arcade MAME is the geometry/behavior ground truth.

## Status / asks for Tighe
- No ROM build was consumed producing this handoff (Tighe chose to hold the build).
- Open question for Cody: which reindex/line mechanism (option in §2) fits the native boundary best —
  per-subround tile banks vs runtime (code,bank)→line resolution. That choice drives the ROM size/timing
  cost and whether the static `gen_reindexed_region.py` is retired or made scene-parameterized.
