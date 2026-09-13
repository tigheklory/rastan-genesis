# Cody - Independent Build 0354 VBlank Accounting Audit

## Scope and result

This is an independent, read-only timing audit of Build 0354. It changes no
production source, specification, ROM, or build number and makes no optimization
proposal. It preserves and analyzes the two existing MAME captures and the two
read-only analysis tools listed below.

The original claim that a Build 0354 publication takes approximately 258 physical
scanlines is **falsified**. That number came from applying modulo-262 arithmetic to
an 8-bit encoded V-counter byte. The authoritative MAME beam-position captures show
that the worst observed complete publication took 65,408 beam dots, or 134.033
physical scanlines. No observed publication occupied a complete 262-line NTSC
frame.

## Baseline and evidence

- Branch: `rastan-direct-proposal`
- HEAD: `7be40963c09c808b54228c8ec108e55c2873113b` (`Build 354`)
- Counter before and after this audit: `354`
- Build 0353 SHA-256:
  `28cf226cbb79edb3e937bb66df6250d6b026e33209aeff828b558d175a2ea582`
- Build 0354 SHA-256:
  `f560e27de9e28dbacb916ba5e758b4b5a1a561c103bfce513ef74d4f2875b9f4`
- Build 0354 `_s` variant SHA-256:
  `a88ef47264022ee1529b2e1f4ba31ebfc40fa5716dd42a63d4019221e41b7b20`
- Numbered Build 0354 artifacts remain preserved. Each inspected Build 0354
  variant is 1,666,744 bytes.

Authoritative read-only captures:

1. `states/traces/build0354_vblank_accounting_independent_20260908_171513/`
   - 1,800 external frames
   - 1,123 complete publications
   - 875 gameplay publications
   - Raw CSV: 2,424,954 bytes
   - Raw CSV SHA-256:
     `ff423237f1c0993ea3d91b5616231b5fefab1534d52c021c8c1ed903137620d4`
2. `states/traces/build0354_vblank_accounting_independent_20260908_172536_stationary/`
   - 1,500 external frames
   - 997 complete publications
   - 749 gameplay publications
   - 237 stationary gameplay publications
   - Raw CSV: 2,070,811 bytes
   - Raw CSV SHA-256:
     `1a587a60f262cfcd0a82f36e12f9c63560d706433b22a2ff09c13b323d40c161`

Preserved tools:

- `tools/mame/scripts/build0354_vblank_independent_audit.lua`
- `tools/mame/scripts/reduce_build0354_vblank_audit.py`

The reducer was rerun only against the preserved captures. Its vertical
representative selection now first considers vertical publications with a
substantive Plane A section (`plane_a > 1000` beam dots), falling back to the full
vertical category only if none exists. The selected vertical representative has a
6,423-dot Plane A publication.

Generated reduction products:

- First capture `vblank_accounting_independent.json`: 21,734 bytes, SHA-256
  `62ba7d927171d0654be2b9ee62f1e4840a8d57fae57b6ba84e59b14a6352b969`
- Second capture `vblank_accounting_independent.json`: 21,724 bytes, SHA-256
  `b12560f5fa33b01b31956e18bb53a6328b8f16eeb2c749a01def35f6acae974e`
- Each capture also contains a regenerated
  `representative_frames_independent.csv`.

## Phase 0 and architecture

Task classification: **INFRASTRUCTURE / INDEPENDENT VALIDATION**.

Relevant prior findings include KF-011 (arcade Level-6/VBlank ownership), KF-019
(sampled-PC limitations), KF-047 (historical candidate path), KF-052 (older VINT
breakdown), KF-053 (double-sync removal), KF-054 (unsafe commit-first ordering),
KF-068 (interrupt-mask context), KF-070 (12-entry residency queue), KF-074
(native lanes bypass the old scanner), and KF-077 (native gameplay path).
OPEN-001, OPEN-017, OPEN-018, and OPEN-024 are context only; this audit neither
opens nor closes an issue. No contradiction with a CONFIRMED or STRONG finding was
identified. KNOWN_FINDINGS impact is Option A: no new indexed finding.

The audit observes the existing Genesis publication path. It does not alter arcade
control flow, VDP ownership, native Plane A/B publication, native sprite
publication, or any compatibility boundary. Architecture compliance is confirmed.

## Why the 8-bit V-counter arithmetic was invalid

