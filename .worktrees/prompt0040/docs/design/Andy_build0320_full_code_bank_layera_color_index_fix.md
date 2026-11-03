# Andy — Build 0320 Full (code,bank) Layer-A Color-Index Fix

**Type:** implementation/verification. EXTENDING. Pattern compiler pending; routing reverted. Line 2 protected.

## 1–4. 0319 rejection + shape-vs-index + why palette-line move failed
Tighe rejected 0317-0319: Layer-A shapes right, colors wrong; Rastan regressed. A 4bpp pattern stores
palette ENTRY NUMBERS per pixel, so a tile can have correct shape but wrong colors when pixels reference the
wrong target index. Moving the same palette from line 1 to line 3 cannot change tile colors (same indices +
same palette contents = same colors), and my supporting CRAM probe was invalid (scene_id=0, attract not
gameplay). Root variable = the OFFLINE source_index->target_index mapping, specifically the 64 dominant-mapped
codes.

## 5. Pairwise good/green evidence (proven from corpus, not screenshots)
64 tile codes produce DIFFERENT final 32-byte patterns per source bank, but Build 0316's code-indexed region
holds ONE (dominant) pattern per code — so the non-dominant bank's cells get wrong indices = wrong colors,
right shape. Examples:
- code 0x308: bank 0x01A (seg 11) final `1377a89d` (= 0316 dominant); bank 0x01C (segs 3,10,11) correct
  final `c31797db` but 0316 renders it as `1377a89d` -> WRONG.
- code 0x309: bank 0x01A `c0caef2c` (dominant) vs bank 0x01C correct `f0ea532e` -> WRONG for 0x01C cells.
- code 0x30A: bank 0x01A `9fc575bd` (dominant) vs bank 0x01C correct `cf70360d` -> WRONG for 0x01C cells.
Total codes with divergent (code,bank) finals (the visible dominant-map bug): **64**.

## 6–7. Multi-map + (code,bank) key
1576 usages, 1314 codes, 64 multi-map codes, 1576 distinct (code,bank) keys, 0 conflicts, 0 missing used
indices. (code,bank) is the complete unambiguous key; dominant maps must go to 0.

## 8–11. Full (code,bank) implementation (design; NOT yet built)
- Target asset `build/rastan-direct/build0320_editor_layera/patterns.bin`: final reindexed 32-byte patterns
  per (code,bank), exact-dedup by final bytes; manifest (code,bank)->target_id/offset/SHA/index_map/records.
- Boundary compiler: retain source bank through record/package model (stop collapsing to code); allocate
  final target-pattern identities into the Plane-A slot range; seven epochs + overlap packages preserved;
  Plane-A cap 484, drops 0; Plane-B unchanged.
- Runtime O(1) variant selector: 1250 normal codes keep code->slot; the 64 variant codes use a compact
  variant descriptor (code -> per-bank slot) selected from the cell's already-available bank at name-word
  generation. No runtime pixel transform / no editor data / no search.
- DMA source becomes the generated target patterns.bin (not the code-indexed region), so the runtime copies
  finished bytes.

## 12–13. Reverts done in Build 0320
0317-0319 palette routing reverted to Build-0316: `palette_hooks.s` PROUTE_FG_LINE 3->1, route FG bank3->line
1, sprites bank51->line 3; `vdp_comm.s` reassert restored to the cache-valid-gated Build-0316 form; the 0319
direct forced Line-3 write removed. Rastan routing thus returns to Build-0316 behavior (regression undone).

## 14. Builds
- 0317-0319: rejected experiments, preserved.
- 0320: 0317-0319 palette-routing REVERT (Rastan un-regressed; == Build-0316 colors, dominant bug still
  present). Built, seven-epoch gate PASS, 30s MAME no crash. Disposition: ROUTING-REVERT BASELINE.
  SHA de137338fcdfe2e8, size 1670840, counter 319->320.

## HONEST STATUS
The full (code,bank) target-pattern asset + runtime variant selector + DMA-source change is a substantial
offline+runtime implementation scoped precisely above but NOT completed/verified in this session's budget.
Build 0320 removes the 0319 regression but does not yet fix the 64-code color bug. The 64-code evidence is
proven and is the exact remaining work.

## USER MUST VERIFY (Build 0320)
1. Rastan is no worse than Build 0316 (routing restored). 2. Exterior unchanged. 3. Cave/water colors are
still the Build-0316 state (the (code,bank) fix is the next build). Layer B unchanged.
