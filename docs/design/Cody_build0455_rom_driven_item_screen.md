# Build 0455 — ROM-Driven Arcade Item-Screen Reconstruction

Date: 2026-10-19  
Agent: Cody  
Status: ACCEPTED by Tighe; acceptance ref `accepted/build-0455`

## Outcome

Build 0454 is visually rejected as a complete candidate, but its native item-screen cut, native
icon path, palette mapping, 64-logical-row to 32-physical-row ring, live `A5+0x10EE` scroll
authority, and one-row crossing path are retained. Build 0455 changes the faulty build-time layout
model and adds the minimum entry snapshot required by the arcade publication timeline.

No coordinate was measured from a screenshot. The reconstruction comes from the original
`maincpu.bin`, the original writer/control flow, and the PC080SN hardware geometry.

## Missing arcade semantic and hardware proof

Build 0454 treated `0x200` bytes as one C-window row. That is false. MAME's PC080SN device defines
each BG tilemap as `TILEMAP_SCAN_ROWS`, 64x64 cells, with 8x8-pixel tiles. Each cell is two 16-bit
words: attribute at `2*tile_index`, code at `2*tile_index+1`. Therefore:

- cell width/height: 8x8 pixels;
- column stride: 4 bytes;
- row stride: 64 * 4 = `0x100` bytes;
- C-window row: `((address & 0x3FFF) / 0x100)`;
- C-window column: `((address & 0xFF) / 4)`;
- semantic visible X: `column*8 - 16` (PC080SN `set_scrolldx(-16, -16)` for Rastan);
- semantic visible Y at a given scroll progress: `unwrapped_row*8 - progress - 8`, where the last
  `8` converts the Rastan raster visible-area top (`y=8`) to screen-local Y;
- one scroll-counter unit is one visible pixel.

The original writer at arcade `0x0563A6` decodes `0xFF` by adding the ROM immediate `0x200` to the
saved destination. With the proven `0x100` hardware row stride, each delimiter advances **two**
8-pixel rows (16 pixels). The missing alternate blank row is why Build 0454 compressed the content
and displayed too many items at once.

The hardware also independently proves the retained ring size: 64 rows * 8 pixels = 512 pixels,
matching the original tick's ROM immediate `AND #0x01FF` at `0x056098`. The 64-row ring is not a
Genesis convenience inferred from Build 0454.

Proof sources:

- canonical Ghidra project/exports under `analysis/ghidra/rastan_arcade/`;
- `build/maincpu.disasm.txt` and `build/regions/maincpu.bin`;
- original writer `0x0563A6`, alias routine `0x0563CE`, page loaders `0x05602C`/`0x056056`, tick
  `0x05607C`, and row advance `0x0560DA`;
- official MAME `src/mame/taito/pc080sn.cpp`, `pc080sn.h`, and `rastan.cpp` device/visible-area
  definitions;
- corrected existing C decompilation in `analysis/decompilation/c/rastan_attract_item_description.c`
  and `raw/000563a6.c`.

## ROM-driven reference model

`gen_native_item_description.py` now decodes the page sources, destinations, attributes, icon
sources, writer delimiter, glyph-alias immediates, scroll mask, cursor start, page-B trigger, and
cursor step from original ROM instructions. It then executes the original text writer over a
separate 64x64 arcade state before converting source codes to native patterns/name words.

The derived presentation is:

- Page A: source `0x05672A`, destination `0x00C00828`, hardware row 8, column 10; 28 stream rows
  occupy rows 8,10,...62.
- Page B: source `0x05697E`, destination `0x00C00028`, physical row 0, column 10; seven stream rows
  occupy physical rows 0,2,...12 and unwrapped presentation rows 64,66,...76.
- Page B publication: derived at scroll progress 96 from cursor start `0xC00400`, trigger
  `0xC00F00`, and cursor step `0x100`.
- Icons: original tables decoded through the page-loader immediates (`0x056226`, 17 records;
  `0x0562B0`, three records). Build 0454 effective banks `0x33`/`0x30` and palette lines 3/2 are
  unchanged.

Page B is absent in the arcade entry snapshot but resident in the final wrapped surface. A single
static map cannot represent both states at physical rows 0..12. Build 0455 therefore generates:

1. a 32-row pre-page-B entry snapshot; and
2. the final 64-row circular map used by ordinary crossings.

Entry copies the snapshot. The unchanged crossing algorithm then sources final-map row
`(31+crossing)&63`, so wrapped Page-B rows enter naturally one row at a time. There is no runtime
text decoder, PC080SN emulator, page-layout interpreter, full-plane rebuild, or new timer.

The durable reference JSON is `build/rastan-direct/native_item_arcade_reference.json`. Its ledger
contains 725 text writes. Every record contains original source address/byte, decoded code,
destination, hardware row/column, unwrapped world row/column, semantic visible X/Y, page, and
attribute. Every nonblank native text cell resolves to original PC080SN pattern bytes; unexplained
native text cells: zero.

