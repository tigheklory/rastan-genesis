TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0079

# Build 0538 — Resume Natural Round-1 Transitions

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0079 Result

Historical prompt resumed: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0076`.
Current prompt: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0079`.

Build 0538 is the normal-game candidate for the natural R1-S1 -> R1-S2 -> R1-S3 transition. It preserves Build 0534's Plane-A implementation, restores gameplay graphics ownership across the retained subround teardown, activates the existing generated Round-1 palette at the first mutually-current package boundary, and translates the original sound decisions without duplicating Re-In-Carnation. The final-segment stale 8-pixel pipe row remains **OPEN**. No Palette Editor, Palette Composer, palette generator, warrior semantic coverage, palette decision, or `Test.json` authored choice was changed.

## Resume State from PROMT-ID-0076

The interrupted tree contained the partially extended `tools/mame/scripts/audio015_arcade_command_timing.lua`. It was reviewed and completed in place rather than discarded or replaced. The existing AUDIO-015 native runtime gate was extended to observe retained commands, package activation, palette equality, and the two natural subround boundaries.

Builds 0535 through 0537 were preserved as consumed development artifacts. Build 0535 exposed a stale canonical coverage expectation; 0536 and 0537 were passing intermediates. Build 0538 is the completed candidate.

## Build 0534 Preserved Baseline

No Build-0534 Plane-A streaming, residency, provenance, selector-1/2 authoring, visible-edge publication, or 28-visible-plus-4-prefetch logic was changed. The semantic cut remains the arcade row/camera decision to final Genesis Plane-A words; the PC080SN name-RAM tail remains retired. There is no new backing map, shadow tilemap, or 32-visible-row assumption.

## Existing Partial Audio Timing Work

The existing arcade harness now records command writes with retained state around natural subround transitions. The native gate records both the retained command stream and the permanent Z80 command ring. Existing captured arcade evidence at `states/traces/prompt0076_arcade_r1s2_to_r1s3_audio_v2/arcade_command_timing.tsv` and Build-0538 Genesis evidence are the ordering authority.

The current normal audio baseline also passes at `states/traces/build0538_audio015_native_runtime/audio_runtime_summary.txt` with zero banked-stream mismatches.

## Original R1-S1 → R1-S2 Transition

The inherited 0076 source finding is real but was overgeneralized. The retained substate-9 route at original `$055F58-$055F72` can emit `$27`, and the earlier `$03A848` route can enter that controller sequence. That does not establish that the captured natural R1-S1 -> R1-S2 boundary uses that route.

Dynamic original-arcade evidence resolves the actual boundary: once record `$0011` is stable, the arcade emits `$25` at frame 787 and `$1B` at frame 788. `$1B` is the six-channel Scene-2/Re-In-Carnation selection. The direct-start derivative deliberately exercises `$27`; both `$1B` and `$27` map to the one existing Re-In-Carnation stream.

## `$27` / `$25` Command Ordering

There is no captured natural `$27` then `$25` pair. The exact natural order is:

1. shared player-appearance cue `$25`;
2. Scene-2 music decision `$1B` on the following frame.

The exact Build-0538 R1-S2 direct-start order is `$27,$1B`; that derivative patches the appearance request to exercise the retained `$27` compatibility route. Therefore `$27` is valid and must survive, but it must not be presented as the command selected by the captured natural boundary.

## Native Sound-Bridge Root Cause

The native bridge used `$25` as the Aggressive World music trigger. That is correct only for a genuine outdoor spawn/reappearance. At castle and boss entries, the same shared appearance cue precedes a separate music decision. Treating every `$25` as Aggressive World could restart the outdoor song and obscure the following transition intent.

`z80_write_command` now publishes the `$25` Aggressive fallback only for the proven outdoor spawn form: gameplay outer state 2, player state 3, spawn-column X, and retained record before `$0011`. Other `$25` forms are consumed. This preserves outdoor start/READY behavior while preventing castle/boss appearance cues from selecting Aggressive World. Authentic `$1B`, `$27`, and `$1C` still pass through the retained 68000 intent -> native command ring -> permanent Z80 driver path.

`specs/audio_native_song_map.json` now maps `$1B` and `$27` to the same existing Re-In-Carnation payload. No song data was added twice.

