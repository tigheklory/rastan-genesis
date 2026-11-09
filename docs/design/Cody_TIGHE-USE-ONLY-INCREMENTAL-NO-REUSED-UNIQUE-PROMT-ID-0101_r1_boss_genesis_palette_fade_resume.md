# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0101

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0101 Result

Build 0540 integrates Tighe's exact R1-S3 boss-room Genesis Line 1, routes the R1 boss body and
Flying Daggers to that one shared line, and replaces the obsolete arcade CLCS fade tail with an
eight-state native Genesis CRAM publisher. The retained arcade boss actor still owns the trigger,
state counter, eight-update cadence, completion, and dagger activation. Canonical and variant gates
pass, and a USA/NTSC Genesis MAME boss-room trace observes the complete fade and five daggers.

`REAL-HARDWARE ACCEPTANCE: PENDING TIGHE`

## Historical PROMT-ID-0100 Interruption

PROMT-ID-0100 is historical and consumed. The resumed inspection found no staged, unstaged, or
untracked partial 0100 implementation. Its already established analysis was preserved and reused;
no worktree reset, clean, rebase, or unrelated discard occurred.

## Resumed Worktree State

- Branch: `rastan-direct-proposal`.
- Starting HEAD: `1b422b490b26ed1307b495f7daccc6bc0e29e449`.
- Starting status: clean; no staged, unstaged, or untracked files.
- Starting counter: 539; latest family: Build 0539.
- Test.json SHA-256:
  `23e95837d4085c18ac9c7b95a34ac23fe499ea91f9dedbfe4af2f1a9d9a27c2b`.
- Partial 0100 files found: NO. Partial work preserved: N/A.

## Repository / Build Baseline

The task started from Build 0539/current HEAD, not the stale AGENTS.md snapshot. The normal Makefile
pipeline first stopped before ROM publication on a canonical coverage invariant. The observed exact
`+0x20000` was the linked effect of adding the third 35,584-entry authored-descriptor index context,
not an unexplained expansion. Both canonical coverage owners were updated from `0x359EB8` to
`0x379EB8`; opcode-replace count stayed 228. The rerun produced Build 0540 and advanced the counter
once, to 540.

## Arcade Source Authority

`build/regions/maincpu.bin` was independently read at `$4708C-$470A9`:

```text
0870 0CC7 0FFF 07CE 007C 0117 0FF4 0C42
0900 0665 0545 0500 0AB9 0750 0000
```

The `$46F84` 16x8 component LUT at semantic state 7 converts those 15 0RGB words to raw live
xBGR-555 Line `$4F` words:

```text
0000 01D0 3B18 7BDE 730E 61C0 3842 23DE
1118 0012 298C 290A 000A 4AD4 014E 0000
```

This matches PROMT-ID-0095 `final_live_words` 16/16. Physical arcade line `$4F`, destination
`$2009E0-$2009FF`, writer `$47004`, and component LUT `$46F84` are therefore verified. The old
half-bright RGB derivation was not used.

## Current Tighe Test.json Target

The current file was read directly and matches the issued fixture with no discrepancies:

```text
0000 0066 06AA 0EEE 0CA6 0A60 0600 04EE
024A 0008 0466 0646 0004 08A8 0046 0000
```

This includes Tighe's authored `0066`, `0646`, and `08A8` choices. No nearest-neighbor substitute
was used and Test.json was not modified.

## Existing Production Boss Palette Owner

Before this task, stage 22 selected palette asset ID zero, so R1-S3 had no authored production
scene owner. A boss-room CRAM blob could be generated but was not embedded or selected. The generic
global Test Line 1 was:

```text
0000 08CC 0242 0486 0064 04A6 04A0 0662
0CCA 0CCC 0028 024C 0422 0AA6 0640 0AC4
```

Effective boss bank `$4F` had no route-table row and therefore fell back to Line 0. There was no
native boss-specific entrance fade; retained `$47004` still executed its unmapped CLCS hardware
tail, which could not publish the intended Genesis Line 1 progression.

## R1-S3 Line-1 Ownership Audit

