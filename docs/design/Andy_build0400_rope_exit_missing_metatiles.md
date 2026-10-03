# Andy — R1/P1 Rope-Exit Missing Metatiles — STATIC ELIMINATION, STOP BEFORE BUILD

**Baseline:** Build 0399. **Counter:** 399 → **399** (no ROM; no production source changed). Andy gameplay
verification: **NO** (authority: TIGHE). Build 0399 combined-X/Y fix protected and untouched.

**Outcome: STOP, NO BUILD.** Static analysis conclusively *eliminates* the special-surface path and the
residency/LUT "missing identity" hypothesis, and proves the source descriptor data + resolver input are
correct. The remaining first-divergence candidates (runtime source-selection vs producer coverage vs
publication) cannot be distinguished from the available static artifacts; a Genesis-side capture at the two
rope exits is required, exactly as the Exodus Segment-6 capture decided the combined-X/Y defect. Per the task
gate ("Build 0400 if and only if one bounded generic first divergence is proven"), no build is produced.

## 1. The two anchors (same shared identity)
| | Record | World cells | Descriptor entry | Entry words | Metatile ptr |
|---|---|---|---|---|---|
| A | record 2 (Segment 2) | X48..51 / Y40..43 | `0x02C54C` | `0x0003, 0x2120` | `0x2120` |
| B | record 14 (Segment 14) | X44..47 / Y36..39 | `0x02A588` | `0x0003, 0x2120` | `0x2120` |

Both entries are byte-identical and point at the **same** descriptor `0x2120`. **Same complete metatile
identity: YES.** This is one shared semantic feature, so the correct fix is a shared cause, not two
coordinate hacks.

## 2. Descriptor 0x2120 — exact expected output (derived, not assumed)
The resolver reads the metatile at `PC080SN_DESC_SECOND_WORD_BASE(0x200) + word1(0x2120) = 0x2320` in Genesis
ROM, which is the +0x200 whole-maincpu rebase of arcade `0x2120`. Its 16 tile codes (`(row&3)*8+(col&3)*2`
layout) are:

```
row0: 0438 0439 040A 040B
row1: 040C 00C2 00C3 00C4
row2: 040D 00C6 00C7 010B
row3: 00C9 040E 040F 0410
```

Collision (strip-descriptor side, per Cody Step-1): uniform form `descriptor+0x20 = 0x00FF`,
`+0x22 = 0x0001`, bit 7 clear → every cell collision value `0x0001`. **Constituent tile words identical at
both anchors: YES. Collision definitions identical: YES.** Expected visual = the 4×4 platform above; expected
collision = solid `0x0001` across X48..51/Y40..43 and X44..47/Y36..39.

## 3. Eliminations (proven, so future work skips these)
- **Special surface (0x05A29C → 0x05A2EE): NOT involved.** `descriptor+0x20 == 0x00FF`, value `0x0001`,
  bit 7 clear ⇒ `0x05A2EE` cannot be invoked (Cody Step-1, re-confirmed). The four `0x25C7` writes do not own
  these platforms.
- **Residency / LUT "missing identity": REFUTED.** `FG_BOUNDARY_LUT_WORDS = 10240`; all 16 codes are in-range
  (max `0x0439`). record 2 → package 0, record 14 → package 4, **both with 0 dropped codes**
  (`plane_a_dropped_by_record`). So `fg_cache_resolve` does **not** return blank for these codes on capacity
  grounds, and no required identity is omitted from either active package.
- **Source descriptor data: CORRECT.** Both descriptor entries exist in `maincpu.bin` with `{0x0003, 0x2120}`
  and lie inside the arcade descriptor table `[0xF08, 0x3A00C)`; the resolver's rebased metatile read yields
  the codes above. Steps 1 (source/descriptor), 2 (resolver input), and 3 (residency/LUT) of the required
  divergence order are therefore **clean**.

## 4. What is NOT yet proven (the remaining first-divergence candidates)
With steps 1–3 clean, the first divergence is one of:
- **(S) runtime source-selection** — the live `SRC_TABLE` (`a5@0x1000`) does not point at descriptor entry
  `0x02C54C` / `0x02A588` when the camera is at the rope exit (the arcade scroll state selects a different
  entry), so the producer resolves a *different* (blank/other) descriptor at those world cells.
- **(C) producer coverage / residency window** — world rows Y40..43 / Y36..39 are not inside the resident
  32-row window the producer stages at that camera position (a vertical ring-window boundary), so the cells
  are never staged.