## Natural Graphics / Package Transition Root Cause

Original `$056440` is shared by two retained callers with different ownership meaning:

- substate 8 is death/READY teardown and genuinely returns presentation ownership to the frontend;
- substate 13 is natural next-subround teardown and is immediately followed by retained gameplay reconstruction.

The native replacement had unconditionally performed the frontend reset. During natural progression this replaced gameplay tile/palette ownership with scene 0 before the new subround package was rebuilt. Direct-start did not take this destructive route, explaining why it appeared correct.

At `apps/rastan-direct/src/pc090oj_hooks.s`, `genesistan_pc090oj_hook_zero_fill_56440` now tests `a5+$13AA == 13`. Only that natural next-subround caller uses `genesistan_gameplay_owner_reset`; all other callers retain the existing frontend reset. The helper reloads scene-1 patterns and deactivates frontend HUD ownership while leaving planes and SAT to the following retained producers.

## Natural Palette Activation Root Cause

The substate-13 ownership handoff occurs before retained `a5+$1242` has advanced to the new stage. Installing a palette at that early point can therefore select the old context. `fg_boundary_install` is the first native boundary where pending record, package, round, and retained stage are mutually current.

After a successful package activation, `fg_boundary_install` now calls the existing `vdp_install_test_lines`. This activates the already-generated Round-1 palette and adds no palette authoring, mapping, generator, or editor path.

Current `analysis/graphics_optimizer/editor_policy/Test.json` SHA-256:
`24914ababc7fab52aac8258dd1f9f7b3d5df230b81421c03d9ce68d1526135ae`.

Palette Editor/generator files modified: **NO**.

## R1-S1 → R1-S2 Fix

The substate-13-specific gameplay ownership handoff preserves scene-1 resources until retained gameplay rebuilds R1-S2. Package 5 activation then publishes the correct name tables and refreshes the unchanged generated palette. The bridge consumes the castle `$25` appearance cue and dispatches the following authentic `$1B` to the existing Re-In-Carnation stream. The `$27` route remains independently accepted and verified by the direct-start derivative.

## R1-S2 → R1-S3 Boss Command and Fix

The proven original boss-entry command is `$1C`. Original arcade evidence shows record `$0017` entry emits `$25` at frame 982 and `$1C` at frame 983. Build 0538 consumes the non-outdoor `$25`, then passes `$1C` through the existing native ring to `06 - The Devil Boss Carnival (Scene 3 Boss)`.

No coordinate, record-number music trigger, duplicated stream, or synthetic boss-selection path was added.

## Final R1-S2 Stale Pipe Row

Status: **OPEN**.

The reported defect is one stale 8-pixel row at the final-segment boundary. This resumed task did not obtain a source-backed first-bad-row capture establishing the expected logical row, stale owner, physical row, selector/front tuple, and exact missed publication point. It is not proven to share the natural package-transition root cause. Altering the working row residency path without that proof would risk repeating Build 0533's broad regression, so Build 0538 deliberately leaves the Build-0534 Plane-A model unchanged.

## Warrior Crouch Handoff for Andy

No warrior palette tooling was changed. Original routine `$04684E` selects programs by `actor+$3E`:

- mode 2: `$93-$96`;
- mode 8 rope: `$4D,$56-$5A` through table `$0468C8`;
- all other modes: `$6E + table[(actor+$0E)&7]` at `$0468E8-$046910`, with table bytes at `$046916` `{05,06,04,03,03,04,06,05}`, producing programs `$71-$74`.

The third branch is the source-backed missing-domain lead for the reported crouch fallback, but this task did not dynamically prove which `actor+$3E` state and selector value is crouch. Andy should capture that state, resolve programs `$71-$74` through the Palette Composer's existing compositor to final sprite codes, and confirm the existing authored green-warrior object bank `$33` before extending semantic coverage. Programs `$71-$74` must not be added speculatively as “crouch” without that runtime identity proof.

## Natural Sequential-Transition Regression

`states/traces/build0538_invincible_audio015_natural_round1_transitions_final/audio_runtime_summary.txt` is PASS. The gate requests completion using the existing stock-MAME retained-state mutation, then observes the unmodified retained transition machinery:

- R1-S2 stable at frame 502: scene 1, tileset 1, retained/active record `$0011`, package 5, generated palette MATCH;
- R1-S3 stable at frame 673: scene 1, tileset 1, retained record `$0017`, active record `$0016` (expected one-record staging lag), package 5, generated palette MATCH;
- published commands include `$25,$1B` and `$25,$1C`;
- retained commands contain the same decisions;
- 12,657 banked stream reads, zero mismatches.

The R1-S2 direct-start regression at `states/traces/build0538_S1-2_audio015_runtime/audio_runtime_summary.txt` is PASS and proves `$27` reaches source `$31A4EC`, enters the same Re-In-Carnation stream, loops at `$31B054`, and has zero bank mismatches. These are machine-state regressions, not gameplay acceptance.

## Candidate Build

Build counter: 538. All listed artifacts are 3,841,720 bytes.

| Purpose | ROM | SHA-256 |
|---|---|---|
| Normal natural progression — primary | `dist/rastan-direct/rastan_direct_video_test_build_0538.bin` | `8279100957f710e768dece23a8b39d1b4c9e978228f0be89f31ec53926747ee6` |
| Normal R1-S2 direct start | `dist/rastan-direct/rastan_direct_video_test_build_0538_S1-2.bin` | `f67cd9d70854f626c65dc3047b081332b52ef2c68a25b041c9cfc772ff7a4e6b` |
| Normal-play invincible | `dist/rastan-direct/rastan_direct_video_test_build_0538_invincible.bin` | `1e1fa1b54ae2c586edc08c8b2c68852ce9d7c934b2a85a19fed9f41c60a910c1` |
| Invincible R1-S2 direct start | `dist/rastan-direct/rastan_direct_video_test_build_0538_invincible_S1-2.bin` | `e594a4ec03e0b5091ce767d76e6c38ac6a6d1d1b2ad35e6457c1bd52354ccdfe` |

The normal Makefile build, canonical gate, gameplay-entry gate, seven-epoch Round-1 package gate, configured variant family, mandatory Genesis NTSC MAME trace, normal audio baseline, natural-transition regression, and direct-start audio regression passed. Build 0538 remains a candidate until Tighe accepts it.

## Manual Test for Tighe

Use the normal ROM first:

1. Start R1-S1 normally and finish it.
2. On entering R1-S2, confirm the castle tiles/package and palette load, and Aggressive World changes to Re-In-Carnation.
3. Continue through R1-S2 using normal and aggressive chain climbing; confirm Build 0534's good scrolling remains.
4. Inspect the final-segment boundary. The one stale pipe row is still OPEN and may remain visible.
5. Enter R1-S3 and confirm The Devil Boss Carnival begins.

The invincible normal-play ROM is available to repeat the same natural path. Warrior crouch palette acceptance is excluded from this task because Andy owns its Palette Composer implementation.

## Files / Local Commits / Logs

Production and regression commits:

- `e62f72b3` — natural transition ownership, sound bridge, and timing harness work;
- `dc2debf3` — current audio-profile canonical coverage;
- `4e894cb5` — matching canonical gate coverage;
- `452873f6` — `$1B` mapping and transition gate;
- `31adf1e7` — palette activation at package transition;
- `5da153de` — finalized natural-transition regression;
- `ce6bf240` — corrected source comment to the dynamically proven natural `$25,$1B` ordering (comment-only, after the behavior-identical Build 0538 artifact).

Principal source/spec/harness files are `apps/rastan-direct/src/scene_load.s`, `apps/rastan-direct/src/pc090oj_hooks.s`, `apps/rastan-direct/src/fg_tile_cache.s`, `apps/rastan-direct/src/sound/sound_comm.s`, `specs/audio_native_song_map.json`, `specs/rastan_direct_remap.json`, `tools/mame/scripts/audio015_arcade_command_timing.lua`, `tools/mame/scripts/audio015_native_runtime_gate.lua`, and `tools/mame/run_audio015_native_runtime_gate.sh`.

Generated build outputs and current counter/manifest changes remain uncommitted by repository convention. No ROM, trace directory, screenshot, or Palette Editor output is committed. No GitHub push was performed.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0079`
