# Andy — Build 0147: PC090OJ Viewport Clipping + Configurable Coordinate Translation

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `64080ce` (Build 0146 accepted). Build 0146 ROM
`3edcf345d1c6e547b993f72b29ab9d80f7fa58823ad992de962391a5ce8a416b` — not overwritten.
**Evidence dir:** `states/traces/build_0147_pc090oj_viewport_clip/`.

## Outcome
**Implemented.** A general PC090OJ coordinate + opaque-geometry viewport clip in `.Lpc090oj_decode_record`. A mirror
record now receives Genesis SAT representation only when at least one opaque pixel of its current (post-flip) pattern
survives the effective viewport. Fully-clipped records stay in the mirror but get no representation, SAT slot, link
entry, tile work, or scanline capacity. On the title this removes the twelve leading-zero score sprites the arcade
hides in its 8-px top margin, restoring the complete `2UP` label. The mirror is byte-identical to Build 0146.

## Proven root cause (settled, Build 0147 analysis)
Arcade PC090OJ renders `screen_y = raw_y` with an 8-px top visible-area margin (`rastan.cpp set_visarea 8..247`,
`m_y_offset = 0`). Leading-zero digits (code 0x2A, opaque rows 0–6) at raw Y=0 land in the clipped margin; label
glyphs (opaque rows 8–14) survive. The Genesis renderer previously mapped raw Y=0 → screen Y=0 with no top clip, so
the zeros rendered and consumed scanline-0 sprite budget, dropping the last chain sprite (`UP`).

## Design
### Where the visibility gate lives
Entirely inside `.Lpc090oj_decode_record` (the single coordinate source of truth — `place_record_in_slot` calls it
for the SAT fields too). Returning "not drawable" already routes a record through the existing
`sync_record_from_mirror` → `deactivate_record` / never-`activate` paths, so a fully-clipped record cleanly loses its
slot/link/worklist and a record that later becomes visible is re-activated automatically. No new renderer, lifecycle,
commit path, or visibility system was added.

### Opaque-pattern metadata (generated before SAT allocation)
`tools/translation/build_pc090oj_opaque_bbox.py` scans the raw cell region `build/regions/pc090oj.bin` (same code
index as the runtime `code` field and the existing blank bitset) and emits a per-code opaque bounding box —
`build/pc090oj_opaque_bbox.bin`, 4096 codes × 4 bytes `{min_row, max_row, min_col, max_col}` in unflipped 16×16 cell
space. It is `.incbin`-linked as `pc090oj_opaque_bbox` (`pc090oj_assets.s`), exactly like `pc090oj_blank_code_bitset`,
and built by a Makefile rule. This is stable asset-derived data available before SAT allocation — visibility is not
coupled to transient slot ownership. Fully-blank cells (already rejected by `pc090oj_blank_code_bitset` before the box
is read) are emitted as `0,0,0,0`.

### Visibility gate (per record, in decode)
1. Sign-extend Y/X; apply the arcade flip inversion (unchanged, now named).
2. Apply the arcade→Genesis viewport origin: `screen = arcade_screen + PC090OJ_TO_GENESIS_{X,Y}_OFFSET`.
3. Look up the code's opaque box; mirror the row span on vertical flip (`MAX_ROW - box`), the col span on horizontal
   flip (`MAX_COL - box`), using the **post-flip** word0 flip bits (bit 15 / bit 14) so the test matches the rendered
   orientation.
4. Drawable iff the opaque screen span intersects the effective clip rectangle on **both** axes:
   `opaque_top < BOTTOM && opaque_bottom >= TOP && opaque_left < RIGHT && opaque_right >= LEFT`. Otherwise not drawable.

A partially-clipped sprite (opaque box straddling an edge) still intersects and remains representable; the VDP clips
the off-screen rows/cols at draw time as before.

### Flip handling
Vertical flip mirrors the opaque **row** span (`[MAX_ROW-max_row, MAX_ROW-min_row]`); horizontal flip mirrors the
opaque **col** span. The flip bits read are the post-inversion word0 bits actually written to the SAT, so the
visibility test and the rendered sprite always agree.

