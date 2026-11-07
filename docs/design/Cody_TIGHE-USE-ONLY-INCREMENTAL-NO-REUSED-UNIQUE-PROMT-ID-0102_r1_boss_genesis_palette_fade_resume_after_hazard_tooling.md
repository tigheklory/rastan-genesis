# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0102

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0102 Result

Build 0544 is the passing production candidate for the R1-S3 boss palette and entrance fade. It
selects Tighe's edited `Test_2_0.json` as the build authority, installs the exact authored boss
Line 1, routes the boss and Flying Daggers to that one line, and preserves the original arcade
eight-state/eight-update fade semantics. Build 0543 is preserved as a rejected diagnostic family:
it exposed a Make dependency-order defect and did not pass the canonical gate.

`REAL-HARDWARE ACCEPTANCE: PENDING TIGHE`

## Historical 0100 / 0101 Interruption

PROMT-ID-0100 was interrupted and PROMT-ID-0101 is superseded. Both remain permanently consumed.
The resumed tree contained committed partial production work from 0101, an untracked superseded
0101 report, and no staged partial 0100 implementation. The established source analysis and native
implementation were reused rather than restarted.

## Current Worktree Ownership Classification

Starting state for this resume:

- Branch: `rastan-direct-proposal`.
- Starting HEAD: `af1de88398a400f2bfbc820245cdbca04e5dcf88`.
- Starting counter: 542; latest family: Build 0542.
- Staged files: none.
- Tighe-authored palette work: modified `Test.json` and `profile_manifest.json`; edited
  `Test_2_0.json` supplied immediately before this resume.
- Andy concurrent work: `rastan_actor_bestiary.html`, `app.js`, `server.py`, both 0091/0092
  verifiers, `build_bestiary.py`, and the two untracked R1-S2 trap reports.
- Cody history: committed 0101 production integration and Build 0540-0542 evidence; untracked
  superseded 0101 report and Test 2.0 reorganization report.
- Unrelated/generated state: MAME monitor log, cheat output, and build products.

No reset, clean, rebase, checkout/discard, `git add .`, or `git add -A` was used. Build and report
commits used explicit file lists only.

## Andy Concurrent Hazard/Tool Work Preserved

The current task did not edit or stage Andy's Composer, Bestiary, verifier, or hazard-report files.
It preserves the established Floor Spike base `$09EA`/anim `0x79`, Ceiling Crusher base
`$09EA`/anim `0xD8`, Pit Flame Layer-A tiles `$093A-$0949` with cycle mode 8, and Falling Water
Layer-A bank `$01F`/tiles `$24BB-$24CA` with cycle mode 9. These are source/tool-ready facts, not
production palette approvals.

## Repository / Build Baseline

The counter advanced 542 -> 543 -> 544. Every produced ROM is retained. Build 0543 failed after
publication and remains **REJECTED / NOT ACCEPTED / DIAGNOSTIC ONLY**. Build 0544 passed the
canonical gate, boot guard, gameplay-entry gate, phase-epoch gate, mandatory GENESIS NTSC trace,
palette gates, and complete variant-set verification. The generated patch manifest reports 228
opcode-replacement sites and canonical Genesis coverage delta `0x50000`.

## Arcade Boss Source Authority

`build/regions/maincpu.bin` was independently read at arcade PCs `$4708C-$470A9`:

```text
0000 0870 0CC7 0FFF 07CE 007C 0117 0FF4
0C42 0900 0665 0545 0500 0AB9 0750 0000
```

The full-bright `$46F84` LUT state produces physical arcade Line `$4F`:

```text
0000 01D0 3B18 7BDE 730E 61C0 3842 23DE
1118 0012 298C 290A 000A 4AD4 014E 0000
```

This matches PROMT-ID-0095 `final_live_words` 16/16. The old half-bright conversion was not used.
Arcade writer `$47004`, component LUT `$46F84`, live range `$2009E0-$2009FF`, and states 0-7
remain the behavior authority.

## Current Tighe Test.json Target

