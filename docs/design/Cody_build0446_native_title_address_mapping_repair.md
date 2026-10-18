# Cody — Build 0446 Native-Title Address-Mapping Repair

## Result

Build 0446 corrects the Build-0445 PC-relative addressing error and passes the
canonical, gameplay-entry, generated residency-epoch, family, and fixed
30-second validations with zero exceptions. It is ready for Tighe's hardware
test. Screen 2 work has not started.

## Exact address proof

`build/rastan-direct/address_map.json` maps:

- arcade wrapper `0x03BB48` to runtime `0x03BD4A`;
- arcade adjacent pointer table `0x03BB7C` to runtime `0x03BD5E`.

The 68000 `LEA d16(PC),A0` base is the address of its extension word. At runtime
`0x03BD52`, the extension word is at `0x03BD54`. Therefore:

```text
Build 0445: 0x03BD54 + 0x0008 = 0x03BD5C  (wrong: preceding RTS)
Build 0446: 0x03BD54 + 0x000A = 0x03BD5E  (correct: mapped table)
```

Build 0445's fault screen proves the wrong calculation with `D0=8`:

```text
wrong base 0x03BD5C + 8 -> 0x03BD64 -> 0xBE880003
FAULT = A0 = 0xBE880003
stacked continuation PC = 0x0007219C
```

Build 0446 final ROM bytes are:

```text
0x03BD4A  3200 0240 007F E548 41FA 000A 4EB9 00072196 4E75
0x03BD5E  0003BE7A 0003BE88 0003BEA0 ...
```

Selector 2 now reads the valid pointer `0x0003BEA0`. No hard-coded runtime
table address, pointer guard, clamp, fallback, repeated PC080SN title draw, or
NOP padding is present.

## Semantic boundary

The cut remains arcade glyph/string producer `0x03BB48`. The retained prefix
computes `D1=selector` and `D0=(selector&0x7F)*4`; the wrapper resolves its
adjacent copied pointer table and calls the Genesis-native Plane-A staging
helper. The retired tail remains the original PC080SN cell-write loop.

The previously proven `0x03AA20` three-entry displacement-table repair remains
active. Generated title maps and semantic SAT data are unchanged.

## Verification

- Generated-title equivalence: PASS.
- Assembly/link and postpatch: PASS.
- Coverage: PASS, `0x295EB8`.
- Canonical gate and boot guards: PASS.
- Gameplay-entry gate: PASS, 564 frames, 240 controlled post-entry frames,
  zero address/bus/illegal exceptions.
- Epoch gate: PASS after synchronizing its stale hard-coded package expectations
  with generated `boundary_report.json` (`6/7/8/9` for records `3/4/11/13`).
  All six production handoffs pass full Plane-A and fixed Plane-B LUT checks
  with zero exceptions.
- Fixed 30-second Genesis NTSC trace: PASS, 1,798 frames.
- Seven-ROM family/configuration verification: PASS.

No production gameplay or rendering behavior was changed by the epoch-gate
metadata synchronization.

## Artifact

- Build: `0446`.
- Canonical ROM:
  `dist/rastan-direct/rastan_direct_video_test_build_0446.bin`.
- Size: `2711224` bytes.
- SHA-256:
  `6e4002611320a568b71b60d791b3898ce13bc1d1124c58647bc0cf39a2ae1d08`.
- `_d`: `018b02d150f7024f2fd004873ffdb1136da732256826ccbcfd3307ea0ea5ea5c`.
- `_s`: `a4f582f8d29b40f88f5c50b0871dc6090e51b82cae6867ca93180433556b006d`.
- `_do`: `101c8bb57b6a6c969cf2581f9fd634104ad346ec474b89f4c95859eb2b6801f5`.
- `_c`: `f061dc5cf20c1454c96b3d73f5a95b4d6e140ce9e6e00205adea3194417e5740`.
- `_full_hud`: `cce2890cf8f6f8eb6ef34c51432e7f08ffdc3ef4251bda883c2b7036b6928e89`.
- `_invincible`: `537b0184244c68961ac8bc5d9d47a640749a7235c2841ddb88b19b52ccf74c11`.
- Counter: `445 -> 446`.
- Exact ROM-producing source commit:
  `f968689388c77b15deaeb38b40e9784c29fe4e0b`.
- Real-hardware acceptance: PENDING TIGHE.
