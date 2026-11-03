# Cody Build 0417 — Rope-Area Hole Source Identification

Date: 2026-10-12. This is a read-only MAME forensic against the existing
canonical Build 0417 ROM. Production source, the Palette Composer profile,
generated graphics, ROM artifacts, and the build counter were not changed.

## Result

The reported rope-wall defect is **not transparency**. In the bounded 12×8
Layer-A sample, all 96 cells and all 32 unique live VRAM patterns have zero
transparent texels. The darkest hole-like pixels are opaque Genesis nibble
`0xA` (Line-3 index 10), whose live CRAM color is `0x0200`.

One exact apparent hole comes from source tile `0x150`, logical usage
`LA-0149`, physical pattern `A-0211`. At source pixel `(4,1)`, arcade index 4
is opaque and has xBGR-555 value `0x30CA` (RGB8 `82,49,98`; direct Genesis
quantization `0x0624`). The Composer maps that source index `4 -> 10`, where
the live/authored Line-3 color is `0x0200` (MAME RGB `0,0,52`). The resulting
pixel is therefore opaque deep blue, not a hole through which Plane B is
visible.

This target index also appears in six other purple-rock tile identities in
the sample. For those identities it is produced by the authored `7 -> 10`
mapping. Arcade bank-3 index 7 is `0x1804` (RGB8 `32,0,49`; direct Genesis
quantization `0x0202`), while the live target remains `0x0200`. Thus the
same target entry removes the red component from those dark-purple details.

## Capture

The established normal coin/start and natural-route input sequence was reused
in Genesis NTSC MAME. The terminal capture occurred only after the rope wall
was fully visible; the screenshot was taken before any terminal VDP-port read.

| Field | Value |
|---|---:|
| ROM | `dist/rastan-direct/rastan_direct_video_test_build_0417.bin` |
| frame | 7792 |
| progression | `0x000B` |
| player X/Y | `0x009E / 0x003F` |
| foreground scroll X/Y | `0x0137 / 0x0189` |
| screenshot | `states/traces/build0417_rope_hole_source/rope_area.png` |
| real VDP dump | `states/traces/build0417_rope_hole_source/actual_vram.bin` |
| staged Plane A | `states/traces/build0417_rope_hole_source/staged_plane_a.bin` |

The real 64 KB VRAM was read through the Mega Drive VDP data/control ports,
using the established terminal-read method. MAME exited immediately after the
read, so the read cannot affect the evidence frame.

## Bounded Layer-A grid

The sample is logical X44..X55 and Y32..Y39. It covers 12 columns by 8 rows
of the purple wall immediately left of the green rope. Each grid entry is the
source tile code. `0x117` is the known A-0154 control.

```text
        X44 X45 X46 X47 X48 X49 X50 X51 X52 X53 X54 X55
Y32     110 132 1E4 150 110 132 1E4 150 110 132 1E4 150
Y33     113 114 1E5 14C 113 114 1E5 14C 113 114 1E5 14C
Y34    *117 118 155 104 117 118 155 104 117 118 155 104
Y35     11B 11C 106 107 11B 11C 106 107 11B 11C 106 107
Y36     110 132 1E4 150 1F6 1F7 1F8 1F9 110 132 1E4 150
Y37     113 114 1E5 14C 1FA 1FB 1FC 1FD 113 114 1E5 14C
Y38    *117 118 155 104 1FE 1FF 200 201 117 118 155 104
Y39     11B 11C 106 107 202 203 204 205 11B 11C 106 107
```

For each of the 96 occurrences, the exact screen position, logical X/Y,
physical Plane-A row/column, source code, usage, physical pattern, staged/live
word, slot, line, flips, and zero coordinates are retained in:

- `states/traces/build0417_rope_hole_source/rope_grid.tsv`
- `states/traces/build0417_rope_hole_source/rope_grid.json`

All 96 staged words equal their final live Plane-A VRAM words. Every word uses
Line 3 and has H/V flip `0/0`.

## Actual live patterns and transparency counts

The table lists every unique identity in the bounded grid. `VRAM bytes` are
the actual 32 bytes read from the named live slot, not a generated-file
assumption.

