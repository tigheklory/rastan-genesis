# Andy — Build 0151: Restore BEST 5 SCORE and ROUND Values (+ Leading-Zero Suppression)

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `2850f92` (Build 0149 accepted). **Accepted build: 0151.**
Build 0150 (`cd7ac8be…`, source-base fix only) is retained as an **intermediate/unaccepted candidate** — it restores
the values but still showed 2 leading zeros; a second production change was required. Builds 0142–0150 not overwritten.
**Evidence dir:** `states/traces/build_0150_highscore_score_round/`.

## Outcome
**Cause A — SCORE/ROUND used the wrong source base** (NAME used the corrected `0x00FF0000` mapped base; SCORE/ROUND
did not). Plus a distinct, pre-existing leading-zero-suppression bug that only became visible once the values were
non-zero. Both fixed; the BEST 5 table now matches the arcade exactly.

## Diagnosis (proven)
The BEST 5 screen (state `2/0/0`) is built by three producers:
- **NAME** — `genesistan_hook_highscore_fg_producer` (arcade 0x3C3FE), descriptor table `0x3C654`, reads
  `ARCADE_HIGHSCORE_SOURCE_BASE(0x00FF0000) + src_off`. Already correct → names render.
- **Row templates** — `genesistan_hook_glyph_renderer_3bd48` renders static strings `"1ST        00"` … `"5TH …"`,
  `"SCORE ROUND NAME"`, `"BEST 5"`, history text.
- **SCORE/ROUND values** — `genesistan_hook_number_renderer_3c2e2` (arcade 0x3C2E2), descriptor table `0x3C57C`,
  fills the digits into the template's blank columns.

The ranking table is **initialized correctly and intact** at `0x00FF0140..0x00FF0165` on the BEST 5 screen (scores
`31 27 00 …`, rounds `03 03 03 02 02`, names) — verified at frames 300/450/600 — so **not a clear/overwrite (cause
D)**. No tilemap producer read the correct table `0x00FF0140`; instead the number renderer read **`0x00FFC140`**
(all zeros, 40 reads by PCs `0x70D6C`/`0x70DCC`). The number-renderer descriptors store **absolute arcade work-RAM
pointers** (`0x0010C1xx`), and the hook computed the source as `a4 = a5 + (source & 0x0000FFFF)` = `0xFF0000 + 0xC1xx`
= `0x00FFCxxx`. The mask kept the `0xC000` A5-base bits instead of subtracting them. **First divergence:** the source
base in `genesistan_hook_number_renderer_3c2e2` (`& 0x0000FFFF` vs `- ARCADE_WORKRAM_A5_BASE`). **Cause A.**

Descriptor table `0x3C57C` (confirmed): [0] score src `0x0010C145` (1ST), [1] `0x0010C148` (2ND), [2] `0x0010C14B`
(3RD), [4] `0x0010C14E` (4TH), [5] `0x0010C151` (5TH), [6–10] round srcs `0x0010C152..0x0010C156` (count `0xFFFF`
"all/round" handler), [11] `0x0010C11E` (1UP). All are `0x0010Cxxx` absolute pointers.

## Fixes (`apps/rastan-direct/src/tilemap_hooks.s`)
1. **Source base (values):**
```asm
+ .equ ARCADE_WORKRAM_A5_BASE, 0x0010C000        ; KF-039
  movea.l %a5, %a4
- andi.l  #0x0000FFFF, %d2                        ; kept 0xC000 A5-base bits -> read 0x00FFCxxx (zero)
+ subi.l  #ARCADE_WORKRAM_A5_BASE, %d2            ; a4 = a5 + (source - 0x0010C000) -> 0x00FF01xx
  adda.l  %d2, %a4
```
2. **Leading-zero suppression (formatting):** the hook already blanks leading `0` cells for the 6-digit score fields,
   gated by `cmpi.w #6, %d7` — but `%d7` (the saved count) is **clobbered** by the digit-emit path
   (`.Ltw_compose_d1_from_d0_d2`), so the check was always false and suppression never ran (harmless while values were
   zero; visible as `00273100` once values were correct). The descriptor pointer `%a0` is still live, so:
