# 1. Executive Summary
Step 5 was implemented by relocating tile-commit ownership from the BG strip commit function to top-level `_VINT_handler` sequencing.

# 2. Previous Tile Commit Ownership
Before this step:
- `_VINT_handler` called `vdp_commit_bg_strips_if_dirty`
- `vdp_commit_bg_strips_if_dirty` internally called `vdp_commit_tiles_if_dirty`

Tile upload was coupled to BG commit ownership.

# 3. New Top-Level VBlank Tile Commit Ownership
After this step:
- `_VINT_handler` now calls `vdp_commit_tiles_if_dirty` directly as a top-level VBlank step
- `_VINT_handler` then calls `vdp_commit_bg_strips_if_dirty`
- `vdp_commit_bg_strips_if_dirty` no longer invokes tile commit internally

# 4. Exact Source Edits
File modified:
- `apps/rastan-direct/src/main_68k.s`

Edits made:
1. Inserted top-level call in `_VINT_handler` immediately before BG row commit:
   - `bsr     vdp_commit_tiles_if_dirty`
2. Removed internal call from `vdp_commit_bg_strips_if_dirty`:
   - removed `bsr     vdp_commit_tiles_if_dirty`

No other edits were made.

# 5. Verification of Decoupling
Verification checks:
- BG commit function contains no tile commit invocation
- Exact call-site grep result for `bsr vdp_commit_tiles_if_dirty` shows one remaining call, at `_VINT_handler`

Result:
- tile commit is now owned only by top-level VBlank path
- BG commit now owns only row publication and dirty-bit clearing

# 6. Build Verification
Executed:
- `make -C apps/rastan-direct`

Result:
- build passed successfully
- no assembler/linker errors
- ROM artifact produced: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0014.bin`

# 7. Runtime Expectations
Expected behavior remains intentionally unchanged:
- tile upload still occurs during VBlank under `tiles_dirty` control
- BG row commit still occurs during VBlank under `bg_row_dirty` control
- only ownership location of tile commit changed

# 8. Final Result
Tile commit ownership is now top-level in `_VINT_handler`, and BG strip commit is decoupled from tile-upload triggering.