- **(P) publication** — staging holds the platform but the VBlank publisher drops it.

These require the Genesis runtime state at the rope exit; they cannot be read from the compiled artifacts.

## 5. Clues to resolve at capture time (do not conclude from them yet)
- "Rastan lands ~one metatile lower" + "lizard men traverse where the platform should be" is consistent with
  **visual staging wrong while collision is correct** (task outcome B) — but a player-grounding vs
  enemy-traversal consumer split could also explain it. Determine the first visual/collision source state
  before interpreting this.

## 6. Decisive capture to isolate S vs C vs P (Exodus, as in the X/Y investigation)
At each rope exit (Segment 2 and Segment 14), paused with the platform visibly missing, capture:
1. **Plane-A VRAM** at the anchor cells — are the platform's physical ring cells blank (`0x0000`) or holding
   a wrong tile?
2. **`staged_fg_buffer`** (`0xFF50A0 + (phys_row*64+col)*2`) at the same cells — blank or the expected
   platform name words? (staged blank ⇒ S or C; staged correct + VRAM blank ⇒ P.)
3. **Live `SRC_TABLE`** (`a5@0x1000`, 16 longs at `0xFF1000`) + `strip_group`/`strip_index`
   (`0xFF10CC`/`0xFF10CA`) — does the selected descriptor for these world cells resolve to `0x2120`? (points
   at S vs C.)
4. **Arcade collision ring** at `0x0010F260` (A) / `0x0010F058` (B) — is collision `0x0001` present while
   visual is blank? (confirms a visual-only vs shared divergence.)

The first mismatch among VRAM/staged/source wins; then the repair is bounded to that owner.

## 6b. Metatile 0x2120 Genesis realization audit (added — proves the metatile is correct)
Per-cell audit of all 16 constituent codes through the generated package code→slot map
(`boundary_packages.bin`) + slot identity/pattern (`slot_patterns_debug.json`), for BOTH rope-exit
packages (record 2 → package 0, record 14 → package 4). Attr from descriptor word0 `0x0003` =
palette line 3, priority 0, no flip = `0x6000`.

