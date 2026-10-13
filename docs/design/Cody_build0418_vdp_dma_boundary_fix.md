# Cody — Build 0418 VDP DMA Boundary Fix

Date: 2026-10-13  
Baseline: Build 0417  
Produced: complete Build 0418 family  
Real-Genesis acceptance: **ACCEPTED by Tighe on real Genesis (2026-10-13)**

## Resume and scope

This work resumed the existing dirty worktree after the interrupted Build 0418
implementation. Correct partial edits were retained and completed in place. No
palette mapping, pattern pixels, background architecture, scheduler, collision,
scroll, or gameplay behavior was changed.

The established root cause was not reinvestigated: Build 0417 uploaded A-0154
from `0x15FFE8` as one 32-byte DMA, crossing the Genesis VDP's 128-KiB source
bank after 24 bytes. Build 0417 `_do` used `0x15FFF8` and crossed after 8 bytes.
Real hardware wrapped each tail within the old source bank.

## Files changed for Build 0418

- `apps/rastan-direct/src/dma.s`: checked autoincrement-2 ROM DMA path.
- `apps/rastan-direct/src/scene_load.s`: 32-byte PC080SN corpus alignment.
- `apps/rastan-direct/src/pc090oj_hooks.s`: ROM-backed sprite-pattern DMA uses
  the checked path.
- `tools/translation/verify_vdp_dma_boundary.py`: deterministic split and
  linked-layout verifier.
- `apps/rastan-direct/Makefile`: runs the new verifier before publication.
- This report, `KNOWN_FINDINGS.md`, and `AGENTS_LOG.md`: durable evidence.

Other pre-existing dirty-tree production changes are the accepted Build
0414–0417 campaign state and were neither discarded nor reworked here.

## Generic DMA implementation

`vdp_dma_words_to_vram` / `dma_words_to_vram` retains its public contract:
`D0` is a VRAM byte destination, `D1` is the 16-bit word count, and `A0` is an
even 68000 source. It preserves `D0/A0`, clobbers `D1-D3/A1`, forces VDP
autoincrement 2, and returns after all requested words have transferred.

The fast check converts the source to a VDP word address and adds the nonzero
word count to its low word. No carry means the existing single-DMA programmer
runs unchanged. Carry with a zero result means the range ends exactly at the
boundary and also remains one DMA. A zero `D1` retains the hardware meaning of
`0x10000` words and is one DMA only at a bank-aligned source.

On a true crossing, the routine computes:

```text
first_words = (0x20000 - (source & 0x1ffff)) / 2
remaining   = total_words - first_words
```

It programs and triggers the first DMA, then explicitly reprograms all DMA
source/length/destination registers for the second DMA using:

```text
second source      = original source + first_words * 2
second destination = original destination + first_words * 2
```

The second source is therefore the real next ROM address, never the VDP's
wrapped bank address. The 16-bit hardware count represents at most `0x10000`
words, so one transfer can cross at most one 64-Kword source boundary; two
chunks are sufficient for the full legal API contract.

The ordinary nonzero, non-crossing path adds six 68000 instructions before the
unchanged DMA programmer: `move.l`, `lsr.l`, `tst.w`, untaken `beq`, `add.w`,
and taken `bcc`. Standard 68000 timing is approximately 38 cycles. It still
triggers exactly one DMA and performs no copying or buffering.

## Bounded caller audit

| Caller | Source and length | Route / result |
|---|---|---|
| Initial Plane B/A names (`fg_tile_cache.s:125..132`) | WRAM staging, 4096 words each | Checked autoinc-2 entry; cannot cross the WRAM end in its bounded allocation; one DMA normally. |
| Fixed and transition PC080SN patterns (`fg_tile_cache.s:347..355`, `524..531`) | ROM corpus, 16 words | Checked entry. Corpus alignment proves every tile is non-crossing and one DMA. |
| Initial package Plane B/A names (`fg_tile_cache.s:548..556`) | WRAM staging, 4096 words | Checked entry; one DMA normally. |
| Dirty Plane B/A rows (`vdp_comm.s:294..334`) | WRAM staging, 64 words | Checked entry; bounded WRAM source. |
| PC090OJ sprite patterns (`pc090oj_hooks.s:3097..3109`) | Arbitrary ROM pattern source, 64 words | Changed from unchecked `noai` to checked autoincrement-2 entry. Non-crossing is one DMA; a crossing splits safely. |
| SAT (`pc090oj_hooks.s:3143..3150`) | WRAM SAT buffer, 320 words | Existing `dma_words_to_vram_noai`, deliberately unchanged. |
| Plane B/A columns (`tilemap_hooks.s:4260..4274`, `4330..4344`) | 64-byte WRAM gather, 32 words, VDP autoincrement 128 | Existing specialized `noai` path, deliberately unchanged; routing it through autoincrement 2 would be wrong. |
| Palette | WRAM palette staging, dedicated CRAM routine | Not a ROM-source VRAM case; unchanged. |

