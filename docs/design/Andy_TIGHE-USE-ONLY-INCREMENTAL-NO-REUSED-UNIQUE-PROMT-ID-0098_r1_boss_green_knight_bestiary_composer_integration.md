# Andy — R1 Boss ROM-Sourced Palette + Green Sword Knight Integration (PROMT-ID-0098)

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0098`

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0098 Result

Two deliverables, both routed through the authoritative manifest → generator → artifact architecture,
with the arcade ROM as the palette authority and **no hard-coded palette values**:

1. **R1 boss palette** is now RGB-**PROVEN**, decoded live from the boss-specific ROM target table
   `maincpu.bin @ 0x4708C` (15 words → physical arcade line `0x4F`), integrating Cody PROMT-ID-0095.
   The blue field-pool (`0x4FE62`) and master-line (`0x4EE16`) hypotheses are rejected. The five
   type-15 records are identified as the **Flying Daggers**, sharing the one boss palette line.
2. The **R1-S2 Green Sword Knight** is now a **first-class manifest actor** + Bestiary card + pose
   gallery (previously prose-only), base `0x033E`, 23 programs / 97 pattern codes.

Everything is verified independently (ROM decode == Cody fixture == Composer == Bestiary swatch),
ROM-mutation-sensitive, Test.json byte-unchanged, no Genesis production / ROM / build-counter / push.

## 0097 Replacement / Expanded Scope

PROMT-ID-0097 is historical/consumed and was **not** reused. This task is the current `0098`
identifier and expands scope from the boss-palette integration alone to also include the Flying
Dagger identity and the Green Sword Knight first-class actor, all through the manifest/generator
architecture (no one-off HTML special-casing, no procedural-prose-only solutions).

## Existing Bestiary Defects

- **R1 boss** rendered neutral/gray with the badge `LINE-F SELECT PROVEN · RGB PENDING` and prose
  that the staged RGB was pending / the field pool disproven — correct for the pre-0095 state, now
  superseded by Cody PROMT-ID-0095's proof.
- **Green Sword Knight** existed only as a prose status box inside the R1-S2 section
  (`object:castle.green_sword_knight.r1.n3` was named in text); the manifest had **no** canonical
  `green_sword_knight` actor record and the Bestiary had no actor card.

Both are fixed at the authoritative source (manifest + generator), not by hand-editing HTML.

## Manifest Authority Repair

`docs/design/rastan_actor_graphics_manifest.json` (the Bestiary's sole semantic source of truth):

- **R1 boss record** (`boss_round1`): `palette_status` PARTIAL→**PROVEN**; added a structured
  `boss_palette_source` descriptor (`kind=boss_target_rom_table`, `rom=maincpu`, `address=0x4708C`,
  `count=15`, `index0=black`, `encoding=arcade_0RGB`, `logical_line=0xF`, `physical_line=0x4F`,
  `live_range=0x2009E0-0x2009FF`, `fade_writer=0x47004`, `fade_lut=0x46F84`, `status=PROVEN`); a
  `rejected_palette_hypotheses` block keeps `0x4FE62`/`0x4EE16`/`A5+0x1600` as history; replaced the
  misleading legacy 8-colour provisional `palette.swatch` (no RGB array stored); added a structured
  `flying_daggers` record; corrected `description`, `palette_source`, `palette_provenance`,
  `render.palette` (now `boss_target_rom_table @0x4708C`), and `palette_instances`.
- **Green Sword Knight record** added to `actors[]` (`technical_id: green_sword_knight_r1`,
  category `ENEMY_CASTLE_SCENE`): object id, base `0x033E`, family 2, scene R1-S2, 23 programs / 97
  codes, excluded foreign programs, embedded sword `0x26B-0x274`, two-layer palette provenance (no
  RGB literals), a `render` spec, and a `pose_gallery` (5 categories).
- **No RGB palette array is stored** for either actor; the generator/Composer decode from the ROM.

## R1 Boss ROM-Sourced Palette Integration

- New ROM-backed decoder (generator `rom_boss_target_palette`, Composer `_rom_boss_target_palette`):
  reads the 15 big-endian `0RGB` words at `0x4708C`, prepends retained black (index 0), expands each
  nibble with the boss target-table convention `pal5bit(n) = (n<<3)|(n>>2)` (deliberately **not** the
  field `_pal5` doubling), yielding the physical-line-`0x4F` palette.
- Independent decode reproduces Cody PROMT-ID-0095's captured final palette **exactly** (16/16):
  `#000000 #423900 #636339 #7B7B7B #396373 #003963 #080839 #7B7B21 #632110 #4A0000 #313129 #292129
  #290000 #525A4A #392900 #000000` — the red/gold/tan/white boss, matching Tighe's arcade captures,
  not the blue field pool.
- `boss_card()` now renders the R1 boss in colour with `RGB PROVEN · ROM 0x4708C` / `physical line
  0x4F` provenance; R2-R6 keep the honest `LINE-F SELECT PROVEN · RGB PENDING` path unchanged.