`VC_MARK` reads the VDP horizontal/vertical counter port at `HW_ADDRESS
0x00C00008`, shifts the word right by eight, and stores only the resulting byte in
Genesis-WRAM `vblank_vc` at `0x00FF6180` and following bytes. It therefore records
only the 8-bit NTSC V-counter encoding. It does not record H position, a ninth
vertical bit, a frame/epoch identifier, or elapsed time.

In 224-line NTSC mode, the observed physical-line encoding is not a monotonic
0-through-261 counter:

- physical lines 0 through 234 expose `0x00` through `0xEA`;
- physical lines 235 through 261 expose `0xE5` through `0xFF`;
- the encoded counter therefore jumps backward from `0xEA` to `0xE5`;
- values `0xE5` through `0xEA` occur at two physical line positions.

Consequently, `(end_byte - start_byte) % 262` mixes an 8-bit encoded value with a
262-line physical modulus. It cannot distinguish the counter discontinuity, the
duplicated encoded values, frame crossings, multiple frame crossings, or
horizontal phase.

For example, the prior marker sequence included `235` followed by `231`. The first
value (`0xEB`) corresponds to physical line 241. The later `0xE7` can correspond to
physical line 231 or 237 in a subsequent frame. Depending on that duplicate branch,
the whole-line interval is 252 or 258 lines before horizontal phase is considered;
the byte stream cannot select between them. Therefore the prior approximately
258-line reconstruction is not physical elapsed-time evidence.

The `_s` diagnostic is also an endpoint indicator rather than a duration timer. It
reads one V-counter byte at the end of servicing, stores an active-line value when
the byte is below `0xE0`, maps later encodings to zero, and retains a running peak.
The displayed `223` means the largest retained endpoint byte was active line 223;
it does not mean the publisher lasted 223 scanlines. A displayed zero similarly
does not prove that publication fit wholly within VBlank.

## Correct physical beam-position accounting

The read-only Lua harness records MAME's physical beam Y and X positions at every
publisher and section boundary. For NTSC Genesis timing used by this capture:

- total physical lines per frame: 262
- beam dots per line (`htotal`): 488
- beam dots per frame: 127,856
- frame rate: 59.922743404 Hz
- frame duration: 16,688.1545 microseconds
- scanline duration: 63.695246 microseconds
- one beam dot: 130.523 nanoseconds
- nominal Genesis 68000 clock: 7,670,453 Hz
- one beam dot: approximately 1.0011709 equivalent 68000 cycles
- 38-line VBlank: approximately 2,420.419 microseconds or 18,565.7
  equivalent 68000 cycles

For each publication, the reducer forms the physical beam position
`beam_y * 488 + beam_x`. It maintains a publication-local epoch and adds
`262 * 488` whenever the physical position decreases. Elapsed time is the
difference between these monotonic expanded positions. This method handles frame
wraps and horizontal phase and does not depend on the debugger's external frame
counter advancing while execution is stopped.

The reported cycle values below are beam-time conversions to equivalent 68000
cycles, not direct CPU-cycle samples.

## Instrumented publication sequence

The Build 0354 publisher marks the fixed sequence:

1. palette
2. tile worklist
3. Plane B
4. Plane A
5. sprites
6. scroll

Seven markers bracket these six calls. The nominal marker body is about 54 68000
cycles (`MOVE.W` absolute-long, `LSR.W #8`, and `MOVE.B` absolute-long). Measured
total marker time has a 379-dot median, or 0.777 scanline and approximately 49.5
microseconds. The reducer excludes marker bodies from component durations. The
small remainder between component plus marker totals and publisher total is wrapper
or otherwise uninstrumented overhead.

## Exact representative publications

The stationary, horizontal, vertical, and sprite-heavy representatives come from
the second capture. The worst observed publication comes from the first capture.
Percentages are shares of the complete publisher interval.

### Stationary representative

- External frame 546; entry beam line 190; exit beam line 244
- Emitted SAT entries: 28
- Pattern worklist/actual DMA entries: 0/0
- Total: 26,572 dots; 54.451 lines; 3,468.3 us; 26,603 equivalent cycles

