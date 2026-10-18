# Cody — Build 0442 invincible runtime-contract repair

**Date:** 2026-10-17

**Baseline:** accepted standard Build 0441, source
`9f07b5dca86f445033247ec79fb92959a3832512`, ROM SHA-256
`43fc0aa15f02549661ce438f71657914cbfed08e655c510caaa85dd80f393337`.

## Hardware-proven defect and first divergence

Build 0441 standard is accepted on real Genesis hardware: enemy contact damages Rastan, produces
the hurt response, and repeated attacks can kill him. Its `_invincible` auxiliary variant was
hardware-proven ineffective and remained vulnerable.

The actual Build 0441 ROM bytes prove the first divergence. Arcade startup `0x03AFEE` maps to
runtime `0x03B1EE` and contains `30 39 00 05 FF 9E`: `MOVE.W (0x0005FF9E).L,D0`. Both the standard
and `_invincible` ROMs contain `0xFFFF` at that stale address. After `NOT.W` and the bit-6 mask,
both therefore store `0x0000` to `A5+0x0040`.

The existing variant patch was not applied to the wrong copy. It correctly changed the relocated
configuration word at `0x05FFD4` from standard `0xFFFF` to `_invincible` `0xFFBF` (patched byte
`0x05FFD5`). The retained startup `MOVE.W` operand was the stale part: its opcode class was not in
the automatic absolute-ROM operand scanner, so it continued to read the old arcade address after
whole-maincpu relocation and shift reflow. The paired `A5+0x0044` initializer at runtime
`0x03B1FE` had the same stale operand.

## Repair

Two declarative, shift-aware operand relocations now cover arcade `0x03AFEE` and `0x03AFFE`.
Both final instructions read the authoritative relocated configuration word at `0x05FFD4`. The
instructions remain six bytes and execute with identical cost; no standard-build runtime work,
polling, per-frame forcing, damage bypass, HP logic, collision suppression, or Genesis-owned
invincibility mechanism was added.

The original arcade sequence remains authoritative:

- standard `0xFFFF -> NOT 0x0000 -> bit 6 0x0000 -> A5+0x0040=0x0000`;
- `_invincible` `0xFFBF -> NOT 0x0040 -> bit 6 0x0040 -> A5+0x0040=0x0040`;
- bit 7 feeding `A5+0x0044` is unchanged;
- configuration bits 0–3 are unchanged;
- ordinary damage still reaches the retained relocated handler, whose original `A5+0x0040` gate
  returns before energy loss/hurt/knockback only in `_invincible`.

The static verifier now follows the actual final-ROM startup operand and reads the word it names,
computes both gate results, checks the paired bit-7 input and bits 0–3, checks allowed ROM
differences, and independently verifies all 66 final damage-dispatch pointers against the original
table plus the authoritative address-map shift relation. It no longer treats a manifest-only
variant write as proof of runtime behavior.

## Build 0442 validation

- Complete family: canonical, `_d`, `_s`, `_do`, `_c`, `_full_hud`, `_invincible` — PASS.
- Canonical and gameplay-entry gates — PASS; known seven-epoch warning remains non-blocking.
- Standard fixed 30-second Genesis NTSC trace — PASS, 1,798 frames:
  `states/traces/rastan_direct_video_test_build_0442_mame_30s_20261017_220456/`.
- Final-ROM invincibility contract — PASS: runtime `0x03B1EE`, read address `0x05FFD4`, standard
  result `0x0000`, `_invincible` result `0x0040`, `A5+0x0044` unchanged, bits 0–3 unchanged,
  damage table 66/66.
- Standard Build 0442 differs from accepted standard Build 0441 at only checksum `0x018F`, the
  two startup operand low bytes `0x03B1F3`/`0x03B203`, and build digit `0x2928DB`.
- `_invincible` rope benchmark: `798 / 798 / 798`, deterministic YES, median `13,317.147 ms`.
  Evidence: `states/traces/build0442_rope_attach_benchmark_invincible/`.

Artifacts:

- standard: `dist/rastan-direct/rastan_direct_video_test_build_0442.bin`, 2,698,936 bytes,
  SHA-256 `76cdf3f0e7b515a227ca7e58b168481d2cdbb9dad0d50f6d1805472b6c1f9284`;
- `_invincible`: `dist/rastan-direct/rastan_direct_video_test_build_0442_invincible.bin`,
  2,698,936 bytes, SHA-256
  `865e611c56068ba080fe927e163d0e1515ad153fc3145541153b92436241161b`.

## Real-hardware acceptance

**BUILD 0442 ACCEPTED BY TIGHE ON REAL GENESIS HARDWARE — 2026-10-17.**

- Accepted source commit: `c7ca1439e5cad8028043e8b3ff56fe7282addb1d`.
- Accepted standard ROM SHA-256:
  `76cdf3f0e7b515a227ca7e58b168481d2cdbb9dad0d50f6d1805472b6c1f9284`.
- Accepted `_invincible` ROM SHA-256:
  `865e611c56068ba080fe927e163d0e1515ad153fc3145541153b92436241161b`.
- Hardware result: standard enemy damage/hurt/eventual death remains restored; `_invincible`
  correctly suppresses ordinary enemy-contact damage through the original arcade gate.
- Accepted `_invincible` rope result: `798 / 798 / 798`, median `13,317.147 ms`.
- Accepted ref: `accepted/build-0442`.
