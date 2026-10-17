# Cody Arcade Bottom-HUD Energy and Item Decompilation

## Scope and evidence

This static-only pass extends the existing arcade C tree for the gameplay
bottom HUD. It does not cover ROUND/stage, the top HUD, Genesis rendering, or
runtime behavior. The original `world_rev1` 68000 disassembly is authoritative;
the preserved Ghidra export and prior reports are corroboration.

The preserved Ghidra inventory has a concrete boundary defect here: it begins
the containing update at unreachable label `0x51090` and classifies
`0x59F92..0x5A29B` as unresolved. The call at `0x41F0E`, contiguous control flow,
and the raw instructions establish the missing functions and boundaries below.

## Functions added

| Function | Exact boundary | Result |
|---|---:|---|
| gameplay update containing both producers | `0x5100A..0x510C4` | complete |
| four-slot bottom-HUD icon producer | `0x59F92..0x5A096` | complete |
| energy/status producer | `0x5A098..0x5A242` | complete |
| energy lifecycle helper | `0x5A244..0x5A288` | complete |
| partial-cell code table | `0x5A28A..0x5A298` | decoded data |

Only one new direct helper was needed: `0x5A244`. The sound entry points
`0x3A0EC` and `0x3A116` are retained as established interfaces and were not
recursively decompiled.

## Caller relationship and ordering

The gameplay path calls `0x5100A` at `0x41F0E`. The containing function has two
outer early-return gates:

- `A5+0x13E2 == 1` returns immediately;
- otherwise, a nonzero `A5+0x1260` is decremented and the function returns.

On an admitted tick, the relevant exact order is:

1. `0x5102A`: pre-HUD helper `0x510FE` and surrounding state work;
2. `0x5104E`: optional `0x5A502` only when `A5+0x0034 == 0`;
3. `0x51054`: energy/status producer `0x5A098`;
4. `0x5105A`: write `A5+0x12FC = 0x00FF`;
5. `0x51060`: icon producer `0x59F92`;
6. `0x51066..0x510B8`: surrounding gameplay work;
7. `0x510BC`: helper `0x5122A`;
8. `0x510C0`: increment frame counter `A5+0x1308`.

`0x59F5E` is not a prelude to either producer on this path. The later
`0x5122A` calls that already-decompiled clear only when `A5+0x1360 == 1`,
`A5+0x13AC == 8`, and `A5+0x13BA == 0x80`; it then performs sound/slot setup and
clears the descriptor bands. Thus the conditional clear follows both producers
inside this containing call.

## `0x59F92` four-slot icon semantics

The output is four consecutive eight-byte records at absolute arcade WRAM
`0x10C170`, `0x10C178`, `0x10C180`, and `0x10C188`. Each record has the
PC090OJ-shaped word layout `{attribute, Y, code, X}`. Each source field is
tested independently, so all four slots can coexist.

| Slot | Source/test | Code | X | Y | Local attribute | Hidden record | Coexists | Confidence |
|---:|---|---:|---:|---:|---:|---|---|---|
| 0 | `A5+0x1388 == 0/1/2/3` | `0x0A6A/0x0A6B/0x0A6C/0x0A6D` | `0x00A0` | `0x00E8` | `0x0003` | when `==0xFF`: `{0x0003,0,0,0}` | yes | proven |
| 1 | `A5+0x140E != 0xFF` | `0x0A68` | `0x00B0` | `0x00E8` | `0x0080` | `{0x0001,0,0,0}` | yes | proven |
| 2 | `A5+0x1410 != 0xFF` | `0x0A66` | `0x00C0` | `0x00E8` | `0x0080` | `{0x0001,0,0,0}` | yes | proven |
| 3 | `A5+0x140C != 0xFF` | `0x0A64` | `0x00D0` | `0x00E8` | `0x0080` | `{0x0001,0,0,0}` | yes | proven |

The routine locally fixes those raw attribute/control words; it does not prove
a friendly palette name for them. The known writers constrain `A5+0x1388` to
`0..3` or `0xFF`. If some unknown writer supplied another non-`0xFF` value, the
original sequential code would omit the code-word store and misalign the final
X store; the raw C intentionally preserves this edge case rather than inventing
a default.

Static source relationships prove:

- `A5+0x1388`: four-state selector written by handlers `0x54F08`, `0x54F1E`,
  `0x54F34`, and `0x54F4A`, and expired to `0xFF` at `0x54DFE`;
- `A5+0x140E`: activated by the proven LIFE/HEALTH handler `0x54F60` and
  initialized hidden at `0x504C6`;
- `A5+0x1410`: activated at `0x55028`, timed/expired by `0x54E2E..0x54E52`;
- `A5+0x140C`: activated at `0x5503E`, timed/expired by `0x54E04..0x54E28`.

The bounded evidence does not safely assign item names to the last two fields,
so the C and this report keep them neutral.