The prompt names current `Test.json`; Tighe's later direct instruction selected edited
`Test_2_0.json` for this build. Both files currently contain the same effective R1-S3 Line 1, so
there is no endpoint discrepancy. The exact production target is:

```text
0000 0066 06AA 0EEE 0CA6 0A60 0600 04EE
024A 0008 0466 0646 0004 08A8 0046 0000
```

The issued fixture matches, including authored `0066`, `0646`, and `08A8`. No nearest-neighbor
substitute was used. `Test.json` SHA-256 before and after is
`ab13104780289fc1f7455a4f2ab94502ef3d6ba6757fe4d147d71e97ad7ec98e`.
Selected `Test_2_0.json` SHA-256 is
`49f38ea9b8c889eb24dbe232a25c590b79755b642abb8d42743d0d8b6a17c04f`.

## Existing Production Boss Palette Owner

Before the 0101/0102 integration, R1-S3 had no authored stage-22 production scene owner: stage 22
selected palette asset zero, the generated boss-room blob was not consumed, generic Test Line 1
was installed, and effective bank `$4F` fell back to Line 0. The prior generic Line 1 was:

```text
0000 08CC 0242 0486 0064 04A6 04A0 0662
0CCA 0CCC 0028 024C 0422 0AA6 0640 0AC4
```

The new owner is the selected-profile R1-S3 stage-22 scene package plus the native boss fade table.
The Makefile now takes `EDITOR_PALETTE_PROFILE_ID`, and every generated palette consumer is
SHA-checked against that selected profile.

## R1-S3 Line-1 Ownership Audit

- Plane A: stage-22 authored uses remain on Line 3.
- Plane B: remains on protected Line 2.
- Rastan: effective bank `$33` remains Line 0.
- Boss body: effective bank `$4F` routes to Line 1.
- Flying Daggers: the same `$4F` routes to Line 1 and uses subset
  `{0,3,4,5,6,8,10,11,13}`.
- The bounded boss capture observed no unrelated visible consumer recolor. Damage/death transient
  behavior is not established by this task.

## Production Boss Palette Integration

The selected profile drives scene CRAM assets, PC090OJ reindex assets, semantic profile assets,
and the boss fade endpoint. A missing Make dependency variable discovered by Build 0543 was fixed:
the three selected CRAM line outputs are now explicit prerequisites before assembly, preventing an
old Line-0 object from being linked with new Test 2.0 provenance.

The graphics semantic cut remains the arcade boss fade decision above the CLCS-specific execution.
Arcade `$47004` is a size-changing replacement to `genesistan_palette_hook_47004`; the retired
chip tail is `$47004 -> $4703C -> $47076` CLCS address/component/store execution. No arcade palette
RAM emulation, runtime RGB conversion, shadow tilemap, or parallel lifecycle was introduced. The
retained arcade actor trigger, state, cadence, completion, and dagger activation remain live.

## Flying Dagger Sharing

Boss body type `$0E` and Flying Daggers type `$0F` both resolve physical bank `$4F`. The scene route
maps that bank to Genesis Line 1. One CRAM line serves both; there is no second dagger line or
duplicate dagger palette.

## Arcade Fade Semantics

- A5+`$26E` enables the fade.
- A5+`$270` selects semantic state 0-7.
- Boss actor `+$09` holds each state 0-6 for eight actor updates.
- State 7 is published, clears the enable, and remains resident.
- The retained state-7 actor path creates the five Flying Daggers.

The GENESIS NTSC trace observes state changes at frames 563, 571, 579, 587, 595, 603, and 611,
exactly eight frames apart, then state 7 held through the end of capture.

## Genesis-Native Fade Translation

The offline generator reads the original arcade source words and component LUT. For states 0-6 it
selects the arcade LUT component at that semantic step, reduces it with `f >> 1`, and packs legal
Genesis `0000 BBB0 GGG0 RRR0`. State 7 is the exact selected Test 2.0 endpoint. All eight states
remain represented, all index-0 values are black, all channels are monotonic, and no generic or
linear substitute fade is used. Runtime work is a bounded table selection and native CRAM publish.

