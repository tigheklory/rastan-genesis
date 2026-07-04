# Cody - Build 0138 PC090OJ DISPLAY_OFF Split

**Date:** 2026-07-03  
**Type:** One narrow production build + static/runtime evidence  
**Baseline:** Build 0137, `dist/rastan-direct/rastan_direct_video_test_build_0137.bin`  
**Baseline SHA256:** `52655015379fdd8524e2c3856b491004d9e7ee7abf15c275af78fa0011175428`  
**Output:** Build 0138, `dist/rastan-direct/rastan_direct_video_test_build_0138.bin`  
**Output SHA256:** `719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615`  
**Scope:** Split PC090OJ WRAM-only sprite preparation out of the DISPLAY_OFF window. No candidate-mask changes. No active-count SAT DMA semantic changes. No tile DMA/cache/decode changes. No PC080SN changes. No BlastEm screenshot/contact-sheet automation.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-010, KF-011, KF-032, KF-036, KF-038, OPEN-001, OPEN-024, and the Build 0135/0136/0137 PC090OJ design/implementation notes. No contradiction detected.

The Build 0137 baseline SHA was verified before editing:

```text
52655015379fdd8524e2c3856b491004d9e7ee7abf15c275af78fa0011175428  dist/rastan-direct/rastan_direct_video_test_build_0137.bin
```

## Implementation

Changed only the authorized production source files:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`

The former combined `vdp_commit_sprites` wrapper was split into:

```asm
vdp_prepare_sprites:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lvcs_mirror_scan
    bsr     .Lvcs_link_chain_build
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts

vdp_commit_sprites:
vdp_commit_sprites_vram:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lvcs_tile_dma
    bsr     .Lvcs_sat_dma
    bsr     .Lvcs_clear_dirty
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

`vdp_commit_sprites` is retained as a required-symbol alias to the VRAM-only wrapper because `specs/rastan_direct_remap.json` still requires that symbol and this task did not authorize spec edits. It no longer names the old combined prepare+DMA behavior.

`_vblank_service` now runs:

```asm
bsr rastan_direct_update_inputs
bsr vdp_prepare_sprites
DISPLAY_OFF
bsr vdp_commit_tiles_if_dirty
bsr vdp_commit_bg_strips_if_dirty
bsr vdp_commit_fg_strips_if_dirty
bsr vdp_commit_sprites_vram
DISPLAY_ON
palette/scroll
jmp 0x3A208
```

## Static Verification

Generated Build 0138 symbols:

```text
000700c2 T _vblank_service
0007202a T vdp_prepare_sprites
0007203c T vdp_commit_sprites
0007203c T vdp_commit_sprites_vram
```

Generated disassembly proves the new order:

```asm
700c2: movem.l save
700c6: bsrw 0x713ce      ; rastan_direct_update_inputs
700ca: bsrw 0x7202a      ; vdp_prepare_sprites, before DISPLAY_OFF
700ce: moveq #1,%d0
700d0: moveq #0x34,%d1
700d2: bsrw 0x7007e      ; DISPLAY_OFF
700d6: bsrw 0x7010e      ; tiles
700da: bsrw 0x70138      ; BG
700de: bsrw 0x70186      ; FG
700e2: bsrw 0x7203c      ; vdp_commit_sprites_vram, inside DISPLAY_OFF
700e6: moveq #1,%d0
700e8: moveq #0x74,%d1
700ea: bsrw 0x7007e      ; DISPLAY_ON
```

Generated wrapper disassembly:

```asm
7202a: movem.l save
7202e: bsrw 0x72080      ; .Lvcs_mirror_scan
72032: bsrw 0x7222a      ; .Lvcs_link_chain_build
72036: movem.l restore
7203a: rts

7203c: movem.l save
72040: bsrw 0x72298      ; .Lvcs_tile_dma
72044: bsrw 0x7235a      ; .Lvcs_sat_dma
72048: bsrw 0x723ea      ; .Lvcs_clear_dirty
7204c: movem.l restore
72050: rts
```

WRAM-only precondition check:

- `.Lvcs_mirror_scan` and `.Lvcs_link_chain_build` read/write PC090OJ object mirror, candidate bitset, descriptor table, SAT staging, counters, and active count. They do not reference `VDP_CTRL` / `VDP_DATA`.
- `.Lvcs_tile_dma` and `.Lvcs_sat_dma` are the routines that load `VDP_CTRL` and perform DMA register programming.
- The routines between `vdp_prepare_sprites` return and `vdp_commit_sprites_vram` entry are `vdp_set_reg`, tile commit, BG commit, and FG commit in `vdp_comm.s`. Source grep found no `staged_sprite_*` or `pc090oj_*` accesses in `vdp_comm.s`; no sprite-staging mutation path exists between prepare and DMA in this service sequence.

## Build Verification

First release attempt stopped at the canonical invariant gate after assembly/postpatch computed the mechanical split delta:

