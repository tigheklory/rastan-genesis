# PROMPT-ID-0033 — Build 0519 authored-palette restoration

## Result

Build 0517's severe color regression was a palette implementation/configuration
bug, not a bad Palette Composer decision: the normal build compiled
`vdp_install_test_lines` with `RASTAN_PALETTE_TEST_PROFILE=0`, so the authored
R1-S1/R1-S2 installer body was absent and gameplay retained fallback/frontend
CRAM. The correction makes the saved P1 profile the normal build authority.
No saved palette decision, gameplay source, checkpoint logic, map/ring logic,
scrolling, collision, tile identity, or audio payload was changed.

Build 0519 is a candidate for Tighe's visual judgment. It is not accepted and
does not claim overall visual correctness.

## A. Preservation status

- Active branch/HEAD at isolation: `rastan-direct-proposal`,
  `122f4ae02111aa436c614a0803c8a6d6f0ae1f40`; the active dirty tree was not
  reset, cleaned, stashed, or broadly checked out.
- Recoverable pre-change capture: `/tmp/rastan-prompt0033-preserve-i9ySyl`.
  - tracked patch: `4c9a80161724eb8cbceeb4aeaf99c3637ec8b10e2c453b403554c15b4ee960f8`
  - ROM-producing inputs/assets archive:
    `8061dcfd98b460702cb621f3723a086f0f7f71b5aa42e3cbf1f1320049f68351`
  - status record: `63337dfab47bd19a9cac3bbdfdadb44ef481f092e95abfa7c83a3451f9c90d0a`
- Isolated repository: `/tmp/rastan-prompt0033-isolated`.
- Exact tracked source commit:
  `ca8b33340a4c6bc2f8bd754187b10826c1d79080`, parent
  `122f4ae02111aa436c614a0803c8a6d6f0ae1f40`.
- Durable source receipt:
  `states/source_snapshots/build_0519_prompt0033/README.md` plus binary
  format-patch SHA-256
  `4389e3dc688f5eb57ac5b7b8afc185e042a680e0e9b74bb954833492018031a7`
  and preserved Build-0517 audio archive SHA-256
  `d46b283ec80848ac86736dce1b2974dd569d5d228ed36cf78f342438cf8b00e5`.
- Reference ROMs remained present:
  - 0503: `d8c2cd1aee9d78efb8ec2c780161d21119c03a96a734f2887126b2530b02297d`
  - 0508: `6cd134226f82cfb6d4c7c3929f7297d1fefd2bd998eb36a7b6780603b136674a`
  - 0512: `d56fd9a1580bce57fb1b700bb1c850573a4bef31098587e4efc03a1c3764e574`
  - 0514: `7547fafb697a72988b65a9e88acdffc728749fe9542b231d8503bb7ee733a04c`
  - 0517: `4848935bd926bcbcb1a4d6a8a277ccec9d88582148702e3a1c5938922607d57e`

## B. Palette provenance

P0 (`Test.json` SHA-256
`30dab473b12dd99e48db2528b2c3c634eefe4cb03f563c9b0ec25b0d1a43d755`)
and P1 (`86505de8a7566e0a13a083bf6b3715fa61eb9242102091aadb589d7583cde9fb`)
were compared byte-for-byte and semantically.

P1 does not change the four global target palette lines or any of P0's existing
sprite/object mappings. It:

- adds six Line-2 object mappings for two rewards and four death/effect objects;
- adds the R1-S2 Castle context with 517 Plane-A mappings on Line 3;
- removes five empty global Line-3 Plane-A mappings (`LA-0000`, `LA-0001`,
  `LA-0500`, `LA-0633`, `LA-0836`) while localizing Castle policy;
- adds read-only Line-2 display/animation metadata and clarifies Line 2 remains
  arcade-controlled; and
- leaves the complete R1-S1 context policy byte-identical to P0.

These are preserved saved authoring choices. Their precise human intent is not
reconstructed, so no authorship attribution or decision rollback is made. No P1
decision was found to be intrinsically wrong. The defect was that Build 0517 did
not consume P1 at runtime.

Build-0519 generated identities:

