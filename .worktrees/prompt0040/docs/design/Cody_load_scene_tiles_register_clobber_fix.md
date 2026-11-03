## Executive Summary
Fixed one bug in `load_scene_tiles` in `apps/rastan-direct/src/main_68k.s`: tile ROM source pointer computation now occurs before the `vdp_set_vram_write_addr` helper call, preventing `arcade_tile` corruption from helper register clobber.

## Preconditions Verified
Verified in current source before edit:
1. `load_scene_tiles` exists.
2. In the manifest loop, `arcade_tile` and `vram_slot` are read, `vdp_set_vram_write_addr` is called, and tile source pointer was computed afterward from the tile register.
3. `vdp_set_vram_write_addr` is called from `load_scene_tiles`.
4. Bug is present: helper writes `%d2`, which destroys the prior `arcade_tile` value in `%d2`.

## Bug Mechanism Confirmed
`load_scene_tiles` used `%d2` for `arcade_tile`, then called `vdp_set_vram_write_addr`.
`vdp_set_vram_write_addr` overwrites `%d2` while building VDP control bits.
After return, source pointer math used the clobbered `%d2`, so uploads read wrong tile ROM source addresses.

## Exact Fix Applied
Inside `.Lload_scene_pair_loop`, moved this block:
- `lea genesistan_pc080sn_tile_rom, %a2`
- `%d4 = (arcade_tile << 5)`
- `adda.l %d4, %a2`

to execute before:
- `%d0 = (vram_slot << 5)`
- `bsr vdp_set_vram_write_addr`

No helper changes, no stack-save workaround, and no calling-convention changes were introduced.

## Loop Semantics Preserved
Per manifest pair, behavior is now:
1. read `arcade_tile`
2. read `vram_slot`
3. compute tile ROM source pointer from `arcade_tile << 5`
4. compute VRAM destination from `vram_slot << 5`
5. call `vdp_set_vram_write_addr`
6. write exactly 16 words to `VDP_DATA`

Sentinel handling, pair iteration order, scene-state updates, and function save/restore framing remain unchanged.

## Build Verification
Executed:
- `make -C apps/rastan-direct`

Result:
- build succeeded
- no assembler errors
- no unresolved symbols
- no duplicate labels
- ROM artifact produced (`apps/rastan-direct/dist/rastan_direct_video_test.bin`)

## Runtime Expectation
Runtime is expected to change by uploading correct PC080SN tile data for manifest pairs instead of repeated/wrong data caused by clobbered tile index during source-pointer computation.

## Final Result
Single-bug fix completed exactly as requested: source-pointer calculation moved before helper call in `load_scene_tiles`, with build success and no scope expansion.
