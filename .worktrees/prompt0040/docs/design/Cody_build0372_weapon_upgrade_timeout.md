# Cody — Build 0372 Weapon Upgrade Timeout

## Result

Build 0372 restores the arcade duration-tier input used by the one shared melee
weapon expiry routine.  The expiry code itself was intact: it advances
`A5+0x1326`, compares it with the duration selected by `A5+0x1418`, then clears
the timer and restores `A5+0x12FA` to normal SWORD state `1`.  Genesis instead
computed `A5+0x1418` from two stale absolute arcade-WRAM reads that addressed ROM.

This task changes that one address contract only.  It does not change weapon
grant logic, rendering, collision, rope, water, cave, READY cleanup, or the
Build 0371 fireball correction.

## First divergence and root cause

Original `0x051102` builds the duration tier from the live score bytes at arcade
WRAM `0x0010C11E/0x0010C11D`, walks thresholds `{0x0010, 0x0030, 0x0060,
0x0100}`, and stores the resulting tier `0..4` at `A5+0x1418`.

Build 0371 retained both absolute operands:

```asm
051102  move.b  0x0010C11E,D0
051108  lsl.w   #8,D0
05110A  move.b  0x0010C11D,D1
...
05112A  move.w  D2,(0x1418,A5)
```

Those addresses are cartridge ROM on Genesis.  Both bytes are `0x0F`, producing
`0x0F0F`, exceeding every threshold and forcing tier `4`.  The melee limit was
therefore `0x1518` ticks instead of the original startup-score tier-0 limit
`0x0BB8`.  This is the first Genesis/original divergence on the requested path.
The timer was not stuck; it was assigned the wrong, much longer duration.

## Original acquisition and expiry semantic

The retained grants at `0x054EC6`, `0x054EDC`, and `0x054EF2` clear
`A5+0x1326` and select melee states `3`, `2`, and `4`, respectively.  State `4`
is proven FIRE SWORD; the individual canonical assignment of states `2` and `3`
to AXE versus HAMMER is not proven here, so their raw selector names are
preserved.

All three reach the same updater at `0x054DD2`.  Its melee tail is:

```asm
054E58  move.w  (0x1418,A5),D0
054E5C  select limit from table 0x054E96
054E68  move.w  (0x1326,A5),D1
054E6C  cmp.w   D0,D1
054E70  clr.w   (0x1326,A5)       ; expiry
054E74  move.w  #1,(0x12FA,A5)   ; normal SWORD
054E7C  addq.w  #1,(0x1326,A5)   ; otherwise advance
```

The duration table is `{0x0BB8, 0x0E10, 0x1068, 0x12C0, 0x1518}`.  Thus the
single correction covers FIRE SWORD state `4` and the shared timed melee states
`2` and `3` (the AXE/HAMMER pair, with their individual selector ordering left
unnamed rather than guessed).

## Fix

The authoritative remap has one 14-to-10-byte shift replacement at original
`0x051102`:

```asm
move.b  (0x011E,A5),D0
lsl.w   #8,D0
move.b  (0x011D,A5),D1
```

These are the retained Genesis work-RAM fields corresponding to original
`0x0010C11E/0x0010C11D`.  The original combine, threshold walk, timer, limit
table, equality condition, clear, and selector restore remain unchanged.  No
weapon-specific branch, forced selector, timer clamp, NOP, RTS bypass, shadow,
or fallback was added.

This gameplay-state repair has no PC080SN/PC090OJ semantic cut or chip tail.  It
only repairs a retained absolute arcade-WRAM operand contract.

## Automated proof

The established diagnostic
`tools/mame/scripts/build0370_flame_left_diagnostic.lua` was extended with a
timer mode; no new trace framework was created.  The extension records the
selector, timer, duration tier, selected limit, and expiry transition, and can
place the existing timer immediately before the selected threshold so the
original expiry endpoint can be proved without waiting thousands of frames.

Original arcade MAME and the exact numbered Genesis NTSC Build 0372 agree:

| Platform | Tier | Limit | Pre-expiry sequence | Result |
|---|---:|---:|---|---|
| ORIGINAL ARCADE | `0` | `0x0BB8` | `0x0BB5, 0x0BB6, 0x0BB7, 0x0BB8` | selector `4 -> 1`, timer `-> 0` |
| GENESIS NTSC 0372 | `0` | `0x0BB8` | `0x0BB5, 0x0BB6, 0x0BB7, 0x0BB8` | selector `4 -> 1`, timer `-> 0` |

The Genesis expiry occurs at frame 505 with `A5+0x12FA=1` and
`A5+0x1326=0`; no exception occurs.  Baseline 0371 under the same probe selected
tier `4` and limit `0x1518`, proving the repaired input is the behavioral delta.
The flame state in this accelerated proof is diagnostic activation, not a claim
of natural pickup coverage; Tighe's BlastEm pickup/duration test remains
required.

Evidence:

- `states/traces/build0372_weapon_timeout_arcade_v2/`
- `states/traces/build0372_weapon_timeout_baseline0371/`
- `states/traces/build0372_weapon_timeout_final/`
- `states/traces/build0372_gameplay_entry_gate_20260923_170949/`
- `states/traces/rastan_direct_video_test_build_0372_mame_30s_20260923_170953/`

## Preservation

The Build 0371 removal at original `0x05480A` remains in the remap.  The final
address map copies through `0x05480A`, has no mapping for the removed
`0x05480A..0x05480E` BSR, and resumes at `0x05480E`.  The accepted 0369 auxiliary
retirement and the existing weapon grants, fireball paths, water, rope, and cave
paths are unchanged by this patch.

## Build and gates

The normal Makefile-owned pipeline published Build 0372.  Canonical and
complete-set gates passed; the Genesis NTSC gameplay-entry gate completed 240
post-entry frames with zero address errors, bus errors, illegal instructions,
or crash-handler entries.  The pre-existing seven-epoch warning remains and is
not caused by this patch.  Manifest opcode replacement count is 229 and Genesis
coverage delta is `0x0`.

All artifacts are 1,719,992 bytes; counter advanced `371 -> 372`.

| Variant | SHA-256 |
|---|---|
| canonical | `e2f4afd7a04761949e0850a6905cbae838170e2665770a461b2b3be3ccb3a602` |
| `_d` | `e5c0c5783e8a70bdb90449e122bc7ff84e3363a890d082bee9c19f71cd7f380a` |
| `_s` | `9adb3b390c479530e1a7c1ff0b986e75b07276b8ce3acc5792073d52a918b970` |
| `_do` | `254c5154e0ef1e9e36709189e0437330c6fe683337a87d0fb3eef84a9ba83dbe` |
| `_c` | `7921aa4002dd04df4147e40bcedd42180fd970865fafabc14df053cdc29dde24` |

Canonical artifact:
`dist/rastan-direct/rastan_direct_video_test_build_0372.bin`.

## Required user validation

BlastEm validation must acquire FIRE SWORD naturally, use it through its normal
duration, confirm restoration to normal SWORD, test one other shared timed melee
upgrade, and recheck left- and right-facing flame fireballs.  Automated proof
does not replace this acceptance step.
