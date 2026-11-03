# Andy — Build 0141 PC090OJ Precomputed Tile-DMA Worklist (Implementation)

**Date:** 2026-07-06
**Type:** Authorized one-off Andy implementation of the reviewed design `docs/design/Andy_pc090oj_precomputed_tile_dma_worklist.md`.
**Baseline:** Build 0140 (`f6e63eb3e3a6d5e82caf9e151ef2eb1c23418633ee7118adad51f1c2081a135c`).
**Branch:** `rastan-direct-proposal` (unchanged; checkpoint HEAD `5182e0092f9d3ee5bf5c5d7b716ac3ac40cc7999`; **not committed, not pushed**).

## Repository preflight
- `git status --short`: clean before edits. Branch `rastan-direct-proposal`. HEAD = checkpoint `5182e009…`. No stash/reset/clean/branch op performed.

## Static preflight (all 7 premises PASS)
1. Code-vs-resident compared **before** DISPLAY_OFF — `.Lpc090oj_emit_slot` (compare + changed-bit) runs in `.Lvcs_mirror_scan → vdp_prepare_sprites`, pre-OFF. ✓
2. Each emitted SAT slot processed once/prepare — emit uses `d0 = pc090oj_emitted_count`, +1/emit. ✓
3. Emitted/active count ≤ 80 — emit gate `cmpi #80 … blo emit / else dropped`. ✓
4. DISPLAY_OFF tile path scanned fixed 80 slots — old `.Lvcs_tile_dma` `cmpi #80,%d7`. ✓
5. Changed bit (0x0004) had no consumer besides `.Lvcs_tile_dma` (`btst #2`); valid bit (0) still consumed by link/decay and preserved. ✓
6. `.Lvcs_clear_dirty` cleared descriptor touched flag (bit 15, never read) + `staged_sprite_dirty` (write-only; SAT DMA is active-count-based); both re-cleared next frame by `.Lvcs_clear_generated_sprite_state`. ✓
7. Residency safely updatable after DMA — 68k bus-stalls through the 68k→VRAM DMA. ✓

No contradiction ⇒ implemented.

## Change (single production source: `apps/rastan-direct/src/pc090oj_hooks.s`)
1. **WRAM (BSS):** `pc090oj_tile_dma_worklist` = 80 × `{word slot, word code}` = 320 B; `pc090oj_tile_dma_count` = 1 word. Placed between `sprite_tile_resident_code` and `pc090oj_object_ram`; `.global` added.
2. **Reset:** `clr.w pc090oj_tile_dma_count` at the top of `vdp_prepare_sprites` (before any emit can append).
3. **Append (pre-OFF):** new leaf `.Lpc090oj_worklist_append_d0_d6`, called from the `emit_slot` residency-mismatch branch; **render path only** (`tst.w pc090oj_scan_active; beq` skips legacy producer emits). Writes `{slot=d0, code=d6}` payload, then increments the count (publish-count-last). `cmpi #80` defensive full-guard. Preserves all caller registers (movem `%d1/%d2/%a0`); leaves `d0`/`d6` intact; does not touch `a1` (live SAT ptr). The `emit_slot` valid/touched flag store is unchanged (valid bit still set for link-chain).
4. **Commit (inside DISPLAY_OFF):** `.Lvcs_tile_dma` replaced — the fixed 80-slot descriptor scan removed; now `move.w pc090oj_tile_dma_count,%d7; beq done` (zero-entry fast path), then a `count`-bounded loop deriving the existing ROM source (`rastan_pc090oj + code*128`), the existing slot-keyed VRAM dest (`(SPRITE_TILE_BASE+slot*4)*32`), the existing 64-word DMA, and updating `sprite_tile_resident_code[slot]` **only after** the DMA trigger.
5. **Removed:** `.Lvcs_clear_dirty` routine and its `bsr` in `vdp_commit_sprites_vram`.

Preserved unchanged: object mirror, candidate handling, `emit_slot` descriptor/SAT emission, `.Lvcs_link_chain_build`, active count, SAT links, `.Lvcs_sat_dma`, sprite ordering, `_vblank_service`/VBlank order/DISPLAY_OFF-ON placement, frame model, `boot.s`, PC080SN, specs.

## Build
- `make -C apps/rastan-direct release` → **GATE_PASS**, boot guard PASS, 30 s auto-trace clean (no crash).
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0141.bin`
- **SHA256:** `cebd389e8114b316881188623b41d4b71808b5738a39d2cd4a773163bc8aa04c`
- **Size:** 1,562,248 B (Build 0140 = 1,562,240; +8 B, matching the coverage delta). Rolling == numbered (`cmp -s` = 0).
- **Files changed:** `apps/rastan-direct/src/pc090oj_hooks.s` (the authorized production source); build byproducts (`out/*.o/.elf`, `out/symbol.txt`, disasm, `build/rom_inventory.json`, trace log); `AGENTS_LOG.md`.
- **Coverage-invariant bump (only tool touch):** `CANONICAL_TOTAL_GENESIS_BYTES_COVERED 0x17D680 → 0x17D688` in `tools/translation/postpatch_startup_rom.py` and `verify_canonical_rom.py` — a **value-only** update (no tool logic), the routine per-build coverage bookkeeping every prior Genesis-code build performed; required because the hard postpatch coverage gate blocks ROM production otherwise. **Flagged for Tighe's confirmation** — it is the sole change outside `pc090oj_hooks.s`/`AGENTS_LOG.md`. `opcode_replace` count is **unchanged (133)**.

## Address-map / WRAM
- `address_map.json`: **gaps = 0, overlaps = 0**; `total_genesis_bytes_covered = 0x17D688`; **no patched-site or wrapper change** (`opcode_replace_and_rom_opcode_replace = 133`).
- WRAM (Build 0141 `out/symbol.txt`): `sprite_tile_resident_code` `0xFF67CE` (160 B) → `pc090oj_tile_dma_worklist` `0xFF686E` (320 B) → `pc090oj_tile_dma_count` `0xFF69AE` (2 B) → `pc090oj_object_ram` `0xFF69B0`. Contiguous, no overlap; +322 B vs Build 0140.
- Old routine boundary: `.Lvcs_tile_dma` = fixed 80-slot descriptor scan. New: `runtime_genesis_pc` `vdp_commit_sprites_vram = 0x072166`; `vdp_prepare_sprites = 0x07214e`; `_vblank_service = 0x0700C2` and DISPLAY_OFF/ON sites `0x0700CE`/`0x0700E6` **unchanged** vs Build 0140.

## Notes
No branch/commit/push. No `boot.s`, PC080SN, spec, Makefile, VBlank-order, DISPLAY_OFF/ON, or frame-model change. Runtime validation in the companion `docs/validation/Andy_pc090oj_tile_dma_worklist_build_0141_runtime.md`.
