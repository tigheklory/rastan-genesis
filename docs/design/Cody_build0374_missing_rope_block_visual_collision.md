# Cody — Build 0374 missing rope-side ledge (stopped without patch)

## Scope and correction

Build 0373's `0x02A290 / 0x3008` identification was wrong. That descriptor is a
spawn-marker-bearing purple-rock block, not the requested standable ledge. The live arcade route
selects `0x02C550`, attribute `0x0003`, metatile `0x2024`, for rows 40..43 / columns 52..55. Its
collision contract is uniformly `0x0001`. The adjacent known-good wall is `0x02C554`.

## Focused 0373 boundary result

The existing cave route was extended only with target-cell sampling in
`states/traces/build0374_missing_rope_block_20260923/build0374_live_target_probe.lua`.

At the retained rope state, `resolve_plane_a_cell` and `staged_fg_buffer` contain the target's
nonzero name words:

```text
62BF 62C8 62B9 62C9
62D8 62EE 62DA 62E2
62DF 630A 62D0 630F
62F2 6308 62F8 62EB
```

The adjacent `0x02C554` control contains:

```text
6315 62D2 62D3 6310
62DD 62F3 62E5 62FC
62D4 62C5 62D7 630C
62EF 6307 62C3 62C7
```

For columns 52..55, the VBlank column publisher writes the target staging values to the exact
row 8..11 Plane-A destinations. A later row DMA republishes the same target values. The focused
VDP command reconstruction observed no later PIO or DMA write to any of those 16 destinations
through the reproduced rope state. The adjacent control follows the same publication path.

The collision producer writes `0x0001` to all 16 target cells and all 16 adjacent-control cells;
the sampled live collision grid retains those values. Thus source resolution, staging, VBlank
job creation, emitted name values, absence of a later name-table overwrite, and collision-grid
publication are all correct in this automated 0373 route.

Direct reads through MAME's exposed `:gen_vdp` `videoram` space returned zero for both the target
and visibly correct neighboring terrain, so that interface is not a valid final-VRAM oracle in
this environment. It cannot establish a target-only VRAM divergence.

## Stop decision

The requested first differing boundary was not proven. No production source, map data, tile
asset, collision data, or build input was changed, and Build 0374 was not produced. This follows
the explicit instruction to stop at the last correct boundary instead of making a speculative
fix.

