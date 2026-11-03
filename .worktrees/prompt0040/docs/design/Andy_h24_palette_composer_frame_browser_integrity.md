# Andy — H24 Palette Composer Frame Browser Integrity

**Agent:** Andy · INFRASTRUCTURE (Palette Composer tooling/UI + authoritative-data consumption).
**No ROM build. Runtime counter 378 → 378. No runtime architecture change. No H25.**

## Phase 0
Read KNOWN_FINDINGS.md (full), OPEN_ISSUES.md, CLOSED_ISSUES.md before task-specific inspection.
- **Relevant priors:** KF-043 (arcade sprite palette bank 51 → Genesis CRAM line 3 — the player/sprite
  palette source), KF-044 (player PC090OJ composer source blocks 0x10D1B2 base + record offsets
  0x10D1D2 upper / 0x10D1F2 lower — consistent with the two-composer H24 architecture). Both are
  consistent with the H24 player findings; nothing contradicted. *(Note: the user flagged that
  KNOWN_FINDINGS.md is stale; these two entries still match the current static evidence, so they were
  used only as light corroboration, not authority. Authority = the arcade ROM tables + generated H24
  artifacts + the actual tool code.)*
- **Rediscovery-hazard HIGH touched:** none of the boot/watchdog HIGH entries apply.
- **Task classification:** INFRASTRUCTURE.
- **Open/Closed issues touched:** OPEN-006 (sprite/high-bank palette mapping) is *supported* by this
  tool (better visual validation of the player line-3 mapping) but not modified or closed.
- **Contradiction of a CONFIRMED/STRONG finding:** NONE.
- **KNOWN_FINDINGS impact:** Option A — no new finding to index (tooling/data-consumption change).

## Problem
The running Palette Composer v0.4 showed the Rastan Body object with an ambiguous "N frames" badge and
only one visible pose; there was no way to browse the complete H24 player frame inventory. A prior pass
had added synthetic usages (idle / up-thrust / COMPLETE aggregate); the COMPLETE aggregate proves
palette-colour coverage but is not a selectable visual frame browser.

## Old implementation
`tools/graphics_editor/server.py` built three player usages (idle, up-thrust, complete). The objects
tab (`app.js`) grouped usages by `object_id` and rendered a small per-rep mini-button strip, but the
palette mapping was keyed per `usage_id`, so switching reps would have shown a different mapping. The
60 valid full-body pairings existed only as hard-coded logic inside `build_bestiary.py`.

## Authoritative H24 source inputs (consumed, not hand-listed)
- `analysis/actor_decompilation/h24_player_frame_cells.tsv` — 75 torso frames (0x5BD40).
- `analysis/actor_decompilation/h24_player_leg_cells.tsv` — 52 leg frames (0x5C466; slot 34 blank).
- `analysis/actor_decompilation/h24_player_frame_reference_map.tsv` — torso positive provenance.
- `analysis/actor_decompilation/h24_player_fullbody_pairings.tsv` — **NEW** generated artifact of the
  60 valid pairings, produced by `tools/analysis/gen_player_fullbody_pairings.py` and consumed by BOTH
  the Composer and the Bestiary (build_bestiary.py now reads it instead of its inline derivation).
- `analysis/decompilation/h24_player_render_contract.json` — two-half render contract (referenced).

## Durable data-flow design
`server.h24_player_frames()` reads the four TSVs and emits browsable reps for ONE Rastan object:
60 full-body pairings + 75 torso + 51 non-blank leg frames, each carrying `frame_category`
(fullbody / torso / legs), a `frame_label`, a `frame_order`, and a shared **`map_key =
object:player.rastan`**. One internal diagnostic aggregate (category `diagnostic`) carries the union of
every player cell so a single mapping provably covers the whole vocabulary — it is labelled a
diagnostic, not a game pose. Enemies keep `map_key == usage_id`.

## UI design (`app.js` + `style.css`)
- Palette mapping keyed by `MK(u) = u.map_key || u.usage_id` everywhere (read, write, preview, MRD,
  solver apply, reverse lookups). All Rastan frames therefore share ONE mapping; selecting a frame
  changes only the previewed artwork.
- New **frame browser** (`renderFrameBrowser`) under the selected object: category selector
  (`Valid Full-Body Pairings (60)` · `Torso Frames (75)` · `Leg Frames (51)` · `Palette Coverage
  (diagnostic)`), `◀ Prev  n/total  Next ▶`, and an exact-selection dropdown. Selecting any control
  calls `selectUsage`, which re-renders both the TRUE ARCADE COMPOSITE and GENESIS TARGET panes.
- The ambiguous "N frames" badge is replaced for Rastan by `60 pairs · 75 torso · 52 legs`.
- Group checkbox adds one representative per object (frames share the mapping).

## Exact files modified
- `tools/analysis/gen_player_fullbody_pairings.py` — **created** (authoritative pairings artifact).
- `analysis/actor_decompilation/h24_player_fullbody_pairings.tsv` — **generated** (60 rows).
- `tools/graphics_editor/server.py` — `h24_player_frames()` rewritten (categorized browsable reps,
  shared `map_key`); usage dict carries `map_key`/`frame_category`/`frame_label`/`frame_order`/
  `player_counts`.
- `tools/graphics_editor/app.js` — `MK`/`usageByMapKey`, `renderFrameBrowser`, mapping sites keyed by
  `MK`, badge fix, group-checkbox one-rep.
- `tools/graphics_editor/style.css` — frame-browser styles.
- `tools/graphics_optimizer/build_bestiary.py` — reads the shared pairings artifact.

## Verification
Server started on 127.0.0.1:8099; `/api/oracle` returns 187 Rastan reps (60 fullbody / 75 torso /
51 legs / 1 diagnostic), all sharing one `map_key`. `/api/render` renders full-body (34×66), torso
(34×34) and leg frames distinctly. Evidence montage `tools/graphics_editor/_frame_browser_evidence.png`
shows Full Body 00, Full Body 30, Torso 12, Legs 05, and Full Body 00 + Full Body 30 under the SAME
shared mapping (skin→green, red→cyan) — the mapping applies identically across different frames.
Regression: all six named enemies still build with `n_used>0` and render. `node --check app.js` and
`py_compile server.py` pass. Game-wide coverage guard PASS; fidelity guard PASS; bestiary regenerates
60 pairings from the shared artifact.

## Source-of-truth treatment
The 60 pairings are now a generated artifact consumed by both tools; neither hard-codes the list. The
Composer consumes the H24 TSVs directly (no hand-written frame list).

## Manifest consistency result
`rastan_actor_graphics_manifest.json` `player_render_architecture` already documents BOTH tracks
(upper A5+0x1244→0x54492→0x5BD40, lower A5+0x1246→0x546A8→0x5C466) and the separate weapon overlay
(0x5CD8A/0x5D068/0x5D346/0x5D666). No stale single-composer authority key exists.

## Architecture compliance
CONFIRMED. Offline tooling only. No Genesis control-flow ownership, no boot/init re-entry, no runtime
lifecycle, no ROM scaffolding, no software PC090OJ device or runtime mirror/shadow.
- Semantic cut: UNCHANGED (no runtime cut modified).
- PC090OJ chip-specific tail: UNCHANGED (no retired runtime tail restored).
- Transitional compatibility: NONE added.

## Open/Closed Issues Impact
- Open issues touched: OPEN-006 (supported, not modified/closed).
- New issues opened: none. Issues closed: none. Deferred: none.

## KNOWN_FINDINGS impact
Option A — No new finding to index (INFRASTRUCTURE tooling/data-consumption change).