## Initial offset selection (evidence)
`vdp_comm.s` defines `VDP_DISPLAY_ORIGIN_Y_BIAS = 8` / `_X_BIAS = 16` and `vdp_commit_scroll` applies **+8** to the
background vertical scroll (and −16 to X), so the background maps the arcade visible-area origin (raster Y=8) to
Genesis display line 0. Sprites previously used offset 0 (screen Y = raw Y), i.e. **8 px below** the background.
Selected initial values:
- **`PC090OJ_TO_GENESIS_Y_OFFSET = -8` ( = `-VDP_DISPLAY_ORIGIN_Y_BIAS`).** This aligns sprites to the background's
  established origin (arcade raster Y=8 → Genesis line 0) **and** places the arcade top margin above the Genesis
  viewport, where the leading-zero records clip out naturally. It prioritises **exact arcade viewport alignment**,
  which coincides with the background's mapping — so surviving sprites move up 8 px only as a direct result of the
  documented transform, and that movement corrects a latent sprite/background offset rather than introducing one.
- **`PC090OJ_TO_GENESIS_X_OFFSET = 0`.** The frontend X already matches the arcade layout; kept configurable and named
  so X can be tuned later without touching clip logic. (The background's −16 X origin bias is a scroll-register
  adjustment; the sprite SAT X bias path is separate and currently correct — no X defect is present.)
Both are named `.equ` and adjustable for later emulator / gameplay / real-CRT tuning without rewriting clip logic.
Remaining validation need: full in-game sprite/background alignment across scrolling gameplay is not yet testable in
attract mode; the value is the best-supported provisional choice and is configurable.

## Named coordinate/clip `.equ` constants (audit)
Added in `pc090oj_hooks.s`: `PC090OJ_PATTERN_WIDTH(16)`, `PC090OJ_PATTERN_HEIGHT(16)`, `PC090OJ_PATTERN_MAX_ROW(15)`,
`PC090OJ_PATTERN_MAX_COL(15)`, `PC090OJ_FLIP_X_TERM(304)`, `PC090OJ_FLIP_Y_TERM(240)`,
`PC090OJ_TO_GENESIS_Y_OFFSET(-8)`, `PC090OJ_TO_GENESIS_X_OFFSET(0)`, `GENESIS_VIEWPORT_LEFT(0)`,
`GENESIS_VIEWPORT_RIGHT(320)`, `GENESIS_VIEWPORT_TOP(0)`, `GENESIS_VIEWPORT_BOTTOM(224)`, `PC090OJ_SAT_Y_BIAS(0x80)`,
`PC090OJ_SAT_X_BIAS(0x80)`. Reused: `SPRITE_TILE_BASE(1024)`. Cross-referenced (documented in comments):
`VDP_DISPLAY_ORIGIN_Y_BIAS(8)` / `_X_BIAS(16)` in `vdp_comm.s`. The former coordinate literals `304`, `240`, `-16`,
`320`, `224`, `0x0080` in the modified coordinate/clip/SAT-conversion path are all now named; remaining literals in
that path are structural (code mask `0x0FFF`, entry stride, flip bit indices, the SAT 9-bit field mask), not
coordinate magic.

## Validation (Genesis MAME, Build 0147)
1. **Mirror preservation.** The full 0x800-byte `pc090oj_object_ram` at the title is **byte-identical to Build 0146**;
   the left/right hidden score records (28–33 / 37–42) remain `code 0x2A, Y 0x0000`.
2. **Representation removal.** Records 28–33 and 37–42: `represented = 0`, `record_to_slot = 0xFF` (no slot).
3. **Resource recovery.** Represented count 23 → **11**; SAT-chain sprites covering scanline 0: 20 → **9**. No
   worklist/link/slot for the culled records.
4. **Visual title.** Unwanted `000000` rows gone; `1UP`, `HIGH SCORE`, and complete `2UP` visible with the short `00`
   scores beneath — matches the arcade header layout (`snaps/gen147_title.png`).
5. **Dynamic non-zero digit.** Debugger experiment on an equivalent unused record: code `0x39` (a different top-inked
   digit) at raw Y=0 → `represented = 0, slot = 0xFF` (still fully clipped). Proves the cull is geometry-driven, not
   code/zero/record-specific.
