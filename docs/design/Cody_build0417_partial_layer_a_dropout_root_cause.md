# Cody — Build 0417 Partial Layer-A Dropout Root Cause

Date: 2026-10-12  
Scope: read-only Build 0417 / Build 0417 `_do` MAME instrumentation and ROM/code forensics  
Production modified: **NO**  
Palette modified: **NO**  
ROM built / build number consumed: **NO / NO**

## Owner fact

The owner fact is accepted without reinterpretation: portions of Layer A inside
the six Segment-2 A-0154 occurrences are missing and Plane B is visible through
them. The defect is sub-tile, and `_do` exposes a larger portion than ordinary
0417.

Target anchor: Segment 2 / record 2, X40/Y38, code `0x117`, physical A-0154,
LA-0092, bank `0x003`, descriptor `0x02A284`, tile-word `0x003098`.

The six physical A-0154 occurrences are:

| # | Source cell | Logical usage | Bank |
|---:|---|---|---:|
| 1 | X44/Y30 | LA-0543 | `0x005` |
| 2 | X48/Y30 | LA-0092 | `0x003` |
| 3 | X44/Y34 | LA-0543 | `0x005` |
| 4 | X52/Y34 | LA-0092 | `0x003` |
| 5 | X40/Y38 | LA-0092 | `0x003` |
| 6 | X44/Y38 | LA-0543 | `0x005` |

All six share one physical pattern and one live Genesis slot, `0x3A4` (VRAM
`0x7480..0x749f`). The shared upload is therefore the common owner of all six
defects.

## Proven mechanism: a ROM DMA crosses a 128-KiB source bank

`fg_boundary_install` constructs each PC080SN upload as:

```asm
source = genesistan_pc080sn_tile_rom + arcade_code * 32
length = 16 words / 32 bytes
destination = slot * 32
```

See `apps/rastan-direct/src/fg_tile_cache.s:344..356`. It calls
`vdp_dma_words_to_vram`, whose primitive programs one unsplit 68k-to-VDP DMA
(`apps/rastan-direct/src/dma.s:130..169`).

The Genesis VDP DMA source counter operates within a 64-Kword / 128-KiB bank.
The repository's established SGDK implementation encodes that contract
directly: `DMA_doDma` calculates the next `0x20000`-byte boundary and splits a
transfer that crosses it (`tools/sgdk/src/dma.c:545..563`); the documented
`Fast` entry is explicitly the version that omits the 128-KiB crossing check
(`tools/sgdk/inc/dma.h:427..432`, `457..462`).

The Build-0417 native primitive performs no such split. A-0154 lands at exactly
the bad boundary:

| Variant | tile-ROM base | `0x117 * 32` | DMA source | Correct bytes before `0x160000` | Rows correct |
|---|---:|---:|---:|---:|---:|
| 0417 | `0x15DD08` | `0x22E0` | `0x15FFE8` | 24 | 6 |
| 0417_do | `0x15DD18` | `0x22E0` | `0x15FFF8` | 8 | 2 |

At `0x160000`, hardware wraps the low 64-Kword source counter to the beginning
of the same 128-KiB bank, `0x140000`. Normal 0417 therefore reads its final 8
bytes from `0x140000..0x140007`; `_do` reads its final 24 bytes from
`0x140000..0x140017`.

The `_do` macro adds the two display-register instructions in
`dma_publish_frame` (`apps/rastan-direct/src/dma.s:72..94`). That grows/reflows
the linked image by `0x10` before the tile corpus. The MAME trace directly
records the resulting A-0154 sources as `0x15FFE8` and `0x15FFF8`. Thus `_do`
does not merely change raster timing: it moves A-0154 sixteen bytes closer to
the DMA-bank boundary, changing the corrupt part from two rows to six.

## Exact loaded pattern bytes and fetch granularity

The intended A-0154 bytes are:

```text
row  intended
0    BB B9 B8 89
1    B9 99 98 88
2    99 66 99 88
3    66 66 99 8B
4    66 66 98 8B
5    66 66 98 8B
6    66 77 69 8B
7    66 77 69 88
```

The actual hardware source sequence implied by the VDP boundary contract is:

| row | normal 0417 | 0417_do |
|---:|---|---|
| 0 | `BBB9B889` | `BBB9B889` |
| 1 | `B9999888` | `B9999888` |
| 2 | `99669988` | `3FEA0005` |
| 3 | `6666998B` | `01040473` |
| 4 | `6666988B` | `00003FF4` |
| 5 | `6666988B` | `00050104` |
| 6 | `04750000` | `04750000` |
| 7 | `3FFE0005` | `3FFE0005` |