| Section | Dots | Lines | Microseconds | Equivalent cycles | Total share |
|---|---:|---:|---:|---:|---:|
| Palette | 49 | 0.100 | 6.4 | 49 | 0.18% |
| Tiles | 41 | 0.084 | 5.4 | 41 | 0.15% |
| Plane B | 45 | 0.092 | 5.9 | 45 | 0.17% |
| Plane A | 702 | 1.439 | 91.6 | 703 | 2.64% |
| Sprites | 24,548 | 50.303 | 3,204.1 | 24,577 | 92.38% |
| Scroll | 454 | 0.930 | 59.3 | 455 | 1.71% |

Sprite section: pattern DMA 75 dots (0.154 lines), palette fixup/routing 23,544
dots (48.246 lines), fixed SAT DMA 490 dots (1.004 lines), and other sprite work
439 dots (0.900 lines). Markers consumed 371 dots (0.760 lines).

### Horizontal-movement representative

- External frame 778; entry beam line 136; exit beam line 229
- Emitted SAT entries: 46
- Pattern worklist/actual DMA entries: 0/0
- Total: 45,437 dots; 93.109 lines; 5,930.6 us; 45,490 equivalent cycles

| Section | Dots | Lines | Microseconds | Equivalent cycles | Total share |
|---|---:|---:|---:|---:|---:|
| Palette | 42 | 0.086 | 5.5 | 42 | 0.09% |
| Tiles | 50 | 0.102 | 6.5 | 50 | 0.11% |
| Plane B | 46 | 0.094 | 6.0 | 46 | 0.10% |
| Plane A | 694 | 1.422 | 90.6 | 695 | 1.53% |
| Sprites | 43,412 | 88.959 | 5,666.3 | 43,463 | 95.54% |
| Scroll | 454 | 0.930 | 59.3 | 455 | 1.00% |

Sprite section: pattern DMA 75 dots (0.154 lines), palette fixup/routing 42,391
dots (86.867 lines), fixed SAT DMA 500 dots (1.025 lines), and other sprite work
446 dots (0.914 lines). Markers consumed 379 dots (0.777 lines).

### Vertical/jump-movement representative

- External frame 1,227; entry beam line 10; exit beam line 57
- Emitted SAT entries: 19
- Pattern worklist/actual DMA entries: 0/0
- Substantive Plane A publication: 6,423 dots
- Total: 22,903 dots; 46.932 lines; 2,989.4 us; 22,930 equivalent cycles

| Section | Dots | Lines | Microseconds | Equivalent cycles | Total share |
|---|---:|---:|---:|---:|---:|
| Palette | 49 | 0.100 | 6.4 | 49 | 0.21% |
| Tiles | 41 | 0.084 | 5.4 | 41 | 0.18% |
| Plane B | 45 | 0.092 | 5.9 | 45 | 0.20% |
| Plane A | 6,423 | 13.162 | 838.3 | 6,431 | 28.04% |
| Sprites | 15,157 | 31.059 | 1,978.3 | 15,175 | 66.18% |
| Scroll | 454 | 0.930 | 59.3 | 455 | 1.98% |

Sprite section: pattern DMA 75 dots (0.154 lines), palette fixup/routing 14,127
dots (28.949 lines), fixed SAT DMA 500 dots (1.025 lines), and other sprite work
455 dots (0.932 lines). Markers consumed 371 dots (0.760 lines).

This representative establishes vertical/jump movement with real Plane A work. It
does not establish a cave or drop-state timing case.

### Sprite-heavy representative

- External frame 881; entry beam line 55; exit beam line 173
- Emitted SAT entries: 51
- Pattern worklist/actual/cancelled entries: 10/10/0
- Pattern bytes transferred: 1,280
- Total: 57,725 dots; 118.289 lines; 7,534.4 us; 57,793 equivalent cycles

| Section | Dots | Lines | Microseconds | Equivalent cycles | Total share |
|---|---:|---:|---:|---:|---:|
| Palette | 41 | 0.084 | 5.4 | 41 | 0.07% |
| Tiles | 41 | 0.084 | 5.4 | 41 | 0.07% |
| Plane B | 45 | 0.092 | 5.9 | 45 | 0.08% |
| Plane A | 694 | 1.422 | 90.6 | 695 | 1.20% |
| Sprites | 55,700 | 114.139 | 7,270.1 | 55,765 | 96.49% |
| Scroll | 454 | 0.930 | 59.3 | 455 | 0.79% |

Sprite section: pattern DMA 7,874 dots (16.135 lines), palette fixup/routing
46,880 dots (96.066 lines), fixed SAT DMA 500 dots (1.025 lines), and other sprite
work 446 dots (0.914 lines). Markers consumed 379 dots (0.777 lines).

