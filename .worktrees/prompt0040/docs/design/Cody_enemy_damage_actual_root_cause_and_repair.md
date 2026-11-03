# Cody — Enemy damage actual root cause and repair

**Date:** 2026-10-17

**Baseline:** standard Build 0440 (`3c1b1bbd60a7b25af53e4eea2a643460467d2209abbd88bf9b9fcedf7cf0c6b7`)

**Hardware result:** Build 0440 rejected: enemy contact produced no damage, hurt animation, or knockback.

## Proven arcade frame order

The gameplay frame owner `0x041F0E` first calls player update `0x05100A`. That routine calls the
damage/event consumer `0x054A2C` at `0x05107C`. Actor update then runs, followed by collision manager
`0x0449B4` at `0x041F20`. Thus the consumer intentionally reads the **previous frame's** list;
`0x0449B4` then clears all four active words at `A5+0x12A8` and `A5+0x12C8` (`0x0449BA..0x0449CE`)
and produces the next frame's records. No intervening writer erases a produced record.

Pass 1 (`0x0449DC..0x044A6C`) scans 29 actors at `A5+0x02C8`, selects each hurtbox through
`0x0446BC`, tests it against the player coordinates `A5+0x10BE/+0x10C0` through
`0x044930 -> 0x044C6C/0x044C72 -> 0x044CBA`, and writes up to four eight-byte records to
`A5+0x12A8`: word `+0=1`, word `+2=0x01TT`, word `+4=actor X`, word `+6=actor Y`. `TT` is actor
byte `+0x29`, not the constant high byte. Normal-difficulty Lizardman template `cfg_28=0x0301`
therefore supplies `TT=1`. Later passes use `A5+0x12C8` for the secondary item/status class; the
weapon/projectile pass begins at `0x044BA6`. The prior C comments that called byte `+2` the type
were endian-wrong and are corrected with this repair.

Build 0440 retains the same order at runtime PCs `0x04210E -> 0x051210 -> 0x054AAA`, followed by
the retained collision producer at `0x044BB4`. Its A5-relative actor, player-box, and record writes
remain mapped to Genesis WRAM. The corrected consumer at runtime `0x054ABE` contains
`LEA 0x00FF12A8,A0`; its four-record loop, eight-byte stride, active test, low-byte type read, and
range checks match the producer.

## First remaining divergence

The consumer converts type 1 to table index 0 and at runtime `0x054B86..0x054B94` loads an absolute
long pointer from the relocated table base `0x055126`. The table itself is arcade
`0x0550A8..0x0551AF`: exactly 66 four-byte code pointers, ending immediately before handler/default
code at `0x0551B0`.

Build 0440 relocated the table base and the handler code but copied **all 66 embedded pointers
verbatim**. Entry 0 still contains arcade `0x000551CC`; the authoritative address map places that
handler at Genesis `0x0005524A`. Consequently ordinary Lizardman contact jumps into the relocated
table data at `0x000551CC` and never reaches the intended handler. The intended handler's gates
(`A5+0x0040`, `A5+0x1366`, `A5+0x12F0`, `A5+0x130E`), energy subtraction at `A5+0x013A`, flags at
`A5+0x12FC/+0x1366/+0x1368`, and hurt reaction `0x05560C` were therefore unreachable through this
dispatch. No additional wrong WRAM literal is upstream of this first divergence.

The Build 0440 conclusion was **partially correct**: rebasing `0x0010D2A8 -> 0x00FF12A8` was
required, but it was not the sole root cause.

## Repair

Build 0441 adds one declarative `absolute_long_pointer_tables` rule for arcade table `0x0550A8`,
66 entries, four bytes each. The established shift-table pipeline relocates every in-window target
through `address_map.json`; it adds no runtime code, collision rule, forced damage, fallback, shadow
state, NOP, or bypass. The semantic chain remains arcade-owned.

Validation requirements are the normal canonical/build-family gates and standard fixed 30-second
Genesis NTSC trace. Real-hardware confirmation of actual contact damage, hurt, knockback,
post-hit invulnerability, recovery, and death remains Tighe-owned.

## Build 0441 result

- Standard ROM: `dist/rastan-direct/rastan_direct_video_test_build_0441.bin`
- Size: 2,698,936 bytes
- SHA-256: `43fc0aa15f02549661ce438f71657914cbfed08e655c510caaa85dd80f393337`
- Generated manifest: table `0x0550A8`, runtime `0x055126`, `66/66` pointer fixes.
- Independent ROM check: all 66 final entries equal their authoritative `address_map.json` targets;
  entry 0 is `0x0005524A`.
- Canonical gate: PASS. Gameplay-entry gate: PASS. Standing seven-epoch gate: known non-blocking FAIL.
- Standard fixed 30-second Genesis NTSC trace: PASS, 1,798 frames, no reported exception.
- Build-family verification: PASS for canonical, `_d`, `_s`, `_do`, `_c`, `_full_hud`, and
  `_invincible`. The `_invincible` feature was not investigated, changed, benchmarked, or validated
  beyond the Makefile's mandatory family mechanical check.
- Real-Genesis enemy-damage acceptance: **ACCEPTED BY TIGHE ON REAL GENESIS HARDWARE**, 2026-10-17.
  Enemy contact reduces health, the hurt response occurs, and repeated attacks can kill Rastan.
  Accepted source commit: `9f07b5dca86f445033247ec79fb92959a3832512`; accepted ref:
  `accepted/build-0441`.
- Known auxiliary defect accepted separately: the Build 0441 `_invincible` family variant behaves
  like the standard build and remains vulnerable. This does not reject the standard Build 0441
  damage repair; the variant defect is scoped to the follow-up Build 0442 repair.