| Code | Usage | Physical | Live word | Slot | Line | H/V | Zero pixels | VRAM bytes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `0x110` | `LA-0085` | `A-0147` | `0x642B` | `0x42B` | 3 | 0/0 | 0 | `7988666699986666799886667999699977799989777999887779988877799668` |
| `0x132` | `LA-0119` | `A-0181` | `0x6438` | `0x438` | 3 | 0/0 | 0 | `8889999988999999899988899988888898888866988886669887867796666677` |
| `0x1E4` | `LA-0263` | `A-0325` | `0x6448` | `0x448` | 3 | 0/0 | 0 | `9966666999776669999776668899766688999669b88997696b8999996b889999` |
| `0x150` | `LA-0149` | `A-0211` | `0x6455` | `0x455` | 3 | 0/0 | 0 | `999989999998a79999b6666698b6666698bb6666998b66669998866699998b66` |
| `0x113` | `LA-0088` | `A-0150` | `0x639B` | `0x39B` | 3 | 0/0 | 0 | `6669888a66698888666987786669877b66699775669999776988899788888aa9` |
| `0x114` | `LA-0089` | `A-0151` | `0x6445` | `0x445` | 3 | 0/0 | 0 | `98888866a98888a68a9888868898888ab889888a7889998a7869998a88999999` |
| `0x1E5` | `LA-0264` | `A-0326` | `0x63A4` | `0x3A4` | 3 | 0/0 | 0 | `66b8699966669999666669978666699786666997888669979986699999986999` |
| `0x14C` | `LA-0145` | `A-0207` | `0x6442` | `0x442` | 3 | 0/0 | 0 | `969998bb6669998b7766998b7776699877776898777768997776689966666999` |
| `0x117` | `LA-0092` | `A-0154` | `0x6468` | `0x468` | 3 | 0/0 | 0 | `bbb9b889b9999888996699886666998b6666988b6666988b6677698b66776988` |
| `0x118` | `LA-0093` | `A-0155` | `0x6460` | `0x460` | 3 | 0/0 | 0 | `9999bb99899988b96b99888967b9868967b99669667b9869b67b8899b677b899` |
| `0x155` | `LA-0154` | `A-0216` | `0x6462` | `0x462` | 3 | 0/0 | 0 | `999a66999999869999998899889999998889998968899989668899996668899a` |
| `0x104` | `LA-0073` | `A-0135` | `0x6441` | `0x441` | 3 | 0/0 | 0 | `9666999999999999999997769999777699997776889967668889966686899966` |
| `0x11B` | `LA-0096` | `A-0158` | `0x639C` | `0x39C` | 3 | 0/0 | 0 | `6677698866676988666669b8666669b99666bb899bbbb8999bbb889999888999` |
| `0x11C` | `LA-0097` | `A-0159` | `0x642E` | `0x42E` | 3 | 0/0 | 0 | `86678a9a8867b8a9a867b8a9a8677889a8667889aa86888a9a8888899aa86899` |
| `0x106` | `LA-0075` | `A-0137` | `0x6399` | `0x399` | 3 | 0/0 | 0 | `66688999666688999666689996666889966666899966668999966689a9966669` |
| `0x107` | `LA-0076` | `A-0138` | `0x6439` | `0x439` | 3 | 0/0 | 0 | `888a99988688a9996668899996668899966668a9996668a9996688a9999988a9` |
| `0x1F6` | `LA-0281` | `A-0343` | `0x632B` | `0x32B` | 3 | 0/0 | 0 | `6933339499433454894444448954444488854444688954446889444468895444` |
| `0x1F7` | `LA-0282` | `A-0344` | `0x62D2` | `0x2D2` | 3 | 0/0 | 0 | `3339994333344444333233943313343433223344233333554333345444333444` |
| `0x1F8` | `LA-0283` | `A-0345` | `0x62D3` | `0x2D3` | 3 | 0/0 | 0 | `3344449933444495433344554444445555544544544445445445544455454444` |
| `0x1F9` | `LA-0284` | `A-0346` | `0x6311` | `0x311` | 3 | 0/0 | 0 | `5555555555555555533553555555555545555553445353334453333344533331` |
| `0x1FA` | `LA-0285` | `A-0347` | `0x6328` | `0x328` | 3 | 0/0 | 0 | `6889544468895443688985448889854488899444889995548988445488844345` |
| `0x1FB` | `LA-0286` | `A-0348` | `0x62F4` | `0x2F4` | 3 | 0/0 | 0 | `4443344444444434444444244344433444454334444543344445533334455445` |
| `0x1FC` | `LA-0287` | `A-0349` | `0x62E6` | `0x2E6` | 3 | 0/0 | 0 | `3545444435544443355444322354332212543333235533443345555533455555` |
| `0x1FD` | `LA-0288` | `A-0350` | `0x62FD` | `0x2FD` | 3 | 0/0 | 0 | `4553221254333123543332335443333354433333544333335544444355544433` |
| `0x1FE` | `LA-0289` | `A-0351` | `0x632C` | `0x32C` | 3 | 0/0 | 0 | `8844322289442123994322236843333468433334688433446884444466884444` |
| `0x1FF` | `LA-0290` | `A-0352` | `0x62C5` | `0x2C5` | 3 | 0/0 | 0 | `2554553323545554335455544455555545555554555555455555334455532344` |
| `0x200` | `LA-0291` | `A-0353` | `0x62D7` | `0x2D7` | 3 | 0/0 | 0 | `3345555543445533444555335555553355554335445433354554445454554454` |
| `0x201` | `LA-0292` | `A-0354` | `0x630D` | `0x30D` | 3 | 0/0 | 0 | `5554444434554434344544444445544444444554444444453334444433233444` |
| `0x202` | `LA-0293` | `A-0355` | `0x6323` | `0x323` | 3 | 0/0 | 0 | `6688455568855555888544458885444598844445984333459843223499332334` |
| `0x203` | `LA-0294` | `A-0356` | `0x6308` | `0x308` | 3 | 0/0 | 0 | `5532344353433442234445533333454333444544344455544444555544455533` |
| `0x204` | `LA-0295` | `A-0357` | `0x62C3` | `0x2C3` | 3 | 0/0 | 0 | `2355554433455553444554533445555334445555444444543444445434555445` |
| `0x205` | `LA-0296` | `A-0358` | `0x62C7` | `0x2C7` | 3 | 0/0 | 0 | `3112344421233334232333333333333333333333433334434444444444444444` |

