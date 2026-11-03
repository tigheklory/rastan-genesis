# Cody — PC080SN BG Hook Implementation

## 1. Executive Summary
The `genesistan_hook_tilemap_plane_a` stub in `apps/rastan-direct/src/main_68k.s` was replaced with a real PC080SN BG strip staging implementation. The hook now reads arcade-produced strip state from WRAM, decodes 16 descriptors per call, writes translated nametable words into `staged_bg_buffer`, updates the BG destination pointer, and sets `bg_dirty` so the existing VBlank BG commit publishes staged data.

## 2. Root Cause Reference
Root cause reference: `docs/design/Andy_arcade_execution_reachability_vs_static_checkerboard.md`.

Confirmed blocker from that audit:
- hook was stub-only
- no staged BG writes
- `bg_dirty` never re-set after frame 1
- checkerboard persisted indefinitely

## 3. Old Stub Behavior
Previous implementation:
- incremented `hook_plane_a_hits`
- returned immediately
- performed no descriptor decode
- performed no `staged_bg_buffer` writes
- did not set `bg_dirty`

## 4. New Hook Behavior
New `genesistan_hook_tilemap_plane_a` behavior:
1. Preserves registers with `movem.l`.
2. Reads strip index from `A5+0x10CA`.
3. Reads BG destination pointer from `A5+0x10A0`.
4. Validates destination pointer against BG C-window range (`0xC00000..0xC03FFF`) and alignment.
5. Computes row/column from destination pointer.
6. Iterates 16 descriptor pointers from `A5+0x1000`.
7. For each valid descriptor:
   - reads `attr_word` and `table_base` from arcade ROM data
   - builds 5-bit attr key and maps it through `genesistan_pc080sn_attr_lut`
   - reads 4 tile codes (strip rows), maps each through `genesistan_pc080sn_tile_vram_lut`
   - combines attr+tile into Genesis nametable words
   - writes words into `staged_bg_buffer`
   - sets `bg_dirty = 1`
8. Advances and writes back updated destination pointer to `A5+0x10A0`.
9. Returns with full register restore.

## 5. Rainbow-Islands-Derived Architecture Decisions
Rainbow-Islands-derived architecture choices used here:
- producer hook stages WRAM state only
- no VDP writes in hook
- VBlank remains sole hardware publish owner
- dirty/publication split remains hook sets dirty, VBlank consumes dirty

## 6. Rastan-Arcade-Derived Decode Semantics
Rastan-arcade semantics used as source of truth:
- strip index source: `A5+0x10CA`
- BG dest_ptr source/update: `A5+0x10A0`
- descriptor count: 16
- per-descriptor row writes: 4
- descriptor list source in WRAM (`A5+0x1000`)
- descriptor validation guards (odd/out-of-range checks)
- table-base guard and strip-index-based row stride logic

## 7. SGDK-Derived Fragments Used Only After Independent Validation
SGDK was treated as a limited artifact source only.

Borrowed fragment class (after validation against current disassembly/Andy audit):
- descriptor-loop structure and attr/tile LUT usage pattern from `genesistan_asm_tilemap_commit_bg`.

Validation basis:
- matched to the documented Rastan BG producer contract and offsets in Andy’s audited plan and disassembly notes.

## 8. Exact Files Modified
- `apps/rastan-direct/src/main_68k.s`
- `docs/design/Cody_pc080sn_bg_hook_implementation.md`
- `AGENTS_LOG.md`

## 9. Permanent vs Temporary Classification
- `genesistan_hook_tilemap_plane_a` real body: `PERMANENT` (required runtime bridge)
- `genesistan_pc080sn_tile_vram_lut` incbin in this file: `BRINGUP_ONLY` placement (functional now, later may be moved to dedicated asset section)
- `genesistan_pc080sn_attr_lut` incbin in this file: `BRINGUP_ONLY` placement (functional now, later may be moved to dedicated asset section)

## 10. Scaffolding Inventory
- No new debug/proof counters added.
- No bypass stubs retained in hook.
- Existing `hook_plane_a_hits` counter remains pre-existing and unchanged.

## 11. Removal / Revert Plan
- No revert planned for the hook body itself.
- Optional follow-on cleanup: move LUT storage from `main_68k.s` to dedicated data/object asset linkage without changing hook semantics.
- Revert method (if required): restore previous hook stub and remove LUT symbol references from this file.

## 12. Build Artifact Path
- Canonical latest ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Numbered artifact emitted by build: `dist/rastan-direct/rastan_direct_video_test_build_0006.bin`

## 13. Verification Performed
- Build completed successfully via `make -C apps/rastan-direct`.
- Patch manifest confirms hook patch remains applied at arcade site:
  - `arcade_pc: 0x055968`
  - `rom_pc: 0x055B68`
  - replacement to `genesistan_hook_tilemap_plane_a`.
- Source-level verification confirms hook now:
  - reads strip index and dest_ptr from required WRAM offsets
  - writes to `staged_bg_buffer`
  - sets `bg_dirty`

## 14. Risks / Known Limitations
- Runtime visual correctness still depends on live descriptor/table population cadence and current tile-content preload state.
- LUT placement in this source file is functional but not final packaging architecture.

## 15. Final Verdict
The BG hook is no longer a stub. The implementation now performs real PC080SN descriptor-driven BG staging and dirty signaling, which removes the previously identified architectural blocker between arcade execution and BG publication.