| Input/output | SHA-256 |
|---|---|
| `Test.json` | `86505de8a7566e0a13a083bf6b3715fa61eb9242102091aadb589d7583cde9fb` |
| `palette_decisions.json` | `2780a06f60905ae1f95907b1b0dbf8ece94affc7da9219394bda880ef2a4da47` |
| CRAM Line 0 | `273ab974ec8c85f4594878a39702d106614d4c7bbb601f667c7234165d99ecaf` |
| CRAM Line 1 | `3cb995de81b06aa89d9ae3408a6953736c2b8e7437f0c134a222cf47afe2f4d5` |
| CRAM Line 3 | `637a34db76429fc7c88917b1b7b0ef07da575f2d728238907aa0923d73f3714f` |
| R1-S1 scene CRAM (Lines 0/1/3) | `fa7147d883dc5a4899bed2d59520441ebfef159b6cfc78d9a06db24ee0a65ebe` |
| R1-S2 scene CRAM (Lines 0/1/3) | `281f9f38c8e58101f6c01aa5d5578605313949ea9e32e26f287355a19767c26d` |
| native PC080SN pattern region | `bddda369992a077a243c1de3dcb0e666eb5bae5315bb43f2ef72e9b238226d27` |
| palette scene selector | `646b33f903988ebc05ae6b6fa794ca87a4458256f50d6ae02fa854b920fd4a91` |
| PC090OJ editor region | `12460aab49d2e4e0cd7b5ce05fd6b8f8cc22e4e1d775522201c2395dc2cfa32a` |
| PC090OJ palette-line LUT | `ea10dec43d7260a98c74c60220ea260eb6ffc5d800a3b53e09797ff1e06c3c51` |

## C. First proven color divergence

Controlled history:

- 0503→0504: P0 did not change; this brackets the separate checkpoint/map
  regression, not a palette-input regression.
- 0508→0512: both use P0; changes are authored native-visual integration.
- 0512→0513: source profile changes P0→P1, but P1 retains R1-S1 and global
  target colors; this is not itself proof of corruption.
- 0514 used `RASTAN_PALETTE_TEST_PROFILE=1` and installed authored scene CRAM.
- 0516/0517 build configuration omitted that flag. 0517 is the earliest
  surviving runnable ROM directly proven to contain the fault (0516 is consumed
  but invalid for acceptance).

At ROM `0x070204`, Build 0517's `vdp_install_test_lines` only clears diagnostic
state and returns. The stage lookup, scene-asset selection, three 16-word copies,
and palette-dirty publication are absent. Its captured 64-word CRAM is:

- SHA-256 `33cfa081efa694f58413e4e111474267bc9a2f971b6af88f9e18f6687b001234`
- Line 0: `0000 0EEE 000E 0468 08AC 046A 0246 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE 0EEE`
- Line 1: `0000 000E 000E 000E 000E 000E 000E 000E 000E 000E 000E 000E 000E 000E 000E 000E`
- Line 2 remains the arcade-controlled sky line.
- Line 3 is fallback/frontend data, not the P1 R1-S1 scene asset.

The first wrong transformation is therefore
`apps/rastan-direct/Makefile`'s profile-off compile setting, which removes the
existing `apps/rastan-direct/src/palette_hooks.s:vdp_install_test_lines` body.
It is category A (authored palette installation omitted), not a category-B tile
identity change and not a category-C authored difference.

## D. Correction

Only `apps/rastan-direct/Makefile` was behaviorally changed for this task:

- lines 94–104: default `RASTAN_PALETTE_TEST_PROFILE` to 1 while retaining an
  explicit override; select the strict profile-on ROM-size invariant;
- the eight postpatch/canonical-gate call sites now consume the named coverage
  value instead of a profile-off literal.

The coverage values are gate accounting only. The sole runtime change is that
the already-existing scene palette/index pipeline is compiled and linked.
`Test.json`, `palette_decisions.json`, Palette Composer, palette conversion,
gameplay, checkpoint restoration, `0x050538`, scene maps, ring initialization,
scrolling, collision, residency, tile-source identity, and actor code were not
edited by this correction.

Semantic cut remains:

`retained scene/stage decision → offline authored P1 palette/index preparation → final Genesis pattern/name/SAT data + staged CRAM → VDP DMA`.

No new graphics boundary was introduced. The retired chip tail remains the
per-write PC080SN/PC090OJ/CLCS execution below that semantic boundary; no shadow
tilemap, runtime pixel reindexer, or compatibility device was added.

