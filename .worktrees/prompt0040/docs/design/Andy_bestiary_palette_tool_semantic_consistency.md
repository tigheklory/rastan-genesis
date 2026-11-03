# Andy — Bestiary / Palette Composer Source-of-Truth Consistency (Weapons + Cave Block + Burst)

**Agent:** Andy · Infrastructure / Tooling / Documentation Consistency. **NO ROM build. No assembly/runtime
change.** Andy performed no gameplay verification — authority: TIGHE. No H25.

> **Counter note:** the prompt states "380 → 380". The live counter is at **383** because Builds 0381–0383
> were produced (and preserved) in the immediately prior task this session (0383 canonical=PASS). This task
> produces no ROM, so the counter legitimately stays at **383** — I did not reset it to 380, because deleting
> or rewinding preserved build history is forbidden by the standing build-number imperative. The prompt's
> "380→380" intent (no build this task) is honored.

## 1. Phase 0
Read `PROMPT_TEMPLATE.md`, `RULES.md`, `ARCHITECTURE.md`, `CLAUDE.md`,
`PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`, then `KNOWN_FINDINGS.md` / `OPEN_ISSUES.md` /
`CLOSED_ISSUES.md` (ledgers known stale; priors only). Relevant priors: the H24 weapon-overlay evidence
(manifest `player_render_architecture.weapon_overlay`), H17 cave block, H16 burst effect, and the sprite
palette route (KF-043/046). **Classification: INFRASTRUCTURE** (tooling + generated documentation
consistency; no system-behavior investigation, no runtime/assembly/ROM change). No CONFIRMED/STRONG finding
contradicted. **KNOWN_FINDINGS impact: Option A — No new finding to index (INFRASTRUCTURE).**

## 2. Source-of-truth statement
The authoritative chain is DECOMPILATION / MANIFEST → { Bestiary, Palette Composer, offline graphics
compiler }. The Bestiary is decompilation/static-arcade-evidence driven — gameplay traces may corroborate
but are never identity authority. This task makes the Bestiary and Palette Composer consume the same proven
semantic/decompilation artifacts for the four equipped weapons, the destroyable cave block, and the burst
effect, with no separate hand-written identity lists in any of the three tools.

## 3. Weapons are static-decompilation derived (proof)
The four equipped weapons were established from the ORIGINAL ARCADE program, NOT Genesis gameplay traces:
selector `A5+0x12FA`, overlay producer `0x54598` (player body-composer tail), slot `A5+0x1244`; tables
SWORD `0x5CD8A` (sel 1), AXE `0x5D346` (sel 2), HAMMER `0x5D666` (sel 3), FIRE SWORD `0x5D068` (sel 4);
grant handlers (`player_weapon_grant_state2/3_*`, `player_fire_sword_grant_54ef2`), decoded PC090OJ piece
records, and raw arcade PC090OJ graphics. Authoritative artifacts:
`docs/design/rastan_actor_graphics_manifest.json` → `player_render_architecture.weapon_overlay.proven_identities`;
`analysis/actor_decompilation/h24_player_weapon_cells.tsv` / `h24_player_weapon_frames.tsv`;
`analysis/decompilation/h24_player_weapon_render_contract.json`. Rendering raw ROM cells for static
identification is not a gameplay trace.

## 4. Bestiary weapon integration (Parts 1–3)
`tools/graphics_optimizer/build_bestiary.py` — added `build_weapons_section()` and wired `{weapons_html}`
after the player section. The section is titled **"Player Equipment — Equipped Weapon Overlays"** (NOT enemy
actors, NOT the Unresolved gallery). It derives ALL identity/selector/table/producer/grant/proof text from
the manifest `weapon_overlay.proven_identities` and the representative arcade artwork from the generated
weapon-cell TSV, composited from arcade `pc090oj.bin` with the sprite palette (line 3). No hard-coded weapon
HTML cards; no gameplay-screenshot/trace arrays. Each card shows: semantic identity, selector, source table,
producer, genuine proven frame count, unique source cells, source-palette evidence, decompilation
provenance, and a representative composite. Badges: **OBJECT PROVEN · NAME PROVEN · FRAMES PROVEN · STATIC
DECOMPILED**. Verified in the generated HTML: the section and all four cards (Sword/Axe/Hammer/Fire Sword)
are present; the Unresolved gallery contains none of them.

## 5. Cave-block Composer integration (Part 4)
`tools/graphics_editor/server.py` — added the destroyable cave-entrance block as a first-class Composer
object `object:hazard.cave_block`, cells 0x0179–0x017C (2×2 composite), effective bank 0x3C, rendered via
the compositor VM from the manifest render spec (base 0x0179, anim 0x70, table 0) — decompilation-driven,
not a trace. Its `map_key` is the EXISTING `usage:cave_block:bank0x3C`, so the already-authored Test.json
mapping is reused (no duplicate key created; verified authored=True). Arcade source palette injected from the
ROM (R1 line 0xC pool, via `_arcade_round_palette(1,12)`) into a local banks copy (caller dict not mutated).
Display name "Cave Entrance Block".

