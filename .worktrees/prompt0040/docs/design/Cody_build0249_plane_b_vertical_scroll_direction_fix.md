# Cody Build 0249 Plane B Vertical Scroll Direction Fix

## Baseline

- Forward source checkpoint: Build 0248, counter `248`.
- Candidate produced: Build 0249, counter `249`.
- Required build command used:
  - `source tools/setup_env.sh && RASTAN_GAMEPLAY_HUD_SPRITES=2 make -C apps/rastan-direct release`
- Scope: Plane B vertical VSRAM direction/phase only.
- Not touched: Plane A source formula, collision, rope/reset, PC090OJ, palettes, audio, gameplay state, source descriptors.

## Problem

User video of Build 0248 showed vertical movement with Plane A/world moving in the expected direction while Plane B clouds/mountains moved the opposite way. Build 0248 native Plane B now uses the same `physical_row = logical_row & 31` resident-window contract as Plane A, but its VSRAM path still kept the old projector-era 8-pixel phase mask.

## Proven Cause

In Build 0248/working source before this task, `vdp_commit_scroll` used:

- Plane A gameplay Y VSRAM: `(-staged_scroll_y_fg + 8) & 0x01FF`
- Plane B gameplay Y VSRAM: `(-staged_scroll_y_bg + 8) & 0x0007`

The `0x0007` mask preserved only tile-row phase and discarded the full 9-bit vertical ring offset. That was valid only for the older tall-buffer/projector architecture, not for native Plane B rows in the same 32-row resident window as Plane A.

Andy's prior Build 0247 evidence is retained as prerequisite proof:

- `a5@0x10EE == a5@0x10B0` for gameplay vertical scrolling.
- Plane B entering-row formulas match Plane A:
  - increasing visible top: `(new_visible_top + 31) & 63`
  - decreasing visible top: `new_visible_top & 63`
- Both native planes use `physical_row = logical_row & 31`.

Therefore Plane B must carry the same full 9-bit VSRAM value as Plane A unless runtime proves a separate scroll source. No separate source was found.

## Implementation

Changed `apps/rastan-direct/src/vdp_comm.s` only:

- Replaced gameplay Plane B Y-scroll mask `andi.w #0x0007, %d0` with `andi.w #0x01FF, %d0`.
- Added a narrow comment documenting that native Plane B now shares the Plane A resident-window contract.

No semantic source formula, row formula, descriptor selection, tile conversion, or scroll staging writer was changed.

## Postpatch Disassembly Proof

Build 0249 postpatch disassembly at `vdp_commit_scroll`:

```asm
70384: movew 0xff40ea,%d0   ; staged_scroll_y_fg
7038a: negw %d0
7038c: addqw #8,%d0
7038e: cmpib #1,0xffb1d0
70396: bnes 0x7039c
70398: andiw #511,%d0       ; Plane A gameplay full 9-bit VSRAM
7039c: movew %d0,0xc00000
703a2: movew 0xff40e8,%d0   ; staged_scroll_y_bg
703a8: negw %d0
703aa: addqw #8,%d0
703ac: cmpib #1,0xffb1d0
703b4: bnes 0x703ba
703b6: andiw #511,%d0       ; Plane B gameplay full 9-bit VSRAM
703ba: movew %d0,0xc00000
```

This proves Build 0249 ROM code emits identical full-range Y-scroll math for Plane A and Plane B in gameplay scene `1`.

## Runtime Scroll Trace

Focused trace artifacts:

- `states/traces/build0249_plane_b_vertical_scroll_direction_fix_clean_20260802_112725/`
- Script: `build0249_plane_b_scroll_clean.lua`
- Samples: `samples.csv`
- Events: `events.csv`
- Summary: `summary.txt`
- MAME exit code: `0`

Final sampled gameplay state at frame `1500`:

```text
state=0002/0003/0000 scene=01
A5+10B0=0149
A5+10EE=0149
staged_scroll_y_fg=0149
staged_scroll_y_bg=0149
Plane A VSRAM calc=(-0149 + 8) & 01FF = 00BF
Plane B VSRAM calc=(-0149 + 8) & 01FF = 00BF
bg_row_dirty=00000000
bg_tall_dirty=00
bg_tall_project_base=0000
```

