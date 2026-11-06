# R1 Boss Palette — Brightness + Render Fix, and Bestiary Artifact Consolidation

**Date:** 2026-11-06 · **Author:** Andy · **Follow-up to:** PROMT-ID-0098 (Tighe-reported defect)

Tighe reviewed the PROMT-ID-0098 integration and reported two defects:

1. The Palette Composer **still rendered the R1 boss sprite blue**.
2. The Bestiary R1 boss looked **dim**, "like the final brightness wasn't used but a step or two
   too early" in the fade.

**Both assertions were CONFIRMED** and fixed. No Genesis production source, ROM, build counter,
CRAM, or push; `Test.json` SHA `e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730`
unchanged.

## Defect 1 — Composer rendered the boss blue (field pool, not the ROM table)

The decoded swatch **table** was fed the correct palette, but the actual rendered **sprite** bypassed
it. The boss pieces carry an embedded palette nibble `0xF`, so `/api/render` fell into its per-piece
branch and recolored every piece through `_arcade_round_palette(1, 0xF)` — the Round-1 **field pool**,
which is blue — never touching the proven ROM target table.

Measured on the real boss-body pieces:

| path | warm/red px | blue px | result |
|---|---|---|---|
| old field-pool path | 243 | 656 | **blue-dominant** (matches Tighe's screenshot) |
| fixed (ROM palette) | 1043 | 36 | **red-dominant** |

**Fix:** each R1 boss usage now carries `render_palette = palF` (the decoded ROM target table).
`/api/render` renders the whole composite with it and **skips** the per-piece field-pool branch.

## Defect 2 — half-brightness decode (a fade step early)

The boss target table was decoded with a **half-bright** nibble expansion,
`_pal4(n) = (n<<3)|(n>>2)`, which maps nibble `0xF → 0x7B` (123 ≈ 48%). Every other arcade palette in
the tool uses the nibble-doubling `_pal5`, which maps `0xF → 0xF7` (247).

`_pal5` of the ROM source table (`0x4708C`) reproduces the arcade's **actual full-illumination live
CRAM** (`0x2009E0–0x2009FF`, Cody PROMT-ID-0095 `final_live_words`) **exactly, all 16 entries** —
proven by decoding the live words as BGR555. Representative entries:

| idx | source 0RGB | old `_pal4` (dim) | fixed `_pal5` (full) | live CRAM |
|---|---|---|---|---|
| 3 (white) | `0FFF` | `#7B7B7B` | `#F7F7F7` | `#F7F7F7` |
| 8 (robe red) | `0C42` | `#632110` | `#C64221` | `#C64221` |
| 9 (deep red) | `0900` | `#4A0000` | `#940000` | `#940000` |

The Cody fixture's `rgb8` field was itself the dim rendering; its `final_live_words` are the authoritative
hardware colours. PROMT-ID-0098 had matched the dim `rgb8` instead of the live CRAM.

**Fix:** `_rom_boss_target_palette` (server) and `rom_boss_target_palette` (bestiary) now decode with
`_pal5`. Still 100% ROM-sourced — no RGB stored in the tool. `_pal4` removed.

## Verification

- `verify_0098_r1_boss_green_knight.py` **39/39 PASS**. R1 now checks the decode against the arcade's
  live CRAM (`final_live_words`, 16/16) plus a full-brightness assertion.
- `verify_0091_handoff.py` 25 PASS · `verify_0092_bestiary_artifact.py` 28 PASS.
- Files changed: `tools/graphics_editor/server.py`, `tools/graphics_optimizer/build_bestiary.py`,
  `tools/graphics_editor/verify_0098_r1_boss_green_knight.py`, `docs/design/rastan_actor_bestiary.html`.

## Bestiary artifact consolidation — ONE canonical artifact

There were two same-named "Rastan Bestiary" artifacts (same `build_bestiary.py` output). Resolved to a
single canonical one:

- **CANONICAL (keep):** `67b741cb-de98-4a0f-9674-9f3d790d6e60` —
  **https://claude.ai/artifact/Dopg3mwMHdUMsZJSQgXDVR** — most recent and complete; the corrected
  full-brightness build is published here.
- **RETIRED (superseded):** `5ba8edb9-fb8b-4ac9-9b0c-9639b666e948`
  (`https://claude.ai/artifact/CKUcQJpzhCoMAZ8fKMnVNF`) — a stale earlier copy. Not deleted (deletion
  needs Tighe's explicit per-artifact confirmation). Do not republish to it; all pointers use the
  canonical URL above.

**Double-click shortcuts to the canonical artifact** (in this folder):
`docs/design/Rastan Bestiary (live).url` (Windows) and `docs/design/OPEN_Rastan_Bestiary.html`
(any browser).

All future `build_bestiary.py` republishes go to the canonical slug `67b741cb`.

## Follow-up — Sprites-view "Derive Palette → Line N" (map the boss)

Tighe cleared Genesis Line 1 to hold the R1-S3 boss but the Sprites view had no one-click "derive a
palette onto a line" like Layer A's **Derive Scene Palette → Line N**; `Recommend Line` also reported
every line as "does not fit" when the line still held stale colours from a prior derive.

Added `deriveSpritePalette(line)` (frontend, `app.js`) and a **Derive Palette → Line {ACTIVE}** button in
the Sprites source action bar, next to *Auto-fill Object* / *Recommend Line*. It is the Sprites analog of
the Layer-A derive: it **owns the chosen editable line** for the selected object — clears entries 1–15,
fills them with the object's proven arcade colours (nearest legal CRAM, MRD-distinct via `nudgeDistinct`),
and maps **every** source index — all in one Undo. Because it owns the line, the stale-colour "does not
fit" case no longer blocks it. Respects Line-2 protection and `editableLines()`; disabled unless the active
line is editable.

For the R1 boss body this is a **clean 1:1 fit**: the 15 arcade colours map to 15 distinct Genesis CRAMs on
Line 1 (reds/golds preserved — e.g. `#C64221`→rgb(182,73,36), gold `#F7F742`→rgb(255,255,73)), so the
Genesis-target preview matches the arcade composite. The boss usage stays `authorable:False` (the tool never
*auto*-assigns a line); this derive is Tighe's explicit manual action, which that flag was always meant to
allow. `node --check app.js` passes. The composer serves `app.js` fresh per load, so a browser refresh picks
it up.

**Correction (same session, two defects Tighe hit on first use):**

1. *Swatches filled dark-grey / colours didn't land.* The first version wrote colours to the **base**
   `POL.target_palette_lines[line]`. But the editing scope is a **context** (R1-S3 BOSS-ROOM), and
   `effEntry` — which renders the Line swatches, the map-table *Target color* column, and the preview —
   overlays the base with context overrides. "Clear Line" leaves explicit **null** scope overrides at
   `context_policies[SCOPE].tpl[line][1..15]`, which masked the base writes → every swatch read empty. Fixed
   by writing at the active scope with `tplSetAt(SCOPE, line, i, cram)` (the same path the Layer-A derive and
   Clear Line use), clearing 1–15 to null first and then filling. Colours now display on Line 1 and in the map
   table; the preview was always correct (it resolves via `effCramAt`).

2. *Button label stale.* The **Derive Palette → Line N** label is built in `renderSource` from `ACTIVE`, but
   clicking a LINE label/swatch only re-rendered the target panel. Added `renderSource()` on active-line
   change (objects tab) in both the LINE-label and swatch `onclick`, so the button now tracks the selected
   line.
