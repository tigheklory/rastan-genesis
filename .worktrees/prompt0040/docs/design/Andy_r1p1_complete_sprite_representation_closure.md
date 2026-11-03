# Andy — R1/P1 Complete Sprite Representation Closure (Weapons + Complete Enemy Corpus + (code,bank))

**Agent:** Andy · Static RE / Infrastructure / Tooling. **NO ROM build. Counter 380 → 380. No H25.**
**Andy performed NO gameplay verification — Tighe owns all gameplay/visual acceptance.**
Resumed after a session limit; prior partial work recovered and continued (not restarted).

## 1. Phase 0
Read KNOWN_FINDINGS / OPEN_ISSUES / CLOSED_ISSUES (known-stale; recorded facts used as priors, current
state from AGENTS_LOG + September design docs + live artifacts). Relevant priors: KF-043 (player sprite
palette bank 51 → CRAM line 3), KF-044 (player composer blocks), Build-0327 (incomplete enemy reindex
coverage + cross-bank shared codes). Classification: **EXTENDING** (static RE + infrastructure). No
CONFIRMED/STRONG finding contradicted. KNOWN_FINDINGS impact: **Option A — no new finding to index**
(recomputes/extends the already-recorded Build-0327 mechanism; the weapon identities are new durable
facts but are captured in the manifest + generated artifacts rather than KNOWN_FINDINGS per the stale-
ledger guidance — flagged for future curation).

## 2. Resume-state inventory
Recovered from the interrupted session (all valid, retained): weapon identity RE + artifacts
(`h24_player_weapon_cells.tsv`, `h24_player_weapon_frames.tsv`, `h24_player_weapon_render_contract.json`),
manifest weapon evidence, the 4 weapon objects in the Composer (`server.py` `h24_weapon_frames`),
coverage matrix v1. Outstanding at resume (completed here): complete enemy corpus, complete
(code,bank) collision analysis, complete enemy browsing in the Composer, coverage matrix v2, this
design doc, the AGENTS_LOG entry, Line-0/1 pressure.

## 3. Build-0380 user result
Rastan **body palette USER ACCEPTED**. Not reopened/modified. Remaining wrong: the 4 equipped weapons
and enemies (Flying Demon, both bats, and frame-dependent partial correctness on others) — consistent
with the proven incomplete enemy reindex coverage.

## 4. Accepted Rastan preservation
`object:player.rastan`, 75 torso / 52 leg / 60 pairings, complete H24 reindex — **unchanged**. No
change to Rastan mapping, colors, or Test.json Rastan entries.

## 5. Historical enemy-coverage prior (Build 0327)
Reindex was based on representative/base-pose code sets; animation cells outside them stayed raw →
wrong colors; some codes occur under multiple effective banks → a flat `code → one cell` model is
insufficient. Numbers recomputed below (they match the historical totals).

## 6. Complete enemy census (authoritative)
From `sprite_census_captured.json` → `r1p1_enemy_semantic_corpus.tsv` (666 cell rows). Complete unique
codes / effective bank: **Chimera 148 (0x34), Flying Demon 112 (0x35, two components), Four-Armed
Insect 106 (0x3A), Lizardman 91 (0x36), Valkyrie 18 (0x32), Large Bat 14 (0x3E), Small Bat 3 (0x3E)**.

