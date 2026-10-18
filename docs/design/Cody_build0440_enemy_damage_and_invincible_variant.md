# Cody — Build 0440 enemy damage and invincible benchmark variant

**Date:** 2026-10-17
**Status:** **REJECTED on real Genesis hardware** — standard enemy contact still caused no damage,
hurt animation, or knockback. The `0x054A40` WRAM rebase is correct but insufficient: Build 0440
did not relocate the 66 embedded handler pointers in dispatch table `0x0550A8`.
**Exact candidate source commit:** `ba4b4c2264993b53193a8067eece3bb9faa71e63`

## Scope and result

Build 0440 corrected one required absolute WRAM operand but **did not restore** the complete retained
original-arcade enemy-to-player damage chain. It also added a permanent, normal-display `_invincible`
build variant for the canonical Genesis rope benchmark. The standard ROM is rejected.

No damage rule, collision test, body-hit producer, dispatcher, handler, hurt/knockback routine, or
post-hit invulnerability rule was replaced. No graphics code was changed.

## Damage address-contract repair

The exact byte-neutral `opcode_replace` in `specs/rastan_direct_remap.json` is:

| Field | Value |
|---|---|
| arcade PC | `0x054A40` |
| original instruction | `LEA 0x0010D2A8,A0` |
| original bytes | `41F90010D2A8` |
| Genesis instruction | `LEA 0x00FF12A8,A0` |
| replacement bytes | `41F900FF12A8` |
| Build-0440 runtime Genesis PC | `0x054ABE` |

The current `address_map.json` is authoritative for the runtime mapping. The final standard ROM at
`0x054ABE` contains `41 F9 00 FF 12 A8`; the stale `0x0010D2A8` operand is absent at that site.
The established sibling repair remains `0x054B1E -> 0x054B9C`, with final bytes
`41 F9 00 FF 12 C8`.

The same address map shows the surrounding arcade-owned chain remains copied code:

| Arcade owner | Build-0440 runtime PC | Status |
|---|---:|---|
| body-hit producer `0x0449B4` | `0x044BB4` | unchanged arcade copy |
| consumer `0x054A40` | `0x054ABE` | only repaired site |
| dispatch `0x0550A8` | `0x055126` | unchanged arcade copy |
| gated handlers `0x0551CC+` | `0x05524A+` | unchanged arcade copy |
| hurt/knockback `0x05560C` | `0x05568A` | unchanged arcade copy |

A byte comparison of accepted Build 0439 and standard Build 0440 found only the Genesis checksum,
the two operand bytes at the repaired consumer, and the crash-screen build-number digits. Thus the
producer, dispatch, damage handlers, energy decrement, hurt/knockback, and post-hit invulnerability
code are unchanged.

## Permanent `_invincible` variant

**Superseded by Build 0442:** real-Genesis testing proved the Build 0440/0441 implementation below
ineffective. The variant patch reached relocated ROM byte `0x05FFD5`, but the startup instructions
still read stale absolute address `0x0005FF9E`; both standard and `_invincible` consequently stored
zero to `A5+0x0040`. Build 0442 shift-relocates the two startup operands to the authoritative
configuration word at `0x05FFD4`. See
`docs/design/Cody_build0442_invincible_runtime_contract_repair.md`.

The build-family flag is `RASTAN_INVINCIBLE ?= 0`. Every standard and pre-existing variant declares
it as zero. The sole normal-display `_invincible` family member declares it as one and shares the
canonical build number.

Static provenance found one writer of `A5+0x0040`: startup at arcade `0x03AFEE..0x03AFFA` reads the
configuration word at `0x05FF9E`, applies `NOT.W`, masks bit 6, and stores the result. The separate
`A5+0x0044` initializer at `0x03AFFE..0x03B00A` reads the same word but masks bit 7. Other readers of
the configuration word use only bits 0-3.

The spec-declared invincible-only data patch changes arcade source byte `0x05FF9F` from `0xFF` to
`0xBF` (Build-0440 ROM PC `0x05FFD5` after shift reflow). The original initializer therefore writes
`0x0040` to `A5+0x0040`. Bit 7 and bits 0-3 do not change, so `A5+0x0044` and the other configuration
consumers remain unchanged. The standard ROM retains `0xFF` and initializes `A5+0x0040` to zero.

