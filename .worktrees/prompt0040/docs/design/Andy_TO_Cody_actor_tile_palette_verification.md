# HANDOFF — Verify & Fix Actor Tile + Palette Reading (Andy → Cody)

**Task class:** static arcade decompilation verification + fix. No Genesis runtime change, no ROM
build, counter stays 360. Original ARCADE `rastan` is authoritative dynamic ground truth; Ghidra
exports + `build/regions/*.bin` are the static source.

**Goal:** the bestiary renders actor sprites and per-round palettes from my decode of the arcade
compositor. Tighe says the output is wrong. Find where my tile-reading and/or palette math is wrong,
fix it, and return the corrected per-actor data (format at the bottom) so Andy can regenerate the
report. **Do not trust my conclusions below — verify each against the ROM and against ORIGINAL
ARCADE MAME.**

---

## Files I touched (all my work is here)

| File | What it is |
|---|---|
| `tools/graphics_optimizer/compositor_vm.py` | My offline emulator of compositor VM `0x3C902` (general path only). START HERE. |
| `tools/graphics_optimizer/build_bestiary.py` | Report generator. `vm_pieces()`/`render_vm()` (~line 55), `dec()` tile decode, `rom_field_palette()` palette. |
| `docs/design/rastan_actor_graphics_manifest.json` | Semantic source of truth. `actors[].render` (method `vm`: base+anim+compositor_table), `actor_census_from_rom`, `bosses`. |
| `docs/design/rastan_actor_bestiary.html` | Generated report (artifact `https://claude.ai/artifact/CKUcQJpzhCoMAZ8fKMnVNF`). |
| `build/regions/maincpu.bin` | 68000 program (I read everything from here). |
| `build/regions/pc090oj.bin` | Sprite tile ROM. |

Base address fact I rely on: **`A5 = 0x10C000`** (arcade work RAM). So `A5+0xNNN` == absolute
`0x10C000+0xNNN`. Verify this first — if it's wrong, much of the below shifts.

---

## What I claim is PROVEN (please re-check, but these validated)

1. **Tile format (`build_bestiary.py:dec`)**: sprite `code` → `code*128` bytes in `pc090oj.bin` =
   one 16×16 4bpp tile, row-major, 8 bytes/row, high nibble = left pixel, color index 0 =
   transparent. (Confirmed earlier by SHA256; Lizardman/demon render correctly with it.)
2. **Palette DATA loader `FUN_0003BA20` @0x3BA20**: for the current round it fills 32 palette lines;
   line `i` ← pool index `maincpu[0x3BA88 + (round-1)*32 + i]`, palette = `0x4FD02 + idx*32`
   (16 0RGB words). 0RGB→RGB8: `pal5(n) = ((n*2)<<3) | ((n*2)>>2)` with n = each 4-bit component.
   (Computed R1 enemy palettes == `analysis/graphics_optimizer/.../enemy_palettes.json` exactly.)
3. **Actor palette LINE `FUN_00045684` @0x45684**: non-boss → nibble =
   `maincpu[0x45722 + (round-1)*12 + family]`; sets `actor+0x27 |= (0x40 | nibble)`. This nibble
   table is nearly round-invariant (only R5/family7 differs). Boss (family2) → table `0x456EC`
   indexed `variant*18 + (round-1)*3 + compAdj`. Alt table `0x4576A` used when `A5+0x2A2 != 0`.
