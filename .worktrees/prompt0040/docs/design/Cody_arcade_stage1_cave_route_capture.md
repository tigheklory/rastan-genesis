# Original Arcade Stage-1 Cave Route Capture

## Scope

This report records the original arcade semantic and scrolling state for the
Stage-1 cave route Tighe actually traverses. It is based on a continuous,
human-controlled run of original arcade MAME machine `rastan`. No Genesis ROM
was run, no gameplay automation was used, and no diagnostic action was required
from Tighe during play.

This is observation and documentation only. It does not change or evaluate
Build 0300, implement a cave fix, determine rope ownership, or investigate the
deferred destructible cave-entrance block.

## Result

The successful route uses semantic level segments **1, 2, and 3**:

- segment 1 contains the outdoor approach, cave entrance, and initial descent;
- segment 2 contains the lower cave interior and the start of the rope approach;
- segment 3 contains the final rope approach, rope climb, upper exit, and the
  first stable outdoor state after the exit.

Therefore, segment boundaries do **not** align one-for-one with visible cave
geography. In particular, segment 1 spans outdoor and cave-looking regions, and
segment 3 spans rope/cave and post-exit outdoor regions. The previously inferred
segment 4/5/6 route is not the route observed in this capture.

`a5+0x1386` (`tm0`) remained `0x0000` throughout the successful route.
`a5+0x10A8` (FG selector) also remained `0x0000` throughout it.

## Capture Method

The durable logger is:

- `tools/mame/scripts/arcade_stage1_cave_route.lua`
- `tools/mame/run_rastan_cave_route_wsl.sh`

The logger sampled the original arcade main CPU once per external emulator
frame and wrote a compact change-event stream in parallel. It recorded:

- runtime PC, A5, main state words, segment, `tm0`, selector, strip, group, and
  page pointer;
- player coordinate anchors at `a5+0x10BE` and `a5+0x10C0`;
- tilemap1/FG scroll at `a5+0x10AE` and `a5+0x10B0`;
- tilemap0/BG scroll at `a5+0x10EC` and `a5+0x10EE`;
- player mode and descriptor base;
- all 16 current FG source pointers at `a5+0x1000..0x103C`;
- all 16 rebuilt FG block pointers at `a5+0x1040..0x107C`.

The exact invocation was:

```text
/usr/games/mame rastan -window -skip_gameinfo -rompath /home/tighe/projects/rastan-genesis/roms -homepath /home/tighe/projects/rastan-genesis/build/mame/home -autoboot_script /home/tighe/projects/rastan-genesis/tools/mame/scripts/arcade_stage1_cave_route.lua
```

MAME exited normally with status 0. The logger recorded 8,406 external frames,
4,379 change events, and zero logger errors.

## Capture Attempts

Tighe reported that the first two lives ended before cave completion and that
the third life entered the cave, exited it, and continued outside before MAME
was closed. The trace agrees with that account:

| Life | Active frame range | Segments reached | Use in this report |
|---|---:|---|---|
| 1 | 2014-3487 | 1, 2 | Failed-attempt context only |
| 2 | 3620-5849 | 1, 2 | Failed-attempt context only |
| 3 | 5982-8406 | 1, 2, 3 | Authoritative complete cave route |

All route classifications below use life 3.

## Coordinate Semantics

The requested player fields are the proven player coordinate anchors at
`a5+0x10BE` and `a5+0x10C0`. Their behavior is viewport/camera-relative during
this route: X repeatedly approaches the gameplay clamp near `0x00A0` rather
than increasing monotonically across the level. They are reported exactly, but
must not be treated alone as a global linear world coordinate. Route position is
reconstructed from segment, strip/group, scroll, page pointer, and player
coordinates together.

FG and BG scroll values are 9-bit ring coordinates. The broad `0x0000-0x01FF`
ranges in the outdoor and lower-cave intervals include normal modulo wrap and
must not be interpreted as a 511-pixel instantaneous jump.

## Authoritative Route Table

All hexadecimal values are raw original-arcade values. `Player` is the
`a5+0x10BE/0x10C0` coordinate pair. FG is tilemap1 scroll; BG is tilemap0
scroll.