### Worst observed complete publication

- First-capture external frame 775; entry beam line 233; exit beam line 105 of
  the following physical frame
- Emitted SAT entries: 46
- Pattern worklist/actual/cancelled entries: 2/2/0
- Pattern bytes transferred: 256
- Total: 65,408 dots; 134.033 lines; 8,537.3 us; 65,485 equivalent cycles
- Frame share: 51.16%

| Section | Dots | Lines | Microseconds | Equivalent cycles | Total share |
|---|---:|---:|---:|---:|---:|
| Palette | 41 | 0.084 | 5.4 | 41 | 0.06% |
| Tiles | 49 | 0.100 | 6.4 | 49 | 0.07% |
| Plane B | 18,472 | 37.852 | 2,411.0 | 18,494 | 28.24% |
| Plane A | 693 | 1.420 | 90.5 | 694 | 1.06% |
| Sprites | 44,957 | 92.125 | 5,867.9 | 45,010 | 68.73% |
| Scroll | 446 | 0.914 | 58.2 | 447 | 0.68% |

Sprite section: pattern DMA 1,640 dots (3.361 lines), palette fixup/routing
42,381 dots (86.846 lines), fixed SAT DMA 490 dots (1.004 lines), and other sprite
work 446 dots (0.914 lines). Markers consumed 390 dots (0.799 lines).

This publication entered at line 233. Plane B crossed into the next frame's active
display, and the two sprite pattern transfers also occurred during active display.
The measured total remains far below a complete 262-line frame.

## Distribution and publisher frequency

First capture, gameplay publications:

- Total: minimum 3,860; median 28,396; p95 47,868; maximum 65,408 dots
- Sprite: median 24,568; p95 43,393; maximum 49,895 dots
- Plane B: median 45; p95 18,471; maximum 18,472 dots
- Plane A: median 701; p95 6,423; maximum 6,431 dots

Second capture, gameplay publications:

- Total: median 26,592; p95 50,182; maximum 57,881 dots
- Sprite: median 24,556; p95 46,514; maximum 55,700 dots
- Plane B: median 45; p95 1,590; maximum 18,472 dots
- Plane A: median 701; p95 6,421; maximum 6,431 dots

Publication is not synonymous with external frame rate. In the first capture,
1,123 publisher invocations occurred across 1,800 external frames (62.39%). Of all
publisher entries, 759 of 1,123 (67.59%) occurred during active display. Among the
875 gameplay publications, 751 (85.83%) entered during active display and 124
entered during VBlank.

In the second capture, 997 invocations occurred across 1,500 external frames
(66.47%). Among 749 gameplay publications, 657 (87.72%) entered during active
display and 92 entered during VBlank. The second capture contains 237 stationary
gameplay publications and independently confirms that long, sprite-dominated
publication is not dependent on continuous player movement.

These data prove that the publisher does not execute once per external frame and
that its entry is not confined to VBlank. The visible `_do` black-bar behavior is
qualitatively consistent with publication extending through active display, but it
does not validate the invalid 258-line arithmetic.

## Sprite publication breakdown

### Pattern DMA

The pattern worklist is bounded to 12 entries. Across the captures, its gameplay
median is zero entries; p95 is eight entries in the first capture and five in the
second; the maximum is 12. Each actual entry transfers 64 words (128 bytes).
Cancelled entries have a maximum of zero in these captures, so no cancellation
churn was observed.

Measured per-entry intervals are 408 to 417 beam dots, with a 417-dot median,
equivalent to approximately 0.836 to 0.855 scanline or 53.3 to 54.4 us per 128-byte
call. The same range was observed for active-display and VBlank calls. This is
elapsed PC-to-PC beam time, including any MAME-modeled DMA stall and call overhead;
the capture does not independently separate those two contributions.

No same-frame duplicate code or duplicate slot entries were found. No exact
consecutive `(code, slot)` worklist repeats were found. The same code appeared in a
different slot between consecutive gameplay publications 57 times in the first
capture and 21 times in the second; this alone does not prove waste because the
existing residency and slot lifecycle may require it.

### Palette fixup and routing

The dominant measured sprite sub-cost is per-emitted-SAT-entry palette fixup. The
native path loops over `pc090oj_emitted_count`; each non-forced entry invokes the
palette selector, which invokes `palette_route_lookup`. That lookup linearly scans
the palette-route table. The maximum observed palette-fixup interval was 47,916
dots, or 98.19 scanlines.