```text
expected total_genesis_bytes_covered=0x17D588 and opcode_replace patched_site count=133;
got total_genesis_bytes_covered=0x17D598 opcode_replace patched_site count=133
```

Only the paired canonical invariant constants were updated to `0x17D598`; `opcode_replace` stayed `133`.

Second release invocation passed:

```text
GATE_PASS
Numbered name verified: rastan_direct_video_test_build_0138.bin
```

Build 0138 artifacts:

```text
719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615  dist/rastan-direct/rastan_direct_video_test_build_0138.bin
719a9af2e8a4afebed793af30687c19e31d6817ea0a8f50b71d9756988044615  apps/rastan-direct/dist/rastan_direct_video_test.bin
size: 1562008 bytes
```

Postpatch manifest gate values:

```text
postpatch_expected_opcode_replace_sites = 133
postpatch_expected_total_genesis_bytes_covered = 0x17D598
patch_counts = {'opcode_replace_and_rom_opcode_replace': 133}
build_context = canonical
```

## Evidence Artifacts

Trace directory:

```text
states/traces/build0138_pc090oj_displayoff_split_20260703_222523/
```

Key files:

- `capture_displayoff_split.lua`
- `no_input_runtime_capture.log`
- `coin_start_runtime_capture.log`
- `debug_coin_start_printf/debug.log`
- `displayoff_split_reduction.json`
- `displayoff_split_reduction.md`
- `build0138_no_input_contact_sheet.png`
- `build0138_coin_start_contact_sheet.png`

The automatic release trace also completed:

```text
states/traces/rastan_direct_video_test_build_0138_mame_30s_20260703_222418/
```

## Runtime Evidence

MAME no-input and coin/start runs completed with status `0`. No crash occurred in the evidence runs.

Native debugger SAT DMA evidence from `debug_coin_start_printf/debug.log`:

```text
Native debugger SAT events: 1492
Complete SAT low/high/trigger triples: 497
Active counts observed: [12, 19, 23, 27, 30, 32]
```

Representative SAT DMA lengths:

| Active | Expected DMA words | D0 words | Low reg | High reg | State | Last-link proof |
|---:|---:|---:|---|---|---|---|
| `12` | `0x0030` | `0x0030` | `9330` | `9400` | `0002/0000/0000` | last slot 11 |
| `19` | `0x004C` | `0x004C` | `934C` | `9400` | `0001/0001/0000` | `slot18_w1=0500` |
| `23` | `0x005C` | `0x005C` | `935C` | `9400` | `0000/0000/0001` | `slot22_w1=0500` |
| `27` | `0x006C` | `0x006C` | `936C` | `9400` | `0000/0000/0000` | last slot 26 |
| `30` | `0x0078` | `0x0078` | `9378` | `9400` | `0002/0002/0006` | `slot29_w1=0500` |
| `32` | `0x0080` | `0x0080` | `9380` | `9400` | `0002/0002/0007` | `slot31_w1=0500` |

This matches the Build 0137 active-count set and active-count-derived DMA lengths. SAT DMA source/dest/trigger logic remains the same; only the wrapper placement changed.

## Build 0137 Comparison

`displayoff_split_reduction.md` compares Build 0138 against the Build 0137 capture set.

Summary:

- Build 0138 captures: `17`
- Build 0137 captures: `17`
- Native debugger triples: `497`, same as Build 0137
- Active-count set: `[12, 19, 23, 27, 30, 32]`, same as Build 0137
- No-input selected capture fields matched Build 0137.
- Coin/start frame-anchor dumps showed selected-field differences at frames `473`, `474`, `534`, `560`, and `620`.

Interpretation of the coin/start frame-anchor differences:

The differences are consistent with the intentional timing shift: sprite scan/link preparation now happens earlier in `_vblank_service`, before DISPLAY_OFF and before the tile/BG/FG commit calls. Some frame-done snapshots therefore sample the sprite staging structures at a different phase of the same per-frame lifecycle. The DMA-side evidence is the authoritative semantic check for the split: it shows the same active-count set, matching DMA word counts, and terminating link proof at the DMA register writes.

No unexpected regression was found in the SAT DMA length/order/link behavior. No mutation path between prepare and DMA was found statically.

## Scope Non-Actions

- No candidate mask changes.
- No active-count SAT DMA semantic changes.
- No SAT DMA source/dest/trigger changes.
- No tile DMA/cache/decode changes.
- No PC080SN changes.
- No BlastEm screenshot/contact-sheet automation.
- No bookmark cycle.
- No OPEN issue closure.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: context only; visual validation remains with Tighe's BlastEm run.
- OPEN-024 / KF-038: context for PC090OJ staging and sprite lifecycle; no issue closure.
- KNOWN_FINDINGS impact: Option A, no new durable finding indexed from this implementation alone.

## STOP

STOP triggered: **NO**.

Implementation is safely placeable for Tighe's BlastEm visual test: Build 0138 preserves the Build 0137 active-count SAT DMA semantics while moving WRAM-only PC090OJ preparation out of the DISPLAY_OFF window.
