# Andy — Bestiary Stale-Claim Repair (PROMT-ID-0092)

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0092`

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0092 Result

Narrow consistency-repair of the **generated Bestiary artifact**
(`docs/design/rastan_actor_bestiary.html`) and the authoritative sources that generate it. The
PROMT-ID-0091 model corrections were substantially right, but the generated artifact still rendered
stale prose that directly contradicted Cody PROMT-ID-0090 and the 0091 report. All such CURRENT
claims were traced to their generator/data source, corrected there (never by hand-editing only the
HTML), the artifact was regenerated, and a new verifier now reads the final HTML and fails on the
prohibited claims.

- Scope kept narrow: **no source re-investigation, no Genesis production code, no ROM build, no
  build-counter change, `Test.json` byte-for-byte unchanged, no GitHub push.**
- Baseline: HEAD `b8433f59` (Andy 0091); Cody 0090 `686767ff` present in history; only the two
  unrelated runtime-output files were already modified and were left unstaged.

## 0091 Acceptance Failure

0091's new verifier (`verify_0091_handoff.py`) re-derived facts from the compositor VM and the live
`/api/oracle` **objects** and passed — while the generated HTML a human actually reads still
contained the old model. The verification gap: nothing asserted against the rendered artifact. Two
authoritative data sources were never swept:

1. `docs/design/rastan_actor_graphics_manifest.json` — the Bestiary's `dashboard`,
   `architecture_status`, per-boss `description`/`render.note`, R6 `boss_component_palette`, and the
   `items_system` detail still carried the obsolete reward three-bank model and the disproven
   boss-RGB-from-field-pool wording.
2. `analysis/actor_decompilation/h25_death_and_effect_families.tsv` — the `item_drop_death` row
   still carried `0x30/0x31/0x37` banks and the three removed Composer objects.

## Stale Reward Claims Found

Obsolete `$30/$31/$37` three-bank reward claims rendered CURRENT in the artifact, by source entry:

| # | Source | Field |
|---|---|---|
| 1 | manifest `dashboard` | "Gameplay item / reward system" cell — `banks 0x30 (1-4) / 0x31 (5-13) / 0x37 (14-17)` |
| 2 | manifest `dashboard` | "Gameplay reward kinds" cell — `banks 0x30/0x31/0x37` |
| 3 | manifest `architecture_status.still_open` | reward bullet — `banks 0x30/0x31/0x37` |
| 4 | manifest `items_system…detail` | `banks 0x30 (kinds 1-4)…` + removed objects `object:effect.item_drop_death`, `object:item.gameplay_reward_b31`, `object:item.gameplay_reward_b37` |
| 5 | H25 TSV `item_drop_death` row | `effective_bank` = `0x30 (kinds 1-4) / 0x31 (5-13) / 0x37 (14-17)`; `composer_key` = the three removed objects; `palette_status` = "banks per kind" |

Count of distinct stale-source reward entries found: **5**. Remaining after repair: **0**.

## Reward Dashboard Repair

Every CURRENT reward statement now describes the Cody-0090 / Andy-0091 source model and separates
source semantics from production integration:

- **Source graphics/palette semantics:** family 12, base `$0A5A`, **compositor selector 2**, anim
  `$13..$23`, codes `$A5A-$A71`, **embedded palette line 0 for kinds 1-13 / line 3 for kinds
  14-17**, `+$27` override clear; one authentic tile per kind; identity `0x40C2E`, score `0x40C40`.
- **Production integration:** explicitly **not yet integrated** into the Genesis offline
  reindex/scene routing — a Cody follow-up (`SOURCE/TOOL READY ≠ PRODUCTION INTEGRATED`).
- The H25 taxonomy card ("Item-drop death / visible gameplay reward pickup (family-12)") now shows
  the `object:item.gameplay_rewards` parent + 17 `object:item.reward.kind01..kind17` children, with
  no bank labels.

No old effective-bank label is conflated with the source palette line.

## Stale Boss Palette Claims Found

Claims that presented the ordinary field pool as the authoritative boss palette, or claimed the boss
RGB was verified:

| # | Source | Text |
|---|---|---|
| 1 | manifest `dashboard` | "Boss clean legal frames" — `palette line F = 0x3BA88[round][15] … colours per pool` |
| 2 | manifest `dashboard` | "Per-round palettes" — `boss line F = 0x3BA88[round][15] proven` |
| 3 | manifest R1 boss `description` | `Render/palette Cody-verified (prog 0x47908, line 0xF pool 11)` |
| 4 | manifest R5 boss `description` | `Render/palette Cody-verified (prog 0x490DE, line 0xF pool 3)` |
| 5 | manifest R1+R5 `render.note` | `Cody MAME-verified body frame+palette` |
| 6 | manifest R6 `boss_component_palette` | `…share the same ROM colours (0x4FE62)` |
| 7 | manifest `architecture_status._note` | `R1/R5 render+palette are Cody-verified` |
| 8 | generator `boss_card()` | provtag `…palette · MAME-verified (Cody)`; palbank `boss line F source = 0x3BA88[round][15] → 0x4FD02 … exact colours per pool`; bar badge `PALETTE line F = 0x3BA88[round][15] proven` |

## Boss Palette Provenance Repair

The artifact now states, for the boss, the proven/pending split honestly and consistently:

**PROVEN** — compositor control selects line F; Round-1 boss body geometry/program (`$061D`,
compositor 1, anim `$00`, program `0x47908`); Round-1 boss scene ownership (R1-S3).

**PARTIAL / PENDING** — exact staged live RGB contents of line F. The field pool
`0x3BA88[round][15] → 0x4FD02` is explicitly labelled **DISPROVEN as boss colours** (R3 field pool 2
= teal vs arcade purple); the real colours come via the master sprite-palette staging
(`0x4EAF6 → 0x200000 → A5+0x1600`), layout not yet resolved.

The boss card image is rendered **neutral/gray** (no invented colours); the card carries no
field-pool swatch. The provtag, palbank, and bar badge all now read as line-F **selection** proven,
**RGB PENDING**. No disproven RGB source is called "MAME-verified palette" anywhere.

## Six-Boss Audit

The dashboard previously generalized `boss line F = 0x3BA88[round][15]` across all bosses. Each boss
card is now independently honest and does not generalize a field-pool rule from the line number:

- **Body identity:** per-round body bases proven (`0x061D/0753/082C/07BF/0988/0B35`).
- **Frame status:** R1/R5 Cody-verified frame; R2/R3/R4/R6 static.
- **Line-selection status:** compositor line-F selection proven (all).
- **RGB-source status:** field pool DISPROVEN as boss colours; exact staged RGB PENDING (all).

Every boss card (12 rendered boss cards, bodies + verified-render variants) carries the
`LINE-F SELECT PROVEN · RGB PENDING` badge — the artifact verifier asserts badge count == boss-card
count. Count of stale generalized `0x3BA88[round][15] = authoritative boss RGB` claims remaining:
**0**.

## Green Knight / Rope Audit

- Green Sword Knight statusbox: **23 programs / 97 pattern codes**; the old `29/109` claim appears
  only inside the removal sentence (no CURRENT `29 programs` / `109 codes` claim).
- Family-8 **Rope Climber** is a separate object `object:castle.rope_climber.family8.r1`
  (base `0x0241`, state `$11`, programs `$56,$59,$5A`; human identity Tighe-visual/PARTIAL).
- `$4D → base $0234`, `$57/$58 → base $01FC` shown as research-only producers; no rope program is
  attributed to `$033E`.

## Hazard Audit

- R1-S2 hazards are **not** misidentified as `$0224` or `$09EA`. The proven PROMPT-0086 identities
  (`0x0224` = pit flame in R2/R4; `0x09EA` = spike/spear/stalagmite in R5) remain in their proven
  scenes, unchanged.
- The R1-S2 hazard candidate groups carry `SOURCE SUBSET PENDING` and are not presented as
  authoritative/authorable. (This task did not alter hazard identity; it only confirmed the
  artifact's hazard prose is honest.)

## Generated Artifact Verifier

New: `tools/graphics_editor/verify_0092_bestiary_artifact.py`. It reads the **final regenerated
HTML** (not Python/server objects) and:

- **fails** on prohibited CURRENT phrases — `banks 0x30/0x31/0x37`, `banks 0x30 (1-4)`,
  `0x30 (kinds 1-4)`, `29 programs`, `109 codes`, `line F = 0x3BA88`, `colours per pool`,
  `MAME-verified body frame+palette`, `Render/palette Cody-verified`, and the removed reward
  Composer objects;
- **requires** the positive replacements — `23 programs / 97 pattern codes`; the family-8 rope
  object + `0x0241`/`$56,$59,$5A`; `compositor 2` + 17 kinds/children + lines 0/3; boss `0x47908` +
  `LINE-F SELECT PROVEN · RGB PENDING` + `staged boss RGB PENDING`; `SOURCE SUBSET PENDING`;
- asserts every boss card carries the honest line-vs-RGB badge (badges == boss cards, ≥6).

Result: **BESTIARY ARTIFACT 0092 PASS (pass=28, 0 failed).**

## Final Forbidden-Phrase Scan

Final scan of the regenerated HTML: every prohibited CURRENT phrase = **0**. Remaining Section-8
needles classified:

- `pool 11` (3×): all **materialized/field** DISPLAY-palette labels (H15 `+0x27=0`), none in a boss
  context — benign (for those actors the field pool IS the proven palette).
- `palette Cody-verified` (Chimera field enemy): benign — field per-round palette is genuinely
  ROM-proven; not a boss, not geometry-only.
- `$033E` as a rope program: **0**. `0x3BA88[round][15]`: **0**.

Affected existing verifiers re-run green: `verify_0091_handoff` (25), `verify_green_knight` (31),
`verify_death_item_families` (15/15), `verify_r1s2_castle_browser` (15); generator
`consistency_check: PASS`.

## Test.json Integrity

- Before: `e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730`
- After:  `e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730`
- Unchanged: **YES.** No authored palette data was touched to repair prose.

## Files / Local Commit / Logs

Changed (tracked):

- `docs/design/rastan_actor_graphics_manifest.json` — dashboard, architecture_status, per-boss
  description/render.note, R6 component palette, items_system reward detail corrected.
- `analysis/actor_decompilation/h25_death_and_effect_families.tsv` — `item_drop_death` row reward
  model corrected (compositor 2 / embedded line 0,3; parent+17-children Composer objects).
- `tools/graphics_optimizer/build_bestiary.py` — `boss_card()` provtag/palbank/bar-badge honesty.
- `docs/design/rastan_actor_bestiary.html` — regenerated (consistency_check PASS; actors=38).
- `tools/graphics_editor/verify_0092_bestiary_artifact.py` — new generated-artifact verifier.

Not touched: Genesis production source, palette packaging, scene selector, ROM-consumed sprite
products, build counter, ROM artifacts, audio, `specs/palette_decisions.json`, `Test.json`. The two
unrelated runtime-output files (`build/mame/home/rastanmon/rastan_monitor.log`,
`tools/mame/cheat/output.json`) were left modified and **unstaged**. Local commit only; **no GitHub
push**.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0092`
