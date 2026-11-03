# Build 0484 through Build 0530 — new-chat project handoff

Date: 2026-11-03

Prepared for Tighe's next ChatGPT chat.

## Immediate status

The current source is at documentation commit
`f63cdd823da286cc19973f422931cdf620725735` on branch
`rastan-direct-proposal`. The ROM-producing source immediately below it is
`974dc0b0c9f3c351536d982e1f0e9dfa2cc45d38`.

The current numbered family is **Build 0530**. It is a candidate, not an
accepted fix.

Build 0530 improved R1-S2 Plane A scrolling, but Tighe can still cause major
Plane A corruption by aggressively jumping upward on the chains. Tighe's
latest gameplay result is therefore:

- ordinary behavior is somewhat better than before;
- aggressive jump-assisted chain climbing still exposes incorrect Plane A
  contents;
- Build 0530 does not close the R1-S2 scrolling defect;
- no source change or Build 0531 has been made in response to this latest
  result.

The next chat should start from this fact. It must not call Build 0530 fixed or
accepted merely because its static gates and mandatory MAME trace passed.

## Current Build 0530 artifacts

All Build 0530 ROMs are 3,792,568 bytes. The most useful test artifacts are:

| Artifact | SHA-256 | Purpose |
|---|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0530.bin` | `dbbc1377286e37a7d61b3ac75df613db6a2f9734a009f0f58e7e02b74c0a248b` | normal candidate |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_S1-2.bin` | `bfb3ed8ffc0e6cfe24cac80a6a1be0523f49cec299393ce4c3f7409ae936a23d` | normal R1-S2 direct start |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_invincible.bin` | `a0fff14f83a848f91e63d1413f7a2373581e4a4fc30d129f7b8e5cb4cf74a4e2` | invincible diagnostic |
| `dist/rastan-direct/rastan_direct_video_test_build_0530_invincible_S1-2.bin` | `6f2afedca192b275bf3068c9e83b534320ca81cc9c6938940093ef78616c65b3` | repeatable R1-S2 climbing test |

The complete family and hashes are recorded in
`docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0060_r1s2_no_publication_residency_fix.md`.

## Acceptance and numbering cautions

- Every number 0484 through 0530 has been consumed. Build 0506 was consumed as
  a deleted/rejected coverage-gate attempt and has no numbered artifact.
- Build 0492 is the last build in this span with an explicit acceptance tag:
  `accepted/build-0492`. Tighe accepted it on physical Genesis hardware for
  the corrected R1-S1 audio behavior.
- Later reports contain narrower acceptance statements and successful gameplay
  observations. In particular, the Build 0521 report treats Build 0519 as its
  accepted normal baseline and calls 0521 the accepted candidate family.
  Neither should be inflated into acceptance of every later graphics change.
- Build 0530 remains a candidate after Tighe's latest failure report.
- Canonical, gameplay-entry, epoch, static, or automated MAME PASS results are
  regression evidence. They are not Tighe's gameplay acceptance.

## What changed since Build 0484

### 1. Builds 0484–0494: permanent native Genesis audio

Builds 0484 and 0485 were the first numbered candidates produced while the
permanent native audio engine and the required opaque replacement/reflow
support were being integrated. Build 0484's normal ROM is 2,813,624 bytes,
SHA-256
`39e7cdd77fbc3260e14698c5b74d04d65004aa9c1dede4257d34fe2a6aab8110`.
Both early candidates were superseded.

Build 0486 was the first durable production-source version of the new audio
path. Its architecture is:

`retained 68000 sound intent -> native command ring -> permanent Z80 driver -> YM2612/PSG`

The retained PC060HA nibble transaction was replaced at the complete sender
boundary. The new runtime did not add a fake sound board or VGM parser. Music
was compiled offline to native timed YM2612/PSG packets, and the Z80 driver
owned playback, timer cadence, cartridge-bank streaming, and intro-to-loop
transition.

Builds 0486–0488 established that the original static `$19` interpretation was
not the live Genesis trigger. Original gameplay publishes `$25` at player
appearance. Build 0488 therefore dispatched Aggressive World from the live
appearance command instead of the dead `$19` path.

Builds 0489–0492 refined death, respawn, restart suppression, and GAME OVER
behavior. Tighe accepted Build 0492 on real hardware. Its accepted normal ROM
is SHA-256
`feb610c0ceef6a25247248733e326fbf4a1cd9fd3cab7cfc478e920fb582f065`,
with source commit `158ddac7` and tag `accepted/build-0492`.

Build 0493 added seven-song native dispatch and diagnostic-only selectors.
Build 0494 repaired Audio Composer routing persistence, restored the two
missing tracks, completed the nine-song library, and wired proven command
mappings including `$27` for R1-S2 Re-In-Carnation. Six authentic song-command
mappings remained unresolved; diagnostic selectors were not presented as
original gameplay mappings. Native SFX remained deferred.

Primary references:

- `docs/design/Cody_AUDIO015_production_audio_architecture.md`
- `docs/design/Cody_build0488_audio_command_semantic_dispatch.md`
- `docs/design/Andy_AUDIO015_restart_and_gameover_fix.md`
- `docs/design/Andy_AUDIO015_multisong_dispatch_and_diagnostic.md`

### 2. Builds 0495–0500: stage selection and native R1/R2 packages

Build-time starting-subround variants were added and then corrected to patch
the actual retained stage-decoder byte at arcade `$05FF9F`. This made the
subround derivatives useful for direct testing without adding runtime stage
hacks.

Build 0499 expanded the existing final-native PC080SN package architecture
through the R1 castle/boss tail and all of Round 2. It added final native stage
maps, package/preload data, and fixed Plane B data while preserving the semantic
cut above chip-specific name-RAM execution. Builds 0496–0498 were diagnostic or
rejected steps used to identify package-count clobbering. Build 0499 corrected
that D5/D6 reuse and reached zero measured R2 package misses.

Build 0500 corrected native Plane A projection. The prior fill folded every
logical destination through `row & 31` too early, so off-window logical rows
42–44 could overwrite visible physical rows 10–12. Build 0500 retained the
six-bit logical row and published only rows inside the live 32-row Genesis
window. This preserved the arcade semantic producer while avoiding a tall
buffer or chip-shaped shadow.

Build 0500 passed matched ORIGINAL ARCADE MAME versus GENESIS NTSC MAME checks
for R1-S1/S2/S3 and R2-S1/S2/S3 after bounded HUD/off-screen exclusions, but it
was still a hardware/visual candidate.

Primary references:

- `docs/design/Andy_RG019_subround_selection_correction.md`
- `docs/design/Cody_build0499_native_stage_graphics_and_level_data.md`
- `docs/design/Cody_build0500_native_plane_stage_assembly.md`

### 3. Builds 0501–0508: selector-1 castle geometry and record streaming

Build 0501 was a rejected row-only diagnostic. Build 0502 restored the
selector-1 castle coordinate contract and consumed the exact rebuilt descriptor
pointers supplied by the retained arcade producer. Static work established the
selector-1 transform as block-axis transpose plus block-column reversal, with
the internal 4x4 metatile orientation preserved.

Build 0503 removed Build 0502's erroneous attribute interpretation and consumed
the rebuilt metatile identity correctly. These builds corrected the producer,
but they did not yet prove the complete upper-chain route.

The scene-fill projection was then moved to the correct post-scroll boundary,
and selector-1 pan rows were precompiled for native streaming. Build 0508 fixed
the first proven post-initialization failure: records 16–21 now had complete
native row/package coverage after leaving the initial scene window. Build 0506
was consumed and deleted after a coverage mismatch; Build 0507 was preserved
but rejected because the new asset was absent from dependency accounting.

Build 0508 still required Tighe's complete castle playthrough. It did not prove
the later fourth-chain path merely because the static row gates passed.

Primary references:

- `docs/design/Cody_build0502_selector1_castle_map_candidate.md`
- `docs/design/Cody_build0503_castle_metatile_pointer_candidate.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0012_r1s2_complete_record_streaming.md`

### 4. Builds 0509–0514: authored Plane A and correct R1-S2 entry

Builds 0509–0512 integrated authored Plane A visuals at the retained live
descriptor boundary. Build 0512 fixed the first descriptor/palette regression,
but its initial R1-S2 validation was later shown to be wrong: Plane B displayed
the wrong 32-row half after the post-fill camera changed to Y=`$0100`.

Builds 0513/0514 corrected that entry defect with a final-native Plane B scene
map selected from the retained post-fill descriptor cursor and final camera
tuple. Build 0514 was byte-equivalent to 0513 except for publication metadata.
At the first reached upward crossings, staged and actual VDP Plane A rows were
exact and Plane B matched the independent arcade oracle.

The natural record 17→21 traversal, fourth-chain behavior, complete masonry
variation, and several object-specific palette decisions remained outside that
automated proof.

Primary references:

- `docs/design/Cody_PROMPT_ID_0018_build0512_live_descriptor_palette_correction.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0022_r1s2_entry_and_scroll_correction.md`

### 5. Builds 0515–0521: authored palette restoration, ROM budget, and R1-S2 music

Build 0517 exposed a severe color regression because the normal build compiled
the existing authored scene-palette installer out with
`RASTAN_PALETTE_TEST_PROFILE=0`. Build 0519 made the saved authored profile the
normal build authority. It did not change Tighe's saved palette decisions; it
restored their runtime consumption. Build 0518 was rejected for this task
because it refreshed unrelated audio inputs.

Build 0519 was 4,054,712 bytes, leaving 139,592 bytes below 4 MiB. The ROM audit
showed that the current dense per-context asset behavior cannot scale to all six
rounds. A shared indexed-library design was projected to fit centrally, but its
high estimate still exceeded 4 MiB. The major recommendation was to replace
dense authored descriptor indexes before authoring all remaining contexts.

Build 0520 was rejected because it regenerated unrelated audio assets and grew
to 4,103,864 bytes. Build 0521 restored the exact Build 0519 audio receipt and
changed only the R1-S2 direct-start request from existing command `$25` to
existing command `$27`.

Re-In-Carnation was **not added a second time**. It was already present in the
nine-song library and already used after the R1-S3 boss. Build 0521 selected the
existing song. The normal and R1-S2 Build 0521 ROMs remained 4,054,712 bytes;
the direct derivative differed from normal at the stage-selector byte and the
music-command immediate.

Primary references:

- `docs/design/Cody_build0519_restore_authored_palette_default.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0035_build0519_rom_audit.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0040_r1s2_reincarnation_music_selection.md`

### 6. Builds 0522–0525: live Plane A scene/checkpoint population

The next work removed dependence on static Plane A scene/checkpoint images.
Build 0525 performs a bounded replay of the retained live native descriptor
producers at arcade semantic boundary `$050538`. It uses the completed selector
saved at `A5+$132C`, preserves the 16-by-4 producer cadence, and restores the
retained stream state after producing the final native 64x32 Plane A image.

Build 0524's last discrepancy was a stale condition-code error: an authored
attribute load of zero accidentally drove a later `BEQ`. Build 0525 added the
required explicit test and reduced the 14 R1-S2 discrepancies to zero.

Build 0525's normal ROM is 3,792,568 bytes, SHA-256
`e5f9b01205ed4a7d535488ab8b5da88522f9df33eeae70ca7d0261a694cbf98d`.
It passed scene/checkpoint, selector-1, VDP, audio, and standard build gates, but
later climbing still required gameplay verification.

Primary references:

- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0043_plane_a_respawn_population_restoration.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0044_plane_a_respawn_completion.md`
- `docs/design/Cody_build0525_plane_a_respawn_completion.md`

