# Build 0532 R1-S2 next-to-author Plane-A boundary fix

Date: 2026-11-03

Build 0532 corrects Build 0531's one-row-inclusive partial-record ownership test. Original arcade
`$055948` publishes using the old strip/group cursor and increments afterward, so the retained
cursor is the next row to author. Selector 1 now owns `[64-front,63]`; selector 2 owns
`[0,front-1]`; both are empty at front zero.

This retains record-16 logical row 63 / physical row 31 at the 16→17 boundary until ordinary
publication actually authors the incoming row. It also corrects the identical record-20→21
boundary mechanism. Build 0531's correctly authored record-17 rows 44–46 at front 21 remain
current-owned. No new buffer, map, hardware emulation, coordinate special case, or gameplay change
was introduced.

ROM-producing source: `566e9c63e5254be6179a0948a34958c20959c68c`.

Expanded deterministic reversal regression: `54591d124c2a017f0b4099dbedf5a3e9516151c3`
(verifier only; post-ROM).

## Primary artifacts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0532.bin` | 3,792,568 | `1682b5409010e4da850d8bc24ebac2877253e5ee8ad5d3e043df36b4fafd6838` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_S1-2.bin` | 3,792,568 | `536ebf66d537804e2330e302681a1acf20307aa6fb7d574d606554be1523fae6` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_invincible_S1-2.bin` | 3,792,568 | `adf3eb18b633f547e21b129ad026c59862a7f921734db9155fe2294c57917879` |

## Verification

Assembly, deterministic Plane-A boundary/reversal oracle, selector equivalence, scene/checkpoint/pan
assets, collision separation, boot, canonical, gameplay entry, all Round-1 package/epoch cases,
mandatory Genesis NTSC trace, and complete configured family pass. Normal and invincible R1-S2
direct starts pass at frame 412 with stage `$0010`, record `$0011`, package 5, full planes, and zero
map misses.

Record 21 disposition is deliberately bounded: the same erroneous boundary mechanism and its
accumulation are proven and corrected, but no existing Build-0531 record-21 first-write trace proves
that it explains every pixel of the larger observed corruption. Tighe's gameplay test decides
whether another defect remains. Build 0532 is not accepted yet.
