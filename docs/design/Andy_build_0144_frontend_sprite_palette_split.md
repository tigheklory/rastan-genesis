# Andy — Build 0144 Frontend Sprite Palette Split (Outcome B, retained)

**Agent:** Andy, temporarily filling Cody's implementation/runtime-evidence role (exception ends Thursday evening).
**Type:** Implementation + verification. One production change, one ROM (Build 0144), runtime evidence.
**Baseline branch/commit:** `rastan-direct-proposal` @ `790e7147a83dcf6b1802cd96bee3b626933b5191`.
**Build 0142 SHA confirmation:** `dist/rastan-direct/rastan_direct_video_test_build_0142.bin` =
`f4c4234910fd56c739f874ad2a176ec447949f4e492b6526d37064f7dd23f245` (accepted baseline, unchanged).

## Outcome
**Outcome B — SAT selector mapping correct; bank-51 palette line 3 is zero.** The SAT selector split works exactly
(bank 48 → Genesis line 2, bank 51 → Genesis line 3, both simultaneously present). The palette staging delivers the
correct **bank-48** colors into staged line 2 (header sprites now render arcade-correct: 1UP yellow, HI SCORE
orange), but staged line 3 is **all zero** on every screen because **arcade palette bank 51 is not carried through
`0x03BA64`** — it reaches Genesis staging via a different producer (`0x059AD4`), which this task explicitly does not
modify. Per the Outcome-B rule, the change is retained: the selector separation and the bank-48 line-2 delivery are a
genuine, architecture-compliant improvement to the frontend header on all five screens.

## Build 0144 ROM
- **Path:** `dist/rastan-direct/rastan_direct_video_test_build_0144.bin`
- **SHA256:** `ba1ed586daa587cf0f6d2ffe851c0771b9d4ad42fb94677af42cdeed3d9d91ae`
- **Size:** 1,563,888 B (Build 0142 = 1,563,844; +44 B from the two edits). GATE_PASS, boot guard PASS, 30 s trace clean.
- Accepted Build 0142 ROM not overwritten.

## Files changed
- Production source: `apps/rastan-direct/src/pc090oj_hooks.s` (SAT selector), `apps/rastan-direct/src/palette_hooks.s`
  (palette determiner `0x03BA64`).
- Paired canonical bookkeeping (value-only, authorized): `CANONICAL_TOTAL_GENESIS_BYTES_COVERED 0x17DCC4 → 0x17DCF0`
  in `tools/translation/postpatch_startup_rom.py` + `verify_canonical_rom.py`; `opcode_replace` unchanged (133).
- Generated: `out/*.o/.elf/symbol.txt`, `build/genesis_postpatch.disasm.txt`, `build/rom_inventory.json`, numbered ROM,
  auto trace — all direct consequences of the two edits + Build 0144.

## Implementation symbols and addresses
- **SAT selector** — `.Lpc090oj_place_record_in_slot` in `pc090oj_hooks.s` (the point that stages `staged_sprite_sat`
  word2 palette bits). No post-staging SAT patching; no direct committed-SAT write.
- **Palette determiner** — `genesistan_palette_hook_3ba64` (`arcade_pc 0x03BA64` / `genesis_rom_offset 0x03BC64` /
  `runtime_genesis_pc 0x07186C`), the producer that determines Genesis CRAM lines 2/3, via the existing
  `staged_palette_words (0xFF609E) → palette_dirty → vdp_commit_palette (0x0701D4) → CRAM` path.

## Old vs new selector behavior
- **Old (Build 0142):** `palette_line = (effective_bank >> 4) & 3` — banks 0x30 and 0x33 both → line 3.
- **New (Build 0144):** `if effective_bank==0x30 → line 2; elif ==0x33 → line 3; else (effective_bank>>4)&3`.
  `effective_bank = (word0 & 0x0F) | sprite_colbank`.

## Old vs new palette determiner
- **Old:** `bank = (dest-0x200000)>>5; if bank>=4 skip; line = bank` (banks 0..3 → lines 0..3).
- **New:** banks 0,1 → lines 0,1 (plane palettes, kept); **bank 48 → line 2**; **bank 51 → line 3**; every other bank
  skipped.

