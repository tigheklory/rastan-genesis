# Andy — Frontend CRAM and Palette-Line Ownership (Verification, Outcome A)

**Agent:** Andy, temporarily filling Cody's verification/runtime-evidence role (exception ends Thursday evening).
**Type:** Verification / evidence. **No ROM, no build number, no production change.**
**Runtime:** GENESIS MAME with accepted Build 0142 (`dist/rastan-direct/rastan_direct_video_test_build_0142.bin`,
SHA256 `f4c4234910fd56c739f874ad2a176ec447949f4e492b6526d37064f7dd23f245`). Branch `rastan-direct-proposal`, head `cc566e6`.
**Evidence dir:** `states/traces/frontend_cram_palette_line_ownership/`.

## Outcome
**Outcome A — evidence complete.** All required ownership evidence for Genesis CRAM lines 2 and 3 was captured across
all five frontend screens. Line 2 has **zero selectors of any kind** (planes, sprites, Window) and is all-zero in
CRAM; line 3 is **sprite-exclusive** (no plane consumer). The line-3 concurrency result is a **conditional conflict**
reported for Claude's design decision (not decided here).

## Phase 0 baseline statement
```
Relevant priors from KNOWN_FINDINGS:
  - KF-010 (BG→Plane B, FG→Plane A) — STRONG; used to map staged_bg_buffer→Plane B, staged_fg_buffer→Plane A.
  - KF-011 (arcade Level-5 VBlank owns progression) — STRONG; respected (evidence-only, no control-flow change).
  - KF-032 (raw PC080SN/PC090OJ writes must route through Genesis staging) — CONFIRMED; relevant to selector-writer ownership.
  - KF-026 (PC090OJ runtime write surface not fully statically enumerable) — STRONG; context (sprite selectors via SAT).
  - KF-021 (sprite early-return + SAT-DMA suppression masks sprites) — STRONG/CONTAMINATED; caution: no such suppression present.
Rediscovery Hazard HIGH findings touched: KF-011, KF-032, KF-021 — all respected (no change introduced).
Deferred-appendix relevant: DEF-004 (palette precomputed offline / direct CRAM DMA) — the live path here is
  staged_palette_words → palette_dirty → vdp_commit_palette; not treated as canonical prior.
Task classification: NEW — investigates CRAM line-2/3 ownership (writers + selectors), not currently indexed in a KF.
Open/Closed issues touched: OPEN-006 (primary), OPEN-024 (context), OPEN-001 (context), OPEN-023 (Window — context).
Contradiction of CONFIRMED or STRONG finding detected during Phase 0 read: NONE.
```

## Method / addresses
GENESIS MAME (Build 0142). Genesis-only WRAM (STATIC SOURCE `apps/rastan-direct/out/symbol.txt`): staged CRAM source
`staged_palette_words` `WRAM 0xFF609E` (64 words); Plane B staging `staged_bg_buffer` `WRAM 0xFF409E`; Plane A staging
`staged_fg_buffer` `WRAM 0xFF509E`; `staged_sprite_sat` `WRAM 0xFF6188`; `pc090oj_object_ram` `WRAM 0xFF69B0`;
`record_to_slot` `WRAM 0xFF71F0`; `represented_records` `WRAM 0xFF72F0`; `pc090oj_sprite_ctrl_shadow` `WRAM 0xFF71D2`.
Actual VDP CRAM read via `:gen_vdp:gfx_palette` `pen_color` (corroboration). Coin insert via the input shim (P1 A =
coin, `tilemap_hooks.s:2052`). Genesis nametable/SAT palette-line = word bits 13-14. Effective arcade bank =
`(word0 & 0x0F) | ((pc090oj_sprite_ctrl_shadow & 0xE0) >> 1)`. CRAM byte offsets: line0 `0x00..0x1F`, line1
`0x20..0x3F`, **line2 `0x40..0x5F`**, **line3 `0x60..0x7F`**.

