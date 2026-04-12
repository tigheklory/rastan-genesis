## Executive Summary
Implemented Step 2 scene/mode transition trigger wiring inside `genesistan_hook_tilemap_plane_a` only. The hook now performs a fast unsigned range check against current scene bounds and a slow unsigned scan of `genesistan_scene_a0_ranges`; on match it calls `load_scene_tiles(scene_id)` and continues into the existing descriptor path.

## Preconditions Verified
Verified before edits:
- `genesistan_hook_tilemap_plane_a` exists.
- `%a0` initially carries source address and is later overwritten by descriptor pointer setup.
- `load_scene_tiles` exists and is callable.
- `genesistan_scene_a0_ranges` exists in ROM.
- `genesistan_current_scene_id`, `genesistan_scene_a0_lo`, and `genesistan_scene_a0_hi` exist in WRAM.

## Preamble Insertion Location
Inserted after destination validation and strip row/col derivation, immediately before:
`lea ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0`

Added explicit completion label:
`.Lscene_preamble_done:` directly before descriptor setup.

## Fast Path (Unsigned)
Implemented exactly:
- `d0 = a0 & 0x00FFFFFF`
- `cmp.l genesistan_scene_a0_lo, d0` + `blo.s -> slow path`
- `cmp.l genesistan_scene_a0_hi, d0` + `bhi.s -> slow path`
- `bra.s .Lscene_preamble_done`

No table scan in fast path.

## Slow Path
Implemented exactly:
- `a1 = genesistan_scene_a0_ranges`
- `d1 = 0` scene index
- loop over 3 `(lo, hi)` pairs
- unsigned checks:
  - below `lo` -> next
  - `d0 <= hi` -> match
- no-match after 3 entries -> `bra.s .Lscene_preamble_done`

## Scene Match Handling
On match:
- `move.l d1, d0`
- `bsr load_scene_tiles`
- `bra.w .Lscene_preamble_done`

No early return; execution continues into descriptor logic.

## Descriptor Loop Preservation
Descriptor setup and descriptor loop body remain unchanged after `.Lscene_preamble_done`.
No tile extraction, LUT, staging, or commit-path logic was modified.

## Build Verification
Executed:
- `make -C apps/rastan-direct`

Results:
- build passes
- no assembler/linker errors
- ROM artifact produced: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0017.bin`

## Final Result
Step 2 trigger preamble implemented as scoped, with unsigned fast/slow path behavior and no scope expansion beyond hook preamble wiring.
