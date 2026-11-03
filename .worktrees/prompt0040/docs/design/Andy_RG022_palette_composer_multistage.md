# Andy — RG-022: Per-Subround Palette Composer Expansion

**Agent:** Andy (Opus) · **Date:** 2026-10-25 · **Graphics baseline:** Cody Build 0499 (RG-021) ·
**Scope:** Palette Composer (`tools/graphics_editor/`) + the canonical registry
`specs/palette_decisions.json`. **Editor-only — no ROM build consumed. Cody owns the native
renderer and the integration points `scene_load.s` / `tilemap_hooks.s` / `palette_hooks.s`.**

## 1. What was built (real tool changes, all tested)

| Artifact | Purpose |
|---|---|
| `specs/palette_subround_map.json` (new) | Authoritative 18-subround × per-environment model: authentic scene keys, native-graphics availability, families. The index the editor/export/Cody share. |
| `tools/graphics_editor/migrate_palette_registry_subround_keys.py` (new) | Safe additive migration: backs up the registry, stamps each existing decision with `scene_applicability`, self-verifies nothing else changed. |
| `specs/palette_decisions.json` (migrated, schema v2) | The 23 R1 decisions preserved byte-for-byte except the additive `scene_applicability`; `subround_key_scheme` recorded. Still the sole registry. |
| `tools/graphics_editor/export_subround_palette_manifest.py` (new) | Deterministic export generator → `build/palette_export/palette_scene_manifest.json` (the contract Cody consumes). |
| `server.py` `/api/subrounds` (added) | Serves the 18-subround model enriched with per-scene palette status. Additive; existing endpoints untouched. |
| `index.html` + `style.css` subround scope panel (added) | Self-contained 18-subround selector showing native + palette status per environment and the active scene/segment/family. Does not touch the existing sprite-authoring UI. |
| `tools/graphics_editor/verify_subround_palette_coverage.py` (new) | 12-check regression/contract suite (all pass). |

## 2. Stable palette-key scheme (RG-022 §2)

`genesistan_current_scene_id` alone is insufficient — R1-S1, R1-S2, R2-S1 all report `scene_id=1`
(verified in RG-020). The authentic key combines:

```
round (a5@0x1242 / 23 + 1)  ·  subround (stage offset in round: 0=Outside, 16=Castle, 22=Boss)
  ·  segment/record band (a5@0x13E)  ·  residency/epoch (PC080SN package)  ·  graphics family
```
Key format: `PAL-R{round}-S{subround}-{family}-{env}` (e.g. `PAL-R1-S2-PLANEA-CASTLE`,
`PAL-R1-S1-PC090OJ`). Correspondence to arcade/native is recorded per environment in
`palette_subround_map.json` (`stage_index`, `records`, `residency_hint`, `family`). Families:
`PLANEA` (authorable, Genesis lines 0/1/3), `PC090OJ` (authorable, sprites), `PLANEB`
(**not authorable — Line 2 is the arcade-controlled Plane-B line**, shown read-only).

## 3. Safe migration (RG-022 §4) — existing work preserved

`migrate_palette_registry_subround_keys.py` backed up the registry to
`specs/_backup/palette_decisions.<utc>.json` and added only `scene_applicability` to each decision
(21 gameplay → `PAL-R1-S1-PC090OJ`; 2 frontend → `FRONTEND`; generic-death/HUD/attract flagged
`cross_scene_candidate` for *explicit* opt-in sharing, never auto-applied). The suite confirms the
decision set and every original field/value are unchanged. Audio Composer and its nine arrangements
are untouched. No editor reset; no replacement registry.

## 4. Native-graphics integration (RG-022 §5) — real RG-021 identities

From Cody RG-021 / Build 0499: native Plane A/B packages now exist for **R1-S2 castle, R1-S3 boss,
and R2-S1/S2/S3** (records 16–22 and 23–45). The map marks these `native_converted`; R4 is
`native_not_converted`/`mode_a` (recognized, content absent); R3/R5/R6 are `mode_b` (not
recognized — source outside `genesistan_scene_a0_ranges`). The UI/manifest distinguish per
environment: **native_status** (converted / not) and **palette_status** (`missing` / `provisional`
/ `approved` / `mixed`). R2 currently carries Cody's raw arcade conversion → surfaced as
provisional/missing until authored. **No subround ever borrows another's approved colors unless its
own scene_key is explicitly listed in a decision's `scene_applicability` (enforced by test 11).**

## 5. Export contract for Cody (RG-022 §6) — delivered now

`build/palette_export/palette_scene_manifest.json`, schema `rastan-palette-scene-manifest/v1`,
produced deterministically by `export_subround_palette_manifest.py`. One row per environment:

```
scene_key, round, subround, env, family, stage_index, record_band,
authorable, native_status, mode, palette_status,
decisions[ {id, status, genesis_lines, scene_applicability} ],
cram_lines[],        # authorable Genesis CRAM lines (Line 2 excluded)
cram_asset,          # path to exported CRAM blob once a scene is approved (null until then)
shared_from          # set only when a decision is EXPLICITLY shared from another scene
```
Contract rules the native build MUST honor:
1. **Line 2 / Plane B is never authored or overwritten.**
2. `palette_status ∈ {missing, provisional}` ⇒ the build keeps the existing arcade conversion for
   that scene and applies **no** Composer palette (no silent substitution).