- The Composer `r1_boss_usages()` colours the body/daggers from `0x4708C` (was `_arcade_round_palette(1,0xF)`).

## Flying Dagger Integration

- Manifest `flying_daggers`: `object:boss.r1.flying_daggers`, type `0x0F`, base `0x061D`, creator
  `0x457B2→0x457D0`, compositor 1, `+0x27=0x00`, initial anim `0x14`, flight anims `0x1A-0x1F`,
  programs `0x47E54/0x47E7A/0x47E7F/0x47E84/0x47E8D/0x47E92/0x47E97`, patterns
  `0x67B,0x67C,0x683-0x689`, embedded line F, physical line `0x4F`.
- The Composer group `object:boss.r1.aux.type15` was renamed to `object:boss.r1.flying_daggers`
  (human label **Flying Daggers**, no longer "Type-15 Auxiliary"), `shares_boss_palette=true`,
  `used_colors` restricted to the proven index subset `{0,3,4,5,6,8,10,11,13}`.
- Bestiary boss card shows the daggers sharing the palette (`SHARES R1 BOSS PALETTE`) and states
  **R1 Boss + Flying Daggers: 1 palette line required**.

## Green Sword Knight Canonical Actor Record

`object:castle.green_sword_knight.r1.n3`, base `0x033E`, family 2, scene R1-S2, directly-scheduled
(`0x4A104`, `+0x3E==2`). Explicitly distinct from the family-8 **Rope Climber**
(`object:castle.rope_climber.family8.r1`, base `0x0241`, programs `0x56/0x59/0x5A`) and the
**Valkyrie** field enemy (base `0x0241`); kept as a real `actors[]` record, not generator prose.

## Green Sword Knight 23/97 Domain

`program_count=23`, `pattern_code_count=97`; `excluded_foreign_programs = [0x4D,0x56,0x57,0x58,0x59,0x5A]`
with the reclassification note (`0x4D`→`0x0234`; `0x56/0x59/0x5A`→`0x0241` family-8;
`0x57/0x58`→`0x01FC`). Independently re-derived in the verifier through the compositor VM: the 23
R1 knight programs decode to exactly 97 distinct pattern codes, with no foreign contamination.

## Green Sword Knight Palette Provenance

ROM-backed, two-layer, no hard-coded RGB: (1) embedded bit-6-clear per-piece program control nibbles
(sword nibble 3 / body nibble 7; airborne 7; short reaction C); (2) the preserved-sweep actor
`+0x27` override (`0x44/0x41`, bit 6) forcing effective line 4/`0x34` or 1/`0x31`. The authorable
green-armor reference is line 3 → `0x3BA88[R1][3]` → pool `0x0C` → `0x4FD02`, decoded from the ROM
(the same reference the Composer renders). The Bestiary swatch equals the independent ROM line-3 decode.

## Green Sword Knight Bestiary Card / Pose Gallery

A proper actor card now sits in the **R1 → Sub-Round 2** section (`R1-S2 Scene Enemy — Green Sword
Knight`): legal compositor-VM preview (green-armor line 3), canonical id, base/family, scene, the
23/97 domain, embedded-sword note, and the Rope-Climber/Valkyrie distinction. An expandable **Pose
gallery** renders legal previews for all five categories — Normal `$93-$96`, Airborne `$20-$23`,
Short reaction `$71-$73`, Low/weapon action A `$A1-$A6`, Low/weapon action B `$97-$9C` — with no
foreign rope/other-base frames.

## Composer R1-S2 Integration

The Palette Composer already exposes the Green Sword Knight as an R1-S2 scene object
(`green_knight_usages`, scene `PAL-R1-S2-PLANEA-CASTLE`) with the complete 23-program domain, pose
groups, two-layer palette provenance, and the sword sub-context. Verified live via `/api/oracle`:
exactly 23 programs, 97 codes (VM re-derived), no `$4D/$56-$5A` contamination, Rope Climber separate.

## Composer R1-S3 Boss Integration

`r1_boss_usages()` now colours the body and the Flying Daggers from ROM `0x4708C` (physical line
`0x4F`), `palette_status.rgb_status = PROVEN`, `rom_source = 0x4708C-0x470A9`, one shared palette
context (`R1 Boss + Flying Daggers`, `palette_line_requirement = 1 line`). Authoring stays gated on
Tighe's final Genesis line mapping — the tool never auto-assigns a Genesis line and exposes no
intermediate fade-state authoring palettes. Verified live: `used_colors` RGB equals the independent
ROM decode for body and daggers.

## Bestiary Dashboard Corrections

- "Boss clean legal frames" and "Per-round palettes": R1 boss normal-state palette **PROVEN** (ROM
  `0x4708C`, physical line `0x4F`), daggers share it; R2-R6 unchanged (line-F selection proven,
  staged RGB pending; field pool not substituted — **R2-R6 boss RGB status not changed**).
