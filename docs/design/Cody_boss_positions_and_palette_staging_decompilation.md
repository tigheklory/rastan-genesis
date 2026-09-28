# Cody — Boss Positions and Palette Staging Decompilation

Scope: original arcade static analysis only. This report uses the canonical Ghidra exports,
`build/maincpu.disasm.txt`, `build/regions/maincpu.bin`, and the repository's local MAME source
reference. No MAME process was run, no Genesis code or ROM was built, and the build counter remains
360. The Bestiary, graphics manifest, and Claude artifact were not edited by this task.

## Result

Both requested machine-code gaps are closed. `0x43458` is the internal entry of the complete
`0x43450` signed-offset positioner. It contains no hidden state or animation selector. Round 5 uses
indices 13 through 17 of its 27-entry table every frame. Round 6 does not use that table: its two
middle records share the primary anchor, while type `0x1A` uses a five-position phase table mirrored
by facing.

The inherited palette-flow premise was backwards. The copy primitive at `0x3A2D0` is
`move.w (A0)+,(A1)+`, so `0x45D7C` and `0x45DC4` publish `A5+0x1600` **to** CLCS palette RAM at
`0x200000`. They never copy `0x200000` into the working table. With normal sprite control `0x60`,
compositor nibble F selects physical palette bank `0x3F`; `0x45DC4` fills that bank from working
line 15. The exact normal boss source is therefore the round table byte
`0x3BA88[(round-1)*32+15]`, selecting a 16-word pool at `0x4FD02 + pool*32`.

## A. `0x43458` complete semantics

The complete containing function occupies `0x43450..0x43482`. Its register contract is:

- `A4`: parent/body `ActorRecord`.
- `A6`: output child/component `ActorRecord`.
- `D0.w`: unsigned offset-table index.
- Output: child `x` at `+0x16` and `y` at `+0x1A`; the full entry additionally writes child
  compositor selector `+0x38=0` and table index `+0x23=D0.b`.

The public entry at `0x43450` clears `child+0x38`, stores the index at `child+0x23`, then falls
through. The internal entry at `0x43458`, used by `0x42380`, deliberately skips those two writes.
Its exact operation is:

```c
dx = (int8_t)ROM[0x43484 + 2*index + 0];
dy = (int8_t)ROM[0x43484 + 2*index + 1];
if (parent->facing == 0) dx = -dx;
child->x = parent->x + dx;
child->y = parent->y + dy;
return;
```

Both fields are sign-extended bytes before 16-bit addition. Facing zero mirrors only X; Y is never
mirrored. The function has no round test, animation dependency, state dependency, flags field,
terminator, indirect call, or return value. The caller determines the index and repeats the update.
For R5, `0x42380` also copies the BODY facing byte and mode byte to each active component before
calling `0x43458` with `13+component_index`.

## B. Boss component position tables

### Table `0x43484`

Format: 27 fixed two-byte entries, `{signed dx, signed dy}`. Index address is
`0x43484 + 2*D0.w`. There are no flags, terminators, animation selectors, or state selectors.

| Index | dx | dy | Index | dx | dy | Index | dx | dy |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 40 | -16 | 9 | 8 | 32 | 18 | 42 | -19 |
| 1 | 34 | 28 | 10 | 52 | -60 | 19 | 24 | -36 |
| 2 | 48 | -16 | 11 | 76 | -4 | 20 | 8 | -44 |
| 3 | 20 | -5 | 12 | 48 | -4 | 21 | -8 | -52 |
| 4 | 6 | -16 | 13 | -3 | -8 | 22 | 0 | -61 |
| 5 | 20 | -20 | 14 | 7 | -8 | 23 | -46 | -61 |
| 6 | 8 | -20 | 15 | 16 | -8 | 24 | -62 | -34 |
| 7 | 20 | -11 | 16 | -7 | -16 | 25 | -72 | -20 |
| 8 | 8 | -11 | 17 | 2 | -16 | 26 | 0 | -72 |

The complete machine-readable dump, including R5 and R6 placement relations, is
`analysis/actor_decompilation/cody_boss_component_positions.tsv`.

### Round-6 type-`0x1A` table

