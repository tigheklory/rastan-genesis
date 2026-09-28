# Boss Palette Recon: exact next decompilation target

Scope: original arcade `maincpu.bin` static analysis only. No Bestiary, manifest, Claude artifact,
Genesis source, ROM, or rack-advance work was changed. Build counter remains 360.

## Result

The old premise is reversed: `0x45684` / table `0x456EC` is **not on the boss creation path**.
Ghidra's call graph has one direct caller of `0x45684`, `0x4A086` at call site `0x4A0CE`, the
field-schedule installer. The boss path `0x45330 -> 0x4449E -> 0x453A8 -> 0x4543E` never calls it.

For the normal legal boss states proved below, actor `+0x27` has its cleared-slot value `0x00`.
That does not select palette line zero. `0x3C9E8` tests `+0x27` bit 6: if clear, the compositor
program control byte remains in D0; if set, the complete `+0x27` byte replaces D0's low byte.
The low nibble finally written to PC090OJ SAT word 0 is therefore:

```
bit6(+0x27) == 0: compositor control byte & 0x0F
bit6(+0x27) == 1: actor +0x27 & 0x0F
```

The existing Ghidra export decompiles `FUN_0003c9e8` as empty `void`, losing this D0 register
input/output contract. This is the exact next function Andy should correct in the live project.

## A. Actor `+0x27` writer inventory

The disassembly was searched for direct byte operations at `A4+39`, word writes starting at
`+0x26/+0x27`, long writes starting at `+0x24`, and whole-record copies. There is no overlapping
word/long writer beyond the copy/clear operations listed here.

| PC | Operation affecting `+0x27` | Record/context | Boss-related | Semantic status |
|---|---|---|---|---|
| `0x4092E` (`0x40934..38`) | Clears a 0x40-byte actor by forward-copying a cleared first word | Actor retire/free-slot invariant | YES: supplies zeroed reusable boss slots | COMPLETE C already present |
| `0x40CE4` | `bclr #6,+0x27` | Non-boss state-handler path | NO | Direct, proven |
| `0x41B60` | Copies one full 0x40-byte actor record, then `0x41B66` clears the source | General actor transfer | NO boss call found | Direct call-site, proven |
| `0x4225A` | `bset #7,+0x27` | State-3 branch for record types below 10 | NO: boss types are `0x0E+` | Direct, proven |
| `0x4235E` | Copies 0x60 words forward from `A5+0x648` to `A5+0x688` | Round-6 BODY cloned into three following component records, including `+0x27` | YES | Direct, proven |
| `0x45376` | `bset #7,+0x27` | First actor in paired type-8/9 setup | NO | Direct, proven |
| `0x45388` | `bset #7,+0x27` | Second actor in paired type-8/9 setup | NO | Direct, proven |
| `0x456B6` | ORs `0x40 | table_byte` into `+0x27` | `0x45684`, called only by field installer `0x4A086/0x4A0CE` | NO boss-body call path | COMPLETE C already present |
| `0x45C04` | `bset #7,+0x27` | Scripted actor placement helper | NO normal boss BODY/component init | Direct, proven |

Boss-related writer sites found: **2** (`0x4092E` clear/invariant and `0x4235E` Round-6 copy).
All actor-related writer/copy sites found: **9**. Bit 7 writes do not enable the render override;
`0x3C9E8` tests bit 6 specifically.

## B. Six boss initialization paths

The common path is:

```
0x45330 -> 0x4449E
round = A5+0x118
record_type = byte[0x444E0 + round - 1]  // 0E 13 14 15 10 17
R1..R5: actor = A5+0x708, compositor +0x38 = 1
R6:     actor = A5+0x648, compositor +0x38 = 2
0x453A8: +0x00=1, +0x05=3, +0x1A=0x0180
0x4543E: index 0x45592 by record_type-8; load +0x1E and +0x01
0x42220: first state-3 boss placement/activation
```

`0x4449E`, `0x453A8`, and `0x4543E` do not write `+0x03`, `+0x27`, or `+0x3E`.
They retain the cleared free-record values: mode `+0x03=0`, override `+0x27=0`, family
`+0x3E=0`. The record-type path is separate from the family-template path; these bosses are not
family-2 records.

