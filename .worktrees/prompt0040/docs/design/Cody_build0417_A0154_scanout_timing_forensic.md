# Cody Build 0417 — A-0154 Scanout-Timing Forensic

## Scope and result

This was a read-only Genesis NTSC MAME comparison of the existing Build 0417
and Build 0417 `_do` ROMs. Production source, palette decisions, ROMs, and the
build counter were not changed.

The owner anchor is confirmed: Segment-2 source cell X40/Y38 is code `0x117`,
physical pattern A-0154, logical usage LA-0092, bank `0x003`, descriptor entry
`0x02A284`, and tile-word address `0x003098`.

The central timing hypothesis is disproven for the six simultaneously marked
features. In the owner-comparable captured frame, A-0154 is complete, all six
Plane-A names are `0x63A4`, and an exact marked pixel is the opaque Plane-A
color selected by nibble 9. It is not the Plane-B pixel beneath it. Normal 0417
and `_do` have identical pixels over all six target cells; their only captured
difference is `_do`'s intentional black band at scanlines 201..218.

There is a separate, real one-frame incremental-publication defect: when the
X40/Y38 cell first enters at the far-right edge, its name is changed from blank
slot `0x297` to A-0154 slot `0x3A4` at V=123, after that cell's scanline 113 was
already fetched. This is a Class-C transient, but it cannot produce six settled
marks simultaneously and does not account for the reported `_do` extent.

## Correct Segment-2 slot

Package data is authoritative here. Records 0/1/2 use package 0, where code
`0x117` maps to slot `0x3A4` (VRAM `0x7480..0x749F`). Slot `0x468`
(`0x8D00..0x8D1F`) belongs to a later package used by the earlier Segment-11
terminal capture. During this Segment-2 capture, slot `0x468` was never written
and remained zero. It is retained in the trace as a disproven control.

The active LUT write makes the assignment at frame 322:

```
code 0x117 -> slot 0x3A4
```

The only A-0154 upload follows at frame 323. Neither slot is reused during the
relevant interval.

## Six source occurrences and screen correlation

The Palette Composer corpus contains six physical A-0154 cells. It also shows
an important precision: three are LA-0092/bank `0x003`, and three are
LA-0543/bank `0x005`; both usages resolve to the same final Line-3 name
`0x63A4` in this scene.

At captured frame 1662 (`FG=0110/0155`, `BG=0188/0155`, player
`00A8/0061`, record 3 retaining Segment-2 terrain), exact 8x8 pattern matching
against the rendered PNG gives:

| Source X/Y | Usage | Plane-A cell | VRAM name | Screen bounds |
|---|---|---:|---:|---:|
| 44/30 | LA-0543 | col 44, row 30 | `0xEF58` | 98..105, 61..68 |
| 48/30 | LA-0092 | col 48, row 30 | `0xEF60` | 130..137, 61..68 |
| 44/34 | LA-0543 | col 44, row 2 | `0xE158` | 98..105, 93..100 |
| 52/34 | LA-0092 | col 52, row 2 | `0xE168` | 162..169, 93..100 |
| 40/38 | LA-0092 | col 40, row 6 | `0xE350` | 66..73, 125..132 |
| 44/38 | LA-0543 | col 44, row 6 | `0xE358` | 98..105, 125..132 |

Five complete A-0154 bitmaps match the screenshot byte-for-byte at those
positions. The fourth is under Rastan's sprite in this automated capture, but
its staged and live name are independently `0x63A4`. This layout is the same
two/top, two/middle, two/bottom arrangement circled by Tighe, so the six
physical occurrences correlate with the six supplied marks.

## Pattern timeline

Both variants establish the package while gameplay loading has the display
off. The upload is one 16-word transfer:

| Event | 0417 | 0417_do |
|---|---:|---:|
| LUT `0x117 -> 0x3A4` | frame 322, V27/H153 | frame 322, V27/H192 |
| upload start/completion observation | frame 323, V124/H177 | frame 323, V124/H216 |
| source | `0x15FFE8` | `0x15FFF8` (variant code/data shift) |
| destination | `0x7480`, 16 words | `0x7480`, 16 words |
| display enabled after scene load | frame 425, V125/H224 | frame 425, V125/H7 |

The resulting bytes in both live terminal VRAM and the independently
reconstructed port-traffic mirror are:

```
bbb9b889b9999888996699886666998b
6666988b6666988b6677698b66776988
```

There are no zero nibbles. The reconstructed 64-KiB VRAM image compares equal
to the terminal VDP-port dump in both variants. All eight rows are complete
more than 100 frames before scene-load display enable. No partial-row scanout
is possible on this path.