- Plane A: all 219 current boss-room authored uses map to Line 3.
- Plane B: remains on protected Line 2.
- Rastan/player: effective bank `$33` remains Line 0.
- Boss body: embedded F plus sprite control `$80` gives `$4F`; now Line 1.
- Flying Daggers: identical `$4F`, with index subset `{0,3,4,5,6,8,10,11,13}`; now Line 1.
- Reachable normal-fight effects: the bounded trace observed one type-`0E` boss and five type-`0F`
  daggers with no unrelated visible recolor. Damage/death transient behavior remains unproven.

## Production Palette Integration

`AuthoredLayerA.SCENES` now includes stage/record 22 and its 219-use boss-room corpus. The generated
stage selector chooses asset ID 3, `palette_hooks.s` embeds the generated R1-S3 Line 0/1/3 asset,
and `vdp_install_test_lines` selects the corresponding third descriptor-index context and CRAM
asset. Full-illumination production Line 1 equals current Test.json bit-for-bit.

The semantic cut is arcade fade intent above the CLCS-specific tail. The first instruction at
arcade `$47004` is a proper size-changing shift replacement to `genesistan_palette_hook_47004` plus
return. The retired tail is `$47004 -> $4703C -> $47076` CLCS address/component/store execution.
No palette-RAM emulation or runtime RGB conversion was introduced.

## Flying Dagger Sharing

The route table now explicitly maps scene-1 PC090OJ effective bank `$4F` to Line 1. The generated
direct palette LUT carries that route to SAT attributes. Body and dagger Test mappings retain their
identity/subset indices, so no second CRAM line or duplicate palette exists.

## Arcade Fade Semantics

Retained state remains authoritative:

- `$42332` semantic trigger sets A5+`$26E`.
- A5+`$270` is the semantic fade state.
- Boss actor `+$09` advances that state after eight actor updates.
- States 0-6 each persist for eight updates.
- State 7 clears A5+`$26E`, is published once, then remains resident.
- The retained step-7 actor path creates the five Flying Daggers.

The native helper reads these values; it does not maintain a parallel timer or state machine.

## Genesis-Native Fade Translation

`gen_r1_boss_fade_cram.py` reads the arcade source and LUT from `maincpu.bin` and reads the final
endpoint from current Test.json. For states 0-6, each source component follows
`ROM[$46F84 + nibble*8 + state]`, is reduced to Genesis precision by `f >> 1`, and is packed as
`0000 BBB0 GGG0 RRR0`. State 7 is the exact authored endpoint. This preserves eight semantic
states, monotonic component progression, and expected adjacent-state collapse without inventing a
generic or linear fade. The generated table is 8 x 16 words (256 bytes), all legal CRAM, with
index 0 black in every state.

The independent verifier checks the generated table, Test.json endpoint, `$4F -> Line 1` route,
native helper/table presence, and `$47004` shift replacement. Build output:

```text
R1_BOSS_FADE_VERIFY_PASS source=full-bright target=Test.json
line=1 states=8 bank4F=line1 line2=untouched
```

## Line 2 / Backdrop Safety

The scene asset and runtime installer copy only Lines 0, 1, and 3. Line 2 remains unchanged and
protected for Plane B. At R1-S3 asset activation, the existing scene owner explicitly clears only
Line 0/index 0 to `0000`; runtime capture confirms it black. No global Line-2 policy changed.

## Palette Decision Registry

`specs/palette_decisions.json` remains the sole registry. New proven decision
`PAL-R1-S3-BOSS-DAGGER-LINE1-001` records the ROM source, physical `$4F`, Test.json target,
Line-1 sharing, eight-state behavior, protected Line 2, consumers, and PROMT-ID-0095/0101
provenance. `specs/palette_subround_map.json` only updates R1-S3 status/index metadata; it does not
duplicate the color decision.

## Builds and Artifacts

All files are 3,972,792 bytes. Canonical, boot, gameplay-entry, seven-epoch, palette, and variant
gates pass.