### 7. Builds 0526–0528: first R1-S2 scrolling corrections

Build 0526 corrected a real mixed-ring error at the record-17 selector-1 to
record-18 selector-0 transition. Columns after the live ring front still belong
to record 17 and must retain selector-1 geometry. Build 0525 had reconstructed
that suffix with selector-0 geometry. Build 0526 reused the existing native
selector row for only the retained suffix.

Tighe then reported that the visible vertical-scroll problem was unchanged.
The observed first chain appeared roughly two metatiles left and the second
roughly one metatile right after vertical scrolling. Those offsets were
observations, not proposed correction constants.

Build 0527 published ordinary entering rows before scroll, but it also produced
no visible change. That established that the failing gameplay route was not the
ordinary `$055948/$055990/$055A14` publication path.

Build 0528 moved the diagnosis to the original no-publication arms at `$055704`
and `$055790`. Those arms update camera Y without writing arcade PC080SN name
RAM. The arcade therefore exposes already-retained rows. Genesis had selected
the advanced current record instead of the completed predecessor. Build 0528
corrected that source selection. Tighe found it **mostly fixed** the stage:
ordinary Up-only climbing could complete without corruption, but fast
jump-assisted climbing could still trigger intermittent Plane A corruption.

Primary references:

- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0053_r1s2_plane_a_scroll_placement_bug.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0055_r1s2_scrolled_metatile_alignment.md`
- `docs/design/Cody_build0528_r1s2_no_publication_retained_row_fix.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0056_fast_rope_climb_scroll_handoff.md`

### 8. Build 0529: diagnostic capture and the confirmed destructive overwrite

Build 0529 did not change production rendering. It preserved Build 0528 and
added an invincible R1-S2 diagnostic derivative plus existing-tool-based trace
capture. Tighe supplied aggressive, mixed, and minimal-jumping gameplay traces.

The trace analysis established:

- jumping is not a separate renderer and is not required to enter the bad path;
- fast jumping changes cadence and creates more crossings/reversals, so it
  exposes the defect more often;
- no evidence supported nondeterministic Python-generated rows;
- no evidence supported a missed dirty bit, partial 64-word DMA, or
  scroll-before-row publication;
- the original `$055704/$055790` operation preserves name RAM, while Genesis
  reconstructed and published a full row;
- valid current-record rows were later overwritten with predecessor-record
  rows.

Confirmed examples included record 17 logical rows 44–46 and 12–14, and record
21 logical rows 60–62 and 35–42. The same deterministic wrong hashes appeared
under different movement styles. Several sparse predecessor-only markers could
not be resolved from the captured hashes because the pre-write resident cells
were not recorded.

Primary references:

- `docs/design/Cody_build0529_r1s2_invincible_rope_trace_diagnostic.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0057_r1s2_rope_trace_comparison.md`
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0059_r1s2_gameplay_trace_analysis.md`

