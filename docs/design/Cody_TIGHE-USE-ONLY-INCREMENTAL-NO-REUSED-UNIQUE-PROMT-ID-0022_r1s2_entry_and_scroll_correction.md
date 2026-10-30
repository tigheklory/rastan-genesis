# PROMPT-ID-0022 — R1-S2 entry and scroll correction

Date: 2026-10-27  
Author: Cody  
Status: **Build 0514 candidate; not accepted; Tighe gameplay verification required**

## Delivered build and exact inputs

The ROM was produced from Git HEAD
`52f2a7c70c0a2b00ff6ccf93057fccbbb2c8438d` plus the preserved uncommitted ROM-producing patch whose
binary Git-diff SHA-256 is
`20d176924dd77e4b8530b2bb7b5be90cacb14b53d4234e84a16a39ec737e51bb`. The patch was not committed
because repository authority assigns commits/pushes to Tighe. No concurrent audio, Andy, Composer, or
test-profile change was reset.

The authoritative authoring input was `analysis/graphics_optimizer/editor_policy/Test.json`, profile
revision 40, modified `2026-10-27T14:50:41Z`, size 305,182 bytes, SHA-256
`86505de8a7566e0a13a083bf6b3715fa61eb9242102091aadb589d7583cde9fb`. The profile manifest SHA-256 is
`14e041fa7b9edc7fd8bb289a917f87ffd3e07a7e479b6fe18c4d2eceeebdfad1`. Although the editor manifest's
UI-active entry is `baseline_current`, the production Makefile explicitly names `Test.json`, and this
build used `RASTAN_PALETTE_TEST_PROFILE=1`; the generated boundary report records that exact profile
hash.

| Artifact | Size | SHA-256 |
|---|---:|---|
| early runtime candidate `dist/rastan-direct/rastan_direct_video_test_build_0513.bin` | 3,825,336 | `a287897eae147898bbd9f13b274bba5d161c044e7317abd328986f0915725f5a` |
| early runtime candidate `dist/rastan-direct/rastan_direct_video_test_build_0513_S1-2.bin` | 3,825,336 | `821e8ca135320618082c1128c596a170b42789dbd0a8c8997483ad4cb4223174` |
| exact-current handoff `dist/rastan-direct/rastan_direct_video_test_build_0514.bin` | 3,825,336 | `7547fafb697a72988b65a9e88acdffc728749fe9542b231d8503bb7ee733a04c` |
| exact-current handoff `dist/rastan-direct/rastan_direct_video_test_build_0514_S1-2.bin` | 3,825,336 | `94480f1c825e7f7f5c760464f8c598a831aaccd4b161e2426fba9db9253aa835` |

The Makefile-owned counter is 514. Its consumed ledger records both 0513 and 0514 as
`canonical=PASS entry=PASS epoch=PASS`. Standard build-family variants were preserved under both
numbers. Build 0513 was reported as soon as it became runnable; Build 0514 is the exact-current
source/spec handoff after the durable policy and remap-note updates. A binary comparison proves 0514
differs from 0513 at only two bytes: the ROM checksum and ASCII build-number digit. All executable,
map, palette, pattern and selector bytes are identical. This remains a candidate, not an accepted
baseline.

## Semantic cut and R1-S1 preservation

The native cut remains:

`retained arcade scene/camera/descriptor/ring decision -> offline final native Plane name/pattern data
-> bounded native scene-map or entering-row/column copy -> VDP publication`.

The retired tail is PC080SN name RAM, C-window addressing, device behavior, and full-map projection.
There is no shadow tilemap, framebuffer, runtime transpose/rotation, pixel reindexing, palette matching,
or general arcade descriptor interpreter.

Build 0512 fixed R1-S1 by restoring the retained live descriptor/ring producer and using its exact
descriptor address to select an offline-prepared authored visual payload. Builds 0513/0514 do not alter
that selector-0 path. Tighe's Build 0512 R1-S1 test remains the direct gameplay evidence; Build 0514's
canonical selector-0, exhaustive descriptor, package-residency, collision and 64-row gates all pass.

## Plane-B root cause and correction

The retained scene fill at arcade `0x0503DC` runs before `0x0504FA` installs the selected record's final
six-word camera tuple. The arcade PC080SN retains 64 logical rows, so changing to Plane-B Y=`$0100`
selects logical top row 33 without losing either half. The Genesis has a 32-row physical plane. Build
0512 left Plane B in the pre-camera physical arrangement (logical rows 0..31) while VSRAM selected
physical top row 1. It therefore displayed the wrong half of the background: bright sky where the
arcade shows the lower mountain/lava band.

