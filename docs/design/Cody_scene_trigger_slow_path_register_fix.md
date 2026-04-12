## Executive Summary
Implemented a single bug fix in `genesistan_hook_tilemap_plane_a` slow-path scene scan: removed `%d1`/`%d2` clobber risk by moving scan temporaries to non-conflicting registers. Fast path and descriptor loop behavior were preserved.

## Preconditions Verified
Verified before edit:
1. `genesistan_hook_tilemap_plane_a` exists.
2. Scene-trigger preamble exists.
3. Slow path used `%d1` as scene counter and `%d2` as scan scratch.
4. Descriptor loop later depends on `%d1` and `%d2` for row/column addressing and dirty-bit marking.
5. Bug was present in current source.

## Bug Mechanism Confirmed
Before the fix, slow path overwrote:
- `%d1` (row index) with scene counter
- `%d2` (column/index base) with range `lo`

When the hook continued into descriptor logic, those corrupted values were reused for staged buffer indexing and row dirty marking, causing latent corruption on first real scene transition.

## Exact Fix Applied
Slow-path scan now uses non-conflicting registers:
- `%d3` = scene counter
- `%d4` / `%d5` = range `lo` / `hi` scratch

Additionally, because `%d5` carries dest pointer for post-loop progression, `%d5` is preserved/restored inside slow path via `%d6` during scan/call flow.

No stack push/pop workaround was used, and no calling conventions were changed.

## Fast Path Preserved
Fast path remains behaviorally unchanged:
- `%a0` masked with `0x00FFFFFF`
- unsigned range check against `genesistan_scene_a0_lo/hi`
- branch to `.Lscene_preamble_done` on match

No fast-path logic redesign was applied.

## Descriptor Loop Preservation
Descriptor loop semantics are preserved:
- `%d1` still carries expected row index when loop starts
- `%d2` still carries expected column-derived value when loop starts
- tile extraction, LUT lookup, nametable write, and row dirty-bit logic remain unchanged

No descriptor-loop algorithm changes were made.

## Build Verification
Executed:
- `make -C apps/rastan-direct`

Result:
- build succeeded
- no assembler errors
- no unresolved symbols
- no duplicate labels
- ROM artifact produced: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0018.bin`

## Runtime Expectation
Runtime behavior should remain unchanged during Title scene (fast path dominant), while avoiding staged-buffer addressing corruption when the first real scene transition forces slow-path execution.

## Final Result
Single-bug slow-path register-clobber fix completed with minimal scope and successful build.
