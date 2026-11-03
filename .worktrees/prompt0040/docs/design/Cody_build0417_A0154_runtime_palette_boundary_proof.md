# Cody Build 0417 — A-0154 Runtime Palette Boundary Proof

Date: 2026-10-12. This is a read-only runtime proof against the existing
Build 0417 canonical ROM. Production source, palette profiles, generated
graphics, the build counter, and ROM artifacts were not changed.

Tighe corrected the requested runtime platform from BlastEm to **MAME Genesis
NTSC** during the task. The capture therefore uses `/usr/games/mame genesis`
with the six-button controller and the canonical Build 0417 ROM.

## Result

The ordered boundary test reaches **Case D**. The live pattern bytes, live
Plane-A name word, and every CRAM entry referenced by A-0154 all match their
Composer-authored expectations. The proposed A-0154 runtime tile/name/palette
diagnosis does not explain the reported visual defect.

## Route and mechanically proven occurrence

Normal coin/start input was supplied by Lua. Continuous RIGHT alone stopped at
progression `0x0003`; this is the unrelated traversal blocker allowed by the
task's fallback clause. The final run retained continuous RIGHT and reused the
already-established jump/attack pulse schedule from
`native_sprite_fullgame_closeout.lua`. It injected no emulated state and
required no human input.

The terminal capture occurred at frame 7713:

| Field | Value |
|---|---:|
| progression (`A5+0x013E`) | `0x000B` (record/segment 11) |
| player X/Y | `0x00A0 / 0x003F` |
| foreground scroll X/Y | `0x0137 / 0x0159` |
| logical target | X44/Y38 |
| physical Plane-A ring cell | col 44 / row 6 (`38 & 31`) |
| calculated screen position | X57/Y223 |
| staged address/value | `0xFF53F8 = 0x6468` |

Thus the statically proven segment-11 X44/Y38 source occurrence was resident
and had entered the live 320x224 viewport. Its live Plane-A VRAM address is
`0xE358`.

## Ordered runtime proof

### 1. VRAM pattern slot

The real Mega Drive VDP VRAM was read terminally through the 68000 VDP
data/control ports, using the established method in
`tools/mame/scripts/probe_genesis_vram_space.lua`.

```text
slot:             0x0468
VRAM byte addr:   0x8D00
expected:         bbb9b889b9999888996699886666998b
                  6666988b6666988b6677698b66776988
actual:           bbb9b889b9999888996699886666998b
                  6666988b6666988b6677698b66776988
byte match:       YES (32/32)
```

The Case-A stop condition is not met.

### 2. Live Plane-A name word

```text
physical cell:    col 44 / row 6
VRAM byte addr:   0xE358
expected word:    0x6468
actual word:      0x6468
pattern:          0x0468
palette line:     3
H flip:           0
V flip:           0
priority:         0
match:            YES
```

The Case-B stop condition is not met.

### 3. Live CRAM Line 3

CRAM was also read terminally through the VDP ports. The live line, the staged
line, and the linked `editor_layera_palette` are:

| Index | Live CRAM | Staged | Editor target | A-0154 uses it? | Result |
|---:|---:|---:|---:|:---:|---|
| 0 | `0x0000` | `0x0000` | `0x0000` | no | match |
| 1 | `0x028C` | `0x028C` | `0x028C` | no | match |
| 2 | `0x044C` | `0x044C` | `0x044C` | no | match |
| 3 | `0x0026` | `0x0026` | `0x0026` | no | match |
| 4 | `0x0004` | `0x0004` | `0x0004` | no | match |
| 5 | `0x0002` | `0x0002` | `0x0002` | no | match |
| 6 | `0x0424` | `0x0424` | `0x0424` | **yes** | **MATCH** |
| 7 | `0x0624` | `0x0624` | `0x0624` | **yes** | **MATCH** |
| 8 | `0x0402` | `0x0402` | `0x0402` | **yes** | **MATCH** |
| 9 | `0x0202` | `0x0202` | `0x0202` | **yes** | **MATCH** |
| 10 | `0x0200` | `0x0200` | `0x0200` | no | match |
| 11 | `0x0422` | `0x0422` | `0x0422` | **yes** | **MATCH** |
| 12 | `0x0440` | `0x0440` | `0x0440` | no | match |
| 13 | `0x0660` | `0x0660` | `0x0660` | no | match |
| 14 | `0x0AA6` | `0x0AA6` | `0x0AA6` | no | match |
| 15 | `0x0AA6` | `0x0AA6` | `0x0884` | no | intended runtime animation |

The only full-line difference is entry 15. Runtime evidence identifies this as
the existing type-9 waterfall animation path, which updates only Line-3 entries
14/15. A-0154 uses indices 6, 7, 8, 9, and 11, so this does not affect the
target.

For reference, the previously proven arcade FG bank-3 carrier line is:

```text
0000 0868 0846 0646 0624 0424 0402 0202
0202 028C 044C 0226 0004 0002 0222 0424
```

The live A-0154 entries do **not** equal that carrier: indices 6/7/8/9/11 are
respectively `0424/0624/0402/0202/0422`, versus carrier
`0402/0202/0202/028C/0226`. The carrier is not the active authority for these
entries.

## Runtime writer and source

The Line-3 write tap recorded the one-shot gameplay installation at frame 323.
Observed post-instruction PC `0x070242` corresponds to the copy instruction at
`0x07023E` inside `vdp_install_test_lines` (`0x070204`). That loop copies all 16
words from linked ROM symbol `editor_layera_palette` at `0x084284` into
`staged_palette_words + 0x60` (`0xFF6100`). It sets `palette_pending`, and
`vdp_commit_palette` at `0x070350` publishes the staged 64-word palette to CRAM
by DMA during VBlank.

No later writer changes A-0154's indices 6/7/8/9/11. The later writes at
`0x073078` and `0x073092` are within `genesistan_palette_hook_59ad4` and affect
only waterfall indices 14/15. At frame 7713, actual CRAM equals staged Line 3
at all 16 entries.

Therefore:

- `editor_layera_palette` is referenced by production runtime: **YES**;
- it is installed during Stage-1 scene activation: **YES**;
- it is overwritten at A-0154's used entries: **NO**;
- it is unreachable/dead data: **NO**;
- `palette_route_table` takes precedence for these entries: **NO**.

## Classification and scope

**Case D — VRAM correct, name word correct, A-0154 CRAM colors already live.**

This disproves the proposed runtime tile-upload, name-publication, and
Composer-color-authority explanations for this exact A-0154 occurrence. Per the
task's stop rule, no alternative visual-source investigation was started.

## Evidence and tooling

Runtime artifacts:

- `states/traces/build0417_A0154_runtime_boundary/runtime_boundary.txt`
- `states/traces/build0417_A0154_runtime_boundary/line3_writers.tsv`

Existing project tools reused:

- the coin/start and natural-route input conventions from
  `tools/mame/scripts/native_sprite_fullgame_closeout.lua`;
- the terminal real-VDP read method from
  `tools/mame/scripts/probe_genesis_vram_space.lua`;
- the prior Build-0417 static target proof in
  `docs/design/Cody_build0417_A0154_palette_composer_pipeline_audit.md`.

New tooling created:

- `tools/mame/scripts/build0417_A0154_runtime_boundary.lua`.

Why new tooling was necessary:

- no existing script tied the real VDP-port reads to the mechanically proven
  record-11 X44/Y38 visible window while also retaining the exact Line-3 writer.

No screenshot color inference was used. No production code, profile, generated
graphics, ROM, or build counter was modified.