This adds no runtime instruction or branch to the standard ROM and no poller to either ROM. In the
invincible variant, overlap, body-hit production, body-hit consumption, and handler dispatch all
execute; the unchanged handlers take their original `A5+0x0040` skip branches. Pits, water, terrain,
timeout, and any other mechanism not gated by that arcade flag are not independently suppressed.

The original Build 0440 `verify_invincible_variant.py` proved only the declared source patch and
allowed ROM differences; it did not follow the final runtime instruction to the address actually
read. Its PASS was therefore insufficient and is superseded by the Build 0442 final-ROM verifier.

## Build artifacts

All seven family artifacts were produced under Build 0440. The counter advanced `439 -> 440`; no
second number was consumed.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `rastan_direct_video_test_build_0440.bin` | 2,698,936 | `3c1b1bbd60a7b25af53e4eea2a643460467d2209abbd88bf9b9fcedf7cf0c6b7` |
| `rastan_direct_video_test_build_0440_d.bin` | 2,698,936 | `c3a6c052eb4e67d2facf16c75987f2bb8f78043c0728d2814da0cd875e785da6` |
| `rastan_direct_video_test_build_0440_s.bin` | 2,698,936 | `9959f28ef6413226e01c9d812b76a21f8143d059daa6b0727bf31e9bab6b4aa7` |
| `rastan_direct_video_test_build_0440_do.bin` | 2,698,936 | `1a278394607514f2529db6fc0a2274e4fcf5d34fcef4725cafbc51dd71ff6524` |
| `rastan_direct_video_test_build_0440_c.bin` | 2,698,936 | `275c20eae7a3de840fb68a9691f26cfc41d7b186fd3915b7c32e3b48237a4aa5` |
| `rastan_direct_video_test_build_0440_full_hud.bin` | 2,694,840 | `950a5239b0e38aa98cbcddcf91734b4bda7645ff56c4341910fee87ab79bb2f1` |
| `rastan_direct_video_test_build_0440_invincible.bin` | 2,698,936 | `d689a1a7dfe50d2b5714e534398f648197059a38cc9441247d94c6cbe8715a3a` |

The initial in-build canonical gate invocation reported a stale expected site count of 231 in
`verify_canonical_rom.py`; the spec and postpatcher correctly reported 232. Updating that verifier
constant and rerunning it against the already-preserved standard Build-0440 bytes produced
`GATE_PASS`. Gameplay-entry passed. The standing Phase-1 epoch gate remained non-blocking `FAIL`.
The unchanged standard Genesis NTSC 30-second trace completed at 1,798 frames:

`states/traces/rastan_direct_video_test_build_0440_mame_30s_20261017_171458/`

## Rope benchmark

The unchanged existing route was run three times in Genesis NTSC MAME on
`rastan_direct_video_test_build_0440_invincible.bin`:

- trials: `799 / 799 / 799`;
- deterministic: **YES**;
- median: `13,333.835 ms`;
- versus historical Build 0439: `+1 frame`, `+16.688 ms`, `+0.125%`;
- versus arcade silver standard: `+28 frames`, `+483.835 ms`.

Evidence: `states/traces/build0440_rope_attach_benchmark_invincible/`.

Build 0439's consumer was broken and skipped the live body-hit list. Build 0440 `_invincible`
executes the restored consumer/dispatch/handler path and exits through the original arcade gate.
The one-frame delta is therefore recorded as restored arcade gameplay work, not automatically as a
graphics regression. This `799` result is the new post-damage-restoration Genesis rope baseline for
future work, subject to acceptance of Build 0440.

## USER MUST VERIFY — standard Build 0440 on real Genesis

Tighe must test the unsuffixed standard ROM and confirm:

- enemy contact visibly produces hurt and knockback;
- continuing contact does not drain energy every frame;
- temporary post-hit invulnerability and later recovery occur;
- a later contact can damage Rastan again and sufficient damage can kill him;
- Rastan can still kill enemies;
- terrain, pits, water/lava, scrolling, and sprites remain normal.

The reduced HUD still hides the energy bar; that is expected. Tighe may optionally check the
`_invincible` ROM to confirm ordinary enemy contact causes no gated damage/hit-stun/knockback while
ungated hazards retain their original behavior.

Real-hardware acceptance of standard Build 0440: **REJECTED BY TIGHE**. See
`docs/design/Cody_enemy_damage_actual_root_cause_and_repair.md` for the first remaining divergence:
unrelocated absolute-long dispatch pointers at arcade table `0x0550A8`.
