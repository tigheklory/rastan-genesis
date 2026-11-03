# Build 0454 — Arcade-Exact Item-Description Semantic Conversion

Date: 2026-10-19
Agent: Cody
Status: ROM candidate produced; Tighe visual/hardware acceptance required

## Outcome

Build 0454 corrects the Build-0453 item-description package generator from original arcade
code and ROM data. It does not replace or weaken the native vertical-ring architecture. The
result remains a precomputed 64x64 logical Plane-B map projected through a 64x32 physical ring,
with the retained arcade `A5+0x10EE` scroll value controlling native VSRAM and exactly one row
replacement at each eight-pixel crossing.

Build 0453 remains preserved and explicitly rejected: source
`d5bae39b67f5df6d5ff3499adfa6972bdf111942`, canonical SHA-256
`628f3025dfffe09a6b2188b0ecc14f5134683b93efdbc3482275dd489fd4a36e`. Its existing rope
benchmark was `798 / 798 / 798` frames, median `13,317.147 ms`, deterministic YES. That proves
performance neutrality against accepted Build 0452, not presentation correctness, and Build 0453
must not be acceptance-locked.

Screenshots were used only as evidence that Build 0453 was visually wrong. No coordinate, spacing,
palette, or placement value was derived from a screenshot.

## Arcade static proof

The final authority is `build/maincpu.disasm.txt` plus the original ROM regions. The current
Build-0454 arcade-to-Genesis relationships below are from generated
`build/rastan-direct/address_map.json`, not a presumed `+0x200` delta.

| Meaning | Arcade PC | Build-0454 runtime PC |
|---|---:|---:|
| page-A entry/build | `0x05602C` / `0x056032` | `0x056090` / `0x056098` |
| page-B build | `0x056056` | `0x0560BC` |
| item-screen tick | `0x05607C` | `0x0560E2` |
| row-stream advance | `0x0560DA` | `0x056144` |
| icon-record copy | `0x056114` | `0x05617E` |
| shared text/layout writer | `0x0563A6` | `0x056410` |
| glyph alias routine | `0x0563CE` | `0x056438` |
| scroll publication | `0x055AB4` | `0x055B18` |
| item palette setup | `0x056176` | `0x0561E0` |
| shared palette load | `0x059AD4` | `0x059B0E` |

One earlier description called arcade `0x563A6` a metatile decompressor and named `0x565A6` /
`0x565CE` as the writer/alias functions. Raw disassembly disproves that wording: original arcade
`0x563A6` is the shared byte-stream text/layout writer and `0x563CE` is its glyph-alias routine.
Original `0x565A6` and `0x565CE` are data. The incorrect names arose from a historical shifted
Genesis correspondence. The C decompilation comments and metadata were corrected accordingly.

### Text and layout

At arcade `0x5602C..0x56054`, page A supplies:

- text/layout source `0x05672A`;
- destination `0x00C00828`;
- attribute word `0x0000`;
- icon source `0x056226`, copied to `0x00D00170` by `0x56114`.

The PC080SN destination encodes row 4, column 10: a row is `0x200` bytes and a cell is four bytes.
The stream contains 28 rows. Its byte values are the actual horizontal layout: spaces are emitted
cells, `0xFF` advances the saved destination by one row, and `0x00` terminates the stream. Ordinary
bytes are glyph codes. `0x563CE` aliases `0x21/22/27/28/29/2C/2D/3F` to
`0x2744..0x274B`. Therefore item-name X, description X, line wrapping, blank space, blank rows,
inter-item spacing, punctuation, and ordering are all encoded by the stream plus this exact writer;
there is no independent uniform item-spacing rule.

At arcade `0x56056..0x5607A`, page B supplies:

- text/layout source `0x05697E`;
- destination `0x00C00028`, physical row 0, column 10;
- attribute word `0x0000`;
- icon source `0x0562B0`, copied to `0x00D00170` by `0x56114`.

Page B contains seven rows. It is not present at initial entry. `0x5607C` decrements
`A5+0x10EE` by one modulo 512 every fourth frame and calls `0x560DA` whenever the result is an
eight-pixel boundary. When the stream cursor reaches `0xC00F00`, after 12 crossings / 96 pixels,
`0x560DA` invokes page B. Its physical rows 0..6 consequently replace the ring aliases of logical
rows 32..38. Treating the raw physical destination as logical rows 0..6, as Build 0453 did,
overwrote the beginning of page A and broke the authored two-page composition.

### Icons, palettes, and scroll relationship

`0x56114` copies each four-word/eight-byte record from `0x56226` (17 page-A records) or
`0x562B0` (three page-B records), stopping at first word `0xFFFF`. The record is
`{attribute, Y, source code, X}`. Those tables are the source of icon identity, base position,
attribute/flip state, page membership, and ordering. At the 96-pixel page-B boundary, the arcade
copy replaces the first three page-A records; the native emitter preserves that ownership change.
Visible Y remains derived from the descriptor Y and live scroll progress, with the arcade retirement
threshold and viewport-origin conversion preserved. The retained attract dispatcher still owns
screen lifetime, Start/credit handling, and teardown.

The item setup path calls `0x56176`, which invokes `0x59AD4` for arcade palette destination/bank
`0x33` from source palette row 4. Item sprite control `0x0060` yields colbank `0x30`; combining
that with the descriptor attribute nibble produces effective banks `0x33` and `0x30`. The existing
generated scene-0 PC090OJ palette decision LUT maps bank `0x33` to Genesis line 3 and bank `0x30`
to line 2. Build 0453 instead forced every icon to line 0. Build 0454 consumes the current generated
`pc090oj_palsel_lut.inc`, so it neither invents a palette number nor creates a duplicate palette
policy. `specs/palette_decisions.json` was consulted; no palette decision was changed, so the
registry required no edit.

