# Cody Arcade Bottom-HUD Lives and ROUND Decompilation

## 1. Scope

This is the bounded static Pass 2 over the original `world_rev1` 68000. It
adds the missing lives and ROUND semantics to the existing arcade C tree and
combines them with Pass 1's energy/item inventory. It does not select or
implement a Genesis renderer, change production source, run MAME, or build a
ROM.

The authoritative evidence is `build/regions/maincpu.bin` and
`build/maincpu.disasm.txt`, reconciled with the Ghidra exports. Older reports
are corroboration only. The historical association of `0x3B2DA..0x3B420`
with the gameplay ROUND HUD is corrected below.

Architecture-policy statement: the lives semantic cut is active-player
reserve-count selection plus a one-digit intent; the ROUND cut is the
one-based stage mirror plus fixed label/digit intents. Their PC090OJ record
construction, and the separate ROUND/READY PC080SN text writes, are the chip
tails. This analysis removes none of those tails and introduces no
transitional compatibility state.

## 2. Lives semantic source

The displayed source is the low byte of the active player's word at
`A5+0x0102`, read as byte address `A5+0x0103` by selector 4 in the exact
ten-byte table entry at `0x3B8A6`:

`{count=1, Y=0xE4, destination=0xD00088, source=0x10C103}`.

It is a **reserve-lives** count, not a total including the current life.
`0x3A186..0x3A190` loads the total/current allotment from `A5+0x0100`,
subtracts one when nonzero, and stores the result at `A5+0x0102`. Thus a
three-life allotment displays `2`. The extra-life path at
`0x3B798/0x3B79C` increments both words and immediately refreshes selector 4.

`A5+0x002A` does not choose between `A5+0x0100` and `A5+0x0102` inside the
renderer. Instead, the 32-word player-buffer swaps at `0x3A294` and
`0x3A2B2` move the selected player's block into the active workspace beginning
at `A5+0x0100`. Consequently `A5+0x0102` is always the selected active
player's reserve count when selector 4 runs.

## 3. Lives rendering producer

`0x3B802` is the digit producer. Selector 4 reads one low-nibble digit,
disables leading-zero suppression because the configured count is one, and
writes record 17 at `0xD00088`. A reserve count of zero therefore remains a
visible `0`, rather than blanking.

The group is restored/shown by internal entry `0x3B8EE`: `0x3B902(D1=0)`
copies the five-record fixed template at `0x3B984`, then selectors 3 and 4
refresh ROUND and lives. Gameplay entry `0x3A64C` invokes this only when
`A5+0x0034 != 0`. Calls to `0x3B902` with `D1=1` hide the entire five-record
group by changing the Y high byte of records 17..21 to one. Lives is also
refreshed directly at `0x3A66A` after reserve initialization and at `0x3B7A2`
after an extra-life award. It is event-driven, not rebuilt every frame.

## 4. Lives artwork / digit / player-icon pieces

Lives is exactly one PC090OJ record:

- fixed control word `0x0000`;
- raw Y `0x00E4`;
- code `0x002A + (reserve & 0x0F)`;
- raw X `0x0000`.

Codes `0x002A..0x0033` are the same digit family used by the shared score
producer. No separate Rastan/player-icon piece is selected or written by
selector 4, by the five-record template, or by its show/hide helper. The
visible bottom-left presentation attributable to this path is the digit
alone. Number and player icon are therefore not two pieces in this producer.

## 5. Lives exact arcade geometry

The single lives digit is one 16x16 PC090OJ piece at raw arcade `(X,Y) =
(0x0000,0x00E4)`, control/attribute `0x0000`. Its Y-high byte is `0` while
visible and `1` while hidden. There is no leading blank at zero.

## 6. Stage/round authoritative state

`A5+0x0118` is authoritative stage/round state. `A5+0x0117` is its display
mirror.

At `0x4527E..0x4529A`, when `A5+0x0104 == 0`, both bytes receive:

`((~word[0x5FF9E]) & 7) + 1`

so initialization is directly one-based. At `0x3A878/0x3A87C`, both bytes
increment. When authoritative `A5+0x0118` reaches 7, `0x3A888` forces only the
display mirror back to 6 and returns. The ordinary displayed range is thus
1..6; there is no zero-to-one conversion at rendering time.

The writes at `0x3B2DA`, `0x3B302`, `0x3B35E`, `0x3B3AA`, and `0x3B3F8`
copy authoritative `A5+0x0118` into ranking/high-score working records. The
calls at `0x3B414/0x3B41A/0x3B420` select text IDs 33..35: `ENTER YOUR
INITIALS`, `SCORE  ROUND  NAME`, and `00`. They are not the gameplay lower-HUD
ROUND producer.

## 7. ROUND text/value construction