## 7. Cross-bank collision table (COMPLETE corpus)
**48 codes collide** — the shared **0x0A73 anim block** (codes 0x0A73..~0x0AA2) appears under banks
**0x34 / 0x36 / 0x3A** for **chimera / four_armed_insect / lizardman**. Decisive: their authored
index_maps DIFFER (chimera `2→6`, lizardman `2→2`, four_armed `2→14`) and target different lines (0 vs
1). Also **0x0275** occurs under 0x35 (Flying Demon) and 0x3E (Large Bat). Therefore a single
code-indexed transformed cell **cannot** satisfy all consumers — the (code,bank) byte-variant
architecture is genuinely required (this is different from Rastan, where complete code coverage alone
sufficed because Rastan's cells are single-bank/single-map).

## 8. (code,bank) representation architecture — status + design
- **Current runtime:** already has a `(scene, effective_bank) → palette-LINE` LUT
  (`pc090oj_palsel_lut.inc`), so the runtime knows each sprite's effective bank and picks the CRAM
  line. It does **not** select a pixel-VARIANT — the reindexed asset is code-indexed (one cell/code).
- **Current generator:** `gen_reindexed_pc090oj.py` is code-indexed and documents "zero cross-bank
  collisions" — TRUE for the representative corpus, FALSE for the complete corpus (48 collisions).
- **Required (spec for the next build task):** offline generate a distinct 128-byte variant per
  `(code, effective bank)` where authored maps differ, plus a `(code,bank) → variant offset` index;
  extend the runtime sprite-upload path to select the variant offset from the effective bank it already
  resolves (bounded O(1), no pixel transform, no PC090OJ emulation). Cell model preserved (code*128, 4
  subtiles, index 0 transparent).
- **Why not implemented in this task:** it is a native-runtime change that **requires a ROM build to
  validate**, and this task is explicitly NO BUILD. Changing the production asset format without a
  validated runtime would leave the tree unbuildable. So the offline+runtime (code,bank) implementation
  is scoped to the next build task; the **data foundation (complete corpus + collision table + differing
  maps) is proven and ready**, and the Composer authoring (below) is the prerequisite Tighe must
  complete first.

## 9–12. Equipped-weapon RE (PROVEN) + corpus
Weapons are a separate PC090OJ overlay appended by the body-composer tail **0x54598**, indexed by the
same frame slot A5+0x1244, table chosen by selector **A5+0x12FA**; SAT staging 0x10D1B2.

| Weapon | selector | table | producer/grant | frames | cells | identity proof |
|---|---|---|---|---|---|---|
| **SWORD** | 1 | 0x5CD8A | respawn 0x504B6 / default | 43 | 13 | base/default weapon (respawn writes 1) |
| **AXE** | 2 | 0x5D346 | `player_weapon_grant_state2_54edc` | 43 | 15 | shaft+head cells; elimination vs hammer |
| **HAMMER** | 3 | 0x5D666 | `player_weapon_grant_state3_54ec6` | 43 | 18 | **ball-and-chain** — cells 0x491–0x49d render as round balls on chains (decisive) |
| **FIRE SWORD** | 4 | 0x5D068 | `player_fire_sword_grant_54ef2` (named) | 43 | 13 | named grant handler; flaming-blade cells |
Do NOT assume table order = weapon order; the mapping was proven from grant-handler names + rendered
shape, NOT from table order or Genesis appearance. Artifacts: `h24_player_weapon_cells.tsv`,
`h24_player_weapon_frames.tsv`, `h24_player_weapon_render_contract.json`. Each weapon is a distinct
palette object (`object:weapon.<name>`) in the sprite palette space — NOT tied to `object:player.rastan`.

## 13. Palette Composer implementation
- **Rastan** complete browsing preserved (Build-0380 accepted mapping untouched).
- **4 weapons** added as first-class authorable objects (`object:weapon.{sword,axe,hammer,fire_sword}`),
  43 frames each, browsable, rendered from arcade pc090oj.bin — NOT YET AUTHORED (Tighe authors).
- **7 enemies** now each expose a **complete-corpus** usage (all census cells → full source palette) in
  addition to the representative composite, sharing the enemy's existing `usage:<name>:bank0x<bank>`
  mapping key — so authoring once covers the entire animation vocabulary and the existing Test.json
  enemy mappings load unchanged. Frame browser (category selector + Prev/current/Next + dropdown) drives
  both panes.
- Shared Genesis target impact is visible via the existing same-line source listing.

## 14. Generator / verifier
- Generator (`gen_reindexed_pc090oj.py`): Rastan is complete (Build 0380). Enemies remain the
  representative corpus — extending them to the complete corpus REQUIRES the (code,bank) variant support
  (§8), which is build-requiring, so it is **not** changed in this no-build task (feeding the complete
  corpus to the current code-indexed generator would trip its collision guard).
- Verifier (`verify_reindexed_pc090oj.py`): unchanged and still PASS for the current authored set; the
  per-(code,bank) assertions are part of the scoped build task.

## 15. Current coverage matrix
`analysis/actor_decompilation/r1p1_sprite_coverage_matrix.tsv`:

| Object | Frames | Codes | (code,bank) variants | Composer | Authored | Generated | Missing | Status |
|---|---|---|---|---|---|---|---|---|
| Rastan | 135 | 344 | 344 | 187 | YES | 344 | 0 | COMPLETE (Build 0380, ACCEPTED) |
| Sword | 43 | 13 | 13 | 43 | no | 0 | 13 | in Composer, not yet authored |
| Axe | 43 | 15 | 15 | 43 | no | 0 | 15 | in Composer, not yet authored |
| Hammer | 43 | 18 | 18 | 43 | no | 0 | 18 | in Composer, not yet authored |
| Fire Sword | 43 | 13 | 13 | 43 | no | 0 | 13 | in Composer, not yet authored |
| Lizardman | complete | 91 | 91 | 91 | YES | 35 | 56 | complete corpus in Composer; gen representative |
| Valkyrie | complete | 18 | 18 | 18 | YES | 8 | 10 | " |
| Four-Armed Insect | complete | 106 | 106 | 106 | YES | 10 | 96 | " |
| Chimera | complete | 148 | 148 | 148 | YES | 11 | 137 | " |
| Flying Demon | complete | 112 | 112 | 112 | YES | 26 | 86 | " (two components) |
| Small Bat | complete | 3 | 3 | 3 | YES | 1 | 2 | " |
| Large Bat | complete | 14 | 14 | 14 | YES | 4 | 10 | " |

## 16. Line-0/1 pressure (CAPACITY CONFLICT — Tighe decides)
Both sprite lines are already **15/15 full** with current partial authoring:
- **Line 0 (full):** rastan + chimera + valkyrie + small_bat + large_bat share all 15 entries.
- **Line 1 (full):** flying_demon + four_armed_insect + lizardman share all 15 entries.
The complete corpora expose more distinct source colors than the partial authoring did, so fitting
every complete enemy palette into the 2×15 shared budget will likely require **merging colors** or
splitting objects across lines. **No auto-merge was performed.** This is an authoring decision for
Tighe (Task M/capacity rule): the Composer now surfaces the complete color demand and the shared-entry
impact so he can decide the compromises before the next build.

## 17. Unresolved authoring conflicts
- Weapon mappings: NOT YET AUTHORED (correctly, not invented).
- Enemy complete-corpus colors vs the full 2×15 line budget: capacity conflict for Tighe.
- Weapon source-palette line: weapons render in the sprite palette space (bank 0x33 basis in the tool);
  the exact per-weapon effective line is confirmed during authoring — flagged, not guessed.

## 18. Files changed
- Created: `analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv`,
  `.../r1p1_sprite_coverage_matrix.tsv`, weapon TSVs + render contract (prior session), this doc.
- `tools/graphics_editor/server.py` — `h24_weapon_frames`, `enemy_complete_usages`, wired into
  `build_usages` (weapons + complete enemy corpora, shared map_keys).
- `tools/graphics_editor/app.js` — weapon/complete category labels in the frame browser.
- `docs/design/rastan_actor_graphics_manifest.json` — weapon identities + enemy corpus references.
- `tools/graphics_editor/gen_reindexed_pc090oj.py` / `verify_reindexed_pc090oj.py` — unchanged this
  task (Rastan-complete from Build 0380; enemy (code,bank) work is build-scoped).

## 19. No-ROM confirmation
No ROM produced. Counter 380 → 380. Build 0381 NOT consumed. `make release` not run.

## 20. Architecture compliance
CONFIRMED. Offline authoring/analysis + Composer tooling only. No Genesis game loop / frame authority /
boot re-entry; no runtime palette solving; no runtime pixel/nibble recoloring; no PC090OJ emulation or
object-RAM mirror; no scaffolding. Semantic cut retained; PC090OJ-specific tail remains retired;
transitional compatibility added: NONE.

## 21. USER MUST VERIFY
Tighe opens the completed Palette Composer, inspects/authors the 4 equipped weapons and the complete
enemy corpora (resolving the Line-0/1 capacity conflict), and saves. Only then is the next build
(implementing the (code,bank) offline+runtime pipeline) requested. Andy makes no gameplay/visual claim.

## 22. Open/Closed Issues Impact
OPEN-006 (sprite/high-bank palette mapping) advanced (complete corpus + weapon identities + (code,bank)
requirement proven); not closed. New issues: the (code,bank) offline+runtime pipeline is the concrete
next build-requiring work item. None closed/deferred.

## 23. KNOWN_FINDINGS impact
Option A — No new finding to index (EXTENDING; recomputes the recorded Build-0327 mechanism and adds
weapon identities to the manifest/artifacts rather than the stale ledger).
