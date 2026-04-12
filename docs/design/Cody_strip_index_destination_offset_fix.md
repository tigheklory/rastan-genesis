1. Executive Summary
Implemented a single bug fix in `genesistan_hook_tilemap_plane_a`: added `%d7` strip-index contribution to destination column offset inside `.Lbg_hook_row_loop`.

2. Preconditions Verified
Verified before edit:
- `genesistan_hook_tilemap_plane_a` exists.
- `%d7` is loaded from `ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5)` near hook entry.
- `%d7` is used on the source side in row processing (`move.w %d7, %d0` then `adda.w %d0, %a4`).
- Destination write offset used `%d2` only and did not include `%d7`.
- Bug was present in current source.

3. Bug Mechanism Confirmed
Hook receives strip calls with `%d7` in 0..3. Source tile selection already used `%d7`, but destination column offset did not. All strip calls therefore targeted the same base column groups, leaving sub-columns 1..3 of each group unwritten/checkerboard.

4. Exact Fix Applied
Inside `.Lbg_hook_row_loop`, after existing:
- `add.w   %d2, %d0`
- `add.w   %d2, %d0`
and before staging write, inserted exactly:
- `add.w   %d7, %d0`
- `add.w   %d7, %d0`

No other code was changed.

5. Row-Loop Semantics Preserved
Destination byte offset now computes as:
`row*128 + (column_group + strip_index)*2`

Row handling (`%d1`), column-group handling (`%d2`), source pointer arithmetic, descriptor parsing, and dirty-bit behavior are unchanged.

6. Bounds Verification
Verified by reasoning:
- `%d2` max = 60
- `%d7` max = 3
- `%d2 + %d7` max = 63
- byte offset max = `31*128 + 63*2 = 4094` within 4096-byte `staged_bg_buffer`

No runtime bounds checks were added.

7. Build Verification
Executed:
- `make -C apps/rastan-direct`

Result:
- build succeeds
- no assembler errors
- no unresolved symbols
- no duplicate labels
- ROM artifact produced: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0021.bin`

8. Runtime Expectation
Expected behavior change: strip calls `%d7=0..3` populate destination sub-columns 0..3 of each 4-column group instead of repeatedly targeting only the base column.

9. Final Result
Single-bug `%d7` destination-offset fix implemented in the required row-loop location with successful build and no scope expansion.