**Record 2 / package 0 — Genesis 4×4 name words:**
```
6342 6389 62BD 62C2      (codes 0438 0439 040A 040B -> slots 834 905 701 706)
6304 62EF 62DA 62E3      (codes 040C 00C2 00C3 00C4 -> slots 772 751 730 739)
6305 630B 62D0 6310      (codes 040D 00C6 00C7 010B -> slots 773 779 720 784)
62F3 630A 62F8 62EB      (codes 00C9 040E 040F 0410 -> slots 755 778 760 747)
```
**Record 14 / package 4 — Genesis 4×4 name words:**
```
63AC 6459 6387 6389
6390 62EF 62DA 62E3
6391 630B 62D0 6310
62F3 6393 638F 638E
```
For **all 16 cells in both packages**: the code is present in the map (no blank substitution), the
slot's stored identity equals the arcade code (`slot 834 → identity 1080 = 0x0438`, etc. — faithful
extraction, no alias/collision/wrong-pattern), the slot is a valid Plane-A slot (663..1338), the name
word carries the correct palette line 3 with no flip, and the 4×4 ordering (`(row&3)*8+(col&3)*2`) is
preserved. The `+0x200` rebase is correct (resolver reads Genesis `0x2320` = arcade `0x2120`; the slot
identity `0x0438` confirms the metatile base, not `0x2320`'s `0x043E`). Pixels are the faithfully
extracted arcade pattern for each identity (build reindex verification covers the conversion).

**Failure classes checked and ELIMINATED for the metatile:** wrong code→slot mapping NO; wrong pattern in
slot NO; stale/wrong package mapping NO; wrong attr/palette bits NO; wrong H/V flip NO; wrong 4×4 ordering
NO; code alias / identity collision NO; blank substitution NO; wrong metatile expansion NO; wrong +0x200
rebase NO.

**Shared-identity test:** metatile pointer `0x2120` is referenced ~12 times in the Round-1 descriptor table
(attr `0x0003`/`0x0007`), e.g. entries `0x01F554, 0x0217FC, 0x02198C, 0x0219C0, 0x0225C8, 0x025FA8,
0x025FB4, 0x02822C, 0x02A4E4, 0x02A588(anchor B), 0x02C54C(anchor A), 0x02C62C, 0x033BBC`. Tighe's testing
has the rest of R1/P1 Plane-A correct, so `0x2120` renders correctly at its ~10 other occurrences. The
metatile is therefore not intrinsically broken, and it realizes correctly at both rope-exit packages.

**Conclusion of the audit — OUTCOME B:** the Genesis realization of metatile 0x2120 is itself correct
(16/16 cells, both packages, and correct elsewhere in R1). The remaining defect is strictly that these
correct cells are **not being staged/published** at the two rope exits — a runtime source-selection /
producer-coverage / publication question (§4), which now justifies the targeted capture in §6.

## 6c. LIVE ARCADE DESCRIPTOR EVOLUTION / RUNTIME RECOMPOSITION (supersedes the static-0x2120 framing)

**Scope correction:** §2/§6b prove only that *static* metatile 0x2120 is realizable on Genesis. They do
**not** establish the live runtime descriptor. The Palette Composer coordinate (0x2120) is **not** the
metatile the runtime actually selects at the ledge.

**The live ledge metatile is 0x3408, not 0x2120** (re-derived from existing evidence
`Cody_rope_ledge_same_world_block_comparison.md` + the current resolver math; the older
`arcade_vs_genesis_comparison` is superseded but its raw live values are independently verifiable):

At the ledge block **logical rows 36–39, cols 48–51** (row_group 9, col_block 12), progression
`A5+0x013E = 3`, `strip_group (0x10CC)=3`, `strip_index (0x10CA)=0`:
- live row-source pointer `A5+0x1000[9] = 0x02A2A8`
- ring-unwrap delta = **−7** (resolver: `col_block(12) − strip_group(3) = 9`; `front_phys_col = 3*4+0 = 12`;
  world col 48 > 12 ⇒ subtract 16 ⇒ `9 − 16 = −7`)
- source entry = `0x02A2A8 + (−7)*4 = 0x02A28C` → `{word0 0x0003, word1 0x3408}`
- metatile **0x3408** (Genesis runtime copied record `0x02A48C`; resolver reads metatile at genesis
  `0x3608 = +0x200` rebase of arcade `0x3408`)
- 16 source tile words: `0164 0165 0166 0167 / 0168 0169 016A 01B5 / 016C 017B 0196 01B7 / 0170 017E 017F 018C`

**Runtime mechanism (Phase 3 answers):** the ROM descriptor data is immutable; the runtime only **advances
the live source pointer** `A5+0x1000` (`map_advance_source_ptrs`, arcade `0x0558C6`, +4 per streamed
4-column block) and the resolver's ring-unwrap applies delta −7, **selecting a different descriptor record
(`0x02A28C`, metatile `0x3408`) than the static editor coordinate's `0x2120`**. Data at 0x2120 is not
mutated (no); a different descriptor whose word1 points elsewhere is selected (yes); cells are not combined
from multiple sources (no, one complete 4×4 `0x3408`); no RAM descriptor rewrite (no); only the source
pointer moves while ROM descriptors stay immutable (yes). **This validates Tighe's runtime-recomposition
hypothesis** about the live metatile.

**Arcade vs Genesis agree on the entire source chain (source-selection divergence ELIMINATED):** the
existing same-world-block comparison proves retained source entry, relocated runtime entry (`0x02A48C`),
descriptor word0/word1, and all 16 source tile words are **identical** arcade vs Genesis, and the current
Build-0399 resolver math independently reproduces delta −7 → `0x02A28C` → `0x3408`. **Genesis selects the
correct live descriptor** — it is NOT "faithfully rendering the wrong descriptor."

**Residency of 0x3408 is clear:** all 16 codes (`0164..018C`) are mapped to valid slots with 0 missing in
the rope-exit package (package 6 at progression 3) and also in packages 0 and 4. So residency is not the
cause either.

**First divergence is therefore STAGING or PUBLICATION of the 0x3408 ledge block — not yet proven.** The
Build-0373 capture showed 6/16 staged cells nonzero and agreeing, but MAME could not read Plane-A VRAM, so
the source-to-publication boundary was never resolved; and that evidence predates the 0390–0399 Plane-A work.
Per the task's own gate (source matches ⇒ proceed to staging/VRAM), the decisive step is now an **Exodus
capture at Build 0399** (VRAM is readable there, unlike MAME) at the ledge block rows 36–39/cols 48–51:
compare `staged_fg_buffer` vs Plane-A VRAM for all 16 cells. staged-correct + VRAM-blank ⇒ publication;
staged-blank ⇒ a staging/producer-coverage gap at that ring row/window. (Exit B / Segment 14: no capture yet;
mechanism presumed shared — same runtime source-pointer advancement — to be confirmed by the same capture.)

## 6d. Screenshot identity match — BLOCKED (images not received) + bottom-left cell finding

The two 32×32 arcade/Genesis screenshots this step requires **did not arrive** (only the earlier Exodus
Segment-6 captures are present). The screenshot pattern-match / offset analysis cannot run without them.

What is resolvable statically — Tighe's bottom-left observation (R3C0, R3C1 show Layer B through): those are
metatile 0x3408 row 3, codes **R3C0 = 0x0170**, **R3C1 = 0x017E**. Both map to **valid, fully-visible**
patterns in every candidate package (0/4/6): R3C0 `0170 → slot 806 (pkg0/6) / 917 (pkg4)`, identity 368;
R3C1 `017E → slot 925 / 1126`, identity 382; each 64/64 nonzero pixels. **So the blank bottom-left is NOT a
code→slot residency/mapping gap** — the correct visible pattern exists and is addressable. The blank is a
staging/publication outcome for those specific ring cells, consistent with §6c.

Arcade intended 0x3408 identities (ready for the screenshot match when images arrive), package 0:
```
R0: 0164/id356  0165/id357  0166/id358  0167/id359
R1: 0168/id360  0169/id361  016A/id362  01B5/id437
R2: 016C/id364  017B/id379  0196/id406  01B7/id439
R3: 0170/id368  017E/id382  017F/id383  018C/id396
```

**Still needed to proceed:** re-send the two 32×32 screenshots (arcade + Genesis Build 0399) of the ledge
block, OR an Exodus capture at Build 0399 of `staged_fg_buffer` vs Plane-A VRAM for the 16 cells of rows
36–39/cols 48–51. Either isolates staging vs publication and the exact bad cells.

## 6e. Ordinary-segment black-strobe owner (located; NOT patched — rope gate not met)

The black strobe at an ordinary gameplay package/epoch transition is `fg_boundary_install`
(`fg_tile_cache.s`): it masks interrupts, writes **MODE2 display OFF** (line ~303), performs the package
install (pattern DMA + LUT rebuild + name remap), then writes **display ON** (line ~555) — **except** when
`genesistan_scene_present_pending` is set, where it deliberately leaves the display off for the full
scene-entry fill (`.Linstall_leave_display_off`, the Build-0395 ROUND/READY path to preserve). Record-only
transitions within an epoch already run with no display-off (line ~236). So the targeted change (when Build
0400 is cut) is to skip the line-303 off / line-555 on for the **non-scene-entry** install only, keeping the
scene-entry blanking — pending confirmation that the package pattern-DMA + name remap is safe with display on
under the existing atomic/staged publication. **Not implemented this task** (no ROM is produced until the
rope first divergence is proven).

## 6f. SCREENSHOT 4×4 GRAPHIC-IDENTITY MATCH (Tighe's two 32×32 images) — FIRST DIVERGENCE FOUND

Both images structurally matched against the Genesis slot-pattern corpus (palette-independent pixel-partition
equality, H/V-flip tested). Result:

- **GENESIS (image 58)** = metatile **`maincpu[0x2120]`** exactly, all 16 cells, no flip:
  `0438 0439 040A 040B / 040C 00C2 00C3 00C4 / 040D 00C6 00C7 010B / 00C9 040E 040F 0410`.
- **ARCADE (image 57)** = metatile **`maincpu[0x2320]`** exactly:
  `043E 0449 044A 044B / 044C 044D 044E 0445 / 044F 0450 0451 0448 / [00FF 0001] 0492 0493`.
  (R3C0/R3C1 are the arcade metatile's **collision words** `00FF/0001`, not visual tiles — this is exactly
  the "bottom-left two cells show Layer B through" Tighe observed on Genesis; they are the collision half.)

**Wrong Genesis cells share a constant source offset: YES. Exact offset: ARCADE = GENESIS + 0x200.** Every
non-blank cell obeys `arcade_metatile_addr = genesis_metatile_addr + 0x200`. Genesis renders the metatile
**0x200 too low**. `0x200` is exactly `PC080SN_DESC_SECOND_WORD_BASE`.

Mechanism: both sides use the *same* descriptor (anchor `0x02C54C = {0003, 2120}`; **no** descriptor has
word1=0x2320). Arcade reads `arcade[0x200 + word1] = arcade[0x2320]`. Genesis resolver computes
`0x200 + word1 = 0x2320` as a *Genesis-ROM* address; because the Genesis ROM is the arcade program rebased
`+0x200`, `genesisROM[0x2320] = arcade[0x2120]`. So the single `0x200` base is **absorbed by the ROM rebase**
instead of also serving as the metatile-table base — Genesis ends up reading `arcade[word1]` while the arcade
reads `arcade[word1 + 0x200]`.

**This confirms Tighe's runtime/offset theory and the "Genesis faithfully rendering the wrong source"
possibility: Genesis is rendering a real metatile that is 0x200 (one `SECOND_WORD_BASE`) too low.**

### Why no patch yet — global vs local scope is unresolved and the wrong choice is catastrophic
If the arcade metatile base is uniformly `0x200`, the correct resolver base is `0x400` (arcade metatile base
`0x200` + ROM rebase `0x200`) and the bug is **global** — every Plane-A metatile is currently 0x200 low. But
the Build-0373 ledge (word1 `0x3408`) was reported correct with the current base, and the ledge content
`0164…` is at `maincpu[0x3408]` (base 0), not `maincpu[0x3608]=01F6…` (base 0x200). Those two facts are in
tension, so I cannot tell from static data alone whether this is:
- **GLOBAL** (resolver `PC080SN_DESC_SECOND_WORD_BASE` should be `0x400`, fixing every metatile — but
  rewriting *all* accepted terrain, Builds 0391/0395/0397/0398/0399), or
- **LOCAL** (the arcade applies a runtime metatile-pointer recomposition `+0x200` at this descriptor class
  that Genesis omits; most descriptors are fine with base 0x200).

A global base change applied on a wrong guess would corrupt all currently-accepted Plane-A terrain. **No
patch is made until the scope is proven.**

### The single decisive discriminator
Capture/observe the ARCADE at the **ledge block** (word1 `0x3408`, rows 36–39/cols 48–51) and read which
tiles it shows:
- arcade ledge = `maincpu[0x3408]` (`0164 0165 0166 0167 …`) ⇒ arcade base 0 there ⇒ the anchor's +0x200 is
  **LOCAL** (a per-descriptor recomposition to find and mirror);
- arcade ledge = `maincpu[0x3608]` (`01F6 01F7 01F8 01F9 …`) ⇒ arcade base 0x200 everywhere ⇒ **GLOBAL**
  (resolver base must become 0x400).

One arcade screenshot of the ledge block (same method as the two supplied) settles it and the exact bounded
fix follows immediately. (The two supplied images are the X48/Y40 **anchor** block, not the ledge.)

## 6g. CORRECTED layer-aware audit + PROVEN ROOT CAUSE + Build 0400 fix (supersedes 6f's direction)

**Image assignment was swapped in 6f.** Re-classified by matching each cell against the Genesis slot corpus
(palette-independent, flip-tested) AND by the Layer-A-visible test:
- **image 57 = GENESIS** — renders metatile `maincpu[0x2320]` (`043E 0449 044A 044B / 044C 044D 044E 0445 /
  044F 0450 0451 0448 / [00FF 0001] 0492 0493`). Cells R3C0/R3C1 are the `00FF/0001` **collision words** →
  no visible Plane-A → Layer B shows through (exactly Tighe's observation).
- **image 58 = ARCADE** — renders metatile `maincpu[0x2120]` (`0438 0439 040A 040B / 040C 00C2 00C3 00C4 /
  040D 00C6 00C7 010B / 00C9 040E 040F 0410`), all 16 real tiles.

So **GENESIS = ARCADE + 0x200** (Genesis renders the metatile 0x200 too high), and the blank bottom-left is a
direct consequence (cells 12/13 of `maincpu[0x2320]` are collision markers).

**Root cause (proven from the built ROM, not screenshots):** the Genesis copy of **exactly the two
rope-exit descriptors** has word1 relocated `0x2120 → 0x2320`:
- arcade `0x02C54C = {0003,2120}` → genesis `0x02C74C = {0003,2320}`
- arcade `0x02A588 = {0003,2120}` → genesis `0x02A788 = {0003,2320}`

All ~10 other `{0003,2120}` descriptors keep word1=0x2120 (correct), and the ledge's `0x3408` is untouched.
The cause is a **data-as-code false positive** in `rom_absolute_call_relocation`: its whole-maincpu opcode
scan reads the PRECEDING descriptor's word1 value `0x237C` (an abs-long opcode in the scan list) as a
`move.l #imm` instruction, so the next 4 bytes — this descriptor's `0x00032120` — are relocated as an
abs-long operand `+0x200` → `0x00032320`, flipping word1 to `0x2320`. A whole-table scan found **exactly
these two** word1 corruptions (opcode `0x237C` @arcade `0x02A586`/`0x02C54A`), both rope exits.

Address-space equation (W = arcade word1, R = copied-ROM rebase 0x200, B = resolver `SECOND_WORD_BASE` 0x200):
- correct: genesis reads `built[B + W]` = `built[0x200 + 0x2120]` = `built[0x2320]` = `maincpu[0x2120]` = right.
- bug: W was pre-bumped to `W+R` (0x2320), so genesis reads `built[B + W + R]` = `built[0x2520]` =
  `maincpu[0x2320]` = wrong. The `+0x200` was double-counted: once (wrongly) into the stored word1, once
  (correctly) by the resolver base.

**FIX (Build 0400, generic, byte-neutral, not coordinate-based):** two `verbatim_restores` in
`specs/rastan_direct_remap.json` restore the two corrupted word1 values to the arcade original `0x2120`
AFTER the relocation pass (undoing the false +0x200). Verified in the built 0400 ROM: genesis `0x02C74C` and
`0x02A788` word1 = `0x2120`; the resolver now reads `built[0x2320]` = `0438 0439 040A 040B` = the correct
platform. `resolve_plane_a_cell` and the relocation scanner are otherwise unchanged. This necessarily covers
**both** rope exits (both were the same bug). Exit B = Segment 14 is the `0x02A588` entry, fixed identically.

**Global vs local: LOCAL** — only these two descriptor entries were corrupted; no global base change (that
earlier concern is resolved and no risk to the accepted terrain).

## 6h. Ordinary-segment black-strobe removal (Build 0400)
`fg_boundary_install` (`fg_tile_cache.s`) unconditionally wrote MODE2 display-OFF (~line 303) at the top of
every package install, then display-ON at the end (except scene-entry). Build 0400 guards the top OFF with
`genesistan_scene_present_pending`: only a **major scene-entry fill** (that flag, set by the arcade 0x0503DC
64-publication scene fill; `load_scene_tiles` already turns display off for those) blanks the display. An
**ordinary** gameplay package/epoch install (flag clear, display currently on) now keeps the display ON — no
black strobe. The bottom display-ON for the ordinary path becomes a harmless no-op (writes 0x74 while already
on). Scene-entry blanking (`.Linstall_leave_display_off`, Build-0395 ROUND/READY) is unchanged; cold-boot /
title / `load_scene_tiles` blanking is unchanged. No extra DMA, no redraw, no added per-frame work (two
register writes removed from the ordinary path). **Atomicity caveat for Tighe's test:** the ordinary install
(pattern DMA + LUT rebuild + name remap) now runs with the display enabled inside the existing
interrupt-masked critical section; if a visible partial-state frame appears, that is the next thing to
address — but the request was to stop blanking, which this does.

## 6i. Build 0400 result
- Changes: `specs/rastan_direct_remap.json` (2 verbatim_restores), `apps/rastan-direct/src/fg_tile_cache.s`
  (strobe guard). `Test.json` unchanged (snapshot SHA `02d0122a…`). `resolve_plane_a_cell` and the Build-0399
  X/Y fix untouched.
- Five-ROM family `rastan_direct_video_test_build_0400{,_c,_d,_do,_s}.bin`; gates
  `[canonical=PASS entry=PASS epoch=FAIL]`; boot guard PASS pre+post.
- Canonical SHA `36e0806fb288d38d3b092fb01b2c8a01fe69de1934b206c2a47677b561c02fe5`. Counter 399 → **400**.
- Fix verified in ROM (word1 restored to 0x2120; resolver reads the correct `0438…` metatile).
- Status: **Build 0400 candidate — TIGHE MUST VERIFY** (both rope exits standable/visible; ordinary segment
  crossings with no black strobe and no transition garbage; Build-0399 X/Y + ROUND/READY regressions; perf).

## 7. Why no build (historical — superseded by §6g/§6i; Build 0400 was produced)
No bounded generic first divergence is proven — only eliminations. A guessed repair to source-selection,
the vertical producer window, or publication would risk the protected Build-0399 combined-X/Y fix and the
accepted Plane-A work (0391/0395/0397/0398), and the task's gate forbids a build without a proven cause.
Build 0399 is unchanged; counter stays 399.

---
Production source changed: **NO** · ROM built: **NO** · Counter after: **399** · Special-surface involved:
**NO** · Build-0399 fix changed: **NO**.