## Build-0453 root cause

The native ring and cadence were sound. The offline package was wrong in three exact ways:

1. It placed page A at logical row 8 rather than decoding `0xC00828` as row 4, column 10.
2. It placed delayed page B at logical rows 0..6 rather than logical rows 32..38, so it overwrote
   page-A content instead of representing the arcade's later physical-ring replacement.
3. It discarded the sprite-control colbank plus per-record attribute nibble and forced all icons to
   Genesis palette line 0 rather than applying the established scene-0 bank-to-line mapping.

The old verifier passed because it shared those same incorrect hard-coded placement and palette
assumptions with the generator. It proved self-consistency, not arcade equivalence.

## Corrected offline conversion and independent gate

`tools/translation/gen_native_item_description.py` now decodes the two actual C-window
destinations, places page B at the proven delayed logical owner, and derives every icon tile word
from the original descriptor plus the generated current palette LUT. The final package contains:

- a complete 64-row by 64-column logical map;
- 28 page-A source rows at row 4/column 10;
- seven page-B source rows at row 32/column 10;
- 27 unique Plane-B patterns;
- 17 page-A plus three page-B icon records;
- effective bank `0x33 -> line 3`, bank `0x30 -> line 2`.

No runtime text interpretation, glyph/layout processing, PC080SN presentation, or decompression was
introduced. The semantic cut remains arcade item attract state/scroll/dwell into final native
Plane-B ring rows and native SAT icon pieces; the retired tail remains the item-specific PC080SN
C-window writer/row stream and PC090OJ tuple-copy/render representation.

`tools/translation/verify_native_item_description.py` independently reconstructs every source cell
from the two original ROM streams and original writer semantics, compares blank and nonblank cells,
compares pattern bytes where tile numbers differ, exhausts all 64 logical ring windows, decodes the
two icon tables independently, and validates identity, X/Y, priority, flip, palette line, and source
pattern bytes.

The strengthened gate was deliberately exercised against preserved Build-0453 outputs:

- the old logical map fails spatial equivalence at row 0, column 10 (`blank source ... is 0x0001`);
- with corrected map/pattern data but the old icon records, it fails the first icon palette check
  (`attr=0x0003`, bank `0x33`, expected line 3, old tile word `0x858B`);
- the corrected package passes:
  `NATIVE_ITEM_VERIFY_PASS logical=64x64 physical=64x32 crossings=64 plane_patterns=27 icons=17+3`.

This detects both classes that escaped the Build-0453 self-check.

## Native ring invariants retained

- Physical Plane B: 64x32.
- Logical presentation: 64x64.
- Initial resident window: logical rows 4..35.
- Mapping: `physical_row = logical_row & 31`.
- Scroll authority: retained arcade `A5+0x10EE`, modulo 512.
- Pixel-scroll frame: native VSRAM update only.
- Eight-pixel crossing: one precomputed 64-word row copy and one dirty physical row.
- Full wrap: no full-plane rebuild and no runtime decompression.

## Validation and artifact

The normal Makefile-owned Build-0454 pipeline passed the corrected item gate, ring and ownership
checks, icon/palette checks, shared frontend HUD, native title, BEST-5, assembly/link, 75-site
shift-table reflow, boot guards, canonical gate, gameplay-entry gate, seven-epoch gate, fixed
30-second USA/NTSC Genesis MAME validation, and complete configured ROM-family validation.

- ROM-producing source commit: `2c83bc25be43c8495f039d429f08eb74667a73f1`
- Canonical artifact: `dist/rastan-direct/rastan_direct_video_test_build_0454.bin`
- Size: `2,735,800` bytes
- Canonical SHA-256: `e3c12b58e7cd7d9a499e26f8fec7aa2db0642d344c2a606f359b99fd55640a5d`
- Counter: `454`
- Family: canonical, `_c`, `_d`, `_do`, `_full_hud`, `_invincible`, `_s`
- Fixed validation trace:
  `states/traces/rastan_direct_video_test_build_0454_mame_30s_20261019_112428`

The unchanged established benchmark was then run against Build 0454 `_invincible`:

```text
798 / 798 / 798 frames
median 13,317.147 ms
deterministic YES
```

Evidence: `states/traces/build0454_rope_attach_benchmark_invincible/`. This exactly matches the
Build-0453 and accepted Build-0452 rope timing; no global gameplay performance regression is
measurable on that route.

## Issue-ledger impact and acceptance

This candidate advances the item-page portion of OPEN-001 but does not close that broad visual
issue before human verification. OPEN-032 remains open: coin-during-item-screen icon teardown must
be verified specifically by Tighe and was not inferred from static or mechanical gates. No new
unresolved issue was discovered, and no issue is closed by this build.

Build 0454 requires Tighe verification on real hardware (or his acceptance environment): exact
arcade-authored layout and spacing, item names and multiline descriptions, icon identities/colors/
alignment, smooth scrolling, no seam/black bar, seamless 512-pixel wrap, correct HUD, coin-time icon
teardown, unchanged earlier attract screens, and no gameplay regression. Until Tighe explicitly
accepts it, Build 0454 is a candidate only.

Phase D/E: NO.