The old verifier encoded the same bad assumption for Plane B: it scored physical rows directly, with
only row zero aliased to logical row 32. Correct final-camera scoring maps every visible logical row as
`physical = logical & 31`. At the matched record-17, selector-1, A/B Y=`$0100` entry, that correction
finds Build 0512 wrong in **2,048/2,048 Plane-B pattern cells**.

The compiler now emits `plane_b_scene_fill_maps.bin`, a final 4 KiB native Plane-B image for each of the
six scene-reinitializing records. It consumes the retained post-fill descriptor cursor and immutable
final camera tuple offline, applies fixed native Plane-B package slots and attributes, and emits final
Genesis names. Runtime `genesistan_plane_a_scene_scroll_reseed_native` now copies the already-native
4 KiB Plane-A map and 4 KiB Plane-B map and marks both planes dirty. It performs no source descriptor
walk and adds no new per-frame processing.

The Plane-B artifact is 24,760 bytes, SHA-256
`0833dbe5c5104e2031a73e7289e0863a5e0cb5fe1f758907ca0a3138becb2941`. The exhaustive gate checks
12,288 Plane-A scene cells, 12,288 Plane-B scene cells, 16,384 selector-1/2 pan cells, and 1,138,688
authored descriptor cells. Collision generation is untouched.

## Independent upward-scroll investigation

The entry defect and upward symptom were tested independently. The earliest reached camera crossing is
record 17, selector 1, A/B Y=`$0104`, where visible top changes from logical row 33 to 32. The exact
first cell chain is:

| Field | Value |
|---|---|
| retained descriptor / entry | `$3A08` / `$3A08` |
| arcade tile / palette bank / attr | `$0812` / `$008` / `$0008` |
| logical coordinate | row 32, column 0 |
| authored visual | `LA-0001`, synthetic code `$16A7` |
| package / resident slot | 5 / `$02EB` |
| compiled native word | `$62EB` |
| staged word / actual VDP word | `$62EB` / `$62EB` |
| resident pattern | byte-exact match |

The durable selector-scroll verifier compares the reached final hardware state, not two compiler
products. At Y=`$0104`, the newly entered Plane-A row has 0/64 compiled/staged mismatches and 0
staged/VDP mismatches. Plane B has 0/2,048 pattern mismatches, zero attribute/LUT/resident-pattern
mismatches, and zero collision-word mismatches against the original arcade name-RAM oracle. At
Y=`$0131`, all seven entered Plane-A rows 26..32 remain exact and the same full Plane-B and collision
checks remain zero. Evidence is in:

- `states/traces/rg0022_build0513_r17_first_scroll/selector1_scroll_verification.json`
- `states/traces/rg0022_build0513_r17_y131/selector1_scroll_verification.json`

Build 0508 and Build 0513 also have identical retained state at the Y=`$0131` capture. Build 0514 is
runtime-equivalent by the two-byte checksum/build-label comparison. The existing offline source
reconstruction independently proves all 4,096 cells of record 17 and all 4,096 cells of
record 21 before package-slot realization.

No independent Plane-A divergence exists in the reached record-17 route. The apparent architecture
change while climbing was the already-wrong Plane-B half-ring becoming visible through different
Plane-A windows as the camera moved. The first wrong displayed data in Build 0512 is therefore Plane B
at scene entry, not a later selector-1 Plane-A publication. Builds 0513/0514 fix that underlying data and
keeps it exact during the reached upward crossings.

The prior Build 0512 result was contradictory because it (1) used the incorrect special Plane-B model,
(2) treated Plane A's authored synthetic carrier codes as though they must equal original raw codes,
and (3) compared Build 0508/current normalized geometry without an independent final-camera Plane-B
oracle. The corrected verifier deliberately reports the raw-code Plane-A limitation while separately
checking orientation, staged-to-VDP publication and resident patterns; selector-row proof uses compiled
authored final words derived from the original descriptor source.

Records 16/17 and the first seven record-17 entering rows are runtime-proven. Record 21 is exhaustive
offline-proven but not runtime-reached: the established automated route still stops at the later chain.
Natural 17->18->19->20->21 transitions therefore remain gameplay verification for Tighe, and this
report does not invent that coverage.

## Masonry palette-bank audit

Andy's commit `bf9a7932` proves 37 physical masonry patterns occur under multiple arcade banks
`$008..$013/$01F`; the intended grey-to-warm change is subtle (about 86..102 luma). Genesis
shadow/highlight would overshoot and alter priority semantics. Builds 0513/0514 leave VDP register `$0C` at
`$8C81` (STE off), adds no shadow sprites, and preserves Line 2.

