# Andy — Build 0143 Frontend Header Sprite Palette Audit (Outcome C)

**Date:** 2026-07-07
**Type:** Bounded palette audit on the accepted Build 0142. **No implementation** — the proven cause is a
broad sprite-palette-bank conflict, which the task's STOP rules forbid fixing here.
**Baseline (unchanged):** branch `rastan-direct-proposal`, commit `bbe4aa6e73cfcf08350ebc286245bad34c95d817`,
ROM `dist/rastan-direct/rastan_direct_video_test_build_0142.bin`, SHA256
`f4c4234910fd56c739f874ad2a176ec447949f4e492b6526d37064f7dd23f245`. No revert, no renderer change.

## Outcome
**Outcome C.** The frontend header colours are wrong because the arcade renders the whole frontend with a global
sprite colour bank (`sprite_ctrl = 0x60` → `sprite_colbank = 48`), so the header text uses **arcade palette bank
48** while the co-resident large item-icon sprites use **arcade palette bank 51**. The Build 0142 renderer's
palette-line formula `(color >> 4) & 3` hashes **both** bank 48 and bank 51 to the **same Genesis palette line 3**,
and the palette producer (`genesistan_palette_hook_3ba64`) loads only arcade banks 0–3 into Genesis lines 0–3 (so
line 3 holds arcade **bank 3**, purple). No single line-3 content change or single producer/renderer edit can make
the header (bank 48) correct without altering the bank-51 item icons on the same line. A correct fix requires a
consistent arcade-bank→Genesis-line assignment (renderer formula **and** producer bank selection, colbank-aware)
— the deferred OPEN-006 sprite-palette-bank architecture — which is broader than one bounded correction and would
alter other sprites. Per the task STOP conditions ("different sampled objects require unrelated fixes", "requires a
broad palette-system redesign", "preserve the Build 0142 renderer"), **Build 0143 was not implemented.**

## Method / authority
- **ARCADE MAME:** `mame rastan -rompath ./roms` (romset verified good), Lua dump of PC090OJ object RAM `0xD00000`,
  palette RAM `0x200000`, sprite-ctrl `0x380000`, PC090OJ ctrl `0xD01BFE`, + snapshot at the attract item screen.
  Authority source confirmed in the repo's reference MAME tree:
  `docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp:187` → `color = (data & 0x000f) | sprite_colbank`, and
  `rastan.cpp` `colpri_cb` → `sprite_colbank = (sprite_ctrl & 0xe0) >> 1`.
- **GENESIS MAME:** `mame genesis -cart <Build 0142>` Lua dump of `pc090oj_object_ram` (`0xFF69B0`),
  `pc090oj_sprite_ctrl_shadow` (`0xFF71D2`), staged SAT (`0xFF6188`), `record_to_slot` (`0xFF71F0`),
  `represented_records` (`0xFF72F0`), `staged_palette_words` (Genesis CRAM staging, `0xFF609E`), + snapshot.
- Evidence: `states/traces/build0143_palette/{arcade,genesis}/` (dumps, snapshots, `analyze` output).

## Producer address correlation (`address_map.json` / patch manifest / symbol.txt)
| producer | arcade PC | Genesis ROM offset | runtime Genesis PC | kind |
|---|---|---|---|---|
| sprite palette producer | `0x03BA64` | `0x03BC64` | `genesistan_palette_hook_3ba64` = `0x07186C` | `patched_site` (opcode_replace `4EB90007186C`) |

Genesis-only state (symbol.txt): `staged_palette_words` `0xFF609E` (4 lines × 16), `pc090oj_sprite_ctrl_shadow`
`0xFF71D2`. Renderer palette-line computation lives in `pc090oj_hooks.s` `.Lpc090oj_place_record_in_slot`
(`word2 = priority | palette | flips | tile-index`, palette = `(((word0 & 0x0f) | colbank) >> 4) & 3`,
`colbank = (sprite_ctrl_shadow & 0xE0) >> 1`).

## Representative sample (ARCADE MAME authority vs GENESIS MAME Build 0142)
Settled attract "item description" screen. Arcade `sprite_ctrl = 0x60` → `sprite_colbank = 48`; Genesis
`sprite_ctrl_shadow = 0x0060` → `colbank = 48` (identical).

| # | class | rec | arcade word0 | arcade sprite_ctrl | arcade bank = word0\|colbank | Genesis mirror word0 | Genesis sctrl_shadow | Genesis formula → line | Genesis CRAM line 3 = arcade bank | expected colour | actual colour |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1UP | 28 | `0x0000` | `0x60` | **48** | `0x0000` | `0x0060` | `(48>>4)&3 = 3` | bank **3** | `#f7f700` yellow | `#f75200`/wrong |
| 2 | HIGH SCORE | 34 | `0x0000` | `0x60` | **48** | `0x0000` | `0x0060` | `3` | bank **3** | `#f75200` orange | `#745774` purple |
| 3 | 2UP | 45 | `0x0000` | `0x60` | **48** | `0x0000` | `0x0060` | `3` | bank **3** | `#f75200` orange | `#745774` purple |
| 4 | score digit | 37 | `0x0000` | `0x60` | **48** | `0x0000` | `0x0060` | `3` | bank **3** | white | `#340034` dark |
| 5 | large item icon (control) | 64 | `0x0003` | `0x60` | **51** | `0x0003` | `0x0060` | `(51>>4)&3 = 3` | bank **3** | bank 51 flesh/red | `#…` bank 3 |

**Genesis CRAM (staged_palette_words) line 3** = `#916d91 #6d4891 #6d486d #48246d …` = arcade **bank 3** (purple),
converted 5→3 bit. **Arcade bank 48** = `… #f65200(orange) #f6f600(yellow) #f6f6f6(white) …` (entries 768–783).
**Arcade bank 51** = flesh/red tones (entries 816–831). Bank 48 ≠ bank 51 ≠ bank 3.

## Exact first divergence
- **A (mirror word0):** Genesis `0x0000` == arcade `0x0000`. **No divergence.**
- **B (global sprite palette-bank control):** Genesis `sprite_ctrl_shadow = 0x60` == arcade `sprite_ctrl = 0x60`;
  both compute `colbank = 48`; both compute `arcade color = word0 | colbank = 48`. **No divergence** — the control
  is correctly captured and translated.
- **C (colour-bank → Genesis palette conversion):** the renderer's `(color >> 4) & 3` maps arcade colour 48 → line 3
  and colour 51 → line 3 (banks 48–63 all alias to line 3). It is also **inconsistent** with the producer, which
  loads arcade banks 0–3 → lines 0–3 by bank index (bits 0–1), not bits 4–5 — so even a gameplay bank-3 sprite would
  mismap (`(3>>4)&3 = line 0` vs bank 3 staged in line 3). **Divergent + inconsistent.**
- **D (CRAM contents of the selected line):** Genesis line 3 holds arcade **bank 3**, but the header needs arcade
  **bank 48**. **Divergent.**

**First divergence = E (both C and D).** All four sampled header records share the *same* divergence uniformly
(every header sprite is arcade bank 48 → line 3 = bank 3), so one correction would explain all header records — but
it is **not boundable**: the large item-icon control sample (arcade bank 51) resolves to the *same* Genesis line 3,
so any change that makes the header (bank 48) correct on line 3 changes the item icons, and separating them requires
changing the renderer's line-selection formula and the producer's bank-loading together (colbank-aware), across all
screens.

## Exact palette correction that would be required (NOT implemented)
A consistent arcade-bank → Genesis-line map used by *both* sides:
1. Renderer: replace `(color >> 4) & 3` with a line selector that separates the concurrently-used banks (e.g.
   `color & 3` distinguishes 48→0 and 51→3), and
2. Producer: load the arcade banks that the active global `sprite_colbank` selects (frontend: banks 48–51) into the
   matching Genesis lines, instead of the fixed banks 0–3.

Because the global `sprite_colbank` changes per screen (frontend = 48; gameplay/title differ), the producer must
load banks dynamically per colbank, and the renderer formula change affects every screen — this is the OPEN-006
sprite-palette-bank architecture, not a single bounded correction, and it risks regressing title/gameplay sprites.
Therefore it is out of scope for this bounded task and is **deferred, not applied.**

## Files changed
**None.** Audit only; no source, tool, ROM, or build change. Build 0142 remains the head of `rastan-direct-proposal`.

## ROM
Unchanged Build 0142: `dist/rastan-direct/rastan_direct_video_test_build_0142.bin`, size 1,563,844 B,
SHA256 `f4c4234910fd56c739f874ad2a176ec447949f4e492b6526d37064f7dd23f245`. No Build 0143 emitted.

## Runtime validation
N/A (no fix implemented). The audit runtime evidence (arcade + Genesis MAME dumps and snapshots) is in
`states/traces/build0143_palette/`. Genesis structural invariants and the black-bar removal from Build 0142 are
unaffected (no change made).

## Commit SHA
None. No commit; working tree source unchanged (`bbe4aa6` remains head).

## Explicitly deferred non-palette defects (out of scope, not investigated/fixed)
Missing `UP` of `1UP`/`2UP`, missing `HIGH SCORE` label, score readout values (`00000`), text content differences
(MANTLE/ARMATURE vs AXE/HAMMER — different item table), sprite positions, missing/extra sprites, left purple bar,
item-screen completeness, gameplay sprites, PC080SN, and the broad sprite-palette-bank mapping (OPEN-006) itself.

## Open/Closed Issues Impact
- **OPEN-006 (sprite/high-bank palette mapping deferred):** this audit **proves** the frontend-header manifestation:
  header sprites use arcade bank 48 (global `sprite_colbank`), item icons use bank 51, both alias to Genesis line 3
  via `(color>>4)&3`, and the producer loads banks 0–3 not 48/51. Not closed; the concrete conflict is now
  documented for the eventual bank-mapping build.
- **OPEN-024 (PC090OJ sprite subsystem incomplete):** unchanged; header palette is a colour defect on top of the
  correct Build 0142 geometry/identity. Not closed.
- No issue closed. No new issue opened (the conflict is a facet of OPEN-006).