## Arcade palette source addresses
- **Bank 48:** arcade palette RAM `0x00200600` (bank 48 × 0x20). Carried through `0x03BA64` at boot
  (`a0=0x00200600`, `sprite_ctrl_shadow=0x0000`). **Delivered to staged line 2.**
- **Bank 51:** arcade palette RAM `0x00200660` (bank 51 × 0x20). **NOT carried through `0x03BA64`** — `0x03BA64`'s
  loops cover `0x200000..0x20061F` (banks 0..48) only. Bank 51 reaches Genesis staging via `genesistan_palette_hook_59ad4`
  (`arcade_pc 0x059AD4`, `d0=0x33`), which this task does not modify. **Staged line 3 stays zero.**

## Staged palette contents (raw Genesis CRAM words, identical on all 5 screens)
- **Staged line 2 (entries 32-47):** `0000 0000 0008 004e 008e 00ee 08ee 0eee 0a00 0e40 0e80 0ec0 0eea 0000 0000 0000`
  → RGB `. . #910000 #ff4800 #ff9100 #ffff00 #ffff91 #ffffff #0000b6 #0048ff #0091ff #00daff #b6ffff . . .` = arcade
  bank 48 (red/orange/yellow/white/blue). **Nonzero and stable across all five screens.**
- **Staged line 3 (entries 48-63):** `0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000`
  = **all zero on all five screens.**

## Committed CRAM contents
`vdp_commit_palette` DMAs all 64 staged words to CRAM (CPU→VDP_DATA, `move.l #0xC0000000` then 64× `move.w`), so
**committed CRAM = `staged_palette_words` verbatim**. The MAME `:gen_vdp:gfx_palette` `pen_color` interface reads all
zero **even for line 0** (the visibly-rendering plane palette), so it does **not** expose live VDP CRAM and is not
used as committed-CRAM evidence (distinct from the raw staged words above). Committed CRAM is therefore established
from the raw staged buffer plus the visual:
- **Committed line 2 = staged line 2 = bank 48** — confirmed by the rendered header colours (below).
- **Committed line 3 = staged line 3 = zero** — confirmed by the black bank-51 sprites (below).

## Per-screen sprite-bank and selector census (Build 0144)
| Screen | state | bank 48 → line | bank 51 → line |
|---|---|---|---|
| title | 0/1/0 | line 2 (23 records) | — |
| throne/story | 0/1/2 | line 2 (23) | — |
| high-score | 2/0/0 | line 2 (23) | — |
| item-desc | 2/2/6 | line 2 (18, records 28-45) | line 3 (4, records 64-67) |
| coined-up | 1/1/0 | line 2 (19) | — |

- No represented bank-48 sprite remains on line 3; no represented bank-51 sprite uses line 2. **Both groups
  simultaneously present on the item screen (bank 48 → line 2, bank 51 → line 3).**
- Represented set and `record_to_slot` **byte-identical** to Build 0142 (22/22 on item). SAT non-palette fields
  (Y, X, tile index, link, size, priority, flip) **unchanged — only palette bits 13-14 differ** (0 non-palette diffs
  across all 80 slots).

## Screenshots reviewed
`states/traces/build_0144_frontend_sprite_palette_split/snaps/` — title, story, high-score, item, coined-up.
- **Title:** header `1UP` = yellow, `HI SCORE` = orange (Build 0142 was orange/purple). Matches arcade intent
  (`1UP #f7f700`, `HIGH SCORE #f75200`).
- **Item:** header renders with bank-48 colours (line 2); persistent header consistent with the other screens.

## Visible result
- **Bank 48 (persistent/header sprites, all 5 screens):** now render with arcade-correct bank-48 colours (yellow 1UP,
  orange HI SCORE, white score digits) — **fixed** from the Build 0142 purple. Planes visually unchanged (plane
  selection untouched; lines 0/1 unchanged).
- **Bank 51 (four item-description sprites, records 64-67):** select line 3, but line 3 CRAM = zero, so they render
  **black/invisible** (Build 0142 rendered them purple via the shared line 3 = bank 3). This is the Outcome-B gap:
  the correct source data for bank 51 is not delivered through `0x03BA64`.

