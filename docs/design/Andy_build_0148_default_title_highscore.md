# Andy — Build 0148: Restore Default Title High Score 273100

> **STATUS: SUPERSEDED / UNACCEPTED — see `docs/design/Andy_build_0149_title_highscore_coin_label.md`.**
> Build 0148 contains only the title-score source-mapping fix below and displays `273100` on the stable no-credit
> title, but a second, separate title-header defect (part of the `HIGH SCORE` label being cleared on coin insertion)
> was found afterward. That required a second production change, so Build 0148 is retained as an unaccepted candidate
> and **Build 0149** (this fix + the coin-transition label-clear fix) is the accepted build. The score-mapping
> investigation and evidence in this document remain valid and are carried into Build 0149.

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `32c6a5a` (Build 0147 accepted, "Build 147 Title Screen Success").
Build 0147 ROM `bb2af8f9da5a005a1fc25ab8a4faabce25479cd576048b4d4e3047ea6cd52ddd` — not overwritten.
**Evidence dir:** `states/traces/build_0148_default_title_highscore/`.

## Outcome
**Cause B — wrong mapped RAM address (implemented).** The default title high score `273100` is correctly translated
and seeded into Genesis work-RAM, but the title score-digit producer `genesistan_pc090oj_hook_score_digit_3b802` read
its score source from the wrong mapped address (region base `0x00100000` instead of the arcade A5 base `0x0010C000`),
landing `0xC000` past the real value at an all-zero window. Correcting the remap base makes the producer read the
value that is already present, restoring `273100`. No value was invented, hardcoded, or substituted.

## Investigation (proven)
The 0x3B802 record table (`.Lhook_3b802_record_table`) selects **mode 2 = HIGH SCORE**: digit count 6, dest
`0xD000D8`, score source `0x0010C142` (arcade absolute work-RAM). The producer remaps the source to Genesis WRAM and
generates digit codes `nibble + 0x2A`.

Runtime capture (settled title frame 150):
- **Arcade** A5 = `0x0010C000`; HIGH SCORE source `0x0010C142` = `00 27 31` (hi..lo); the full ranking table lives at
  `0x0010C140..0x0010C165` = `31 27 00  31 27 00  72 25 00  78 19 00  54 12 00  20 11 00 | 03 03 03 02 02 | 43 4F 42
  54 48 53 59 41 47 54 4B 47 59 54 4E` (6 scores, 5 rounds, names COB/THS/YAG/TKG/YTN).
- **Genesis** A5 = `0x00FF0000`. The same ranking table is present, byte-identical, at `0x00FF0140..0x00FF0165` — i.e.
  the high-score init already seeded it at `genesis = 0xFF0000 + (arcade - 0x0010C000)` (the names land at
  `0x00FF0157`, matching `ARCADE_HIGHSCORE_SOURCE_BASE`). HIGH SCORE value is at `0x00FF0142` = `00 27 31`.
- **But** the 0x3B802 hook computed its source as `a5 + (source - 0x00100000)` = `0xFF0000 + 0xC142` = `0x00FFC142`,
  which reads `00 00 00`. `0x00FFC142` is `0xC000` above the real value.

**First exact divergence:** the score-source remap base. Correct mapping (used by the init and the name producer):
`genesis = a5 + (source - 0x0010C000)`. The hook used `- 0x00100000`, an off-by-`0xC000` base error, so it read an
empty window and produced all-zero (leading-zero-suppressed → `00`) digits. The high-score initialization hypothesis
is **not** the cause — initialization is present and correct; the defect is purely the producer's source address map.

Cause classification: **B (wrong mapped RAM address)**. (A/C/D ruled out: the value is initialized (A no), control
flow runs (C no), and the correct mode/record/source pointer is selected — only the mapping constant was wrong (D no).)

## Implementation
`apps/rastan-direct/src/pc090oj_hooks.s`, one constant in the 0x3B802 source remap plus a named base:
```asm
+ .equ ARCADE_WORKRAM_A5_BASE, 0x0010C000   ; arcade A5 work-RAM base (arcade 0x0010C000 -> Genesis a5 0x00FF0000)
  ...
  move.l  %a2, %d2
- subi.l  #0x00100000, %d2
+ subi.l  #ARCADE_WORKRAM_A5_BASE, %d2
  movea.l %a5, %a2
  adda.l  %d2, %a2
```
This is preferred-fix option 2 (correct the mapped address/pointer) at the producer's authoritative source read. The
producer still displays whatever value is stored in its source; only the address it reads is corrected. It affects all
five 0x3B802 modes uniformly (1UP/2UP/HIGH SCORE/credits), all anchored at the same arcade A5 base, so every score now
reads the correct `0x00FF01xx` work-RAM. No mirror/SAT direct write, no hardcoded text/digits, no title-screen or
record-number special-case, no clipping/offset/allocation/palette/renderer change.