4. **Compositor VM general path `0x3C902`** validated on TWO actors: Lizardman (base 0x004B,
   anim 0x17) → clean green reptile; Flying Demon (base 0x0129, anim 0x30) → winged creature
   matching Tighe's R3 screenshot. See emulator; each piece = 4 bytes `[ctrl, coordA, tileOff,
   coordB]`, tile = `+0x1E base ± tileOff`, palette attr from `+0x27`.
5. **Actor base resolution** (`0x4544e` @0x4544e): non-boss base = table `0x45502` (variant 0) or
   `0x45562` (variant≠0), indexed by `+0x3E family * 8`, word0 of the 8-byte record. `+0x01`
   (anim index) = record byte 3. A THIRD loader `0x4543e` (real entry 0x45442) indexes table
   `0x45592` by `(+0x06 record-type - 8)*8`; `0x45592` = `0x45562+0x30`, holds fam6-11 variant bases
   then rec6/7 = **0x061D** and rec8/9 = **0x0988** (bases my earlier census missed).

---

## Where I think my output is WRONG (focus here)

These are the suspects for the bad rendering. Please confirm/refute each from the code + arcade MAME.

**A. Compositor selection (`+0x38`) is probably wrong for most actors.**
`0x3D054` picks the compositor by `actor+0x38` (1→0x4770E table 0x4771C; 2→0x3F0BC table 0x3F0CE;
3→0x3FFDC table 0x40004; 4→0x3FFF0 table 0x4002C; else comp0 table 0x3D09E). I rendered **every**
field actor with **comp0 (table 0x3D09E)** because Lizardman happened to be comp0. But `+0x38` comes
from the spawn record byte2 low-nibble (`0x4A086 @0x4A096`) and varies per actor. A wrong table →
the program pointer is garbage → tiles scatter. **This is my #1 suspected bug.** Recover the real
`+0x38` per actor/animation.

**B. The anim index I use may be the wrong frame.**
I use `+0x01` = base-table byte3 as the animation index into the compositor table. But the render
list the compositor actually reads is a COPY at `A5+0x5C8` / `A5+0x748` / `A5+0x8C8` (see
`FUN_00045dfa` @0x45DFA: `d0 = renderrec+0x01`, `d7 = renderrec+0x02` facing, `d6 = renderrec+0x20`,
stride 0x40, 6/6/5 slots, SAT dest `0xD00460`/`0xD00170`/`0xD00300`). `+0x01` there is the CURRENT
animation frame, updated at runtime (writers around `0x421BA`, `0x3AFB6`). So my "static" anim may
not be a valid standing frame for every actor. Verify which anim index is the correct idle/rep frame
per actor (arcade MAME: read the render record's `+0x01` when the actor is on screen).

**C. Special-op programs are NOT emulated at all.**
`0x3C902` dispatches the first byte's high nibble: `0x10→0x3C830, 0x20→0x3C7A4, 0x30→0x3C6DC,
0x50/0x60→0x3C4D2, 0x90→0x3C75C, 0xA0→0x3C550, 0xB0→0x3C636, 0xC0→0x3C586`. These read `a0@(2)` as a
pointer and index sub-frames by `a4+0x0B`. My emulator returns `None` for these (I render raw tiles
instead). **Centaur 0x061D, dragon 0x0988, base 0x0889, and the bosses use these special ops** — so
they are currently unrendered/scattered. These handlers need decoding and emulating.

**D. Coordinate axes / flip only validated for facing=0.**
My emulator maps piece `x = coordB (+0x16)`, `y = coordA (+0x1A)`, `hflip` from ctrl nibble 0x40.
I only validated facing (`+0x02`) = 0. The facing=1 branch (`0x3C960`, negates coordB and tile
offset) and `d6`/`+0x20` mode (`0x3CA26`) are un-validated. Confirm axis assignment and both flips.

**E. Boss body base is unresolved (two conflicting loaders).**
Family-2 loader `0x4544e` returns base **0x033E**; but the boss paired-init `0x45342 @0x45342` sets
`+0x06 = 8/9` (from `A5+0xC5A`) and calls `0x4543e` → table `0x45592` → **0x0129 / 0x02AF**. I do NOT
know which base actually renders, nor the per-round boss (the scripted dispatch `0x4AB5C` selects per
round via `A5+0x13E`). The lexicon `round{N}_boss_composite` geometries are misidentified/duplicated
(round1/4/6 byte-identical) — do NOT use them. Resolve the real per-round boss actor record.

**F. Palette line → hardware mapping.**
`+0x27 = 0x40|nibble`, nibble 0-15. I assume the sprite uses palette line = nibble and that the data
in that line is the per-round pool (point 2). Validated for R1 field enemies, but confirm for later
rounds and for bosses/specials (whose palette may be overwritten after spawn, or use `A5+0x2A2`
alt table / boss table `0x456EC`).

---

## How to verify (cheap, decisive)

Prefer static (Ghidra + the .bin files) first; use ORIGINAL ARCADE MAME only for the dynamic facts
(real `+0x38`, real anim frame, real palette RAM). Suggested:

1. Static: for each actor, from its spawn record / base table recover **base (`+0x1E`), family
   (`+0x3E`), variant (`+0x752`), compositor (`+0x38`), anim (`+0x01`)**. Correct my assumption that
   `+0x38`=0.
2. Static: emulate the correct compositor table for that `+0x38`, INCLUDING the special ops
   (C above), to produce the real piece list.
3. Arcade MAME ground truth (use `tools/mame/run_rastan_trace_wsl.sh` / the FU1 playtrace): with an
   actor on screen, dump the render record (`A5+0x5C8+`) fields and the produced SAT
   (`0xD00460`/`0xD00170`/`0xD00300`) and CRAM/palette, and compare to the emulator. This tells you
   the true tile codes, coords, flip, and palette line the hardware used — the definitive check on
   my emulator.
4. Palette: dump the actual arcade palette RAM per round for the actor's line and compare to my
   `0x3BA88→0x4FD02` computation.

---

## What to return to Andy (so he can update the manifest + regenerate)

For **each actor** (all 38 census bases; prioritize: the 11 I render via VM, plus centaur 0x061D,
dragon 0x0988, 0x0889, and the 6 bosses), a record:

```
base_code, family(+0x3E), variant(+0x752), compositor(+0x38), anim_index(+0x01 used),
per_round: { R1..R6: { palette_line(nibble), pool_index, palette_rgb[16] } },
piece_list: [ {tile_code, x, y, hflip, vflip}, ... ]   # OR a verified PNG per actor/round
which_of_my_claims_A..F_were_wrong_and_the_correction,
notes (e.g. actor not present in some rounds, palette overwritten after spawn, boss per-round mapping)
```

Plus, specifically:
- Corrected `+0x38` compositor per actor.
- The decoded special-op handlers (C) enough to produce legal frames for 0x061D / 0x0988 / 0x0889
  and the bosses.
- The real per-round boss actor (base/variant/anim) resolved from `0x4AB5C` + `0x45342`.
- Confirmation or correction of `A5 = 0x10C000`, the coord axis mapping, and the flip handling.

Andy will consume that into `rastan_actor_graphics_manifest.json` (`actors[].render` = method `vm`
with base/anim/compositor_table, and `palette_instances`) and re-run `build_bestiary.py`.

---

## Quick pointers (addresses)
Spawn record copy `0x4A086`; schedule `0x4A104`; base tables `0x45502`/`0x45562`/`0x45592`; boss
tables `0x454BA/0x454D2/0x454EA`; palette-line `0x45722` (+alt `0x4576A`, boss `0x456EC`); palette
loader `0x3BA20` (pool-idx `0x3BA88`, pool `0x4FD02`); render entry `0x3D054`; VM `0x3C902`
(comp tables `0x3D09E/0x4771C/0x3F0CE/0x40004/0x4002C`); render setup `0x45DFA` (SAT
`0xD00460/0xD00170/0xD00300`); boss paired-init `0x45342`; scripted dispatch `0x4AB5C`
(selector `A5+0x13E`).