| Purpose | Artifact | SHA-256 |
|---|---|---|
| Normal play; primary hardware test | `dist/rastan-direct/rastan_direct_video_test_build_0540.bin` | `d579c026e4be66466e909f2e91f437470a50d5e89ef1ccf9e661ab5dd4008b87` |
| Supported direct R1-S3 route | `dist/rastan-direct/rastan_direct_video_test_build_0540_S1-3.bin` | `fbd7c18d642ffdee6411b873148678c4a62c05f891ce389b2e5351ddc4cc42b6` |
| Invincible normal-route test | `dist/rastan-direct/rastan_direct_video_test_build_0540_invincible.bin` | `69e364a269cdacd125991f1287eef9b1165f27267eb745c63d5ef27153fe1afe` |
| CPU-bar diagnostic | `dist/rastan-direct/rastan_direct_video_test_build_0540_d.bin` | `56b2ecc2cc3750bad6e97629479f97db01b5dece72faf22bc501d983d8ea3389` |
| Score diagnostic | `dist/rastan-direct/rastan_direct_video_test_build_0540_s.bin` | `3396a48d5def36132665f4a4f52a73d5fdcce96dc57444fa8a1a410e36add368` |
| Display-off diagnostic | `dist/rastan-direct/rastan_direct_video_test_build_0540_do.bin` | `c6d8e2ace94b550931227d79a5f317a35ba3f7fa258e9300d7b27c0074011ac8` |
| Rack-advance cheat variant | `dist/rastan-direct/rastan_direct_video_test_build_0540_c.bin` | `59c43b1aba88b8387ea2579f88ade438efaaa79f0f85e11a5b7fb2d39c1c8d55` |
| Full-HUD diagnostic | `dist/rastan-direct/rastan_direct_video_test_build_0540_full_hud.bin` | `9d3476c796c6478e4c4b12320822dd107c0b9819dbb779423455e3a8b75920a7` |

The first build invocation stopped before ROM publication; it did not consume 0540. The corrected
rerun produced the one 0540 family and advanced the counter to 540.

## USA/NTSC Emulator Evidence

Machine: USA/NTSC `genesis`, never PAL `megadriv`.

- Mandatory 30-second trace:
  `states/traces/rastan_direct_video_test_build_0540_mame_30s_20261106_160007`.
- Boss trace: `states/traces/prompt0101_build0540_r1s3_palette`.
- Supported direct-start stage observed: `$0016` (22), one type-`0E` boss.
- Trigger/frame 555: state 0 and black Line 1.
- State changes: frames 563, 571, 579, 587, 595, 603, and 611: exactly eight frames apart.
- Frame 611: state 7, enable cleared, five type-`0F` daggers created, exact authored Line 1.
- Actual CRAM capture equals staged CRAM. Line 0/index 0 is black and Line 2 retains its Plane-B
  words.
- Screenshots show the entrance progression, fully illuminated red/gold boss, and an active Flying
  Dagger. No unrelated visible recolor was observed in this bounded capture.

Local original-arcade comparison is PROMT-ID-0095 trace
`states/traces/prompt0095_original_arcade_r1_boss_palette`; local Composer/Bestiary provenance is
the corrected PROMT-ID-0098 integration. No external artifact URL was used.

## Known Unrelated Issues

This task does not claim to fix R1-S2 stale/repeated Plane-A rows, Green Sword Knight geometry or
residency, reward palettes, hazard palettes, or the post-boss softlock. R1-S3 now has an authored
stage-22 Plane-A/CRAM package and the direct-start capture uses it, but natural-transition acceptance
and any broader R1-S3 package defect remain subject to Tighe's gameplay test. Boss damage/death
palette effects remain unproven.

## Real-Hardware Acceptance

`REAL-HARDWARE ACCEPTANCE: PENDING TIGHE`

Recommended test order: use the `_S1-3` derivative for rapid visual/fade/dagger inspection, the
normal 0540 ROM for natural R1-S1 -> R1-S2 -> R1-S3 audio/scene regression, and the invincible ROM
when extended survival is useful. The existing tooling does not provide a combined invincible
`_S1-3` derivative, and no temporary start hack was added.

## Files / Commits / Logs

- Source/spec integration: `930cb77d`.
- Canonical coverage declaration: `ee4e3c97`.
- Build 0540 generated evidence/artifacts: `9c777488`.
- Documentation/log commit: this report and the appended log entry; hash reported in the final
  response because a commit cannot contain its own hash.
- No GitHub push.
- Palette Composer changed: NO.
- Bestiary changed: NO.
- Green Sword Knight tooling changed: NO.
- Test.json changed: NO.
- Audio changed: NO.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0101`