## 6. Burst Composer integration (Parts 5–6)
Added the burst/impact effect as a Composer object `object:effect.burst` (EFFECT, not an enemy), base
0x0275, three proven forms exposed as frames sharing ONE palette identity: anim **0x9E (8 pieces) / 0x9F (9)
/ 0xA0 (10)** — piece counts match the manifest exactly. Rendered via the compositor VM from the manifest
render spec (base 0x0275, table 0), effective palette derived from decompiled compositor semantics
(compositor control nibble 0 → arcade R1 line 0 → bank 0x30, via `_arcade_round_palette(1,0)`) — **not
guessed from naming**. Test.json has no burst mapping, so it is shown **UNAUTHORED** (verified authored=False);
this task never authors, optimizes, or saves it — Tighe will map it before any future build. The three forms
share the single `map_key` `usage:burst:bank0x30` and are browsable via the existing frame browser
(Prev/current/Next/dropdown); the frontend gained `hazard`/`effect` category labels
(`tools/graphics_editor/app.js`).

## 7. Shared generated-data flow (Part 7)
No duplicate identity lists were introduced. Weapons: Bestiary + Composer + generator all read
`h24_player_weapon_cells.tsv` (+ manifest weapon_overlay) and apply the identical **frame-69 artefact
exclusion** (player-slot overrun; HAMMER frame 69 = blank 0x0003×3). The Composer weapon frame count is now
42 genuine frames (was 43), matching the Build-0383 generator and the Bestiary. Cave block + burst: Bestiary
and Composer both derive from the manifest render specs via the same compositor VM. A `frame69_artifact` note
was added to the manifest `weapon_overlay` so the identity authority documents the exclusion.

## 8. Test.json preservation (Part 8)
This task did **not** modify `analysis/graphics_optimizer/editor_policy/Test.json`. Proven mechanically: the
Composer only writes the profile through its interactive `do_POST` handler (never run here); my read-only
`build_usages`/`sprite_bank_colors` calls left the file mtime unchanged. Adding the Burst object to the UI
saves no mapping (UNAUTHORED); no optimizer/auto-fill was run.
**Observed (not caused by this task):** the live Test.json (SHA `7b8848c5…`) now differs from the frozen
Build-0381/0383 snapshot (`31dedf43…`) — `object:player.rastan` index 12 changed 0→5 and `context_policies`
changed, saved at 18:03 on 2026-09-28. This is Tighe's own Composer re-authoring between builds; the tools
correctly reflect the live profile. All existing authored choices (Rastan, the four weapons, enemies,
`cave_block`) remain present; the `cave_block` mapping is unchanged.

## 9. Verification
- Bestiary regenerated: `consistency_check: PASS`; "Player Equipment — Equipped Weapon Overlays" present with
  Sword/Axe/Hammer/Fire Sword (OBJECT/NAME/FRAMES PROVEN + STATIC DECOMPILED); cave block + burst still
  present; Unresolved gallery contains none of the six objects.
- Composer (`build_usages`): `object:hazard.cave_block` (1 usage, 4 pieces, bank 0x3C, authored=True, reuses
  `usage:cave_block:bank0x3C`); `object:effect.burst` (3 usages, 8/9/10 pieces, bank 0x30, authored=False =
  UNAUTHORED); weapons 42 frames each (frame-69 excluded); Rastan + all enemies still present.
- `node --check app.js` OK; `server.py` parses; manifest JSON valid.

## 10. No-ROM confirmation
No ROM produced; counter stays 383. No assembly/runtime/gameplay-source change (no `pc090oj_hooks.s`, no
sprite residency, no selector). Files changed this task: `tools/graphics_optimizer/build_bestiary.py`,
`tools/graphics_editor/server.py`, `tools/graphics_editor/app.js`,
`docs/design/rastan_actor_graphics_manifest.json` (frame-69 note + earlier player_composer key),
`docs/design/rastan_actor_bestiary.html` (regenerated). Architecture compliance CONFIRMED (offline
tooling/docs only; no chip mirror/emulation; arcade owns execution).

## 11. Open/Closed Issues Impact
OPEN-006 context only (weapons/cave/burst now consistently surfaced across Bestiary + Composer; burst awaits
Tighe authoring). No issues opened/closed/deferred by this infrastructure pass.

## 12. KNOWN_FINDINGS impact
Option A — No new finding to index (INFRASTRUCTURE classification).