Five frontend screens (GENESIS MAME + USER-VISUAL snapshots): title (`0/1/0`), throne/story (`0/1/2`), high-score
(`2/0/0`), item-description (`2/2/6`), coined-up (`1/1/0`, after P1-A coin). All at `sprite_ctrl_shadow = 0x0060` →
sprite_colbank 48.

## 1a. CRAM-writer ownership, lines 2 and 3 — CONFIRMED (no exception)
Native watchpoint on staged CRAM line 2 (`0xFF60DE..0xFF60FD`) and line 3 (`0xFF60FE..0xFF611D`) across the frontend
found exactly two writer PCs, both inside expected ownership:
- `runtime_genesis_pc 0x000002A4` = `_bootstrap_clear_staging` (+0x5A) — one-time cold-boot BSS zero-clear (writes 0).
- `runtime_genesis_pc 0x000718DA` = `genesistan_palette_hook_3ba64` (+0x6E) — the known palette path
  (`staged_palette_words → palette_dirty → vdp_commit_palette → CRAM`).

**No writer targets CRAM line 2 or line 3 outside that path.** Line 2's contents are arcade **bank 2** (which is all
zero in the arcade palette RAM), written by `0x03BA64` at boot; line 3's contents are arcade **bank 3**, written by
`0x03BA64` at boot (`sprite_ctrl_shadow=0x0000`, colbank 0). Neither is rewritten during the frontend.

## 1b. Palette-selector-writer ownership, lines 2 and 3 — CONFIRMED (no exception)
- **Planes (PC080SN):** `staged_bg_buffer`/`staged_fg_buffer` select only palette lines 0 and 1 on all five screens
  (full 2048-word scan; zero line-2 and zero line-3 plane cells). Expected owner; no line-2/3 plane selector exists.
- **Sprites (PC090OJ):** `staged_sprite_sat` word2 bits 13-14; produced by the Build 0142 renderer
  (`.Lpc090oj_place_record_in_slot`). Selects **line 3** (never line 2). Expected owner.
- **Window:** VDP window registers 17/18 = 0 at boot (`boot` VDP init); the VBlank commit sequence
  (`_vblank_service`) commits tiles/BG-strips/FG-strips/sprites/palette/scroll only — **no Window plane commit**.
  Window contributes no selectors.

No selector writer to lines 2 or 3 exists outside the PC080SN / PC090OJ / (inert) Window owners.

## 2. Line-2 selector counts per layer, per screen — NO SELECTORS
| Screen | Plane A | Plane B | Window | SAT |
|---|---:|---:|---:|---:|
| title (0/1/0) | 0 | 0 | 0 (inert) | 0 |
| story (0/1/2) | 0 | 0 | 0 | 0 |
| high-score (2/0/0) | 0 | 0 | 0 | 0 |
| item-desc (2/2/6) | 0 | 0 | 0 | 0 |
| coined-up (1/1/0) | 0 | 0 | 0 | 0 |

**Line 2 has zero selectors on every layer of every frontend screen**, and CRAM line 2 = all zero (staged and VDP
`pen_color`). No pixel-index audit is needed because there is no line-2 selector to audit.

## 5-continued. What a nonzero bank in line 2 would make visible
**Nothing.** With zero selectors (no nametable cell, no sprite) choosing line 2 on any of the five screens, replacing
the all-zero line-2 CRAM with a nonzero bank would not reveal or recolor any visible plane or sprite. The central risk
("an all-zero line could still be selected and render black") is directly disproven for line 2: no selector uses it.

## 3. Line-3 consumers per layer, per screen
| Screen | Plane A | Plane B | Window | SAT (records → effective banks) |
|---|---:|---:|---:|---|
| title | 0 | 0 | 0 | 23 sprites → bank 48 |
| story | 0 | 0 | 0 | 23 → bank 48 |
| high-score | 0 | 0 | 0 | 23 → bank 48 |
| item-desc | 0 | 0 | 0 | 22 → bank 48 ×18 (records 28-45), **bank 51 ×4 (records 64-67)** |
| coined-up | 0 | 0 | 0 | 19 → bank 48 |