There are therefore no Case-A (`source 0 -> Genesis 0`) or Case-B (`source
nonzero -> Genesis 0`) candidate pixels in this sample.

## Exact visible apparent-hole attribution

The occurrence at logical X47/Y32 is final Plane-A physical cell col47/row0.
Its live name word is at VRAM `0xE05E`:

```text
screen coordinate             X67/Y124
matched tile top-left         X63/Y123
physical Plane-A cell         col47/row0
logical map cell              X47/Y32
source tile                   0x150
logical usage                 LA-0149
physical pattern              A-0211
live Plane-A word             0x6455
live VRAM slot                0x455
pixel within tile             X4/Y1
live Genesis nibble           0xA (decimal 10)
MAME screenshot RGB           0,0,52
```

The 8×8 live slot pattern matches the displayed tile at X63/Y123 for 64/64
pixels. Thus the spatial attribution does not depend on guessing from the
tile's general appearance.

Original PC080SN source tile `0x150` at `(4,1)` contains opaque index 4:

```text
arcade source index           4
arcade bank-3 xBGR-555        0x30CA
arcade RGB8                   82,49,98
direct Genesis quantization   0x0624
Composer context              context:gameplay.r01.p01
Composer mapping              LA-0149: 4 -> 10, target Line 3
live target CRAM              Line 3 index 10 = 0x0200
```

This is **OPAQUE WRONG COLOR**, not true transparency. The full list of 66
opaque index-10 pixels in the bounded region is retained in
`states/traces/build0417_rope_hole_source/opaque_dark_pixels.tsv`.

The affected purple-rock identities carrying at least one such live index-10
pixel are:

| Code | Usage | Physical | Source mapped to 10 | Index-10 pixels/tile |
|---|---|---|---:|---:|
| `0x150` | `LA-0149` | `A-0211` | 4 | 1 |
| `0x113` | `LA-0088` | `A-0150` | 7 | 3 |
| `0x114` | `LA-0089` | `A-0151` | 7 | 7 |
| `0x155` | `LA-0154` | `A-0216` | 7 | 2 |
| `0x11C` | `LA-0097` | `A-0159` | 7 | 13 |
| `0x106` | `LA-0075` | `A-0137` | 7 | 1 |
| `0x107` | `LA-0076` | `A-0138` | 7 | 6 |

## A-0154 control

`0x117 / LA-0092 / A-0154` remains the negative control:

- live word `0x6468`, slot `0x468`, Line 3, no flips;
- live bytes exactly match the expected finalized pattern;
- transparent pixel count is 0;
- the prior runtime proof established that all CRAM entries it uses are exact.

It is not the source of an actual transparent hole.

## Classification

**OPAQUE WRONG COLOR.** The exact visually dark pixel is nonzero at every
boundary: arcade source index 4, Composer target index 10, and live Genesis
nibble `0xA`. The apparent hole is created by the authored/live `0x0200`
target color, not by Plane-A transparency, a wrong name word, or a missing
VRAM pattern.

## Tooling and scope

Reused:

- normal input route from `native_sprite_fullgame_closeout.lua`;
- real VDP-port read method from `probe_genesis_vram_space.lua`;
- static Layer-A resolver in `tools/graphics_editor/server.py`;
- the completed A-0154 runtime proof.

Created for this bounded capture:

- `tools/mame/scripts/build0417_rope_hole_source.lua`.

No production source, palette profile, ROM, or build-number state was changed.