### PC090OJ-specific cut for `0x59F92`

The retained semantic contract is:

`four source fields -> independent visibility + selected {attribute,Y,code,X}`.

The chip-specific tail is construction of fixed eight-byte PC090OJ staging
records at `0x10C170..0x10C188`. Its first destination setup is `0x59F9A`, with
the other visible paths beginning at `0x59FFC`, `0x5A032`, and `0x5A068` (and
parallel hidden-record paths at `0x59FDE`, `0x5A014`, `0x5A04A`, `0x5A080`).
Selection and record stores are interleaved in the original function, so this
is a semantic cut, not a claim that one contiguous suffix contains all logic.

## `0x5A098` energy/status semantics

The source is the word at `A5+0x013A`. Bit 15 marks it invalid; the function
clears the full word to zero in that case. Otherwise the display units are its
high byte. Units are clamped to 48, then divided into six cells of eight units.

Output starts at PC090OJ record 9 (`0xD00048`), with Y `0x00E8` and X beginning
at `0x0010` and advancing by 16 pixels per ordered position.

### Energy-to-cell mapping

| Semantic output | Condition/value | Code | Geometry |
|---|---|---:|---|
| leading indicator | state machine from `0x12A4/0x12A6/0x1306/0x130A` | `0x03CA` or `0x03CB` | X `0x10`, Y `0xE8`; may be a preserved hole |
| left cap | only when `A5+0x12FC == 1` | `0x03CC` | X `0x20`, Y `0xE8` |
| each full 8-unit cell | `units / 8` | `0x03CD` | six-cell band from X `0x30` |
| remainder 1..7 | `units & 7` | `0x03D4, 0x03D3, 0x03D2, 0x03D1, 0x03D0, 0x03CF, 0x03CE` | next cell |
| empty/remainder 0 | unused cells | `0x03D5` | fills band to six cells |

The table word at `0x5A28A` is the zero/remainder-0 entry `0x03D5`; indexed
remainders 1..7 read `0x5A28C..0x5A298` as shown above. This corrects a common
off-by-one reading of the table but does not differ from the later native
implementation.

The leading indicator derives a bit selector from `(energy_units >> 3)`, folds
it into the range used by the animation fields, and either emits `0x03CA/03CB`
or advances over the first output record as a semantic hole. The bar/cap is
rebuilt only when `A5+0x12FC == 1`; otherwise the existing records remain.

When there are zero full cells, `A5+0x1328` becomes 1 and the first energy-cell
code (record 11, code word at `0xD0005C`) blinks between the remembered
partial/empty code `A5+0x132A` and `0x03D5`, controlled by
`(A5+0x1308 >> 1) & 1`.

Helper `0x5A244` preserves the low/normal-energy lifecycle in
`A5+0x13CE` and publishes transition/steady values in `A5+0x13D2`. The caller
then preserves both sound side effects: command 6 through `0x3A0EC` for the
low-energy steady event when `A5+0x12F4 == 0`, and command `0x29` through
`0x3A116` for the return-to-normal transition.

### PC090OJ-specific cut for `0x5A098`

The retained semantic contract is:

`energy/animation/lifecycle state -> ordered visible-piece intents and sounds`.

The first hardware-specific destination ownership is
`movea.l #0xD00048,A0` at `0x5A0AE`. Actual PC090OJ record stores begin at
`0x5A11A`; further stores occur at `0x5A13E`, `0x5A188`, `0x5A1AC`, and
`0x5A1D0`, and the low-energy post-build code mutation is
`0x5A1EC..0x5A20C`. As with `0x59F92`, semantic selection and chip-tail writes
are interleaved, so a native implementation must preserve the state machine,
lifecycle writes, and sound calls while replacing record address arithmetic
and record stores.

## Reconciliation and remaining work

The arcade C reconstruction agrees with the prior `0x5A098` reconstruction:
source/scaling, 48-unit clamp, six cells, full/partial/empty codes, leading
indicator, refresh retention, low-energy blink, lifecycle, sounds, and geometry
all match. The only clarification is the explicit remainder-table base entry:
`0x5A28A` is `0x03D5`, while remainder 1 begins at `0x5A28C` with `0x03D4`.

No indispensable semantic helper remains unresolved. The exact friendly item
identities behind `A5+0x1410` and `A5+0x140C` remain unknown by design; proving
them would require a separately bounded provenance pass. ROUND/stage ownership,
codes, geometry, gates, and lifecycle remain entirely for the separate requested
ROUND/stage pass.

This newly proven `0x59F92` family turns the Build-0435 statement “additional
non-energy bottom/status gameplay HUD: NONE PROVEN” into resolved evidence; that
older wording was absence of proof, not proof of absence. This pass does not
evaluate or change the Build-0435 Genesis implementation.

No production Genesis source, Makefile, build artifact, runtime trace, or build
number was changed or created.
