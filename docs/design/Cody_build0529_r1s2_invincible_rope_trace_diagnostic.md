# Build 0529 — invincible R1-S2 rope-trace diagnostic

Date: 2026-11-02  
Agent: Cody  
Task: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0057`  
Baseline: Build 0528  
Produced build: 0529, diagnostic candidate only

## Outcome

Build 0529 preserves Build 0528 production behavior and adds no renderer or gameplay code. Its
Makefile-owned `_invincible` family member uses the established original-arcade startup
configuration to assert `A5+$0040` bit `$0040`. The R1-S2 derivative then applies the existing
build-time selector `$DF` and Re-In-Carnation command `$27`. The same derivative is the input to
both manual trace modes.

Tool/source commit used to build the ROM family:
`1c53a3be1ea5b832058aeb204cd09cd6513cd428`. The production assembly is unchanged from Build 0528's
implementation commit `e667827c7ba776813e692d78b718887e10564fda`; commit `1c53a3be` adds only
external diagnostic tools.

Build counter advanced 0528 -> 0529. The consumed ledger records
`0529 PRODUCED ... [canonical=PASS entry=PASS epoch=PASS]`.

## Permanent artifacts

All artifacts are 3,792,568 bytes.

| ROM | SHA-256 |
|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0529.bin` | `0c3273ea9c429b1e5660e9567464b9bd6267022195d91d5cc58f9e66fada2b96` |
| `dist/rastan-direct/rastan_direct_video_test_build_0529_d.bin` | `82679a6b17ff06fc9dc56f701ee75134c7ff607fda28cd0e0244a0ccc3677727` |
| `dist/rastan-direct/rastan_direct_video_test_build_0529_s.bin` | `5330b85e65d0621120fc75d0fbef7c02f2aef288497720751e07cdb128cd1522` |
| `dist/rastan-direct/rastan_direct_video_test_build_0529_do.bin` | `99a0067a383ad25df1cacaa39102a8972baf6e2b064ffbbe78755df5679f9bae` |
| `dist/rastan-direct/rastan_direct_video_test_build_0529_c.bin` | `111b73f4d1fbaba11af88ce2d0dcfec57bee9b6fb326f0e4d4adad6b4672b4b7` |
| `dist/rastan-direct/rastan_direct_video_test_build_0529_full_hud.bin` | `e67b8d4fd8b38a20018a919722d8be80d24f71e7868147ae1e40390ac2d3f63c` |
| `dist/rastan-direct/rastan_direct_video_test_build_0529_invincible.bin` | `6b3f24e19a3109f6c99d5bf42c6624d11e0d174c87b05abb97aae1c2e91ad5d6` |
| `dist/rastan-direct/rastan_direct_video_test_build_0529_invincible_S1-2.bin` | `f47d3ed5c91e5e7a424de8f71e7f5622fbd8a71fbbf4a98e693992bbd8421e4a` |

The diagnostic derivative differs from its `_invincible` parent at exactly two bytes:

- ROM `$0508A3`: sound command `$25 -> $27` for natural R1-S2 Re-In-Carnation initialization;
- ROM `$05FF9F`: original stage selector `$FF -> $DF` for R1-S2.

Its invincibility configuration remains inherited from the verified parent.

## Invincibility semantic scope

The stock arcade cheat continuously asserts bit 6 at arcade `A5+$0040` (`$10C040`). Genesis
retained work RAM maps A5 to `$FF0000`, so the corresponding state is `$FF0040`. The existing
`_invincible` builder does not poll or force RAM each frame: it patches the source configuration
word to `$FFBF`, and the original retained startup sequence computes
`NOT.W / ANDI.B #$40 -> A5+$0040=$0040`.

The release verifier proved:

- standard `$FFFF -> A5+$0040=$0000`;
- invincible `$FFBF -> A5+$0040=$0040`;
- paired `A5+$0044` bit 7 and configuration bits 0..3 unchanged;
- all 66 final damage-dispatch pointers correct;
- no unrelated standard-versus-invincible ROM difference.

This suppresses ordinary health loss, hurt state, knockback, and enemy-contact death through the
original arcade gate. It does not rewrite jumping, rope attachment, acceleration, velocity,
facing, collision lookup, enemy AI, camera, or scroll. At an actual damaging contact the absence
of hit-stun/knockback necessarily changes the reaction compared with a vulnerable player. The
stock cheat explicitly warns that falling into water remains lethal.

## Architecture and protection

There is no production semantic cut in this task. Build 0528's cut remains
`arcade Plane-A semantic decision -> final Genesis name words`; the retired PC080SN chip tail
remains retired. No Plane A/B source, generated map, Composer asset, palette, sprite, audio engine,
movement, collision, checkpoint, DMA, or scroll source changed. The trace is host-side MAME Lua.

## Validation

- canonical gate: PASS; 228 opcode-replacement sites, expected coverage `$39DEB8`, delta `$50000`;
- boot, gameplay-entry, six Round-1 epoch/package and complete seven-variant-family gates: PASS;
- mandatory Genesis NTSC MAME trace: PASS, 1,798 frames;
- invincibility runtime-contract verifier: PASS, unrelated differences 0;
- R1-S2 derivative static verifier: PASS, exactly the selector/audio bytes above;
- established Genesis NTSC functional probe: PASS at frame 412, live stage `$0010`, record `$0011`,
  round 1, selector byte `$DF`, Plane A/B 2,048 nonzero sampled words each, native map misses 0;
- both interactive launcher modes: smoke-start PASS using the exact diagnostic ROM;
- comparator: execution PASS on the two smoke captures.

The smoke runs were headless and did not substitute for manual gameplay. The interactive default is
visible 640x448 MAME with sound where available.

## Status

Candidate diagnostic only. It does not fix or diagnose the intermittent corruption by itself.
Tighe's two complete manual playthroughs determine whether and where corruption occurs. Water/fall
death remains a known limitation of the arcade-equivalent invincibility gate.