There are two distinct presentations.

### Persistent gameplay lower HUD

The `0x3B984` template supplies three fixed label pieces:

| Piece | Code | Raw X | Raw Y | Control |
|---|---:|---:|---:|---:|
| label 0 | `0x0034` | `0x0100` | `0x00E8` | `0x0000` |
| label 1 | `0x0035` | `0x0110` | `0x00E8` | `0x0000` |
| label 2 | `0x0036` | `0x0120` | `0x00E8` | `0x0000` |

Selector 3 at `0x3B89C` reads byte `A5+0x0117`, takes its low nibble, and
writes code `0x002A + value` to record 21 at raw X `0x0128`, raw Y `0x00E8`.
The one-piece configuration forces even zero visible, although normal state is
one-based. The label is artwork in three PC090OJ codes, not an ASCII string.

### ROUND/READY transition overlay

`0x3A6B2..0x3A754` first hides PC090OJ records 17..21. In the normal
non-test path (`A5+0x0104 == 0`), generic writer `0x3BB48` receives selector
55. Descriptor `0x3C16E` is `{destination=0xC08C48, attribute=0,
text="ROUND"}`. The digit is written directly at `0x3A72A` to code-word
address `0xC08C62` as `0x0030 | byte[A5+0x0117]`. The physical name cells are
row 12, columns 18..22 for `ROUND`, with the digit at row 12, column 24.
READY is text selector 56 at `0xC08E4C`; PLAYER 1/2 READY uses selectors 4/5.

This overlay is constructed once by the round-start transition state. It is
not the persistent lower-right gameplay HUD.

## 8. ROUND rendering ownership

Ownership is a lifecycle combination:

- persistent gameplay `ROUND n`: **PC090OJ**, records 18..21;
- round-start `ROUND ... READY` overlay: **PC080SN/text**, descriptor writer
  plus one direct code-word store.

The answer for the persistent lower HUD requested by this pass is PC090OJ.
The existence of the transition text path does not imply a Genesis Window or
plane choice.

## 9. ROUND exact arcade geometry

Persistent label pieces are 16x16 at `(0x100,0xE8)`, `(0x110,0xE8)`, and
`(0x120,0xE8)`; the 16x16 digit is at `(0x128,0xE8)`. All four control words
are `0x0000`. They are restored/refreshed together at `0x3B8EE` and hidden
together by `0x3B902(D1=1)`.

The transition overlay occupies the PC080SN physical name cells identified in
section 7. Its descriptor attribute is `0x0000`.

## 10. Complete lower-HUD component table

All pixel coordinates below are raw arcade PC090OJ coordinates. Every listed
piece is 16x16. `event` means show/init/award/round transition, not per-frame.

| Component | Source state | Arcade producer | Subsystem | X | Y | Pieces | Code | Local attr | Visibility | Update | Confidence |
|---|---|---|---|---:|---:|---:|---|---:|---|---|---|
| reserve-lives digit | active-player `A5+0x0102` low byte | `0x3B802` selector 4 | PC090OJ | `0x0000` | `0x00E4` | 1 | `0x002A + digit` | `0x0000` | group visible; zero not blanked | event | proven |
| energy indicator | `0x12A4/0x12A6/0x1306/0x130A` | `0x5A098` | PC090OJ | `0x0010` | `0x00E8` | 1 | `0x03CA/0x03CB` | `0x0000` | phase/bit-selected; otherwise preserved hole | admitted HUD tick | proven |
| energy left cap | `A5+0x12FC==1` | `0x5A098` | PC090OJ | `0x0020` | `0x00E8` | 1 | `0x03CC` | `0x0000` | rebuilt only on refresh | admitted tick when gated | proven |
| energy cell 0 | high byte `A5+0x013A` | `0x5A098` | PC090OJ | `0x0030` | `0x00E8` | 1 | `0x03CD`, partial, or `0x03D5` | `0x0000` | refresh; low cell may blink | admitted tick when gated | proven |
| energy cell 1 | same | `0x5A098` | PC090OJ | `0x0040` | `0x00E8` | 1 | same family | `0x0000` | refresh | admitted tick when gated | proven |
| energy cell 2 | same | `0x5A098` | PC090OJ | `0x0050` | `0x00E8` | 1 | same family | `0x0000` | refresh | admitted tick when gated | proven |
| energy cell 3 | same | `0x5A098` | PC090OJ | `0x0060` | `0x00E8` | 1 | same family | `0x0000` | refresh | admitted tick when gated | proven |
| energy cell 4 | same | `0x5A098` | PC090OJ | `0x0070` | `0x00E8` | 1 | same family | `0x0000` | refresh | admitted tick when gated | proven |
| energy cell 5 | same | `0x5A098` | PC090OJ | `0x0080` | `0x00E8` | 1 | same family | `0x0000` | refresh | admitted tick when gated | proven |
| pickup/status slot 0 | `A5+0x1388` | `0x59F92` | PC090OJ staging record | `0x00A0` | `0x00E8` | 1 | `0x0A6A..0x0A6D` | `0x0003` | source `0..3`; hidden at `0xFF` | admitted HUD tick | proven |
| pickup/status slot 1 | `A5+0x140E` | `0x59F92` | PC090OJ staging record | `0x00B0` | `0x00E8` | 1 | `0x0A68` | `0x0080` | visible unless `0xFF` | admitted HUD tick | proven |
| pickup/status slot 2 | `A5+0x1410` | `0x59F92` | PC090OJ staging record | `0x00C0` | `0x00E8` | 1 | `0x0A66` | `0x0080` | visible unless `0xFF` | admitted HUD tick | proven |
| pickup/status slot 3 | `A5+0x140C` | `0x59F92` | PC090OJ staging record | `0x00D0` | `0x00E8` | 1 | `0x0A64` | `0x0080` | visible unless `0xFF` | admitted HUD tick | proven |
| ROUND label piece 0 | fixed template | `0x3B984` / `0x3B8EE` | PC090OJ | `0x0100` | `0x00E8` | 1 of 3 | `0x0034` | `0x0000` | records 17..21 group visible | event | proven |
| ROUND label piece 1 | fixed template | same | PC090OJ | `0x0110` | `0x00E8` | 1 of 3 | `0x0035` | `0x0000` | same | event | proven |
| ROUND label piece 2 | fixed template | same | PC090OJ | `0x0120` | `0x00E8` | 1 of 3 | `0x0036` | `0x0000` | same | event | proven |
| round/stage digit | display mirror `A5+0x0117` | `0x3B802` selector 3 | PC090OJ | `0x0128` | `0x00E8` | 1 | `0x002A + round` | `0x0000` | same; zero not blanked | event | proven |