## Independent oracle

`verify_native_item_description.py` independently decodes the original ROM writer/page immediates
and reconstructs the entry and final surfaces without consuming generator placement constants.
It compares semantic source identity and exact pattern bytes rather than native tile numbers.

The preserved Build 0454 package was copied before edits and run against this oracle. It fails as
required:

- first mismatch: final row 0, column 10; expected arcade code `0x0052`, native word `0x0000`;
- total mismatches: 987;
- categories: missing final text 237; unexpected final text 268; wrong final pattern 94;
  missing/wrong entry text 146; stale entry text 242.

The corrected package passes with zero mismatches:

`NATIVE_ITEM_VERIFY_PASS oracle=ROM+PC080SN logical=64x64 physical=64x32 crossings=64 plane_patterns=27 icons=17+3`

This proves the oracle does not reproduce Build 0454's row-stride/page-placement assumptions.

## Retained runtime and semantic cut

Semantic cut: original item attract state, live scroll, dwell, and page timeline -> precompiled
Genesis Plane-B rows and native SAT icons. Retired chip tail: PC080SN byte-stream/C-window
realization and PC090OJ object-record hardware realization.

- physical Plane B: 64x32;
- logical circular surface: 64x64 / 512x512 pixels;
- mapping: `physical_row = logical_row & 31`;
- pixel-only frame: VSRAM update only;
- row crossing: one 64-word precompiled row plus one dirty bit;
- full wrap: no full rebuild;
- runtime text/layout processing: none;
- runtime PC080SN emulation: none.

The only runtime-support correction is selecting the generated entry snapshot and changing the
entry owner range from rows 4..35 to physical rows 0..31. The ring advance body, scroll cadence,
VSRAM path, native icon emitter, dwell/retirement, and palette semantics are unchanged.

## Exact PC/function correlation

Generated `build/rastan-direct/address_map.json` is the mapping authority:

| Function | Arcade PC | Build 0455 Genesis PC |
|---|---:|---:|
| page-A semantic cut | `0x05602C` | `0x056090` |
| page-B writer caller | `0x056056` | `0x0560BC` |
| item tick semantic cut | `0x05607C` | `0x0560E2` |
| row/page timeline | `0x0560DA` | `0x056144` |
| icon record copy | `0x056114` | `0x05617E` |
| text/layout writer | `0x0563A6` | `0x056410` |
| glyph aliases | `0x0563CE` | `0x056438` |
| scroll publication | `0x055AB4` | `0x055B18` |
| item palette setup | `0x056176` | `0x0561E0` |
| shared palette load | `0x059AD4` | `0x059B0E` |

## Validation and artifacts

PASS: ROM-driven arcade oracle, native conversion, ring invariants, icon/palette semantics, VRAM
ownership, shared HUD, title, BEST-5, assembly/link, 75-site shift reflow, canonical gate,
gameplay-entry gate, seven-epoch gate, fixed 30-second Genesis NTSC MAME, invincibility verifier,
and complete seven-ROM family (canonical, `_d`, `_s`, `_do`, `_c`, `_full_hud`, `_invincible`).

- Source commit: `bb09135dee3e6491a844c84635a70710291a33f6`
- Canonical: `dist/rastan-direct/rastan_direct_video_test_build_0455.bin`
- Canonical SHA-256: `3a2141bd5aa1f1dafbb0d5a59fa408e736f29c32ae377e595ab982e45aa8db68`
- `_invincible` SHA-256: `91db6af42904a4563dc7d5b91abf3c1ecd3d5ba1745e1ee5a30463ae8f865755`
- Size: 2,739,896 bytes each
- Counter: 455
- Fixed trace: `states/traces/rastan_direct_video_test_build_0455_mame_30s_20261019_120827`
- Rope evidence: `states/traces/build0455_rope_attach_benchmark_invincible/`
- Rope: 798 / 798 / 798 frames; median 13,317.147 ms; deterministic YES

The rope result exactly matches accepted Build 0452 and rejected-but-performance-neutral Builds
0453/0454. No global gameplay performance regression is measurable on the established route.

## Issue-ledger impact and acceptance

Build 0454 is recorded as visually rejected. Build 0455 advances the item-screen portion of
OPEN-001 but does not close it without Tighe visual verification. OPEN-032 remains open: this task
did not prove coin-during-item-screen icon teardown. No CLOSED issue changes.

Tighe visually accepted Build 0455. The exact accepted ROM-producing source is
`bb09135dee3e6491a844c84635a70710291a33f6`, locked by `accepted/build-0455`; the later
bookkeeping commit `3d0bcc31` does not replace that source identity. The accepted deterministic
rope result is 798/798/798 frames, median 13,317.147 ms. OPEN-032 remains open because item-screen
acceptance did not establish coin-up icon teardown.

Phase D: NO. Phase E: NO.
