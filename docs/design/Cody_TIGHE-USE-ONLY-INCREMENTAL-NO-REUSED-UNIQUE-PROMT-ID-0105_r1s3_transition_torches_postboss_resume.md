TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0105

# Cody — Build 0545 R1-S3 transition, torches, and Round-1 completion resume

Date: 2026-11-07

Current identifier: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0105`

Resumes historical/consumed PROMT-ID-0104.

Production source commit: `dbd5d5a1`
Build profile: `Test_2_0`, SHA-256
`49f38ea9b8c889eb24dbe232a25c590b79755b642abb8d42743d0d8b6a17c04f`.

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0105 Result

Build 0545 retains the completed 0104 source correction and passes the new source/ROM verifier plus
two USA/NTSC `genesis` runtime routes.  The direct R1-S3 route observes 564 live torch-name changes.
The natural R1-S1 → R1-S2 → R1-S3 route uses only the repository's established two
"Finish Current Sub-Round" requests, then defeats the boss with ordinary controller input.  It observes
2,271 torch-name changes and advances to Round 2 at frame 2,563.  No timer skip, forced boss-death state,
or direct Round-2 jump is used.

The resumed validation also corrects one important 0104 interpretation.  Original arcade `$055F42`
compares the retained round selector at `$10C118` with **6** before calling `$05725A/$057272`.  Therefore
the large-Rastan / "THIS IS ONLY A PART..." sequence is the final ending after Round 6, not an intermission
after the Round-1 boss.  The correct R1 result is direct progression to Round 2.  Build 0545 does exactly
that.  The final-ending PC080SN-tail corrections in `dbd5d5a1` remain valid, but they are not claimed as
R1 runtime evidence.

`REAL-HARDWARE ACCEPTANCE: PENDING TIGHE`

## Build 0544 Real-Hardware Failure

Tighe's Build-0544 evidence remains the reproduction authority:

- natural R1-S2 → R1-S3: required Plane A absent and stale/wrong Plane B visible — **YES, reproduced by
  Tighe; not rerun visually in this resume**;
- direct R1-S3 static boss room — **YES, reproduced by Tighe**;
- direct torches absent — **YES, reproduced by Tighe**;
- BlastEm post-boss fault — **YES, reproduced by Tighe; not reproduced by this USA/NTSC MAME run**.

The reported BlastEm address `$C00A28` must not be conflated with the final-ending `$C08000` clear at
arcade `$0575C4`.  The latter is source-gated to the Round-6 ending.  Build 0545's natural R1 run reaches
Round 2 without entering `$057272`, so the prior statement that `$0575C4` caused the R1 post-boss event
is contradicted by both the arcade caller gate and the live R1 run.

## Direct vs Natural Scene Initialization

Direct/cold entry already carried `genesistan_scene_present_pending` into the retained `$050482`
scene-fill completion boundary.  Natural subround teardown at arcade `$056440` cleared both planes and
reloaded generic gameplay residency, but did not arm the one-shot full-scene publication.

At the failing natural checkpoint the retained record was `$0017`, while the native owner remained
record `$0016`, package 5.  That transient mismatch is legal only if the freshly cleared physical planes
are rebuilt and published.  Build 0544 did not guarantee that publication.

## First Scene-Entry Divergence

The first semantic divergence was the missing publication latch in
`genesistan_gameplay_owner_reset`, not the stage-22 asset, palette, or boss actor.  The correction is
`apps/rastan-direct/src/scene_load.s:265-280`: arm `genesistan_scene_present_pending` before reloading
scene-1 patterns.  This converges natural entry on the same retained full-scene producer used by direct
entry; it does not select a stage, row, or graphic.

## Stage-22 Package Fix

No duplicate natural-route package was created.  Runtime 0545 natural evidence records:

- stage `$0016` (decimal 22);
- retained record `$0017`;
- active owner record `$0016`;
- package 5;
- gameplay scene 1 and PC080SN tileset 1;
- `boss_scene_converged=YES`.

The same owner tuple is observed by the direct route.  Raw staged name words are not required to be
byte-identical between routes because cache-slot assignment, ring placement, and live torch phase are
route state; the semantic package and resident logical-row provenance are the comparison authority.

## Plane-A Publication

Natural stage-22 package active: **YES**.  The full-scene latch is consumed by the existing scene reseed,
which reconstructs final native name words and installs 32 exact logical-row identities before marking all
Plane-A rows dirty.  Automated semantic publication: **YES**.  Natural/direct semantic owner and
provenance match: **YES**.  Final visual acceptance: **pending Tighe**.

No C-window shadow, tall map, second tilemap, or runtime pixel conversion was introduced.

## Plane-B Ownership / Teardown

Plane B is not blindly wiped.  The same pending scene-entry reseed selects the build-time compiled
`genesistan_plane_b_scene_fill_maps`, copies the selected 64×32 final native name words to the existing
staging buffer, and marks its rows dirty (`tilemap_hooks.s`, scene-reseed Plane-B branch).  This replaces
the cleared/stale R1-S2 surface under the same retained transition owner.

Stale Plane B reproduced in 0544: **YES, Tighe hardware evidence**.  Source-side stale-owner cause fixed:
**YES**.  Runtime owner/package convergence: **YES**.  Stale visible background eliminated on real
hardware: **pending Tighe**.  Line-2 CRAM changed by this task: **NO**.

## Animated Torch Arcade Source

The owner is PC080SN Layer A, not PC090OJ and not a CRAM-only cycle.

- retained producer: `$0596F4`;
- retired PC080SN chip tail / native semantic cut: `$059736`;
- Round-1 stream: `$059792`;
- header: 4 phases × 6 groups;
- shared phase source: retained `A5+$1362 >> 2`;
- work: four updates per phase and a 16-update cycle;
- tile codes: `$1AC0-$1AD1` from the PC080SN graphics region;
- retained attribute: `$001E`, resolved through the existing native tile/attribute LUT and the selected
  R1-S3 Plane-A palette;
- destinations (two per group): `$C0AABC/$C0AA3C`, `$C0ABBC/$C0AB3C`,
  `$C0ACBC/$C0AC3C`, `$C0AAC0/$C0AA40`, `$C0ABC0/$C0AB40`,
  `$C0ACC0/$C0AC40`.

All twelve destinations use the same retained animation phase.

## Animated Torch Genesis Translation

The semantic cut is above the chip-specific execution tail: the arcade routine keeps choosing phase,
tile words, count, and PC080SN destinations; `genesistan_phase3_fg_anim_native` emits final Genesis
Plane-A names.  The retired tail is the raw PC080SN name-RAM write.

The correction at `tilemap_hooks.s:2941-2960` replaces scroll-guess filtering with the existing exact
`plane_a_resident_logical_rows` provenance.  A logical destination may update physical `row&31` only when
that physical row currently owns the same logical row.  Direct-start torches animated: **YES, 564 changes**.
Natural-route torches animated: **YES, 2,271 changes**.

## Boss Palette/Fade Regression

Tighe's authored Line 1 is unchanged:

`0000 0066 06AA 0EEE 0CA6 0A60 0600 04EE 024A 0008 0466 0646 0004 08A8 0046 0000`

Boss body remains Line 1; Flying Daggers remain the same Line 1; Line 2 remains protected; Line0/index0
remains black.  The eight semantic states, eight-update cadence, and held state 7 remain covered by the
existing Build-0545 palette/fade verification.  No palette data or Composer source was changed here.

## Arcade Boss-Death Sequence

For ordinary rounds, the controller around `$055F3E` takes the non-final branch: it preserves the current
record, performs the retained clear/setup calls, spawns event/actor `$27`, and advances the normal
subround/round controller.  In the 0545 natural run the Round-1 boss is defeated and the retained selector
changes from 1/stage `$0016` to 2/stage `$0017` at frame 2,563.

Only when the selector equals 6 does `$055F4E` call `$05725A`, which initializes `A5+$13D8/$13DA` and
enters the final ending state machine at `$057272`.

## Genesis Softlock Root Cause

Two facts must be kept separate:

1. The final-ending state-6/state-8 routine `$0575C4` really does write the obsolete PC080SN Layer-A
   surface at `$C08000`.  `dbd5d5a1` correctly replaces only that chip tail with a native Plane-A staging
   clear (`tilemap_hooks.s:4691-4720`).
2. That routine is not on the normal R1 → R2 path.  Therefore it cannot, by itself, explain Tighe's
   R1 BlastEm `$C00A28` report.  Build 0545's R1 MAME run does not reproduce a lock and reaches Round 2.

The final-ending fix is retained; no false claim is made that the R1 BlastEm address was independently
reproduced or proven by this run.

## Round-Clear Condition

R1 completion is the retained normal-round branch and stage/round advancement, not `A5+$13D8 == 1`.
The latter selects the Round-6 ending controller.  The runtime gate now enforces the correct R1 condition:
natural stage 22, converged scene owner, live torches, boss defeat through controller input, then selector 2
and stage `$0017`.

## Congratulations / Intermission State

There is no post-R1 congratulations state in the original code.  `$05725A/$057272` is the final-game
ending after Round 6.  Consequently:

- boss defeat reaches an R1 congratulations screen: **NO — not an arcade R1 behavior**;
- R1 congratulations completes: **NOT APPLICABLE**;
- Round 2 begins correctly: **YES**;
- timeout/direct-jump hack used: **NO**.

## Large Rastan Graphic Source

For the Round-6 ending (not R1), the original descriptors begin at `$05816A`:

- source `$05822A` → PC080SN `$C00000`, 32×16;
- source `$05822A` → `$C00080`, 32×16;
- source `$05862A` → `$C01000`, 32×16;
- source `$058A2A` → `$C01080`, 32×16.

This is original PC080SN block data translated through the existing generated End-Round preload (1,067
tile/slot pairs), not enlarged player sprites, title art, or screenshot-derived pixels.  It is a native
plane presentation; the PC080SN write tail is retired.

## Congratulations Text Source

The final-ending text pointer record is at `$057908`; exact text begins at `$057910` and is rendered by
the retained text path around `$057624/$0576D2` through PC090OJ text objects:

```text
THIS IS ONLY A
PART OF MY LONG
STORY-ONLY A
PART TO BECOME
A KING.
IF I HAVE
ANOTHER CHANCE,
I'LL TELL YOU
MY OTHER
ADVENTUROUS
STORIES.
```

The static verifier locks the exact bytes and line breaks.  It does not relabel this Round-6 text as an
R1 message.

## Intermission Palette / Rendering

For the final ending, `$057808` loads the original palettes from `$057F2A`, `$05802A`, `$05812A`, and
`$05814A` (banks 4, 5, 6, and `$41`).  `genesistan_endround_owner_enter` selects generated End-Round
pattern residency before that retained palette load; visibility is held until the original initial block
producers finish at `$0574A2`.  The source cut preserves the retained palette, timers, actor/text writers,
and progression.

## Post-Boss Audio Semantics

The working Round-1 audio path is unchanged, including the R1-S2 → R1-S3 `$25,$1C` sequence.  The final
ending's state-2 actor/event `$20` is retained at the original `$03A0EC` call.  This task did not alter or
claim a new broader audio command mapping.

## Round-2 Progression

The 0545 natural route reaches Round 2 at frame 2,563 with final selector 2, progression marker `$17`,
stage `$0017`, active record `$0018`, and package 6.  It does so through the retained controller after an
ordinary input-driven boss defeat.

## Natural End-to-End Regression Gate

Durable runner: `tools/mame/run_round1_completion_runtime_gate.sh`; Lua observer:
`tools/mame/scripts/round1_completion_runtime_gate.lua`.

Build 0545 invincible natural result: **PASS**.  Evidence:
`states/traces/prompt0105_build0545_natural_round1_completion_final/`.

- two established pre-boss finish requests;
- stage-22 scene owner converged;
- exact torch-row residency observed;
- 2,271 live torch word changes;
- boss defeated via controller input;
- Round 2 reached;
- no End-Round/final-ending state claimed for R1.

## Direct-Start Regression Gate

Build 0545 invincible direct R1-S3 result: **PASS**.  Evidence:
`states/traces/prompt0105_build0545_direct_round1_completion_final/`.

- stage-22 scene owner converged;
- exact torch-row residency observed;
- 564 live torch word changes;
- route subsequently advanced, but direct start is not used as proof of natural transition state.

## Water-Pit / Falling-Water Terminology Correction

No hazard production work was performed.  Current terminology is preserved:

- Water Pit: PC080SN Layer A, bank `$01F`, pool `$24BB-$24C2`, submerged channel
  `$24C3-$24CA`, record 20;
- Falling Water streams: PC090OJ sprite, palette lines `$1A-$1D` proven, graphics base still
  source-pending.

## Builds / Artifacts

No Build 0546 was generated because production source/spec remain byte-identical to `dbd5d5a1`, the
source identity that produced 0545.  Counter remains 545.  Every file below is 3,972,792 bytes.

| Artifact | SHA-256 | Purpose/result |
|---|---|---|
| `rastan_direct_video_test_build_0545.bin` | `5da23bd608431075934557ab1d7cf09ae639cb86772f97635226c44e06923291` | normal candidate; baseline gates PASS |
| `..._0545_invincible.bin` | `40ac11fec6e81c00a69c4d1e245608a2f3f719714f2b4d5b61e70feb17ea12af` | natural regression; PASS |
| `..._0545_S1-3.bin` | `7bfb2f9273309a6565f2c01a53ce4077bcd7d728e989e12d1a2ea81fd4207dc6` | supported direct R1-S3 |
| `..._0545_invincible_S1-3.bin` | `790b960745acd733c1fd1037d139ff010fa011bdfb634388d32beb25ca0c6c45` | direct torch regression; PASS |
| `..._0545_c.bin` | `222b87707d9b4dff575f213a97e5831c6586ce17fca2879603d61455ec033b6b` | MODE-cheat family member |
| `..._0545_d.bin` | `cf16fb2babb0079a07fbcff9ba51144295c5065984b3313cad21fb393c9a87fb` | diagnostic family member |
| `..._0545_do.bin` | `2786d77c9dff71a6dfca322d99a92e9eb42ff46f60c791a39db575c057604909` | diagnostic-output family member |
| `..._0545_full_hud.bin` | `b6ff95845c79de2a44f4c84f7459afbd32fea770b6e1ae1c985c5bc1672bf270` | full-HUD family member |
| `..._0545_s.bin` | `3457182e8ad3850c0d9156af5fcb0439bd8ddd78f4fb063b5d1f65f5b86efba7` | score family member |

## USA/NTSC Evidence

Target: MAME `genesis`, USA/NTSC — **YES**.  PAL `megadriv` was not used.  Existing 0545 build evidence
already passed the canonical, gameplay-entry, phase-epoch, palette, complete-family, and mandatory
30-second USA/NTSC gates.  This resume adds the two PASS routes above and the static verifier.

`verify_round1_completion_semantics.py` passes 0545 with:

`torches=4x6 provenance=exact ending_gate=round6 endround_preload=1067 text=exact`.

The same verifier fails 0544 at the missing `$05727A` semantic hook, so the strengthened gate would reject
the previous ROM.  It also locks the natural publication latch, exact torch provenance, all 12 destinations,
the three final-ending hooks, Round-6 gate, exact final text, and End-Round preload count.

## Real-Hardware Acceptance

Automated results establish the source/ROM contracts and USA/NTSC MAME progression.  They do not replace
Tighe's visual and BlastEm/hardware acceptance.  Required manual checks remain natural R1-S2 → R1-S3
visual Plane A/Plane B, torches, boss palette/fade/daggers, and clean R1 → R2 transition.

`REAL-HARDWARE ACCEPTANCE: PENDING TIGHE`

## Files / Commits / Logs

Production source commit:

- `dbd5d5a1` — `Fix Round 1 scene and end-round ownership (0104)`.

Resume verification/documentation files:

- `apps/rastan-direct/Makefile` — invokes the new ROM-aware verifier;
- `tools/translation/verify_round1_completion_semantics.py`;
- `tools/mame/run_round1_completion_runtime_gate.sh`;
- `tools/mame/scripts/round1_completion_runtime_gate.lua`;
- this report;
- append-only `AGENTS_LOG.md` entry.

Safety:

- Test/Test 2.0 modified by Cody in 0105: **NO**;
- boss authored palette changed: **NO**;
- Andy tooling staged: **NO**;
- unrelated hazards production-integrated: **NO**;
- new shadow tilemap or hardware emulation: **NO**;
- timeout/direct-Round-2 hack: **NO**;
- GitHub push: **NO**.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0105