Representative gameplay samples from frames `600..1500` all show:

```text
scene=01, A5+10B0=0149, A5+10EE=0149,
staged_scroll_y_fg=0149, staged_scroll_y_bg=0149,
fg_vsram_calc=00BF, bg_vsram_calc=00BF
```

This proves the sampled gameplay runtime state feeds identical Plane A and Plane B vertical scroll values after the Build 0249 correction.

## Helper / Compatibility Census

Runtime write-tap evidence from the focused trace:

- `staged_bg_tall_buffer_write`: `158` writes, first frame `0`, last frame `0`.
- `bg_dirty_state_write`: `4` writes, first frame `0`, last frame `0`.
- During gameplay samples (`scene=01`, frames `600..1500`):
  - `bg_tall_dirty=00`
  - `bg_tall_project_base=0000`
  - no tall-buffer writes after initialization.

Disassembly evidence for dispatch/helper routes:

- Native Plane B row helper entry remains at runtime `0x0709C4`.
- Native Plane B producer helper entry remains at runtime `0x070AF2`.
- Legacy `genesistan_hook_tilemap_bg_fill` remains at runtime `0x0710D8` for non-gameplay/frontend paths.
- Legacy `genesistan_hook_tilemap_bg_fill_tall` remains linked at runtime `0x0711AE`, but the focused gameplay trace did not observe gameplay tall-buffer writes.
- `vdp_project_bg_tall_if_dirty` remains linked at runtime `0x070138`, but gameplay tall state stayed clear in sampled scene `1`.

## Double-Dispatch Resolution

The Build 0248 report excerpt omitted the branch after the native helper, creating a false-looking fallthrough risk. Build 0249 disassembly proves the dispatch is single-route:

```asm
724e4: tstw %d6
724e6: beqs 0x724ee
724e8: bsrw 0x70af2       ; native gameplay Plane B helper
724ec: bras 0x724f2       ; skips legacy fill
724ee: bsrw 0x710d8       ; legacy non-gameplay fill
724f2: addal #256,%a0
```

Verdict: double dispatch existed: `NO`; correction needed: `NO`.

## Build Verification

- Build output: `dist/rastan-direct/rastan_direct_video_test_build_0249.bin`
- Rolling output: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA-256: `8aad4470bf2d9fd2390823dc5aceb5a902e32e2b1906fece055c013d21087674`
- Size: `1590240` bytes
- Counter: `249`
- Numbered and rolling artifacts match: `YES`
- `GATE_PASS`: `YES`
- `RASTAN_GAMEPLAY_HUD_SPRITES=2`: build command and generated `pc090oj_config.inc` path used by release build.

## Visual Status

This task proves the VSRAM direction/phase correction in code, disassembly, and sampled runtime scroll fields. I did not perform a human visual gameplay acceptance pass in BlastEm/Exodus. User should verify Build 0249 visually against the Build 0248 reversed-Plane-B-scroll video.

Expected visual result:

- During the vertical drop, Plane B clouds/mountains should scroll in the same vertical phase/direction as Plane A/world under the native resident-window contract.
- P1 score/`1UP`/HUD behavior should remain as Build 0248; no HUD or PC090OJ change was made.

## Architecture Compliance

- Semantic arcade source decision preserved.
- No C-window/name-RAM shadow, tall-buffer projection, or software PC080SN path was introduced.
- Transitional compatibility remains linked but is not gameplay Plane B authority for the sampled runtime path.
- No Plane A/collision/rope/reset/palette/PC090OJ logic changed.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001-adjacent native PC080SN Plane B gameplay rendering.
- New issues opened: none.
- Issues closed: none.
- Deferred intentionally: rope/reset/collision, PC090OJ, palette/HUD, remaining native Plane B visual acceptance.

## KNOWN_FINDINGS Impact

Option A: no new finding to index. This is a bounded correction to the Build 0248 native Plane B VSRAM commit path.

## STOP Status

STOP not triggered. The exact cause was proven and the fix boundary was one VSRAM mask in `vdp_commit_scroll`.