### 9. Build 0530: per-row residency provenance, improved but incomplete

Build 0530 added a 32-byte provenance vector named
`plane_a_resident_logical_rows`. It does not duplicate graphics. The existing
`staged_fg_buffer` remains the one final native 64x32 Plane A image.

The intended rule is:

- if logical row N already owns physical row `N & 31`, a source
  no-publication event preserves the existing words and does not dirty the row;
- if that slot contains logical alias N+32, the existing materializer constructs
  N, marks the complete row dirty, and changes its owner;
- ordinary selector-1/2 publication records ownership only after the complete
  64-cell row;
- scene/checkpoint replay seeds all 32 identities from the final camera.

Current source locations in `apps/rastan-direct/src/tilemap_hooks.s` are:

- lines 775–789: ordinary selector-1/2 ownership update;
- lines 878–895: scene/checkpoint ownership seed;
- lines 1430–1452: no-publication exact-logical retention check;
- lines 1605–1618: dirtying and ownership update after materialization;
- lines 5366–5372: the 32-byte provenance vector.

The static verifier covers every demonstrated Build 0529 destructive sequence
and separate N/N+32 materialization cases. All normal build gates passed.

However, the Build 0530 report explicitly left sparse predecessor-only first
materialization unresolved. Tighe's subsequent aggressive chain-climbing test
still produces substantial Plane A corruption. Therefore at least one live
sequence remains outside the corrected same-logical retention case, or the
first predecessor materialization/source state is still wrong. That is a
bounded hypothesis, not yet a proven new root cause.