## Validation (Genesis MAME, Build 0148)
1. **Cold-boot title shows 273100** (`snaps/gen148_title.png`), matching the arcade header.
2. **Source bytes match:** Genesis `0x00FF0142` = `00 27 31` == arcade `0x0010C142` = `00 27 31`.
3. **Mirror digit records match the arcade** (records 27..22, dest `0xD000D8` down): codes
   `0x2A,0x2A,0x2C,0x31,0x2D,0x2B`, leading-zero records 27/26 at Y=`0x0110` (offscreen, suppressed), records 25..22
   at Y=`0x0010` (represented, slots 08/07/06/05) — byte-identical to the arcade records 22..27.
4. **Debugger substitution:** breakpoint at the hook substituting the source with `55 44 00` produced digit codes
   `0x2A,0x2A,0x2E,0x2E,0x2F,0x2F` (value `445500`) — the producer displays the source value, not a constant.
5. **Multiple clean boots:** 3/3 cold boots show source `0x00FF0142 = 00 27 31` and visible digits `2731` (=273100),
   identical each boot.
6. **Build 0147 clipping intact:** no unwanted top zero rows (the 12 leading-zero score records 28–33/37–42 remain
   culled, 12/12); complete `1UP`, `HIGH SCORE`, `2UP`; visible `1UP`/`2UP` `00` scores retained; the two HIGH SCORE
   leading zeros (records 26/27, Y offscreen) receive no SAT slot; no fully-clipped record regained a slot
   (represented 11 → 15, the +4 being the newly-visible high-score digits, all on-screen at Y=0x10).
7. **Build 0145 palette / Build 0146 HIGH SCORE intact:** item screen (state 2/2/6) staged line 3 (bank 51)
   byte-identical to Build 0145; all four bank-51 item sprites (64–67) represented; HIGH SCORE label complete.
8. **Other screens:** attract cycle ran clean (states 2/0/0 → 2/2/6, no crash). The story/ranking screen header also
   shows `HIGH SCORE 273100`. The BEST-5 ranking-table SCORE/ROUND columns still read `00000000 / 0` — this is the
   **separate, pre-existing ranking-page score problem** (a different producer), explicitly out of scope and
   **unchanged** by this fix; the ranking NAMES (COB/THS/YAG/TKG/YTN) render correctly. No new regression.
9. **Address-map:** `opcode_replace = 133`; `total_genesis_bytes_covered = 0x181D50`; **gaps = [], overlaps = []**.

## Build 0148
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0148.bin`
- **SHA256:** `151aab018a17787b7bb2143eaee0458b9342a1d1928de856adbb6e9ba76fbbc8`
- **Size:** 1,580,368 B (identical to Build 0147; the change is an immediate-value constant). GATE_PASS; boot guard
  PASS; 30-s auto-trace clean. Coverage constant unchanged. Builds 0142–0147 not overwritten.
- **Files changed:** `apps/rastan-direct/src/pc090oj_hooks.s` (added `ARCADE_WORKRAM_A5_BASE`; corrected the 0x3B802
  source remap), regenerated `out/pc090oj_hooks.o/.elf/symbol.txt` + `build/rom_inventory.json`, this doc,
  `AGENTS_LOG.md`, `OPEN_ISSUES.md`.

## Architecture-compliance statement
CONFIRMED. The change is a single mapped-address correction inside the existing arcade-called score-digit producer
(returns via RTS), reusing the existing mirror-write pipeline. The producer continues to read its authoritative
work-RAM source and display whatever value is stored there. No default seeding, no hardcoded value/text/digits, no
direct PC090OJ mirror/SAT write, no title/record special-case, and no change to Build 0147 clipping/offsets/allocation
or the palette/renderer. Real-hardware validation NOT CLAIMED.

## Open/Closed Issues Impact
- **OPEN-001 (title/attract graphics incomplete):** materially advanced — the title `HIGH SCORE 273100` now displays
  (was `00`), via a mapped-address correction to the existing score producer. Not closed (the separate ranking-page
  SCORE/ROUND columns and other title/score items remain).
- No issue closed; no duplicate opened. The ranking-page SCORE/ROUND defect is noted as a separate open item, not
  addressed here.

## Scope statement
The ranking-page BEST-5 SCORE/ROUND columns, score-value gameplay behavior, palette, clipping/offsets (Build 0147),
PC080SN, gameplay, audio, and real hardware were not changed.