3. A decision governs a scene only if that `scene_key` is in its `scene_applicability` (explicit;
   cross-round sharing requires the target key to be listed, never inferred).
4. Deterministic: identical inputs → identical bytes (build-dependency safe).

Identifiers Cody keys on at runtime: `round` (`a5@0x1242/23`), `subround`, `record band`
(`a5@0x13E`), `family`. **I did not edit `scene_load.s` / `tilemap_hooks.s` / `palette_hooks.s`** —
Cody wires runtime selection to these keys. CRAM output format = the existing per-line 16-entry
Genesis CRAM words the Composer already emits (via `export_palette_policy.py`); the new per-scene
`cram_asset` path will be `build/palette_export/cram/<scene_key>.bin` once a scene is approved.

## 6. Scenes requiring Tighe's palette authoring (RG-022 §7, deliverable #9)

All color approval is Tighe's; the editor prepares source/provisional only. **Priority order
(native graphics exist):**
1. **R1-S2 castle** — `PAL-R1-S2-PLANEA-CASTLE` (+ `PAL-R1-S2-PC090OJ` if castle sprites differ).
2. **R1-S3 boss** — `PAL-R1-S3-PLANEA-BOSS` (+ `PAL-R1-S3-PC090OJ`).
3. **R2** — `PAL-R2-S1-PLANEA-OUTDOOR`, `PAL-R2-S2-PLANEA-CASTLE`, `PAL-R2-S3-PLANEA-BOSS` (+ R2
   sprite families as they diverge from R1).

Deferred until Cody converts them (blocked, not authorable yet): all R3–R6 Plane-A environments
(R3/R5/R6 also need the `scene_a0_ranges` Mode-B fix first). The manifest lists every missing
scene_key.

## 7. Verification (RG-022 §8) and honesty

`verify_subround_palette_coverage.py` — 12/12 pass: 18 subrounds selectable; multiple environments
per subround; unique scene keys; **R1 decisions survived migration unchanged**; export deterministic;
status accuracy; **no silent cross-subround application**; Plane B never authorable. The
`/api/subrounds` endpoint was exercised in-process. **Not claimed:** that any palette *looks*
correct — that is Tighe's visual approval. No ROM build was produced (editor-only).

## 8. What is in place vs. next iteration

In place and tested: the authentic key scheme, the 18-subround/environment model, the safe registry
migration, the deterministic export contract + generator, the status model, the subround scope UI,
and the regression suite. Next (gated by Tighe authoring the colors): per-environment background
color-mapping reuses the existing Composer mapping machinery (`editor_policy` `context_policies`,
keyed by the new scene keys) and, on approval, emits the per-scene `cram_asset`; Cody then consumes
the manifest at the integration points. No approved R1 decision changes in that step.

---

## 9. Follow-up fix (same assignment): the editor now LOADS real per-subround graphics

**Problem reported by Tighe:** selecting R1-S2 in the subround panel only changed the label — it did
not load the castle tiles/enemies. The first pass delivered the key/model/export *metadata* but the
editor's graphics corpus (`plane_a_uses.json`, `_MAP_BASES`) was hardcoded to R1 outdoor records 0–15,
so there was nothing to display for castle/boss/R2.

**Fix (reuses Cody's committed ARCADE-SOURCE decoders, not the Genesis assembly Cody is still
correcting under RG-023):**
- `tools/graphics_editor/gen_subround_layera_corpus.py` — generates the per-subround Layer-A authoring
  corpus from the arcade source via `analyze_graphics.decode_plane_a(mc, gfx, segments)` (exact
  `plane_a_uses` rows) + arcade palette banks decoded from the startup base `0x4EAF6 + bank*32`
  (`0RGB` nibble → rgb8 via `_pal5`, matching the editor). Output:
  `analysis/graphics_optimizer/subround_corpus/<scene_key>/` + `index.json`. Generated for R1-S2 castle
  (records 16–21), R1-S3 boss (22), R2-S1/S2/S3 (23–45), and the R1-S1 caves.
- `server.py` made scene-aware: `build_layera(scene)`, `plane_bank_colors(scene)`, `layera_map(seg,
  scene)`, `layera_pattern_detail(pid, scene)` load the per-subround corpus; `/api/layera`,
  `/api/layera_map` (segment clamp widened 0→138), `/api/layera_pattern` accept `?scene=`.
- `app.js` made scene-aware (`ACTIVE_SCENE`, `sceneQS`, per-scene cache invalidation, record-band
  segment dropdowns) + `window.loadSubroundScene(scene_key, records)`.
- The subround panel's PLANEA environments now have a **"Load into editor ▸"** button that loads that
  subround's real arcade tilemap/tiles/palette banks into the Layer-A view and jumps to its first
  record.

**Verified (server-backed tests 13/14, all pass):** castle/boss/R2 each load real arcade tiles that
**fully resolve** (record 16 → 3648 cells resolved, 0 unresolved; boss 4096; R2 3086) with their own
distinct palette banks (castle 0x008–0x014/0x01F, not R1's 0x003–0x01D), and the castle bank colors
match the editor's authoritative R1 capture where banks overlap. Round-1 outdoor and all existing
approvals are untouched. **Sprites/enemies per-subround roster is the remaining piece** (the sprite
corpus is still R1-P1; surfaced in the panel as "sprites (per-scene roster pending)") — next step.