`0x4E976` maps phase `A5+0x0F42` to one of five entries and simultaneously produces animation
`48 + 9*index`. `0x4EAC6` is the nonzero-facing table; `0x4EADA` is the zero-facing table with X
negated and Y unchanged.

| Phase | Index | Anim | Facing nonzero `(dx,dy)` | Facing zero `(dx,dy)` |
|---:|---:|---:|---:|---:|
| 0 | 0 | 48 | `(64,-48)` | `(-64,-48)` |
| 3 | 1 | 57 | `(56,-64)` | `(-56,-64)` |
| 6 | 2 | 66 | `(48,-80)` | `(-48,-80)` |
| 9 | 3 | 75 | `(56,-32)` | `(-56,-32)` |
| any other nonzero value | 4 | 84 | `(40,-8)` | `(-40,-8)` |

## C. Complete Round-5 structural layout

The BODY is the record at `A5+0x0708`, type `0x10`, base `0x0988`, initial animation `0x82`.
`0x423B2` creates five owned structural records; `0x42380` updates every active record on every
BODY update. All five are active simultaneously in the normal state.

| Render order | Slot | Type | Base | Anim | State | Table index | Relative position when facing != 0 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `A5+0x05C8` | `0x11` | `0x0988` | `0x89` | `0x11` | 13 | `(-3,-8)` |
| 1 | `A5+0x0608` | `0x11` | `0x0988` | `0x89` | `0x11` | 14 | `(7,-8)` |
| 2 | `A5+0x0648` | `0x11` | `0x0988` | `0x89` | `0x11` | 15 | `(16,-8)` |
| 3 | `A5+0x0688` | `0x11` | `0x0988` | `0x89` | `0x11` | 16 | `(-7,-16)` |
| 4 | `A5+0x06C8` | `0x11` | `0x0988` | `0x89` | `0x11` | 17 | `(2,-16)` |
| 5 | `A5+0x0708` | `0x10` BODY | `0x0988` | BODY-controlled | BODY-controlled | — | `(0,0)` |

Facing zero negates each listed X offset. The component owner is the BODY: it supplies facing,
mode, X, and Y. No component offset varies with BODY animation or state. `0x45DFA` traverses the
component pool in ascending slot order and the BODY after the five components. This is sufficient
to assemble the complete normal R5 composite statically.

## D. Complete Round-6 structural layout

`0x42340` places the primary at `(304,232)`, sets state `0x10`, and invokes the forward copy
primitive for `0x60` words with destination exactly `0x40` bytes after the source. Because the
copy overlaps and proceeds forward, the primary's complete 64-byte record repeats into the next
three slots. `0x423F4` then assigns types `0x17..0x1A` and reloads each type template.

| Render order | Slot | Type | Base | Initial anim | Placement/update ownership |
|---:|---:|---:|---:|---:|---|
| 0 | `A5+0x0648` | `0x17` | `0x0B35` | `0x66` | Primary BODY; owns facing/X/Y |
| 1 | `A5+0x0688` | `0x18` | `0x0AED` | `0x82` | Exact primary facing/X/Y copy via `0x4E7C6` while `A5+0x272 != 0` |
| 2 | `A5+0x06C8` | `0x19` | `0x0CCB` | `0x7C` | Exact primary facing/X/Y copy via `0x4E7C6` while `A5+0x272 != 0` |
| 3 | `A5+0x0708` | `0x1A` | `0x0BEB` | `0x30` | Primary-relative phase position via `0x4E69C` while `A5+0x272 != 0` |

At creation, all four records overlap at the primary anchor because of the copy. In the active
normal update state, types `0x18` and `0x19` remain anchor-sharing layers; type `0x1A` uses the
five phase-dependent offsets in section B. `0x4E9A2`, called after type-`0x1A` placement, computes
arena-side globals and does not alter its X/Y. `0x45DFA` renders slots in the ascending order shown.
This parameterized facing/phase model is sufficient to reconstruct the complete dragon for every
normal placement state.

## E. `0x200000` palette-RAM format