## Name-word timeline

The six cells are incrementally replaced from `0x6297` (Line 3, blank slot
`0x297`) to `0x63A4` as they enter the resident ring:

| Source X/Y | Name address | frame | 0417 beam | `_do` beam | screen X/Y then | Ready before fetch? |
|---|---:|---:|---:|---:|---:|---|
| 40/38 | `E350` | 1437 | V123/H248 | V123/H90 | 304/113 | **NO**; one visible stale frame |
| 44/34 | `E158` | 1466 | V85/H205 | V85/H240 | 369/97 | offscreen |
| 44/38 | `E358` | 1466 | V85/H205 | V85/H240 | 369/129 | offscreen |
| 44/30 | `EF58` | 1466 | V85/H205 | V85/H240 | 369/65 | offscreen |
| 48/30 | `EF60` | 1488 | V207/H196 | V207/H251 | 433/67 | offscreen |
| 52/34 | `E168` | 1519 | V66/H171 | V66/H58 | 497/81 | offscreen |

Thus X40/Y38 can expose blank slot `0x297` for one frame at the right edge.
The other five names are installed while still horizontally offscreen. By the
owner-comparable frame, every name has been correct for at least 143 frames.
The pattern was ready 1,114 frames before the first name publication, so this
is not a pattern-before-name/residency race.

## Comparable 0417 versus `_do` frame

Both runs reach the same state at frame 1662. The immediately preceding
publication phase is:

| Variant | publication start | publication end | display behavior |
|---|---:|---:|---|
| 0417 | frame 1661 V199 | V217 | remains on |
| 0417_do | frame 1661 V200 | V218 | forced off V200..V218 |

No A-0154 pattern or target-name write occurs in that frame or the preceding
frame. All target scanlines are 61..132, before this late publication phase.

The PNG comparison contains exactly 5,760 differing pixels: all 320 pixels on
each scanline 201..218, and every `_do` value is black. Across all six A-0154
8x8 bounds there are zero normal-versus-`_do` pixel differences. Therefore
`_do` does not finish any A-0154 upload or name later in a way that enlarges
these six features in this mechanically identical MAME state. Its captured
difference is exclusively the intentional black timing band.

## Exact X40/Y38 compositor proof

Pixel `(69,125)` is local pixel `(3,0)` of the exact X40/Y38 A-0154 cell.
Using the captured scroll state and live VDP data:

```
screen (69,125)
  -> Plane A coordinate (323,48)
  -> Plane A cell col 40 / row 6
  -> name address 0xE350
  -> name 0x63A4
  -> slot 0x3A4, Line 3
  -> pattern pixel (3,0)
  -> nibble 9
  -> CRAM word 0x0202
  -> rendered RGB (52,0,52)
```

The independent Plane-B chain at that same screen pixel is:

```
Plane B coordinate (443,48)
  -> cell col 55 / row 6
  -> name address 0xC36E
  -> name 0x4211
  -> slot 0x211, Line 2
  -> pattern pixel (3,0)
  -> nibble 3
  -> CRAM word 0x0644
  -> expected RGB (87,87,116)
```

The captured rendered pixel is `(52,0,52)`: exactly Plane A and not Plane B.
This satisfies the prompt's required exception before discussing an opaque
appearance: the selected marked feature is an opaque A-0154 pixel, not a
transparent scanout hole.

## Classification

**Owner-marked six-at-once appearance: Class H.** At the actual displayed
frame, pattern, names, residency, and compositor fetch are correct. The exact
marked pixel is Plane A, so the asserted Layer-B-through-A model is
contradicted by direct MAME pixel evidence.

**Separate entrance transient: Class C.** X40/Y38 alone can display blank slot
`0x297` for one frame because its name publication occurs ten scanlines after
its fetch. That bounded defect deserves a separate correction task if Tighe
wants the entrance transient fixed, but it is not evidence for six persistent
holes and no patch is made here.

## Evidence

- Trace tool: `tools/mame/scripts/build0417_A0154_scanout_timing.lua`
- Normal evidence: `states/traces/build0417_A0154_scanout_timing/normal/`
- `_do` evidence: `states/traces/build0417_A0154_scanout_timing/do/`
- Normal ROM SHA-256:
  `36f8300bedc077c9b3af99c83c1b0fc9d2623e2acfa4541e7cea86f8d78b4835`
- `_do` ROM SHA-256:
  `d7fd99773ba612ffa411b06966fc89fbec8b393e75cd53367472716cfa2f8e8f`

No production or palette file was modified. No ROM was built. The counter
remains 417.
