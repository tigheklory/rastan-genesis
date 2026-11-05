TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0091

# Andy — Palette Composer / Bestiary Implementation of Cody PROMT-ID-0090

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0091 Result

Implemented Cody PROMPT-ID-0090's source/runtime findings in the **Palette Composer** and **Bestiary** so
they accurately represent the game to a human user. All corrections are source-model + tooling + UI; **no
Genesis production code, no ROM, no build-counter change, no `specs/palette_decisions.json` change, and
`Test.json` is byte-for-byte unchanged.** No GitHub push.

Headline corrections (all independently verified):

- Green Sword Knight domain corrected **29 programs / 109 codes → 23 programs / 97 codes**; the six foreign
  programs `$4D,$56-$5A` are removed from base `$033E`.
- The family-8 **Rope Climber** (base `$0241`, programs `$56,$59,$5A`) is split out as a separate object.
- The 17 gameplay rewards are modeled as **one parent + 17 individual children**, compositor 2, embedded
  line 0 (kinds 1-13) / line 3 (kinds 14-17); the false three-bank (`$30/$31/$37`) model is removed.
- The R1-S2 hazards are shown as **disabled Plane-A candidates (SOURCE SUBSET PENDING)** — explicitly not
  `$0224`/`$09EA`; `$0224` (R2/R4) and `$09EA` (R5) are preserved in their proven scenes.
- The **Round 1 boss** is a scene-local R1-S3 group (body / type-15 aux / death), line F proven, RGB pending.
- UI gains Round→Sub-Round nav metadata, an Authoring/Research split, mapping-scope + human-identity badges,
  a per-scene CRAM line-ownership panel, the backdrop BLACK invariant, and the R1-S3 conditional Line-2.

## Repository Baseline

