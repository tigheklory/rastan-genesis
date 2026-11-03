# GAME OVER and 1UP/Score Palette and Pattern Provenance

**Date:** 2026-10-19
**Scope:** read-only handoff to Andy; no palette policy or production rendering change

## Large flashing GAME OVER

### Original arcade semantic owner

This is not a PC080SN text plane. It is a bespoke eight-glyph PC090OJ sprite row used by the
no-human attract/demo gameplay state. `FUN_0005100a` calls the producer at arcade `0x05104E ->
0x05A502` when `A5+0x34 == 0`. The current native gate further preserves the observed owning tuple
`A5+(0,2,4) = (2,3,0/1)`.

`0x05A502..0x05A5AA` writes complete records 83..90. Every record has attribute word 0 and X/Y/code:

| Letter | Code | X | PC090OJ source bytes |
|---|---:|---:|---:|
| G | `0x0037` | `0x0060` | `0x1B80..0x1BFF` |
| A | `0x0038` | `0x0070` | `0x1C00..0x1C7F` |
| M | `0x003F` | `0x0080` | `0x1F80..0x1FFF` |
| E | `0x0040` | `0x0090` | `0x2000..0x207F` |
| O | `0x0041` | `0x00B0` | `0x2080..0x20FF` |
| V | `0x0042` | `0x00C0` | `0x2100..0x217F` |
| E | `0x0043` | `0x00D0` | `0x2180..0x21FF` |
| R | `0x0044` | `0x00E0` | `0x2200..0x227F` |

Each code is one 16x16 PC090OJ pattern (four Genesis 8x8 cells). The flash does not alternate
patterns, attributes, or palettes: bit 5 of the gameplay phase word at `0x10C200` selects Y `0x0070`
or hidden/parked Y `0x0180`. The native path emits nothing during the hidden phase.

Attribute nibble 0 combined with sprite-control colbank `0x60` gives effective arcade bank `0x30`.
For R1, bank 0 uses round-row entry `0x3BA88[0] = 11`, hence source palette
`0x4FD02 + 11*0x20 = 0x4FE62`:

```text
0000 0000 0800 0F50 0F90 0FF0 0FF9 0FFF
000B 005F 009F 00DF 0AFF 0000 0000 0000
```

These are original 0RGB words; they are provenance, not a proposed Genesis color assignment.

### Current Genesis realization

`.Lnq_gameover_emit` in `apps/rastan-direct/src/pc090oj_hooks.s` directly emits the same eight
semantic codes through the native gameplay sprite finalizer. The patterns use the shared dynamic
PC090OJ residency cache, so there is no fixed per-family slot: each glyph occupies four consecutive
cells within physical Genesis pattern range 1339..1534 as allocated. It is SAT output, not a name
table or plane.

The effective bank remains `0x30`. The current generated scene-1 palette LUT maps bank `0x30` to
Genesis line 0 because the saved Test profile authors `usage:burst:bank0x30 -> line 0`. That entry is
for the burst/effect object, not the GAME OVER semantic family. `specs/palette_decisions.json` has no
GAME OVER decision, and the Palette Composer exposes bank `0x30` only through the burst object.
Therefore the current line is an accidental shared-bank policy result, not semantic ownership.

**Exact family identifier for Andy:**
`PC090OJ_ATTRACT_GAMEOVER_CODES_0037_0038_003F_0044_BANK_30`

**Missing from Palette Composer:** YES. Andy should add this as its own semantic object/domain while
preserving the proven bank-0x30 source palette; it must not inherit the burst object's meaning merely
because the effective bank is shared.

## 1UP / score

### Original arcade semantic owner

The owner chain is `0x03B8B0` (HUD setup), `0x03B930` (static record copier), and `0x03B802`
(six BCD score digits). `0x03B930` clears word 0 for every record, so the fixed labels and digits use
attribute nibble 0/no flip and effective bank `0x30` under sprite-control colbank `0x60`.

The P1 static template at `0x03B9B0..0x03B9D3` contains six digit placeholders and these labels:

```text
Y=0x0010 code=0x0039 X=0x0040
Y=0x0000 code=0x0048 X=0x0028
Y=0x0000 code=0x0046 X=0x0038
```

The score updater reads BCD state at `A5+0x011E` and maps nibbles to codes `0x002A..0x0033` at six
positions, suppressing leading zero. The original source ranges are:

- digits `0x002A..0x0033`: PC090OJ bytes `0x1500..0x19FF`;
- label `0x0039`: `0x1C80..0x1CFF`;
- label `0x0046`: `0x2300..0x237F`;
- label `0x0048`: `0x2400..0x247F`.

Thus 1UP labels and score digits share one original palette family/effective bank, but they are
different pattern subfamilies.

### Current Genesis realizations

`tools/translation/gen_native_hud.py` generates the shared frontend HUD from the raw PC090OJ
patterns. Its fixed pattern assignments include:

- P1 labels: code `0x39` -> cells 1359..1362, `0x48` -> 1363..1366,
  `0x46` -> 1367..1370;
- digits: `0x2A` -> 1379..1382 through `0x33` -> 1415..1418.

The generated frontend SAT words use `0xC000|tile`, selecting Genesis palette line 2. The reduced
gameplay P1 producer `.Lnq_project_p1_hud` is a second realization: it emits the same semantic codes
with the HUD-white/direct/fixed-screen tag, uses `pc090oj_hud_white_genesis.bin` (opaque pixels
offline-remapped to index 2 for codes `0x02A..0x048`), and the finalizer selects line 3. The current
red result therefore comes from target line/package ownership, not evidence that the arcade family
is red. No new white constant or palette was added here.

Neither semantic family exists in `specs/palette_decisions.json`. The generic bank-0x30 LUT entry is
owned by `usage:burst:bank0x30`, while the generated static HUD bypasses that LUT and hardcodes line
2; the gameplay HUD-white path bypasses it and selects line 3. Andy must reconcile these consumers in
the Palette Composer/registry instead of hard-coding another color.

**Exact family identifiers for Andy:**

- `PC090OJ_HUD_SCORE_DIGITS_002A_0033_BANK_30`
- `PC090OJ_HUD_P1_LABEL_0039_0046_0048_BANK_30`

**1UP and digits same family:** same arcade palette family YES; same pattern family NO.

**Missing Palette Composer classification:** YES for both semantic subfamilies. Tighe's required
semantic result is pure white, but the numeric target mapping remains Andy's palette-policy task.

## Files and routines for the handoff

- Original code/data: `build/maincpu.disasm.txt` at `0x05104E`, `0x05A502`, `0x03B802`,
  `0x03B8B0`, `0x03B930`, `0x03B9B0`; `build/regions/maincpu.bin`; `build/regions/pc090oj.bin`.
- Native GAME OVER: `apps/rastan-direct/src/pc090oj_hooks.s` `.Lnq_gameover_emit` and
  `.Lnq_gameover_labels`.
- Native HUD: `tools/translation/gen_native_hud.py`,
  `build/rastan-direct/native_hud_report.json`, `.Lnq_project_p1_hud`, and
  `tools/translation/build_pc090oj_hud_white.py`.
- Palette policy: `build/rastan-direct/build0400/Test.snapshot.json`,
  `tools/translation/gen_pc090oj_palsel_lut.py`, generated
  `apps/rastan-direct/out/pc090oj_palsel_lut.inc`, and `specs/palette_decisions.json`.

No Palette Composer profile, LUT generator, canonical palette registry, CRAM source, SAT path, or
production palette behavior was modified by this provenance pass.
