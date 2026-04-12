## Executive Summary
Implemented a single bug fix in `genesistan_hook_tilemap_plane_a`: added missing `%d2` outer-loop column advance at `.Lbg_hook_desc_done` so descriptor processing advances columns instead of repeatedly writing one column.

## Preconditions Verified
Verified before edit:
1. `genesistan_hook_tilemap_plane_a` exists.
2. `%d2` is extracted from destination before the outer descriptor loop.
3. `.Lbg_hook_desc_done` advances `%d5` by `0x00000400`.
4. `%d2` was not being advanced at `.Lbg_hook_desc_done`.
5. Bug was present in current source.

## Bug Mechanism Confirmed
`%d2` is the staged BG column index used in row write addressing. The outer descriptor loop advanced `%d5` by `0x400` per descriptor (equivalent to +4 columns), but `%d2` remained fixed. As a result, all descriptors overwrote the same column and most columns retained checkerboard fill.

## Exact Fix Applied
At `.Lbg_hook_desc_done`, after:
`addi.l  #0x00000400, %d5`
and before:
`dbra    %d6, .Lbg_hook_desc_loop`
inserted exactly:
- `addq.w  #4, %d2`
- `andi.w  #0x003F, %d2`

No other logic was changed.

## Outer Loop Semantics Preserved
Outer loop now performs:
1. process descriptor
2. advance `%d5` by `0x400`
3. advance `%d2` by 4 columns
4. wrap `%d2` at 64
5. iterate

Row logic, invalid-descriptor path, descriptor count, tile lookup, nametable writes, and dirty-bit behavior were preserved.

## Build Verification
Executed:
- `make -C apps/rastan-direct`

Result:
- build succeeded
- no assembler errors
- no unresolved symbols
- no duplicate labels
- ROM artifact produced: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0019.bin`

## Runtime Expectation
Runtime is expected to change by allowing all 16 descriptors in each hook pass to cover advancing columns instead of repeatedly overwriting one column.

## Final Result
Single-bug `%d2` column-advance fix implemented at the required location with successful build and no scope expansion.