The four `0x59F92` outputs are semantically selected before being placed in
chip-shaped WRAM records; the table names that original ownership without
endorsing that intermediary for a future Genesis implementation.

## 11. Raw arcade -> current Genesis Y mapping table

Original arcade visibility is Y 8..247 (240 lines). The current Genesis sprite
mapping subtracts eight and displays Y 0..223 (224 lines).

| Component | Arcade raw Y | Current mapped Y | Current 224-line result |
|---|---:|---:|---|
| reserve-lives digit | `0xE4` (228) | `0xDC` (220) | only top 4 lines of a 16px piece lie in-frame |
| energy indicator/cap/cells | `0xE8` (232) | `0xE0` (224) | outside visible frame |
| four pickup/status slots | `0xE8` (232) | `0xE0` (224) | outside visible frame |
| persistent ROUND label/digit | `0xE8` (232) | `0xE0` (224) | outside visible frame |

This documents the geometry only. It does not choose 240-line mode, movement,
cropping, a Window/plane, SAT, or mixed presentation.

## 12. Unresolved semantic questions

No semantic blocker remains for the requested lives or ROUND inventory. Pass
1's deliberately neutral friendly names for `A5+0x1410` and `A5+0x140C`
remain unresolved but do not block lower-HUD geometry or ownership.

## 13. Functions added to C tree

Primary bounded functions:

- `0x3B802` digit producer and exact five-entry configuration table;
- `0x3A64C` gameplay lower-HUD show boundary;
- `0x3A6B2` ROUND/READY transition presentation.

Six supporting helpers/boundaries, at the session limit but not beyond it:

- `0x3B866` leading-zero helper;
- `0x3B8EE` lower-HUD restore/refresh entry;
- `0x3B902` five-record restore/hide owner;
- `0x4527E` one-based stage initialization;
- `0x3A860` stage increment/display cap;
- `0x3BB48` generic PC080SN text writer.

The semantic model is extended in `rastan_player_hud.c`; raw reconstructions
are under `analysis/decompilation/c/raw/`. Coverage and README metadata are
updated.

## 14. What remains before Genesis implementation design

The original arcade lower-HUD semantics, geometry, ownership, visibility, and
update cadence requested by Passes 1 and 2 are now complete. The next task may
make an explicit Genesis presentation decision using the full table, but this
report makes none.

Open/closed issue impact: OPEN-024 is refined with exact original ownership;
it is not closed. OPEN-021 is confirmed separate because its SCORE/ROUND
columns belong to the high-score table. CLOSED-019 remains closed and is not
reopened. Known-findings impact is a refinement of KF-013 and KF-076 rather
than a contradiction; no direct `KNOWN_FINDINGS.md` edit is proposed in this
bounded pass.

