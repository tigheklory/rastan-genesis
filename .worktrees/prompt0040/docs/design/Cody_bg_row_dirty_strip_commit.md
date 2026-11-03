# 1. Executive Summary
Step 4 was implemented: whole-plane BG dirty/commit was replaced with row-based `bg_row_dirty` strip commit in `apps/rastan-direct/src/main_68k.s`.

# 2. bg_dirty Variable Replacement
`bg_dirty` was removed and replaced with:
- `bg_row_dirty: .long 0`

This provides one dirty bit per BG row (32 rows).

Initialization was updated to:
- `move.l #0xFFFFFFFF, bg_row_dirty`

so all rows are committed on first frame.

# 3. Hook Dirty-Bit Update
In `genesistan_hook_tilemap_plane_a`, whole-plane dirty set was replaced with row-bit marking using register-based bit operations.

Implemented pattern:
- `move.l  bg_row_dirty, %d0`
- `bset    %d1, %d0`
- `move.l  %d0, bg_row_dirty`

`%d1` is the existing computed row index already used by staging logic.

# 4. FG Path Evaluation
No FG path changes were made.

Only BG dirty granularity and BG commit behavior were changed.

# 5. Reference Cleanup Verification
Verified after change:
- no `bg_dirty` references remain
- no `vdp_commit_bg` whole-plane function remains
- `_VINT_handler` now calls `vdp_commit_bg_strips_if_dirty`

# 6. Build Verification
Executed:
- `make -C apps/rastan-direct`

Result:
- build passed successfully
- no assembler/link errors
- ROM artifact produced at `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0012.bin`

# 7. Final Result
Row-based BG strip commit is active.

Behavioral intent is preserved except for commit granularity:
- frame 1 commits all rows
- subsequent frames commit only rows marked dirty by the hook
- dirty rows are cleared per-row with early exit when mask reaches zero.