- HEAD at start and at report time: `686767ff53e35c085050631aa7b1a11e67a2bbee` ("Document Build 539 R1S2
  R1S3 asset audit") — this is the expected Cody PROMPT-ID-0090 handoff commit; HEAD has not moved beyond it.
- No reset/rebase/clean. The only pre-existing working-tree modifications were two unrelated runtime-output
  files (`build/mame/home/rastanmon/rastan_monitor.log`, `tools/mame/cheat/output.json`); they were not read
  as authority, staged, or reverted.
- `Test.json` SHA-256 before and after: `e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730`
  (Cody 0090 value, unchanged).

## Cody 0090 Handoff Consumed

Read in full:
`docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0090_r1s2_r1s3_asset_palette_ui_handoff.md`.
Its source-backed object census, `$4D/$56-$5A` re-audit, reward path, boss tables, and UI handoff were
treated as the implementation specification. Where it conflicts with PROMPT-ID-0078/0080/0084, older Bestiary
labels, and the old Composer hardcoded groups, Cody's findings win; historical reports are left historical.

## Green Sword Knight Correction

`gen_reindexed_pc090oj.py::GREEN_KNIGHT_ANIMS` is now the 23-program set
`$93-$96, $71-$73, $20-$23, $97-$9C, $A1-$A6`. The server model (`green_knight_usages`,
`KNIGHT_ANIM_STATE`, `POSE_LABEL`, comments) drops the `rope` group. Independently re-derived via the
compositor VM: **23 programs → 97 distinct pattern codes**, and the complete moving-weapon sword artwork
`26B-274` is still covered. Canonical object `object:castle.green_sword_knight.r1.n3`. The two-layer palette
provenance (embedded defaults + actor `+$27` override) is preserved; the stale `rope_shared_sheet` default
line was removed. `verify_green_knight.py` and `verify_reindexed_pc090oj.py` updated to assert 23/97 and
foreign-program non-contamination. `pc090oj_editor.bin` is an untracked build product; regenerating it to the
23/97 domain is the Cody production follow-up (Section 41 #4).

## Family-8 Rope Climber

New `rope_climber_usages()` emits `object:castle.rope_climber.family8.r1`: base `$0241`, family 8, state
`$11`, programs `$56,$59,$5A` (comp 0), R1-S2 scene usage, per-piece arcade palettes, independent mapping
(the `$033E` mapping does not apply). Human identity is shown **PARTIAL / Tighe-visual** ("Rope Climber");
technical identity is PROVEN. Its generated production coverage is a Cody follow-up.

## `$4D/$56-$5A` Reclassification

Per Cody: `$4D`→base `$0234`; `$56`→base `$0241` (fam 8); `$57`/`$58`→base `$01FC`; `$59`/`$5A`→base `$0241`
(fam 8) or `$0546` by writer. None is the family-2 `$033E` knight. `$56,$59,$5A` live in the rope-climber
object; `$4D,$57,$58` are research-view producers (the normalizer tags raw producer / controller object ids
`view=research`, hidden from Authoring). `(base, program)` identity is preserved; a program number is not a
global sprite identity.

## Reward Model Correction

`gameplay_reward_usages()` replaces the three false bank objects (`object:effect.item_drop_death`,
`object:item.gameplay_reward_b31`, `object:item.gameplay_reward_b37`, all removed). All 17 kinds are one
parent `object:item.gameplay_rewards` with children `object:item.reward.kind01..kind17`. Source path:
`+$36 → $40CCC/$40D32 → family 12 base $0A5A → compositor 2 → anim $13-$23 → embedded line 0 (1-13) / 3
(14-17)`. Compositor-2 single-tile codes verified to match Cody's census exactly (`$A5A…$A69`, `$A6E-$A71`).
Each child exposes kind / identity byte / value / anim / code / embedded line / preview / human-name PENDING.
Nothing is auto-mapped to a Genesis line.

## R1-S2 Hazard Organization

The R1-S2 hazards are PC080SN Plane-A (or mixed tile/palette-animation) graphics with PENDING source subset.
`r1s2_hazard_candidates()` emits seven disabled candidate groups (Floor Spikes, Suspended/Moving Spike Trap,
Moving Wooden Gate, Falling Water, Pit Flame Animation, Static Lava, Rope/Chain Terrain) under Hazards/Traps
with human name + round/sub-round + hardware class + what-is-known, `authorable=false`, `hazard_pending=true`,
no pieces, no source codes — they can never author a mapping. They are explicitly **not** `$0224`/`$09EA`.
`$0224` (pit flame) is preserved as the R2/R4 castle actor and `$09EA` (spike/spear/stalagmite) is added as
the R5 castle actor, both carrying their Tighe HUMAN IDENTITY.

## Round 1 Boss Integration

`r1_boss_usages()` emits a scene-local R1-S3 group (`group_label` "Round 1 Boss"): body
`object:boss.r1.body` (base `$061D`, rec type `$0E`, slot A5+`$0708`, comp 1, anim `$00`, program `$47908`,
`+$27=0`), type-15 auxiliary `object:boss.r1.aux.type15` (rec type `$0F` via `$457B2/$457D0`, comp 1, anim
`$14`, program `$47E54`), and `object:boss.r1.effect.death` (PARTIAL, disabled). Not presented as a field
enemy. Source **line F is shown PROVEN**; exact staged RGB is PARTIAL/pending, so ordinary family-2 field
palette is NOT applied and the groups are not authorable (no invented colors).

## Round/Sub-Round Navigation

The oracle now emits `round_nav` (Round → Sub-Round, with the boss flag on sub-rounds whose scene key is a
BOSS scene, e.g. R1-S3) and a `scene_group_order` (Scene summary, Layer A/B, Player, Weapons, Scene Enemies,
Boss, Hazards, Rewards, Projectiles, Effects, HUD). Each usage carries `round`/`subround` (derived from its
scene key) so the client presents Round 1 → {Sub-Round 1, Sub-Round 2, Sub-Round 3 / Boss}. The existing
scene filter keeps unrelated rounds out of the ordinary list; scene-local objects (hazards, boss, rope
climber) show only in their sub-round.

## Authoring vs Research Views

The client list has an explicit **Authoring / Research** toggle. Authoring shows only scene-appropriate
authorable assets and hides `view=research` producers/controllers; Research reveals unresolved producers,
controllers, and every scene. Hazard/palette-pending groups still appear in Authoring but **disabled**
("SOURCE SUBSET PENDING" / "PALETTE PENDING") and cannot author a mapping.

## Mapping Scope Model

Every usage carries `mapping_scope` (`scene` for scene-local objects, `shared` for truly scene-independent
assets) shown as a badge. Scene-local objects have a `scene_key`; shared assets do not. A **LEGACY / NEEDS
REVIEW** banner lists any profile mapping whose key no longer matches a live object (the orphaned old reward
mappings in Test.json) — preserved, not deleted, and not applied. Local-override vs inherited editing scope
(the existing context-policy mechanism) is unchanged.

## Palette Ownership Panel

The Layer-A view now renders a per-scene CRAM line-ownership panel (served scene-aware from
`/api/layera`): for each of Lines 0-3 it shows owner, EDITABLE / PROTECTED / CONDITIONAL state, backdrop
role, animated indices, and the ownership note. Line 0 carries the backdrop BLACK invariant; Line 2 shows
Layer-B protection (and the R1-S3 CONDITIONAL state).

## R1-S3 Conditional Line-2 Handling

`scene_line_ownership("PAL-R1-S3-PLANEA-BOSS")` marks Line 2 `CONDITIONAL` and keeps it locked/protected:
Plane B still has nonblank data, active publication, and active scroll paths, so visual occlusion is not
proven. The model can represent "FREE IN THIS SCENE ONLY" with start/end ownership if Cody later proves a
safe interval, but global Line-2 protection is never changed from this scene badge. The target panel shows
the conditional note when R1-S3 is active.

## Backdrop Black Invariant UI

`BACKDROP_INVARIANT` (Line 0 / index 0 = `0x0000`) is surfaced in the oracle, the line-ownership panel, and
the target-panel banner, labeled a project-level production invariant (VDP reg 7) owned by Cody for the
scene-package fix. The Composer does **not** rewrite Test.json to enforce it and does not treat backdrop
black as a Tighe color decision needing reapproval.

## Bestiary Synchronization

`build_bestiary.py` regenerated (`consistency_check: PASS`, 38 actors): Green Knight statusbox corrected to
23/97 with the rope-climber split and `$4D/$57/$58` note; the reward family statusbox corrected to
compositor 2 / line 0 / line 3 with one parent + 17 children (`object:item.gameplay_rewards`,
`object:item.reward.kind01..17`) and the three-bank model removed; the R1-S2 hazard statusbox records the
disabled Plane-A candidate groups (not `$0224`/`$09EA`); the R1 boss body (`$061D`) is present in the boss
section. The Bestiary states production integration is distinct from source/tool identity.

## Independent Verification

New `tools/graphics_editor/verify_0091_handoff.py` (25 checks, all independently re-derived, not imported
from the implementation) — PASS: Green Knight 23/97 + no `$4D/$56-$5A` contamination; rope climber base
`$0241` programs `$56,$59,$5A` separate object; 17 reward children, compositor 2, lines 0/3, codes
`$A5A-$A71`; boss body/aux programs + R1-S3 scope + line F proven + not authorable; Authoring/Research
navigation (no unrelated rounds in R1-S2 authoring; boss group in R1-S3; controllers hidden from authoring);
backdrop invariant; R1-S3 conditional Line-2 locked; hazard candidates disabled; Test.json byte-unchanged.

Updated/kept-green: `verify_green_knight.py` (31 PASS), `verify_reindexed_pc090oj.py` (23/97),
`verify_death_item_families.py` (15/15), `verify_r1s2_castle_browser.py` (15), `verify_r1s2_actor_roster.py`
(5), `verify_independent_scopes.py` (9), `verify_per_piece_palette.py` (6), `verify_scene_automap.py` (44).
`verify_subround_palette_coverage.py` has one pre-existing failure (check 7, registry-migration backup),
independent of this task's files.

## Test.json Integrity

`analysis/graphics_optimizer/editor_policy/Test.json` SHA-256 before and after:
`e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730` — unchanged. No authored target colors or
palette decisions were altered. Orphaned old-reward mappings inside Test.json are preserved and surfaced as
LEGACY/NEEDS REVIEW in the UI rather than edited. `specs/palette_decisions.json` is unchanged.

## Files / Local Commit / Logs

Modified: `tools/graphics_editor/server.py`, `tools/graphics_editor/gen_reindexed_pc090oj.py`,
`tools/graphics_editor/app.js`, `tools/graphics_editor/style.css`,
`tools/graphics_editor/verify_green_knight.py`, `tools/graphics_editor/verify_reindexed_pc090oj.py`,
`tools/graphics_editor/verify_death_item_families.py`, `tools/graphics_editor/verify_r1s2_castle_browser.py`,
`tools/graphics_optimizer/build_bestiary.py`, `docs/design/rastan_actor_bestiary.html`.
New: `tools/graphics_editor/verify_0091_handoff.py`, this report, and the `AGENTS_LOG.md` entry.

Incidental verifier-written scratch profiles (`editor_policy/profile_manifest.json`, `t_*.json`) were
reverted so the commit contains only intended changes. No ROM built, no build number consumed, no generated
ROM artifact changed, no Cody production source touched, no GitHub push.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0091
