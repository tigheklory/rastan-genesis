# Build 0525 Plane A respawn completion

Identifier: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0044`

This continuation resumed the interrupted PROMT-ID-0043 work on branch `rastan-direct-proposal` at
HEAD `c7ac1f1c`, preserving the uncommitted descriptor-cadence/saved-selector work, diagnostic traces,
and numbered Builds 0522–0524. No reset, cleanup, rollback to `4ee94e06`, or unrelated Palette
Composer/audio/sprite change was performed.

Implementation commits are `c7ac1f1c` (initial live-producer restoration) and `59260a9e` (final
descriptor cadence, saved selector, stale-condition root-cause fix, coverage invariant, and evidence
tooling). The preserved pre-task source snapshot remains `4ee94e06`.

## Final Build 0524 root cause

The first bad write occurs inside `genesistan_hook_tilemap_plane_a_selector0_native` during the
post-camera `$050538` replay. Build 0524 loads authored logical code `$1731` into D3 and then loads its
valid authored attribute `$0000`; the next `BEQ` sees the attribute load's Z flag and skips the active
LUT (`$1731 -> $0301`). The selector-0 staging store therefore writes unresolved `$1731`. Helper-exit,
settled staging, and VDP VRAM captures all contain the same 14 bad words, disproving the later-camera
overwrite hypothesis.

The minimal fix is `TST.W D3` before the blank branch. It repairs the shared selector-0 translation
boundary and does not special-case code `$1731`, the 14 coordinates, R1-S2, or a checkpoint.

Full first-writer addresses, all 14 coordinate/descriptor identities, before/after words, architecture,
and verification evidence are in
`docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0043_plane_a_respawn_population_restoration.md`.

## Verification and delivery

- R1-S1, R1-S2, and R1-S3 initial authored-name comparisons: 0 mismatches.
- All three staging buffers equal actual Plane A VDP VRAM.
- R1-S2 has 0 remaining `$1731` words; active slot `$0301` references the correct authored pattern.
- R1-S2 selector-1 Y=`$013F`: 0 entering-row, VDP, Plane B, pattern, LUT, or collision mismatches.
- Death/respawn route: PASS through 3 deaths and 2 restarts; staged and actual VRAM rings match.
- Canonical gate, gameplay-entry gate, seven-epoch gate, mandatory Genesis NTSC trace, and all seven
  standard variants: PASS.
- Direct R1-S2 Re-In-Carnation: command `$27`, intro/loop observed, zero bank mismatches, unchanged
  Build 0521 payload bytes.

Candidate ROM: `dist/rastan-direct/rastan_direct_video_test_build_0525.bin`

Size: 3,792,568 bytes

SHA-256: `e5f9b01205ed4a7d535488ab8b5da88522f9df33eeae70ca7d0261a694cbf98d`

Build counter: `0525`

Direct test derivatives:

- R1-S2: `dist/rastan-direct/rastan_direct_video_test_build_0525_S1-2.bin`, SHA-256
  `12a90eb5c1b94d6a98742b26d2ccac3aa63de093d5d6aad75d0b51185d802491`.
- R1-S3: `dist/rastan-direct/rastan_direct_video_test_build_0525_S1-3.bin`, SHA-256
  `a6da6793afc621eaf73f4242974abdee6aa8786e5037e171c3ffeae52dbd9194`.

Build 0525 is a candidate, not an accepted build. The automated package gate proves record `$000B`
uses package 10 with a complete LUT, but only Tighe can verify actual checkpoint respawn behavior.
Tighe should also test later R1-S2 climbing/scrolling and R1-S3 before acceptance.