| Route region | Frames | Segment | tm0 | Selector | Player X/Y | FG X/Y | BG X/Y | Strip/group | Page pointer |
|---|---:|---|---|---|---|---|---|---|---|
| Outdoor approach | 5982-6875 | 1 | 0000 | 0000 | 0020-00A0 / 0030-0070 | 0000-01FF / 0000-01FF | 0000-01FF / 0000-01FF | 0-3 / 0-F | 050F6C |
| Cave entrance transition | 6876-6893 | 1 | 0000 | 0000 | 0091 / 004C-006C | 016F / 0149 | 00B8 / 0149 | 3 / F | 050F6C |
| Initial descent | 6894-6970 | 1 | 0000 | 0000 | 0091-00A0 / 004C-00CC | 0169-016F / 0105-0149 | 00B5-00B8 / 0105-0149 | 3 / F | 050F6C |
| Lower cave/interior | 6971-7426 | 2 | 0000 | 0000 | 0096-00A0 / 0088-00CC | 0001-01FF / 0105 | 0000-01FF / 0105 | 0-3 / 0-C | 050F6D |
| Rope region/approach | 7427-7505 | 2, 3 | 0000 | 0000 | 00A0 / 00A8-00CC | 0145-01CD / 0105 | 01A3-01E7 / 0105 | 0-3 / 0-F | 050F6D, 050F6E |
| Rope climb | 7506-8034 | 3 | 0000 | 0000 | 00A7 / 0040-00A8 | 0145 / 0105-0120 | 01A3 / 0105-0120 | 0 / 1 | 050F6E |
| Upper cave exit | 8035-8203 | 3 | 0000 | 0000 | 00A4-00A7 / 0040-006B | 00EB-0145 / 0124-015D | 0176-01A3 / 0124-015D | 0-3 / 1-3 | 050F6E |
| First stable outdoor after exit | 8204-8406 | 3 | 0000 | 0000 | 00A4 / 0064 | 00EB / 015D | 0176 / 015D | 3 / 3 | 050F6E |

The final interval is the first stable post-exit state confirmed by Tighe's run.
Without an in-run visual marker, the exact first visually outdoor frame cannot
be selected more narrowly than the preceding upper-exit interval, frames
8035-8203. No repeated playthrough is needed to establish segment membership.

## Region Transitions

| Boundary | Frame transition | Semantic change |
|---|---:|---|
| Outdoor to entrance | 6875 -> 6876 | player mode 0 -> 2; segment remains 1 |
| Entrance to descent | 6893 -> 6894 | player mode 2 -> 3; segment remains 1 |
| Descent to lower interior | 6970 -> 6971 | segment 1 -> 2; strip/group 3/F -> 0/0; page 050F6C -> 050F6D |
| Interior to rope approach | 7426 -> 7427 | analytical boundary only; segment remains 2 |
| Rope approach to climb | 7505 -> 7506 | player mode 3 -> 4; segment is 3 |
| Rope climb to upper exit | 8034 -> 8035 | player mode 4 -> 2; segment remains 3 |
| Upper exit to stable outside | 8203 -> 8204 | stable endpoint; segment remains 3 |

The segment 2 -> 3 boundary occurs inside the rope-approach interval, before the
mode-4 rope climb. Neither the cave entrance nor cave exit is a segment boundary.

## Cave Segment Membership

| Geographic state | Observed segment value(s) |
|---|---|
| Immediately before cave entry | 1 |
| Cave entrance | 1 |
| Initial descent | 1 |
| Lower/interior cave | 2 |
| Rope approach | 2, then 3 |
| Rope climb | 3 |
| Cave exit | 3 |
| Immediately after exit | 3 |

## tm0 and Selector Behavior

- `tm0` (`a5+0x1386`): constant `0x0000` for frames 5982-8406.
- FG selector (`a5+0x10A8`): constant `0x0000` for frames 5982-8406.

There is no selector transition that marks cave entry, rope entry, or cave exit
in this successful route. Source progression occurs under selector 0.

## FG Source Progression

The observed source family follows the established form:

```text
0x1691C + strip*0x22C0 + level_segment*0x40 + group*4
```

The complete per-region start/end pointer lists are preserved in
`arcade_stage1_cave_route_regions.csv`. The important semantic changes are:

- segment 1 page `0x050F6C`: sources progress from
  `01695C 018C1C ... 034FDC 03729C` to
  `016998 018C58 ... 035018 0372D8`;
- segment 2 page `0x050F6D`: sources progress from
  `01699C 018C5C ... 03501C 0372DC` to
  `0169CC 018C8C ... 03504C 03730C`;
