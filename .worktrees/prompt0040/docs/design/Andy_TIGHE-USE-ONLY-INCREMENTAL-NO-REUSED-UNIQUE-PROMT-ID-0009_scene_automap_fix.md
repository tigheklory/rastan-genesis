# PROMPT-ID-0009 — Fix Scene-Specific Layer A Automapping

**Author:** Andy · **Date:** 2026-10-25 · **Branch:** `rastan-direct-proposal`
**Scope:** Palette Composer only (`tools/graphics_editor/`). No ROM build, no native Genesis code, no
Audio Composer, no approved-palette overwrites.

## Final acceptance (met at the data layer)
Selecting **R1-S2 Castle** and running Auto-map now maps **only R1-S2's** Layer-A usages to R1-S2's
Genesis colors, writing **only** to `PAL-R1-S2-PLANEA-CASTLE`'s context. R1-S1, R2-S2, every other
subround, and the global/phase mappings are provably unchanged. The same isolation holds for every
supported subround. Proven headless by `verify_scene_automap.py` (16/16) + `verify_independent_scopes.py`
(9/9, no regression). Browser-only items (dialog text seen live, Undo/Redo UI, stale-async abort) are
listed as manual steps.

---

## 1. Root cause
Two defects made Auto-map write to Round 1 / Phase 1 regardless of the selected scene:

1. **Client `phaseContext()`** walked the context chain for a `…rNN.pNN` phase node and, finding none
   for the new `PAL-R*-S*-PLANEA-*` scene keys, **fell back to `context:gameplay.r01.p01`**. So the
   destination context, the confirmation text, and the written plane mappings all became R1/P1.
2. **Server `phase_layera_automap()`** called `build_layera()` with **no scene**, i.e. always the frozen
   R1/P1 corpus — so even the *source* usages/colors were R1/P1, never the selected subround.

A third, directly-related defect (Req 8): the group-solve source `layera_solver_usages()` also used
`build_layera()` with no scene, and `loadSubroundScene()` had a `ctxById(sceneKey) ? sceneKey : r01.p01`
fallback that could still route a real subround selection to R1/P1.

## 2. Fix — client (`app.js`)
- Replaced `phaseContext()` with **`automapContext()`**: a `PAL-*` scope resolves to **its own** scene
  context (`{id:SCOPE, scene:SCOPE, kind:'scene'}`); a genuine `…pNN` phase node resolves phase-wide on
  the R1/P1 corpus (`scene:null`); **anything else returns null — never an r01.p01 fallback.**
- `phaseAutoMap()` rewritten:
  - sends `scene` to the server; **verifies the echoed scene identity** before applying;
  - **stale guard** — if `SCOPE`/`ACTIVE_SCENE` changed during the async call, the result is discarded;
  - **fills unmapped first**; if existing mappings would change, a **second explicit confirm** is required;
  - writes only to the destination context's `plane_usage_palette_mappings`, as **one** `pushUndo()` txn;
  - target CRAM colors are never touched.
- Button renamed to **“Auto-map Current Scene”** for a scene scope (phase label only for a real phase
  scope); the confirm/result now report scene key, Genesis line, usages considered, new, replaced, and
  blocked counts, and “target colors will NOT change”.
- `loadSubroundScene()` fallback removed: a real subround selection authors on its **own** scene key,
  only the explicit R1-S1 outdoor scene uses `r01.p01`, deselection returns to `r01.p01`.
- `solveLA()` sends the active scene so the group-solve source corpus follows the scene.

## 3. Fix — server (`server.py`)
- `phase_layera_automap(line, target_colors, scene=None)` → `build_layera(scene)`; response **echoes
  `scene`**.
- `/api/phase_automap` validates: editable line (Line 2 → 403); populated colors (→ 400); a provided
  `scene` must be a `PAL-*` key (→ 400 otherwise) **with an existing corpus** (`_scene_corpus_dir`) or it
  **fails 404 — no R1/P1 substitution**. `scene:null` keeps the R1/P1 phase corpus.
- `layera_solver_usages(ids, scene=None)` → `build_layera(scene)`; `/api/solve` accepts + validates `scene`.

## 4. Existing-mapping protection
Auto-map only fills unmapped usages unless the user separately confirms replacement; it never changes the
16 target CRAM colors, never auto-approves decisions, and never writes Line 2, the global map, or another
scene. Approved R1-S1 decisions, scene-specific overrides, inherited entries, and profile persistence are
preserved (verified C3/C4/C5).

## 5. Other mapping paths (Req 8 audit)
Single-tile map, clear, and delete all go through `setPlaneMapping`/`delPlaneMapping`, which already write
at the active `SCOPE` (the scene context for a subround) — no R1/P1 fallback. The only source-corpus
blindness was the group solver, now fixed. No unrelated redesign.

## 6. Tests (`tools/graphics_editor/verify_scene_automap.py`, 16/16)
- **A** R1-S2 echoes its scene + proposals ⊆ R1-S2 corpus.
- **B** R2-S2 echoes its own scene + proposals ⊆ R2-S2 corpus.
- **C** apply→save→reload stores under the scene; R1-S1 byte-identical; nothing in global map; CRAM colors unchanged.
- **E** unknown scene→404, corpus-less scene→404, Line 2→403, invalid key→400 (never R1/P1).
- **F** `scene:null` R1/P1 phase works and differs from the subround corpus.
- Manual (browser): confirm-dialog wording, Undo/Redo one-transaction + after scene switch, stale-async abort, cancel = no change.

## 7. Scaffolding / audit
New durable test tool: `tools/graphics_editor/verify_scene_automap.py` (reusable regression gate). No
disposable `/tmp` scripts, no production scaffolding, no `rts`/NOP, no ROM build, no registry duplication.

## Preserved
R1-S2 / R2-S2 visual maps (Cody's selector-aware decoder) untouched; native runtime untouched; Audio
Composer untouched; approved palettes untouched; no ROM build number consumed.