## Outcome B detail
```
bank 48:
  source address:            arcade palette RAM 0x00200600 (via 0x03BA64 boot load)
  SAT selector result:       Genesis line 2 (correct)
  staged line-2 contents:    0000 0000 0008 004e 008e 00ee 08ee 0eee 0a00 0e40 0e80 0ec0 0eea 0000 0000 0000 (bank 48)
  committed CRAM line 2:     = staged (DMA'd verbatim); confirmed by rendered header colours
  visible result:            CORRECT — 1UP yellow, HI SCORE orange, white digits (arcade-consistent), all 5 screens

bank 51:
  source address:            arcade palette RAM 0x00200660 (reaches staging via 0x059AD4 d0=0x33, NOT 0x03BA64)
  SAT selector result:       Genesis line 3 (correct)
  staged line-3 contents:    all zero (bank 51 not carried by 0x03BA64)
  committed CRAM line 3:     zero
  visible result:            INCORRECT — four item sprites (records 64-67) render black/invisible
```
Per the Outcome-B rule, the later arcade palette producer (`0x059AD4`) was **not** investigated or modified, and no
refresh path was added. The selector separation itself is useful and architecture-compliant (it fixes the header on
all five screens and does not touch geometry, identity, planes, or the commit path), so the production change is
**retained**, not reverted. The bank-51 line-3 delivery is a bounded follow-up: route arcade bank 51 into staged
line 3 through its actual producer (`0x059AD4`) in a future task.

## Address-map validation / integrity
`opcode_replace = 133` (unchanged); `total_genesis_bytes_covered = 1563888 = 0x17DCF0`; `segment_coverage.gaps = []`,
`overlaps = []`. No patched-site/wrapper byte change.

## Unexpected-delta assessment
None. The ROM delta is confined to the two edited helper bodies plus their direct relocation/branch-displacement
consequences (one short→word branch widening in `0x03BA64`), the paired canonical coverage constant, and normal
generated metadata for Build 0144. No unrelated production source changed.

## Architecture-compliance statement
CONFIRMED. Both edits are in-place arithmetic inside existing arcade-called helpers (`place_record_in_slot`,
`genesistan_palette_hook_3ba64`) that return via RTS. No Genesis-owned loop, lifecycle, screen-state machine, second
VBlank, boot re-entry, direct/unscheduled CRAM write, second palette path, restoration mechanism, duplicated palette
state, or diagnostic instrumentation was added. All VDP output continues through `staged_palette_words`/`palette_dirty`
/`vdp_commit_palette` and the single arcade-owned VBlank.

## Open/Closed Issues Impact
- **OPEN-006 (sprite/high-bank palette mapping deferred):** advanced, not closed. The frontend sprite-palette selector
  split is implemented and validated: bank 48 → Genesis line 2 renders arcade-correct header colours on all five
  frontend screens; bank 51 → Genesis line 3 has correct selectors but zero palette data because bank 51 is delivered
  via `0x059AD4`, not the `0x03BA64` determiner modified here. Remaining OPEN-006 work: route arcade bank 51 into
  staged line 3 through `0x059AD4`.
- **OPEN-024 / OPEN-001:** context only, unchanged, not closed.
- No issue closed; no duplicate opened.

## KNOWN_FINDINGS impact
Propose (pending curation, not auto-added): a new entry — the frontend sprite palette split (bank 48 → line 2 via the
SAT selector + `0x03BA64` determiner) renders correct header colours, but arcade bank 51 is not carried by `0x03BA64`
(covers banks 0..48 at `0x200000..0x20061F`) and instead reaches Genesis staging through `0x059AD4` (`d0=0x33`), so a
single-determiner remap leaves Genesis line 3 zero. Confidence CONFIRMED (native producer evidence + staged/SAT dumps
+ visual), Applicability BUILD_SPECIFIC (Build 0144 frontend), Rediscovery Hazard HIGH. (Extends the pending KF-039/
KF-040 proposals.)

## Explicit statements
The production change was **retained** (clean Outcome B). No unrelated graphics/gameplay/sprite/tilemap/input/crash
defect was investigated. The later palette producer (`0x059AD4`) was not modified.