```asm
- cmpi.w  #6, %d7
+ cmpi.w  #6, (%a0)                               ; re-read the count from the live descriptor
  bne     .Lnr3c2e2_done
```

Both are minimal in-place corrections in the existing arcade-called producer, using the KF-039 named constant. No
hardcoded scores/rounds/text/tile-codes, no row-number special-cases, no direct SAT/tilemap patching, no data seeding,
no second renderer, and no change to the correct NAME path or to PC090OJ clipping/SAT/palette/title-score behavior.

## Validation (Genesis MAME, Build 0151)
- **BEST 5 table** (`snaps/best5_0151.png`) matches the arcade exactly:
  `1ST 273100 3 COB · 2ND 257200 3 THS · 3RD 197800 3 YAG · 4TH 125400 2 TKG · 5TH 112000 2 YTN`.
- **Dynamic ownership** (`snaps/best5_subst.png`): a debugger-only substitution of the 1ST ranking source
  (`0xFF0143..45 = 66 55 44`, round `0xFF0152 = 07`) changed the display to `44556600` / `ALL` while NAME stayed
  `COB` — the values follow the source; nothing is hardcoded (experiment not committed).
- **Header** `HIGH SCORE 273100` correct on the title/story headers; **no-credit title** correct; **coined title
  prompt** retains the complete HIGH SCORE label (records 4–8 = `3b/3a/3c/3d/3e` intact through the coin transition —
  Build 0149).
- **Regressions:** hidden top zero rows culled 12/12 and represented total 15 (Build 0146/0147); complete 1UP / HIGH
  SCORE / 2UP; item screen (2/2/6) staged line 3 (bank 51) byte-identical and item sprites 64–67 represented (Build
  0145); multi-boot 273100 consistent.
- **Address-map:** `opcode_replace = 133`; `total_genesis_bytes_covered = 0x181D50`; **gaps = [], overlaps = []`.
  GATE_PASS; boot guard PASS; 30-s auto-trace clean; coverage unchanged.

## Build 0151
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0151.bin`
- **SHA256:** `eab3a3fbfa27327ff5a34ba729467e43f59b3c2940f8bc84c27310a7f1e9429b`
- **Size:** 1,580,368 B. **Files changed:** `apps/rastan-direct/src/tilemap_hooks.s`, regenerated
  `out/tilemap_hooks.o/.elf/symbol.txt` + `build/rom_inventory.json`, this doc, `AGENTS_LOG.md`, `OPEN_ISSUES.md`,
  `KNOWN_FINDINGS.md` (KF-039 reinforced).

## Architecture-compliance statement
CONFIRMED. Two in-place corrections inside the existing arcade-called number-renderer producer (returns via RTS),
reusing the existing FG staging pipeline and the KF-039 A5-base mapping rule. No hardcoded values/text/tiles, no
row-number/title special-casing, no direct staged-tilemap/SAT/VRAM patching, no data seeding, no second renderer, and
no change to the NAME path, PC090OJ clipping/offsets/SAT/palette, or title-score mapping. Real-hardware validation NOT
CLAIMED.

## Open/Closed Issues Impact
- **OPEN-001 (title/attract graphics incomplete):** materially advanced — the BEST 5 SCORE and ROUND columns now
  render the correct arcade values (273100/257200/197800/125400/112000, rounds 3/3/3/2/2), matching the arcade. Not
  closed (other post-title/frontend items remain).
- No issue closed; no duplicate opened; no data-seed issue created (initialization was already correct).

## Deferred (explicitly out of scope, not blockers)
Post-item header damage, stray `2731` on item/player-start screens, missing item sprites, the item-scroll screen, the
pinned `0xC08C62` write, credit-display positioning, TAITO AMERICA vs JAPAN, and gameplay were **not** investigated or
changed.
