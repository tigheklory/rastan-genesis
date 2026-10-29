# PROMPT-ID-0029 — R1-S2 Castle Actors in the Palette Composer Browser

**Author:** Andy · **Date:** 2026-10-29 · **Status:** COMPLETE (resumed after usage-limit interruption)
**Commit:** `af8fc21b` · **Scope:** Palette Composer catalog + browser only.
**No ROM build, no Ghidra decompilation, no Genesis runtime change, no new palette editing/persistence
(0030), no Test.json / authored-decision change.** No build number consumed.

---

## Objective
Make the verified R1-S2 castle actor graphics (PROMPT-ID-0025 roster) selectable and browsable in the
existing Palette Composer, using real static arcade sprite data and the per-piece arcade palette from
PROMPT-ID-0028 — additively, without disturbing R1-S1 or any authored work.

## What was implemented

### Server (`tools/graphics_editor/server.py`)
- **`r1s2_castle_usages()`** (module-cached in `_CASTLE_USAGES_CACHE`): appends the castle actors to the
  existing `build_usages` catalog. Decoded statically via the existing `_manifest_vm_pieces` /
  `compositor_vm` (the Bestiary route — **no trace**). No parallel browser/endpoint.
  - **base `$0224`** (marker 'E', state `$18`/`0x44082`) and **base `$00F4`** (marker 'E' retarget via
    `0x40E88`) each exposed as one `object_id` with **24 distinct composite frames** (deduped by piece
    signature). Route-documented anims (`$91`, `$27` / `$70`) and multi-bank frames are ranked first so
    the real frames surface, not just low default anims. The actor exposes `frames_total_distinct` for
    honesty about the full 218-anim space.
  - **marker 'M' burst** (`$4D`, state `$1B`/`0x43ECC`, `arcade_43f4e_burst`, 5 children): represented
    **honestly as INCOMPLETE** — coordinate-only (seeded-SAT) child presentation is not statically
    decodable as one composite, so the entry has **0 pieces, `composite_proven=false`, `incomplete=true`,
    no fabricated frames**.
  - Each piece keeps its own arcade palette nibble (`palette`); `_castle_used_colors()` lists the distinct
    per-bank source colours (keyed by `(nibble, pixel index)`) for the source chips.
  - All castle usages carry `scene_key = "PAL-R1-S2-PLANEA-CASTLE"` and `round = 1`; identity labels are
    **provisional and source-derived only** (no "Armored Man"/"Wizard" assertion).
- **`/api/render` usage path**: castle actors (usages with `round` + per-piece `palette`) render each
  piece with its own arcade palette (PROMPT-0028 preserved) for both the source and the unmapped preview
  (authored Genesis mapping is PROMPT-0030). Existing single-bank usages unchanged.

### Client (`tools/graphics_editor/app.js`)
- The Objects list filters usages by `scene_key`: a usage shows if it has no `scene_key` (general R1/P1
  enemies/player/items — always) or its `scene_key === ACTIVE_SCENE`. So castle actors appear **only when
  R1-S2 is the active scope** and are never shown as R1-S1 assets. The existing frame browser
  (`renderFrameBrowser`, `reps>1`) navigates the castle frames; no new UI architecture.

## Scaffolding inventory & removal plan
No scaffolding was added to the production ROM or runtime. The only new tooling file is the durable,
reusable regression test `tools/graphics_editor/verify_r1s2_castle_browser.py` (kept, not scaffolding).
The `_CASTLE_USAGES_CACHE` is an in-process cache, not disk state. Nothing to remove. No `/tmp` scripts,
no NOP/RTS/stub, no registry duplication.

## Verification
`tools/graphics_editor/verify_r1s2_castle_browser.py` — **11/11 PASS**:
server loads; `/api/oracle` returns 49 castle usages + **382 R1/P1 usages intact & untagged**;
`$0224`/`$00F4` browsable (multiple frames each); route-documented **anim `$91` is multi-bank (banks 3+12)
and its composite uses BOTH source palettes**; marker-'M' burst incomplete with no fabricated frames;
castle usages scene-tagged; oracle idempotent (cache → no duplicates); **Test.json SHA-256 unchanged**.
No regression: `verify_per_piece_palette` 6/6, `verify_scene_automap` 44/44, `verify_independent_scopes`
9/9; `app.js` passes `node --check`.

## Status / remaining
- **Done:** castle actors discoverable + frame-navigable in the editor with correct per-piece arcade
  colours, scene-filtered, additive, R1-S1 unchanged, Test.json untouched.
- **Deferred (by design):** authored Genesis palette mapping/editing/persistence for these actors
  (PROMPT-0030); full Ghidra C of the marker-'M' child presentation (PROMPT-0031); **visual confirmation
  of which base is the "Armored Man" vs "Wizard"** — the arcade code does not settle the name, so it is
  left provisional for Tighe to confirm in the browser.

## Files changed
- `tools/graphics_editor/server.py`
- `tools/graphics_editor/app.js`
- `tools/graphics_editor/verify_r1s2_castle_browser.py` (new)
- `AGENTS_LOG.md`, this design note.

---

## CORRECTION (PROMPT-ID-0038, 2026-10-29) — round attribution reconciled from source

My 0029 (and the 0025 roster) **mis-attributed bases `0x0224`/`0x00F4` to R1-S2.** Reconciled against the
maintained C and Bestiary H14:

- Handler `0x44082` (`h5_44082`, state 0x18) has a progress guard: `if (progress_13e < 0x18) arcade_4092e()`
  (RETIRE, no base write). R1-S2's progress is `0x11..0x16` (< `0x18`), so **the R1 'E' marker retires and
  `0x0224` never materializes in R1.** H14 confirms: Round 1 prog 0x15 'E' → "prog<0x18 → 4092e", base `-`.
- **Correct rounds (Bestiary H14, exact `+0x1E` write):** `0x0224` → **R2, R4**; `0x00F4` → **R4, R5, R6**.
- The **only** R1-S2 marker actor is the **'M' burst** (`0x4d`→`0x43ECC`, H14 R1 prog 0x11) — children
  identity PENDING, kept INCOMPLETE (no fabricated art).

**Fix applied:** `r1s2_castle_usages()` now emits one browsable object per `(base, round)` — `0x0224`@R2 /
`0x0224`@R4 (PAL-R2-S2 / PAL-R4-S2), `0x00F4`@R4/R5/R6 — each with its correct per-round palette; the
`'M'` burst stays R1-S2. The scene filter is unchanged (one `scene_key` per instance). The **Bestiary
manifest already carried the correct H14 attribution**, so no Bestiary change was needed — it is
authoritative; the 0025 roster JSON was corrected (v2) to a derived cross-check pointing at it.

Verification: `verify_r1s2_castle_browser.py` **11/11** (R1-S2 = only the 'M' burst; `0x0224`=R2/R4,
`0x00F4`=R4/R5/R6; multi-bank `0x91` uses both banks; per-round mechanism round-sensitive; R1/P1 intact;
Test.json unchanged). `verify_r1s2_actor_roster.py` 5/5. No new C was needed — the guard was already in
`rastan_actor_behavior.c`; the error was my roster tooling not applying it.