Primary reference:

- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0060_r1s2_no_publication_residency_fix.md`

## What is currently proven

1. The R1-S2 failure is visual Plane A state/publication, not a need to shift
   individual chains by hardcoded metatile offsets.
2. Aggressive jumping is an effective reproducer, but the existing evidence
   does not prove a jump-specific renderer bug.
3. Ordinary and jump-assisted movement can drive different camera cadence and
   direction-transition sequences, while the camera step remains capped and
   the row-crossing helpers iterate crossings.
4. The offline row assets are deterministic. There is no evidence that Python
   emits intermittently different row contents based on input.
5. Build 0528 definitely destroyed some valid current rows by reconstructing
   predecessor rows during an arcade semantic no-write.
6. Build 0530's per-physical-row identity rule is justified for that confirmed
   current-row destruction and should not be removed merely because another
   case remains.
7. Static/canonical PASS does not cover all temporal retained-ring histories.
8. No shadow tilemap, full-scene backing map, virtual PC080SN device, or second
   32-row graphics buffer was added by Build 0530.

## What remains unresolved

1. The exact first wrong writer and source choice in Tighe's new Build 0530
   aggressive-climb failure have not been captured.
2. Build 0529's sparse predecessor-only markers remain unresolved. Their first
   materialization still uses the Build 0528 predecessor source logic.
3. It is not yet proven whether the remaining Build 0530 failure is:
   - an incorrect first predecessor materialization;
   - provenance not updated by another legitimate Plane A producer;
   - a later same-frame Plane A writer replacing a staged row;
   - state loss across a record/direction transition; or
   - a different retained-ring history not represented by the current 32 tags.
4. No evidence currently justifies altering collision, movement, camera speed,
   palettes, sprites, audio, or the offline assets to mask this defect.
5. The whole six-round game does not fit under the current dense authored
   context growth model; shared indexed asset work remains future scope.
6. Native SFX and six authentic music-command mappings remain separate audio
   work and are not part of the present scrolling failure.

## Smallest recommended next action

Preserve Build 0530's confirmed same-logical retention improvement. Reuse the
existing Build 0529 trace mechanism and the exact aggressive climbing route to
capture the **first** Build 0530 corruption, with enough information to answer:

1. Which physical row and logical row first become wrong?
2. What provenance tag was present immediately before the write?
3. Which producer wrote the row: no-publication materialization, ordinary
   selector publication, animation, reseed, or another existing Plane A path?
4. What were the current record, current selector, completed selector, strip,
   group, front, old/new foreground Y, and direction transition?
5. Was the wrong row already resident before the attempted materialization?

The most valuable comparison is the first bad Build 0530 write against the
same original-arcade resident physical row. Do not begin by broadening the
buffer architecture or hardcoding visible feature positions.

## Files the new chat should read first

Read in this order:

1. `RULES.md`
2. `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`
3. this handoff
4. `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0059_r1s2_gameplay_trace_analysis.md`
5. `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0060_r1s2_no_publication_residency_fix.md`
6. `apps/rastan-direct/src/tilemap_hooks.s`, especially the current locations
   listed above
7. `tools/translation/verify_bg_a_incremental_background.py`
8. the preserved Build 0529 captures under
   `states/traces/r1s2_rope_build_0529/`

For older provenance, follow the phase-specific references in this document
rather than restarting the full investigation.

## Repository state at handoff creation

- Branch: `rastan-direct-proposal`
- HEAD: `f63cdd823da286cc19973f422931cdf620725735`
- ROM-producing source: `974dc0b0c9f3c351536d982e1f0e9dfa2cc45d38`
- Build counter: `0530`
- The worktree already contains many modified generated outputs and unrelated
  untracked work. They predate this handoff and must not be reset, cleaned, or
  included casually.
- This handoff adds documentation only. It does not build a ROM, consume a
  number, alter production source, or claim acceptance.
