# One-Click "Derive Scene Palette" (whole-tileset closest-Genesis derive)

**Author:** Andy · **Date:** 2026-10-25 · **Branch:** `rastan-direct-proposal`
**Trigger:** Tighe direct request (not a numbered PROMPT-ID) — "I really want to do the whole tileset",
instead of per-tile "Copy Used Colors" or per-usage checkbox selection for "Derive Shared Palette".
**Scope:** Palette Composer only (`tools/graphics_editor/`). No ROM build, no native code, no Audio
Composer, no approved-palette overwrite.

## What it does
A single button, **"Derive Scene Palette → Lines 0/1/3"** (left panel, under Auto-map), derives the
closest-possible Genesis palette for the **entire** selected subround tileset and maps every usage —
no hand-selection.

## Algorithm (honors Plane-A semantics)
Each Plane-A tile/usage draws from exactly ONE palette line, so the derive is **bank-centric**:
1. Per arcade bank, collect the distinct source colors its usages actually use; quantize each to its
   **nearest legal CRAM by CIEDE2000**, kept distinct within the bank (so a bank never self-merges → MRD 0).
2. **Pack** the banks into the authorable lines (0, 1, 3), each line holding ≤15 CRAMs, merging banks
   that share colors (greedy, least-growth first). A bank that fits no line is **BLOCKED** — its usages
   are reported and left unmapped, never merged or substituted.
3. Emit each line's palette (indices 1–15) and, per usage, `line` + `index_map` onto those entries.

## Isolation (per-subround independence)
On apply: derived **colors** are written to the destination context's **per-scene override**
(`context_policies[scene].tpl`), NOT the shared base `target_palette_lines` — so one subround's palette
never clobbers another's. **Mappings** go to `context_policies[scene].plane_usage_palette_mappings`.
Both at the same scope, one Undo transaction. Line 2 is never written. Index 0 stays transparent.
Scene identity is verified (echoed by the server) and a stale-selection guard prevents applying a result
to a different scene than requested. Unknown / corpus-less scenes fail (404) — the R1/P1 corpus is never
substituted.

## Server
`GET`→`POST /api/scene_palette {scene, lines}` → `derive_scene_palette(scene, lines)` in
`tools/graphics_editor/server.py` (new `_nearest_cram` ΔE helper). Same fail-safe scene validation as
`/api/phase_automap`.

## Results (observed)
- `PAL-R1-S2-PLANEA-CASTLE`: 14/15 banks placed (1 blocked — 45 slots can't hold all 15 banks' distinct
  colors), 501/520 usages mapped, Lines 0/1/3 each filled to 15. Blocked bank's 19 usages are reported.
- `PAL-R2-S2-PLANEA-CASTLE`: 5/5 banks, 234/234 usages mapped (fits Line 0 alone).

## Usage note (scope/corpus alignment)
The derive targets the **editing scope** (`automapContext()` → the active `PAL-*` scene). If the editing
scope and the loaded corpus disagree (e.g. header shows R3-S2 while R1-S2 is loaded), click **"Load into
editor"** on the intended scene first so scope + corpus + save target all agree; a scope with no corpus
returns a clear 404 rather than deriving the wrong tiles.

## Tests
`tools/graphics_editor/verify_scene_automap.py` — 25/25 (adds G1–G9: scene identity, mappings ⊆ scene
corpus, lines filled with CRAM strings, one-line-per-usage, unknown-scene 404, colors stored as per-scene
override with base untouched, R1-S1 untouched, Line 2 never written). No ROM build, no scaffolding, no
rts/NOP.