The corrupt values are the exact ROM bytes at the wrapped source
`0x140000..0x140017`, not inferred colors. A Genesis 8x8 4-bpp pattern row is
four bytes, so the 24-byte versus 8-byte boundary remainder produces a clean
whole-row cutoff: six correct rows in normal, two in `_do`. Within a corrupt
row, each zero nibble is Plane-A color index zero and is transparent, exposing
the corresponding Plane-B pixel.

## Normal 0417 defect masks

`X` means the loaded Plane-A nibble is zero and Plane B shows through. The
shared physical slot makes the mask identical at all six occurrences.

```text
#1              #2              #3
........         ........         ........
........         ........         ........
........         ........         ........
........         ........         ........
........         ........         ........
........         ........         ........
X...XXXX         X...XXXX         X...XXXX
....XXX.         ....XXX.         ....XXX.

#4              #5              #6
........         ........         ........
........         ........         ........
........         ........         ........
........         ........         ........
........         ........         ........
........         ........         ........
X...XXXX         X...XXXX         X...XXXX
....XXX.         ....XXX.         ....XXX.
```

Missing pixels: **8 per occurrence; 48 across six**.

## Build 0417_do defect masks

```text
#1              #2              #3
........         ........         ........
........         ........         ........
....XXX.         ....XXX.         ....XXX.
X.X.X...         X.X.X...         X.X.X...
XXXX....         XXXX....         XXXX....
XXX.X.X.         XXX.X.X.         XXX.X.X.
X...XXXX         X...XXXX         X...XXXX
....XXX.         ....XXX.         ....XXX.

#4              #5              #6
........         ........         ........
........         ........         ........
....XXX.         ....XXX.         ....XXX.
X.X.X...         X.X.X...         X.X.X...
XXXX....         XXXX....         XXXX....
XXX.X.X.         XXX.X.X.         XXX.X.X.
X...XXXX         X...XXXX         X...XXXX
....XXX.         ....XXX.         ....XXX.
```

Missing pixels: **23 per occurrence; 138 across six**.  
Missing in both variants: **8 per occurrence / 48 total**.  
Additional `_do` pixels: **15 per occurrence / 90 total**.

The growth is four additional complete pattern scanlines (rows 2..5), with the
column mask within each row determined by zero nibbles in the wrapped ROM
bytes. This is the exact 4-byte pattern-row granularity expected from the DMA
boundary positions.

## Full compositor classification

Ignoring sprite priority/occlusion, the plane classification is complete:

| Variant | Per occurrence: Plane A | Per occurrence: Plane B | Six occurrences: Plane A | Six occurrences: Plane B | Unresolved |
|---|---:|---:|---:|---:|---:|
| 0417 hardware contract | 56 | 8 | 336 | 48 | 0 |
| 0417_do hardware contract | 41 | 23 | 246 | 138 | 0 |

The eight-row masks above are the full 64-pixel classification for each of the
six cells: every `X` is Plane B; every `.` is a nonzero Plane-A pixel. Nonzero
wrapped nibbles may have the wrong Plane-A color but are not counted as the
owner-confirmed transparency defect.

At the comparable MAME frame 1662, the six Plane-B cells underneath are:

| # | Plane-B name address | name | slot |
|---:|---:|---:|---:|
| 1 | `0xCF76` | `0x41A6` | `0x1A6` |
| 2 | `0xCF7E` | `0x41AA` | `0x1AA` |
| 3 | `0xC176` | `0x41E6` | `0x1E6` |
| 4 | `0xC106` | `0x4255` | `0x255` |
| 5 | `0xC36E` | `0x4211` | `0x211` |
| 6 | `0xC376` | `0x41E2` | `0x1E2` |

Therefore the exposed RGB differs by occurrence even though the zero mask is
identical, which matches six repeated holes revealing different mountain
pixels beneath them.

MAME's comparable PNG uses the intended contiguous source instead of the
hardware-wrapped source. Its full 64-pixel reconstruction reports 64/64 Plane
A pixels for occurrences 1, 2, 3, 5, and 6. Occurrence 4 has 28 Plane-A pixels
and 36 screenshot pixels covered by Rastan's sprite; none are Plane B. This is
an emulator/hardware DMA-source-model mismatch, not a contradiction of the
owner fact.

## Exact six-cell scanline state

At the comparable state (frame 1662, FG `0x0110/0x0155`, BG
`0x0188/0x0155`), the six bounds are:

| # | Plane-A name | Screen X | Screen Y | MAME name during all 8 rows | Hardware pattern rows |
|---:|---:|---:|---:|---|---|
| 1 | `0xEF58` | 98..105 | 61..68 | `0x63A4` | normal 0..5 correct, 6..7 wrapped; `_do` 0..1 correct, 2..7 wrapped |
| 2 | `0xEF60` | 130..137 | 61..68 | `0x63A4` | same shared slot |
| 3 | `0xE158` | 98..105 | 93..100 | `0x63A4` | same shared slot |
| 4 | `0xE168` | 162..169 | 93..100 | `0x63A4` | same shared slot |
| 5 | `0xE350` | 66..73 | 125..132 | `0x63A4` | same shared slot |
| 6 | `0xE358` | 98..105 | 125..132 | `0x63A4` | same shared slot |

There is no mid-tile name change in this settled owner-comparable frame. Slot
`0x297` contains zeros and the previously proven X40/Y38 entrance-frame
`0x6297 -> 0x63A4` race remains real, but it is not the six-at-once defect:
all six settled names point to `0x3A4`. The sub-tile split is inside the shared
pattern uploaded to slot `0x3A4`.

## Full VDP activity and active-display audit

The reused trace was extended to capture all VDP control commands, register
writes, PIO writes, DMA starts, DMA destinations/counts/sources, and an
end-bound observation at the next VDP access. Raw timelines:

- `states/traces/build0417_A0154_partial_dropout/normal/vdp_events.tsv`
  (23,624 events plus header)
- `states/traces/build0417_A0154_partial_dropout/do/vdp_events.tsv`
  (26,870 events plus header)

Representative target-scene active-display work is:

| Frame | Normal 0417 VDP activity | `_do` display bracket / corresponding activity | Target-row relation |
|---:|---|---|---|
| 1649 | Plane-B 32-word DMA `C008`, V120..127; SAT V131..132 | OFF V115 through ON V133 | crosses bottom A-0154 scanlines |
| 1651 | Plane-A 32-word DMA `E010`, V85..92; six 64-word sprite-pattern DMAs V95..104; SAT V105..106 | OFF V79 through ON V107 | crosses middle scanlines |
| 1659 | Plane-B 32-word DMA `C00A`, V47..55; sprite-pattern DMAs V59..63; SAT V64..65 | OFF V43 through ON V66 | crosses top scanlines |
| 1662 | SAT 320-word DMA `F800`, V153..154; HScroll/VSRAM V154 | OFF V149 through ON V155 | after all six target ranges (Y61..132) |

Thus active-display DMA and `_do` forced-blank bands are both real performance
defects. They are not the A-0154 root cause:

1. at the owner-comparable frame no VDP operation overlaps target rows;
2. no A-0154 pattern or six target-name write occurs during those rows;
3. the normal and `_do` source-boundary positions independently predict the
   exact 6-row versus 2-row valid pattern split;
4. the wrapped ROM bytes independently predict the exact 8 versus 23
   transparent-nibble masks.

The Sega technical overview states that memory-to-VRAM DMA is supported during
active scan at the reduced active-scan transfer rate. Such unrelated DMA can
delay the CPU and can expose partial updates when it writes scanned data, but
it does not substitute bytes in the already resident `0x3A4` pattern. The
fixed, pattern-relative holes are instead produced at the one-time A-0154 ROM
upload.

`_do` additionally creates the intentional black diagnostic bands shown in the
timeline. Those full-width black rows are separate from the owner-marked
Plane-B-through-A mask.

## Why settled VRAM looks correct in MAME

The trace's software mirror and MAME live VRAM both contain the intended
contiguous 32 bytes because MAME completed the DMA across `0x160000` instead of
applying the real VDP 64-Kword source-counter wrap. Consequently terminal MAME
VRAM, names, CRAM, and screenshots are internally consistent but do not model
this hardware boundary condition. On hardware, the DMA completes and the
settled name remains `0x63A4`; what is wrong is the settled content of slot
`0x3A4` after the wrapped source read.

## Root cause and repair boundary

**Root cause:** `vdp_dma_words_to_vram` issues A-0154's 16-word ROM upload as
one DMA even though `[source, source+32)` crosses a 128-KiB VDP DMA source-bank
boundary. Normal 0417 crosses after 24 bytes; `_do` crosses after 8 bytes due
to its `+0x10` linked-image shift. Hardware wraps to `0x140000`, injecting 8
versus 24 unrelated bytes. Their zero nibbles expose Plane B.

This mechanism explains:

- partial-tile Layer-B exposure: **YES**;
- all six occurrences: **YES**, through the shared slot `0x3A4`;
- larger `_do` exposure: **YES**, 23 versus 8 zero nibbles per occurrence;
- correct MAME settled state: **YES**, emulator source-counter mismatch;
- timing-sensitive build-layout change without a palette change: **YES**.

No repair is implemented in this task. The bounded repair boundary for a later
build is to make ROM-source VDP DMA 128-KiB-safe (split at `0x20000` boundaries
or guarantee source alignment), without changing A-0154, LA-0092, palettes,
name words, or gameplay.