After the sprite reroute, every `dma_words_to_vram_noai` caller is a bounded
WRAM source. The specialized entry intentionally does not claim generic ROM
boundary safety because its column callers use a different destination step.

## PC080SN alignment and A-0154

`.balign 32` is immediately before `genesistan_pc080sn_tile_rom`; padding is
only before the label. Tile addressing remains `base + code*32`, with no bytes
or padding inserted inside the 524,288-byte corpus.

| Layout | Corpus base | A-0154 (`code 0x117`) source | Outcome |
|---|---:|---:|---|
| 0417 normal | `0x15DD08` | `0x15FFE8` | crossed after 24 bytes |
| 0417 `_do` | `0x15DD18` | `0x15FFF8` | crossed after 8 bytes |
| 0418 normal | `0x15DD80` | `0x160060` | aligned, one 16-word DMA |
| 0418 `_do` | `0x15DD80` | `0x160060` | aligned, one 16-word DMA |

All five final layouts are aligned and non-crossing:

| Variant | Corpus base | A-0154 source | Bytes to next boundary |
|---|---:|---:|---:|
| normal | `0x15DD80` | `0x160060` | `0x1FFA0` |
| `_c` | `0x15DF60` | `0x160240` | `0x1FDC0` |
| `_d` | `0x15DDA0` | `0x160080` | `0x1FF80` |
| `_do` | `0x15DD80` | `0x160060` | `0x1FFA0` |
| `_s` | `0x15DE20` | `0x160100` | `0x1FF00` |

Because `0x20000` is divisible by 32, every `base + code*32` address is
32-byte aligned and no individual PC080SN tile can cross a source bank.

## Deterministic verification

`verify_vdp_dma_boundary.py` validates the assembly ownership/routing, linked
corpus address, every one of the 16,384 aligned tile starts, A-0154's one-DMA
layout, and reconstructed contiguous bytes for these cases:

| Source / 32-byte length | Expected chunks | Result |
|---|---|---|
| boundary - 32 | 32 | PASS |
| boundary - 24 | 24 + 8 (`12 + 4` words) | PASS |
| boundary - 8 | 8 + 24 (`4 + 12` words) | PASS |
| boundary | 32 | PASS |
| linked A-0154 | 32 (`16` words) | PASS |

The source corpus SHA-256 remains
`9c7ceddae22b34c6a31904c5d9caa8410d672cf4d4ffea774387bda4acec6964`.
A-0154's 32 bytes in Build 0417, the generated corpus, and every Build 0418
artifact are identical:

```text
bbb9b889b9999888996699886666998b6666988b6666988b6677698b66776988
```

`specs/palette_decisions.json` was unchanged (SHA-256
`eee0171ff16317ed4239bdeab4e4a11fdcbf931a2ed806196f7d5697e62b907e`).

## Build and gates

All five artifacts are 1,998,520 bytes:

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0418.bin` | `816675e9e008833c9d30fe266485b26eae2dad26ef7b210090a75ced8105af54` |
| `rastan_direct_video_test_build_0418_c.bin` | `b90a27ea2e76c9b992672ed7d58df2314541a3b087e51517ad7b7193b14e6995` |
| `rastan_direct_video_test_build_0418_d.bin` | `2393b681e23d44cf7e266c8372130d86762a8357d9c685f5a50637a178b6b4f5` |
| `rastan_direct_video_test_build_0418_do.bin` | `dd8e0930e69512b2550bcebc2038f7f4caf5170cefd1e99f86130d2cdf188ef9` |
| `rastan_direct_video_test_build_0418_s.bin` | `3a22badb001350de5cec07bed9da093ba1da53fe11007ce1b7fbfd432b0633fa` |

- New VDP DMA boundary/alignment gate: PASS.
- Full-span background coherence gate: PASS.
- Boot guards: PASS for all family builds.
- Canonical gate: PASS.
- Gameplay-entry gate: PASS; zero address/bus/illegal/crash-handler events.
- Mandatory 30-second Genesis NTSC MAME trace: completed, no unmapped access.
- Full family presence gate: PASS.
- Standing seven-epoch route gate: FAIL after observing only the initial epoch.
  This is the same recorded status as Builds 0414–0417 and was not broadened
  into this source-boundary task.

## Real-Genesis acceptance checklist

- [x] Normal 0418: all six Segment-2 A-0154 holes are gone.
- [x] 0418 `_do`: all six A-0154 holes are gone.
- [x] No new Layer-A/Layer-B corruption attributable to this fix was reported.
- [x] No sprite, palette, or gameplay regression attributable to this fix was reported.
- [x] `_do` black bands are recognized as expected and separate.

Tighe's real-hardware result formally accepts Build 0418 as the forward
baseline and closes both the six-hole A-0154 symptom and its generic
128-KiB-source-boundary DMA defect. This acceptance does **not** close the
separate IRQ6/full-frame overrun, active-display DMA, `_do` forced-black
bands, one-frame entering-cell transient, or background-runtime-cost work.

Active-display DMA scheduling, `_do` bands, and the one-frame entrance name
transient were not changed in Build 0418.