**Line 3 is sprite-exclusive on every screen — no Plane A/B/Window consumer.** Under the current Build 0142 renderer
formula `(effective_bank >> 4) & 3`, every frontend sprite (banks 48 and 51 both) hashes to line 3, so on the
item screen the bank-48 header sprites and the bank-51 item-icon sprites co-reside on line 3.

## 7. Can bank 51 occupy line 3 without a simultaneous conflict?
- **Plane conflict: NONE** — no plane (A/B/Window) consumes line 3 on any screen.
- **Unrelated-sprite conflict: YES under the current formula** — the bank-48 header sprites also select line 3 (item
  screen), so writing bank 51 into line 3's CRAM would recolor those bank-48 header sprites.
- The only other sprite bank co-resident on line 3 is bank 48; there are no third sprite banks (see census). If the
  header bank (48) is routed off line 3 (e.g. to the free line 2 — which requires the renderer formula change the
  candidate presupposes), line 3 becomes bank-51-exclusive and the conflict dissolves. **This is a design decision;
  it is not decided here.**

## 4. / 8. Line-3 replacement and restoration sequence — NOT PRESENT / NOT REQUIRED
CRAM line 3 is **byte-identical across all five frontend screens** (single distinct value:
`0000 0868 0846 0646 0624 0424 0402 0202 0202 028c 044c 0226 0004 0002 0222 0424` = Genesis conversion of arcade
bank 3). It is written once, at boot, by `arcade_pc 0x03BA64` / `genesis_rom_offset 0x03BC64` /
`runtime_genesis_pc 0x07186C` (`genesistan_palette_hook_3ba64`) with `sprite_ctrl_shadow=0x0000` (derived
sprite_colbank 0), `palette_dirty` asserted, and is **never rewritten during the frontend**. No existing producer
restores or replaces line 3 across the frontend cycle; **no restoration mechanism exists, and none is required**
(the line is static). Implication for the candidate (evidence only, not a decision): a bank written into line 3 would
persist unchanged across all five frontend screens.

## 5. CRAM dumps
Per-screen raw + RGB evidence: `states/traces/frontend_cram_palette_line_ownership/cram_<screen>.txt` (all 64 words per
line, RGB, and the arcade-bank source per line = `line N ← arcade bank N` via the `0x03BA64` boot load). Full binary
captures (`<screen>.bin`: state, sctrl, CRAM, SAT, mirror, record_to_slot, represented, staged BG, staged FG) alongside.
- **Line 2 (0x40..0x5F), all five screens:** `0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000` — **all zero: YES**.
- **Line 3 (0x60..0x7F), all five screens:** `0000 0868 0846 0646 0624 0424 0402 0202 0202 028c 044c 0226 0004 0002 0222 0424` (identical/static).

## 6. Effective frontend sprite-bank census
| Screen | Effective bank | Record IDs | Current Genesis line |
|---|---:|---|---:|
| title | 48 | 23 represented (word0 nib 0) | 3 |
| story | 48 | 23 | 3 |
| high-score | 48 | 23 | 3 |
| item-desc | 48 | records 28-45 (18) | 3 |
| item-desc | 51 | records 64-67 (4) | 3 |
| coined-up | 48 | 19 | 3 |

**Banks 48 and 51 are the only high arcade sprite banks needing representation in the scoped frontend: CONFIRMED.**

## Ownership-result summary (per Outcome A)
- CRAM-writer ownership lines 2/3: **CONFIRMED** (boot zero-clear + `0x03BA64` palette path only; no exception).
- Palette-selector-writer ownership lines 2/3: **CONFIRMED** (planes lines 0/1 only; sprites line 3 via PC090OJ;
  Window inert; no exception).
- Line-2 availability: **NO SELECTORS** (free/unowned; nonzero bank would reveal/recolor nothing).
- Line-3 concurrency: **CONFLICT under the current formula** (bank 48 + bank 51 co-reside on line 3; no plane
  conflict); resolvable only by routing the header bank off line 3 (design decision).
