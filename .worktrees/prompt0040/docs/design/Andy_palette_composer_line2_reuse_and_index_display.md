# Andy — Palette Composer: Line-2 reuse, index display, larger swatches, Layer-B colors + animated-sky index

**Date:** 2026-10-20 · **Type:** Tooling (graphics editor UI/behavior) + one arcade palette capture.
**No production assembly / ROM / baseline / gameplay change.** Requested by Tighe across two prompts.
Files are the Palette Composer only (`tools/graphics_editor/`), plus one captured data file and the
established arcade MAME palette-dump tool (read-only).

## Goals (Tighe's requests)

1. Line 2 was fully locked. Only the **ability to edit Line-2 colors** should stay locked — Tighe wants
   to **reuse** Line-2 colors for objects in some cases.
2. Know **which Line-2 index is animated** (the sky/time-of-day color) so it can be avoided.
3. When editing an object, show **index numbers** on the target palette so it's clear which indices are
   already assigned; make the **swatches larger** (readability).
4. Line-2 colors were not visible ("empty"); they should be **shown**.

## What changed

### A. Line 2: reusable, still not editable
- `editable: false` for Line 2 is preserved **only for color editing** (no sliders, no new colors, no
  recolor — `showTarget()` still returns the read-only protected view for Line 2; `mapWithAuto` never
  writes a Line-2 CRAM).
- Line 2 is now **selectable** (click its label to make it active) and its **occupied** swatches are
  **clickable to reuse**: select a source color, click a Line-2 color → the object's index maps to that
  Line-2 index (status shows `[reusing Layer-B color]`). Mapping onto an **empty** Line-2 index is
  refused (that would require creating a color = editing).
- `app.js`: `mapWithAuto` gained a protected-line branch (reuse-only; rejects empty); the protected
  swatch render became click-to-reuse; the protected label click sets `ACTIVE`.

### B. Index numbers + object-assignment tags + larger swatches
- Every target swatch now shows its **index number** (top-right; bright on occupied, faint on empty).
- For the selected object, each index it is already mapped to gets a **cyan ring + source-index tag**
  (`i3`) at bottom-left — so "is a color already assigned to this index" is visible at a glance.
- Swatch size **22px → 40px**; index/tag fonts enlarged (`style.css`).

### C. Line-2 colors are now displayed (read-only)
- **Why they were empty:** Line 2 is the **arcade-controlled time-of-day Layer-B palette**. The editor
  profile stores Line 2 as all-null and the build's CRAM report emits only lines 0/1/3
  (`line_order:[0,1,3]`) — there were literally no Line-2 values to draw.
- Fix: the server now serves a **read-only Layer-B display palette** (`line2_display`), loaded from
  `analysis/graphics_optimizer/round1_phase1_corpus/layer_b_display_palette.json`, and `app.js` renders
  it on Line 2 when the profile entry is null. Display only — never editable, never written to the
  profile.

### D. Animated sky index — IDENTIFIED = **index 1**
- Captured the ORIGINAL ARCADE palette RAM (`0x200000`) at four time-of-day frames (360/460/700/1000)
  using the existing `tools/mame/scripts/arcade_layera_palette_dump.lua` (read-only, arcade `rastan`).
- **Layer B (Genesis Line 2) = arcade palette RAM bank `0x001`** (the sky + ground background palette;
  confirmed by content — blues at 7/8, ground browns at 2-6). Bank 0x002 (named in
  `layer_b_palette_usage.csv`) is zero at these frames and is not the displayed palette.
- Diffing the four frames: the **only** entry that changes is **bank 1, index 1**
  (`0x0000` at frame 360 → `0x00EE` yellow at 460/700/1000) — the sky/sun time-of-day color.
- So **`LINE_OWNERS["2"].animated_indices = [1]`** (server). `app.js` renders animated Line-2 indices
  with a dashed-amber outline + ⚡, an "ANIMATED sky — avoid" tooltip, and a confirm before reuse.

## Evidence / provenance

- `animated_indices = [1]`: VERIFIED by the 4-frame arcade capture diff (only bank1:1 changes).
- Layer-B display colors: the arcade runtime palette RAM bank 0x001 at frame 460 (representative);
  per-frame values retained in the data file.
- **Honesty note:** the arcade-bank-0x001 → Genesis-Line-2 correspondence is **inferred from palette
  content** (bank 1 is unmistakably the sky/ground background), not from a wired pipeline fact. The
  display is for reference/authoring; it is not a claim about the production generator. Line 2 remains
  arcade-controlled and non-editable.

## Production-integration caveat (for Cody — not done here)

Mapping an object onto **Line 2** is now authorable in the tool, but whether the generator/runtime
(`gen_reindexed_pc090oj.py` / the semantic-profile path) honors a Line-2 target is a separate
production-integration question. This change unlocks the **authoring** side only; no generator/runtime
change was made.

## Files changed

- `tools/graphics_editor/app.js` — Line-2 reuse (`mapWithAuto` protected branch), index numbers +
  object-assignment tags (`decorate`), animated marker (`animatedIndices`), Line-2 display rendering.
- `tools/graphics_editor/style.css` — swatch 22px→40px; `.idx` / `.objtag` / `.anim` labels;
  `.objassigned` / `.animidx` / `.protusable` classes.
- `tools/graphics_editor/server.py` — `LINE_OWNERS["2"].animated_indices=[1]`; `_layer_b_display()` +
  `line2_display` injected in `_backfill_policy`.
- `analysis/graphics_optimizer/round1_phase1_corpus/layer_b_display_palette.json` — NEW; captured
  Layer-B palette + per-frame values + `animated_indices`.
- `build/mame/layerb_palette/palette_ram_f{360,460,700,1000}.bin` — generated capture output.

## To use

Restart the editor server (`tools/graphics_editor/run.sh`) and refresh. No existing Test-profile
decisions or colors were changed; no ROM/production/baseline modification.