6. **Move into visible area.** Same digit code `0x39` at raw Y=0x20 → `represented = 1, slot = 0x0B` — automatically
   represented.
7. **Flip handling.** Same digit code `0x39` at raw Y=0 with vertical flip (word0 = 0x8000) → `represented = 1,
   slot = 0x0C`: the flipped opaque rows move to the bottom half and survive the clip. Horizontal clipping is the
   symmetric column path and did not drop any on-screen frontend/item sprite.
8. **Coordinate-constant audit.** See list above; modified coordinate/clip logic contains no unexplained coordinate
   magic numbers.
9. **Sprite/background relationship.** Initial Y offset −8 selected to match the background's +8 origin bias; item
   weapon/sword sprites (records 64–67, Y 0x40–0x70) now sit up 8 px, aligning with their item-name rows
   (`snaps/gen147_item.png` vs Build 0146 `gen146_item.png`). X offset 0 (no X landmark divergence observed).
10. **Regression.** Build 0146 HIGH SCORE correction intact (complete `HIGH SCORE`); Build 0145 item-sprite palette
    intact — item screen state 2/2/6, staged line 3 (bank 51) **byte-identical** to Build 0145, all four bank-51 item
    sprites (records 64–67) represented and visible; only the twelve leading zeros culled (item represented 22 → 10).
    Frontend sprite identities, mirror ownership, and staging→commit architecture unchanged.

## Build 0147
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0147.bin`
- **SHA256:** `bb2af8f9da5a005a1fc25ab8a4faabce25479cd576048b4d4e3047ea6cd52ddd`
- **Size:** 1,580,368 B (Build 0146 = 1,563,892; +16,476 = 16,384-byte opaque-box table + ~92 B decode).
- **Address-map:** `opcode_replace = 133`; `total_genesis_bytes_covered = 0x181D50`; **gaps = [], overlaps = []**.
- **Paired canonical (value-only, authorized):** `CANONICAL_TOTAL_GENESIS_BYTES_COVERED 0x17DCF4 → 0x181D50` in
  `postpatch_startup_rom.py` + `verify_canonical_rom.py`; opcode count unchanged (133). GATE_PASS; boot guard PASS;
  30-s auto-trace clean. Builds 0142–0146 not overwritten.
- **Files changed:** `apps/rastan-direct/src/pc090oj_hooks.s` (constants + decode), `pc090oj_assets.s` (incbin),
  `apps/rastan-direct/Makefile` (asset rule), `tools/translation/build_pc090oj_opaque_bbox.py` (new),
  `tools/translation/postpatch_startup_rom.py` + `verify_canonical_rom.py` (coverage), regenerated
  `out/*.o/.elf/symbol.txt` + `build/rom_inventory.json`, this doc, `AGENTS_LOG.md`, `OPEN_ISSUES.md`.

## Architecture-compliance statement
CONFIRMED. The change is a decode-time visibility gate inside the existing arcade-called helper path, using stable
asset-derived pattern metadata generated at build time. It preserves every mirror record (culls SAT representation
only), reuses the existing candidate → decode → activate/deactivate pipeline, adds no second renderer/lifecycle/commit
path, and applies a general coordinate+clip rule with no special-casing of records 28–33/37–42/34/43, code 0x2A,
zero digits, score patterns, the title screen, `UP`, the final SAT slot, or any chain position.

## Open/Closed Issues Impact
- **OPEN-001 (title/attract graphics incomplete):** materially advanced — the missing `UP` in `2UP` is fixed via a
  faithful viewport rule, and the extra rendered leading-zero score rows are removed by the same rule (one root
  cause). Not closed (other title/score-value items remain).
- **OPEN-024 (PC090OJ subsystem incomplete):** advanced — a general arcade visible-area top-clip + opaque-geometry
  SAT-representation gate, plus named, configurable sprite viewport offsets aligned to the background origin. Not
  closed.
- No issue closed; no duplicate opened.

## Scope statement
PC080SN was inspected (offset evidence) but not modified. Score values, real-gameplay scrolling alignment, real
hardware, other frontend/gameplay content, and X-offset tuning were not changed. Real-hardware validation NOT CLAIMED.