- Line-3 restoration: **NOT PRESENT / NOT REQUIRED** (line 3 static across all five screens).
- Sprite-bank census complete: **YES** (banks 48, 51).

## Files changed
Documentation and evidence only: this report; `AGENTS_LOG.md`; `OPEN_ISSUES.md`; evidence under
`states/traces/frontend_cram_palette_line_ownership/`. **No production source, spec, tool, Makefile, generated asset,
ROM, or build number.** Build produced: **NO**. ROM produced: **NO**.

## Boundaries honored
No design decision or production change was made; assignment choice is left to Claude. Gameplay (black screen /
palette) and all listed non-palette defects were not investigated. Architecture compliance: **CONFIRMED** — evidence
collected only via debugger breakpoints/watchpoints/memory dumps and existing inputs; no instrumentation, no
Genesis-owned loop/lifecycle, no second VBlank, no boot re-entry, no source change.

## Open/Closed Issues Impact
- **OPEN-006 (sprite/high-bank palette mapping deferred):** newly proven ownership facts recorded — Genesis CRAM line 2
  is unowned (zero selectors, all-zero CRAM) across all five frontend screens; line 3 is sprite-exclusive (no plane
  consumer) and currently shared by banks 48+51; CRAM line N currently mirrors arcade bank N via the `0x03BA64` boot
  load; line 3 is static across the frontend with no restoration producer. Not closed.
- **OPEN-024 / OPEN-001:** context only; unchanged, not closed.
- **OPEN-023 (Window layer unimplemented):** corroborated — Window is inert (regs 17/18 = 0, no window commit); no
  Window selectors. Not closed, not modified.
- No issue closed; no duplicate opened.

## KNOWN_FINDINGS impact — Option B (proposed new entry, pending curation)
```
KF-040 (proposed) — Frontend Genesis CRAM line 2 is unowned; line 3 is sprite-exclusive and static
Status: ACTIVE | Confidence: CONFIRMED (native watchpoint + staged/VDP CRAM dumps + full nametable/SAT scans, 5 screens)
Applicability: BUILD_SPECIFIC (Build 0142 frontend: title/story/high-score/item/coined-up) | Rediscovery Hazard: HIGH
Addresses: staged_palette_words WRAM 0xFF609E (CRAM line2 0x40..0x5F, line3 0x60..0x7F); staged_bg_buffer 0xFF409E; staged_fg_buffer 0xFF509E; staged_sprite_sat 0xFF6188; genesistan_palette_hook_3ba64 runtime 0x07186C (arcade_pc 0x03BA64); _bootstrap_clear_staging runtime 0x00024A
Finding: Across the five frontend screens, no Plane A, Plane B, Window, or SAT entry selects Genesis palette line 2, and CRAM line 2 is all zero (staged + VDP pen_color). Line 3 is selected only by PC090OJ sprites (no plane consumer); CRAM line 3 is byte-identical across all five screens (arcade bank 3), written once at boot by 0x03BA64 (sprite_colbank 0) and never rewritten in the frontend. CRAM lines 2/3 are written only by the boot BSS zero-clear (0x0002A4) and the 0x03BA64 palette path (0x0718DA). Effective frontend sprite banks are 48 (all screens) and 51 (item screen); the Build 0142 renderer (bank>>4)&3 hashes both to line 3.
Use as prior: For a frontend sprite-palette-line remap, line 2 is a free line (no selector, no plane) and line 3 is sprite-exclusive; but a nonzero bank in line 3 recolors every line-3 sprite (all frontend sprites under the current formula), and CRAM line N currently mirrors arcade bank N via the single 0x03BA64 boot load with no per-screen restoration.
Related Issues: OPEN-006, OPEN-024, OPEN-023
```
(Proposal only; the earlier KF-039 proposal from the Build 0143 STOP is also pending curation.)

## Explicit statements
No design decision and no production change were made. Gameplay and non-palette defects were not investigated.
