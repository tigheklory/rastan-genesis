# Andy — Build 0149: Title HIGH SCORE 273100 + Coin-Transition Label Clear Fix

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `32c6a5a` (Build 0147 accepted). **Accepted build: 0149.**
Build 0148 (`151aab01…`) is retained as an **unaccepted candidate** (title-score fix only; see
`docs/design/Andy_build_0148_default_title_highscore.md`). Builds 0142–0148 not overwritten.
**Evidence dir:** `states/traces/build_0148_default_title_highscore/`.

## Outcome
Two bounded, proven title-header corrections, both faithful to the arcade:
1. **Title HIGH SCORE value = Cause B (wrong mapped RAM address).** `genesistan_pc090oj_hook_score_digit_3b802`
   remapped its work-RAM score source with region base `0x00100000` instead of the arcade A5 base `0x0010C000`,
   reading an all-zero window (`0x00FFC142`) instead of the real value (`0x00FF0142`). The high-score table was
   already correctly initialized; only the read address was wrong. (Full evidence: the Build 0148 report.)
2. **Coin-transition partial-label = Cause A (translated clear helper writes the wrong record range).**
   `genesistan_pc090oj_hook_target_59f5e` cleared PC090OJ records **0–7**, but the arcade `0x59F5E` clears **8
   records starting at `0x00D00048` (records 9–16)** and never touches the HIGH SCORE label records 4–8. The wrong
   range wiped label records 4–7 (GH/HI/S/CO) on coin insertion, leaving only record 8 (RE) → "RE" above 273100.

## Proven score-source mapping (settled)
- Arcade title high-score source: `0x0010C140..0x0010C142` = `31 27 00` = value **273100** (records read from
  `0x0010C142` down; 0x3B802 mode 2, count 6, dest `0x00D000D8`).
- Genesis initialization already present and correct: `0x00FF0140..0x00FF0165` is **byte-identical to the arcade
  ranking table** (`31 27 00 …`, names COB/THS/YAG/TKG/YTN at `0x00FF0157`), i.e. `genesis = a5 + (arcade -
  0x0010C000)`, `a5 = 0x00FF0000`. Value at `0x00FF0142` = `00 27 31`.
- The 0x3B802 hook read `a5 + (source - 0x00100000)` = `0x00FFC142` (all zeros) — off by `0xC000`.
- **Fix:** `subi.l #ARCADE_WORKRAM_A5_BASE(=0x0010C000)` (was `#0x00100000`). No RAM seed, no literal digits, no
  mirror/SAT write, no zero substitution, no title-specific logic. Initialization already existed — **not** a
  missing-default-seed defect.
- **Debugger substitution proof:** a hook-entry breakpoint replacing the source with `55 44 00` makes the normal
  producer emit digit codes `2A 2A 2E 2E 2F 2F` (value `445500`) — the display follows the source, not a constant.

## Proven coin-transition divergence
Reproduced by injecting a coin (Genesis P1 A; arcade `:SYSTEM` Coin 1) during the title on both machines and comparing
mirror records 4–8 at equivalent frames (no-credit → transition → credited-prompt):
- **Arcade:** records 4–8 = `3b/3a/3c/3d/3e` (full HIGH SCORE) remain **unchanged** through the entire coin
  transition (frames 150/185/230/320/430).
- **Genesis Build 0148:** at the coin state change (state `0/1/0` → `1/0/0`, frame ~170) records 4–7 became
  `code 0x0000, Y=0x0180, rep=0, slot=0xff`; only record 8 survived.
- **Writer traced:** the record-4 code write at the transition came from `.Lpc090oj_emit_slot` (`0x71976`), caller RA
  `0x719C0`, outer caller `genesistan_pc090oj_hook_target_59f5e` (`0x71B84`). That function loops `d0 = 0..7` calling
  `.Lpc090oj_clear_slot` (word0=0, Y=0x180, code=0).
- **Arcade original `0x59F5E`** (disassembled from `build/regions/maincpu.bin`): `move.w #8,d1; movea.l
  #0x00D00048,a0; clr.l d0; move.l d0,(a0)+; move.l d0,(a0)+; subq.w #1,d1; bne …` — clears **8 records from
  `0x00D00048` = record 9** (records 9–16), then writes the `0x0010C170` work-RAM tuple. The Genesis second (work-RAM
  `A5+0x170`) part was already faithful; only the **record range of the clear loop was wrong (0–7 vs 9–16)**.

**First exact divergence:** the clear-loop start record / range in `genesistan_pc090oj_hook_target_59f5e` (0 vs 9).