- segment 3 page `0x050F6E`: rope sources settle at
  `0169E0 018CA0 01AF60 01D220 01F4E0 0217A0 023A60 025D20 027FE0 02A2A0 02C560 02E820 030AE0 032DA0 035060 037320`;
- after the rope, segment-3 sources advance to
  `0169E8 018CA8 01AF68 01D228 01F4E8 0217A8 023A68 025D28 027FE8 02A2A8 02C568 02E828 030AE8 032DA8 035068 037328`.

The source changes confirm that visible route progression is not identified by
segment alone. Strip/group and source-pointer state advance within each segment.

## Rope Runtime Location

The rope climb is the exact mode-4 interval at frames **7506-8034**:

- segment: `0x0003`
- `tm0`: `0x0000`
- selector: `0x0000`
- player X: fixed `0x00A7`
- player Y: `0x00A8` through `0x0040`
- FG scroll X: fixed `0x0145`
- FG scroll Y: `0x0105` through `0x0120`
- BG scroll X: fixed `0x01A3`
- BG scroll Y: `0x0105` through `0x0120`
- strip/group: `0x0000/0x0001`
- page pointer: `0x050F6E`
- current FG sources:
  `0169E0 018CA0 01AF60 01D220 01F4E0 0217A0 023A60 025D20 027FE0 02A2A0 02C560 02E820 030AE0 032DA0 035060 037320`

The interval begins with player mode `3 -> 4` and ends with mode `4 -> 2`.

Rope semantic owner: **NOT DETERMINED BY THIS CAPTURE**.

## Deferred Cave-Entrance Block

The successful route crossed the deferred cave-entrance-block area. Its bounded
future-search window is frames **6876-6970**:

- segment `0x0001`, `tm0=0`, selector 0;
- strip/group `3/F`, page pointer `0x050F6C`;
- player X `0x0091-0x00A0`, player Y `0x004C-0x00CC`;
- FG X `0x0169-0x016F`, FG Y `0x0105-0x0149`;
- BG X `0x00B5-0x00B8`, BG Y `0x0105-0x0149`.

This documents the runtime location encountered by the route. The exact block
cell and semantic owner were not isolated because no visual marker was required
during play and ownership investigation is outside this task.

## Preserved Evidence

Trace directory:

`states/traces/original_arcade_stage1_cave_route_20260820_144438/`

| Artifact | Lines | Bytes | SHA-256 |
|---|---:|---:|---|
| `arcade_stage1_cave_route_frames.csv` | 8,407 | 3,120,572 | `94715a0cf7d107835e9c238f7ba66fc0325cdd3bb7199c414bc92a640167b67a` |
| `arcade_stage1_cave_route_events.tsv` | 4,380 | 1,427,422 | `1c143c4c95cbb91ba9c7bd89ac172e492e132a4fd0abba35e725f83ed8ebec31` |
| `arcade_stage1_cave_route_regions.csv` | 9 | 6,157 | `25af7a99fdccfab819ab77794bc578aa8cbbe8fc69b9c2f7ae87b1b9c24a836e` |
| `arcade_stage1_cave_route_key_transitions.tsv` | 8 | 1,385 | `86cc0058828cc2261ce7f74a1663d31eab97f0b4573c1c14f1bb47ff454894be` |
| `capture_command.txt` | 10 | 705 | `fdf84c9015addc02bcbd9945b7e88df683c185f7e73b008fdc1d006f43102350` |
| `logger_metadata.txt` | 16 | 436 | `ec707da232255f634d05e37bcbb49842a85d7983561603365a912c4fb66be068` |

The region CSV is the machine-readable authoritative route table; the key
transition TSV records the exact boundary samples used by this report.

## Limits and Non-Claims

- Geographic region labels are post-run interpretations of a continuous trace;
  the underlying frame/state records remain the authority.
- The exact first visually outdoor frame lies within frames 8035-8203; frame
  8204 is the first stable user-confirmed post-exit state.
- The player coordinate anchors are not independently sufficient as global world
  coordinates because the camera keeps them near the viewport clamp.
- This capture does not prove rope ownership or cave-block ownership.
- This capture does not assess or change Genesis Build 0300.
- No Genesis production source, ROM, or build counter changed.

## Architecture Compliance

This task observed the original arcade semantic producer state without changing
arcade behavior. It introduced only reusable MAME capture tooling, permanent
trace evidence, this report, and the required agent log entry. No PC080SN or
PC090OJ compatibility implementation was added, no Genesis production path was
modified, and Build 0301 was not consumed.