## Line 2 / Backdrop Safety

The scene installer copies Lines 0, 1, and 3 only. Line 2 remains protected and unchanged. R1-S3
Line 0/index 0 is `0000` black. The bounded trace confirms the black backdrop invariant. Broader
R1-S3 Layer-A natural-transition acceptance remains pending Tighe.

## Hazard Production Non-Changes

This task makes no production palette decision or ROM integration for Floor Spike, Ceiling
Spike/Crusher, Pit Flame, or Falling Water. Authorable/proven source objects are not treated as
approved target palettes. No hazard production ownership was changed.

## Production Palette Registry

`specs/palette_decisions.json` remains the sole registry. Existing decision
`PAL-R1-S3-BOSS-DAGGER-LINE1-001` now records Test 2.0 provenance, exact Line-1 endpoint, physical
arcade line `$4F`, boss/dagger sharing, PROMT-ID-0095 source semantics, PROMT-ID-0102 production
integration, and protected Line 2. No duplicate registry was created.

## Builds / Artifacts

All listed ROMs are 3,972,792 bytes.

Build 0543 — **REJECTED / NOT ACCEPTED / DIAGNOSTIC ONLY**. Canonical gate failed with
`GATE_FAIL_2_1_INCBIN_SHA_MISMATCH` because the selected Test 2.0 Line-0 file had not been generated
before assembly; variant-set verification also found unrelated differences. Preserved artifacts:

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0543.bin` | `359bb198432b85217ef08a4d0ae0428ecb797502d5056d2dcf90a777b8fbdffb` |
| `rastan_direct_video_test_build_0543_d.bin` | `1f243890decdc9c07a3c6c1404e29b77b8757e2ec42e558ca562d98a2660c95d` |
| `rastan_direct_video_test_build_0543_s.bin` | `f6a3a59d823fdcabec4571aa71bf6d37a14186bf3fb100b79d7e6ee855511409` |
| `rastan_direct_video_test_build_0543_do.bin` | `4ee5576321a2e118db4aecc4e895e86a8071bb3a57cd2055a42e148e6c3f50ef` |
| `rastan_direct_video_test_build_0543_c.bin` | `2ebadde9ae1ec866bc2849a11a9ad2c348cd63bdf04c2638893abfe9fdb56112` |
| `rastan_direct_video_test_build_0543_full_hud.bin` | `0edd702d45258a779b07b7dc6cde46866a9883476739e877ce784a56b9f42470` |
| `rastan_direct_video_test_build_0543_invincible.bin` | `9e226ff9bcbd00657af97634b5e3fa59e7627226eea13e49ab6f048bf3b9e65a` |

Build 0544 — passing candidate. Canonical, boot, gameplay-entry, phase-epoch, palette, mandatory
trace, and complete variant-set checks pass:

| Purpose | Artifact | SHA-256 |
|---|---|---|
| Normal/hardware candidate | `rastan_direct_video_test_build_0544.bin` | `2b20fa2e09430c1a83004f6bb345e7d2ed861c97bb0ad759d116d1aaea5fd084` |
| Supported direct R1-S3 | `rastan_direct_video_test_build_0544_S1-3.bin` | `03d47674073e73b18cc1af3f2ca5afc2d67fcef6f00cc1975843e0566c5bf847` |
| CPU-bar diagnostic | `rastan_direct_video_test_build_0544_d.bin` | `b2627b3f8c0c10377debc7ecd8d7ada304bc74957a6a813d07c9083b81c0470a` |
| Score diagnostic | `rastan_direct_video_test_build_0544_s.bin` | `0056605cc5c3db92cfcfea3859f4d0958750f3db57559d736f20b6afd62f5fb0` |
| Display-off diagnostic | `rastan_direct_video_test_build_0544_do.bin` | `db5036458474d8213adde9b79e6971d6792377c587e630aedf3ee86e6eb03ce0` |
| Rack-advance cheat | `rastan_direct_video_test_build_0544_c.bin` | `53961fa24b102a8dfbd07fd1f90411065fae0020b91c20413ef423c5d51e3e27` |
| Full HUD | `rastan_direct_video_test_build_0544_full_hud.bin` | `448deb74171222e8172521cab1aa37f5b7f036c55e369a0c089a84e298868316` |
| Invincible normal route | `rastan_direct_video_test_build_0544_invincible.bin` | `1e42cbb7d46dfebb27e0c8be6812afac5a40db8f88881de78e099ab3f3f10449` |

## USA/NTSC Emulator Evidence

Platform: **GENESIS NTSC**, MAME `genesis`; PAL `megadriv` was not used.

- Mandatory trace: `states/traces/rastan_direct_video_test_build_0544_mame_30s_20261106_210414`.
- Gameplay-entry gate: `states/traces/build0544_gameplay_entry_gate_20261106_210403`.
- Phase-epoch gate: `states/traces/build0544_phase1_epoch_gate_20261106_210405`.
- Boss capture: `states/traces/prompt0102_build0544_r1s3_palette`.
- Observed stage `$0016`, one type-`0E` boss, five type-`0F` daggers, exact eight-frame state
  spacing, exact state-7 Line 1, and held final state.
- Screenshots show the entrance progression, fully illuminated red/gold boss, and active Flying
  Daggers. No unrelated visible recolor was observed within this bounded capture.

Existing project tools reused: supported `make test-subround ROUND=1 SUBROUND=3`, Makefile gates,
and the established PROMT-ID-0101 boss-fade MAME Lua capture.

New tooling created: none.

Why new tooling was necessary: not applicable; the established harness covered the evidence need.

## Known Unrelated Production Issues

No claim is made for R1-S2 stale/repeated Plane-A rows, Green Sword Knight geometry/residency,
reward palettes, R1-S2 hazard production palettes, broader R1-S3 natural-transition package
behavior, boss damage/death transient palettes, or the post-boss softlock. No audio behavior was
changed.

## Commit File Ownership

- `ba176405`: selected Test 2.0 profile integration, exact profile provenance, registry/source
  updates, and Test 2.0 file as supplied by Tighe.
- `9b5617dd`: selected palette assets ordered before assembly.
- `c62e66a5`: explicit Build 0544 generated evidence only.
- Documentation/log commit: reported in the final response because a commit cannot contain its
  own hash.

The Cody commits do not stage Andy's tool/Bestiary/hazard files, Tighe's dirty `Test.json` or
`profile_manifest.json`, unrelated runtime logs, or the superseded 0101 report. No GitHub push.

## Real-Hardware Acceptance

`REAL-HARDWARE ACCEPTANCE: PENDING TIGHE`

### USER MUST VERIFY

1. Use `_S1-3` to confirm the entrance starts dark, advances smoothly, ends with the intended
   red/gold full-bright boss, and keeps Flying Daggers on the same correct palette.
2. Use normal 0544 to enter R1-S3 naturally and confirm the scene palette/package and the existing
   R1-S2 -> R1-S3 boss-music transition remain correct.
3. Defeat the boss and confirm whether the known post-boss lockup still occurs; this task did not
   address it.
4. Check Rastan, the boss room, and visible effects for any unexpected recolor caused by the
   selected Test 2.0 global Line-0 organization.

STOP status: NO. Implementation and automated/GENESIS NTSC evidence are complete; hardware
acceptance is pending Tighe.

## Files / Commits / Logs

Production files changed by this resume are the selected-profile Makefile/source/spec/generator/
verifier set in `ba176405` and the dependency correction in `9b5617dd`. Generated Build 0544
evidence is in `c62e66a5`. This report and the append-only AGENTS_LOG entry are the final
documentation commit. ROMs remain in `dist/rastan-direct/`; runtime evidence remains under
`states/traces/`. Palette Composer changed by Cody: NO. Bestiary changed by Cody: NO. Green Sword
Knight tooling changed by Cody: NO. Andy hazard tooling changed by Cody: NO. Audio changed: NO.
GitHub push: NO.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0102`