## Corrections (`apps/rastan-direct/src/pc090oj_hooks.s`)
```asm
+ .equ ARCADE_WORKRAM_A5_BASE, 0x0010C000          ; arcade A5 work-RAM base
  ; 0x3B802 score source remap:
- subi.l  #0x00100000, %d2
+ subi.l  #ARCADE_WORKRAM_A5_BASE, %d2

+ .equ HOOK_59F5E_CLEAR_FIRST_RECORD, 9            ; (0x00D00048 - PC090OJ_HW_BASE) / 8
+ .equ HOOK_59F5E_CLEAR_RECORD_COUNT, 8
  ; genesistan_pc090oj_hook_target_59f5e clear loop:
- moveq #0, %d0            ...  cmpi.w #8, %d0
+ moveq #HOOK_59F5E_CLEAR_FIRST_RECORD, %d0
+       ...  cmpi.w #(HOOK_59F5E_CLEAR_FIRST_RECORD + HOOK_59F5E_CLEAR_RECORD_COUNT), %d0
```
Both are minimal in-place corrections inside existing arcade-called helpers, using named constants. The shared
`.Lpc090oj_clear_slot` (3 callers) was left unchanged — a code-0 record is non-drawable regardless of its Y, so the
Genesis Y=0x180 park and the arcade Y=0 clear yield the same (non-represented) result; only the record range mattered.

## Validation (Genesis MAME, Build 0149)
### Stable no-credit title
`1UP 00`, complete `HIGH SCORE`, `273100`, complete `2UP 00`; no unwanted top zero rows (12/12 leading-zero score
records culled); logo/sword/TAITO/copyright unchanged (`snaps/coin_gen149_150.png`).
### Coined title transition
Records 4–8 = `3b/3a/3c/3d/3e`, all represented (slots 0–4), **unchanged** at frames 150/185/230/320/430 — identical
to the arcade; complete `HIGH SCORE 273100` retained on the credited "PUSH ONLY 1 PLAYER BUTTON" prompt
(`snaps/coin_gen149_230.png`); no stale/partial `RE`; leading-zero score records stay culled (no unnecessary clipped
records consume SAT resources).
### Source ownership
Debugger substitution `55 44 00` → displayed `445500`; no hardcoded 273100/digit sequence; Genesis table
`0x00FF0140..0x00FF0165` byte-equivalent to the arcade source.
### Regressions
- **Build 0145 palette:** item screen (2/2/6) staged line 3 (bank 51) byte-identical to Build 0145; all four bank-51
  item sprites (64–67) represented.
- **Build 0146 HIGH SCORE:** complete label (records 4–8), no record-4 clobber.
- **Build 0147 clipping:** 12/12 leading zeros culled, represented total 15; complete `2UP`.
- **Multiple clean boots:** 3/3 (0148) + 2/2 (0149) cold boots show `0x00FF0142 = 00 27 31` → `273100`.
- **Address-map:** `opcode_replace = 133`, `total_genesis_bytes_covered = 0x181D50`, **gaps = [], overlaps = []`.
- GATE_PASS, boot guard PASS, 30-s auto-trace clean.

## Build 0149
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0149.bin`
- **SHA256:** `84317ce92364865d2b96d02f31f35fd96b73c4f074ca7fe8b0a3a6c28e0ec3eb`
- **Size:** 1,580,368 B (unchanged; both fixes are same-size constant/immediate changes). Coverage unchanged.
- **Files changed:** `apps/rastan-direct/src/pc090oj_hooks.s`, regenerated `out/pc090oj_hooks.o/.elf/symbol.txt` +
  `build/rom_inventory.json`, this doc, the Build 0148 report (superseded banner), `AGENTS_LOG.md`, `OPEN_ISSUES.md`,
  `KNOWN_FINDINGS.md`.

## Architecture-compliance statement
CONFIRMED. Both corrections are inside existing arcade-called helper bodies (RTS), reusing the existing mirror-write /
clear pipeline. No special-casing of the text `HIGH SCORE`, any title-state number, or record numbers (the clear range
is the arcade's own `0x00D00048`-derived range, not a label carve-out); no SAT/mirror direct patching; no sprite
preserve/delete keyed on coin; no label reordering/priority; no new renderer/scene lifecycle; no change to Build 0147
clipping/offsets or the proven title-score source mapping. Real-hardware validation NOT CLAIMED.

## Deferred (explicitly out of scope, not blockers)
The ranking-table SCORE/ROUND values, item-scroll screen, missing item sprites, stray `2731` on later item/start
screens, the pinned BlastEm `0xC08C62` write, TAITO AMERICA vs JAPAN copyright, and gameplay were **not** investigated
or changed. The credited screen reached here ("PUSH ONLY 1 PLAYER BUTTON") is a title-owned prompt and retains the
correct header; later post-title scenes are outside this title-only task.

## Open/Closed Issues Impact
- **OPEN-001 (title/attract graphics incomplete):** materially advanced — the title/credited-title header is now
  correct (complete `HIGH SCORE 273100` on no-credit and through coin insertion). Not closed (ranking-page
  SCORE/ROUND and other post-title items remain).
- No issue closed; no duplicate opened. No missing-default-seed issue was created (initialization was correct).