`0x200000` is physical CLCS palette RAM, not a software staging buffer. It has 2048 16-bit entries:
128 sequential lines of 16 colors, 32 bytes per line, 4096 bytes total. There is no interleave or
line rearrangement in the copy paths.

Cold-start function `0x3B9F8` writes:

- physical lines 0..47: 768 sequential converted words from ROM `0x4EAF6`;
- physical line 48: 16 converted words from pool 11 at ROM `0x4FE62`;
- physical lines 49..127: untouched by this function.

During palette transition, `0x45D7C` writes the old working table to physical lines 0..31 in eight
chunks of 64 words. It then calls `0x3BA20` to replace the working table with the current round's
32 selected lines. `0x45DC4` writes that new working table to physical lines 48..79, also in eight
chunks of 64 words. Lines 80..127 are not part of these publishers.

The independent `0x59AD4` updater selects `source_row*16` from a caller-supplied ROM table and
updates exactly one caller-selected physical line. Source word `0xFFFF` preserves the destination
color; other words use the same 0RGB-to-xBGR conversion. Static inventory of the relevant direct
writers found no hidden boss-line-F permutation or second boss-specific writer.

## F. `A5+0x1600` working-palette format

The working structure is 512 contiguous 16-bit words: 32 logical lines by 16 colors, 1024 bytes.
Line `n` begins at `A5+0x1600 + n*32`. `0x3BA20` indexes the 192-byte table at `0x3BA88` as six
round rows of 32 bytes:

```c
pool = ROM8[0x3BA88 + (round-1)*32 + working_line];
source = 0x4FD02 + pool*32;
for (color=0; color<16; ++color)
    working[working_line][color] = convert_0RGB_to_xBGR555(source[color]);
```

The exact conversion used by `0x3BA56` and `0x59ADE` is:

```c
dst = ((src & 0x0F00) >> 7) | ((src & 0x00F0) << 2) | ((src & 0x000F) << 11);
```

There are no extra banks inside this structure, no 16-color interleave, and no reordering beyond
the per-round pool-index byte for each line.

## G. Logical palette line to physical colors

The PC090OJ driver combines the sprite control bank with the low compositor nibble:

```c
physical_bank = ((sprite_ctrl & 0x00E0) >> 1) | (compositor_nibble & 0x0F);
```

Normal sprite control is `0x60`, so the base is `0x30`. Logical nibble F therefore selects physical
bank `0x3F` (decimal 63). `0x45DC4` maps working lines 0..31 to physical lines 48..79, hence:

```text
logical F -> physical 0x3F -> 63 - 48 = working line 15
          -> A5+0x1600 + 15*32 = A5+0x17E0
          -> round lookup byte [(round-1)*32+15]
          -> ROM pool 0x4FD02 + pool*32
```

## H. Round-3 actual boss palette source

Round 3 lookup byte `0x3BAD7` is `2`. Its exact source is pool 2 at `0x4FD42`:

```text
0000 0222 0055 0277 0388 049A 05BC 0CCE
0BBB 0FF0 0FF0 0FF0 0FF0 0FF0 0FF0 0FF0
```

Converted xBGR-555 words are:

```text
0000 1084 2940 39C4 4206 5248 62CA 7318
5AD6 03DE 03DE 03DE 03DE 03DE 03DE 03DE
```

This result does **not** naturally produce the purple/magenta premise stated in the task. Static
code and ROM establish pool 2 with no further mapper between working line 15 and physical bank
`0x3F`. Geometry was not changed and screenshot colors were not sampled. Because new MAME work was
explicitly forbidden, the honest conclusion is that the supplied visual acceptance premise is
contradicted by the requested static evidence—possibly because of frame/scene attribution or color
presentation—not that another undecompiled staging function exists.

## I. Round 1–6 normal boss palette sources

Every BODY compositor selects logical F, but the round table changes its content. Offsets below are
relative to `A5+0x1600` and physical `0x200000` respectively.