## E. Validation

Build 0519 (`GENESIS_COVERAGE_DELTA=0x90000` to retain the exact Build-0517
audio payload) passed:

- pre/post boot guards and canonical `GATE_PASS`;
- gameplay-entry gate (570 external frames, gameplay/player control observed,
  zero address/bus/illegal/crash-handler events);
- six Round-1 epoch cases, full Plane-A LUT and fixed Plane-B LUT checks;
- native metatile, Plane-B visual-record, collision/visual independence,
  title, HUD, item, palette-family, selector-stream, and final-life gates;
- mandatory 30-second Genesis NTSC MAME trace; and
- complete seven-ROM family verification.

Hardware-state captures are under
`states/traces/prompt0033_build0519_palette/`:

- R1-S1: stage `0x0000`, active record `1`, package `0`; actual CRAM equals
  staged CRAM and Lines 0/1/3 equal the authored scene asset byte-for-byte.
  CRAM SHA-256:
  `0d08b515e99f5c1a8c8eff2c29401ad3558b95d5ce7b1b4bbeba971bf02cb7e3`.
- R1-S2: stage `0x0010`, active record `17`, package `5`; actual CRAM equals
  staged CRAM and Lines 0/1/3 equal the independent Castle scene asset
  byte-for-byte. CRAM SHA-256:
  `0cd324a48a3d9c788e7df285be648b3002ed95745bbb8d37cb612e3e1577c1d6`.
- Captured name-word palette bits: R1-S1 Plane B is Line 2 for all 2048 cells,
  Plane A is Line 3 for all 2048 cells; R1-S2 Plane B remains Line 2, while
  Plane A has 2034 Line-3 and 14 Line-0 cells. Captured active SAT palette-line
  distributions are R1-S1 `{0:12, 1:16, 2:2}` and R1-S2 `{0:22, 2:6}`.
- Actual VRAM hashes are `6adee6a644c42101bab2bb2086aa30bdd01e47d01048847805b2d61b4d381dd5`
  (R1-S1) and `1a9ba27415511a534b4cb2eaca42b84eab741cd5a785d62442d85948e0d676d6`
  (R1-S2).

The profile-on build intentionally changes the offline index-remapped PC080SN
artifacts (`native_pattern_region`, scene/pan/record maps,
`authored_descriptor_visuals`, boundary packages/constants/report,
`palette_scene_select`) plus `palette_hooks.o` and address/layout metadata.
The three global CRAM-line binaries, PC090OJ editor region, PC090OJ palette LUT,
saved P1 profile, and palette registry are unchanged. Full LUT gates prove the
changed map/pattern outputs retain their source identities and geometry while
applying the authored index permutations.

An initial 0518 build refreshed a concurrent audio profile and was rejected for
this prompt, although it passed palette/runtime gates; it remains preserved as
consumed. Build 0519 restores the archived 0517 audio inputs. All nine linked
native track payloads compare byte-for-byte with Build 0517 (individual sizes
and SHA-256 values match), and the Z80 driver remains
`3a5e0c27a692544de0c9f36f6f6472ee18f637c93277adc63e3e3a408c7a464c`.

Candidate artifact:

- `dist/rastan-direct/rastan_direct_video_test_build_0519.bin`
- SHA-256 `ab34fc39a1cf635e0cdd1c69a37b6e0d46eab90f4ec1104bf7e2962eced43706`
- size 4,054,712 bytes (below 4 MiB)
- counter/ledger 519
- R1-S2 derivative SHA-256
  `7b5aa95dd951972f730b7380c1e4413ad0279f901304ee4a8a1214bd4a9a0de8`

## F. Remaining defects and acceptance boundary

- R1-S1 segment-4 checkpoint Plane-A restoration remains unresolved by this
  task. Build 0519 intentionally retains the same checkpoint architecture.
- R1-S2 later-chain behavior remains unaccepted.
- Wrong scenery caused by any remaining graphics-identity defect is not fixed by
  this palette correction.
- CRAM/VDP evidence proves the saved profile is now installed and selected, but
  final aesthetic correctness of Tighe's custom colors remains Tighe's manual
  judgment in RetroArch/BlastEm or hardware.
- Build 0519 is a candidate only; it is not declared accepted.