| Round | Slot | `+03` | `+06` | `+1E` | `+27` | `+38` | `+3E` | Initial `+01` | Template address |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `A5+0708` | 00 | 0E | 061D | 00 | 01 | 00 | 00 | `0x455C2` |
| 2 | `A5+0708` | 00 | 13 | 0753 | 00 | 01 | 00 | D6 | `0x455EA` |
| 3 | `A5+0708` | 00 | 14 | 082C | 00 | 01 | 00 | 24 | `0x455F2` |
| 4 | `A5+0708` | 00 | 15 | 07BF | 00 | 01 | 00 | E0 | `0x455FA` |
| 5 | `A5+0708` | 00 | 10 | 0988 | 00 | 01 | 00 | 82 | `0x455D2` |
| 6 | `A5+0648` | 00 | 17 | 0B35 | 00 | 02 | 00 | 66 | `0x4560A` |

The first normal state positions the BODY at `0x42326` (R1), `0x42318` (R2), `0x42310`
(R3), `0x42308` (R4), `0x4236A` (R5), or `0x42340` (R6), then changes the BODY behavior state
to `0x10`. None of those branches changes `+0x27` or `+0x3E`.

## C. Why `0x45684` / `0x456EC` inputs are irrelevant to boss BODY

The special `0x456EC` index really is:

```
(A4+0x752) * 18
+ (A5+0x118 - 1) * 3
+ normalized(A4+0x38), where selectors >=3 subtract 2
```

But it is selected only when `A4+0x3E == 2` inside `0x45684`. `A4+0x752` is the parallel
per-slot variant byte written by the field installer at `0x4A09C`, not a global boss selector.
The same installer writes `+0x3E` at `0x4A08A`, writes `+0x38` at `0x4A096`, calls the family
loader at `0x4A0C8`, and is the sole static caller of `0x45684` at `0x4A0CE`.

Boss creation uses none of that path. Therefore there is no missing boss variant value to recover
from `0x456EC`; treating it as a generic boss palette table is stale.

## D. Post-initialization palette overrides

No normal boss update range writes `A4+0x27`, calls `0x45684`, or copies a new attribute byte into
the BODY. This includes the per-round dispatch `0x46BE0 -> 0x4CC2C` and the R2/R3/R4/R6 entries
`0x4D110`, `0x4D650`, `0x4DB50`, and `0x4E29C`, plus the R1/R5 helpers `0x4CE6C` and `0x4E13C`.

- Initial palette: compositor program control nibble, because `+0x27=0`.
- Normal display palette: same source; animation changes choose another compositor program, not a
  new actor attribute.
- Damage/flash: the actor collision path uses other state/flash fields (not `+0x27`); no actor
  palette-override writer was found on the boss paths.
- Death/effect: separately created effect/projectile records use their own compositor programs;
  they do not overwrite the boss BODY `+0x27`.

This report proves one legal normal state per boss. A future phase-by-phase visual audit would need
to enumerate every animation index selected by the large boss behavior routines, but that is not a
dependency for the normal palette requested here.

## E. Component palette behavior

| Boss | Component creation | Attribute behavior | Legal initial program palette |
|---|---|---|---|
| R1 | Type `0x0F` records later created by `0x457B2/0x457D0` | Independently initialized in cleared slots; no `0x45684`; `+0x27=0` | Anim `0x14`, selector 1, program `0x47E54`, line F. These are later auxiliary/projectile records, not required by the initial BODY state. |
| R2 | No owned structural record created in initial BODY setup | BODY only | Line F |
| R3 | No owned structural record created in initial BODY setup | BODY only | Line F |
| R4 | No owned structural record created in initial BODY setup | BODY only | Line F |
| R5 | Five type `0x11` records at `A5+0x5C8..6C8`, creator `0x423B2` | Cleared slots; independently loaded; no `0x45684`; `+0x27=0` | Anim `0x89`, selector 1, program `0x491FD`, line F for all five |
| R6 | BODY is copied by `0x4235E` into three following records; `0x423F4` assigns types `0x17..1A` and reloads templates | Inherit BODY `+0x27=0`; no independent resolver | Types 17/18/19 use line F; type 1A uses line 0 |

Round-6 exact initial component programs are: type 17/base `0x0B35`, anim `0x66`, program
`0x3FA5E`, line F; type 18/base `0x0AED`, anim `0x82`, program `0x3FF96`, line F; type
19/base `0x0CCB`, anim `0x7C`, program `0x3FE74`, line F; type 1A/base `0x0BEB`, anim
`0x30`, program `0x3F488`, line 0.

## F. Render-time consumer

The closed chain is:

```
0x45DFA boss render loops
  -> 0x3D054 (+0x38 selects program table; +0x01 selects offset)
  -> selector 1 table 0x4771C or selector 2 table 0x3F0CE
  -> 0x3C902 shared compositor
  -> 0x3CA00 reads compositor control byte into D0
  -> 0x3C9E8 optionally replaces D0.low with actor +0x27
  -> 0x3C982 / 0x3C9C2 writes D0 to PC090OJ SAT word 0
```

