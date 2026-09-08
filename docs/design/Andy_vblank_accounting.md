# Andy — VBlank Publication Accounting (measured, Build 0354)

**Task:** VBlank/performance accounting (measurement, not attribution-by-assumption).
**Runtime C:** NO. Builds 0348–0354 preserved.

## Method
Two measurements, both read-only at the ROM level:
1. **Total overrun** — the existing `_s` (score-metric) diagnostic reads the VDP V-counter at the end
   of `_vblank_service` and displays the worst-case overrun in scanlines (0 = fit in VBlank; N = bled
   into active line N). Read from `0xFF011E` during driven gameplay.
2. **Per-commit attribution (Build 0354)** — added V-counter checkpoints (`vblank_vc[0..6]`, macro
   `VC_MARK`) around each of the six commits in `dma_publish_frame`. A read-only trace reads the
   marks; consecutive deltas (mod 262) = scanlines each commit consumed.

`frame_done`-sampled dirty masks / worklist counts are **not** used for attribution — they are cleared
or reset by the VBlank commit before the sample (confirmed: `bg_row_dirty`/`fg_row_dirty` and
`pc090oj_tile_dma_count` all read near-zero at `frame_done` yet the phase overruns).

## Result 1 — total overrun (severe)
Driven gameplay + rightward scroll (0353_s), `0xFF011E` peak-overrun metric:
`173 → 189 → 222 → 223 (pinned)`. Active display = 224 lines. **The publication phase overruns by
nearly a full frame** — this is the slowness and the large `_do` display-off black bars.

## Result 2 — per-commit attribution (0354, worst frame = 261 scanlines)
| commit (`dma_publish_frame`) | scanlines |
|---|---|
| `vdp_commit_palette` | 0 |
| `vdp_commit_tiles_if_dirty` | 0 |
| `vdp_commit_bg_strips_if_dirty` (Plane B) | 0 |
| `vdp_commit_fg_narrow_strips` (Plane A) | **2** |
| `vdp_commit_sprites_vram` (sprites) | **258** |
| `vdp_commit_scroll` | 1 |

**The sprite commit is ≈98% of the overrun. Plane A is 2 lines; Plane B / palette / tiles / scroll
are ~0.** The Plane-A column work (0350) and the resolver work (0351–0353) are **not** the perf
problem — this is measured, not assumed.

## Where inside the sprite commit
`vdp_commit_sprites_vram` (`pc090oj_hooks.s:2003`) = `.Lvcs_tile_dma` (a bounded
`pc090oj_tile_dma_count` worklist of 128-byte sprite-cell DMAs) + `.Lnative_pal_fixup`
(≤80-sprite loop, ~30-50 lines of CPU) + `.Lvcs_sat_dma` (640-byte SAT DMA). CPU work alone accounts
for only ~40-50 lines, so the remaining ~200 lines is **DMA volume + stall**:
- `pc090oj_tile_dma_count` is **undercounted** at `frame_done` (the worklist resets right after the
  commit); the true per-frame cell count on heavy frames is the prime suspect.
- once the phase overruns VBlank, the remaining sprite DMAs run **during active display**, where VRAM
  DMA is throttled (~205 bytes/line) — a compounding feedback that turns a moderate overshoot into a
  full-frame stall.

## Proposal (performance work — next task, not this one)
Target the **sprite subsystem only**; leave Plane A/B/palette/scroll alone (measured negligible).
1. Finer measurement first (Build 0355): add `VC_MARK`s **inside** `vdp_commit_sprites_vram`
   (after tile-DMA, after pal_fixup, after SAT-DMA) and capture the **true pre-reset**
   `pc090oj_tile_dma_count` in-ROM, to split the 258 lines among tile-DMA / pal_fixup / SAT and
   confirm the cell volume.
2. Then reduce whichever dominates — most likely bound/incrementalize sprite **pattern** uploads
   (don't re-DMA unchanged cells; the worklist should already aim at this — verify it isn't
   re-uploading resident cells), and ensure the sprite DMA fits the VBlank window so it never spills
   into active display (which is what makes it catastrophic).

## Build 0354
Diagnostic-instrumented build (adds the `VC_MARK` V-counter checkpoints to `dma_publish_frame`;
negligible cost, no rendering change). release SHA — see ledger; `[canonical=PASS entry=PASS
epoch=FAIL]` (fragile synthetic gate; non-blocking); 30s smoke exceptions=0. Builds 0348–0354 all
preserved. `vblank_vc` at `0xFF6180`.

## Status
Accounting delivered: overrun is severe (~a full frame) and is **the sprite commit**, not Plane A.
`D00462` crash unchanged/separate. Next: Build 0355 finer sprite-commit split, then the reduction.