Across the combined 1,624 gameplay publications, emitted SAT entry count and
palette-fixup duration have Pearson correlation `r = 0.990215`. A descriptive
least-squares fit is 989.56 beam dots, or 2.028 scanlines, per emitted entry. This
slope is not asserted as a constant per-entry cost because route-table scan depth
and forced-line cases vary.

Representative medians further show the relationship:

| Emitted entries | Median palette-fixup dots | Median lines | Samples |
|---:|---:|---:|---:|
| 20 | 15,172.0 | 31.090 | 280 |
| 28 | 23,545.5 | 48.249 | 318 |
| 41 | 36,399.0 | 74.588 | 25 |
| 46 | 42,382.0 | 86.848 | 43 |
| 51 | 46,880.5 | 96.067 | 2 |

This establishes palette routing as the dominant observed gameplay sprite hotspot,
not pattern DMA.

### SAT DMA

When a sprite frame is ready, the existing path transfers a fixed 80-entry SAT:
320 words or 640 bytes. The measured interval is approximately 490 to 509 beam
dots, or about 1.00 to 1.04 scanlines. It is therefore a small, bounded portion of
the sprite section compared with per-entry palette fixup.

## Facts, inference, and unsupported cases

### Proven by source and the preserved captures

- `VC_MARK` stores only an 8-bit V-counter encoding.
- Modulo-262 subtraction of those bytes is not physical elapsed-time accounting.
- MAME physical `beam_y`/`beam_x` accounting handles horizontal phase and frame
  wrap for these complete publications.
- The maximum observed complete publication is 65,408 dots or 134.033 scanlines.
- No observed complete publication consumes a full 262-line frame.
- Sprite publication dominates the representative gameplay publications, ranging
  from 66.18% to 96.49% in the selected category representatives and 68.73% in
  the overall worst publication.
- Pattern DMA is bounded to 12 entries and commonly zero.
- Fixed 640-byte SAT DMA is approximately one scanline.
- Palette fixup/routing dominates measured sprite time and strongly tracks emitted
  SAT entry count.
- Publisher entry frequently occurs during active display.
- Only 1,123 publications occurred over 1,800 external frames in the first capture.
- The 237 stationary publications in the second capture independently confirm the
  central timing result.

### Inference, explicitly bounded

- Repeated linear `palette_route_lookup` scans are the source-level mechanism most
  consistent with the measured per-emitted-entry palette-fixup scaling. The timing
  capture brackets the palette-fixup region but does not individually timestamp
  each comparison in each scan.
- The `_do` black bars are consistent with publication during active display, but
  they are qualitative evidence only.

### Unsupported by these captures

- These captures do not establish cave-specific or drop-specific publication
  behavior.
- They do not prove that every possible gameplay publication is below the observed
  maximum; 134.033 lines is the maximum in the sampled evidence, not a universal
  static upper bound.
- They do not isolate raw VDP DMA stall from surrounding CPU instruction overhead.
- They do not establish whether changing any measured hotspot would be safe or
  beneficial. No optimization boundary is proposed here.

## Conclusion

The hypothesis that Build 0354 VBlank publication takes approximately 258 physical
scanlines is **falsified**. The value came from invalid arithmetic on an 8-bit,
non-monotonic NTSC V-counter encoding. Physical beam accounting finds a worst
observed complete publication of approximately 134 scanlines, about 51.16% of one
NTSC frame.

The broader concern that publication is long and often overlaps active display is
supported. Sprite publication is the dominant measured gameplay section. Within
sprites, repeated per-emitted-entry palette fixup and linear palette-route lookup
are the dominant measured hotspot; pattern DMA is bounded and commonly absent, and
the fixed SAT DMA is approximately one scanline. These are audit findings only.
No optimization is recommended or implemented.

Build 0355 is neither required nor authorized by this audit. `D00462` is unchanged
and remains outside this timing task.

## Change and preservation statement

- Production source changed: NO
- Specification changed: NO
- ROM changed or produced: NO
- Build counter changed: NO (`354`)
- Numbered ROM deleted or overwritten: NO
- Emulator rerun: NO
- Existing read-only reducer rerun against preserved evidence: YES
- Durable files changed by this completion: this report and `AGENTS_LOG.md`