The current Test profile contains 517 R1-S2 Plane-A mappings: 500 on Line 3, 16 deliberate flame/
background reuses on Line 2, and one on Line 0. The native compiler keys authored visuals by
`(tile code, palette bank, flip)`, so every distinction actually authored is preserved offline. Audit of
the 37 multi-bank masonry patterns finds 11 already produce multiple native reindexed pattern variants;
26 remain intentionally collapsed by the current authored index maps. Builds 0513/0514 preserve the 11 and
does not silently rewrite the other 26.

Line 3 is fully occupied. Its existing `$0222` can represent the dark grey treatment. The representative
arcade warm value cited by Andy quantizes to Genesis `$0226`, which is not present; adding that second
treatment requires exactly one Line-3 index to be freed or replaced, plus Tighe-authored bank/index-map
assignments for the cells that should use it. No Line 0/1/2 allocation or Line-3 replacement was made.
Thus entry/scroll alignment is fixed, but the complete subtle masonry gradient remains a specific
Palette Composer decision for Tighe rather than an unauthorized automatic palette change.

## Current Composer object decisions and production-consumer gap

The preserved Test profile contains Line-2 mappings for:

- `object:item.gameplay_reward_b31` and `object:item.gameplay_reward_b37`;
- `object:effect.specialized_death_019d` and `object:effect.specialized_death_09dc`;
- `object:effect.item_drop_death` and `object:effect.bat_death`.

The governing decisions are `PAL-PC090OJ-GAMEPLAY-REWARD-B31-001`,
`PAL-PC090OJ-GAMEPLAY-REWARD-B37-001`, `PAL-PC090OJ-SPECIALIZED-DEATH-019D-001`,
`PAL-PC090OJ-SPECIALIZED-DEATH-09DC-001`, `PAL-PC090OJ-ENEMY-ITEM-DROP-DEATH-001`,
`PAL-PC090OJ-BAT-DEATH-001`, `PAL-PC090OJ-ORDINARY-ENEMY-DEATH-001`, and
`PAL-PC090OJ-ENEMY-DEATH-BURST-001`.

The Plane-A compiler consumes the scene mappings. The production PC090OJ reindexer corpus, semantic
profile report, and palette-selector LUT do **not** contain the six newly exposed reward/death object
IDs; the generated semantic report confirms all six absent. The selector LUT can select by retained
bank/scene semantics but cannot infer these object IDs, and the death-frame compiler consumes the
already-built editor region. Therefore the six decisions are safely saved but are **not yet represented
as object-specific production pattern variants in Builds 0513/0514**. No new sprite architecture was invented
under this stage-graphics task. This is an explicit integration gap, not a claim of implementation.

Because Builds 0513/0514 do not add a new CRAM owner or change object selection, they cannot newly cause scene,
drop, or death transitions to overwrite each other. Actual appearances of the six unsupported object
families remain unverified and cannot be used as regression proof.

## Performance and publication cost

Host-only MAME `totalcycles` probes on the behavior-identical 0513 S1-2 ROM measure the one-time scene reseed at
62,008 cycles, versus 31,154 in Build 0512: +30,854 cycles once per scene reinitialization. The
selector-1 entering-row path is unchanged at the established 1,412 cycles; selector-0 and Z80 sound
paths are untouched. No hot-path descriptor processing was added.

Build 0512 already dirtied and published all 32 Plane-B rows from its earlier fill. Builds 0513/0514 publish
the same 4,096 Plane-B name bytes and same dirty mask, but copies the correct offline map into WRAM
first. Therefore VBlank/VDP transfer volume and command count are unchanged. ROM grows by one aligned
32 KiB region; the actual final ROM size increases from 3,792,568 to 3,825,336 bytes (+32,768).

## Validation boundary

Passed: canonical ROM gate, boot/gameplay-entry and epoch/package gates, mandatory ~30-second Genesis
NTSC MAME trace, exhaustive native scene/pan/descriptor/selector/collision/64-row gates, matched arcade
entry Plane B, actual VDP entry and reached upward-scroll checks, and one-time cycle measurement. Visual
inspection shows the lower mountain/lava band through the entry windows instead of Build 0512's sky.

Not claimed: natural records 18..21, earlier-chain interactions, fourth-chain visual/collision/
attachment behavior, a complete R1-S2 playthrough, the six new object mappings in production, complete
masonry variation, or broad manual selector-0/later-stage regression testing. Tighe must test those and
is the only authority who can accept Build 0514.