No mask, shift, or remap changes the low nibble after `0x3C9E8`. Thus the SAT palette line is
exactly word0 bits 3:0.

Initial BODY results:

| Round | Anim | Program | Control-byte line | Final line |
|---|---:|---:|---:|---:|
| 1 | 00 | `0x47908` | F | F |
| 2 | D6 | `0x499DA` | F | F |
| 3 | 24 | `0x47EB4` | F | F |
| 4 | E0 | `0x49B90` | F | F |
| 5 | 82 | `0x490DE` | F | F |
| 6 | 66 | `0x3FA5E` | F | F |

## G. Palette line to ROM colors

`0x3BA20` implements the static palette load:

```
A1 = 0x3BA88 + (round-1)*32
for line 0..31:
    pool = byte[A1 + line]
    source = 0x4FD02 + pool*32
    0x3BA64 converts 16 0RGB words to arcade xBGR-555
```

For BODY line F:

| Round | Lookup byte | Pool | ROM color source |
|---|---:|---:|---:|
| 1 | `0x3BA97` | 11 | `0x4FE62` |
| 2 | `0x3BAB7` | 3 | `0x4FD62` |
| 3 | `0x3BAD7` | 2 | `0x4FD42` |
| 4 | `0x3BAF7` | 11 | `0x4FE62` |
| 5 | `0x3BB17` | 3 | `0x4FD62` |
| 6 | `0x3BB37` | 11 | `0x4FE62` |

Round-6 type-1A's line-0 lookup is `0x3BB28`, also pool 11 / `0x4FE62`; therefore all four
Round-6 structural records resolve to the same ROM color pool despite one record using SAT line 0.

The exact 16-word sources and their `0x3BA64` xBGR-555 results are:

| Pool/source | ROM 0RGB words | Converted arcade xBGR-555 words |
|---|---|---|
| 11 / `0x4FE62` | `0000 0000 0800 0F50 0F90 0FF0 0FF9 0FFF 000B 005F 009F 00DF 0AFF 0000 0000 0000` | `0000 0000 0010 015E 025E 03DE 4BDE 7BDE 5800 7940 7A40 7B40 7BD4 0000 0000 0000` |
| 3 / `0x4FD62` | `0000 0A90 0C34 0A00 0530 0000 0000 0999 0000 0A70 0040 0555 0850 0700 0000 0DDD` | `0000 0254 20D8 0014 00CA 0000 0000 4A52 0000 01D4 0100 294A 0150 000E 0000 6B5A` |
| 2 / `0x4FD42` | `0000 0222 0055 0277 0388 049A 05BC 0CCE 0BBB 0FF0 0FF0 0FF0 0FF0 0FF0 0FF0 0FF0` | `0000 1084 2940 39C4 4206 5248 62CA 7318 5AD6 03DE 03DE 03DE 03DE 03DE 03DE 03DE` |

## H. Exact unresolved dependency

There is no unresolved machine-code dependency for the six normal palette results. The remaining
problem is a **Ghidra decompiler representation defect**: `FUN_0003c9e8` is exported as an empty
`void` function, hiding its D0 return value and making `+0x27` look like the unconditional palette
source.

## I. Recommended next Andy decompilation target

**TARGET 1: `0x03C9E8..0x03C9F4` (`FUN_0003c9e8`).**

In the live Ghidra project, give it the semantic role `apply_actor_attribute_override`, model D0 as
both input and return, and record the exact rule: bit 6 clear preserves compositor control; bit 6
set replaces the low byte with `ActorRecord.pal_attr`. Then update callers `0x3C97E` and `0x3C9BE`
inside the `0x3C902` compositor so the returned D0 flows to SAT word 0.

Why first: this four-instruction leaf decides whether boss palette comes from `+0x27` or from the
compositor program. Until its return contract is represented, decompiling more boss state code
cannot fix the wrong `0x456EC` assumption.

What it resolves: all six boss BODY palette sources, all R5 component sources, all four R6 record
sources, and the precise boundary between table-driven field-actor overrides and embedded
compositor attributes.

Secondary target, only if Andy later wants every phase/damage animation rather than one legal
normal state: enumerate the animation indices selected by `0x4D110`, `0x4D650`, `0x4DB50`, and
`0x4E29C`, then decode only those entries in `0x4771C` / `0x3F0CE`. That is not required to close
the present normal-palette chain.

## Preserved C

- Raw: `analysis/decompilation/c/raw/0003c9e8.c`
- Semantic: `analysis/decompilation/c/rastan_actor_render.c`
- Coverage: `analysis/decompilation/c/function_coverage.csv` (`0003c9e8`, COMPLETE)
