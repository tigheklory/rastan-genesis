1. Executive Summary
Implemented one surgical fix in `genesistan_hook_tilemap_plane_a`: added the missing `%d1` row reset in the outer descriptor-loop tail so row selection remains constant across all 16 descriptors while `%d2` continues horizontal advancement.

2. Preconditions Verified
Verified before edit:
- `genesistan_hook_tilemap_plane_a` exists.
- `%d1` is extracted from destination before the outer descriptor loop.
- Inner row loop advances `%d1` by 1 for 4 iterations.
- `.Lbg_hook_desc_done` contains existing `%d2` advance (`addq.w #4, %d2` / `andi.w #0x003F, %d2`).
- `.Lbg_hook_desc_done` did not contain `%d1` reset by subtracting 4.
- Bug was present in current source.

3. Bug Mechanism Confirmed
Inner row loop increments `%d1` four times per descriptor. Without resetting `%d1` at descriptor tail, row origin drifts by +4 each descriptor, creating diagonal write distribution while destination semantics require constant row group across descriptor sweep.

4. Exact Fix Applied
At `.Lbg_hook_desc_done`, after existing `%d2` update block and before `dbra %d6, .Lbg_hook_desc_loop`, inserted exactly:
- `subq.w  #4, %d1`
- `andi.w  #0x001F, %d1`

No other code was changed.

5. Outer Loop Semantics Preserved
Outer loop behavior after fix:
1. process descriptor
2. advance `%d5` by `0x400`
3. advance `%d2` by 4 columns
4. wrap `%d2` at 64
5. reset `%d1` back to original row group
6. continue loop

`%d5` and `%d2` progression are unchanged from prior fix.

6. Invalid-Descriptor Path Preservation
Invalid path still does:
- `addq.w #4, %d1`
- `andi.w #0x001F, %d1`
then falls through `.Lbg_hook_desc_done`, where new reset subtracts 4 and wraps.
Net effect preserves original row group as required, with no special-case branch additions.

7. Build Verification
Executed:
- `make -C apps/rastan-direct`

Result:
- build succeeds
- no assembler errors
- no unresolved symbols
- no duplicate labels
- ROM artifact produced: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0020.bin`

8. Runtime Expectation
Expected runtime change: descriptors sweep horizontally across the same 4-row band per hook pass instead of diagonal drift from accumulated row offset.

9. Final Result
Single-bug `%d1` row-reset fix implemented at required location with successful build and no scope expansion.