| Round | Logical | Working offset | Physical bank / byte offset | Lookup | Pool | ROM source | 16 raw 0RGB words |
|---:|---:|---:|---:|---:|---:|---:|---|
| R1 | F | `+0x01E0` | `0x3F / +0x07E0` | `0x3BA97` | 11 | `0x4FE62` | `0000 0000 0800 0F50 0F90 0FF0 0FF9 0FFF 000B 005F 009F 00DF 0AFF 0000 0000 0000` |
| R2 | F | `+0x01E0` | `0x3F / +0x07E0` | `0x3BAB7` | 3 | `0x4FD62` | `0000 0A90 0C34 0A00 0530 0000 0000 0999 0000 0A70 0040 0555 0850 0700 0000 0DDD` |
| R3 | F | `+0x01E0` | `0x3F / +0x07E0` | `0x3BAD7` | 2 | `0x4FD42` | `0000 0222 0055 0277 0388 049A 05BC 0CCE 0BBB 0FF0 0FF0 0FF0 0FF0 0FF0 0FF0 0FF0` |
| R4 | F | `+0x01E0` | `0x3F / +0x07E0` | `0x3BAF7` | 11 | `0x4FE62` | `0000 0000 0800 0F50 0F90 0FF0 0FF9 0FFF 000B 005F 009F 00DF 0AFF 0000 0000 0000` |
| R5 | F | `+0x01E0` | `0x3F / +0x07E0` | `0x3BB17` | 3 | `0x4FD62` | `0000 0A90 0C34 0A00 0530 0000 0000 0999 0000 0A70 0040 0555 0850 0700 0000 0DDD` |
| R6 | F | `+0x01E0` | `0x3F / +0x07E0` | `0x3BB37` | 11 | `0x4FE62` | `0000 0000 0800 0F50 0F90 0FF0 0FF9 0FFF 000B 005F 009F 00DF 0AFF 0000 0000 0000` |

The machine-readable form is `analysis/actor_decompilation/cody_boss_palettes.tsv`. Round-6 type
`0x1A` initially uses logical line 0, but its round-6 line-0 lookup also selects pool 11; therefore
all four R6 structural records resolve to the same source palette in this state.

## J. Raw and semantic C inventory

New raw reconstructions:

- `raw/00043458.c`: complete `0x43450`, internal `0x43458`, and table `0x43484`.
- `raw/00042340.c`: R6 anchor initialization and overlapping four-record copy.
- `raw/0004e7c6.c`: R6 type-`0x18/0x19` anchor synchronization.
- `raw/0004e976.c`: R6 phase bucket and animation selection.
- `raw/0004e69c.c`: R6 type-`0x1A` placement and final helper call.
- `raw/0003a2d0.c`: word-copy direction and count contract.
- `raw/0003b9f8.c`: cold-start CLCS initialization.
- `raw/00045d7c.c`: lines 0..31 publisher and round reload transition.
- `raw/00045dc4.c`: lines 48..79 publisher.
- `raw/00059ad4.c`: direct 16-color physical-line writer.

The existing `raw/0003ba20.c` was corrected to preserve the now-proven publication direction.
Semantic counterparts are in `rastan_boss_composite.c`; the R5 caller is also represented in
`rastan_actor_subsystems.c`. Coverage, historical audit, and README entries were updated.

## K. Remaining genuinely undecompiled dependencies

There is no undecompiled executable dependency for the requested normal R5/R6 placement or the
six normal line-F palette sources. `0x4E9A2` remains outside the semantic placement lift, but the
raw `0x4E69C` preserves its call and inspection proves it does not alter type-`0x1A` X/Y; its
arena-side bookkeeping is unrelated to reconstructing the composite. All-animation boss phase
auditing remains intentionally outside this task.

The unresolved item is empirical rather than a missing code dependency: the claimed R3 purple
screenshot does not agree with pool 2 selected by the static program. Resolving that external
evidence conflict would require confirming the screenshot's exact original-arcade state or taking
an original-arcade runtime sample, which this task explicitly prohibited.

## Tool reuse and validation boundary

Existing project tools/evidence reused: canonical Ghidra exports under `analysis/ghidra/`, the
canonical disassembly and maincpu region, existing actor decompilation guards, and the checked-in
MAME `rastan.cpp` reference for PC090OJ bank semantics. New tooling created: none. New tooling was
not necessary because the repository already contained every static-analysis and validation
facility required for this decompilation.