- New "R1-S2 Green Sword Knight" dashboard row marks the actor as a first-class R1-S2 actor.
- The boss-gallery status box no longer claims R1/R5 "palettes MAME-verified"; it states the R1
  ROM-sourced proof and keeps R2-R6 honest.

## ROM-Sourced Palette Verification

`tools/graphics_editor/verify_0098_r1_boss_green_knight.py` (38/38 PASS):

- **Source decode**: independent read of `maincpu.bin @ 0x4708C-0x470A9` == Cody rgb8 (16/16); and
  `!=` the field pool `0x3BA88[R1][F]`.
- **Composer result**: `/api/oracle` body+daggers `used_colors` == independent ROM decode; status
  PROVEN/`0x4708C`/`0x4F`; daggers share palette, restricted to the proven subset; not auto-authorable.
- **Bestiary result**: all 16 ROM-decoded `rgb(...)` swatches present; `RGB PROVEN · ROM 0x4708C`;
  no `0x4FE62`/`0x4EE16`.
- **Mutation sensitivity**: perturbing one `0x4708C` component on an **isolated buffer** changes both
  the independent decode and the Composer decode; the real `maincpu.bin` SHA is unchanged.
- **Green Knight**: manifest record present/correct; VM re-derives 23/97; Composer + Bestiary card
  in R1-S2; Rope Climber / Valkyrie distinct; knight swatch == independent ROM line-3 decode.

## No-Hardcoded-Palette Audit

The verifier confirms none of `server.py`, `build_bestiary.py`, or the manifest contains a stored
R1-boss palette block — not the 16 final live xBGR words, not the 15 source `0RGB` words, not the 16
`#RRGGBB` values (a ≥4-consecutive-value heuristic over Cody's fixture sequences returns 0 for each
file). No literal Green Sword Knight RGB table is introduced either. All palette values are derived
from `maincpu.bin` at run time. Cody's fixture values live only in the verifier (allowed as an
expected-value fixture for independent verification).

## Generated Artifact Verification

`docs/design/rastan_actor_bestiary.html` was regenerated from the manifest (actors=39; consistency
PASS). Inspection of the actual HTML:

- **R1-S2** — a normal actor card headed `Green Sword Knight` with preview, palette info, 23/97
  domain, and an expandable pose gallery (not merely a prose paragraph).
- **R1-S3 Boss** — a colour R1 boss card with the ROM-derived final palette, `RGB PROVEN`,
  `ROM 0x4708C` provenance, physical `0x4F`, and the Flying Daggers sharing the palette. No
  neutral/gray placeholder, no blue `0x4FE62` boss.

Existing verifiers remain green: `verify_0092_bestiary_artifact` (boss-badge check updated for the
now-proven R1), `verify_0091_handoff` (BO2 renamed to Flying Daggers; BO3 updated to RGB PROVEN /
ROM `0x4708C`), `verify_green_knight`, `verify_r1s2_actor_roster`, `verify_r1s2_castle_browser`,
`verify_death_item_families`, `verify_scene_automap`, `verify_palette_families`,
`verify_independent_scopes`. (`verify_subround_palette_coverage` has one **pre-existing** failure —
check 7, a `specs/palette_decisions.json` migration-backup comparison — identical on a clean tree,
unrelated to this task; `palette_decisions.json` was not touched.)

## Test.json Integrity

- Before: `e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730`
- After:  `e03dd2aa24f30adb3fd0566af0b917914b49d8cd1533441431be485dd2d6b730`
- Unchanged: **YES.**

## Files / Local Commit / Logs

Changed (tracked):

- `docs/design/rastan_actor_graphics_manifest.json` — R1 boss `boss_palette_source` descriptor +
  rejected hypotheses + `flying_daggers`; Green Sword Knight actor record; dashboard corrections.
- `tools/graphics_optimizer/build_bestiary.py` — `rom_boss_target_palette` decoder; ROM-sourced
  `boss_card()`; `green_knight_card()` + R1-S2 injection; boss-gallery status-box wording.
- `tools/graphics_editor/server.py` — `_rom_boss_target_palette` decoder; `r1_boss_usages()` ROM
  palette + Flying Dagger identity + shared-context/PROVEN status.
- `tools/graphics_editor/verify_0091_handoff.py` — boss BO2/BO3/BO4 updated to the 0095-proven state.
- `tools/graphics_editor/verify_0092_bestiary_artifact.py` — per-boss-card badge check updated
  (R1 proven + R2-R6 pending).
- `docs/design/rastan_actor_bestiary.html` — regenerated.

New (tracked):

- `tools/graphics_editor/verify_0098_r1_boss_green_knight.py` — independent ROM/Composer/Bestiary
  + mutation + Green Knight verifier (38/38 PASS).

Not touched: Genesis production source, ROM artifacts, build counter, CRAM allocation, Plane A/B,
sprite production assets, audio, `specs/palette_decisions.json`, `Test.json`. Transient verifier
editor-policy test outputs were restored. Local commit only; **no GitHub push**. The documentation
commit hash is reported in the final response (a commit cannot embed its own hash).

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0098`
