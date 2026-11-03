# Cody Build 0416 — BG-A Fine-Scroll Residency Repair

## Scope and status

Build 0416 preserves the Build-0415 incremental background architecture and
repairs its real-Genesis visual regression. It changes the resident visual
window from 40x28 complete cells to the minimum fine-scroll-safe 41x29 cells
for both Plane A and Plane B. Collision remains a full 64-cell orthogonal
span. BG-B, generated map records (Background Phase C), sprite optimization,
scheduler work, Phase D/E, and H25 were not started.

Build 0415 remains a performance improvement but is **real-hardware visually
rejected**. Build 0416 passed the mechanical gates and requires Tighe's real
Genesis acceptance test, especially with the `_do` ROM.

## Root cause and first divergence

The 320x224 viewport contains 40x28 complete 8x8 cells only when both scroll
axes are tile-aligned. Any non-zero horizontal fine scroll exposes part of a
41st column; any non-zero vertical fine scroll exposes part of a 29th row.
Build 0415 maintained only 40x28 cells, so those partial cells retained
coherent older ring data.

The first wrong boundary was the producer/staged name-table image on both
planes:

- Plane A omitted the partial 41st column and 29th row.
- Plane B omitted the same partial cells in its independently scrolling view.
- The publisher correctly published the staged data it was given.
- The final VDP name tables therefore exposed stale but valid-looking terrain,
  mountains, or sky during fine scrolling.

The minimal failing case is a one-pixel camera movement that changes fine
scroll without crossing an 8-pixel cell boundary. No entering-strip producer
runs, but the VDP begins sampling the omitted partial row or column. The
corrected 41x29 window already contains those cells.

Andy independently confirmed this diagnosis in
`docs/design/Andy_build0415_bg_a_regression_forensic_review.md`. The review
also established that 32 resident rows and 64 resident columns are unnecessary:
only 29 rows and 41 columns can be sampled simultaneously by this viewport.

## Repair

`apps/rastan-direct/src/tilemap_hooks.s` now defines:

```asm
BG_A_RESIDENT_ROWS = 29
BG_A_RESIDENT_COLS = 41
```

Those bounds are applied consistently to:

- selector-0 Plane-A entering columns;
- the Plane-B directional entering-column producer;
- selector-1/2 Plane-A entering rows;
- Plane-A pan entering rows;
- Plane-B pan entering rows.

The 64x64 collision ring remains full-span. Existing accessor macros,
row/column dirty masks, gather buffers, and DMA publication remain intact.

## Plane-B parallax contract

Plane B does not derive its window from Plane A. Its entering-row origin uses
`ARCADE_PC080SN_SCROLL_X_BG_OFFSET`. Its entering-column cadence and physical
column use the retained Plane-B state at A5+0x10D0, A5+0x10D8, and A5+0x10EC,
including the Plane-B group/subcolumn fields.

The enhanced verifier separately passes:

- Plane A crosses while Plane B stays within its cell;
- Plane B crosses while Plane A stays within its cell;
- both planes cross together;
- fine-offset-only movement with no crossing.

No additional Plane-B correction was required beyond applying the 41x29
resident dimensions to its existing independent state.

## Gather and DMA exoneration

The dirty-column publisher scans every set bit. For each dirty column it
re-gathers 32 words from the final staged plane, immediately performs that
column's DMA, and then advances to the next bit. The scratch buffer is a
publish-time transient, not persistent producer state, so multiple dirty
columns cannot overwrite one another before publication.

Row and column producers both finish updating staging before VBlank scans the
dirty masks. Their intersection is therefore gathered from the final combined
staged state.

Column DMA remains correct and unchanged:

- Plane A destination: `VRAM_PLANE_A_BASE + column*2`;
- Plane B destination: `VRAM_PLANE_B_BASE + column*2`;
- length: 32 words;
- VDP destination autoincrement: 128 bytes;
- word `k` lands at `plane_base + column*2 + k*128`.

## Enhanced verifier

The original Build-0415 verifier encoded the same incomplete assumption as
production: it treated 40x28 complete cells as the entire visible set and did
not model the physical ring, fine-scroll exposure, or independent Plane-B
phase. It could therefore pass the broken implementation.

`tools/translation/verify_bg_a_incremental_background.py` now models the
physical 64x32 planes and explicitly requires the rejected 40x28 contract to
fail. The 41x29 contract passes horizontal and vertical fine offsets 0..7,
diagonal offsets, independent Plane-B parallax, horizontal and vertical wrap,
row/column overlap, multiple dirty columns, gather lifetime, and strided DMA.

Verifier result:

```text
PASS BG-A incremental background: broken 0415 fails; 41x29 resident windows
pass fine-scroll 0..7, independent Plane-B parallax, wrap, row/column overlap,
multi-dirty gather lifetime, and strided DMA
```

## Corrected work counts

| Entering-strip work | Build 0414 | Build 0415 rejected | Build 0416 |
|---|---:|---:|---:|
| Horizontal Plane-A visual rows | 64 | 28 | 29 |
| Horizontal Plane-B visual rows | 32 | 28 | 29 |
| Horizontal collision cells | 64 | 64 | 64 |
| Vertical Plane-A visual columns | 64 | 40 | 41 |
| Vertical Plane-B visual columns | 64 | 40 | 41 |
| Vertical collision cells where applicable | 64 | 64 | 64 |

## Performance

Apples-to-apples controlled traces used the same representative scrolling
route:

- Build 0414: `states/traces/build0415_step1_baseline0414_bfixed/`
- Build 0415 rejected: `states/traces/build0415_candidate_step1_final/`
- Build 0416: `states/traces/build0416_corrected_performance/`

All three intervals contain 22 representative pan events.

| Metric | Build 0414 | Build 0415 rejected | Build 0416 | 0416 vs 0414 | 0416 vs 0415 |
|---|---:|---:|---:|---:|---:|
| Row/map median | 153,890 | 98,298 | 100,704 | -34.56% | +2.45% |
| Worker median | 230,636 | 172,396 | 174,892 | -24.17% | +1.45% |
| IRQ median | 233,829 | 179,471 | 181,967 | -22.18% | +1.39% |

Selector-0 averages changed from 92,608 cycles in rejected 0415 to 94,034 in
0416 while retaining 64 collision cells and increasing Plane-A visual rows
from 28 to 29. Thus nearly all of Build 0415's performance gain survives. The
representative 181,967-cycle IRQ remains above the 128,009-cycle one-frame
budget; BG-A alone was not expected to clear that threshold.

No static/sprite performance regression is attributed to this repair. Tighe's
real-hardware observation remains approximately four enemies before the
diagnostic bar in Builds 0413, 0414, and 0415; the 0416 source change affects
only background resident spans.

## Gates and closeout

- rejected 40x28 model fails enhanced verifier: YES;
- corrected 41x29 model passes: YES;
- fine H/V 0..7, diagonal, physical Plane A/B visibility: PASS;
- independent Plane-B parallax cases: PASS;
- row+column coexistence and multi-dirty gather: PASS;
- 32-word/autoincrement-128 column DMA: PASS;
- collision and horizontal/vertical wrap: PASS;
- canonical gate: PASS;
- gameplay-entry gate: PASS, exceptions `0/0/0/0`;
- steady-state VDP ownership: PASS;
- generator, direct-dispatch, packed-bank, fast-enqueue, and A4/A5 checks: PASS;
- sprite completion manifest: 49 complete, 0 partial, 0 reachable unresolved;
- runtime player fallback, generic fallback, and piece adapter: `0/0/0`;
- runtime sprite descriptor and piece parsing: 0;
- Build 0416 `_c` closeout: COMPLETE, 18/18 subrounds, crash `0000`.

The Makefile's pre-existing seven-epoch labeled gate remains `FAIL`; it is not
a new Build-0416 exception or regression.

Historical closeout note: Build 0415 `_c` also reached 18/18 with fallback,
adapter, and crash all zero. That automated result does not override Tighe's
real-hardware visual rejection of Build 0415.

## Artifacts and acceptance

All five Build 0416 ROMs are 1,998,520 bytes:

| Variant | SHA-256 |
|---|---|
| canonical | `7578b5c107f42f0bfce9623607944ee4d8f56f262bc6facdf9c57fcf9b880e4b` |
| `_c` | `4373f47660d9927d3b21ae9caab2a2b364aa21cba3c090a8ffab3d2844e40e34` |
| `_d` | `c0a1012e5b1d29eeecbd8b2d3e7fec6210d392db6fbe5994a8057a1dad28418a` |
| `_do` | `bfea941adaa1eca37811ee2e921efabff860bcdc9e46a2243c6376b31e8be15c` |
| `_s` | `4025883a0784750df4226d85fcf4cc0aa94af16ae202ed6ed2da40c24fcf0e24` |

Tighe must test Build 0416 `_do` on real Genesis for horizontal, vertical,
diagonal, slow fine, and long continuous scrolling; Plane-A terrain; Plane-B
mountain/sky parallax; boundaries; enemies plus scrolling; collision; rope;
and the cave block if practical. Acceptance requires no stale/displaced plane
regions, edge strips, fine-scroll corruption, or new seams.

